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
import types

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

    def measurement_idle(self, delay=0.0, exact=False, emit_interval=1):
        '''
        Indicate that the measurement is idle and handle events.

        This function will check whether an abort has been requested and
        handle queued events for a time up to 'delay' (in seconds).
        
        It starts by emitting the 'measurement-idle' signal to allow callbacks
        to be executed by the time this function handles the event queue.
        After that it handles events and sleeps for periods of 10msec. Every
        <emit_interval> seconds it will emit another measurement-idle signal.

        If exact=True, timing should be a bit more precise, but in this case
        a delay <= 1msec will result in NO gui interaction.
        '''

        start = qttime()

        self.emit('measurement-idle')
        lastemit = qttime()

        while True:
            self.check_abort()

            curtime = qttime()
            if curtime - lastemit > emit_interval:
                self.emit('measurement-idle')
                lastemit = curtime

            dt = curtime - start

            gtk.gdk.threads_enter()
            while gtk.events_pending() and (not exact or (dt + 0.001) < delay):
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

def exception_handler(self, etype, value, tb):
    get_flowcontrol().measurement_end()
    raise etype, value, tb

class Scheduler():
    '''
    Schedule a certain task to run either periodically on a 'timeout', or
    when receiving a 'measurement-idle' signal (or both).
    '''

    def __init__(self, function, timeout=1, idle_mintime=1,
                 timeout_mode=True, idle_mode=False, start=True):
        self._function = function
        self._flow = get_flowcontrol()
        self._timeout_mode = timeout_mode
        self._idle_mode = idle_mode

        ##  IDLE SPECIFIC INIT
        self._idle_hid = None
        self._idle_mintime = idle_mintime
        self._idle_lasttime = 0

        ## TIMEOUT SPECIFIC INIT
        self._timer_hid = None
        self._mstart_hid = None
        self._mend_hid = None
        self._timeout = timeout

        if start is True:
            self.start()

    ### START CODE TIMEOUT MODE

    def _measurement_connect(self):
        if self._mstart_hid is None:
            self._mstart_hid = self._flow.connect("measurement-start", self._measurement_start_cb)
        if self._mend_hid is None:
            self._mend_hid = self._flow.connect("measurement-end", self._measurement_end_cb)

    def _measurement_disconnect(self):
        if self._mstart_hid is not None:
            self._flow.disconnect(self._mstart_hid)
            self._mstart_hid = None
        if self._mend_hid is not None:
            self._flow.disconnect(self._mend_hid)
            self._mend_hid = None

    def _measurement_start_cb(self, widget):
        self._stop_timeout()

    def _measurement_end_cb(self, widget):
        self._start_timeout()

    def _timeout_cb(self):
        self._function()
        return True

    def _start_timeout(self):
        if self._timer_hid is None:
            self._timer_hid = gobject.timeout_add(int(self._timeout*1000), self._timeout_cb)
        else:
            print 'timer already started'

    def _start_timeout_and_connect(self):
        meas_status = self._flow.get_status()
        if (meas_status == 'stopped'):
            self._start_timeout()
            self._measurement_connect()
        elif (meas_status == 'running'):
            self._measurement_connect()

    def _stop_timeout(self):
        if self._timer_hid is not None:
            gobject.source_remove(self._timer_hid)
            self._timer_hid = None
        else:
            print 'timer already stopped'

    def _stop_timeout_and_disconnect(self):
        self._stop_timeout()
        self._measurement_disconnect()

    def set_timeout(self, timeout):
        '''
        Set the time interval for the periodic task.
        '''
        self._timeout = timeout
        if self._timer_hid is not None:
            self._stop_timeout()
            self._start_timeout()

    def get_timeout(self):
        '''
        Get the time interval for the periodic task.
        '''
        return self._timeout

    def set_timeout_mode(self, val, restart=True):
        '''
        (De)Activate timeout mode. If restart=True the scheduler will be
        restarted with the new option.
        '''

        if type(val) is not types.BooleanType:
            print 'wrong input type'
            return
        self._timeout_mode = val

        if restart:
            self.restart()

    def get_timeout_mode(self):
        '''
        Get the current status for timeout mode.
        '''
        return self._timeout_mode

    ### END CODE TIMEOUT MODE

    ### START CODE IDLE MODE

    def _measurement_idle_cb(self, widget):
        now = qttime()
        if (now - self._idle_lasttime) > self._idle_mintime:
            self._idle_lasttime = now
            self._function()

    def _start_idle(self):
        if self._idle_hid is None:
            self._idle_hid = self._flow.connect("measurement-idle", self._measurement_idle_cb)
        else:
            print 'already waiting for idle'

    def _stop_idle(self):
        if self._idle_hid is not None:
            self._flow.disconnect(self._idle_hid)
            self._idle_hid = None
        else:
            print 'already stopped waiting for idle'

    def set_idle_mintime(self, mintime):
        '''
        Set the minimum time to wait before running the task again.
        '''
        self._idle_mintime = mintime

    def get_idle_mintime(self):
        '''
        Get the minimum time to wait before running the task again.
        '''
        return self._idle_mintime

    def set_idle_mode(self, val, restart=True):
        '''
        (De)Activate idle mode. If restart=True the scheduler will be
        restarted with the new option.
        '''

        if type(val) is not types.BooleanType:
            print 'wrong input type'
            return
        self._idle_mode = val

        if restart:
            self.restart()

    def get_idle_mode(self):
        '''
        Get the current status for idle mode
        '''
        return self._idle_mode

    ### END CODE IDLE MODE

    def start(self):
        '''
        Start the task in either idle mode, timeout mode or both, depending on which are set to True.
        See: set_idle_mode & set_timeout_mode
        '''
        if self._idle_mode:
            self._start_idle()
        if self._timeout_mode:
            self._start_timeout_and_connect()

    def stop(self):
        '''
        Stop the scheduled task. If running both in 'timeout' and 'idle' mode, then both will be stopped.
        '''
        if self._timer_hid is not None:
            self._stop_timeout_and_disconnect()
        if self._idle_hid is not None:
            self._stop_idle()

    def restart(self):
        '''
        Restart scheduler with current settings.
        '''
        self.stop()
        self.start()

try:
    _flowcontrol
except NameError:
    _flowcontrol = FlowControl()

def get_flowcontrol():
    global _flowcontrol
    return _flowcontrol

