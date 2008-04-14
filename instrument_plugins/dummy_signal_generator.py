from instrument import Instrument
import types

import time
import math

class dummy_signal_generator(Instrument):

    TYPE_SIN = 1
    TYPE_SQUARE = 2
    TYPE_SAW = 3

    def __init__(self, name, address=None):
        Instrument.__init__(self, name, tags=['measure', 'generate'])

        self.add_parameter('type', type=types.StringType,
                flags=Instrument.FLAG_GETSET)

        self.add_parameter('amplitude', type=types.FloatType,
                flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                minval=0, maxval=1000,
                units='AU')

        self.add_parameter('frequency', type=types.FloatType,
                flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                minval=0, maxval=1000,
                units='Hz')

        self.add_parameter('wave', type=types.FloatType,
                flags=Instrument.FLAG_GET,
                units='AU')

        self.set_type('sin')
        self.set_amplitude(1)
        self.set_frequency(0.2)

        self._start_time = time.time()

    def _do_set_type(self, val):
        val = val.upper()

        if val == 'SIN':
            self._type = self.TYPE_SIN
        elif val == 'SQR':
            self._type = self.TYPE_SQUARE
        elif val == 'SAW':
            self._type = self.TYPE_SAW
        else:
            return

        self._type_str = val

    def _do_get_type(self):
        return self._type_str

    def _do_set_amplitude(self, val):
        self._amplitude = val

    def _do_set_frequency(self, val):
        self._frequency = val

    def _do_get_wave(self):
        dt = time.time() - self._start_time
        if self._type == self.TYPE_SIN:
            return self._amplitude * math.sin(dt * self._frequency * 2 * math.pi)
        elif self._type == self.TYPE_SQUARE:
            arg = dt * self._frequency
            amod = arg - math.floor(arg)
            if amod < 0.5:
                return self._amplitude
            else:
                return -self._amplitude
        elif self._type == self.TYPE_SAW:
            arg = dt * self._frequency
            amod = arg - math.floor(arg)
            if amod < 0.9:
                return (amod - 0.45) * 2 / 0.9 * self._amplitude
            else:
                return -(amod - 0.95) * 2 / 0.1 * self._amplitude
