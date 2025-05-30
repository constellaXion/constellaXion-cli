# import os
# import pytest
# from click.testing import CliRunner
# from constellaxion.commands.init import (
#     init_model,
#     init_dataset,
#     init_training,
#     init,
# )
# from constellaxion.handlers.model import Model
# from constellaxion.handlers.dataset import Dataset
# from constellaxion.handlers.training import Training

# @pytest.fixture
# def valid_model_config():
#     return {
#         "id": "test-model",
#         "base": "gpt2",
#     }

# @pytest.fixture
# def valid_dataset_config():
#     return {
#         "train": "train.json",
#         "val": "val.json",
#         "test": "test.json",
#     }

# @pytest.fixture
# def valid_training_config():
#     return {
#         "epochs": 3,
#         "batch_size": 32,
#     }

# def test_init_model_valid_config(valid_model_config):
#     """Test model initialization with valid config."""
#     model = init_model(valid_model_config)
#     print(model.id)
#     assert isinstance(model, Model)
#     assert model.id == "test-model"
#     assert model.base_model == "gpt2"

# # def test_init_model_invalid_config():
# #     """Test model initialization with invalid config."""
# #     with pytest.raises(AttributeError):
# #         init_model({})

# # def test_init_dataset_valid_config(valid_dataset_config, valid_model_config):
# #     """Test dataset initialization with valid config."""
# #     dataset = init_dataset(valid_dataset_config, valid_model_config)
# #     assert isinstance(dataset, Dataset)
# #     assert dataset.train == "train.json"
# #     assert dataset.val == "val.json"
# #     assert dataset.test == "test.json"
# #     assert dataset.model_id == "test-model"

# # def test_init_dataset_invalid_config(valid_model_config):
# #     """Test dataset initialization with invalid config."""
# #     with pytest.raises(AttributeError):
# #         init_dataset({}, valid_model_config)

# # def test_init_training_valid_config(valid_training_config):
# #     """Test training initialization with valid config."""
# #     training = init_training(valid_training_config)
# #     assert isinstance(training, Training)
# #     assert training.epochs == 3
# #     assert training.batch_size == 32

# # def test_init_training_invalid_config():
# #     """Test training initialization with invalid config."""
# #     with pytest.raises(AttributeError):
# #         init_training({})

# # def test_init_command_with_invalid_yaml(tmp_path):
# #     """Test init command with invalid YAML file."""
# #     runner = CliRunner()
# #     with runner.isolated_filesystem():
# #         # Create an invalid YAML file
# #         with open("model.yaml", "w") as f:
# #             f.write("invalid: yaml: content: [")
        
# #         result = runner.invoke(init)
# #         assert result.exit_code != 0
# #         assert "Error" in result.output

# # def test_init_command_with_missing_yaml(tmp_path):
# #     """Test init command with missing YAML file."""
# #     runner = CliRunner()
# #     with runner.isolated_filesystem():
# #         result = runner.invoke(init)
# #         assert result.exit_code != 0
# #         assert "Error: model.yaml file not found" in result.output 