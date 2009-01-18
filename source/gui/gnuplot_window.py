# gnuplot_window.py, window to tweak apearance of a gnuplot instance
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
from plot_engines import qtgnuplot

from gettext import gettext as _L

import lib.gui as gui
from lib.gui import dropdowns, qtwindow

class AxisSettings(gtk.Frame):

    def __init__(self, axis):
        gtk.Frame.__init__(self, 'Axis %s' % axis)
        self._axis = axis
        self._plot = None
        self._ignore_changes = False

        self._label_entry = gtk.Entry()
        self._label_but = gtk.Button(_L('Set'))
        self._label_but.connect('clicked', self._label_clicked_cb)

        self._min_range = gtk.Entry()
        self._min_range.set_width_chars(10)
        self._max_range = gtk.Entry()
        self._max_range.set_width_chars(10)
        self._range_but = gtk.Button(_L('Set'))
        self._range_but.connect('clicked', self._range_clicked_cb)

        self._logcheck = gtk.CheckButton('Log')
        self._logcheck.set_active(False)
        self._logcheck.connect('toggled', self._log_toggled_cb)

        vbox = gui.pack_vbox([
            gui.pack_hbox([
                gtk.Label(_L('Label')),
                self._label_entry,
                self._label_but], True, True),
            gui.pack_hbox([
                gtk.Label(_L('Range')),
                self._min_range,
                self._max_range,
                self._range_but], True, True),
            self._logcheck], False, False)

        self.add(vbox)

    def set_plot(self, plot):
        self._plot = plot
        info = plot.get_properties()

        self._ignore_changes = True

        name = '%slog' % self._axis
        if name in info:
            self._logcheck.set_active(info[name] == True)
        else:
            self._logcheck.set_active(False)

        name = '%srange' % self._axis
        if name in info and len(info[name]) == 2:
            self._min_range.set_text(info[name][0])
            self._max_range.set_text(info[name][1])
        else:
            self._min_range.set_text('')
            self._max_range.set_text('')

        name = '%slabel' % self._axis
        if name in info:
            self._label_entry.set_text(info[name])
        else:
            self._label_entry.set_text('')

        self._ignore_changes = False

    def set_sensitive(self, sens):
        self._logcheck.set_sensitive(sens)
        self._label_entry.set_sensitive(sens)
        self._label_but.set_sensitive(sens)
        self._min_range.set_sensitive(sens)
        self._max_range.set_sensitive(sens)
        self._range_but.set_sensitive(sens)

    def _log_toggled_cb(self, widget):
        if self._ignore_changes or self._plot is None:
            return
        log = self._logcheck.get_active()
        name = '%slog' % self._axis
        self._plot.set_property(name, log, update=True)

    def _range_clicked_cb(self, widget):
        if self._ignore_changes or self._plot is None:
            return
        minval = self._min_range.get_text()
        maxval = self._max_range.get_text()
        name = '%srange' % self._axis
        self._plot.set_property(name, (minval, maxval), update=True)

    def _label_clicked_cb(self, widget):
        if self._ignore_changes or self._plot is None:
            return
        name = '%slabel' % self._axis
        label = self._label_entry.get_text()
        self._plot.set_property(name, label, update=True)

class GnuplotWindow(qtwindow.QTWindow):

    def __init__(self):
        qtwindow.QTWindow.__init__(self, 'gnuplot', 'Gnuplot Tweak')
        self.connect("delete-event", self._delete_event_cb)

        self._ignore_changes = False
        self._current_plot = None
        self._plot_state = {}

        self._plot_dropdown = dropdowns.NamedListDropdown(qt.plots)
        self._plot_dropdown.connect('changed', self._plot_changed_cb)

        list = qtgnuplot.Plot3D.get_styles()
        self._styles_dropdown = dropdowns.StringListDropdown(list)
        self._styles_dropdown.connect('changed', self._style_changed_cb)

        list = qtgnuplot.Plot3D.get_palettes()
        self._palette_dropdown = dropdowns.StringListDropdown(list)
        self._palette_dropdown.connect('changed', self._palette_changed_cb)

        self._gamma_hid = None
        self._gamma_spin = gtk.SpinButton()
        self._gamma_spin.set_range(0.0, 5.0)
        self._gamma_spin.set_digits(2)
        self._gamma_spin.set_increments(0.01, 0.1)
        self._gamma_spin.set_value(1)
        self._gamma_spin.connect('changed', self._gamma_changed_cb)

        self._save_as_frame = gtk.Frame(_L('Save as'))
        list = qtgnuplot.Plot3D.get_save_as_types()
        self._filename_entry = gtk.Entry()
        self._save_as_dropdown = dropdowns.StringListDropdown(list)
        self._save_button = gtk.Button(_L('Save'))
        self._save_button.connect('clicked', self._save_clicked_cb)
        self._save_gp_button = gtk.Button(_L('Save .gp file'))
        self._save_gp_button.connect('clicked', self._save_gp_clicked_cb)

        vbox = gui.pack_vbox([
            gui.pack_hbox([
                gtk.Label(_L('Filename')),
                self._filename_entry], True, True),
            gui.pack_hbox([
                self._save_as_dropdown,
                self._save_button], True, True),
            self._save_gp_button], False, False)
        self._save_as_frame.add(vbox)

        self._axis_x = AxisSettings('x')
        self._axis_y = AxisSettings('y')
        self._axis_z = AxisSettings('z')
        self._axis_cb = AxisSettings('cb')

        self._autorange_xy = gtk.Button(_L('Autorange XY'))
        self._autorange_xy.connect('clicked', self._autorange_xyz_cb, False)
        self._autorange_xyz = gtk.Button(_L('Autorange XYZ'))
        self._autorange_xyz.connect('clicked', self._autorange_xyz_cb, True)

        vbox = gui.pack_vbox([
            gui.pack_hbox([
                gtk.Label(_L('Plot')),
                self._plot_dropdown], True, True),
            gui.pack_hbox([
                gtk.Label(_L('Style')),
                self._styles_dropdown], True, True),
            gui.pack_hbox([
                gtk.Label(_L('Palette')),
                self._palette_dropdown], True, True),
            gui.pack_hbox([
                gtk.Label(_L('Gamma')),
                self._gamma_spin], True, True),
            self._save_as_frame,
            self._axis_x,
            self._axis_y,
            self._axis_z,
            self._axis_cb,
            gui.pack_hbox([
                self._autorange_xy,
                self._autorange_xyz], True, True),
    	], False, False)
        vbox.set_border_width(4)
        self.add(vbox)

        vbox.show_all()

    def _delete_event_cb(self, widget, event, data=None):
        self.hide()
        return True

    def _plot_changed_cb(self, widget):
        plot = self._plot_dropdown.get_item()
        if isinstance(plot, qtgnuplot.Plot2D):
            zactive = False
        elif isinstance(plot, qtgnuplot.Plot3D):
            zactive = True
        else:
            self._current_plot = None
            return

        self._ignore_changes = True

        self._current_plot = plot
        info = plot.get_properties()
        if 'style' in info:
            self._styles_dropdown.set_item(info['style'])
        if 'palette' in info:
            if 'name' in info['palette']:
                self._palette_dropdown.set_item(info['palette']['name'])
            if 'gamma' in info['palette']:
                self._gamma_spin.set_value(float(info['palette']['gamma']))

        self._axis_x.set_plot(plot)
        self._axis_y.set_plot(plot)
        self._axis_z.set_plot(plot)
        self._axis_cb.set_plot(plot)

        self._axis_z.set_sensitive(zactive)
        self._axis_cb.set_sensitive(zactive)
        self._styles_dropdown.set_sensitive(zactive)
        self._palette_dropdown.set_sensitive(zactive)
        self._gamma_spin.set_sensitive(zactive)

        self._ignore_changes = False

    def _style_changed_cb(self, widget):
        if self._ignore_changes or self._current_plot is None:
            return
        stylename = self._styles_dropdown.get_item()
        self._current_plot.set_style(stylename)
        self._plot_state['style'] = stylename

    def _palette_changed_cb(self, widget):
        if self._ignore_changes or self._current_plot is None:
            return
        palname = self._palette_dropdown.get_item()
        gamma = self._gamma_spin.get_value()
        self._current_plot.set_palette(palname, gamma=gamma)

    def _gamma_changed_cb(self, widget):
        if self._ignore_changes or self._current_plot is None:
            return
        value = self._gamma_spin.get_value()
        if self._gamma_hid is not None:
            gobject.source_remove(self._gamma_hid)
        self._gamma_hid = gobject.timeout_add(500, self._palette_changed_cb, \
             None)

    def _save_clicked_cb(self, widget):
        if self._current_plot is not None:
            format = self._save_as_dropdown.get_item()
            func = getattr(self._current_plot, 'save_%s' % format, None)
            if func is not None:
                func()

    def _save_gp_clicked_cb(self, widget):
        if self._current_plot is not None:
            self._current_plot.save_gp()

    def _autorange_xyz_cb(self, widget, autoz):
        self._axis_x._min_range.set_text('')
        self._axis_x._max_range.set_text('')
        self._current_plot.set_xrange()
        self._axis_y._min_range.set_text('')
        self._axis_y._max_range.set_text('')
        self._current_plot.set_yrange()
        if autoz:
            self._axis_z._min_range.set_text('')
            self._axis_z._max_range.set_text('')
            self._current_plot.set_zrange()

