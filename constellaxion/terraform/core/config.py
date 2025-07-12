from dataclasses import dataclass
from typing import Any, Dict, Optional

from constellaxion.terraform.core.enums import CloudProvider


@dataclass
class TerraformConfig:
    """Unified configuration for all terraform operations.

    Attributes:
        provider: CloudProvider enum for the target cloud
        region: Target cloud region
        profile: Optional provider profile (AWS profile, etc.)
        project_id: Optional GCP project ID
        workspace_dir: Optional custom workspace directory
    """

    provider: CloudProvider
    region: str
    profile: Optional[str] = None
    project_id: Optional[str] = None
    workspace_dir: Optional[str] = None

    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not self.region or not self.region.strip():
            errors.append("Region is required")

        if self.provider == CloudProvider.GCP and not self.project_id:
            errors.append("project_id is required for GCP")

        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {"provider": self.provider.value, "region": self.region}

        if self.profile:
            result["profile"] = self.profile
        if self.project_id:
            result["project_id"] = self.project_id
        if self.workspace_dir:
            result["workspace_dir"] = self.workspace_dir

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TerraformConfig":
        """Create from dictionary."""
        provider_str = data.get("provider", "aws")
        provider = CloudProvider.AWS if provider_str == "aws" else CloudProvider.GCP

        return cls(
            provider=provider,
            region=data["region"],
            profile=data.get("profile"),
            project_id=data.get("project_id"),
            workspace_dir=data.get("workspace_dir"),
        )
