import time
import gobject

gobject.threads.init()
import threading

class Measurement(gobject.GObject):

    def __init__(self):
        gobject.GObject.__init__(self)

    def emit(self, *args):
        gobject.idle_add(gobject.GObject.emit, self, *args)

    def start(self, func=None):
        if func is None:
            return False
        
    def stop(self):
        pass

    def new_data(self, data):
        self.emit('new-data', data)

class Measurements(gobject.GObject):

    def __init__(self):
        pass



measurements = Measurements()
