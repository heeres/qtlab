# SR830.py, Stanford Research 830 DSP lock-in driver
# Katja Nowack, Stevan Nadj-Perge, Arjan Beukman, Reinier Heeres
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
import time

class SR830(Instrument):
    '''
    This is the python driver for the Lock-In SR830 from Stanford Research Systems.

    Usage:
    Initialize with
    <name> = instruments.create('name', 'SR830', address='<GPIB address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the SR830.

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

        self.add_parameter('mode',
           flags=Instrument.FLAG_SET,
           type=types.BooleanType)
        self.add_parameter('frequency', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=1e-3, maxval=102e3,
            units='Hz', format='%.04e')
        self.add_parameter('phase', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-360, maxval=729.99, units='deg')
        self.add_parameter('harmonic',type=types.IntType,
                           flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
                           minval=1, maxval=19999)
        self.add_parameter('amplitude', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0.004, maxval=5.0,
            units='V', format='%.04e')
        self.add_parameter('X', flags=Instrument.FLAG_GET, units='V', type=types.FloatType)
        self.add_parameter('Y', flags=Instrument.FLAG_GET, units='V', type=types.FloatType)
        self.add_parameter('R', flags=Instrument.FLAG_GET, units='V', type=types.FloatType)
        self.add_parameter('P', flags=Instrument.FLAG_GET, units='deg', type=types.FloatType)
        self.add_parameter('tau', type=types.IntType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map={
                0 : "10mus",
                1 : "30mus",
                2 : "100mus",
                3 : "300mus",
                4 : "1ms",
                5 : "3ms",
                6 : "10ms",
                7 : "30ms",
                8 : "100ms",
                9 : "300ms",
                10 : "1s",
                11 : "3s",
                12 : "10s",
                13 : "30s",
                14 : "100s",
                15 : "300s",
                16 : "1ks",
                17 : "3ks",
                18 : "10ks",
                19 : "30ks"
            })
        self.add_parameter('out', type=types.FloatType, channels=(1,2,3,4),
            flags=Instrument.FLAG_GETSET,
            minval=-10.5, maxval=10.5, units='V', format='%.3f')
        self.add_parameter('in', type=types.FloatType, channels=(1,2,3,4),
            flags=Instrument.FLAG_GET,
            minval=-10.5, maxval=10.5, units='V', format='%.3f')
        self.add_parameter('sensitivity', type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            format_map={
                0 : "2nV",
                1 : "5nV",
                2 : "10nV",
                3 : "20nV",
                4 : "50 nV",
                5 : "100nV",
                6 : "200nV",
                7 : "500nV",
                8 : "1muV",
                9 : "2muV",
                10 : "5muV",
                11 : "10muV",
                12 : "20muV",
                13 : "50muV",
                14 : "100muV",
                15 : "200muV",
                16 : "500muV",
                17 : "1mV",
                18 : "2mV",
                19 : "5mV",
                20 : "10mV",
                21 : "20mV",
                22 : "50mV",
                23 : "100mV",
                24 : "200mV",
                25 : "500mV",
                26 : "1V"
            })
        self.add_parameter('reserve', type=types.IntType,
                           flags=Instrument.FLAG_GETSET,
                           format_map={0:'High reserve', 1:'Normal', 2:'Low noise'})
        self.add_parameter('input_config', type=types.IntType,
                           flags=Instrument.FLAG_GETSET,
                           format_map={0:'A', 1:'A-B', 2:'CVC 1MOhm', 3:'CVC 100MOhm'})
        self.add_parameter('input_shield', type=types.BooleanType,
                           flags=Instrument.FLAG_GETSET,
                           format_map={False:'Float', True:'GND'})
        self.add_parameter('input_coupling', type=types.BooleanType,
                           flags=Instrument.FLAG_GETSET,
                           format_map={False:'AC', True:'DC'})
        self.add_parameter('notch_filter', type=types.IntType,
                           flags=Instrument.FLAG_GETSET,
                           format_map={0:'off', 1:'1xline', 2:'2xline', 3:'both'})
        self.add_parameter('ref_input', type=types.BooleanType,
                           flags=Instrument.FLAG_GETSET,
                           format_map={False:'external', True:'internal'})
        self.add_parameter('ext_trigger', type=types.IntType,
                           flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
                           format_map={0:'Sine', 1:'TTL rising edge', 2:'TTL falling edge'})
        self.add_parameter('sync_filter', type=types.BooleanType,
                           flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
                           format_map={False:'off', True:'on'})
        self.add_parameter('filter_slope', type=types.IntType,
                           flags=Instrument.FLAG_GETSET,
                           format_map={0:'6dB/oct.', 1:'12dB/oct.', 2:'18dB/oct.', 3:'24dB/oct.'})
        self.add_parameter('unlocked', type=types.BooleanType,
                           flags=Instrument.FLAG_GET,
                           format_map={False:'locked', True:'unlocked'})
        self.add_parameter('input_overload', type=types.BooleanType,
                           flags=Instrument.FLAG_GET,
                           format_map={False:'normal', True:'overload'})
        self.add_parameter('time_constant_overload', type=types.BooleanType,
                           flags=Instrument.FLAG_GET,
                           format_map={False:'normal', True:'overload'})
        self.add_parameter('output_overload', type=types.BooleanType,
                           flags=Instrument.FLAG_GET,
                           format_map={False:'normal', True:'overload'})

        self.add_function('reset')
        self.add_function('get_all')

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
        logging.info(__name__ + ' : reading all settings from instrument')
        self.get_sensitivity()
        self.get_tau()
        self.get_frequency()
        self.get_amplitude()
        self.get_phase()
        self.get_X()
        self.get_Y()
        self.get_R()
        self.get_P()
        self.get_ref_input()
        self.get_ext_trigger()
        self.get_sync_filter()
        self.get_harmonic()
        self.get_input_config()
        self.get_input_shield()
        self.get_input_coupling()
        self.get_notch_filter()
        self.get_reserve()
        self.get_filter_slope()
        self.get_unlocked()
        self.get_input_overload()
        self.get_time_constant_overload()
        self.get_output_overload()

    def disable_front_panel(self):
        '''
        enables the front panel of the lock-in
        while being in remote control
        '''
        self._visainstrument.write('OVRM 0')

    def enable_front_panel(self):
        '''
        enables the front panel of the lock-in
        while being in remote control
        '''
        self._visainstrument.write('OVRM 1')

    def auto_phase(self):
        '''
        offsets the phase so that
        the Y component is zero
        '''
        self._visainstrument.write('APHS')

    def direct_output(self):
        '''
        select GPIB as interface
        '''
        self._visainstrument.write('OUTX 1')

    def read_output(self,output, ovl):
        '''
        Read out R,X,Y or phase (P) of the Lock-In

        Input:
            mode (int) :
            1 : "X",
            2 : "Y",
            3 : "R"
            4 : "P"

        '''
        parameters = {
        1 : "X",
        2 : "Y",
        3 : "R",
        4 : "P"
        }
        self.direct_output()
        if parameters.__contains__(output):
            logging.info(__name__ + ' : Reading parameter from instrument: %s ' %parameters.get(output))
            if ovl:
                self.get_input_overload()
                self.get_time_constant_overload()
                self.get_output_overload()
            readvalue = float(self._visainstrument.ask('OUTP?%s' %output))
        else:
            print 'Wrong output requested.'
        return readvalue

    def do_get_X(self, ovl=False):
        '''
        Read out X of the Lock In
        Check for overloads if ovl is True
        '''
        return self.read_output(1, ovl)

    def do_get_Y(self, ovl=False):
        '''
        Read out Y of the Lock In
        Check for overloads if ovl is True
        '''
        return self.read_output(2, ovl)

    def do_get_R(self, ovl=False):
        '''
        Read out R of the Lock In
        Check for overloads if ovl is True
        '''
        return self.read_output(3, ovl)

    def do_get_P(self, ovl=False):
        '''
        Read out P of the Lock In
        Check for overloads if ovl is True
        '''
        return self.read_output(4, ovl)

    def do_set_frequency(self, frequency):
        '''
        Set frequency of the local oscillator

        Input:
            frequency (float) : frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting frequency to %s Hz' % frequency)
        self._visainstrument.write('FREQ %e' % frequency)


    def do_get_frequency(self):
        '''
        Get the frequency of the local oscillator

        Input:
            None

        Output:
            frequency (float) : frequency in Hz
        '''
        self.direct_output()
        logging.debug(__name__ + ' : reading frequency from instrument')
        return float(self._visainstrument.ask('FREQ?'))

    def do_get_amplitude(self):
        '''
        Get the frequency of the local oscillator

        Input:
            None

        Output:
            frequency (float) : frequency in Hz
        '''
        self.direct_output()
        logging.debug(__name__ + ' : reading frequency from instrument')
        return float(self._visainstrument.ask('SLVL?'))

    def do_set_mode(self,val):
        logging.debug(__name__ + ' : Setting Reference mode to external' )
        self._visainstrument.write('FMOD %d' %val)


    def do_set_amplitude(self, amplitude):
        '''
        Set frequency of the local oscillator

        Input:
            frequency (float) : frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting amplitude to %s V' % amplitude)
        self._visainstrument.write('SLVL %e' % amplitude)


    def do_set_tau(self,timeconstant):
        '''
        Set the time constant of the LockIn

        Input:
            time constant (integer) : integer from 0 to 19

        Output:
            None
        '''

        self.direct_output()
        logging.debug(__name__ + ' : setting time constant on instrument to %s'%(timeconstant))
        self._visainstrument.write('OFLT %s' % timeconstant)

    def do_get_tau(self):
        '''
        Get the time constant of the LockIn

        Input:
            None
        Output:
            time constant (integer) : integer from 0 to 19
        '''

        self.direct_output()
        logging.debug(__name__ + ' : getting time constant on instrument')
        return float(self._visainstrument.ask('OFLT?'))

    def do_set_sensitivity(self, sens):
        '''
        Set the sensitivity of the LockIn

        Input:
            sensitivity (integer) : integer from 0 to 26

        Output:
            None
        '''

        self.direct_output()
        logging.debug(__name__ + ' : setting sensitivity on instrument to %s'%(sens))
        self._visainstrument.write('SENS %d' % sens)

    def do_get_sensitivity(self):
        '''
        Get the sensitivity
            Output:
            sensitivity (integer) : integer from 0 to 26
        '''
        self.direct_output()
        logging.debug(__name__ + ' : reading sensitivity from instrument')
        return float(self._visainstrument.ask('SENS?'))

    def do_get_phase(self):
        '''
        Get the reference phase shift

        Input:
            None

        Output:
            phase (float) : reference phase shit in degree
        '''
        self.direct_output()
        logging.debug(__name__ + ' : reading frequency from instrument')
        return float(self._visainstrument.ask('PHAS?'))


    def do_set_phase(self, phase):
        '''
        Set the reference phase shift

        Input:
            phase (float) : reference phase shit in degree

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting the reference phase shift to %s degree' %phase)
        self._visainstrument.write('PHAS %e' % phase)

    def set_aux(self, output, value):
        '''
        Set the voltage on the aux output
        Input:
            output - number 1-4 (defining which output you are addressing)
            value  - the voltage in Volts
        Output:
            None
        '''
        logging.debug(__name__ + ' : setting the output %(out)i to value %(val).3f' % {'out':output,'val': value})
        self._visainstrument.write('AUXV %(out)i, %(val).3f' % {'out':output,'val':value})

    def read_aux(self, output):
        '''
        Query the voltage on the aux output
        Input:
            output - number 1-4 (defining which output you are addressing)
        Output:
            voltage on the output D/A converter
        '''
        logging.debug(__name__ + ' : reading the output %i' %output)
        return float(self._visainstrument.ask('AUXV? %i' %output))

    def get_oaux(self, value):
        '''
        Query the voltage on the aux output
        Input:
            output - number 1-4 (defining which output you are adressing)
        Output:
            voltage on the input A/D converter
        '''
        logging.debug(__name__ + ' : reading the input %i' %value)
        return float(self._visainstrument.ask('OAUX? %i' %value))

    def do_set_out(self, value, channel):
        '''
        Set output voltage, rounded to nearest mV.
        '''
        self.set_aux(channel, value)

    def do_get_out(self, channel):
        '''
        Read output voltage.
        '''
        return self.read_aux(channel)

    def do_get_in(self, channel):
        '''
        Read input voltage, resolution is 1/3 mV.
        '''
        return self.get_oaux(channel)

    def do_get_ref_input(self):
        '''
        Query reference input: internal (true,1) or external (false,0)
        '''
        return int(self._visainstrument.ask('FMOD?'))==1

    def do_set_ref_input(self, value):
        '''
        Set reference input: internal (true,1) or external (false,0)
        '''
        if value:
            self._visainstrument.write('FMOD 1')
        else:
            self._visainstrument.write('FMOD 0')

    def do_get_ext_trigger(self):
        '''
        Query trigger source for external reference: sine (0), TTL rising edge (1), TTL falling edge (2)
        '''
        return int(self._visainstrument.ask('RSLP?'))

    def do_set_ext_trigger(self, value):
        '''
        Set trigger source for external reference: sine (0), TTL rising edge (1), TTL falling edge (2)
        '''
        self._visainstrument.write('RSLP '+ str(value))

    def do_get_sync_filter(self):
        '''
        Query sync filter. Note: only available below 200Hz
        '''
        return int(self._visainstrument.ask('SYNC?'))==1

    def do_set_sync_filter(self, value):
        '''
        Set sync filter. Note: only available below 200Hz
        '''
        if value:
            self._visainstrument.write('SYNC 1')
        else:
            self._visainstrument.write('SYNC 0')

    def do_get_harmonic(self):
        '''
        Query detection harmonic in the range of 1..19999.
        Note: frequency*harmonic<102kHz
        '''
        return int(self._visainstrument.ask('HARM?'))

    def do_set_harmonic(self, value):
        '''
        Set detection harmonic in the range of 1..19999.
        Note: frequency*harmonic<102kHz
        '''
        self._visainstrument.write('HARM '+ str(value))

    def do_get_input_config(self):
        '''
        Query input configuration: A (0), A-B (1), CVC 1MOhm (2), CVC 100MOhm (3)
        '''
        return int(self._visainstrument.ask('ISRC?'))

    def do_set_input_config(self, value):
        '''
        Set input configuration: A (0), A-B (1), CVC 1MOhm (2), CVC 100MOhm (3)
        '''
        self._visainstrument.write('ISRC '+ str(value))

    def do_get_input_shield(self):
        '''
        Query input shield: float (false,0), gnd (true,1)
        '''
        return int(self._visainstrument.ask('IGND?'))==1

    def do_set_input_shield(self, value):
        '''
        Set input shield: float (false,0), gnd (true,1)
        '''
        if value:
            self._visainstrument.write('IGND 1')
        else:
            self._visainstrument.write('IGND 0')

    def do_get_input_coupling(self):
        '''
        Query input coupling: AC (false,0), DC (true,1)
        '''
        return int(self._visainstrument.ask('ICPL?'))==1

    def do_set_input_coupling(self, value):
        '''
        Set input coupling: AC (false,0), DC (true,1)
        '''
        if value:
            self._visainstrument.write('ICPL 1')
        else:
            self._visainstrument.write('ICPL 0')

    def do_get_notch_filter(self):
        '''
        Query notch filter: none (0), 1xline (1), 2xline(2), both (3)
        '''
        return int(self._visainstrument.ask('ILIN?'))

    def do_set_notch_filter(self, value):
        '''
        Set notch filter: none (0), 1xline (1), 2xline(2), both (3)
        '''
        self._visainstrument.write('ILIN ' + str(value))

    def do_get_reserve(self):
        '''
        Query reserve: High reserve (0), Normal (1), Low noise (2)
        '''
        return int(self._visainstrument.ask('RMOD?'))

    def do_set_reserve(self, value):
        '''
        Set reserve: High reserve (0), Normal (1), Low noise (2)
        '''
        self._visainstrument.write('RMOD ' + str(value))

    def do_get_filter_slope(self):
        '''
        Query filter slope: 6dB/oct. (0), 12dB/oct. (1), 18dB/oct. (2), 24dB/oct. (3)
        '''
        return int(self._visainstrument.ask('OFSL?'))

    def do_set_filter_slope(self, value):
        '''
        Set filter slope: 6dB/oct. (0), 12dB/oct. (1), 18dB/oct. (2), 24dB/oct. (3)
        '''
        self._visainstrument.write('OFSL ' + str(value))
    def do_get_unlocked(self, update=True):
        '''
        Query if PLL is locked.
        Note: the status bit will be cleared after readout!
        Set update to True for querying present unlock situation, False for querying past events
        '''
        if update:
           self._visainstrument.ask('LIAS? 3')     #for realtime detection we clear the bit by reading it
           time.sleep(0.02)                        #and wait for a little while so that it can be set
        return int(self._visainstrument.ask('LIAS? 3'))==1

    def do_get_input_overload(self, update=True):
        '''
        Query if input or amplifier is in overload.
        Note: the status bit will be cleared after readout!
        Set update to True for querying present overload, False for querying past events
        '''
        if update:
            self._visainstrument.ask('LIAS? 0')     #for realtime detection we clear the bit by reading it
            time.sleep(0.02)                        #and wait for a little while so that it can be set again
        return int(self._visainstrument.ask('LIAS? 0'))==1

    def do_get_time_constant_overload(self, update=True):
        '''
        Query if filter is in overload.
        Note: the status bit will be cleared after readout!
        Set update to True for querying present overload, False for querying past events
        '''
        if update:
            self._visainstrument.ask('LIAS? 1')     #for realtime detection we clear the bit by reading it
            time.sleep(0.02)                        #and wait for a little while so that it can be set again
        return int(self._visainstrument.ask('LIAS? 1'))==1

    def do_get_output_overload(self, update=True):
        '''
        Query if output (also main display) is in overload.
        Note: the status bit will be cleared after readout!
        Set update to True for querying present overload, False for querying past events
        '''
        if update:
            self._visainstrument.ask('LIAS? 2')     #for realtime detection we clear the bit by reading it
            time.sleep(0.02)                        #and wait for a little while so that it can be set again
        return int(self._visainstrument.ask('LIAS? 2'))==1
