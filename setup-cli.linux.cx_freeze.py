from cx_Freeze import setup, Executable

import sys
import os
import shutil
import version
import PIL, glob

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
    'PIL._imaging',
    'modules.default_css'
]

excludes = [
    'PyQt5', 
    'pywin',
    'Tkconstants',
    'Tkinter',
    'tcl'
]

data_files = [
    (os.path.join(base_dir, 'modules', 'dictionaries'), 'dictionaries'),
    (os.path.join(base_dir, 'profiles'), 'profiles'),
    (os.path.join(base_dir, 'fb2mobi.config'), 'fb2mobi.config'),
    (os.path.join(base_dir, 'spaces.xsl'), 'spaces.xsl'),
    (os.path.join(base_dir, 'kindlegen'), 'kindlegen'),
    (os.path.join(PIL.__path__[0], '.libs'), 'lib/python3.6/.libs'),
#    (os.path.join(base_dir, 'ui/locale/qtbase_ru.qm'), 'ui/locale/qtbase_ru.qm'),
#    (os.path.join(base_dir, 'ui/locale/fb2mobi_ru.qm'), 'ui/locale/fb2mobi_ru.qm')
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
            'packages': 'json,lxml,PIL',
            'include_files': data_files,
            'includes': includes,
            'excludes': excludes,
        }
    },
    executables = [
        Executable('fb2mobi.py'),
        Executable('synccovers.py')
    ]
)
