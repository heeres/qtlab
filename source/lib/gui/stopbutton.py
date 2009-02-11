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

