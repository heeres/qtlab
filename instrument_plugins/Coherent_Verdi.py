# Coherent_Verdi.py
# Reinier Heeres <reinier@heeres.eu>, 2013
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

class Coherent_Verdi(Instrument):

    def __init__(self, name, address, reset=False):
        Instrument.__init__(self, name, tags=['physical'])
                
        # Set parameters
        self._address = address
        
        # Add functions
        self.add_function('reset')
        self.add_function('get_all')
#        self.add_function('optimize_LBO')
#        self.add_function('optimize_diodes')

        self.add_parameter('tgt_power',
            type=types.FloatType, units='W', format='%.04f',
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('output_power',
            type=types.FloatType, units='W', format='%.03f',
            flags=Instrument.FLAG_GET)
        self.add_parameter('shutter',
            type=types.IntType, format_map={0: 'Closed', 1: 'Open'},
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('mode',
            type=types.IntType, format_map={1: 'Light', 0: 'Current'},
            flags=Instrument.FLAG_GET)
        self.add_parameter('current',
            type=types.FloatType, units='A', format='%.01f',
            flags=Instrument.FLAG_GET)
        self.add_parameter('Tbaseplate',
            type=types.FloatType, units='C', format='%.02f',
            flags=Instrument.FLAG_GET)
        self.add_parameter('Tetalon',
            type=types.FloatType, units='C', format='%.02f',
            flags=Instrument.FLAG_GET)
        self.add_parameter('TLBO',
            type=types.FloatType, units='C', format='%.02f',
            flags=Instrument.FLAG_GET)
        self.add_parameter('Tdiode',
            type=types.FloatType, units='C', format='%.02f',
            flags=Instrument.FLAG_GET, channels=(1,2))
        self.add_parameter('THSdiode',
            type=types.FloatType, units='C', format='%.02f',
            flags=Instrument.FLAG_GET, channels=(1,2))
        self.add_parameter('Idiode',
            type=types.FloatType, units='A', format='%.01f',
            flags=Instrument.FLAG_GET, channels=(1,2))
        self.add_parameter('Tvanadate',
            type=types.FloatType, units='C', format='%.02f',
            flags=Instrument.FLAG_GET, channels=(1,2))
        self.add_parameter('PCdiode',
            type=types.FloatType, units='W', format='%.02f',
            flags=Instrument.FLAG_GET, channels=(1,2))
        
        self._visa = visa.SerialInstrument(address,
                        data_bits=8, stop_bits=1, parity=0,
                        baud_rate=19200, term_chars='\r\n')

        if reset:
            self.reset()
        else:
            self.get_all()

    def reset(self):
        self.get_all()

    def get_all(self):
        self.get_tgt_power()
        self.get_output_power()
        self.get_shutter()
        self.get_mode()
        self.get_Tdiode1()
        self.get_Tdiode2()
        self.get_THSdiode1()
        self.get_THSdiode2()
        self.get_Idiode1()
        self.get_Idiode2()
        self.get_Tbaseplate()
        self.get_Tetalon()
        self.get_TLBO()
        self.get_Tvanadate1()
        self.get_Tvanadate2()
        self.get_current()
        self.get_PCdiode1()
        self.get_PCdiode2()

    def _query(self, cmd):
        s = self._visa.ask(cmd)
        cmd = cmd.strip()
        if len(s) > len(cmd):
            return s[len(cmd):]
        else:
            return 0
        
    def do_get_output_power(self):
        s = self._query('?P\r\n')
        return float(s)

    def do_get_shutter(self):
        s = self._query('?S\r\n')
        return int(s)
        
    def do_set_shutter(self, s):
        s = self._query('S = %d\r\n' % s)
        return int(s)

    def do_get_mode(self):
        s = self._query('?M\r\n')
        return int(s)
        
    def do_get_tgt_power(self):
        s = self._query('?SP\r\n')
        return float(s)
            
    def do_set_tgt_power(self, p):
        self._visa.ask('P = %.04f\r\n')
        return True
        
    def do_get_Tbaseplate(self):
        s = self._query('?BT\r\n')
        return float(s)

    def do_get_Tetalon(self):
        s = self._query('?ET\r\n')
        return float(s)

    def do_get_TLBO(self):
        s = self._query('?LBOT\r\n')
        return float(s)

    def do_get_THSdiode(self, channel):
        s = self._query('?D%dHST\r\n' % channel)
        return float(s)
        
    def do_get_Tdiode(self, channel):
        s = self._query('?D%dT\r\n' % channel)
        return float(s)

    def do_get_Idiode(self, channel):
        s = self._query('?D%dC\r\n' % channel)
        return float(s)
        
    def do_get_Tvanadate(self, channel):
        if channel == 1:
            s = self._query('?VT\r\n')
        else:
            s = self._query('?V2T\r\n')
        return float(s)

    def do_get_PCdiode(self, channel):
        s = self._query('?D%dPC\r\n' % channel)
        return float(s)
        
    def do_get_current(self):
        s = self._query('?C\r\n')
        return float(s)
