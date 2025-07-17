import click

from constellaxion.commands.aws import aws
from constellaxion.commands.init import init
from constellaxion.commands.list_cmd import list_cmd
from constellaxion.commands.login import login
from constellaxion.commands.model import model


@click.group()
def cli():
    """Constellaxion CLI: Infrastructure deployment for LLMs"""
    pass


cli.add_command(login)
cli.add_command(init)
cli.add_command(model)
cli.add_command(aws)
cli.add_command(list_cmd)

if __name__ == "__main__":
    cli()
