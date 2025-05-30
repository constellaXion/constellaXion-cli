from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("CONSTELLAXION_API_KEY", "test_api_key")
    monkeypatch.setenv("CONSTELLAXION_ENV", "test")
