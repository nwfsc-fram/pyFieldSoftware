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

# Useful library. http://click.pocoo.org/5/api/#click.confirm
import click

from cx_Freeze import setup, Executable
from buildzipper import buildzipper

PYTHON_DIR = sys.exec_prefix
#path_platforms = os.path.join(PYTHON_DIR, 'Lib\site-packages\PyQt5\plugins\platforms\qwindows.dll')
path_sqlite_dll = os.path.join(PYTHON_DIR, 'DLLs\sqlite3.dll')

PYQT5_DIR = os.path.join(PYTHON_DIR, 'lib\site-packages\PyQt5')
includes = ['PyQt5.Qt', 'PyQt5.QtNetwork', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtMultimedia']

includefiles = [
#        path_platforms,
		path_sqlite_dll,
        ('../data/trawl_backdeck.db', 'data/trawl_backdeck.db'),  # explicit source, destination path
        ('../resources/', 'resources'),
        ('../py/ashop', 'py/ashop'),
        ('../py/common', 'py/common'),
		('../py/trawl', 'py/trawl'),
        ('../qml/ashop', 'qml/ashop'),
        ('../qml/common', 'qml/common'),
        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQuick.2'), 'QtQuick.2'),
        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQuick'), 'QtQuick'),
        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQml'), 'QtQml'),
        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQml'), ''),
        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtGraphicalEffects'), 'QtGraphicalEffects'),
		(os.path.join(PYQT5_DIR, 'Qt', 'qml', 'Qt'), 'Qt'),		
        ]
excludes = []
packages = ['os', 'apsw', 'peewee', 'playhouse',
            'fractions', 'dateutil', 'winsound', 'win32print', 'win32ui', 'serial']
path = []

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
                     'includes':      includes, 
                     'include_files': includefiles,
                     'excludes':      excludes, 
                     'packages':      packages, 
                     'path':          path,
                     'build_exe':     'build/exe.win64-3.6/ashop'
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
exe = None
if sys.platform == 'win32':
    exe = Executable(
      script='../main_ashop.py',
      initScript=None,
      # base='Console',  # useful for debugging
      base='Win32GUI',  # use this to hide console output (releases)
      targetName='productus.exe',
#      compress=True,
#      copyDependentFiles=True,
#      appendScriptToExe=False,
#      appendScriptToLibrary=False,
      icon='../resources/ico/trawl2.ico'
    )

# Prompt to nuke existing directory
deployed_path = 'build\exe.win64-3.6\ashop'
if os.path.exists(deployed_path):
    if click.confirm('Path ' + deployed_path + ' exists. Delete?', default=True):
        shutil.rmtree(deployed_path)
        print('Deleted ' + deployed_path)

setup(  
      name='ASHOP Productus',
      version='0.1',
      author='FRAM Data',
      description='ASHOP Productus',
      options={'build_exe': build_exe_options},
      executables=[exe]
)

# Zip up our creation
buildzipper.create_zip_archive(base_folder=deployed_path, filedesc='ashop')
