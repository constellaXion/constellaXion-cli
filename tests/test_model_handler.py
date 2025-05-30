# import pytest
# from constellaxion.handlers.model import Model
# from constellaxion.types.model_types import BaseModelName

# def test_model_initialization():
#     """Test that a Model can be initialized with valid parameters."""
#     model = Model("test-model", BaseModelName.GPT2)
#     assert model.id == "test-model"
#     assert model.base_model == BaseModelName.GPT2

# def test_model_invalid_base_model():
#     """Test that Model raises an error with invalid base model."""
#     with pytest.raises(TypeError):
#         Model("test-model", "invalid-model")

# def test_model_empty_id():
#     """Test that Model raises an error with empty ID."""
#     with pytest.raises(ValueError):
#         Model("", BaseModelName.GPT2)

# def test_model_none_id():
#     """Test that Model raises an error with None ID."""
#     with pytest.raises(TypeError):
#         Model(None, BaseModelName.GPT2)

# def test_model_none_base_model():
#     """Test that Model raises an error with None base model."""
#     with pytest.raises(TypeError):
#         Model("test-model", None)
