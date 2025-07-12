"""Single result type for all terraform operations."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TerraformResult:
    """Unified result for all terraform operations.

    Attributes:
        success: Whether the operation succeeded
        message: Human-readable result message
        stdout: Command output (for terraform commands)
        stderr: Error output (for terraform commands)
        returncode: Exit code (for terraform commands)
        data: Optional operation-specific data (backend_config, resources, etc.)
        error: Optional detailed error information
    """

    success: bool
    message: str
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize data dict if not provided."""
        if self.data is None:
            self.data = {}

    @property
    def output(self) -> str:
        """Get combined output for display."""
        return self.stdout if self.stdout else self.stderr

    def get_backend_config(self) -> Optional[Dict[str, Any]]:
        """Get backend configuration from data."""
        return self.data.get("backend_config")

    def get_resources(self) -> List[Dict[str, Any]]:
        """Get resources list from data."""
        return self.data.get("resources", [])

    def get_destroyed_resources(self) -> List[str]:
        """Get destroyed resources list from data."""
        return self.data.get("destroyed_resources", [])

    def set_backend_config(self, config: Dict[str, Any]) -> None:
        """Set backend configuration in data."""
        self.data["backend_config"] = config

    def set_resources(self, resources: List[Dict[str, Any]]) -> None:
        """Set resources list in data."""
        self.data["resources"] = resources

    def add_destroyed_resource(self, resource: str) -> None:
        """Add a destroyed resource to the list."""
        if "destroyed_resources" not in self.data:
            self.data["destroyed_resources"] = []
        self.data["destroyed_resources"].append(resource)
