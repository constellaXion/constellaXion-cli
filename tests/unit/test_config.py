import os
import tempfile

from constellaxion.terraform.core.config import TerraformConfig
from constellaxion.terraform.core.enums import CloudProvider


class TestConfigValidation:
    """Test configuration validation logic."""

    def test_valid_aws_config(self):
        """Valid AWS configuration passes validation."""
        config = TerraformConfig(
            provider=CloudProvider.AWS, region="us-east-1", profile="test-profile"
        )

        is_valid, errors = config.validate()

        assert is_valid is True  # nosec: B101
        assert len(errors) == 0  # nosec: B101

    def test_valid_gcp_config(self):
        """Valid GCP configuration passes validation."""
        config = TerraformConfig(
            provider=CloudProvider.GCP,
            region="us-central1",
            project_id="test-project-123",
        )

        is_valid, errors = config.validate()

        assert is_valid is True  # nosec: B101
        assert len(errors) == 0  # nosec: B101

    def test_empty_region_fails(self):
        """Empty region fails validation."""
        config = TerraformConfig(provider=CloudProvider.AWS, region="")

        is_valid, errors = config.validate()

        assert is_valid is False  # nosec: B101
        assert "Region is required" in errors  # nosec: B101

    def test_whitespace_region_fails(self):
        """Whitespace-only region fails validation."""
        config = TerraformConfig(provider=CloudProvider.AWS, region="   \t\n   ")

        is_valid, errors = config.validate()

        assert is_valid is False  # nosec: B101
        assert "Region is required" in errors  # nosec: B101

    def test_gcp_missing_project_id_fails(self):
        """GCP config without project_id fails validation."""
        config = TerraformConfig(provider=CloudProvider.GCP, region="us-central1")

        is_valid, errors = config.validate()

        assert is_valid is False  # nosec: B101
        assert "project_id is required for GCP" in errors  # nosec: B101

    def test_gcp_with_empty_project_id_fails(self):
        """GCP config with empty project_id fails validation."""
        config = TerraformConfig(
            provider=CloudProvider.GCP, region="us-central1", project_id=""
        )

        is_valid, errors = config.validate()

        assert is_valid is False  # nosec: B101
        assert "project_id is required for GCP" in errors  # nosec: B101

    def test_multiple_validation_errors(self):
        """Multiple validation errors are collected."""
        config = TerraformConfig(
            provider=CloudProvider.GCP,
            region="",  # Empty region
            # Missing project_id
        )

        is_valid, errors = config.validate()

        assert is_valid is False  # nosec: B101
        assert len(errors) == 2  # nosec: B101
        assert "Region is required" in errors  # nosec: B101
        assert "project_id is required for GCP" in errors  # nosec: B101


class TestConfigSerialization:
    """Test configuration serialization and deserialization."""

    def test_aws_to_dict(self):
        """AWS config serializes correctly to dictionary."""
        config = TerraformConfig(
            provider=CloudProvider.AWS,
            region="us-east-1",
            profile="test-profile",
            workspace_dir="/custom/workspace",
        )

        result = config.to_dict()

        expected = {
            "provider": "aws",
            "region": "us-east-1",
            "profile": "test-profile",
            "workspace_dir": "/custom/workspace",
        }
        assert result == expected  # nosec: B101

    def test_gcp_to_dict(self):
        """GCP config serializes correctly to dictionary."""
        config = TerraformConfig(
            provider=CloudProvider.GCP,
            region="us-central1",
            project_id="test-project-123",
        )

        result = config.to_dict()

        expected = {
            "provider": "gcp",
            "region": "us-central1",
            "project_id": "test-project-123",
        }
        assert result == expected  # nosec: B101

    def test_from_dict_aws(self):
        """AWS config deserializes correctly from dictionary."""
        data = {"provider": "aws", "region": "us-west-2", "profile": "prod-profile"}

        config = TerraformConfig.from_dict(data)

        assert config.provider == CloudProvider.AWS  # nosec: B101
        assert config.region == "us-west-2"  # nosec: B101
        assert config.profile == "prod-profile"  # nosec: B101
        assert config.project_id is None  # nosec: B101

    def test_from_dict_gcp(self):
        """GCP config deserializes correctly from dictionary."""
        data = {
            "provider": "gcp",
            "region": "europe-west1",
            "project_id": "my-gcp-project",
        }

        config = TerraformConfig.from_dict(data)

        assert config.provider == CloudProvider.GCP  # nosec: B101
        assert config.region == "europe-west1"  # nosec: B101
        assert config.project_id == "my-gcp-project"  # nosec: B101
        assert config.profile is None  # nosec: B101

    def test_roundtrip_serialization(self):
        """Config survives roundtrip serialization."""
        original = TerraformConfig(
            provider=CloudProvider.AWS,
            region="ap-southeast-1",
            profile="staging",
            workspace_dir=os.path.join(tempfile.gettempdir(), "custom"),
        )

        # Serialize and deserialize
        data = original.to_dict()
        restored = TerraformConfig.from_dict(data)

        assert restored.provider == original.provider  # nosec: B101
        assert restored.region == original.region  # nosec: B101
        assert restored.profile == original.profile  # nosec: B101
        assert restored.workspace_dir == original.workspace_dir  # nosec: B101
