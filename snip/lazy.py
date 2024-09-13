class Lazy:
    def __init__(self, fn, *args, **kwargs):
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._result = None

    def _evaluate(self):
        if self._result is None:
            self._result = self._fn(*self._args, **self._kwargs)
        return self._result

    def __getattr__(self, name):
        return getattr(self._evaluate(), name)

    def __getitem__(self, key):
        return self._evaluate()[key]

    def __setitem__(self, key, value):
        self._evaluate()[key] = value

    def __len__(self):
        return len(self._evaluate())

    def __iter__(self):
        return iter(self._evaluate())

    def __contains__(self, item):
        return item in self._evaluate()

    def __str__(self):
        return str(self._evaluate())

    def __repr__(self):
        return repr(self._evaluate())

def lazy(fn, *args, **kwargs):
    return Lazy(fn, *args, **kwargs)
