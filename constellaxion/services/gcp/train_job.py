import json

from google.cloud import aiplatform, storage
import pkg_resources

from constellaxion.models.model_map import model_map


def create_vertex_dataset(
    model_id: str,
    bucket_name: str,
    train_set: str,
    val_set: str,
    test_set: str,
    location: str,
) -> None:
    """
    Checks if a default metadata store exists in the project at the specified location.
    Creates one if it doesn't exist.

    Args:
        project_id (str): GCP project ID
        location (str): GCP region (e.g., 'us-central1')
    """
    try:
        # Create GCS paths
        gcs_paths = [
            f"gs://{bucket_name}/{train_set}",
            f"gs://{bucket_name}/{val_set}",
            f"gs://{bucket_name}/{test_set}",
        ]

        # Create dataset without using paths as label values
        aiplatform.TabularDataset.create(
            display_name=f"{model_id}-dataset",
            location=location,
            gcs_source=gcs_paths,
            labels={"model_id": model_id},
        )

    except Exception as e:
        print(f"Warning: Error while checking/creating metadata store: {str(e)}")
        print("Continuing with training...")


def upload_data_to_gcp(config: dict):
    """
    Upload dataset to GCP, ensuring the bucket exists.

    Args:
        config (dict): Configuration dictionary with bucket and dataset details.
    """
    client = storage.Client()
    bucket_name = config["deploy"]["bucket_name"]

    # Check if bucket exists
    bucket = client.bucket(bucket_name)
    if not bucket.exists():
        print(f"Bucket '{bucket_name}' does not exist. Creating it...")
        bucket = client.create_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' created successfully.")

    # Upload training dataset
    train_blob = bucket.blob(config["dataset"]["train"]["cloud"])
    train_blob.upload_from_filename(config["dataset"]["train"]["local"])
    print(f"Uploaded training dataset to {train_blob.name}")

    # Upload validation dataset
    val_blob = bucket.blob(config["dataset"]["val"]["cloud"])
    val_blob.upload_from_filename(config["dataset"]["val"]["local"])
    print(f"Uploaded validation dataset to {val_blob.name}")

    # Upload test dataset
    test_blob = bucket.blob(config["dataset"]["test"]["cloud"])
    test_blob.upload_from_filename(config["dataset"]["test"]["local"])
    print(f"Uploaded test dataset to {test_blob.name}")


def create_training_job(
    project: str,
    location: str,
    staging_bucket: str,
    display_name: str,
    script_path: str,
    container_uri: str,
    service_account: str,
    # requirements: str,
    machine_type: str,
    accelerator_type: str,
    accelerator_count: int,
    replica_count: int,
    experiment_name: str,
    args: list[str],
) -> None:
    """Creates and runs a Vertex AI custom training job with TensorBoard integration."""
    aiplatform.init(project=project, location=location, staging_bucket=staging_bucket)

    # Try to get existing experiment, create if it doesn't exist
    try:
        experiment = aiplatform.Experiment(experiment_name)
    except Exception:
        experiment = aiplatform.Experiment.create(experiment_name)

    # Get TensorBoard instance
    tensorboard = experiment.get_backing_tensorboard_resource()
    if tensorboard is None:
        # Create a new TensorBoard instance if one doesn't exist
        tensorboard = aiplatform.Tensorboard.create(
            display_name=f"{experiment_name}-tensorboard",
            project=project,
            location=location,
        )
        # Associate the tensorboard with the experiment
        experiment.assign_backing_tensorboard(tensorboard)

    tensorboard_resource_name = tensorboard.gca_resource.name
    print(f"Original Tensorboard resource name: {tensorboard_resource_name}")
    # Extract experiment ID from the resource name
    experiment_id = experiment.resource_name.split("/")[-1]

    # Parse the tensorboard resource name to get project ID and tensorboard ID
    parts = tensorboard_resource_name.split("/")
    project_number = parts[1]  # Gets the numeric project ID
    tensorboard_id = parts[-1]

    # Generate Tensorboard URL in the correct format
    tensorboard_url = (
        f"https://{location}.tensorboard.googleusercontent.com/experiment/"
        f"projects+{project_number}+locations+{location}+tensorboards+{tensorboard_id}"
        f"+experiments+{experiment_id}/#scalars"
    )
    print(f"Tensorboard URL: {tensorboard_url}")

    # Read existing job.json
    try:
        with open("job.json", "r", encoding="utf-8") as f:
            job_config = json.load(f)
    except FileNotFoundError:
        job_config = {}

    # Ensure 'training' key exists
    if "training" not in job_config:
        job_config["training"] = {}

    # Add tensorboard URL to training section
    job_config["training"]["tensorboard_url"] = tensorboard_url

    # Write updated config back to job.json
    with open("job.json", "w", encoding="utf-8") as f:
        json.dump(job_config, f, indent=4)

    job = aiplatform.CustomJob.from_local_script(
        display_name=display_name,
        script_path=script_path,
        container_uri=container_uri,
        # requirements=requirements,
        machine_type=machine_type,
        accelerator_type=accelerator_type,
        accelerator_count=accelerator_count,
        replica_count=replica_count,
        args=args,
    )
    print(f"Tensorboard resource name: {tensorboard_resource_name}")
    job.run(service_account=service_account, tensorboard=tensorboard_resource_name)


def run_training_job(config):
    """
    Run a training job for a given model.

    Args:
        config (dict): Configuration dictionary with model and dataset details.
    """
    base_model_alias = config["model"]["base_model"]
    bucket_name = config["deploy"]["bucket_name"]
    model_id = config["model"]["model_id"]
    train_set = config["dataset"]["train"]["cloud"]
    val_set = config["dataset"]["val"]["cloud"]
    test_set = config["dataset"]["test"]["cloud"]
    script_path = pkg_resources.resource_filename(
        "constellaxion.models.scripts.gcp", "lora.py"
    )
    infra_config = model_map[base_model_alias]["gcp_infra"]
    dtype = model_map[base_model_alias]["dtype"]
    max_seq_length = model_map[base_model_alias]["max_seq_length"]
    base_model = model_map[base_model_alias]["base_model"]
    # Upload data to GCP
    upload_data_to_gcp(config)
    project_id = config["deploy"]["project_id"]
    location = config["deploy"]["region"]
    experiment_name = (
        f"{config['model']['model_id']}-lora-{config['training']['epochs']}e"
    )
    # Add this before initializing the experiment
    create_vertex_dataset(
        experiment_name, bucket_name, train_set, val_set, test_set, location
    )
    create_training_job(
        project=project_id,
        location=location,
        staging_bucket=f"gs://{bucket_name}/{config['deploy']['staging_dir']}",
        display_name=config["model"]["model_id"],
        script_path=script_path,
        # requirements=finetune_packages,
        container_uri=infra_config["images"]["finetune"],
        service_account=config["deploy"]["service_account"],
        machine_type=infra_config["machine_type"],
        accelerator_type=infra_config["accelerator_type"],
        accelerator_count=infra_config["accelerator_count"],
        replica_count=infra_config["replica_count"],
        experiment_name=experiment_name,
        args=[
            f"--epochs={config['training']['epochs']}",
            f"--batch-size={config['training']['batch_size']}",
            f"--train-set={config['dataset']['train']['cloud']}",
            f"--val-set={config['dataset']['val']['cloud']}",
            f"--test-set={config['dataset']['test']['cloud']}",
            f"--dtype={dtype}",
            f"--max-seq-length={max_seq_length}",
            f"--base-model={base_model}",
            f"--bucket-name={bucket_name}",
            f"--model-path={config['deploy']['model_path']}",
            f"--experiments-dir={config['deploy']['experiments_dir']}",
            f"--location={location}",
            f"--project-id={project_id}",
            f"--model-id={model_id}",
            f"--experiment-name={experiment_name}",
        ],
    )
