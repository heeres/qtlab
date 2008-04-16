import gtk
import gobject

from gettext import gettext as _

class QTInstrumentFrame(gtk.Frame):

    def __init__(self, ins, **kwargs):
        gtk.Frame.__init__(self, **kwargs)

        self.set_label(ins.get_name())

        self._instrument = ins
        self._parameters = {}
        self._add_parameters()

    def _add_parameters(self):
        self._left_box = gtk.VBox()
        self._right_box = gtk.VBox()
        for (param, popts) in self._instrument.get_parameters().iteritems():
            plabel = gtk.Label(param)
            plabel.set_justify(gtk.JUSTIFY_RIGHT)
            self._left_box.pack_start(plabel, False, False)

            vlabel = gtk.Label('%s' % self._instrument.get(param, query=False))
            vlabel.set_justify(gtk.JUSTIFY_LEFT)
            self._right_box.pack_start(vlabel, False, False)

            self._parameters[param] = vlabel

        self.add(pack_hbox([self._left_box, self._right_box]))

    def update_parameter(self, param, val):
        if param in self._parameters:
            self._parameters[param].set_text('%s' % val)

class QTInstruments(QTWindow):

    def __init__(self):
        QTWindow.__init__(self, 'Instruments')

        self.connect("delete-event", self._delete_event_cb)

        global instruments
        self._instruments = instruments

        instruments.connect('instrument-added', self._instrument_added_cb)
        instruments.connect('instrument-removed', self._instrument_removed_cb)
        instruments.connect('instrument-changed', self._instrument_changed_cb)

        self._vbox = gtk.VBox()
        self._vbox.set_border_width(4)
        self._ins_widgets = {}
        self._add_instruments()

        self._scrolled_win = gtk.ScrolledWindow()
        self._scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._scrolled_win.add_with_viewport(self._vbox)
        self.add(self._scrolled_win)

    def _add_instrument(self, ins):
        name = ins.get_name()
        self._ins_widgets[name] = QTInstrumentFrame(ins)
        self._vbox.pack_start(self._ins_widgets[name], False, False)

    def _remove_instrument(self, ins):
        name = ins.get_name()
        if name in self._ins_widgets:
            self._vbox.remove(self._ins_widgets[name])
            del self._ins_widgets[name]

    def _update_instrument(self, ins, changes):
        name = ins.get_name()
        if name in self._ins_widgets:
            for (param, val) in changes.iteritems():
                self._ins_widgets[name].update_parameter(param, val)

    def _add_instruments(self):
        for (name, ins) in self._instruments.get_instruments():
            self._add_instrument(ins)

    def _delete_event_cb(self, widget, event, data=None):
        print 'Hiding instruments window, use showinstruments() to get it back'
        self.hide()
        return True

    def _instrument_added_cb(self, sender, instrument):
        self._add_instrument(instrument)

    def _instrument_removed_cb(self, sender, instrument):
        self._remove_instrument(instrument)

    def _instrument_changed_cb(self, sender, instrument, changes):
        self._update_instrument(instrument, changes)

def showinstruments():
    global _inswin
    _inswin.show()

def hideinstruments():
    global _inswin
    _inswin.hide()

_inswin = QTInstruments()

def get_inswin():
    global _inswin
    return _inswin

if __name__ == "__main__":
    gtk.main()

