# hdf5_data.py, handling data in hdf5 container
#
# Wolfgang Pfaff <wolfgangpfff@gmail.com>
# Reinier Heeres <reinier@heeres.eu>
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

"""
Module providing handling of HDF5 data within qtlab.

Contains:
- a data class (HDF5Data) which is essentially a wrapper of a h5py data
  object, adapted for usage with qtlab
- name generators in the style of qtlab Data objects
- functions to create standard data sets
"""

import gobject
import os
import time
import h5py
import logging
import numpy as np

from lib.config import get_config
config = get_config()
in_qtlab = config.get('qtlab', False)
from lib.network.object_sharer import SharedGObject, cache_result

if in_qtlab:
    import qt

import data

class DateTimeGenerator(data.DateTimeGenerator):

    def new_filename(self, data_obj):
        base, ext = os.path.splitext(data.DateTimeGenerator.new_filename(
            self, data_obj))
        return base + '.hdf5'

class DataGroup(SharedGObject):
    """
    A data group consists of a set of arrays that will be saved together
    in a group inside a HDF5 container.

    At the moment this does not have too many improvements over using just the
    bare container, but the concept should be useful for plotting, ensuring
    correct dimensionalities, etc.
    """

    def __init__(self, name, hdf5_data, base='/', **kw):
        self.name = name
        self.h5d = hdf5_data._file
        self.base = base
        self.groupname = base + name
        self._filepath = hdf5_data.get_filepath()
        self._folder = hdf5_data.get_folder()

        if self.name in self.h5d[base].keys():
            self.group = self.h5d[base]
        else:
            self.group = self.h5d.create_group(self.groupname)

        # all kws are interpreted as meta data
        for k in kw:
            self.group.attrs[k] = kw[k]

    def __getitem__(self, name):
        return self.group[name].value

    def __setitem__(self, name, val):
        if name in self.group.keys():

            # store old attributes
            attrs = dict(self.group[name].attrs)

            # delete and re-create; overwrite doesn't work with hdf5
            del self.group[name]
            dim = self.group.create_dataset(name, data=val)
            for k, v in attrs.iteritems():
                dim.attrs[k] = v

            return True

        # not sure whether this behavior makes sense, wild guess ATM
        else:
            logging.error("Unknown dimension '%s'. Please use add_dimension."\
                    % name)
            return False

    def get_filepath(self):
        return self._filepath

    def get_folder(self):
        return self._folder

    def add_dimension(self, name, dim_type, data, **meta):
        '''
        Add a dimension to the data group.
        dim_type is not restricted, but 'coordinate' and 'value' should be
        used to specify what the dimension represents.
        Extra keywords are added as meta data.
        '''

        if name in self.group.keys():
            logging.error("Dimension '%s' already exists in data set '%s'" \
                    % (name, self.name))
            return False

        if data is None:
            data = np.array([np.NaN])

        dim = self.group.create_dataset(name, data=data)
        dim.attrs['dim_type'] = dim_type

        for k in meta:
            dim.attrs[k] = meta[k]

        return True

    def add(self, name, data=None, **meta):
        '''
        Add an unspecified dimension, optionally with known data.
        Extra keywords are added as meta data.
        '''
        return self.add_dimension(name, 'unspecified', data, **meta)

    def add_coordinate(self, name, data=None, **meta):
        '''
        Add a coordinate dimension, optionally with known data.
        Extra keywords are added as meta data.
        '''
        return self.add_dimension(name, 'coordinate', data, **meta)

    def add_value(self, name, data=None, **meta):
        '''
        Add a value dimension, optionally with known data.
        Extra keywords are added as meta data.
        '''
        return self.add_dimension(name, 'value', data, **meta)

    def loop1d_data(self, *args, **kwargs):
        kwargs['group'] = self
        return loop1d_data(*args, **kwargs)

    def loop2d_data(self, *args, **kwargs):
        kwargs['group'] = self
        return loop2d_data(*args, **kwargs)

class HDF5Data:

    _data_list = data.Data._data_list
    _filename_generator = DateTimeGenerator()

    def __init__(self, *args, **kwargs):
        """
        Creates an empty data set including the file, for which the currently
        set file name generator is used.

        kwargs:
            name (string) : default is 'data'
        """

        # FIXME: the name generation here is a bit nasty
        name = kwargs.get('name', 'data')
        name = data.Data._data_list.new_item_name(self, name)
        self._name = name

        filepath = kwargs.get('filepath, None')
        if filepath:
            self._filepath = filepath

        else:
            self._localtime = time.localtime()
            self._timestamp = time.asctime(self._localtime)
            self._timemark = time.strftime('%H%M%S', self._localtime)
            self._datemark = time.strftime('%Y%m%d', self._localtime)
            self._filepath =  self._filename_generator.new_filename(self)

        self._folder, self._filename = os.path.split(self._filepath)
        if not os.path.isdir(self._folder):
            os.makedirs(self._folder)
        self._file = h5py.File(self._filepath, 'a')
        self.flush()

    def __getitem__(self, name):
        return self._file[name]

    def __setitem__(self, name, val):
        self._file[name] = val

    def __repr__(self):
        ret = "HDF5Data '%s', filename '%s'" % (self._name, self._filename)
        return ret

    def get_filepath(self):
        return self._filepath

    def get_folder(self):
        return self._folder

    def create_dataset(self, *args, **kwargs):
        return self._file.create_dataset(*args, **kwargs)

    def create_group(self, *args, **kwargs):
        '''Create a raw HDF5 group in the file.'''
        return self._file.create_group(*args, **kwargs)

    def create_data_group(self, name, **kwargs):
        '''Create a DataGroup object.'''
        return DataGroup(name, self, **kwargs)

    def flush(self):
        self._file.flush()

    def close(self):
        self._file.close()

def loop1d_data(xs, ynames=('ys', ), name='data', xname='xs', data=None, group=None):
    '''
    Create 1D loop data group. If <data> is specified it is created in that
    HDF5 data file.
    The x coordinates should be specified in <xs> and will be named <xname>.
    <ynames> is a list that specifies the value data sets that will be created.
    '''
    if not group:
        if not data:
            data = HDF5Data()
    group = d.create_data_group(name)
    group.add_coordinate(xs, data=xs)
    for yname in ynames:
        group.add_value(yname, np.zeros((len(xs),)))
    return group

def loop2d_data(xs, ys, znames=('zs', ), name='data', xname='xs', yname='ys', data=None, group=None):
    '''
    Create 2D loop data group. If <data> is specified it is created in that
    HDF5 data file.
    The x and y coordinates should be specified in <xs> and <ys> and will be
    named <xname> and <yname>. <znames> is a list that specifies the value
    data sets that will be created.
    '''
    if not group:
        if not data:
            data = HDF5Data()
        group = d.create_data_group(name)
    group.add_coordinate(xname, data=xs)
    group.add_coordinate(yname, data=ys)
    for zname in znames:
        group.add_value(zname, np.zeros((len(xs), len(ys))))
    return group

