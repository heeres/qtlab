# Agilent_8753E2.py class, to perform the communication between the Wrapper and the device
# Pablo Asshoff <techie@gmx.de>, 2013
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from instrument import Instrument
import visa
import types
import logging
import numpy
import math

class Agilent_8753E2(Instrument):
    '''
    This is the driver for the Agilent 8753E2 Network Analyzer

    Usage:
    Initialize with
    <name> = instruments.create('name', 'Agilent_8753E2', address='<GPIB address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Agilent_8753E2, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false

        Output:
            None
        '''
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.timeout = 1

        # Add parameters
        self.add_parameter('startfrequency', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=9e3, maxval=6e9,
            units='Hz', format='%.04e')
        self.add_parameter('stopfrequency', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=9e3, maxval=6e9,
            units='Hz', format='%.04e')
        self.add_parameter('span', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=3e9, 
            units='Hz', format='%.04e')

        # Add functions
        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('read_trace')
#        self.add_function('plot_trace')        
#        self.add_function('save_trace')

        if reset:
            self.reset()
        else:
            self.get_all()

    # Functions
    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST;*CLS')    # zuvor nur *RST
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : reading all settings from instrument')
        self.get_startfrequency()
        self.get_stopfrequency()
        self.get_span()

    def read_trace(self):
        '''
        Read a trace
        p.427 Manual

        Input:
            None

        Output:
            trace
        '''
        logging.debug(__name__ + ' : performing trace readout')
        #self._visainstrument.write('OPC?;SING;')   
        #only use previous command if single sweep is required, not for readout of display as is.
        self._visainstrument.write('FORM4;')
        return(self._visainstrument.ask('OUTPFORM;'))

#    def plot_trace(self,trace):
#        '''
#        plot the trace returned from read_trace()
#        p.427 Manual
#
#        Input:
#            Trace
#
#        Output:
#            trace
#        '''
#        array1 = trace
#        array2 = array1.replace('E','e')
#        array2 = array2.replace('\n',',')
#        array3 = numpy.fromstring(array2, sep=',')
#        y = array3[::2]
#        startfreq = self.get_startfrequency()
#        stopfreq = self.get_stopfrequency()
#        steps = (stopfreq-startfreq)/(len(y)-1)
#        x = arange(startfreq,stopfreq+0.001,steps)
#        qt.Plot2D(x,y)
#
#    def save_trace(self,trace,filename):
#        '''
#        plot the trace returned from read_trace()
#        p.427 Manual
#
#        Input:
#            Trace
#
#        Output:
#            trace
#        '''
#        #convert data returned from instrument:
#        array1 = trace
#        array2 = array1.replace('E','e')
#        array2 = array2.replace('\n',',')
#        array3 = numpy.fromstring(array2, sep=',')
#        y = array3[::2]
#        startfreq = self.get_startfrequency()
#        stopfreq = self.get_stopfrequency()
#        steps = (stopfreq-startfreq)/(len(y)-1)
#        x = arange(startfreq,stopfreq+0.001,steps)
#        qt.Plot2D(x,y)
#        #create a file and save trace:        
#        f = open(filename, 'w')
#        f.write('frequency[Hz] power[dB]')
#        for i in range(len(x)):
#            f.write(str(x[i]))
#            f.write(' ')
#            f.write(str(y[i]))
#            f.write('\n')
#        f.close()

    # communication with machine
    def do_get_startfrequency(self):
        '''
        Get start frequency from device

        Input:
            None

        Output:
            startfrequency (float) : start frequency in Hz
        '''
        logging.debug(__name__ + ' : reading start frequency from instrument')
        return float(self._visainstrument.ask('STAR?;'))

    def do_set_startfrequency(self, startfrequency):
        '''
        Set start frequency of device

        Input:
            startfrequency (float) : start frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting start frequency to %s GHz' % startfrequency)
        self._visainstrument.write('STAR; %e' % startfrequency)
        #self._visainstrument.write('STAR; %e MHZ;' % startfrequency)

    def do_get_stopfrequency(self):
        '''
        Get stop frequency from device

        Input:
            None

        Output:
            stopfrequency (float) : stop frequency in Hz
        '''
        logging.debug(__name__ + ' : reading stop frequency from instrument')
        return float(self._visainstrument.ask('STOP?;'))

    def do_set_stopfrequency(self, stopfrequency):
        '''
        Set stop frequency of device

        Input:
            stopfrequency (float) : stop frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting stop frequency to %s GHz' % stopfrequency)
        self._visainstrument.write('STOP; %e' % stopfrequency)
        #self._visainstrument.write('STAR; %e MHZ;' % startfrequency)

    def do_get_span(self):
        '''
        Get span from device

        Input:
            None

        Output:
            span (float) : span in Hz
        '''
        logging.debug(__name__ + ' : reading span from instrument')
        return float(self._visainstrument.ask('SPAN?;'))

    def do_set_span(self,span):
        '''
        Set span of device

        Input:
            span (float) : span in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting span to %s Hz' % span)
        self._visainstrument.write('SPAN; %e' % span)

