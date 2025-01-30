import os
import json
import click
from constellaxion.handlers.cloud_job import GCPDeployJob


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
def job():
    """Manage jobs"""
    pass


@job.command()
@click.option("--model", required=True, help="Model ID")
def prompt(model: str):
    """Prompt a deployed model"""
    click.echo(click.style(
        f"🤖 Hello! Start chatting with {model}", fg="green"))

    while True:
        config = get_job()
        if config and config['deploy']['endpoint_path']:
            click.echo(click.style("\nYou: ", fg="green"), nl=False)
            prompt = input()
            if prompt.lower() in ['exit', 'quit']:
                break
            job = GCPDeployJob()
            response = job.prompt(prompt, config)
            click.echo(click.style(f"\n🤖 {model}: ", fg="green") + response)
        else:
            click.echo(click.style(
                "Trained model not found. Try training and deploying a model first", fg="red"))


@job.command()
def run():
    """Run training job"""
    click.echo(click.style(f"Preparing training job...", fg="blue"))
    config = get_job()
    if config:
        cloud = config['deploy']['provider']
        match cloud:
            case "gcp":
                job = GCPDeployJob()
                job.run(config)


@job.command(help="Serve a trained model")
@click.option("--model", required=True, help="Trained Model ID")
def serve(model: str):
    """Serve Model"""
    click.echo(click.style(f"Serving model with ID: {model}", fg="blue"))
    config = get_job()
    if config:
        cloud = config['deploy']['provider']
        match cloud:
            case "gcp":
                job = GCPDeployJob()
                job.serve(config)


@job.command()
def view():
    """View the status or details of one or more jobs"""
    get_job(print=True)
