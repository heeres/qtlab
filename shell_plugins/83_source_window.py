import gtk
import gobject

import gtksourceview2
import pango

from gettext import gettext as _

class QTSource(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.move(310, 310)

        self.set_size_request(500, 500)
        self.set_border_width(1)
        self.set_title(_('Source'))

        self.connect("delete-event", self._delete_event_cb)

        menu = [
            {'name': _('File'), 'submenu':
                [
                    {'name': _('Save'), 'action': self._save_cb},
                    {'name': _('Open'), 'action': self._open_cb},
                    {'name': _('Run'), 'action': self._run_cb}
                ]
            }
        ]

        self.menu = gui.build_menu(menu)

        self.setup_source_view()

        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.menu, False, False)
        self.vbox.pack_start(self.source_win)
        self.add(self.vbox)

        self.show_all()

    def setup_source_view(self):
        self._buffer = gtksourceview2.Buffer()
        lang_manager = gtksourceview2.language_manager_get_default()
        if 'python' in lang_manager.get_language_ids():
            lang = lang_manager.get_language('python')
            self._buffer.set_language(lang)

#        self._buffer.set_highlight(True)

        self.source_view = gtksourceview2.View(self._buffer)
        self.source_view.set_editable(True)
        self.source_view.set_cursor_visible(True)
        self.source_view.set_show_line_numbers(True)
        self.source_view.set_wrap_mode(gtk.WRAP_CHAR)
        self.source_view.modify_font(pango.FontDescription("Monospace 10"))

        self.source_win = gtk.ScrolledWindow()
        self.source_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.source_win.add(self.source_view)

    def _delete_event_cb(self, widget, event, data=None):
        print 'Hiding source window, use showsource() to get it back'
        self.hide()
        return True

    def _save_cb(self):
        pass

    def _open_cb(self):
        pass

    def _run_cb(self):
        code = ''
        exec(code)

def showsource():
    global _soucewin
    _sourcewin.show()

_sourcewin = QTSource()
if __name__ == "__main__":
    gtk.main()

