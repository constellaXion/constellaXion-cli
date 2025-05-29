from google.cloud import aiplatform

from constellaxion.models.model_map import model_map


def create_model_from_custom_container(model_name: str, image_uri: str, env_vars: dict):
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


def run_serving_job(config):
    project_id = config["deploy"]["project_id"]
    model_id = config["model"]["model_id"]
    location = config["deploy"]["location"]
    base_model_id = config["model"]["base_model"]
    bucket_name = config["deploy"]["bucket_name"]
    model_path = config["deploy"]["model_path"]
    service_account = config["deploy"]["service_account"]
    base_model = model_map[base_model_id]["namespace"]
    infra_config = model_map[base_model_id]["infra"]
    image_uri = infra_config["serve_image_uri"]
    machine_type = infra_config["machine_type"]
    accelerator_type = infra_config["accelerator_type"]
    accelerator_count = infra_config["accelerator_count"]
    replica_count = infra_config["replica_count"]
    env_vars = {
        "GCS_BUCKET_NAME": bucket_name,
        "MODEL_PATH": model_path,
        "BASE_MODEL": base_model,
    }
    # Initialize the Vertex AI SDK
    aiplatform.init(project=project_id, location=location)
    # Register a model
    model = create_model_from_custom_container(model_id, image_uri, env_vars)
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
