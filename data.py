# data.py, Data class
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gobject
from gettext import gettext as _
import os
import time

import instruments

import config

class Data(gobject.GObject):
    '''
    This class should take care of all your data saving needs.
    '''

    __gsignals__ = {
        'new-data-point': (gobject.SIGNAL_RUN_FIRST,
                            gobject.TYPE_NONE,
                            ()),
        'new-data-block': (gobject.SIGNAL_RUN_FIRST,
                            gobject.TYPE_NONE,
                            ())
    }
                           # [gobject.TYPE_PYOBJECT]

    def __init__(self, basedir=None):
        gobject.GObject.__init__(self)

        if basedir is None:
            basedir = config.get_config()['datadir']

        if not os.path.isdir(basedir):
            raise ValueError("directory '%s' doest not exist" % basedir)
        self._basedir = basedir

        self._instruments = instruments.get_instruments()

    def create_datafile(self, filename, datesubdir=True):
        '''
        Create a new data file.

        Input:
            filename (string): defines the data file name (without extension)

        Output:
            None
        '''

        if datesubdir:
            dstr = time.strftime('%Y%m%d')
            self._subdir = dstr
        else:
            self._subdir = ''

        path = os.path.join(self._basedir, self._subdir)
        if not os.path.isdir(path):
            os.makedirs(path)
        self._fulldir = path

        tstr = time.strftime('%H%M%S')
        self._filename = tstr + '_' + filename

        self._timestamp = time.asctime()
        self.create_settings_file(self._filename)

        header_text  = '# Filename: %s.dat\n' % self._filename
        header_text += '# Timestamp: %s\n\n' % self._timestamp

        self._file = file('%s/%s.dat' % (self._fulldir, self._filename), 'w+')
        self._file.write(header_text)
        self._file.flush()

        self._col_nr = 0
        self._col_info = []

        self._line_nr = 0
        self._block_nr = 0

    def create_settings_file(self, filename):
        '''
        Create the 'settings file' which is simply a dump of all the
        instrument settings to a file.

        Input:
            filename (string): name of settings file (without extension)

        Output:
            None
        '''

        header  = '# Filename: %s.set\n' % filename
        header += '# Timestamp: %s\n\n' % self._timestamp

        text = ''
        for (iname, ins) in self._instruments.get_instruments().iteritems():
            text += 'Instrument: %s\n' % iname
            for (param, popts) in ins.get_parameters().iteritems():
                text += '\t%s: %s\n' % (param, ins.get(param, query=False))

        fname = '%s/%s.set' % (self._fulldir, filename)
        settings_file = file(fname, 'w+')
        settings_file.write(header)
        settings_file.write(text)
        settings_file.close()

    def add_column_to_header(self, instrument, parameter, units=None):
        '''
        Create the header of the data file. It is called for each collumn
        of data that will be in the data file.

        Input:
            instrument (string): name of instrument
            parameter (string): name of parameter

        Output:
            None
        '''

        if self._instruments.get_instruments().has_key(instrument):
            ins = self._instruments.get(instrument)

            if not ins.get_parameters().has_key(parameter):
                print __name__ + ': Adding column, but instrument "%s" does not have parameter "%s"' % (instrument, parameter)
            elif units is None:
                if ins.get_parameter_options(parameter).has_key('units'):
                    units = ins.get_parameter_options(parameter)['units']

        else:
            print __name__ + ': Adding column, but instrument "%s" does not exist' % instrument

        if units is None:
            print __name__ + ': Added column, but unit is not defined for parameter "%s" of instrument "%s"' % (parameter, instrument)
            units = _('Undefined')

        self._col_nr += 1
        self._col_info.append({
            'instrument': instrument,
            'parameter': parameter,
            'units': units})

        text  = '# Column %i:\n' % self._col_nr
        text += '# \t Intrument: %s\n' % instrument
        text += '# \t Parameter: %s\n' % parameter
        text += '# \t Unit: %s\n\n' % units

        self._file.write(text)

    def add_comment_to_header(self, comment):
        '''
        Add comment in the header of the data file.

        Input:
            comment (string): text that you would like in the header

        Output:
            None
        '''

        self._file.write('# ' + comment + '\n\n')

    def add_data_point(self, *values):
        '''
        Add a new line to the data file with the values seperated by tabs.
        It will also emit a signal for possible data plots.

        Input:
            *values (numbers): a list of comma separated values

        Output:
            None
        '''

        line = ''
        for i in values:
            line += str(i) + '\t'
        self._file.write(line + '\n')
        self._file.flush()
        self._line_nr += 1
        self.emit('new-data-point')

    def new_data_block(self):
        '''
        Put an empty line in the data file (useful for gnuplot 3d plotting)

        Input:
            None

        Output:
            None
        '''

        self._file.write('\n')
        self._block_nr += 1
        self._line_nr = 0
        self.emit('new-data-block')

    def close_datafile(self):
        '''
        Close the data file.

        Input:
            None

        Output:
            None
        '''

        self._file.close()

    def get_filename(self):
        return self._filename

    def get_fulldir(self):
        return self._fulldir

    def get_subdir(self):
        return self._subdir

    def get_basedir(self):
        return self._basedir

    def get_line_nr(self):
        return self._line_nr

    def get_block_nr(self):
        return self._block_nr

    def get_col_info(self):
        return self._col_info
