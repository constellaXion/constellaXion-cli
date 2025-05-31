"""Initialize a new model configuration and setup required resources."""

import os

import click
from halo import Halo
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from tabulate import tabulate
import yaml

from constellaxion.handlers.cloud_job import AWSDeployJob, GCPDeployJob
from constellaxion.handlers.dataset import Dataset
from constellaxion.handlers.model import Model
from constellaxion.handlers.training import Training
from constellaxion.services.aws.iam import create_aws_permissions
from constellaxion.services.gcp.iam import create_service_account

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

    Returns:
        Model: Initialized model instance

    Raises:
        AttributeError: If required attributes (id or base) are missing
    """
    model_id = model_config.get("id")
    base = model_config.get("base")
    if not model_id:
        raise AttributeError("Missing value, model.id in model.yaml file")
    if not base:
        raise AttributeError("Missing value, model.base in model.yaml file")
    return Model(model_id, base)


def init_dataset(dataset_config, model_config):
    """Initialize the dataset

    Args:
        dataset_config (dict): Dataset config details
    """
    model_id = model_config.get("id")
    train = dataset_config.get("train")
    val = dataset_config.get("val")
    test = dataset_config.get("test")
    if not train:
        raise AttributeError("Missing value, dataset.train in model.yaml file")
    if not val:
        raise AttributeError("Missing value, dataset.val in model.yaml file")
    if not test:
        raise AttributeError("Missing value, dataset.test in model.yaml file")
    return Dataset(train, val, test, model_id)


def init_training(training_config):
    """Initialize the dataset

    Args:
        dataset_config (dict): Dataset config details
    """
    epochs = training_config.get("epochs")
    batch_size = training_config.get("batch_size")
    if not epochs:
        raise AttributeError("Missing value, training.epochs in model.yaml file")
    if not batch_size:
        raise AttributeError("Missing value, training.batch_size in model.yaml file")
    return Training(epochs, batch_size)


def init_job(job_config, model: Model, dataset: Dataset, training: Training):
    """Initialize the deployment job definition

    Args:
        job_config (list): List of dicts containing deployment job config details
    """
    platform = None
    if "aws" in job_config:
        platform = "aws"
    elif "gcp" in job_config:
        platform = "gcp"
    else:
        click.echo(
            "Error: Missing value, job.gcp or job.aws in model.yaml file", err=True
        )
    # Initialize GCP resources
    if platform == "gcp":
        gcp = job_config.get("gcp")
        project_id = gcp.get("project_id")
        region = gcp.get("region")
        if not project_id:
            click.echo(
                "Error: Missing value, job.gcp.project_id in model.yaml file", err=True
            )
        if not region:
            click.echo(
                "Error: Missing value, job.gcp.region in model.yaml file", err=True
            )

        click.echo(f"Initializing resources for project: {project_id}")
        try:
            service_account_email = create_service_account(project_id)
            if service_account_email:
                click.echo("The required GCP Service Account is ready to use 🦾")
        except (ValueError, RuntimeError) as e:
            click.echo(f"Error: {str(e)}", err=True)
        job = GCPDeployJob()
        # Create job config
        job.create_config(
            model, project_id, region, service_account_email, dataset, training
        )

    # Initialize AWS resources
    elif platform == "aws":
        aws = job_config.get("aws")
        region = aws.get("region")
        if not region:
            raise ValueError("Missing value, job.aws.region in model.yaml file")
        create_aws_permissions()
        job = AWSDeployJob()
        # Create job config
        job.create_config(model, region, dataset, training)


def show_after_init_command_table():
    """Show the command table"""
    table = [
        ["Command", "Description"],
        ["constellaXion model view", "View the current model configuration"],
        ["constellaXion model train", "Run finetuning job"],
        ["constellaXion model deploy", "Deploy a foundation model"],
    ]
    click.echo(tabulate(table, headers="firstrow", tablefmt="grid"))


@click.command(help="Initialize a new model")
def init():
    """
    Initialize a new model
    """
    # Print the logo
    console.print(
        Panel(Text(CONSTELLAXION_LOGO, justify="center"), style="#47589B", expand=True)
    )

    # Start loading animation
    spinner = Halo(spinner="dots")
    spinner.start()

    # Load the model config
    model_config = os.path.join(os.getcwd(), "model.yaml")
    if not os.path.exists(model_config):
        click.echo("Error: model.yaml file not found in current directory.", err=True)
        raise click.Abort()

    click.echo("Preparing new model config 📡")
    try:
        with open(model_config, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            training = None
            dataset = None
            # Get configs
            model_config = config.get("model")
            training_config = config.get("training")
            # If training config is present, initialize training
            if training_config:
                training = init_training(training_config)
                dataset_config = config.get("dataset")
                # Ensure dataset config is present if training config is present
                if not dataset_config:
                    click.echo(
                        "Error: Missing value, dataset in model.yaml file", err=True
                    )
                    raise click.Abort()
                dataset = init_dataset(dataset_config, model_config)
            deploy_config = config.get("deploy")
            if not deploy_config:
                click.echo("Error: Missing value, deploy in model.yaml file", err=True)
                raise click.Abort()
            # Init configs
            model = init_model(model_config)
            init_job(deploy_config, model, dataset, training)

            spinner.succeed("Initialization complete!")
            click.echo(click.style("Job Config created", fg="green"))
            show_after_init_command_table()
    # Parse values and excecute commands
    except yaml.YAMLError as e:
        click.echo(f"Error parsing model.yaml: {str(e)}", err=True)
        raise click.Abort()
    except (OSError, ValueError, KeyError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
