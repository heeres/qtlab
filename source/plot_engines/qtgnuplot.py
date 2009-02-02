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

import os
import time
import random
import types
import logging

import qt
from lib.namedlist import NamedList
import plot

import gnuplotpipe

class _GnuPlotList(NamedList):

    def __init__(self):
        NamedList.__init__(self, 'plot', type=NamedList.TYPE_ACTIVE)

    def create(self, name):
        return gnuplotpipe.GnuplotPipe()

    def get(self, name=''):
        '''Get Gnuplot instance from list and verify whether it's alive.'''

        item = NamedList.get(self, name)
        if item is None:
            return None

        try:
            item.cmd('print 0')
            time.sleep(0.1)
            item.cmd('print 0')
        except IOError:
            del self[name]
            item = NamedList.get(self, name)

        return item

class _QTGnuPlot():
    """
    Base class for 2D/3D QT gnuplot classes.
    """

    _SAVE_AS_TYPES = [
        'ps',
        'png',
        'jpeg',
        'svg',
    ]

    _gnuplot_list = _GnuPlotList()

    _COMMAND_MAP = {
        'xlabel': 'set xlabel "%s"\n',
        'x2label': 'set x2label "%s"\n',
        'ylabel': 'set ylabel "%s"\n',
        'y2label': 'set y2label "%s"\n',
        'zlabel': 'set zlabel "%s"\n',
        'cblabel': 'set cblabel "%s"\n',

        'xlog': 'set logscale x %s\n',
        'x2log': 'set logscale x2 %s\n',
        'ylog': 'set logscale y %s\n',
        'y2log': 'set logscale y2 %s\n',
        'zlog': 'set logscale z %s\n',
        'cblog': 'set logscale cb %s\n',

        'xrange': 'set xrange [%s:%s]\n',
        'x2range': 'set x2range [%s:%s]\n',
        'yrange': 'set yrange [%s:%s]\n',
        'y2range': 'set y2range [%s:%s]\n',
        'zrange': 'set zrange [%s:%s]\n',
        'cbrange': 'set cbrange [%s:%s]\n',
    }

    def __init__(self):
        name = self.get_name()
        self._gnuplot = self._gnuplot_list[name]
        self.cmd('reset')

        term = self._gnuplot.get_default_terminal()
        if term is None:
            self._default_terminal = 'x11'
        else:
            self._default_terminal = term[0]
        self._gnuplot.set_terminal(self._default_terminal,
            'title "%s"' % name)

        self._auto_suffix_counter = 0
        self._auto_suffix_gp_counter = 0

    def create_command(self, name, val):
        '''Create command for a plot property.'''

        if name not in self._COMMAND_MAP:
            return None

        if type(val) is types.BooleanType:
            if val:
                cmd = self._COMMAND_MAP[name] % ''
            else:
                cmd = 'un' + self._COMMAND_MAP[name] % ''
        else:
            cmd = self._COMMAND_MAP[name] % val

        return cmd

    def set_property(self, name, val, update=False):
        '''Set a plot property value.'''
        cmd = self.create_command(name, val)
        if cmd is not None and cmd != '':
            self.cmd(cmd)
        return plot.Plot.set_property(self, name, val, update=update)

    def get_commands(self):
        '''Get commands for the current plot properties.'''
        cmd = ''
        for key, val in self.get_properties().iteritems():
            line = self.create_command(key, val)
            if line is not None and line != '':
                cmd += line
        return cmd

    def clear(self):
        '''Clear the plot.'''
        self.cmd('clear')
        Plot.clear(self)

    def get_first_filepath(self):
        '''Return filepath of first data item.'''
        if len(self._data) > 0:
            return self._data[0]['data'].get_filepath()
        else:
            return ''

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

        self._gnuplot.set_terminal(terminal)
        fn, ext = os.path.splitext(self.get_first_filepath())
        # Fix GnuPlot on windows issue
        fn = fn.replace('\\', '/')
        suffix = self._generate_suffix(**kwargs)
        self._gnuplot.cmd('set output "%s%s.%s"' % (fn, suffix, extension))

        self._gnuplot.cmd('replot')
        self._gnuplot.set_terminal(self._default_terminal)
        self._gnuplot.cmd('set output')
        self._gnuplot.cmd('replot')

    @staticmethod
    def get_save_as_types():
        return _QTGnuPlot._SAVE_AS_TYPES

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

    def set_range(self, axis, minval, maxval, update=True):
        if minval is None or minval == '':
            minval = '*'
        if maxval is None or maxval == '':
            maxval = '*'
        cmd = '%srange' % axis
        self.set_property(cmd, (minval, maxval), update=update)

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
        self.cmd(cmd)
        return True

    def cmd(self, cmdstr):
        '''Send command to gnuplot instance directly.'''
        if self._gnuplot is not None:
            self._gnuplot.cmd(cmdstr)

    def live(self):
        self._gnuplot.live()

class Plot2D(plot.Plot2D, _QTGnuPlot):
    '''
    Class to create line plots.
    '''

    def __init__(self, *args, **kwargs):
        kwargs['needtempfile'] = True
        plot.Plot2D.__init__(self, *args, **kwargs)
        _QTGnuPlot.__init__(self)

        self.cmd('set grid')
        self.cmd('set style data lines')

        self.set_labels()
        self.update()

    def set_property(self, *args, **kwargs):
        return _QTGnuPlot.set_property(self, *args, **kwargs)

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

            if fullpath:
                filepath = data.get_filepath()
            else:
                filepath = data.get_filename()
            filepath = filepath.replace('\\','/')

            if len(coorddims) == 0:
                using = '%d' % (valdim + 1)
            elif len(coorddims) == 1:
                using = '%d:%d' % (coorddims[0] + 1, valdim + 1)
            else:
                logging.error('Need 0 or 1 coordinate dimensions!')
                continue

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
            if len(coorddims) == 0:
                every = "::%d" % (startpoint)
            else:
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
        s = self.get_commands()
        s += self.create_plot_command(fullpath=False)
        self._write_gp(s)

    def _get_temp_file(self):
        return '/tmp/qtgnuplot.tmp.%d' % random.random()

class Plot3D(plot.Plot3D, _QTGnuPlot):
    '''
    Class to create surface plots using gnuplot.
    '''

    # For backwards compatibility
    STYLE_IMAGE = 'image'
    STYLE_3D = '3d'

    _STYLES = {
        'image': {
            'style': [
                'unset pm3d',
                'set view map',
                'set style data image',
            ],
            'splotopt': '',
        },
        'image3d': {
            'style': [
                'set pm3d map corners2color c1',
            ],
            'splotopt': 'with pm3d',
        },
        'points': {
            'style': [
                'unset pm3d',
                'set view 60,15'
            ],
            'splotopt': 'with points',
        },
        'lines': {
            'style': [
                'unset pm3d',
                'set view 60,16'
            ],
            'splotopt': 'with lines',
        },
        '3d': {
            'style': [
                'set pm3d corners2color c1',
                'set view 60,15',
            ],
            'splotopt': 'with pm3d',
        },
        '3dpoints' : {
            'style': [
                'set pm3d corners2color c1',
                'set view 60,15',
            ],
            'splotopt': 'with points',
        },
        '3dlines': {
            'style': [
                'set pm3d corners2color c1',
                'set view 60,15',
            ],
            'splotopt': 'with lines',
        },
    }

    _PALETTE_MAP = {
        'default': (7, 5, 15),
        'hot': (21, 22, 23),
        'ocean': (23, 28, 3),
        'rainbow': (33, 13, 10),
        'afmhot': (34, 35, 36),
        'bw': (7, 7, 7),
        'redwhiteblue': (-34, 13, 34),
        'bluewhitered': (34, 13, -34),
    }

    # Palette functions in gnuplot, so we can use them with custom gamma
    _PALETTE_FUNCTIONS = {
        0: '0',
        1: '0.5',
        2: '1',
        3: '%(x)s',
        4: '%(x)s**2',
        5: '%(x)s**3',
        6: '%(x)s**4',
        7: 'sqrt(%(x)s)',
        8: 'sqrt(sqrt(%(x)s))',
        9: 'sin(90*%(x)s*0.0174532925)',
        10: 'cos(90*%(x)s*0.0174532925)',
        11: 'abs(%(x)s-0.5)',
        12: '(2.0*%(x)s-1)*(2.0*%(x)s-1)',
        13: 'sin(180*%(x)s*0.0174532925)',
        14: 'abs(cos(180*%(x)s*0.0174532925))',
        15: 'sin(360*%(x)s*0.0174532925)',
        16: 'cos(360*%(x)s*0.0174532925)',
        17: 'abs(sin(360*%(x)s*0.0174532925))',
        18: 'abs(cos(360*%(x)s*0.0174532925))',
        19: 'abs(sin(720*%(x)s*0.0174532925))',
        20: 'abs(cos(720*%(x)s*0.0174532925))',
        21: '3*%(x)s',
        22: '3*%(x)s-1',
        23: '3*%(x)s-2',
        24: 'abs(3*%(x)s-1)',
        25: 'abs(3*%(x)s-2)',
        26: '1.5*%(x)s-0.5',
        27: '1.5*%(x)s-1',
        28: 'abs(1.5*%(x)s-0.5)',
        29: 'abs(1.5*%(x)s-1)',
        30: '0',
        31: '0',
        32: '0',
        33: 'abs(2*%(x)s-0.5)',
        34: '2*%(x)s',
        35: '2*%(x)s-0.5',
        36: '2*%(x)s-1',
    }

    def __init__(self, *args, **kwargs):
        kwargs['needtempfile'] = True
        plot.Plot3D.__init__(self, *args, **kwargs)
        _QTGnuPlot.__init__(self)

        style = kwargs.get('style', None)

        self.set_style(style)
        _QTGnuPlot.cmd(self, 'unset key')
        self.set_labels()
        self.set_palette('default', gamma=1.0)

    def set_property(self, *args, **kwargs):
        return _QTGnuPlot.set_property(self, *args, **kwargs)

    def create_command(self, name, val):
        if name == 'style':
            ret = '\n'.join(self._STYLES[val]['style']) + '\n'
            return ret

        elif name == 'palette':
            if type(val) is not types.DictType:
                logging.warning('Invalid palette properties: %s', val)
                return None

            return self._create_palette_commands(**val)

        else:
            return _QTGnuPlot.create_command(self, name, val)

    @staticmethod
    def get_styles():
        styles = Plot3D._STYLES.keys()
        styles.sort()
        return styles

    def set_style(self, style, update=True):
        '''Set plotting style.'''

        if style is None:
            style = qt.config.get('gnuplot_style', 'image3d')

        if style not in self._STYLES:
            logging.warning('Unknown style: %s', style)
            return None

        self.set_property('style', style, update=update)

    @staticmethod
    def get_palettes():
        '''Return available palettes.'''
        pals = Plot3D._PALETTE_MAP.keys()
        pals.sort()
        return pals

    def set_palette(self, pal, gamma=1.0, update=True):
        '''
        Set a color palette.

        Input:
            pal (string): palette name, get available ones with get_palettes()
            gamma (float): gamma correction, if gamma=1 a 'simple' gnuplot
                palette function will be used.
            update (bool): whether to update the current plot.
        '''

        if pal not in self._PALETTE_MAP:
            logging.warning('Unknown palette: %s', pal)
            return False

        self.set_property('palette', dict(name=pal, gamma=gamma), \
                update=update)

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
            style = self.get_property('style')

            if len(coorddims) != 2:
                logging.error('Unable to plot without two coordinate columns')
                continue

            if fullpath:
                filepath = data.get_filepath()
            else:
                filepath = data.get_filename()
            filepath = filepath.replace('\\','/')

            using = '%d:%d:%d' % (coorddims[0] + 1, coorddims[1] + 1, valdim + 1)

            if style == self.STYLE_IMAGE:
                stopblock = data.get_nblocks_complete() - 1
                if stopblock < 1:
                    logging.warning('Unable to plot in style "image" with <=1 block')
                    continue
                everystr = 'every :::0::%s' % (stopblock)
            else:
                everystr = ''


            if not first:
                s += ', '
            else:
                first = False
            s += '"%s" using %s %s' % (str(filepath), using, everystr)
            s += self._STYLES[style]['splotopt']

        # gnuplot (version 4.3 november) has bug for placing keys (legends)
        # here we put ugly hack as a temporary fix
        # also remove 'unset key' in __init__ when reverting this hack
            s  = ('set label 1 "%s" at screen 0.1,0.9' % filepath) + '\n' + s

        if first:
            return ''
        else:
            return s

    def save_gp(self):
        '''Save file that can be opened with gnuplot.'''
        s = self.get_commands()
        s += self.create_plot_command(fullpath=False)
        self._write_gp(s)

    def _new_data_point_cb(self, sender):
        if self.get_property('style') != self.STYLE_IMAGE:
            self.update(force=False)

    def _palette_func(self, func_id):
        if func_id >= 0:
            return self._PALETTE_FUNCTIONS[abs(func_id)] % \
                    dict(x='(gray**gamma)')
        else:
            return self._PALETTE_FUNCTIONS[abs(func_id)] % \
                    dict(x='((1-gray)**gamma)')

    def _create_palette_commands(self, **kwargs):
        name = kwargs.get('name', 'default')
        gamma = kwargs.get('gamma', 1.0)

        map = self._PALETTE_MAP[name]
        cmd = ''
        if gamma == 1.0:
            cmd += 'set palette rgbformulae %d,%d,%d\n' % \
                (map[0], map[1], map[2])
        else:
            cmd += 'gamma = %f\n' % float(1/gamma)

            cmd += 'rcol(gray) = %s\n' % (self._palette_func(map[0]))
            cmd += 'gcol(gray) = %s\n' % (self._palette_func(map[1]))
            cmd += 'bcol(gray) = %s\n' % (self._palette_func(map[2]))
            cmd += 'set palette model RGB functions rcol(gray), gcol(gray), bcol(gray)\n'

        return cmd
