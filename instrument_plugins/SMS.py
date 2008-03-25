from instrument import Instrument
import types
import pyvisa.vpp43 as vpp43
from time import sleep
import logging
import pickle

class SMS(Instrument):
    '''
    TODO:
    3) weten we zeker dat de bins kloppen?
    4) hoe snel is het nu eigenlijk?
    5) delays voor voorkomen collisions?
    6) close serial?    
    7) Deze faket een hard get met een file
    8) Moet je een signaal kunnen sturen naar een apparaat dat uit staat?
    9) Wat te doen wanneer er onterecht wordt gevraagd naar een file? Resetten?
    10) Moet er bij inlezen data worden gecontroleerd of de dacpolarity nog klopt?
    11) 'get pol dac' en 'set pol dac' updaten niet de wrapper voor andere drie dacs
    '''

    def __init__(self, name, address, reset=False, numdacs=8): #  
        Instrument.__init__(self, name)
    
        # Set parameters
        self._address = address
        self.numdacs = numdacs
        self.pol_num = range(self.numdacs)  
        self._values = {}
        self._filename = 'SMS_' + address + '.dat'
                    
        # Add functions
        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('MeasureADC_ON')
        self.add_function('MeasureADC_OFF')
        self.add_function('MeasureDAC_ON')
        self.add_function('MeasureDAC_OFF')
        self.add_function('SaveParameters')
        self.add_function('LoadParameters')
        
        # Add parameters
        self.add_parameter('dac', type=types.FloatType, flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,self.numdacs), minval=0, maxval=0, units='Volts')
        self.add_parameter('pol_dac', type=types.StringType, flags=Instrument.FLAG_GET,
            channels=(1,self.numdacs))
        self.add_parameter('BattVoltagePos', type=types.FloatType, flags=Instrument.FLAG_GET, units='Volts')
        self.add_parameter('BattVoltageNeg', type=types.FloatType, flags=Instrument.FLAG_GET, units='Volts')
             
        self._open_serial_connection()

        if reset:
            self.reset()
        else: 
            self.get_all()
    
    # open serial connection
    def _open_serial_connection(self): # check
        logging.debug(__name__ + ' : opening connection')    
        self._session = vpp43.open_default_resource_manager()
        self._vi = vpp43.open(self._session,self._address)

        vpp43.set_attribute(self._vi,vpp43.VI_ATTR_ASRL_BAUD, 19200)
        vpp43.set_attribute(self._vi,vpp43.VI_ATTR_ASRL_DATA_BITS, 8)
        vpp43.set_attribute(self._vi,vpp43.VI_ATTR_ASRL_STOP_BITS, vpp43.VI_ASRL_STOP_ONE)
        vpp43.set_attribute(self._vi,vpp43.VI_ATTR_ASRL_PARITY, vpp43.VI_ASRL_PAR_EVEN)
        
    
    # close serial connection
    def _close_serial_connection(self): # check
        logging.debug(__name__ + ' : closing connection')    
        vpp43.close(self._vi)
        
    # Wrapper functions    
    def reset(self, **kwargs): # check
        logging.debug(__name__ + ' : resetting instrument')

        for i in range(1,self.numdacs,4):
            getattr(self, "get_pol_dac" + str(i))()
        
        print self._values

        
        for i in range(self.numdacs):       
            getattr(self, 'set_dac' + str(i+1))(0)
            
    def get_all(self): # check      
        # mist hier nog iets?? Dacpolarities opvragen??
        logging.debug(__name__ + ' : get all data from memory')        

        for i in range(1,1+self.numdacs/4):
            getattr(self,'get_pol_dac' + str(4*i))()    

        for i in range(self.numdacs):
            getattr(self, 'get_dac' + str(i+1))()            

    # functions
    def MeasureADC_ON(self): # check
        self._WriteToInstrument('PC1ADCON;')
        logging.debug(__name__ + ' : Measure ADC set to ON')        
        
    def MeasureADC_OFF(self): # check
        self._WriteToInstrument('PC1ADCOFF;')
        logging.debug(__name__ + ' : Measore ADC set to OFF')        
    
    def MeasureDAC_ON(self): # check
        self._WriteToInstrument('PC2DACON;')
        logging.debug(__name__ + ' : Measure DAC set to ON')
    
    def MeasureDAC_OFF(self): # check
        self._WriteToInstrument('PC2DACOFF;')
        logging.debug(__name__ + ' : Measure DAC set to OFF')
      
    def SaveParameters(self):
        self._save_values()
        
    def LoadParameters(self):
        self._load_values()

    # Communication with wrapper
    def _do_get_dac(self, channel): # check
        self._load_values()
        logging.debug(__name__ + ' : reading and cpnverting to voltage from memory for dac%s' % channel)
        byteval = self._ask_value('byteval_dac' + str(channel))
        voltage = self._bytevalue_to_voltage(byteval) + self._ask_value('corr_dac' + str(channel))
        return voltage            

    def _do_set_dac(self, voltage, channel): #done
        bytevalue = self._voltage_to_bytevalue(voltage - self._ask_value('corr_dac' + str(channel)))
        numtekst = '00'
        if (channel<10):
            numtekst = '0' + str(channel)
        elif (channel<100)&(channel>9):
            numtekst = str(channel)
        
        # format string
        bytestring = str(bytevalue)
        while (len(bytestring)<5):
            bytestring = '0' + bytestring
        
        self._WriteToInstrument('D' + numtekst + ',' + bytestring + ';')
        self._store_value('byteval_dac' + str(channel), bytevalue)
        logging.debug(__name__ + ' : setting voltage of dac%s to %s Volts' % (channel, voltage)) 
        self._save_values()
  

    # Base functions to handle the polarity   
    def _do_get_pol_dac(self, channel): # check
        
        # Also set bounds of dacs        
        set = ((channel-1)/4)+1
        
        logging.debug(__name__ + ' : Reading polarity of dac ' + str(channel))
        
        self._WriteToInstrument('POLD' + str(set) + ';')
        val = self._ReadBuffer()
                
        if (val == '-4V ... 0V'):
            polarity = 'NEG'
            correction = -4.0
        elif (val == '-2V ... +2V'):
            polarity = 'BIP'
            correction = -2.0
        elif (val == ' 0V ... +4V'):
            polarity = 'POS'
            correction = 0.0;
        else:
            print 'fout'
            return 'Fout'
            
        for i in range(1+(set-1)*4,1+set*4):
            self.set_parameter_bounds('dac' + str(i),correction,4.0+correction)
            self._store_value('pol_dac' + str(i), polarity)
            self._store_value('corr_dac' + str(i), correction)
            
        return polarity

    def _do_get_BattVoltagePos(self): # check
        self._WriteToInstrument('BCMAINPOS;')
        tekst = self._ReadBuffer()
        logging.debug(__name__ + ' : Reading Positive Battery voltage ' + str(tekst))
        return tekst
            
    def _do_get_BattVoltageNeg(self): # check
        self._WriteToInstrument('BCMAINNEG;')
        tekst = self._ReadBuffer()
        logging.debug(__name__ + ' : Reading Negative Battery voltage ' + str(tekst))
        return tekst

            
    #  Retrieving data from buffer
    def _ReadBuffer(self): # check
        sleep(0.5)
        tekst = vpp43.read(self._vi,vpp43.get_attribute(self._vi, vpp43.VI_ATTR_ASRL_AVAIL_NUM))
        logging.debug(__name__ + ' : Reading buffer: ' + str(tekst))
        
        print 'Read from buffer : ' + tekst
        
        if (tekst==''):
            return tekst        
        elif (tekst[0]=='E'):
            logging.error(__name__ + ' : An error occurred during readout of instrument : ' + tekst)
        else: 
            return tekst
            
    # Send data to instrument
    def _WriteToInstrument(self, tekst): # check
        # clear buffer
        restbuffer = self._ReadBuffer()
        logging.debug(__name__ + ' : Write tekst to instrument: ' + tekst)
        if (restbuffer!=''):
            logging.error(__name__ + ' : Buffer contained unread data : ' + restbuffer)
        sleep(0.5)
        vpp43.write(self._vi, tekst)
        print 'String sent : ' + tekst
        
    # Keep track of data
    def _store_value(self, name, val): # check
        self._values[name] = val
    
    def _ask_value(self, name): # check
        if name in self._values:
            return self._values[name]
        else:
            logging.error(__name__ + " : Try to read non-existing parameter from memory : " + name)
    
    
    def _load_values(self): # check
        logging.debug(__name__ + ' : Unpickling data')
    
        try:
            file = open(self._filename,'r')
            self._values = pickle.load(file)    
            file.close()
            return True
        except:
            logging.debug(__name + " : Try to open nonexisting file")
            return False
    
    def _save_values(self): # check
        logging.debug(__name__ + ' : Pickling data')
        file = open(self._filename,'w')
        pickle.dump(self._values, file)    
        file.close()    
    
    
    # Conversion of data    
    def _voltage_to_bytevalue(self, voltage): # check
        bytevalue = int(round(voltage/4.0*65535))
        return bytevalue

    def _bytevalue_to_voltage(self, bytevalue): # check
        value = 4.0*(bytevalue/65535.0)
        return value