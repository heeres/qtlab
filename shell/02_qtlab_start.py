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

import qtflow
qt.flow = qtflow.get_flowcontrol()

import instruments
qt.instruments = instruments.get_instruments()

import config
qt.config = config.get_config()
qt.config['qtlabdir'] = config.get_workdir()

from data import Data
qt.data = Data.get_named_list()
qt.Data = Data

from lib.gui import qtwindow
qt.windows = qtwindow.QTWindow.get_named_list()

if qt.config.get('plot_type', 'gnuplot') == 'matplotlib':
    from plot_engines.qtmatplotlib import Plot2D, Plot3D
else:
    from plot_engines.qtgnuplot import Plot2D, Plot3D

import plot
qt.Plot2D = Plot2D
qt.plots = plot.Plot.get_named_list()
qt.Plot3D = Plot3D
from plot import plot

# Set exception handler
try:
    import qtflow
    __IP.set_custom_exc((KeyboardInterrupt,), qtflow.exception_handler)
except Exception, e:
    print 'Error: %s' % str(e)

