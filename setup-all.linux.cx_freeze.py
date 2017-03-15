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
    'modules.default_css'
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
    (os.path.join(base_dir, 'spaces.xsl'), 'spaces.xsl'),
    (os.path.join(base_dir, 'kindlegen'), 'kindlegen'),
    (os.path.join(base_dir, 'ui/locale/qtbase_ru.qm'), 'ui/locale/qtbase_ru.qm'),
    (os.path.join(base_dir, 'ui/locale/fb2mobi_ru.qm'), 'ui/locale/fb2mobi_ru.qm')
]

pil_libs = glob.glob(os.path.join(PIL.__path__[0], '.libs/*'))
if len(pil_libs) > 0:
    data_files = pil_libs + data_files

qt5_libs = glob.glob(os.path.join("/usr/lib/", 'libQt5*.so.5.8.0'))
if len(qt5_libs) > 0:
    data_files = qt5_libs + data_files

icu_libs = glob.glob(os.path.join("/usr/lib/", 'libicu*.so.58.2'))
if len(icu_libs) > 0:
    data_files = icu_libs + data_files

setup(
    name = "fb2mobi",
    version = version.VERSION,
    options={
        'build_exe': {
#            'silent': 1,
            'build_exe': 'dist',
            'zip_exclude_packages': '',
            'zip_include_packages': '*',
            'packages': 'lxml,PIL,PyQt5',
            'include_files': data_files,
            'includes': includes,
            'excludes': excludes,
        }
    },
    executables = [
        Executable('fb2mobi-gui.py'),
        Executable('fb2mobi.py'),
        Executable('synccovers.py')
    ]
)
