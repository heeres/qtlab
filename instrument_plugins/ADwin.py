#!/usr/bin/python

from instrument import Instrument
import _ADwin.ADwin as _ADwin
import logging

class ADwin(Instrument):

    def __init__(self, name, process):
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._ADwin = _ADwin
        self._DEVICENUMBER = 1
        self._BTL = 'c:\\adwin\\adwin9.btl'
        self._PROCESS = process

        self._ADwin.Set_DeviceNo(self._DEVICENUMBER)
        self._ADwin.Boot(self._BTL)
        if (self.checkError('boot') > 0):
            pass
        self._ADwin.Load_Process(self._PROCESS)
        if (self.checkError('load_process') > 0):
            pass

        self.add_function('start')

    def checkError(self, s='<unspecified>'):
        err = self._ADwin.Get_Last_Error()
        if err:
            print "*** " + s + ": " + self._ADwin.Get_Last_Error_Text(err)
            return err
        return 0

    def start(self):
        self._ADwin.Start_Process(1)


