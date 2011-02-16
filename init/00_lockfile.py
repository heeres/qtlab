from lib import config
_cfg = config.create_config('qtlab.cfg')
_cfg.load_userconfig()
_cfg.setup_tempdir()
del _cfg

import os
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

_lockname = os.path.join(config.get_execdir(), 'qtlab.lock')
lockfile.set_filename(_lockname)
del _lockname

msg = "QTlab already running, start with '-f' to force start.\n"
msg += "Press s<enter> to start anyway or just <enter> to quit."
lockfile.check_lockfile(msg)
import qtflow
register_exit(qtflow.qtlab_exit)
