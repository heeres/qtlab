# Global namespace

import os
import sys
from qtflow import get_flowcontrol
from instruments import get_instruments
from lib import config as _config
from data import Data
from plot import Plot, plot, plot3, replot_all
from lib.gui.qtwindow import QTWindow
from scripts import Scripts, Script

config = _config.get_config()

data = Data.get_named_list()
instruments = get_instruments()
windows = QTWindow.get_named_list()
frontpanels = {}
sliders = {}
scripts = Scripts()

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
    version_file = os.path.join(config['execdir'], 'VERSION')
    try:
        f = file(version_file,'r')
        str = f.readline()
        str = str.rstrip('\n\r')
        f.close()
    except:
        str = 'NO VERSION FILE'
    return str

class qApp:
    '''Class to fix a bug in matplotlib.pyplot back-end detection.'''
    @staticmethod
    def startingUp():
        return True

