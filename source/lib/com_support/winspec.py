import win32com.client
import numpy as np
import qt

# To also generate win32com.client.constants
dispatch = win32com.client.gencache.EnsureDispatch

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
    _exp = dispatch('WinX32.ExpSetup.2')
    _app = dispatch('WinX32.Winx32App.2')
    _const = win32com.client.constants

MAX_SLEEPS = 1000

def get_spectrum(wlen=True, max_sleeps=MAX_SLEEPS):
    '''
    Get a spectrum using winspec.

    If wlen is True it returns a 2D numpy array with wavelength and counts
    as the columns. If wlen is False it returns a 1D array with counts.

    max_sleeps is the maximum number of 0.1 second sleeps that will be
    performed before the call times out, default: 1000.
    '''

    doc = dispatch('WinX32.DocFile.3')
    _exp.Start(doc)
    i = 0
    while < MAX_SLEEPS:
        status, ret = _exp.GetParam(_const.EXP_RUNNING)
        if status == 0:
            break
        i += 1
	qt.msleep(0.1)
    if i == MAX_SLEEPS:
        print 'Warning: maximum delay exceeded'
        return None

    xdim = doc.GetParam(_const.DM_XDIM)
    ydim = doc.GetParam(_const.DM_YDIM)
    if xdim[1] != 1 or ydim != (1, 1):
        raise ValueError('Can only get 1D spectra')

    spectrum = [doc.GetPixel(1, 1, i + 1) for i in range(xdim[0])]
    if wlen:
        calib = doc.GetCalibration()
        wlens = [calib.Lambda(i + 1) for i in range(xdim[0])]
        spectrum = zip(wlens, spectrum)

    return np.array(spectrum)

_initialize()

