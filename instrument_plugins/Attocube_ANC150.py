# Attocube_ANC150, attocube piezo step controller ANC150 driver
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
import copy

class Attocube_ANC150(Instrument):

    _RE_MODE = re.compile('mode = (\w+)')
    _RE_FREQ = re.compile('frequency = (\d+) Hz')
    _RE_VOLT = re.compile('voltage = (\d+) V')
    _RE_CAP = re.compile('capacitance = (\d+) C')
    _RE_SN = re.compile('serial number (\d+)')
    _RE_VER = re.compile('version (.*)')

    _ERRMSG_AXIS = "Axis not in computer control mode"

    def __init__(self, name, address, reset=False, **kwargs):
        Instrument.__init__(self, name, address=address, reset=False, **kwargs)

        self._address = address
        self._visa = visa.instrument(self._address,
                        baud_rate=38400, data_bits=8, stop_bits=1,
                        parity=visa.no_parity, term_chars='\r\n',
                        timeout=2)
        self._clear_buffer()
        self._last_error = ''
        self._last_ccon_warning = [0, 0, 0]

        self.add_parameter('version',
            flags=Instrument.FLAG_GET,
            type=types.StringType)

        self.add_parameter('mode',
            flags=Instrument.FLAG_GETSET,
            channels=(1, 3),
            type=types.StringType,
            format_map={
                'E': 'Ext',
                'S': 'Stp',
                'G': 'Gnd',
                'C': 'Cap',
            },
            doc="mode is one of 'ext', 'stp', 'gnd' or 'cap', or first letter")

        self.add_parameter('frequency',
            flags=Instrument.FLAG_GETSET,
            channels=(1, 3),
            type=types.IntType,
            minval=0, maxval=8000)

        self.add_parameter('voltage',
            flags=Instrument.FLAG_GETSET,
            channels=(1, 3),
            type=types.IntType,
            minval=0, maxval=70)

        self.add_parameter('capacitance',
            flags=Instrument.FLAG_GET,
            channels=(1, 3),
            type=types.IntType)

        self._speed = [0, 0, 0]
        self.add_parameter('speed',
            flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET,
            doc="""
            Set speed for continuous motion mode.
            """)

        self.add_function('step', parameters=[{
                'name': 'channel',
                'type': types.IntType,
            }, {
                'name': 'steps',
                'type': types.IntType
            }])

        self.add_function('start')
        self.add_function('stop')

        if reset:
            self.reset()
        else:
            self.get_all()

    def _clear_buffer(self):
        self._visa.clear()
        time.sleep(0.02)
        self._visa.write('')

    def get_last_error(self):
        return self._last_error

    def _ask(self, query):
        self._visa.write(query)
        try:
            line, lastline = '', ''
            while not (line.startswith('OK') or line.startswith('ERROR')):
                lastline = line
                line = self._visa.read()
        finally:
            if line.startswith('ERROR'):
                self._last_error = lastline
                return None
            else:
                return lastline

    def _short_cmd(self, query):
        self._visa.write(query)
        line = self._visa.read()
        if line.find('+') != -1:
            return True
        else:
            return False

    def _parse(self, reply, regexp):
        if reply is None:
            return None

        m = regexp.search(reply)
        if m is None:
            return None
        else:
            return m.group(1)

    def reset(self):
        self._visa.write('resetp')

    def get_all(self):
        for ch in xrange(1, 4):
            self.get('mode%d' % ch)
            self.get('frequency%d' % ch)
            self.get('voltage%d' % ch)

    def _do_get_version(self):
        reply = self._ask('ver')
        ver = self._parse(reply, self._RE_VER)
        return ver

    def _do_get_mode(self, channel):
        reply = self._ask('getm %d' % channel)
        return self._parse(reply, self._RE_MODE)

    def _do_set_mode(self, mode, channel):
        ret = self._short_cmd('$M%d%s' % (channel, mode))
        if ret:
            return True
        else:
            # Warn about axis not being in computer control once per minute
            ret = self.get('mode%d' % channel)
            if ret is None and self.get_last_error() == self._ERRMSG_AXIS and \
                    (time.time() - self._last_ccon_warning[channel - 1]) > 60:
                self._last_ccon_warning[channel - 1] = time.time()
                logging.warning('Axis %d not in computer control mode', channel)
            return ret

    def _do_get_frequency(self, channel):
        reply = self._ask('getf %d' % channel)
        return self._parse(reply, self._RE_FREQ)

    def _do_set_frequency(self, freq, channel):
        reply = self._ask('setf %d %d' % (channel, freq))
        return (reply is not None)

    def _do_get_voltage(self, channel):
        reply = self._ask('getv %d' % channel)
        return self._parse(reply, self._RE_VOLT)

    def _do_set_voltage(self, volt, channel):
        reply = self._ask('setv %d %d' % (channel, volt))
        return (reply is not None)

    def _do_get_capacitance(self, channel):
        reply = self._ask('getc %d' % channel)
        return self._parse(reply, self._RE_CAP)

    def step(self, channel, steps):
        if steps == 0:
            return True

        if steps > 0:
            dir = 'u'
        else:
            dir = 'd'
            steps = -steps

        if steps == 1:
            ret = self._short_cmd('$S%d%s' % (channel, dir.upper()))
            if not ret:
                logging.info('Axis %d problem, trying to set mode', channel)
                self.set('mode%d' % channel, 's')
                ret = self._short_cmd('$S%d%s' % (channel, dir.upper()))

            return ret

        if steps == 'c' or steps == -1:
            steps = 'c'
        else:
            steps = str(steps)

        reply = self._ask('step%s %d %s' % (dir, channel, steps))
        if not reply:
            logging.info('Axis %d problem, trying to set mode', channel)
            self.set('mode%d' % channel, 's')
            reply = self._ask('step%s %d %s' % (dir, channel, steps))

        return (reply is not None)

    def _do_set_speed(self, val):
        for i in range(len(self._speed)):
            if self._speed[i] != val[i]:
                self.set('frequency%d' % (i + 1), int(abs(val[i])))
        self._speed = copy.copy(val)

    def start(self):
        '''Start continuous motion'''

        for i in range(len(self._speed)):
            mode = self.get('mode%d' % (i + 1), query=False)

            self.set('mode%d' % (i + 1), 'stp')
            if self._speed[i] > 0:
                self.stepu(i + 1, 'c')
            elif self._speed[i] < 0:
                self.stepd(i + 1, 'c')

    def stop(self):
        '''Stop continuous motion'''

        for i in range(len(self._speed)):
            self._ask('stop %d' % (i + 1))
