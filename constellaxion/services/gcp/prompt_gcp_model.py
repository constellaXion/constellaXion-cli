from google.cloud import aiplatform


def send_gcp_prompt(prompt: str, endpoint_path: str, location: str):
    """Sends a request to a Vertex AI endpoint and returns the response."""
    # The AI Platform services require regional API endpoints.
    client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
    # Initialize Vertex AI client
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)

    instances = [{"prompt": prompt}]

    # Make prediction request
    request = {
        "endpoint": endpoint_path,
        "instances": instances,
    }

    response = client.predict(**request)

    return response.predictions[0]["prediction"]
