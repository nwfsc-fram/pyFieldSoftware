# cx_freeze build script
# Written for cx-Freeze==5.0

# When executed, installs the keys necessary for OPTECS authentication
# REQUIRES set_optecs_sync_pw.py (not in a public repository.)

# Outputs by default to build\exe.win32-3.6\
# Modify path_platforms as required

# Usage:
# build_observer.py build
# build_observer.py bdist_msi


import sys
import os
import shutil

# Useful library. http://click.pocoo.org/5/api/#click.confirm
import click

from cx_Freeze import setup, Executable
from buildzipper import buildzipper

PYTHON_DIR = sys.exec_prefix

includes = []
includefiles = [
    # N.B. The following are 2-element tuples, for explicit source and destination path
    ('../py/', 'py'),
    ]

excludes = []
# These packages are ones that cx-Freeze doesn't auto-detect
packages = ['keyring', 'click']
path = []

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
     'includes':      includes,
     'include_files': includefiles,
     'excludes':      excludes,
     'packages':      packages,
     'path':          path,
     'build_exe':     'exe.win32-3.6/observer_keyinstaller'
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
exe = None
if sys.platform == 'win32':
    exe = Executable(
        script='../py/observer/set_optecs_sync_pw.py',
        initScript=None,
        base='Console',
        targetName='observer_keyinstaller.exe',
        # compress=True,
        # copyDependentFiles=True,
        # appendScriptToExe=False,
        # appendScriptToLibrary=False,
        icon=None
    )


# Prompt to nuke existing directory
deployed_path = 'exe.win32-3.6'
if os.path.exists(deployed_path):
    if click.confirm('Path ' + deployed_path + ' exists. Delete?', default=True):
        shutil.rmtree(deployed_path)
        print('Deleted ' + deployed_path)

setup(
    name='Observer Back Deck Key Installer',
    version='0.1',
    author='FRAM Data',
    description='Observer Back Deck Key Installer',
    options={'build_exe': build_exe_options
             },
    executables=[exe],
)
# Zip up our creation
buildzipper.create_zip_archive(base_folder=deployed_path, filedesc='observer_keyinstaller')

# clean up
# Prompt to nuke existing directory
clean_paths = ['exe.win32-3.6']
if click.confirm('Cleaning up. Delete paths {0}? '.format(clean_paths), default=True):
    for path in clean_paths:
        if os.path.exists(deployed_path):
            shutil.rmtree(deployed_path)
            print('Deleted ' + deployed_path)
