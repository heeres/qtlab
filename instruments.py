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
import logging
import sys
import instrument

import config

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
                    ([gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT])),
        'tags-added': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT]))
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        self._instruments = {}
        self._instruments_info = {}
        self._tags = ['All']

    def __getitem__(self, key):
        return self.get(key)

    def __repr__(self):
        s = "Instruments list %s" % str(self.get_instrument_names())
        return s

    def add(self, ins, create_args={}):
        '''
        Add instrument to the internal instruments list and listen
        to signals emitted by the instrument.

        Input:  Instrument object
        Output: None
        '''
        info = {'create_args': create_args}
        info['changed_hid'] = ins.connect('changed', self._instrument_changed_cb)
        info['removed_hid'] = ins.connect('removed', self._instrument_removed_cb)
        info['reload_hid'] = ins.connect('reload', self._instrument_reload_cb)
        self._instruments[ins.get_name()] = ins
        self._instruments_info[ins.get_name()] = info

        newtags = []
        for tag in ins.get_tags():
            if tag not in self._tags:
                self._tags.append(tag)
                newtags.append(tag)
        if len(newtags) > 0:
            self.emit('tags-added', newtags)

    def get(self, name):
        '''
        Return Instrument object with name 'name'. 
        
        Input:  name of instrument (string)
        Output: Instrument object
        '''

        if isinstance(name, instrument.Instrument):
            return name

        if type(name) == types.TupleType:
            if len(name) != 1:
                return None
            name = name[0]

        if self._instruments.has_key(name):
            return self._instruments[name]
        else:
            return None

    def get_instrument_names(self):
        keys = self._instruments.keys()
        keys.sort()
        return keys

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
        pdir = os.path.join(config.get_workdir(), 'instrument_plugins')
        filelist = os.listdir(pdir)
        for path_fn in filelist:
            path, fn = os.path.split(path_fn)
            name, ext = os.path.splitext(fn)
            if ext == '.py' and name != "__init__" and name[0] != '_':
                ret.append(name)

        ret.sort()
        return ret

    def type_exists(self, typename):
        driverfn = os.path.join(config.get_workdir(), 'instrument_plugins')
        driverfn = os.path.join(driverfn, '%s.py' % typename)
        return os.path.exists(driverfn)

    def get_type_arguments(self, typename):
        '''
        Return info about the arguments of the constructor of 'typename'.

        Input:
            typename (string)
        Output:
            Tuple of (args, varargs, varkw, defaults)
            args: argument names
            varargs: name of '*' argument
            varkw: name of '**' argument
            defaults: default values
        '''

        importstr = """if True:
                import instrument_plugins.%(type)s
                import inspect
                _info = inspect.getargspec(instrument_plugins.%(type)s.%(type)s.__init__)""" \
            % {'type': typename}

        try:
            _info = None
            code.compile_command(importstr)
            exec importstr
            return _info

        except Exception, e:
            return None

    def get_instrument_by_type(self, typename):
        '''
        Return existing Instrument instance of type 'typename'.
        '''

        for name, ins in self._instruments.items():
            if ins.get_type() == typename:
                return ins
        return None

    def get_tags(self):
        '''
        Return list of tags present in instruments.
        '''

        return self._tags

    def create(self, name, instype, **kwargs):
        '''
        Create an instrument called 'name' of type 'type'.

        Input:  (1) name of the newly created instrument (string)
                (2) type of instrument (string)
                (3) optional: keyword arguments.
                    (1) tags, array of strings representing tags
                    (2) many instruments require address=<address>

        Output: Instrument object
        '''

        if not self.type_exists(instype):
            logging.error('Instrument type %s not supported', instype)
            return None

        argstr = ''
        for (kwname, kwval) in kwargs.iteritems():
            if kwname in ('tags'):
                continue
            argstr += ',%s=%r' % (kwname, kwval)

        importstr = """if True:
                import instrument_plugins.%(type)s
                _ins = instrument_plugins.%(type)s.%(type)s(%(name)r%(args)s)""" \
            % {'type': instype, 'name': name, 'args': argstr}

        _ins = None

        code.compile_command(importstr)
        exec importstr

        if _ins is None:
            logging.error('Unable to create instrument')
            return None

        self.add(_ins, create_args=kwargs)

        self.emit('instrument-added', _ins)
        return _ins

    def reload_module(self, instype):
        modname = 'instrument_plugins.%s' % instype
        for mod in sys.modules:
            if mod == modname:
                logging.info('Reloading module %s', mod)
                reload(sys.modules[mod])
                break

    def reload(self, ins):
        '''
        Try to reload the module associated with instrument 'ins' and return
        the new instance. Note that references to the old instance will not
        be replaced, so care has to be taken that you refer to the newly
        created object.

        In general about reloading: your milage may vary!

        Input:
            ins (Instrument or string): the instrument to reload

        Output:
            Reloaded instrument
        '''

        if type(ins) is types.StringType:
            ins = self.get(ins)
        if ins is None:
            return None

        insname = ins.get_name()
        instype = ins.get_type()
        kwargs = self._instruments_info[insname]['create_args']

        self.reload_module(instype)
        ins.remove()

        return self.create(insname, instype, **kwargs)

    def _instrument_removed_cb(self, sender, name):
        '''
        Remove instrument from list and emit instrument-removed signal.

        Input:  (1) sender of signal
                (2) instrument name
        Output: None
        '''
        if self._instruments.has_key(name):
            del self._instruments[name]
            del self._instruments_info[name]

        self.emit('instrument-removed', name)

    def _instrument_reload_cb(self, sender):
        '''
        Reload instrument and emit instrument-changed signal.

        Input:
            sender (instrument): instrument to be reloaded

        Output:
            None
        '''
        newins = self.reload(sender)
        self.emit('instrument-changed', newins, {})

    def _instrument_changed_cb(self, sender, changes):
        '''
        Emit signal when values of an Instrument change.

        Input:
            sender (Instrument): sender of message
            changes (dict): dictionary of changed parameters

        Output:
            None
        '''

        self.emit('instrument-changed', sender, changes)

_instruments = None
def get_instruments():
    global _instruments
    if _instruments is None:
        _instruments = Instruments()
    return _instruments

if __name__ == '__main__':
    i = get_instruments()
    i.create('test1', 'HP1234')
