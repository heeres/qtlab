
from instrument import Instrument
import types

class example(Instrument):

    def __init__(self, name, address=None, reset=False):
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

        self.add_function('reset')
        self.add_function('step')

        # dummy values for simulating instrument
        self._dummy_value = 1
        self._dummy_speed = 2
        self._dummy_input = [1, 4, 9, 16]
        self._dummy_output = [0, 1, 2, 3]
        self._dummy_gain = 10

        if address == None:
            raise ValueError('Example Instrument requires an address parameter')
        else:
            print 'Example Instrument  address %s' % address

        if reset:
            self.reset()
        else:
            self.get_all()

    def reset(self):
        """Reset example instrument"""

        self.set_value(1)
        self.set_speed('slow')
        self.set_gain(20)

        self.set_ch1_output(0)
        self.set_ch2_output(0)
        self.set_ch3_output(0)
        self.set_ch4_output(0)

        return True

    def get_all(self):

        self.get_value()
        self.get_speed()
        self.get_gain()

        self.get_ch1_output()
        self.get_ch2_output()
        self.get_ch3_output()
        self.get_ch4_output()

        return True

    def do_get_value(self):
        return self._dummy_value

    def do_get_speed(self):
        return self._dummy_speed

    def do_set_speed(self, val):
        self._dummy_speed = val

    def do_get_input(self, channel):
        return self._dummy_input[channel-1]

    def do_get_output(self, channel):
        return self._dummy_output[channel-1]

    def do_set_output(self, val, channel, times2=False):
        if times2:
            val *= 2
        self._dummy_output[channel-1] = val

    def do_set_gain(self, val):
        self._dummy_gain = val

    def step(self, channel, stepsize=0.1):
        '''Step channel <channel>'''
        print 'Stepping channel %d by %f' % (channel, stepsize)
        cur = self.get('ch%d_output' % channel, query=False)
        self.set('ch%d_output' % channel, cur + stepsize)

