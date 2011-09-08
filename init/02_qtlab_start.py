import types
from instrument import Instrument
from lib.misc import exact_time
from lib import temp
from time import sleep

#set_debug(True)
from lib.network.object_sharer import start_glibtcp_server, SharedObject, \
        PythonInterpreter
start_glibtcp_server()
SharedObject.server.add_allowed_ip('130.161.*.*')
SharedObject.server.add_allowed_ip('145.94.*.*')
PythonInterpreter('python_server', globals())

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
import numpy as np
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
