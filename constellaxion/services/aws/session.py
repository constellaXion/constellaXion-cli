import boto3
from botocore.exceptions import NoCredentialsError, ProfileNotFound


def create_aws_session(profile_name=None, region=None):
    """Create boto3 session with optional profile support."""
    try:
        kwargs = {}
        if profile_name:
            kwargs["profile_name"] = profile_name
        if region:
            kwargs["region_name"] = region

        session = boto3.Session(**kwargs)

        session.client("sts").get_caller_identity()

        return session

    except ProfileNotFound:
        available = boto3.Session().available_profiles
        raise ValueError(
            f"AWS profile '{profile_name}' not found. Available: {available}"
        )
    except NoCredentialsError:
        raise ValueError(
            "No AWS credentials found. Run 'aws configure' or set environment variables."
        )
