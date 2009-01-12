import qt

import qtflow
qt.flow = qtflow.get_flowcontrol()

import instruments
qt.instruments = instruments.get_instruments()

import config
qt.config = config.get_config()
qt.config['qtlabdir'] = config.get_workdir()
sys.path.append(qt.config['qtlabdir'])

from data import Data
qt.data = Data.get_named_list()

if qt.config.get('plot_type', 'gnuplot') == 'matplotlib':
    from qtmatplotlib import Plot2D, Plot3D
else:
    from qtgnuplot import Plot2D, Plot3D

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

