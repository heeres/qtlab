from lib.network import tcpserver

class QTHandler(tcpserver.GlibTCPHandler):

    def handle(self, data):
        data = data.strip()
        if len(data) == 0:
            return

        try:
            retval = eval(data, globals(), globals())
        except Exception, e:
            retval = str(e)

        self.socket.send(str(retval))

try:
    qt.server = tcpserver.GlibTCPServer(("127.0.0.1", 12000), QTHandler)
except Exception, e:
    logging.warning('Failed to start network server: %s', str(e))
