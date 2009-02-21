:: qtlab.bat
:: Runs QTlab on Windows
::
:: QTlab needs some programs to exist in the system PATH. They can be
:: defined globally in "configuration_panel => system => advanced =>
:: system_variables", or on the commandline just before execution of
:: QTlab.
::
::SET PATH=%CD%\3rd_party\gtk\bin;%CD%\3rd_party\gtk\lib;%PATH%
::SET GTK_BASEPATH=%CD%\3rd_party\gtk
::
::SET PATH=%CD%\3rd_party\gnuplot\binaries;%PATH%
::
::SET PATH=%CD%\3rd_party\Console2\;%PATH%

start Console -w "QTLab" -r "/k c:\python25\python c:\python25\scripts\ipython.py -gthread -p sh source/qtlab_client_shell.py"
exit
