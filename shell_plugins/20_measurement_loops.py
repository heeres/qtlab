#20_measurement_loops.py, measurement loops for lab environment

def _get_steps(start, end, steps, stepsize):
    if steps == 0 and stepsize == 0:
        return -1, -1

    if steps == 0:
        steps = round((end - start) / stepsize) + 1
    stepsize = (end - start) / (steps - 1)

    return steps, stepsize

def measure1d(
        read_ins, read_var,
        sweep_ins, sweep_var, start, end, steps=0, stepsize=0):

    steps, stepsize = _get_steps(start, end, steps, stepsize)
    if steps == -1:
        return []

    data = []
    for i in xrange(steps):
        x = start + stepsize * i
        sweep_ins.set(sweep_var, x)
        y = read_ins.get(read_var)
        data.append(((x), (y)))
