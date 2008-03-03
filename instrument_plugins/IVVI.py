from instrument import Instrument

class IVVI(Instrument):

    def __init__(self, name):
        Instrument.__init__(self, name)

    def get(self, parameter):
        print 'Getting %s' % parameter
        return 'x'

    def set(self, parameter, value):
        print 'Setting %s to %s' % (parameter, value)
        return True
