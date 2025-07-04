import os
from unittest.mock import MagicMock, patch

import pytest

from constellaxion.handlers.cloud_job import AWSDeployJob, GCPDeployJob
from constellaxion.handlers.dataset import Dataset
from constellaxion.handlers.model import Model
from constellaxion.handlers.training import Training


@pytest.fixture
def valid_model():
    """Test model with valid configuration."""
    return Model("test-model", "tiny-llama-1b")


@pytest.fixture
def valid_dataset():
    """Test dataset with valid configuration."""
    return Dataset("train.csv", "val.csv", "test.csv", "test-model")


@pytest.fixture
def valid_training():
    """Test training with valid configuration."""
    return Training(3, 32)


def test_gcp_deploy_job_create_config_with_invalid_model():
    """Test GCP deploy job configuration creation with invalid model."""
    with pytest.raises(AttributeError):
        GCPDeployJob.create_config(
            None,
            "test-project",
            "us-central1",
            "test@test-project.iam.gserviceaccount.com",
            None,
            None,
        )


def test_aws_deploy_job_create_config_with_invalid_model():
    """Test AWS deploy job configuration creation with invalid model."""
    with pytest.raises(AttributeError):
        AWSDeployJob.create_config(None, "us-east-1", None, None)


def test_gcp_deploy_job_create_config_with_missing_project_id(
    valid_model, valid_dataset, valid_training
):
    """Test GCP deploy job configuration creation with missing project ID."""
    with pytest.raises(ValueError):
        GCPDeployJob.create_config(
            valid_model,
            "",
            "us-central1",
            "test@test-project.iam.gserviceaccount.com",
            valid_dataset,
            valid_training,
        )


def test_aws_deploy_job_create_config_with_missing_region(
    valid_model, valid_dataset, valid_training
):
    """Test AWS deploy job configuration creation with missing region."""
    with pytest.raises(ValueError):
        AWSDeployJob.create_config(valid_model, "", valid_dataset, valid_training)


@patch("constellaxion.services.gcp.gcp_deploy_job.run_gcp_deploy_job")
def test_gcp_deploy_job_deploy_with_invalid_config(_mock_run_gcp_deploy_job):
    """Test GCP deploy job deployment with invalid config."""
    with pytest.raises(KeyError):
        GCPDeployJob.deploy({})


@patch.dict(os.environ, {
    'AWS_ACCESS_KEY_ID': 'fake_key',
    'AWS_SECRET_ACCESS_KEY': 'fake_secret',
    'AWS_DEFAULT_REGION': 'us-east-1'
})
@patch("boto3.Session")
@patch("constellaxion.services.aws.aws_deploy_job.run_aws_deploy_job")
def test_aws_deploy_job_deploy_with_invalid_config(mock_run_aws_deploy_job, mock_session):
    """Test AWS deploy job deployment with invalid config."""
    # Create a mock session with a mock client method
    mock_session_instance = MagicMock()
    mock_sts_client = MagicMock()
    mock_sts_client.get_caller_identity.return_value = {
        'UserId': 'fake_user_id',
        'Account': '123456789012',
        'Arn': 'arn:aws:iam::123456789012:user/fake-user'
    }
    mock_session_instance.client.return_value = mock_sts_client
    mock_session.return_value = mock_session_instance
    
    with pytest.raises(KeyError):
        AWSDeployJob.deploy({})



@patch("constellaxion.services.gcp.prompt_gcp_model.send_gcp_prompt")
def test_gcp_deploy_job_prompt_with_invalid_config(_mock_send_gcp_prompt):
    """Test GCP deploy job prompt with invalid config."""
    with pytest.raises(KeyError):
        GCPDeployJob.prompt("Test prompt", {})


@patch("constellaxion.services.aws.prompt_aws_model.send_aws_prompt")
def test_aws_deploy_job_prompt_with_invalid_config(_mock_send_aws_prompt):
    """Test AWS deploy job prompt with invalid config."""
    with pytest.raises(KeyError):
        AWSDeployJob.prompt("Test prompt", {})
