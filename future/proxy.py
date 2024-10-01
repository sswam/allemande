class Proxy:
    def __init__(self, obj):
        self._obj = obj

    def __getattribute__(self, name):
        if name == '_obj':
            return object.__getattribute__(self, name)
        return getattr(object.__getattribute__(self, '_obj'), name)

    def __setattr__(self, name, value):
        if name == '_obj':
            object.__setattr__(self, name, value)
        else:
            setattr(self._obj, name, value)

    def __delattr__(self, name):
        delattr(self._obj, name)

    def __dir__(self):
        return dir(self._obj)

    def __getattr__(self, name):
        return getattr(self._obj, name)
