# qtflow.py, handle 'flow control' in the QT lab environment
# Pieter de Groot, <pieterdegroot@gmail.com>, 2008
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

import sys
import gobject
import gtk

import time
from gettext import gettext as _L
from packages.calltimer import qttime

class FlowControl(gobject.GObject):
    '''
    Class for flow control of the QT measurement environment.
    '''

    __gsignals__ = {
            'measurement-start': (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,()),
            'measurement-end': (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,()),
            'measurement-idle': (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,()),
    }

    STATUS_STOPPED = 0
    STATUS_RUNNING = 1

    def __init__(self):
        gobject.GObject.__init__(self)
        self._status = 'stopped'
        self._measurements_running = 0
        self._abort = False

    #########
    ### signals
    #########

    def measurement_start(self):
        '''
        Indicate the start of a measurement.

        FIXME: The following is disabled due to lack of exception catching.
        This will increment the internal measurement counter, and if a
        measurement was not running, it will emit the 'measurement-start'
        signal.
        '''

        self._measurements_running += 1
        if True: #self._measurements_running == 1:
            self._set_status('running')
            self.emit('measurement-start')

    def measurement_end(self, abort=False):
        '''
        Indicate the end of a measurement.

        FIXME: The following is disabled due to lack of exception catching.
        This will decrement the internal measurement counter if abort=False,
        and set it to 0 in abort=True. If the counter reached zero (e.g. the
        last measurement was stopped, it will emit the 'measurement-end'
        signal.
        '''

        if abort:
            self._measurements_running = 0
        else:
            self._measurements_running -= 1

        if True: #self._measurements_running == 0:
            self._set_status('stopped')
            self.emit('measurement-end')

    def measurement_idle(self, delay=0.002):
        '''
        Indicate that the measurement is idle. Note that a delay <= 1msec
        will result in NO gui interaction.

        This function will check whether an abort has been requested and
        handle queued events for a time up to 'delay' (in seconds).
        
        It starts by emitting the 'measurement-idle' signal to allow callbacks
        to be executed by the time this function handles the event queue.

        A 1 msec safety margin is used to ensure proper timing (e.g. no
        events will be handled if less than this time is available). If no
        events are available a sleep of 10 msec will be performed.
        '''

        self.emit('measurement-idle')

        start = qttime()
        while True:
            self.check_abort()
            dt = qttime() - start

            gtk.gdk.threads_enter()
            while gtk.events_pending() and (dt + 0.001) < delay:
                gtk.main_iteration_do(False)
                dt = qttime() - start
            gtk.gdk.threads_leave()

            if dt + 0.01 < delay:
                time.sleep(0.01)
            else:
                time.sleep(max(0, delay - dt))
                return

    ############
    ### status
    ############

    def get_status(self):
        '''Get status, one of "running", "stopped" '''
        return self._status
    
    def _set_status(self, val):
        self._status = val

    def check_abort(self):
        '''Check whether an abort has been requested.'''

        if self._abort:
            self._abort = False
            self.measurement_end(abort=True)
            raise ValueError(_L('Human abort'))
    
    def set_abort(self):
        '''Request an abort.'''
        self._abort = True

def exception_handler(etype, value, tb):
    get_flowcontrol().measurement_end()
    raise etype, value, tb

try:
    _flowcontrol
except NameError:
    _flowcontrol = FlowControl()

    # Attach our exception handler to stop measurements
    oldhook = sys.excepthook
    sys.excepthook = exception_handler

def get_flowcontrol():
    global _flowcontrol
    return _flowcontrol

