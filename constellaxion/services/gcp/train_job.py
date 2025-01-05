import json
from google.cloud import aiplatform, storage
from constellaxion.services.gcp.model_map import model_map
from google.cloud import storage
import pkg_resources


def upload_data_to_gcp(config: dict):
    """
    Upload dataset to GCP, ensuring the bucket exists.

    Args:
        config (dict): Configuration dictionary with bucket and dataset details.
    """
    client = storage.Client()
    bucket_name = config['deploy']['bucket_name']

    # Check if bucket exists
    bucket = client.bucket(bucket_name)
    if not bucket.exists():
        print(f"Bucket '{bucket_name}' does not exist. Creating it...")
        bucket = client.create_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' created successfully.")

    # Upload training dataset
    train_blob = bucket.blob(config['dataset']['train']['cloud'])
    train_blob.upload_from_filename(config['dataset']['train']['local'])
    print(f"Uploaded training dataset to {train_blob.name}")

    # Upload validation dataset
    val_blob = bucket.blob(config['dataset']['val']['cloud'])
    val_blob.upload_from_filename(config['dataset']['val']['local'])
    print(f"Uploaded validation dataset to {val_blob.name}")

    # Upload test dataset
    test_blob = bucket.blob(config['dataset']['test']['cloud'])
    test_blob.upload_from_filename(config['dataset']['test']['local'])
    print(f"Uploaded test dataset to {test_blob.name}")


def create_custom_job_with_experiment_autologging_sample(
        project: str,
        location: str,
        staging_bucket: str,
        display_name: str,
        script_path: str,
        container_uri: str,
        service_account: str,
        requirements: str,
        machine_type: str,
        accelerator_type: str,
        accelerator_count: int,
        replica_count: int,
        args: list[str]
) -> None:
    aiplatform.init(project=project, location=location,
                    staging_bucket=staging_bucket)
    job = aiplatform.CustomJob.from_local_script(
        display_name=display_name,
        script_path=script_path,
        container_uri=container_uri,
        requirements=requirements,
        machine_type=machine_type,
        accelerator_type=accelerator_type,
        accelerator_count=accelerator_count,
        replica_count=replica_count,
        args=args
    )
    job.run(service_account=service_account)


def run_training_job(config):
    model_name = config['model']['base_model']
    bucket_name = config['deploy']['bucket_name']
    script_path = pkg_resources.resource_filename(
        "constellaxion.models.tinyllama_1b.gcp", "lora.py")
    print(script_path)
    # script_path = model_map[model_name]["lora"]
    infra_config = model_map[model_name]["infra"]
    upload_data_to_gcp(config)
    create_custom_job_with_experiment_autologging_sample(
        project=config['deploy']['project_id'],
        location=config['deploy']['location'],
        staging_bucket=f"gs://{bucket_name}/{config['deploy']['staging_dir']}",
        display_name=config['model']['model_id'],
        script_path=script_path,
        requirements=infra_config['requirements'],
        container_uri=infra_config['container_uri'],
        service_account=config['deploy']['service_account'],
        machine_type=infra_config['machine_type'],
        accelerator_type=infra_config['accelerator_type'],
        accelerator_count=infra_config['accelerator_count'],
        replica_count=infra_config['replica_count'],
        args=[
            f"--train-set={config['dataset']['train']}",
            f"--val-set={config['dataset']['val']}",
            f"--test-set={config['dataset']['test']}",
            f"--bucket-name={config['deploy']['bucket_name']}",
            f"--model-path={config['deploy']['model_path']}",
            f"--experiments-dir={config['deploy']['experiments_dir']}",
            f"--staging-dir={config['deploy']['staging_dir']}"
        ]
    )
