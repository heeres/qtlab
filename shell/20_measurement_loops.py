#20_measurement_loops.py, measurement loops for lab environment

import os
import shutil
import copy
from lib import calltimer

def _get_steps(start, end, steps, stepsize):
    if steps == 0 and stepsize == 0:
        return -1, -1

    if steps == 0:
        steps = round((end - start) / stepsize) + 1
    stepsize = (end - start) / (steps - 1)

    return steps, stepsize

def measure1d(
        read_ins, read_var,
        sweep_ins, sweep_var, start, end, **kwargs):

    m = Measurement()
    m.add_coordinate(start, end, sweep_ins, sweep_var, **kwargs)
    m.add_measurement(read_ins, read_var)

def measure2d(
        read_ins, read_var,
        xsweep_ins, xsweep_var, xstart, xend,
        ysweep_ins, ysweep_var, ystart, yend,
        delay,
        **kwargs):

    m = Measurement(delay=delay)

    if 'ysteps' in kwargs:
        m.add_coordinate(ysweep_ins, ysweep_var, ystart, yend,
            steps=kwargs['ysteps'])
    elif 'ystepsize' in kwargs:
        m.add_coordinate(ysweep_ins, ysweep_var, xstart, xend,
            stepsize=kwargs['ystepsize'])
    else:
        print 'measure2d() needs ysteps or ystepsize argument'

    if 'xsteps' in kwargs:
        m.add_coordinate(xsweep_ins, xsweep_var, xstart, xend,
            steps=kwargs['xsteps'])
    elif 'xstepsize' in kwargs:
        m.add_coordinate(xsweep_ins, xsweep_var, xstart, xend,
            stepsize=kwargs['xstepsize'])
    else:
        print 'measure2d() needs xsteps or xstepsize argument'

    m.add_measurement(read_ins, read_var)

    m.start()

def qtrun(filepath, name=''):
    if not os.path.isfile(filepath):
        raise ValueError("file '%s' does not exist" % filepath)

    dir, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)

    if ext != '.py':
        raise ValueError("file '%s' is not of type .py" % filepath)

    data = qt.data[name]
    data.create_datafile(name)
    tstr_filename = data.get_filename() + '.py'
    fulldir = data.get_fulldir()

    if os.path.isfile(tstr_filename):
        raise ValueError("file '%s' already exists, could not copy" % tstr_filename)
    shutil.copy(filepath, fulldir + '/' + tstr_filename)

    try:
        fn = fulldir + '/' + tstr_filename

        # Make sure we don't mess up our globals
        gvars = copy.copy(globals())
        execfile(fn, gvars)
    except Exception, e:
        data.close_datafile()
        print '\n    => Measurement Aborted: %s <=' % e
    finally:
        data.close_datafile()

def qtrun_thread(filepath, name=''):
    calltimer.ThreadCall(qtrun, filepath, name)

