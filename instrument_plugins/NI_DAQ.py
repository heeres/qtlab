# NI_DAQ.py, National Instruments Data AcQuisition instrument driver
# Reinier Heeres <reinier@heeres.eu>, 2009
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

import types
from lib.dll_support import nidaq
from instrument import Instrument
import qt

def _get_channel(devchan):
    if not '/' in devchan:
        return devchan
    parts = devchan.split('/')
    if len(parts) != 2:
        return devchan
    return parts[1]

class NI_DAQ(Instrument):

    def __init__(self, name, id):
        Instrument.__init__(self, name, tags=['physical'])

        self._id = id

        for ch_in in self._get_input_channels():
            ch_in = _get_channel(ch_in)
            self.add_parameter(ch_in,
                flags=Instrument.FLAG_GET,
                type=types.FloatType,
                units='V',
                tags=['measure'],
                get_func=self.do_get_input,
                channel=ch_in)

        for ch_out in self._get_output_channels():
            ch_out = _get_channel(ch_out)
            self.add_parameter(ch_out,
                flags=Instrument.FLAG_SET,
                type=types.FloatType,
                units='V',
                tags=['sweep'],
                set_func=self.do_set_output,
                channel=ch_out)

        self.add_parameter('chan_config',
            flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET,
            type=types.StringType,
            option_list=('Default', 'RSE', 'NRSE', 'Diff', 'PseudoDiff'))

        self.add_function('reset')

        self.reset()
        self.set_chan_config('RSE')
        self.get_all()

    def get_all(self):
        ch_in = [_get_channel(ch) for ch in self._get_input_channels()]
        self.get(ch_in)

    def reset(self):
        '''Reset device.'''
        nidaq.reset_device(self._id)

    def _get_input_channels(self):
        return nidaq.get_physical_input_channels(self._id)

    def _get_output_channels(self):
        return nidaq.get_physical_output_channels(self._id)

    def do_get_input(self, channel):
        devchan = '%s/%s' % (self._id, channel)
        return nidaq.read(devchan, config=self._chan_config)

    def do_set_output(self, val, channel):
        devchan = '%s/%s' % (self._id, channel)
        return nidaq.write(devchan, val)

    def do_set_chan_config(self, val):
        self._chan_config = val

def detect_instruments():
    '''Refresh NI DAQ instrument list.'''

    for name in nidaq.get_device_names():
        qt.instruments.create('NI%s' % name, 'NI_DAQ', id=name)

