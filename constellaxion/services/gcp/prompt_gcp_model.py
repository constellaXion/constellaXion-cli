import requests

def send_gcp_prompt(prompt: str, endpoint_path: str):
    """Sends a request to a Cloud Run service endpoint and returns the response."""

    # Send POST request to the /predict endpoint
    response = requests.post(
        f"{endpoint_path}/predict",
        json={"instances": [{"prompt": prompt}]},
        headers={"Content-Type": "application/json"},
        # stream=True
    )
    response.raise_for_status()
    return response.json()["predictions"][0]["response"]
