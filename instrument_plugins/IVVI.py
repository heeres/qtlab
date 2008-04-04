# IVVI.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <m.c.schaafsma@student.tudelft.nl>, 2008
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
import types
import pyvisa.vpp43 as vpp43
from time import sleep
import logging

class IVVI(Instrument):
    '''
    This is the python driver for the IVVI-rack
    
    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'IVVI', address='<ASRL address>',
        reset=<bool>, numdacs=<multiple of 4>, polarity=<list of polarity strings>)
        
    The last three parameters are optional. Default parameters are
    reset=False, numdacs=8, polarity=['BIP', 'BIP']
    alternatives for the polarity are 'NEG' and 'POS'
    
    Callable functions:
    <name>.set_dac<dacnum>(<voltage>)
    <name>.get_dac<dacnum>()
    <name>.set_pol_dacs_<dacnum>_to_<dacnum>(<polarity>)
    <name>.get_pol_dac<dacnum>()
    <name>.reset()
    
    TODO:
    3) weten we zeker dat de bins kloppen?
    4) hoe snel is het nu eigenlijk?
    5) delays voor voorkomen collisions?
	6) close serial?
    '''

    def __init__(self, name, address, reset=False, numdacs=8,
        polarity=['BIP', 'BIP', 'BIP', 'BIP']):
        '''
        Initialzes the driver
        __init__(name, address, reset=False, numdacs=8,
        polarity=['BIP', 'BIP', 'BIP', 'BIP']):
        
        Loads the following functions into the wrapper
        
        <name>.reset()
        
            For each dac:
            <name>.set_dac<dacnum>(<voltage>)
            <name>.get_dac<dacnum>()
            <name>.get_pol_dac<dacnum>()

            For each rack of dacs
            <name>.set_pol_dacs_<dacnum>_to_<dacnum>(<polarity>)
            The polarity is 'NEG', 'BIP' or 'POS'
            
            The functions _do_set_pol_dacs are also instantiated here
        '''
        
        Instrument.__init__(self, name)
        
        logging.debug(__name__ + ' : Initializing instrument IVVI')

        # Set parameters
        self._address = address
        self.numdacs = numdacs
        self.pol_num = range(self.numdacs)  
            
        # Add functions
        self.add_function('reset')
        
        # Create functions to set the dacpolarity for each set of dacs, and add them to the wrapper
        for j in range(numdacs/4):
            tekst = "pol_dacs_%s_to_%s", str(4*j+1,4*j+4)
            setattr(self, "_do_set_" + tekst, lambda flag:
                self._change_pol_dacrack(flag, rack=j))
            self.add_parameter(tekst, type=types.StringType,
                flags=Instrument.FLAG_SET)                
            getattr(self, "set_" + tekst)(polarity[j])

        # Add the rest of the parameters
        self.add_parameter('dac', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,self.numdacs), minval=self.pol_num[0],
            maxval=self.pol_num[0] + 4.0, units='Volts')
        self.add_parameter('pol_dac', type=types.StringType,
            flags=Instrument.FLAG_GET, channels=(1,self.numdacs))
        
        self._open_serial_connection()

        if reset:
            self.reset()
        else: 
            self.get_all()
    
    # open serial connection
    def _open_serial_connection(self):
        '''
        _open_serial_connection()
        Opens the ASRL connection using vpp43
        baud=115200, databits=8, stop=one, parity=odd
        '''  
        logging.debug(__name__ + ' : Opening serial connection')
        self._session = vpp43.open_default_resource_manager()
        self._vi = vpp43.open(self._session, self._address)

        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_BAUD, 115200)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_DATA_BITS, 8)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_STOP_BITS,
            vpp43.VI_ASRL_STOP_ONE)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_PARITY,
            vpp43.VI_ASRL_PAR_ODD)
        
    
    # close serial connection
    def _close_serial_connection(self):
        '''
        _close_serial_connection()
        Closes the serial connection
        '''
        logging.debug(__name__ + ' : Closing serial connection')
        vpp43.close(self._vi)
            
        
    def reset(self, **kwargs):
        '''
        reset(**kwargs)
        Resets all dacs to 0 volts
        '''
        logging.debug(__name__ + ' : resetting instrument')

        for i in range(self.numdacs):
            self._do_set_dac(0, i+1)

    def get_all(self):
        '''
        get_all()
        Gets all dacvalues from the device, and all polarities from memory
        and updates the wrapper
        '''
        for i in range(1, self.numdacs+1):
            getattr(self, "get_dac" + str(i))()
            getattr(self, "get_pol_dac" + str(i))()
               
    # Conversion of data    
    def _voltage_to_bytes(self, voltage):
        '''
        _voltage_to_bytes(voltage)
        Converts a voltage on a 0v-4v scale to a 16bit integer equivalent
        output is a list of two bytes
        '''
        bytevalue = int(round(voltage/4.0*65535))
        dataH = int(bytevalue/256)
        dataL = bytevalue - dataH*256
        return (dataH, dataL)

    def _numbers_to_voltages(self, numbers):
        '''
        _numbers_to_voltages(numbers)
        Converts a list of bytes to a list containing
        the corresponding voltages
        '''
        values = range(self.numdacs)    
        for i in range(self.numdacs):
            values[i] = (numbers[2 + 2*i]*256 + numbers[3 + 2*i])/65535.0*4.0+self.pol_num[i]
        return values    
        
    # Communication with device
    def _do_get_dac(self, channel):
        '''
        _do_get_dac(channel)
        Returns the value of the specified dac
        '''
        logging.debug(__name__ + ' : reading voltage from dac%s' % channel)
        voltages = self._get_dac()
        return voltages[channel-1]            

    def _do_set_dac(self, voltage, channel):
        '''
        _do_set_dac(voltage, channel)
        Sets the specified dac to the specified voltage        
        '''
        (DataH,DataL) = self._voltage_to_bytes(voltage - self.pol_num[channel-1])
        message = "%c%c%c%c%c%c%c" % (7, 0, 2, 1, channel, DataH, DataL)
        data_out_size = 2
        reply = self._send_and_read(message, data_out_size)
        logging.debug(__name__ + ' : setting voltage of dac%s to %s Volts' 
            % (channel, voltage)) 
        return reply

    def _get_dac(self, **kwargs):
        '''
        _get_dac(**kwargs)
        Reads from device and returns all dacvoltages
        '''
        message = "%c%c%c%c" % (4, 0, 18, 2)
        data_out_size = 18
        reply = self._send_and_read(message, data_out_size)
        voltages = self._numbers_to_voltages(reply)
        return voltages 
        
    def _send_and_read(self, message, data_out_size):
        '''
        _send_and_read(message, data_out_size)
        Performs the communication with the device
        Returns a list of bytes
        '''
        vpp43.write(self._vi, message)
        data_out_string =  vpp43.read(self._vi, data_out_size)
        data_out_numbers = [ord(s) for s in data_out_string]
        
        if data_out_numbers[1] != 0:
            logging.error(__name__ + ' : Error while reading : %s', data_out_numbers)
            
        return data_out_numbers
    
    # Base functions to handle the polarity
    def _change_pol_dacrack(self, flag, rack):
        '''
        _change_pol_dacrack(flag, rack)
        Changes the polarity of the specified set of dacs
        '''
        for i in range(4*(rack),4*(rack+1)):
        
            logging.debug(__name__ + ' : Setting polarity to ' + flag.upper())
        
            if (flag.upper() == 'NEG'):
                self.pol_num[i] = -4
            elif (flag.upper() == 'BIP'):
                self.pol_num[i] = -2
            elif (flag.upper() == 'POS'):
                self.pol_num[i] = 0
            else:
                logging.error(__name__ + ' : Try to set invalid dacpolarity')
            self.set_parameter_bounds('dac' + str(i+1),self.pol_num[i],
                4+self.pol_num[i])
            
    
    def _do_get_pol_dac(self, channel):
        '''
        _do_get_pol_dac(channel)
        Returns the polarity of the dac channel specified
        '''
        val = self.pol_num[channel-1]
        
        logging.debug(__name__ + ' : Reading dacpolarity')
        
        if (val == -4):
            return 'NEG'
        elif (val == -2):
            return 'BIP'
        elif (val == 0):
            return 'POS'
        else:
            return 'Fout'
    