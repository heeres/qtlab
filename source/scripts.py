import os

class Script():

    def __init__(self, fn):
        self._fn = fn
        self._read_doc()

    def _read_doc(self):
        self.__doc__ = ''
        if not os.path.exists(self._fn):
            return

        f = open(self._fn, 'r')
        for line in f:
            line2 = line.strip(' \t')
            if len(line2) > 0 and line2[0] == '#':
                self.__doc__ += line

    def __call__(self, *args, **kwargs):
        locals = {
                'args': args,
                'kwargs': kwargs,
        }
        execfile(self._fn, locals)

class Scripts():

    def __init__(self):
        self._dirs = ['scripts', ]
        self._cache = {}

    def get(self, name):
        if name in self._cache:
            return self._cache[name]

        for dname in self._dirs:
            fn = os.path.join(dname, name)
            if os.path.exists(fn):
                return Script(fn)

