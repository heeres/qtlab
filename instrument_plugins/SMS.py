# SMS.py class, to perform the communication between the Wrapper and the device
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
import pickle

class SMS(Instrument):
    '''
    This is the driver for the SMS Sample Measurement System
    
    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'SMS', address='<ASRL address>',
        reset=<bool>, numdacs=<multiple of 4>)
        
    The last two parameters are optional. Delfaults are
    reset=False, numdacs=8
    When reset=False make sure the specified parameterfile exists
    
    Callable functions:
    <name>.reset()
    <name>.get_all()
    <name>.measure_adc_on()
    <name>.measure_adc_off()
    <name>.measure_dac_on()
    <name>.measure_dac_off()
    <name>.save_parameters()
    <name>.load_parameters()
    <name>.battvoltage_pos()
    <name>.battvoltage_neg()
    
    For each dac:
    <name>.set_dac<dacnum>(<voltage>)
    <name>.get_dac<dacnum>()
    <name>.get_pol_dac<dacnum>()    
    
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

    def __init__(self, name, address, reset=False, numdacs=8):
        '''
        Initializes the driver
        __init__(name, address, reset=False, numdacs=8):
        
        Dacvalues are stored  in "'SMS_' + address + '.dat'"
        
        The following functions are loaded into the wrapper
        
        <name>.reset()
        <name>.get_all()
        <name>.measure_adc_on()
        <name>.measure_adc_off()
        <name>.measure_dac_on()
        <name>.measure_dac_off()
        <name>.save_parameters()
        <name>.load_parameters()
        <name>.battvoltage_pos()
        <name>.battvoltage_neg()
        
        For each dac:
        <name>.set_dac<dacnum>(<voltage>)
        <name>.get_dac<dacnum>()
        <name>.get_pol_dac<dacnum>()        
        '''
    
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
        self.add_function('measure_adc_on')
        self.add_function('measure_adc_off')
        self.add_function('measure_dac_on')
        self.add_function('measure_dac_off')
        self.add_function('save_parameters')
        self.add_function('load_parameters')
        
        # Add parameters
        self.add_parameter('dac', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self.numdacs), minval=0, maxval=0, units='Volts')
        self.add_parameter('pol_dac', type=types.StringType,
            flags=Instrument.FLAG_GET, channels=(1, self.numdacs))
        self.add_parameter('battvoltage_pos', type=types.FloatType,
            flags=Instrument.FLAG_GET, units='Volts')
        self.add_parameter('battvoltage_neg', type=types.FloatType,
            flags=Instrument.FLAG_GET, units='Volts')
             
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
        baud=19200, databits=8, stop=one, parity=even
        '''      
        logging.debug(__name__ + ' : opening connection')    
        self._session = vpp43.open_default_resource_manager()
        self._vi = vpp43.open(self._session, self._address)

        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_BAUD, 19200)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_DATA_BITS, 8)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_STOP_BITS,
            vpp43.VI_ASRL_STOP_ONE)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_PARITY,
            vpp43.VI_ASRL_PAR_EVEN)
        
    # close serial connection
    def _close_serial_connection(self):
        '''
        _close_serial_connection()
        Close the serial connection
        '''
        logging.debug(__name__ + ' : closing connection')    
        vpp43.close(self._vi)
        
    # Wrapper functions    
    def reset(self, **kwargs):
        '''
        reset(**kwargs)
        Reset the dacs to zero voltage
        '''
        logging.debug(__name__ + ' : resetting instrument')

        for i in range(1,self.numdacs,4):
            getattr(self, "get_pol_dac" + str(i))()
        
        for i in range(self.numdacs):       
            getattr(self, 'set_dac' + str(i+1))(0)
            
    def get_all(self):
        '''
        get_all()
        Get all polarities from device, and update the wrapper
        with data from memory
        '''
        logging.debug(__name__ + ' : get all data from memory')        

        for i in range(1,1+self.numdacs/4):
            getattr(self,'get_pol_dac' + str(4*i))()    

        for i in range(self.numdacs):
            getattr(self, 'get_dac' + str(i+1))()            

    # functions
    def measure_adc_on(self):
        '''
        measure_adc_on()
        Set the measure adc to 'on'
        '''
        self._write_to_instrument('PC1ADCON;')
        logging.debug(__name__ + ' : Measure ADC set to ON')        
        
    def measure_adc_off(self):
        '''
        measure_adc_off()
        Set the measure adc to 'off'
        '''
        self._write_to_instrument('PC1ADCOFF;')
        logging.debug(__name__ + ' : Measore ADC set to OFF')        
    
    def measure_dac_on(self):
        '''
        measure_dac_on()
        Set the measure dac to 'on'
        '''
        self._write_to_instrument('PC2DACON;')
        logging.debug(__name__ + ' : Measure DAC set to ON')
    
    def measure_dac_off(self):
        '''
        measure_dac_off()
        Set the measure dac to 'off'
        '''
        self._write_to_instrument('PC2DACOFF;')
        logging.debug(__name__ + ' : Measure DAC set to OFF')
      
    def save_parameters(self):
        '''
        save_parameters()
        Writes parameters from memory to harddisk
        '''
        self._save_values()
        
    def load_parameters(self):
        '''
        load_parameters()
        Reads parameters from harddisk into memory
        '''
        self._load_values()

    # Communication with wrapper
    def _do_get_dac(self, channel):
        '''
        _do_get_dac(channel)
        Reads the specified dacvalue from memory
        '''
        self._load_values()
        logging.debug(__name__ + ' : reading and converting to \
            voltage from memory for dac%s' % channel)
        byteval = self._ask_value('byteval_dac' + str(channel))
        voltage = self._bytevalue_to_voltage(byteval) +
            self._ask_value('corr_dac' + str(channel))
        return voltage            

    def _do_set_dac(self, voltage, channel):
        '''
        _do_set_dac(voltage, channel)
        Sets the dac to the specified voltage
        '''
        bytevalue = self._voltage_to_bytevalue(voltage - 
            self._ask_value('corr_dac' + str(channel)))
        numtekst = '00'
        if (channel<10):
            numtekst = '0' + str(channel)
        elif (channel<100)&(channel>9):
            numtekst = str(channel)
        
        # format string
        bytestring = str(bytevalue)
        while (len(bytestring)<5):
            bytestring = '0' + bytestring
        
        self._write_to_instrument('D' + numtekst + ',' + bytestring + ';')
        self._store_value('byteval_dac' + str(channel), bytevalue)
        logging.debug(__name__ + ' : setting voltage of dac%s to \
            %s Volts' % (channel, voltage)) 
        self._save_values()  

    # Base functions to handle the polarity   
    def _do_get_pol_dac(self, channel, direct=True):
        '''
        _do_get_pol_dac(channel, direct=True)
        Updates the polarities
        only use with direct=True
        '''        
        set = ((channel-1)/4)+1        
               
        logging.debug(__name__ + ' : Reading polarity of dac ' + str(channel))

        if (direct):        
            self._write_to_instrument('POLD' + str(set) + ';')
            val = self._read_buffer()
                    
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
             
            self._save_values()

            for i in range(1+(set-1)*4,1+set*4):        
                getattr(self, 'get_pol_dac' + str(i))(direct=False)
        
        return self._ask_value('pol_dac' + str(channel))

    def _do_get_battvoltage_pos(self):
        '''
        _do_get_battvoltage_pos()
        Returns the positive battery voltage
        '''
        self._write_to_instrument('BCMAINPOS;')
        tekst = self._read_buffer()
        logging.debug(__name__ + ' : Reading Positive Battery voltage '
            + str(tekst))
        return tekst
            
    def _do_get_battvoltage_neg(self):
        '''
        _do_get_battvoltage_neg()
        Returns the negative battery voltage
        '''
        self._write_to_instrument('BCMAINNEG;')
        tekst = self._read_buffer()
        logging.debug(__name__ + ' : Reading Negative Battery voltage '
            + str(tekst))
        return tekst

            
    #  Retrieving data from buffer
    def _read_buffer(self):
        '''
        _read_buffer()
        Returns a string containing the content of the buffer
        '''
        sleep(0.5)
        tekst = vpp43.read(self._vi,vpp43.get_attribute(self._vi,
            vpp43.VI_ATTR_ASRL_AVAIL_NUM))
        logging.debug(__name__ + ' : Reading buffer: ' + str(tekst))
        
        if (tekst==''):
            return tekst        
        elif (tekst[0]=='E'):
            logging.error(__name__ + ' : An error occurred during \
                readout of instrument : ' + tekst)
        else: 
            return tekst
            
    # Send data to instrument
    def _write_to_instrument(self, tekst):
        '''
        _write_to_instrument(tekst)
        Writes a string to the instrument, after the buffer is cleared        
        '''
        # clear buffer
        restbuffer = self._read_buffer()
        logging.debug(__name__ + ' : Write tekst to instrument: ' + tekst)
        if (restbuffer!=''):
            logging.error(__name__ + ' : Buffer contained unread data : '
                + restbuffer)
        sleep(0.5)
        vpp43.write(self._vi, tekst)
        print 'String sent : ' + tekst
        
    # Keep track of data
    def _store_value(self, name, val):
        '''
        _store_value(name, val)
        Stores a value in local memory
        '''
        self._values[name] = val
    
    def _ask_value(self, name):
        '''
        _ask_value(name)
        Asks for a parameter stored in memory
        '''
        if name in self._values:
            return self._values[name]
        else:
            logging.error(__name__ + " : Try to read non-existing \
                parameter from memory : " + name)
    
    def _load_values(self):
        '''
        _load_values()
        Loads the dacvalues from the local harddisk into memory 
        '''
        logging.debug(__name__ + ' : Unpickling data')
        try:
            file = open(self._filename,'r')
            self._values = pickle.load(file)    
            file.close()
            return True
        except:
            logging.debug(__name + " : Try to open nonexisting file")
            return False
    
    def _save_values(self):
        '''
        _save_values()
        Stores the dacvalues and polarities on the local harddisk
        '''
        logging.debug(__name__ + ' : Pickling data')
        file = open(self._filename,'w')
        pickle.dump(self._values, file)    
        file.close()
    
    # Conversion of data    
    def _voltage_to_bytevalue(self, voltage):
        '''
        _voltage_to_bytevalue(voltage)
        Converts a voltage on a 0v-4v scale to a 16bits bytevalue
        '''
        bytevalue = int(round(voltage/4.0*65535))
        return bytevalue

    def _bytevalue_to_voltage(self, bytevalue):
        '''
        _bytevalue_to_voltage(bytevalue)
        Converts a 16bits bytevalue to a voltage on a 0v-4v scale
        '''
        value = 4.0*(bytevalue/65535.0)
        return value