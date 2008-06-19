import math

def dict_to_ordered_tuples(d):
    keys = d.keys()
    keys.sort()
    ret = [(key, d[key]) for key in keys]
    return ret

def seconds_to_str(secs):
    hours = math.floor(secs / 3600)
    secs -= hours * 3600
    mins = math.floor(secs / 60)
    secs = math.floor(secs - mins * 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)
