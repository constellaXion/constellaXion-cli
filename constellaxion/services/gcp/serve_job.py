import subprocess
import sys
import tempfile
import yaml
from constellaxion.utils import get_model_map

accelerator_type_map = {
    "NVIDIA_L4": "nvidia-l4",
    "NVIDIA_L4_8": "nvidia-l4",
    "NVIDIA_L4_16": "nvidia-l4",
    "NVIDIA_L4_32": "nvidia-l4",
    "NVIDIA_L4_64": "nvidia-l4",
}

def deploy_cloud_run_service_gpu(
    service_name: str,
    image_uri: str,
    region: str,
    project_id: str,
    env_vars: dict,
    gpu_type: str,
    gpu_memory: str,
    cpu_cores: str,
    gpu_count: str = "1",
    allow_unauthenticated: bool = True,
    service_account: str = None,
):
    """
    Deploy a GPU-enabled Cloud Run service with specified GPU type, memory, CPU cores and count.
    Uses gcloud run deploy to configure machine type and GPU settings. Environment variables are
    passed via a temporary YAML file.
    """

    # Convert environment variables into YAML format for env vars file
    env_vars_yaml = {k: str(v) for k, v in env_vars.items()}

    # Write env vars YAML to a temp file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp:
        yaml.dump(env_vars_yaml, tmp)
        env_vars_yaml_path = tmp.name

    # Deploy the service using gcloud beta
    cmd = [
        "gcloud", "run", "deploy", service_name,
        "--image", image_uri,
        "--platform", "managed",
        "--allow-unauthenticated",
        "--region", region,
        "--project", project_id,
        "--cpu", cpu_cores,
        "--memory", gpu_memory,
        "--timeout", "300s",
        "--execution-environment", "gen2",
        "--gpu", gpu_count,
        "--gpu-type", gpu_type,
        "--min-instances", "1",
        "--max-instances", "1",
        "--env-vars-file", env_vars_yaml_path,
        "--no-gpu-zonal-redundancy",
        "--service-account", service_account,
    ]

    print(f"Deploying GPU-backed Cloud Run service '{service_name}' with 32GB /tmp disk...")
    try:
        subprocess.run(cmd, check=True)
        print(f"Service '{service_name}' deployed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Deployment failed: {e}")
        sys.exit(1)

    # Grant public (unauthenticated) access if required
    if allow_unauthenticated:
        print(f"Granting unauthenticated (public) access to '{service_name}'...")
        try:
            subprocess.run([
                "gcloud", "beta", "run", "services", "add-iam-policy-binding", service_name,
                "--region", region,
                "--member", "allUsers",
                "--role", "roles/run.invoker",
                "--project", project_id
            ], check=True)
            print(f"Public access granted to '{service_name}'.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to grant public access: {e}")


def run_serving_job(config):
    deploy_config = config.get("deploy", {})
    if not deploy_config:
        raise KeyError("Invalid config, missing deploy section")
    model_config = config.get("model", {})
    if not model_config:
        raise KeyError("Invalid config, missing model section")
    base_model_alias = model_config.get("base_model")
    model_map = get_model_map(base_model_alias)
    infra_config = model_map.get("gcp_infra", {})
    model_id = model_config.get("model_id")
    image_uri = infra_config.get("images").get("finetuned")
    accelerator_type = infra_config.get("accelerator_type")
    accelerator_count = infra_config.get("accelerator_count")
    cpu_cores = infra_config.get("cpu_cores", 8)
    gpu_memory = infra_config.get("gpu_memory", "32Gi")
    dtype = infra_config.get("dtype")
    service_account = deploy_config.get("service_account")
    region = deploy_config.get("region")  
    project_id = deploy_config.get("project_id")
    bucket_name = deploy_config.get("bucket_name")
    # Environment variables
    env_vars = {
        "GCS_BUCKET_NAME": bucket_name,
        "DTYPE": dtype,
        "MODEL_NAME": model_id,
    }
    deploy_cloud_run_service_gpu(
        service_name=model_id,
        image_uri=image_uri,
        region="europe-west4",
        project_id=project_id,
        env_vars=env_vars,
        gpu_type=accelerator_type_map.get(accelerator_type),
        gpu_count=str(accelerator_count),
        gpu_memory=gpu_memory,
        cpu_cores=str(cpu_cores),
        service_account=service_account,
    )