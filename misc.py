import math
import StringIO

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

def pil_to_pixbuf(pilimage):
    import gtk

    file = StringIO.StringIO()
    pilimage.save(file, 'ppm')
    contents = file.getvalue()
    file.close()

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
        buffer = ""
        len = vpp43.get_attribute(self.vi, vpp43.VI_ATTR_ASRL_AVAIL_NUM)
        while len > 0:
            chunk = vpp43.read(self.vi, len)
            buffer += chunk
            len = vpp43.get_attribute(self.vi, vpp43.VI_ATTR_ASRL_AVAIL_NUM)
    finally:
        visa._removefilter("ignore", "VI_SUCCESS_MAX_CNT")
    return buffer

def sign(val):
    if val < 0:
        return -1
    else:
        return 1

