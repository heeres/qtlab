import time
import gobject

import calltimer

import data

from config import get_config

class Measurement(gobject.GObject):

    __gsignals__ = {
        'finished': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
    }

    def __init__(self, name, **kwargs):
        gobject.GObject.__init__(self)

        self._thread = None
        self._options = kwargs

        self._coords = []
        self._measurements = []

        dstr = time.strftime('%Y%m%d')
        tstr = time.strftime('%H%M%S')
        mname = '%s_%s' % (tstr, name)
        mfn = '%s/%s/%s.dat' % (get_config()['datadir'], dstr, mname)
        self._data = data.QTData(mname, mfn)

    def _add_coordinate_options(self, coord, **kwargs):
        if 'steps' in kwargs:
            coord['steps'] = kwargs['steps']
            coord['stepsize'] = float(coord['end'] - coord['start']) / (kwargs['steps'] - 1.0)
        elif 'stepsize' in kwargs:
            if start < end:
                coord['stepsize'] = kwargs['stepsize']
            else:
                coord['stepsize'] = -kwargs['stepsize']
            coord['steps'] = math.ceil((coord['end'] - coord['start']) / kwargs['stepsize'])
        else:
            print '_add_coordinate_options requires steps or stepsize argument'

        if 'delay' in kwargs:
            coord['delay'] = kwargs['delay']

        self._coords.append(coord)

    def add_coordinate(self, ins, var, start, end, **kwargs):
        '''
        Add a loop coordinate to the internal list. The first coordinate is
        the outer part of the loop, the last coordinate the inner part. The
        measurement loop will set the value of instrument ins, variable var.

        Input:
            ins (Instrument): the instrument
            var (string): the variable to sweep
            start (float): start value
            end (float): end value
            **kwargs: options:
                steps (int) or stepsize (float). One of these is required.
                delay (float): delay after setting value, in ms

        Output:
            None
        '''

        coord = {'start': float(start), 'end': float(end), 'ins': ins, 'var': var}
        self._add_coordinate_options(coord, **kwargs)

        self._data.add_coordinate(**coord)

    def add_coordinate_func(self, func, start, end, **kwargs):
        '''
        Add a loop coordinate to the internal list. The first coordinate is
        the outer part of the loop, the last coordinate the inner part. The
        measurement loop will call function func with the variable value.

        Input:
            func (function): the function to call
            start (float): start value
            end (float): end value
            **kwargs: options:
                steps (int) or stepsize (float). One of these is required.
                delay (float): delay after setting value, in ms

        Output:
            None
        '''

        coord = {'start': float(start), 'end': float(end), 'func': func}
        self._add_coordinate_options(coord, **kwargs)

        self._data.add_coordinate(**coord)

    def add_measurement(self, ins, var, **kwargs):
        '''
        Add a measurement to the internal list.

        Input:
            ins (Instrument): the instrument to use
            var (string): the variable to measure

        Output:
            None
        '''

        meas = {'ins': ins, 'var': var}
        for key, val in kwargs.iteritems():
            meas[key] = val
        self._measurements.append(meas)

        self._data.add_value(**meas)

    def add_measurement_func(self, func, **kwargs):
        meas = {'func': func}
        for key, val in kwargs.iter_items():
            meas[key] = val
        self._measurements.append(meas)

        self._data.add_value(**meas)

    def emit(self, *args):
        gobject.idle_add(gobject.GObject.emit, self, *args)

    def _set_start_values(self):
        for coord in self._coords:
            val = coord['start']

            if 'ins' in coord:
                ins = coord['ins']
                ins.set(coord['var'], val)
            elif 'func' in coord:
                func = coord['func']
                func(val)

    def _do_measurements(self):
        data = []
        for m in self._measurements:
            if 'ins' in m:
                ins = m['ins']
                data.append(ins.get(m['var']))
            elif 'func' in m:
                func = m['func']
                data.append(func())
            else:
                print 'Measurement action undefined'

        return data

    def _measure(self, iter):
        '''
        The main measurement function. Convert iter to coordinates and
        set parameters accordingly. Then measure the required variables.

        Input:
            iter (int): the iteration number

        Output:
            float: extra requested timeout in ms
        '''

        extra_delay = 0

        index = self.iter_to_index(iter)
        coords = self.index_to_coords(index)
        delta = []

        for i in xrange(len(coords)):
            delta.append(index[i] - self._last_index[i])

        self._last_index = index

        # Set loop variables
        for i in xrange(len(coords)):
            if delta[i] != 0:
                val = coords[i]
                if 'ins' in self._coords[i]:
                    ins = self._coords[i]['ins']
                    ins.set(self._coords[i]['var'], val)
                elif 'func' in self._coords[i]:
                    func = self._coords[i]['func']
                    func(val)

                if 'delay' in self._coords[i]:
                    extra_delay += self._coords[i]['delay'] / 1000.0

        data = self._do_measurements()
        self._data.add(data, cor=coords)

        return extra_delay

    def start(self, blocking=False):
        '''
        Start measurement loop.

        Input:
            blocking (boolean): If false (default) do measurement in a thread.

        Output:
            None
        '''

        self._set_start_values()
        
        self._data.start_measure()

        # determine loop delay
        last_coord = self._coords[len(self._coords) - 1]
        if 'delay' in self._options:
            delay = self._options['delay']
        elif 'delay' in last_coord:
            delay = last_coord['delay']
        else:
            print 'measurement delay undefined'
            return False

        # determine loop steps
        n = 1
        for coord in self._coords:
            n *= coord['steps']

        self._last_index = []
        for i in xrange(len(self._coords)):
            self._last_index.append(0)

        if not blocking:
            self._thread = calltimer.CallTimerThread(self._measure, delay, n)
            self._thread.connect('finished', self._finished_cb)
        else:
            self._thread = calltimer.CallTimer(self._measure, delay, n)

        self._thread.start()

    def stop(self):
        if self._thread is not None:
            self._thread.set_stop_request()
            self._thread.join()

    def _finished_cb(self, sender, *args):
        print '_finished_cb'
        for i in args:
            print '    %r' % i
        self.emit('finished', self)

    def new_data(self, data):
        self.emit('new-data', data)

    def iter_to_index(self, iter):
        ret = []
        for opts in self._coords:
            v = iter % opts['steps']
            ret.append(v)
            iter = (iter - v) / opts['steps']

        return ret

    def index_to_coords(self, index):
        ret = []
        i = 0
        for opts in self._coords:
            v = opts['start'] + index[i] * opts['stepsize']
            ret.append(v)
            i += 1

        return ret

class Measurements(gobject.GObject):

    def __init__(self):
        pass

measurements = Measurements()
