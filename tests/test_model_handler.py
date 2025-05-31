import pytest

from constellaxion.handlers.model import Model


def test_model_initialization():
    """Test that a Model can be initialized with valid parameters."""
    model = Model("test-model", "tiny-llama-1b")
    assert model.id == "test-model"  # nosec: B101
    assert model.base_model == "tiny-llama-1b"  # nosec: B101


def test_model_empty_base_model():
    """Test that Model raises an error with invalid base model."""
    with pytest.raises(ValueError):
        Model("test-model", "")


def test_model_empty_id():
    """Test that Model raises an error with empty ID."""
    with pytest.raises(ValueError):
        Model("", "tiny-llama-1b")


def test_model_none_id():
    """Test that Model raises an error with None ID."""
    with pytest.raises(ValueError):
        Model(None, "tiny-llama-1b")


def test_model_none_base_model():
    """Test that Model raises an error with None base model."""
    with pytest.raises(ValueError):
        Model("test-model", None)
