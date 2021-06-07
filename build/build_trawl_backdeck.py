# cx_freeze build script
# Written with cx-Freeze==4.3.4

# Outputs by default to build\exe.win64-3.6\
# Note: will NOT delete anything in that directory
# Modify path_platforms as required

# Usage:
# build_trawl_backdeck.py build


import sys
import os
import shutil
import subprocess
from pathlib import Path
import fileinput  # for updating build number in-place
import re

# Useful library. http://click.pocoo.org/5/api/#click.confirm
import click

from cx_Freeze import setup, Executable
from buildzipper import buildzipper
from py.trawl.TrawlBackdeckConfig import TRAWL_BACKDECK_VERSION

def increment_build_number(do_increment=True) -> str:
    """
    Increment build number (function copied from Optecs.build_observer.py)
    @param do_increment: perform increment. For testing, can set this to False
    @return: Full TrawlBackdeck String version string
    """
    build_config_path = '../py/trawl/TrawlBackdeckConfig.py'
    if not os.path.exists(build_config_path):
        print('*** Unable to increment build #.')
        return
    version_info = None
    for i, line in enumerate(fileinput.input(build_config_path, inplace=1)):
        m = re.search(r'TRAWL_BACKDECK_VERSION = \"[0-9]*\.[0-9]*\.[0-9]*\+(?P<build_num>[0-9]*)', line)
        if m:
            old_build_num = int(m.group('build_num'))
            if do_increment:
                line = line.replace('+' + str(old_build_num), '+' + str(old_build_num + 1))
            m = re.search(r'TRAWL_BACKDECK_VERSION = \"(?P<TRAWL_BACKDECK_VERSION>[0-9]*\.[0-9]*\.[0-9]*\+[0-9]*)', line)
            version_info = m.group('TRAWL_BACKDECK_VERSION')
        sys.stdout.write(line)

    return version_info


PYTHON_DIR = sys.exec_prefix

#path_platforms = os.path.join(PYTHON_DIR, 'Lib\site-packages\PyQt5\plugins\platforms\qwindows.dll')
path_sqlite_dll = os.path.join(PYTHON_DIR, 'Scripts\sqlite3.dll')

PYQT5_DIR = os.path.join(PYTHON_DIR, 'lib\site-packages\PyQt5')
includes = ['PyQt5.Qt', 'PyQt5.QtNetwork', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtMultimedia']

ROOT_PYTHON_DIR = 'C:\\Python36'
os.environ["TCL_LIBRARY"] = os.path.join(ROOT_PYTHON_DIR, "tcl", "tcl8.6")
os.environ["TK_LIBRARY"] = os.path.join(ROOT_PYTHON_DIR, "tcl", "tk8.6")

# Compile the QML into the qrc.py file
PYRCC_DIR = os.path.join(PYTHON_DIR, 'Scripts\pyrcc5.exe')
QRC_PATH = str(Path(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../qrc/trawl_backdeck.qrc')).resolve())
QRCPY_PATH = str(Path(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../py/trawl/trawl_backdeck_qrc.py')).resolve())
print('\npyrcc: ' + PYRCC_DIR + '\nqrc: ' + QRC_PATH + '\nqrcpy: ' + QRCPY_PATH + '\n')
subprocess.check_output([PYRCC_DIR, QRC_PATH, '-o', QRCPY_PATH])

includefiles = [
#        path_platforms,
		path_sqlite_dll,
        ('../data/trawl_backdeck.db', 'data/trawl_backdeck.db'),  # explicit source, destination path
        ('../resources/', 'resources'),
        ('../py/trawl', 'py/trawl'),
        ('../py/common', 'py/common'),
        ('../qml/trawl', 'qml/trawl'),
        ('../qml/common', 'qml/common'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQuick.2'), 'QtQuick.2'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQuick'), 'QtQuick'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQml'), 'QtQml'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQml'), ''),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtGraphicalEffects'), 'QtGraphicalEffects'),
#		(os.path.join(PYQT5_DIR, 'Qt', 'qml', 'Qt'), 'Qt'),
    (os.path.join(PYTHON_DIR, 'Scripts', 'tcl86t.dll'), 'tcl86t.dll'),
    (os.path.join(PYTHON_DIR, 'Scripts', 'tk86t.dll'), 'tk86t.dll')
        ]
excludes = []
packages = ['os', 'apsw', 'peewee', 'playhouse', 'asyncio', 'logging', 'arrow',
            'fractions', 'dateutil', 'winsound', 'win32print', 'win32ui', 'serial', 'unittest']
path = []

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
                     'includes':      includes, 
                     'include_files': includefiles,
                     'excludes':      excludes, 
                     'packages':      packages, 
                     'path':          path,
                     'build_exe':     'build/exe.win64-3.6/trawl_backdeck'
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
exe = None
if sys.platform == 'win32':
    exe = Executable(
      script='../main_trawl_backdeck.py',
      initScript=None,
      # base='Console',  # useful for debugging
      base='Win32GUI',  # use this to hide console output (releases)
      targetName='trawl_backdeck.exe',
#      compress=True,
#      copyDependentFiles=True,
#      appendScriptToExe=False,
#      appendScriptToLibrary=False,
      icon='../resources/ico/trawl2.ico'
    )

# Prompt to nuke existing directory
deployed_path = r'build\exe.win64-3.6\trawl_backdeck'
if os.path.exists(deployed_path):
#    if click.confirm('Path ' + deployed_path + ' exists. Delete?', default=True):
	shutil.rmtree(deployed_path)
	print('Deleted ' + deployed_path)

setup(  
      name='Trawl Back Deck',
      version='1.0',  # Leaving as is to make build happy
      author='FRAM Data',
      description='Trawl Back Deck',
      options={'build_exe': build_exe_options},
      executables=[exe]
)

# Zip up our creation
buildzipper.create_zip_archive(base_folder=deployed_path, filedesc=f'trawl_backdeck', version=TRAWL_BACKDECK_VERSION)
increment_build_number()  # increment variable on TrawlBackdeckConfig.py every build
