from instrument import Instrument
import visa
import types
import logging
from time import sleep

class HP8657B(Instrument):
    '''
    This is the python driver for the HP 8657B 
    signal generator
    
    TODO:
    1. Implement a reset that DOES work
    2. Adjust timing
    '''

    def __init__(self, name, address, reset=False, freq=1e9, pow=-143.4): #  address als derde parameter verwijderd!!
        Instrument.__init__(self, name)

        self._address = address        
        self._visainstrument = visa.instrument(self._address)
        sleep(1)

        self.add_parameter('frequency', type=types.FloatType, flags=Instrument.FLAG_SET,
            minval=0.1e6, maxval=2060e6, units='Hz')
        self.add_parameter('power', type=types.FloatType, flags=Instrument.FLAG_SET,
            minval=-143.5, maxval=17, units='dBm')
        self.add_parameter('status', type=types.StringType,
            flags=Instrument.FLAG_SET)
            
        self.add_function('reset')            
        self.add_function('set_all')

            
        if reset:
            self.reset(freq,pow)
        else:
            self.set_all(freq,pow)

           
# initialization related

    def reset(self, freq, pow):
        '''
        Reset device to default values, has to be ajusted jet
        '''
        
        logging.debug(__name__ + ' : Resetting instrument')
#        self._visainstrument.write('DC1')
        self.set_all(100e6,-143.5)
        
        #This updates all the variables in memory to the instrument values
    def set_all(self, freq, pow):
        self.set_power(pow)
        sleep(0.1)
        self.set_frequency(freq)
        sleep(0.1)

 

# communication with machine


    def _do_set_frequency(self, frequency):
        '''
        Set frequency of device
        '''	
        logging.debug(__name__ + ' : setting frequency to %s GHz' % frequency)
        # sending value to instrument
        self._visainstrument.write('FR%.0fHZ' % frequency)
 
    def _do_set_power(self,power):
        '''
        Set output power of device
        '''	
        logging.debug(__name__ + ' : setting power to %s dBm' % power)
        # sending value to instrument
        self._visainstrument.write('AP%.1fDM' % power) 
 
    def _do_set_status(self,status):
        '''
        Set status to 'on' or 'off'
        '''	
        if status.upper() == 'ON':
            self._visainstrument.write('R3')
        elif status.upper() == 'OFF':
            self._visainstrument.write('R2')
        else:
            raise ValueError('set_status(): can only set on or off')
        logging.debug(__name__ + ' : setting status to "%s"' % status)

# shortcuts ?
    def off(self):
        '''
        Set status to 'off'
        '''
        self.set_status('off')

    def on(self):
        '''
        Set status to 'on'
        '''
        self.set_status('on')
