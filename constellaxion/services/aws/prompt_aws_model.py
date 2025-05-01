"""Module for sending prompts to SageMaker endpoints and receiving responses."""
import boto3
import json
def send_aws_prompt(prompt: str, endpoint_name: str, region: str):
    """Sends a request to a SageMaker endpoint and returns the response."""
    sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=region)
    body = bytes(f'{{"inputs": "{prompt}"}}', 'utf-8')
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        Body=body,
        ContentType='application/json'
    )
    payload = response['Body'].read().decode('utf-8')
    text = json.loads(payload)['generated_text']

    return text