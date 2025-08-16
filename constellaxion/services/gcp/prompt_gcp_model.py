from google.cloud import aiplatform
import requests


def send_gcp_prompt(
    prompt: str, endpoint_path: str, region: str, is_foundation_model: bool = False
):
    """Sends a request to a Cloud Run service endpoint and returns the response."""
    if is_foundation_model:
        return send_gcp_prompt_with_endpoint_path(prompt, endpoint_path, region)

    # Send POST request to the /predict endpoint
    response = requests.post(
        f"{endpoint_path}/predict",
        json={"instances": [{"prompt": prompt}]},
        headers={"Content-Type": "application/json"},
        timeout=60,  # 60 second timeout to prevent hanging requests
        # stream=True
    )
    response.raise_for_status()
    return response.json()["predictions"][0]["response"]


def send_gcp_prompt_with_endpoint_path(prompt: str, endpoint_path: str, region: str):
    """An intermediary method for handling requests to Vertex AI while we transition to Cloud Run.
    Sends a request to a Vertex AI endpoint and returns the response.
    """
    client_options = {"api_endpoint": f"{region}-aiplatform.googleapis.com"}
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)

    # Make a prediction request
    response = client.predict(
        endpoint=endpoint_path,
        instances=[{"prompt": prompt}],
    )
    return response.predictions[0]["prediction"]
