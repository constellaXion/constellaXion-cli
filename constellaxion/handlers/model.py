"""Model class for handling model configuration."""


class Model:
    """Represents a model with its ID and base model configuration."""

    def __init__(self, model_id: str, base_model: str):
        if not model_id or not base_model:
            raise ValueError("model must have an id and base in model.yaml file")
        self.id = model_id
        self.base_model = base_model
