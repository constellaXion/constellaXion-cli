"""List commands"""

import webbrowser

import click


@click.group(name="list")
def list_cmd():
    """List available resources"""
    pass


@list_cmd.command()
def models():
    """List available models"""
    try:
        webbrowser.open("https://constellaxion.ai/models")
    except (webbrowser.Error, OSError) as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"))
