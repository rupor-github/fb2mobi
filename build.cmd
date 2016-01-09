REM cssutils 1.0.1
REM lxml 3.4.4 
REM py2exe 0.9.2.2

setlocal

set PYTHON_VER=34
set PYTHON_DIR=d:\python

%PYTHON_DIR%\python%PYTHON_VER%\python.exe setup-cli.win32.py
call release.cmd x64

REM %PYTHON_DIR%\python%PYTHON_VER%_32\python.exe setup-cli.win32.py
REM call release.cmd x86

endlocal

:FIN