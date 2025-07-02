import pytest
from unittest.mock import patch

from constellaxion.services.bootstrap import bootstrap_aws_infrastructure


class TestBootstrapLegacyFunction:
    """Test bootstrap_aws_infrastructure legacy compatibility."""
    
    @patch('constellaxion.services.bootstrap.bootstrap_aws')
    def test_successful_bootstrap_returns_backend_config(self, mock_bootstrap_aws):
        """Successful bootstrap returns backend config directly."""
        expected_backend = {
            "bucket": "test-bucket",
            "region": "us-east-1",
            "dynamodb_table": "test-locks"
        }
        
        mock_bootstrap_aws.return_value = {
            "success": True,
            "message": "Success",
            "backend_config": expected_backend,
            "error": None
        }
        
        result = bootstrap_aws_infrastructure("test-profile", "us-east-1")
        
        assert result == expected_backend
        mock_bootstrap_aws.assert_called_once_with("us-east-1", "test-profile")
        
    @patch('constellaxion.services.bootstrap.bootstrap_aws')
    def test_failed_bootstrap_raises_value_error(self, mock_bootstrap_aws):
        """Failed bootstrap raises ValueError with message."""
        error_message = "Bootstrap failed: Authentication error"
        
        mock_bootstrap_aws.return_value = {
            "success": False,
            "message": error_message,
            "backend_config": None,
            "error": "Authentication failed"
        }
        
        with pytest.raises(ValueError, match=error_message):
            bootstrap_aws_infrastructure("test-profile", "us-east-1")
            
    @patch('constellaxion.services.bootstrap.bootstrap_aws')
    def test_none_profile_handled(self, mock_bootstrap_aws):
        """None profile is passed correctly to underlying function."""
        mock_bootstrap_aws.return_value = {
            "success": True,
            "message": "Success",
            "backend_config": {},
            "error": None
        }
        
        bootstrap_aws_infrastructure(None, "us-east-1")
        
        mock_bootstrap_aws.assert_called_once_with("us-east-1", None)
        
    @patch('constellaxion.services.bootstrap.bootstrap_aws')
    def test_empty_string_profile_handled(self, mock_bootstrap_aws):
        """Empty string profile is passed correctly."""
        mock_bootstrap_aws.return_value = {
            "success": True,
            "message": "Success",
            "backend_config": {},
            "error": None
        }
        
        bootstrap_aws_infrastructure("", "us-east-1")
        
        mock_bootstrap_aws.assert_called_once_with("us-east-1", "")


class TestBootstrapParameterValidation:
    """Test parameter validation in bootstrap functions."""
    
    @patch('constellaxion.services.bootstrap.bootstrap_aws')
    def test_region_parameter_passed_correctly(self, mock_bootstrap_aws):
        """Region parameter is passed correctly to underlying service."""
        mock_bootstrap_aws.return_value = {
            "success": True,
            "message": "Success",
            "backend_config": {},
            "error": None
        }
        
        test_region = "eu-west-1"
        bootstrap_aws_infrastructure("test-profile", test_region)
        
        mock_bootstrap_aws.assert_called_once_with(test_region, "test-profile")
        
    @patch('constellaxion.services.bootstrap.bootstrap_aws')
    def test_profile_parameter_passed_correctly(self, mock_bootstrap_aws):
        """Profile parameter is passed correctly to underlying service."""
        mock_bootstrap_aws.return_value = {
            "success": True,
            "message": "Success", 
            "backend_config": {},
            "error": None
        }
        
        test_profile = "production-profile"
        bootstrap_aws_infrastructure(test_profile, "us-east-1")
        
        mock_bootstrap_aws.assert_called_once_with("us-east-1", test_profile)


class TestBootstrapErrorPropagation:
    """Test error propagation from underlying service."""
    
    @patch('constellaxion.services.bootstrap.bootstrap_aws')
    def test_network_error_propagated(self, mock_bootstrap_aws):
        """Network errors are properly propagated."""
        error_message = "Network connection failed"
        
        mock_bootstrap_aws.return_value = {
            "success": False,
            "message": error_message,
            "backend_config": None,
            "error": "ConnectionError: Unable to reach AWS"
        }
        
        with pytest.raises(ValueError, match=error_message):
            bootstrap_aws_infrastructure("test-profile", "us-east-1")
            
    @patch('constellaxion.services.bootstrap.bootstrap_aws')
    def test_authentication_error_propagated(self, mock_bootstrap_aws):
        """Authentication errors are properly propagated."""
        error_message = "AWS authentication failed"
        
        mock_bootstrap_aws.return_value = {
            "success": False,
            "message": error_message,
            "backend_config": None,
            "error": "InvalidCredentials: Check your AWS credentials"
        }
        
        with pytest.raises(ValueError, match=error_message):
            bootstrap_aws_infrastructure("test-profile", "us-east-1")
            
    @patch('constellaxion.services.bootstrap.bootstrap_aws')
    def test_terraform_error_propagated(self, mock_bootstrap_aws):
        """Terraform errors are properly propagated."""
        error_message = "Terraform initialization failed"
        
        mock_bootstrap_aws.return_value = {
            "success": False,
            "message": error_message,
            "backend_config": None,
            "error": "TerraformError: Backend configuration invalid"
        }
        
        with pytest.raises(ValueError, match=error_message):
            bootstrap_aws_infrastructure("test-profile", "us-east-1")