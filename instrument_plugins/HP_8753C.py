# HP_8753C.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <mcschaafsma@gmail.com>, 2008
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

from instrument import Instrument
import visa
import types
import logging
from time import sleep
import struct

class HP_8753C(Instrument):
    '''
    This is the python driver for the HP 8753C
    network analyzer

    Usage:
    Initialise with
    <name> = instruments.create('<name>', 'HP_8753C', address='<GPIB address>',
        reset=<bool>)

    The last parameter is optional. Default is reset=False

    TODO:
    1. make todo list
    2. ask Pieter about the purpose of the specific tools
    3. fix docstrings
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the HP_8753C, and communicates with the wrapper

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false
        '''
        Instrument.__init__(self, name)

        self._address = address
        self._visainstrument = visa.instrument(self._address)

        self.add_parameter('IF_Bandwidth', flags=Instrument.FLAG_SET, type=types.IntType)
        self.add_parameter('numpoints', flags=Instrument.FLAG_SET, type=types.IntType)
        self.add_parameter('start_freq', flags=Instrument.FLAG_SET, type=types.FloatType)
        self.add_parameter('stop_freq', flags=Instrument.FLAG_SET, type=types.FloatType)
        self.add_parameter('power', flags=Instrument.FLAG_SET, type=types.FloatType)

        self.add_function('set_freq_3GHz')
        self.add_function('set_freq_6GHz')
        self.add_function('set_measurement_S11')
        self.add_function('set_measurement_S22')
        self.add_function('set_measurement_S12')
        self.add_function('set_measurement_S21')
        self.add_function('set_conversion_off')
        self.add_function('set_average_off')
        self.add_function('set_smooth_off')
        self.add_function('set_correction_off')
        self.add_function('set_format_logm')
        self.add_function('set_format_phas')
        self.add_function('set_trigger_exttoff')
        self.add_function('set_trigger_hold')
        self.add_function('send_trigger')
        self.add_function('reset')
        self.add_function('set_lin_freq')

    def default_init(self):

        sl = 1

        print 'resetting'
        self.reset()
        sleep(sl)

        print 'set correction off'
        self.set_correction_off()
        sleep(sl)
        print 'set averaging off'
        self.set_average_off()
        sleep(sl)
        print 'set smoothing off'
        self.set_smooth_off()
        sleep(sl)
        print 'set conversion off'
        self.set_conversion_off()
        sleep(sl)

        print 'set IF bandwidth'
        self.set_IF_Bandwidth(3000)
        sleep(sl)
        print 'set numpoints'
        self.set_numpoints(401)
        sleep(sl)
        print 'set format logm'
        self.set_format_logm()
        sleep(sl)
        print 'set measurement S11'
        self.set_measurement_S11()
        sleep(sl)
        print 'set trigger exttoff'
        self.set_trigger_exttoff()
        sleep(sl)
        print 'set trigger hold'
        self.set_trigger_hold()
        sleep(sl)

        print 'set start freq'
        self.set_start_freq(10e6)
        sleep(sl)
        print 'set stop freq'
        self.set_stop_freq(3e9)
        sleep(sl)


    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('PRES;')

    def read(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        data = self._visainstrument.ask('FORM2;DISPDATA;OUTPFORM')
        d = [struct.unpack('>f', data[i:i+4])[0] for i in range(4, len(data),8)]
        return d

    def set_freq_3GHz(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('FREQRANG3GHz')

    def set_freq_6GHz(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('FREQRANG6GHz')

    def set_measurement_S11(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('S11;')

    def set_measurement_S22(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('S22;')

    def set_measurement_S12(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('S12;')

    def set_measurement_S21(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('S21;')

    def set_conversion_off(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('CONVOFF;')

    def set_average_off(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('AVEROOFF;')

    def set_smooth_off(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('SMOOOOFF;')

    def _do_set_IF_Bandwidth(self, bw):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('IFBW%d;' %bw)

    def set_correction_off(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('CORROFF;CORIOFF;')

    def set_format_logm(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('LOGM;')

    def set_format_phas(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('PHAS;')

    def set_trigger_exttoff(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('EXTTOFF;')

    def set_trigger_hold(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('HOLD;')

    def send_trigger(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('SING;')

    def _do_set_numpoints(self, numpts):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('POIN%d;' %numpts)

    def _do_set_start_freq(self, freq):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('STAR%eHZ;' %freq)

    def _do_set_stop_freq(self, freq):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('STOP%eHZ;' %freq)

    def _do_set_power(self, pow):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('POWE%.3e;' % pow)

    def set_lin_freq(self):
        '''
        Do some stuff

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('LINFREQ;')
