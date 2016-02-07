IF .%1. == .. GOTO ERR

del fb2mobi_%1.7z >nul
cd dist
7z.exe a ..\fb2mobi_%1.7z 
cd ..

goto FIN

:ERR

echo x86 or x64?

:FIN