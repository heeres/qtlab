import qt
from instruments import get_instruments
qt.instruments = get_instruments()

from config import get_config
qt.config = get_config()

from data import Data
import datalist
qt.data = datalist.DataList()

from misc import *

if qt.config.get('plot_type', 'gnuplot') == 'matplotlib':
    from qtmatplotlib import Plot2D, Plot3D
else:
    from qtgnuplot import Plot2D, Plot3D

