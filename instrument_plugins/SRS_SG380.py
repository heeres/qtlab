# This Python file uses the following encoding: utf-8
# SRS_SG386.py class, to perform the communication between the Wrapper and the device
# Chunming Yin 2013
# Gabriele de Boo <ggdeboo@gmail.com> 2014
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

class SRS_SG380(Instrument):
    '''
    This is the driver for the Stanford Research Systems (SRS) SG380 range signal generators.
    There are three models:
        SG382 (DC to 2.025 GHz)
        SG384 (DC to 4.050 GHz)
        SG386 (DC to 6.075 GHz)
    The wrapper will identify the model and set the ranges accordingly.
    
    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'SRS_SG386', address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the SRS Signal Generator, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument SRS_SG386')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
	try:
	    identity = self._visainstrument.ask('*IDN?')
	    model = identity[26:31]
	except IndexError:
	    raise Warning('The instrument is not a SRS RF signal generator. %s' % model)

	if model not in ['SG382','SG384','SG386']:
	    raise Warning('The instrument is not a SRS RF signal generator.')
        logging.info('The model is %s' % model)

        options = {'1':'Rear clock outputs', '2':'RF doubler and DC outputs', '3':'IQ modulation inputs and outputs', '4':'OCXO timebase','5':'Rubidium timebase'}
	for idx in range(1,5):
	    option_installed = bool(int(self._visainstrument.ask('OPTN? %i' % idx)))
	    if option_installed:
	        logging.info('Option %s is installed' % options[str(idx)])

	minfreq_ntype = 950e3      
	if model == 'SG382':
	    maxfreq_ntype = 2.025e9
	elif model == 'SG384':
	    maxfreq_ntype = 4.050e9
	else:
	    maxfreq_ntype = 6.075e9

        self.add_parameter('ntype_power',
            flags=Instrument.FLAG_GETSET, units='dBm', minval=-110, maxval=16.5, type=types.FloatType)
	self.add_parameter('bnc_power',
            flags=Instrument.FLAG_GETSET, units='dBm', minval=-110, maxval=16.5, type=types.FloatType)
	self.add_parameter('bnc_output_status',
            flags=Instrument.FLAG_GETSET, type=types.BooleanType)

        self.add_parameter('frequency',
            flags=Instrument.FLAG_GETSET, units='Hz', minval=0.95e6, maxval=maxfreq_ntype, type=types.FloatType)
        self.add_parameter('status',
            flags=Instrument.FLAG_GETSET, type=types.StringType)
        self.add_parameter('Frequency_Modulation_Rate',
            flags=Instrument.FLAG_GETSET, units='Hz', minval=1e-6, maxval=50e3, type=types.FloatType)
        self.add_parameter('Frequency_Modulation_Size',
            flags=Instrument.FLAG_GETSET, units='Hz', minval=0.1, maxval=32e6, type=types.FloatType)
        self.add_parameter('modulation_coupling', 
            flags=Instrument.FLAG_GETSET, type=types.StringType,
            option_list=('DC', 'AC'))
        self.add_parameter('modulation_function',
            flags=Instrument.FLAG_GETSET, type=types.StringType,
            option_list=('sine',
                         'ramp',
                         'triangle',
                         'square',
                         'noise',
                         'external'))
        self.add_parameter('modulation_type',
            flags=Instrument.FLAG_GETSET, type=types.StringType,
            option_list=('AM',
                        'FM',
                        'PhaseM',
                        'sweep',
                        'pulse',
                        'blank',
                        'IQ'))

        self.add_parameter('Modulation_State',
            flags=Instrument.FLAG_GETSET, type=types.StringType)
        self.add_parameter('rf_output_block_temperature',
            flags=Instrument.FLAG_GET, type=types.FloatType)
        self.add_parameter('timebase',
            flags=Instrument.FLAG_GET, type=types.StringType)
        self.add_parameter('list_mode',
            flags=Instrument.FLAG_GETSET, type=types.BooleanType)
##        self.add_parameter('Frequency_List',
##            flags=Instrument.FLAG_SET, type=numpy.ndarray)
##        self.add_parameter('Power_List',
##            flags=Instrument.FLAG_SET, type=numpy.ndarray)
##        self.add_parameter('Dwell_Times_List',
##            flags=Instrument.FLAG_SET, type=numpy.ndarray)

        self.add_function('reset')
        self.add_function('get_all')
##        self.add_function('List_sweep_freq_on')
##        self.add_function('List_sweep_freq_off')
##        self.add_function('List_sweep_power_on')
##        self.add_function('List_sweep_power_on')
        self.add_function('trigger')
        self.add_function('list_on')
        self.add_function('list_off')
        self.add_function('create_list')
        self.add_function('get_list_entry')
        self.add_function('set_list_entry')
        self.add_function('get_error')


        if (reset):
            self.reset()
        else:
            self.get_all()

    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        self._visainstrument.write('*RST')
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
        logging.info(__name__ + ' : get all')
        self.get_ntype_power()
        self.get_bnc_power()
        self.get_frequency()
        self.get_status()
        self.get_bnc_output_status()
        self.get_rf_output_block_temperature()
        self.get_timebase()
        self.get_list_mode()
        self.get_modulation_function()
        self.get_modulation_coupling()
        self.get_modulation_type()

    def do_get_ntype_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (?) : power in dBm
        '''
        logging.debug(__name__ + ' : get ntype power')
        return float(self._visainstrument.ask('AMPR?'))

    def do_set_ntype_power(self, amp):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : set ntype power to %f' % amp)
        self._visainstrument.write('AMPR%s' % amp)

    def do_get_bnc_power(self):
        '''
        Reads the power of the bnc output from the instrument

        Input:
            None

        Output:
            ampl (?) : power in dBm
        '''
        logging.debug(__name__ + ' : get bnc_power')
        return float(self._visainstrument.ask('AMPL?'))

    def do_set_bnc_power(self, amp):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : set bnc_power to %f' % amp)
        self._visainstrument.write('AMPL %s' % amp)

    def do_get_bnc_output_status(self):
        '''
	Get the output status of the BNC connector.
	'''
	logging.debug(__name__ + ' : get the bnc output status')
	return bool(self._visainstrument.ask('ENBL?'))

    def do_set_bnc_output_status(self, status):
        '''
	Set the output status of the BNC connector.
	Input:
	    True : On
	    False : Off
	Output:
	    None
	'''
	logging.debug(__name__ + ' : set the bnc output status to %s' % status)
	self._visainstrument.write('ENBL %i' % status)

    def do_get_frequency(self):
        '''
        Reads the frequency of the signal from the instrument

        Input:
            None

        Output:
            freq (float) : Frequency in Hz
        '''
        logging.debug(__name__ + ' : get frequency')
        return float(self._visainstrument.ask('FREQ?'))

    def do_set_frequency(self, freq):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : set frequency to %f' % freq)
        self._visainstrument.write('FREQ%s' % freq)

    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + ' : get status')
        stat = self._visainstrument.ask('ENBR?')

        if (stat=='1'):
          return 'ON'
        elif (stat=='0'):
          return 'OFF'
        else:
          raise ValueError('Output status not specified : %s' % stat)
        return

    def do_set_status(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (string) : 'On' or 'Off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if (status.upper()=='ON'):
            status = 1
        elif (status.upper()=='OFF'):
            status = 0
        else:
            raise ValueError('set_status(): can only set on or off')
        self._visainstrument.write('ENBR%s' % status)

    def do_get_Frequency_Modulation_Rate(self):
        '''
        Get the size of the frequency modulation of FM
        '''
        logging.debug(__name__ + ' : get FM rate')
        return float(self._visainstrument.ask('RATE?'))

    def do_set_Frequency_Modulation_Rate(self, size):
        '''
        Set the size of the frequency modulation of FM
        '''
        logging.debug(__name__ + ' : set FM rate to %s' % size)
        self._visainstrument.write('RATE%s' % size)

    def do_get_Frequency_Modulation_Size(self):
        '''
        Get the size of the frequency modulation of FM
        '''
        logging.debug(__name__ + ' : get FM size')
        return float(self._visainstrument.ask('FDEV?'))

    def do_set_Frequency_Modulation_Size(self, size):
        '''
        Set the size of the frequency modulation of FM
        '''
        logging.debug(__name__ + ' : set FM size to %s' % size)
        self._visainstrument.write('FDEV%s' % size)

    def do_get_Modulation_State(self):
        '''
        Get the status of the modulation
        '''
        logging.debug(__name__ + ' : get Modulation state')
        response = self._visainstrument.ask('MODL?')
        if response == '0':
            return 'OFF'
        if response == '1':
            return 'ON'
    def do_set_Modulation_State(self, status):
        '''
        Set the status of the modulation

        Input:
            status (string) : 'On' or 'Off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if (status.upper()=='ON'):
            status = 1
        elif (status.upper()=='OFF'):
            status = 0
        else:
            raise ValueError('set_status(): can only set on or off')
        self._visainstrument.write('MODL%s' % status)

    def do_get_modulation_coupling(self):
        '''
        Get the modulation coupling
        Output:
            'DC'
            'AC'
        '''
        logging.debug(__name__ + ' : get modulation coupling')
        response = self._visainstrument.ask('COUP?')
        if response == '0':
            return 'AC'
        elif response == '1':
            return 'DC'
        else:
            logging.warning(__name__ + ' : answer to COUP? was not 0 or 1 : %s' % response)

    def do_set_modulation_coupling(self, coupling):
        '''
        Set the modulation coupling
        Input:
            'AC'
            'DC'
        '''
        logging.debug(__name__ + ' : set modulation coupling to %s' % coupling)
        if coupling == 'AC':
            self._visainstrument.write('COUP 0')
        if coupling == 'DC':
            self._visainstrument.write('COUP 1')

    def do_get_modulation_function(self):
        '''
        Get the modulation function
        0 Sine wave:    sine
        1 Ramp:         ramp
        2 Triangle:     triangle
        3 Square:       square
        4 Noise:        noise
        5 External:     external 
        '''
        logging.debug(__name__ + ' : get the modulation function')
        response = self._visainstrument.ask('MFNC?')
        if response == '0':
            return 'sine'
        elif response == '1':
            return 'ramp'
        elif response == '2':
            return 'triangle'
        elif response == '3':
            return 'square'
        elif response == '4':
            return 'noise'
        elif response == '5':
            return 'external'
        else:
            logging.warning(__name__ + ' : answer to MFNC? was not expected : %s' % response)

    def do_set_modulation_function(self, function):
        '''
        '''
        function_dict = {'SINE'     : 0,
                         'RAMP'     : 1,
                         'TRIANGLE' : 2,
                         'SQUARE'   : 3,
                         'NOISE'    : 4,
                         'EXTERNAL' : 5}
        logging.debug(__name__ + ' : set the modulation function to %s' % function)
        self._visainstrument.write('MFNC %s' % function_dict[function])

    def do_get_modulation_type(self):
        '''
        
        '''
        logging.debug(__name__ + ' : get the modulation type')
        response = self._visainstrument.ask('TYPE?')
        if response == '0':
            return 'AM'
        elif response == '1':
            return 'FM'
        elif response == '2':
            return 'PhaseM'
        elif response == '3':
            return 'sweep'
        elif response == '4':
            return 'pulse'
        elif response == '5':
            return 'blank'
        elif response == '6':
            return 'IQ'
        else:
            logging.warning(__name__ + ' : answer to TYPE? was not expected : %s' % response)

    def do_set_modulation_type(self, mtype):
        '''
        '''
        type_dict = {    'AM'     : 0,
                         'FM'     : 1,
                         'PHASEM' : 2,
                         'SWEEP'  : 3,
                         'PULSE'  : 4,
                         'BLANK'  : 5,
                         'IQ'     : 6}
        logging.debug(__name__ + ' : set the modulation type to %s' % mtype)
        self._visainstrument.write('TYPE %s' % type_dict[mtype])

    def do_get_rf_output_block_temperature(self):
        '''
	Get the temperature of the RF output block.
	'''
	return float(self._visainstrument.ask('TEMP?'))

    def do_get_timebase(self):
	'''
	Get the timebase of the instrument.
	'''
	timebase_dict = {'0':'Crystal', '1':'OCXO', '2':'Rubidium', '3':'External'}
	return timebase_dict[self._visainstrument.ask('TIMB?')]

    def trigger(self):
        '''
        Send a trigger to the instrument. Used for List mode.
        '''
        logging.debug(__name__ + ' : trigger')
        self._visainstrument.write('*TRG')

    def list_on(self):
        self._visainstrument.write('LSTE 1')

    def list_off(self):
        self._visainstrument.write('LSTE 0')

    def do_get_list_mode(self):
        '''
        Get whether the instrument is in list mode or not.
        Returns True or False
        '''
        return bool(self._visainstrument.ask('LSTE?'))

    def do_set_list_mode(self, on):
        '''
        Set whether the instrument is in list mode or not.
        '''
        self._visainstrument.write('LSTE %i' % on)

    def get_list_entry(self, index):
        '''
        Get the list entry for a given index.
        '''
        self._visainstrument.write('LSTI %i' % index)
        return self._visainstrument.ask('LSTI?')         

    def set_list_entry(self, index, *args, **kwargs):
        '''
        list_entry creates a list state for the list mode of the instrument.
        See page 80 of the manual.
        '''
        logging.debug(__name__ + ' : list_entry index %i' %index)
        command_list = ['N']*15
        if 'frequency' in kwargs:
            command_list[0]=str(kwargs['frequency'])
        if 'phase' in kwargs:
            command_list[1]=str(kwargs['phase'])
        if 'lf_amplitude' in kwargs:
            command_list[2]=str(kwargs['lf_amplitude'])
        if 'lf_offset' in kwargs:
            command_list[3]=str(kwargs['lf_offset'])
        if 'rf_amplitude' in kwargs:
            command_list[4]=('%.2f' % kwargs['rf_amplitude'])
        if 'font_panel_display' in kwargs:
            if kwargs['front_panel_display'] in range(13):
                command_list[5]=str(kwargs['front_panel_display'])
            else:
                logging.error('Incorrect value for front_panel_display.')
        if 'enable_setting' in kwargs:
            if kwargs['enable_setting'] in range(32):
                command_list[6]=str(kwargs['enable_setting'])
            else:
                logging.error('Incorrect value for enable_setting')
        if 'modulation_type' in kwargs:
            '''
            0 AM
            1 FM
            2 PhaseM
            3 Sweep
            4 Pulse
            5 Blank
            6 IQ (if option 3 is installed)
            '''
            if kwargs['modulation_type'] in range(7):
                command_list[7]=str(kwargs['modulation_type'])
        
        command_string = ','.join(command_list)
        logging.info(__name__ + ' : command list: LSTP %i %s' %(index,command_string))
        self._visainstrument.write('LSTP %i,%s' %(index, command_string))

    def create_list(self, size):
        '''
        Create a list with a certain size.
        '''
        answer = self._visainstrument.ask('LSTC? %i' % size)
        if answer:
            print 'List succesfully created.'
        else:
            print 'There was an error.'

    def get_error(self):
        return self._visainstrument.ask('LERR?')
            
    # shortcuts
    def off(self):
        '''
        Set status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_status('off')

    def on(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_status('on')

