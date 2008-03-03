import gtk
import gobject

from gettext import gettext as _

class QTTune(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.move(210, 210)

        self.set_size_request(500, 150)
        self.set_border_width(1)
        self.set_title(_('Tune'))

        self.connect("delete-event", self._delete_event_cb)

        self._ins_combo = InstrumentDropdown()
        self._ins_combo.connect('changed', self._instrument_changed_cb)

        self._param_combo = InstrumentParameterDropdown()
        self._param_combo.connect('changed', self._parameter_changed_cb)

        self._get_but = gtk.Button('Get')
        self._get_but.connect('clicked', self._get_param_clicked_cb)
        self._param_edit = gtk.Entry()
        self._set_but = gtk.Button('Set')
        self._set_but.connect('clicked', self._set_param_clicked_cb)
        param_getset = pack_hbox([self._get_but, self._param_edit, self._set_but])

        self._function_combo = InstrumentFunctionDropdown()
        self._function_combo.connect('changed', self._function_changed_cb)

        self._call_but = gtk.Button('Call')
        self._call_but.connect('clicked', self._call_function_clicked_cb)

        h1 = pack_hbox([
            gtk.Label(_('Instrument')),
            self._ins_combo])
        h2 = pack_hbox([
            gtk.Label(_('Parameter')),
            self._param_combo])
        h3 = pack_hbox([
            gtk.Label(_('Function')),
            self._function_combo])
        self.add(pack_vbox([h1, h2, param_getset, h3, self._call_but], False, False))

        self.show_all()

    def _delete_event_cb(self, widget, event, data=None):
        print 'Hiding tune window, use showtune() to get it back'
        self.hide()
        return True

    def _instrument_changed_cb(self, widget):
        ins = self._ins_combo.get_instrument()
        self._param_combo.set_instrument(ins)
        self._function_combo.set_instrument(ins)
        print 'Selected instrument: %s' % (ins)

    def _parameter_changed_cb(self, widget):
        param = self._param_combo.get_parameter()
        print 'Selected parameter %s' % (param)

    def _function_changed_cb(self, widget):
        func = self._function_combo.get_function()
        print 'Selected function %s' % (func)

    def _get_param_clicked_cb(self, widget):
        ins = self._ins_combo.get_instrument()

        param = self._param_combo.get_parameter()
        val = ins.get(param)
        print 'Param: %r, val: %r' % (param, val)

        self._param_edit.set_text('%r' % val)

    def _set_param_clicked_cb(self, widget):
        ins = self._ins_combo.get_instrument()

        param = self._param_combo.get_parameter()
        val = self._param_edit.get_text()

        ins.set(param, val)

    def _call_function_clicked_cb(self, widget):
        ins = self._ins_combo.get_instrument()
        funcname = self._function_combo.get_function()
        ins.call(funcname)

def showtune():
    global _tunewin
    _tunewin.show()

_tunewin = QTTune()
if __name__ == "__main__":
    gtk.main()

