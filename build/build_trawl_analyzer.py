# cx_freeze build script
# Written with cx-Freeze==4.3.4

# Outputs by default to build\exe.win32-3.4\
# Note: will NOT delete anything in that directory
# Modify path_platforms as required

# Usage:
# build_trawl_analyzer.py build

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
path_sqlite_dll = os.path.join(PYTHON_DIR, 'Scripts\sqlite3.dll')

PYQT5_DIR = os.path.join(PYTHON_DIR, 'lib\site-packages\PyQt5')
includes = ['PyQt5.Qt', 'PyQt5.QtNetwork', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtMultimedia', 'PyQt5.QtChart']

os.environ["TCL_LIBRARY"] = os.path.join(PYTHON_DIR, "lib", "tcl8.6")
os.environ["TK_LIBRARY"] = os.path.join(PYTHON_DIR, "lib", "tk8.6")

# Compile the QML into the qrc.py file
PYRCC_DIR = os.path.join(PYTHON_DIR, 'Scripts\pyrcc5.exe')
QRC_PATH = str(Path(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../qrc/trawl_analyzer.qrc')).resolve())
QRCPY_PATH = str(Path(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../py/trawl/trawl_analyzer_qrc.py')).resolve())
print('\npyrcc: ' + PYRCC_DIR + '\nqrc: ' + QRC_PATH + '\nqrcpy: ' + QRCPY_PATH + '\n')
subprocess.check_output([PYRCC_DIR, QRC_PATH, '-o', QRCPY_PATH])

"""

Note for SCIPY.  Had to modify the cx_freeze hooks.py file from (Lib\site-packages\cx_Freeze\hooks.py):

finder.IncludePackage("scipy.lib")

to

finder.IncludePackage("scipy._lib")

also added scipy to the list of packages to include, but dropped it from the includefiles
"""



includefiles = [
#        path_platforms,
		path_sqlite_dll,
        ('../data/trawl_analyzer.db', 'data/trawl_analyzer.db'),  # explicit source, destination path
        ('../resources/', 'resources'),
		('../py/trawl_analyzer', 'py/trawl_analyzer'),
        ('../py/common', 'py/common'),
        ('../qml/trawl_analyzer', 'qml/trawl_analyzer'),
		('../qml/common', 'qml/common'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQuick.2'), 'QtQuick.2'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQuick'), 'QtQuick'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQml'), 'QtQml'),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtQml'), ''),
#        (os.path.join(PYQT5_DIR, 'Qt', 'qml', 'QtGraphicalEffects'), 'QtGraphicalEffects'),
#		(os.path.join(PYQT5_DIR, 'Qt', 'qml', 'Qt'), 'Qt'),
#		(os.path.join(PYTHON_DIR, 'Lib', 'site-packages', 'scipy'), 'scipy'),
		(os.path.join(PYTHON_DIR, 'Scripts', 'tcl86t.dll'), 'tcl86t.dll'),
		(os.path.join(PYTHON_DIR, 'Scripts', 'tk86t.dll'), 'tk86t.dll')
        ]
excludes = []
packages = ['os', 'apsw', 'asyncio', 'peewee', 'playhouse', 'cProfile', 'timeit', 'numpy',
            'fractions', 'dateutil', 'winsound', 'serial', 'arrow', 'matplotlib', 
			'seaborn', 'pandas', 'tkinter', 'geographiclib']
path = []

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
                     'includes':      includes, 
                     'include_files': includefiles,
                     'excludes':      excludes, 
                     'packages':      packages, 
                     'path':          path,
                     'build_exe':     'build/exe.win64-3.6/trawl_analyzer'
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
exe = None
if sys.platform == 'win32':
    exe = Executable(
      script='../main_trawl_analyzer.py',
      initScript=None,
      # base='Console',  # useful for debugging
      base='Win32GUI',  # use this to hide console output (releases)
      targetName='trawl_analyzer.exe'
    )

# Prompt to nuke existing directory
deployed_path = r'build\exe.win64-3.6\trawl_analyzer'
if os.path.exists(deployed_path):
#    if click.confirm('Path ' + deployed_path + ' exists. Delete?', default=True):
	shutil.rmtree(deployed_path, ignore_errors=True)
	print('Deleted ' + deployed_path)

setup(  
      name='Trawl Analyzer',
      version='0.1',
      author='FRAM Data',
      description='Trawl Analyzer',
      options={'build_exe': build_exe_options},
      executables=[exe]
)

# Zip up our creation
buildzipper.create_zip_archive(base_folder=deployed_path, filedesc='trawl_analyzer')
