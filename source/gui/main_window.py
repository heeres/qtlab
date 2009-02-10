# main_window.py, main window for QT lab environment
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
from gettext import gettext as _L

import qt
import lib.gui as gui
from lib.gui import qtwindow, stopbutton

class MainWindow(qtwindow.QTWindow):

    _main_created = False

    def __init__(self):
        if MainWindow._main_created:
            logging.error('Error: Main window already created!')
            return
        MainWindow._main_created = True

        qtwindow.QTWindow.__init__(self, 'main', 'QT Lab', add_to_main=False)
        self.connect("delete-event", self._delete_event_cb)

        self.vbox = gtk.VBox()

        menu = [
            {'name': _L('File'), 'icon': '', 'submenu':
                [
                {'name': _L('Save'), 'icon': '', 'action': self._save_cb},
                {'name': _L('Exit'), 'icon': '', 'action': self._exit_cb}
                ]
            },
            {'name': _L('Help'), 'icon': '', 'submenu':
                [
                {'name': _L('About'), 'icon': ''}
                ]
            }
        ]
        self.menu = gui.build_menu(menu)

        self._liveplot_but = gtk.ToggleButton(_L('Live Plotting'))
        self._liveplot_but.set_active(qt.config.get('auto-update', True))
        self._liveplot_but.connect('clicked', self._toggle_liveplot_cb)
        self._stop_but = stopbutton.StopButton()

        self._window_button_vbox = gtk.VBox()
        self._window_buttons = []

        v1 = gui.pack_vbox([
            self._liveplot_but,
            self._stop_but,
            self._window_button_vbox])

        self.vbox.pack_start(self.menu, False, False)
        self.vbox.pack_start(v1, False, False)
        self.add(self.vbox)

        self.show_all()

    def add_window(self, win):
        '''Add a button for window 'win' to the main window.'''

        title = win.get_title()
        button = gtk.ToggleButton(title)
        self._window_buttons.append(button)

        visible = qt.config.get('%s_show' % title, False)
        button.set_active(visible)

        # Connecting to clicked also triggers response on calling set_active()
        button.connect('released', self._toggle_visibility_cb, win)
        win.connect('show', self._visibility_changed_cb, button)
        win.connect('hide', self._visibility_changed_cb, button)

        button.show()
        self._window_button_vbox.pack_start(button)

    def load_instruments(self):
        return

    def _delete_event_cb(self, widget, event, data=None):
        self.hide()
        return True

    def _destroy_cb(self, widget, data=None):
        config = config.get_config()
        config.save()
        gtk.main_quit()

    def _save_cb(self, widget):
        pass

    def _exit_cb(self, widget):
        pass

    def _toggle_visibility_cb(self, button, window):
        if (window.flags() & gtk.VISIBLE):
            window.hide()
        else:
            window.show()

    def _visibility_changed_cb(self, window, button):
        if window.flags() & gtk.VISIBLE:
            button.set_active(True)
        else:
            button.set_active(False)

    def _toggle_liveplot_cb(self, widget):
        qt.config.set('auto-update', not qt.config.get('auto-update'))

