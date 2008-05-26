# M2I2030.py driver class, to perform the communication between the Wrapper and the card
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <mcschaafsma@gmail.com>, 2008
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

from ctypes import *
from instrument_plugins._Spectrum_M2i2030.errors import errors as _spcm_errors
from instrument_plugins._Spectrum_M2i2030.regs import regs as _spcm_regs
from instrument import Instrument
import pickle
from time import sleep, time
import types
import logging
import numpy

class Spectrum_M2i2030(Instrument):
    '''
    This is the driver for the Spectrum M2i2030 data acquisition card

    Usage:
    Initialize with
    <name> = instruments.create('name', 'Spectrum_M2i2030')

    TODO:
    1) Fix get all
    2) Fix readout modes
    3) Fix representation and organisation of data
    4) Readout of two channels
    5) Add self._cardopened oid ??
    '''

    def __init__(self, name):
        '''
        Initializes the dataacquisition card, and communicates with the wrapper.

        Usage:
            Use in a simple measurementloop as:
            <name>.init_default(memsize, posttrigger, amp)

            And repeat:
            <name>.start_with_trigger_and_waitready()
            <name>.readout_singlemode_float()

        Input:
            name (string) : name of the instrument

        Output:
            None
        '''
        # Initialize wrapper
        logging.info(__name__ + ' : Initializing instrument Spectrum')
        Instrument.__init__(self, name, tags=['physical'])

        # Load dll and open connection
        self._card_is_open = False
        self._load_dll()
        self._open()

        # add parameters
        self.add_parameter('timeout', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('trigger_delay', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('memsize', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('post_trigger', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('input_offset_ch0', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('input_offset_ch1', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('input_amp_ch0', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('input_amp_ch1', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('spc_samplerate', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('reference_clock', flags=Instrument.FLAG_GETSET, type=types.IntType)
        self.add_parameter('segmentsize', flags=Instrument.FLAG_GETSET, type=types.IntType)

        self.add_parameter('serial', flags=Instrument.FLAG_GET)
        self.add_parameter('ramsize', flags=Instrument.FLAG_GET)
        self.add_parameter('card_status', flags=Instrument.FLAG_GET)

        # add functions
        self.add_function('start')
        self.add_function('start_with_trigger_and_waitready')
        self.add_function('reset')
        self.add_function('writesetup')
        self.add_function('enable_trigger')
        self.add_function('force_trigger')
        self.add_function('disable_trigger')
        self.add_function('stop')
        self.add_function('waitprefull')
        self.add_function('waittrigger')
        self.add_function('waitready')
        self.add_function('set_card_mode_singleshotreadout')
        self.add_function('select_channel0')
        self.add_function('select_channel1')
        self.add_function('select_channel01')
        self.add_function('input_term_ch0_50Ohm')
        self.add_function('input_term_ch0_1MOhm')
        self.add_function('input_term_ch1_50Ohm')
        self.add_function('input_term_ch1_1MOhm')
        self.add_function('set_clock_50Ohm')
        self.add_function('set_clock_highOhm')
        self.add_function('set_clockmode_pll')
        self.add_function('set_clockmode_quartz1')
        self.add_function('set_single_mode')
        self.add_function('trigger_mode_pos')
        self.add_function('trigger_mode_neg')
        self.add_function('set_trigger_ORmask_tmask_ext0')
        self.add_function('trigger_termination_50Ohm')
        self.add_function('trigger_termination_highOhm')
        self.add_function('readout_singlemode')

        self.reset()

    def __del__(self):
        '''
        Closes up the Spectrum driver

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Deleting Spectrum instrument')
        self._close()

    def _load_dll(self):
        '''
        Loads the functions from spcm_win32.dll

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Loading spcm_win32.dll')
        self._spcm_win32 = windll.LoadLibrary('C:\\WINDOWS\\System32\\spcm_win32')

        self._spcm_win32.open           = self._spcm_win32["_spcm_hOpen@4"]
        self._spcm_win32.close          = self._spcm_win32["_spcm_vClose@4"]
        self._spcm_win32.SetParam32     = self._spcm_win32["_spcm_dwSetParam_i32@12"]
        self._spcm_win32.SetParam64m    = self._spcm_win32["_spcm_dwSetParam_i64m@16"]
        self._spcm_win32.SetParam64     = self._spcm_win32["_spcm_dwSetParam_i64@16"]
        self._spcm_win32.GetParam32     = self._spcm_win32["_spcm_dwGetParam_i32@12"]
        self._spcm_win32.GetParam64m    = self._spcm_win32["_spcm_dwGetParam_i64m@16"]
        self._spcm_win32.GetParam64     = self._spcm_win32["_spcm_dwGetParam_i64@12"]
        self._spcm_win32.DefTransfer64m = self._spcm_win32["_spcm_dwDefTransfer_i64m@36"]
        self._spcm_win32.DefTransfer64  = self._spcm_win32["_spcm_dwDefTransfer_i64@36"]
        self._spcm_win32.InValidateBuf  = self._spcm_win32["_spcm_dwInvalidateBuf@8"]
        self._spcm_win32.GetErrorInfo   = self._spcm_win32["_spcm_dwGetErrorInfo_i32@16"]

    # Base communication tools
    def _open(self):
        '''
        Opens the card, and creates a handle.
        Only execute once.

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Try to open card')
        if ( not self._card_is_open):
          self._spcm_win32.handel = self._spcm_win32.open('spcm0')
          self._card_is_open = True
        else:
          logging.warning(__name__ + ' : Card is already open !')

        if (self._spcm_win32.handel==0):
            logging.error(__name__ + ' : Unable to open card')
            self._card_is_open = False

    def _close(self):
        '''
        Closes the card

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Try to close card')
        self._spcm_win32.close(self._spcm_win32.handel)

    def _set_param(self, regnum, regval):
        '''
        Sets the register to the specified value
        Returns the '0', if succesfull,
        returns the errormessage if an error occurred

        Register flags are listed in M2I2030_regs.py

        Input:
            regnum (register flag)       : Flag corresponding with the register
            regval (register flag)       : Flag corresponding with the value to be set


        Output:
            '0' or errormessage (string)
        '''
        logging.debug(__name__ + ' : Set reg %s to %s' %(regnum, regval))
        err = self._spcm_win32.SetParam32(self._spcm_win32.handel, regnum, regval)
        if (err==0):
            return 0
        else:
            return self._get_error()

    def _get_param(self, regnum):
        '''
        Reads out a register on the card.
        Returns the register value, if succesfull,
        returns the errormessage if an error occurred

        Register flags are listed in M2I2030_regs.py

        Input:
            regnum (register flag)       : Flag corresponding with the register

        Output:
            value (int)     : Register value
            or
            error (string)  : Error message
        '''
        logging.debug(__name__ + ' : Reading Reg %s' %(regnum))
        val = c_int()
        p_antw = pointer(val)

        err = self._spcm_win32.GetParam32(self._spcm_win32.handel, regnum, p_antw)
        if (err==0):
            return p_antw.contents.value
        else:
            logging.error(__name__ + ' : Error %s while accessing reg %s' %(err,regnum))
            return self._get_error()

    def _invalidate_buffer(self, buffertype):
        '''
        Discards the buffer.

        Input:
            buffertype (register flag) : the flag containing the type of buffer.
                                         probably SPCM_BUF_DATA

        Output:
            None
        '''
        logging.debug(__name__ + ' : Invalidating buffer')
        er = self._spcm_win32.InValidateBuf(self._spcm_win32.handel, buffertype)

    def _get_error(self):
        '''
        Reads out and returns the error buffer

        Input:
            None

        Output:
            Errormessage (string)
        '''
        # try to read out error
        logging.debug(__name__ + ' : Reading error')
        j = (c_char * 200)()
        e1 = c_int()
        e2 = c_int()
        p_errortekst = pointer(j)
        p_er1 = pointer(e1)
        p_er2 = pointer(e2)

        self._spcm_win32.GetErrorInfo(self._spcm_win32.handel, p_er1, p_er2, p_errortekst)

        tekst = ""

        for ii in range(200):
            tekst  = tekst + p_errortekst.contents[ii]
        logging.error(__name__ + ' : ' + tekst)
        return tekst

    def _do_get_serial(self):
        '''
        Reads out the serial number of the card.

        Input:
            None

        Output:
            serial (int) : The serial number
        '''
        logging.debug(__name__ + ' : Reading serial number')
        return self._get_param(_spcm_regs.SPC_PCISERIALNO)

    def _do_get_ramsize(self):
        '''
        Returns the size of the random access memory installed
        on the card

        Input:
            None

        Output:
            ramsize (int) : number of bytes
        '''
        logging.debug(__name__ + ' : Reading Ram size')
        return self._get_param(_spcm_regs.SPC_PCIMEMSIZE)

    def init_default(self, memsize=2048, posttrigger=1024, amp=500):
        '''
        Initiates the card in default single shot readout mode.
        Trigger is set on ext0 with a positive slope
        The buffersize and range are set

        Input:
            memsize (int)   : number of datapoints that are read out
                                default = 2048
            posttrigger(int): number of datapoints taken after the trigger
                                default = 1024
            amp (int)       : half of the range in millivolts
                                default = 500

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initialing card for default single shot readout')

        # Set the modes
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_EXT0_MODE, _spcm_regs.SPC_TM_POS);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_EXT0_PULSEWIDTH, 0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_OUTPUT, 0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_TERM, 1);

        # Set channel information
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_CHENABLE, _spcm_regs.CHANNEL0)
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_CARDMODE, _spcm_regs.SPC_REC_STD_SINGLE)
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_MEMSIZE, memsize)
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_POSTTRIGGER, posttrigger)
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_AMP0, amp)

        # Set the masks
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_ORMASK, _spcm_regs.SPC_TMASK_EXT0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_ANDMASK,        0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_CH_ORMASK0,     0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_CH_ORMASK1,     0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_CH_ANDMASK0,    0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_CH_ANDMASK1,    0);

    def init_multiple_recording(self, nums = 1024, segsize=2048, posttrigger=1024, amp=500): #use this one
        '''
        Initiates the card in default multiple recording mode.
        Trigger is set on ext0 with a positive slope
        The buffersize and range are set, even as the number of readouts

        Input:
            nums (int)      : number of consequtive measurements
                                default = 128
            segsize (int)   : number of datapoints that are read out in one shot
                                default = 2048
            posttrigger(int): number of datapoints taken after the trigger
                                default = 1024
            amp (int)       : half of the range in millivolts
                                default = 500

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initialing card for default multiple shot readout')

        memsize = nums*segsize

        # Set the modes
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_EXT0_MODE, _spcm_regs.SPC_TM_POS);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_EXT0_PULSEWIDTH, 0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_OUTPUT, 0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_TERM, 1);

        # Set channel information
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_CHENABLE, _spcm_regs.CHANNEL0)
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_CARDMODE, _spcm_regs.SPC_REC_STD_MULTI)
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_SEGMENTSIZE, segsize)
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_MEMSIZE, memsize)
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_POSTTRIGGER, posttrigger)
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_AMP0, amp)

        # Set the masks
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_ORMASK, _spcm_regs.SPC_TMASK_EXT0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_ANDMASK,        0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_CH_ORMASK0,     0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_CH_ORMASK1,     0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_CH_ANDMASK0,    0);
        self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_TRIG_CH_ANDMASK1,    0);

    #  Initialization functions
    def start(self):
        '''
        Starts the card

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Card started')
        self._set_param(_spcm_regs.SPC_M2CMD, _spcm_regs.M2CMD_CARD_START)

    def start_with_trigger(self):
        '''
        Start the card, enables trigger, and waits till
        the trigger went off

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Card started with trigger')
        self._set_param(_spcm_regs.SPC_M2CMD,
            _spcm_regs.M2CMD_CARD_START | _spcm_regs.M2CMD_CARD_ENABLETRIGGER)

    def start_with_trigger_and_waitready(self):
        '''
        Start the card, enables trigger, and waits till
        the trigger went off

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Card started with trigger and waitready')
        self._set_param(_spcm_regs.SPC_M2CMD,
            _spcm_regs.M2CMD_CARD_START | _spcm_regs.M2CMD_CARD_ENABLETRIGGER | _spcm_regs.M2CMD_CARD_WAITREADY)

    def reset(self):
        '''
        Resets the card to default values

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Reset card')
        self._set_param(_spcm_regs.SPC_M2CMD, _spcm_regs.M2CMD_CARD_RESET)
        self.get_all()

    def get_all(self):
        logging.debug(__name__ + ' : getting all values from card')

        self.get_input_amp_ch0()
        self.get_input_amp_ch1()
        self.get_input_offset_ch0()
        self.get_input_offset_ch1()

        self.get_memsize()
        self.get_segmentsize()
        self.get_post_trigger()
        self.get_spc_samplerate()
        self.get_reference_clock()
        self.get_trigger_delay()

        self.get_timeout()

        self.get_ramsize()
        self.get_serial()

    def writesetup(self):
        '''
        Writes the current setup to the card without starting the hardware.
        This command may be useful if changing some internal settings
        like clock frequency and enabling outputs.

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Write setup enabled')
        self._set_param(_spcm_regs.SPC_M2CMD, _spcm_regs.M2CMD_CARD_WRITESETUP)

    def enable_trigger(self):
        '''
        Enables the trigger

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Enable trigger')
        self._set_param(_spcm_regs.SPC_M2CMD, _spcm_regs.M2CMD_CARD_ENABLETRIGGER)

    def force_trigger(self):
        '''
        Force a trigger

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Force trigger')
        self._set_param(_spcm_regs.SPC_M2CMD, _spcm_regs.M2CMD_CARD_FORCETRIGGER)

    def disable_trigger(self):
        '''
        Disables the trigger

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Disable trigger')
        self._set_param(_spcm_regs.SPC_M2CMD, _spcm_regs.M2CMD_CARD_DISABLETRIGGER)

    def stop(self):
        '''
        Stop the card

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Stop card')
        self._set_param(_spcm_regs.SPC_M2CMD, _spcm_regs.M2CMD_CARD_STOP)

    def waitprefull(self):
        '''
        Acquisition modes only: the command waits until the pretrigger
        area has once been filled with data. After pretrigger area
        has been filled the internal trigger engine starts to look for trigger
        events if the trigger detection has been enabled.

        Input:
            None

        Output:
            None
       '''
        logging.debug(__name__ + ' : Wait prefull enabled')
        self._set_param(_spcm_regs.SPC_M2CMD, _spcm_regs.M2CMD_WAITPREFULL)

    def waittrigger(self):
        '''
        Waits until the first trigger event has been detected by the card.
        If using a mode with multiple trigger events like Multiple Recording
        or Gated Sampling there only the first trigger detection will
        generate an interrupt for this wait command.

        Input:
            None

        Output:
            None
       '''
        logging.debug(__name__ + ' : Wait trigger enabled')
        self._set_param(_spcm_regs.SPC_M2CMD, _spcm_regs.M2CMD_WAITTRIGGER)

    def waitready(self):
        '''
        Waits till trigger signal is received

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Waitready activated')
        self._set_param(_spcm_regs.SPC_M2CMD, _spcm_regs.M2CMD_CARD_WAITREADY)

    def _do_set_timeout(self, timeout):
        '''
        Set card timeout

        Input:
            timeout (int) : timeout in milliseconds

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set timeout to %s' % timeout)
        self._set_param(_spcm_regs.SPC_TIMEOUT, timeout)

    def _do_get_timeout(self):
        '''
        Get card timeout

        Input:
            None

        Output:
            timeout (int) : timeout in milliseconds
        '''
        logging.debug(__name__ + ' : Get timeout')
        return self._get_param(_spcm_regs.SPC_TIMEOUT)

    def _do_get_card_status(self):
        '''
        Returns the card status, see p136 of manual

        Input:
            None

        Output:
            status (int): Integer corresponding to the card thatus
        '''
        logging.debug(__name__ + ' : Get card status')
        return self._get_param(_spcm_regs.SPC_M2STATUS)

    def _do_set_trigger_delay(self, nums):
        '''
        Set the trigger delay

        Input:
            nums (int) : number of sample clocks delay

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set trigger delay to %s' % nums)
        self._set_param(_spcm_regs.SPC_TRIG_DELAY, nums)

    def _do_get_trigger_delay(self):
        '''
        Get the trigger delay

        Input:
            None

        Output:
            nums (int) : number of sample clocks delay

        '''
        logging.debug(__name__ + ' : Get trigger delay')
        return self._get_param(_spcm_regs.SPC_TRIG_DELAY)

    def set_card_mode_singleshotreadout(self):
        '''
        Set the card to the single shot readout mode.
        Use this one for default measurements

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set to single shot readout')
        self._set_param(_spcm_regs.SPC_CARDMODE, _spcm_regs.SPC_REC_STD_SINGLE)

    def _do_set_memsize(self, lMemsize):
        '''
        Sets the size of the datapoints taken

        Input:
            lMemsize (int) : number of datapoints

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set memsize to %s' % lMemzise)
        self._set_param(_spcm_regs.SPC_MEMSIZE, lMemsize)

    def _do_get_memsize(self):
        '''
        Get the number of datapoints that are read out

        Input:
            None

        Output:
            memsize (int) : number of datapoints
        '''
        logging.debug(__name__ + ' : Get memzise')
        return self._get_param(_spcm_regs.SPC_MEMSIZE)

    def _do_set_segmentsize(self, lSegsize):
        '''
        Sets the size of the datapoints taken per trigger

        Input:
            lMemsize (int) : number of datapoints

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set segment size to %s' % lSegsize)
        self._set_param(_spcm_regs.SPC_SEGMENTSIZE, lSegsize)

    def _do_get_segmentsize(self):
        '''
        Get the number of datapoints that are read out
        per trigger

        Input:
            None

        Output:
            segmentsize (int) : number of datapoints
        '''
        logging.debug(__name__ + ' : Get segment size')
        return self._get_param(_spcm_regs.SPC_SEGMENTSIZE)

    def _do_set_post_trigger(self, posttrigger):
        '''
        Sets the number of points that are read out
        after the trigger event

        Input:
            posttrigger (int) : number of points

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set post trigger to %s' % posttrigger)
        self._set_param( _spcm_regs.SPC_POSTTRIGGER, posttrigger)

    def _do_get_post_trigger(self):
        '''
        Gets the number of points that are read out
        after the trigger event

        Input:
            None

        Output:
            posttrigger (int) : number of points
        '''
        logging.debug(__name__ + ' : Get post trigger')
        return self._get_param( _spcm_regs.SPC_POSTTRIGGER)

    def select_channel0(self):
        '''
        Select channel 0 for measurement

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Select channel 0')
        self._set_param(_spcm_regs.SPC_CHENABLE, _spcm_regs.CHANNEL0)

    def select_channel1(self):
        '''
        Select channel 1 for measurement

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Select channel 1')
        self._set_param(_spcm_regs.SPC_CHENABLE, _spcm_regs.CHANNEL1)

    def select_channel01(self):
        '''
        Select channels 0 and 1 for measurement

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Select channels 0 and 1')
        self._set_param(_spcm_regs.SPC_CHENABLE, _spcm_regs.CHANNEL0 | _spcm_regs.CHANNEL1)

    def _do_set_input_amp_ch0(self, amp):
        '''
        Sets the amplitude of the range of channel 0
        The range defines the precision of the analog-digital conversion

        Input:
            amp (int): amplitude of the channel in millivolts

        Output:
            None
        '''
        logging.debug(__name__ + ' : Setting input amp0 to %s' % amp)
        self._set_param(_spcm_regs.SPC_AMP0, amp)

    def _do_set_input_amp_ch1(self, amp):
        '''
        Sets the amplitude of the range of channel 1
        The range defines the precision of the analog-digital conversion

        Input:
            amp (int): amplitude of the channel in millivolts

        Output:
            None
        '''
        logging.debug(__name__ + ' : Setting input amp1 to %s' % amp)
        self._set_param(_spcm_regs.SPC_AMP1, amp)

    def _do_set_input_offset_ch0(self, offset):
        '''
        Sets the offset of channel 0 as a percentage
        of the range

        Input:
            offset (int): percentage of range

        Output:
            None
        '''
        logging.debug(__name__ + ' : Setting input offset0 to %s' % offset)
        self._set_param(_spcm_regs.SPC_OFFS0, offset)

    def _do_set_input_offset_ch1(self, offset):
        '''
        Sets the offset of channel 1 as a percentage
        of the range

        Input:
            offset (int): percentage of range

        Output:
            None
        '''
        logging.debug(__name__ + ' : Setting input offset1 to %s' % offset)
        self._set_param(_spcm_regs.SPC_OFFS1, offset)

    def _do_get_input_amp_ch0(self):
        '''
        Gets the amplitude of the range of channel 0
        The range defines the precision of the analog-digital conversion

        Input:
            None

        Output:
            amp (int): amplitude of the channel in millivolts
        '''
        logging.debug(__name__ + ' : Getting input amp0')
        return self._get_param(_spcm_regs.SPC_AMP0)

    def _do_get_input_amp_ch1(self):
        '''
        Gets the amplitude of the range of channel 1
        The range defines the precision of the analog-digital conversion

        Input:
            None

        Output:
            amp (int): amplitude of the channel in millivolts
        '''
        logging.debug(__name__ + ' : Getting input amp1')
        return self._get_param(_spcm_regs.SPC_AMP1)

    def _do_get_input_offset_ch0(self):
        '''
        Gets the offset of channel 0 as a percentage
        of the range

        Input:
            None

        Output:
            offset (int): percentage of range
        '''
        logging.debug(__name__ + ' : Getting input offset0')
        return self._get_param(_spcm_regs.SPC_OFFS0)

    def _do_get_input_offset_ch1(self):
        '''
        Gets the offset of channel 1 as a percentage
        of the range

        Input:
            None

        Output:
            offset (int): percentage of range
        '''
        logging.debug(__name__ + ' : Getting input offset1')
        return self._get_param(_spcm_regs.SPC_OFFS1)

    def input_term_ch0_50Ohm(self):
        '''
        Sets the input termination of
        channel 0 to 50 Ohm

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set input termination ch0 to 50 Ohm')
        self._set_param(_spcm_regs.SPC_50OHM0, 1)

    def input_term_ch0_1MOhm(self):
        '''
        Sets the input termination of
        channel 0 tot 1 MOhm

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set input termination ch0 to 1 MOhm')
        self._set_param(_spcm_regs.SPC_50OHM0, 0)

    def input_term_ch1_50Ohm(self):
        '''
        Sets the input termination of
        channel 1 to 50 Ohm

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set input termination ch1 to 50 Ohm')
        self._set_param(_spcm_regs.SPC_50OHM1, 1)

    def input_term_ch1_1MOhm(self):
        '''
        Sets the input termination of
        channel 1 to 1 MOhm

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set input termination ch1 to 1 MOhm')
        self._set_param(_spcm_regs.SPC_50OHM1, 0)

    def set_clock_50Ohm(self):
        '''
        Sets the clock input termination to 50 Ohm

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set clock termination to 50 Ohm')
        self._set_param(_spcm_regs.SPC_CLOCK50OHM, 1)

    def set_clock_highOhm(self):
        '''
        Sets the clock input termination
        to high impedance

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set clock termination to high impedance')
        self._set_param(_spcm_regs.SPC_CLOCK50OHM, 0)

    def set_clockmode_pll(self):
        '''
        Sets the clock mode to PLL

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set clock mode to pll')
        self._set_param(_spcm_regs.SPC_CLOCKMODE, _spcm_regs.SPC_CM_INTPLL)

    def set_clockmode_quartz1(self):
        '''
        Sets the clock mode to quartz1

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set clock mode to quartz1')
        self._set_param(_spcm_regs.SPC_CLOCKMODE, _spcm_regs.SPC_CM_QUARTZ1)

    def _do_set_spc_samplerate(self, rate):
        '''
        defines the sampling rate in Hz for internal
        sample rate generation

        Input:
            rate (int) : sample rate in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set spc samplerate to %s' % rate)
        rate = int(rate)
        self._set_param(_spcm_regs.SPC_SAMPLERATE, rate)

    def _do_get_spc_samplerate(self):
        '''
        gets the sampling rate in Hz for internal
        sample rate generation

        Input:
            None

        Output:
            rate (int) : sample rate in Hz
        '''
        logging.debug(__name__ + ' : Get spc samplerate')
        return self._get_param(_spcm_regs.SPC_SAMPLERATE)

    def _do_set_reference_clock(self, freq):
        '''
        Programs the external reference clock

        Input:
            freq (int) : frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set reference clock freq to %s' % freq)
        self._set_param(_spcm_regs.SPC_REFERENCECLOCK, freq)

    def _do_get_reference_clock(self):
        '''
        Gets the external reference clock setting

        Input:
            None

        Output:
            freq (int) : frequency in Hz
        '''
        logging.debug(__name__ + ' : Get reference clock setting')
        return self._get_param(_spcm_regs.SPC_REFERENCECLOCK)

    def set_single_mode(self):
        '''
        Sets the card in single mode readout status

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set the card in single mode readout status')
        self._set_param(_spcm_regs.SPC_CARDMODE, _spcm_regs.SPC_REC_STD_SINGLE)

    def trigger_mode_pos(self):
        '''
        Sets the trigger mode of ext0
        to positive slope

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set trigger mode pos')
        self._set_param(_spcm_regs.SPC_TRIG_EXT0_MODE, _spcm_regs.SPC_TM_POS)

    def trigger_mode_neg(self):
        '''
        Sets the trigger mode of ext0
        to negative slope

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set trigger mode neg')
        self._set_param(_spcm_regs.SPC_TRIG_EXT0_MODE, _spcm_regs.SPC_TM_NEG)

    def set_trigger_ORmask_tmask_ext0(self):
        '''
        Set trigger OR mask tmask ext0

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set trigger OR mask tmask ext0')
        self._set_param(_spcm_regs.SPC_TRIG_ORMASK, _spcm_regs.SPC_TMASK_EXT0)

    def set_trigger_ORmask_tmask_NO_ch0(self):
        '''
        Set trigger OR mask tmask No ch 0

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set trigger OR mask tmask No ch 0')
        self._set_param(_spcm_regs.SPC_TRIG_CH_ORMASK0, 0)

    def set_trigger_ORmask_tmask_NO_ch1(self):
        '''
        Set trigger OR mask tmask No ch 1

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set trigger OR mask tmask No ch 1')
        self._set_param(_spcm_regs.SPC_TRIG_CH_ORMASK1, 0)

    def trigger_termination_50Ohm(self):
        '''
        Sets the trigger input termination
        to 50 Ohm

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set trigger termination to 50 Ohm')
        self._set_param(_spcm_regs.SPC_TRIG_TERM, 1)

    def trigger_termination_highOhm(self):
        '''
        Sets the trigger input termination
        to high impedance

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set trigger termination to high impedance')
        self._set_param(_spcm_regs.SPC_TRIG_TERM, 0)

    def readout_singlemode_bin(self):
        '''
        Reads out the buffer, and returns a list with the size of the
        buffer. Contains only data if the channel is triggered.

        Input:
            None

        Output:
            data (int[memsize]): The data of the buffer
        '''
        logging.debug(__name__ + ' : Readout binaries from buffer')
        lMemsize = self.get_memsize()

        a = (c_int8 * lMemsize)()
        p_data = pointer(a)

        err = self._spcm_win32.DefTransfer64(self._spcm_win32.handel, _spcm_regs.SPCM_BUF_DATA, 1,
            0, p_data, c_int64(0), c_int64(lMemsize))
        err = self._spcm_win32.SetParam32(self._spcm_win32.handel, _spcm_regs.SPC_M2CMD,
            _spcm_regs.M2CMD_DATA_STARTDMA)
        return p_data.contents[:]

    def readout_singlemode_float(self):
        '''
        Reads out the buffer, and converts the data to the actual input voltage.
        Returns a list with the size of the buffer.
        Contains only data if the channel is triggered.

        Input:
            None

        Output:
            dataout (float[memsize]): The data of the buffer
        '''
        logging.debug(__name__ + ' : Readout float after converting from binaries')
        amp = float(self.get_input_amp_ch0())
        offset = float(self.get_input_offset_ch0())
        datain = self.readout_singlemode_bin()
        dataout = []
        datain = numpy.array(datain, numpy.float32)
        dataout = 2.0 * amp * (datain / 255.0) + offset
        return dataout

    def test(self, memsize=2048, posttrigger=1024, amp=500):
        '''
        Reads out the buffer, and returns a list with the size of the
        buffer. Contains only data if the channel is triggered.

        Input:
            memsize (int)       : number of datapoints taken
                                    default = 2048
            posttrigger (int)   : numbers of points taken after the trigger
                                    default = 1024
            amp (int)           : half of the range in millivolts
                                    default = 500

        Output:
            data (int[memsize]): Measurement data
        '''
        self.init_default(memsize=memsize, posttrigger=posttrigger, amp=amp)
        print 'starting card and waiting for trigger'
        self.start_with_trigger_and_waitready()
        print "received trigger"
        self.data = self.readout_singlemode_float()
        return self.data
