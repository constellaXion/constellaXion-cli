from typing import Dict, Any

from constellaxion.terraform.manager import TerraformManager
from constellaxion.terraform.core.config import TerraformConfig
from constellaxion.terraform.core.enums import CloudProvider


class TerraformService:
    
    def bootstrap_infrastructure(self, provider: str, region: str, profile: str = None, **kwargs) -> Dict[str, Any]:
        """Bootstrap cloud infrastructure.
        
        Args:
            provider: Cloud provider ("aws" or "gcp")
            region: Target region
            profile: Optional profile name
            **kwargs: Additional provider-specific options
            
        Returns:
            Dictionary with operation results
        """
        provider_enum = CloudProvider.AWS if provider == "aws" else CloudProvider.GCP
        config = TerraformConfig(
            provider=provider_enum,
            region=region,
            profile=profile,
            project_id=kwargs.get("project_id")
        )
        
        is_valid, errors = config.validate()
        if not is_valid:
            return {
                "success": False,
                "message": "Configuration validation failed",
                "error": "; ".join(errors)
            }
        
        manager = TerraformManager(config)
        result = manager.bootstrap()
        
        return {
            "success": result.success,
            "message": result.message,
            "backend_config": result.get_backend_config(),
            "error": result.error
        }
    
    def destroy_infrastructure(self, provider: str, region: str, profile: str = None, **kwargs) -> Dict[str, Any]:
        """Destroy all infrastructure.
        
        Args:
            provider: Cloud provider ("aws" or "gcp")
            region: Target region
            profile: Optional profile name
            **kwargs: Additional provider-specific options
            
        Returns:
            Dictionary with operation results
        """
        provider_enum = CloudProvider.AWS if provider == "aws" else CloudProvider.GCP
        config = TerraformConfig(
            provider=provider_enum,
            region=region,
            profile=profile,
            project_id=kwargs.get("project_id")
        )
        
        manager = TerraformManager(config)
        result = manager.destroy()
        
        return {
            "success": result.success,
            "message": result.message,
            "destroyed_resources": result.get_destroyed_resources(),
            "error": result.error
        }
    
    def list_resources(self, provider: str, region: str, profile: str = None, force_clean: bool = False, **kwargs) -> Dict[str, Any]:
        """List all managed resources.
        
        Args:
            provider: Cloud provider ("aws" or "gcp")
            region: Target region
            profile: Optional profile name
            force_clean: If True, force clean workspace initialization
            **kwargs: Additional provider-specific options
            
        Returns:
            Dictionary with resources list
        """
        provider_enum = CloudProvider.AWS if provider == "aws" else CloudProvider.GCP
        config = TerraformConfig(
            provider=provider_enum,
            region=region,
            profile=profile,
            project_id=kwargs.get("project_id")
        )
        
        manager = TerraformManager(config)
        result = manager.list_resources(force_clean=force_clean)
        
        return {
            "success": result.success,
            "resources": result.get_resources(),
            "total_count": len(result.get_resources()),
            "provider": provider,
            "region": region,
            "error": result.error
        }


def bootstrap_aws(region: str, profile: str = None) -> Dict[str, Any]:
    """Bootstrap AWS infrastructure."""
    service = TerraformService()
    return service.bootstrap_infrastructure("aws", region, profile)


def destroy_aws(region: str, profile: str = None) -> Dict[str, Any]:
    """Destroy AWS infrastructure."""
    service = TerraformService()
    return service.destroy_infrastructure("aws", region, profile)


def list_aws_resources(region: str, profile: str = None, force_clean: bool = False) -> Dict[str, Any]:
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


def bootstrap_gcp(
    region: str, 
    project_id: str, 
    profile: str = None
) -> Dict[str, Any]:
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
        profile=profile
    )
    return service.bootstrap_infrastructure(config)