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

from gettext import gettext as _

class QTLab(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.move(0, 0)

        self.set_size_request(200, 200)
        self.set_border_width(1)
        self.set_title('QT Lab')

        self.connect("delete-event", self._delete_event_cb)

        self.vbox = gtk.VBox()

        menu = [
            {'name': _('File'), 'icon': '', 'submenu':
                [
                {'name': _('Save'), 'icon': '', 'action': self._save_cb},
                {'name': _('Exit'), 'icon': '', 'action': self._exit_cb}
                ]
            },
            {'name': _('View'), 'icon': '', 'submenu':
                [
                {'name': _('Shell'), 'icon': '', 'action': self._view_shell_cb},
                {'name': _('Plot'), 'icon': '', 'action': self._view_plot_cb}
                ]
            },
            {'name': _('Help'), 'icon': '', 'submenu':
                [
                {'name': _('About'), 'icon': ''}
                ]
            }
        ]
        self.menu = gui.build_menu(menu)

        self._ins_but = gtk.Button('Instruments')
        self._ins_but.connect('clicked', self._toggle_visibility_cb, get_inswin())
        self._tune_but = gtk.Button('Tune')
        self._tune_but.connect('clicked', self._toggle_visibility_cb, get_tunewin())
        self._source_but = gtk.Button('Source')
        self._source_but.connect('clicked', self._toggle_visibility_cb, get_sourcewin())
        self._measure_but = gtk.Button('Measure')
        self._measure_but.connect('clicked', self._toggle_visibility_cb, get_measurewin())

        v1 = pack_vbox([
            self._ins_but,
            self._tune_but,
            self._source_but,
            self._measure_but])

        self.vbox.pack_start(self.menu, False, False)
        self.vbox.pack_start(v1, False, False)
        self.add(self.vbox)

        self.show_all()

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

def showmain():
    global _labwin
    _labwin.show()

_labwin = QTLab()
if __name__ == "__main__":
    gtk.main()
