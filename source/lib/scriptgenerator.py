import time

def get_date():
    return time.strftime('%Y-%m-%d %H:%M:%S')

class LoopGenerator():

    HEAD = \
"""# Measurement script automatically generated on %(date)s
print "\\nStarting generated measurement..."

import qt
import numpy as np

qt.mstart()
"""

    def __init__(self, **kwargs):
        self._options = kwargs
        self.reset()

    def reset(self):
        self._i = ''
        self._s = ''
        self._loopvars = []
        self._measvars = []
        self._inslist = []

        self._head = self.HEAD % dict(date=get_date())
        self._head += 'delay = %.03f\n' % self._options.get('delay', 0.010)

        self._plots = ''

    def _add_ins(self, ins):
        if ins not in self._inslist:
            self._inslist.append(ins)
            self._head += '%s = qt.instruments[%r]\n' % (ins, ins)

    def add_loop(self, var, ins, insvar, start, end, steps=None, delta=None):
        if steps:
            self._s += self._i + 'for %s in np.linspace(%s, %s, %s):\n' % (var, start, end, steps)
        elif delta:
            self._s += self._i + 'for %s in np.arange(%s, %s, %s):\n' % (var, start, end, delta)
        else:
            raise ValueError('No steps or delta specified')

        self._add_ins(ins)
        self._loopvars.append((var, dict(ins=ins, insvar=insvar, start=start, end=end, steps=steps, delta=delta)))
        self._i += '    '
        self._s += self._i + '%s.set(%r, %s)\n' % (ins, insvar, var)

    def add_meas(self, var, ins, insvar):
        if len(self._measvars) == 0:
            self._s += self._i + 'qt.msleep(delay)\n\n'

        self._s += self._i + '%s = %s.get(%r)\n' % (var, ins, insvar)

        if len(self._loopvars) == 1:
            if len(self._measvars) == 0:
                self._plots += 'p = qt.Plot2D()\n'
                self._plots += 'p.add_data(d)\n'
            elif len(self._measvars) == 1:
                self._plots += 'p.add_data(d, valdim=2, right=True)\n'

        elif len(self._loopvars) == 2:
            if len(self._measvars) == 0:
                self._plots += 'p = qt.Plot3D(d)\n'

        self._measvars.append(var)
        self._add_ins(ins)

    def add_finish(self, **kwargs):

        self._loopvars.reverse()
        lvs = [l[0] for l in self._loopvars]
        self._s += self._i + 'd.add_data_point('
        self._s += ','.join(lvs) + ','
        self._s += ','.join(self._measvars) + ')\n\n'

        for i in range(len(self._loopvars) - 1):
            self._i = self._i[:-4]
            self._s += self._i + 'd.new_block()\n'

        self._s += '\nqt.mend()\n'

    def _get_data(self):
        d = 'd = qt.Data(name=%r)\n' % self._options.get('name', 'auto')
        for var, opts in self._loopvars:
            if opts['steps']:
                d += 'd.add_coordinate(%r, start=%r, end=%r, steps=%r, size=%r)\n' % (var, opts['start'], opts['end'], opts['steps'], opts['steps'])
            else:
                d += 'd.add_coordinate(%r, start=%r, end=%r, delta=%r)\n' % (var, opts['start'], opts['end'], opts['delta'])

        for var in self._measvars:
            d += 'd.add_value(%r)\n' % (var, )

        d += 'd.create_file()\n'
        return d

    def get_script(self):
        data = self._get_data()
        return self._head + '\n' + data + '\n' + self._plots + '\n' + self._s

class MeasurementGenerator():

    HEAD = """
from lib.measurement import Measurement

m = Measurement()
"""

    def __init__(self):
        self.reset()

    def reset(self):
        self._s = ''
        self._head = self.HEAD
        self._loopvars = []
        self._measvars = []
        self._inslist = []

    def add_loop(self, var, ins, insvar, start, end, steps=None, delta=None, units=None):
        if steps:
            self._s += 'm.add_coordinate(%r, %r, start=%r, end=%r, steps=%r, units=%r)\n' % (ins, insvar, start, end, steps, units)
        elif delta:
            self._s += 'm.add_coordinate(%r, %r, start=%r, end=%r, delta=%r, units=%r)\n' % (ins, insvar, start, end, delta, units)
        else:
            raise ValueError('No steps or delta specified')

    def add_meas(self, var, ins, insvar):
        self._s += 'm.add_measurement(%r, %r)\n' % (ins, insvar)

    def add_finish(self, **kwargs):
        self._s += 'm.start()\n'

    def add_plots(self, plot_info):
        pass

    def get_script(self):
        return self._head + self._s

if __name__ == "__main__":
    for cl in LoopGenerator, MeasurementGenerator:
        s = cl()
        s.add_plots()
        s.add_loop('y', 'combined', 'magnet', -2, 2, steps=9)
        s.add_loop('x', 'combined', 'magnet', 0, 5, steps=11)
        s.add_meas('v1', 'dsgen', 'wave')
        s.add_meas('v2', 'dsgen', 'wave')
        s.add_finish()
        scr = s.get_script()
        print 'Script:\n%s' % (scr, )

