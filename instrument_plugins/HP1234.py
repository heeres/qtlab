from instrument import Instrument
import types

class HP1234(Instrument):

    READ_STRINGS = {
    'speed': 'S?',
    'trigger': 'T?'
    }

    def __init__(self, name, address=None):
        Instrument.__init__(self, name)

        self.add_parameter('value', type=types.FloatType,
                flags=Instrument.FLAG_GET)
        self.add_parameter('speed', type=types.IntType,
                flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
           minval=0, maxval=10)

        self.add_function('reset', flags=Instrument.FLAG_KWARGS)

        self.set_default_read_var('value')
        self.set_default_write_var('value')

        if address == None:
            raise ValueError('HP1234 requires an address parameter')
        else:
            print 'HP1234 address %s' % address

    def _do_get_value(self):
        return 1

    def _do_get_speed(self):
        print 'Getting speed'
        return 2

    def _do_set_speed(self, val):
        print 'Set speed to %s' % val
        return True

    def remove(self):
        Instrument.remove(self)

    def reset(self, **kwargs):
        """Reset HP1234"""

        print 'Resetting...'

        return 1
