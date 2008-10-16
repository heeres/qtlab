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
import datalist
qt.data = datalist.DataList()

if qt.config.get('plot_type', 'gnuplot') == 'matplotlib':
    from qtmatplotlib import Plot2D, Plot3D
else:
    from qtgnuplot import Plot2D, Plot3D

qt.Plot2D = Plot2D
qt.Plot3D = Plot3D
