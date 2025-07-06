import pytest
from constellaxion.services.terraform_service import TerraformService


class TestServiceResponseStructure:
    """Test service response structure consistency."""
    
    def test_bootstrap_response_keys(self):
        """Bootstrap response contains all required keys."""
        service = TerraformService()
        result = service.bootstrap_infrastructure("aws", "us-east-1")
        
        required_keys = ["success", "message", "backend_config", "error"]
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
            
    def test_destroy_response_keys(self):
        """Destroy response contains all required keys."""
        service = TerraformService()
        result = service.destroy_infrastructure("aws", "us-east-1")
        
        required_keys = ["success", "message", "destroyed_resources", "error"]
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
            
    def test_list_resources_response_keys(self):
        """List resources response contains all required keys."""
        service = TerraformService()
        result = service.list_resources("aws", "us-east-1")
        
        required_keys = ["success", "resources", "total_count", "provider", "region", "error"]
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"


class TestServiceValidation:
    """Test service input validation."""
    
    def test_aws_valid_config(self):
        """AWS configuration validation accepts valid input."""
        service = TerraformService()
        result = service.bootstrap_infrastructure("aws", "us-east-1", "test-profile")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "message" in result
        
    def test_gcp_missing_project_id(self):
        """GCP validation fails when project_id is missing."""
        service = TerraformService()
        result = service.bootstrap_infrastructure("gcp", "us-central1")
        
        assert result["success"] is False
        assert "project_id is required for GCP" in result["error"]
        
    def test_empty_region_validation(self):
        """Validation fails with empty region."""
        service = TerraformService()
        result = service.bootstrap_infrastructure("aws", "")
        
        assert result["success"] is False
        assert "Region is required" in result["error"]
        
    def test_whitespace_region_validation(self):
        """Validation fails with whitespace-only region."""
        service = TerraformService()
        result = service.bootstrap_infrastructure("aws", "   ")
        
        assert result["success"] is False
        assert "Region is required" in result["error"]
        
    def test_list_resources_count_consistency(self):
        """List resources count matches resources length."""
        service = TerraformService()
        result = service.list_resources("aws", "us-east-1")
        
        if result["success"]:
            assert result["total_count"] == len(result["resources"])
        assert result["provider"] == "aws"
        assert result["region"] == "us-east-1"


class TestServiceErrorHandling:
    """Test service error handling behavior."""
    
    def test_bootstrap_handles_invalid_provider(self):
        """Bootstrap handles invalid provider gracefully."""
        service = TerraformService()
        result = service.bootstrap_infrastructure("invalid-provider", "us-east-1")
        
        assert result["success"] is False
        assert result["error"] is not None
        
    def test_destroy_handles_invalid_provider(self):
        """Destroy handles invalid provider gracefully."""
        service = TerraformService()
        result = service.destroy_infrastructure("invalid-provider", "us-east-1")
        
        assert result["success"] is False
        assert result["error"] is not None
        
    def test_list_resources_handles_invalid_provider(self):
        """List resources handles invalid provider gracefully."""
        service = TerraformService()
        result = service.list_resources("invalid-provider", "us-east-1")
        
        assert result["success"] is False
        assert result["error"] is not None