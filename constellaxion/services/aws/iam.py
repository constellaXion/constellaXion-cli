import json

import boto3
from botocore.exceptions import ClientError

ROLE_NAME = "constellaxion-admin"
POLICIES = [
    "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess",
]


def get_current_user_arn():
    """Get the ARN of the currently authenticated IAM user."""
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        return identity["Arn"]
    except ClientError as e:
        print(
            "Error: Could not determine the current user. Are you logged in with AWS CLI?"
        )
        print(f"Details: {e}")
        raise


def add_inline_ecr_policy(iam_client):
    """Adds an inline ECR access policy to the Constellaxion IAM role."""
    ecr_inline_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                ],
                "Resource": "*",
            }
        ],
    }

    try:
        iam_client.put_role_policy(
            RoleName=ROLE_NAME,
            PolicyName="ConstellaxionECRAccess",
            PolicyDocument=json.dumps(ecr_inline_policy),
        )
        print("Inline ECR access policy attached to role.")
    except ClientError as e:
        print(f"Failed to attach inline policy: {e}")
        raise


def create_iam_role():
    """Create the Constellaxion IAM role with proper trust and attach policies."""
    iam = boto3.client("iam")

    assume_role_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": ["sagemaker.amazonaws.com", "ecs-tasks.amazonaws.com"]
                },
                "Action": "sts:AssumeRole",
            }
        ],
    }

    try:
        iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
            Description="Constellaxion Admin Role for deploying and training models",
        )
        print(f"Role '{ROLE_NAME}' created successfully.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            print(f"Role '{ROLE_NAME}' already exists. Continuing...")
        else:
            raise

    for policy_arn in POLICIES:
        try:
            iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn=policy_arn)
            print(f"Attached policy: {policy_arn}")
        except ClientError as e:
            print(f"Failed to attach policy {policy_arn}: {e}")
            raise

    # Attach inline ECR policy
    add_inline_ecr_policy(iam)


def create_aws_permissions():
    """Creates the Constellaxion IAM role and attaches necessary policies."""
    try:
        user_arn = get_current_user_arn()
        print(f"Authenticated as: {user_arn}")
        create_iam_role()
        print("IAM initialization complete.")
    except Exception as e:
        print(f"Initialization failed: {e}")
