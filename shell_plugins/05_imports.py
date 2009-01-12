import types
from instrument import Instrument
from packages.qtwindow import QTWindow

from packages.calltimer import qttime

from gui import pack_hbox, pack_vbox

try:
    import psyco
    psyco.full()
    logging.info('psyco acceleration enabled')
except:
    logging.info('psyco acceleration not enabled')
