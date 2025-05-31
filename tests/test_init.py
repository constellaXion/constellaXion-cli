from click.testing import CliRunner
import pytest

from constellaxion.commands.init import init, init_dataset, init_model, init_training
from constellaxion.handlers.dataset import Dataset
from constellaxion.handlers.model import Model
from constellaxion.handlers.training import Training


@pytest.fixture
def valid_model_config():
    """Test model initialization with valid config."""
    return {
        "id": "test-model",
        "base": "tiny-llama-1b",
    }


@pytest.fixture
def valid_dataset_config():
    """Test dataset initialization with valid config."""
    return {
        "train": "./train.csv",
        "val": "./val.csv",
        "test": "./test.csv",
    }


@pytest.fixture
def valid_training_config():
    """Test training initialization with valid config."""
    return {
        "epochs": 3,
        "batch_size": 32,
    }


def test_init_model_valid_config(valid_model_config):
    """Test model initialization with valid config."""
    model = init_model(valid_model_config)
    print(model.id)
    print(model.base_model)
    assert isinstance(model, Model)  # nosec: B101
    assert model.id == "test-model"  # nosec: B101
    assert model.base_model == "tiny-llama-1b"  # nosec: B101


def test_init_model_invalid_config():
    """Test model initialization with invalid config."""
    with pytest.raises(AttributeError):
        init_model({})


def test_init_dataset_valid_config(valid_dataset_config, valid_model_config):
    """Test dataset initialization with valid config."""
    dataset = init_dataset(valid_dataset_config, valid_model_config)
    assert isinstance(dataset, Dataset)  # nosec: B101
    assert dataset.train == "./train.csv"  # nosec: B101
    assert dataset.val == "./val.csv"  # nosec: B101
    assert dataset.test == "./test.csv"  # nosec: B101
    assert dataset.model_id == "test-model"  # nosec: B101


def test_init_dataset_invalid_config(valid_model_config):
    """Test dataset initialization with invalid config."""
    with pytest.raises(AttributeError):
        init_dataset({}, valid_model_config)


def test_init_training_valid_config(valid_training_config):
    """Test training initialization with valid config."""
    training = init_training(valid_training_config)
    assert isinstance(training, Training)  # nosec: B101
    assert training.epochs == 3  # nosec: B101
    assert training.batch_size == 32  # nosec: B101


def test_init_training_invalid_config():
    """Test training initialization with invalid config."""
    with pytest.raises(AttributeError):
        init_training({})


def test_init_command_with_invalid_yaml():
    """Test init command with invalid YAML file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create an invalid YAML file
        with open("model.yaml", "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [")

        result = runner.invoke(init)
        assert result.exit_code == 1  # nosec: B101
        assert "mapping values are not allowed here" in result.output  # nosec: B101


def test_init_command_with_missing_yaml():
    """Test init command with missing YAML file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(init)
        assert result.exit_code == 1  # nosec: B101
        assert "Error: model.yaml file not found" in result.output  # nosec: B101
