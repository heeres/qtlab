# RS_SMR40.py class, to perform the communication between the Wrapper and the device
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

class RS_SMR40(Instrument):
    '''
    This is the python driver for the Rohde & Schwarz SMR40 
    signal generator
    
    Usage:
    Initialize with
    <name> = instruments.create('name', 'RS_SMR40', address='<GPIB address>',
        reset=<bool>)
        
    Callable functions:
    <name>.reset()
    <name>.get_all()
    <name>.get_frequency()
    <name>.set_frequency(<value>)
    <name>.get_power()
    <name>.set_power(<value>)
    <name>.get_status()
    <name>.set_status(<'on' or 'off'>)   
    
    Shortcuts:
    <name>.on()
    <name>.off()
    '''

    def __init__(self, name, address, reset=False): #  address als derde parameter verwijderd!!
        Instrument.__init__(self, name)

        self._address = address        
        self._visainstrument = visa.instrument(self._address)

        self.add_parameter('frequency', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=1e9, maxval=40e9, units='Hz')
        self.add_parameter('power', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-30, maxval=25, units='dBm')
        self.add_parameter('status', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
            
        self.add_function('reset')            
        self.add_function('get_all')
            
        if reset:
            self.reset()
        else: 
            self.get_all()
           
    # Functions
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
        Read settings from device
        '''        
        logging.debug(__name__ + ' : reading all settings from instrument')
        self._frequency = self.get_frequency()
        self._power = self.get_power()
        self._status = self.get_status()

# communication with machine

    def _do_get_frequency(self):
        '''
        _do_get_frequency()
        Get frequency from device
        '''        
        logging.debug(__name__ + ' : reading frequency from instrument')
        # getting value from instrument to memory
        self._frequency = float(self._visainstrument.ask('SOUR:FREQ?'))
        return self._frequency

    def _do_set_frequency(self, frequency):
        '''
        _do_set_frequency(frequency)
        Set frequency of device
        '''	
        logging.debug(__name__ + ' : setting frequency to %s GHz' % frequency)
        # sending value to instrument
        self._visainstrument.write('SOUR:FREQ %e' % frequency)

    def _do_get_power(self):
        '''
        _do_get_power()
        Get output power from device
        '''	
        logging.debug(__name__ + ' : reading power from instrument')
        # getting value from instrument to memory
        self._power = float(self._visainstrument.ask('SOUR:POW?'))
        return self._power

    def _do_set_power(self,power):
        '''
        _do_set_power(power)
        Set output power of device
        '''	
        logging.debug(__name__ + ' : setting power to %s dBm' % power)
        # sending value to instrument
        self._visainstrument.ask('SOUR:POW %e' % power) 

    def _do_get_status(self):
        '''
        _do_get_status()
        Get status from device
        '''	
        logging.debug(__name__ + ' : reading status from instrument')
        # getting value from instrument to memory
        cmd = self._visainstrument.ask(':OUTP:STAT?')
        
        if cmd == '1':
            self._status = 'on'
        elif cmd == '0':
            self._status = 'off'
        else:
            self._status = 'error'
            logging.debug(__name__ + ' : Unexpected Readout from get_status ')            
        
        return self._status
 
    def _do_set_status(self,status):
        '''
        _do_set_status(status)
        Set status to 'on' or 'off'
        '''	
        if status.upper() in ('ON', 'OFF'):
            status = status.upper()
        else:
            raise ValueError('set_status(): can only set on or off')
        logging.debug(__name__ + ' : setting status to "%s"' % status)
        # sending value to instrument
        self._visainstrument.write(':OUTP:STAT %s' % status) 

    # shortcuts
    def off(self):
        '''
        off()
        Set status to 'off'
        '''
        self.set_status('off')

    def on(self):
        '''
        on()
        Set status to 'on'
        '''
        self.set_status('on')