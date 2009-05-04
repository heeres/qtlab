# insproxy.py, class to act as a proxy for Instrument objects.
# Mostly to facilitate easy reloading of instruments.
# Reinier Heeres <reinier@heeres.eu>, 2009
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

import inspect
import types
import qt

class Proxy():

    def __init__(self, name):
        self._name = name
        self._proxy_names = []

        self._setup_proxy()
        qt.instruments.connect('instrument-added', self._ins_added_cb)
        qt.instruments.connect('instrument-removed', self._ins_removed_cb)

    _FUNCTION_TYPES = (
            types.MethodType,
            types.BuiltinMethodType,
            types.FunctionType,
    )

    def _setup_proxy(self):
        ins = qt.instruments[self._name]
        members = inspect.getmembers(ins)
        for (name, item) in members:
            if type(item) in self._FUNCTION_TYPES \
                    and not name.startswith('_'):
                self._proxy_names.append(name)
                setattr(self, name, item)

    def _remove_functions(self):
        for name in self._proxy_names:
            del self.__dict__[name]
        self._proxy_names = []

    def _ins_added_cb(self, sender, ins):
        if ins.get_name() == self._name:
            self._setup_proxy()

    def _ins_removed_cb(self, sender, insname):
        if insname == self._name:
            self._remove_functions()

