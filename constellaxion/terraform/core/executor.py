import os
from pathlib import Path
import subprocess  # nosec: B404 - Used for legitimate Terraform CLI operations with proper validation
from typing import Any, Dict, List, Optional

import click

from constellaxion.terraform.core.binary import TerraformBinary
from constellaxion.terraform.core.result import TerraformResult


class TerraformExecutor:
    """Handles terraform command execution."""

    def __init__(self, binary: TerraformBinary) -> None:
        """Initialize terraform command executor."""
        self.binary = binary

    def _validate_command(self, command: List[str]) -> None:
        """Validate terraform command to prevent command injection."""
        # Only allow valid terraform subcommands
        valid_commands = {
            "init", "apply", "destroy", "refresh", "output", "state", "plan", "validate",
            "workspace", "import", "taint", "untaint", "force-unlock", "console"
        }
        
        # Check if the first command is a valid terraform subcommand
        if command and command[0] not in valid_commands:
            raise ValueError(f"Invalid terraform command: {command[0]}. Allowed commands: {', '.join(valid_commands)}")
        
        # Validate that no command contains shell metacharacters
        for arg in command:
            if any(char in arg for char in [';', '&', '|', '>', '<', '`', '$', '(', ')', '{', '}', '[', ']', '\\', '"', "'"]):
                raise ValueError(f"Command argument contains invalid characters: {arg}")

    def _validate_working_dir(self, working_dir: Path) -> None:
        """Validate working directory path for security."""
        # Ensure working directory is absolute and doesn't contain path traversal
        working_dir = working_dir.resolve()
        if ".." in str(working_dir) or working_dir.is_symlink():
            raise ValueError(f"Invalid working directory path: {working_dir}")
        
        # Ensure the directory exists and is accessible
        if not working_dir.exists():
            raise FileNotFoundError(f"Working directory does not exist: {working_dir}")
        if not working_dir.is_dir():
            raise ValueError(f"Working directory is not a directory: {working_dir}")

    def _validate_env_vars(self, env_vars: Optional[Dict[str, str]]) -> None:
        """Validate environment variables for security."""
        if env_vars:
            for key, value in env_vars.items():
                # Validate key names (no shell metacharacters)
                if any(char in key for char in [';', '&', '|', '>', '<', '`', '$', '(', ')', '{', '}', '[', ']', '\\', '"', "'"]):
                    raise ValueError(f"Environment variable key contains invalid characters: {key}")
                # Validate values (no shell metacharacters)
                if any(char in value for char in [';', '&', '|', '>', '<', '`', '$', '(', ')', '{', '}', '[', ']', '\\', '"', "'"]):
                    raise ValueError(f"Environment variable value contains invalid characters: {value}")

    def execute(
        self,
        command: List[str],
        working_dir: Path,
        env_vars: Optional[Dict[str, str]] = None,
        capture_output: bool = False,
        show_output: bool = True,
    ) -> TerraformResult:
        """Execute a terraform command."""
        # Validate all inputs before execution
        self._validate_working_dir(working_dir)
        self._validate_command(command)
        self._validate_env_vars(env_vars)
        
        full_command = [str(self.binary.get_path())] + command

        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        if capture_output:
            return self._execute_with_capture(full_command, working_dir, env)
        else:
            return self._execute_with_streaming(
                full_command, working_dir, env, show_output
            )

    def init(
        self,
        working_dir: Path,
        backend_config: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> TerraformResult:
        """Run terraform init."""
        command = ["init"]

        if backend_config:
            for key, value in backend_config.items():
                command.extend(["-backend-config", f"{key}={value}"])

        if kwargs.get("upgrade"):
            command.append("-upgrade")
        if kwargs.get("reconfigure"):
            command.append("-reconfigure")

        result = self.execute(command, working_dir)
        return TerraformResult(
            success=result.success,
            message="Init completed" if result.success else "Init failed",
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )

    def apply(
        self, working_dir: Path, var_file: Optional[Path] = None
    ) -> TerraformResult:
        """Run terraform apply."""
        command = ["apply", "-auto-approve"]

        if var_file and var_file.exists():
            command.extend(["-var-file", str(var_file)])

        result = self.execute(command, working_dir)
        return TerraformResult(
            success=result.success,
            message="Apply completed" if result.success else "Apply failed",
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )

    def destroy(
        self, working_dir: Path, var_file: Optional[Path] = None
    ) -> TerraformResult:
        """Run terraform destroy."""
        command = ["destroy", "-auto-approve"]

        if var_file and var_file.exists():
            command.extend(["-var-file", str(var_file)])

        result = self.execute(command, working_dir)
        return TerraformResult(
            success=result.success,
            message="Destroy completed" if result.success else "Destroy failed",
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )

    def refresh(self, working_dir: Path) -> TerraformResult:
        """Run terraform refresh to sync state with remote."""
        result = self.execute(["refresh", "-auto-approve"], working_dir)
        return TerraformResult(
            success=result.success,
            message="Refresh completed" if result.success else "Refresh failed",
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )

    def output(self, working_dir: Path, json_format: bool = True) -> TerraformResult:
        """Get terraform outputs."""
        command = ["output"]
        if json_format:
            command.append("-json")

        result = self.execute(command, working_dir, capture_output=True)
        return TerraformResult(
            success=result.success,
            message="Output retrieved" if result.success else "Output failed",
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )

    def state_list(self, working_dir: Path) -> TerraformResult:
        """List resources in terraform state."""
        result = self.execute(["state", "list"], working_dir, capture_output=True)
        return TerraformResult(
            success=result.success,
            message="State listed" if result.success else "State list failed",
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )

    def _execute_with_capture(
        self, command: List[str], cwd: Path, env: Dict[str, str]
    ) -> TerraformResult:
        """Execute command and capture output."""
        try:
            # Command is validated above to prevent injection attacks
            process = subprocess.run(
                command,
                cwd=str(cwd),
                env=env,
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                timeout=1800,
                shell=False,  # Explicitly disable shell to prevent shell injection
            )  # nosec: B603 - Command validated above

            return TerraformResult(
                success=process.returncode == 0,
                message="Command executed",
                stdout=process.stdout,
                stderr=process.stderr,
                returncode=process.returncode,
            )

        except subprocess.TimeoutExpired:
            return TerraformResult(
                success=False,
                message="Command timed out",
                stderr="Command timed out after 30 minutes",
                returncode=-1,
            )
        except Exception as e:
            return TerraformResult(
                success=False,
                message="Execution failed",
                stderr=f"Failed to execute terraform: {e}",
                returncode=-1,
            )

    def _execute_with_streaming(
        self, command: List[str], cwd: Path, env: Dict[str, str], show_output: bool
    ) -> TerraformResult:
        """Execute command with streaming output."""
        try:
            # Command is validated above to prevent injection attacks
            process = subprocess.Popen(
                command,
                cwd=str(cwd),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                shell=False,  # Explicitly disable shell to prevent shell injection
            )  # nosec: B603 - Command validated above

            stdout_lines = []
            if process.stdout:
                for line in iter(process.stdout.readline, ""):
                    if show_output:
                        click.echo(line, nl=False)
                    stdout_lines.append(line)

                process.stdout.close()

            returncode = process.wait()
            stdout = "".join(stdout_lines)

            return TerraformResult(
                success=returncode == 0,
                message="Command executed",
                stdout=stdout,
                stderr="",
                returncode=returncode,
            )

        except Exception as e:
            return TerraformResult(
                success=False,
                message="Execution failed",
                stderr=f"Failed to execute terraform: {e}",
                returncode=-1,
            )
