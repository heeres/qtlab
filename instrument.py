# instrument.py, base class to implement instrument objects
# Reinier Heeres <reinier@heeres.eu>, 2008
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

import types
import gobject

class Instrument(gobject.GObject):
    """
    Base class for instruments.

    Usage:
    Instrument.get(<variable name or list>)
    Instrument.set(<variable name or list>)

    Implement an instrument:
    In __init__ call self.add_variable(<name>, <option dict>)
    Implement _do_get_<variable> and _do_set_<variable> functions
    """

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
        'removed': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT]))
    }

    FLAG_GET = 0x01
    FLAG_SET = 0x02
    FLAG_GETSET = 0x03
    FLAG_GET_AFTER_SET = 0x04

    FLAG_KWARGS = 0x100

    def __init__(self, name):
        gobject.GObject.__init__(self)

        self._name = name
        self._initialized = False
        self._locked = False

        self._parameters = {}
        self._functions = {}

        self._default_read_var = None
        self._default_write_var = None

    def __str__(self):
        return "Instrument '%s'" % (self.get_name())

    def get_name(self):
        return self._name

    def initialize(self):
        self._initialized = True

    def remove(self):
        self.emit('removed', self.get_name())

    def is_initialized(self):
        return self._initialized

    def add_parameter(self, name, **kwargs):
        options = kwargs
        if not options.has_key('flags'):
            options['flags'] = Instrument.FLAG_GETSET
        self._parameters[name] = options

        # Create proxies
        if options['flags'] & Instrument.FLAG_GET:
            setattr(self, 'get_%s' % name, lambda query=True: self.get(name, query))
        if options['flags'] & Instrument.FLAG_SET:
            setattr(self, 'set_%s' % name, lambda x: self.set(name, x))

#        setattr(self, name,
#            property(lambda: self.get(name), lambda x: self.set(name, x)))

    def get_parameter_options(self, name):
        if self._parameters.has_key(name):
            return self._parameters[name]
        else:
            return None

    def get_parameter_names(self):
        return self._parameters.keys()

    def get_parameters(self):
        return self._parameters

    def _get_value(self, name, query=True):
        if name in self._parameters:
            p = self._parameters[name]
        else:
            print 'Could not retrieve options for parameter %s' % name
            return None

        if not query:
            print 'Getting cached value'
            if 'value' in p:
                return p['value']
            else:
                print 'Trying to access cached value, but none available'
                return None

        if not p['flags'] & Instrument.FLAG_GET:
            print 'Instrument does not support getting of %s' % name
            return None

        try:
            func = getattr(self, '_do_get_%s' % name)
        except Exception, e:
            print 'Instrument does not implement getting of %s' % name
            return None

        return func()

    def get(self, name, query=True):
        if type(name) in (types.ListType, types.TupleType):
            result = {}
            for key in name:
                val = self._get_value(name, query)
                if val is not None:
                    result[key] = val

            return result

        else:
            return self._get_value(name, query)

    def _set_value(self, name, value):
        if self._parameters.has_key(name):
            p = self._parameters[name]
        else:
            return None

        if not p['flags'] & Instrument.FLAG_SET:
            print 'Instrument does not support setting of %s' % name
            return None

        if 'type' in p:
            if p['type'] == types.IntType:
                value = int(value)
            elif p['type'] == types.FloatType:
                value = float(value)
            elif p['type'] == types.StringType:
                pass
            else:
                print 'Unsupported type: %r' % p['type']

        if 'minval' in p and value < p['minval']:
            print 'Trying to set too small value: %s' % value
            return None

        if 'maxval' in p and value > p['maxval']:
            print 'Trying to set too large value: %s' % value
            return None

        try:
            func = getattr(self, '_do_set_%s' % name)
        except Exception, e:
            print 'Instrument does not implement setting of %s' % name
            return None

        ret = func(value)
        p['value'] = ret
        return ret

    def set(self, name, value=None):
        if self._locked:
            print 'Trying to set value of locked instrument (%s)' % self.get_name()
            return False

        result = True
        changed = {}
        if type(name) == types.DictType:
            for key, val in name.iteritems():
                if self._set_value(key, val):
                    changed[key] = val
                else:
                    result = False

        else:
            if self._set_value(name, value):
                changed[name] = value
            else:
                result = False

#        if len(changed) > 0:
#            self.emit('changed', changed)

        return result

    def add_function(self, name, **options):
        if hasattr(self, name):
            f = getattr(self, name)
            if hasattr(f, '__doc__'):
                options['doc'] = getattr(f, '__doc__')

        self._functions[name] = options

    def get_function_options(self, name):
        if self._functions.has_key(name):
            return self._functions[name]
        else:
            return None

    def get_function_names(self):
        return self._functions.keys()

    def get_functions(self):
        return self._functions

    def call(self, funcname, **kwargs):
        f = getattr(self, funcname)
        f(**kwargs)

    def lock(self):
        self._locked = True

    def unlock(self):
        self._locked = False

    def set_default_read_var(self, name):
        self._default_read_var = name

    def set_default_write_var(self, name):
        self._default_write_var = name

