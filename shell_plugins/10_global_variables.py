import qt

from instruments import get_instruments
qt.instruments = get_instruments()

from config import get_config
qt.config = get_config()

from data import Data
data = Data()

import qtgnuplot
plot2d = qtgnuplot.Plot2D(data)
plot3d = qtgnuplot.Plot3D(data)

from misc import *
