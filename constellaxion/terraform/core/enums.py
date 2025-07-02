from enum import Enum


class CloudProvider(Enum):
    """Supported cloud providers."""
    AWS = "aws"
    GCP = "gcp"


class TerraformLayer(Enum):
    """Available terraform layers with their paths."""
    AWS_BACKEND = "basic/00-backend"
    AWS_IAM = "basic/01-iam"
    
    @property
    def workspace_name(self) -> str:
        """Get workspace directory name for the layer."""
        return self.value.replace('/', '_')


# Constants
TERRAFORM_VERSION = "1.8.0"