class Set:
    def __init__(self, type: str, path: str):
        self.type = type
        self.path = path


class Dataset:
    def __init__(self, train: str, val: str, test: str, model_id: str):
        self._train = Set("train", train)
        self._val = Set("val", val)
        self._test = Set("test", test)
        self.model_id = model_id
        self.train = self._get_train()
        self.val = self._get_val()
        self.test = self._get_test()

    def _get_train(self):
        """Get the train path."""
        return self._train.path

    def _get_val(self):
        """Get the val path."""
        return self._val.path

    def _get_test(self):
        """Get the test path."""
        return self._test.path

    def to_dict(self):
        """Convert the dataset to a dictionary."""
        return {
            "train": {"local": self.train, "cloud": f"{self.model_id}/data/train.csv"},
            "val": {"local": self.val, "cloud": f"{self.model_id}/data/val.csv"},
            "test": {"local": self.test, "cloud": f"{self.model_id}/data/test.csv"},
        }
