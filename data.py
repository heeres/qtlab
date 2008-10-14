# data.py, class for handling measurement data
# Reinier Heeres <reinier@heeres.eu>
# Pieter de Groot <pieterdegroot@gmail.com>
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
import os
import time
import numpy
import types
import re
import logging

from misc import *
from gettext import gettext as _L

import qt
import config

def create_data_dir(datadir, datesubdir=True, timesubdir=True):
    path = datadir
    if datesubdir:
        path = os.path.join(path, time.strftime('%Y%m%d'))
    if timesubdir:
        path = os.path.join(path, time.strftime('%H%M%S'))

    if not os.path.isdir(path):
        os.makedirs(path)

    return path

def new_filename(name):
    tstr = time.strftime('%H%M%S')
    return '%s_%s.dat' % (tstr, name)

class Data(gobject.GObject):
    '''
    Data class
    '''

    __gsignals__ = {
        'new-data-point': (gobject.SIGNAL_RUN_FIRST,
                            gobject.TYPE_NONE,
                            ()),
        'new-data-block': (gobject.SIGNAL_RUN_FIRST,
                            gobject.TYPE_NONE,
                            ())
    }

    _METADATA_INFO = {
        'instrument': {
            're': re.compile('^#[ \t]*Ins?trument: ?(.*)$', re.I),
            'type': types.StringType
        },
        'parameter': {
            're': re.compile('^#[ \t]*Parameter: ?(.*)$', re.I),
            'type': types.StringType
        },
        'units': {
            're': re.compile('^#[ \t]*Units?: ?(.*)$', re.I),
            'type': types.StringType
        },
        'steps': {
            're': re.compile('^#[ \t]*Steps?: ?(.*)$', re.I),
            'type': types.IntType
        },
        'stepsize': {
            're': re.compile('^#[ \t]*Stepsizes?: ?(.*)$', re.I),
            'type': types.FloatType
        },
        'name': {
            're': re.compile('^#[ \t]*Name: ?(.*)$', re.I),
            'type': types.StringType
        },
        'type': {
            're': re.compile('^#[ \t]*Type?: ?(.*)$', re.I),
            'type': types.StringType,
            'function': lambda self, type: self._type_added(type)
        },
    }

    _META_STEPRE = re.compile('^#.*[ \t](\d+) steps', re.I)
    _META_COLRE = re.compile('^#.*Column ?(\d+)', re.I)
    _META_COMMENTRE = re.compile('^#(.*)', re.I)

    def __init__(self, filepath='', name='', data=None, infile=True, inmem=True, **kwargs):
        '''
        Create data object

        Input:
            filepath (string)
            name (string)
            data (numpy.array)
            infile (bool)
            inmem (bool)
        '''

        gobject.GObject.__init__(self)

        self._inmem = inmem
        self._options = kwargs

        # Dimension info
        self._dimensions = []

        # Number of coordinate dimensions
        self._ncoordinates = 0

        # Number of value dimensions
        self._nvalues = 0

        # Number of data points
        self._npoints = 0

        self._name = name
        self._comment = []
        self._timestamp = time.asctime()
        self._timemark = time.strftime('%H%M%S')
        self._datemark = time.strftime('%Y%m%d')

        if data is not None:
            self._data = data
            self._infile = False
        else:
            self._data = numpy.array([])
            self._infile = infile

        if filepath != '':
            self.set_filepath(filepath, inmem)
            self._infile = True
        else:
            self._dir = ''
            self._filename = ''
            self._infile = infile

    def __getitem__(self, index):
        return self._data[index]

    def __setitem__(self, index, val):
        self._data[index] = val

    def add_coordinate(self, name, **kwargs):
        '''
        Add a coordinate dimension. Use add_value() to add a value dimension.
        '''
        kwargs['name'] = name
        kwargs['type'] = 'coordinate'
        if 'size' not in kwargs:
            kwargs['size'] = 0
        self._ncoordinates += 1
        self._dimensions.append(kwargs)

    def add_value(self, name, **kwargs):
        '''
        Add a value dimension. Use add_dimension() to add a coordinate dimension.
        '''
        kwargs['name'] = name
        kwargs['type'] = 'value'
        self._nvalues += 1
        self._dimensions.append(kwargs)

    def add_comment(self, comment):
        self._comment.append(comment)

    def get_comment(self):
        return self._comment

    def add_data_point(self, *args, **kwargs):
        '''
        Add a new data point to the data set (in memory and/or on disk).

        Input:
            *args:
                n column values
            **kwargs:
                newblock (boolean): marks a new 'block' starts after this point

        Output:
            None
        '''

        if len(self._dimensions) == 0:
            logging.warning('add_data_point(): no dimensions specified, adding according to data')
            self._add_missing_dimensions(len(args))

        if len(args) < len(self._dimensions):
            logging.warning('add_data_point(): missing columns (%d < %d)' % \
                (len(args), len(self._dimensions)))
            return
        elif len(args) > len(self._dimensions):
            logging.warning('add_data_point(): too many columns (%d > %d)' % \
                (len(args), len(self._dimensions)))
            return

        if self._inmem:
            if len(self._data) == 0:
                self._data = numpy.atleast_2d(args)
            else:
                self._data = numpy.append(self._data, [args], axis=0)

        if self._infile:
            self._write_data_line(args)

        self._npoints += 1

        if 'newblock' in kwargs and kwargs['newblock']:
            self.new_block()
        else:
            self.emit('new-data-point')

    def new_block(self):
        if self._infile:
            self._file.write('\n')

        self._dimensions[self.get_ncoordinates() - 1]['size'] += 1

        self.emit('new-data-block')

    def get_data(self):
        '''
        Return data as a numpy.array.
        '''

        if not self._inmem and self._infile:
            self._load_file()

        if self._inmem:
            return self._data
        else:
            return None

    def get_dimensions(self):
        '''Return info for all dimensions.'''
        return self._dimensions

    def get_dimension_size(self, dim):
        '''Return size of dimensions dim'''

        if dim >= len(self._dimensions):
            return 0

        if 'size' in self._dimensions[dim]:
            return self._dimensions[dim]['size']
        else:
            return 0

    def get_ndimensions(self):
        '''Return number of dimensions.'''
        return len(self._dimensions)

    def get_coordinates(self):
        '''Return info for all coordinate dimensions.'''
        return self._dimensions[:self._ncoordinates]

    def get_ncoordinates(self):
        '''Return number of coordinate dimensions.'''
        return self._ncoordinates

    def get_values(self):
        '''Return info for all value dimensions.'''
        return self._dimensions[0:self._nvalues]

    def get_nvalues(self):
        '''Return number of value dimensions.'''
        return self._nvalues

    def get_npoints(self):
        '''Return number of data points'''
        return self._npoints

    def format_label(self, dim):
        '''Return a formatted label for dimensions dim'''

        if dim >= len(self._dimensions):
            return ''

        info = self._dimensions[dim]

        label = ''
        if 'name' in info:
            label += info['name']

        if 'instrument' in info and 'parameter' in info:
            label += ' (%s %s' % (info['instrument'], info['parameter'])
            if 'units' in info:
                label += ' [%s]' % info['units']
            label += ')'

        elif 'name' not in info:
            label = 'dim%d' % dim

        return label

    def get_filename(self):
        return self._filename

    def get_dir(self):
        return self._dir

    def get_filepath(self):
        return os.path.join(self._dir, self._filename)

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    def get_time_name(self):
        return '%s_%s' % (self._timemark, self._name)

    def get_settings_filepath(self):
        fn, ext = os.path.splitext(self.get_filepath())
        return fn + '.set'

    def set_filepath(self, fp, inmem=True):
        self._dir, self._filename = os.path.split(fp)
        if inmem:
            if self._load_file():
                self._inmem = True
            else:
                self._inmem = False

    def _type_added(self, name):
        if name == 'coordinate':
            self._ncoordinates += 1
        elif name == 'values':
            self._nvalues += 1

    def _parse_meta_data(self, line):
        m = self._META_STEPRE.match(line)
        if m is not None:
            self._dimensions.append(int(m.group(1)))
            return True

        m = self._META_COLRE.match(line)
        if m is not None:
            index = int(m.group(1))
            if index > len(self._dimensions):
                self._dimensions.append({})
            return True

        colnum = len(self._dimensions) - 1

        for tagname, metainfo in self._METADATA_INFO.iteritems():
            m = metainfo['re'].match(line)
            if m is not None:
                if metainfo['type'] == types.FloatType:
                    self._dimensions[colnum][tagname] = float(m.group(1))
                elif metainfo['type'] == types.IntType:
                    self._dimensions[colnum][tagname] = int(m.group(1))
                else:
                    self._dimensions[colnum][tagname] = m.group(1)

                if 'function' in metainfo:
                    metainfo['function'](self, m.group(1))

                return True

        m = self._META_COMMENTRE.match(line)
        if m is not None:
            self._comment.append(m.group(1))

    def _detect_dimensions_size(self):
        for colnum in range(self.get_ncoordinates()):
            opt = self._dimensions[colnum]
            if 'size' in opt and opt['size'] > 0:
                dimsize = opt['size']
            elif 'steps' in opt:
                dimsize = opt['steps']
            else:
                vals = []
                for i in xrange(len(self._data)):
                    if self._data[i][colnum] not in vals:
                        vals.append(self._data[i][colnum])
                dimsize = len(vals)

            logging.info('Column %d has size %d', colnum, dimsize)
            opt['size'] = dimsize

    def _add_missing_dimensions(self, nfields):
        '''
        Add extra dimensions so that the total equals nfields.
        Only the last field will be tagged as a value, the rest will be
        coordinates.
        '''

        # Add info for (assumed coordinate) columns that had no metadata
        while self.get_ndimensions() < nfields - 1:
            self.add_coordinate('col%d' % (self.get_ndimensions() + 1))

        # Add info for (assumed value) column that had no metadata
        if self.get_ndimensions() < nfields:
            self.add_value('col%d' % (self.get_ndimensions() + 1))

        # If types are not specified assume all except one are coordinates
        if self.get_ncoordinates() == 0 and nfields > 1:
            self._ncoordinates = nfields - 1
            self._nvalues = 1

    def _load_file(self):
        """
        Load data from file and store internally.
        """

        try:
            f = file(self.get_filepath(), 'r')
        except:
            logging.warning('Unable to open file %s' % self.get_filepath())
            return False

        self._dimensions = []
        self._values = []
        self._comment = []
        data = []
        nfields = 0

        for line in f:
            line = line.rstrip(' \n\t\r')

            # Strip comment
            commentpos = line.find('#')
            if commentpos != -1:
                self._parse_meta_data(line)
                line = line[:commentpos]

            fields = line.split()
            if len(fields) > nfields:
                nfields = len(fields)

            fields = [float(f) for f in fields]
            if len(fields) > 0:
                data.append(fields)

        self._add_missing_dimensions(nfields)

        self._data = numpy.array(data)
        self._npoints = len(self._data)
        self._inmem = True

        self._detect_dimensions_size()

        return True

    def _write_settings_file(self):
        fn = self.get_settings_filepath()
        f = open(fn)
        f.write('Filename: %s\n', self._filename)
        f.write('Timestamp: %s\n\n', self._timestamp)

        inslist = dict_to_ordered_tuples(qt.instruments)
        for (iname, ins) in inslist:
            write('Instrument: %s\n' % iname)
            parlist = dict_to_ordered_tuples(ins.get_parameters())
            for (param, popts) in parlist:
                f.write('\t%s: %s\n' % (param, ins.get(param, query=False)))

        f.close()

    def _write_header(self):
        self._file.write('# Filename: %s\n' % self._filename)
        self._file.write('# Timestamp: %s\n\n' % self._timestamp)
        for line in self._comment:
            self._file.write('# %s\n' % line)

        i = 1
        for dim in self._dimensions:
            self._file.write('# Column %d:\n' % i)
            for key, val in dict_to_ordered_tuples(dim):
                self._file.write('#\t%s: %s\n' % (key, val))
            i += 1

        self._file.write('\n')

    def _write_data_line(self, args):
        line = str(args[0])
        for i in args[1:]:
            line += '\t%f' % i
        line += '\n'
        self._file.write(line)
        self._file.flush()

    def _write_data(self):
        if not self._inmem:
            logging.warning('Unable to _write_data() without having it memory')
            return False

        for vals in self._data:
            self._write_data_line(vals)

    def create_file(self, name=None, filepath=None):
        '''
        Create a new data file and leave it open.

        This function should be called after adding the comment and the
        coordinate and value metadata, because it writes the file header.
        '''

        if name is None and filepath is None:
            name = self._name

        if filepath is None:
            self._dir = create_data_dir(qt.config['datadir'])
            self._filename = new_filename(name)
        else:
            self._dir, self._filename = os.path.split(filepath)

        try:
            self._file = open(self.get_filepath(), 'w+')
        except:
            logging.error('Unable to open file')
            return False

        self._write_header()

        return True

    def close_file(self):
        '''
        Close open data file.
        '''

        if self._file is not None:
            self._file.close()
            self._file = None

    def write_file(self, name=None, filepath=None):
        '''
        Create and write a new data file.
        '''

        if not self.create_file():
            return

        self._write_data()
        self.close_file()

        self._write_settings_file()

def slice(data, coords, vals):
    """
    Return new data object with a slice of the given data set
    """
