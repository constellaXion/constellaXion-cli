import pytest

from constellaxion.handlers.dataset import Dataset, Set


def test_set_initialization():
    """Test that a Set can be initialized with valid parameters."""
    dataset_set = Set("train", "train.csv")
    assert dataset_set.type == "train"  # nosec: B101
    assert dataset_set.path == "train.csv"  # nosec: B101


def test_dataset_initialization():
    """Test that a Dataset can be initialized with valid parameters."""
    dataset = Dataset("train.csv", "val.csv", "test.csv", "test-model")
    assert dataset.train == "train.csv"  # nosec: B101
    assert dataset.val == "val.csv"  # nosec: B101
    assert dataset.test == "test.csv"  # nosec: B101
    assert dataset.model_id == "test-model"  # nosec: B101


def test_dataset_to_dict():
    """Test that to_dict returns the correct dictionary structure."""
    dataset = Dataset("train.csv", "val.csv", "test.csv", "test-model")
    expected = {
        "train": {"local": "train.csv", "cloud": "test-model/data/train.csv"},
        "val": {"local": "val.csv", "cloud": "test-model/data/val.csv"},
        "test": {"local": "test.csv", "cloud": "test-model/data/test.csv"},
    }
    assert dataset.to_dict() == expected  # nosec: B101


def test_dataset_empty_paths():
    """Test that Dataset raises an error with empty paths."""
    with pytest.raises(ValueError):
        Dataset("", "val.csv", "test.csv", "test-model")
    with pytest.raises(ValueError):
        Dataset("train.csv", "", "test.csv", "test-model")
    with pytest.raises(ValueError):
        Dataset("train.csv", "val.csv", "", "test-model")


def test_dataset_none_paths():
    """Test that Dataset raises an error with None paths."""
    with pytest.raises(ValueError):
        Dataset(None, "val.csv", "test.csv", "test-model")
    with pytest.raises(ValueError):
        Dataset("train.csv", None, "test.csv", "test-model")
    with pytest.raises(ValueError):
        Dataset("train.csv", "val.csv", None, "test-model")


def test_dataset_empty_model_id():
    """Test that Dataset raises an error with empty model_id."""
    with pytest.raises(ValueError):
        Dataset("train.csv", "val.csv", "test.csv", "")


def test_dataset_none_model_id():
    """Test that Dataset raises an error with None model_id."""
    with pytest.raises(ValueError):
        Dataset("train.csv", "val.csv", "test.csv", None)
