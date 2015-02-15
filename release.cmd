IF .%1. == .. GOTO ERR

del fb2mobi_%1.7z >nul
copy dist\fb2mobi.exe .
7z.exe a fb2mobi_%1.7z fb2mobi.exe fb2mobi.config profiles
del fb2mobi.exe

goto FIN

:ERR

echo x86 or x64?

:FIN