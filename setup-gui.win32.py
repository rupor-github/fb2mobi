from distutils.core import setup
import py2exe
import sys
import os
import shutil

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


manifest = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="fb2mobi-gui.py"
    type="win32"
  />
  <description>fb2mobi-gui.py</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel
            level="asInvoker"
            uiAccess="false">
        </requestedExecutionLevel>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
            type="win32"
            name="Microsoft.VC90.CRT"
            version="9.0.21022.8"
            processorArchitecture="x86"
            publicKeyToken="1fc8b3b9a1e18e3b">
      </assemblyIdentity>
    </dependentAssembly>
  </dependency>
  <dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
  </dependency>
</assembly>
'''

includes = [
    'lxml.etree', 
    'lxml._elementpath', 
    'gzip', 
    'hyphenations.ru', 
    'hyphenations.en',
    'hyphenations.uk',
    'hyphenations.de',  
    'default_css',
    'email',
    'email.mime.base',
    'email.mime.multipart',
    'email.mime.text',
    'wx.lib.pubsub.*',
    'wx.lib.pubsub.core.*',
    'wx.lib.pubsub.core.kwargs.*'
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
    name='fb2conv-gui',
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
    windows=[
        {
            'script': 'fb2conv-gui.py',
            'icon_resources': [(0, 'images/fb2conv.ico')],
            'other_resources': [(24, 1, manifest)]
        }
    ]
    ,
    zipfile=None
)



