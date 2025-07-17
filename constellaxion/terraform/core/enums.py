from enum import Enum


class CloudProvider(Enum):
    """Supported cloud providers."""

    AWS = "aws"
    GCP = "gcp"

    @classmethod
    def from_string(cls, provider_str: str) -> "CloudProvider":
        """Convert string to CloudProvider enum with validation.

        Args:
            provider_str: Provider string to convert

        Returns:
            CloudProvider enum value

        Raises:
            ValueError: If provider string is not supported
        """
        provider_map = {"aws": cls.AWS, "gcp": cls.GCP}

        if provider_str not in provider_map:
            supported = ", ".join(f"'{p}'" for p in provider_map.keys())
            raise ValueError(
                f"Provider '{provider_str}' is not supported. Supported providers: {supported}"
            )

        return provider_map[provider_str]


class TerraformLayer(Enum):
    """Available terraform layers with their paths."""

    AWS_BACKEND = "basic/00-backend"
    AWS_IAM = "basic/01-iam"

    @property
    def workspace_name(self) -> str:
        """Get workspace directory name for the layer."""
        return self.value.replace("/", "_")


# Constants
TERRAFORM_VERSION = "1.8.0"
