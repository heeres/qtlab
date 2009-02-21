# Global namespace

import os
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
msleep = flow.measurement_idle
mstart = flow.measurement_start
mend = flow.measurement_end

if config.get('plot_type', 'gnuplot') == 'matplotlib':
    from plot_engines.qtmatplotlib import Plot2D, Plot3D
else:
    from plot_engines.qtgnuplot import Plot2D, Plot3D

plots = Plot.get_named_list()

def version():
    version_file = os.path.join(config['qtlabdir'], 'VERSION')
    try:
        f = file(version_file,'r')
        str = f.readline()
        str = str.rstrip('\n\r')
        f.close()
    except:
        str = 'NO VERSION FILE'

    return str


