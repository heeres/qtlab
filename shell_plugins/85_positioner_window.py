# 85_positioner_window.py, window to control a positioning instrument
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
import logging
import qt

from gettext import gettext as _L

from qttable import QTTable

class PositionControls(gtk.Frame):

    __gsignals__ = {
        'direction-clicked': (gobject.SIGNAL_RUN_FIRST,
                        gobject.TYPE_NONE,
                        ([gobject.TYPE_PYOBJECT])),
        'direction-released': (gobject.SIGNAL_RUN_FIRST,
                        gobject.TYPE_NONE,
                        ([gobject.TYPE_PYOBJECT])),
        'max-speed-changed': (gobject.SIGNAL_RUN_FIRST,
                        gobject.TYPE_NONE,
                        ([gobject.TYPE_PYOBJECT])),
        'min-speed-changed': (gobject.SIGNAL_RUN_FIRST,
                        gobject.TYPE_NONE,
                        ([gobject.TYPE_PYOBJECT])),
        'accel-changed': (gobject.SIGNAL_RUN_FIRST,
                        gobject.TYPE_NONE,
                        ([gobject.TYPE_PYOBJECT])),
        'decel-changed': (gobject.SIGNAL_RUN_FIRST,
                        gobject.TYPE_NONE,
                        ([gobject.TYPE_PYOBJECT])),
    }

    def __init__(self, ins):
        gtk.Frame.__init__(self)

        self.set_label(_L('Controls'))

        self._table = gtk.Table(3, 9)
        self._button_up = gtk.Button('/\\')
        self._button_up.connect('pressed', lambda x: self._direction_clicked(True, 0, 1, 0))
        self._button_up.connect('released', lambda x: self._direction_clicked(False, 0, 1, 0))
        self._table.attach(self._button_up, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, 0)
        self._button_down = gtk.Button('\\/')
        self._button_down.connect('pressed', lambda x: self._direction_clicked(True, 0, -1, 0))
        self._button_down.connect('released', lambda x: self._direction_clicked(False, 0, -1, 0))
        self._table.attach(self._button_down, 1, 2, 2, 3, gtk.EXPAND | gtk.FILL, 0)

        self._button_left = gtk.Button('<')
        self._button_left.connect('pressed', lambda x: self._direction_clicked(True, -1, 0, 0))
        self._button_left.connect('released', lambda x: self._direction_clicked(False, -1, 0, 0))
        self._table.attach(self._button_left, 0, 1, 1, 2, gtk.EXPAND | gtk.FILL, 0)
        self._button_right = gtk.Button('>')
        self._button_right.connect('pressed', lambda x: self._direction_clicked(True, 1, 0, 0))
        self._button_right.connect('released', lambda x: self._direction_clicked(False, 1, 0, 0))
        self._table.attach(self._button_right, 2, 3, 1, 2, gtk.EXPAND | gtk.FILL, 0)

        self._button_z_up = gtk.Button('/\\')
        self._button_z_up.connect('pressed', lambda x: self._direction_clicked(True, 0, 0, 1))
        self._button_z_up.connect('released', lambda x: self._direction_clicked(False, 0, 0, 1))
        self._table.attach(self._button_z_up, 4, 5, 0, 1, gtk.EXPAND | gtk.FILL, 0)
        self._button_z_down = gtk.Button('\/')
        self._button_z_down.connect('pressed', lambda x: self._direction_clicked(True, 0, 0, -1))
        self._button_z_down.connect('released', lambda x: self._direction_clicked(False, 0, 0, -1))
        self._table.attach(self._button_z_down, 4, 5, 2, 3, gtk.EXPAND | gtk.FILL, 0)

        self._max_speed = gtk.VScale()
        self._max_speed.set_size_request(100, 90)
        self._max_speed.set_range(1, 500)
        self._max_speed.set_inverted(True)
        self._max_speed.connect('value-changed', self._max_speed_changed_cb)
        self._max_speed.set_value(250)
        self._max_speed.set_digits(1)
        self._table.attach(gtk.Label(_L('Max speed')), 5, 6, 0, 1, 0, 0)
        self._table.attach(self._max_speed, 5, 6, 1, 3, 0, 0)

        self._min_speed = gtk.VScale()
        self._min_speed.set_size_request(100, 90)
        self._min_speed.set_range(1, 500)
        self._min_speed.set_inverted(True)
        self._min_speed.connect('value-changed', self._min_speed_changed_cb)
        self._min_speed.set_value(50)
        self._min_speed.set_digits(1)
        self._table.attach(gtk.Label(_L('Min speed')), 6, 7, 0, 1, 0, 0)
        self._table.attach(self._min_speed, 6, 7, 1, 3, 0, 0)

        self._accel = gtk.VScale()
        self._accel.set_size_request(100, 90)
        self._accel.set_range(1.1, 4.0)
        self._accel.set_inverted(True)
        self._accel.connect('value-changed', self._accel_changed_cb)
        self._accel.set_value(1.5)
        self._accel.set_digits(2)
        self._table.attach(gtk.Label(_L('Acceleration')), 7, 8, 0, 1, 0, 0)
        self._table.attach(self._accel, 7, 8, 1, 3, 0, 0)

        self._decel = gtk.VScale()
        self._decel.set_size_request(100, 90)
        self._decel.set_range(1.1, 4.0)
        self._decel.set_inverted(True)
        self._decel.connect('value-changed', self._decel_changed_cb)
        self._decel.set_value(2.0)
        self._decel.set_digits(2)
        self._table.attach(gtk.Label(_L('Deceleration')), 8, 9, 0, 1, 0, 0)
        self._table.attach(self._decel, 8, 9, 1, 3, 0, 0)

        self.connect('key-press-event', self._key_pressed_cb)
        self.connect('key-release-event', self._key_released_cb)

        self.add(self._table)

        self.set_instrument(ins)

    def set_instrument(self, ins):
        self._instrument = ins
        if self._instrument is not None:
            self._channels = ins.get_channels()
        else:
            self._channels = 0

        bval = False
        if self._channels > 0:
            bval = True
        self._button_left.set_sensitive(bval)
        self._button_right.set_sensitive(bval)

        bval = False
        if self._channels > 1:
            bval = True
        self._button_up.set_sensitive(bval)
        self._button_down.set_sensitive(bval)

        bval = False
        if self._channels > 2:
            bval = True
        self._button_z_up.set_sensitive(bval)
        self._button_z_down.set_sensitive(bval)

    def _direction_clicked(self, clicked, x, y, z):
        coord = []
        if self._channels > 0:
            coord.append(x)
        if self._channels > 1:
            coord.append(y)
        if self._channels > 2:
            coord.append(z)

        if clicked:
            self.emit('direction-clicked', coord)
        else:
            self.emit('direction-released', coord)

    def _key_pressed_cb(self, sender, key):
        pass

    def _key_released_cb(self, sender, key):
        pass

    def _max_speed_changed_cb(self, sender):
        self.emit('max-speed-changed', sender.get_value())

    def _min_speed_changed_cb(self, sender):
        self.emit('min-speed-changed', sender.get_value())

    def get_max_speed(self):
        return self._max_speed.get_value()

    def get_min_speed(self):
        return self._min_speed.get_value()

    def get_accel(self):
        return self._accel.get_value()

    def get_decel(self):
        return self._decel.get_value()

    def _accel_changed_cb(self, sender):
        self.emit('accel-changed', sender.get_value())

    def _decel_changed_cb(self, sender):
        self.emit('decel-changed', sender.get_value())

class PositionBookmarks(gtk.Frame):

    __gsignals__ = {
        'go-request': (gobject.SIGNAL_RUN_FIRST,
                        gobject.TYPE_NONE,
                        ([gobject.TYPE_PYOBJECT])),
    }

    def __init__(self, ins):
        gtk.Frame.__init__(self)

        self.set_label(_L('Bookmarks'))

        self._add_button = gtk.Button(_L('Add'))
        self._add_button.connect('clicked', self._add_clicked_cb)

        self._goxy_button = gtk.Button(_L('Goto XY'))
        self._goxy_button.connect('clicked', self._go_clicked_cb, 2)

        self._goxyz_button = gtk.Button(_L('Goto XYZ'))
        self._goxyz_button.connect('clicked', self._go_clicked_cb, 3)

        self._remove_button = gtk.Button(_L('Remove'))
        self._remove_button.connect('clicked', self._remove_clicked_cb)

        self._tree_model = gtk.ListStore(str, str)
        self._tree_view = QTTable([
            ('Label', {}),
            ('Position', {})
            ], self._tree_model)

        self._label_entry = gtk.Entry()

        self.set_instrument(ins)

        vbox = pack_vbox([
                pack_hbox([
                    gtk.Label(_L('Label')),
                    self._label_entry], True, False),
                pack_hbox([
                    self._add_button,
                    self._goxy_button,
                    self._goxyz_button,
                    self._remove_button], True, True),
                self._tree_view
                ], False, False)
        vbox.set_border_width(4)

        self.add(vbox)

    def set_instrument(self, ins):
        self._ins = ins

        bval = False
        if ins is not None:
            bval = True
        self._add_button.set_sensitive(bval)

        bval = False
        if ins is not None and ins.get_channels() > 1:
            bval = True
        self._goxy_button.set_sensitive(bval)

        bval = False
        if ins is not None and ins.get_channels() > 2:
            bval = True
        self._goxyz_button.set_sensitive(bval)

    def _add_clicked_cb(self, widget):
        pos = self._ins.get_position()
        posstr = self._ins.format_parameter_value('position', pos)
        label = self._label_entry.get_text()
        self._tree_model.append((label, posstr))

    def _remove_clicked_cb(self, widget):
        (model, rows) = self._tree_view.get_selection().get_selected_rows()
        for row in rows:
            iter = model.get_iter(row)
            model.remove(iter)

    def _go_clicked_cb(self, widget, nchannels):
        (model, rows) = self._tree_view.get_selection().get_selected_rows()
        if len(rows) != 1:
            logging.warning('Select 1 row only!')

        row = rows[0]
        iter = model.get_iter(row)
        posstr = model.get_value(iter, 1)

        pos = eval(posstr)
        pos = pos[:nchannels]
        self.emit('go-request', pos)

class QTPositioner(QTWindow):

    def __init__(self):
        QTWindow.__init__(self, 'Positioner')
        self.connect("delete-event", self._delete_event_cb)

        self._controls = PositionControls(None)
        self._controls.connect('direction-clicked', self._direction_clicked_cb)
        self._controls.connect('direction-released', self._direction_released_cb)
        self._controls.connect('max-speed-changed', self._max_speed_changed_cb)
        self._controls.connect('min-speed-changed', self._min_speed_changed_cb)
        self._controls.connect('accel-changed', self._accel_changed_cb)
        self._controls.connect('decel-changed', self._decel_changed_cb)
        self._max_speed = self._controls.get_max_speed()
        self._min_speed = self._controls.get_min_speed()
        self._accel_factor = self._controls.get_accel()
        self._decel_factor = self._controls.get_decel()

        self._bookmarks = PositionBookmarks(None)
        self._bookmarks.connect('go-request', self._go_request)

        self._ins_combo = InstrumentDropdown(types=['positioner'])
        self._ins_combo.connect('changed', self._instrument_changed_cb)
        self._instrument = None

        poslabel = gtk.Label()
        poslabel.set_markup('<big>%s</big>' % _L('Position'))
        self._position_label = gtk.Label()
        self._update_position()

        vbox = pack_vbox([
            self._ins_combo,
            pack_hbox([
                poslabel,
                self._position_label], True, True),
            self._controls,
            self._bookmarks], False, False)

        # Speed control variables
        self._direction_down = (0, 0, 0)
        self._step_done = False
        self._speed = [0, 0, 0]
        self._timer_hid = None
        self._counter = 0

        self.add(vbox)
        vbox.show_all()

    def _delete_event_cb(self, widget, event, data=None):
        print 'Hiding positioner window, use showpositioner() to get it back'
        self.hide()
        return True

    def _instrument_changed_cb(self, widget):
        ins = self._ins_combo.get_instrument()
        self._instrument = ins
        self._controls.set_instrument(ins)
        self._bookmarks.set_instrument(ins)
        self._update_position()

    def _go_request(self, sender, position):
        self._instrument.move_abs(position)

    def _direction_clicked_cb(self, sender, direction):
        self._direction_down = direction
        self._step_done = False
        if self._timer_hid is None:
            self._timer_hid = gobject.timeout_add(100, self._position_timer)

    def _direction_released_cb(self, sender, direction):
        if not self._step_done and self._speed == [0, 0, 0]:
            if self._timer_hid is not None:
                gobject.source_remove(self._timer_hid)
            self._timer_hid = None
            self._do_single_step()

        self._direction_down = (0, 0, 0)

    def _do_single_step(self):
        for i in range(len(self._direction_down)):
            if self._direction_down[i] != 0:
                self._instrument.step(i, misc.sign(self._direction_down[i]))

    def _update_speed(self):
        for i in range(len(self._direction_down)):
            if self._direction_down[i] != 0:
                if self._speed[i] == 0:
                    self._speed[i] = self._direction_down[i] * self._min_speed
                else:
                    self._speed[i] = self._speed[i] * self._accel_factor
                    if abs(self._speed[i]) >= self._max_speed:
                        self._speed[i] = misc.sign(self._speed[i]) * self._max_speed
            else:
                self._speed[i] = self._speed[i] / self._decel_factor
                if abs(self._speed[i]) < self._min_speed:
                    self._speed[i] = 0

        if self._speed != [0, 0, 0]:
            self._step_done = True
            self._instrument.set_speed(self._speed)
            self._instrument.start()
            return True
        else:
            self._instrument.stop()
            return False

        return ret

    def _update_position(self):
        if self._instrument is not None and self._instrument.has_parameter('position'):
            pos = self._instrument.get_position()
            posstr = self._instrument.format_parameter_value('position', pos)
        else:
            posstr = 'None'
        self._position_label.set_markup('<big>%s</big>' % posstr)

    def _position_timer(self):
        self._counter += 1
        ret = self._update_speed()
        if not ret:
            self._timer_hid = None
        if (self._counter % 5) == 0 or not ret:
            self._update_position()
        return ret

    def _max_speed_changed_cb(self, sender, val):
        self._max_speed = val

    def _min_speed_changed_cb(self, sender, val):
        self._min_speed = val

    def _accel_changed_cb(self, sender, val):
        self._accel_factor = val

    def _decel_changed_cb(self, sender, val):
        self._decel_factor = val

def showpositioner():
    get_positionerwin().show_all()

def hidepositioner():
    get_positionerwin().hide_all()

try:
    qt.positionerwin
except:
    qt.positionerwin = QTPositioner()

def get_positionerwin():
    return qt.positionerwin

if __name__ == "__main__":
    gtk.main()

