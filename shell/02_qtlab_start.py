import types
from instrument import Instrument
from lib.gui.qtwindow import QTWindow
from lib.calltimer import qttime
from lib.gui import pack_hbox, pack_vbox

try:
    import psyco
    psyco.full()
    logging.info('psyco acceleration enabled')
except:
    logging.info('psyco acceleration not enabled')
        
import qt
from plot import plot
Plot2D = qt.Plot2D
Plot3D = qt.Plot3D

# Set exception handler
try:
    import qtflow
    __IP.set_custom_exc((KeyboardInterrupt,), qtflow.exception_handler)
except Exception, e:
    print 'Error: %s' % str(e)

