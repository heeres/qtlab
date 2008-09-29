# Attocube_ARC200, attocube resistive readout module ARC200 driver
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
import visa
import types
import logging
import re
import time

class Attocube_ARC200(Instrument):

    REF_5V = 0
    REF_3V = 1
    REF_1V = 2
    REF_05V = 3
    REF_03V = 4
    REF_01V = 5

    UNIT_PERCENT = 0
    UNIT_MICRON = 1
    UNIT_MM = 2
    UNIT_V = 3
    UNIT_MG = 4
    UNIT_G = 5
    UNITS = {
        UNIT_PERCENT: '%',
        UNIT_MICRON: '',
        UNIT_MM: 'mm',
        UNIT_V: 'V',
        UNIT_MG: 'mS',
        UNIT_G: 'S'
    }

    def __init__(self, name, address, reset=False, **kwargs):
        Instrument.__init__(self, name, address=address, reset=reset, **kwargs)

        self._address = address
        self._visa = visa.instrument(self._address,
                        baud_rate=57600, data_bits=8, stop_bits=1,
                        parity=visa.no_parity, term_chars='')

        self.add_parameter('mode',
            flags=Instrument.FLAG_SET,
            type=types.IntType,
            format_map={
                0: 'CONT',
                1: 'SINGLE',
            },
            doc="""
            Get/set mode:
                0: Continuous
                1: Single measurement
            """)
        self.add_parameter('refvoltage',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            minval=0, maxval=self.REF_01V)

        self.add_parameter('units',
            flags=Instrument.FLAG_SET,
            type=types.IntType,
            minval=0, maxval=self.UNIT_G,
            format_function=lambda uid: self.UNITS[uid])

        self.add_parameter('position',
            flags=Instrument.FLAG_GET,
	    format='%.03f, %.03f, %.03f')

        if reset:
            self.reset()
        else:
            self.set_mode(1)
            self.set_units(self.UNIT_PERCENT)
            self.get_all()

    def write_line(self, query):
        self._visa.write(query)
        time.sleep(0.05)
        self._visa.write('\r')

    def ask(self, query):
        self._visa.write(query)
        time.sleep(0.05)
        reply = self._visa.read()
        return reply.rstrip(' \t\r\n')
        
    def reset(self):
        self.write_line('resetp')

    def get_all(self):
        self.get_position()

    def _do_set_mode(self, mode):
        '''
        Set the measurement mode to continuous (0) or interval (1)
        '''

        if int(mode) not in (0, 1):
            return False

        logging.info('Setting mode %s' % mode)
                
        self.write_line('SM%d' % mode)
        self._visa.clear()

    def _do_set_voltage(self, ref):
        self.write_line('SRE %d' % ref)

    def _do_get_position(self):
        reply = self.ask('C')
        str_list = reply.split(',')
        float_list = [float(str_item) for str_item in str_list]
        return float_list

    def _do_set_channel_units(self, channel, units_id):
        self.write_line('SU%d%d' % (channel, units_id))

    def _do_set_units(self, units_id):
        self._do_set_channel_units(1, units_id)
        self._do_set_channel_units(2, units_id)
        self._do_set_channel_units(3, units_id)
        self.set_parameter_options('values', units=self.UNITS[units_id])
