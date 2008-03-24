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
import copy

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
    FLAG_SOFTGET = 0x08

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
        if 'flags' not in options:
            options['flags'] = Instrument.FLAG_GETSET
        if 'type' not in options:
            options['type'] = types.NoneType

        # If defining channels call add_parameter for each channel 
        if 'channels' in options:
            if len(options['channels']) != 2:
                print 'Error: channels has to have a valid range'
                return None

            minch, maxch = options['channels']
            for i in xrange(minch, maxch + 1):
                chopt = copy.copy(options)
                del chopt['channels']
                chopt['channel'] = i
                chopt['base_name'] = name
                self.add_parameter('%s%d' % (name, i), **chopt)

            return

        self._parameters[name] = options

        if 'channel' in options:
            ch = options['channel']
            more_opts = {'channel': ch}
        else:
            more_opts = {}

        if options['flags'] & Instrument.FLAG_GET:
            setattr(self, 'get_%s' % name, lambda query=True: \
                self.get(name, query=query, **more_opts))
        if options['flags'] & Instrument.FLAG_SOFTGET:
            setattr(self, 'get_%s' % name, lambda: \
                self.get(name, query=False, **more_opts))
        if options['flags'] & Instrument.FLAG_SET:
            setattr(self, 'set_%s' % name, lambda val: \
                self.set(name, val, **more_opts))

#        setattr(self, name,
#            property(lambda: self.get(name), lambda x: self.set(name, x)))

    def get_parameter_options(self, name):
        if self._parameters.has_key(name):
            return self._parameters[name]
        else:
            return None

    def set_parameter_options(self, name, **kwargs):
        if name not in self._parameters:
            print 'Parameter %s not defined' % name
            return None

        for key, val in kwargs.iteritems():
            self._parameters[name][key] = val

    def set_parameter_bounds(self, name, minval, maxval):
        self.set_parameter_options(name, minval=minval, maxval=maxval)

    def set_channel_bounds(self, name, channel, minval, maxval):
        self.set_parameter_options('%s%d' % (name, channel), \
            minval=minval, maxval=maxval)

    def get_parameter_names(self):
        return self._parameters.keys()

    def get_parameters(self):
        return self._parameters

    def _get_value(self, name, query=True, **kwargs):
        if name in self._parameters:
            p = self._parameters[name]
        else:
            print 'Could not retrieve options for parameter %s' % name
            return None

        if 'channel' in p and 'channel' not in kwargs:
            kwargs['channel'] = p['channel']

        if not query:
            print 'Getting cached value'
            if 'value' in p:
                return p['value']
            else:
                print 'Trying to access cached value, but none available'
                return None

        # Check this here; getting of cached values should work
        if not p['flags'] & Instrument.FLAG_GET:
            print 'Instrument does not support getting of %s' % name
            return None

        if 'base_name' in p:
            base_name = p['base_name']
        else:
            base_name = name

        try:
            func = getattr(self, '_do_get_%s' % base_name)
        except Exception, e:
            print 'Instrument does not implement getting of %s' % base_name
            return None

        return func(**kwargs)

    def get(self, name, query=True, **kwargs):
        if type(name) in (types.ListType, types.TupleType):
            result = {}
            for key in name:
                val = self._get_value(name, query, **kwargs)
                if val is not None:
                    result[key] = val

            return result

        else:
            return self._get_value(name, query, **kwargs)

    def _set_value(self, name, value, **kwargs):
        if self._parameters.has_key(name):
            p = self._parameters[name]
        else:
            return None

        if not p['flags'] & Instrument.FLAG_SET:
            print 'Instrument does not support setting of %s' % name
            return None

        if 'channel' in p and 'channel' not in kwargs:
            kwargs['channel'] = p['channel']
         
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

        if 'base_name' in p:
            base_name = p['base_name']
        else:
            base_name = name

        try:
            func = getattr(self, '_do_set_%s' % base_name)
        except Exception, e:
            print 'Instrument does not implement setting of %s' % base_name
            return None

        ret = func(value, **kwargs)
        if p['flags'] & self.FLAG_GET_AFTER_SET:
                ret = self._get_value(name, **kwargs)

        p['value'] = ret
        return ret

    def set(self, name, value, **kwargs):
        if self._locked:
            print 'Trying to set value of locked instrument (%s)' % self.get_name()
            return False

        result = True
        changed = {}
        if type(name) == types.DictType:
            for key, val in name.iteritems():
                if self._set_value(key, val, **kwargs):
                    changed[key] = val
                else:
                    result = False

        else:
            if self._set_value(name, value, **kwargs):
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

