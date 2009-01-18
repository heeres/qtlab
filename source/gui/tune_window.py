# tune_window.py, window to tune instrument parameter
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

import lib.gui as gui
from lib.gui.flexscale import FlexScale
from lib.gui import dropdowns, qtwindow

class TuneWindow(qtwindow.QTWindow):

    def __init__(self):
        qtwindow.QTWindow.__init__(self, 'tune', 'Tune')
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
        param_getset = gui.pack_hbox([self._get_but, self._param_edit, \
                self._set_but])

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
        controls = gui.pack_hbox([
            self._spin_but,
            self._coarse_slider,
            self._fine_slider])

        h1 = gui.pack_hbox([
            gtk.Label(_('Instrument')),
            self._ins_combo])
        h2 = gui.pack_hbox([
            gtk.Label(_('Parameter')),
            self._param_combo])
        h3 = gui.pack_hbox([
            gtk.Label(_('Function')),
            self._function_combo])

        self._vbox = gui.pack_vbox([h1, h2, param_getset, h3,
                self._call_but, controls], False, False)

        self._vbox.show_all()
        self.add(self._vbox)

    def _delete_event_cb(self, widget, event, data=None):
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

