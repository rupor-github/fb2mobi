IF .%1. == .. GOTO ERR
set UI=_all
IF .%2. == .gui. set UI=_gui
IF .%2. == .cli. set UI=_cli

del fb2mobi%UI%_%1.7z >nul
cd dist
7z.exe a ..\fb2mobi%UI%_%1.7z
cd ..

goto FIN

:ERR

echo x86 or x64?

:FIN