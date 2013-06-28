# QTLab gui client

import logging
l = logging.getLogger()
l.setLevel(logging.WARNING)

import os
import sys
import time
import optparse
adddir = os.path.join(os.getcwd(), 'source')
sys.path.insert(0, adddir)

# We should not overwrite the config file set up by client_shared.py
from lib import config
config = config.get_config()

from lib.network import object_sharer as objsh

from lib.misc import get_traceback
TB = get_traceback()()

def setup_windows():
    from windows import main_window
    main_window.Window()

    winpath = os.path.join(config['execdir'], 'clients/gui_client/windows')
    for fn in os.listdir(winpath):
        if not fn.endswith('_window.py') or fn == 'main_window.py':
            continue

        dir, fn = os.path.split(fn)
        classname = os.path.splitext(fn)[0]

        if config.get('exclude_%s' % classname, False):
            logging.info('Skipping class %s', classname)
            continue

        logging.info('Loading class %s...', classname)
        start = time.time()
        codestr = "from windows import %s\n%s.Window()" % (classname, classname)
        try:
            exec codestr
        except Exception, e:
            print 'Error loading window %s' % classname
            TB()

        delta = time.time() - start
        logging.info('   Time = %.03s', delta)

def _close_gui_cb(*args):
    import gtk
    import qtclient as qt
    logging.info('Closing GUI')
    qt.config.save(delay=0)
    try:
        gtk.main_quit()
    except:
        pass
    sys.exit()

objsh.helper.register_event_callback('disconnected', _close_gui_cb)
import qtclient as qt
qt.flow.connect('close-gui', _close_gui_cb)
setup_windows()

# Ignore CTRL-C
import signal
signal.signal(signal.SIGINT, signal.SIG_IGN)

import gtk
gtk.main()

