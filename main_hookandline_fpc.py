# Testing PyQt5 and Observer Electronic Back Deck user interface.

import sys
import threading
import traceback
import io
import os
import glob
import shutil
import re

import arrow

from PyQt5.QtCore import QUrl, qInstallMessageHandler, QObject, QThread, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QSplashScreen
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType, QQmlComponent, QQmlEngine
from PyQt5.QtQuick import QQuickView
from py.common.QSingleApplication import QtSingleApplication

from PyQt5 import QtGui, QtCore


# TODO Imports from PyQt5.QtQuick might be necessary to get pyinstaller to add
from PyQt5.QtQuick import *

import py.hookandline.hookandline_fpc_qrc
import logging

from py.common.FramUtil import FramUtil
from py.common.FramLog import FramLog
from py.common.FramTreeItem import FramTreeItem
from py.hookandline.HookandlineFpcDB import HookandlineFpcDB
from py.hookandline.FpcMain import FpcMain
from py.hookandline.SensorDataFeeds import SensorDataFeeds
from py.hookandline.SerialPortManager import SerialPortManager
from py.hookandline.DataConverter import DataConverter
from py.hookandline.TextFieldDoubleValidator import TextFieldDoubleValidator
from py.hookandline.Settings import Settings
from py.hookandline.RpcServer import RpcServer
from py.hookandline.SpeciesReview import SpeciesReview
from py.hookandline.SerialPortSimulator import SerialPortSimulator
from py.hookandline.EndOfSiteValidation import EndOfSiteValidation


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
    logging.info(f"except_type = {except_type}, except_value = {except_value}, "
                 f"traceback_obj = {traceback_obj}")

    if QApplication.instance():
        app = QApplication.instance()
        app.unhandledExceptionCaught.emit(except_type, except_value, traceback_obj)

    else:
        logging.info("not a QApplication")


sys.excepthook = exception_hook


class FpcSplash(QSplashScreen):
    """
    Class to hold splash screen config
    Helpful: https://stackoverflow.com/questions/58661539/create-splash-screen-in-pyqt5
    # 265: Splash screen should help indicate when HookLogger is booting
    TODO: Make gif animated???
    TODO: Loading screen with message and pic... progress bar???
    TODO: Consolidate in "Common" folder
    """
    def __init__(self):
        super(QSplashScreen, self).__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.SplashScreen)
        self.setPixmap(QtGui.QPixmap("./resources/images/hooklogger_icon.png"))
        self.setWindowOpacity(0.80)


class HookandlineFpc(QObject):

    def __init__(self):

        super().__init__()

        qInstallMessageHandler(FramUtil.qt_msg_handler)

        # self.app = QApplication(sys.argv)

        appGuid = 'F3FF80BA-BA05-4277-8063-82A6DB9245A2'
        self.app = QtSingleApplication(appGuid, sys.argv)
        self.app.setWindowIcon(QtGui.QIcon("resources/ico/hooklogger_v2.ico"))
        splash = FpcSplash()
        splash.show()
        if self.app.isRunning():
            sys.exit(0)

        # qmlRegisterType(FramTreeItem, 'FramTreeItem', 1, 0, 'FramTreeItem')

        self.engine = QQmlApplicationEngine()

        qmlRegisterType(TextFieldDoubleValidator, "FRAM", 1, 0, "TextFieldDoubleValidator")

        self.context = self.engine.rootContext()

        fl = FramLog()
        self.context.setContextProperty('framLog', fl)

        db = HookandlineFpcDB()
        self.context.setContextProperty('db', db)

        # self.textfield_double_validator = TextFieldDoubleValidator()
        # self.context.setContextProperty('TextFieldDoubleValidator', self.textfield_double_validator)

        # PyQt5 Threading approach
        self._rpc_thread = QThread()
        self._rpc_worker = RpcServer()
        self._rpc_worker.moveToThread(self._rpc_thread)
        self._rpc_worker.speciesChanged.connect(self._species_changed)
        self._rpc_thread.started.connect(self._rpc_worker.run)
        self._rpc_thread.start()

        logging.info(f"\tRPC thread and worker established")

        # Technique that works - traditional python threading, although the queue is not needed anymore
        # self._queue = Queue()
        # self._rpc_server = threading.Thread(target=RpcServer, kwargs={'queue': self._queue})
        # self._rpc_server.setDaemon(True)
        # self._rpc_server.start()

        self.fpc_main = FpcMain(app=self)
        self.settings = Settings(db=db)
        self.serial_port_manager = SerialPortManager(app=self, db=db)
        self.serial_port_simulator = SerialPortSimulator(app=self, db=db)
        self.data_converter = DataConverter(app=self, db=db)
        self.sensor_data_feeds = SensorDataFeeds(app=self, db=db)
        self.species_review = SpeciesReview(app=self, db=db)
        self.end_of_site_validation = EndOfSiteValidation(app=self, db=db)
        logging.info(f"\tComponent classes all initialized")

        self.context.setContextProperty('fpcMain', self.fpc_main)
        self.context.setContextProperty('settings', self.settings)
        self.context.setContextProperty('serialPortManager', self.serial_port_manager)
        self.context.setContextProperty('serialPortSimulator', self.serial_port_simulator)
        self.context.setContextProperty('dataConverter', self.data_converter)
        self.context.setContextProperty('sensorDataFeeds', self.sensor_data_feeds)
        self.context.setContextProperty('speciesReview', self.species_review)
        self.context.setContextProperty('endOfSiteValidation', self.end_of_site_validation)

        logging.info(f"\tContext Properties all set")

        # self.widget = self.app.instance()
        # self.widget.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)
        # self.widget.setAttribute(QtCore.Qt.WA_NoSystemBackground)

        # self.view = QQuickView()
        # self.view.setSource(QUrl('qrc:/qml/hookandline/main_fpc.qml'))
        # self.view.show()

        try:
            self.engine.load(QUrl('qrc:/qml/hookandline/main_fpc.qml'))
            splash.close()
            self.win = self.engine.rootObjects()[0]
            self.msg_box = self.win.findChild(QObject, "dlgUnhandledException")

            logging.info(f"\tmain_fpc.qml loaded")

            self.engine.quit.connect(self.app.quit)
            sys.exit(self.app.exec_())

        except Exception as ex:

            logging.error(f"error loading the application: {ex}")

    def _species_changed(self, station, set_id, adh):
        """
        Method called when a species is changed by the HookMatrix or the CutterStation and we need to dynamically
        update the SpeciesReviewDialog
        :param station: HookMatrix or CutterStation
        :param set: The set number
        :param adh: 3-character value, i.e. the ADH could be A21, A34
        :return:
        """
        self.species_review.species_changed(station=station, set_id=set_id, adh=adh)

    def exception_caught(self, except_type, except_value, traceback_obj):

        tbinfofile = io.StringIO()
        traceback.print_tb(traceback_obj, None, tbinfofile)
        tbinfofile.seek(0)
        tbinfo = tbinfofile.read()

        log_filename = "survey_backdeck_debug.log"
        log_filepath = os.path.join(os.getcwd(), log_filename)

        msg = f"Exception occurred at {arrow.now().format('MM/DD/YYYY HH:mm:ss')}\n\n Please check log file at:\n{log_filepath}\n\n{except_type}: {except_value}\n\n{tbinfo}"
        logging.info(f"{msg}")
        self.msg_box.show(msg)
        logging.info(f"Survey Backdeck is quitting at {arrow.now().format('MM/DD/YYYY HH:mm:ss')}")


def archive_logfiles(todays_log):

    logging.info(f"archiving log files")
    dst = "logs"
    if not os.path.exists(dst):
        os.mkdir(dst)
    for filename in glob.glob(f"HookLogger_*.log"):
        try:
            if not re.match(todays_log, filename):
                if not os.path.exists(os.path.join(dst, filename)):
                    shutil.move(src=filename, dst=dst)
        except Exception as ex:
            logging.info(f"Error archiving file {filename}: {ex}")


# Main Function
if __name__ == '__main__':

    # Create main app
    log_filename = f"HookLogger_{arrow.now().format('YYYYMMDD')}.log"
    log_fmt = '%(asctime)s %(levelname)s:%(filename)s:%(lineno)s:%(message)s'
    logging.basicConfig(level=logging.DEBUG, filename=log_filename, format=log_fmt, filemode='a')

    logger = logging.getLogger("peewee")
    logger.setLevel(logging.WARNING)

    # Also output to console (stderr)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter(log_fmt)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    logging.info("-" * 100)
    logging.info("Starting HookLogger Software")
    logging.info("-" * 100)

    archive_logfiles(todays_log=log_filename)

    hlf = HookandlineFpc()

