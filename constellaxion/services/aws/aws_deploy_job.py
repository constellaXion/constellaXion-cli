"""AWS LMI deployment module for deploying models to SageMaker endpoints using Large Model Inference."""

import boto3
import sagemaker
from sagemaker.djl_inference.model import DJLModel

from constellaxion.services.aws.utils import get_aws_account_id
from constellaxion.utils import get_model_map


def create_model_from_lmi_container(
    base_model: str, env_vars: dict, execution_role: str
):
    """Creates a SageMaker model using the LMI container."""
    model = DJLModel(model_id=base_model, env=env_vars, role=execution_role)
    return model


def deploy_model_to_endpoint(model, model_id: str, instance_type: str):
    """Deploys a model to a SageMaker endpoint using LMI."""
    endpoint_name = sagemaker.utils.name_from_base(model_id)
    predictor = model.deploy(
        initial_instance_count=1,
        instance_type=instance_type,
        endpoint_name=endpoint_name,
    )
    return predictor


def run_aws_deploy_job(config):
    """Runs the LMI deployment job by creating and deploying a model to SageMaker."""
    deploy_config = config.get("deploy", {})
    if not deploy_config:
        raise KeyError("Invalid config, missing deploy section")
    model_config = config.get("model", {})
    if not model_config:
        raise KeyError("Invalid config, missing model section")
    base_model_alias = model_config.get("base_model", None)
    model_id = model_config.get("model_id", None)
    hf_token = model_config.get("hf_token", None)
    region = deploy_config.get("region", None)
    iam_role = deploy_config.get("iam_role", None)
    account_id = get_aws_account_id()
    role_arn = f"arn:aws:iam::{account_id}:role/{iam_role}"
    # Get the model infra config from the constellaxion database
    model_map = get_model_map(base_model_alias)
    base_model = model_map.get("base_model", None)
    hf_token_required = model_map.get("hf_token_required", False)
    if hf_token_required and not hf_token:
        raise ValueError(
            "This is a protected model, please provide a valid HF token in model.yaml file"
        )
    max_model_length = model_map.get("max_model_length", None)
    # Use the LMI container image
    # image_uri = (
    #     "763104351884.dkr.ecr.us-west-2.amazonaws.com/"
    #     "djl-inference:0.25.0-lmi-deepspeed0.10.0-cu118"
    infra_config = model_map.get("aws_infra", {})
    instance_type = infra_config.get("instance_type", None)
    accelerator_count = infra_config.get("accelerator_count", 1)
    dtype = "float16" if not infra_config.get("dtype") else infra_config.get("dtype")
    option_rolling_batch = infra_config.get("option_rolling_batch", "vllm")

    # LMI specific environment variables
    env_vars = {
        "MODEL_ID": base_model,
        "DTYPE": dtype,
        "OPTION_MODEL_LOADING_TIMEOUT": "3600",
        "OPTION_ROLLING_BATCH": option_rolling_batch,
        "OPTION_MAX_ROLLING_BATCH_SIZE": "32",
        "OPTION_TENSOR_PARALLEL_DEGREE": str(accelerator_count),
        "OPTION_LOAD_IN_8BIT": "true" if dtype == "int8" else "false",
        "OPTION_LOAD_IN_4BIT": "true" if dtype == "int4" else "false",
    }
    if hf_token:
        env_vars["HF_TOKEN"] = hf_token
    if max_model_length:
        env_vars["OPTION_MAX_MODEL_LEN"] = str(max_model_length)
        env_vars["OPTION_MAX_SEQ_LEN"] = str(max_model_length)
    boto3.setup_default_session(region_name=region)

    # Register the model with LMI container
    model = create_model_from_lmi_container(base_model, env_vars, role_arn)

    # Deploy to endpoint
    predictor = deploy_model_to_endpoint(model, model_id, instance_type)
    endpoint_name = predictor.endpoint_name
    return endpoint_name
