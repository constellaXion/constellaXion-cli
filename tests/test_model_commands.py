import json
from unittest.mock import patch

from click.testing import CliRunner
import pytest

from constellaxion.commands.model import get_job, model


@pytest.fixture
def valid_job_config():
    """Test job configuration."""
    return {
        "model": {"model_id": "test-model", "base_model": "tiny-llama-1b"},
        "deploy": {
            "provider": "gcp",
            "endpoint_path": "projects/test/locations/us-central1/endpoints/test-endpoint",
            "region": "us-central1",
        },
    }


@pytest.fixture
def runner():
    """Click test runner."""
    return CliRunner()


def test_get_job_with_missing_file(runner):
    """Test get_job when job.json doesn't exist."""
    with runner.isolated_filesystem():
        result = get_job()
        assert result is None  # nosec: B101


def test_get_job_with_valid_file(runner, valid_job_config):
    """Test get_job with valid job.json."""
    with runner.isolated_filesystem():
        with open("job.json", "w", encoding="utf-8") as f:
            json.dump(valid_job_config, f)
        result = get_job()
        assert result == valid_job_config  # nosec: B101


# @patch("constellaxion.handlers.cloud_job.GCPDeployJob.prompt")
# def test_model_prompt_command_gcp(mock_prompt, runner, valid_job_config):
#     """Test model prompt command with GCP provider."""
#     mock_prompt.return_value = "Test response"
#     with runner.isolated_filesystem():
#         with open("job.json", "w", encoding="utf-8") as f:
#             json.dump(valid_job_config, f)
#         with patch("builtins.input", return_value="test prompt"):
#             result = runner.invoke(model, ["prompt"])
#             assert result.exit_code == 0
#             mock_prompt.assert_called_once_with("test prompt", valid_job_config)


# @patch("constellaxion.handlers.cloud_job.AWSDeployJob.prompt")
# def test_model_prompt_command_aws(mock_prompt, runner, valid_job_config):
#     """Test model prompt command with AWS provider."""
#     mock_prompt.return_value = "Test response"
#     valid_job_config["deploy"]["provider"] = "aws"
#     with runner.isolated_filesystem():
#         with open("job.json", "w") as f:
#             json.dump(valid_job_config, f)
#         with patch("builtins.input", return_value="test prompt"):
#             result = runner.invoke(model, ["prompt"])
#             assert result.exit_code == 0
#             mock_prompt.assert_called_once_with("test prompt", valid_job_config)


# def test_model_prompt_command_without_endpoint(runner, valid_job_config):
#     """Test model prompt command when endpoint is not set."""
#     valid_job_config["deploy"]["endpoint_path"] = ""
#     with runner.isolated_filesystem():
#         with open("job.json", "w") as f:
#             json.dump(valid_job_config, f)
#         result = runner.invoke(model, ["prompt"])
#         assert result.exit_code == 0
#         assert "Error: Trained model not found" in result.output


@patch("constellaxion.handlers.cloud_job.GCPDeployJob.run")
def test_model_train_command_gcp(mock_run, runner, valid_job_config):
    """Test model train command with GCP provider."""
    with runner.isolated_filesystem():
        with open("job.json", "w", encoding="utf-8") as f:
            json.dump(valid_job_config, f)
        result = runner.invoke(model, ["train"])
        assert result.exit_code == 0  # nosec: B101
        mock_run.assert_called_once_with(valid_job_config)


@patch("constellaxion.handlers.cloud_job.GCPDeployJob.serve")
def test_model_serve_command_gcp(mock_serve, runner, valid_job_config):
    """Test model serve command with GCP provider."""
    with runner.isolated_filesystem():
        with open("job.json", "w", encoding="utf-8") as f:
            json.dump(valid_job_config, f)
        result = runner.invoke(model, ["serve"])
        assert result.exit_code == 0  # nosec: B101
        mock_serve.assert_called_once_with(valid_job_config)


@patch("constellaxion.handlers.cloud_job.AWSDeployJob.serve")
def test_model_serve_command_aws(mock_serve, runner, valid_job_config):
    """Test model serve command with AWS provider."""
    valid_job_config["deploy"]["provider"] = "aws"
    with runner.isolated_filesystem():
        with open("job.json", "w", encoding="utf-8") as f:
            json.dump(valid_job_config, f)
        result = runner.invoke(model, ["serve"])
        assert result.exit_code == 0  # nosec: B101
        mock_serve.assert_called_once_with(valid_job_config)


@patch("constellaxion.handlers.cloud_job.GCPDeployJob.deploy")
def test_model_deploy_command_gcp(mock_deploy, runner, valid_job_config):
    """Test model deploy command with GCP provider."""
    with runner.isolated_filesystem():
        with open("job.json", "w", encoding="utf-8") as f:
            json.dump(valid_job_config, f)
        result = runner.invoke(model, ["deploy"])
        assert result.exit_code == 0  # nosec: B101
        mock_deploy.assert_called_once_with(valid_job_config)


@patch("constellaxion.handlers.cloud_job.AWSDeployJob.deploy")
def test_model_deploy_command_aws(mock_deploy, runner, valid_job_config):
    """Test model deploy command with AWS provider."""
    valid_job_config["deploy"]["provider"] = "aws"
    with runner.isolated_filesystem():
        with open("job.json", "w", encoding="utf-8") as f:
            json.dump(valid_job_config, f)
        result = runner.invoke(model, ["deploy"])
        assert result.exit_code == 0  # nosec: B101
        mock_deploy.assert_called_once_with(valid_job_config)
