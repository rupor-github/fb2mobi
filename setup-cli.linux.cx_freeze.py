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
    (os.path.join(base_dir, 'default_cover.jpg'), 'default_cover.jpg'),
    (os.path.join(base_dir, 'spaces.xsl'), 'spaces.xsl'),
    (os.path.join(base_dir, 'kindlegen'), 'kindlegen'),
    (os.path.join(PIL.__path__[0], '.libs'), 'lib/.libs'),
]

setup(
    name = "fb2mobi",
    version = version.VERSION,
    options={
        'build_exe': {
            'zip_exclude_packages': '',
            'zip_include_packages': '*',
            'packages': 'json,lxml,PIL',
            'include_files': data_files,
            'includes': includes,
            'excludes': excludes,
            'replace_paths': [('*','library.zip/')],
        }
    },
    executables = [
        Executable('fb2mobi.py'),
        Executable('synccovers.py')
    ]
)
