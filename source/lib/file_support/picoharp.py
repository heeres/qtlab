# picoharp.py, class for reading/writing Picoharp data files
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

import numpy as np
import struct
import sys

from lib.namedstruct import *

_T2WRAPAROUND = 210698240
_RESOLUTION = 4e-12

GENERAL_HEADER_INFO = (
        ('Ident', S, 16),
        ('FormatVersion', S, 6),
        ('CreatorName', S, 18),
        ('CreatorVersion', S, 12),
        ('FileTime', S, 18),
        ('CRLF', C, 2),
        ('Comment', S, 256),
        ('NumberOfCurves', U32, 1),
        ('BitsPerHistogBin', U32, 1),
        ('RoutingChannels', U32, 1),
        ('NumberOfBoards', U32, 1),
        ('ActiveCurve', U32, 1),
        ('MeasurementMode', U32, 1),
        ('SubMode', U32, 1),
        ('RangeNo', U32, 1),
        ('Offset', U32, 1),
        ('AcquisitionTime', U32, 1),
        ('StopAt', U32, 1),
        ('StopOnOvfl', U32, 1),
        ('Restart', U32, 1),
        ('DisplayLinLog', U32, 1),
        ('DisplayTimeAxisFrom', U32, 1),
        ('DisplayTimeAxisTo', U32, 1),
        ('DisplayCountAxisFrom', U32, 1),
        ('DisplayCountAxisTo', U32, 1),
        ('DisplayCurve1MapTo', U32, 1),
        ('DisplayCurve1Show', U32, 1),
        ('DisplayCurve2MapTo', U32, 1),
        ('DisplayCurve2Show', U32, 1),
        ('DisplayCurve3MapTo', U32, 1),
        ('DisplayCurve3Show', U32, 1),
        ('DisplayCurve4MapTo', U32, 1),
        ('DisplayCurve4Show', U32, 1),
        ('DisplayCurve5MapTo', U32, 1),
        ('DisplayCurve5Show', U32, 1),
        ('DisplayCurve6MapTo', U32, 1),
        ('DisplayCurve6Show', U32, 1),
        ('DisplayCurve7MapTo', U32, 1),
        ('DisplayCurve7Show', U32, 1),
        ('DisplayCurve8MapTo', U32, 1),
        ('DisplayCurve8Show', U32, 1),
        ('Param1Start', FLOAT, 1),
        ('Param1Step', FLOAT, 1),
        ('Param1End', FLOAT, 1),
        ('Param2Start', FLOAT, 1),
        ('Param2Step', FLOAT, 1),
        ('Param2End', FLOAT, 1),
        ('Param3Start', FLOAT, 1),
        ('Param3Step', FLOAT, 1),
        ('Param3End', FLOAT, 1),
        ('RepeatMode', U32, 1),
        ('RepeatsPerCurve', U32, 1),
        ('RepeatTime', U32, 1),
        ('RepeatWaitTime', U32, 1),
        ('ScriptName', S, 20),
        ('HardwareIdent', S, 16),
        ('HardwareVersion', S, 8),
        ('HardwareSerial', U32, 1),
		('SyncDivider', U32, 1),
		('CFDZeroCross0', U32, 1),
		('CFDLevel0', U32, 1),
		('CFDZeroCross1', U32, 1),
		('CFDLevel1', U32, 1),
		('Resolution', FLOAT, 1),
		('RouterModelCode', U32, 1),
		('RouterEnabled', U32, 1),
		('RtChan1_InputType', U32, 1),
		('RtChan1_InputLevel', U32, 1),
		('RtChan1_InputEdge', U32, 1),
		('RtChan1_CFDPresent', U32, 1),
		('RtChan1_CFDLevel', U32, 1),
		('RtChan1_CFDZeroCross', U32, 1),
		('RtChan2_InputType', U32, 1),
		('RtChan2_InputLevel', U32, 1),
		('RtChan2_InputEdge', U32, 1),
		('RtChan2_CFDPresent', U32, 1),
		('RtChan2_CFDLevel', U32, 1),
		('RtChan2_CFDZeroCross', U32, 1),
		('RtChan3_InputType', U32, 1),
		('RtChan3_InputLevel', U32, 1),
		('RtChan3_InputEdge', U32, 1),
		('RtChan3_CFDPresent', U32, 1),
		('RtChan3_CFDLevel', U32, 1),
		('RtChan3_CFDZeroCross', U32, 1),
		('RtChan4_InputType', U32, 1),
		('RtChan4_InputLevel', U32, 1),
		('RtChan4_InputEdge', U32, 1),
		('RtChan4_CFDPresent', U32, 1),
		('RtChan4_CFDLevel', U32, 1),
		('RtChan4_CFDZeroCross', U32, 1),
    )

class PHDFile:

    _HEADERINFO = GENERAL_HEADER_INFO

    _CURVEINFO = (
		('CurveIndex', U32, 1),
		('TimeOfRecording', U32, 1),
		('HardwareIdent', C, 16),
		('HardwareVersion', C, 8),
		('HardwareSerial', U32, 1),
		('SyncDivider', U32, 1),
		('CFDZeroCross0', U32, 1),
		('CFDLevel0', U32, 1),
		('CFDZeroCross1', U32, 1),
		('CFDLevel1', U32, 1),
		('Offset', U32, 1),
		('RoutingChannel', U32, 1),
		('ExtDevices', U32, 1),
		('MeasMode', U32, 1),
		('SubMode', U32, 1),
		('P1', FLOAT, 1),
		('P2', FLOAT, 1),
		('P3', FLOAT, 1),
		('RangeNo', U32, 1),
		('Resolution', FLOAT, 1),
		('Channels', U32, 1),
		('AcquisitionTime', U32, 1),
		('StopAfter', U32, 1),
		('StopReason', U32, 1),
		('InpRate0', U32, 1),
		('InpRate1', U32, 1),
		('HistCountRate', U32, 1),
		('IntegralCount', U64, 1),
		('Reserved', U32, 1),
		('DataOffset', U32, 1),
		('RouterModelCode', U32, 1),
		('RouterEnabled', U32, 1),
		('RtChan_InputType', U32, 1),
		('RtChan_InputLevel', U32, 1),
		('RtChan_InputEdge', U32, 1),
		('RtChan_CFDPresent', U32, 1),
		('RtChan_CFDLevel', U32, 1),
		('RtChan_CFDZeroCross', U32, 1),
    )

    def __init__(self, filename=None):
        self._info = {}
        self._filename = ''
        self._data = None

        # Little-endian
        self._header_struct = NamedStruct(self._HEADERINFO, alignment='<')
        self._curve_struct = NamedStruct(self._CURVEINFO, alignment='<')

        if filename:
            self.load(filename)

    def load(self, filename):
        f = open(filename, 'rb')
        data = f.read(692)
        self._header = self._header_struct.unpack(data)

        self._curve_info = []
        self._curve = []
        for i in range(self._header['NumberOfCurves']):
            data = f.read(172)
            curve = self._curve_struct.unpack(data)
            self._curve_info.append(curve)

        for curve in self._curve_info:
            f.seek(curve['DataOffset'])
            if self._header['BitsPerHistogBin'] != 32:
                print 'Can only read 32 bit data'

            ar = np.zeros(curve['Channels'])
            for i in range(curve['Channels']):
                data = f.read(4)
                ar[i] = struct.unpack('<L', data)[0]

            self._curve.append(ar)

    def get_header(self):
        return self._header

    def get_curve_info(self, i):
        return self._curve_info[i]

    def get_curve(self, i, xdim=True):
        y = self._curve[i]
        if xdim:
            x = [j * self._curve_info[i]['Resolution'] for j in range(len(y))]
            return np.column_stack((x, y))
        else:
           return y

class PT2File:

    _HEADERINFO = GENERAL_HEADER_INFO

    _T2T3INFO = (
		('ExtDevices', U32, 1),
		('Reserved1', U32, 1),
		('Reserved2', U32, 1),
		('InpRate0', U32, 1),
		('InpRate1', U32, 1),
		('StopAfter', U32, 1),  # In ms
		('StopReason', U32, 1), # 0 = time over, 1 = manual, 2 = overflow
		('NumRecords', U32, 1),
		('ImgHdrSize', U32, 1),
    )

    def __init__(self, filename=None):
        self._info = {}
        self._filename = ''
        self._data = None

        # Little-endian
        self._header_struct = NamedStruct(self._HEADERINFO, alignment='<')
        self._t2t3_struct = NamedStruct(self._T2T3INFO, alignment='<')

        if filename:
            self.load(filename)

    def load(self, filename, progress=0):
        f = open(filename, 'rb')
        data = f.read(692)
        self._header = self._header_struct.unpack(data)

        data = f.read(36)
        self._t2t3 = self._t2t3_struct.unpack(data)

        data = f.read(self._t2t3['ImgHdrSize'])

        self._data = np.fromfile(f, np.uint32, -1)

    def get_data(self):
        return self._data

    def get_ch_data(self, ch, progress=0):
        chs = (self._data >> 28)
        d = self._data.astype(np.float64)

        # Add overflows
        idx = np.where(d == 0xf0000000)[0]
        add = 0
        starti = 0
        for endi in idx:
            d[starti:endi] += add
            starti = endi + 1
            add += _T2WRAPAROUND
        d[starti:] += add

        # Convert to time
        mask = (chs == ch)
        d = d[mask] * _RESOLUTION

        return d

    def get_header(self):
        return self._header

    def get_t2t3(self):
        return self._t2t3

    def get_data(self):
        return self._data

class PT3File(PT2File):
    def __init__(self, filename=None):
        PT2File.__init__(self, filename)

def test_phd(fname):
    phd = PHDFile(fname)

    print 'Info:'
    info = phd.get_header()
    for line in phd._HEADERINFO:
        key = line[0]
        val = info[key]
        print '  %s => %r' % (key, val)

    for i in range(info['NumberOfCurves']):
        print 'Curve %d:' % (i, )
        cinfo = phd.get_curve_info(i)
        for line in phd._CURVEINFO:
            key = line[0]
            val = cinfo[key]
            print '  %s => %r' % (key, val)

        import matplotlib.pyplot as plt
        xys = phd.get_curve(i)
        xs, ys = xys[:,0], xys[:,1]
        plt.plot(xs, ys)

    plt.show()

def test_pt2(fname):
    t2 = PT2File(fname)

    print 'Header info:'
    info = t2.get_header()
    for line in t2._HEADERINFO:
        key = line[0]
        val = info[key]
        print '  %s => %r' % (key, val)

    print 'PT2/PT3 info:'
    info = t2.get_t2t3()
    for line in t2._T2T3INFO:
        key = line[0]
        val = info[key]
        print '  %s => %r' % (key, val)

    data = t2.get_data()
    print 'Data size: %s, type: %s' % (data.size, data.dtype)

    data = t2.get_ch_data(0, progress=1000)
    print 'Channel data: %s, type: %s' % (data.size, data.size)

    avgdt = data[-1] / data.size
    print 'Average dt: %.03f us' % (avgdt * 1e6, )

    import matplotlib.pyplot as plt

    print 'Time-trace construction...'
    binsize = 5e-3
    plt.figure()
    n, bins, patches = plt.hist(data, bins=(120/binsize), range=(0,120), histtype='step')
    plt.xlabel('Time (s)')
    plt.ylabel('Counts / %.03f ms bin' % (binsize*1e3))
    plt.savefig('timebins.pdf')

    print 'Start-stop construction'
    NDELTAS = 10
    print 'NDELTAS = %s --> ok to %.03f us' % (NDELTAS, NDELTAS*avgdt*1e6)
    deltas = np.array([])
    for i in range(1, NDELTAS):
        newdeltas = data[i:]-data[:-i]
        deltas = np.concatenate((deltas, newdeltas), axis=0)

    plt.figure()
    binsize = 0.05      # us
    n, bins, patches = plt.hist(deltas*1e6, bins=10/binsize, range=(0,10), histtype='step')
    plt.xlabel('dt (us)')
    plt.ylabel('Events / %.03f us (start - %d stops)' % (binsize, NDELTAS))
    plt.savefig('dtbins.pdf')

if __name__ == '__main__':
    import os

    if len(sys.argv) == 2:
        fname = sys.argv[1]
    else:
        fname = 'test.phd'

    if os.path.splitext(fname)[1] == '.phd':
        test_phd(fname)
    else:
        test_pt2(fname)

