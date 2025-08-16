from typing import Any, Dict

import click
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from constellaxion.handlers.cloud_job import AWSDeployJob, GCPDeployJob
from constellaxion.utils import get_job


def prompt_model(prompt: str):
    """
    Prompt the model.
    """
    config = get_job()
    cloud_providers = {"aws": AWSDeployJob, "gcp": GCPDeployJob}
    provider = config.get("deploy", {}).get("provider", None)
    region = config.get("deploy", {}).get("region", None)
    is_foundation_model = True if config.get("training") is None else False
    if provider in cloud_providers:
        job = cloud_providers[provider]()
        return job.prompt(prompt, config, region, is_foundation_model)
    return None


def prompt_streaming_server_app():
    """
    Create the FastAPI application.
    """
    app = FastAPI()

    # Add CORS middleware with explicit configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,  # Allow credentials (cookies, authorization headers)
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
        expose_headers=["*"],  # Expose all headers
        max_age=3600,  # Cache preflight requests for 1 hour
    )

    @app.post("/prompt")
    async def handle_prompt(request: Request):
        """
        Handle prompt requests.
        """
        try:
            # Get the prompt from the request
            data = await request.json()
            prompt = data.get("prompt", "")
            response = prompt_model(prompt)

            # Create a streaming response
            async def stream_response():
                if hasattr(response, "read"):
                    # If response is a file-like object
                    buffer = ""
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        if isinstance(chunk, bytes):
                            chunk = chunk.decode("utf-8")
                        buffer += chunk
                        # Process complete SSE events
                        while "\n\n" in buffer:
                            event, buffer = buffer.split("\n\n", 1)
                            if event.startswith("data: "):
                                # Clean up the event data
                                data = event[
                                    6:
                                ].strip()  # Remove 'data: ' prefix and whitespace
                                if data and not data.endswith(
                                    ","
                                ):  # Skip empty events and trailing commas
                                    yield f"data: {data}\n\n".encode("utf-8")
                else:
                    # If response is a string or bytes
                    if isinstance(response, bytes):
                        response_text = response.decode("utf-8")
                    else:
                        response_text = response
                    # Process the response as SSE events
                    for line in response_text.split("\n"):
                        if line.startswith("data: "):
                            data = line[
                                6:
                            ].strip()  # Remove 'data: ' prefix and whitespace
                            if data and not data.endswith(
                                ","
                            ):  # Skip empty events and trailing commas
                                yield f"data: {data}\n\n".encode("utf-8")

            return StreamingResponse(
                stream_response(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                },
            )
        except Exception as e:
            click.echo(
                click.style(f"Error handling prompt request: {str(e)}", fg="red")
            )
            raise

    return app


def prompt_server_app():
    """
    Create the FastAPI application for handling JSON responses.
    """
    app = FastAPI()

    # Add CORS middleware with explicit configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,  # Allow credentials (cookies, authorization headers)
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
        expose_headers=["*"],  # Expose all headers
        max_age=3600,  # Cache preflight requests for 1 hour
    )

    @app.post("/prompt")
    async def handle_prompt(request: Request) -> Dict[str, Any]:
        """
        Handle prompt requests and return JSON responses.
        """
        try:
            # Get the prompt from the request
            data = await request.json()
            prompt = data.get("prompt", "")
            response = prompt_model(prompt)
            if isinstance(response, dict):
                response_text = response.get("prediction", str(response))
            elif hasattr(response, "read"):
                response_text = response.read().decode("utf-8")
            elif isinstance(response, bytes):
                response_text = response.decode("utf-8")
            else:
                response_text = str(response)
            return {
                "status": "success",
                "response": response_text.strip(),
                "prompt": prompt,
                "provider": get_job().get("deploy", {}).get("provider", "unknown"),
            }
        except Exception as e:
            click.echo(
                click.style(f"Error handling prompt request: {str(e)}", fg="red")
            )
            return {
                "status": "error",
                "error": str(e),
                "prompt": prompt,
                "provider": get_job().get("deploy", {}).get("provider", "unknown"),
            }

    return app
