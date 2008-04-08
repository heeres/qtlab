import gobject
import simplejson

class QTConfig(gobject.GObject):
    '''
    Class to manage settings for the QTLab environment.
    '''

    CONFIG_FILE = 'qtlab.cfg'

    def __init__(self):
        gobject.GObject.__init__(self)

        self._config = {}
        self._defaults = {}

        self.load_defaults()
        self.load()

    def load_defaults(self):
        self._defaults['test'] = True
        self._defaults['datadir'] = './data'

    def save_defaults(self):
        return

    def load(self):
        '''
        Load settings.
        '''

        f = file(self.CONFIG_FILE, 'r')

        try:
            self._config = simplejson.load(f)
        except Exception, e:
            self._config = {}

        f.close()

    def save(self):
        '''
        Save settings.
        '''

        f = file(self.CONFIG_FILE, 'w+')
        simplejson.dump(self._config, f, indent=4)
        f.close()

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, val):
        self.set(key, val)

    def get(self, key, default=None):
        '''
        Get configuration variable.

        Input:
            key (string): variable name
            default (any type): default variable value

        Output:
            None
        '''

        if key in self._config:
            return self._config[key]
        elif default is not None:
            return default
        elif key in self._defaults:
            return self._defaults[key]
        else:
            return None

    def set(self, key, val):
        '''
        Set configuration variable.

        Input:
            key (string): variable name
            val (any type): variable value

        Output:
            None
        '''

        self._config[key] = val


_config = None

def get_config():
    global _config
    if _config is None:
        _config = QTConfig()
    return _config
