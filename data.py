import os

class QTData():

    def __init__(self, name, fn):
        self._name = name
        self._filename = fn
        self._f = None

        self._coordinates = []
        self._values = []

        self._cor = []
        self._val = []
        self._points = 0

    def add_coordinate(self, **kwargs):
        self._coordinates.append(kwargs)

    def add_value(self, **kwargs):
        self._values.append(kwargs)

    def _open(self):
        if self._f is not None:
            self._close()

        path, fn = os.path.split(self._filename)
        if not os.path.exists(path):
            os.makedirs(path)

        if os.path.exists(self._filename):
            print 'File exists; overwrite?'

        self._f = open(self._filename, 'w')

    def _close(self):
        if self._f is not None:
            self._f.close()
            self._f = None

    def start_measure(self):
        self._open()

    def stop_measure(self):
        self._close()

    def _write_last_line(self):
        i = self._points - 1
        s = '%f' % self._cor[i][0]
        for j in xrange(1, len(self._coordinates)):
            s += ',%f' % self._cor[i][j]
        for j in xrange(0, len(self._values)):
            s += ',%f' % self._val[i][j]
        s += '\n'

        self._f.write(s)
        self._f.flush()

    def add(self, val, cor=None):
        if cor is None:
            if len(self._coordinates) != 0:
                print 'Coordinates expected'
        else:
            if len(self._coordinates) == 0:
                print 'Coordinates not expected'
            self._cor.append(cor)

        self._val.append(val)

        self._points += 1

        if True:
            self._write_last_line()

    def plot(self, **kwargs):
        pass

