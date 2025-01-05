import click
from constellaxion.commands.login import login
from constellaxion.commands.init import init
from constellaxion.commands.job import job


@click.group()
def cli():
    """Constellaxion CLI: Infrastructure deployment for LLMs"""
    pass


cli.add_command(login)
cli.add_command(init)
cli.add_command(job)

if __name__ == "__main__":
    cli()
