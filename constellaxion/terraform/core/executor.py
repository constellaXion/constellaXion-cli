import os
import subprocess
import click
from pathlib import Path
from typing import Dict, List, Optional, Any

from constellaxion.terraform.core.binary import TerraformBinary
from constellaxion.terraform.core.result import TerraformResult


class TerraformExecutor:
    """Handles terraform command execution."""
    
    def __init__(self, binary: TerraformBinary) -> None:
        """Initialize terraform command executor."""
        self.binary = binary
    
    def execute(
        self,
        command: List[str],
        working_dir: Path,
        env_vars: Optional[Dict[str, str]] = None,
        capture_output: bool = False,
        show_output: bool = True
    ) -> TerraformResult:
        """Execute a terraform command."""
        if not working_dir.exists():
            raise FileNotFoundError(f"Working directory does not exist: {working_dir}")
        
        full_command = [str(self.binary.get_path())] + command
        
        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        
        if capture_output:
            return self._execute_with_capture(full_command, working_dir, env)
        else:
            return self._execute_with_streaming(full_command, working_dir, env, show_output)
    
    def init(
        self, 
        working_dir: Path, 
        backend_config: Optional[Dict[str, str]] = None, 
        **kwargs: Any
    ) -> TerraformResult:
        """Run terraform init."""
        command = ['init']
        
        if backend_config:
            for key, value in backend_config.items():
                command.extend(['-backend-config', f'{key}={value}'])
        
        if kwargs.get('upgrade'):
            command.append('-upgrade')
        if kwargs.get('reconfigure'):
            command.append('-reconfigure')
        
        result = self.execute(command, working_dir)
        return TerraformResult(
            success=result.success,
            message="Init completed" if result.success else "Init failed",
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode
        )
    
    def apply(self, working_dir: Path, var_file: Optional[Path] = None) -> TerraformResult:
        """Run terraform apply."""
        command = ['apply', '-auto-approve']
        
        if var_file and var_file.exists():
            command.extend(['-var-file', str(var_file)])
        
        result = self.execute(command, working_dir)
        return TerraformResult(
            success=result.success,
            message="Apply completed" if result.success else "Apply failed",
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode
        )
    
    def destroy(self, working_dir: Path, var_file: Optional[Path] = None) -> TerraformResult:
        """Run terraform destroy."""
        command = ['destroy', '-auto-approve']
        
        if var_file and var_file.exists():
            command.extend(['-var-file', str(var_file)])
        
        result = self.execute(command, working_dir)
        return TerraformResult(
            success=result.success,
            message="Destroy completed" if result.success else "Destroy failed",
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode
        )
    
    def refresh(self, working_dir: Path) -> TerraformResult:
        """Run terraform refresh to sync state with remote."""
        result = self.execute(['refresh', '-auto-approve'], working_dir)
        return TerraformResult(
            success=result.success,
            message="Refresh completed" if result.success else "Refresh failed",
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode
        )
    
    def output(self, working_dir: Path, json_format: bool = True) -> TerraformResult:
        """Get terraform outputs."""
        command = ['output']
        if json_format:
            command.append('-json')
        
        result = self.execute(command, working_dir, capture_output=True)
        return TerraformResult(
            success=result.success,
            message="Output retrieved" if result.success else "Output failed",
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode
        )
    
    def state_list(self, working_dir: Path) -> TerraformResult:
        """List resources in terraform state."""
        result = self.execute(['state', 'list'], working_dir, capture_output=True)
        return TerraformResult(
            success=result.success,
            message="State listed" if result.success else "State list failed",
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode
        )
    
    def _execute_with_capture(self, command: List[str], cwd: Path, env: Dict[str, str]) -> TerraformResult:
        """Execute command and capture output."""
        try:
            process = subprocess.run(
                command,
                cwd=str(cwd),
                env=env,
                capture_output=True,
                text=True,
                check=False,
                encoding='utf-8',
                timeout=1800
            )
            
            return TerraformResult(
                success=process.returncode == 0,
                message="Command executed",
                stdout=process.stdout,
                stderr=process.stderr,
                returncode=process.returncode
            )
            
        except subprocess.TimeoutExpired:
            return TerraformResult(
                success=False,
                message="Command timed out",
                stderr="Command timed out after 30 minutes",
                returncode=-1
            )
        except Exception as e:
            return TerraformResult(
                success=False,
                message="Execution failed",
                stderr=f"Failed to execute terraform: {e}",
                returncode=-1
            )
    
    def _execute_with_streaming(
        self, 
        command: List[str], 
        cwd: Path, 
        env: Dict[str, str],
        show_output: bool
    ) -> TerraformResult:
        """Execute command with streaming output."""
        try:
            process = subprocess.Popen(
                command,
                cwd=str(cwd),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8'
            )
            
            stdout_lines = []
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
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
                returncode=returncode
            )
            
        except Exception as e:
            return TerraformResult(
                success=False,
                message="Execution failed",
                stderr=f"Failed to execute terraform: {e}",
                returncode=-1
            )