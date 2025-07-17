from typing import Any, Dict

from constellaxion.terraform.core.config import TerraformConfig
from constellaxion.terraform.core.enums import CloudProvider
from constellaxion.terraform.manager import TerraformManager


class TerraformService:

    def bootstrap_infrastructure(
        self, provider: str, region: str, profile: str = None, **kwargs
    ) -> Dict[str, Any]:
        """Bootstrap cloud infrastructure."""
        try:
            config = self._validate_and_create_config(
                provider, region, profile, **kwargs
            )
            manager = TerraformManager(config)
            result = manager.bootstrap()

            return {
                "success": result.success,
                "message": result.message,
                "backend_config": result.get_backend_config(),
                "error": result.error,
            }
        except ValueError as e:
            return self._create_error_response("bootstrap", provider, region, str(e))

    def destroy_infrastructure(
        self, provider: str, region: str, profile: str = None, **kwargs
    ) -> Dict[str, Any]:
        """Destroy all infrastructure."""
        try:
            config = self._validate_and_create_config(
                provider, region, profile, **kwargs
            )
            manager = TerraformManager(config)
            result = manager.destroy()

            return {
                "success": result.success,
                "message": result.message,
                "destroyed_resources": result.get_destroyed_resources(),
                "error": result.error,
            }
        except ValueError as e:
            return self._create_error_response("destroy", provider, region, str(e))

    def list_resources(
        self,
        provider: str,
        region: str,
        profile: str = None,
        force_clean: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """List all managed resources."""
        try:
            config = self._validate_and_create_config(
                provider, region, profile, **kwargs
            )
            manager = TerraformManager(config)
            result = manager.list_resources(force_clean=force_clean)

            return {
                "success": result.success,
                "resources": result.get_resources(),
                "total_count": len(result.get_resources()),
                "provider": provider,
                "region": region,
                "error": result.error,
            }
        except ValueError as e:
            return self._create_error_response(
                "list_resources", provider, region, str(e)
            )

    def _validate_and_create_config(
        self, provider: str, region: str, profile: str = None, **kwargs
    ) -> TerraformConfig:
        """Validate provider and create configuration.

        Raises:
            ValueError: If provider is invalid or config validation fails
        """
        provider_enum = CloudProvider.from_string(provider)  # Validates provider
        config = TerraformConfig(
            provider=provider_enum,
            region=region,
            profile=profile,
            project_id=kwargs.get("project_id"),
            workspace_dir=kwargs.get("workspace_dir"),
        )

        is_valid, errors = config.validate()
        if not is_valid:
            raise ValueError("; ".join(errors))

        return config

    def _create_error_response(
        self, operation: str, provider: str, region: str, error: str
    ) -> Dict[str, Any]:
        """Create standardized error response."""
        base_response = {
            "success": False,
            "message": f"Failed to {operation}",
            "error": error,
        }

        # Add operation-specific fields
        if operation == "bootstrap":
            base_response["backend_config"] = None
        elif operation == "destroy":
            base_response["destroyed_resources"] = []
        elif operation == "list_resources":
            base_response.update(
                {
                    "resources": [],
                    "total_count": 0,
                    "provider": provider,
                    "region": region,
                }
            )

        return base_response


def bootstrap_aws(region: str, profile: str = None) -> Dict[str, Any]:
    """Bootstrap AWS infrastructure."""
    service = TerraformService()
    return service.bootstrap_infrastructure("aws", region, profile)


def destroy_aws(region: str, profile: str = None) -> Dict[str, Any]:
    """Destroy AWS infrastructure."""
    service = TerraformService()
    return service.destroy_infrastructure("aws", region, profile)


def list_aws_resources(
    region: str, profile: str = None, force_clean: bool = False
) -> Dict[str, Any]:
    """List AWS resources - convenience function.

    Args:
        region: AWS region to list resources in
        profile: Optional AWS profile name
        force_clean: If True, force clean workspace initialization

    Returns:
        Dictionary with resource listing results
    """
    service = TerraformService()
    return service.list_resources("aws", region, profile, force_clean=force_clean)


def bootstrap_gcp(region: str, project_id: str, profile: str = None) -> Dict[str, Any]:
    """Bootstrap GCP infrastructure - convenience function.

    Args:
        region: GCP region to bootstrap in
        project_id: GCP project ID
        profile: Optional GCP profile name

    Returns:
        Dictionary with bootstrap results
    """
    service = TerraformService()
    config = TerraformConfig(
        provider=CloudProvider.GCP,
        region=region,
        project_id=project_id,
        profile=profile,
    )
    return service.bootstrap_infrastructure(config)
