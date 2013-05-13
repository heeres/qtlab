# network.py, functions for tcp/ip client/server integration with glib.
# Based on network.py from Sugar, Copyright (C) 2006-2007 Red Hat, Inc.
# Extended by Reinier Heeres for the QT Lab environment, (C)2008
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import gobject
import socket

from lib.network.object_sharer import helper, PORT
from lib.network.tcpserver import GlibTCPHandler

from PyQt4 import QtGui, QtCore

# methods/classes for QT4 clients that replace the glib-based ones
class QtTCPHandler(GlibTCPHandler, QtCore.QObject):
    def __init__(self, sock, client_address, server, packet_len=False):
        QtCore.QObject.__init__(self)
        GlibTCPHandler.__init__(self, sock, client_address, server, packet_len)

        self.socket_notifier = QtCore.QSocketNotifier(\
            self.socket.fileno(), QtCore.QSocketNotifier.Read)
        self.socket_notifier.setEnabled(True)
        self.socket_notifier.activated.connect(self._socketwatcher_recv)

    def enable_callbacks(self):
        return

    def disable_callbacks(self):
        return

    def _socketwatcher_recv(self, *args):
        self._handle_recv(self.socket, gobject.IO_IN)

class QtQtlabHandler(QtTCPHandler):
    def __init__(self, sock, client_address, server):
        QtTCPHandler.__init__(self, sock, client_address, server,
                packet_len=True)
        self.client = helper.add_client(self.socket, self)

    def handle(self, data):
        if len(data) > 0:
            data = helper.handle_data(self.socket, data)
        return True
