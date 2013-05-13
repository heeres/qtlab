# Script to start a GTK-based QTLab client

import os
import sys
import logging

import client_shared
args, pargs = client_shared.process_args()

from lib.network import object_sharer as objsh

def _close_gui_cb(*args):
    import gtk
    import qtclient as qt
    logging.info('Closing client')
    qt.config.save(delay=0)
    try:
        gtk.main_quit()
    except:
        pass
    sys.exit()

if __name__ == "__main__":
    srv = objsh.start_glibtcp_client('localhost', port=args.port, nretry=60)

    # Be sure to talk to the qtlab instance that we just connected to
    if srv:
        import lib.config as cfg
        cfg.get_config()['instance_name'] = srv.get_instance_name()

    objsh.helper.register_event_callback('disconnected', _close_gui_cb)

    if args.module:
        logging.info('Importing module %s', args.module)
        __import__(args.module, globals())

    if args.disable_io:
        os.close(sys.stdin.fileno())
        os.close(sys.stdout.fileno())
        os.close(sys.stderr.fileno())

    # Ignore CTRL-C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    import gtk
    gtk.main()

