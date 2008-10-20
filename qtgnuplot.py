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

import logging

import qt
from namedlist import NamedList
import plot

class _GnuPlotList(NamedList):
    def __init__(self):
        NamedList.__init__(self, 'plot', type=NamedList.TYPE_ACTIVE)

    def create(self, name):
        return Gnuplot.Gnuplot()

class _QTGnuPlot():
    """
    Base class for 2D/3D QT gnuplot classes.
    """

    _gnuplot_list = _GnuPlotList()

    def __init__(self, name):
        self._gnuplot = self._gnuplot_list[name]
        self._default_terminal = Gnuplot.gp.GnuplotOpts.default_term
        if self._default_terminal == 'x11':
            self._default_terminal = 'wxt'
        self._gnuplot('set terminal %s title "%s"' % \
            (self._default_terminal, name))

        self._xlabel = None
        self._x2label = None
        self._ylabel = None
        self._y2label = None
        self._zlabel = None

    def clear(self):
        self._gnuplot.clear()

    def get_first_filepath(self):
        return self._data[0]['data'].get_filepath()

    def save_as_type(self, terminal, extension):
        self._gnuplot('set terminal %s' % terminal)
        fn, ext = os.path.splitext(self.get_first_filepath())
        self._gnuplot('set output "%s.%s"' % (fn, extension))
        self._gnuplot('replot')
        self._gnuplot('set terminal %s' % self._default_terminal)
        self._gnuplot('set output')
        self._gnuplot('replot')

    def save_ps(self):
        '''Save postscript version of the plot'''
        self.save_as_type('postscript color', 'ps')

    def save_png(self):
        '''Save png version of the plot'''
        self.save_as_type('png size 1024,768', 'png')

    def save_jpeg(self):
        '''Save jpeg version of the plot'''
        self.save_as_type('jpeg', 'jpg')

    def save_svg(self):
        '''Save svg version of the plot'''
        self.save_as_type('svg', 'svg')

    def _write_gp(self, s):
        fn, ext = os.path.splitext(self.get_first_filepath())
        f = open('%s.gp' % str(fn), 'w')
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

class Plot2D(plot.Plot2D, _QTGnuPlot):
    '''
    Class to create line plots.
    '''

    def __init__(self, *args, **kwargs):
        plot.Plot2D.__init__(self, *args, **kwargs)
        name = self._name
        _QTGnuPlot.__init__(self, name)

        self._gnuplot('set grid')
        self._gnuplot('set style data lines')

        self.set_labels()
        self.update()

    def _do_update(self):
        '''
        Force an update of the plot.

        Input:
            None

        Output:
            None
        '''

        s = ''
        i = 0
        for datadict in self._data:
            data = datadict['data']
            coorddims = datadict['coorddims']
            valdim = datadict['valdim']

            if len(coorddims) != 1:
                logging.error('Unable to plot without defined coordinate columns')
                continue

            filepath = data.get_filepath()
            using = coorddims[0] + 1, valdim + 1
            npoints_last_block = data.get_npoints_last_block()

            if npoints_last_block < 2:
                return True

            startpoint = max(0, npoints_last_block - self._maxpoints)
            startblock = max(0, data.get_nblocks() - self._maxtraces + 1)
            every = None, None, startpoint, startblock

            if 'top' in datadict:
                self._gnuplot('set x2tics')
                axes = 'x2'
            else:
                axes = 'x1'
            if 'right' in datadict:
                self._gnuplot('set y2tics')
                axes += 'y2'
            else:
                axes += 'y1'

            if s != '':
                s += ', '
            s += "Gnuplot.File(%r, using=%r, every=%r, axes=%r)" % \
                (str(filepath), using, every, axes)

            i += 1

        if len(s) > 0:
            exec('self._gnuplot.plot(%s)' % s)

        return True

    def save_gp(self):
        '''Save file that can be opened with gnuplot.'''

        s = 'set grid\n'
        s += 'set style data lines\n'
        s += self.get_label_commands()
        s += 'plot "%s"\n' % (self._data.get_filename())
        self._write_gp(s)

class Plot3D(plot.Plot3D, _QTGnuPlot):
    '''
    Class to create surface plots.
    '''

    STYLE_IMAGE = 1
    STYLE_3D = 2

    _COMMANDS = {
        STYLE_IMAGE: {
            'style': ['set view map', 'set style data image'],
            'splotopt': {},
        },
        STYLE_3D: {
            'style': ['set pm3d'],
            'splotopt': {'with': 'lines'},
        }
    }

    def __init__(self, *args, **kwargs):
        plot.Plot3D.__init__(self, *args, **kwargs)
        name = self._name
        _QTGnuPlot.__init__(self, name)

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

    def _do_update(self):
        '''
        Force an update of the plot.

        Input:
            None

        Output:
            None
        '''

        for datadict in self._data:
            data = datadict['data']
            coorddims = datadict['coorddims']
            valdim = datadict['valdim']

            if len(coorddims) != 2:
                logging.error('Unable to plot without defined coordinate columns')
                continue

            filepath = str(data.get_filepath())
            using = coorddims[0] + 1, coorddims[1] + 1, valdim + 1
            stopblock = data.get_dimension_size(coorddims[1]) - 1
            if stopblock < 1:
                return True

            self._gnuplot.splot(Gnuplot.File(filepath, using=using, \
                            every=(None, None, None, 0, None, stopblock),
                            **self._COMMANDS[self._style]['splotopt']))

        return True

    def save_gp(self):
        '''Save file that can be opened with gnuplot.'''

        s = '\n'.join(self._COMMANDS[self._style]['style'])
        s += self.get_label_commands()
        if len(self._data) > 0:
            s += '\nsplot "%s"\n' % (self._data[0]['data'].get_filename())
        self._write_gp(s)

    def _new_data_point_cb(self, sender):
        if self._style != self.STYLE_IMAGE:
            self.update(force=False)

def plotxy(x, y, **kwargs):
    pass

def plotxyz(x, y, z, **kwargs):
    pass

