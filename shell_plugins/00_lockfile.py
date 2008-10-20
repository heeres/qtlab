import os
import sys
import config

_remove_lock = True

def get_lockfile():
    return os.path.join(config.get_workdir(), 'qtlab.lock')

def qtlab_exit():
    print "Closing QTlab..."

    global _remove_lock
    if _remove_lock:
        try:
            os.remove(get_lockfile())
        except:
            pass

sys.exitfunc = qtlab_exit

if os.path.exists(get_lockfile()):
    if '-f' not in sys.argv:
        print "QTlab already running, start with '-f' to force start."
        print "Press s<enter> to start anyway or just <enter> to quit."

        line = sys.stdin.readline().strip()
        if line != 's':
            _remove_lock = False
            sys.exit()

f = file('qtlab.lock', 'w+')
f.close()
