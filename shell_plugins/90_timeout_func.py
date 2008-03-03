import gobject

def measure_cb(ins, var):
    print 'measure_cb: %s, %s' % (ins, var)
    return True

def start_measure(ins, var):
    global _timer_hid
    _timer_hid = gobject.timeout_add(1000, measure_cb, ins, var)

def stop_measure():
    global _timer_hid
    if _timer_hid is not None:
        gobject.source_remove(_timer_hid)
    _timer_hid = None
