import click

from constellaxion.commands.init import init
from constellaxion.commands.login import login
from constellaxion.commands.model import model


@click.group()
def cli():
    """Constellaxion CLI: Infrastructure deployment for LLMs"""
    pass


cli.add_command(login)
cli.add_command(init)
cli.add_command(model)

if __name__ == "__main__":
    cli()
