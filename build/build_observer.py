# cx_freeze build script
# Written for cx-Freeze==5.0

# Outputs by default to build\exe.win32-3.6\
# Modify path_platforms as required

# Usage:
# build_observer.py --mode ifqadmin

# PYTHON 3.6 build requires patch to freezer.py
# comment out lines 626-7
# C:\ ... \virtualenv\optecs-python36\Lib\site-packages\cx_Freeze\freezer.py
# https://bitbucket.org/anthony_tuininga/cx_freeze/issues/131/fatal-python-error-py_initialize-unable-to

# DB Encryption: use encrypt_build_databases.py

# Manual steps:
#see.exe test_to_be_encrypted.db
#sqlite> PRAGMA rekey = (key)
#sqlite> PRAGMA journal_mode=DELETE;
# refer to key installer script for PW.

import sys
import os
import shutil

import re
import fileinput  # for updating build number in-place

from time import sleep

from cx_Freeze import setup, Executable
from buildzipper import buildzipper

import argparse

parser = argparse.ArgumentParser(description='Build OPTECS')
parser.add_argument("--mode", choices=['ifqadmin', 'prod', 'training'], help="Build type, ifqadmin updates version #",
                    action="store", required=True)
args = parser.parse_args()

print(f'Build selected: {args.mode}')

SCRIPT_DEBUG_MODE = False

# IMPORTANT: Only enable one of these at a time: (Slow disk/? (McAfee) usually causes overlapping build issues.)
BUILD_IFQDEV_VERSION = False  # Obsolete - might not need this again
BUILD_IFQADMIN_VERSION = args.mode == 'ifqadmin'  # also increments build #
BUILD_PRODUCTION_VERSION = args.mode == 'prod'  # does not increment
BUILD_TRAINING_VERSION = args.mode == 'training'  # does not increment

ICON_FILE_PROD = '../resources/ico/optecs.ico'
ICON_FILE_TEST = '../resources/ico/optecs_training.ico'

INCREMENT_BUILD = True if BUILD_IFQADMIN_VERSION else False  # False to leave ObserverConfig.py untouched
PERFORM_FULLSCREEN_CHECK = True  # True for Prod, False to not update QML for fullscreen mode
DEL_EXE_DIR = True  # delete temp exe.winxx dir after build

USE_ENCRYPTED_DATABASES = False if BUILD_IFQDEV_VERSION else True

custom_build_suffix = '_NoEncryption' if BUILD_IFQDEV_VERSION else ''
# example format: _NoEncryption (used when making one-off builds)

# At this point, we are done with our custom args.
# cx_Freeze requires the 'build' arg, so let's set it explicitly now
newArgs = [sys.argv[0], 'build']
sys.argv = newArgs

if USE_ENCRYPTED_DATABASES:
    print(' ******* BE SURE ENCRYPTION IS ENABLED IN ObserverConfig.py *******')
    DB_TARGET_PATH = r'data\observer_encrypted.db'
    IFQADMIN_SOURCE_DB = '../data/clean_observer_IFQADMIN_encrypted.db'
    IFQDEV_SOURCE_DB = '../data/clean_observer_IFQDEV_encrypted.db'
    IFQ_SOURCE_DB = '../data/clean_observer_IFQ_encrypted.db'
    IFQ_TRAINING_SOURCE_DB = '../data/clean_observer_IFQ_TRAINING_encrypted.db'
else:
    DB_TARGET_PATH = r'data\observer.db'
    IFQADMIN_SOURCE_DB = '../data/clean_observer_IFQADMIN.db'
    IFQDEV_SOURCE_DB = '../data/clean_observer_IFQDEV.db'
    IFQ_SOURCE_DB = '../data/clean_observer_IFQ.db'
    IFQ_TRAINING_SOURCE_DB = '../data/clean_observer_IFQ_TRAINING.db'

file_lock_delay_secs = 30  # let windows/ McAfee finish locking files between builds


def check_fullscreen_setting(prompt_to_fix=True) -> bool:
    """
    Check if fullscreen flag is set in code
    @param prompt_to_fix: prompt to modify code to remedy
    @return: Replaced fullscreen setting
    """
    settings_path = '../qml/observer/ObserverSettings.qml'
    if not os.path.exists(settings_path):
        print('*** Unable to find ObserverSettings.qml to check')
        return False

    do_replace = True

    did_replace = False
    for i, line in enumerate(fileinput.input(settings_path, inplace=1)):
        m = re.search(r'startup_small_window: *true', line)
        if m and do_replace:
            line = line.replace('true', 'false')
            did_replace = True

        sys.stdout.write(line)

    return did_replace

def increment_build_number(do_increment=True) -> str:
    """
    Increment build number
    @param do_increment: perform increment. For testing, can set this to False
    @return: Full OPTECS version string
    """
    build_config_path = '../py/observer/ObserverConfig.py'
    if not os.path.exists(build_config_path):
        print('*** Unable to increment build #.')
        return
    version_info = None
    for i, line in enumerate(fileinput.input(build_config_path, inplace=1)):
        m = re.search(r'optecs_version = \"[0-9]*\.[0-9]*\.[0-9]*\+(?P<build_num>[0-9]*)', line)
        if m:
            old_build_num = int(m.group('build_num'))
            if do_increment:
                line = line.replace('+' + str(old_build_num), '+' + str(old_build_num + 1))
            m = re.search(r'optecs_version = \"(?P<optecs_version>[0-9]*\.[0-9]*\.[0-9]*\+[0-9]*)', line)
            version_info = m.group('optecs_version')
        sys.stdout.write(line)

    return version_info


if PERFORM_FULLSCREEN_CHECK and check_fullscreen_setting():
    print('Fullscreen mode was activated. Re-run build to regenerate observer_qrc.py.')
    sys.exit(0)

optecs_version = increment_build_number(do_increment=INCREMENT_BUILD)

print(f'Building OPTECS version {optecs_version}')
PYTHON_DIR = sys.exec_prefix
PYQT5_DIR = os.path.join(PYTHON_DIR, 'lib\site-packages\PyQt5\Qt')


def running_in_anaconda_environment():
    return 'Continuum' in PYTHON_DIR and 'Anaconda' in PYTHON_DIR


if not running_in_anaconda_environment():
    path_platforms = os.path.join(PYTHON_DIR, 'lib\site-packages\PyQt5\Qt\plugins\platforms')
    # path_sqlite_dll = os.path.join(PYTHON_DIR, 'Scripts\sqlite3.dll')  # for virtualenv
    path_sqlite_dll = os.path.join('C:\Python36', 'DLLs\sqlite3.dll')  # for native python36

    # https://bitbucket.org/anthony_tuininga/cx_freeze/issues/155/required-environment-variables-tcl_library
    os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_DIR, r'lib\tcl8.6')
    os.environ['TK_LIBRARY'] = os.path.join(PYTHON_DIR, r'lib\tcl8.6')

    PYQT5_QML_DIR = os.path.join(PYQT5_DIR, 'qml')
else:  # Anaconda
    print("Building in an Anaconda environment.")
    path_platforms = os.path.join(PYTHON_DIR, 'Library', 'plugins', 'platforms')

    # https://bitbucket.org/anthony_tuininga/cx_freeze/issues/155/required-environment-variables-tcl_library
    os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_DIR, r'DLLs\tcl8.6')
    os.environ['TK_LIBRARY'] = os.path.join(PYTHON_DIR, r'DLLs\tcl8.6')

    # QML directory in Anaconda is a grandchild, not a child of PYTHON_DIR.
    PYQT5_QML_DIR = os.path.join(os.path.join(PYTHON_DIR, 'Library', 'qml'))

if not os.path.isdir(path_platforms):
    # Make sure directory containing qwindows.dll is included in install package:
    print("ERROR: Can't find platforms subdirectory ({}).".format(path_platforms))
    sys.exit(1)

includes = ['PyQt5.QtNetwork', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets']

includefiles_ifqadmin = [
    path_platforms,
    # N.B. The following are 2-element tuples, for explicit source and destination path
    (IFQADMIN_SOURCE_DB, DB_TARGET_PATH),
    # Contents of TRIP_CHECKS table currently aren't sync'ed. This will be fixed. In the meantime
    # include a json file containing all the trip checks.
    ('../resources/', 'resources'),
    ('../py/', 'py'),
    ('../qml/', 'qml'),
    (os.path.join(PYQT5_QML_DIR, 'QtQuick.2'), 'QtQuick.2'),
    (os.path.join(PYQT5_QML_DIR, 'QtQuick'), 'QtQuick'),
    (os.path.join(PYQT5_QML_DIR, 'QtQml'), 'QtQml'),
    (os.path.join(PYQT5_QML_DIR, 'QtGraphicalEffects'), 'QtGraphicalEffects'),
]

includefiles_ifqdev = [
    path_platforms,
    # N.B. The following are 2-element tuples, for explicit source and destination path
    (IFQDEV_SOURCE_DB, DB_TARGET_PATH),
    # Contents of TRIP_CHECKS table currently aren't sync'ed. This will be fixed. In the meantime
    # include a json file containing all the trip checks.
    ('../resources/', 'resources'),
    ('../py/', 'py'),
    ('../qml/', 'qml'),
    (os.path.join(PYQT5_QML_DIR, 'QtQuick.2'), 'QtQuick.2'),
    (os.path.join(PYQT5_QML_DIR, 'QtQuick'), 'QtQuick'),
    (os.path.join(PYQT5_QML_DIR, 'QtQml'), 'QtQml'),
    (os.path.join(PYQT5_QML_DIR, 'QtGraphicalEffects'), 'QtGraphicalEffects'),
]

includefiles_ifq = [
    path_platforms,
    # N.B. The following are 2-element tuples, for explicit source and destination path
    (IFQ_SOURCE_DB, DB_TARGET_PATH),
    # Contents of TRIP_CHECKS table currently aren't sync'ed. This will be fixed. In the meantime
    # include a json file containing all the trip checks.
    ('../resources/', 'resources'),
    ('../py/', 'py'),
    ('../qml/', 'qml'),
    (os.path.join(PYQT5_QML_DIR, 'QtQuick.2'), 'QtQuick.2'),
    (os.path.join(PYQT5_QML_DIR, 'QtQuick'), 'QtQuick'),
    (os.path.join(PYQT5_QML_DIR, 'QtQml'), 'QtQml'),
    (os.path.join(PYQT5_QML_DIR, 'QtGraphicalEffects'), 'QtGraphicalEffects'),
]

includefiles_ifq_training = [
    path_platforms,
    # N.B. The following are 2-element tuples, for explicit source and destination path
    (IFQ_TRAINING_SOURCE_DB, DB_TARGET_PATH),
    # Contents of TRIP_CHECKS table currently aren't sync'ed. This will be fixed. In the meantime
    # include a json file containing all the trip checks.
    ('../resources/', 'resources'),
    ('../py/', 'py'),
    ('../qml/', 'qml'),
    (os.path.join(PYQT5_QML_DIR, 'QtQuick.2'), 'QtQuick.2'),
    (os.path.join(PYQT5_QML_DIR, 'QtQuick'), 'QtQuick'),
    (os.path.join(PYQT5_QML_DIR, 'QtQml'), 'QtQml'),
    (os.path.join(PYQT5_QML_DIR, 'QtGraphicalEffects'), 'QtGraphicalEffects'),
]

if not running_in_anaconda_environment() and path_sqlite_dll:
    includefiles_ifq.append(path_sqlite_dll)  # for some reason this went away in cx_freeze 5.0)
    includefiles_ifqadmin.append(path_sqlite_dll)  # for some reason this went away in cx_freeze 5.0)
    includefiles_ifqdev.append(path_sqlite_dll)  # for some reason this went away in cx_freeze 5.0)
    includefiles_ifq_training.append(path_sqlite_dll)  # for some reason this went away in cx_freeze 5.0)

excludes = []
# These packages are ones that cx-Freeze doesn't auto-detect
packages = ['os', 'apsw', 'peewee', 'playhouse', 'fractions',
            'dateutil', 'encodings', 'arrow', 'idna',
            'logging', 'keyring', 'lxml', 'socket',
            'sqlparse', 'typing', 'zeep', 'filecmp', 'asyncio', 'pygame', 'idna', 'geopy']
path = []

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options_ifq = {
    'includes': includes,
    'include_files': includefiles_ifq,
    'excludes': excludes,
    'packages': packages,
    'path': path,
    'build_exe': 'exe.win32-3.6/observer'
}

build_exe_options_ifqdev = {
    'includes': includes,
    'include_files': includefiles_ifqdev,
    'excludes': excludes,
    'packages': packages,
    'path': path,
    'build_exe': 'exe.win32-3.6/observer'
}

build_exe_options_ifqadmin = {
    'includes': includes,
    'include_files': includefiles_ifqadmin,
    'excludes': excludes,
    'packages': packages,
    'path': path,
    'build_exe': 'exe.win32-3.6/observer'
}

build_exe_options_ifqtraining = {
    'includes': includes,
    'include_files': includefiles_ifq_training,
    'excludes': excludes,
    'packages': packages,
    'path': path,
    'build_exe': 'exe.win32-3.6/observer'
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
exe = None
icon_path = ICON_FILE_PROD if BUILD_PRODUCTION_VERSION else ICON_FILE_TEST
if sys.platform == 'win32':
    exe = Executable(
        script='../main_observer.py',
        initScript=None,
        # base='Console',  # useful for debugging
        base='Win32GUI',  # use this to hide console output (releases)
        targetName='observer.exe',
        # compress=True,
        # copyDependentFiles=True,
        # appendScriptToExe=False,
        # appendScriptToLibrary=False,
        icon=icon_path
    )

# Prompt to nuke existing directory
deployed_path = 'exe.win32-3.6'
if os.path.exists(deployed_path):
    if DEL_EXE_DIR:
        shutil.rmtree(deployed_path)
        print('Deleted ' + deployed_path)

# http://stackoverflow.com/questions/15734703/use-cx-freeze-to-create-an-msi-that-adds-a-shortcut-to-the-desktop
# http://msdn.microsoft.com/en-us/library/windows/desktop/aa371847(v=vs.85).aspx
shortcut_table = [
    ('DesktopShortcut',  # Shortcut
     'DesktopFolder',  # Directory_
     'Observer Back Deck',  # Name
     'TARGETDIR',  # Component_
     '[TARGETDIR]observer.exe',  # Target
     None,  # Arguments
     None,  # Description
     None,  # Hotkey
     None,  # Icon
     None,  # IconIndex
     None,  # ShowCmd
     'TARGETDIR'  # WkDir
     )
]

# Now create the table dictionary
msi_data = {"Shortcut": shortcut_table}

# Change some default MSI options and specify the use of the above defined tables
bdist_msi_options = {'data': msi_data,
                     'upgrade_code': '7b3ef1df-02a8-4eae-a21a-7eb3ad91b86d',  # so new installs overwrite old
                     }

# Use the correct path to build MSIst
install_exe_options = {'build_dir': 'exe.win32-3.6/observer'}


# Prompt to nuke existing directory
def cleanup(cleanup_path, prompt=not SCRIPT_DEBUG_MODE):
    if DEL_EXE_DIR:
        if os.path.exists(cleanup_path):
            shutil.rmtree(cleanup_path)
            print('Deleted ' + cleanup_path)


if BUILD_IFQADMIN_VERSION:
    setup(
        name='Observer Back Deck TEST',
        version='1.0',
        author='FRAM Data',
        description='Observer Back Deck',
        options={'build_exe': build_exe_options_ifqadmin,
                 'bdist_msi': bdist_msi_options,
                 'install_exe': install_exe_options,
                 },
        executables=[exe],
    )

    # Zip up our creation
    buildzipper.create_zip_archive(base_folder=deployed_path, filedesc=f'OPTECS_FG_IFQADMIN{custom_build_suffix}', version=optecs_version)

if BUILD_IFQDEV_VERSION:
    if BUILD_IFQADMIN_VERSION:
        print(f'Sleeping for {file_lock_delay_secs} seconds (release file locks)')
        sleep(file_lock_delay_secs)
    setup(
        name='Observer Back Deck DEV',
        version='1.0',
        author='FRAM Data',
        description='Observer Back Deck',
        options={'build_exe': build_exe_options_ifqdev,
                 'bdist_msi': bdist_msi_options,
                 'install_exe': install_exe_options,
                 },
        executables=[exe],
    )

    # Zip up our creation
    buildzipper.create_zip_archive(base_folder=deployed_path, filedesc=f'OPTECS_FG_IFQDEV{custom_build_suffix}', version=optecs_version)

if BUILD_PRODUCTION_VERSION:
    if BUILD_IFQADMIN_VERSION or BUILD_IFQDEV_VERSION:
        print(f'Sleeping for {file_lock_delay_secs} seconds (release file locks)')
        sleep(file_lock_delay_secs)
    setup(
        name='Observer Back Deck',
        version='1.0',
        author='FRAM Data',
        description='Observer Back Deck',
        options={'build_exe': build_exe_options_ifq,
                 'bdist_msi': bdist_msi_options,
                 'install_exe': install_exe_options,
                 },
        executables=[exe],
    )

    # Zip up our creation
    buildzipper.create_zip_archive(base_folder=deployed_path, filedesc=f'OPTECS_FG_PRODUCTION{custom_build_suffix}', version=optecs_version)

if BUILD_TRAINING_VERSION:
    if BUILD_IFQADMIN_VERSION or BUILD_IFQDEV_VERSION:
        print(f'Sleeping for {file_lock_delay_secs} seconds (release file locks)')
        sleep(file_lock_delay_secs)
    setup(
        name='Observer Back Deck TRAINING',
        version='1.0',
        author='FRAM Data',
        description='Observer Back Deck',
        options={'build_exe': build_exe_options_ifqtraining,
                 'bdist_msi': bdist_msi_options,
                 'install_exe': install_exe_options,
                 },
        executables=[exe],
    )

    # Zip up our creation
    buildzipper.create_zip_archive(base_folder=deployed_path, filedesc=f'OPTECS_FG_TRAINING{custom_build_suffix}', version=optecs_version)

cleanup(deployed_path)
