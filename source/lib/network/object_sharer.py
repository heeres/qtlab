# object_sharer.py, TCP/IP client/server for sharing python objects
# Reinier Heeres <reinier@heeres.eu>, 2010
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
from lib.network import tcpserver
import copy
import random
import inspect
import time
import gobject

PORT = 12002
BUFSIZE = 8192

class ObjectSharer():
    '''
    The object sharer containing both client and server functions.
    '''

    TIMEOUT = 2

    def __init__(self):
        self._functions = {}
        self._objects = {}
        self._clients = []
        self._object_cache = {}
        self._client_cache = {}

        self._last_hid = 0
        self._last_call_id = 0
        self._return_cbs = {}
        self._return_vals = {}

        # Store callback info indexed on hid and on signam__objname
        self._callbacks_hid = {}
        self._callbacks_name = {}

    def add_client(self, conn, handler):
        '''
        Add a client through connection 'conn'.
        '''
        info = self.call(conn, 'root', 'get_object', 'root')
        if info is None:
            logging.warning('Unable to get client root object')
            return None
        client = ObjectProxy(conn, info)
        self._clients.append(client)
        logging.info('Added client %r', client.get_id())
        return client

    def remove_client(self, client):
        if client in self._clients:
            del self._clients[self._clients.index(client)]

    def _client_disconnected(self, conn):
        for client in self._clients:
            if client.get_connection() == conn:
                logging.warning('Client disconnected, removing')
                self.remove_client(client)
                break

    def get_clients(self):
        return self._clients

    def generate_objname(self):
        return 'obj_%d' % (random.randint(0, 1e6), )

    def get_objects(self):
        return self._objects

    def add_object(self, object):
        if not isinstance(object, SharedObject):
            logging.error('Not a shareable object')
            return False

        objname = object.get_shared_name()
        if objname in self._objects:
            logging.error('Object with name %s already exists', objname)
            return False

        self._objects[objname] = object
        if objname is not 'root':
            self._objects['root'].emit('object-added', objname)

        return True

    def remove_object(self, objname):
        if objname in self._objects:
            del self._objects[objname]
            self._objects['root'].emit('object-removed', objname)

    def _get_object_from(self, client, objname):
        info = client.get_object(objname)
        proxy = ObjectProxy(client.get_connection(), info)
        self._object_cache[objname] = proxy
        return proxy

    def find_object(self, objname):
        '''
        Locate a shared object. Search locally and with connected clients.
        '''

        # Local objects
        if objname in self._objects:
            return self._objects[objname]

        # Remote objects which have a local proxy
        if objname in self._object_cache:
            return self._object_cache[objname]

        # Cached names of objects on remote clients
        for client, object_names in self._client_cache.iteritems():
            if objname in object_names:
                return self._get_object_from(client, objname)

        # Full search
        for client in self._clients:
            names = client.list_objects()
            self._client_cache[client] = names
            if objname in names:
                return self._get_object_from(client, objname)

        return None

    def _pickle_packet(self, info, data):
        try:
            retdata = pickle.dumps((info, data))
        except Exception, e:
            msg = 'Unable to encode object: %s' % str(e)
            retdata = pickle.dumps((info, msg))
        return retdata

    def _unpickle_packet(self, data):
        try:
            return pickle.loads(data)
        except Exception, e:
            logging.warning('Unable to decode object: %s', str(e))
            raise e

    def _send_return(self, conn, callid, retval):
        logging.debug('Returning for call %d: %r', callid, retval)
        retinfo = ('return', callid)
        retdata = self._pickle_packet(retinfo, retval)
        self.send_packet(conn, retdata)

    def handle(self, conn, data):
        '''
        Process incoming data from connection 'conn'
        '''

        try:
            info, callinfo = self._unpickle_packet(data)
        except Exception, e:
            return
        logging.debug('Handling packet %r', info)

        if info[0] == 'return':
            # Asynchronous function reply
            callid = info[1]
            if callid not in self._return_cbs:
                logging.warning('Return received for unknown call %d', callid)
                return
            func = self._return_cbs[callid]
            del self._return_cbs[callid]
            func(callinfo)
            return

        elif info[0] not in ('call', 'signal'):
            logging.warning('Invalid request: %r, %r', info, callinfo)
            return False

        (objname, funcname, args, kwargs) = callinfo
        logging.debug('Handling: %s.%s(%r, %r)', objname, funcname, args, kwargs)
        if objname not in self._objects:
            msg = 'Object %s not available' % objname
            logging.warning(msg)
            if info[0] != 'signal':
                self._send_return(conn, info[1], ValueError(msg))
            return None

        obj = self._objects[objname]
        func = getattr(obj, funcname)
        try:
            ret = func(*args, **kwargs)
        except Exception, e:
            ret = e

        if info[0] == 'signal':
            # No need to send return
            return

        self._send_return(conn, info[1], ret)

    def recv_packet(self, conn):
        data = conn.recv(2)
        if len(data) == 0:
            logging.warning('Client disconnected')
            self._client_disconnected(conn)
            return None

        datalen = ord(data[0]) * 256 + ord(data[1])
        try:
            data = conn.recv(datalen)
        except:
            logging.warning('Receive exception!')
            self._client_disconnected(conn)
        return data

    def send_packet(self, conn, data):
        dlen = len(data)
        if dlen > 0xffff:
            logging.error('Trying to send too long packet: %d', dlen)
            return False

        tosend = '%c%c' % (int(dlen / 256), dlen & 0xff)
        tosend += data
        try:
            ret = conn.send(tosend)
            if ret != len(tosend):
                logging.warning('Only %d bytes got sent instead of %d', ret, len(tosend))
        except:
            logging.warning('Send exception, assuming client disconnected')
            self._client_disconnected(conn)

        return True

    def _call_cb(self, callid, val):
        if callid in self._return_vals:
            logging.warning('Call %d timed out', callid)
            del self._return_vals[callid]
        else:
            self._return_vals[callid] = val

    def call(self, conn, objname, funcname, *args, **kwargs):
        '''
        Call a function through connection 'conn'
        '''

        is_signal = kwargs.pop('signal', False)
        if not is_signal:
            self._last_call_id += 1
            callid = self._last_call_id
            cb = kwargs.pop('callback', None)
            if cb is not None:
                self._return_cbs[callid] = cb
            else:
                self._return_cbs[callid] = lambda val: self._call_cb(callid, val)

            info = ('call', callid)
        else:
            cb = None
            info = ('signal', )

        logging.debug('Calling %s.%s(%r, %r), info=%r', objname, funcname, args, kwargs, info)

        callinfo = (objname, funcname, args, kwargs)
        cmd = self._pickle_packet(info, callinfo)
        start_time = time.time()
        self.send_packet(conn, cmd)

        ret = None
        return_ok = False
        if cb is None and not is_signal:
            # Wait for return
            while time.time() - start_time < self.TIMEOUT:
                if callid in self._return_vals:
                    ret = self._return_vals[callid]
                    del self._return_vals[callid]
                    if isinstance(ret, Exception):
                        raise Exception('Remote error: %s' % str(ret))
                    return ret

                import select
                lists = select.select([conn], [], [])
                if len(lists[0]) > 0:
                    data = self.recv_packet(conn)
                    self.handle(conn, data)
                else:
                    time.sleep(0.002)

            # Mark as timed-out
            self._return_vals[callid] = None

        return None

    def connect(self, objname, signame, callback, *args):
        '''
        Called by ObjectProxy instances to register a callback request.
        '''
        self._last_hid += 1
        info = {
                'hid': self._last_hid,
                'object': objname,
                'signal': signame,
                'function': callback,
                'args': args,
        }

        self._callbacks_hid[self._last_hid] = info
        name = '%s__%s' % (objname, signame)
        if name in self._callbacks_name:
            self._callbacks_name[name].append(info)
        else:
            self._callbacks_name[name] = [info]

        return self._last_hid

    def disconnect(self, hid):
        if hid in self._callbacks_hid:
            del self._callbacks[hid]

        for name, info_list in self._callbacks_name.iteritems():
            for index, info in enumerate(info_list):
                if info['hid'] == hid:
                    del self._callbacks_name[name][index]
                    break

    def emit_signal(self, objname, signame, *args, **kwargs):
        logging.info('Emitting %s(%r, %r) for %s to %d clients',
                signame, args, kwargs, objname, len(self._clients))

        kwargs['signal'] = True
        for client in self._clients:
            client.receive_signal(objname, signame, *args, **kwargs)

    def receive_signal(self, objname, signame, *args, **kwargs):
        logging.info('Received signal %s(%r, %r) from %s',
                signame, args, kwargs, objname)

        ncalls = 0
        start = time.time()
        name = '%s__%s' % (objname, signame)
        if name in self._callbacks_name:
            info_list = self._callbacks_name[name]
            for info in info_list:
                try:
                    info['function'](*args, **kwargs)
                    ncalls += 1
                except Exception, e:
                    logging.warning('Callback failed: %s', str(e))

        end = time.time()
        logging.debug('Did %d callbacks in %.03fms for sig %s',
                ncalls, (end - start) * 1000, signame)

class SharedObject():
    '''
    Server side object that can be shared and emit signals.
    '''

    def __init__(self, name):
        self.__last_hid = 1
        self.__callbacks = {}
        self.__name = name
        helper.add_object(self)

    def get_shared_name(self):
        return self.__name

    def emit(self, signal, *args, **kwargs):
        helper.emit_signal(self.__name, signal, *args, **kwargs)

    def connect(self, signame, callback, *args):
        self.__last_hid += 1
        self.__callbacks[self.__last_hid] = {
                'signal': signame,
                'function': callback,
                'args': args,
                }
        return self.__last_hid

    def disconnect(self, hid):
        if hid in self.__callbacks:
            del self.__callbacks[hid]

class SharedGObject(gobject.GObject, SharedObject):

    def __init__(self, name):
        logging.debug('Creating shared Gobject: %r', name)
        self.__hid_map = {}
        gobject.GObject.__init__(self)
        SharedObject.__init__(self, name)

    def connect(self, signal, *args, **kwargs):
        hid = SharedObject.connect(self, signal, *args, **kwargs)
        ghid = gobject.GObject.connect(self, signal, *args, **kwargs)
        self.__hid_map[ghid] = hid
        return ghid

    def emit(self, signal, *args, **kwargs):
        # The 'None' here is the 'sender'
        SharedObject.emit(self, signal, None, *args, **kwargs)
        return gobject.GObject.emit(self, signal, *args, **kwargs)

    def disconnect(self, ghid):
        if ghid not in self.__hid_map:
            return
        hid = self.__hid_map[ghid]
        SharedObject.disconnect(self, hid)
        del self.__hid_map[ghid]
        return gobject.GObject.disconnect(self, ghid)

class _FunctionCall():

    def __init__(self, conn, objname, funcname, share_options):
        self._conn = conn
        self._objname = objname
        self._funcname = funcname

        if share_options is None:
            self._share_options = {}
        else:
            self._share_options = share_options

        self._cached_result = None

    def __call__(self, *args, **kwargs):
        cache = self._share_options.get('cache_result', False) 
        if cache and self._cached_result is not None:
            return self._cached_result

        ret = helper.call(self._conn, self._objname, self._funcname, *args, **kwargs)
        if cache:
            self._cached_result = ret
        return ret

class ObjectProxy():
    '''
    Client side object proxy.
    '''

    def __init__(self, conn, info):
        self.__conn = conn
        self.__name = info['name']
        self.__new_hid = 1
        self.__callbacks = {}

        for funcname, share_options in info['functions']:
            setattr(self, funcname, _FunctionCall(self.__conn, self.__name, funcname, share_options))

        for propname in info['properties']:
            setattr(self, propname, 'blaat')

    def get_connection(self):
        return self.__conn

    def connect(self, signame, func):
        return helper.connect(self.__name, signame, func)

    def disconnect(self, hid):
        if self.client:
            return self.__client.disconnect(hid)

def cache_result(f):
    f._share_options = {'cache_result': True}
    return f

class RootObject(SharedObject):

    def __init__(self, name):
        SharedObject.__init__(self, name)
        self._objects = helper.get_objects()
        self._id = random.randint(0, 1e6)

    def get_object(self, objname):
        if objname not in self._objects:
            raise Exception('Object not found')

        obj = self._objects[objname]
        props = []
        funcs = []
        for key, val in inspect.getmembers(obj):
            if key.startswith('_') or key in ObjectProxy.__dict__:
                continue
            elif callable(val):
                if hasattr(val, '_share_options'):
                    opts = val._share_options
                else:
                    opts = None
                funcs.append((key, opts))
            else:
                props.append(key)

        info = {
            'name': objname,
            'properties': props,
            'functions': funcs
        }
        return info

    def receive_signal(self, objname, signame, *args, **kwargs):
        helper.receive_signal(objname, signame, *args, **kwargs)

    def list_objects(self):
        return self._objects.keys()

    @cache_result
    def get_id(self):
        return self._id

    def hello_world(self, *args, **kwargs):
        return 'Hello world!'

    def hello_exception(self):
        1 / 0

class PythonInterpreter(SharedObject):

    def __init__(self, name, namespace={}):
        SharedObject.__init__(self, name)
        self._namespace = namespace

    def cmd(self, cmd):
        retval = eval(cmd, self._namespace, self._namespace)
        return retval

class _DummyHandler(tcpserver.GlibTCPHandler):

    def __init__(self, sock, client_address, server):
        tcpserver.GlibTCPHandler.__init__(self, sock, client_address, server,
                packet_len=True)
        helper.add_client(self.socket, self)

    def handle(self, data):
        helper.handle(self.socket, data)
        return True

def start_glibtcp_server(port=PORT):
    try:
        server = tcpserver.GlibTCPServer(('', port), _DummyHandler, '127.0.0.1')
        SharedObject.server = server
    except Exception, e:
        logging.warning('Failed to start sharing server: %s', str(e))

def start_glibtcp_client(host, port=PORT):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        handler = _DummyHandler(sock, 'client', 'server')
    except Exception, e:
        logging.warning('Failed to start sharing client: %s', str(e))

helper = ObjectSharer()
RootObject('root')

