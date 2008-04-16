def dict_to_ordered_tuples(d):
    keys = d.keys()
    keys.sort()
    ret = [(key, d[key]) for key in keys]
    return ret
