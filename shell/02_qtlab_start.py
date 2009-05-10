import types
from instrument import Instrument
from lib.gui.qtwindow import QTWindow
from lib.misc import exact_time
from lib import temp

if False:
    import psyco
    psyco.full()
    logging.info('psyco acceleration enabled')
else:
    logging.info('psyco acceleration not enabled')

import qt
from qt import plot, plot3, Plot2D, Plot3D, Data
qt._IP = __IP

import numpy
from numpy import linspace, arange, array, pi

temp.File.set_temp_dir(qt.config['tempdir'])

# Set exception handler
try:
    import qtflow
    # Note: This does not seem to work for 'KeyboardInterrupt',
    # likely it is already caught by ipython itself.
    __IP.set_custom_exc((Exception, ), qtflow.exception_handler)
except Exception, e:
    print 'Error: %s' % str(e)
