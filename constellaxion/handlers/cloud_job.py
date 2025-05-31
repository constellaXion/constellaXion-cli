"""Module for handling cloud deployment jobs across different providers (AWS, GCP)."""

from abc import ABC, abstractmethod
import json

from constellaxion.handlers.dataset import Dataset
from constellaxion.handlers.model import Model
from constellaxion.handlers.training import Training
from constellaxion.services.aws.aws_deploy_job import run_aws_deploy_job
from constellaxion.services.aws.prompt_aws_model import send_aws_prompt
from constellaxion.services.gcp.gcp_deploy_job import run_gcp_deploy_job
from constellaxion.services.gcp.prompt_gcp_model import send_gcp_prompt
from constellaxion.services.gcp.serve_job import run_serving_job
from constellaxion.services.gcp.train_job import run_training_job


class BaseCloudJob(ABC):
    """Base class for cloud deployment jobs providing common interface for model deployment."""

    def __init__(self):
        pass

    @staticmethod
    @abstractmethod
    def run(config):
        """Run model finetuning on GCP"""
        pass

    @staticmethod
    @abstractmethod
    def create_config(config):
        """Create a JSON configuration file from model and dataset attributes."""
        pass


class GCPDeployJob(BaseCloudJob):
    """GCP deployment job class."""

    @staticmethod
    def run(config):
        """Run model finetuning on GCP"""
        run_training_job(config)

    @staticmethod
    def serve(config):
        """Serve finetuned model on GCP"""
        endpoint_path = run_serving_job(config)
        config["deploy"]["endpoint_path"] = endpoint_path
        with open("job.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    @staticmethod
    def deploy(config):
        """Deploy foundation model to GCP"""
        endpoint_path = run_gcp_deploy_job(config)
        config["deploy"]["endpoint_path"] = endpoint_path
        with open("job.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    @staticmethod
    def prompt(prompt, config):
        """Send prompt to model"""
        endpoint_path = config["deploy"]["endpoint_path"]
        region = config["deploy"]["region"]
        response = send_gcp_prompt(prompt, endpoint_path, region)
        return response

    @staticmethod
    def create_config(
        model: Model,
        project_id: str,
        region: str,
        service_account: str,
        dataset: Dataset,
        training: Training,
    ):
        """Create a JSON configuration file from model and dataset attributes."""
        if not project_id or not region or not service_account:
            raise ValueError(
                "model, project_id, region, and service_account must be provided"
            )
        bucket_name = f"constellaxion-{project_id}"
        job_config = {
            "model": {
                "model_id": model.id,
                "base_model": model.base_model,
            },
            "dataset": dataset.to_dict() if dataset else None,
            "training": training.to_dict() if training else None,
            "deploy": {
                "provider": "gcp",
                "project_id": project_id,
                "region": region,
                "bucket_name": bucket_name,
                "staging_dir": f"{model.id}/staging",
                "experiments_dir": f"{model.id}/experiments",
                "model_path": f"{model.id}/model",
                "service_account": service_account,
            },
        }
        with open("job.json", "w", encoding="utf-8") as f:
            json.dump(job_config, f, indent=4)


class AWSDeployJob(BaseCloudJob):
    """AWS deployment job class."""

    @staticmethod
    def run(*args, **kwargs):
        """Run model finetuning on AWS"""

    @staticmethod
    def serve(*args, **kwargs):
        """Serve finetuned model on AWS"""

    @staticmethod
    def deploy(config):
        """Deploy foundation model to AWS"""
        endpoint_path = run_aws_deploy_job(config)
        config["deploy"]["endpoint_path"] = endpoint_path
        with open("job.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    @staticmethod
    def prompt(prompt, config):
        """Send prompt to model"""
        endpoint_path = config["deploy"]["endpoint_path"]
        region = config["deploy"]["region"]
        response = send_aws_prompt(prompt, endpoint_path, region)
        return response

    @staticmethod
    def create_config(model: Model, region: str, dataset: Dataset, training: Training):
        """Create a JSON configuration file from model and dataset attributes."""
        if not region:
            raise ValueError("region must be provided")
        job_config = {
            "model": {
                "model_id": model.id,
                "base_model": model.base_model,
            },
            "dataset": dataset.to_dict() if dataset else None,
            "training": training.to_dict() if training else None,
            "deploy": {
                "provider": "aws",
                "region": region,
                "bucket_name": f"constellaxion-{model.id}",
                "staging_dir": f"{model.id}/staging",
                "experiments_dir": f"{model.id}/experiments",
                "model_path": f"{model.id}/model",
                "iam_role": "constellaxion-admin",
            },
        }
        with open("job.json", "w", encoding="utf-8") as f:
            json.dump(job_config, f, indent=4)
