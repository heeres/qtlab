import gobject
import simplejson

import os

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

    def load_defaults(self):
        self._defaults['test'] = True
        self._defaults['datadir'] = './data'

    def save_defaults(self):
        return

    def load(self):
        '''
        Load settings.
        '''

        try:
            f = file(self.CONFIG_FILE, 'r')
            self._config = simplejson.load(f)
            f.close()
        except Exception, e:
            logging.warning('Unable to load config file')
            self._config = {}

    def save(self):
        '''
        Save settings.
        '''

        try:
            f = file(self.CONFIG_FILE, 'w+')
            simplejson.dump(self._config, f, indent=4, sort_keys=True)
            f.close()
        except Exception, e:
            logging.warning('Unable to save config file')

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

_config = None
_work_dir = os.getcwd()

def get_config():
    '''Get configuration object.'''
    global _config
    if _config is None:
        _config = QTConfig()
    return _config

def get_workdir():
    '''Get work directory we started in.'''
    global _work_dir
    return _work_dir
