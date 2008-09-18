# 80_main_window.py, main window for QT lab environment
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
import gui
import qt

from gettext import gettext as _L

class QTLab(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.move(0, 0)

        self.set_size_request(200, 200)
        self.set_border_width(1)
        self.set_title('QT Lab')

        self.connect("delete-event", self._delete_event_cb)
        gui.get_guisignals().connect("update-gui", self._update_gui_cb)
        gui.get_guisignals().connect("register-global",
            self._register_global_cb)

        self.vbox = gtk.VBox()

        menu = [
            {'name': _L('File'), 'icon': '', 'submenu':
                [
                {'name': _L('Save'), 'icon': '', 'action': self._save_cb},
                {'name': _L('Exit'), 'icon': '', 'action': self._exit_cb}
                ]
            },
            {'name': _L('View'), 'icon': '', 'submenu':
                [
                {'name': _L('Shell'), 'icon': '', 'action': self._view_shell_cb},
                {'name': _L('Plot'), 'icon': '', 'action': self._view_plot_cb}
                ]
            },
            {'name': _L('Help'), 'icon': '', 'submenu':
                [
                {'name': _L('About'), 'icon': ''}
                ]
            }
        ]
        self.menu = gui.build_menu(menu)

        self._liveplot_but = gtk.Button(_L('Live Plotting'))
        self._liveplot_but.connect('clicked', self._toggle_liveplot_cb)
        self._stop_but = gtk.Button(_L('Stop'))
        self._stop_but.connect('clicked', self._toggle_stop_cb)

        self._window_button_vbox = gtk.VBox()

        v1 = pack_vbox([
            self._liveplot_but,
            self._stop_but,
            self._window_button_vbox])

        self.vbox.pack_start(self.menu, False, False)
        self.vbox.pack_start(v1, False, False)
        self.add(self.vbox)

        self.show_all()

    def add_window(self, win):
        title = win.get_title()
        button = gtk.Button(title)
        button.connect('clicked', self._toggle_visibility_cb, win)
        button.show()
        self._window_button_vbox.pack_start(button)

    def load_instruments(self):
        return

    def _delete_event_cb(self, widget, event, data=None):
        # Change False to True and the main window will not be destroyed
        # with a "delete_event".
        print 'Hiding main window, use showmain() to get it back'
        self.hide()
        return True

    def _destroy_cb(self, widget, data=None):
        print 'Storing configuration settings...'
        config = config.get_config()
        config.save()
        gtk.main_quit()

    def _save_cb(self, widget):
        print 'Save'

    def _exit_cb(self, widget):
        pass
#        gtk.main_quit()

    def _toggle_visibility_cb(self, widget, window):
        if (window.flags() & gtk.VISIBLE):
            window.hide()
        else:
            window.show_all()

    def _view_shell_cb(self, widget):
        if self.shell is None:
            self.shell = ShellWindow()
        elif not (self.shell.flags() & gtk.VISIBLE):
            self.shell.show()
        else:
            print '%r' % self.shell.flags()

    def _view_plot_cb(self, widget):
        if self.plot is None or not (self.plot.flags() & gtk.VISIBLE):
            self.plot = PlotWindow()
        else:
            print '%r' % self.plot.flags()

    def _update_gui_cb(self, widget):
        gtk.gdk.threads_enter()
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        gtk.gdk.threads_leave()

    def _register_global_cb(self, sender, name, val):
        code = 'global %s\n%s = %s' % (name, name, val)
        exec(code, globals())

    def _toggle_liveplot_cb(self, widget):
        qt.config.set('auto-update', not qt.config.get('auto-update'))

    def _toggle_stop_cb(self, widget):
        gui.set_abort()

try:
    qt.mainwin
except:
    qt.mainwin = QTLab()

def get_mainwin():
    return qt.mainwin

def showmain():
    get_mainwin().show()

def hidemain():
    get_mainwin().hide()

if __name__ == "__main__":
    gtk.main()
