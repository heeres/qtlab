import os
import sys
import config
from lib import temp
from lib.misc import exit_ipython

_remove_lock = True

def get_lockfile():
    return os.path.join(config.get_qtlabdir(), 'qtlab.lock')

def qtlab_exit():
    print "\nClosing QTlab..."

    try:
        qt.flow.exit_request()
    except:
        pass

    # Remove temporary files
    temp.File.remove_all()

    global _remove_lock
    if _remove_lock:
        try:
            os.remove(get_lockfile())
        except:
            pass

def _check_lockfile():
    if os.path.exists(get_lockfile()):
        if '-f' not in sys.argv:
            print "QTlab already running, start with '-f' to force start."
            print "Press s<enter> to start anyway or just <enter> to quit."

            line = sys.stdin.readline().strip()
            if line != 's':
                _remove_lock = False
                exit_ipython()
                sys.exit()

    onkill = [qtlab_exit]
    for cb in __IP.on_kill:
        onkill.append(cb)
    __IP.on_kill = onkill

    f = file(get_lockfile(), 'w+')
    f.close()

_check_lockfile()
