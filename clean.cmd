rd /S /Q build
rd /S /Q dist
del *.pyc
del *.log
del *.fb2
del *.zip
del *.mobi
del *.epub
del *.azw3
del modules\*.pyc
del modules\hyphenations\*.pyc

for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s/q "%%d"
