""" This module allows you to create references to variables, object
attributes, dictionary items and array items, and modify them dynamically. """


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


class AttrReference:
    def __init__(self, obj, attr):
        self._ref_obj = obj
        self._ref_attr = attr

    def refget(self):
        return getattr(self._ref_obj, self._ref_attr)

    def refset(self, value):
        setattr(self._ref_obj, self._ref_attr, value)


class KeyReference:
    def __init__(self, obj, key):
        self._ref_obj = obj
        self._ref_key = key

    def refget(self):
        return self._ref_obj[self._ref_key]

    def refset(self, value):
        self._ref_obj[self._ref_key] = value


class AttrReferenceProxy(AttrReference):
    def __getattribute__(self, name):
        if name in ['_ref_obj', '_ref_attr', 'refget', 'refset']:
            return object.__getattribute__(self, name)
        return getattr(self.refget(), name)

    def __setattr__(self, name, value):
        if name in ['_ref_obj', '_ref_attr']:
            object.__setattr__(self, name, value)
        else:
            setattr(self.refget(), name, value)

    def __delattr__(self, name):
        delattr(self.refget(), name)

    def __dir__(self):
        return dir(self.refget())

    def __getattr__(self, name):
        return getattr(self.refget(), name)


class KeyReferenceProxy(KeyReference):
    def __getattribute__(self, name):
        if name in ['_ref_obj', '_ref_key', 'refget', 'refset']:
            return object.__getattribute__(self, name)
        return getattr(self.refget(), name)

    def __setattr__(self, name, value):
        if name in ['_ref_obj', '_ref_key']:
            object.__setattr__(self, name, value)
        else:
            setattr(self.refget(), name, value)

    def __delattr__(self, name):
        delattr(self.refget(), name)

    def __dir__(self):
        return dir(self.refget())

    def __getattr__(self, name):
        return getattr(self.refget(), name)


def ref(obj, item=None, key=None, attr=None):
    if item is not None:
        if getattr(obj, '__getitem__', None):
            key = item
        else:
            attr = item
    if key is None:
        return AttrReferenceProxy(obj, attr)
    elif attr is not None:
        return KeyReferenceProxy(obj, key)
    else:
        raise ValueError('Invalid reference, must specify item, key, or attr')
