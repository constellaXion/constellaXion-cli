import multiprocessing
import os
import webbrowser

import pkg_resources
import uvicorn

from constellaxion.ui.server.prompt_server import prompt_server_app
from constellaxion.ui.server.ui_server import ui_server_app


def run_ui_server(ui_directory: str, port: int):
    """
    Launch the UI server.
    """
    os.chdir(ui_directory)
    app = ui_server_app()
    webbrowser.open(f"http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port)


def run_prompt_server(port: int = 8001):
    """
    Launch the prompt server.
    """
    app = prompt_server_app()
    uvicorn.run(app, host="127.0.0.1", port=port)


class PromptManager:
    """
    Manage the prompt.
    """

    def run(self):
        """
        Serve a static UI from a given directory.

        Args:
            directory (str): The directory containing the static files to serve.
            port (int): The port to serve the UI on.
        """
        # Get UI directory and ports
        static_file_dir = pkg_resources.resource_filename("constellaxion", "ui/prompts")
        browser_port = 9000
        api_port = browser_port + 1  # API server runs on next port

        # Start static file server in a separate process
        static_process = multiprocessing.Process(
            target=run_ui_server, args=(static_file_dir, browser_port)
        )
        static_process.start()

        # Start API server in a separate process
        api_process = multiprocessing.Process(
            target=run_prompt_server, args=(api_port,)
        )
        api_process.start()

        # Wait for both processes
        static_process.join()
        api_process.join()
