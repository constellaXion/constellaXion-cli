"""LoRA fine-tuning script with Unsloth optimizations for GCP deployment."""

import argparse
import inspect
import os

# Must be first non-standard import!
from unsloth import FastLanguageModel, is_bfloat16_supported

from constellaxion_utils.gcs.gcs_uploader import ModelManager
from datasets import Dataset
from google.cloud import aiplatform, storage
import pandas as pd
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
args = parser.parse_args()

SEED = 42

LOCAL_MODEL_DIR = "./models"
CHECKPOINT_DIR = "./checkpoints"
MODEL_NAME = args.base_model
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


def gcs_uri_to_fuse_path(gcs_uri: str) -> str:
    """
    Convert a gs:// URI to its FUSE-mounted /gcs/ path.

    Args:
        gcs_uri (str): A GCS path in the form gs://bucket-name/path/to/file

    Returns:
        str: The corresponding /gcs/bucket-name/path/to/file path

    Raises:
        ValueError: If the input is not a valid gs:// URI
    """
    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI: {gcs_uri}. Must start with 'gs://'")

    # Remove 'gs://' and split into bucket and path
    parts = gcs_uri[5:].split("/", 1)
    bucket = parts[0]
    path = parts[1] if len(parts) > 1 else ""

    return f"/gcs/{bucket}/{path}" if path else f"/gcs/{bucket}"


tensorboard_path = gcs_uri_to_fuse_path(tensorboard_path)

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
checkpoint = model_manager.prepare_checkpoint(
    GCS_BUCKET_NAME, EXPERIMENT_DIR, CHECKPOINT_DIR
)

if checkpoint:
    MODEL_PATH = checkpoint
else:
    MODEL_PATH = MODEL_NAME


# Initialize Unsloth FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_PATH,
    max_seq_length=int(MAX_SEQ_LENGTH),
    dtype=None if not DTYPE or DTYPE == "None" else DTYPE,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=32,  # Choose any number > 0 ! Suggested 8, 16, 32, 64, 128
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    lora_alpha=32,
    lora_dropout=0,  # Currently only supports dropout = 0
    bias="none",  # Currently only supports bias = "none"
    use_gradient_checkpointing=False,  # @@@ IF YOU GET OUT OF MEMORY - set to True @@@
    random_state=3407,
    use_rslora=False,  # We support rank stabilized LoRA
    loftq_config=None,  # And LoftQ
)

# Prepare model with LoRA
# model = get_peft_model(model, lora_config)

# if checkpoint:
#     model.load_state_dict(PeftModel.from_pretrained(model, MODEL_PATH).state_dict())

model.print_trainable_parameters()


EOS_TOKEN = tokenizer.eos_token


def format_prompts(example):
    """Formatter for training and validation examples"""
    output_texts = []
    for i in range(len(example["prompt"])):
        text = (
            inspect.cleandoc(
                f"""
## Prompt:
{example["prompt"][i]}
## Response:
{example["response"][i]}
"""
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

# Train Model
train_args = TrainingArguments(
    per_device_train_batch_size=int(BATCH_SIZE),
    gradient_accumulation_steps=4,
    warmup_ratio=0.1,
    num_train_epochs=int(EPOCHS),
    learning_rate=2e-5,
    eval_strategy="steps",
    fp16=not is_bfloat16_supported(),
    bf16=is_bfloat16_supported(),
    logging_steps=100,
    save_strategy="steps",
    save_steps=0.2,
    optim="adamw_8bit",
    weight_decay=0.1,
    lr_scheduler_type="linear",
    seed=3407,
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


def save_model_tokenizer_locally(m, t, save_dir):
    """Save model and tokenizer locally"""
    os.makedirs(save_dir, exist_ok=True)
    m.save_pretrained(save_dir)
    t.save_pretrained(save_dir)
    print(f"Model and tokenizer saved locally to {save_dir}")


def save_and_upload_model(m, t):
    """Save and upload model"""
    # Save locally
    save_model_tokenizer_locally(m, t, LOCAL_MODEL_DIR)

    # Upload to GCS
    upload_directory_to_gcs(LOCAL_MODEL_DIR, GCS_BUCKET_NAME, GCS_MODEL_PATH)


save_and_upload_model(trainer.model, tokenizer)
