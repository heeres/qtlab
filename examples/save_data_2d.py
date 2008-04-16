#!/usr/bin/python
# File name: save_data.py

from numpy import *
from time import time,sleep
from data import Data
from qtgnuplot import Plot2D
from qtgnuplot import Plot3D

def lorentzian(x, center, width):
    return 1/pi*(0.5*width)/((x-center)**2+(0.5*width)**2)

def addnoise(x, variance):
    return x+variance*random.randn(size(x))

x = arange(0,10,0.01)
y = arange(-5,5,0.1)

def z(x,y):
    return addnoise(lorentzian(x,y*y/5+1,0.1),0.1)[0]


data = Data()

plot1 = Plot2D(data,cols=(1,3))
plot1.add_trace((1,2))
plot1.set_auto_update()
plot1.set_maxpoints(200)

#plot2 = Plot3D(data,cols=(1,2,3))
#plot2.set_auto_update_block()


data.create_datafile('data','./data')
data.add_column_to_header('dmm1','value')
data.add_column_to_header('dmm1','input3')
data.add_column_to_header('dmm1','speed')
data.add_comment_to_header('some comment here')


tic = time()

for j in arange(0,size(y)-1):
    tic2 = time()
    for i in arange(0,size(x)-1):
        data.add_data_point(x[i],y[j],z(x[i],y[j]))
        sleep(0.05)

        gui.update_gui()
        gui.check_abort()

    data.new_data_block()
    toc2 = time()
    print toc2 - tic2

toc = time()

print toc - tic

data.close_datafile()

raw_input('press return to exit')

