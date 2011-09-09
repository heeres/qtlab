from lib import config
_cfg = config.create_config('qtlab.cfg')
_cfg.load_userconfig()
_cfg.setup_tempdir()
del _cfg

import os
from lib import lockfile
from lib.misc import register_exit

_lockname = os.path.join(config.get_execdir(), 'qtlab.lock')
lockfile.set_filename(_lockname)
del _lockname

msg = "QTlab already running, start with '-f' to force start.\n"
msg += "Press s<enter> to start anyway or just <enter> to quit."
lockfile.check_lockfile(msg)

# Other functions should be registered using qt.flow.register_exit_handler
import qtflow
register_exit(qtflow.qtlab_exit)
