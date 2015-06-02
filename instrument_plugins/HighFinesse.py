# HighFinesse.py - Instrument plugin to communicate with a High Finesse 
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
from ctypes import *

wlmData = windll.wlmData

GetWvl = wlmData.GetWavelength
GetWvl.restype = c_double
GetFrq = wlmData.GetFrequency
GetFrq.restype = c_double
GetLw = wlmData.GetLinewidth
GetLw.restype = c_double
GetPwr = wlmData.GetPowerNum
GetPwr.restype = c_double

class HighFinesse(Instrument):
    '''High Finesse Wavelength meter'''

    def __init__(self, name, reset=False):
        Instrument.__init__(self,name)

        self.add_parameter('wavelength',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                units='nm')
	self.add_parameter('frequency',
	        type=types.FloatType,
		flags=Instrument.FLAG_GET,
		units='THz')
	self.add_parameter('linewidth',
		type=types.FloatType,
		flags=Instrument.FLAG_GET,
		units='THz')
        self.add_parameter('power',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                units='microW')

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
	self.get_frequency()

#### communication with machine

    def do_get_wavelength(self):
	Wavelength = GetWvl(c_double(0))
        return Wavelength

    def do_get_power(self):
        return GetPwr(c_long(1), c_double(0))

    def do_get_frequency(self):
	return GetFrq(c_double(0))

    def do_get_linewidth(self):
	return GetLw(c_char_p(cReturnFrequency),c_double(0))

