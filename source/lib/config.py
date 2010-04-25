import gobject
import os

# for backward compatibility to python 2.5
try:
    import json
except:
    import simplejson as json

import logging

class Config(gobject.GObject):
    '''
    Class to manage settings for the QTLab environment.
    '''

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
    }

    def __init__(self, filename):
        gobject.GObject.__init__(self)

        self._filename = filename
        self._config = {}
        self._defaults = {}
        self._save_hid = None

        self.load_defaults()
        self.load()

    def load_userconfig(self):
        filename = os.path.join(get_execdir(), 'userconfig.py')
        if os.path.exists(filename):
            logging.debug('Loading userconfig from %s', filename)
            execfile(filename, {'config': self})

    def setup_tempdir(self):
        '''Get directory for temporary files.'''

        dir = self.get('tempdir', None)

        if dir == None:
            dir = os.path.join(get_execdir(), 'tmp')
            self.set('tempdir', dir)
        if not os.path.exists(dir):
            os.makedirs(dir)

        return dir

    def _get_filename(self):
        return os.path.join(get_execdir(), self._filename)

    def load_defaults(self):
        self._defaults['execdir'] = get_execdir()
        self._defaults['datadir'] = os.path.join(get_execdir(), 'data')

    def save_defaults(self):
        return

    def load(self):
        '''
        Load settings.
        '''

        try:
            filename = self._get_filename()
            logging.debug('Loading settings from %s', filename)
            f = file(self._get_filename(), 'r')
            self._config = json.load(f)
            f.close()
        except Exception, e:
            logging.warning('Unable to load config file')
            self._config = {}

    def remove(self, remove_list, save=True):
        '''
        Remove settings from config file

        Input:
            remove_list [string] : list of items to remove
        '''

        for item in remove_list:
            if item in self._config:
                del self._config[item]

        if save:
            self.save()

    def save(self, delay=5):
        '''
        Save settings.

        'delay' specifies the delay (in seconds) to use to avoid saving
        too often.
        '''

        if delay == 0:
            self._do_save()
        elif self._save_hid is None:
            self._save_hid = gobject.timeout_add(delay * 1000, self._do_save)

    def _do_save(self):
        self._save_hid = None
        try:
            filename = self._get_filename()
            logging.debug('Saving settings to %s', filename)
            f = file(filename, 'w+')
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

_config = None

def create_config(filename):
    global _config
    _config = Config(filename)
    return _config

_execdir = os.getcwd()

def get_execdir():
    '''Get work directory we started in.'''
    global _execdir
    return _execdir

