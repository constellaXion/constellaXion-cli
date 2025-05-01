"""AWS LMI deployment module for deploying models to SageMaker endpoints using Large Model Inference."""
import boto3
import sagemaker
from sagemaker.djl_inference.model import DJLModel
from constellaxion.models.model_map import model_map
from constellaxion.services.aws.utils import get_aws_account_id


def create_model_from_lmi_container(base_model: str, env_vars: dict, execution_role: str):
    """Creates a SageMaker model using the LMI container."""
    model = DJLModel(
        model_id=base_model,
        env=env_vars,
        role=execution_role
    )
    return model


def get_or_create_endpoint_config(endpoint_config_name: str, model_id: str, instance_type: str,
                                accelerator_type: str, accelerator_count: int):
    """Gets or creates a SageMaker endpoint configuration for LMI."""
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

        sm.create_endpoint_config(
            EndpointConfigName=endpoint_config_name,
            ProductionVariants=[production_variant]
        )
        print(f"Created endpoint config: {endpoint_config_name}")


def deploy_model_to_endpoint(model, model_id: str, instance_type: str):
    """Deploys a model to a SageMaker endpoint using LMI."""
    endpoint_name = sagemaker.utils.name_from_base(model_id)
    predictor = model.deploy(
        initial_instance_count=1,
        instance_type=instance_type,
        endpoint_name=endpoint_name,
    )
    return predictor


def configure_autoscaling(endpoint_name: str, min_capacity: int, max_capacity: int):
    """Configures autoscaling for the LMI endpoint."""
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
    """Runs the LMI deployment job by creating and deploying a model to SageMaker."""
    base_model = config['model']['base_model']
    model_id = config['model']['model_id']
    region = config['deploy']['region']
    iam_role = config['deploy']['iam_role']
    account_id = get_aws_account_id()
    role_arn = f"arn:aws:iam::{account_id}:role/{iam_role}"
    infra_config = model_map[base_model]["aws_infra"]
    
    # Use the LMI container image
    image_uri = "763104351884.dkr.ecr.us-west-2.amazonaws.com/djl-inference:0.25.0-lmi-deepspeed0.10.0-cu118"
    
    instance_type = infra_config['instance_type']
    # accelerator_type = infra_config.get('accelerator_type')
    accelerator_count = infra_config.get('accelerator_count', 1)
    dtype = "float16" if not infra_config.get('dtype') else infra_config.get('dtype')
    # autoscale = config['deploy'].get('autoscale', False)
    # min_capacity = infra_config.get('min_replica_count', 1)
    # max_capacity = infra_config.get('max_replica_count', 2)

    # LMI specific environment variables
    env_vars = {
        "MODEL_ID": base_model,
        "DTYPE": dtype,
        "OPTION_MODEL_LOADING_TIMEOUT": "3600",
        "OPTION_ROLLING_BATCH": "lmi-dist",
        "OPTION_MAX_ROLLING_BATCH_SIZE": "32",
        "OPTION_TENSOR_PARALLEL_DEGREE": str(accelerator_count),
        "OPTION_LOAD_IN_8BIT": "true" if dtype == "int8" else "false",
        "OPTION_LOAD_IN_4BIT": "true" if dtype == "int4" else "false"
    }

    boto3.setup_default_session(region_name=region)

    # Register the model with LMI container
    model = create_model_from_lmi_container(base_model, env_vars, role_arn)

    # Deploy to endpoint
    predictor = deploy_model_to_endpoint(model, model_id, instance_type)
    endpoint_name = predictor.endpoint_name
    print(predictor)
    # # Optional autoscaling
    # if autoscale:
    #     configure_autoscaling(endpoint_name, min_capacity=min_capacity, max_capacity=max_capacity)

    # return endpoint_name
    return endpoint_name