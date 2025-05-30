from constellaxion.types.model_types import BaseModelName


class Model:
    """Represents a model with its ID and base model configuration."""

    def __init__(self, model_id: str, base_model: BaseModelName):
        if not model_id:
            raise ValueError("model_id cannot be empty")
        if not isinstance(base_model, BaseModelName):
            raise TypeError(f"base_model must be a BaseModelName enum, got {type(base_model)}")
        self.id = model_id
        self.base_model = base_model
