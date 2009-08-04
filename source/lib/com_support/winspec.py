# winspec.py, COM wrapper for use with Roper Scientific's Winspec
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

from comtypes.client import CreateObject, Constants
import numpy as np
import time

_exp = None
_app = None
_const = None

def _initialize():
    '''
    Create objects. Associated constants will be available in the _const
    object. Note that it's not possible to request the contents of that;
    one has to look in the Python file generated with gen_py.
    '''
    global _exp, _app, _const
    _exp = CreateObject('WinX32.ExpSetup.2')
    _app = CreateObject('WinX32.Winx32App.2')
    _const = Constants(_exp)

def _get_wavelen(coord, coeffs):
    val = 0
    for power, coef in enumerate(coeffs):
        val += coef * (coord + 1) ** power
    return val

# Default maximum number of sleeps for 250sec
MAX_SLEEPS = 5000

def get_spectrum(wlen=True, wlenpoly=True):
    '''
    Get a spectrum using winspec.

    If wlen is True it returns a 2D numpy array with wavelength and counts
    as the columns. If wlen is False it returns a 1D array with counts.
    If wlenpoly is True the polynomial approximation for determining the
    wavelength will be used, which is quite a bit faster than querying winspec
    for the individual pixels. It can be off by ~0.3nm.
    '''

    doc = CreateObject('WinX32.DocFile.3')
    _exp.Start(doc)
    i = 0
    while i < MAX_SLEEPS:
        status = _exp.SGetParam(_const.EXP_RUNNING)[1]
        if status == 0:
            break
        i += 1
        time.sleep(0.05)

    if i == MAX_SLEEPS:
        print 'Warning: maximum delay exceeded'
        return None

    xdim = doc.SGetParam(_const.DM_XDIM)[1]
    ydim = doc.SGetParam(_const.DM_YDIM)[1]
    if ydim != 1:
        raise ValueError('Can only get 1D spectra')

    spectrum = np.array(doc.GetFrame(1))
    spectrum.flatten()
    if wlen:
        calib = doc.GetCalibration()
        if wlenpoly:
            order = calib.Order
            coeffs = [calib.PolyCoeffs(i) for i in range(order + 1)]
            wlens = [_get_wavelen(i, coeffs) for i in range(xdim)]
        else:
            wlens = [calib.Lambda(i + 1) for i in range(xdim)]
        spectrum = zip(wlens, spectrum)

    return np.array(spectrum)

_initialize()

