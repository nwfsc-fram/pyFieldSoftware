__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        main_trawl_analyzer.py
# Purpose:     Main entry into the Trawl Analyzer software
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     November 2, 2016
# License:     MIT
#-------------------------------------------------------------------------------
import sys
import logging
import traceback
import io
import arrow
import os
import signal
from uuid import uuid1
import arrow

from PyQt5.QtCore import QUrl, qFatal
from PyQt5.QtCore import qInstallMessageHandler, QCoreApplication
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMessageBox
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
# from PyQt5.Qt import QQmlComponent
from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject
from PyQt5 import QtCore
from PyQt5.QtQuick import *
import importlib
from matplotlib.figure import Figure

from py.common.QSingleApplication import QtSingleApplication

from py.common.FramUtil import FramUtil
from py.common.FramLog import FramLog
from py.common.FramTreeItem import FramTreeItem
# from py.trawl.WindowFrameSize import WindowFrameSize
from py.trawl_analyzer.TrawlAnalyzerDB import TrawlAnalyzerDB
from py.trawl_analyzer.FileManagement import FileManagement
from py.trawl_analyzer.DataCompleteness import DataCompleteness, SortFilterProxyModel
from py.trawl_analyzer.Settings import Settings
from py.trawl_analyzer.TimeSeries import TimeSeries
from py.trawl_analyzer.CommonFunctions import CommonFunctions
# from py.trawl.Home import Home
# from py.trawl.QAQC import QAQC
# from py.trawl.Reports import Reports
# from py.trawl.Settings import Settings
# from py.trawl.StateMachine import StateMachine
# from py.trawl.Notes import Notes

from py.common.SoundPlayer import SoundPlayer

import py.trawl_analyzer.trawl_analyzer_qrc


from py.trawl_analyzer.backend_qtquick5 import FigureCanvasQTAgg
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


def exception_hook(except_type, except_value, traceback_obj):
    """
    Global function to log an unhandled exception, including its stack trace,
    to display a message box with a summary of the exception for the observer,
    and upon observer hitting OK, to exit trawl analyzer with a non-zero return value.

    Based upon https://riverbankcomputing.com/pipermail/pyqt/2009-May/022961.html

    :param except_type:
    :param except_value:
    :param traceback_obj:
    :return:
    """
    # logging.error("Caught an unhandled exception in Trawl Analyzer.")
    # error_ret_value = 1
    # log_filename = "trawl_analzyer_debug.log"
    # log_filepath = os.path.join(os.getcwd(), log_filename)
    # notice = f"An unhandled exception occurred and is captured in the log file\n{log_filepath}\n"
    #
    # tbinfofile = io.StringIO()
    # traceback.print_tb(traceback_obj, None, tbinfofile)
    # tbinfofile.seek(0)
    # tbinfo = tbinfofile.read()
    #
    # except_summary = f"Exception Summary: {except_type}: {except_value}"
    #
    # time_str = arrow.now().format('MM/DD/YYYY, HH:mm:ss')

    # First, to the log file:
    # try:
    #     logging.error(f"Exception occurred at: {time_str}")
    #     logging.error(f"{except_summary}")
    #     logging.error(f"Exception Trace:\n{tbinfo}")
    #     # logging.error(version_info)
    # except IOError:
    #     pass

    if QApplication.instance():
        app = QApplication.instance()
        app.unhandledExceptionCaught.emit(except_type, except_value, traceback_obj)
        # msgbox = app.findChild(QObject, "dlgUnhandledException")
        # msgbox.show()
        # app.aboutToQuit.emit()
        # app.exit(error_ret_value)

        # Now to a message box
        # msg = f"{time_str}\n{except_summary}\n\nHit OK to exit Trawl Analyzer"
        # msg = f"{notice}\n{msg}"
        # errorbox = QMessageBox()
        # errorbox.setIcon(QMessageBox.Critical)
        # errorbox.setText(msg)
        # errorbox.exec_()


    else:
        logging.info("not a QApplication")


    # Tell PyQt to exit with an error value
    # QCoreApplication.exit(error_ret_value)


sys.excepthook = exception_hook


class TrawlAnalyzer:

    def __init__(self):

        logging.info(f"Trawl Analyzer starting at: {arrow.now().format('MM/DD/YYYY HH:mm:ss')}")

        qInstallMessageHandler(FramUtil.qt_msg_handler)

        app_guid = str(uuid1())
        logging.info(f"uuid={app_guid}")

        self.app = QtSingleApplication(app_guid, sys.argv)
        if self.app.isRunning():
            sys.exit(0)

        self.app.unhandledExceptionCaught.connect(self.exception_caught)
        # self.app.aboutToQuit.connect(self.about_to_quit_callback)

        self.engine = QQmlApplicationEngine()
        self.context = self.engine.rootContext()

        qmlRegisterType(FramTreeItem, 'FramTreeItem', 1, 0, 'FramTreeItem')
        qmlRegisterType(SortFilterProxyModel, "SortFilterProxyModel", 0, 1, "SortFilterProxyModel")
        # qmlRegisterType(MatplotlibFigure, "MatplotlibFigure", 1, 0, "MatplotlibFigure")

        qmlRegisterType(FigureCanvasQTAgg, "MplBackend", 1, 0, "MplFigureCanvas")

        # Set Contexts
        # wfs = WindowFrameSize()
        # self.context.setContextProperty('wfs', wfs)

        self.settings = Settings(app=self)
        self.context.setContextProperty("settings", self.settings)

        fl = FramLog()
        self.context.setContextProperty('framLog', fl)

        self.db = TrawlAnalyzerDB()
        self.context.setContextProperty('db', self.db)

        self.common_functions = CommonFunctions(app=self)
        self.context.setContextProperty('commonFunctions', self.common_functions)

        self.file_management = FileManagement(app=self, db=self.db)
        self.context.setContextProperty("fileManagement", self.file_management)

        self.data_completeness = DataCompleteness(app=self, db=self.db)
        self.context.setContextProperty("dataCompleteness", self.data_completeness)

        self.time_series = TimeSeries(app=self, db=self.db)
        self.context.setContextProperty("timeSeries", self.time_series)

        self.engine.load(QUrl('qrc:/qml/trawl_analyzer/main_trawl_analyzer.qml'))

        """
        Used to access QML objects from Python.  References:
        https://forum.qt.io/topic/62966/parent-in-pyqt5-with-qml
        http://stackoverflow.com/questions/24111717/how-to-bind-buttons-in-qt-quick-to-python-pyqt-5
        """
        self.win = self.engine.rootObjects()[0]
        self.qml_item = self.win.findChild(QObject, "mplFigure")
        self.time_series.set_qml_item(self.qml_item)

        self.msg_box = self.win.findChild(QObject, "dlgUnhandledException")


        self.tracklines_item = self.win.findChild(QObject, "mplTracklines")
        self.time_series._mpl_map.set_qml_item(self.tracklines_item)

        self.engine.quit.connect(self.app.quit)
        sys.exit(self.app.exec_())

    def exception_caught(self, except_type, except_value, traceback_obj):

        # Stop all background threads
        self.file_management.stop_background_threads()
        self.data_completeness.stop_data_loading()
        self.time_series.stop_background_threads()

        tbinfofile = io.StringIO()
        traceback.print_tb(traceback_obj, None, tbinfofile)
        tbinfofile.seek(0)
        tbinfo = tbinfofile.read()

        log_filename = "trawl_analzyer_debug.log"
        log_filepath = os.path.join(os.getcwd(), log_filename)

        msg = f"Exception occurred at {arrow.now().format('MM/DD/YYYY HH:mm:ss')}\n\n Please check log file at:\n{log_filepath}\n\n{except_type}: {except_value}\n\n{tbinfo}"
        logging.info(f"{msg}")
        self.msg_box.show(msg)
        logging.info(f"Trawl Analyzer is quitting at {arrow.now().format('MM/DD/YYYY HH:mm:ss')}")

    # def about_to_quit_callback(self):
    #
    #     logging.info("about to quit callback")


# Main Function
if __name__ == '__main__':

    # sys.excepthook = exception_hook

    # Create main app
    # qmlRegisterType(WindowFrameSize, 'py.trawl.WindowFrameSize', 1, 0, 'WindowFrameSize')
    # logging.basicConfig(level=logging.DEBUG)

    log_fmt = '%(levelname)s:%(filename)s:%(lineno)s:%(message)s'
    logging.basicConfig(level=logging.DEBUG, filename='trawl_analyzer_debug.log', format=log_fmt, filemode='w')

    logger = logging.getLogger("peewee")
    logger.setLevel(logging.WARNING)

    # Also output to console (stderr)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter(log_fmt)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    ta = TrawlAnalyzer()


