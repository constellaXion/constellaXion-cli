import os
import yaml
import click
from constellaxion.handlers.model import Model
from constellaxion.handlers.dataset import Dataset
from constellaxion.handlers.cloud_job import GCPDeployJob
from constellaxion.services.gcp.iam import create_service_account


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


def init_job(model: Model, dataset: Dataset, job_config):
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
        job.create_config(model, dataset, project_id,
                          location, service_account_email)


@click.command(help="Initialize a new model")
def init():
    """
    Initialize a new model
    """
    model_config = os.path.join(os.getcwd(), "model.yaml")
    if not os.path.exists(model_config):
        click.echo(
            "Error: model.yaml file not found in current directory.", err=True)
        return

    click.echo("Preparing new model job 🤖")
    try:
        with open(model_config, 'r') as file:
            config = yaml.safe_load(file)
            # Get configs
            model_config = config.get('model')
            dataset_config = config.get('dataset')
            deploy_config = config.get('deploy')
            # Init configs
            model = init_model(model_config)
            dataset = init_dataset(dataset_config)
            init_job(model, dataset, deploy_config)
            click.echo(
                click.style("Job Config created. Run 'constellaXion job view' to see details or 'constellaXion job run' to start training your model", fg="green"))
        # Parse values and excecute commands
    except yaml.YAMLError as e:
        click.echo(f"Error parsing model.yaml: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
