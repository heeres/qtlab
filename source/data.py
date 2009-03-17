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

from gettext import gettext as _L

import qt
from lib import namedlist, temp
from lib.misc import dict_to_ordered_tuples, get_arg_type
from lib.calltimer import ThreadSafeGObject

def create_data_dir(datadir, name=None, ts=None, datesubdir=True, timesubdir=True):
    '''
    Create and return a new data directory.

    Input:
        datadir (string): base directory
        name (string): optional name of measurement
        ts (time.localtime()): timestamp which will be used if timesubdir=True
        datesubdir (bool): whether to create a subdirectory for the date
        timesubdir (bool): whether to create a subdirectory for the time

    Output:
        The directory to place the new file in
    '''

    path = datadir
    if ts is None:
        ts = time.localtime()
    if datesubdir:
        path = os.path.join(path, time.strftime('%Y%m%d', ts))
    if timesubdir:
        tsd = time.strftime('%H%M%S', ts)
        if name is not None:
            tsd += '_' + name
        path = os.path.join(path, tsd)

    if not os.path.isdir(path):
        os.makedirs(path)

    return path

def new_filename(name, ts=None):
    '''Return a new filename, based on name and timestamp.'''

    if ts is None:
        ts = time.localtime()
    tstr = time.strftime('%H%M%S', ts)
    return '%s_%s.dat' % (tstr, name)

class _DataList(namedlist.NamedList):
    def __init__(self, time_name=False):
        namedlist.NamedList.__init__(self, base_name='data')

        self._time_name = time_name

    def new_item_name(self, item, name):
        '''Function to generate a new item name.'''

        if name == '':
            self._auto_counter += 1
            name = self._base_name + str(self._auto_counter)

        if self._time_name:
            return item.get_time_name()
        else:
            return name

class Data(ThreadSafeGObject):
    '''
    Data class
    '''

    _data_list = _DataList()

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

    _INT_TYPES = (
            types.IntType, types.LongType,
            numpy.int, numpy.int0, numpy.int8,
            numpy.int16, numpy.int32, numpy.int64,
    )

    def __init__(self, *args, **kwargs):
        '''
        Create data object. There are three different uses:
        1) create an empty data object for use in a measurement
        2) create a data object and fill immediately with a numpy array
        3) create a data object from an existing data file

        All inputs are optional.
        The 'name' input is used in an internal list (accessable through
        qt.data). If omitted, a name will be auto generated.
        This 'name' will also be used later to auto generate a filename
        when calling 'create_file()' (if that is called without options).
        The input 'filename' here is only used for loading an existing file.

        args input:
            filename (string), set the filename to load.
            data (numpy.array), array to construct data object for

        kwargs input:
            name (string), default will be 'data<n>'
            infile (bool), default True
            inmem (bool), default False if no file specified, True otherwise
            tempfile (bool), default False. If True create a temporary file
                for the data.
        '''

        ThreadSafeGObject.__init__(self)

        name = kwargs.get('name', '')
        infile = kwargs.get('infile', True)
        inmem = kwargs.get('inmem', False)

        self._inmem = inmem
        self._tempfile = kwargs.get('tempfile', False)
        self._options = kwargs
        self._file = None

        # Dimension info
        self._dimensions = []
        self._block_sizes = []

        # Number of coordinate dimensions
        self._ncoordinates = 0

        # Number of value dimensions
        self._nvalues = 0

        # Number of data points
        self._npoints = 0
        self._npoints_last_block = 0
        self._npoints_max_block = 0

        self._comment = []
        self._timestamp = time.asctime()
        self._localtime = time.localtime()
        self._timemark = time.strftime('%H%M%S', self._localtime)
        self._datemark = time.strftime('%Y%m%d', self._localtime)

        # FIXME: the name generation here is a bit nasty
        name = Data._data_list.new_item_name(self, name)
        self._name = name

        data = get_arg_type(args, kwargs,
                (numpy.ndarray, list, tuple),
                'data')
        if data is not None:
            self.set_data(data)
        else:
            self._data = numpy.array([])
            self._infile = infile

        filepath = get_arg_type(args, kwargs, types.StringType, 'filepath')
        if self._tempfile:
            self.create_tempfile(filepath)
        elif filepath is not None and filepath != '':
            if 'inmem' not in kwargs:
                inmem = True
            self.set_filepath(filepath, inmem)
            self._infile = True
        else:
            self._dir = ''
            self._filename = ''
            self._infile = infile

        Data._data_list.add(name, self)

        try:
            qt.flow.connect('stop-request', self._stop_request_cb)
        except:
            pass

    def __repr__(self):
        ret = "Data '%s', filename '%s'" % (self._name, self._filename)
        return ret

    def __getitem__(self, index):
        return self._data[index]

    def __setitem__(self, index, val):
        self._data[index] = val

### Data info

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

    def get_npoints_max_block(self):
        '''Return the maximum number of data points in a block.'''
        return self._npoints_max_block

    def get_npoints_last_block(self):
        '''Return number of data points in most recent block'''
        return self.get_block_size(self.get_nblocks() - 1)

    def get_nblocks(self):
        '''Return number of blocks.'''
        nblocks = len(self._block_sizes)
        if self._npoints_last_block > 0:
            return nblocks + 1
        else:
            return nblocks

    def get_nblocks_complete(self):
        '''Return number of completed blocks.'''
        return len(self._block_sizes)

    def get_block_size(self, blockid):
        if blockid == len(self._block_sizes):
            return self._npoints_last_block
        elif blockid < 0 or blockid > len(self._block_sizes):
            return 0
        else:
            return self._block_sizes[blockid]

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

### File info

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

    def is_file_open(self):
        '''Return whether a file is open or not.'''

        if self._file is not None:
            return True
        else:
            return False

### Measurement info

    def add_coordinate(self, name, **kwargs):
        '''
        Add a coordinate dimension. Use add_value() to add a value dimension.

        Input:
            name (string): the name for this coordinate
            kwargs: you can add any info here, but predefined are:
                size (int): the size of this dimension
                instrument (Instrument): instrument this coordinate belongs to
                parameter (string): parameter of the instrument
                units (string): units of this coordinate
                precision (int): precision of stored data, default is
                    'default_precision' from config, or 12 if not defined.
                format (string): format of stored data, not used by default
        '''

        kwargs['name'] = name
        kwargs['type'] = 'coordinate'
        if 'size' not in kwargs:
            kwargs['size'] = 0
        self._ncoordinates += 1
        self._dimensions.append(kwargs)

    def add_value(self, name, **kwargs):
        '''
        Add a value dimension. Use add_dimension() to add a coordinate
        dimension.

        Input:
            name (string): the name for this coordinate
            kwargs: you can add any info here, but predefined are:
                instrument (Instrument): instrument this coordinate belongs to
                parameter (string): parameter of the instrument
                units (string): units of this coordinate
                precision (int): precision of stored data, default is
                    'default_precision' from config, or 12 if not defined.
                format (string): format of stored data, not used by default
        '''
        kwargs['name'] = name
        kwargs['type'] = 'value'
        self._nvalues += 1
        self._dimensions.append(kwargs)

    def add_comment(self, comment):
        '''Add comment to the Data object.'''
        self._comment.append(comment)

    def get_comment(self):
        '''Return the comment for the Data object.'''
        return self._comment

### File writing

    def create_file(self, name=None, filepath=None, settings_file=True):
        '''
        Create a new data file and leave it open. In addition a
        settings file is generated, unless settings_file=False is
        specified.

        This function should be called after adding the comment and the
        coordinate and value metadata, because it writes the file header.
        '''

        if name is None and filepath is None:
            name = self._name

        if filepath is None:
            self._dir = create_data_dir(qt.config['datadir'], \
                name=name, ts=self._localtime)
            self._filename = new_filename(name, ts=self._localtime)
        else:
            self._dir, self._filename = os.path.split(filepath)

        try:
            self._file = open(self.get_filepath(), 'w+')
        except:
            logging.error('Unable to open file')
            return False

        self._write_header()

        if settings_file:
            self._write_settings_file()

        return True

    def close_file(self):
        '''
        Close open data file.
        '''

        if self._file is not None:
            self._file.close()
            self._file = None

    def _write_settings_file(self):
        fn = self.get_settings_filepath()
        f = open(fn, 'w+')
        f.write('Filename: %s\n' % self._filename)
        f.write('Timestamp: %s\n\n' % self._timestamp)

        inslist = dict_to_ordered_tuples(qt.instruments.get_instruments())
        for (iname, ins) in inslist:
            f.write('Instrument: %s\n' % iname)
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

    def _format_data_value(self, val, colnum):
        if type(val) in self._INT_TYPES:
            return '%d' % val

        if colnum < len(self._dimensions):
            opts = self._dimensions[colnum]
            if 'format' in opts:
                return opts['format'] % val
            elif 'precision' in opts:
                format = '%%.%de' % opts['precision']
                return format % val

        precision = qt.config.get('default_precision', 12)
        format = '%%.%de' % precision
        return format % val

    def _write_data_line(self, args):
        '''
        Write a line of data.
        Args can be a single value or an numpy.array / list / tuple.
        '''

        if hasattr(args, '__len__'):
            if len(args) > 0:
                line = self._format_data_value(args[0], 0)
                for colnum in range(1, len(args)):
                    line += '\t%s' % \
                            self._format_data_value(args[colnum], colnum)
            else:
                line = ''
        else:
            line = self._format_data_value(args, 0)

        line += '\n'
        self._file.write(line)
        self._file.flush()

    def _get_block_columns(self):
        blockcols = []
        for i in range(self.get_ncoordinates()):
            if len(self._data) > 1 and self._data[0][i] == self._data[1][i]:
                blockcols.append(True)
            else:
                blockcols.append(False)
        for i in range(self.get_nvalues()):
            blockcols.append(False)

        return blockcols

    def _write_data(self):
        if not self._inmem:
            logging.warning('Unable to _write_data() without having it memory')
            return False

        blockcols = self._get_block_columns()

        lastvals = None
        for vals in self._data:
            if type(vals) is numpy.ndarray and lastvals is not None:
                for i in range(len(vals)):
                    if blockcols[i] and vals[i] != lastvals[i]:
                        self._file.write('\n')

            self._write_data_line(vals)
            lastvals = vals

### High-level file writing

    def write_file(self, name=None, filepath=None):
        '''
        Create and write a new data file.
        '''

        if not self.create_file():
            return

        self._write_data()
        self.close_file()

    def create_tempfile(self, path=None):
        '''
        Create a temporary file, optionally called <path>.
        '''

        self._file = temp.File(path)

        try:
            self._write_data()
            self._dir, self._filename = os.path.split(self._file.name)
            self._file.close()
            self._tempfile = True
        except Exception, e:
            logging.warning('Error creating temporary file: %s', e)
            self._dir = ''
            self._filename = ''
            self._tempfile = False

### Adding data

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
        self._npoints_last_block += 1
        if self._npoints_last_block > self._npoints_max_block:
            self._npoints_max_block = self._npoints_last_block

        if 'newblock' in kwargs and kwargs['newblock']:
            self.new_block()
        else:
            self.emit('new-data-point')

    def new_block(self):
        '''Start a new data block.'''

        if self._infile:
            self._file.write('\n')

        self._dimensions[self.get_ncoordinates() - 1]['size'] += 1
        self._block_sizes.append(self._npoints_last_block)
        self._npoints_last_block = 0

        self.emit('new-data-block')

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

### Set array data

    def set_data(self, data):
        '''
        Set data, can be a numpy.array or a list / tuple. The latter will be
        converted to a numpy.array.
        '''

        if not isinstance(data, numpy.ndarray):
            data = numpy.array(data)
        self._data = data
        self._inmem = True
        self._infile = False
        self._npoints = len(self._data)

        # Add dimension information
        if len(data.shape) == 1:
            self.add_value('Y')
        elif len(data.shape) == 2:
            if data.shape[1] == 2:
                self.add_coordinate('X')
                self.add_value('Y')
            elif data.shape[1] == 3:
                self.add_coordinate('X')
                self.add_coordinate('Y')
                self.add_value('Z')
            else:
                for i in range(data.shape[1]):
                    self.add_coordinate('col%d' % i)

### File reading

    def _count_coord_val_dims(self):
        self._ncoordinates = 0
        self._nvalues = 0
        for info in self._dimensions:
            if info.get('type', 'coordinate') == 'coordinate':
                self._ncoordinates += 1
            else:
                self._nvalues += 1
        if self._nvalues == 0 and self._ncoordinates > 0:
            self._nvalues = 1
            self._ncoordinates -= 1

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

        self._block_sizes = []
        self._npoints = 0
        self._npoints_last_block = 0
        self._npoints_max_block = 0

        blocksize = 0

        for line in f:
            line = line.rstrip(' \n\t\r')

            # Count blocks
            if len(line) == 0 and len(data) > 0:
                self._block_sizes.append(blocksize)
                if blocksize > self._npoints_max_block:
                    self._npoints_max_block = blocksize
                blocksize = 0

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
                blocksize += 1

        self._add_missing_dimensions(nfields)
        self._count_coord_val_dims()

        self._data = numpy.array(data)
        self._npoints = len(self._data)
        self._inmem = True

        self._npoints_last_block = blocksize

        self._detect_dimensions_size()

        return True

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
        ncoords = self.get_ncoordinates()
        for colnum in range(ncoords):
            if colnum >= len(self._dimensions):
                return False

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

        if self._data is not None:
            newshape = []
            for colnum in range(ncoords):
                opt = self._dimensions[colnum]
                newshape.append(opt['size'])

            newshape.append(self.get_ndimensions())
            try:
                self._data = self._data.reshape(newshape)
                logging.warning('Data reshaped, but axis might be reversed.')
            except Exception, e:
                print 'Unable to reshape array: %s' % e

        return True

    def set_filepath(self, fp, inmem=True):
        self._dir, self._filename = os.path.split(fp)
        if inmem:
            if self._load_file():
                self._inmem = True
            else:
                self._inmem = False

### Misc

    def _stop_request_cb(self, sender):
        '''Called when qtflow emits a stop-request.'''
        self.close_file()

    @staticmethod
    def get_named_list():
        return Data._data_list

    @staticmethod
    def get(name):
        return Data._data_list.get(name)

def slice(data, coords, vals):
    """
    Return new data object with a slice of the given data set
    """
