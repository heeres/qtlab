import gtk

from gettext import gettext as _

class QTLab(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.move(0, 0)

        self.set_size_request(500, 100)
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
        self.menu = self.build_menu(menu, root=True)
        self.vbox.pack_start(self.menu, False, False)
        self.add(self.vbox)

#        self.shell = ShellWindow()
#        self.plot = PlotWindow()

        self.show_all()

    def load_instruments(self):
        return

    def build_menu(self, tree, root=False):
        if root:
            menu = gtk.MenuBar()
        else:
            menu = gtk.Menu()

        for element in tree:
            item = gtk.MenuItem(element['name'])
            if element.has_key('icon'):
                pass
            if element.has_key('submenu'):
                item.set_submenu(self.build_menu(element['submenu']))
            elif element.has_key('action'):
                item.connect('activate', element['action'])
            menu.add(item)

        return menu

    def _delete_event_cb(self, widget, event, data=None):
        # Change False to True and the main window will not be destroyed
        # with a "delete_event".
        print 'Hiding main window, use showmain() to get it back'
        self.hide()
        return True

#    def _destroy_cb(self, widget, data=None):
#        gtk.main_quit()

    def _save_cb(self, widget):
        print 'Save'

    def _exit_cb(self, widget):
        pass
#        gtk.main_quit()

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
