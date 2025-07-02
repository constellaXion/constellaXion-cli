from typing import Dict, Optional

from constellaxion.services.terraform_service import bootstrap_aws 


def bootstrap_aws_infrastructure(profile: Optional[str], region: str) -> Dict:
    """Bootstrap AWS infrastructure - legacy compatibility function.
    
    This function maintains backward compatibility during migration.
    New code should use TerraformService directly.
    
    Args:
        profile: Optional AWS profile name
        region: AWS region to bootstrap in
        
    Returns:
        Backend configuration dictionary if successful
        
    Raises:
        ValueError: If bootstrap operation fails
    """
    result = bootstrap_aws(region, profile)
    
    if result["success"]:
        return result["backend_config"]
    else:
        raise ValueError(result["message"])