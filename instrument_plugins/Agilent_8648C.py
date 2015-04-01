# Agilent_8648C.py class, to perform the communication between the Wrapper and the device
# Sam Hile <samhile@gmail.com>, 2011
# Karsten Beckmann <karsten.beckmann@stud.tu-darmstadt.de>, 2012
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
import qt

class Agilent_8648C(Instrument):
    '''
    This is the driver for the Agilent 8648C Signal Genarator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Agilent_8648C', address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Agilent_8648C, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Agilent_8648C')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)

        # Implemented parameters        
        self.add_parameter('power',
            flags=Instrument.FLAG_GETSET, units='dBm', minval=-136, maxval=13, type=types.FloatType)
        self.add_parameter('frequency',
            flags=Instrument.FLAG_GETSET, units='MHz', minval=9e-3, maxval=3.2e3, type=types.FloatType)
        self.add_parameter('output_status',
            flags=Instrument.FLAG_GETSET, type=types.BooleanType)
        self.add_parameter('frequency_modulation_status',
            flags=Instrument.FLAG_GET, type=types.BooleanType)
        self.add_parameter('frequency_modulation_deviation',
            flags=Instrument.FLAG_GET, type=types.FloatType, units='Hz')
        self.add_parameter('frequency_modulation_source',
            flags=Instrument.FLAG_GET, type=types.StringType,
            option_list=('INT','EXT'))
        self.add_parameter('amplitude_modulation_status',
            flags=Instrument.FLAG_GET, type=types.BooleanType)
        self.add_parameter('frequency_reference_status',
            flags=Instrument.FLAG_GET, type=types.BooleanType)
        self.add_parameter('automatic_attenuator_control_status',
            flags=Instrument.FLAG_GET, type=types.BooleanType)
                        
        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('on')
        self.add_function('off')
#        self.add_function('alc_off')

        self._power_step = 5e-1
        self._power_step_time = 100e-3

        self._frequency_step = 500e-2
        self._frequency_step_time = 100e-3

        if (reset):
            self.reset()
        else:
            self.get_all()

    def set_power_ramp(self, power_step, power_step_time):
        '''
        Set power ramp settings, default values set in "__init__"

        Input:
            power step and power step time
        Output:
            none
        '''        
        self._power_step = power_step
        self._power_step_time = power_step_time

    def set_frequency_ramp(self, frequency_step, frequency_step_time):
        '''
        Set frequency ramp settings, default values set in "__init__"

        Input:
            frequency step and frequency step time
        Output:
            none
        '''
        self._frequency_step = frequency_step
        self._frequency_step_time = frequency_step_time

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
        self.get_power()
        self.get_frequency()
        self.get_output_status()
        self.get_frequency_modulation_status()
        self.get_frequency_modulation_deviation()
        self.get_frequency_modulation_source()
        self.get_amplitude_modulation_status()
        self.get_frequency_reference_status()
        self.get_automatic_attenuator_control_status()

    def do_get_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (float) : power in dBm
        '''
        logging.debug(__name__ + ' : get power')
        return float(self._visainstrument.ask('POW:AMPL?'))

#    def alc_off(self):
#        '''
#        Turn ALC off
#        '''
#        logging.debug(__name__ + ' : turn ALC off')
#        self._visainstrument.write('POW:ALC OFF')

        
    def do_set_power(self, amp):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in dBm

        Output:
            None
        '''

        start_power = self.get_power(1)
        
        step = self._power_step * cmp(amp, start_power)
        step_time = self._power_step_time
        power_ramp = []
        if not(step == 0):
            Nramp = int(abs((start_power - amp) / step))
            power_ramp = [x * step + start_power for x in range(Nramp + 1)]
            power_ramp.append(amp)
        else:
            power_ramp = [start_power, amp]
        
        for v in power_ramp:
            logging.debug(__name__ + ' : set power to %f dBm' % amp)            
            self._visainstrument.write('POW:AMPL %s dBm' % v) 
            qt.msleep(step_time)
            self.get_power()
        return self.get_power()

        #logging.debug(__name__ + ' : set power to %f dBm' % amp)
        #self._visainstrument.write('POW:AMPL %s dBm' % amp)        

    def do_get_frequency(self):
        '''
        Reads the frequency of the signal from the instrument

        Input:
            None

        Output:
            freq (float) : Frequency in Hz
        '''

        logging.debug(__name__ + ' : get frequency')
        return float(self._visainstrument.ask('FREQ:CW?'))

    def do_set_frequency(self, freq):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in MHz

        Output:
            None
        '''

        start_frequency = self.get_frequency()/1e6
        #print "get_freq"+str(self.get_frequency())
        step = self._frequency_step * cmp(freq, start_frequency)
        step_time = self._frequency_step_time
        frequency_ramp = []
        if not(step == 0):
            Nramp = int(abs((start_frequency - freq) / step))
            #print 'sf'+str(start_frequency)
            #print 'gf'+str(freq)
            #print 'step'+str(step)
            frequency_ramp = [x * step + start_frequency for x in range(Nramp + 1)]
            frequency_ramp.append(freq)
        else:
            frequency_ramp = [start_frequency, freq]
        
        for v in frequency_ramp:
            logging.debug(__name__ + ' : set frequency to %f MHz' % freq)            
            self._visainstrument.write('FREQ:CW %s MHz' % v) 
            qt.msleep(step_time)
            self.get_frequency()
        return self.get_frequency()

           #logging.debug(__name__ + ' : set frequency to %f MHz' % freq)            
           #self._visainstrument.write('FREQ:CW %s MHz' % v) 
         

    def do_get_output_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (Boolean) : True or False
        '''
        logging.debug(__name__ + ' : get status')
        stat = self._visainstrument.ask('OUTP:STAT?')

        if (stat=='1'):
          return True
        elif (stat=='0'):
          return False
        else:
          raise ValueError('Output status not specified : %s' % stat)
        return

    def do_set_output_status(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (Boolean) : True or False

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
#        if status.upper() in ('ON', 'OFF'):
#            status = status.upper()
#        else:
#            raise ValueError('set_status(): can only set on or off')
        if status:
            self._visainstrument.write('OUTP:STAT ON')
        else:
            self._visainstrument.write('OUTP:STAT OFF')
#        self._visainstrument.write('OUTP:STAT %s' % status)

    def do_get_frequency_modulation_status(self):
        '''
        Input:
            None
        Output:
            True or False
        '''
        logging.debug(__name__ + ' : get the frequency modulation status.')
        answer = self._visainstrument.ask('FM:STAT?')
        if answer == '1':
            return True
        elif answer == '0':
            return False
        else:
            raise ValueError('Frequency modulation status not specified : %s' % answer)

    def do_get_frequency_modulation_deviation(self):
        '''
        Input:
            None
        Output:
            Frequency Deviation in Hz
        '''
        logging.debug(__name__ + ' : get the frequency modulation deviation.')
        answer = self._visainstrument.ask('FM:DEV?')
        return float(answer)

    def do_get_frequency_modulation_source(self):
        '''
        Input:
            None
        Output:
            INTERNAL
            EXTERNAL
        '''
        logging.debug(__name__ + ' : get the frequency modulation source.')
        answer = self._visainstrument.ask('FM:SOUR?')
        if (answer == 'INTERNAL') or (answer == 'EXTERNAL'):
            return answer
        else:
            raise ValueError('Frequency modulation source not specified: %s' % answer)

    def do_get_amplitude_modulation_status(self):
        '''
        Get the amplitude modulation status.
        Input:
            None
        Output:
            True or False
        '''
        logging.debug(__name__ + ' : get the amplitude modulation status.')
        answer = self._visainstrument.ask('AM:STAT?')
        if answer == '0':
            return False
        elif answer == '1':
            return True
        else:
            raise ValueError('Amplitude modulation status not specified: %s' % answer)

    def do_get_frequency_reference_status(self):
        '''
        Get whether the frequency reference mode is off or on.
        Input:
            None
        Output:
            True or False
        '''
        logging.debug(__name__ + ' : get the frequency reference status.')
        answer = self._visainstrument.ask('FREQ:REF:STAT?')
        if answer == '0':
            return False
        elif answer == '1':
            return True
        else:
            raise ValueError('Frequency reference status not specified: %s' % answer)

    def do_get_automatic_attenuator_control_status(self):
        '''
        Get whether the automatic attenuator control is on or off.
        Input:
            None
        Output:
            True or False
        '''
        logging.debug(__name__ + ' : get the automatic attenuator control status.')
        answer = self._visainstrument.ask('POW:ATT:AUTO?')
        if answer == '0':
            return False
        elif answer == '1':
            return True
        else:
            raise ValueError('Automatic attenuator control status not specified: %s' % answer)

    # shortcuts
    def off(self):
        '''
        Set status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_output_status(False)

    def on(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_output_status(True)

