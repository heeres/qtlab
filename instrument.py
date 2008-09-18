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
import time
import math

import logging

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
                    ([gobject.TYPE_PYOBJECT])),
        'parameter-added': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
        'parameter-changed': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
        'reload': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([]))
    }

    # FLAGS are used to to set extra properties on a parameter.

    FLAG_GET = 0x01             # Parameter is gettable
    FLAG_SET = 0x02             # {arameter is settable
    FLAG_GETSET = 0x03          # Shortcut for GET and SET
    FLAG_GET_AFTER_SET = 0x04   # perform a 'get' after a 'set'
    FLAG_SOFTGET = 0x08         # 'get' operation is simulated in software,
                                # e.g. an internally stored value is returned.
                                # Only use for parameters that cannot be read
                                # back from a device.
    FLAG_PERSIST = 0x10         # Write parameter to config file if it is set,
                                # try to read again for a new instance

    def __init__(self, name, **kwargs):
        gobject.GObject.__init__(self)

        self._name = name
        self._initialized = False
        self._locked = False

        self._options = kwargs
        if 'tags' not in self._options:
            self._options['tags'] = []

        self._parameters = {}
        self._functions = {}
        self._probe_ids = []

        self._default_read_var = None
        self._default_write_var = None

    def __str__(self):
        return "Instrument '%s'" % (self.get_name())

    def get_name(self):
        '''
        Returns the name of the instrument as a string

        Input: None
        Output: name of instrument (string)
        '''

        return self._name

    def get_type(self):
        """Return type of instrument as a string."""
        modname = str(self.__module__)
        return modname.split('.')[1]

    def get_options(self):
        return self._options

    def get_tags(self):
        '''
        Returns array of tags

        Input: None
        Output: array of strings
        '''

        return self._options['tags']

    def add_tag(self, tag):
        '''
        Add tag to the tag list

        Input: tag (string)
        Output: None
        '''

        self._options['tags'].append(tag)

    def has_tag(self, tags):
        '''
        Return whether instrument has any tag in 'tags'
        '''

        if type(tags) is types.ListType:
            for tag in tags:
                if tag in self._options['tags']:
                    return True
            return False

        else:
            if tags in self._options['tags']:
                return True

        return False

    def initialize(self):
        '''
        Currently unsupported; might be used in the future to perform
        extra initialization in sub-classed Instruments.

        Input: None
        Output: None
        '''
        self._initialized = True

    def remove(self):
        '''
        Notifies the environment that the instrument is removed.
        Override this in a sub-classed Instrument to perform cleanup.

        Input: None
        Output: None
        '''
        self.emit('removed', self.get_name())

    def is_initialized(self):
        '''
        Return whether Instrument is initialized.

        Input: None
        Output: Boolean
        '''
        return self._initialized

    def add_parameter(self, name, **kwargs):
        '''
        Create an instrument 'parameter' that is known by the whole
        environment (gui etc).

        This function creates the 'get_<name>' and 'set_<name>' wrapper
        functions that will perform checks on parameters and finally call
        '_do_get_<name>' and '_do_set_<name>'. The latter functions should
        be implemented in the instrument driver.

        Input:
            name (string): the name of the parameter (string)
            optional keywords:
                type: types.FloatType, types.StringType, etc.
                flags: bitwise or of Instrument.FLAG_ constants.
                    If not set, FLAG_GETSET is default
                channels: tuple. Automagically create channels, e.g.
                    (1, 4) will make channels 1, 2, 3, 4.
                minval, maxval: values for bound checking
                units (string): units for this parameter
                maxstep (float): maximum step size when changing parameter
                stepdelay (float): delay when setting steps (in milliseconds)
                tags (array): tags for this parameter
        Output: None
        '''
        options = kwargs
        if 'flags' not in options:
            options['flags'] = Instrument.FLAG_GETSET
        if 'type' not in options:
            options['type'] = types.NoneType
        if 'tags' not in options:
            options['tags'] = []

        # If defining channels call add_parameter for each channel
        if 'channels' in options:
            if len(options['channels']) == 2 and type(options['channels'][0]) is types.IntType:
                minch, maxch = options['channels']
                channels = xrange(minch, maxch + 1)
            else:
                channels = options['channels']

            for i in channels:
                chopt = copy.copy(options)
                del chopt['channels']
                chopt['channel'] = i
                chopt['base_name'] = name

                if 'channel_prefix' in options:
                    var_name = options['channel_prefix'] % i + name
                else:
                    var_name = '%s%s' % (name, i)

                self.add_parameter(var_name, **chopt)

            return

        self._parameters[name] = options

        if 'channel' in options:
            ch = options['channel']
        else:
            ch = None

        if options['flags'] & Instrument.FLAG_GET:
            if ch is not None:
                func = lambda query=True, **lopts: \
                    self.get(name, query=query, channel=ch, **lopts)
            else:
                func = lambda query=True, **lopts: \
                    self.get(name, query=query, **lopts)

            func.__doc__ = 'Get variable %s' % name
            setattr(self, 'get_%s' % name,  func)

        if options['flags'] & Instrument.FLAG_SOFTGET:
            if ch is not None:
                func = lambda query=True, **lopts: \
                    self.get(name, query=False, channel=ch, **lopts)
            else:
                func = lambda query=True, **lopts: \
                    self.get(name, query=False, **lopts)

            func.__doc__ = 'Get variable %s (internal stored value)' % name
            setattr(self, 'get_%s' % name,  func)

        if options['flags'] & Instrument.FLAG_SET:
            if ch is not None:
                func = lambda val, **lopts: self.set(name, val, channel=ch, **lopts)
            else:
                func = lambda val, **lopts: self.set(name, val, **lopts)

            func.__doc__ = 'Set variable %s' % name
            if 'doc' in options:
                func.__doc__ += '\n%s' % options['doc']
            setattr(self, 'set_%s' % name, func)

#        setattr(self, name,
#            property(lambda: self.get(name), lambda x: self.set(name, x)))

        if options['flags'] & self.FLAG_PERSIST:
            import qt
            val = qt.config.get('persist_%s_%s' % (self._name, name))
            options['value'] = val
        else:
            options['value'] = None

        if 'probe_interval' in options:
            interval = options['probe_interval']
            self._probe_ids.append(gobject.timeout_add(interval,
                lambda: self.get(name)))

        self.emit('parameter-added', name)

    def get_parameter_options(self, name):
        '''
        Return list of options for paramter.

        Input: name (string)
        Output: dictionary of options
        '''
        if self._parameters.has_key(name):
            return self._parameters[name]
        else:
            return None

    def set_parameter_options(self, name, **kwargs):
        '''
        Change parameter options.

        Input:  name of parameter (string)
        Ouput:  None
        '''
        if name not in self._parameters:
            print 'Parameter %s not defined' % name
            return None

        for key, val in kwargs.iteritems():
            self._parameters[name][key] = val

        self.emit('parameter-changed', name)

    def get_parameter_tags(self, name):
        '''
        Return tags for parameter 'name'.

        Input:  name of parameter (string)
        Ouput:  array of tags
        '''

        if name not in self._parameters:
            return []

        return self._parameters[name]['tags']

    def add_parameter_tag(self, name, tag):
        '''
        Add tag to list of tags for parameter 'name'.

        Input:  (1) name of parameter (string)
                (2) tag (string)
        Ouput:  None
        '''

        if name not in self._parameters:
            return

        self._parameters[name]['tags'].append(tag)

    def set_parameter_bounds(self, name, minval, maxval):
        '''
        Change the bounds for a parameter.

        Input:  (1) name of parameter (string)
                (2) minimum value
                (3) maximum value
        Output: None
        '''
        self.set_parameter_options(name, minval=minval, maxval=maxval)

    def set_channel_bounds(self, name, channel, minval, maxval):
        '''
        Change the bounds for a channel.

        Input:  (1) name of parameter (string)
                (2) channel number (int)
                (3) minimum value
                (4) maximum value
        Output: None
        '''

        opts = self.get_parameter_options(name)
        if 'channel_prefix' in opts:
            var_name = opts['channel_prefix'] % channel + name
        else:
            var_name = '%s%d' % (name, channel)

        self.set_parameter_options(var_name, minval=minval, maxval=maxval)

    def get_parameter_names(self):
        '''
        Returns a list of parameter names.

        Input: None
        Output: all the paramter names (list of strings)
        '''
        return self._parameters.keys()

    def get_parameters(self):
        '''
        Return the parameter dictionary.

        Input: None
        Ouput: Dictionary, keys are parameter names, values are the options.
        '''
        return self._parameters

    def format_parameter_value(self, param, val):
        opt = self.get_parameter_options(param)

        if 'format' in opt:
            format = opt['format']
        else:
            format = '%s'

        if type(val) in (types.ListType, types.TupleType):
            val = tuple(val)
            if type(format) not in (types.ListType, types.TupleType):
                format = ['%s, ' % format for i in val]

        elif type(val) is types.DictType:
            fmt = ""
            first = True
            for k in val.keys():
                if first:
                    fmt += '%s: %s' % (k, format)
                    first = False
                else:
                    fmt += ', %s: %s' % (k, format)
            format = fmt
            val = tuple(val.values())

        try:
            valstr = format % (val)
        except Exception, e:
            valstr = str(val)

        if 'units' in opt:
            unitstr = ' %s' % opt['units']
        else:
            unitstr = ''

        return '%s%s' % (valstr, unitstr)

    def format_range(self, param):
        popts = self.get_parameter_options(param)
        text = ''
        if 'minval' in popts or 'maxval' in popts:

            if 'format' in popts:
                format = popts['format']
            else:
                format = '%s'

            text = '['
            if 'minval' in popts:
                text += format % popts['minval']
            text += ' : '
            if 'maxval' in popts:
                text += format % popts['maxval']
            text += ']'

        return text

    def format_rate(self, param):
        popts = self.get_parameter_options(param)
        text = ''
        if 'maxstep' in popts:
            text += '%s' % popts['maxstep']
            if 'stepdelay' in popts:
                text += ' / %sms' % popts['stepdelay']
            else:
                test += ' / 100ms'

        return text

    def _get_value(self, name, query=True, **kwargs):
        '''
        Private wrapper function to get a value.

        Input:  (1) name of parameter (string)
                (2) query the instrument or return stored value (Boolean)
                (3) optional list of extra options
        Output: value of parameter (whatever type the instrument driver returns)
        '''

        if name in self._parameters:
            p = self._parameters[name]
        else:
            print 'Could not retrieve options for parameter %s' % name
            return None

        if 'channel' in p and 'channel' not in kwargs:
            kwargs['channel'] = p['channel']

        if not query or p['flags'] & self.FLAG_SOFTGET:
            if 'value' in p:
                return p['value']
            else:
#                logging.debug('Trying to access cached value, but none available')
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

        value = func(**kwargs)
        if 'type' in p:
            try:
                if p['type'] == types.IntType:
                    value = int(value)
                elif p['type'] == types.FloatType:
                    value = float(value)
                elif p['type'] == types.StringType:
                    pass
                elif p['type'] == types.BooleanType:
                    value = bool(value)
                elif p['type'] == types.NoneType:
                    pass
            except:
                logging.warning('Unable to cast value "%s" to %s', value, p['type'])

        p['value'] = value
        return value

    def get(self, name, query=True, **kwargs):
        '''
        Get one or more Instrument parameter values.

        Input:  (1) name of parameter (string, or list/tuple of strings)
                (2) query the instrument or return stored value (Boolean)
                (3) optional list of arguments
        Output: Single value, or dictionary of parameter -> values
                Type is whatever the instrument driver returns.
        '''

        changed = {}

        if type(name) in (types.ListType, types.TupleType):
            result = {}
            for key in name:
                val = self._get_value(name, query, **kwargs)
                if val is not None:
                    result[key] = val
                    changed[key] = val

        else:
            result = self._get_value(name, query, **kwargs)
            changed[name] = result

        if len(changed) > 0 and query:
            self.emit('changed', changed)

        return result

    def _set_value(self, name, value, **kwargs):
        '''
        Private wrapper function to set a value.

        Input:  (1) name of parameter (string)
                (2) value of parameter (whatever type the parameter supports).
                    Type casting is performed if necessary.
                (3) Optional keyword args that will be passed on.
        Output: Value returned by the _do_set_<name> function,
                or result of get in FLAG_GET_AFTER_SET specified.
        '''
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
            elif p['type'] == types.BooleanType:
                value = bool(value)
            elif p['type'] == types.NoneType:
                pass
            else:
                logging.warning('Unsupported type %s for parameter %s',
                    p['type'], name)

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

        if 'maxstep' in p:
            curval = p['value']

            delta = curval - value
            if delta < 0:
                sign = 1
            else:
                sign = -1

            if 'stepdelay' in p:
                delay = p['stepdelay']
            else:
                delay = 50

            while math.fabs(delta) > 0:
                if math.fabs(delta) > p['maxstep']:
                    curval += sign * p['maxstep']
                    delta += sign * p['maxstep']
                else:
                    curval = value
                    delta = 0

                ret = func(curval, **kwargs)

                if delta != 0:
                    time.sleep(delay / 1000.0)

        else:
            ret = func(value, **kwargs)

        if p['flags'] & self.FLAG_GET_AFTER_SET:
            value = self._get_value(name, **kwargs)

        if p['flags'] & self.FLAG_PERSIST:
            import qt
            qt.config.set('persist_%s_%s' % (self._name, name), value)
            qt.config.save()

        p['value'] = value
        return value

    def set(self, name, value, **kwargs):
        '''
        Set one or more Instrument parameter values.

        Checks whether the Instrument is locked and checks value bounds,
        if specified by minval / maxval.

        Input:  (1) name of parameter (string), or dictionary of
                    parameter -> value
                (2) value to send to instrument (whatever the parameter needs)
                (3) Optional keyword args that will be passed on.
        Output: True or False whether the operation succeeded.
                For multiple sets return False if any of the parameters failed.
        '''
        if self._locked:
            print 'Trying to set value of locked instrument (%s)' % self.get_name()
            return False

        result = True
        changed = {}
        if type(name) == types.DictType:
            for key, val in name.iteritems():
                if self._set_value(key, val, **kwargs) is not None:
                    changed[key] = val

        else:
            if self._set_value(name, value, **kwargs) is not None:
                changed[name] = value

        if len(changed) > 0:
            self.emit('changed', changed)

        return result

    def add_function(self, name, **options):
        '''
        Inform the Instrument wrapper class to expose a function.

        Input:  (1) name of function (string)
                (2) dictionary of extra options
        Output: None
        '''
        if hasattr(self, name):
            f = getattr(self, name)
            if hasattr(f, '__doc__'):
                options['doc'] = getattr(f, '__doc__')

        self._functions[name] = options

    def get_function_options(self, name):
        '''
        Return options for an Instrument function.

        Input:  name of function (string)
        Output: dictionary of options for function 'name'
        '''
        if self._functions.has_key(name):
            return self._functions[name]
        else:
            return None

    def get_function_parameters(self, name):
        '''
        Return info about parameters for function.
        '''
        if self._functions.has_key(name):
            if self._functions[name].has_key('parameters'):
                return self._functions[name]['parameters']
        return None

    def get_function_names(self):
        '''
        Return the list of exposed Instrument function names.

        Input: None
        Output: list of function names (list of strings)
        '''
        return self._functions.keys()

    def get_functions(self):
        '''
        Return the exposed functions dictionary.

        Input: None
        Ouput: Dictionary, keys are function  names, values are the options.
        '''
        return self._functions

    def call(self, funcname, **kwargs):
        '''
        Call the exposed function 'funcname'.

        Input:  (1) function name (string)
                (2) Optional keyword args that will be passed on.
        Output: None
        '''
        f = getattr(self, funcname)
        f(**kwargs)

    def lock(self):
        '''
        Lock the instrument; no parameters can be changed until the Instrument
        is unlocked.

        Input: None
        Output: None
        '''
        self._locked = True

    def unlock(self):
        '''
        Unlock the instrument; parameters can be changed.

        Input: None
        Output: None
        '''
        self._locked = False

    def set_default_read_var(self, name):
        '''
        For future use.

        Input: name of variable (string)
        Output: None
        '''
        self._default_read_var = name

    def set_default_write_var(self, name):
        '''
        For future use.

        Input: name of variable (string)
        Output: None
        '''
        self._default_write_var = name

    def reload(self):
        '''
        Signal the Instruments collection object to reload this instrument.

        Note that this function does not return anything! The preferred
        function to use is Instruments.reload(ins); see that for more details.

        Input:
            None
        Output:
            None
        '''
        self.emit('reload')
