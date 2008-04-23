from instruments import Instruments, get_instruments
instruments = get_instruments()

from config import QTConfig, get_config
config = get_config()

from data import Data
data = Data()

import qtgnuplot
plot2d = qtgnuplot.Plot2D(data)
plot3d = qtgnuplot.Plot3D(data)

