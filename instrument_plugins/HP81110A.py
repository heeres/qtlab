# HP81110A.py class, to perform the communication between the Wrapper and the device
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
import visa
import types
import logging

class HP81110A(Instrument):
    '''
    This is the python driver for the HP81110A 
    pulse generator
    
    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'HP81110A', address='<GPIB address>',
        reset=<bool>)
        
    Callable functions:
    <name>.reset()
    <name>.get_all()    
    <name>.get_display()
    <name>.set_display(<'on' or 'off'>)
    
    For addressing channel 2 replace the '1':
    <name>.get_delay1()
    <name>.set_delay1(<value>)
    <name>.get_width1()
    <name>.set_width1(<value>)
    <name>.get_high1()
    <name>.set_high1(<value>)
    <name>.get_low1()
    <name>.set_low1(<value>)
    <name>.get_status1()
    <name>.set_status1(<value>)   

    TODO: 
    1) Check the get_all
    '''

    def __init__(self, name, address, reset=False):
        '''
        __init__(name, address, reset=False)
        Initializes the driver.
        
        The following functions are added to the wrapper:
        'reset' and 'get_all'
        
        The following parameters are added to the wrapper:
        'delay', 'width', 'high', 'low' and 'status'.
        All for both channel 1 and 2
        
        Also the parameter 'display' is added
        '''
        Instrument.__init__(self, name)

        self._address = address        
        self._visainstrument = visa.instrument(self._address)

        self.add_parameter('delay', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), minval=0.0, maxval=999, units='sec')
        self.add_parameter('width', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), minval=-6.25e-9, maxval=999.5, units='sec')
        self.add_parameter('high', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), minval=-9.90, maxval=10.0, units='Volts')
        self.add_parameter('low', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), minval=-10.0, maxval=9.90, units='Volts')
        self.add_parameter('status', type=types.StringType, channels=(1, 2),
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('display', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET) 
            
        self.add_function('reset')
        self.add_function('get_all')
            
        if reset:
            self.reset()
        else: 
            self.get_all()
           
           
    def reset(self):
        '''
        reset()
        Reset device to default values
        '''        
        logging.debug(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')
        
        #This updates all the variables in memory to the instrument values
        self.get_all()

    def get_all(self):
        '''
        get_all()
        Read settings from device, and updates the wrapper
        '''        
        logging.debug(__name__ + ' : reading all settings from instrument')
        
        for i in range(1,3):
            getattr(self, 'get_delay%s' % i)()
            getattr(self, 'get_width%s' % i)()
            getattr(self, 'get_high%s' % i)()
            getattr(self, 'get_low%s' % i)()
            getattr(self, 'get_status%s' % i)()        

    # communication with device
    def _do_get_delay(self, channel):
        '''
        _do_get_delay(channel)
        Reads the pulse delay from the device for the specified channel
        '''
        return self._visainstrument.ask(':PULS:DEL' + str(channel) + "?")
    
    def _do_set_delay(self, val, channel):
        '''
        _do_set_delay(val, channel)
        Sets the delay of the pulse of the specified channel
        '''
        self._visainstrument.write(':PULS:DEL' + str(channel) + " " + str(val) + "S")
    
    def _do_get_width(self, channel):
        '''
        _do_get_width(channel)
        Reads the pulse width from the device for the specified channel
        '''
        return self._visainstrument.ask(':PULS:WIDT' + str(channel) + "?")
    
    def _do_set_width(self, val, channel):
        '''
        _do_set_width(val, channel)
        Sets the width of the pulse of the specified channel
        '''
        self._visainstrument.write(':PULS:WIDT' + str(channel) + " " + str(val) + "S")
    
    def _do_get_high(self, channel):
        '''
        _do_get_high(channel)
        Reads the upper value from the device for the specified channel
        '''
        return self._visainstrument.ask(':VOLT' + str(channel) + ':HIGH?')

    def _do_set_high(self, val, channel):
        '''
        _do_set_high(val, channel)
        Sets the upper value of the specified channel
        '''
        self._visainstrument.write(':VOLT' + str(channel) + ":HIGH " + str(val) + "V")
    
    def _do_get_low(self, channel):
        '''
        _do_get_low(channel)
        Reads the lower value from the device for the specified channel
        '''
        return self._visainstrument.ask(':VOLT' + str(channel) + ':LOW?')
    
    def _do_set_low(self, val, channel):
        '''
        _do_set_low(val, channel)
        Sets the lower value of the specified channel
        '''
        self._visainstrument.write(':VOLT' + str(channel) + ":LOW " + str(val)        + "V")
    
    def _do_get_status(self, channel):
        '''
        _do_get_status(channel)
        Reads the status from the device for the specified channel
        '''
        val = self._visainstrument.ask('OUTP' + str(channel) + '?')
        if (val=='1'):
            return 'on'
        elif (val=='0'):
            return 'off'
        return 'error'    
        
    def _do_set_status(self, val, channel):
        '''
        _do_set_status(<'on' or 'off'>, channel)
        Sets the status of the specified channel
        '''
        if ((val.upper()=='ON') | (val.upper()=='OFF')):
            self._visainstrument.write('OUTP' + str(channel) + " " + val)
        else:
            logging.error('Try tot set OUTP to ' + str(val))    
    
    def _do_get_display(self):
        '''
        _do_get_display()
        Reads the display status from the device
        '''
        val = self._visainstrument.ask('DISP?')
        if (val=='1'):
            return 'on'
        elif (val=='0'):
            return 'off'
        return 'error'
    
    def _do_set_display(self, val):
        '''
        _do_set_display(<'on' or 'off'>)
        Sets the display status of the device
        '''
        if ((val.upper()=='ON') | (val.upper()=='OFF')):
            self._visainstrument.write('DISP ' + val)
        else:
            logging.error('Try tot set display to ' +val)