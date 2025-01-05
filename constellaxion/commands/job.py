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


@job.command()
def view():
    """View the status or details of one or more jobs"""
    get_job(print=True)
