from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import click
from pathlib import Path


def ui_server_app():
    """
    Create the FastAPI application for serving the UI.
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

    # Get the current directory
    static_dir = Path(os.getcwd())
    # Mount the static directory
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def serve_index():
        """
        Serve the index.html file.
        """
        try:
            index_path = static_dir / "index.html"
            if not index_path.exists():
                raise FileNotFoundError("index.html not found")
            return FileResponse(str(index_path))
        except Exception as e:
            click.echo(click.style(f"Error serving index.html: {str(e)}", fg="red"))
            return HTMLResponse(
                content="<h1>Error</h1><p>Failed to load the application.</p>",
                status_code=500
            )

    @app.get("/{path:path}")
    async def serve_static(path: str):
        """
        Serve static files.
        """
        try:
            file_path = static_dir / path
            if not file_path.exists():
                # If file doesn't exist, serve index.html for SPA routing
                return await serve_index()
            return FileResponse(str(file_path))
        except Exception as e:
            click.echo(click.style(f"Error serving static file {path}: {str(e)}", fg="red"))
            return HTMLResponse(
                content=f"<h1>Error</h1><p>Failed to load {path}</p>",
                status_code=500
            )

    return app
