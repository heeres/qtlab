import os
import sys

_remove_lock = True

def qtlab_exit():
    print "Closing QTlab..."

    global _remove_lock
    if _remove_lock:
        try:
            os.remove('qtlab.lock')
        except:
            pass

sys.exitfunc = qtlab_exit

if os.path.exists('qtlab.lock'):
    print 'Argv: %s' % str(sys.argv)
    if '-f' not in sys.argv:
        print "QTlab already running, start with '-f' to force start"
        _remove_lock = False
        sys.exit()

f = file('qtlab.lock', 'w+')
f.close()
