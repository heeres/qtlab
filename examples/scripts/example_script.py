# Example script for QTLab
#
# Arguments can be passed in the args and kwargs variables.
# args is a list of parameters in the order they are given,
# kwargs a dictionary of keyword arguments.
#
# This example script takes 2 fixed parameters and shows how to use
# keyword arguments.

arg1, arg2 = args
print 'Arg1: %s, arg2: %s' % (arg1, arg2)

for key, val in kwargs.iteritems():
    print 'Keyword arg: %s = %s' % (key, val)

# A script can return a value by calling set_return
set_return('Return value')

