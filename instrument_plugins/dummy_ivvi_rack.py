from instrument import Instrument

class dummy_ivvi_rack(Instrument):
    '''this is a dummy ivvi rack'''

    def __init__(self,name):

        # address?
        reset=False

        Instrument.__init__(self,name)
        self.add_parameter('dacvalue', flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET, minval=0, maxval=10)

        self._dummy_dacvalue = [-99,-99,-99,-99,-99,-99,-99,-99]
        self._dacvalue = [-99,-99,-99,-99,-99,-99,-99,-99]

        if reset:
            self.reset()
        else:
            self.get_all()

#### initialization related

    def reset(self):
        print __name__ + ' : resetting instrument'
        self._dummy_dacvalue = [0,0,0,0,0,0,0,0]
        self.get_all()

    def get_all(self):
        print __name__ + ' : reading all settings from instrument'
        for i in range(1,9):
            self._dacvalue[i-1] = self._do_get_dacvalue(i)
   
#### communication with machine

    def _do_get_dacvalue(self,dacnr,hard=True):
        if hard:
            print __name__ + ' : reading dac %i value from instrument' % dacnr
            self._dacvalue[dacnr-1]=self._dummy_dacvalue[dacnr-1]
            return self._dacvalue[dacnr-1]
        else:
            print __name__ + ' : reading dac %i value from instrument' % dacnr
            return self._dacvalue[dacnr-1]

    def _do_set_dacvalue(self,dacnr,value):
        print __name__ + ' : setting dac %i to %f' % (dacnr,value)
        self._dacvalue[dacnr-1] = value
        self._do_get_dacvalue(dacnr)
