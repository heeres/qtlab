# qtgnuplot.py, classes for plotting with gnuplot
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

import Gnuplot
import os
import time

import logging

import qt
from namedlist import NamedList
import plot

class _GnuPlotList(NamedList):
    def __init__(self):
        NamedList.__init__(self, 'plot', type=NamedList.TYPE_ACTIVE)

    def create(self, name):
        return Gnuplot.Gnuplot()

    def get(self, name=''):
        '''Get Gnuplot instance from list and verify whether it's alive.'''

        item = NamedList.get(self, name)
        if item is None:
            return None

        try:
            item('')
            time.sleep(0.1)
            item('')
        except:
            del self[name]
            item = NamedList.get(self, name)

        return item

class _QTGnuPlot():
    """
    Base class for 2D/3D QT gnuplot classes.
    """

    _gnuplot_list = _GnuPlotList()

    def __init__(self):
        name = self.get_name()
        self._gnuplot = self._gnuplot_list[name]
        self._gnuplot('reset')
        self._default_terminal = Gnuplot.gp.GnuplotOpts.default_term
        if self._default_terminal == 'x11':
            self._default_terminal = 'wxt'
        self._gnuplot('set terminal %s title "%s"' % \
            (self._default_terminal, name))

        self._auto_suffix_counter = 0
        self._auto_suffix_gp_counter = 0

        self._xlabel = None
        self._x2label = None
        self._ylabel = None
        self._y2label = None
        self._zlabel = None

    def clear(self):
        '''Clear the plot.'''
        self._gnuplot.clear()

    def get_first_filepath(self):
        '''Return filepath of first data item.'''
        return self._data[0]['data'].get_filepath()

    def _generate_suffix(self, gp=False, **kwargs):
        append_graphname = kwargs.get('append_graphname', True)
        add_suffix = kwargs.get('suffix', None)
        autosuffix = kwargs.get('autosuffix', True)

        suffix = ''
        if append_graphname:
            suffix = '_' + self.get_name()
        if add_suffix is not None:
            suffix += '_' + str(add_suffix)
        if autosuffix:
            if gp and self._auto_suffix_gp_counter > 0:
                suffix += '_%d' % self._auto_suffix_gp_counter
            elif not gp and self._auto_suffix_counter > 0:
                suffix += '_%d' % self._auto_suffix_counter

            if gp:
                self._auto_suffix_gp_counter += 1
            else:
                self._auto_suffix_counter += 1

        return suffix

    def save_as_type(self, terminal, extension, **kwargs):
        '''Save a different version of the plot.'''

        self.update()

        self._gnuplot('set terminal %s' % terminal)
        fn, ext = os.path.splitext(self.get_first_filepath())
        # Fix GnuPlot on windows issue
        fn = fn.replace('\\', '\\\\')
        suffix = self._generate_suffix(**kwargs)
        self._gnuplot('set output "%s%s.%s"' % (fn, suffix, extension))

        self._gnuplot('replot')
        self._gnuplot('set terminal %s' % self._default_terminal)
        self._gnuplot('set output')
        self._gnuplot('replot')

    def save_ps(self, **kwargs):
        '''Save postscript version of the plot'''
        self.save_as_type('postscript color', 'ps', **kwargs)

    def save_png(self, **kwargs):
        '''Save png version of the plot'''
        self.save_as_type('png size 1024,768', 'png', **kwargs)

    def save_jpeg(self, **kwargs):
        '''Save jpeg version of the plot'''
        self.save_as_type('jpeg', 'jpg', **kwargs)

    def save_svg(self, **kwargs):
        '''Save svg version of the plot'''
        self.save_as_type('svg', 'svg', **kwargs)

    def _write_gp(self, s, **kwargs):
        fn, ext = os.path.splitext(self.get_first_filepath())
        suffix = self._generate_suffix(gp=True, **kwargs)
        f = open('%s%s.gp' % (str(fn), suffix), 'w')
        f.write(s)
        f.close()

    def set_xlabel(self, val, right=False):
        '''Set label for left or right x axis.'''

        if right:
            self._gnuplot('set x2label "%s"' % val)
            self._x2label = val
        else:
            self._gnuplot('set xlabel "%s"' % val)
            self._xlabel = val

    def set_ylabel(self, val, top=False):
        '''Set label for bottom or top y axis.'''

        if top:
            self._gnuplot('set y2label "%s"' % val)
            self._y2label = val
        else:
            self._gnuplot('set ylabel "%s"' % val)
            self._ylabel = val

    def set_zlabel(self, val):
        '''Set label for z axis.'''

        self._gnuplot('set cblabel "%s"' % val)
        self._zlabel = val

    def get_label_commands(self):
        cmd = ''
        if self._xlabel is not None:
            cmd += 'set xlabel "%s"\n' % self._xlabel
        if self._x2label is not None:
            cmd += 'set x2label "%s"\n' % self._x2label
        if self._ylabel is not None:
            cmd += 'set ylabel "%s"\n' % self._ylabel
        if self._y2label is not None:
            cmd += 'set y2label "%s"\n' % self._y2label
        if self._zlabel is not None:
            cmd += 'set cblabel "%s"\n' % self._zlabel
        return cmd

    @staticmethod
    def get_named_list():
        return _QTGnuPlot._gnuplot_list

    @staticmethod
    def get(name):
        return _QTGnuPlot._gnuplot_list.get(name)

    def _do_update(self):
        '''
        Perform an update of the plot.
        '''

        cmd = self.create_plot_command()
        self._gnuplot(cmd)
        return True

class Plot2D(plot.Plot2D, _QTGnuPlot):
    '''
    Class to create line plots.
    '''

    def __init__(self, *args, **kwargs):
        plot.Plot2D.__init__(self, *args, **kwargs)
        _QTGnuPlot.__init__(self)

        self._gnuplot('set grid')
        self._gnuplot('set style data lines')

        self.set_labels()
        self.update()

    def create_plot_command(self, fullpath=True, data_entry=None):
        '''
        Create a gnuplot plot command.
        If data_entry is given only that item will be used, otherwise
        all items are included.
        '''

        s = 'plot '
        first = True

        if data_entry is not None:
            items = [data_entry]
        else:
            items = self._data

        for datadict in items:
            data = datadict['data']
            coorddims = datadict['coorddims']
            valdim = datadict['valdim']

            if len(coorddims) != 1:
                logging.error('Unable to plot without a single coordinate column')
                continue

            if fullpath:
                filepath = data.get_filepath()
            else:
                filepath = data.get_filename()
            filepath = filepath.replace('\\','/')

            using = '%d:%d' % (coorddims[0] + 1, valdim + 1)
            npoints = data.get_npoints()
            if npoints < 2:
                continue

            nblocks = data.get_nblocks()
            npoints_last_block = data.get_block_size(nblocks - 1)
            if npoints_last_block < 2:
                nblocks -= 1
                npoints_last_block = data.get_block_size(nblocks - 1)

            startpoint = max(0, npoints_last_block - self._maxpoints)
            startblock = max(0, nblocks - self._maxtraces)
            every = '::%d:%d' % (startpoint, startblock)

            if 'top' in datadict:
                axes = 'x2'
            else:
                axes = 'x1'
            if 'right' in datadict:
                axes += 'y2'
            else:
                axes += 'y1'

            if not first:
                s += ', '
            else:
                first = False
            s += '"%s" using %s every %s axes %s' % \
                (str(filepath), using, every, axes)

        if first:
            return ''
        else:
            return s

    def save_gp(self):
        '''Save file that can be opened with gnuplot.'''

        s = 'set grid\n'
        s += 'set style data lines\n'
        s += self.get_label_commands()
        s += self.create_plot_command(fullpath=False)
        self._write_gp(s)

class Plot3D(plot.Plot3D, _QTGnuPlot):
    '''
    Class to create surface plots.
    '''

    STYLE_IMAGE = 1
    STYLE_3D = 2

    _COMMANDS = {
        STYLE_IMAGE: {
            'style': ['set view map', 'set style data image', 'unset key'],
            'splotopt': {},
        },
        STYLE_3D: {
            'style': ['set pm3d'],
            'splotopt': {'with': 'lines'},
        }
    }

    def __init__(self, *args, **kwargs):
        plot.Plot3D.__init__(self, *args, **kwargs)
        _QTGnuPlot.__init__(self)

        style = kwargs.get('style', None)
        self.set_style(style)

        self.set_labels()
        self.update()

    def set_style(self, style):
        '''Set plotting style.'''

        if style is None:
            style = qt.config.get('gnuplot_style', self.STYLE_3D)

        self._style = style
        for cmd in self._COMMANDS[self._style]['style']:
            self._gnuplot(cmd)

    def create_plot_command(self, fullpath=True, data_entry=None):
        '''
        Create a gnuplot splot command.
        If data_entry is given only that item will be used, otherwise
        all items are included.
        '''

        s = 'splot '
        first = True

        if data_entry is not None:
            items = [data_entry]
        else:
            items = self._data

        for datadict in items:
            data = datadict['data']
            coorddims = datadict['coorddims']
            valdim = datadict['valdim']

            if len(coorddims) != 2:
                logging.error('Unable to plot without two coordinate columns')
                continue

            if fullpath:
                filepath = data.get_filepath()
            else:
                filepath = data.get_filename()
            filepath = filepath.replace('\\','/')

            using = '%d:%d:%d' % (coorddims[0] + 1, coorddims[1] + 1, valdim + 1)

            stopblock = data.get_nblocks_complete() - 1
            if stopblock < 1:
                continue

            every = ':::0::%d' % (stopblock)

            if not first:
                s += ', '
            else:
                first = False
            s += '"%s" using %s every %s' % (str(filepath), using, every)

            for k, v in self._COMMANDS[self._style]['splotopt'].iteritems():
                s += ' %s %s' % (k, v)

        # gnuplot (version 4.3 november) has bug for placing keys (legends)
        # here we put ugly hack as a temporary fix
        # also remove 'unset key' above __init__ when reverting this hack
        s  = ('set label 1 "%s" at screen 0.1,0.9' % filepath) + '\n' + s

        if first:
            return ''
        else:
            return s

    def save_gp(self):
        '''Save file that can be opened with gnuplot.'''

        s = '\n'.join(self._COMMANDS[self._style]['style']) + '\n'
        s += self.get_label_commands()
        s += self.create_plot_command(fullpath=False)
        self._write_gp(s)

    def _new_data_point_cb(self, sender):
        if self._style != self.STYLE_IMAGE:
            self.update(force=False)

