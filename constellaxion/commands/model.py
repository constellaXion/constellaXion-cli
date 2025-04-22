import os
import json
import click
from constellaxion.handlers.cloud_job import GCPDeployJob, AWSDeployJob


def get_job(print=False):
    if os.path.exists("job.json"):
        with open("job.json", "r") as f:
            config = json.load(f)
        if print:
            click.echo(click.style(
                "Model Job Config Details:", bold=True, fg="blue"))
            click.echo(json.dumps(config, indent=4))
        return config
    else:
        click.echo(click.style(
            "Error: job.json not found. Run 'constellaxion init' first", fg="red"))
        return None


@click.group()
def model():
    """Manage model jobs"""
    pass


@model.command()
@click.option("--model", required=True, help="Model ID")
def prompt(model: str):
    """Prompt a deployed model"""
    click.echo(click.style(
        f"Send a prompt to {model}", fg="yellow"))

    while True:
        config = get_job()
        if config and config['deploy']['endpoint_path']:
            click.echo(click.style("\nPrompt: ", fg="green"), nl=False)
            prompt = input()
            if prompt.lower() in ['exit', 'quit']:
                break
            job = GCPDeployJob()
            response = job.prompt(prompt, config)
            click.echo(click.style(f"\n🤖 {model}: ", fg="green") + response)
        else:
            click.echo(click.style(
                "Error: Trained model not found. Try training and deploying a model first", fg="red"))
            break


@model.command()
def train():
    """Run training job"""
    click.echo(click.style(f"Preparing training job...", fg="blue"))
    config = get_job()
    if config:
        cloud = config['deploy']['provider']
        if cloud == "gcp":
            job = GCPDeployJob()
            job.run(config)
        # elif cloud == "aws":
        #     job = AWSDeployJob()
        #     job.run(config)


@model.command(help="Serve a trained model")
@click.option("--model", required=True, help="Trained Model ID")
def serve(model: str):
    """Serve Model"""
    click.echo(click.style(f"Serving model with ID: {model}", fg="blue"))
    config = get_job()
    if config:
        cloud = config['deploy']['provider']
        if cloud == "gcp":
            job = GCPDeployJob()
            job.serve(config)


@model.command()
def deploy():
    """Deploy a model"""
    click.echo(click.style(f"Deploying model...", fg="blue"))
    job_config = get_job()
    cloud = job_config['deploy']['provider']
    if cloud == "gcp":
        job = GCPDeployJob()
        job.deploy(job_config)
    elif cloud == "aws":
        job = AWSDeployJob()
        job.deploy(job_config)


@model.command()
def view():
    """View the status or details of one or more jobs"""
    get_job(print=True)
