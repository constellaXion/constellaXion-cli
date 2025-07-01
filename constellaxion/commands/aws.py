import click
from rich.console import Console
from rich.table import Table
from typing import Optional
from botocore.exceptions import ClientError
import shutil
import os
import json

from constellaxion.services.aws.session import create_aws_session
from constellaxion.services.terraform_manager import TerraformManager
from constellaxion.utils import get_job

# Initialize Rich Console for beautiful output
console = Console()

@click.group()
def aws():
    """Commands for managing AWS foundational resources."""
    pass

def get_aws_config_from_context() -> (Optional[str], Optional[str]):
    """
    Attempts to get AWS profile and region from job.json,
    otherwise prompts the user.
    """
    config = get_job(show=False, fail_silently=True)
    profile = None
    region = None

    if config and config.get("deploy", {}).get("provider") == "aws":
        deploy_config = config["deploy"]
        profile = deploy_config.get("profile")
        region = deploy_config.get("region")
        click.echo(f"Using configuration from local job.json (Profile: {profile or 'default'}, Region: {region}).")
    
    if not region:
        region = click.prompt(
            "Please enter the AWS region to check",
        )
    if not profile:
        profile_input = click.prompt(
            "Please enter the AWS profile to use (leave blank for default)",
            default="",
            show_default=False,
        )
        profile = profile_input if profile_input else None

    return profile, region

@aws.command("list-resources")
def list_resources():
    """
    Lists all foundational AWS resources managed by Constellaxion.

    This command checks for the real-world existence of the backend resources
    and inspects the remote Terraform state for all other resources.
    """
    profile, region = get_aws_config_from_context()
    
    click.echo(f"\nScanning for resources in region '{region}' using profile '{profile or 'default'}'...")

    try:
        table = Table(title="Constellaxion Managed AWS Resources", show_header=True, header_style="bold magenta")
        table.add_column("Resource Type", style="dim", width=40)
        table.add_column("Name / Terraform Address", style="cyan")
        table.add_column("Status", style="green")

        # --- Part 1: Check for foundational resources via AWS API ---
        table.add_section()
        table.add_row("[bold]Terraform Backend[/bold]", "", "")
        
        session = create_aws_session(profile, region)
        account_id = session.client("sts").get_caller_identity()["Account"]
        s3_client = session.client("s3")
        dynamodb_client = session.client("dynamodb")
        
        bucket_name = f"constellaxion-tf-state-{account_id}-{region}"
        dynamo_table_name = f"{bucket_name}-locks"

        try:
            s3_client.head_bucket(Bucket=bucket_name)
            table.add_row("S3 Bucket", bucket_name, "✅ Found")
        except ClientError:
            table.add_row("S3 Bucket", bucket_name, "[yellow]Not Found[/yellow]")

        try:
            dynamodb_client.describe_table(TableName=dynamo_table_name)
            table.add_row("DynamoDB Lock Table", dynamo_table_name, "✅ Found")
        except ClientError:
            table.add_row("DynamoDB Lock Table", dynamo_table_name, "[yellow]Not Found[/yellow]")

        # --- Part 2: List resources from the remote IAM state file ---
        table.add_section()
        table.add_row("[bold]IAM & Permissions (from remote state)[/bold]", "", "")

        from pathlib import Path
        PROJECT_CONFIG_DIR = Path.home() / ".constellaxion"
        tf_manager = TerraformManager(platform="aws", workspace_dir=PROJECT_CONFIG_DIR / "tf_workspaces")
        
        remote_backend_config = {
            "bucket": bucket_name,
            "region": region,
            "dynamodb_table": dynamo_table_name,
            "key": "iam/terraform.tfstate"
        }

        iam_layer = tf_manager.get_layer(
            layer_name='basic/01-iam',
            backend_config=remote_backend_config,
            aws_profile=profile
        )
        iam_resources = iam_layer.list_state()

        if not iam_resources:
            table.add_row("No IAM resources found in state.", "", "")
        else:
            for resource in iam_resources:
                resource_type = resource.split('.')[0]
                table.add_row(resource_type, resource, "✅ Managed in State")

        console.print(table)

    except Exception as e:
        console.print(f"\n[bold red]Error listing resources:[/bold red] {e}")


@aws.command("destroy")
@click.option('--yes', '-y', is_flag=True, help="Bypass interactive confirmation and proceed with destruction.")
def destroy(yes: bool):
    """
    Destroys ALL foundational AWS resources managed by Constellaxion.

    This is a DESTRUCTIVE operation and will delete the IAM roles, S3 backend
    bucket, and DynamoDB lock table. This cannot be undone.
    """
    profile, region = get_aws_config_from_context()
    
    if not yes:
        console.print("\n[bold red]⚠️  DANGER ZONE: RESOURCE DESTRUCTION ⚠️[/bold red]")
        console.print("This command will permanently delete all foundational infrastructure, including:")
        console.print("- The 'constellaxion-admin' IAM role and its policies.")
        console.print("- The S3 bucket holding all Terraform state files.")
        console.print("- The DynamoDB table used for state locking.")
        console.print("\nThis action is irreversible and will affect all projects using this AWS account/region.\n")

    try:
        session = create_aws_session(profile, region)
        account_id = session.client("sts").get_caller_identity()["Account"]
        s3_client = session.client("s3")

        bucket_name = f"constellaxion-tf-state-{account_id}-{region}"

        if not yes:
            # Safety check: make the user type the bucket name to confirm.
            confirmation = click.prompt(
                f"To proceed, please type the full name of the S3 backend bucket: [cyan]{bucket_name}[/cyan]"
            )

            if confirmation != bucket_name:
                console.print("[bold red]Confirmation failed. Aborting destruction.[/bold red]")
                return
        else:
            console.print(f"[yellow]--yes flag provided. Bypassing confirmation for bucket: {bucket_name}[/yellow]")

        console.print("\n[yellow]Proceeding with destruction...[/yellow]")
        
        from pathlib import Path
        PROJECT_CONFIG_DIR = Path.home() / ".constellaxion"
        tf_manager = TerraformManager(platform="aws", workspace_dir=PROJECT_CONFIG_DIR / "tf_workspaces")

        # 1. Discover all state files in the S3 bucket
        click.echo(f"Listing all state files in bucket '{bucket_name}'...")
        all_state_keys = []
        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)
            for page in pages:
                for obj in page.get('Contents', []):
                    if obj['Key'].endswith('terraform.tfstate'):
                        all_state_keys.append(obj['Key'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                click.echo(f"Backend bucket '{bucket_name}' does not exist. Nothing to destroy from remote state.")
                all_state_keys = []
            else:
                raise

        # 2. Destroy resources for each remote state file
        for state_key in all_state_keys:
            layer_name = None
            if "iam/terraform.tfstate" in state_key:
                layer_name = "basic/01-iam"
            else:
                click.echo(f"[yellow]Skipping unknown state file: {state_key}[/yellow]")
                continue

            click.echo(f"\nDestroying resources for layer '{layer_name}' (state: s3://{bucket_name}/{state_key})...")
            
            layer_backend_config = {
                "bucket": bucket_name,
                "region": region,
                "dynamodb_table": f"{bucket_name}-locks",
                "key": state_key
            }
            
            layer_to_destroy = tf_manager.get_layer(
                layer_name=layer_name,
                backend_config=layer_backend_config,
                aws_profile=profile
            )
            layer_to_destroy.destroy(tf_vars={"region": region})

        # 3. Destroy the backend infrastructure itself (using its local state)
        click.echo(f"\nDestroying the backend infrastructure (bucket and lock table)...")
        backend_layer = tf_manager.get_layer(
            layer_name='basic/00-backend',
            aws_profile=profile
        )
        # We must provide all variables required by the terraform config.
        backend_layer.destroy(tf_vars={"region": region, "bucket_name": bucket_name, "enable_dynamodb_locking": True})

        # 4. Clean up local workspaces
        click.echo("\nCleaning up local workspaces...")
        workspace_path = PROJECT_CONFIG_DIR / "tf_workspaces" / "aws"
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
            click.echo(f"Removed local workspace: {workspace_path}")
            
        # 5. Clean up the local job.json file
        click.echo("\nUpdating local job.json...")
        job_file_path = "job.json"
        if os.path.exists(job_file_path):
            try:
                with open(job_file_path, "r") as f:
                    job_config = json.load(f)
                
                if "terraform_backend" in job_config.get("deploy", {}):
                    del job_config["deploy"]["terraform_backend"]
                    
                    with open(job_file_path, "w") as f:
                        json.dump(job_config, f, indent=4)
                    console.print(f"[green]✅ Removed 'terraform_backend' section from '{job_file_path}'.[/green]")
                else:
                    click.echo(f"No 'terraform_backend' section found in '{job_file_path}'. Nothing to do.")

            except (json.JSONDecodeError, IOError) as e:
                console.print(f"[yellow]Warning: Could not read or update '{job_file_path}': {e}[/yellow]")
        else:
            click.echo("No local job.json found to update.")

        console.print("\n[bold green]✅ Destruction complete. System is reset.[/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]An error occurred during destruction:[/bold red] {e}")