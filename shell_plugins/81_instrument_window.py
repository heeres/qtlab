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

from gettext import gettext as _L

import qt
from packages import dropdowns

class QTAddInstrumentFrame(gtk.Frame):

    def __init__(self, **kwargs):
        gtk.Frame.__init__(self, **kwargs)

        self._instruments = qt.instruments

        self.set_label(_L('Add instrument'))

        name_label = gtk.Label(_L('Name'))
        self._name_entry = gtk.Entry()
        self._name_entry.connect('changed', self._name_changed_cb)

        type_label = gtk.Label(_L('Type'))
        self._type_dropdown = dropdowns.InstrumentTypeDropdown()
        self._type_dropdown.connect('changed', self._dropdown_changed_cb)
        self._add_button = gtk.Button(_L('Add'))
        self._add_button.connect('clicked', self._add_clicked_cb)
        self._add_button.set_sensitive(False)

        self._argument_table = gtk.Table(2, 2)
        self._argument_table.attach(name_label, 0, 1, 0, 1)
        self._argument_table.attach(self._name_entry, 1, 2, 0, 1)
        self._argument_table.attach(type_label, 0, 1, 1, 2)
        self._argument_table.attach(self._type_dropdown, 1, 2, 1, 2)
        self._argument_info = {}

        self.add(pack_vbox([
                self._argument_table,
                self._add_button
            ], False, False))

        self.show_all()

    def _dropdown_changed_cb(self, widget):
        type_name = self._type_dropdown.get_typename()
        if type_name is None:
            args = None
        else:
            args = self._instruments.get_type_arguments(type_name)
        self._set_type_arguments(args)

        self._update_add_button_sensitivity()

    def _remove_arguments(self):
        for name, info in self._argument_info.iteritems():
            self._argument_table.remove(info['label'])
            self._argument_table.remove(info['entry'])

        self._argument_info = {}

    def _set_type_arguments(self, args):
        self._remove_arguments()
        if args is None:
            return

        i = -1
        rows = 0
        arg_names = args[0]
        defaults = args[3]
        for name in arg_names:
            i += 1
            if name in ('self', 'name'):
                continue
            rows += 1

            label = gtk.Label(name)
            entry = gtk.Entry()
            if defaults is not None and i >= len(arg_names) - len(defaults):
                entry.set_text(str(defaults[i - len(arg_names) + len(defaults)]))

            self._argument_info[name] = {'label': label, 'entry': entry}
            self._argument_table.resize(rows + 2, 2)
            self._argument_table.attach(label, 0, 1, rows + 2, rows + 3)
            self._argument_table.attach(entry, 1, 2, rows + 2, rows + 3)

        self.show_all()

    def _add_clicked_cb(self, widget):
        name = self._name_entry.get_text()
        typename = self._type_dropdown.get_typename()
        args = {}
        for param, info in self._argument_info.iteritems():
            value = info['entry'].get_text()
            try:
                value = eval(value)
            except:
                pass

            if value == '':
                value = None
            args[param] = value

        logging.debug("Creating %s as %s, **args: %r", name, typename, args)
        ins = qt.instruments.create(name, typename, **args)
        if ins is not None:
            self._name_entry.set_text('')
            self._type_dropdown.select_none_type()

    def _name_changed_cb(self, widget):
        self._update_add_button_sensitivity()

    def _update_add_button_sensitivity(self):
        typename = self._type_dropdown.get_typename()
        namelen = len(self._name_entry.get_text())

        if typename is not None and typename != '' and namelen > 0:
            self._add_button.set_sensitive(True)
        else:
            self._add_button.set_sensitive(False)

class QTInstrumentFrame(gtk.Frame):

    def __init__(self, ins, show_range, show_rate, **kwargs):
        gtk.Frame.__init__(self, **kwargs)

        self.set_label(ins.get_name())

        self._tips = gtk.Tooltips()
        self._tips.enable()

        self._instrument = ins
        self._label_name = {}
        self._label_val = {}
        self._label_range = {}
        self._label_rate = {}
        self._update_dict = {}

        self._add_parameters()

        ins.connect('parameter-added', self._parameter_added_cb)
        ins.connect('parameter-changed', self._parameter_changed_cb)

        self.show()
        self.show_range_column(show_range)
        self.show_rate_column(show_rate)

        # Update variables twice per second
        gobject.timeout_add(500, self._do_update_parameters_timer)

    def _add_parameter_by_name(self, param):
        popts = self._instrument.get_parameter_options(param)

        if 'doc' in popts:
            plabel = gtk.Label(param + ' [?]')
            self._tips.set_tip(plabel, popts['doc'])
        else:
            plabel = gtk.Label(param)

        plabel.set_justify(gtk.JUSTIFY_RIGHT)
        plabel.show()
        self._name_box.pack_start(plabel, False, False)

        vlabel = gtk.Label(self._instrument.format_parameter_value(param,
            self._instrument.get(param, query=False)))
        vlabel.set_justify(gtk.JUSTIFY_LEFT)
        vlabel.show()
        self._val_box.pack_start(vlabel, False, False)

        self._add_range_info(param, popts)
        self._add_rate_info(param, popts)

        self._label_name[param] = plabel
        self._label_val[param] = vlabel

    def _add_range_info(self, param, popts):
        text = self._instrument.format_range(param)
        rlabel = gtk.Label(text)
        rlabel.set_justify(gtk.JUSTIFY_LEFT)
        rlabel.show()
        self._range_box.pack_start(rlabel, False, False)

        self._label_range[param] = rlabel

    def _add_rate_info(self, param, popts):
        text = self._instrument.format_rate(param)
        rlabel = gtk.Label(text)
        rlabel.set_justify(gtk.JUSTIFY_LEFT)
        rlabel.show()
        self._rate_box.pack_start(rlabel, False, False)

        self._label_rate[param] = rlabel

    def _add_parameters(self):
        self._name_box = gtk.VBox()
        self._name_box.show()
        self._val_box = gtk.VBox()
        self._val_box.show()
        self._range_box = gtk.VBox()
        self._range_box.show()
        self._rate_box = gtk.VBox()
        self._rate_box.hide()

        parameters = self._instrument.get_parameter_names()
        parameters.sort()
        for param in parameters:
            self._add_parameter_by_name(param)

        hbox = pack_hbox([self._name_box, self._val_box, self._range_box,
            self._rate_box])
        hbox.set_border_width(1)
        hbox.show()
        self.add(hbox)

        self.show()

    def _parameter_added_cb(self, sender, name):
        self._add_parameter_by_name(name)

    def _do_update_parameters_timer(self):
        gtk.gdk.threads_enter()

        for param, val in self._update_dict.iteritems():
            if param in self._label_val:
                self._label_val[param].set_text(
                    self._instrument.format_parameter_value(param, val))

        self._update_dict = {}

        gtk.gdk.threads_leave()

        return True

    def update_parameter(self, param, val):
        """
        Set parameter to be updated on next refresh.
        """

        self._update_dict[param] = val

    def get_instrument(self):
        return self._instrument

    def show_range_column(self, show):
        if not show:
            self._range_box.hide()
        else:
            self._range_box.show()

    def show_rate_column(self, show):
        if not show:
            self._rate_box.hide()
        else:
            self._rate_box.show()

    def _parameter_changed_cb(self, sender, param):
        if param not in self._label_range:
            return False

        self._label_range[param].set_text(self._instrument.format_range(param))
        self._label_rate[param].set_text(self._instrument.format_rate(param))

class QTInstruments(QTWindow):

    def __init__(self):
        QTWindow.__init__(self, 'Instruments')

        self.connect("delete-event", self._delete_event_cb)

        self._instruments = qt.instruments

        qt.instruments.connect('instrument-added', self._instrument_added_cb)
        qt.instruments.connect('instrument-removed', self._instrument_removed_cb)
        qt.instruments.connect('instrument-changed', self._instrument_changed_cb)

        self._tags_dropdown = dropdowns.TagsDropdown()
        self._tags_dropdown.connect('changed', self._tag_changed_cb)
        self._tags_dropdown.show()

        self._vbox = gtk.VBox()
        self._vbox.set_border_width(4)
        self._vbox.pack_start(pack_hbox([
            gtk.Label(_L('Types')),
            self._tags_dropdown]), False, False)

        self._range_toggle = gtk.ToggleButton(_L('Range'))
        self._range_toggle.set_active(True)
        self._range_toggle.connect('toggled', self._range_toggled_cb)
        self._rate_toggle = gtk.ToggleButton(_L('Rate'))
        self._rate_toggle.set_active(False)
        self._rate_toggle.connect('toggled', self._rate_toggled_cb)

        self._vbox.pack_start(pack_hbox([
            self._range_toggle,
            self._rate_toggle], True, True))

        self._ins_widgets = {}
        self._add_instruments()

        self._scrolled_win = gtk.ScrolledWindow()
        self._scrolled_win.show()
        self._scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._scrolled_win.add_with_viewport(self._vbox)

        self._add_instrument_frame = QTAddInstrumentFrame()

        self._notebook = gtk.Notebook()
        self._notebook.append_page(self._scrolled_win,
            gtk.Label(_L('Info')))
        self._notebook.append_page(self._add_instrument_frame,
            gtk.Label(_L('Create')))
        self._notebook.show_all()
        self.add(self._notebook)

    def _add_instrument(self, ins):
        name = ins.get_name()
        self._ins_widgets[name] = QTInstrumentFrame(ins,
            self._range_toggle.get_active(),
            self._rate_toggle.get_active())
        self._vbox.pack_start(self._ins_widgets[name], False, False)

    def _remove_instrument(self, insname):
        if insname in self._ins_widgets:
            self._vbox.remove(self._ins_widgets[insname])
            del self._ins_widgets[insname]

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

    def _instrument_removed_cb(self, sender, insname):
        self._remove_instrument(insname)

    def _instrument_changed_cb(self, sender, instrument, changes):
        self._update_instrument(instrument, changes)

    def _tag_changed_cb(self, sender):
        tag = self._tags_dropdown.get_active_text()
        for name, widget in self._ins_widgets.iteritems():
            ins = widget.get_instrument()
            if tag == 'All' or tag in ins.get_tags():
                widget.show()
            else:
                widget.hide()

    def _range_toggled_cb(self, sender):
        state = self._range_toggle.get_active()
        for name, widget in self._ins_widgets.iteritems():
            widget.show_range_column(state)

    def _rate_toggled_cb(self, sender):
        state = self._rate_toggle.get_active()
        for name, widget in self._ins_widgets.iteritems():
            widget.show_rate_column(state)

try:
    qt.inswin
except:
    qt.inswin = QTInstruments()

def showinstruments():
    get_inswin().show()

def hideinstruments():
    get_inswin().hide()

def get_inswin():
    return qt.inswin

if __name__ == "__main__":
    gtk.main()

