# HP_3325B.py class, to perform the communication between the Wrapper and the device
# Gabriele de Boo <ggdeboo@gmail.com> 2014
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
from visa import instrument
import types
import logging
from time import sleep

class HP_3325B(Instrument):
    '''
    This is the python driver for the HP 3325B
    synthesizer

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'HP_33120A', address='<GPIB address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the HP_3325B, and communicates with the wrapper.
        Our model doesn't have the high voltage option so I didn't add the use 
        of that option in this wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false

        Output:
            None
        '''
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = instrument(self._address)

        self.add_parameter('frequency',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=0.0, maxval=60.999999e6,
                units='Hz')
        self.add_parameter('amplitude',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=0.001, maxval=40.0,
                units='V')
        self.add_parameter('offset',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=-5.0, maxval=5.0,
                units='V')
        self.add_parameter('connected_output',
                type=types.StringType,
                flags=Instrument.FLAG_GETSET,
                option_list=['front','rear'])
        self.add_parameter('function',
                type=types.StringType,
                flags=Instrument.FLAG_GETSET,
                option_list=['DC','sine','square','triangle','positive ramp','negative ramp'])
        self.add_parameter('amplitude_modulation_status',
                type=types.BooleanType,
                flags=Instrument.FLAG_GET)

        self.add_function('reset')
        self.add_function('get_all')
 
        if reset:
            self.reset()
        else:
            self.get_all()

    def get_all(self):
        self.get_frequency()
        self.get_connected_output()
        self.get_amplitude()
        self.get_offset()
        self.get_function()
        self.get_amplitude_modulation_status()

    def reset(self):
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')
        sleep(0.1)
        self.get_all()

# Parameters

    def do_set_frequency(self, freq):
        '''
        Sets the frequency. Uses Hz.
        '''
        logging.debug(__name__ + ' : Setting frequency')
        self._visainstrument.write('FR%8.3fHZ' % freq)

    def do_get_frequency(self):
        logging.debug(__name__ + ' : Getting frequency')
        response = self._visainstrument.ask('IFR')
        if response[-2:] == 'HZ':
            freq = response[2:-2]
        elif response[-2:] == 'KH':
            freq = response[2:-2]*1e3
        elif response[-2:] == 'MH':
            freq = response[2:-2]*1e6
        else:
            logging.warning(__name__ + ' : Response incorrect.')
            return False
        return float(freq)

    def do_set_amplitude(self, amp):
        logging.debug(__name__ + ' : Setting amplitude')
        self._visainstrument.write('AM%5.6fVO' % amp)

    def do_get_amplitude(self):
        '''
        Gets the amplitude in V.
        '''
        logging.debug(__name__ + ' : Getting amplitude')
        response = self._visainstrument.ask('IAM')
        if not response.startswith('AM'):
            logging.warning(__name__ + ' : Wrong response.')
            raise ValueError('Response from instrument was wrong.')
        amp = response[2:-2]
        if response[-2:] == 'VO':
            return amp
        elif response[-2:] == 'MV':
            return amp*1000
#        elif response[-2:] == 'DB':
#        elif response[-2:] == 'DV':

    def do_set_offset(self, amp):
        logging.debug(__name__ + ' : Setting amplitude')
        self._visainstrument.write('OF%5.6fVO' % amp)

    def do_get_offset(self):
        '''
        Gets the amplitude in V.
        '''
        logging.debug(__name__ + ' : Getting amplitude')
        response = self._visainstrument.ask('IOF')
        if not response.startswith('OF'):
            logging.warning(__name__ + ' : Wrong response.')
            raise ValueError('Response from instrument was wrong.')
        amp = response[2:-2]
        if response[-2:] == 'VO':
            return amp
        elif response[-2:] == 'MV':
            return amp*1000

    def do_get_connected_output(self):
        logging.debug(__name__ + ' : Getting which output is connected.')
        response = self._visainstrument.ask('IRF')
        if response == 'RF1':
            return 'front'
        elif response == 'RF2':
            return 'rear'
        else:
            logging.warning(__name__ + ' : Response incorrect.')
            return False

    def do_set_connected_output(self, output):
        '''
        Options are 'front' and 'rear'.
        '''
        logging.debug(__name__ + ' : Setting the connected output to %s.' % output)
        if output == 'FRONT':
            self._visainstrument.write('RF1')
        else:
            self._visainstrument.write('RF2')

    def do_get_function(self):
        '''
        Get the current waveform function of the instrument.
        options are:
            'DC'
            'sine'
            'square'
            'triangle'
            'positive ramp'
            'negative ramp'
        '''
        logging.debug(__name__ + ' : Getting the waveform function.')
        response = self._visainstrument.ask('IFU')
        if not response.startswith('FU'):
            logging.warning(__name__ + ' : Wrong response.')
            raise ValueError('Response from instrument was wrong.')
        if response[2] == '0':
            return 'DC'
        elif response[2] == '1':
            return 'sine'
        elif response[2] == '2':
            return 'square'
        elif response[2] == '3':
            return 'triangle'
        elif response[2] == '4':
            return 'positive ramp'
        elif response[2] == '5':
            return 'negative ramp'

    def do_set_function(self, function):
        '''
        Set the current waveform function of the instrument.
        options are:
            'DC'
            'sine'
            'square'
            'triangle'
            'positive ramp'
            'negative ramp'
        '''
        logging.debug(__name__ + ' : Setting the waveform function to %s.' % function)
        if function == 'DC':
            self._visainstrument.write('FU0')
        if function == 'SINE':
            self._visainstrument.write('FU1')
        if function == 'SQUARE':
            self._visainstrument.write('FU2')
        if function == 'TRIANGLE':
            self._visainstrument.write('FU3')
        if function == 'POSITIVE RAMP':
            self._visainstrument.write('FU4')
        if function == 'NEGATIVE RAMP':
            self._visainstrument.write('FU5')

    def do_get_amplitude_modulation_status(self):
        '''
        Get the amplitude modulation status.
        Returns True or False
        '''
        logging.debug(__name__ + ' : Getting the amplitude modulation status.')
        response = self._visainstrument.ask('IMA')
        if not response.startswith('MA'):
            logging.warning(__name__ + ' : Wrong response.')
            raise ValueError('Response from instrument was wrong.')
        if response[2] == '0':
            return False
        if response[2] == '1':
            return True
