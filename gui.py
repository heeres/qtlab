# gui.py, GUI helper functions for QT lab environment
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

from gettext import gettext as _

def build_menu(tree, root=True):
    """Build a gtk menu, including submenu's

    tree is an array of items, each item being a dictionary with:
    -'name': the visible item name
    -'icon': an (optional) icon
    -'submenu': an array of items representing a submenu
    """

    if root:
        menu = gtk.MenuBar()
    else:
        menu = gtk.Menu()

    for element in tree:
        item = gtk.MenuItem(element['name'])
        if element.has_key('icon'):
            pass
        if element.has_key('submenu'):
            item.set_submenu(build_menu(element['submenu'], root=False))
        elif element.has_key('action'):
            item.connect('activate', element['action'])
        menu.add(item)

    return menu
