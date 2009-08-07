import gobject
import os

# for backward compatibility to python 2.5
try:
    import json
except:
    import simplejson as json

import logging

class QTConfig(gobject.GObject):
    '''
    Class to manage settings for the QTLab environment.
    '''

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
    }

    CONFIG_FILE = 'qtlab.cfg'

    def __init__(self):
        gobject.GObject.__init__(self)

        self._config = {}
        self._defaults = {}

        self.load_defaults()
        self.load()

    def _get_filename(self):
        return os.path.join(get_qtlabdir(), self.CONFIG_FILE)

    def load_defaults(self):
        self._defaults['test'] = True
        self._defaults['datadir'] = os.path.join(get_qtlabdir(), 'data')

    def save_defaults(self):
        return

    def load(self):
        '''
        Load settings.
        '''

        try:
            f = file(self._get_filename(), 'r')
            self._config = json.load(f)
            f.close()
        except Exception, e:
            logging.warning('Unable to load config file')
            self._config = {}

    def save(self):
        '''
        Save settings.
        '''

        try:
            f = file(self._get_filename(), 'w+')
            json.dump(self._config, f, indent=4, sort_keys=True)
            f.close()
        except Exception, e:
            logging.warning('Unable to save config file')

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, val):
        self.set(key, val)

    def get(self, key, default=None):
        '''
        Get configuration variable. If it is not defined, return the default
        value. In this case, the variable will be set to this default to
        ensure consistency.

        Input:
            key (string): variable name
            default (any type): default variable value

        Output:
            None
        '''

        if key in self._config:
            return self._config[key]
        elif default is not None:
            self._config[key] = default
            return default
        elif key in self._defaults:
            val = self._defaults[key]
            self._config[key] = val
            return val
        else:
            return None

    def set(self, key, val, save=True):
        '''
        Set configuration variable.

        Input:
            key (string): variable name
            val (any type): variable value

        Output:
            None
        '''

        self._config[key] = val
        if save:
            self.save()

        self.emit('changed', {key: val})

    def get_all(self):
        return self._config

def get_config():
    '''Get configuration object.'''
    return _config

def get_qtlabdir():
    '''Get work directory we started in.'''
    return _qtlab_dir

def get_tempdir():
    '''Get directory for temporary files.'''
    dir = _config.get('tempdir', None)
    if dir == None:
        dir = os.path.join(get_qtlabdir(), 'tmp')
        _config['tempdir'] = dir
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir

_qtlab_dir = os.path.split(os.path.dirname(__file__))[0]
_config = QTConfig()
_config['qtlabdir'] = _qtlab_dir

# Load user defined configuration
if os.path.exists(os.path.join(get_qtlabdir(), 'userconfig.py')):
    execfile(os.path.join(get_qtlabdir(), 'userconfig.py'), {'config': _config})

get_tempdir()
