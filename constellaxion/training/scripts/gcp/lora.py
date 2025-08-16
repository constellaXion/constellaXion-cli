"""LoRA fine-tuning script with Unsloth optimizations for GCP deployment."""

import argparse
import inspect
import os

# Must be first non-standard import!
from unsloth import FastLanguageModel, is_bfloat16_supported

from constellaxion_utils.gcp.tools import ModelManager, gcs_uri_to_fuse_path
from datasets import Dataset
from google.cloud import aiplatform, storage
import pandas as pd
import requests
from transformers import TrainingArguments
from transformers.integrations import TensorBoardCallback
from trl import SFTTrainer

# Parse cli args
parser = argparse.ArgumentParser()
parser.add_argument("--epochs", type=str, required=True, help="Training epochs")
parser.add_argument("--batch-size", type=str, required=True, help="Batch size")
parser.add_argument("--train-set", type=str, required=True, help="Training set path")
parser.add_argument("--val-set", type=str, required=True, help="Validation set path")
parser.add_argument("--test-set", type=str, required=True, help="Test set path")
parser.add_argument("--dtype", type=str, required=True, help="Data type")
parser.add_argument(
    "--max-seq-length", type=str, required=True, help="Max sequence length"
)
parser.add_argument("--bucket-name", type=str, required=True, help="GCS bucket name")
parser.add_argument(
    "--model-path", type=str, required=True, help="Model artefacts output path"
)
parser.add_argument("--model-id", type=str, required=True, help="Model ID")
parser.add_argument("--base-model", type=str, required=True, help="Base model name")
parser.add_argument(
    "--experiments-dir", type=str, required=True, help="Experiments output path"
)
parser.add_argument("--location", type=str, required=True, help="Location")
parser.add_argument("--project-id", type=str, required=True, help="Project ID")
parser.add_argument(
    "--experiment-name", type=str, required=True, help="Experiment name"
)
parser.add_argument("--alias", type=str, required=True, help="Alias")
args = parser.parse_args()

LOCAL_MODEL_DIR = "./models"
CHECKPOINT_DIR = "./checkpoints"
MODEL_NAME = args.base_model
ALIAS = args.alias
GCS_BUCKET_NAME = args.bucket_name
GCS_MODEL_PATH = args.model_path
LOCATION = args.location
PROJECT_ID = args.project_id
MODEL_ID = args.model_id
EPOCHS = args.epochs
BATCH_SIZE = args.batch_size
EXPERIMENT_NAME = args.experiment_name
EXPERIMENT_DIR = args.experiments_dir
DTYPE = args.dtype
MAX_SEQ_LENGTH = args.max_seq_length
tensorboard_path = os.environ.get("AIP_TENSORBOARD_LOG_DIR")
TRAIN_SET = f"gs://{GCS_BUCKET_NAME}/{args.train_set}"
VAL_SET = f"gs://{GCS_BUCKET_NAME}/{args.val_set}"
TEST_SET = f"gs://{GCS_BUCKET_NAME}/{args.test_set}"
OUTPUT_DIR = f"/gcs/{GCS_BUCKET_NAME}/{EXPERIMENT_DIR}"
MERGED_MODEL_DIR = f"/gcs/{GCS_BUCKET_NAME}/{MODEL_ID}/model"
SAVE_METHOD = "merged_16bit"


# Dataset
train_df = pd.read_csv(TRAIN_SET)
val_df = pd.read_csv(VAL_SET)
test_df = pd.read_csv(TEST_SET)

dataset = {
    "train": Dataset.from_pandas(train_df),
    "val": Dataset.from_pandas(val_df),
    "test": Dataset.from_pandas(test_df),
}

model_manager = ModelManager()
checkpoint = model_manager.get_latest_checkpoint(
    GCS_BUCKET_NAME, EXPERIMENT_DIR, CHECKPOINT_DIR
)

if checkpoint:
    MODEL_PATH = checkpoint
else:
    MODEL_PATH = MODEL_NAME

# Get model configs for the specified model
url = f"https://us-central1-constellaxion.cloudfunctions.net/getModelConfigsByAlias?alias={ALIAS}"
response = requests.get(url)
data = response.json()
train_kwargs = data.get("args").get("train_kwargs", {})
peft_kwargs = data.get("args").get("peft_kwargs", {})


# Initialize Unsloth FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_PATH,
    max_seq_length=int(MAX_SEQ_LENGTH),
    dtype=None if not DTYPE or DTYPE == "None" else DTYPE,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    **peft_kwargs,
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    loftq_config=peft_kwargs.get("loftq_config", None),
)

model.print_trainable_parameters()


EOS_TOKEN = tokenizer.eos_token

prompt_template = """
{prompt}
## Response:
{response}
"""


def format_prompts(example):
    """Formatter for training and validation examples"""
    output_texts = []
    for i in range(len(example["prompt"])):
        text = (
            inspect.cleandoc(
                prompt_template.format(
                    prompt=example["prompt"][i], response=example["response"][i]
                )
            )
            + EOS_TOKEN
        )
        output_texts.append(text)
    return {"text": output_texts}


# Map datasets to format_prompts
train_dataset = dataset["train"].map(
    format_prompts, batched=True, remove_columns=["prompt", "response"]
)
val_dataset = dataset["val"].map(
    format_prompts, batched=True, remove_columns=["prompt", "response"]
)

# Initialize Vertex AI with experiment tracking
aiplatform.init(
    project=PROJECT_ID,
    location=LOCATION,
    experiment=EXPERIMENT_NAME,
    experiment_description="constellaXion LoRA fine-tuning experiment",
)

tensorboard_path = gcs_uri_to_fuse_path(tensorboard_path)

# Train Model
train_args = TrainingArguments(
    **train_kwargs,
    per_device_train_batch_size=int(BATCH_SIZE),
    num_train_epochs=int(EPOCHS),
    eval_strategy="steps",
    fp16=not is_bfloat16_supported(),
    bf16=is_bfloat16_supported(),
    logging_steps=100,
    save_strategy="steps",
    save_steps=0.2,
    output_dir=OUTPUT_DIR,
    report_to=["tensorboard"],
    logging_dir=tensorboard_path,
)

trainer = SFTTrainer(
    formatting_func=format_prompts,
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    dataset_text_field="text",
    max_seq_length=int(MAX_SEQ_LENGTH),
    dataset_num_proc=2,
    packing=True,  # Packs short sequences together to save time!
    args=train_args,
    callbacks=[TensorBoardCallback()],
)

# Train model
if checkpoint:
    trainer.train(resume_from_checkpoint=MODEL_PATH)
else:
    trainer.train()


# Upload model to GCS
def upload_directory_to_gcs(local_path, bucket_name, gcs_path):
    """Upload to GCS"""
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    for root, _, files in os.walk(local_path):
        for file in files:
            local_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_file_path, local_path)
            gcs_blob_path = os.path.join(gcs_path, relative_path)

            blob = bucket.blob(gcs_blob_path)
            blob.upload_from_filename(local_file_path)
            print(
                f"Uploaded {local_file_path} to " f"gs://{bucket_name}/{gcs_blob_path}"
            )


def save_merged_model(m, t, save_dir):
    """Save model and tokenizer locally"""
    os.makedirs(save_dir, exist_ok=True)
    m.save_pretrained_merged(save_dir, t, save_method=SAVE_METHOD)
    print(f"Merged model saved to {save_dir}")


# Save merged model
save_merged_model(trainer.model, tokenizer, MERGED_MODEL_DIR)
