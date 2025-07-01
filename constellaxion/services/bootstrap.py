import click
from typing import Optional, Dict
from botocore.exceptions import ClientError
from pathlib import Path

from constellaxion.services.terraform_manager import TerraformManager
from constellaxion.services.aws.session import create_aws_session

def bootstrap_aws_infrastructure(profile: Optional[str], region: str) -> Dict:
    click.echo(click.style("🚀 Verifying foundational AWS infrastructure...", fg="cyan"))
    PROJECT_CONFIG_DIR = Path.home() / ".constellaxion"
    tf_manager = TerraformManager(platform="aws", workspace_dir=PROJECT_CONFIG_DIR / "tf_workspaces")

    # --- Step 1: Backend Setup ---
    try:
        session = create_aws_session(profile, region)
        account_id = session.client("sts").get_caller_identity()["Account"]
        s3_client = session.client("s3")
        dynamodb_client = session.client("dynamodb")
        
        backend_name_prefix = f"constellaxion-tf-state-{account_id}-{region}"
        bucket_name = backend_name_prefix
        dynamo_table_name = f"{backend_name_prefix}-locks"
        
        backend_config = {"bucket": bucket_name, "region": region, "dynamodb_table": dynamo_table_name}
        
        bucket_exists = False
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            bucket_exists = True
        except ClientError as e:
            if e.response['Error']['Code'] != '404': raise e

        dynamo_table_exists = False
        try:
            dynamodb_client.describe_table(TableName=dynamo_table_name)
            dynamo_table_exists = True
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException': raise e

        if not bucket_exists or not dynamo_table_exists:
            click.echo("Foundational resources are incomplete. Running Terraform to create/update...")
            # Get the backend layer object (this runs init)
            backend_layer = tf_manager.get_layer(layer_name='basic/00-backend', aws_profile=profile)
            # Apply the changes
            backend_layer.apply(tf_vars={"region": region, "bucket_name": bucket_name, "enable_dynamodb_locking": True})
        else:
            click.echo(click.style(f"✅ Found existing state bucket and lock table.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"❌ Error during backend setup: {e}", fg="red"), err=True)
        raise

    # --- Step 2: Apply the IAM layer ---
    click.echo("\nVerifying IAM permissions layer...")
    try:
        session = create_aws_session(profile, region)
        iam_client = session.client('iam')
        role_name = 'constellaxion-admin'
        resource_address = 'aws_iam_role.constellaxion_admin'
        
        iam_backend_config = backend_config.copy()
        iam_backend_config["key"] = "iam/terraform.tfstate"
        
        # Get the IAM layer object (this runs init with the S3 backend)
        iam_layer = tf_manager.get_layer(
            layer_name='basic/01-iam',
            backend_config=iam_backend_config,
            aws_profile=profile
        )

        role_exists_in_aws = False
        try:
            iam_client.get_role(RoleName=role_name)
            role_exists_in_aws = True
        except iam_client.exceptions.NoSuchEntityException:
            pass

        role_in_state = resource_address in iam_layer.list_state()

        if role_exists_in_aws and not role_in_state:
            click.echo(f"Role '{role_name}' exists but is not managed by Terraform. Importing it...")
            iam_layer.import_resource(tf_vars={"region": region}, resource_address=resource_address, resource_id=role_name)

        click.echo("Applying IAM configuration to ensure consistency...")
        iam_outputs = iam_layer.apply(tf_vars={"region": region})
        
        output_role_name = iam_outputs['iam_role_name']['value']
        click.echo(click.style(f"✅ IAM role '{output_role_name}' is configured correctly.", fg="green"))
        
    except Exception as e:
        click.echo(click.style(f"❌ Error applying IAM layer: {e}", fg="red"), err=True)
        raise
    
    click.echo(click.style("🎉 AWS foundation is ready.", fg="green", bold=True))
    return backend_config