# data_window.py, window to browse data files
# Reinier Heeres, <reinier@heeres.eu>, 2009
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
import os
import types

from gettext import gettext as _L
import lib.gui as gui
from lib.gui import dropdowns, qtwindow, qttable
from lib import databrowser

class DataWindow(qtwindow.QTWindow):

    def __init__(self):
        qtwindow.QTWindow.__init__(self, 'data', _L('Data Browser'))
        self.connect("delete-event", self._delete_event_cb)

        self._browser = None
        self._meta_tags = set([])
        self._meta_tag = 'header'
        self._cur_path = None

        self._dir_entry = gtk.Entry()
        self._dir_entry.connect('activate', self._dir_activate_cb)
        self._dir_button = gtk.Button(_L('Browse'))
        self._dir_button.connect('clicked', self._dir_button_clicked_cb)
        self._dir_hbox = gui.pack_hbox(
                (gtk.Label('Directory'), self._dir_entry, self._dir_button),
                True, True)

        self._plot2d_button = gtk.Button(_L('Plot2D'))
        self._plot2d_button.connect('clicked', self._plot2d_clicked_cb)
        self._plot3d_button = gtk.Button(_L('Plot3D'))
        self._plot3d_button.connect('clicked', self._plot3d_clicked_cb)
        self._plot_name = gtk.Entry()
        self._plot_name.set_text('databrowser')
        self._plot_style = gtk.Entry()
        self._clear_check = gtk.CheckButton()
        self._clear_check.set_active(True)
        self._clear_button = gtk.Button(_L('Clear'))
        self._clear_button.connect('clicked', self._clear_clicked_cb)

        hbox1 = gtk.HBox(spacing=10)
        hbox1.pack_start(gtk.Label(_L('Name')), False, False)
        hbox1.pack_start(self._plot_name, False, True)
        hbox2 = gtk.HBox(spacing=10)
        hbox2.pack_start(gtk.Label(_L('Clear')), False, False)
        hbox2.pack_start(self._clear_check, False, True)
        hbox3 = gtk.HBox(spacing=10)
        hbox3.pack_start(gtk.Label(_L('Style')), False, False)
        hbox3.pack_start(self._plot_style, False, True)

        self._plot_box = gui.pack_vbox([
            hbox1, hbox2, hbox3,
            gui.pack_hbox([self._plot2d_button, self._plot3d_button,
                self._clear_button], True, True),
            ], True, True)
        self._plot_box.set_border_width(4)
        self._plot_frame = gtk.Frame('Plot')
        self._plot_frame.add(self._plot_box)

        self._entries_model = gtk.ListStore(str)
        self._entry_map = {}
        self._entries_view = qttable.QTTable([(_L('Filename'), {})], \
                self._entries_model)
        self._entries_view.connect('row-activated', self._row_activated_cb)
        self._entries_scroll = gtk.ScrolledWindow()
        self._entries_scroll.set_policy(gtk.POLICY_AUTOMATIC, \
                gtk.POLICY_AUTOMATIC)
        self._entries_scroll.add_with_viewport(self._entries_view)

        self._info_view = gtk.TextView()
        self._info_view.set_border_width(4)
        self._meta_dropdown = dropdowns.StringListDropdown([])
        self._meta_dropdown.connect('changed', self._meta_drop_changed_cb)
        self._info_box = gui.pack_vbox([
            self._meta_dropdown,
            self._info_view], False, False)
        self._info_box.set_border_width(4)

        self._views_hbox = gui.pack_hbox(
                (self._entries_scroll, self._info_box), True, True)

        vbox = gtk.VBox()
        vbox.pack_start(self._dir_hbox, False, False)
        vbox.pack_start(self._plot_frame, False, False)
        vbox.pack_start(self._views_hbox, True, True)
        self.add(vbox)

        vbox.show_all()

    def _delete_event_cb(self, widget, event, data=None):
        self.hide()
        return True

    def _update_entries(self):
        self._entries_model.clear()
        self._entry_map.clear()
        self._meta_tags.clear()
        for i in self._browser.get_entries():
            dir, fn = os.path.split(i.get_filename())
            self._entries_model.append([fn])
            self._entry_map[fn] = i
            self._meta_tags |= set(i.get_metadata().keys())

        tags = tuple(self._meta_tags)
        self._meta_dropdown.set_items(tags)
        if self._meta_tag in tags:
            self._meta_dropdown.set_item(self._meta_tag)

    def _dir_activate_cb(self, sender):
        dir = sender.get_text()
        self._browser = databrowser.Browser(dir)
        self._update_entries()

    def _dir_button_clicked_cb(self, sender):
        chooser = gtk.FileChooserDialog(
                title=_L('Select directory'),
                action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                    gtk.STOCK_OPEN, gtk.RESPONSE_OK))

        ret = chooser.run()
        if ret == gtk.RESPONSE_OK:
            self._dir_entry.set_text(chooser.get_filename())
            self._dir_entry.activate()

        chooser.destroy()

    def _update_info_for_path(self, path):
        self._cur_path = path

        fn = self._entries_model[path][0]
        info = self._entry_map.get(fn, None)
        if info is None:
            return

        meta = info.get_metadata()
        data = meta.get(self._meta_tag, '')
        if type(data) in (types.ListType, types.TupleType):
            text = '\n'.join(data)
        else:
            text = str(data)

        buf = self._info_view.get_buffer()
        buf.set_text(text)

    def _row_activated_cb(self, treeview, path, view_column):
        self._update_info_for_path(path)

    def _meta_drop_changed_cb(self, sender):
        self._meta_tag = self._meta_dropdown.get_item()
        if self._cur_path is not None:
            self._update_info_for_path(self._cur_path)

    def _get_selected_files(self):
        files = []
        (model, rows) = self._entries_view.get_selection().get_selected_rows()
        for row in rows:
            iter = model.get_iter(row)
            files.append(model[iter][0])
        return files

    def _plot2d_clicked_cb(self, sender):
        name = self._plot_name.get_text()
        style = self._plot_style.get_text()
        clear = self._clear_check.get_active()
        files = self._get_selected_files()
        for fn in files:
            fullfn = self._entry_map[fn].get_filename()
            d = qt.Data(fullfn)
            qt.plot(d, style, name=name, clear=clear)

    def _plot3d_clicked_cb(self, sender):
        name = self._plot_name.get_text()
        clear = self._clear_check.get_active()
        files = self._get_selected_files()
        for fn in files:
            d = qt.Data(self._entry_map[fn].get_filename())
            qt.plot3(d, name=name, clear=clear)

    def _clear_clicked_cb(self, sender):
        name = self._plot_name.get_text()
        plot = qt.plots[name]
        if plot is not None:
            plot.clear()

