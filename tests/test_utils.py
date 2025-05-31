import json
import logging

import pytest

from constellaxion.utils import get_json, get_level_name


def test_get_level_name():
    """Test that get_level_name returns the correct level names."""
    assert get_level_name(logging.DEBUG) == "DEBUG"  # nosec: B101
    assert get_level_name(logging.INFO) == "INFO"  # nosec: B101
    assert get_level_name(logging.WARNING) == "WARNING"  # nosec: B101
    assert get_level_name(logging.ERROR) == "ERROR"  # nosec: B101
    assert get_level_name(logging.CRITICAL) == "CRITICAL"  # nosec: B101
    assert get_level_name(999) == "NOTSET"  # nosec: B101


def test_get_json(tmp_path):
    """Test that get_json correctly reads JSON files."""
    # Create a temporary JSON file
    test_json = {"test": "data"}
    json_path = tmp_path / "test.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(test_json, f)
    # Test reading the JSON file
    result = get_json(json_path)
    assert result == test_json  # nosec: B101


def test_get_json_invalid_file():
    """Test that get_json raises an error for invalid files."""
    with pytest.raises(FileNotFoundError):
        get_json("invalid_file.json")
