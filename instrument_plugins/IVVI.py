from instrument import Instrument
import types
import pyvisa.vpp43 as vpp43
from time import sleep
import logging

class IVVI(Instrument):
    '''
    TODO:
    1) moeten de dacs automatisch door wrapper gegenereerd worden (NEE) done
    2) willen we per dac polarity kunnen zetten? (NEE) done
    3) weten we zeker dat de bins kloppen?
    4) hoe snel is het nu eigenlijk?
    5) delays voor voorkomen collisions?
	6) close serial?
    '''

    def __init__(self, name, address, reset=False, numdacs=8, polarity=['BIP','BIP','BIP','BIP']): #  address als derde parameter verwijderd!!
        Instrument.__init__(self, name)

        # Set parameters
        self._address = address
        self.numdacs = numdacs
        self.pol_num = range(self.numdacs)  
                
            
        # Add functions
        self.add_function('reset')

        self.add_parameter('dac', type=types.FloatType, flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,self.numdacs), minval=self.pol_num[0], maxval=self.pol_num[0] + 4.0, units='Volts')
        self.add_parameter('pol_dac', type=types.StringType, flags=Instrument.FLAG_GETSET,
            channels=(1,self.numdacs))

        # Set polarity of the dacs
        for j in range(numdacs/4):
            for i in range(4*j,4*j+4):
                # Define polarity
                self._do_set_pol_dac(polarity[j], i+1)
                
        
        self._open_serial_connection()

        if reset:
            self.reset()
        else: 
            self.get_all()
    
    # open serial connection
    def _open_serial_connection(self):
    
        self._session = vpp43.open_default_resource_manager()
        self._vi = vpp43.open(self._session,self._address)

        vpp43.set_attribute(self._vi,vpp43.VI_ATTR_ASRL_BAUD, 115200)
        vpp43.set_attribute(self._vi,vpp43.VI_ATTR_ASRL_DATA_BITS, 8)
        vpp43.set_attribute(self._vi,vpp43.VI_ATTR_ASRL_STOP_BITS, vpp43.VI_ASRL_STOP_ONE)
        vpp43.set_attribute(self._vi,vpp43.VI_ATTR_ASRL_PARITY, vpp43.VI_ASRL_PAR_ODD)
        
    
    # close serial connection
    def _close_serial_connection(self):
        vpp43.close(self._vi)
            
        
    def reset(self, **kwargs):
        logging.debug(__name__ + ' : resetting instrument')

        for i in range(self.numdacs):
            self._do_set_dac(0,i+1)

    def get_all(self):        
        
        for i in range(1,self.numdacs+1):
            getattr(self, "get_dac" + str(i))()
            getattr(self, "get_pol_dac" + str(i))()
               
    # Conversion of data
    
    def _voltage_to_bytes(self, voltage):
        bytevalue = int(round(voltage/4.0*65535))
        dataH = int(bytevalue/256)
        dataL = bytevalue - dataH*256
        return (dataH,dataL)

    def _numbers_to_voltages(self, numbers):
        values = range(self.numdacs)    
        for i in range(self.numdacs):
            values[i] = (numbers[2 + 2*i]*256 + numbers[3 + 2*i])/65535.0*4.0+self.pol_num[i]
        return values    
        
    # Communication with device
    def _do_get_dac(self, channel):
        logging.debug(__name__ + ' : reading voltage from dac%s' % channel)
        voltages = self._get_dac()
        return voltages[channel-1]            

    def _do_set_dac(self, voltage, channel):
        (DataH,DataL) = self._voltage_to_bytes(voltage - self.pol_num[channel-1])
        message = "%c%c%c%c%c%c%c" % (7,0,2,1,channel,DataH,DataL)
        data_out_size = 2
        reply = self._send_and_read(message,data_out_size)
        logging.debug(__name__ + ' : setting voltage of dac%s to %s Volts' % (channel, voltage)) 
        return reply

    def _get_dac(self, **kwargs):
        message = "%c%c%c%c" % (4,0,18,2)
        data_out_size = 18
        reply = self._send_and_read(message,data_out_size)
        voltages = self._numbers_to_voltages(reply)
        return voltages 
        
    def _send_and_read(self, message,data_out_size):

        vpp43.write(self._vi,message)
        data_out_string =  vpp43.read(self._vi,data_out_size)
        data_out_numbers = [ord(s) for s in data_out_string]
        
        if data_out_numbers[1] != 0:
            print "error detected!"
            print data_out_numbers
            # apply logging
            
        return data_out_numbers
        
    
    
    # Base functions to handle the polarity
    def _do_set_pol_dac(self, flag, channel):
    
        for i in range(4*((channel-1)/4),4+4*((channel-1)/4)):
        
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
    