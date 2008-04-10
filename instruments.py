# instruments.py, code for a collection of instruments.
# Reinier heeres, <reinier@heeres.eu>, 2008
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import code
import gobject
import types
import os

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
        '''
        Add instrument to the internal instruments list and listen
        to signals emitted by the instrument.

        Input:  Instrument object
        Output: None
        '''
        ins.connect('changed', self._instrument_changed_cb)
        ins.connect('removed', self._instrument_removed_cb)
        self._instruments[ins.get_name()] = ins

    def get(self, name):
        '''
        Return Instrument object with name 'name'. 
        
        Input:  name of instrument (string)
        Output: Instrument object
        '''
        
        if type(name) == types.TupleType:
            if len(name) != 1:
                return None
            name = name[0]

        if self._instruments.has_key(name):
            return self._instruments[name]
        else:
            return None

    def get_instruments(self):
        '''
        Return the instruments dictionary of name -> Instrument.
        '''
        return self._instruments

    def get_types(self):
        '''
        Return list of supported instrument types
        '''

        ret = []
        filelist = os.listdir('instrument_plugins')
        for path_fn in filelist:
            path, fn = os.path.split(path_fn)
            name, ext = os.path.splitext(fn)
            if ext == '.py' and name != "__init__":
                ret.append(name)

        return ret

    def create(self, name, type, **kwargs):
        '''
        Create an instrument called 'name' of type 'type'.

        Input:  (1) name of the newly created instrument (string)
                (2) type of instrument (string)
                (3) optional: keyword arguments.
                    (1) tags, array of strings representing tags
                    (2) many instruments require address=<address>

        Output: Instrument object
        '''
        argstr = ''
        for (kwname, kwval) in kwargs.iteritems():
            argstr += ',%s=%r' % (kwname, kwval)

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
        '''
        Remove instrument from list and emit instrument-removed signal.

        Input:  (1) sender of signal
                (2) instrument name
        Output: None
        '''
        if self._instruments.has_key(name):
            del self._instruments[name]
        self.emit('instrument-removed', name)

    def _instrument_changed_cb(self, sender, name, changes):
        '''
        Emit signal when values of an Instrument change.

        Input:  (1) sender of message
                (2) name of instrument
                (3) dictionary of changed parameters
        Output: None
        '''
        if self._instruments.has_key(name):
            self.emit('instrument-changed', name, changes)

_instruments = None
def get_instruments():
    global _instruments
    if _instruments is None:
        _instruments = Instruments()
    return _instruments

if __name__ == '__main__':
    i = get_instruments()
    i.create('test1', 'HP1234')
