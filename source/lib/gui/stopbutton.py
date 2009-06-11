import gtk
from gettext import gettext as _L
import qt

class StopButton(gtk.Button):

    def __init__(self):
        gtk.Button.__init__(self, _L('Stop'))

        self.set_sensitive(qt.flow.is_measuring())
        self.connect('clicked', self._toggle_stop_cb)

        qt.flow.connect('measurement-start', self._measurement_start_cb)
        qt.flow.connect('measurement-end', self._measurement_end_cb)

    def _toggle_stop_cb(self, sender):
        qt.flow.set_abort()

    def _measurement_start_cb(self, widget):
        self.set_sensitive(True)

    def _measurement_end_cb(self, widget):
        self.set_sensitive(False)

class PauseButton(gtk.ToggleButton):

    def __init__(self):
        gtk.ToggleButton.__init__(self)

        self.set_active(False)
        self.set_pause(False)
        self.set_sensitive(qt.flow.is_measuring())
        self.connect('clicked', self._toggle_cb)

        qt.flow.connect('measurement-start', self._measurement_start_cb)
        qt.flow.connect('measurement-end', self._measurement_end_cb)

    def set_pause(self, pause):
        self._pause = pause
        if pause:
            self.set_label(_L('Continue'))
        else:
            self.set_label(_L('Pause'))
        qt.flow.set_pause(self._pause)

    def _toggle_cb(self, sender):
        self.set_pause(not self._pause)

    def _measurement_start_cb(self, widget):
        self.set_sensitive(True)

    def _measurement_end_cb(self, widget):
        self.set_sensitive(False)
        self.set_pause(False)

