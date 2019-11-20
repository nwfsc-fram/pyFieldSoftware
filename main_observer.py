# -----------------------------------------------------------------------------
# Name:        main_observer.py
# Purpose:     Observer Electronic Back Deck user interface.
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 1, 2016
# License:     MIT
# ------------------------------------------------------------------------------

import arrow
import cProfile
import io
import logging
import os
import pstats
from socket import gethostname
import sys
import time

from PyQt5.QtCore import QUrl, qInstallMessageHandler, QT_VERSION_STR
from PyQt5.QtQml import QQmlApplicationEngine

# Note: pyinstaller doesn't copy over the 'qmldir' files required by QtQuick,
# thus requires a build script to do the copy
from PyQt5.QtQuick import *  # needed by pyinstaller, don't remove
import py.observer.observer_qrc  # Required resources

from py.common.FramUtil import FramUtil
from py.common.QSingleApplication import QtSingleApplication

from py.observer.ObserverAutoComplete import ObserverAutoComplete as AutoComplete
from py.observer.ObserverDBSyncController import ObserverDBSyncController
from py.observer.ObserverData import ObserverData
from py.observer.ObserverErrorReports import ObserverErrorReports
from py.observer.ObserverState import ObserverState
from py.observer.ObserverDBBaseModel import connect_orm, close_orm, get_db_version_info
from py.observer.ObserverSoundPlayer import SoundPlayer

from py.observer.ObserverConfig import optecs_version

# Custom Models
from py.observer.UnhandledExceptionHandler import UnhandledExceptionHandler
from py.observer.WeightMethod import WeightMethod
from py.observer.SampleMethod import SampleMethod
from py.observer.DiscardReason import DiscardReason
from py.observer.CatchCategory import CatchCategory
from py.observer.ObserverDBMigrations import ObserverDBMigrations

PROFILE_CODE = False


class ObserverLogUtility:
    """
    Just a utility class to collect naming and archiving of OPTECS log files.
    Only used by main_observer, so included here.

    Conventions:
    -   One log file a day. Open in append to handle multiple sessions in one day.
    -   Convention for log file name: observer_<hostname>_YYYYMMDD.log.
    -   Provide a utility to move any log files in PWD other than today's to a subdirectory, LogArchive.
    """
    log_archive_subdirectory = "log_archive"

    @staticmethod
    def get_log_file_prefix():
        socket_hostname = gethostname()
        hostname = socket_hostname if socket_hostname else "UnknownHost"
        return "observer_" + hostname + "_"

    @staticmethod
    def _get_log_archive_path():
        return os.path.join(os.getcwd(), ObserverLogUtility.log_archive_subdirectory)

    @staticmethod
    def _create_archive_directory_if_nonexistent():
        archive_dir = ObserverLogUtility._get_log_archive_path()
        if not os.path.exists(archive_dir):
            logger.info("LogArchive subdirectory doesn't exist. Creating.")
            os.makedirs(archive_dir)

    @staticmethod
    def get_log_file_name_for_today():
        log_file_prefix = ObserverLogUtility.get_log_file_prefix()
        log_filename_date_qualifier = arrow.now().format('YYYYMMDD')
        log_filename = f"{log_file_prefix}{log_filename_date_qualifier}.log"
        return log_filename

    @staticmethod
    def get_log_format():
        """
        https://docs.python.org/3/library/logging.html#formatter-objects
        :return: log format for OPTECS
        """
        return '%(asctime)s %(levelname)s %(filename)s(%(lineno)s) "%(message)s"'

    @staticmethod
    def get_date_format():
        """
        https://docs.python.org/3/library/logging.html#formatter-objects
        :return: log format for OPTECS
        """
        return '%Y-%m-%dT%H:%M:%S'


    @staticmethod
    def archive_log_files(exclude=None):
        """
        Assumes log files are in PWD.
        :param exclude: filenames to exclude from archiving. This typically will be today's log file only.
        :return:
        """
        import glob
        import shutil

        ObserverLogUtility._create_archive_directory_if_nonexistent()

        log_file_prefix = ObserverLogUtility.get_log_file_prefix()
        log_archive_path = ObserverLogUtility._get_log_archive_path()

        # Only finds log files in this century. Should be good.
        for filename in glob.glob(f'{log_file_prefix}20[0-9][0-9][0-1][0-9][0-9][0-9].log'):
            if exclude is not None and filename in exclude:
                logging.debug(f"Excluding {filename} from archiving.")
            else:
                # Shouldn't happen, but if filename already exists in archive directory, log error and skip move.
                dest_filepath = os.path.join(log_archive_path, filename)
                if os.path.isfile(dest_filepath):
                    logging.error(f'Logfile {filename} already exists in log archive directory ' +
                                  f'{log_archive_path}; skipping')
                else:
                    shutil.move(filename, dest_filepath)
                    logging.info(f'Moved logfile {filename} to {dest_filepath}.')


def disableQMLDiskCache():
    """
    For Qt 5.8, QML disk caching is broken (doesn't update when QML changes.)
    """
    os.environ['QML_DISABLE_DISK_CACHE'] = '1'


# __name__ in Anaconda environment is 'observer__main__'
if __name__ == '__main__' or __name__ == 'observer__main__':

    disableQMLDiskCache()

    pr = cProfile.Profile()
    if PROFILE_CODE:
        pr.enable()

    # Shut up peewee, if desired
    logger = logging.getLogger('peewee')
    logger.setLevel(logging.WARNING)

    # Create main file logger
    log_filename_for_today = ObserverLogUtility.get_log_file_name_for_today()
    log_fmt = ObserverLogUtility.get_log_format()
    date_fmt = ObserverLogUtility.get_date_format()
    log_mode_append = 'a'  # Append mode so that all sessions on one day are logged to same file.
    log_level = logging.INFO if ObserverState.getset_setting('logging_level', 'INFO') == 'INFO' else 'DEBUG'
    logging.basicConfig(level=log_level, filename=log_filename_for_today, format=log_fmt, datefmt=date_fmt,
                        filemode=log_mode_append)

    # Also output to console (stderr)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter(log_fmt, date_fmt)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    qInstallMessageHandler(FramUtil.qt_msg_handler)

    logging.info("-" * 60)  # Separate each session with a horizontal line.
    logging.info(f'OPTECS v{optecs_version} application launched ' + time.strftime("%m/%d/%Y %H:%M"))

    # Move older log files to a subdirectory, excluding today's
    ObserverLogUtility.archive_log_files(exclude=[log_filename_for_today])

    # perform any migrations required prior to run
    migrator = ObserverDBMigrations()
    migrator.perform_migrations()

    connect_orm()  # ObserverORM

    main_qml = QUrl('qrc:/qml/observer/ObserverLogin.qml')
    appGuid = '8284d07e-d07c-4aad-8874-36720e37ce53'
    app = QtSingleApplication(appGuid, sys.argv)

    logging.info(f'Qt Version: {QT_VERSION_STR}')
    logging.info(get_db_version_info())
    # logging.info('after self.app')
    if app.isRunning():
        logging.error('Application is already running, abort.')
        sys.exit(-1)

    engine = QQmlApplicationEngine()
    context = engine.rootContext()

    # Set context properties
    observer_data = ObserverData()
    context.setContextProperty('observer_data', observer_data)

    appstate = ObserverState(db=observer_data)
    context.setContextProperty('appstate', appstate)

    weight_method = WeightMethod(db=observer_data)
    context.setContextProperty('weightMethod', weight_method)

    sample_method = SampleMethod(db=observer_data)
    context.setContextProperty('sampleMethod', sample_method)

    discard_reason = DiscardReason(db=observer_data)
    context.setContextProperty('discardReason', discard_reason)

    catch_category = CatchCategory(db=observer_data)
    context.setContextProperty('catchCategory', catch_category)

    autocomplete = AutoComplete(db=observer_data)
    context.setContextProperty('autocomplete', autocomplete)

    db_sync = ObserverDBSyncController()
    context.setContextProperty('db_sync', db_sync)

    error_reports = ObserverErrorReports()
    context.setContextProperty('errorReports', error_reports)

    framutil = FramUtil()
    context.setContextProperty('framutil', framutil)

    sound_player = SoundPlayer()
    context.setContextProperty('soundPlayer', sound_player)

    # On an unhandled exception: log, display message box, and exit OPTECS.
    UnhandledExceptionHandler.connect_to_system_excepthook(
        logging, log_filename_for_today, appstate)

    engine.load(main_qml)
    engine.quit.connect(app.quit)
    ret = app.exec_()
    if PROFILE_CODE:
        pr.disable()
        s = io.StringIO()
        sortby = 'ncalls'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())

    close_orm()  # ObserverORM
    sys.exit(ret)
