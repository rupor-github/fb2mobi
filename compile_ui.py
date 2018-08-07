from glob import glob
from subprocess import call
import os

SRCPATH = 'ui'
DESTPATH = 'ui'

def compile_ui():
    for uifile in glob(os.path.join(SRCPATH, '*.ui')):
        pyfile = os.path.join(DESTPATH, os.path.splitext(os.path.split(uifile)[1])[0] + '.py')
        uifile = os.path.normpath(uifile)
        pyfile = os.path.normpath(pyfile)
        call('pyuic5 --from-imports {} -o {}'.format(uifile, pyfile), shell=True)

def compile_rc():
    for uifile in glob(os.path.join(SRCPATH, '*.qrc')):
        pyfile = os.path.join(DESTPATH, os.path.splitext(os.path.split(uifile)[1])[0] + '_rc.py')
        uifile = os.path.normpath(uifile)
        pyfile = os.path.normpath(pyfile)
        call('pyrcc5 {} -o {}'.format(uifile, pyfile), shell=True)

def compile_pro():
    for pro_file in glob(os.path.join('.', '*.pro')):
        call('pylupdate5 {}'.format(pro_file), shell=True)



if __name__ == '__main__':
    compile_ui()
    compile_rc()
    compile_pro()
