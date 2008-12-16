# 82_tune_window.py, window to tune instrument parameter
# Reinier Heeres, <reinier@heeres.eu>, 2008
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk
import gobject
import qt

from gettext import gettext as _

from packages.flexscale import FlexScale
from packages import dropdowns

class QTTune(QTWindow):

    def __init__(self):
        QTWindow.__init__(self, 'Tune')
        self.connect("delete-event", self._delete_event_cb)

        self._ins_combo = dropdowns.InstrumentDropdown()
        self._ins_combo.connect('changed', self._instrument_changed_cb)

        self._param_combo = dropdowns.InstrumentParameterDropdown()
        self._param_combo.connect('changed', self._parameter_changed_cb)

        self._get_but = gtk.Button('Get')
        self._get_but.connect('clicked', self._get_param_clicked_cb)
        self._param_edit = gtk.Entry()
        self._set_but = gtk.Button('Set')
        self._set_but.connect('clicked', self._set_param_clicked_cb)
        param_getset = pack_hbox([self._get_but, self._param_edit, self._set_but])

        self._function_combo = dropdowns.InstrumentFunctionDropdown()
        self._function_combo.connect('changed', self._function_changed_cb)

        self._call_but = gtk.Button('Call')
        self._call_but.connect('clicked', self._call_function_clicked_cb)

        self._spin_but = FlexScale(-10, 10, scaling=FlexScale.SCALE_SQRT)
        self._coarse_slider = gtk.VScale()
        self._coarse_slider.set_size_request(50, 100)
        self._coarse_slider.set_range(-10, 10)
        self._fine_slider = gtk.VScale()
        self._fine_slider.set_range(-1, 1)
        controls = pack_hbox([
            self._spin_but,
            self._coarse_slider,
            self._fine_slider])

        h1 = pack_hbox([
            gtk.Label(_('Instrument')),
            self._ins_combo])
        h2 = pack_hbox([
            gtk.Label(_('Parameter')),
            self._param_combo])
        h3 = pack_hbox([
            gtk.Label(_('Function')),
            self._function_combo])

        self._vbox = pack_vbox([h1, h2, param_getset, h3, self._call_but, controls], False, False)

        self._vbox.show_all()
        self.add(self._vbox)
 
    def _delete_event_cb(self, widget, event, data=None):
        print 'Hiding tune window, use showtune() to get it back'
        self.hide()
        return True

    def _instrument_changed_cb(self, widget):
        ins = self._ins_combo.get_instrument()
        self._param_combo.set_instrument(ins)
        self._function_combo.set_instrument(ins)

    def _parameter_changed_cb(self, widget):
        param = self._param_combo.get_parameter()

    def _function_changed_cb(self, widget):
        func = self._function_combo.get_function()

    def _get_param_clicked_cb(self, widget):
        ins = self._ins_combo.get_instrument()

        param = self._param_combo.get_parameter()
        val = ins.get(param)

        self._param_edit.set_text('%s' % val)

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
    get_tunewin().show_all()

def hidetune():
    get_tunewin().hide_all()

try:
    qt.tunewin
except:
    qt.tunewin = QTTune()

def get_tunewin():
    return qt.tunewin

if __name__ == "__main__":
    gtk.main()

