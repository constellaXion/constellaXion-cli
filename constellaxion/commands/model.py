import json
import os

import click

from constellaxion.handlers.cloud_job import AWSDeployJob, GCPDeployJob


def get_job(show=False):
    """Load and optionally print the job configuration from job.json."""
    if os.path.exists("job.json"):
        with open("job.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        if show:
            click.echo(click.style("Model Job Config Details:", bold=True, fg="blue"))
            click.echo(json.dumps(config, indent=4))
        return config
    else:
        click.echo(
            click.style(
                "Error: job.json not found. Run 'constellaxion init' first", fg="red"
            )
        )
        return None


@click.group()
def model():
    """Manage model jobs"""
    pass


@model.command()
def prompt():
    """Prompt a deployed model"""
    config = get_job()
    cloud = config["deploy"]["provider"]
    model_id = config["model"]["model_id"]
    click.clear()  # Clear the screen
    click.echo(click.style(f"Send a prompt to {model_id}", fg="yellow", bold=True))
    click.echo(click.style("Type 'exit' or 'quit' to quit"))
    while True:
        if cloud and config["deploy"]["endpoint_path"]:
            response = ""
            click.echo(click.style("\nPrompt: ", fg="green"), nl=False)
            txt = input()
            if txt.lower() in ["exit", "quit"]:
                break

            if cloud == "gcp":
                job = GCPDeployJob()
                response = job.prompt(txt, config)
            elif cloud == "aws":
                job = AWSDeployJob()
                response = job.prompt(txt, config)
            click.echo(click.style(f"\n🤖 {model_id}: ", fg="green") + response)
        else:
            click.echo(
                click.style(
                    "Error: Trained model not found. Try training and deploying a model first",
                    fg="red",
                )
            )
            break


@model.command()
def train():
    """Run training job"""
    click.echo(click.style("Preparing training job...", fg="blue"))
    config = get_job()
    if config:
        cloud = config["deploy"]["provider"]
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
        model_id = config["model"]["model_id"]
        click.echo(click.style(f"Serving model with ID: {model_id}", fg="blue"))
        cloud = config["deploy"]["provider"]
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
    cloud = job_config["deploy"]["provider"]
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
