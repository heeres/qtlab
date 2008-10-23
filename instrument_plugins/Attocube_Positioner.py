# Attocube_Positioner, Attocube positioner with software feedback
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
import logging
import random
import math
import misc
import time
import qt
from packages import positioning

class Attocube_Positioner(Instrument):

    def __init__(self, name, anc=None, arc=None, channels=3):
        Instrument.__init__(self, name, tags=['positioner'])

        if type(anc) is types.StringType:
            self._anc = qt.instruments[anc]
        else:
            self._anc = anc
        if type(arc) is types.StringType:
            self._arc = qt.instruments[arc]
        else:
            self._arc = arc

        # Instrument parameters
        self.add_parameter('position',
            flags=Instrument.FLAG_GET,
            format='%.03f, %.03f, %.03f')
        self.add_parameter('speed',
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('channels',
            flags=Instrument.FLAG_GETSET)
        self.set_channels(channels)

        # Instrument functions
        self.add_function('start')
        self.add_function('stop')
        self.add_function('move_abs')

    def _do_get_position(self, query=True):
        return self._arc.get_position(query=query)

    def _do_get_channels(self, query=True):
        return self._channels

    def _do_set_channels(self, val, query=True):
        self._channels = val

    def start(self):
        self._anc.start()

    def stop(self):
        self._anc.stop()

    def step(self, chan, nsteps):
        self._anc.step(chan + 1, nsteps)

    def _do_get_speed(self):
        return self._anc.get_speed()

    def _do_set_speed(self, val):
        self._anc.set_speed(val)

    def move_abs(self, pos, **kwargs):
        '''
        move_abs, move to an absolute position using feedback read-out.

        Input:
            x (float): x position
            y (float): y position
            startstep: start steps to use
            maxstep: maximum steps
            minstep: minimum steps for fine position
        '''

        self._anc.set_mode1('stp')
        self._anc.set_frequency1(200)
        self._anc.set_mode2('stp')
        self._anc.set_frequency2(200)
        self._anc.set_mode3('stp')
        self._anc.set_frequency3(200)
        positioning.move_abs(self._arc, self._anc, pos,
            startstep=4, maxstep=512, minstep=1,
            channel_ofs=1)
#        self._anc.set_mode1('gnd')
#        self._anc.set_mode2('gnd')
#        self._anc.set_mode3('gnd')
