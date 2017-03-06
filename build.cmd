REM cssutils lxml py2exe pyqt pyhyphen

setlocal

set PYTHON_VER=3.6.0
set PYTHON_DIR=d:\python

%PYTHON_DIR%\python%PYTHON_VER%_x64\python.exe setup-all.win32.cx_freeze.py
call release.cmd x64

%PYTHON_DIR%\python%PYTHON_VER%_x86\python.exe setup-all.win32.cx_freeze.py
call release.cmd x86

endlocal

:FIN