
from instrument import Instrument
import types

import sys,IPython.ultraTB
sys.excepthook = IPython.ultraTB.FormattedTB(mode='Verbose',color_scheme='Linux', call_pdb=1)

class example(Instrument):

    READ_STRINGS = {
    'speed': 'S?',
    'trigger': 'T?'
    }

    def __init__(self, name, address=None):
        Instrument.__init__(self, name, tags=['measure'])

        self.add_parameter('value', type=types.FloatType,
                flags=Instrument.FLAG_GET,
                tags=['measure'])
        self.add_parameter('speed', type=types.IntType,
                flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
                minval=0, maxval=2,
                format_map={0: 'slow', 1: 'medium', 2: 'fast'})
        self.add_parameter('input', type=types.FloatType,
                flags=Instrument.FLAG_GET,
                channels=(1, 4),
                minval=0, maxval=10,
                tags=['measure'],
                units='mV')
        self.add_parameter('output', type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 4), channel_prefix='ch%d_',
                minval=0, maxval=10,
                maxstep=0.1, stepdelay=50,
                tags=['sweep'],
                units='mV')
        self.add_parameter('gain', type=types.FloatType,
                flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET | Instrument.FLAG_PERSIST,
                minval=1, maxval=1e9,
                format='%.02e')

#        self.set_channel_bounds('output', 1, -1, 1)

        self.add_function('reset')
        self.add_function('step')

        self.set_default_read_var('value')
        self.set_default_write_var('value')

        if address == None:
            raise ValueError('HP1234 requires an address parameter')
        else:
            print 'HP1234 address %s' % address

        self.reset()

    def do_get_value(self):
        return 1

    def do_get_speed(self):
        print 'Getting speed'
        return 2

    def do_set_speed(self, val):
        print 'Set speed to %s' % val
        return True

    def do_get_input(self, channel):
        return channel * channel

    def do_get_output(self, channel):
        return 0

    def do_set_output(self, val, channel, times2=False):
        if times2:
            val *= 2

    def do_set_gain(self, val):
        return val

    def remove(self):
        Instrument.remove(self)

    def reset(self, **kwargs):
        """Reset example instrument"""

        self.get_ch1_output()
        self.get_ch2_output()
        self.get_ch3_output()
        self.get_ch4_output()
        return True

    def step(self, channel, stepsize=0.1):
        '''Step channel <channel>'''
        print 'Stepping channel %d by %f' % (channel, stepsize)
        cur = self.get('ch%d_output' % channel, query=False)
        self.set('ch%d_output' % channel, cur + stepsize)

