"""Module for sending prompts to SageMaker endpoints and receiving responses."""
import json
import logging
import boto3
from constellaxion.utils import suppress_logs_and_warnings

# # Suppress everything below CRITICAL globally
# logging.basicConfig(level=logging.CRITICAL)

# logging.getLogger('sagemaker.djl_inference.model').setLevel(logging.CRITICAL)
# logging.getLogger('sagemaker.config').setLevel(logging.CRITICAL)
# logging.getLogger('boto3').setLevel(logging.CRITICAL)
# logging.getLogger('botocore').setLevel(logging.CRITICAL)
# logging.getLogger('pydantic').setLevel(logging.CRITICAL)

def send_aws_prompt(prompt: str, endpoint_name: str, region: str):
    """Sends a request to a SageMaker endpoint and returns the response."""
    try:
        with suppress_logs_and_warnings():
            sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=region)
            body = bytes(f'{{"inputs": "{prompt}"}}', 'utf-8')
            response = sagemaker_runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                Body=body,
                ContentType='application/json'
            )
            payload = response['Body'].read().decode('utf-8')
            text = json.loads(payload)['generated_text']
    except (boto3.exceptions.Boto3Error, json.JSONDecodeError, KeyError) as e:
        print(f"Error sending prompt to SageMaker endpoint: {e}")
        return None

    return text
