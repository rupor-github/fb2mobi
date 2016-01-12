from distutils.core import setup
from glob import glob

import py2exe
import sys
import os

base_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.join(base_dir, 'modules'))

sys.argv.append('py2exe')

try:
    shutil.rmtree(os.path.join(base_dir, 'build'))
except:
    pass
try:
    shutil.rmtree(os.path.join(base_dir, 'dist'))
except:
    pass

includes = [
    'lxml.etree', 
    'lxml._elementpath', 
    'gzip',
    'pyphen',
    'default_css'
]

dll_excludes = [
    'w9xpopen.exe'
]

excludes = [
    'pywin', 
    'pywin.debugger', 
    'pywin.debugger.dbgcon',
    'pywin.dialogs', 
    'pywin.dialogs.list', 
    'Tkconstants',
    'Tkinter',
    'tcl'
]

setup(
    data_files = [("dictionaries", glob(os.path.join(base_dir, 'modules', 'dictionaries', '*.dic')))],
    options = {
        'py2exe': {
            'compressed': 1,
            'optimize': 2,
            'bundle_files': 1,
            'includes': includes,
            'excludes': excludes,
            'dll_excludes': dll_excludes
        }
    },
    console=['fb2mobi.py'],
    zipfile=None
)

