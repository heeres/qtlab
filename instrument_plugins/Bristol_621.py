# Bristol_621.py - Instrument plugin to communicate with a Bristol 621 
# wavelengthmeter
# Gabriele de Boo <g.deboo@student.unsw.edu.au>
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
import logging
from ctypes import *

CLDevIFace = cdll.CLDevIFace

CLOpenUSBSerialDevice = CLDevIFace.CLOpenUSBSerialDevice
CLOpenUSBSerialDevice.restype = c_long
CLCloseDevice = CLDevIFace.CLCloseDevice
CLSetLambdaUnits = CLDevIFace.CLSetLambdaUnits
CLSetLambdaUnits.restype = c_int
CLGetLambdaReading = CLDevIFace.CLGetLambdaReading
CLGetLambdaReading.restype = c_double
CLGetPowerReading = CLDevIFace.CLGetPowerReading
CLGetPowerReading.restype = c_float

class Bristol_621(Instrument):
    '''Bristol 621 Wavelength meter'''

    def __init__(self, name, address=None, reset=False):
        Instrument.__init__(self,name)
        self.devHandle = CLOpenUSBSerialDevice(c_long(address))
        logging.info('Device handle of Bristol wavemeter is %s' % self.devHandle)
        # Set wavelength reading to nm
        CLSetLambdaUnits(c_int(self.devHandle), c_uint(0))

        self.add_parameter('wavelength',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                units='nm')
#	self.add_parameter('frequency',
#	        type=types.FloatType,
#		flags=Instrument.FLAG_GET,
#		units='THz')
        self.add_parameter('power',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                units='mW')

        self.add_function('close_device')

        if reset:
            self.reset()
        else:
            self.get_all()

#### initialization related

    def reset(self):
        print __name__ + ' : resetting instrument'

    def get_all(self):
        print __name__ + ' : reading all settings from instrument'
        self.get_wavelength()
        self.get_power()

#### communication with machine

    def do_get_wavelength(self):
        wavelength = None
        while wavelength == None:
            wavelength = CLGetLambdaReading(c_int(self.devHandle))
        logging.debug('Measured wavelength is %s.' % wavelength)
        return wavelength

    def do_get_power(self):
        power = CLGetPowerReading(c_int(self.devHandle))
        logging.debug('Measured power is %s.' % power)
        return power

    def close_device(self):
        if (CLCloseDevice(c_int(self.devHandle)) != 0):
            logging.warning('%s: Closing device was unsuccesfull.' % self.name)
