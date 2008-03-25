from instrument import Instrument
import visa
import types
import logging

class HP81110A(Instrument):
    '''
    This is the python driver for the HP 81110 A 
    pulse generator
    '''

    def __init__(self, name, address, reset=False): #  address als derde parameter verwijderd!!
        Instrument.__init__(self, name)

        self._address = address        
        self._visainstrument = visa.instrument(self._address)

        self.add_parameter('delay', type=types.FloatType, flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,2), minval=0.0, maxval=999, units='sec')
        self.add_parameter('width', type=types.FloatType, flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,2), minval=-6.25e-9, maxval=999.5, units='sec')
        self.add_parameter('high', type=types.FloatType, flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,2), minval=-9.90, maxval=10.0, units='Volts')
        self.add_parameter('low', type=types.FloatType, flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,2), minval=-10.0, maxval=9.90, units='Volts')
        self.add_parameter('status', type=types.StringType,
            channels=(1,2), flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('display', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
            
            
        self.add_function('reset')
        self.add_function('get_all')

            
        if reset:
            self.reset()
        else: 
            self.get_all()
           
# initialization related

    def reset(self):
        '''
        Reset device to default values
        '''
        
        logging.debug(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')
        
        #This updates all the variables in memory to the instrument values
        self.get_all()

    def get_all(self):
        '''
        Read settings from device
        '''        
        logging.debug(__name__ + ' : reading all settings from instrument')
        # have to fix this

# communication with machine

    def _do_get_delay(self, channel):
        return self._visainstrument.ask(':PULS:DEL' + str(channel) + "?")
    
    def _do_set_delay(self, val, channel):
        self._visainstrument.write(':PULS:DEL' + str(channel) + " " + str(val) + "S")
    
    def _do_get_width(self, channel):
        return self._visainstrument.ask(':PULS:WIDT' + str(channel) + "?")
    
    def _do_set_width(self, val, channel):
        self._visainstrument.write(':PULS:WIDT' + str(channel) + " " + str(val) + "S")
    
    def _do_get_high(self, channel):
        return self._visainstrument.ask(':VOLT' + str(channel) + ':HIGH?')

    def _do_set_high(self, val, channel):
        self._visainstrument.write(':VOLT' + str(channel) + ":HIGH " + str(val) + "V")
    
    def _do_get_low(self, channel):
        return self._visainstrument.ask(':VOLT' + str(channel) + ':LOW?')
    
    def _do_set_low(self, val, channel):
        self._visainstrument.write(':VOLT' + str(channel) + ":LOW " + str(val)        + "V")

    
    def _do_get_status(self, channel):
        val = self._visainstrument.ask('OUTP' + str(channel) + '?')
        if (val=='1'):
            return 'on'
        elif (val=='0'):
            return 'off'
        return 'error'    
        
    def _do_set_status(self, val, channel):
        if ((val.upper()=='ON') | (val.upper()=='OFF')):
            self._visainstrument.write('OUTP' + str(channel) + " " + val)
        else:
            logging.error('Try tot set OUTP to ' + str(val))    

    
    def _do_get_display(self):
        val = self._visainstrument.ask('DISP?')
        if (val=='1'):
            return 'on'
        elif (val=='0'):
            return 'off'
        return 'error'

    
    def _do_set_display(self, val):
        if ((val.upper()=='ON') | (val.upper()=='OFF')):
            self._visainstrument.write('DISP ' + val)
        else:
            logging.error('Try tot set display to ' +val)    
    
    