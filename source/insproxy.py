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
import instrument

class Proxy():

    def __init__(self, name):
        self._name = name
        self._proxy_names = []
        self._setup_done = False

        self._setup_proxy()
        qt.instruments.connect('instrument-added', self._ins_added_cb)
        qt.instruments.connect('instrument-removed', self._ins_removed_cb)

    _FUNCTION_TYPES = (
            types.MethodType,
            types.BuiltinMethodType,
            types.FunctionType,
    )

    def _setup_proxy(self):
        if self._setup_done:
            return
        self._setup_done = True

        self._ins = qt.instruments.get(self._name, proxy=False)
        members = inspect.getmembers(self._ins)

        toadd = instrument.Instrument.__dict__.keys()
        toadd += self._ins.__class__.__dict__.keys()
        toadd += self._ins._added_methods
        for (name, item) in members:
            if type(item) in self._FUNCTION_TYPES \
                    and not name.startswith('_') and name in toadd:
                self._proxy_names.append(name)
                setattr(self, name, item)

    def _remove_functions(self):
        self._setup_done = False
        for name in self._proxy_names:
            delattr(self, name)
        self._proxy_names = []
        self._ins = None

    def _ins_added_cb(self, sender, ins):
        if ins.get_name() == self._name:
            self._setup_proxy()

    def _ins_removed_cb(self, sender, insname):
        if insname == self._name:
            self._remove_functions()

