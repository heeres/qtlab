# remote_instrument.py, TCP/IP client/server for sharing instruments between
# remote QTlab instances.
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

import logging
import pickle
import socket
from lib.network import tcpserver, tcpclient
import qt
import copy

PORT = 12001
BUFSIZE = 8192

def ins_get(insname, parname):
    return qt.instruments[insname].get(parname)

def ins_set(insname, parname, val):
    return qt.instruments[insname].set(parname, val)

def ins_call(insname, funcname, *args, **kwargs):
    func = getattr(qt.instruments[insname], funcname)
    return func(*args, **kwargs)

def get_ins_list():
    return qt.instruments.get_instrument_names()

def get_ins_parameters(insname):
    params = copy.copy(qt.instruments[insname].get_parameters())
    for name in params.keys():
        params[name] = copy.copy(params[name])
        params[name]['get_func'] = None
        params[name]['set_func'] = None
    return params

def get_ins_functions(insname):
    funcs = copy.copy(qt.instruments[insname].get_functions())
    for name in funcs.keys():
        funcs[name] = copy.copy(funcs[name])
    return funcs

def hello_world():
    return 'Hello world!'

class InstrumentServer(tcpserver.GlibTCPHandler):

    def __init__(self, *args):
        tcpserver.GlibTCPHandler.__init__(self, *args)
        self._functions = {}
        self._register_function('ins_get', ins_get)
        self._register_function('ins_set', ins_set)
        self._register_function('ins_call', ins_call)
        self._register_function('ins_list', get_ins_list)
        self._register_function('ins_parameters', get_ins_parameters)
        self._register_function('ins_functions', get_ins_functions)
        self._register_function('hello_world', hello_world)

    def _register_function(self, name, func):
        self._functions[name] = func

    def handle(self, data):
        try:
            callinfo = pickle.loads(data)
            (funcname, args, kwargs) = callinfo
            if funcname not in self._functions:
                logging.warning('Function %s not supported', funcname)
                return None
            func = self._functions[funcname]
            ret = func(*args, **kwargs)
            data = pickle.dumps(ret)
            self.socket.send(data)
        except Exception, e:
            logging.warning('Call from remote client failed: %s', e)
            self.socket.send(pickle.dumps('Error: %s' % e))

class InstrumentClient(tcpclient.TCPClient):

    def __init__(self, host, port=PORT):
        tcpclient.TCPClient.__init__(self, host, port)

    def _call(self, funcname, *args, **kwargs):
        try:
            cmd = pickle.dumps((funcname, args, kwargs))
            self.send(cmd)
            data = self.recv(BUFSIZE, 2)
            ret = pickle.loads(data)
            return ret
        except Exception, e:
            logging.warning('Call to remote host failed: %s', e)
            return None

    def get_instruments(self):
        return self._call('ins_list')

    def get_instrument_parameters(self, insname):
        return self._call('ins_parameters', insname)

    def get_instrument_functions(self, insname):
        return self._call('ins_functions', insname)

    def ins_get(self, insname, parname):
        return self._call('ins_get', insname, parname)

    def ins_set(self, insname, parname, val):
        return self._call('ins_set', insname, parname, val)

    def ins_call(self, insname, funcname, *args, **kwargs):
        return self._call('ins_call', insname, funcname, *args, **kwargs)

def start_server(port=PORT):
    try:
        qt.server_instruments = tcpserver.GlibTCPServer(('', port), \
                InstrumentServer)
    except Exception, e:
        logging.warning('Failed to start instrument server: %s', str(e))
