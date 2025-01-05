class Set():
    def __init__(self, type: str, path: str):
        self.type = type
        self.path = path


class Dataset():
    def __init__(self, train: str, val: str, test: str):
        self._train = Set('train', train)
        self._val = Set('val', val)
        self._test = Set('test', test)
        self.train = self._get_train()
        self.val = self._get_val()
        self.test = self._get_test()

    def _get_train(self):
        return self._train.path

    def _get_val(self):
        return self._val.path

    def _get_test(self):
        return self._test.path
