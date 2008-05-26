#!/usr/bin/python

from ADwin import *
#from sys import exit, platform
import sys

DEVICENUMBER = 1

if platform == 'win32':
    BTL = 'c:\\adwin\\adwin9.btl'
else:
    BTL = 'adwin9.btl'
    
PROCESS = 'C:\\ADwin\\ADbasic\\samples_ADwin\\Bas_dmo1.T91'

def checkError(s):
    err = Get_Last_Error()
    if err:
        print "*** " + s + ": " + Get_Last_Error_Text(err)
        return err
    return 0


Set_DeviceNo(DEVICENUMBER)

# Boot, load and start
Boot(BTL)
if (checkError('Boot') > 0): exit()
p = Processor_Type()
if p > 1000: p -= 1000
print 'Processor: T%d' %p

Load_Process(PROCESS)
if (checkError('Load_Process') > 0): exit()

Start_Process(1)
print ((Process_Status(1) == 1) and 'Process_Status: running') or 'Process_Status: not running'

# Parameter - remember inc(par_1) in proc1.bas
for i in range(1, 81):
    Set_Par(i, i)
print 'Get_Par_All: ',
print Get_Par_All() 
print 'Par_1: ',
for i in range(10):
    print Get_Par(1),
print

# Data-Access
SetData_Long(1, range(1, 11), 1, 10)
intData = GetData_Long(1, 1, 10)
if (checkError('GetData_Long') > 0): exit()
print 'GetData_Long: ',
print intData

SetData_String(3, 'Hello World!1234567890')
print 'GetData_String: %s' %GetData_String(3, 11)

# Fifo-Access
empty = Fifo_Empty(2)
print 'Fifo empty: %d' %empty,
SetFifo_Long(2, range(1, empty+1), empty)
empty = Fifo_Empty(2)
for i in range(3):
    print empty,
    arr = GetFifo_Long(2, 100)
    empty = Fifo_Empty(2)
print empty
print 'Fifo: ',
print arr[0:10]

