# datalist.py, base class to implement named lists
# Reinier Heeres <reinier@heeres.eu>, 2008
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

import data
import namedlist

class DataList(namedlist.NamedList):
    def __init__(self, time_name=True):
        namedlist.NamedList.__init__(self, 'data')

        self._time_name = time_name

    def new_item_name(self, item, name):
        '''Function to generate a new item name.'''

        if name == '':
            self._auto_counter += 1
            name = self._base_name + str(self._auto_counter)
            item.set_name(name)

        if self._time_name:
            return item.get_time_name()
        else:
            return item.get_name()

    def create(self, name, **kwargs):
        '''Function to create a new data object, do not call directly.'''
        return data.Data(name=name, **kwargs)

