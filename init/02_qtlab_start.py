import types
from instrument import Instrument
from lib.gui.qtwindow import QTWindow
from lib.misc import exact_time
from lib import temp
from time import sleep

if False:
    import psyco
    psyco.full()
    logging.info('psyco acceleration enabled')
else:
    logging.info('psyco acceleration not enabled')

import qt
from qt import plot, plot3, Plot2D, Plot3D, Data
qt._IP = __IP

from numpy import *
try:
    from scipy import constants as const
except:
    pass

temp.File.set_temp_dir(qt.config['tempdir'])

# change startdir if commandline option is given
if __startdir__ is not None:
    qt.config['startdir'] = __startdir__
# FIXME: use of __startdir__ is spread over multiple scripts:
# 1) source/qtlab_client_shell.py
# 2) init/02_qtlab_start.py
# This should be solved differently

# Set exception handler
try:
    import qtflow
    # Note: This does not seem to work for 'KeyboardInterrupt',
    # likely it is already caught by ipython itself.
    __IP.set_custom_exc((Exception, ), qtflow.exception_handler)
except Exception, e:
    print 'Error: %s' % str(e)
