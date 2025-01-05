import os
import argparse
import pandas as pd
from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
from transformers import TrainingArguments, AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, TaskType, get_peft_model
from datasets import Dataset
from torch.utils.data import DataLoader
from google.cloud import storage

# Parse cli args
parser = argparse.ArgumentParser()
parser.add_argument("--train-set", type=str, required=True,
                    help="Training set path")
parser.add_argument("--val-set", type=str, required=True,
                    help="Validation set path")
parser.add_argument("--test-set", type=str, required=True,
                    help="Test set path")
parser.add_argument("--bucket-name", type=str, required=True,
                    help="GCS bucket name")
parser.add_argument("--model-path", type=str, required=True,
                    help="Model artefacts output path")
parser.add_argument("--experiments-dir", type=str, required=True,
                    help="Experiments output path")
parser.add_argument("--staging-dir", type=str, required=True,
                    help="Staging path")

args = parser.parse_args()

SEED = 42

MODEL_NAME = 'TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T'
PAD_TOKEN = '<pad>'

LOCAL_MODEL_DIR = './model'
GCS_BUCKET_NAME = args.bucket_name
GCS_MODEL_PATH = args.model_path
TRAIN_CSV = f"gs://{GCS_BUCKET_NAME}/{args.train_set}"
VAL_CSV = f"gs://{GCS_BUCKET_NAME}/{args.val_set}"
TEST_CSV = f"gs://{GCS_BUCKET_NAME}/{args.test_set}"
OUTPUT_DIR = args.experiments_dir

# Dataset
train_df = pd.read_csv(TRAIN_CSV)
val_df = pd.read_csv(VAL_CSV)
test_df = pd.read_csv(TEST_CSV)

dataset = {
    "train": Dataset.from_pandas(train_df),
    "val": Dataset.from_pandas(val_df),
    "test": Dataset.from_pandas(test_df)
}

# Tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME, add_eos_token=True, use_fast=True)
tokenizer.add_special_tokens({"pad_token": PAD_TOKEN})
tokenizer.padding_side = "right"

# Model
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME, device_map="auto", trust_remote_code=True)
model.resize_token_embeddings(len(tokenizer), pad_to_multiple_of=8)

model.pad_token_id = tokenizer.pad_token_id
model.config.pad_token_id = tokenizer.pad_token_id
print(model.config)
print(model)

# LoRA
lora_config = LoraConfig(
    r=128, lora_alpha=128,
    target_modules=[
        "self_attn.q_proj",
        "self_attn.k_proj",
        "self_attn.v_proj",
        "self_attn.o_proj"
    ],
    lora_dropout=0.1,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Prepare data loader
response_template = "\n### Prediction:"
response_template_ids = tokenizer.encode(
    response_template, add_special_tokens=False)

collator = DataCollatorForCompletionOnlyLM(
    response_template_ids, tokenizer=tokenizer)

examples = dataset["train"][0]
encodings = [tokenizer(e) for e in examples]

dataloader = DataLoader(encodings, collate_fn=collator, batch_size=1)
batch = next(iter(dataloader))
print(batch.keys())

# Train Model
train_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=1,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    optim="adamw_torch",
    evaluation_strategy="steps",
    eval_steps=0.2,
    logging_steps=10,
    learning_rate=1e-4,
    fp16=True,
    save_strategy="epoch",
    max_grad_norm=1.0,
    warmup_ratio=0.1,
    lr_scheduler_type="constant",
    save_safetensors=True,
    seed=SEED
)

trainer = SFTTrainer(
    model=model,
    args=train_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["val"],
    tokenizer=tokenizer,
    max_seq_length=1024,
    data_collator=collator
)

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
            print(
                f"Uploaded {local_file_path} to gs://{bucket_name}/{gcs_blob_path}")


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
