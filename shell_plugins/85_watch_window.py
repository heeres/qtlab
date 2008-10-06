# 85_watch_window.py, window to watch one or more instrument parameters
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

from gettext import gettext as _L

from qttable import QTTable
from packages import dropdowns

class QTWatch(QTWindow):

    def __init__(self):
        QTWindow.__init__(self, 'Watch')
        self.connect("delete-event", self._delete_event_cb)

        self._watch = {}

        self._frame = gtk.Frame()
        self._frame.set_label(_L('Add variable'))

        self._ins_combo = dropdowns.InstrumentDropdown()
        self._ins_combo.connect('changed', self._instrument_changed_cb)

        self._param_combo = dropdowns.InstrumentParameterDropdown()
        self._param_combo.connect('changed', self._parameter_changed_cb)

        self._interval = gtk.SpinButton(climb_rate=1, digits=0)
        self._interval.set_range(10, 100000)
        self._interval.set_value(500)
        interval = pack_hbox([self._interval, gtk.Label('ms')], False, False)

        self._add_button = gtk.Button(_L('Add'))
        self._add_button.connect('clicked', self._add_clicked_cb)
        self._remove_button = gtk.Button(_L('Remove'))
        self._remove_button.connect('clicked', self._remove_clicked_cb)

        buttons = pack_hbox([self._add_button, self._remove_button], False, False)

        self._tree_model = gtk.ListStore(str, str, str)
        self._tree_view = QTTable([
            (_L('Parameter'), {}),
            (_L('Delay'), {}),
            (_L('Value'), {'scale': 3.0}),
            ], self._tree_model)

    	vbox = pack_vbox([
            self._ins_combo,
    		self._param_combo,
    		interval,
    		buttons,
    	], False, False)
        vbox.set_border_width(4)
        self._frame.add(vbox)

        vbox = pack_vbox([
            self._frame,
            self._tree_view,
        ], False, False)
        self.add(vbox)

        vbox.show_all()

    def _delete_event_cb(self, widget, event, data=None):
        print 'Hiding watch window, use showwatch() to get it back'
        self.hide()
        return True

    def _instrument_changed_cb(self, widget):
        ins = self._ins_combo.get_instrument()
        self._param_combo.set_instrument(ins)

    def _parameter_changed_cb(self, widget):
        param = self._param_combo.get_parameter()

    def _add_clicked_cb(self, widget):
        ins = self._ins_combo.get_instrument()
        param = self._param_combo.get_parameter()
        delay = int(self._interval.get_value())
        ins_param = ins.get_name() + "." + param
        if ins_param in self._watch:
            return

        iter = self._tree_model.append((ins_param, '%d ms' % delay, ''))
        info = {
            'instrument': ins,
            'parameter': param,
            'delay': delay,
            'iter': iter
        }
        hid = gobject.timeout_add(delay, lambda: self._get_value(info))

        self._watch[ins_param] = hid

    def _remove_clicked_cb(self, widget):
        (model, rows) = self._tree_view.get_selection().get_selected_rows()
        for row in rows:
            iter = model.get_iter(row)
            ins_param = model.get_value(iter, 0)
            model.remove(iter)

            gobject.source_remove(self._watch[ins_param])
            del self._watch[ins_param]

    def _get_value(self, info):
        if not (self.flags() & gtk.VISIBLE):
            return True

        ins = info['instrument']
        param = info['parameter']

        val = ins.get(param)
        strval = ins.format_parameter_value(param, val)
        self._tree_model.set(info['iter'], 2, strval)

        return True

def showwatch():
    get_watchwin().show_all()

def hidewatch():
    get_watchwin().hide_all()

try:
    qt.watchwin
except:
    qt.watchwin = QTWatch()

def get_watchwin():
    return qt.watchwin

if __name__ == "__main__":
    gtk.main()

