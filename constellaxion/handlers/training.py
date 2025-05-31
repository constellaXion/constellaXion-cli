class Training:
    """Training class for handling training parameters."""

    def __init__(self, epochs: str, batch_size):
        if not epochs or not batch_size:
            raise ValueError("Epochs and batch size must be provided")
        self.epochs = epochs
        self.batch_size = batch_size

    def to_dict(self):
        """Convert the training to a dictionary."""
        return {
            "epochs": self.epochs,
            "batch_size": self.batch_size,
        }
