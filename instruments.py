#instruments.py, code for a collection of instruments.
#Implements creation etc.

import code
import gobject

class Instruments(gobject.GObject):

    __gsignals__ = {
        'instrument-added': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
        'instrument-removed': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
        'instrument-changed': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT]))
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        self._instruments = {}

    def __getitem__(self, key):
        return self.get(key)

    def add(self, ins):
        ins.connect('changed', self._instrument_changed_cb)
        ins.connect('removed', self._instrument_removed_cb)
        self._instruments[ins.get_name()] = ins

    def get(self, name):
        if len(name) != 1:
            return None

        name = name[0]
        if self._instruments.has_key(name):
            return self._instruments[name]
        else:
            return None

    def get_instruments(self):
        return self._instruments

    def create(self, name, type, args={}):
        argstr = ''
        for (name, val) in args.iteritems():
            argstr += ',%s=%s' % (name, val)

        importstr = 'import instrument_plugins.%s\n' % type
        importstr += '_ins = instrument_plugins.%s.%s(name%s)' % (type, type, argstr)
#        print 'Executing: %s' % importstr
        try:
            _ins = None

            code.compile_command(importstr)
            exec importstr

            if _ins is None:
                print 'Unable to create instrument'
                return None

            self.add(_ins)

        except Exception, e:
            print 'error: %s' % e
            return None

        self.emit('instrument-added', name)
        return _ins

    def _instrument_removed_cb(self, sender, name):
        if self._instruments.has_key(name):
            del self._instruments[name]
        self.emit('instrument-removed', name)

    def _instrument_changed_cb(self, sender, name, changes):
        if self._instruments.has_key(name):
            self.emit('instrument-changed', name, changes)

if __name__ == '__main__':
    i = Instruments()
    i.create('test1', 'HP1234')
