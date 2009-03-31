# IVVI.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Reinier Heeres <reinier@heeres.eu>, 2008
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
import numpy

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
        if numdacs / 4 * 4 == numdacs and numdacs > 0:
            self._numdacs = numdacs
        else:
            logging.error(__name__ + ' : specified number of dacs needs to be multiple of 4')
        self.pol_num = range(self._numdacs)

        # Add functions
        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('set_dacs_zero')

        # Create functions to set the dacpolarity for each set of dacs, and add them to the wrapper
        self.add_parameter('pol_dacrack',
            type=types.StringType,
            channels=(1, self._numdacs/4),
            flags=Instrument.FLAG_SET)

        self._setdacbounds = False
        for j in range(numdacs / 4):
            self.set('pol_dacrack%d' % (j+1), polarity[j])
        self._setdacbounds = True

        # Add the rest of the parameters
        self.add_parameter('dac',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._numdacs),
            minval=self.pol_num[0],
            maxval=self.pol_num[0] + 4000.0,
            maxstep=10, stepdelay=50,
            units='mV', format='%.02f',
            tags=['sweep'])

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
        self.set_dacs_zero()
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
        for i in range(self._numdacs):
            self.get('dac%d' % (i+1))

    def set_dacs_zero(self):
        for i in range(self._numdacs):
            self.set('dac%d' % (i+1), 0)

    # Conversion of data
    def _mvoltage_to_bytes(self, mvoltage):
        '''
        Converts a mvoltage on a 0mV-4000mV scale to a 16-bit integer equivalent
        output is a list of two bytes

        Input:
            mvoltage (float) : a mvoltage in the 0mV-4000mV range

        Output:
            (dataH, dataL) (int, int) : The high and low value byte equivalent
        '''
        logging.debug(__name__ + ' : Converting %f mVolts to bytes' % mvoltage)
        bytevalue = int(round(mvoltage/4000.0*65535))
        dataH = int(bytevalue/256)
        dataL = bytevalue - dataH*256
        return (dataH, dataL)

    def _numbers_to_mvoltages(self, numbers):
        '''
        Converts a list of bytes to a list containing
        the corresponding mvoltages
        '''
        logging.debug(__name__ + ' : Converting numbers to mvoltages')
        values = range(self._numdacs)
        for i in range(self._numdacs):
            values[i] = ((numbers[2 + 2*i]*256 + numbers[3 + 2*i])/65535.0*4000.0) + self.pol_num[i]
        return values

    # Communication with device
    def _do_get_dac(self, channel):
        '''
        Returns the value of the specified dac

        Input:
            channel (int) : 1 based index of the dac

        Output:
            voltage (float) : dacvalue in mV
        '''
        logging.debug(__name__ + ' : reading voltage from dac%s' % channel)
        mvoltages = self._get_dacs()
        return mvoltages[channel - 1]

    def _do_set_dac(self, mvoltage, channel):
        '''
        Sets the specified dac to the specified voltage

        Input:
            mvoltage (float) : output voltage in mV
            channel (int)    : 1 based index of the dac

        Output:
            reply (string) : errormessage
        '''
        logging.debug(__name__ + ' : setting voltage of dac%s to %.01f mV' % \
            (channel, mvoltage))
        (DataH, DataL) = self._mvoltage_to_bytes(mvoltage - self.pol_num[channel-1])
        message = "%c%c%c%c%c%c%c" % (7, 0, 2, 1, channel, DataH, DataL)
        reply = self._send_and_read(message)
        return reply

    def _get_dacs(self):
        '''
        Reads from device and returns all dacvoltages in a list

        Input:
            None

        Output:
            voltages (float[]) : list containing all dacvoltages (in mV)
        '''
        logging.debug(__name__ + ' : getting dac voltages from instrument')
        message = "%c%c%c%c" % (4, 0, self._numdacs*2+2, 2)
        reply = self._send_and_read(message)
        mvoltages = self._numbers_to_mvoltages(reply)
        return mvoltages

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

    def _do_set_pol_dacrack(self, flag, channel):
        '''
        Changes the polarity of the specified set of dacs

        Input:
            flag (string) : 'BIP', 'POS' or 'NEG'
            channel (int) : 0 based index of the rack

        Output:
            None
        '''
        logging.debug(__name__ + ' :  setting polarity of rack %d to %s' % (channel, flag))
        for i in range(4*(channel-1),4*(channel)):
            if (flag.upper() == 'NEG'):
                self.pol_num[i] = -4000
            elif (flag.upper() == 'BIP'):
                self.pol_num[i] = -2000
            elif (flag.upper() == 'POS'):
                self.pol_num[i] = 0
            else:
                logging.error(__name__ + ' : Try to set invalid dacpolarity')

            if self._setdacbounds:
                self.set_parameter_bounds('dac' + str(i+1),
                        self.pol_num[i], self.pol_num[i] + 4000.0)

        if self._setdacbounds:
            self.get_all()

    def get_pol_dac(self, dacnr):
        '''
        Returns the polarity of the dac channel specified

        Input:
            dacnr (int) : 1 based index of the dac

        Output:
            polarity (string) : 'BIP', 'POS' or 'NEG'
        '''
        logging.debug(__name__ + ' : getting polarity of dac %d' % dacnr)
        val = self.pol_num[dacnr-1]

        if (val == -4000):
            return 'NEG'
        elif (val == -2000):
            return 'BIP'
        elif (val == 0):
            return 'POS'
        else:
            return 'Invalid polarity in memory'

    def byte_limited_arange(self, start, stop, step=1, pol=None, dacnr=None):
        '''
        Creates array of mvoltages, in integer steps of the dac resolution. Either
        the dac polarity, or the dacnr needs to be specified.
        '''
        if pol is not None and dacnr is not None:
            logging.error('byte_limited_arange: speficy "pol" OR "dacnr", NOT both!')
        elif pol is None and dacnr is None:
            logging.error('byte_limited_arange: need to specify "pol" or "dacnr"')
        elif dacnr is not None:
            pol = self.get_pol_dac(dacnr)

        if (pol.upper() == 'NEG'):
            polnum = -4000
        elif (pol.upper() == 'BIP'):
            polnum = -2000
        elif (pol.upper() == 'POS'):
            polnum = 0
        else:
            logging.error(__name__ + ' : Try to set invalid dacpolarity')

        start_byte = int(round((start-polnum)/4000.0*65535))
        stop_byte = int(round((stop-polnum)/4000.0*65535))
        byte_vec = numpy.arange(start_byte, stop_byte+1, step)
        mvolt_vec = byte_vec/65535.0 * 4000.0 + polnum
        return mvolt_vec
