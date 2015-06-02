# June 2013 - Gabriele de Boo
from instrument import Instrument
from lib import visafunc
from time import sleep
import visa
import logging
import types

freqs = (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)

def int2wvl(i):
    wvl = 900.0+float(i)/4000*200
    return wvl

def wvl2int(wvl):
    i = (wvl-900.0)/200*4000
    return i

class Superlum_BS_1060(Instrument):
    def __init__(self, name, address, reset=False):
        logging.info('Initializing instrument Superlum')
        Instrument.__init__(self, name, tags=['physical'])
        self._address = address
        self._name = name
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.baud_rate = 57600
        self._visainstrument.term_chars = '\r\n'	

        self._visainstrument.clear()
        self._visainstrument.ask('') # It always returns 'AE' after the clear command
        self._visainstrument.ask('S12')

#        self.add_function('reset')
        self.add_function('identify')
        self.add_function('set_to_local')
        self.add_function('set_to_remote')
        self.add_function('set_power_low')
        self.add_function('set_power_high')

        self.add_parameter('optical_output',
            type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('booster_emission',
            type=types.BooleanType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('power',
            type=types.StringType,
            flags=Instrument.FLAG_GET,
	    option_list=(
		    'low',
		    'high'))
        self.add_parameter('master_key_control',
            type=types.BooleanType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('full_tuning_range',
            type=types.ListType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('operating_mode',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
	    option_list=(
		    'manual',
		    'external',
		    'automatic',
		    'modulation'))
        self.add_parameter('manual_mode_wavelength',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=1024.0, maxval=1094.0, units='nm')
        self.add_parameter('sweep_mode_start',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=1024.0, maxval=1094.0, units='nm')
        self.add_parameter('sweep_mode_end',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=1024.0, maxval=1094.0, units='nm')
        self.add_parameter('sweep_speed',
            type=types.IntType,
            flags=Instrument.FLAG_GETSET, minval=2, maxval=10000, units='nm/s')
        self.add_parameter('modulation_mode_wavelength1',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=1024.0, maxval=1094.0, units='nm')
        self.add_parameter('modulation_mode_wavelength2',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=1024.0, maxval=1094.0, units='nm')
        self.add_parameter('modulation_mode_frequency',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, units='Hz',
	    option_list=freqs)

        self.get_all()

    def get_all(self):
        self.identify()
        self.get_optical_output()
        self.get_booster_emission()
        self.get_power()
        self.get_master_key_control()
        self.get_full_tuning_range()
        self.get_operating_mode()
        self.get_manual_mode_wavelength()
        self.get_sweep_mode_start()
        self.get_sweep_mode_end()
        self.get_sweep_speed()
        self.get_modulation_mode_wavelength1()
        self.get_modulation_mode_wavelength2()
        self.get_modulation_mode_frequency()
#        self.get_Sweep_Slow()

    def identify(self):
        reply = self._visainstrument.ask('S0')
        if reply.startswith('S20'):
            return reply[3:]

    def do_get_optical_output(self):
        '''
        Probes whether the optical output is active.
        
        Input:
            None
        Output:
            True when it is on, False when it is off
            In case of an error a warning exception is raised.
        '''
        logging.debug('Getting the optical output of %s.' % self._name)
        reply = self.reply_error_check(self._visainstrument.ask('S20'))

        if reply.startswith('A2'):
            data1 = int(reply[2:5])
            data2 = int(reply[6:7])
            if ((data1 < 97) or (data1 == 97) or (data1 ==113)):
                return False
                logging.info('The optical output of %s is off' % self._name)
            else:
                return True
                logging.info('The optical output of %s is on' % self._name)
        else:
            logging.warning('%s responded with an unknown string: %s' % ( self._name, reply))
            raise Warning('%s responded with an unknown string: %s' % ( self._name, reply))

    def do_set_optical_output(self, output):
        '''
        Sets the optical output.

        Input:
            True to turn the laser on
            False to turn the laser off
        Output:
            None
        '''
        logging.info('Setting the optical output of %s to %s.' % (self._name, output))
        if output: 
            if not self.do_get_optical_output():
                reply = self._visainstrument.ask('S21')
                sleep(0.5)
                self.get_booster_emission()
            else:
#                print 'Optical output is already enabled.'
                logging.info('The optical output of %s already was on.' %self._name)
        else:
            if self.do_get_optical_output():
                reply = self._visainstrument.ask('S21')
                self.get_booster_emission()
            else:
#                print 'Optical output is already disabled.'
                logging.info('The optical output of %s already was off.' %self._name)

    def do_get_booster_emission(self):
        '''
        Get the status of the booster emission.

        Input:
            None
        Output:
            True if booster emission is on
            False if booster emission is off
        '''
        logging.info('Getting the status of the booster emission of %s.' % self._name)
        reply = self.reply_error_check(self._visainstrument.ask('S20'))
        if reply.startswith('A2'):
            data1 = int(reply[2:5])
            data2 = int(reply[6:7])
            if (data2 == 2) or (data2 == 6):
                return False
            else:
                return True
        else:
            logging.warning('%s responded with: %s.' % (self._name, reply))

    def do_get_power(self):
        reply = self.reply_error_check(self._visainstrument.ask('S40'))
        if reply.startswith('A4'):
            data1 = int(reply[2:5])
            data2 = int(reply[6:7])
            if data1 < 104:
                return 'low'
            if data1 > 112:
                return 'high'
            else:
                return 0
        else:
            logging.warning('get_power: %s responded with %s.' % (self._name, reply))
            raise Warning('%s get_power failed because the response was: %s.' % (self._name, reply))
    
    def set_power_low(self):
        if self.get_optical_output:
            if self.get_power() == 'low':
                logging.info('Power is already low.')
            else:
                reply = self.reply_error_check(self._visainstrument.ask('S41'))
        else:
            logging.warning('set_power_low failed for %s because the optical output is active.' % self._name)
            raise Warning('The power of %s can not be changed because the optical output is active.' % self._name)

    def set_power_high(self):
        if self.get_optical_output:
            if self.get_power() == 'High':
                logging.info('Power is already high.')
            else:
                reply = self._visainstrument.ask('S41')
        else:
            logging.warning('set_power_high failed for %s because the optical output is active.' % self._name)
            raise Warning('The power of %s can not be changed because the optical output is active.' % self._name)

    def do_get_master_key_control(self):
        '''
        Get the status of the Master Key control.
        Input:
            None
        Output:
            True when 1
            False when 0
            Raise warning if the instrument is under local control.
        '''
        reply = self.reply_error_check(self._visainstrument.ask('S20'))
        if reply.startswith('A2'):
            data1 = int(reply[2:5])
            data2 = int(reply[6:7])
            if data1 < 97:
                return False
            else:
                return True
        else:
            logging.warning('get_master_key_control: %s responded with %s.' % (self._name, reply))
            raise Warning('%s get_master_key_control failed because the response was: %s.' % (self._name, reply))

#    def _send_and_read(self, message):
#        logging.debug('Sending %r', message)
#        reply = self._visainstrument.ask(message)
#        return reply

    def set_to_local(self):
        logging.debug('Setting to local.')
        reply = self._visainstrument.ask('S11')
        if reply == 'A11':
            print 'Superlum set to local mode.'
        else:
            print 'Superlum command failed with error: ' + reply

    def do_get_full_tuning_range(self):
        # The Full Tuning range consists of one list, with two lists inside
        # [[end wavelength low power, start wavelength low power, end wavelength high power, start wavelength high power]]
        logging.debug('Getting Full Tuning Range.')
        reply = self.reply_error_check(self._visainstrument.ask('S52'))
        if reply.startswith('A52'):
            start_low = int2wvl(int(reply[3:7]))
        reply = self._visainstrument.ask('S51')
        if reply.startswith('A51'):
            end_low = int2wvl(int(reply[3:7]))
        reply = self._visainstrument.ask('S54')
        if reply.startswith('A54'):
            start_high = int2wvl(int(reply[3:7]))
        reply = self._visainstrument.ask('S53')
        if reply.startswith('A53'):
            end_high = int2wvl(int(reply[3:7]))
        return [[start_low, end_low], [start_high, end_high]]

    def do_get_operating_mode(self):
        logging.debug('Getting operating mode.')
        reply = self.reply_error_check(self._visainstrument.ask('S60'))
        if reply.startswith('A6'):
            if reply[2] == '1':
                return 'manual'
            elif reply[2] == '2':
                return 'automatic'
            elif reply[2] == '3':
                return 'external'
            elif reply[2] == '4':
                return 'modulation'
        else:
            logging.warning('get_operating_mode: %s responded with %s.' % (self._name, reply))
            raise Warning('%s get_operating_mode failed because the response was: %s.' % (self._name, reply))

    def do_set_operating_mode(self, mode):
        if mode == 'manual':
            self._visainstrument.ask('S61')
        elif mode == 'automatic':
            self._visainstrument.ask('S62')
        elif mode == 'external':
            self._visainstrument.ask('S63')
        elif mode == 'modulation':
            self._visainstrument.ask('S64')
        else:
            print 'Mode selection value is wrong, choose either manual, automatic, external or modulation.'

    def set_to_remote(self):
        logging.debug('Setting to remote.')
        reply = self._visainstrument.ask('S12')
        if reply == 'A12':
            print 'Superlum set to remote mode.'
        else:
            print 'Superlum command failed with error: ' + reply

    def do_get_manual_mode_wavelength(self):
        reply = self.reply_error_check(self._visainstrument.ask('S71'))
        if reply.startswith('A71'):
            return int2wvl(reply[3:7])
        else:
            logging.warning('get_manual_mode_Wavelength: %s responded with %s.' % (self._name, reply))
            raise Warning('%s get_manual_mode_Wavelength failed because the response was: %s.' % (self._name, reply))

    def do_set_manual_mode_wavelength(self, wvl):
        '''
        Set the wavelength in the Manual Mode
        Input:
            Wavelength in nanometers
        Output:
            None
        '''
        logging.info('Setting the wavelength of %s to %.2f.' % (self._name, wvl))
        laser_string = '%0*d' % (4, wvl2int(wvl))
        reply = self.reply_error_check(self._visainstrument.ask('S81'+laser_string))
        if reply == ('A81'+laser_string):
#            print 'Wavelength changed to %4.2f nm' % wvl
            logging.debug('Wavelength succesfully set.')
        else:
#            print 'Error: ' + reply
            logging.warning('set_manual_mode_wavelength: Failed with reply from laser: %s' % reply)
            raise Warning('%s responded with an incorrect string: %s' % ( self._name, reply))

    def do_get_sweep_mode_start(self):
        logging.debug('Getting Sweep Mode Start.')
        reply = self.reply_error_check(self._visainstrument.ask('S72'))
        if reply.startswith('A72'):
            return int2wvl(reply[3:7])
        else:
            logging.warning('get_sweep_mode_start: %s responded with %s.' % (self._name, reply))
            raise Warning('%s get_sweep_mode_start failed because the response was: %s.' % (self._name, reply))

    def do_set_sweep_mode_start(self, wvl):
        logging.debug('Setting sweep mode start.')
        laser_string = '%0*d' % (4, wvl2int(wvl))
        reply = self._visainstrument.ask('S82'+laser_string)
        if reply == ('A82'+laser_string):
            print 'Sweep Mode Start changed to %4.2f nm' % wvl
        else:
            print 'Error: ' + reply

    def do_get_sweep_mode_end(self):
        logging.debug('Getting sweep mode end.')
        reply = self.reply_error_check(self._visainstrument.ask('S73'))
        if reply.startswith('A73'):
            return int2wvl(reply[3:7])
        else:
            logging.warning('get_Sweep_Mode_End: %s responded with %s.' % (self._name, reply))
            raise Warning('%s get_Sweep_Mode_End failed because the response was: %s.' % (self._name, reply))

    def do_set_sweep_mode_end(self, wvl):
        logging.debug('Setting sweep mode end.')
        laser_string = '%0*d' % (4, wvl2int(wvl))
        reply = self._visainstrument.ask('S83'+laser_string)
        if reply == ('A83'+laser_string):
            print 'Sweep mode end changed to ' + wvl
        else:
            print 'Error: ' + reply

    def do_get_sweep_speed(self):
        logging.debug('Getting sweep speed.')
        # If the sweep speed is slow:
        # 2 - 9 nm/s in steps of 1 nm
        # If the sweep speed is fast:
        # 0001 is the 4-byte code for 10 nm/s
        # 1000 is the 4-byte code for 10000 nm/s
        # Steps of 10 nm, so conversion is just multiplication by 10
        reply1 = self.reply_error_check(self._visainstrument.ask('S74'))
        reply2 = self.reply_error_check(self._visainstrument.ask('S78'))
        if reply1.startswith('A74'):
            if int(reply1[3:7])>0:
                return (10*int(reply1[3:7])) # Fast sweep speed
            else:
                return (reply2[3:5]) # Slow sweep speed
        else:
            logging.warning('get_sweep_speed: %s responded with %s.' % (self._name, reply))
            raise Warning('%s get_sweep_sweep failed because the response was: %s.' % (self._name, reply))

    def do_set_sweep_speed(self, speed):
        if speed < 10:
            reply = self._visainstrument.ask('S88'+str(speed))
            if reply.startswith('A88'):
                print 'Fast Sweep Speed set to %d nm/s' % speed
            else:
                print 'Error: ' + reply
        else:
            reply = self._visainstrument.ask('S84'+str(speed/10))
            if reply.startswith('A84'):
                print 'Fast Sweep Speed set to %d nm/s' % speed
            else:
                print 'Error: ' + reply

    def do_get_modulation_mode_wavelength1(self):
        logging.debug('Getting Modulation Mode Wavelength1.')
        reply = self.reply_error_check(self._visainstrument.ask('S75'))
        if reply.startswith('A75'):
            return int2wvl(reply[3:7])
        else:
            logging.warning('get_modulation_mode_wavelength1: %s responded with %s.' % (self._name, reply))
            raise Warning('%s get_modulation_mode_wavelength1 failed because the response was: %s.' % (self._name, reply))

    def do_set_modulation_mode_wavelength1(self, wvl):
        logging.debug('Setting modulation mode wavelength1.')
        laser_string = '%0*d' % (4, wvl2int(wvl))
        reply = self.reply_error_check(self._visainstrument.ask('S85'+laser_string))
        if reply == ('A85'+laser_string):
            print 'Modulation mode wavelength 1 set to ' + str(wvl)
        else:
            logging.warning('set_Modulation_Mode_Wavelength1: %s responded with %s.' % (self._name, reply))
            raise Warning('%s set_Modulation_Mode_Wavelength1 failed because the response was: %s.' % (self._name, reply))

    def do_get_modulation_mode_wavelength2(self):
        logging.debug('Getting modulation mode wavelength2.')
        reply = self.reply_error_check(self._visainstrument.ask('S76'))
        if reply.startswith('A76'):
            return int2wvl(reply[2:6])
        else:
            logging.warning('get_modulation_mode_wavelength2: %s responded with %s.' % (self._name, reply))
            raise Warning('%s get_modulation_mode_wavelength2 failed because the response was: %s.' % (self._name, reply))

    def do_set_modulation_mode_wavelength2(self, wvl):
        logging.debug('Setting modulation mode wavelength2.')
        laser_string = '%0*d' % (4, wvl2int(wvl))
        reply = self.reply_error_check(self._visainstrument.ask('S86'+laser_string))
        if reply == ('A86'+laser_string):
            print 'Modulation mode wavelength 1 set to ' + str(wvl)
        else:
            logging.warning('set_modulation_mode_wavelength2: %s responded with %s.' % (self._name, reply))
            raise Warning('%s set_modulation_mode_wavelength2 failed because the response was: %s.' % (self._name, reply))

    def do_get_modulation_mode_frequency(self):
        logging.debug('Getting the modulation mode frequency.')
        reply = self.reply_error_check(self._visainstrument.ask('S77'))
        if reply.startswith('A77'):
            freq_number = int(reply[3:5])
            return freqs[freq_number-1]
        else:
            logging.warning('get_modulation_mode_frequency: %s responded with %s.' % (self._name, reply))
            raise Warning('%s get_modulation_mode_frequency failed because the response was: %s.' % (self._name, reply))

    def do_set_modulation_mode_frequency(self, freq):
        logging.debug('Setting the modulation mode frequency.')
        if freq in freqs:
            i = freqs.index(freq)
            print i 
            laser_string = '%0*d' % (2,(i+1))
            print laser_string
            reply = self._visainstrument.ask('S87'+laser_string)
            if reply == ('A87'+laser_string):
                print 'Modulation mode frequency set to ' + str(freq)
            else:
                print 'Error: ' + reply
        else:
            print 'Frequency not in allowed frequencies'
            print 'Allowed frequencies' + str(freqs)

    def reply_error_check(self, reply):
        '''
        The instrument replies with two error messages:
        <AL>: Instrument is under local control.
              Any query except the control change query is denied.
        <AE>: General error.
        
	If any of these errors occur the program should throw an exception
        because the errors are avoidable.
        Input:
            Reply from the instrument
        Output:
            Reply from the instrument
        '''
	if reply == 'AL':
            logging.warning('%s responded with AL.' % self._name)
            raise Warning(
	        'The function could not be executed becase %s is under local control.'
                % self._name)
	elif reply == 'AE':
            logging.warning('%s responded with AE.' % self._name)
            raise Warning(
                'The function could not be executed becase %s responded with a general error.' 
		% self._name)
        else:
            return reply
