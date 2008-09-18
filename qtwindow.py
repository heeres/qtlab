import gtk
import gobject

from gettext import gettext as _

import qt
import config

class QTWindow(gtk.Window):

    def __init__(self, title, add_to_main=True):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        self._title = title
        self._config = config.get_config()

        winx, winy = self._config.get('%s_pos' % title, (10, 10))
        self.move(winx, winy)

        width, height = self._config.get('%s_size' % self._title, (200, 400))
        self.set_size_request(50, 50)
        self.resize(width, height)

        self.set_border_width(1)

        self.set_title(_(title))

        show = self._config.get('%s_show' % self._title, False)
        if show:
            gobject.timeout_add(100, self._do_show)

        self.connect('size-allocate', self._size_allocate_cb)
        self.connect('show', lambda x: self._show_hide_cb(x, True))
        self.connect('hide', lambda x: self._show_hide_cb(x, False))

        if add_to_main:
            self._add_to_main()

    def _do_show(self):
        self.show()

    def _size_allocate_cb(self, sender, alloc):
        self._config.set('%s_size' % self._title, (alloc.width, alloc.height))

    def _show_hide_cb(self, sender, show):
        self._config.set('%s_show' % self._title, show)

        if show:
            pos = self.get_position()
            self._config.set('%s_pos' % self._title, pos)

    def get_title(self):
        return self._title

    def _add_to_main(self):
        qt.mainwin.add_window(self)
