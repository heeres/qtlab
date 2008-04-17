# qtgnuplot.py, classes for plotting
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
import Gnuplot
from time import time

class Plot2D(gobject.GObject):
    '''
    Class to create line plots.
    '''

    def __init__(self, _data, cols=(1, 2), mintime=0.5, maxpoints=500):
        gobject.GObject.__init__(self)

        self._data = _data

        self._gnuplot = Gnuplot.Gnuplot()
        self._gnuplot('set grid')
        self._gnuplot('set style data lines')

        self._cols = []
        self._cols.append(cols)

        self._auto_update_hid = None

        self._time_of_last_plot = 0
        self.set_mintime(mintime)
        self.set_maxpoints(maxpoints)

    def reset_cols(self, cols):
        '''
        Reset the plot list and adds the first set of columns to be plotted.

        Input:
            cols (tuple of 2 ints): indices of the columns to be plotted

        Output:
            None
        '''

        self._cols = []
        self._cols.append(cols)

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

        filename = self._data.get_filename() + '.dat'
        dir = self._data.get_dir()
        path = dir + '/' + filename

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
        if ((time() - self._time_of_last_plot) > self.mintime) and get_live_plotting():
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

        self._auto_update_hid = self._data.connect('new-data-point', self._new_data_point_cb)

    def unset_auto_update(self):
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
            self.mintime = 0
        else:
            self.mintime = mintime

    def set_maxpoints(self, maxpoints=0):
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

class Plot3D(gobject.GObject):
    '''
    Class to plot x, y, z data.
    '''

    # todo:
    # 1) does non-rect-grid plotting work?
    # 2) lastpoint/maxpoints not needed in 3d
    # 3) update per point?
    # 4) filename through event-message but dir not?

    def __init__(self, _data, cols=(1, 2, 3), mintime=0.5):
        gobject.GObject.__init__(self)
        self._gnuplot = Gnuplot.Gnuplot()
        self._gnuplot('set grid')
        self._gnuplot('set view map')
        #self._gnuplot('set pm3d map')
        self._gnuplot('set style data image')

        self._data = _data
        self._cols = cols
        self._time_of_last_plot = 0
        self._min_time_between_plots = mintime
#        self._maxpoints = maxpoints

    def update_plot(self):
        '''
        Force an update of the plot.

        Input:
            None

        Output:
            None
        '''

        print 'update_plot'
        block_nr = self._data.get_block_nr()
        stopblock = block_nr - 1
        if stopblock < 0:
            stopblock = 0

#        startpoint = self._data._line_nr - self._maxpoints
#        if startpoint < 1:
#            startpoint = 1

        filename = self._data.get_filename() + '.dat'
        dir = self._data.get_dir()
        path = dir + '/' + filename

        self.set_labels(self._cols)

        if block_nr <= 1:
            return False

        self._gnuplot.splot(Gnuplot.File(path, using=self._cols, \
            every=(None, None, None, 0, None, stopblock)))

        return True

#    def set_auto_update_point(self):
#self._data.connect('new-data-point', self._received_update_plot_cb)

    def _new_data_block_cb(self, sender):
        if (((time() - self._time_of_last_plot) > self._min_time_between_plots) and get_live_plotting()):
            self.update_plot()
            self._time_of_last_plot = time()

    def set_auto_update_block(self):
        self._data.connect('new-data-block', self._new_data_block_cb)

    def reset_cols(self, cols):
        '''
        Reset the plot list and adds the first set of columns to be plotted.

        Input:
            cols (tuple of 2 ints): indices of the columngs to be plotted

        Output:
            None
        '''

        self._cols = cols

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

    def set_mintime(self, mintime):
        self._min_time_between_plots = mintime

#    def set_maxpoints(self, maxpoints):
#        self._maxpoints = maxpoints

_live_plotting = True
def toggle_live_plotting():
    global _live_plotting
    _live_plotting = not _live_plotting

def get_live_plotting():
    global _live_plotting
    return _live_plotting

