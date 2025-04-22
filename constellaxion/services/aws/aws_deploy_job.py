import boto3
import uuid
from constellaxion.models.model_map import model_map
from constellaxion.services.aws.utils import get_aws_account_id


def create_model_from_custom_container(model_id: str, image_uri: str, env_vars: dict, execution_role: str):
    sm = boto3.client("sagemaker")
    model_name_unique = f"{model_id}-{uuid.uuid4().hex[:8]}"
    sm.create_model(
        ModelName=model_name_unique,
        PrimaryContainer={
            "Image": image_uri,
            "Environment": env_vars
        },
        ExecutionRoleArn=execution_role,
    )
    print(f"Model created: {model_name_unique}")
    return model_name_unique


def get_or_create_endpoint_config(endpoint_config_name: str, model_id: str, instance_type: str,
                                  accelerator_type: str, accelerator_count: int):
    sm = boto3.client("sagemaker")
    try:
        sm.describe_endpoint_config(EndpointConfigName=endpoint_config_name)
        print(f"Using existing endpoint config: {endpoint_config_name}")
    except sm.exceptions.ClientError:
        print("Creating new endpoint config...")
        production_variant = {
            "VariantName": "AllTraffic",
            "ModelName": model_id,
            "InitialInstanceCount": 1,
            "InstanceType": instance_type,
            "InitialVariantWeight": 1.0
        }
        if accelerator_type:
            production_variant["AcceleratorType"] = accelerator_type

        sm.create_endpoint_config(
            EndpointConfigName=endpoint_config_name,
            ProductionVariants=[production_variant]
        )
        print(f"Created endpoint config: {endpoint_config_name}")


def deploy_model_to_endpoint(model_name: str, model_id: str, instance_type: str,
                             accelerator_type: str, accelerator_count: int):
    sm = boto3.client("sagemaker")
    endpoint_config_name = f"{model_id}-config"
    get_or_create_endpoint_config(endpoint_config_name, model_id, instance_type, accelerator_type, accelerator_count)

    try:
        sm.describe_endpoint(EndpointName=model_id)
        print(f"Updating existing endpoint: {model_id}")
        sm.update_endpoint(
            EndpointName=model_id,
            EndpointConfigName=endpoint_config_name
        )
    except sm.exceptions.ClientError:
        print("Creating new endpoint...")
        sm.create_endpoint(
            EndpointName=model_id,
            EndpointConfigName=endpoint_config_name
        )
    print(f"Model deployed to endpoint: {model_id}")
    return model_id


def configure_autoscaling(endpoint_name: str, min_capacity: int, max_capacity: int):
    client = boto3.client("application-autoscaling")

    resource_id = f"endpoint/{endpoint_name}/variant/AllTraffic"
    client.register_scalable_target(
        ServiceNamespace="sagemaker",
        ResourceId=resource_id,
        ScalableDimension="sagemaker:variant:DesiredInstanceCount",
        MinCapacity=min_capacity,
        MaxCapacity=max_capacity,
    )

    client.put_scaling_policy(
        PolicyName="ConstellaxionScalingPolicy",
        ServiceNamespace="sagemaker",
        ResourceId=resource_id,
        ScalableDimension="sagemaker:variant:DesiredInstanceCount",
        PolicyType="TargetTrackingScaling",
        TargetTrackingScalingPolicyConfiguration={
            "TargetValue": 70.0,
            "PredefinedMetricSpecification": {
                "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance"
            },
            "ScaleInCooldown": 300,
            "ScaleOutCooldown": 60
        }
    )
    print(f"Autoscaling configured: min={min_capacity}, max={max_capacity}")


def run_aws_deploy_job(config):
    base_model = config['model']['base_model']
    model_id = config['model']['model_id']
    region = config['deploy']['region']
    iam_role = config['deploy']['iam_role']
    account_id = get_aws_account_id()
    role_arn = f"arn:aws:iam::{account_id}:role/{iam_role}"
    infra_config = model_map[base_model]["aws_infra"]
    image_uri = model_map[base_model]["images"]["serve"]
    instance_type = infra_config['instance_type']
    accelerator_type = infra_config.get('accelerator_type')
    accelerator_count = infra_config.get('accelerator_count', 1)
    dtype = "float16" if not infra_config.get('dtype') else infra_config.get('dtype')
    autoscale = config['deploy'].get('autoscale', False)
    min_capacity = infra_config.get('min_replica_count', 1)
    max_capacity = infra_config.get('max_replica_count', 2)

    env_vars = {
        "MODEL_NAME": base_model,
        "DTYPE": dtype
    }

    boto3.setup_default_session(region_name=region)

    # Register the model
    model_name = create_model_from_custom_container(model_id, image_uri, env_vars, role_arn)

    # Deploy to endpoint
    endpoint_name = deploy_model_to_endpoint(model_name, model_id, instance_type,
                                             accelerator_type, accelerator_count)

    # Optional autoscaling
    if autoscale:
        configure_autoscaling(endpoint_name, min_capacity=min_capacity, max_capacity=max_capacity)

    return endpoint_name