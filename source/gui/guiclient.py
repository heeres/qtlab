# QTLab gui client

import logging
l = logging.getLogger()
l.setLevel(logging.WARNING)

import os, sys, time
adddir = os.path.join(os.getcwd(), 'source')
sys.path.append(adddir)

from lib import config
config = config.create_config('qtlabgui.cfg')

from lib.network import object_sharer as objsh

from IPython.ultraTB import AutoFormattedTB
TB = AutoFormattedTB()

def setup_windows():
    from windows import main_window
    main_window.Window()

    winpath = os.path.join(config['execdir'], 'source/gui/windows')
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

objsh.start_glibtcp_client('localhost', nretry=60)
import qtclient as qt
setup_windows()

if __name__ == "__main__":
    import gtk
    gtk.main()

