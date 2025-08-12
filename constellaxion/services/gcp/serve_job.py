import subprocess
import sys
import tempfile
import yaml
import json
from constellaxion.utils import get_model_map
from constellaxion.services.gcp.cloud_run import accelerator_type_map, ensure_region

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
    Deploy a GPU-enabled Cloud Run service with specifications
    
    Returns:
        str: The service URL of the deployed Cloud Run service
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

    # Extract the service URL
    print(f"Extracting service URL for '{service_name}'...")
    try:
        result = subprocess.run([
            "gcloud", "run", "services", "describe", service_name,
            "--region", region,
            "--project", project_id,
            "--format", "json"
        ], capture_output=True, text=True, check=True)
        
        service_info = json.loads(result.stdout)
        service_url = service_info.get("status", {}).get("url")
        
        if service_url:
            return service_url
        else:
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to extract service URL: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse service info: {e}")
        return None


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

    region = ensure_region(region)
    
    # Environment variables
    env_vars = {
        "GCS_BUCKET_NAME": bucket_name,
        "DTYPE": dtype,
        "MODEL_NAME": model_id,
    }
    service_url = deploy_cloud_run_service_gpu(
        service_name=model_id,
        image_uri=image_uri,
        region=region,
        project_id=project_id,
        env_vars=env_vars,
        gpu_type=accelerator_type_map().get(accelerator_type),
        gpu_count=str(accelerator_count),
        gpu_memory=gpu_memory,
        cpu_cores=str(cpu_cores),
        service_account=service_account,
    )
    
    if service_url:
        print(f"\n🎉 Deployment successful! Your service is available at: {service_url}")
        return service_url
    else:
        print("\n⚠️  Deployment completed but could not retrieve service URL please check the logs above or your Cloud Run console")
        return None
