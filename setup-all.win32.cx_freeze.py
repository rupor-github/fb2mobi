from cx_Freeze import setup, Executable

import sys
import os
import shutil
import version
import site

base_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
sys.argv.append('build_exe')

try:
    shutil.rmtree(os.path.join(base_dir, 'build'))
except:
    pass

try:
    shutil.rmtree(os.path.join(base_dir, 'dist'))
except:
    pass

includes = [
    'lxml._elementpath',
    'modules.default_css',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets'
]

excludes = [
    'pywin',
    'Tkconstants',
    'Tkinter',
    'tcl'
]

data_files = [
    (os.path.join(base_dir, 'modules', 'dictionaries'), 'dictionaries'),
    (os.path.join(base_dir, 'profiles'), 'profiles'),
    (os.path.join(base_dir, 'fb2mobi.config'), 'fb2mobi.config'),
    (os.path.join(base_dir, 'fb2epub.config'), 'fb2epub.config'),
    (os.path.join(base_dir, 'spaces.xsl'), 'spaces.xsl'),
    (os.path.join(base_dir, 'kindlegen.exe'), 'kindlegen.exe'),
    (os.path.join(base_dir, 'ui/locale/qtbase_ru.qm'), 'ui/locale/qtbase_ru.qm'),
    (os.path.join(base_dir, 'ui/locale/fb2mobi_ru.qm'), 'ui/locale/fb2mobi_ru.qm'),
    (os.path.join(site.getsitepackages()[1], 'PyQt5/Qt/plugins/platforms/qwindows.dll'), "platforms/qwindows.dll")
]

setup(
    name = "fb2mobi",
    version = version.VERSION,
    options={
        'build_exe': {
#            'silent': 1,
#            'build_exe': 'dist',
            'zip_exclude_packages': '',
            'zip_include_packages': '*',
            'include_files': data_files,
            'includes': includes,
            'excludes': excludes,
        }
    },
    executables = [
        Executable('fb2mobi.py'),
        Executable('fb2mobi.py',targetName='fb2epub.exe'),
        Executable('synccovers.py'),
        Executable('fb2mobi-gui.py', base='Win32GUI', icon='ui/fb2mobi.ico')
    ]
)
