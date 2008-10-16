import math
import StringIO

def dict_to_ordered_tuples(dic):
    '''Convert a dictionary to a list of tuples, sorted by key.'''
    keys = dic.keys()
    keys.sort()
    ret = [(key, dic[key]) for key in keys]
    return ret

def seconds_to_str(secs):
    '''Convert a number of seconds to hh:mm:ss string.'''
    hours = math.floor(secs / 3600)
    secs -= hours * 3600
    mins = math.floor(secs / 60)
    secs = math.floor(secs - mins * 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)

def pil_to_pixbuf(pilimage):
    '''Convert a PIL image to a pixbuf.'''
    import gtk

    data = StringIO.StringIO()
    pilimage.save(data, 'ppm')
    contents = data.getvalue()
    data.close()

    loader = gtk.gdk.PixbufLoader('pnm')
    loader.write(contents, len (contents))
    pixbuf = loader.get_pixbuf()
    loader.close()

    return pixbuf

def visa_read_all(visains):
    """
    Read all available data from the input buffer.

    Hopefully this will be included in the visa code soon.
    """

    import visa
    import pyvisa.vpp43 as vpp43

    visa.warnings.filterwarnings("ignore", "VI_SUCCESS_MAX_CNT")
    try:
        buf = ""
        blen = vpp43.get_attribute(visains, vpp43.VI_ATTR_ASRL_AVAIL_NUM)
        while blen > 0:
            chunk = vpp43.read(visains, blen)
            buf += chunk
            blen = vpp43.get_attribute(visains, vpp43.VI_ATTR_ASRL_AVAIL_NUM)
    finally:
        visa._removefilter("ignore", "VI_SUCCESS_MAX_CNT")
    return buffer

def sign(val):
    '''Return the sign of a value.'''
    if val < 0:
        return -1
    else:
        return 1

def get_kwarg(kwarg, name, default):
    if name in kwarg:
        return kwarg[name]
    else:
        return default

def get_arg_type(args, kwargs, checktype, name=None):
    '''
    Get first argument of type 'typename'.
    If a specific name is specified, the kwargs dictionary is checked first.
    '''

    if name is not None and name in kwargs:
        return kwargs['name']

    for arg in args:
        if isinstance(arg, checktype):
            return arg

    return None

