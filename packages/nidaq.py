import ctypes
import types
import numpy

nidaq = ctypes.windll.nicaiu

int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
TaskHandle = uInt32

DAQmx_Val_Cfg_Default = int32(-1)
DAQmx_Val_Volts = 10348
DAQmx_Val_Rising = 10280
DAQmx_Val_FiniteSamps = 10178
DAQmx_Val_GroupByChannel = 0

def CHK(err):
    '''Error checking routine'''

    if err < 0:
        buf_size = 100
        buf = ctypes.create_string_buffer('\000' * buf_size)
        nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
        raise RuntimeError('Nidaq call failed with error %d: %s' % \
            (err, repr(buf.value)))

def buf_to_list(buf):
    name = ''
    namelist = []
    for ch in buf:
        if ch in '\000 \t\n':
            if len(name) > 0:
                namelist.append(name)
                name = ''
            if ch == '\000':
                break
        else:
            name += ch

    return namelist

def get_device_names():
    '''Return a list of available NIDAQ devices.'''

    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetSysDevNames(ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def reset_device(dev):
    '''Reset device "dev"'''
    nidaq.DAQmxResetDevice(dev)

def get_physical_input_channels(dev):
    '''Return a list of physical input channels on a device.'''

    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetDevAIPhysicalChans(dev, ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def get_physical_output_channels(dev):
    '''Return a list of physical output channels on a device.'''

    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetDevAOPhysicalChans(dev, ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def read_dac(devchan, samples=1, freq=10000.0, minv=-10.0, maxv=10.0,
            timeout=10.0):
    '''
    Read up to max_samples from a DAC. Seems to have trouble reading 1 sample!

    Input:
        devchan (string): device/channel specifier, such as Dev1/ai0
        samples (int): the number of samples to read
        freq (float): the sampling frequency
        minv (float): the minimum voltage
        maxv (float): the maximum voltage
        timeout (float): the time in seconds to wait for completion

    Output:
        A numpy.array with the data on success, None on error
    '''

    if samples == 1:
        retsamples = 1
        samples = 2
    else:
        retsamples = samples

    data = numpy.zeros(samples, dtype=numpy.float64)

    taskHandle = TaskHandle(0)
    CHK(nidaq.DAQmxCreateTask("", ctypes.byref(taskHandle)))
    CHK(nidaq.DAQmxCreateAIVoltageChan(taskHandle, devchan, "",
                                       DAQmx_Val_Cfg_Default,
                                       float64(minv), float64(maxv),
                                       DAQmx_Val_Volts, None))

    CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle, "", float64(freq),
                                    DAQmx_Val_Rising, DAQmx_Val_FiniteSamps,
                                    uInt64(samples)));

    CHK(nidaq.DAQmxStartTask(taskHandle))

    read = int32()
    CHK(nidaq.DAQmxReadAnalogF64(taskHandle, samples, float64(timeout),
                                 DAQmx_Val_GroupByChannel, data.ctypes.data,
                                 samples, ctypes.byref(read), None))

    if taskHandle.value != 0:
        nidaq.DAQmxStopTask(taskHandle)
        nidaq.DAQmxClearTask(taskHandle)

    if read > 0:
        if retsamples == 1:
            return data[0]
        else:
            return data[:read.value]
    else:
        return None

def write_dac(devchan, data, freq=10000.0, minv=-10.0, maxv=10.0,
                timeout=10.0):
    '''
    Write dac values

    Input:
        devchan (string): device/channel specifier, such as Dev1/ao0
        data (int/float/numpy.array): data to write
        freq (float): the the minimum voltage
        maxv (float): the maximum voltage
        timeout (float): the time in seconds to wait for completion

    Output:
        Number of values written
    '''

    if type(data) in (types.IntType, types.FloatType):
        data = numpy.array([data], dtype=numpy.float64)
    elif isinstance(data, numpy.ndarray):
        if data.dtype is not numpy.float64:
            data = numpy.array(data, dtype=numpy.float64)
    elif len(data) > 0:
        data = numpy.array(data, dtype=numpy.float64)
    samples = len(data)

    taskHandle = TaskHandle(0)
    CHK(nidaq.DAQmxCreateTask("", ctypes.byref(taskHandle)))
    CHK(nidaq.DAQmxCreateAOVoltageChan(taskHandle, devchan, "",
        float64(minv), float64(maxv), DAQmx_Val_Volts, None))
    CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle, "", float64(freq),
        DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, uInt64(samples)))

    CHK(nidaq.DAQmxStartTask(taskHandle))
    written = int32()
    CHK(nidaq.DAQmxWriteAnalogF64(taskHandle, samples, 0, float64(timeout),
        DAQmx_Val_GroupByChannel, data.ctypes.data,
        ctypes.byref(written), None))

    if taskHandle.value != 0:
        nidaq.DAQmxStopTask(taskHandle)
        nidaq.DAQmxClearTask(taskHandle)

    return written.value

