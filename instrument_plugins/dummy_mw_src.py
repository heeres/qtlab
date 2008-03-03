from instrument import Instrument

class dummy_mw_src(Instrument):
    '''this is a dummy microwave source'''

    def __init__(self, name):

#   this part need to be looked at!
#    def __init__(self, name, address, reset=False):
#        self.address = address
        reset=False

        Instrument.__init__(self,name)
        self.add_parameter('frequency', flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=10, units='Hz')
        self.add_parameter('power', flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-120, maxval=25, units='dBm')
        self.add_parameter('phase', flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET, minval=-180, maxval=180)
        self.add_parameter('status', flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)

        # this represents all the instrument settings for a currently uninitilized/unresetted machine. 
        # This can be removed for a real insrument
        self._dummy_frequency = -99
        self._dummy_power = -99
        self._dummy_phase = -99
        self._dummy_status = 'none'


        if reset:
            self.reset()
        else: 
            self.get_all()
           
#### initialization related

    def reset(self):
        print __name__ + ' : resetting instrument' 

        #This resets the values of the 'dummy' instrument:
        self._dummy_frequency = 20
        self._dummy_power = -120
        self._dummy_phase = 0
        self._dummy_status = 'off'
        
        #This updates all the variables in memory to the instrument values
        self.get_all()

    def get_all(self):
        print __name__ + ' : reading all settings from instrument'
        self._frequency = self._do_get_frequency(hard=True)
        self._power = self._do_get_power(hard=True)
        self._phase = self._do_get_phase(hard=True)
        self._status = self._do_get_status(hard=True)

#### communication with machine

    def _do_get_frequency(self, hard=True):
        if hard:
            print __name__ + ' : reading frequency from instrument'
            # getting value from instrument to memory
            self._frequency = self._dummy_frequency
            return self._frequency
        else:
            print __name__ + ' : reading frequency from memory'
            return self._frequency

    def _do_set_frequency(self, frequency):
        print __name__ + ' : setting frequency to %s GHz' % frequency
        # sending value to instrument
        self._dummy_frequency = frequency
        # hard getting instrument value to memory
        self._do_get_frequency()

    def _do_get_power(self,hard=True):
        if hard:
            print __name__ + ' : reading power from instrument'
            # getting value from instrument to memory
            self._power = self._dummy_power
            return self._power
        else:
            print __name__ + ' : reading power from memory'
            return self._power

    def _do_set_power(self,power):
        print __name__ + ' : setting power to %s dBm' % power
        # sending value to instrument
        self._dummy_power = power 
        # hard getting instrument value to memory
        self._do_get_power()

    def _do_get_phase(self,hard=True):
        if hard:
            print __name__ + ' : reading phase from instrument'
            # getting value from instrument to memory
            self._phase = self._dummy_phase
            return self._phase
        else:
            print __name__ + ' : reading phase from memory'
            return self._phase

    def _do_set_phase(self,phase):
        print __name__ + ' : setting phase to %s degrees' % phase
        # sending value to instrument
        self._dummy_phase = phase
        # updating value in memory to new instrument value
        self._do_get_phase()

    def _do_get_status(self,hard=True):
        if hard:
            print __name__ + ' : reading status from instrument'
            # getting value from instrument to memory
            self._status = self._dummy_status
            return self._status
        else:
            print __name__ + ' : reading status from memory'
            return self._status

    def _do_set_status(self,status):
        print __name__ + ' : setting status to "%s"' % status
        # sending value to instrument
        self._dummy_status = status 
        # hard getting instrument value to memory
        self._do_get_status()

### shorcuts ?
    def off(self):
        self.set_status('off')

    def on(self):
        self.set_status('on')
