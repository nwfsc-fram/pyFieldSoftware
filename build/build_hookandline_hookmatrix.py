# cx_freeze build script
# Written with cx-Freeze==4.3.4

# Outputs by default to build\exe.win32-3.5\
# Note: will NOT delete anything in that directory
# Modify path_platforms as required

# Usage:
# build_hookandline_fpc.py build


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
QRC_PATH = str(Path(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../qrc/hookandline_hookmatrix.qrc')).resolve())
QRCPY_PATH = str(Path(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../py/hookandline_hookmatrix/hookandline_hookmatrix_qrc.py')).resolve())
print('\npyrcc: ' + PYRCC_DIR + '\nqrc: ' + QRC_PATH + '\nqrcpy: ' + QRCPY_PATH + '\n')
subprocess.check_output([PYRCC_DIR, QRC_PATH, '-o', QRCPY_PATH])

includefiles = [
		path_sqlite_dll,  # for some reason this went away in cx_freeze 5.0		
        ('../data/hookandline_hookmatrix.db', 'data/hookandline_hookmatrix.db'),  # explicit source, destination path
        ('../resources/', 'resources'),
        ('../py/hookandline_hookmatrix', 'py/hookandline_hookmatrix'),
        ('../py/common', 'py/common'),
        ('../qml/hookandline_hookmatrix', 'qml/hookandline_hookmatrix'),
		('../qml/common', 'qml/common'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQuick.2'), 'QtQuick.2'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQuick'), 'QtQuick'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQml'), 'QtQml'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQml'), ''),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtGraphicalEffects'), 'QtGraphicalEffects'),
#		(os.path.join(PYQT5_DIR, 'Qt', 'qml', 'Qt'), 'Qt'),	
        ]
excludes = []
packages = ['os', 'apsw', 'peewee', 'serial', 'fractions', 'dateutil', 'playhouse', 'arrow',
            'asyncio', 'logging', 'pathlib', 'winsound']
path = []

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
                     'includes':      includes, 
                     'include_files': includefiles,
                     'excludes':      excludes, 
                     'packages':      packages, 
                     'path':          path,
                     'build_exe':     'build/exe.win64-3.6/HookMatrix'
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
exe = None
if sys.platform == 'win32':
    exe = Executable(
      script='../main_hookandline_hookmatrix.py',
      initScript=None,
      # base='Console',  # useful for debugging
      base='Win32GUI',  # use this to hide console output (releases)
      targetName='HookMatrix.exe',
      icon='../resources/ico/hooklogger.ico'
    )

# Prompt to nuke existing directory
deployed_path = 'build\exe.win64-3.6\HookMatrix'
if os.path.exists(deployed_path):
#    if click.confirm('Path ' + deployed_path + ' exists. Delete?', default=True):
	shutil.rmtree(deployed_path)
	print('Deleted ' + deployed_path)

setup(  
      name='Hook & Line HookMatrix',
      version='1.0',
      author='FRAM Data',
      description='Hook & Line HookMatrix',
      options={'build_exe': build_exe_options},
      executables=[exe]
)

# Zip up our creation
buildzipper.create_zip_archive(base_folder=deployed_path, filedesc='hookandline_hookmatrix')
