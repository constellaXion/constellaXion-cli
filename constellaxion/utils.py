"""Utility functions for the constellaxion CLI."""

import contextlib
import json
import logging
import os

import click
import requests


def get_json(path):
    """Get job configuration"""
    with open(path, "r", encoding="utf-8") as f:
        j = json.load(f)
        return j


@contextlib.contextmanager
def suppress_logs_and_warnings():
    """Context manager to temporarily suppress all logs and warnings."""
    logging.basicConfig(level=logging.CRITICAL)
    logging.getLogger("sagemaker.config").setLevel(logging.CRITICAL)
    logging.getLogger("boto3").setLevel(logging.CRITICAL)
    logging.getLogger("botocore").setLevel(logging.CRITICAL)
    logging.getLogger("pydantic").setLevel(logging.CRITICAL)


# Function to get the effective level name
def get_level_name(level):
    """Get the effective level name for a logging level."""
    if level == logging.DEBUG:
        return "DEBUG"
    elif level == logging.INFO:
        return "INFO"
    elif level == logging.WARNING:
        return "WARNING"
    elif level == logging.ERROR:
        return "ERROR"
    elif level == logging.CRITICAL:
        return "CRITICAL"
    else:
        return "NOTSET"


def check_logging_levels():
    """Check the logging levels of all loggers."""
    # Get the root logger
    root_logger = logging.getLogger()
    # Get all other loggers
    loggers = logging.Logger.manager.loggerDict
    with open("log.txt", "w", encoding="utf-8") as f:
        f.write(f"Logger: root, Level: {get_level_name(root_logger.level)}\n")
        for name, logger in loggers.items():
            if isinstance(logger, logging.PlaceHolder):
                continue
            f.write(f"Logger: {name}, Level: {get_level_name(logger.level)}\n")


def get_model_map(alias: str):
    """Get the model map from the"""
    url = f"https://us-central1-constellaxion.cloudfunctions.net/getModelByAlias?alias={alias}"
    response = requests.get(url, timeout=60)
    data = response.json()
    return data.get("model", {})


def get_job(show=False):
    """Load and optionally print the job configuration from job.json."""
    print(os.getcwd())
    if os.path.exists("job.json"):
        with open("job.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        if show:
            click.echo(click.style("Model Job Config Details:", bold=True, fg="blue"))
            click.echo(json.dumps(config, indent=4))
        return config
    else:
        click.echo(
            click.style(
                "Error: job.json not found. Run 'constellaxion init' first", fg="red"
            )
        )
        return None
