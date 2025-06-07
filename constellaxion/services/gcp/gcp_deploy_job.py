from google.cloud import aiplatform

from constellaxion.utils import get_model_map


def create_model_from_custom_container(model_name: str, image_uri: str, env_vars: dict):
    """Creates a Vertex AI model from a custom container image."""
    print("Creating model from custom container...")

    # Define the container and model
    model = aiplatform.Model.upload(
        display_name=model_name,
        serving_container_image_uri=image_uri,
        serving_container_ports=[8080],  # Port your container exposes
        # Optional, adjust if your container provides health checks
        serving_container_health_route="/health",
        # Optional, adjust if your container provides a prediction endpoint
        serving_container_predict_route="/predict",
        serving_container_environment_variables=env_vars,
    )
    print(f"Model created successfully: {model.resource_name}")
    return model


# Deploy the model to an endpoint


def deploy_model_to_endpoint(
    model,
    model_id: str,
    machine_type: str,
    accelerator_type: str,
    accelerator_count: int,
    replica_count: int,
    service_account: str,
):
    """Deploys a model to a Vertex AI endpoint with specified compute resources."""
    # Check if the endpoint exists, create it if not
    endpoints = aiplatform.Endpoint.list(filter=f'display_name="{model_id}"')
    if endpoints:
        endpoint = endpoints[0]  # Use the first matching endpoint
        print(f"Using existing endpoint: {endpoint.display_name}")
    else:
        # Create a new endpoint
        endpoint = aiplatform.Endpoint.create(display_name=model_id)
        print(f"Created new endpoint: {endpoint.display_name}")

    # Deploy the model to the endpoint
    model.deploy(
        endpoint=endpoint,
        deployed_model_display_name=model_id,
        traffic_split={"0": 100},  # Route all traffic to this model
        accelerator_type=accelerator_type,
        accelerator_count=accelerator_count,
        machine_type=machine_type,
        min_replica_count=replica_count,
        max_replica_count=replica_count,
        service_account=service_account,
    )

    print(f"Model deployed to endpoint: {endpoint.resource_name}")
    return endpoint.resource_name


def run_gcp_deploy_job(config):
    """Runs the GCP deployment job by creating and deploying a model to Vertex AI."""
    deploy_config = config.get("deploy", {})
    if not deploy_config:
        raise KeyError("Invalid config, missing deploy section")
    model_config = config.get("model", {})
    if not model_config:
        raise KeyError("Invalid config, missing model section")
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
    image_uri = infra_config.get("images", {}).get("serve", None)
    machine_type = infra_config.get("machine_type", None)
    accelerator_type = infra_config.get("accelerator_type", None)
    accelerator_count = infra_config.get("accelerator_count", None)
    replica_count = infra_config.get("replica_count", None)
    dtype = infra_config.get("dtype", None)
    env_vars = {"MODEL_NAME": base_model, "DTYPE": dtype}
    if hf_token:
        env_vars["HF_TOKEN"] = hf_token
    # Initialize the Vertex AI SDK
    aiplatform.init(project=project_id, location=region)
    # # Download the model
    model = create_model_from_custom_container(base_model, image_uri, env_vars)
    # Deploy model to endpoint
    endpoint_path = deploy_model_to_endpoint(
        model,
        model_id,
        machine_type,
        accelerator_type,
        accelerator_count,
        replica_count,
        service_account,
    )
    return endpoint_path
