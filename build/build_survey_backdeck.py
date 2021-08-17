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
from build_config import increment_build_number

PYTHON_DIR = sys.exec_prefix
#path_platforms = os.path.join(PYTHON_DIR, 'Lib\site-packages\PyQt5\plugins\platforms\qwindows.dll')
path_sqlite_dll = os.path.join(PYTHON_DIR, 'DLLs\sqlite3.dll')

PYQT5_DIR = os.path.join(PYTHON_DIR, 'lib\site-packages\PyQt5')
includes = ['PyQt5.Qt', 'PyQt5.QtNetwork', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtMultimedia']

# Compile the QML into the qrc.py file
PYRCC_DIR = os.path.join(PYTHON_DIR, 'Scripts\pyrcc5.exe')
QRC_PATH = str(Path(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../qrc/survey_backdeck.qrc')).resolve())
QRCPY_PATH = str(Path(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../py/survey_backdeck/survey_backdeck_qrc.py')).resolve())
print('\npyrcc: ' + PYRCC_DIR + '\nqrc: ' + QRC_PATH + '\nqrcpy: ' + QRCPY_PATH + '\n')
subprocess.check_output([PYRCC_DIR, QRC_PATH, '-o', QRCPY_PATH])

# increment build number
version = increment_build_number('../py/survey_backdeck/CutterConfig.py', 'CUTTER_VERSION')

includefiles = [
#        path_platforms,
		path_sqlite_dll,
        ('../data/hookandline_cutter.db', 'data/hookandline_cutter.db'),  # explicit source, destination path
        ('../resources/', 'resources'),
        ('../py/survey_backdeck', 'py/survey_backdeck'),
        ('../py/common', 'py/common'),
        ('../qml/survey_backdeck', 'qml/survey_backdeck'),
        ('../qml/common', 'qml/common'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQuick.2'), 'QtQuick.2'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQuick'), 'QtQuick'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQml'), 'QtQml'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQml'), ''),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtGraphicalEffects'), 'QtGraphicalEffects'),
#		(os.path.join(PYQT5_DIR, 'Qt', 'qml', 'Qt'), 'Qt'),		
        ]
excludes = []
packages = ['os', 'apsw', 'peewee', 'playhouse', 'asyncio', 'logging',
            'fractions', 'dateutil', 'winsound', 'win32print', 'win32ui', 'serial', 'pathlib']
path = []

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
                     'includes':      includes, 
                     'include_files': includefiles,
                     'excludes':      excludes, 
                     'packages':      packages, 
                     'path':          path,
                     'build_exe':     'build/exe.win64-3.6/CutterStation'
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
exe = None
if sys.platform == 'win32':
    exe = Executable(
      script='../main_survey_backdeck.py',
      initScript=None,
      # base='Console',  # useful for debugging
      base='Win32GUI',  # use this to hide console output (releases)
      targetName='CutterStation.exe',
#      compress=True,
#      copyDependentFiles=True,
#      appendScriptToExe=False,
#      appendScriptToLibrary=False,
      icon='../resources/ico/trawl2.ico'
    )

# Prompt to nuke existing directory
deployed_path = 'build\exe.win64-3.6\CutterStation'
if os.path.exists(deployed_path):
#    if click.confirm('Path ' + deployed_path + ' exists. Delete?', default=True):
        shutil.rmtree(deployed_path)
        print('Deleted ' + deployed_path)

setup(  
      name='Cutter Station',
      version='0.1',
      author='FRAM Data',
      description='Survey Backdeck',
      options={'build_exe': build_exe_options},
      executables=[exe]
)

# Zip up our creation
buildzipper.create_zip_archive(base_folder=deployed_path, filedesc=f'CutterStation_{version}')
