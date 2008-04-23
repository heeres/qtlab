#!/usr/bin/python
# File name: save_data_2d.py
# this example should be run with "qtrun('save_data_2d.py')"

from numpy import *
from time import time,sleep

def lorentzian(x, center, width):
    return 1/pi*(0.5*width)/((x-center)**2+(0.5*width)**2)

def addnoise(x, variance):
    return x+variance*random.randn(size(x))

x = arange(0,10,0.01)
y = arange(-5,5,0.1)

def z(x,y):
    return addnoise(lorentzian(x,y*y/5+1,0.1),0.1)[0]

plot2d.clear()
plot2d.reset_cols((1,3))
plot2d.add_trace((1,2))
plot2d.set_auto_update()
plot2d.set_maxpoints(200)

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

