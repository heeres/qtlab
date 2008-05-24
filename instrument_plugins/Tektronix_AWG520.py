from instrument import Instrument
import visa
import types
import logging
import numpy
import struct



class AWG520(Instrument):
    '''
    todo:
    trigger mode     AWGC:RMOD TRIG/CONT
    trigger level    TRIG:LEV %.3f
    trigger impedance     TRIG:IMP 1e3 / 50
    waveform to file
    send file
    send waveform (needs to create file out of existing waveforms?) then call send file

     think about:    clock, waveform length
    '''

    def __init__(self, name, address, reset=False):
        Instrument.__init__(self, name)
        
        self._address = address        
        self._visainstrument = visa.instrument(self._address)

    def reset(self):
        self._visainstrument.write('*RST')
        
    def send_waveform(self,w,m1,m2,filename,clock):
        m = m1 + numpy.multiply(m2,2)
        ws = ''
        for i in range(0,len(w)):
            ws = ws + struct.pack('<fB',w[i],m[i])
        
        s1 = 'MMEM:DATA "%s",' % filename
        s3 = 'MAGIC 1000\n'
        s5 = ws
        s6 = 'CLOCK %.10e\n' % clock
        
        s4 = '#4' + str(len(s5))
        s2 = '#4' + str(len(s6) + len(s5) + len(s4) + len(s3))
            
        mes = s1 + s2 + s3 + s4 + s5 + s6
        
        self._visainstrument.write(mes)
        
    def ch1_set_filename(self,name):
        self._visainstrument.write('SOUR1:FUNC:USER "%s","MAIN"' % name)
        
    def ch1_set_amp(self,amp):
        self._visainstrument.write('SOUR:VOLT:LEV:IMM:AMPL %.6f' % amp)
        
    def ch1_set_off(self,off):
        self._visainstrument.write('SOUR:VOLT:LEV:IMM:OFFS %.6f' % off)
        
    def ch1_set_marker1_low(self,low):
        self._visainstrument.write('SOUR:MARK1:VOLT:LEV:IMM:LOW %.3f' % low)
        
    def ch1_set_marker1_high(self,high):
        self._visainstrument.write('SOUR:MARK1:VOLT:LEV:IMM:HIGH %.3f' % high)
        
    def ch1_set_marker2_low(self,low):
        self._visainstrument.write('SOUR:MARK2:VOLT:LEV:IMM:LOW %.3f' % low)
        
    def ch1_set_marker2_high(self,high):
        self._visainstrument.write('SOUR:MARK2:VOLT:LEV:IMM:HIGH %.3f' % high)
        


