# watch_window.py, window to watch one or more instrument parameters
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
import time
import qt

from gettext import gettext as _L

import lib.gui as gui
from lib.gui.qttable import QTTable
from lib.gui import dropdowns, qtwindow

import gobject
from lib.calltimer import GObjectThread

class WatchThread(GObjectThread):

    __gsignals__ = {
        'update': (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ([gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT])),
        'set-delay': (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ([gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT])),
    }

    def __init__(self, id, ins, var, delay):
        GObjectThread.__init__(self)

        self._id = id
        self._ins = ins
        self._var = var
        self._delay = delay

    def run(self):
        avgtime = self._delay

        while not self.stop.get():
            start = time.time()
            val = self._ins.get(self._var)
            stop = time.time()

            self.emit('update', self._id, val)

            # Update delay if we're querying too fast
            avgtime = avgtime * 0.9 + (stop - start) * 0.1
            if avgtime > self._delay:
                self._delay *= 2
                self.emit('set-delay', self._id, self._delay)

            delay = self._delay - (stop - start)
            if delay > 0:
                time.sleep(delay)

class WatchWindow(qtwindow.QTWindow):

    def __init__(self):
        qtwindow.QTWindow.__init__(self, 'watch', 'Watch')
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
        interval = gui.pack_hbox([self._interval, gtk.Label('ms')], \
                False, False)

        self._add_button = gtk.Button(_L('Add'))
        self._add_button.connect('clicked', self._add_clicked_cb)
        self._remove_button = gtk.Button(_L('Remove'))
        self._remove_button.connect('clicked', self._remove_clicked_cb)

        buttons = gui.pack_hbox([self._add_button, self._remove_button], \
                False, False)

        self._tree_model = gtk.ListStore(str, str, str)
        self._tree_view = QTTable([
            (_L('Parameter'), {}),
            (_L('Delay'), {}),
            (_L('Value'), {'scale': 3.0}),
            ], self._tree_model)

        vbox = gui.pack_vbox([
            self._ins_combo,
    		self._param_combo,
    		interval,
    		buttons,
    	], False, False)
        vbox.set_border_width(4)
        self._frame.add(vbox)

        vbox = gui.pack_vbox([
            self._frame,
            self._tree_view,
        ], False, False)
        self.add(vbox)

        vbox.show_all()

        qt.flow.connect('exit-request', self._exit_request_cb)

    def _delete_event_cb(self, widget, event, data=None):
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
        thread = WatchThread(ins_param, ins, param, delay / 1000.0)
        thread.connect('update', self._update_cb)
        thread.connect('set-delay', self._set_delay_cb)
        info = {
            'instrument': ins,
            'parameter': param,
            'delay': delay,
            'iter': iter,
            'thread': thread,
        }

        self._watch[ins_param] = info
        thread.start()

    def _update_cb(self, sender, ins_param, val):
        if not (self.flags() & gtk.VISIBLE):
            return

        if ins_param not in self._watch:
            return

        info = self._watch[ins_param]
        ins = info['instrument']
        param = info['parameter']
        strval = ins.format_parameter_value(param, val)
        self._tree_model.set(info['iter'], 2, strval)

    def _set_delay_cb(self, sender, ins_param, delay):
        info = self._watch[ins_param]
        strval = '%d ms' % (delay * 1000.0)
        self._tree_model.set(info['iter'], 1, strval)

    def _remove_clicked_cb(self, widget):
        (model, rows) = self._tree_view.get_selection().get_selected_rows()
        for row in rows:
            iter = model.get_iter(row)
            ins_param = model.get_value(iter, 0)
            model.remove(iter)

            thread = self._watch[ins_param]['thread']
            thread.stop.set(True)
            del self._watch[ins_param]

    def _exit_request_cb(self, sender):
        print 'Closing watch threads...'
        for ins_param, info in self._watch.iteritems():
            thread = info['thread']
            thread.stop.set(True)
        self._watch = {}

