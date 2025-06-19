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
    cloud_providers = {"gcp": GCPDeployJob}
    provider = config.get("deploy", {}).get("provider", None)
    if provider in cloud_providers:
        job = cloud_providers[provider]()
        job.run(config)
    else:
        click.echo(click.style("No cloud provider found", fg="red"))


@model.command(help="Serve a trained model")
def serve():
    """Serve Model"""
    config = get_job()
    cloud_providers = {"aws": AWSDeployJob, "gcp": GCPDeployJob}
    provider = config.get("deploy", {}).get("provider", None)
    if provider in cloud_providers:
        job = cloud_providers[provider]()
        job.serve(config)
    else:
        click.echo(click.style("No cloud provider found", fg="red"))


@model.command()
def deploy():
    """Deploy a model"""
    click.echo(click.style("Deploying model...", fg="blue"))
    config = get_job()
    cloud_providers = {"aws": AWSDeployJob, "gcp": GCPDeployJob}
    provider = config.get("deploy", {}).get("provider", None)
    if provider in cloud_providers:
        job = cloud_providers[provider]()
        job.deploy(config)
    else:
        click.echo(click.style("No cloud provider found", fg="red"))


@model.command()
def view():
    """View the status or details of one or more jobs"""
    get_job(show=True)
