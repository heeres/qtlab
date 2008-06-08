# 81_instrument_window.py, window to monitor instruments
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

from gettext import gettext as _

import qt

class QTInstrumentFrame(gtk.Frame):

    def __init__(self, ins, **kwargs):
        gtk.Frame.__init__(self, **kwargs)

        self.set_label(ins.get_name())

        self._instrument = ins
        self._parameters = {}
        self._add_parameters()

        ins.connect('parameter-added', self._parameter_added_cb)

        self.show_all()

    def _add_parameter_by_name(self, param):
        popts = self._instrument.get_parameter_options(param)

        plabel = gtk.Label(param)
        plabel.set_justify(gtk.JUSTIFY_RIGHT)
        plabel.show()
        self._left_box.pack_start(plabel, False, False)

        vlabel = gtk.Label(self._instrument.format_parameter_value(param,
            self._instrument.get(param, query=False)))
        vlabel.set_justify(gtk.JUSTIFY_LEFT)
        vlabel.show()
        self._right_box.pack_start(vlabel, False, False)

        self._parameters[param] = vlabel

    def _add_parameters(self):
        self._left_box = gtk.VBox()
        self._right_box = gtk.VBox()

        parameters = self._instrument.get_parameter_names()
        parameters.sort()
        for param in parameters:
            self._add_parameter_by_name(param)

        self.add(pack_hbox([self._left_box, self._right_box]))

    def _parameter_added_cb(self, sender, name):
        self._add_parameter_by_name(name)

    def update_parameter(self, param, val):
        if param in self._parameters:
            self._parameters[param].set_text(
                self._instrument.format_parameter_value(param, val))

    def get_instrument(self):
        return self._instrument

class QTInstruments(QTWindow):

    def __init__(self):
        QTWindow.__init__(self, 'Instruments')

        self.connect("delete-event", self._delete_event_cb)

        self._instruments = qt.instruments

        qt.instruments.connect('instrument-added', self._instrument_added_cb)
        qt.instruments.connect('instrument-removed', self._instrument_removed_cb)
        qt.instruments.connect('instrument-changed', self._instrument_changed_cb)

        self._tags_dropdown = TagsDropdown()
        self._tags_dropdown.connect('changed', self._tag_changed_cb)

        self._vbox = gtk.VBox()
        self._vbox.set_border_width(4)
        self._vbox.pack_start(pack_hbox([
            gtk.Label(_('Types')),
            self._tags_dropdown]), False, False)

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

    def _tag_changed_cb(self, sender):
        tag = self._tags_dropdown.get_active_text()
        for name, widget in self._ins_widgets.iteritems():
            ins = widget.get_instrument()
            if tag == 'All' or tag in ins.get_tags():
                widget.show_all()
            else:
                widget.hide_all()

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

