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

# Useful library. http://click.pocoo.org/5/api/#click.confirm
import click

from cx_Freeze import setup, Executable
from buildzipper import buildzipper

PYTHON_DIR = sys.exec_prefix
#path_platforms = os.path.join(PYTHON_DIR, 'Lib\site-packages\PyQt5\plugins\platforms\qwindows.dll')
path_sqlite_dll = os.path.join(PYTHON_DIR, 'DLLs\sqlite3.dll')

PYQT5_DIR = os.path.join(PYTHON_DIR, 'lib\site-packages\PyQt5')
includes = ['PyQt5.Qt', 'PyQt5.QtNetwork', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtMultimedia']

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
        ]
excludes = []
packages = ['os', 'apsw', 'peewee', 'playhouse', 'asyncio', 'logging', 'arrow',
            'fractions', 'dateutil', 'winsound', 'win32print', 'win32ui', 'serial']
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

# GUI applications require a different base on Windows (the default is for a console application).
base = None
exe = None
if sys.platform == 'win32':
    exe = Executable(
      script='../main_trawl_backdeck.py',
      initScript=None,
      # base='Console',  # useful for debugging
      base='Win32GUI',  # use this to hide console output (releases)
      targetName='trawl_backdeck.exe',
      icon='../resources/ico/trawl2.ico'
    )

# Prompt to nuke existing directory
deployed_path = r'build\exe.win64-3.6\trawl_backdeck'
if os.path.exists(deployed_path):
	shutil.rmtree(deployed_path)
	print('Deleted ' + deployed_path)

setup(  
      name='Trawl Back Deck',
      version='1.0',
      author='FRAM Data',
      description='Trawl Back Deck',
      options={'build_exe': build_exe_options},
      executables=[exe]
)

# Zip up our creation
buildzipper.create_zip_archive(base_folder=deployed_path, filedesc='trawl_backdeck',
                               folders_to_zip=['trawl_backdeck/trawl_backdeck.exe', 'trawl_backdeck/py',
                                               'trawl_backdeck/data/trawl_backdeck.db'])

