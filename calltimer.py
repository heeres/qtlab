# calltimer.py, class to do a callback several times in a separate thread.
# Reinier Heeres, <reinier@heeres.eu>, 2008
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

import time
import gobject

gobject.threads_init()
import threading

class CallTimerThread(threading.Thread, gobject.GObject):
    '''
    Class to several times do a callback with a specified delay in a separate
    thread.
    '''

    __gsignals__ = {
        'finished': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
    }

    def __init__(self, cb, delay, n, *args, **kwargs):
        '''
        Create CallTimerThread

        Input:
            cb (function): callback
            delay (float): time delay in ms
            n (int): number of times to call
            *args: optional arguments to the callback
            **kwargs: optional named arguments to the callback
        '''

        gobject.GObject.__init__(self)
        threading.Thread.__init__(self)

        self._cb = cb
        self._delay = delay
        self._n = n
        self._args = args
        self._kwargs = kwargs

        self._stop_lock = threading.Lock()
        self._stop_requested = False

    def run(self):
        tstart = time.time()
        extra_delay = 0

        i = 0
        while i < self._n:
            f = self._cb
            extra_delay += f(i, *self._args, **self._kwargs)

            if self.get_stop_request():
                print 'Stop requested'
                break

            i += 1
            if i == self._n:
                break

            # delay
            tn = time.time()
            req_delay = tstart + extra_delay / 1000.0 + float(i) * self._delay / 1000.0 - tn
            if req_delay > 0:
                time.sleep(req_delay)

        self.emit('finished', self)

    def set_stop_request(self):
        self._stop_lock.acquire()
        self._stop_requested = True
        self._stop_lock.release()

    def get_stop_request(self):
        self._stop_lock.acquire()
        ret = self._stop_requested
        self._stop_lock.release()
        return ret

    def _idle_emit(self, signal, *args):
        try:
            gobject.GObject.emit(self, signal, *args)
        except Exception, e:
            print 'Error: %s' % e

    def emit(self, signal, *args):
        gobject.idle_add(self._idle_emit, signal, *args)

class CallTimer:
    '''
    Class to several times do a callback with a specified delay, blocking.
    '''

    def __init__(self, cb, delay, n, *args, **kwargs):
        '''
        Create CallTimer

        Input:
            cb (function): callback
            delay (float): time delay in ms
            n (int): number of times to call
            *args: optional arguments to the callback
            **kwargs: optional named arguments to the callback
        '''

        self._cb = cb
        self._delay = delay
        self._n = n
        self._args = args
        self._kwargs = kwargs

    def start(self):
        tstart = time.time()

        i = 0
        while i < self._n:
            self._cb(i, *self._args, **self._kwargs)

            i += 1
            if i == self._n:
                break

            # delay
            tn = time.time()
            req_delay = tstart + float(i) * self._delay / 1000.0 - tn
            if req_delay > 0:
                time.sleep(req_delay)

class ThreadCall(threading.Thread):
    '''
    Class to execute a function in a separate thread.
    '''

    def __init__(self, func, *args, **kwargs):
        '''
        Input:
            func (function): function to call
            *args: optional arguments to the function
            **kwargs: optional named arguments to the function
        '''

        threading.Thread.__init__(self)

        self._func = func
        self._args = args
        self._kwargs = kwargs

        self.start()

    def run(self):
        self._func(*self._args, **self._kwargs)
