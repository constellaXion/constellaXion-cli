"""Model commands"""

import click

from constellaxion.handlers.cloud_job import AWSDeployJob, GCPDeployJob
from constellaxion.ui.server.run import PromptManager
from constellaxion.utils import get_job


@click.group()
def model():
    """Manage model jobs"""
    pass


@model.command()
def prompt():
    """Prompt a deployed model"""
    click.clear()  # Clear the screen
    prompt_manager = PromptManager()
    prompt_manager.run()


@model.command()
def train():
    """Run training job"""
    click.echo(click.style("Preparing training job...", fg="blue"))
    config = get_job()
    if config:
        cloud = config.get("deploy", {}).get("provider", None)
        if cloud == "gcp":
            job = GCPDeployJob()
            job.run(config)
        # elif cloud == "aws":
        #     job = AWSDeployJob()
        #     job.run(config)


@model.command(help="Serve a trained model")
def serve():
    """Serve Model"""
    config = get_job()
    if config:
        model_id = config.get("model", {}).get("model_id", None)
        click.echo(click.style(f"Serving model with ID: {model_id}", fg="blue"))
        cloud = config.get("deploy", {}).get("provider", None)
        if cloud == "gcp":
            job = GCPDeployJob()
            job.serve(config)
        elif cloud == "aws":
            job = AWSDeployJob()
            job.serve(config)


@model.command()
def deploy():
    """Deploy a model"""
    click.echo(click.style("Deploying model...", fg="blue"))
    job_config = get_job()
    cloud = job_config.get("deploy", {}).get("provider", None)
    if cloud == "gcp":
        job = GCPDeployJob()
        job.deploy(job_config)
    elif cloud == "aws":
        job = AWSDeployJob()
        job.deploy(job_config)


@model.command()
def view():
    """View the status or details of one or more jobs"""
    get_job(show=True)
