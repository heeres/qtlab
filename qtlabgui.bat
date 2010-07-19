:: qtlabgui.bat
:: Runs QTlab GUI part on Windows
::
:: QTlab needs some programs to exist in the system PATH. They can be
:: defined globally in "configuration_panel => system => advanced =>
:: system_variables", or on the commandline just before execution of
:: QTlab.

SET PATH=%CD%\3rd_party\gtk\bin;%CD%\3rd_party\gtk\lib;%PATH%
SET GTK_BASEPATH=%CD%\3rd_party\gtk

SET PATH=%CD%\3rd_party\gnuplot\bin;%PATH%

SET PATH=%CD%\3rd_party\Console2\;%PATH%

start Console -w "QTLab GUI" -r "/k c:\python26\python c:\python26\scripts\ipython.py -gthread -p sh source/gui/guiclient.py"
:: start c:\python26\python source/gui/guiclient.py
exit
