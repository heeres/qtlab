import numpy as np
import qt

d = qt.Data()
d.add_coordinate('X')
d.add_value('Y')
d.create_file()
p = plot(d)

qt.mstart()

for x in arange(0, 40, 0.1):
    y = np.sin(x) + np.random.rand()/10
    d.add_data_point(x, y)
    qt.msleep(0.1)

qt.mend()
d.close_file()
