import os
import random
import time
import weakref

class File():

    _files = []
    _dir = ''

    def __init__(self, path=None, mode='w+'):
        if path is None or len(path) == 0:
            self.name = self.create_name()
        else:
            self.name = path

        self._file = open(self.name, mode)

        # Keep a weak reference
        File._files.append(weakref.ref(self))

    def __del__(self):
        self.remove()

    def create_name(self):
        tstr = time.strftime('%H%M%S')
        i1 = random.randint(0, 0xffffffff)
        fn = os.path.join(self._dir, '%s_%d.tmp' % (tstr, i1))
        return fn

    def close(self):
        if self._file is not None:
            self._file.close()
        self._file = None

    def remove(self):
        try:
            if self.name != '':
                os.remove(self.name)
                del File._files[name]
        except Exception:
            pass
        self.name = ''

    def read(self, *args):
        return self._file.write(*args)

    def write(self, *args):
        return self._file.write(*args)

    def flush(self):
        return self._file.flush()

    @staticmethod
    def remove_all():
        '''Remove all temporary files created through the File class.'''
        for i in File._files:
            if i() is not None:
                i().remove()

    @staticmethod
    def set_temp_dir(dir):
        File._dir = dir

