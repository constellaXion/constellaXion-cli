from google.cloud import run_v2
from google.cloud.run_v2 import Service
from google.cloud.run_v2.types import Container, EnvVar, ResourceRequirements

from constellaxion.utils import get_model_map


def create_cloud_run_service(
    project_id: str,
    region: str,
    service_name: str,
    image_uri: str,
    env_vars: dict,
    service_account: str,
    memory: str = "4Gi",
    cpu: str = "2",
    gpu_type: str = "nvidia-tesla-t4",
    gpu_count: int = 1,
    min_instances: int = 1,
    max_instances: int = 10,
):
    """Creates or updates a Cloud Run service for model serving with GPU support."""
    print("Creating/updating Cloud Run service with GPU support...")

    # Initialize the Cloud Run client
    client = run_v2.ServicesClient()

    # Convert env_vars dict to list of EnvVar objects
    env_vars_list = [EnvVar(name=key, value=value) for key, value in env_vars.items()]

    # Create the container configuration
    container = Container(
        image=image_uri,
        env=env_vars_list,
        ports=[{"container_port": 8080}],  # Default port for model serving
        resources=ResourceRequirements(
            limits={
                "memory": memory,
                "cpu": cpu,
                "nvidia.com/gpu": str(gpu_count),  # Specify GPU count
            }
        ),
    )

    # Create the service configuration
    service = Service(
        name=f"projects/{project_id}/locations/{region}/services/{service_name}",
        template=run_v2.RevisionTemplate(
            containers=[container],
            service_account=service_account,
            scaling=run_v2.RevisionScaling(
                min_instance_count=min_instances,
                max_instance_count=max_instances,
            ),
            execution_environment="EXECUTION_ENVIRONMENT_GEN2",
            # Add GPU configuration
            annotations={
                "run.googleapis.com/gpu-type": gpu_type,
                "run.googleapis.com/gpu-count": str(gpu_count),
            },
        ),
    )

    # Create or update the service
    operation = client.update_service(service=service)
    result = operation.result()

    print(f"Cloud Run service created/updated successfully: {result.name}")
    return result.name


def run_gcp_cloud_run_deploy(config):
    """Runs the GCP Cloud Run deployment job for model serving with GPU support."""
    deploy_config = config.get("deploy", {})
    if not deploy_config:
        raise KeyError("Invalid config, missing deploy section")
    model_config = config.get("model", {})
    if not model_config:
        raise KeyError("Invalid config, missing model section")

    # Extract configuration values
    project_id = deploy_config.get("project_id", None)
    region = deploy_config.get("region", None)
    base_model_alias = model_config.get("base_model", None)
    model_id = model_config.get("model_id", None)
    hf_token = model_config.get("hf_token", None)
    service_account = deploy_config.get("service_account", None)

    # Get the model infra config from the constellaxion database
    model_map = get_model_map(base_model_alias)
    base_model = model_map.get("base_model", None)
    infra_config = model_map.get("gcp_infra", {})
    hf_token_required = model_map.get("hf_token_required", False)

    if hf_token_required and not hf_token:
        raise ValueError(
            "This is a protected model, please provide a valid HF token in model.yaml file and rerun `constellaxion init`"
        )

    # Get infrastructure configuration
    image_uri = infra_config.get("images", {}).get("serve", None)
    memory = infra_config.get(
        "memory", "16Gi"
    )  # Increased default memory for GPU workloads
    cpu = infra_config.get("cpu", "4")  # Increased default CPU for GPU workloads
    gpu_type = infra_config.get("gpu_type", "nvidia-tesla-t4")
    gpu_count = infra_config.get("gpu_count", 1)
    min_instances = infra_config.get("min_instances", 1)
    max_instances = infra_config.get("max_instances", 10)
    dtype = infra_config.get("dtype", None)

    # Prepare environment variables
    env_vars = {
        "MODEL_NAME": base_model,
        "DTYPE": dtype,
        "CUDA_VISIBLE_DEVICES": "0",  # Enable GPU visibility
    }
    if hf_token:
        env_vars["HF_TOKEN"] = hf_token

    # Deploy to Cloud Run
    service_path = create_cloud_run_service(
        project_id=project_id,
        region=region,
        service_name=model_id,
        image_uri=image_uri,
        env_vars=env_vars,
        service_account=service_account,
        memory=memory,
        cpu=cpu,
        gpu_type=gpu_type,
        gpu_count=gpu_count,
        min_instances=min_instances,
        max_instances=max_instances,
    )

    return service_path
