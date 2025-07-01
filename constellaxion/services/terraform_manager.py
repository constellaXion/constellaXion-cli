import os
import sys
import platform
import subprocess
import json
import requests
import zipfile
import shutil
import pkg_resources
from pathlib import Path
from tqdm import tqdm
from typing import Dict, Optional
import click

TERRAFORM_VERSION = "1.8.0"

class TerraformExecutionError(Exception):
    def __init__(self, message, stdout, stderr, returncode):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

class TerraformLayer:
    """Represents a single, initialized Terraform layer workspace."""
    def __init__(self, manager: 'TerraformManager', layer_name: str, backend_config: Optional[Dict] = None, aws_profile: Optional[str] = None):
        self.manager = manager
        self.layer_name = layer_name
        self.aws_profile = aws_profile
        self.workspace_dir = self.manager.workspace_dir / self.layer_name.replace('/', '_')

        self._prepare_workspace()

        if backend_config:
            self._generate_backend_tf(backend_config)

        # We can now remove -migrate-state as the workspace is always clean.
        self._run_command(['init'])

    def _prepare_workspace(self):
        source_dir = self.manager.layers_source_root / self.layer_name
        if not source_dir.is_dir():
            raise FileNotFoundError(f"Terraform source directory not found at: {source_dir}")

        # --- KEY CHANGE 1: Always start with a clean workspace for each run ---
        # This prevents any old state or backend configs from interfering.
        if self.workspace_dir.exists():
            shutil.rmtree(self.workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        # --- END KEY CHANGE 1 ---
        
        for item in source_dir.iterdir():
            if item.is_file() and item.name.endswith('.tf'):
                shutil.copy(item, self.workspace_dir)

    def destroy(self, tf_vars: dict):
        """
        Destroys all resources managed by this layer.
        This is a destructive operation.
        """
        vars_file_path = self.workspace_dir / 'terraform.tfvars.json'
        with open(vars_file_path, 'w') as f:
            json.dump(tf_vars, f)
        
        try:
            self._run_command(['destroy', '-auto-approve'])
        finally:
            if vars_file_path.exists():
                vars_file_path.unlink()

    def _generate_backend_tf(self, backend_config: Dict):
        """Generates a backend.tf file for remote state configuration."""
        bucket = backend_config.get("bucket")
        key = backend_config.get("key")
        region = backend_config.get("region")
        dynamodb_table = backend_config.get("dynamodb_table")
        if not all([bucket, key, region]):
            raise ValueError("Backend config requires 'bucket', 'key', and 'region'.")

        # --- THIS IS THE FINAL FIX ---
        # The key is to ensure the final closing braces are on new lines.
        content = f'''
terraform {{
  backend "s3" {{
    bucket         = "{bucket}"
    key            = "{key}"
    region         = "{region}"
'''
        if dynamodb_table:
            content += f'    dynamodb_table = "{dynamodb_table}"\n'
        
        # This structure ensures a newline before each closing brace.
        content += '''  }
}
'''
        # --- END FIX ---
        
        with open(self.workspace_dir / "_backend.tf", "w") as f:
            f.write(content)
        click.echo(f"Configured S3 backend in bucket '{bucket}' with key '{key}'.")
    def _run_command(self, command: list, capture_json_output=False):
        """A wrapper to call the manager's run command with the correct context."""
        return self.manager._run_command(command, self.workspace_dir, self.aws_profile, capture_json_output)

    def list_state(self) -> list[str]:
        """Lists all resources currently managed in the state for this layer."""
        try:
            process = self._run_command(['state', 'list'])
            return [line.strip() for line in process.stdout.strip().split('\n') if line.strip()]
        except TerraformExecutionError as e:
            if "No resources found in the state" in e.stdout or not e.stdout.strip():
                return []
            raise e

    def import_resource(self, tf_vars: dict, resource_address: str, resource_id: str):
        """Imports an existing resource into this layer's state."""
        click.echo(f"Attempting to import {resource_id} into {resource_address}...")
        vars_file_path = self.workspace_dir / 'terraform.tfvars.json'
        with open(vars_file_path, 'w') as f:
            json.dump(tf_vars, f)
        
        try:
            self._run_command(['import', f'-var-file={vars_file_path.name}', resource_address, resource_id])
        except TerraformExecutionError as e:
            if "already in state" in e.stdout:
                click.echo(click.style(f"Resource {resource_address} is already managed by Terraform. No import needed.", fg="green"))
            else:
                raise e
        finally:
            if vars_file_path.exists():
                vars_file_path.unlink()

    def apply(self, tf_vars: dict) -> dict:
        """Applies the configuration for this layer and returns the outputs."""
        vars_file_path = self.workspace_dir / 'terraform.tfvars.json'
        with open(vars_file_path, 'w') as f:
            json.dump(tf_vars, f)
        
        try:
            self._run_command(['apply', '-auto-approve'])
            output_process = self._run_command(['output', '-json'], capture_json_output=True)
            return json.loads(output_process.stdout)
        finally:
            if vars_file_path.exists():
                vars_file_path.unlink()


class TerraformManager:
    def __init__(self, platform: str, workspace_dir: Path):
        if platform not in ['aws', 'gcp']:
            raise ValueError("Platform must be 'aws' or 'gcp'.")
        
        self.platform = platform
        self.workspace_dir = workspace_dir / self.platform
        self.binary_path = self._get_or_download_terraform()
        self.layers_source_root = self._get_layers_source_path()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def get_layer(self, layer_name: str, backend_config: Optional[Dict] = None, aws_profile: Optional[str] = None) -> TerraformLayer:
        """
        Gets a fully initialized and ready-to-use TerraformLayer object.
        The initialization (`init`) is done when the object is created.
        """
        return TerraformLayer(self, layer_name, backend_config, aws_profile)

    def _run_command(self, command: list, cwd: Path, aws_profile: Optional[str] = None, capture_json_output=False):
        """
        Internal method to execute Terraform commands. It can either stream output
        or capture it, depending on the need.
        """
        full_command = [str(self.binary_path)] + command
        env = os.environ.copy()
        if aws_profile:
            env['AWS_PROFILE'] = aws_profile
        
        if capture_json_output:
            try:
                process = subprocess.run(
                    full_command, cwd=str(cwd), env=env, capture_output=True, text=True, check=True, encoding='utf-8'
                )
                return process
            except subprocess.CalledProcessError as e:
                raise TerraformExecutionError(f"Terraform command failed: {' '.join(full_command)}", e.stdout, e.stderr, e.returncode)
        else:
            if aws_profile:
                click.echo(f"Terraform is using AWS profile: '{aws_profile}'")
            process = subprocess.Popen(
                full_command, cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8'
            )
            stdout_lines = []
            for line in iter(process.stdout.readline, ''):
                click.echo(line, nl=False)
                stdout_lines.append(line)
            process.stdout.close()
            returncode = process.wait()
            
            if returncode != 0:
                raise TerraformExecutionError(f"Terraform command failed with exit code {returncode}", "".join(stdout_lines), "", returncode)
            
            class DummyProcess:
                stdout = "".join(stdout_lines)
            return DummyProcess

    def _get_layers_source_path(self) -> Path:
        """Finds the path to the bundled Terraform source files within the package."""
        path_str = pkg_resources.resource_filename(
            'constellaxion', f'terraform/{self.platform}/layers'
        )
        return Path(path_str)

    def _get_or_download_terraform(self) -> Path:
        """Checks for a cached Terraform binary or downloads it if not present."""
        cache_dir = Path(self._get_cache_dir())
        binary_name = "terraform.exe" if sys.platform == "win32" else "terraform"
        binary_path = cache_dir / binary_name

        if binary_path.is_file():
            return binary_path

        print(f"First-time setup: downloading Terraform v{TERRAFORM_VERSION}...")
        
        os_name_map = {'darwin': 'darwin', 'linux': 'linux', 'win32': 'windows'}
        arch_map = {'x86_64': 'amd64', 'AMD64': 'amd64', 'aarch64': 'arm64', 'arm64': 'arm64'}
        
        os_name = os_name_map.get(sys.platform)
        arch = arch_map.get(platform.machine())

        if not os_name or not arch:
            raise NotImplementedError(f"Unsupported platform: {sys.platform} {platform.machine()}")

        zip_name = f"terraform_{TERRAFORM_VERSION}_{os_name}_{arch}.zip"
        url = f"https://releases.hashicorp.com/terraform/{TERRAFORM_VERSION}/{zip_name}"
        zip_path = cache_dir / zip_name

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            with open(zip_path, 'wb') as f, tqdm(
                desc=zip_name, total=total_size, unit='iB', unit_scale=True, unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    f.write(data)
                    bar.update(len(data))
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to download Terraform: {e}")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(cache_dir)
        
        if sys.platform != "win32":
            os.chmod(binary_path, 0o755)

        zip_path.unlink()

        print("Terraform download complete.")
        return binary_path
        
    def _get_cache_dir(self) -> str:
        """Determines the appropriate cache directory based on the OS."""
        if sys.platform == "win32":
            path = os.path.join(os.environ["LOCALAPPDATA"], "Constellaxion", "Cache")
        elif sys.platform == "darwin":
            path = os.path.join(os.path.expanduser("~"), "Library", "Caches", "Constellaxion")
        else:
            path = os.path.join(os.path.expanduser("~"), ".cache", "constellaxion")
        
        os.makedirs(path, exist_ok=True)
        return path