import os
import config
from lib import lockfile
from lib.misc import register_exit

def qtlab_exit():
    print "\nClosing QTlab..."

    import lib.temp
    try:
        qt.flow.exit_request()
    except:
        pass

    # Remove temporary files
    lib.temp.File.remove_all()
    lockfile.remove_lockfile()

_lockname = os.path.join(config.get_qtlabdir(), 'qtlab.lock')
lockfile.set_filename(_lockname)

msg = "QTlab already running, start with '-f' to force start.\n"
msg += "Press s<enter> to start anyway or just <enter> to quit."
lockfile.check_lockfile(msg)
register_exit(qtlab_exit)
