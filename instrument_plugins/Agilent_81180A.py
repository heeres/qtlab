# Agilent_81180A.py class, to perform the communication between the Wrapper and the device
# Pablo Asshoff, Dec. 2013
# 
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
import numpy

class Agilent_81180A(Instrument):
    '''
    This is the driver for the Agilent_81180A Signal Genarator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Agilent_81180A', address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Agilent_81180A, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Agilent_81180A')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)

        self.add_parameter('channel',
            flags=Instrument.FLAG_GETSET, units='', type=types.IntType)
        self.add_parameter('output',
            flags=Instrument.FLAG_GETSET, units='', type=types.StringType)
        self.add_parameter('frequency',
            flags=Instrument.FLAG_GETSET, units='Hz', minval=1e5, maxval=20e9, type=types.FloatType)
        self.add_parameter('voltage',
            flags=Instrument.FLAG_GETSET, units='V', minval=0.05, maxval=0.5, type=types.FloatType)


        self.add_function('reset')
        self.add_function ('get_all')


        if (reset):
            self.reset()
        else:
            self.get_all()

    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        self._visainstrument.write('*RST\n')
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : get all')
        self.get_channel()
        self.get_output()
        #self.get_power()
        #self.get_phase()
        self.get_frequency()


    def do_set_channel(self, channelnumber):
        '''
        Set the active channel

        Input:
            channel (integer) : 1 or 2

        Output:
            None
        '''
        logging.debug(__name__ + ' : set active channel: %i' % channelnumber)
        self._visainstrument.write('INST:SEL %i \n' % channelnumber) 

    def do_get_channel(self):
        '''
        Reads the active channel from the instrument

        Input:
            None

        Output:
            Active Channel : 1 or 2
        '''
        logging.debug(__name__ + ' : active channel')
        return int(self._visainstrument.ask('INST:SEL?\n'))

    def do_set_output(self, on_off):
        '''
        Set the active channel

        Input:
            on or off (str) : 

        Output:
            None
        '''
        logging.debug(__name__ + ' : set output of active channel: %s' % on_off)
        self._visainstrument.write('OUTP:STAT %s\n' % on_off) 

    def do_get_output(self):
        '''
        Reads weather the output is on or off from the instrument

        Input:
            None

        Output:
            On or Off (1/0)
        '''
        logging.debug(__name__ + ' : output is on or off')
        return str(self._visainstrument.ask('OUTP:STAT?\n'))


    def do_set_frequency(self, freq):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : set frequency to %f' % freq)
        self._visainstrument.write('SOUR:FREQ %f\n' % freq)


    def do_get_frequency(self):
        '''
        Reads the frequency of the signal from the instrument

        Input:
            None

        Output:
            freq (float) : Frequency in Hz
        '''
        logging.debug(__name__ + ' : get frequency')
        return float(self._visainstrument.ask('SOUR:FREQ?\n'))







    def do_set_voltage(self, volt):
        '''
        Set the voltage of the instrument

        Input:
            volt (float) : voltage in V

        Output:
            None
        '''
        logging.debug(__name__ + ' : set vooltage to %f' % volt)
        self._visainstrument.write('SOUR:VOLT %f\n' % volt)


    def do_get_frequency(self):
        '''
        Reads the voltage setting from the instrument

        Input:
            None

        Output:
            volt (float) : voltage in V
        '''
        logging.debug(__name__ + ' : get voltage')
        return float(self._visainstrument.ask('SOUR:VOLT?\n'))







