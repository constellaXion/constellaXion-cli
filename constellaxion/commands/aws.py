from typing import Optional

import click

from constellaxion.services.terraform_service import TerraformService
from constellaxion.terraform.core.display import (
    print_error,
    print_info,
    print_resource_table,
    print_success,
    print_warning,
)
from constellaxion.utils import get_job


@click.group()
def aws():
    """Commands for managing AWS foundational resources."""
    pass


def _get_aws_config(
    region_override: Optional[str] = None, profile_override: Optional[str] = None
) -> tuple[str, Optional[str]]:
    """Get AWS region and profile from job, CLI overrides, or prompt user."""
    config = get_job(show=False, fail_silently=True)
    profile = None
    region = None

    if config and config.get("deploy", {}).get("provider") == "aws":
        deploy_config = config["deploy"]
        profile = deploy_config.get("profile")
        region = deploy_config.get("region")
        print_info(
            f"Using config from job.json (Profile: {profile or 'default'}, Region: {region})"
        )

    if region_override:
        region = region_override
        print_info(f"Region overridden to: {region}")

    if profile_override:
        profile = profile_override
        print_info(f"Profile overridden to: {profile}")

    if not region:
        region = click.prompt("Please enter the AWS region")
    if not profile:
        profile_input = click.prompt(
            "Please enter the AWS profile (leave blank for default)",
            default="",
            show_default=False,
        )
        profile = profile_input if profile_input else None

    return region, profile


@aws.command("list-resources")
@click.option("--clean", is_flag=True, help="Force clean workspace initialization")
def list_resources(clean: bool):
    """List all foundational AWS resources managed by Constellaxion."""
    try:
        region, profile = _get_aws_config()
        service = TerraformService()

        print_info(
            f"Scanning resources in region '{region}' using profile '{profile or 'default'}'..."
        )

        result = service.list_resources("aws", region, profile, force_clean=clean)

        if not result["success"]:
            print_error("Failed to list resources", result.get("error"))
            return

        print_resource_table(
            title="Constellaxion Managed AWS Resources",
            resources=result["resources"],
            provider=result["provider"],
            region=result["region"],
        )

    except Exception as e:
        print_error(f"Unexpected error: {e}")


@aws.command("destroy")
@click.option("--all", "-a", is_flag=True, help="Bypass confirmation")
def destroy(all: bool):
    """Destroy ALL foundational AWS resources managed by Constellaxion."""
    try:
        region, profile = _get_aws_config()
        service = TerraformService()

        if not all:
            print_warning("DANGER ZONE: RESOURCE DESTRUCTION")
            click.echo("\nThis will permanently delete:")
            click.echo("- IAM roles and policies")
            click.echo("- S3 terraform state bucket")
            click.echo("- DynamoDB state lock table")
            click.echo("\nThis action is irreversible!")

            if not click.confirm("\nAre you sure you want to proceed?"):
                print_info("Operation cancelled.")
                return

        result = service.destroy_infrastructure("aws", region, profile)

        if result["success"]:
            print_success("Destruction completed successfully")

            destroyed = result.get("destroyed_resources", [])
            if destroyed:
                click.echo("\nDestroyed resources:")
                for resource in destroyed:
                    click.echo(f"  • {resource}")
        else:
            print_error("Destruction failed", result.get("error"))

    except Exception as e:
        print_error(f"Unexpected error: {e}")


@aws.command("bootstrap")
@click.option("--region", "-r", help="AWS region")
@click.option("--profile", "-p", help="AWS profile")
def bootstrap(region: Optional[str], profile: Optional[str]):
    """Bootstrap foundational AWS infrastructure."""
    try:
        final_region, final_profile = _get_aws_config(region, profile)

        service = TerraformService()
        result = service.bootstrap_infrastructure("aws", final_region, final_profile)

        if result["success"]:
            print_success("AWS infrastructure bootstrapped successfully")

            backend = result.get("backend_config")
            if backend:
                click.echo(f"\nBackend: s3://{backend.get('bucket')}")
                click.echo(f"Region: {backend.get('region')}")
                click.echo(f"Lock Table: {backend.get('dynamodb_table')}")
        else:
            print_error("Bootstrap failed", result.get("error"))

    except Exception as e:
        print_error(f"Unexpected error: {e}")


@aws.command("status")
def status():
    """Show AWS infrastructure status."""
    try:
        region, profile = _get_aws_config()
        service = TerraformService()

        click.echo("\n📊 AWS Infrastructure Status")
        click.echo(f"Region: {region}")
        click.echo(f"Profile: {profile or 'default'}")

        result = service.list_resources("aws", region, profile)
        if result["success"]:
            total = result["total_count"]
            click.echo(f"Managed Resources: {total}")

            if total > 0:
                by_type = {}
                for resource in result["resources"]:
                    rtype = resource["resource_type"]
                    by_type[rtype] = by_type.get(rtype, 0) + 1

                for rtype, count in by_type.items():
                    click.echo(f"  {rtype}: {count}")
        else:
            print_warning("Could not retrieve resource information")

    except Exception as e:
        print_error(f"Unexpected error: {e}")
