# SMS.py class, to perform the communication between the Wrapper and the device
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

#
#    TODO:
#    8) implement resend all if reset=False ?
#    9) Wat te doen wanneer er onterecht wordt gevraagd naar een file? Resetten?
#    10) Moet er bij inlezen data worden gecontroleerd of de dacpolarity nog klopt?
#

from instrument import Instrument
import types
import pyvisa.vpp43 as vpp43
from time import sleep
import logging
import pickle
import config

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
   '''

    def __init__(self, name, address, reset=False, numdacs=8):
        '''
        Initializes the SMS, and communicates with the wrapper
        Dacvalues are stored  in "'SMS_' + address + '.dat'" ??really??

        Input:
            name (string)        : name of the instrument
            address (string)     : ASRL address
            reset (bool)         : resets to default values, default=false
            numdacs (int)        : number of dacs, multiple of 4, default=8

        Output:
            None
        '''
        logging.info(__name__ + ' : Initializing instrument SMS')
        Instrument.__init__(self, name, tags=['physical'])

        # Set parameters

        self._address = address
        self.numdacs = numdacs
        self.pol_num = range(self.numdacs)
        self._values = {}
        self._filepath = 'f:/qtlab' # FIXME this should come from config
        self._filename = self._filepath + 'SMS_' + address + '.dat'
        #self._filepath = config.get_qtlabdir()
        #self._filename = self._filepath + '/instrument_plugins/' + 'SMS_' + address + '.dat'

        # Add functions
        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('measure_adc_on')
        self.add_function('measure_adc_off')
        self.add_function('measure_dac_on')
        self.add_function('measure_dac_off')
        self.add_function('get_battvoltages')

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

    def __del__(self):
        '''
        Closes up the SMS driver

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Deleting SMS instrument')
        self._close_serial_connection()

    # open serial connection
    def _open_serial_connection(self):
        '''
        Opens the ASRL connection using vpp43
        baud=19200, databits=8, stop=one, parity=even, no end char for reads

        Input:
            None

        Output:
            None
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
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_END_IN,
            vpp43.VI_ASRL_END_NONE)

    # close serial connection
    def _close_serial_connection(self):
        '''
        Close the serial connection

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : closing connection')
        vpp43.close(self._vi)

    # Wrapper functions
    def reset(self):
        '''
        Reset the dacs to zero voltage

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : resetting instrument')

        for i in range(1, self.numdacs, 4):
            logging.debug(__name__ + ' : getting polarity for dacrack %d' % i)
            self.get('pol_dac%d' % i)

        for i in range(1, self.numdacs+1):
            logging.debug(__name__ + ' : setting value of dac %d to 0.0' % i)
            self.set('dac%d' % i, 0.0)

    def get_all(self):
        '''
        Reads all polarities from the instrument, and updates the wrapper
        with data from memory

        Input:
            None

        Output:
            None
        '''
        logging.warning(__name__ + ' : WARNING! getting data from file, \
          instrument does not support getting')

        self._load_values_from_file()

        for i in range(1, self.numdacs, 4):
            logging.debug(__name__ + ' : getting polarity for dacrack %d' % i)
            self.get('pol_dac%d' % i)

        for i in range(self.numdacs):
            logging.debug(__name__ + ' : getting value for dac %d' % (i+1))
            self.get('dac%d' % (i+1))

    # functions
    def measure_adc_on(self):
        '''
        Set the measure adc to 'on'

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set Measure ADC to ON')
        self._write_to_instrument('PC1ADCON;')

    def measure_adc_off(self):
        '''
        Set the measure adc to 'off'

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set Measure ADC to OFF')
        self._write_to_instrument('PC1ADCOFF;')

    def measure_dac_on(self):
        '''
        Set the measure dac to 'on'

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set Measure DAC to ON')
        self._write_to_instrument('PC2DACON;')

    def measure_dac_off(self):
        '''
        Set the measure dac to 'off'

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set Measure DAC to OFF')
        self._write_to_instrument('PC2DACOFF;')

    # Communication with wrapper
    def _do_get_dac(self, channel):
        '''
        Reads the specified dacvalue from memory

        Input:
            channel (int) : 1 based index of the dac

        Output:
            voltage (float) : dacvalue in Volts
        '''
        logging.debug(__name__ + ' : reading and converting to \
            voltage from memory for dac%s' % channel)
        self._load_values_from_file()

        #print channel
        byteval = self._ask_value('byteval_dac' + str(channel))
        voltage = self._bytevalue_to_voltage(byteval) + self._ask_value('corr_dac' + str(channel))
        return voltage

    def _do_set_dac(self, voltage, channel):
        '''
        Sets the dac to the specified voltage

        Input:
            voltage (float) : dacvalue in Volts
            channel (int)   : 1 based index of the dac

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting voltage of dac%s to \
            %s Volts' % (channel, voltage))
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
        self._save_values_to_file()

    # Base functions to handle the polarity
    def _do_get_pol_dac(self, channel, direct=True):
        '''
        Updates the polarities in memory of the
        rack containing the specified channel.
        WARNING: Only use with direct=True

        Input:
            channel (int) : 1 based index of the dac for which the
                            polarities of the rack need to be updated

        Output:
            polarity (string) : 'BIP', 'POS' or 'NEG'
        '''
        logging.debug(__name__ + ' : Reading polarity of dac %d' % channel)
        set = ((channel-1)/4)+1

        if (direct):
            self._write_to_instrument('POLD' + str(set) + ';')
            val = self._read_buffer()
            logging.debug(__name__ + ' : received %s' % val)
            if (val == '-4V ...  0V'):
                polarity = 'NEG'
                correction = -4.0
            elif (val == '-2V ... +2V'):
                polarity = 'BIP'
                correction = -2.0
            elif (val == ' 0V ... +4V'):
                polarity = 'POS'
                correction = 0.0
            else:
                logging.error(__name__ + ' : Invalid polarity : %s' % val)
            logging.debug(__name__ + ' : polarity = %s (type = %s), correction = %f (type = %s)' % (polarity, type(polarity), correction, type(correction)))

            for i in range(1+(set-1)*4,1+set*4):
                logging.debug(__name__ + ' : saving info for dac %d' % i)
                self.set_parameter_bounds('dac' + str(i), correction,4.0+correction)
                self._store_value('pol_dac' + str(i), polarity)
                self._store_value('corr_dac' + str(i), correction)

            logging.debug(__name__ + ' : saving info list to file')
            self._save_values_to_file()

            for i in range(1+(set-1)*4,1+set*4):
                logging.debug(__name__ + ' : getting info from file for dac %d' % i)
                getattr(self, 'get_pol_dac' + str(i))(direct=False)
                getattr(self, 'get_dac' + str(i))

        logging.debug(__name__ + ' : returning polarity for dac %d' % channel)
        return self._ask_value('pol_dac' + str(channel))

    def get_battvoltages(self):
        self.get_battvoltage_neg()
        self.get_battvoltage_pos()

    def _do_get_battvoltage_pos(self):
        '''
        Returns the positive battery voltage

        Input:
            None

        Output:
            voltage (float) : battery voltage in Volts
        '''
        logging.debug(__name__ + ' : Reading Positive Battery voltage')
        self._write_to_instrument('BCMAINPOS;')
        reply = float(self._read_buffer())
        return reply

    def _do_get_battvoltage_neg(self):
        '''
        Returns the negative battery voltage

        Input:
            None

        Output:
            voltage (float) : battery voltage in Volts
        '''
        logging.debug(__name__ + ' : Reading Negative Battery voltage')
        self._write_to_instrument('BCMAINNEG;')
        reply = float(self._read_buffer())
        return reply

    #  Retrieving data from buffer
    def _read_buffer(self):
        '''
        Returns a string containing the content of the buffer

        Input:
            None

        Output:
            buffer (string) : data in buffer
        '''
        logging.debug(__name__ + ' : Reading buffer')
        tekst = vpp43.read(self._vi,vpp43.get_attribute(self._vi,
            vpp43.VI_ATTR_ASRL_AVAIL_NUM))
        sleep(0.05)

        if (tekst==''):
            return tekst
        elif (tekst[0]=='E'):
            logging.error(__name__  + ' : An error occurred during \
                readout of instrument : ' + tekst)
        else:
            return tekst

    # Send data to instrument
    def _write_to_instrument(self, tekst):
        '''
        Writes a string to the instrument, after the buffer is cleared

        Input:
            tekst (string) : data to be written to the instrument

        Output:
            None
        '''
        logging.debug(__name__ + ' : Start running _write_to_instrument with:' + tekst)
        # clear buffer
        logging.debug(__name__ + ' : clearing buffer')
        restbuffer = self._read_buffer()
        sleep(0.05)
        if (restbuffer!=''):
            logging.error(__name__ + ' : Buffer contained unread data : ' +
                restbuffer)
        logging.debug(__name__ + ' : writing to vpp43')
        vpp43.write(self._vi, tekst)
        sleep(0.05)

    # Keep track of data
    def _store_value(self, name, val):
        '''
        Stores a value in local memory
        self._values

        Input:
            name (string) : name of the variable
            val (depends) : value of variable

        Output:
            None
        '''
        logging.debug(__name__ + ' : Store %s as %s' % (name, val))
        self._values[name] = val

    def _ask_value(self, name):
        '''
        Asks for a parameter stored in memory
        self._values

        Input:
            name (string) : name of the variable

        Output:
            val (depends) : value of variable
        '''
        logging.debug(__name__ + ' : Ask for %s' % name)
        if name in self._values:
            return self._values[name]
        else:
            logging.error(__name__  + " : Try to read non-existing \
                parameter from memory : " + name)

    def _load_values_from_file(self):
        '''
        Loads the dacvalues from the local harddisk into memory

        Input:
            None

        Output:
            succesfull (bool) : false if loading failed
        '''
        logging.debug(__name__ + ' : Unpickling data')
        try:
            file = open(self._filename,'r')
            self._values = pickle.load(file)
            file.close()
            return True
        except:
            logging.debug(__name__ + " : Try to open nonexisting file")
            # error or warning??
            return False

    def _save_values_to_file(self):
        '''
        Stores the dacvalues and polarities on the local harddisk

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Pickling data')
        file = open(self._filename,'w')
        pickle.dump(self._values, file)
        file.close()

    # Conversion of data
    def _voltage_to_bytevalue(self, voltage):
        '''
        Converts a voltage on a 0V-4V scale to a 16-bits bytevalue

        Input:
            voltage (float) : a voltage in the 0V-4V range

        Output:
            byevalue (int) : the 16-bits bytevalue
        '''
        logging.debug(__name__ + ' : Converting %f volts to bytes' % voltage)
        bytevalue = int(round(voltage/4.0*65535))
        return bytevalue

    def _bytevalue_to_voltage(self, bytevalue):
        '''
        Converts a 16-bits bytevalue to a voltage on a 0V-4V scale

        Input:
            byevalue (int) : the 16-bits bytevalue

        Output:
            voltage (float) : a voltage in the 0V-4V range
        '''
        logging.debug(__name__ + ' : Converting byte %i' % bytevalue)
        value = 4.0*(bytevalue/65535.0)
        return value
