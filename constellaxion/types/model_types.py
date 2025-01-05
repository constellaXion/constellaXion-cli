from typing import List
from enum import Enum


class BaseModelName(str, Enum):
    LLAMA_3_1_8B = "llama-3.1-8B"
    LLAMA_3_1_13B = "llama-3.1-13B"
    TINY_LLAMA_1B = "TinyLlama-1B"


class TrainType(str, Enum):
    FINE_TUNE = "fine-tune"
    TRANSFER = "transfer"
