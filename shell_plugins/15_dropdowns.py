# 15_dropdowns.py, dropdown support for Instruments
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

import qt

def pack_hbox(items, expand=True, fill=True):
    hbox = gtk.HBox()
    for i in items:
        hbox.pack_start(i, expand, fill)
#        hbox.pack_start(i)
    return hbox

def pack_vbox(items, expand=True, fill=True):
    vbox = gtk.VBox()
    for i in items:
        vbox.pack_start(i, expand, fill)
#        vbox.pack_start(i)
    return vbox

class QTComboBox(gtk.ComboBox):

    def __init__(self, model):
        gtk.ComboBox.__init__(self, model=model)
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)

class InstrumentDropdown(QTComboBox):
    '''
    Dropdown to select an instrument.
    '''

    def __init__(self, types=[]):
        self._ins_list = gtk.ListStore(gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._ins_list)

        self._types = types
        self._ins_list.append(['<None>'])
        self._instruments = qt.instruments
        for name, ins in self._instruments.get_instruments().iteritems():
            if len(types) == 0 or ins.has_tag(types):
                self._ins_list.append([ins.get_name()])

        self._instruments.connect('instrument-added', self._instrument_added_cb)
        self._instruments.connect('instrument-removed', self._instrument_removed_cb)
        self._instruments.connect('instrument-changed', self._instrument_changed_cb)

    def _instrument_added_cb(self, sender, instrument):
        if len(self._types) == 0 or instrument.has_tag(self._types):
            self._ins_list.append([instrument.get_name()])

    def _instrument_removed_cb(self, sender, insname):
        logging.debug('Instrument removed: %s', insname)

        i = self._ins_list.get_iter_root()
        while i:
            if self._ins_list.get_value(i, 0) == insname:
                self._ins_list.remove(i)
                break
            i = self._ins_list.iter_next(i)


    def _instrument_changed_cb(self, sender, instrument, changes):
        return

    def get_instrument(self):
        try:
            item = self.get_active_iter()
            ins_name = self._ins_list.get(item, 0)
            return self._instruments[ins_name]
        except:
            return None

class InstrumentTypeDropdown(QTComboBox):
    '''
    Dropdown to select an instrument type.
    '''

    def __init__(self):
        self._type_list = gtk.ListStore(gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._type_list)

        self._type_list.append(['<None>'])
        for name in qt.instruments.get_types():
            self._type_list.append([name])

    def get_typename(self):
        try:
            item = self.get_active_iter()
            type_name = self._type_list.get(item, 0)
            if type_name[0] == '<None>':
                return None
            else:
                return type_name[0]

        except:
            return None

    def select_none_type(self):
        self.set_active(0)

class InstrumentParameterDropdown(QTComboBox):
    '''
    Dropdown to select a parameter from a given instrument.
    '''

    def __init__(self, instrument=None, flags=Instrument.FLAG_GETSET, types=[]):
        self._param_list = gtk.ListStore(gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._param_list)

        self._instrument = None
        self._insname = ''
        self.set_instrument(instrument)

        self._flags = flags
        self._types = types

        self._instruments = qt.instruments
        self._instruments.connect('instrument-removed', self._instrument_removed_cb)

    def set_flags(self, flags):
        if flags != self._flags:
            ins = self._instrument
            self.set_instrument(None)
            self.set_instrument(ins)

    def set_types(self, types):
        if self._types != types:
            self._types = types
            return self.update_list()

    def _instrument_removed_cb(self, sender, insname):
        if insname == self._instrument:
            logging.debug('Instrument for dropdown removed: %s', instrument)
            self.set_instrument(None)

    def _parameter_added_cb(self, sender, param):
        #FIXME: this needs to be improved
        ins = self._instrument
        self.set_instrument(None)
        self.set_instrument(ins)

    def set_instrument(self, ins):
        if type(ins) == types.StringType:
            ins = qt.instruments[ins]

        if self._instrument == ins:
            return True

        if ins is not None:
            self._insname = ins.get_name()
        else:
            self._insname = ''

        self._instrument = ins
        self._param_list.clear()
        if ins is not None:
            self._param_list.append(['<None>'])

            self._instrument.connect('parameter-added', self._parameter_added_cb)

            for (name, options) in dict_to_ordered_tuples(ins.get_parameters()):
                if len(self._types) > 0 and options['type'] not in self._types:
                    continue

                if options['flags'] & self._flags:
                    self._param_list.append([name])
        else:
            self._param_list.clear()

    def get_parameter(self):
        try:
            item = self.get_active_iter()
            param_name = self._param_list.get(item, 0)

            # FIXME: What is going on here?!
            return param_name[0]
        except:
            return None

class InstrumentFunctionDropdown(QTComboBox):
    '''
    Dropdown to select a function from a given instrument.
    '''

    def __init__(self, instrument=None):
        self._func_list = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._func_list)

        self._instrument = None
        self._insname = ''
        self.set_instrument(instrument)

        self._instruments = qt.instruments
        self._instruments.connect('instrument-removed', self._instrument_removed_cb)

    def _instrument_removed_cb(self, sender, insname):
        if insname == self._insname:
            logging.debug('Instrument for dropdown removed: %s', insname)
            self.set_instrument(None)

    def _instrument_changed_cb(self, sender, instrument, property, value):
        return

    def set_instrument(self, ins):
        if type(ins) == types.StringType:
            ins = qt.instruments[ins]

        if self._instrument == ins:
            return True

        if ins is not None:
            self._insname = ins.get_name()
        else:
            self._insname = ''

        self._instrument = ins
        self._func_list.clear()
        if ins is not None:
            self._func_list.append(['<None>', '<Nothing>'])

            funcs = ins.get_functions()
            for (name, options) in dict_to_ordered_tuples(funcs):
                if 'doc' in options:
                    doc = options['doc']
                else:
                    doc = ''
                self._func_list.append([name, doc])
        else:
            self._func_list.clear()

    def get_function(self):
        try:
            item = self.get_active_iter()
            func_name = self._func_list.get(item, 0)
            return func_name[0]
        except:
            return None

class AllParametersDropdown(QTComboBox):
    '''
    Dropdown to select a parameter from any instrument.
    '''

    def __init__(self, flags=Instrument.FLAG_GETSET, types=[], tags=[]):
        self._param_list = gtk.ListStore(gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._param_list)

        self._flags = flags
        self._types = types
        self._tags = tags
        self._parameter_added_hids = {}
        self.update_list()

        self._instruments = qt.instruments
        self._instruments.connect('instrument-added', self._instrument_added_cb)
        self._instruments.connect('instrument-removed', self._instrument_removed_cb)
        self._instruments.connect('instrument-changed', self._instrument_changed_cb)

    def _instrument_added_cb(self, sender, instrument):
        self.update_list()

    def _instrument_removed_cb(self, sender, instrument):
        self.update_list()

    def _instrument_changed_cb(self, sender, instrument, changes):
        return

    def set_flags(self, flags):
        if self._flags != flags:
            self._flags = flags
            return self.update_list()

    def set_types(self, types):
        if self._types != types:
            self._types = types
            return self.update_list()

    def set_tags(self, tags):
        if self._tags != tags:
            self._tags = tags
            return self.update_list()

    def update_list(self):
        self._param_list.clear()
        self._param_list.append(['<None>'])

        for ins, hid in self._parameter_added_hids.iteritems():
            if ins.handler_is_connected(hid):
                ins.disconnect(hid)

        inslist = dict_to_ordered_tuples(qt.instruments.get_instruments())
        for (insname, ins) in inslist:
            self._parameter_added_hids[ins] = ins.connect('parameter-added',
                self._parameter_added_cb)

            params = dict_to_ordered_tuples(ins.get_parameters())
            for (varname, options) in params:

                if len(self._tags) > 0:
                    tag_ok = False
                    for tag in self._tags:
                        if tag in options['tags']:
                            tag_ok = True
                            break
                else:
                    tag_ok = True

                if options['flags'] & self._flags and tag_ok:
                    add_name = '%s.%s' % (insname, varname)
                    self._param_list.append([add_name])

    def get_selection(self):
        try:
            selstr = self.get_active_text()
            if selstr == '':
                return None

            insname, dot, parname = selstr.partition('.')
            logging.debug('Selected instrument %s, parameter %s', insname, parname)

            ins = self._instruments[insname]
            if ins is None:
                return None

            return ins, parname

        except Exception, e:
            return None

    def _parameter_added_cb(self, sender, param):
        self.update_list()

class TagsDropdown(QTComboBox):

    def __init__(self):
        self._tags = gtk.ListStore(gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._tags)

        self._instruments = qt.instruments
        self._instruments.connect('tags-added', self._tags_added_cb)

        for i in self._instruments.get_tags():
            self._tags.append([i])

    def _tags_added_cb(self, sender, tags):
        for tag in tags:
            self._tags.append([tag])
