:: qtlabgui.bat
:: Runs QTlab GUI part on Windows

@ECHO OFF

:: Check if GTK is installed, if not assume GTK is in 3rd_party folder
IF DEFINED GTK_BASEPATH GOTO mark2
SET GTK_BASEPATH=%CD%\3rd_party\gtk
SET PATH=%CD%\3rd_party\gtk\bin;%CD%\3rd_party\gtk\lib;%PATH%
:mark2

:: Check for version of python
IF EXIST c:\python27\python.exe (
    SET PYTHON_PATH=c:\python27
    GOTO mark1
)
IF EXIST c:\python26\python.exe (
    SET PYTHON_PATH=c:\python26
    GOTO mark1
)
:mark1

:: Run QTlab GUI
start %PYTHON_PATH%\pythonw.exe source/gui/guiclient.py
