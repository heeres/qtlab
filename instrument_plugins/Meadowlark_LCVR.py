# Meadowlark_LCVR.py qtlab driver for Meadowlark LCVR
# Device manual at http://www.zaber.com/wiki/Manuals/T-NM
#
# Reinier Heeres <reinier@heeres.eu>, 2009
# Umberto Perinetti <umberto.perinetti@gmail.com>, 2009
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

import ctypes
import numpy as np
import time
from instrument import Instrument
import types
import logging
import qt

# Code that identifies the LCVR controller
_guid = np.array([0x8b, 0x5b, 0x2b, 0xa2,
                  0x70, 0xc6, 0x98, 0x41,
                  0x93, 0x85, 0xaa, 0xba,
                  0x9d, 0xfc, 0x7d, 0x2b], dtype=np.uint8)

_flags = 0x40000000

def get_device_count():
    '''Return number of devices present.'''
    return _drv.USBDRVD_GetDevCount(_guid.ctypes.data)

def open_device(devid):
    '''Open device and return device handle.'''
    ret = _drv.USBDRVD_OpenDevice(devid, _flags, _guid.ctypes.data)
    if ret == -1:
        print 'Unable to open device'
    return ret

def close_device(devhandle):
    return _drv.USBDRVD_CloseDevice(devhandle)

def open_pipe(devid, pipeid):
    '''Open a pipe and return the pipe handle.'''
    ret = _drv.USBDRVD_PipeOpen(devid, pipeid, _flags, _guid.ctypes.data)
    if ret == -1:
        print 'Unable to open pipe'
    return ret

def close_pipe(devid, pipehandle):
    return _drv.USBDRVD_PipeClose(pipehandle)

def bulk_write(devhandle, cmd):
    buf = ctypes.create_string_buffer(cmd)
    ret = _drv.USBDRVD_BulkWrite(devhandle, 1, buf, len(cmd))
    if ret == -1:
        print 'Write failed'
    return ret

def bulk_read(devhandle):
    buf = ctypes.create_string_buffer('\000' * 256)
    output = _drv.USBDRVD_BulkRead(devhandle, 0, buf, len(buf))
    return buf.value

class Meadowlark_LCVR(Instrument):

    def __init__(self, name, devid=1):
        logging.info(__name__ + ' : Initializing Meadowlark LCVR')
        Instrument.__init__(self, name, tags=['physical'])

        self._devhandle = open_device(devid)
        self._pipe0 = open_pipe(devid, 0)
        self._pipe1 = open_pipe(devid, 1)
        self._alias_info = {}

        self.add_parameter('version',
            flags=Instrument.FLAG_GET,
            type=types.StringType)

        self.add_parameter('voltage',
            flags=Instrument.FLAG_GETSET,
            channels=(1, 4),
            type=types.FloatType)

    def write(self, cmd):
        ret = bulk_write(self._devhandle, cmd)

    def read(self):
        reply = bulk_read(self._devhandle)
        reply = reply.rstrip()
        return reply

    def ask(self, cmd):
        self.write(cmd)
        time.sleep(0.02)
        return self.read()

    def do_get_version(self):
        return self.ask('ver:?\r')

    def do_get_voltage(self, channel):
        reply = self.ask('ld:%d,?\r' % channel)
        if reply.find(',') != -1:
            val = round(1000 * int(reply.split(',')[1]) / 6553.5)
            return val / 1000
        return 0

    def do_set_voltage(self, volts, channel):
        ii = round(volts * 6553.5)
        return self.ask('ld:%d,%d\r' % (channel, ii))

    def do_set_alias(self, name, val):
        if name not in self._alias_info:
            logging.warning('LCVR: No such alias')
            return False
        if val not in self._alias_info[name]:
            logging.warning('LCVR: No such alias value')
            return False
        for ch, chval in self._alias_info[name][val]:
            self.set('voltage%d' % ch, chval)
        return True

    def add_alias(self, name, channel_info):
        '''
        channel_info is a dictionary. For each possible setting it
        contains a list of (channel, value) tuples. For example:
        {
            'H': ((1, 1.0), (2, 2.0)),
            'V': ((2, 2.0), (1, 1.0)),
        }
        '''

        if name in self._alias_info:
            logging.warning('Alias already exists!')
            return False
        self._alias_info[name] = channel_info

        self.add_parameter(name,
            flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET,
            option_list=channel_info.keys(),
            set_func=lambda val: self.do_set_alias(name, val),
            type=types.StringType,
            )

def detect_instruments():
    count = get_device_count()
    for id in range(count):
        qt.instruments.create('LCVR%d' % id + 1,
                'Meadowlark_LCVR', devid=id + 1)

# Apparently it differs whether windll or cdll is required
_drv = ctypes.cdll.usbdrvd
try:
    get_device_count()
except:
    _drv = ctypes.windll.usbdrvd

