# IVVI.py class, to perform the communication between the Wrapper and the device
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

    TODO:
    1) fix changing all polarities instead of only the first 8
    2) explain everything /rewrite init
    '''

    def __init__(self, name, address, reset=False, numdacs=8,
        polarity=['BIP', 'BIP', 'BIP', 'BIP']):
        '''
        Initialzes the IVVI, and communicates with the wrapper

        Input:
            name (string)        : name of the instrument
            address (string)     : ASRL address
            reset (bool)         : resets to default values, default=false
            numdacs (int)        : number of dacs, multiple of 4, default=8
            polarity (string[4]) : list of polarities of each set of 4 dacs
                                   choose from 'BIP', 'POS', 'NEG',
                                   default=['BIP', 'BIP', 'BIP', 'BIP']
        Output:
            None
        '''
        logging.info(__name__ + ' : Initializing instrument IVVI')
        Instrument.__init__(self, name, tags=['physical'])

        # Set parameters
        self._address = address
        self.numdacs = numdacs
        self.pol_num = range(self.numdacs)

        # Add functions
        self.add_function('reset')
        self.add_function('get_all')
        self._askdacs = False # what does this do?

        # Create functions to set the dacpolarity for each set of dacs, and add them to the wrapper
        for j in range(numdacs/4):
            tekst = "pol_dacs_%s_to_%s" % (str(4*j+1),str(4*j+4))
            self.add_parameter(tekst, type=types.StringType,
                flags=Instrument.FLAG_SET)
            getattr(self, "set_" + tekst)(polarity[j])

        # Add the rest of the parameters
        self.add_parameter('dac', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1,self.numdacs), minval=self.pol_num[0],
            maxval=self.pol_num[0] + 4.0, units='Volts')

        self._askdacs=True

        self.add_parameter('pol_dac', type=types.StringType,
            flags=Instrument.FLAG_GET, channels=(1,self.numdacs))

        for j in range(numdacs/4):
            tekst = "pol_dacs_%s_to_%s" % (str(4*j+1),str(4*j+4))
            getattr(self, "set_" + tekst)(polarity[j])

        self._open_serial_connection()

        if reset:
            self.reset()
        else:
            self.get_all()

    def __del__(self):
        '''
        Closes up the IVVI driver

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Deleting IVVI instrument')
        self._close_serial_connection()

    # open serial connection
    def _open_serial_connection(self):
        '''
        Opens the ASRL connection using vpp43
        baud=115200, databits=8, stop=one, parity=odd, no end char for reads

        Input:
            None

        Output:
            None
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
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_END_IN,
            vpp43.VI_ASRL_END_NONE)

    # close serial connection
    def _close_serial_connection(self):
        '''
        Closes the serial connection

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Closing serial connection')
        vpp43.close(self._vi)

    def reset(self):
        '''
        Resets all dacs to 0 volts

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        for i in range(1, self.numdacs+1):
            getattr(self, "set_dac" + str(i))(0.0)
        self.get_all()

    def get_all(self):
        '''
        Gets all dacvalues from the device, all polarities from memory
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : get all')
        for i in range(1, self.numdacs+1):
            getattr(self, "get_dac" + str(i))()
            getattr(self, "get_pol_dac" + str(i))()

    # Conversion of data
    def _voltage_to_bytes(self, voltage):
        '''
        Converts a voltage on a 0V-4V scale to a 16-bit integer equivalent
        output is a list of two bytes

        Input:
            voltage (float) : a voltage in the 0V-4V range

        Output:
            (dataH, dataL) (int, int) : The high and low value byte equivalent
        '''
        logging.debug(__name__ + ' : Converting %f Volts to bytes' % voltage)
        bytevalue = int(round(voltage/4.0*65535))
        dataH = int(bytevalue/256)
        dataL = bytevalue - dataH*256
        return (dataH, dataL)

    def _numbers_to_voltages(self, numbers):
        '''
        Converts a list of bytes to a list containing
        the corresponding voltages
        '''
        logging.debug(__name__ + ' : Converting numbers to voltages')
        values = range(self.numdacs)
        for i in range(self.numdacs):
            values[i] = (numbers[2 + 2*i]*256 + numbers[3 + 2*i])/65535.0*4.0+self.pol_num[i]
        return values

    # Communication with device
    def _do_get_dac(self, channel):
        '''
        Returns the value of the specified dac

        Input:
            channel (int) : 1 based index of the dac

        Output:
            voltage (float) : dacvalue in Volts
        '''
        logging.debug(__name__ + ' : reading voltage from dac%s' % channel)
        voltages = self._get_dac()
        return voltages[channel-1]

    def _do_set_dac(self, voltage, channel):
        '''
        Sets the specified dac to the specified voltage

        Input:
            voltage (float) : dacvoltage
            channel (int)   : 1 based index of the dac

        Output:
            reply (string) : errormessage
        '''
        logging.debug(__name__ + ' : setting voltage of dac%s to %s Volts'
          % (channel, voltage))
        (DataH,DataL) = self._voltage_to_bytes(voltage - self.pol_num[channel-1])
        message = "%c%c%c%c%c%c%c" % (7, 0, 2, 1, channel, DataH, DataL)
        reply = self._send_and_read(message)
        return reply

    def _get_dac(self):
        '''
        Reads from device and returns all dacvoltages in a list

        Input:
            None

        Output:
            voltages (float[]) : list containing all dacvoltages
        '''
        logging.debug(__name__ + ' : getting dac voltages from instrument')
        message = "%c%c%c%c" % (4, 0, 18, 2)
        reply = self._send_and_read(message)
        voltages = self._numbers_to_voltages(reply)
        return voltages

    def _send_and_read(self, message):
        '''
        Performs the communication with the device
        Raises an error if one occurred
        Returns a list of bytes

        Input:
            message (string)    : string conform the IVVI protocol

        Output:
            data_out_numbers (int[]) : return message
        '''
        logging.debug(__name__ + ' : do communication with instrument')
        vpp43.write(self._vi, message)
        sleep(0.02)
        data_out_string =  vpp43.read(self._vi, vpp43.get_attribute(self._vi, vpp43.VI_ATTR_ASRL_AVAIL_NUM))
        sleep(0.02)
        data_out_numbers = [ord(s) for s in data_out_string]

        if (data_out_numbers[1] != 0) or (len(data_out_numbers) != data_out_numbers[0]):
            logging.error(__name__ + ' : Error while reading : %s', data_out_numbers)

        return data_out_numbers

 #    Base functions to handle the polarity
    def _do_set_pol_dacs_1_to_4(self, flag): # MC fixme
        '''
        Sets the polarity of the first 4 dacs in the designated mode

        Input:
            flag (string) : 'BIP', 'POS' or 'NEG'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set polarity of dacs 1 to 4 to %s' % flag)
        self._change_pol_dacrack(flag, 0)

    def _do_set_pol_dacs_5_to_8(self, flag):
        '''
        Sets the polarity of the second 4 dacs in the designated mode

        Input:
            flag (string) : 'BIP', 'POS' or 'NEG'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set polarity of dacs 5 to 8 to %s' % flag)
        self._change_pol_dacrack(flag, 1)

    def _change_pol_dacrack(self, flag, rack):
        '''
        Changes the polarity of the specified set of dacs

        Input:
            flag (string) : 'BIP', 'POS' or 'NEG'
            rack (int) : 0 based index of the rack

        Output:
            None
        '''
        logging.debug(__name__ + ' :  setting polarity of rack %d to %s' % (rack, flag))
        for i in range(4*(rack),4*(rack+1)):
            if (flag.upper() == 'NEG'):
                self.pol_num[i] = -4
            elif (flag.upper() == 'BIP'):
                self.pol_num[i] = -2
            elif (flag.upper() == 'POS'):
                self.pol_num[i] = 0
            else:
                logging.error(__name__ + ' : Try to set invalid dacpolarity')

            if (self._askdacs):
                self.set_parameter_bounds('dac' + str(i+1),self.pol_num[i],
                    4+self.pol_num[i])

    def _do_get_pol_dac(self, channel):
        '''
        Returns the polarity of the dac channel specified

        Input:
            channel (int) : 1 based index of the dac

        Output:
            polarity (string) : 'BIP', 'POS' or 'NEG'
        '''
        logging.debug(__name__ + ' : getting polarity of dac %d' % channel)
        val = self.pol_num[channel-1]

        if (val == -4):
            return 'NEG'
        elif (val == -2):
            return 'BIP'
        elif (val == 0):
            return 'POS'
        else:
            return 'Invalid polarity in memory'
