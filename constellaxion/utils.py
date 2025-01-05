import os
import json
import click


def get_json(path):
    """Get job configuration"""
    with open(path, "r") as f:
        j = json.load(f)
        return j
