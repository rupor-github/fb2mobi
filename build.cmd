REM cssutils lxml py2exe

setlocal

set PYTHON_VER=36
set PYTHON_DIR=d:\python

%PYTHON_DIR%\python%PYTHON_VER%\python.exe setup-cli.win32.cx_freeze.py
call release.cmd x64

%PYTHON_DIR%\python%PYTHON_VER%_32\python.exe setup-cli.win32.cx_freeze.py
call release.cmd x86

endlocal

:FIN