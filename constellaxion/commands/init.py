import os
import shutil
import yaml
import click
from constellaxion.handlers.model import Model
from constellaxion.handlers.dataset import Dataset
from constellaxion.handlers.training import Training
from constellaxion.handlers.cloud_job import GCPDeployJob
from constellaxion.services.gcp.iam import create_service_account
import pyfiglet
import random
import time
from rich.console import Console
from rich.text import Text
from rich.progress import Progress
from rich.panel import Panel
from halo import Halo
import sys
import subprocess

console = Console()

CONSTELLAXION_LOGO = """\
░█▀▀░█▀█░█▀█░█▀▀░▀█▀░█▀▀░█░░░█░░░█▀█░█░█░▀█▀░█▀█░█▀█
░█░░░█░█░█░█░▀▀█░░█░░█▀▀░█░░░█░░░█▀█░▄▀▄░░█░░█░█░█░█
░▀▀▀░▀▀▀░▀░▀░▀▀▀░░▀░░▀▀▀░▀▀▀░▀▀▀░▀░▀░▀░▀░▀▀▀░▀▀▀░▀░▀
"""


CXN_LOGO = """\
 ██████╗██╗  ██╗███╗   ██╗
██╔════╝╚██╗██╔╝████╗  ██║
██║      ╚███╔╝ ██╔██╗ ██║
██║      ██╔██╗ ██║╚██╗██║
╚██████╗██╔╝ ██╗██║ ╚████║
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
"""

def init_model(model_config):
    """Initialize the model

    Args:
        model_config (dict): Model config details
    """
    id = model_config.get('id')
    base = model_config.get('base')
    if not id:
        click.echo(
            f"Error: Missing value, model.id in model.yaml file", err=True)
    if not base:
        click.echo(
            f"Error: Missing value, model.base in model.yaml file", err=True)
    return Model(id, base)


def init_dataset(dataset_config):
    """Initialize the dataset

    Args:
        dataset_config (dict): Dataset config details
    """
    train = dataset_config.get('train')
    val = dataset_config.get('val')
    test = dataset_config.get('test')
    if not train:
        click.echo(
            f"Error: Missing value, dataset.train in model.yaml file", err=True)
    if not val:
        click.echo(
            f"Error: Missing value, dataset.val in model.yaml file", err=True)
    if not test:
        click.echo(
            f"Error: Missing value, dataset.test in model.yaml file", err=True)
    return Dataset(train, val, test)


def init_training(training_config):
    """Initialize the dataset

    Args:
        dataset_config (dict): Dataset config details
    """
    epochs = training_config.get('epochs')
    batch_size = training_config.get('batch_size')
    if not epochs:
        click.echo(
            f"Error: Missing value, training.epochs in model.yaml file", err=True)
    if not batch_size:
        click.echo(
            f"Error: Missing value, training.batch_size in model.yaml file", err=True)
    return Training(epochs, batch_size)


def init_job(job_config, model: Model, dataset: Dataset, training: Training):
    """Initialize the deployment job definition

    Args:
        job_config (list): List of dicts containing deployment job config details
    """
    gcp = job_config.get('gcp')
    if gcp:
        project_id = gcp.get('project_id')
        location = gcp.get('location')
        if not project_id:
            click.echo(
                f"Error: Missing value, job.gcp.project_id in model.yaml file", err=True)
        if not location:
            click.echo(
                f"Error: Missing value, job.gcp.location in model.yaml file", err=True)

        click.echo(f"Initializing resources for project: {project_id}")
        try:
            service_account_email = create_service_account(project_id)
            if service_account_email:
                click.echo(
                    "The required GCP Service Account is ready to use 🦾")
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
        job = GCPDeployJob()
        # Create job config
        job.create_config(model, project_id,
                          location, service_account_email, dataset, training)


@click.command(help="Initialize a new model")
def init():
    """
    Initialize a new model
    """
    # Print the logo
    console.print(Panel(Text(CONSTELLAXION_LOGO, justify="center"), style="#47589B", expand=True))

    # Start loading animation
    spinner = Halo(spinner='dots')
    spinner.start()

    # Load the model config
    model_config = os.path.join(os.getcwd(), "model.yaml")
    if not os.path.exists(model_config):
        click.echo(
            "Error: model.yaml file not found in current directory.", err=True)
        return

    click.echo("Preparing new model config 📡")
    try:
        with open(model_config, 'r') as file:
            config = yaml.safe_load(file)
            training = None
            dataset = None
            # Get configs
            model_config = config.get('model')
            training_config = config.get('training')
            # If training config is present, initialize training
            if training_config:
                training = init_training(training_config)
                dataset_config = config.get('dataset')
                # Ensure dataset config is present if training config is present
                if not dataset_config:
                    click.echo(
                        "Error: Missing value, dataset in model.yaml file", err=True)
                    return
                dataset = init_dataset(dataset_config)
            deploy_config = config.get('deploy')
            if not deploy_config:
                click.echo(
                    "Error: Missing value, deploy in model.yaml file", err=True)
                return
            # Init configs
            model = init_model(model_config)
            init_job(deploy_config, model, dataset, training)

            spinner.succeed('Initialization complete!')
            click.echo(
                click.style("Job Config created. Run 'constellaXion model view' to see details or 'constellaXion model train' to start training your model", fg="green"))

        # Parse values and excecute commands
    except yaml.YAMLError as e:
        click.echo(f"Error parsing model.yaml: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)

