from constellaxion.types.model_types import BaseModelName, TrainType


class Model:
    def __init__(self, id: str, base_model: BaseModelName):
        self.id = id
        self.base_model = base_model
