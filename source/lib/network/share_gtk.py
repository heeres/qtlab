import tcpservergtk
import object_sharer as objsh
import socket
import time
import logging
import gobject

class Handler(tcpservergtk.GlibTCPHandler):

    def __init__(self, sock, client_address, server):
        tcpservergtk.GlibTCPHandler.__init__(self, sock, client_address, server,
                packet_len=True)
        self.client = objsh.helper.add_client(self.socket, self)

    def handle(self, data):
        if len(data) > 0:
            data = objsh.helper.handle_data(self.socket, data)
        return True

_flush_queue_hid = None

def setup_glib_flush_queue():
    global _flush_queue_hid
    if _flush_queue_hid is not None:
        return
    _flush_queue_hid = gobject.timeout_add(2000, objsh.helper._process_send_queue)

def start_server(host='', port=objsh.PORT):
    try:
        server = tcpservergtk.GlibTCPServer((host, port), Handler, '127.0.0.1')
        objsh.SharedObject.server = server
        setup_glib_flush_queue()
        return True
    except Exception, e:
        logging.warning('Failed to start sharing server: %s', str(e))
        return False

def start_client(host, port=objsh.PORT, nretry=1):
    while nretry > 0:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            handler = Handler(sock, 'client', 'server')
            setup_glib_flush_queue()
            return handler.client
        except Exception, e:
            logging.warning('Failed to start sharing client: %s', str(e))
            if nretry > 0:
                logging.info('Retrying in 2 seconds...')
                time.sleep(2)
    return False

