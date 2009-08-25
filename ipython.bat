:: ipython.bat
:: Runs IPython like in qtlab.bat, without actually starting QTLab.
::
:: Useful for testing and debugging.

::SET PATH=%CD%\3rd_party\Console2\;%PATH%

start Console -w "IPython" -r "/k c:\python26\python c:\python26\scripts\ipython.py -p sh"
exit
