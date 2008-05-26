# Keithley_2700.py class, to perform the communication between the Wrapper and the device
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
import numpy
import struct

class Keithley_2700(Instrument):
    '''
    This is the driver for the Keithley 2700 Multimeter

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keithley_2700', address='<GBIP address>',
        reset=<bool>)

    The reset is optional, default is False

    TODO
    1) Fix docstrings
    2) Fix formats
    '''
    
    def __init__(self, name, address, reset=False):
        '''
        Initializes the Keithley_2700, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false

        Output:
            None
        '''
        # Initialize wrapper functions
        Instrument.__init__(self, name, tags=['physical'])

        logging.debug(__name__ + ' : Initializing instrument')

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._modes = ['VOLT:AC', 'VOLT:DC', 'CURR:AC', 'CURR:DC', 'RES',
            'FRES', 'TEMP', 'FREQ']

        # Add parameters to wrapper
        self.add_parameter('range',
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='', minval=0.1, maxval=1000)
        self.add_parameter('trigger_mode',
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='')
        self.add_parameter('trigger_count',
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='num')
        self.add_parameter('trigger_delay',
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='sec', minval=0, maxval=999999.999)
        self.add_parameter('trigger_source',
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='')
        self.add_parameter('trigger_timer',
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='sec', minval=0.001, maxval=99999.999)
        self.add_parameter('mode',
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='')
        self.add_parameter('digits',
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='num', minval=4, maxval=7)
        self.add_parameter('readval', flags=Instrument.FLAG_GET, units='arb. units',
            type=types.FloatType)
        self.add_parameter('readlastval', flags=Instrument.FLAG_GET, units='arb. units',
            type=types.FloatType)
        self.add_parameter('integrationtime',
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='num', type=types.FloatType, minval=2e-4, maxval=1)

        # Add functions to wrapper
        self.add_function('set_mode_volt_ac')
        self.add_function('set_mode_volt_dc')
        self.add_function('set_mode_curr_ac')
        self.add_function('set_mode_curr_dc')
        self.add_function('set_mode_res')
        self.add_function('set_mode_fres')
        self.add_function('set_mode_temp')
        self.add_function('set_mode_freq')
        self.add_function('set_range_auto')
        self.add_function('set_trigger_cont')
        self.add_function('set_trigger_disc')
        self.add_function('reset_trigger')
        self.add_function('reset')
        self.add_function('get_all')

        self.add_function('read')
        self.add_function('readlast')

        if reset:
            self.reset()
        else:
            self.get_all()

# functions
    def reset(self):
        '''
        Resets instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')
        self.get_all()

    def get_all(self):
        '''
        Reads all relevant parameters from instrument

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Get all relevant data from device')
        self.get_range()
        self.get_trigger_mode()
        self.get_trigger_count()
        self.get_trigger_delay()
        self.get_trigger_source()
        self.get_trigger_timer()
        self.get_mode()
        self.get_digits()

    def read(self):
        '''
        Triggers the device and reads the string
        Do not use when trigger mode is 'CONT'
        Instead use readlast

        Input:
            None

        Output:
            value (string) : current value on input  FIXME make float
        '''
        # needs to be enhanced!! Depends on trigger
        logging.debug(__name__ + ' : Trigger and read')
        return self._visainstrument.ask('READ?')

    def readlast(self):
        '''
        Reads last string from device

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Read last data')
        return self._visainstrument.ask('DATA?')

    def _do_get_readlastval(self):
        '''
        Returns the current float value

        Input:
            None

        Output:
            None
        '''
        tekst = self.readlast()
        return float(tekst[0:15])

    def _do_get_readval(self):
        '''
        Triggers the device and reads float value
        Do not use when trigger mode is 'CONT'
        Instead use readlastval

        Input:
            None

        Output:
            None
        '''
        tekst = self.read()
        return float(tekst[0:15])

    def set_mode_volt_ac(self):
        '''
        Set mode to AC Voltage

        Input:
            None

        Output:
            None
        '''
        self._do_set_mode('VOLT:AC')

    def set_mode_volt_dc(self):
        '''
        Set mode to DC Voltage

        Input:
            None

        Output:
            None
        '''
        self._do_set_mode('VOLT:DC')

    def set_mode_curr_ac(self):
        '''
        Set mode to AC Current

        Input:
            None

        Output:
            None
        '''
        self._do_set_mode('CURR:AC')

    def set_mode_curr_dc(self):
        '''
        Set mode to DC Current

        Input:
            None

        Output:
            None
        '''
        self._do_set_mode('CURR:DC')

    def set_mode_res(self):
        '''
        Set mode to Resistance

        Input:
            None

        Output:
            None
        '''
        self._do_set_mode('RES')

    def set_mode_fres(self):
        '''
        Set mode to 'four wire Resistance'

        Input:
            None

        Output:
            None
        '''
        self._do_set_mode('FRES')

    def set_mode_temp(self):
        '''
        Set mode to Temperature

        Input:
            None

        Output:
            None
        '''
        self._do_set_mode('TEMP')

    def set_mode_freq(self):
        '''
        Set mode to Frequency

        Input:
            None

        Output:
            None
        '''
        self._do_set_mode('FREQ')

    def set_range_auto(self, mode=None):
        '''
        Set range to Auto

        Input:
            None

        Output:
            None
        '''
        if mode is None:
            mode = self._do_get_mode(query=False)
        self._set_func_par_value(mode,'RANG:AUTO', 'ON')

    def set_trigger_cont(self):
        '''
        Set trigger mode to Continuous

        Input:
            None

        Output:
            None
        '''
        self._do_set_trigger_mode('ON')

    def set_trigger_disc(self):
        '''
        Set trigger mode to Discrete

        Input:
            None

        Output:
            None
        '''
        self._do_set_trigger_mode('OFF')

    def reset_trigger(self):
        '''
        Reset trigger status

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Resetting trigger')
        self._visainstrument.write(':ABOR')

# parameters
    def _do_set_range(self, val, mode=None):
        '''
        Set range to the specified value

        Input:
            None

        Output:
            None
        '''
        if mode is None:
            mode = self._do_get_mode(query=False)
        self._set_func_par_value(mode,'RANG', val)

    def _do_get_range(self, mode=None):
        '''
        Get range

        Input:
            None

        Output:
            None
        '''
        if mode is None:
            mode = self._do_get_mode(query=False)
        return self._get_func_par(mode, 'RANG')

    def _do_set_digits(self, val, mode=None):
        '''
        Set digits to the specified value ?? Which values are alowed?

        Input:
            None

        Output:
            None
        '''
        if mode is None:
            mode = self._do_get_mode(query=False)
        self._set_func_par_value(mode,'DIG', val)

    def _do_get_digits(self, mode=None):
        '''
        Get digits

        Input:
            None

        Output:
            None
        '''
        if mode is None:
            mode = self._do_get_mode(query=False)
        return self._get_func_par(mode, 'DIG')

    def _do_set_integrationtime(self, val, mode=None):
        '''
        Set integration time to the specified value

        Input:
            None

        Output:
            None
        '''
        if mode is None:
            mode = self._do_get_mode(query=False)
        self._set_func_par_value(mode,'APER', val)

    def _do_get_integrationtime(self, mode=None):
        '''
        Get integration time

        Input:
            None

        Output:
            None
        '''
        if mode is None:
            mode = self._do_get_mode(query=False)
        return self._get_func_par(mode, 'APER')

# core functionality
    def _do_set_trigger_mode(self, mode):
        '''
        Set trigger mode to the specified value 'ON' or 'OFF'

        Input:
            None

        Output:
            None
        '''
        if mode is None:
            mode = self._do_get_mode(query=False)
        self._set_func_par_value('INIT', 'CONT', mode)

    def _do_get_trigger_mode(self):
        '''
        Get trigger mode from instrument

        Input:
            None

        Output:
            None
        '''
        return self._get_func_par('INIT', 'CONT')

    def _do_set_trigger_count(self, val):
        '''
        Set trigger count
        if val>9999 count is set to INF

        Input:
            None

        Output:
            None
        '''
        if (val>9999):
            val='INF'
        self._set_func_par_value('TRIG', 'COUN', val)

    def _do_get_trigger_count(self):
        '''
        Get trigger count

        Input:
            None

        Output:
            None
        '''
        return self._get_func_par('TRIG', 'COUN')

    def _do_set_trigger_delay(self, val):
        '''
        Set trigger delay to the specified value

        Input:
            None

        Output:
            None
        '''
        self._set_func_par_value('TRIG', 'DEL', val)

    def _do_get_trigger_delay(self):
        '''
        Read trigger delay from instrument

        Input:
            None

        Output:
            None
        '''
        return self._get_func_par('TRIG', 'DEL')

    def _do_set_trigger_source(self, val):
        '''
        Set trigger source

        Input:
            None

        Output:
            None
        '''
        self._set_func_par_value('TRIG', 'SOUR', val)

    def _do_get_trigger_source(self):
        '''
        Read trigger source from instrument

        Input:
            None

        Output:
            None
        '''
        return self._get_func_par('TRIG', 'SOUR')

    def _do_set_trigger_timer(self, val):
        '''
        Set the trigger timer

        Input:
            None

        Output:
            None
        '''
        self._set_func_par_value('TRIG', 'TIM', val)

    def _do_get_trigger_timer(self):
        '''
        Read the value for the trigger timer from the instrument

        Input:
            None

        Output:
            None
        '''
        return self._get_func_par('TRIG', 'TIM')

    def _do_set_mode(self, mode):
        '''
        Set the mode to the specified value

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set mode to %s' %mode)
        if (mode in self._modes):
            string = ':CONF:%s' %mode
            self._visainstrument.write(string)
        else:
            print 'invalid mode!'

    def _do_get_mode(self):
        '''
        Read the mode from the device

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Reading mode from instrument')
        string = ':CONF?'
        return self._visainstrument.ask(string).strip('"')

  # core communication
    def _set_func_par_value(self, func, par, val):
        '''
        For internal use only!!
        Changes the value of the parameter for the function specified
    
        Input:
            func (string) : 
            par (string)  :
            val (depends??) :
    
        Output:
            None
        '''
        string = ':%s:%s %s' %(func, par, val)
        logging.debug(__name__ + ' : Set instrument to %s' %string)
        print string
        self._visainstrument.write(string)

    def _get_func_par(self, func, par):
        '''
        For internal use only!!
        Reads the value of the parameter for the function specified
        from the instrument
    
        Input:
            func (string) : 
            par (string)  :
    
        Output:
            val (depends??) :
        '''
        string = ':%s:%s?' %(func, par)
        logging.debug(__name__ + ' : ask instrument for %s' %string)
        return self._visainstrument.ask(string)
