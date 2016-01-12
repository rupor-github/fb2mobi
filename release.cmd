IF .%1. == .. GOTO ERR

del fb2mobi_%1.7z >nul
cd dist
7z.exe a ..\fb2mobi_%1.7z fb2mobi.exe dictionaries
cd ..

7z.exe a fb2mobi_%1.7z fb2mobi.config spaces.xsl profiles

goto FIN

:ERR

echo x86 or x64?

:FIN