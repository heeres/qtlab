#!/usr/bin/python
# File name: save_and_plot_data.py
#
# This example should be run with "execfile('save_and_plot_data.py')"

from numpy import *
from time import time,sleep
import qt

# this part is to simulate some data
def lorentzian(x, center, width):
    return 1/pi*(0.5*width)/((x-center)**2+(0.5*width)**2)

def addnoise(x, variance):
    return x+variance*random.randn(size(x))

x = arange(0,10,0.01)
y = arange(-5,5,0.1)

def z(x,y):
    return addnoise(lorentzian(x,y*y/5+1,0.1),0.1)[0]

# here is where the actual measurement programm starts

# you indicate that a measurement is about to 
# start and other processes should stop
qt.flow.measurement_start()

# a new data object is made, and the file will be called 
# <timestamp>_testmeasurement.dat
data = qt.Data(name='testmeasurement')

# Adding coordinate and values info is optional, but recommended.
# If you don't supply it, the data class will guess your data format.
data.add_coordinate('dmm1.value')
#data.add_coordinate('dmm1.value', instrument=dmm1, parameter='value')
data.add_coordinate('dmm1.input3')
data.add_value('dmm1.speed')

data.add_comment('some comment here')
data.add_comment('some more comment here')
data.create_file()

# you create two plot-objects. If the 'name' already exists, then
# that window will be used in stead of opening a new one.
plot2d = qt.Plot2D(data, name='measure2D')
plot3d = qt.Plot3D(data, name='measure3D', style='image3d')

tic = time()

for j in arange(0,size(y)-1):
    tic2 = time()
    for i in arange(0,size(x)-1):
        data.add_data_point(x[i],y[j],z(x[i],y[j]))
        qt.sleep(0.01)
    data.new_block()
    toc2 = time()
    print toc2 - tic2

toc = time()

print toc - tic

data.close_file()
qt.flow.measurement_end()
