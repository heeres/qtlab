from instrument import Instrument

class dummy_pulse_src(Instrument):
    '''this is a dummy pouse source'''

    def __init__(self, name):

#   this part needs to be looked at!
#    def __init__(self, address, reset=False):
#       self.address = address
        reset=False

# question:  do you need to call Instrument.get_something(self) if you want to send signal that new value is there?

        Instrument.__init__(self,name)
        self.add_parameter('start', flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET, minval=0, maxval=1)
        self.add_parameter('length', flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET, minval=0, maxval=1)
        self.add_parameter('amplitude', flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET, minval=-3.8, maxval=3.8)
        self.add_parameter('status', flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)

        # deze moet weg als er echte hardware is
        self._dummy_start = -99 
        self._dummy_length = -99
        self._dummy_amplitude = -99
        self._dummy_status = 'none'

        if reset:
            self.reset()
        else: 
            self.get_all()
           
#### initialization related

    def reset(self):
        print __name__, ': resetting instrument' 

        #This resets the values of the 'dummy' instrument:
        self._dummy_start = 20
        self._dummy_length = -120
        self._dummy_amplitude = 0
        self._dummy_status = 'off'
        
        #This updates all the variables in memory to the instrument values
        self.get_all()

    def get_all(self):
        print __name__, ': reading all settings from instrument'
        self._start = self._do_get_start(hard=True)
        self._length = self._do_get_length(hard=True)
        self._amplitude = self._do_get_amplitude(hard=True)
        self._status = self._do_get_status(hard=True)

#### communication with machine

    def _do_get_start(self, hard=True):
        if hard:
            print __name__ + ' : reading start from instrument'
            # getting value from instrument to memory
            self._start = self._dummy_start
            return self._start
        else:
            print __name__ + ' : reading start from memory'
            return self._start

    def _do_set_start(self, start):
        print __name__ + ': setting start to %s GHz' % start
        # sending value to instrument
        self._dummy_start = start
        # updating value in memory to new instrument value
        self._do_get_start()

    def _do_get_length(self,hard=True):
        if hard:
            print __name__ + ' : reading length from instrument'
            # getting value from instrument to memory
            self._length = self._dummy_length
            return self._length
        else:
            print __name__ + ' : reading length from memory'
            return self._length

    def _do_set_length(self,length):
        print __name__ + ' : setting length to %s dBm' % length
        # sending value to instrument
        self._dummy_length = length 
        # updating value in memory to new instrument value
        self._do_get_length()

    def _do_get_amplitude(self,hard=True):
        if hard:
            print __name__ + ' : reading amplitude from instrument'
            # getting value from instrument to memory
            self._amplitude = self._dummy_amplitude
            return self._amplitude
        else:
            print __name__ + ' : reading amplitude from memory'
            return self._amplitude

    def _do_set_amplitude(self,amplitude):
        print __name__ + ' : setting amplitude to %s degrees' % amplitude
        # sending value to instrument
        self._dummy_amplitude = amplitude
        # updating value in memory to new instrument value
        self._do_get_amplitude()

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
        # updating value in memory to new instrument value
        self._do_get_status()

### shorcuts ?
#    def off(self):
#        Instrument.set_status(self,'off')
#        self.set_status('off')
#
#    def on(self):
#        self.set_status('on')
