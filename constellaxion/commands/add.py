import click
from constellaxion.services.gcp.iam import create_service_account


@click.command(help="Sync a new project to Osyris")
@click.option('--project-id', required=True, help='GCP Project ID')
def add(project_id: str):
    """
    Add a project
    """
    click.echo(f"Initializing resources for project: {project_id}")
    try:
        create_service_account(project_id)
        click.echo(
            "constellaxion-admin service account successfully created and roles assigned!")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
