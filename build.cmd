REM cssutils lxml py2exe pyqt pyhyphen

setlocal

set PYTHON_VER=36
set PYTHON_DIR=d:\python

%PYTHON_DIR%\python%PYTHON_VER%\python.exe setup-cli.win32.cx_freeze.py
call release.cmd x64
%PYTHON_DIR%\python%PYTHON_VER%\python.exe setup-gui.win32.cx_freeze.py
call release.cmd x64 gui

%PYTHON_DIR%\python%PYTHON_VER%_32\python.exe setup-cli.win32.cx_freeze.py
call release.cmd x86
%PYTHON_DIR%\python%PYTHON_VER%_32\python.exe setup-gui.win32.cx_freeze.py
call release.cmd x86 gui

endlocal

:FIN