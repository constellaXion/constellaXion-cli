import shutil
import json
import pkg_resources
from pathlib import Path
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError

from constellaxion.terraform.core.enums import CloudProvider, TerraformLayer
from constellaxion.terraform.core.config import TerraformConfig
from constellaxion.terraform.core.result import TerraformResult
from constellaxion.terraform.core.binary import TerraformBinary
from constellaxion.terraform.core.executor import TerraformExecutor
from constellaxion.terraform.core.display import print_info
from constellaxion.services.aws.session import create_aws_session


class TerraformManager:
    """Simplified terraform manager for all operations.
    
    This class handles all terraform operations including bootstrap, destroy,
    layer management, and resource listing. It eliminates the complex
    abstraction hierarchy in favor of simple, direct methods.
    """
    
    def __init__(self, config: TerraformConfig):
        """Initialize terraform manager.
        
        Args:
            config: TerraformConfig with provider and settings
        """
        self.config = config
        self.binary = TerraformBinary()
        self.executor = TerraformExecutor(self.binary)
        
        base_dir = Path.home() / ".constellaxion" / "tf_workspaces"
        self.workspace_dir = Path(config.workspace_dir) if config.workspace_dir else base_dir / config.provider.value
        self.source_dir = self._get_source_dir()
    
    def bootstrap(self) -> TerraformResult:
        """Bootstrap cloud infrastructure.
        
        Returns:
            TerraformResult with backend configuration if successful
        """
        if self.config.provider == CloudProvider.AWS:
            return self._bootstrap_aws()
        elif self.config.provider == CloudProvider.GCP:
            return TerraformResult(False, "GCP bootstrap not implemented yet")
        else:
            return TerraformResult(False, f"Unsupported provider: {self.config.provider}")
    
    def destroy(self) -> TerraformResult:
        """Destroy all infrastructure.
        
        Returns:
            TerraformResult with destroyed resources list
        """
        if self.config.provider == CloudProvider.AWS:
            return self._destroy_aws()
        elif self.config.provider == CloudProvider.GCP:
            return TerraformResult(False, "GCP destroy not implemented yet")
        else:
            return TerraformResult(False, f"Unsupported provider: {self.config.provider}")
    
    def list_resources(self, force_clean: bool = False) -> TerraformResult:
        """List all managed resources.
        
        Args:
            force_clean: If True, force clean workspace initialization
            
        Returns:
            TerraformResult with resources list in data
        """
        if self.config.provider == CloudProvider.AWS:
            return self._list_aws_resources(force_clean)
        elif self.config.provider == CloudProvider.GCP:
            return TerraformResult(False, "GCP resource listing not implemented yet")
        else:
            return TerraformResult(False, f"Unsupported provider: {self.config.provider}")
    
    def apply_layer(
        self, 
        layer: TerraformLayer, 
        variables: Dict[str, Any],
        backend_config: Optional[Dict[str, Any]] = None,
        force_clean: bool = False
    ) -> TerraformResult:
        """Apply a specific terraform layer.
        
        Args:
            layer: TerraformLayer to apply
            variables: Terraform variables
            backend_config: Optional backend configuration
            force_clean: If True, force full workspace reinitialization
            
        Returns:
            TerraformResult from the apply operation
        """
        workspace_path = self._prepare_workspace_optimized(layer, backend_config, force_clean)
        
        env_vars = {}
        if self.config.provider == CloudProvider.AWS and self.config.profile:
            env_vars['AWS_PROFILE'] = self.config.profile
        
        vars_file = workspace_path / "terraform.tfvars.json"
        with open(vars_file, 'w') as f:
            json.dump(variables, f, indent=2)
        
        try:
            apply_cmd = ['apply', '-auto-approve']
            if vars_file.exists():
                apply_cmd.extend(['-var-file', str(vars_file)])
            
            apply_result = self.executor.execute(apply_cmd, workspace_path, env_vars)
            if not apply_result.success:
                return TerraformResult(False, "Failed to apply", stderr=apply_result.stderr)
            
            output_result = self.executor.execute(['output', '-json'], workspace_path, env_vars, capture_output=True)
            outputs = {}
            if output_result.success and output_result.stdout.strip():
                try:
                    outputs = json.loads(output_result.stdout)
                except json.JSONDecodeError:
                    pass
            
            return TerraformResult(
                True, 
                f"Successfully applied {layer.value}",
                data={"outputs": outputs}
            )
            
        finally:
            if vars_file.exists():
                vars_file.unlink()
    
    def destroy_layer(
        self,
        layer: TerraformLayer,
        variables: Dict[str, Any],
        backend_config: Optional[Dict[str, Any]] = None,
        force_clean: bool = False
    ) -> TerraformResult:
        """Destroy a specific terraform layer.
        
        Args:
            layer: TerraformLayer to destroy
            variables: Terraform variables
            backend_config: Optional backend configuration
            force_clean: If True, force full workspace reinitialization
            
        Returns:
            TerraformResult from the destroy operation
        """
        workspace_path = self._prepare_workspace_optimized(layer, backend_config, force_clean)
        
        env_vars = {}
        if self.config.provider == CloudProvider.AWS and self.config.profile:
            env_vars['AWS_PROFILE'] = self.config.profile
        
        vars_file = workspace_path / "terraform.tfvars.json"
        with open(vars_file, 'w') as f:
            json.dump(variables, f, indent=2)
        
        try:
            resources = []
            state_result = self.executor.execute(['state', 'list'], workspace_path, env_vars, capture_output=True)
            if state_result.success and state_result.stdout.strip():
                resources = [line.strip() for line in state_result.stdout.strip().split('\n') if line.strip()]
            
            destroy_cmd = ['destroy', '-auto-approve']
            if vars_file.exists():
                destroy_cmd.extend(['-var-file', str(vars_file)])
            
            destroy_result = self.executor.execute(destroy_cmd, workspace_path, env_vars)
            if not destroy_result.success:
                return TerraformResult(False, "Failed to destroy", stderr=destroy_result.stderr)
            
            result = TerraformResult(True, f"Successfully destroyed {layer.value}")
            result.data["destroyed_resources"] = resources
            return result
            
        finally:
            if vars_file.exists():
                vars_file.unlink()
    
    def cleanup(self) -> None:
        """Clean up all workspaces."""
        if self.workspace_dir.exists():
            shutil.rmtree(self.workspace_dir)
    
    
    def _prepare_workspace_optimized(
        self, 
        layer: TerraformLayer, 
        backend_config: Optional[Dict[str, Any]] = None,
        force_clean: bool = False
    ) -> Path:
        """Prepare workspace using optimized initialization strategy.
        
        Args:
            layer: TerraformLayer to prepare workspace for
            backend_config: Optional backend configuration
            force_clean: If True, force full reinitialization
            
        Returns:
            Path to the prepared workspace
        """
        workspace_path = self.workspace_dir / layer.workspace_name
        
        env_vars = {}
        if self.config.provider == CloudProvider.AWS and self.config.profile:
            env_vars['AWS_PROFILE'] = self.config.profile
        
        needs_full_init = (
            force_clean or
            self._needs_full_initialization(workspace_path, backend_config)
        )
        
        if needs_full_init:
            print_info(f"Initializing {layer.value} workspace...")
            self._prepare_clean_workspace(workspace_path, layer, backend_config)
            
            init_result = self.executor.execute(['init'], workspace_path, env_vars)
            if not init_result.success:
                raise RuntimeError(f"Failed to initialize workspace: {init_result.stderr}")
        else:
            print_info(f"Syncing {layer.value} workspace...")
            
            init_result = self.executor.execute(['init', '-upgrade=false'], workspace_path, env_vars)
            if not init_result.success:
                print_info(f"Quick sync failed, doing full initialization...")
                self._prepare_clean_workspace(workspace_path, layer, backend_config)
                init_result = self.executor.execute(['init'], workspace_path, env_vars)
                if not init_result.success:
                    raise RuntimeError(f"Failed to initialize workspace: {init_result.stderr}")
        
        return workspace_path
    
    def _needs_full_initialization(self, workspace_path: Path, backend_config: Optional[Dict[str, Any]]) -> bool:
        """Check if workspace needs full reinitialization.
        
        Args:
            workspace_path: Path to the workspace
            backend_config: Backend configuration to check against
            
        Returns:
            True if full initialization is needed
        """
        if not self._workspace_exists_and_valid(workspace_path):
            return True
        
        if self._backend_config_changed(workspace_path, backend_config):
            return True
        
        if self._terraform_files_stale(workspace_path):
            return True
        
        return False
    
    def _workspace_exists_and_valid(self, workspace_path: Path) -> bool:
        """Check if workspace exists and has valid terraform structure.
        
        Args:
            workspace_path: Path to check
            
        Returns:
            True if workspace is valid
        """
        if not workspace_path.exists():
            return False
        
        terraform_dir = workspace_path / ".terraform"
        if not terraform_dir.exists():
            return False
        
        tf_files = list(workspace_path.glob("*.tf"))
        if not tf_files:
            return False
        
        return True
    
    def _backend_config_changed(self, workspace_path: Path, backend_config: Optional[Dict[str, Any]]) -> bool:
        """Check if backend configuration has changed.
        
        Args:
            workspace_path: Path to workspace
            backend_config: Current backend configuration
            
        Returns:
            True if backend config changed
        """
        backend_file = workspace_path / "_backend.tf"
        
        if not backend_config:
            return backend_file.exists()
        
        if not backend_file.exists():
            return True
        
        try:
            with open(backend_file, 'r') as f:
                existing_content = f.read()
            
            expected_content = self._generate_backend_tf(backend_config)
            return existing_content.strip() != expected_content.strip()
        except Exception:
            return True
    
    def _terraform_files_stale(self, workspace_path: Path) -> bool:
        """Check if terraform files in workspace are stale compared to source.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            True if files are stale and need refresh
        """
        # For now, we'll assume files are never stale once copied
        # In the future, we could compare timestamps or checksums
        # between source and workspace
        return False
    
    def _prepare_clean_workspace(
        self, 
        workspace_path: Path, 
        layer: TerraformLayer, 
        backend_config: Optional[Dict[str, Any]]
    ) -> None:
        """Prepare a completely clean workspace.
        
        Args:
            workspace_path: Path to workspace
            layer: TerraformLayer being prepared
            backend_config: Optional backend configuration
        """
        source_path = self.source_dir / layer.value
        
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
        workspace_path.mkdir(parents=True)
        
        for tf_file in source_path.glob("*.tf"):
            shutil.copy(tf_file, workspace_path)
        
        if backend_config:
            backend_content = self._generate_backend_tf(backend_config)
            with open(workspace_path / "_backend.tf", "w") as f:
                f.write(backend_content)
    
    def _prepare_workspace(
        self, 
        layer: TerraformLayer, 
        backend_config: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Legacy workspace preparation - delegates to optimized version."""
        return self._prepare_workspace_optimized(layer, backend_config, force_clean=False)
    
    
    def _bootstrap_aws(self) -> TerraformResult:
        """Bootstrap AWS infrastructure."""
        try:
            print_info("🚀 Bootstrapping AWS infrastructure...")
            
            session = create_aws_session(self.config.profile, self.config.region)
            account_id = session.client("sts").get_caller_identity()["Account"]
            
            bucket_name = f"constellaxion-tf-state-{account_id}-{self.config.region}"
            backend_config = {
                "bucket": bucket_name,
                "region": self.config.region,
                "dynamodb_table": f"{bucket_name}-locks"
            }
            
            if not self._aws_backend_exists(session, backend_config):
                print_info("Setting up terraform backend...")
                backend_result = self.apply_layer(
                    TerraformLayer.AWS_BACKEND,
                    {
                        "region": self.config.region,
                        "bucket_name": bucket_name,
                        "enable_dynamodb_locking": True
                    }
                )
                if not backend_result.success:
                    return backend_result
            
            print_info("Setting up IAM permissions...")
            iam_backend_config = backend_config.copy()
            iam_backend_config["key"] = "iam/terraform.tfstate"
            
            self._import_existing_iam_role(session)
            
            iam_result = self.apply_layer(
                TerraformLayer.AWS_IAM,
                {"region": self.config.region},
                iam_backend_config
            )
            if not iam_result.success:
                return iam_result
            
            result = TerraformResult(True, "AWS infrastructure bootstrapped successfully")
            result.set_backend_config(backend_config)
            return result
            
        except Exception as e:
            return TerraformResult(False, f"Bootstrap failed: {str(e)}", error=str(e))
    
    def _destroy_aws(self) -> TerraformResult:
        """Destroy AWS infrastructure."""
        try:
            print_info("🗑️ Destroying AWS infrastructure...")
            
            session = create_aws_session(self.config.profile, self.config.region)
            account_id = session.client("sts").get_caller_identity()["Account"]
            bucket_name = f"constellaxion-tf-state-{account_id}-{self.config.region}"
            
            destroyed_resources = []
            
            iam_backend_config = {
                "bucket": bucket_name,
                "region": self.config.region,
                "dynamodb_table": f"{bucket_name}-locks",
                "key": "iam/terraform.tfstate"
            }
            
            try:
                iam_result = self.destroy_layer(
                    TerraformLayer.AWS_IAM,
                    {"region": self.config.region},
                    iam_backend_config
                )
                if iam_result.success:
                    destroyed_resources.extend(iam_result.get_destroyed_resources())
            except Exception as e:
                print_info(f"Note: Could not destroy IAM layer: {e}")
            
            backend_result = self.destroy_layer(
                TerraformLayer.AWS_BACKEND,
                {
                    "region": self.config.region,
                    "bucket_name": bucket_name,
                    "enable_dynamodb_locking": True
                }
            )
            if backend_result.success:
                destroyed_resources.extend(backend_result.get_destroyed_resources())
            
            self.cleanup()
            
            result = TerraformResult(True, "AWS infrastructure destroyed successfully")
            result.data["destroyed_resources"] = destroyed_resources
            return result
            
        except Exception as e:
            return TerraformResult(False, f"Destroy failed: {str(e)}", error=str(e))
    
    def _list_aws_resources(self, force_clean: bool = False) -> TerraformResult:
        """List AWS resources.
        
        Args:
            force_clean: If True, force clean workspace initialization
        """
        try:
            session = create_aws_session(self.config.profile, self.config.region)
            account_id = session.client("sts").get_caller_identity()["Account"]
            bucket_name = f"constellaxion-tf-state-{account_id}-{self.config.region}"
            
            resources = []
            
            resources.extend(self._list_aws_backend_resources(session, bucket_name))
            
            resources.extend(self._list_aws_iam_resources(bucket_name, force_clean))
            
            result = TerraformResult(True, f"Found {len(resources)} resources")
            result.set_resources(resources)
            return result
            
        except Exception as e:
            return TerraformResult(False, f"Failed to list resources: {str(e)}", error=str(e))
    
    
    def _get_source_dir(self) -> Path:
        """Get terraform source directory."""
        source_path = pkg_resources.resource_filename(
            'constellaxion', f'terraform/{self.config.provider.value}/layers'
        )
        return Path(source_path)
    
    def _generate_backend_tf(self, backend_config: Dict[str, Any]) -> str:
        """Generate backend.tf content."""
        if "bucket" in backend_config and "region" in backend_config:
            # S3 backend
            bucket = backend_config["bucket"]
            key = backend_config.get("key", "terraform.tfstate")
            region = backend_config["region"]
            table = backend_config.get("dynamodb_table")
            
            content = f'''terraform {{
  backend "s3" {{
    bucket = "{bucket}"
    key    = "{key}"
    region = "{region}"
'''
            if table:
                content += f'    dynamodb_table = "{table}"\n'
            content += '  }\n}\n'
            return content
        else:
            raise ValueError(f"Unsupported backend config: {backend_config}")
    
    def _aws_backend_exists(self, session, backend_config: Dict[str, Any]) -> bool:
        """Check if AWS backend exists."""
        try:
            s3_client = session.client("s3")
            dynamodb_client = session.client("dynamodb")
            
            s3_client.head_bucket(Bucket=backend_config["bucket"])
            dynamodb_client.describe_table(TableName=backend_config["dynamodb_table"])
            return True
        except ClientError:
            return False
    
    def _import_existing_iam_role(self, session) -> None:
        """Import existing IAM role if it exists."""
        try:
            iam_client = session.client('iam')
            role_name = 'constellaxion-admin'
            
            try:
                iam_client.get_role(RoleName=role_name)
                print_info(f"Found existing IAM role: {role_name}")
            except iam_client.exceptions.NoSuchEntityException:
                pass  
        except Exception as e:
            print_info(f"Could not check for existing IAM role: {e}")
    
    def _list_aws_backend_resources(self, session, bucket_name: str) -> List[Dict[str, Any]]:
        """List AWS backend resources."""
        resources = []
        
        s3_client = session.client("s3")
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            resources.append({
                "resource_type": "S3 Bucket",
                "name": bucket_name,
                "status": "✅ Found",
                "source": "aws_api"
            })
        except ClientError:
            resources.append({
                "resource_type": "S3 Bucket",
                "name": bucket_name,
                "status": "❌ Not Found",
                "source": "aws_api"
            })
        
        table_name = f"{bucket_name}-locks"
        dynamodb_client = session.client("dynamodb")
        try:
            dynamodb_client.describe_table(TableName=table_name)
            resources.append({
                "resource_type": "DynamoDB Lock Table",
                "name": table_name,
                "status": "✅ Found",
                "source": "aws_api"
            })
        except ClientError:
            resources.append({
                "resource_type": "DynamoDB Lock Table",
                "name": table_name,
                "status": "❌ Not Found",
                "source": "aws_api"
            })
        
        return resources
    
    def _list_aws_iam_resources(self, bucket_name: str, force_clean: bool = False) -> List[Dict[str, Any]]:
        """List AWS IAM resources from state.
        
        Args:
            bucket_name: S3 bucket name for terraform state
            force_clean: If True, force clean workspace initialization
        """
        resources = []
        
        try:
            env_vars = {}
            if self.config.provider == CloudProvider.AWS and self.config.profile:
                env_vars['AWS_PROFILE'] = self.config.profile
            
            iam_backend_config = {
                "bucket": bucket_name,
                "region": self.config.region,
                "dynamodb_table": f"{bucket_name}-locks",
                "key": "iam/terraform.tfstate"
            }
            
            workspace_path = self._prepare_workspace_optimized(
                TerraformLayer.AWS_IAM, 
                iam_backend_config, 
                force_clean=force_clean
            )
            
            state_result = self.executor.execute(['state', 'list'], workspace_path, env_vars, capture_output=True)
            if state_result.success and state_result.stdout.strip():
                state_resources = [line.strip() for line in state_result.stdout.strip().split('\n') if line.strip()]
                for resource in state_resources:
                    resource_type = resource.split('.')[0].replace('aws_', '').replace('_', ' ').title()
                    resources.append({
                        "resource_type": resource_type,
                        "name": resource,
                        "status": "✅ Managed in State",
                        "source": "terraform_state"
                    })
        except Exception:
            # If we can't read state, that's okay
            pass
        
        return resources