# import pytest
# from constellaxion.handlers.dataset import Dataset, Set

# def test_set_initialization():
#     """Test that a Set can be initialized with valid parameters."""
#     dataset_set = Set("train", "train.json")
#     assert dataset_set.type == "train"
#     assert dataset_set.path == "train.json"

# def test_dataset_initialization():
#     """Test that a Dataset can be initialized with valid parameters."""
#     dataset = Dataset("train.json", "val.json", "test.json", "test-model")
#     assert dataset.train == "train.json"
#     assert dataset.val == "val.json"
#     assert dataset.test == "test.json"
#     assert dataset.model_id == "test-model"

# def test_dataset_to_dict():
#     """Test that to_dict returns the correct dictionary structure."""
#     dataset = Dataset("train.json", "val.json", "test.json", "test-model")
#     expected = {
#         "train": {"local": "train.json", "cloud": "test-model/data/train.csv"},
#         "val": {"local": "val.json", "cloud": "test-model/data/val.csv"},
#         "test": {"local": "test.json", "cloud": "test-model/data/test.csv"},
#     }
#     assert dataset.to_dict() == expected

# def test_dataset_empty_paths():
#     """Test that Dataset raises an error with empty paths."""
#     with pytest.raises(ValueError):
#         Dataset("", "val.json", "test.json", "test-model")
#     with pytest.raises(ValueError):
#         Dataset("train.json", "", "test.json", "test-model")
#     with pytest.raises(ValueError):
#         Dataset("train.json", "val.json", "", "test-model")

# def test_dataset_none_paths():
#     """Test that Dataset raises an error with None paths."""
#     with pytest.raises(TypeError):
#         Dataset(None, "val.json", "test.json", "test-model")
#     with pytest.raises(TypeError):
#         Dataset("train.json", None, "test.json", "test-model")
#     with pytest.raises(TypeError):
#         Dataset("train.json", "val.json", None, "test-model")

# def test_dataset_empty_model_id():
#     """Test that Dataset raises an error with empty model_id."""
#     with pytest.raises(ValueError):
#         Dataset("train.json", "val.json", "test.json", "")

# def test_dataset_none_model_id():
#     """Test that Dataset raises an error with None model_id."""
#     with pytest.raises(TypeError):
#         Dataset("train.json", "val.json", "test.json", None)
