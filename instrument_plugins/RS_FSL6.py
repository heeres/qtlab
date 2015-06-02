# RS_FSL6.py class, to perform the communication between the Wrapper and the device
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

class RS_FSL6(Instrument):
    '''
    This is the driver for the Rohde & Schwarz FSL6 Spectrum Analyser

    Usage:
    Initialize with
    <name> = instruments.create('name', 'RS_FSL6', address='<GPIB address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the RS_FSL6, and communicates with the wrapper.

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
        self.add_parameter('centerfrequency', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=9e3, maxval=6e9,
            units='Hz', format='%.04e')
        self.add_parameter('span', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=3e9, 
            units='Hz', format='%.04e')
        self.add_parameter('referencelevel', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-80, maxval=30,
            units='dBm', format='%.04e')
        self.add_parameter('sweeptime', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=1e-6, maxval=60,
            units='s', format='%.04e')
        self.add_parameter('channelpower', type=types.FloatType,
            flags=Instrument.FLAG_GET, 
            units='W', format='%.10e')
        self.add_parameter('timetracemarkerpower', type=types.FloatType,
            flags=Instrument.FLAG_GET, 
            units='W', format='%.10e')
        self.add_parameter('IQresult', type=types.StringType,
            flags=Instrument.FLAG_GET, 
            units='')
        self.add_parameter('tracedata', type=types.StringType,
            flags=Instrument.FLAG_GET, 
            units='')
        self.add_parameter('display_onoff',
            flags=Instrument.FLAG_SET,
            type=types.StringType, units='')
        self.add_parameter('triggerlevel', type=types.FloatType,
            flags=Instrument.FLAG_SET,
            minval=0.5, maxval=3.5,
            units='V', format='%.04e')


        # Add functions
        self.add_function('reset')
        self.add_function('get_all')

        self.add_function('init_power_measurement')
        self.add_function('init_IQ_measurement')
        self.add_function('init_zero_span')
        self.add_function('init_trace_readout')
        self.add_function('start_sweep')
        self.add_function('stop_power_measurement')
        self.add_function('convert_dBuV_to_V')  # works but apparently not needed, device returns usually V by default
#        self.add_function('stop_remote_control')
#        self.add_function('trigger_mode')
#        self.add_function('enable_trigger')


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
        self.get_centerfrequency()
        self.get_span()
        self.get_referencelevel()
        self.get_sweeptime()
        self.get_channelpower()

    def do_set_display_onoff(self, type):
        '''
        Set the display on or off

        Input:
            type (string) : 'on' or 'off'

        Output:
            None
        '''

        logging.debug('set display to %s', type)
        if type is 'on':
            self._visainstrument.write('SYST:DISP:UPD ON') 
        elif type is 'off':
            self._visainstrument.write('SYST:DISP:UPD OFF') 
        else:
            logging.error('invalid type %s' % type)







    def init_IQ_measurement(self):
        '''
        Initializes an I/Q measurement

        Input:
            None

        Output:
            None
       '''
        logging.debug(__name__ + ' : initialization of I/Q (quadrature) measurement')
        
        #setting the trigger level to 0.5 V (bounds: 0.5 V to 3.5 V, p.1590 of operating manual, RST value 1.4 V)
        self._visainstrument.write('TRIG:LEV 0.5 V')
        #self._visainstrument.write('BAND:RES 20MHz')     #resultion bandwidth. 20 MHz, only for test
        self._visainstrument.write('FREQ:SPAN 0Hz')        
        self._visainstrument.write('TRAC:IQ:STAT ON')       
        #enables acquisition of I/Q data, trace display on device not possible in this operation mode
        self._visainstrument.write('TRAC:IQ:SET NORM,20MHz,64MHz,EXT,POS,0,640')     
        #self._visainstrument.write('TRAC:IQ:SET NORM,100kHz,32MHz,EXT,POS,0,512') 
        #sample measurement configuration
        #filter: NORM, RBW: 10MHz, sample rate: 32 MHz, trigger source: external (EXT) / internal (IMM), trigger slope: positive, 
        #pretrigger samples: 0, numer of samples: 512
        self._visainstrument.write('FORMat ASC')        #selects format of response data (either REAL,32 or ASC for ASCII)
        self._visainstrument.write('FREQ:CONT OFF')
        #return self._visainstrument.write('TRAC:IQ:DATA?')         #starts measurements and reads results
        #self._visainstrument.write('INIT;*WAI')             #apparently not necessary
        #self._visainstrument.write('TRAC:IQ OFF')        #close I/Q operation mode

    def init_power_measurement(self):
        '''
        Initializes a channel power measurement

        Input:
            None

        Output:
            None

        maybe add sweeptime parameter etc. later and measure both sidebands for better statistics
        '''
        logging.debug(__name__ + ' : initialization of channel power measurement')
        self._visainstrument.write('POW:ACH:ACP 0')      
        self._visainstrument.write('POW:ACH:BAND 5KHZ')       
        #self._visainstrument.write('POW:ACH:BAND:ACH 40KHZ')          
        #self._visainstrument.write('POW:ACH:BAND:ALT1 50KHZ')      
        #self._visainstrument.write('POW:ACH:BAND:ALT2 60KHZ')       
        #self._visainstrument.write('POW:ACH:SPAC 30KHZ') 
        #self._visainstrument.write('POW:ACH:SPAC:ALT1 100KHZ')      
        #self._visainstrument.write('POW:ACH:SPAC:ALT2 140KHZ')        
        self._visainstrument.write('POW:ACH:MODE ABS')      # Switches on absolute power measurement.     
        self._visainstrument.write('INIT:CONT ON')    	# Switches over to single sweep mode (for OFF!!).     
        self._visainstrument.write('INIT;*WAI')    		# Starts a sweep and waits for the end of the sweep.

    def stop_power_measurement(self):
        '''
        Initializes a channel power measurement

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : stop channel power measurement') 
        self._visainstrument.write('INIT:CONT ON')    	# Switches over to continuous sweep mode.   

    def init_zero_span(self,resbw,vidbw):
        '''
        Initializes a zero span measurement

        Input:
            resolution bandwidth, video bandwidth

        Output:
            None
       '''
        logging.debug(__name__ + ' : initialization of zero span measurement')
        self._visainstrument.write('FREQ:SPAN 0Hz')   
        self._visainstrument.write('BAND:RES %s' % resbw)     #resolution bandwidth, suggested: 100kHz
        self._visainstrument.write('BAND:VID %s' % vidbw)     #video bandwidth, suggested: 100kHz       
        #sweep time --> set from measurement script
        #self._visainstrument.write('CALC:MARK:FUNC:SUMM:PPE ON ')  # not required if time trace is evaluate in control computer
        self._visainstrument.write('INIT;*WAI')           # starts a sweep and waits for the end of the sweep.

    def start_sweep(self):
        logging.debug(__name__ + ' : start a sweep and wait till finished')
        self._visainstrument.write('INIT')
        #self._visainstrument.write('*WAI')


    def init_trace_readout(self):
        '''
        Read a trace
        p. 230 operating manual

        Input:
            mode, either ASCII or binary

        Output:
            None
        '''
        logging.debug(__name__ + ' : initialization of trace readout')
        self._visainstrument.write('FORM ASC')
        #if mode == 'ASCII':
        #    self._visainstrument.write('FORM ASC')         
        #elif mode == 'binary':
        #    self._visainstrument.write('FORM REAL,32')      
        #else: 
        #    print 'Not a valid mode, function requires mode as argument, parameter either ASC for ASCII file or binary for binary file'
        #    # ASCII file format, alternative: FORMat REAL,32 (binary file) / FORM ASC for ASCII
        ##self._visainstrument.write('MMEM:STOR:TRAC 1,'TEMPTRACE.DAT'')   
        #    #the previous command just creates a file locally on the analyer
        ##self._visainstrument.write('TRAC? TRACE1')
      

    def convert_dBuV_to_V(self,dBuV):
        '''
        converts dBuV to Volt

        Input:
            Voltage in dBuV

        Output:
            Voltage in Volt
        '''
        logging.debug(__name__ + ' : convert dBuV to Volt') 
        UinV = 10**(dBuV/20)/1E6    # formula from http://www.kathrein.de/include/pegelumrechnung.cfm
        return UinV


    def convert_dBm_to_W(self,dBm):
        '''
        converts dBm to Watt

        Input:
            power in dBm

        Output:
            power in Watt
        '''
        logging.debug(__name__ + ' : convert dBm to Watt') 
        PinW = 10**(dBm/10)/1E3    # formula from http://www.kathrein.de/include/pegelumrechnung.cfm
        return PinW



#    def stop_remote_control(self):
#        '''
#        Initializes a channel power measurement
#
#        Input:
#            None
#
#        Output:
#            None
#        '''
#        logging.debug(__name__ + ' : set to local control') 
#        self._visainstrument.write('INIT:CONT OFF')    	#GPIB  COMMAND  ??????



    # communication with machine
    def do_get_centerfrequency(self):
        '''
        Get center frequency from device

        Input:
            None

        Output:
            centerfrequency (float) : center frequency in Hz
        '''
        logging.debug(__name__ + ' : reading center frequency from instrument')
        return float(self._visainstrument.ask('FREQ:CENT?'))




    def do_set_centerfrequency(self, centerfrequency):
        '''
        Set center frequency of device

        Input:
            centerfrequency (float) : center frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting center frequency to %s Hz' % centerfrequency)
        self._visainstrument.write('FREQ:CENT %e' % centerfrequency)




    def do_set_triggerlevel(self, triggerlevel):
        '''
        Set trigger level for TTL input

        Input:
            trigger level (float) : center frequency in V

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting trigger level to %s V' % triggerlevel)
        self._visainstrument.write('TRIG:LEV %e V' % triggerlevel)        


    def do_get_span(self):
        '''
        Get span from device

        Input:
            None

        Output:
            span (float) : span in Hz
        '''
        logging.debug(__name__ + ' : reading span from instrument')
        return float(self._visainstrument.ask('FREQ:SPAN?'))

    def do_set_span(self,span):
        '''
        Set span of device

        Input:
            span (float) : span in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting span to %s Hz' % span)
        self._visainstrument.write('FREQ:SPAN %e' % span)

    def do_get_referencelevel(self):
        '''
        Get reference level from device

        Input:
            None

        Output:
            referencelevel (float) : reference level in dBm
        '''
        logging.debug(__name__ + ' : reading referencelevel from instrument')
        return float(self._visainstrument.ask('DISP:TRAC:Y:RLEV?'))

    def do_set_referencelevel(self,referencelevel):
        '''
        Set referencelevel of device

        Input:
            referencelevel (float) : reference level in dBm(??)

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting referencelevel to %s dBm' % referencelevel)
        self._visainstrument.write('DISP:TRAC:Y:RLEV %e' % referencelevel)

    def do_get_sweeptime(self):
        '''
        Get sweeptime level from device

        Input:
            None

        Output:
            sweeptime (float) : sweep time in s
        '''
        logging.debug(__name__ + ' : reading sweeptime from instrument')
        return float(self._visainstrument.ask('SWE:TIME?'))

    def do_set_sweeptime(self,sweeptime):
        '''
        Set sweeptime of device

        Input:
            sweeptime (float) : sweep time in s

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting sweeptime to %s s' % sweeptime)
        self._visainstrument.write('SWE:TIME %e' % sweeptime)

    def do_get_IQresult(self):
        '''
        Get IQresult level from device in I/Q mode

        Input:
            None

        Output:
            IQresult (string) : either REAL,32 or ASCII, depending on choice in init_IQ_measurement
        '''
        logging.debug(__name__ + ' : reading result of I/Q measurement from instrument')
        #self._visainstrument.write('INIT,*WAI')        
        #self._visainstrument.write('*CLS')
        self._visainstrument.write('INIT') 
        return self._visainstrument.ask('TRAC:IQ:DATA?')
        #self._visainstrument.write('INIT,*WAI')        
        #return self._visainstrument.ask('TRAC:IQ:DATA:MEM? 0,4096')



    def do_get_tracedata(self):
        '''
        read out trace data from device

        Input:
            None

        Output:
            tracedata (string) : either REAL,32 or ASCII, depending on choice 
        '''
        logging.debug(__name__ + ' : reading result of I/Q measurement from instrument')
        self._visainstrument.write('INIT,*WAI')
        #self._visainstrument.write('FORM ASC')      # ASCII file format, alternative: FORMat REAL,32 (binary file)
        return self._visainstrument.ask('TRAC? TRACE1')


    def do_get_channelpower(self):
        '''
        Get channel power from device (in MEAS. menu on front panel of the RS-FSL6, 
        command CP/ACP/MC-ACP)
        
        In measurement, call self.init_power_measurement() before reading channelpower!

	    Documentation for remote control command in 'Operating manual', p. 821

        Input:
            None

        Output:
            channelpower (float) : channel power in ??unit
        '''
        logging.debug(__name__ + ' : reading channelpower from instrument')
        self._visainstrument.write('*WAI')    		# Starts a sweep and waits for the end of the sweep.
        return float(self._visainstrument.ask('CALC:MARK:FUNC:POW:RES? ACP'))



    def do_get_timetracemarkerpower(self):
        '''
        Get marker power from device in zero span mode
        
        In measurement, call init_zero_span() before reading mean power!

	    Documentation for remote control command in 'Operating manual', p. 1609

        Input:
            None

        Output:
            timetracemarkerpower (float) : marker power in V!! (even if display shows dBuV)
        '''
        logging.debug(__name__ + ' : reading marker power in zero span mode from instrument')
        self._visainstrument.write('INIT;*WAI')    		# Starts a sweep and waits for the end of the sweep.
        return float(self._visainstrument.ask('CALC:MARK:FUNC:SUMM:PPE:RES?'))

