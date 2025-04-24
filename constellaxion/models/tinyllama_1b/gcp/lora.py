import argparse
import inspect
import os
import threading
import time

import pandas as pd
from constellaxion_utils.gcs.gcs_uploader import (GCSUploaderHandler,
                                                  ModelManager)
from datasets import Dataset
from google.cloud import aiplatform, storage
from peft import LoraConfig, TaskType, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.integrations import TensorBoardCallback
from trl import DataCollatorForCompletionOnlyLM, SFTConfig, SFTTrainer
from watchdog.observers import Observer

# Parse cli args
parser = argparse.ArgumentParser()
parser.add_argument("--epochs", type=str, required=True, help="Training epochs")
parser.add_argument("--batch-size", type=str, required=True, help="Batch size")
parser.add_argument("--train-set", type=str, required=True, help="Training set path")
parser.add_argument("--val-set", type=str, required=True, help="Validation set path")
parser.add_argument("--test-set", type=str, required=True, help="Test set path")
parser.add_argument("--bucket-name", type=str, required=True, help="GCS bucket name")
parser.add_argument(
    "--model-path", type=str, required=True, help="Model artefacts output path"
)
parser.add_argument("--model-id", type=str, required=True, help="Model ID")
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

MODEL_NAME = "TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T"
PAD_TOKEN = "<pad>"

LOCAL_MODEL_DIR = "./model"
CHECKPOINT_DIR = "./checkpoints"
GCS_BUCKET_NAME = args.bucket_name
GCS_MODEL_PATH = args.model_path
LOCATION = args.location
PROJECT_ID = args.project_id
MODEL_ID = args.model_id
EPOCHS = args.epochs
BATCH_SIZE = args.batch_size
EXPERIMENT_NAME = args.experiment_name
EXPERIMENT_DIR = args.experiments_dir
tensorboard_path = os.environ.get("AIP_TENSORBOARD_LOG_DIR")

train_set = f"gs://{GCS_BUCKET_NAME}/{args.train_set}"
val_set = f"gs://{GCS_BUCKET_NAME}/{args.val_set}"
test_set = f"gs://{GCS_BUCKET_NAME}/{args.test_set}"
output_dir = f"gs://{GCS_BUCKET_NAME}/{EXPERIMENT_DIR}"


def start_gcs_sync(local_dir, gcs_dir):
    event_handler = GCSUploaderHandler(local_dir, gcs_dir)
    observer = Observer()
    observer.schedule(event_handler, path=local_dir, recursive=True)
    observer.start()
    print(f"🚀 Started syncing from {local_dir} to {gcs_dir}")

    # Run indefinitely until stopped
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# Dataset
train_df = pd.read_csv(train_set)
val_df = pd.read_csv(val_set)
test_df = pd.read_csv(test_set)

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

# Tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, add_eos_token=True, use_fast=True)
tokenizer.add_special_tokens({"pad_token": PAD_TOKEN})
tokenizer.padding_side = "right"

# Model
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME, device_map="auto", trust_remote_code=True
)
model.resize_token_embeddings(len(tokenizer), pad_to_multiple_of=8)

model.pad_token_id = tokenizer.pad_token_id
model.config.pad_token_id = tokenizer.pad_token_id
print(model.config)
print(model)

# LoRA
lora_config = LoraConfig(
    r=128,
    lora_alpha=128,
    target_modules=[
        "self_attn.q_proj",
        "self_attn.k_proj",
        "self_attn.v_proj",
        "self_attn.o_proj",
        "mlp.gate_proj",
        "mlp.up_proj",
        "mlp.down_proj",
    ],
    lora_dropout=0.1,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

model = get_peft_model(model, lora_config)

# if checkpoint:
#     model.load_state_dict(PeftModel.from_pretrained(model, MODEL_PATH).state_dict())
#     # model = model.merge_and_unload()

model.print_trainable_parameters()

# Prepare data loader
# response_template = "\n### Response:"
# todo: add instruction and response template
response_template = "\n### Prediction:"
response_template_ids = tokenizer.encode(response_template, add_special_tokens=False)[
    2:
]

collator = DataCollatorForCompletionOnlyLM(response_template_ids, tokenizer=tokenizer)


# def format_prompts(example):
#     text = inspect.cleandoc(
#             f"""
# ### Prompt:
# {example["prompt"]}
# ### Response:
# {example["response"]}
# """
#     )
#     return text


def format_prompts(example):
    text = inspect.cleandoc(
        f"""
### Title:
{example["title"]}
### Text:
{example["text"]}
### Prediction:
subject: {example["subject"]}
sentiment: {example["sentiment"]}
"""
    )
    return text


# Initialize Vertex AI with experiment tracking
aiplatform.init(
    project=PROJECT_ID,
    location=LOCATION,
    experiment=EXPERIMENT_NAME,
    experiment_description="TinyLlama LoRA fine-tuning experiment",
)

# Train Model
train_args = SFTConfig(
    output_dir="./experiments",
    num_train_epochs=int(EPOCHS),
    per_device_train_batch_size=int(BATCH_SIZE),
    gradient_accumulation_steps=4,
    optim="adamw_torch",
    evaluation_strategy="steps",
    logging_steps=50,
    learning_rate=1e-4,
    fp16=True,
    save_strategy="steps",
    save_steps=0.1,
    max_grad_norm=1.0,
    warmup_ratio=0.1,
    lr_scheduler_type="constant",
    save_safetensors=True,
    seed=SEED,
    max_seq_length=1024,
    report_to=["tensorboard"],
    logging_dir=tensorboard_path,
)

trainer = SFTTrainer(
    model=model,
    args=train_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["val"],
    tokenizer=tokenizer,
    formatting_func=format_prompts,
    data_collator=collator,
    callbacks=[TensorBoardCallback()],
)

# Start the GCS sync in a separate thread
os.makedirs("./experiments", exist_ok=True)
sync_thread = threading.Thread(
    target=start_gcs_sync, args=("./experiments", output_dir), daemon=True
)
sync_thread.start()

if checkpoint:
    trainer.train(resume_from_checkpoint=MODEL_PATH)
else:
    # Train model
    trainer.train()


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
            print(f"Uploaded {local_file_path} to gs://{bucket_name}/{gcs_blob_path}")


def save_model_tokenizer_locally(model, tokenizer, save_dir):
    """Save model and tokenizer locally"""
    os.makedirs(save_dir, exist_ok=True)
    model.save_pretrained(save_dir)
    tokenizer.save_pretrained(save_dir)
    print(f"Model and tokenizer saved locally to {save_dir}")


def save_and_upload_model(model, tokenizer):
    """Saven and upload model"""
    # Save locally
    save_model_tokenizer_locally(model, tokenizer, LOCAL_MODEL_DIR)

    # Upload to GCS
    upload_directory_to_gcs(LOCAL_MODEL_DIR, GCS_BUCKET_NAME, GCS_MODEL_PATH)


save_and_upload_model(trainer.model, tokenizer)
