# qtgnuplot.py, classes for plotting
# Pieter de Groot <pieterdegroot@gmail.com>
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

import gobject
import Gnuplot
from time import time
import os

class _QTGnuPlot(gobject.GObject):
    """
    Base class for 2D/3D QT gnuplot classes.
    """

    def __init__(self, data, cols, mintime, maxpoints):
        gobject.GObject.__init__(self)

        self._data = data
        self._cols = [cols]
        self.set_mintime(mintime)
        self.set_maxpoints(maxpoints)

        self._basedir = self._data.get_basedir()
        self._dir = None

        self._gnuplot = Gnuplot.Gnuplot()
        self._gnuplot('cd "%s"' % self._basedir)

        self._default_terminal = Gnuplot.gp.GnuplotOpts.default_term

        self._auto_update_hid = None
        self._time_of_last_plot = 0

    def reset_cols(self, cols):
        '''
        Reset the plot list and adds the first set of columns to be plotted.

        Input:
            cols (tuple of 2 or 3 ints): indices of the columns to be plotted

        Output:
            None
        '''

        self._cols = []
        self._cols.append(cols)

    def clear(self):
        self._gnuplot.clear()

    def save_as_type(self, terminal, extension):
        self._gnuplot('set terminal %s' % terminal)
        self._gnuplot('set output "%s/%s.%s"' % \
            (self._data.get_subdir(), self._data.get_filename(), extension))
        self._gnuplot('replot')
        self._gnuplot('set terminal %s' % self._default_terminal)
        self._gnuplot('set output')
        self._gnuplot('replot')

    def save_ps(self):
        '''Save postscript version of the plot'''
        self.save_as_type('postscript color', 'ps')

    def save_png(self):
        '''Save png version of the plot'''
        self.save_as_type('png', 'png')

    def save_jpeg(self):
        '''Save jpeg version of the plot'''
        self.save_as_type('jpeg', 'jpg')

    def save_svg(self):
        '''Save svg version of the plot'''
        self.save_as_type('svg', 'svg')

    def _write_gp(self, contents):
        fname = '%s/%s.gp' % (self._data.get_fulldir(), self._data.get_filename())
        f = file(fname, 'w+')
        f.write(contents)
        f.close()

    def set_mintime(self, mintime):
        '''
        'mintime' gives the minimum time between plots, to avoid potential
        slowing down if every data point coming in is plotted immediately.

        Input:
            mintime (float): minimum time in seconds

        Output:
            None
        '''

        if mintime < 0:
            self._mintime = 0
        else:
            self._mintime = mintime

    def set_maxpoints(self, maxpoints):
        '''
        When maxpoints is set to a value > 1 the plot will only show this
        number of (the last) data points.

        Input:
            maxpoints (integer): number of points to plot. (0 = infinite, default)

        Output:
            None
        '''

        if maxpoints < 1:
            self._maxpoints = 0
        else:
            self._maxpoints = maxpoints

class Plot2D(_QTGnuPlot):
    '''
    Class to create line plots.
    '''

    def __init__(self, data, cols=(1, 2), mintime=0.5, maxpoints=10000):
        _QTGnuPlot.__init__(self, data, cols, mintime, maxpoints)

        self._gnuplot('set grid')
        self._gnuplot('set style data lines')

    def add_trace(self, cols):
        '''
        Add another trace to the same plot. It uses the same data file,
        so only the columns need to be specified.

        Input:
            cols (tuple of int): x and y index of columns to plot

        Output:
            None
        '''

        self._cols.append(cols)

    def update_plot(self):
        '''
        Force an update of the plot.

        Input:
            None

        Output:
            None
        '''

        filedir = self._data.get_fulldir()
        filename = self._data.get_filename()
        dir = self._data.get_subdir()
        tbasedir = self._data.get_basedir()
        if self._basedir is not tbasedir:
            self._gnuplot('cd "%s"' % tbasedir)
            self._basedir = tbasedir

        path = str(os.path.join(dir, filename))

        block_nr = self._data.get_block_nr()
        line_nr = self._data.get_line_nr()

        startpoint = line_nr - self._maxpoints
        if startpoint < 0:
            startpoint = 0

        if line_nr <= 1:
            return False

        self.set_labels(self._cols[0])

        sd = ''
        for _cols in self._cols:
            if sd is not '':
                sd += ', '

            sd += 'Gnuplot.File(path, using=%s, every=(None, None, %i, %i))' % \
                (str(_cols), startpoint, block_nr)

        exec('self._gnuplot.plot(%s)' % sd)

        return True

    def _new_data_point_cb(self, sender):
        if ((time() - self._time_of_last_plot) > self._mintime) and get_live_plotting():
            self.update_plot()
            self._time_of_last_plot = time()

    def set_auto_update(self):
        '''
        Set the plot to auto-update each time a new data point is added to a file.

        See also set_mintime

        Input:
            None

        Output:
            None
        '''
        if self._auto_update_hid != None:
            print 'auto_update already turned on'
            return
        self._auto_update_hid = self._data.connect('new-data-point', self._new_data_point_cb)

    def unset_auto_update(self):
        if self._auto_update_hid == None:
            print 'auto_update already turned off'
            return
        self._data.disconnect(self._auto_update_hid)
        self._auto_update_hid = None

    def set_labels(self, cols):
        '''
        Set the labels in the plot.

        Input:
            cols (tuple of int): index of x and y col

        Output:
            None
        '''

        col_info = self._data.get_col_info()
        if len(col_info) < 1:
            self._gnuplot.xlabel('')
            self._gnuplot.ylabel('')
            return False

        colx = col_info[cols[0] - 1]
        coly = col_info[cols[1] - 1]
        self._gnuplot.xlabel('%s %s [%s]' % (colx['instrument'], colx['parameter'], colx['units']))
        self._gnuplot.ylabel('%s %s [%s]' % (coly['instrument'], coly['parameter'], coly['units']))

    def save_gp(self):
        s = 'set grid\n'
        s += 'set style data lines\n'
        s += 'set xlabel "%s"\n' % self._xlabel
        s += 'set ylabel "%s"\n' % self._ylabel
        s += 'plot "%s.dat"\n' % (self._data.get_filename())
        self._write_gp(s)

class Plot3D(_QTGnuPlot):
    '''
    Class to plot x, y, z data.
    '''

    # todo:
    # 1) does non-rect-grid plotting work?
    # 2) lastpoint/maxpoints not needed in 3d
    # 3) update per point?

    def __init__(self, data, cols=(1, 2, 3), mintime=0.5):
        _QTGnuPlot.__init__(self, data, cols, mintime, 0)

        self._gnuplot('set view map')
        self._gnuplot('set style data image')

    def update_plot(self):
        '''
        Force an update of the plot.

        Input:
            None

        Output:
            None
        '''

        block_nr = self._data.get_block_nr()
        stopblock = block_nr - 1
        if stopblock < 0:
            stopblock = 0

        filedir = self._data.get_fulldir()
        filename = self._data.get_filename()
        dir = self._data.get_subdir()
        tbasedir = self._data.get_basedir()
        if self._basedir is not tbasedir:
            self._gnuplot('cd "%s"' % tbasedir)
            self._basedir = tbasedir

        path = str(os.path.join(dir, filename))

        self.set_labels(self._cols[0])

        if block_nr <= 1:
            return False

        print 'using: %s' % str(self._cols[0])
        self._gnuplot.splot(Gnuplot.File(path, using=self._cols[0], \
            every=(None, None, None, 0, None, stopblock)))

        return True

    def _new_data_block_cb(self, sender):
        if (((time() - self._time_of_last_plot) > self._mintime) and get_live_plotting()):
            self.update_plot()
            self._time_of_last_plot = time()

    def set_auto_update_block(self):
        '''
        Set the plot to auto-update each time a data block is completed in the data file.

        Input:
            None

        Output:
            None
        '''
        if self._auto_update_hid != None:
            print 'auto_update_block already turned on'
            return
        self._auto_update_hid = self._data.connect('new-data-block', self._new_data_block_cb)

    def unset_auto_update_block(self):
        if self._auto_update_hid == None:
            print 'auto_update_block already turned off'
            return
        self._data.disconnect(self._auto_update_hid)
        self._auto_update_hid = None

    def set_labels(self, cols):
        '''
        Set the labels in the plot.

        Input:
            cols (tuple of int) - index of x, y and z col

        output:
            None
        '''

        col_info = self._data.get_col_info()
        if len(col_info) < 1:
            self._gnuplot.xlabel('')
            self._gnuplot.ylabel('')
            self._gnuplot('set clabel ""')
            return False

        colx = col_info[cols[0] - 1]
        coly = col_info[cols[1] - 1]
        colz = col_info[cols[2] - 1]
        self._gnuplot.xlabel('%s %s [%s]' % \
            (colx['instrument'], colx['parameter'], colx['units']))
        self._gnuplot.ylabel('%s %s [%s]' % \
            (coly['instrument'], coly['parameter'], coly['units']))
        self._gnuplot('set cblabel "%s %s [%s]"' % \
            (colz['instrument'], colz['parameter'], colz['units']))

    def save_gp(self):
        s = 'set grid\n'
        s += 'set style data image\n'
        s += 'set view map\n'
        s += 'set xlabel "%s"\n' % self._xlabel
        s += 'set ylabel "%s"\n' % self._ylabel
        s += 'set cblabel "%s"\n' % self._cblabel
        s += 'plot "%s.dat"\n' % (self._data.get_filename())
        self._write_gp(s)

_live_plotting = True
def toggle_live_plotting():
    global _live_plotting
    _live_plotting = not _live_plotting

def get_live_plotting():
    global _live_plotting
    return _live_plotting

