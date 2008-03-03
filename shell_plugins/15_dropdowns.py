import gtk

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

class InstrumentDropdown(gtk.ComboBoxEntry):

    def __init__(self):
        self._ins_list = gtk.ListStore(gobject.TYPE_STRING)
        gtk.ComboBoxEntry.__init__(self, model=self._ins_list)

        global instruments
        self._instruments = instruments
        self._instruments.connect('instrument-added', self._instrument_added_cb)
        self._instruments.connect('instrument-removed', self._instrument_removed_cb)
        self._instruments.connect('instrument-changed', self._instrument_changed_cb)

    def _instrument_added_cb(self, sender, instrument):
        self._ins_list.append([instrument])

    def _instrument_removed_cb(self, sender, instrument):
        print 'Instrument removed: %s' % instrument

        i = self._ins_list.get_iter_root()
        while i:
            if self._ins_list.get_value(i, 0) == instrument:
                self._ins_list.remove(i)
                break
            i = self._ins_list.iter_next(i)


    def _instrument_changed_cb(self, sender, instrument, property, value):
        print 'Instrument changed: %s' % instrument

    def get_instrument(self):
        try:
            item = self.get_active_iter()
            ins_name = self._ins_list.get(item, 0)
            return self._instruments[ins_name]
        except:
            return None

class InstrumentParameterDropdown(gtk.ComboBoxEntry):

    def __init__(self, instrument=None, flags=Instrument.FLAG_GETSET):
        self._param_list = gtk.ListStore(gobject.TYPE_STRING)
        gtk.ComboBoxEntry.__init__(self, model=self._param_list)

        self._instrument = instrument
        self._flags = flags

        global instruments
        self._instruments = instruments
        self._instruments.connect('instrument-removed', self._instrument_removed_cb)

    def set_flags(self, flags):
        if flags != self._flags:
            ins = self._instrument
            self.set_instrument(None)
            self.set_instrument(ins)

    def _instrument_removed_cb(self, sender, instrument):
        if instrument == self._instrument:
            print 'Instrument for dropdown removed: %s' % instrument
            self.set_instrument(None)

    def _instrument_changed_cb(self, sender, instrument, property, value):
        print 'Instrument changed: %s' % instrument

    def set_instrument(self, ins):
        if type(ins) == types.StringType:
            global instruments
            ins = instruments[ins]

        if self._instrument == ins:
            return True

        self._instrument = ins
        self._param_list.clear()
        if ins is not None:
            params = ins.get_parameters()
            for name, options in params.iteritems():
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

class InstrumentFunctionDropdown(gtk.ComboBoxEntry):

    def __init__(self, instrument=None):
        self._func_list = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        gtk.ComboBoxEntry.__init__(self, model=self._func_list)

        self._instrument = instrument

        global instruments
        self._instruments = instruments
        self._instruments.connect('instrument-removed', self._instrument_removed_cb)

    def _instrument_removed_cb(self, sender, instrument):
        if instrument == self._instrument:
            print 'Instrument for dropdown removed: %s' % instrument
            self.set_instrument(None)

    def _instrument_changed_cb(self, sender, instrument, property, value):
        print 'Instrument changed: %s' % instrument

    def set_instrument(self, ins):
        if type(ins) == types.StringType:
            global instruments
            ins = instruments[ins]

        if self._instrument == ins:
            return True

        self._instrument = ins
        self._func_list.clear()
        if ins is not None:
            funcs = ins.get_functions()
            for (name, options) in funcs.iteritems():
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

