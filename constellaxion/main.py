import click

from constellaxion.commands.init import init
from constellaxion.commands.login import login
from constellaxion.commands.model import model
from constellaxion.commands.aws import aws

@click.group()
def cli():
    """Constellaxion CLI: Infrastructure deployment for LLMs"""
    pass


cli.add_command(login)
cli.add_command(init)
cli.add_command(model)
cli.add_command(aws)

if __name__ == "__main__":
    cli()
