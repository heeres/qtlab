#!/usr/bin/python
# File name: save_data_2d.py
# this example should be run with "qtrun('save_data_2d.py')"

from numpy import *
from time import time,sleep
import qt

def lorentzian(x, center, width):
    return 1/pi*(0.5*width)/((x-center)**2+(0.5*width)**2)

def addnoise(x, variance):
    return x+variance*random.randn(size(x))

x = arange(0,10,0.01)
y = arange(-5,5,0.1)

def z(x,y):
    return addnoise(lorentzian(x,y*y/5+1,0.1),0.1)[0]

data = qt.data.get('testmeasurement')
data.add_coordinate('dmm1.value', instrument=dmm1, parameter='value')
data.add_coordinate('dmm1.input3')
data.add_value('dmm1.speed')
data.add_comment('some comment here')
data.add_comment('some more comment here')
data.create_file()

plot2d = Plot2D(data=data, name='measure2D')
plot2d.clear()
#plot2d.set_maxpoints(200)
plot3d = Plot3D(data=data, name='measure3D', style=Plot3D.STYLE_IMAGE)
plot3d.clear()

tic = time()

for j in arange(0,size(y)-1):
    tic2 = time()
    for i in arange(0,size(x)-1):
        data.add_data_point(x[i],y[j],z(x[i],y[j]))
        sleep(0.01)

        gui.update_gui()
        gui.check_abort()

    data.new_block()
    toc2 = time()
    print toc2 - tic2

toc = time()

print toc - tic

data.close_file()

raw_input('press return to exit')

