# Delta_PSC232.py driver for the PSC232 Delta Power Supply Controller
# Gabriele de Boo <g.deboo@student.unsw.edu.au>, 2012
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
import visa

class Delta_PSC232(Instrument):

    def __init__(self, name, address=None, channel=1):
        Instrument.__init__(self, name, tags=['measure'])

        self._address = address
#	self._term_chars = '\n\r\x04'
        self._channel = channel
        self._visains = visa.instrument(address) #, term_chars = "\n\r\x04") # Hoo Rah
        self._visains.baud_rate = 4800L
        self._visains.write("*R")               # Reset the instrument
        self._visains.write("CH "+str(channel)) # Talking to the correct instrument

        self.add_parameter('Minimum_Voltage', type=types.FloatType,
                           flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET)
        self.add_parameter('Maximum_Voltage', type=types.FloatType,
                           flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET)
        self.add_parameter('Minimum_Current', type=types.FloatType,
                           flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET)
        self.add_parameter('Maximum_Current', type=types.FloatType,
                           flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET)
        self.add_parameter('Voltage', type=types.FloatType,
                           flags=Instrument.FLAG_GETSET)
        self.add_parameter('Current', type=types.FloatType,
                           flags=Instrument.FLAG_GETSET)

#        self.add_function('set_defaults')
        self.set_defaults()

    def set_defaults(self):
        '''Set default parameters.'''
        self.set_Minimum_Voltage(0)
        self.set_Maximum_Voltage(30)
        self.set_Minimum_Current(0)
        self.set_Maximum_Current(5)
        self._visains.write("REMOTE")

    def do_set_Minimum_Voltage(self, minvol):
        self._visains.write("SOUR:VOLT:MIN " + str(minvol))

    def do_set_Maximum_Voltage(self, maxvol):    
        self._visains.write("SOUR:VOLT:MAX " + str(maxvol))

    def do_set_Minimum_Current(self, mincur):
        self._visains.write("SOUR:CURR:MIN " + str(mincur))

    def do_set_Maximum_Current(self, maxcur):        
        self._visains.write("SOUR:CURR:MAX " + str(maxcur))

    def do_set_Voltage(self, V):
        self._visains.write("SOU:VOLT " + str(V))

    def do_set_Current(self, I):
        self._visains.write("SOU:CURR " + str(I))

    def do_get_Voltage(self):
#        return self._remove_EOT(self._visains.ask("MEAS:VOLT?"))
        return float(self._visains.ask("MEAS:VOLT?"))

    def do_get_Current(self):
        return float(self._visains.ask("MEAS:CURR?"))

