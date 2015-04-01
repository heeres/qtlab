# Thorlabs_FiberSwitch.py - Instrument plugin to communicate with 
#                           a Thorlabs Fiberswitch
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
from qt import msleep
import logging
from visa import SerialInstrument
import types

class Thorlabs_FiberSwitch(Instrument):
    '''
    Thorlabs Fiber Switch

    The switch is being used to switch between two inputs for a connected
    wavemeter. The wavemeter reading should be accessed through this wrapper 
    so that the correct reading is given for the specified port and because
    it will block access during that time for other readings.

    When creating the instrument the used wavemeter should be specified.

    '''

    def __init__(self, name, address, wavemeter, reset=False):
        logging.debug('Initializing fiber switch on port %s.' % address)
        Instrument.__init__(self, name, tags=['physical'])
        self._visainstrument = SerialInstrument(address)
        self._visainstrument.baud_rate = 115200
        self._visainstrument.term_chars = '\n'

        self.wait_time = 0.3
        self._wavemeter = wavemeter

        self.add_parameter('active_port',
                type=types.IntType,
                flags=Instrument.FLAG_GETSET,
                minval=1, maxval=2)
        self.add_parameter('port1_wavelength',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                units='nm')
        self.add_parameter('port2_wavelength',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                units='nm')
        self.add_parameter('port1_power',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                units='mW')
        self.add_parameter('port2_power',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                units='mW')
        
        if reset:
            self.reset()
        else:
            self.get_all()

#### initialization related

    def reset(self):
        print __name__ + ' : resetting instrument'

    def get_all(self):
        print __name__ + ' : reading all settings from instrument'
        self.get_active_port()
        self.get_port1_wavelength()
        self.get_port1_power()
        self.get_port2_wavelength()
        self.get_port2_power()

#### communication with machine
    def do_get_active_port(self):
        return self._visainstrument.ask('S?')

    def do_set_active_port(self, port):
        self._visainstrument.write('S %i' %port)
        if self.get_active_port() == port:
            return True
        else:
            raise Warning('The switch did not reply with the expected port.')

    def do_get_port1_wavelength(self):
        if self.get_active_port() == 2:
            self.set_active_port(1)
            msleep(self.wait_time)
        return self._wavemeter.get_wavelength()

    def do_get_port2_wavelength(self):
        if self.get_active_port() == 1:
            self.set_active_port(2)
            msleep(self.wait_time)
        return self._wavemeter.get_wavelength()

    def do_get_port1_power(self):
        if self.get_active_port()==2:
            self.set_active_port(1)
            msleep(self.wait_time)
        return self._wavemeter.get_power()

    def do_get_port2_power(self):
        if self.get_active_port()==1:
            self.set_active_port(2)
            msleep(self.wait_time)
        return self._wavemeter.get_power()
