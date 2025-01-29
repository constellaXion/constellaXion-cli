from google.cloud import aiplatform
import json

# Configuration
PROJECT_ID = "your-gcp-project-id"
REGION = "us-central1"  # Change to your region
ENDPOINT_ID = "your-endpoint-id"  # The ID of the deployed endpoint
# Modify based on your model input
INSTANCE_INPUT = {"input_text": "Hello, how are you?"}
# Optional: Use if multiple models are deployed on the endpoint
DEPLOYED_MODEL_ID = None


def query_vertex_ai_endpoint(project_id, region, endpoint_id, instance, deployed_model_id=None):
    """Sends a request to a Vertex AI endpoint and returns the response."""
    # Initialize Vertex AI client
    client = aiplatform.gapic.PredictionServiceClient()

    # Format the endpoint path
    endpoint_path = client.endpoint_path(
        project=project_id,
        location=region,
        endpoint=endpoint_id
    )

    # Format the instance as a list
    # Ensures correct JSON format
    instances = [json.loads(json.dumps(instance))]

    # Make prediction request
    request = {
        "endpoint": endpoint_path,
        "instances": instances,
    }

    if deployed_model_id:
        request["deployed_model_id"] = deployed_model_id

    response = client.predict(**request)

    return response.predictions


if __name__ == "__main__":
    predictions = query_vertex_ai_endpoint(
        PROJECT_ID, REGION, ENDPOINT_ID, INSTANCE_INPUT, DEPLOYED_MODEL_ID)
    print("Predictions:", predictions)
