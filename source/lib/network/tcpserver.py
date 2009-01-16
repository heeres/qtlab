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

import os

import gobject
import SimpleHTTPServer
import SocketServer
import socket
import time
import code

class GlibTCPServer(SocketServer.TCPServer):
    """GlibTCPServer

    Integrate socket accept into glib mainloop.
    """

    allow_reuse_address = True
    request_queue_size = 20

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address,
                                        RequestHandlerClass)
        self.socket.setblocking(0)  # Set nonblocking

        # Watch the listener socket for data
        gobject.io_add_watch(self.socket, gobject.IO_IN, self._handle_accept)

    def _handle_accept(self, source, condition):
        """Process incoming data on the server's socket by doing an accept()
        via handle_request()."""
        if not (condition & gobject.IO_IN):
            return True
        self.handle_request()
        return True

    def close_request(self, request):
        """Called to clean up an individual request."""
        # let the request be closed by the request handler when its done
        pass

class GlibTCPHandler(SocketServer.BaseRequestHandler):
    '''
    Class to do asynchronous request handling integrated with GTK mainloop.
    '''

    BUFSIZE = 4096

    def __init__(self, request, client_address, server):
        if not isinstance(request, socket.socket):
            raise ValueError('Only stream sockets supported')

        self.socket = request
        self.client_address = client_address
        self.server = server

        self.socket.setblocking(0)
        self._in_hid = gobject.io_add_watch(self.socket, \
            gobject.IO_IN | gobject.IO_ERR | gobject.IO_HUP, self._handle_recv)

    def setup(self):
        pass

    def _handle_recv(self, socket, number):
        data = ''
        while True:
            try:
                chunk = socket.recv(self.BUFSIZE)
                data += chunk
            except Exception, e:
                break

            if len(chunk) == 0:
                break

        if len(data) == 0:
            self._handle_hup()
        else:
            self.handle(data)

        return True

    def _handle_hup(self):
        if self._in_hid is not None:
            gobject.source_remove(self._in_hid)
            self._in_hid = None

    def handle(self, data):
        '''Override this function to handle actual data.'''
        print 'Data: %s, self: %r' % (data, repr(self))
        time.sleep(0.1)

    def finish(self):
        return

