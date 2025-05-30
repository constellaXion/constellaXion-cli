class Training:
    def __init__(self, epochs: str, batch_size):
        self.epochs = epochs
        self.batch_size = batch_size

    def to_dict(self):
        """Convert the training to a dictionary."""
        return {
            "epochs": self.epochs,
            "batch_size": self.batch_size,
        }
