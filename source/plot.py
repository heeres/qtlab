# plot.py, abstract plotting classes
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
import logging
import os
import time
import types
import numpy

import qt
from data import Data
from lib import namedlist
from lib.misc import get_arg_type, get_dict_keys

class _PlotList(namedlist.NamedList):
    def __init__(self):
        namedlist.NamedList.__init__(self, base_name='plot')

class Plot(gobject.GObject):
    '''
    Base class / interface for plot implementations.

    Implementing _do_update will make sure the plot is updated when new data
    is available (only when the global qt auto_update flag is set and the
    plot was last updated longer than mintime (sec) ago.
    '''

    _plot_list = _PlotList()

    def __init__(self, *args, **kwargs):
        '''
        Create a plot object.

        args input:
            data objects (Data)
            filenames (string)

        kwargs input:
            name (string), default will be 'plot<n>'
            maxpoints (int), maximum number of points to show, default 10000
            maxtraces (int), maximum number of traces to show, default 5
            mintime (int, seconds), default 1
            autoupdate (bool), default None, which means listen to global
            needtempfile (bool), default False. Whether the plot needs data
            in a temporary file.
        '''

        gobject.GObject.__init__(self)

        maxpoints = kwargs.get('maxpoints', 10000)
        maxtraces = kwargs.get('maxtraces', 5)
        mintime = kwargs.get('mintime', 1)
        autoupdate = kwargs.get('autoupdate', None)
        needtempfile = kwargs.get('needtempfile', False)
        name = kwargs.get('name', '')
        self._name = Plot._plot_list.new_item_name(self, name)

        self._config = qt.config
        self._data = []

        # Plot properties, things such as maxpoints might be migrated here.
        self._properties = {}

        self._maxpoints = maxpoints
        self._maxtraces = maxtraces
        self._mintime = mintime
        self._autoupdate = autoupdate
        self._needtempfile = needtempfile

        self._last_update = 0

        for arg in args:
            if isinstance(arg, Data):
                data_args = get_dict_keys(kwargs, ('coorddim', 'coorddims', 'valdim'))
                self.add_data(arg, **data_args)
            elif type(arg) is types.StringType and os.path.isfile(arg):
                data = Data(arg)
                self.add_data(data)

        Plot._plot_list.add(self._name, self)

    def get_name(self):
        '''Get plot name.'''
        return self._name

    def add_data(self, data, **kwargs):
        '''Add a Data class with options to the plot list.'''

        kwargs['data'] = data
        kwargs['new-data-point-hid'] = \
                data.connect('new-data-point', self._new_data_point_cb)
        kwargs['new-data-block-hid'] = \
                data.connect('new-data-block', self._new_data_block_cb)
        self._data.append(kwargs)

    def set_property(self, prop, val, update=False):
        self._properties[prop] = val
        if update:
            self.update()

    def get_property(self, prop, default=None):
        return self._properties.get(prop, default)

    def get_properties(self):
        return self._properties

    def set_properties(self, props, update=True):
        for key, val in props.iteritems():
            self.set_property(key, val, update=False)
        if update:
            self.update()

    # Predefined properties, actual handling needs to be implemented in
    # the set_property() function of the implementation class.

    def set_xlabel(self, val, update=True):
        '''Set label for left x axis.'''
        self.set_property('xlabel', val, update=update)

    def set_x2label(self, val, update=True):
        '''Set label for right x axis.'''
        self.set_property('x2label', val, update=update)

    def set_ylabel(self, val, update=True):
        '''Set label for bottom y axis.'''
        self.set_property('ylabel', val, update=update)

    def set_y2label(self, val, update=True):
        '''Set label for top y axis.'''
        self.set_property('y2label', val, update=update)

    def set_zlabel(self, val, update=True):
        '''Set label for z/color axis.'''
        self.set_property('zlabel', val, update=update)

    def set_xlog(self, val, update=True):
        '''Set log scale on left x axis.'''
        self.set_property('xlog', val, update=update)

    def set_x2log(self, val, update=True):
        '''Set log scale on right x axis.'''
        self.set_property('x2log', val, update=update)

    def set_ylog(self, val, update=True):
        '''Set log scale on bottom y axis.'''
        self.set_property('ylog', val, update=update)

    def set_y2log(self, val, update=True):
        '''Set log scale on top y axis.'''
        self.set_property('y2log', val, update=update)

    # Implementation classes need to implement set_range()

    def set_xrange(self, minval=None, maxval=None, update=True):
        '''Set left x axis range, None means auto.'''
        self.set_range('x', minval, maxval, update=update)

    def set_x2range(self, minval=None, maxval=None, update=True):
        '''Set right x axis range, None means auto.'''
        self.set_range('x2', minval, maxval, update=update)

    def set_yrange(self, minval=None, maxval=None, update=True):
        '''Set bottom y axis range, None means auto.'''
        self.set_range('y', minval, maxval, update=update)

    def set_y2range(self, minval=None, maxval=None, update=True):
        '''Set top y axis range, None means auto.'''
        self.set_range('y2', minval, maxval, update=update)

    def set_zrange(self, minval=None, maxval=None, update=True):
        '''Set z axis range, None means auto.'''
        self.set_range('z', minval, maxval, update=update)

    def clear(self):
        '''Clear the plot and remove all data items.'''

        logging.info('Clearing plot %s...', self._name)
        while len(self._data) > 0:
            info = self._data[0]
            if 'new-data-point-hid' in info:
                info['data'].disconnect(info['new-data-point-hid'])
            if 'new-data-block-hid' in info:
                info['data'].disconnect(info['new-data-block-hid'])
            del self._data[0]

    def set_title(self, val):
        '''Set the title of the plot window. Override in implementation.'''
        pass

    def add_legend(self, val):
        '''Add a legend to the plot window. Override in implementation.'''
        pass

    def update(self, force=True, **kwargs):
        '''
        Update the plot.

        Input:
            force (bool): if True force an update, else check whether we
                would like to autoupdate and whether the last update is longer
                than 'mintime' ago.
        '''

        dt = time.time() - self._last_update

        if not force and self._autoupdate is not None and not self._autoupdate:
            return

        cfgau = self._config.get('auto-update', True)
        if force or (cfgau and dt > self._mintime):
            self._last_update = time.time()
            self._do_update(**kwargs)

    def _new_data_point_cb(self, sender):
        try:
            self.update(force=False)
        except Exception, e:
            logging.warning('Failed to update plot %s: %s', self._name, str(e))

    def _new_data_block_cb(self, sender):
        self.update(force=False)

    def set_maxpoints(self, val):
        self._maxpoints = val

    @staticmethod
    def get_named_list():
        return Plot._plot_list

    @staticmethod
    def get(name):
        return Plot._plot_list[name]

    def get_needtempfile(self):
        '''Return whether this plot type needs temporary files.'''
        return self._needtempfile

class Plot2D(Plot):
    '''
    Abstract base class for a 2D plot.
    Real implementations should at least implement:
        - set_xlabel(self, label)
        - set_ylabel(self, label)
    '''

    def __init__(self, *args, **kwargs):
        Plot.__init__(self, *args, **kwargs)

    def add_data(self, data, coorddim=None, valdim=None, **kwargs):
        '''
        Add data to 2D plot.

        Input:
            data (Data):
                Data object
            coorddim (int):
                Which coordinate column to use (0 by default)
            valdim (int):
                Which value column to use for plotting (0 by default)
        '''

        if coorddim is None:
            ncoord = data.get_ncoordinates()
            #FIXME: labels
            if ncoord == 0:
                coorddims = ()
            else:
                coorddims = (0,)
                if ncoord > 1:
                    logging.info('Data object has multiple coordinates, using the first one')
        else:
            coorddims = (coorddim,)

        if valdim is None:
            if data.get_nvalues() > 1:
                logging.info('Data object has multiple values, using the first one')
            valdim = data.get_ncoordinates()

        kwargs['coorddims'] = coorddims
        kwargs['valdim'] = valdim
        Plot.add_data(self, data, **kwargs)

    def set_labels(self, left='', bottom='', right='', top='', update=True):
        for datadict in self._data:
            data = datadict['data']
            if 'right' in datadict and right == '':
                right = data.format_label(datadict['coorddims'][0])
            elif left == '':
                left = data.format_label(datadict['coorddims'][0])

            if 'top' in datadict and top == '':
                top = data.format_label(datadict['valdim'])
            elif bottom == '':
                bottom = data.format_label(datadict['valdim'])

        if left != '':
            self.set_xlabel(left, update=False)
        if right != '':
            self.set_x2label(right, update=False)
        if bottom != '':
            self.set_ylabel(bottom, update=False)
        if top != '':
            self.set_y2label(top, update=False)

        if update:
            self.update()

class Plot3D(Plot):
    '''
    Abstract base class for a 3D plot.
    Real implementations should at least implement:
        - set_xlabel(self, label)
        - set_ylabel(self, label)
        - set_zlabel(self, label)
    '''

    def __init__(self, *args, **kwargs):
        if 'mintime' not in kwargs:
            kwargs['mintime'] = 2
        Plot.__init__(self, *args, **kwargs)

    def add_data(self, data, coorddims=None, valdim=None):
        '''
        Add data to 3D plot.

        Input:
            data (Data):
                Data object
            coorddim (tuple(int)):
                Which coordinate columns to use ((0, 1) by default)
            valdim (int):
                Which value column to use for plotting (0 by default)
        '''

        if coorddims is None:
            if data.get_ncoordinates() > 2:
                logging.info('Data object has multiple coordinates, using the first two')
            coorddims = (0, 1)

        if valdim is None:
            if data.get_nvalues() > 1:
                logging.info('Data object has multiple values, using the first one')
            valdim = data.get_ncoordinates()
            if valdim < 2:
                valdim = 2

        Plot.add_data(self, data, coorddims=coorddims, valdim=valdim)

    def set_labels(self, x='', y='', z=''):
        '''
        Set labels in the plot. Use x, y and z if specified, else let the data
        object create the proper format for each dimensions
        '''

        for datadict in self._data:
            data = datadict['data']
            if x == '':
                x = data.format_label(datadict['coorddims'][0])
            if y == '':
                y = data.format_label(datadict['coorddims'][1])
            if z == '':
                z = data.format_label(datadict['valdim'])

        if x != '':
            self.set_xlabel(x)
        if y != '':
            self.set_ylabel(y)
        if z != '':
            self.set_zlabel(z)

def _get_plot_options(i, *args):
    return ()

def plot(*args, **kwargs):
    '''
    Plot items.

    Variable argument input:
        Data object(s)
        numpy array(s), size n x 1 (two n x 1 arrays to represent y and x),
            or n x 2
        color string(s), such as 'r', 'g', 'b'

    Keyword argument input:
        name (string): the plot name to use, defaults to 'plot'
        coorddim, valdim: specify coordinate and value dimension for Data
            object.
    '''

    plotname = kwargs.get('name', 'plot')
    graph = qt.plots[plotname]
    if graph is None:
        graph = qt.Plot2D(name=plotname)
    coorddim = kwargs.get('coorddim', None)
    valdim = kwargs.get('valdim', None)
    globalx = kwargs.get('x', None)
    if type(globalx) in (types.ListType, types.TupleType):
        globalx = numpy.array(globalx)

    # Clear plot if requested
    clear = kwargs.get('clear', False)
    if clear:
        graph.clear()

    # Convert all lists / tuples to numpy.arrays
    args = list(args)
    for i in range(len(args)):
        if type(args[i]) in (types.ListType, types.TupleType):
            args[i] = numpy.array(args[i])

    i = 0
    while i < len(args):

        # This is easy
        if isinstance(args[i], Data):
            opts = _get_plot_options(i + 1, *args)
            graph.add_data(args[i], coorddim=coorddim, valdim=valdim)
            i += 1 + len(opts)

        elif isinstance(args[i], numpy.ndarray):
            if len(args[i].shape) == 1:
                if globalx is not None:
                    y = args[i]
                    data = numpy.column_stack((globalx, y))
                elif i + 1 < len(args) and type(args[i+1]) is numpy.ndarray:
                    x = args[i]
                    y = args[i + 1]
                    data = numpy.column_stack((x, y))
                    i += 1
                else:
                    data = args[i]

            elif len(args[i].shape) == 2:
                data = args[i]

            else:
                print 'Unable to plot array of shape %r' % (args[i].shape)
                i += 1
                continue

            tmp = graph.get_needtempfile()
            data = Data(data=data, tempfile=tmp)
            graph.add_data(data, coorddim=coorddim, valdim=valdim)
            i += 1

        else:
            print 'Unhandled argument: %r' % args[i]
            i += 1

    graph.update()
    return graph

