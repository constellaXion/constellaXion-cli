from __future__ import annotations
import sys
from typing import Iterable, Sequence
import click

def accelerator_type_map():
    return {
        "NVIDIA_L4": "nvidia-l4",
        "NVIDIA_A100_80GB": "nvidia-a100-80gb",
        "NVIDIA_H100_80GB": "nvidia-h100-80gb",
    }

allowed_gpu_regions = [
    "asia-southeast1",
    "asia-south1",
    "europe-west1",
    "europe-west4",
    "us-central1",
    "us-east4"
]

def ensure_region(region: str | None) -> str:
    """
    Return a valid region. If `region` is not in `allowed_regions`, prompt the user
    with an interactive picker (arrow keys + number shortcuts) and confirm with Enter.
    Falls back to numeric prompt when not attached to a TTY or if questionary is missing.
    """
    allowed: Sequence[str] = sorted(allowed_gpu_regions)
    if not allowed:
        raise click.UsageError("No allowed regions configured.")
    if region in allowed:
        return region  # already valid
    click.secho(f"⚠️ Your selected region is not available for GPU serving with Cloud Run. Please select a region from the available options:", fg="blue", bold=True)
    # Try full-screen-ish interactive select first (arrow keys + numbers)
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            import questionary  # built on prompt_toolkit
            # Number each item so number shortcuts are obvious, and enable shortcuts.
            numbered = [f"{i+1}. {r}" for i, r in enumerate(allowed)]
            sel = questionary.select(
                f"(↑/↓ to navigate, numbers 1–9 to jump, Enter to confirm)",
                choices=numbered,
                use_shortcuts=True,   # 1–9 work as quick selectors
                qmark=">",
                pointer="➤",
                instruction="",
            ).ask()
            if sel is None:
                raise click.Abort()
            # Extract the region part from "N. region"
            return sel.split(". ", 1)[1]
        except ImportError:
            # Fall back to numeric prompt if questionary isn't installed
            pass

    # Fallback: plain numeric selection (works in CI/non‑TTY)
    for i, r in enumerate(allowed, 1):
        click.echo(f"  {i}. {r}")
    idx = click.prompt("Enter number", type=click.IntRange(1, len(allowed)))
    return allowed[idx - 1]