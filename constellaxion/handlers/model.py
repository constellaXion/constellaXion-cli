from constellaxion.types.model_types import BaseModelName


class Model:
    """Represents a model with its ID and base model configuration."""
    def __init__(self, id: str, base_model: BaseModelName):
        self.id = id
        self.base_model = base_model
