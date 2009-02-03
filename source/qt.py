# Global namespace

from qtflow import get_flowcontrol
from instruments import get_instruments
import config as _config
from data import Data
from plot import Plot
from lib.gui.qtwindow import QTWindow

config = _config.get_config()
config['qtlabdir'] = _config.get_workdir()
data = Data.get_named_list()
instruments = get_instruments()
windows = QTWindow.get_named_list()

flow = get_flowcontrol()
sleep = flow.measurement_idle

if config.get('plot_type', 'gnuplot') == 'matplotlib':
    from plot_engines.qtmatplotlib import Plot2D, Plot3D
else:
    from plot_engines.qtgnuplot import Plot2D, Plot3D

plots = Plot.get_named_list()
