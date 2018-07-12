from cx_Freeze import setup, Executable

import sys
import os
import shutil
import version
import site

base_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
sys.argv.append('bdist_mac')
# sys.argv.append('--qt-menu-nib=/opt/local/libexec/qt5/plugins/')

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
    'PyQt5.QtWidgets',
    'httplib2.socks',
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
    (os.path.join(base_dir, 'default_cover.jpg'), 'default_cover.jpg'),
    (os.path.join(base_dir, 'kindlegen'), 'kindlegen'),
    (os.path.join(base_dir, 'ui/locale/qtbase_ru.qm'), 'ui/locale/qtbase_ru.qm'),
    (os.path.join(base_dir, 'ui/locale/fb2mobi_ru.qm'), 'ui/locale/fb2mobi_ru.qm'),
    (os.path.join(base_dir, 'client_secret.json'), 'client_secret.json'),
    (os.path.join(base_dir, 'cacerts.txt'), 'cacerts.txt'),
]

plist = os.path.join(base_dir, 'ui/Info.plist')

setup(
    name = "fb2mobi-gui",
    version = version.VERSION,
    options={
        'build_exe': {
           # 'silent': 1,
            #'build_exe': 'dist',
            'zip_exclude_packages': '',
            'zip_include_packages': '*',
            'include_files': data_files,
            'includes': includes,
            'excludes': excludes,
        },
        'bdist_mac': {
            'iconfile': 'ui/fb2mobi.icns',
            'custom_info_plist': plist,
            'bundle_name': 'fb2mobi',
            'qt_menu_nib': '/opt/local/libexec/qt5/plugins/'
        }
    },
    executables = [
        Executable('fb2mobi-gui.py'),
        Executable('fb2mobi.py'),
        Executable('synccovers.py')

    ]
)

if os.path.isdir(os.path.join(base_dir, 'build/fb2mobi.app')):
    if not os.path.isdir(os.path.join(base_dir, 'build/CLI')):
        shutil.copytree(os.path.join(base_dir, 'mac_CLI'), os.path.join(base_dir, 'build/CLI'))

