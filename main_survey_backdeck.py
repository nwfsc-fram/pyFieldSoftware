__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        main_trawl_backdeck.py
# Purpose:     Main entry into the Trawl Backdeck software
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 11, 2016
# License:     MIT
#-------------------------------------------------------------------------------
import sys
import logging
import traceback
import io
import os
import arrow
import re
import glob
import shutil

from PyQt5.QtCore import QUrl, qInstallMessageHandler
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt5.Qt import QQmlComponent
from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject
from PyQt5 import QtCore
from PyQt5.QtQuick import *
from py.common.QSingleApplication import QtSingleApplication
from PyQt5 import QtGui

from py.common.FramUtil import FramUtil
from py.common.FramLog import FramLog
from py.common.SoundPlayer import SoundPlayer
# from py.trawl.WindowFrameSize import WindowFrameSize
# from py.trawl.TrawlBackdeckDB import TrawlBackdeckDB

from py.survey_backdeck.SurveyBackdeckDB import HookAndLineHookCutterDB
from py.survey_backdeck.FishSampling import FishSampling, SortFilterProxyModel
from py.survey_backdeck.RpcClient import RpcClient
from py.survey_backdeck.Sites import Sites
from py.survey_backdeck.StateMachine import StateMachine
from py.survey_backdeck.SerialPortManager import SerialPortManager
from py.survey_backdeck.LabelPrinter import LabelPrinter
from py.survey_backdeck.Notes import Notes
from py.survey_backdeck.Settings import Settings

import py.survey_backdeck.survey_backdeck_qrc


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


class Backdeck:

    def __init__(self):

        qInstallMessageHandler(FramUtil.qt_msg_handler)

        self.rpc = RpcClient()

        # self.app = QApplication(sys.argv)

        appGuid = 'F3FF80BA-BA05-4277-8063-82A6DB9245A5'
        self.app = QtSingleApplication(appGuid, sys.argv)
        self.app.setWindowIcon(QtGui.QIcon("resources/ico/cutter.ico"))
        if self.app.isRunning():
            sys.exit(0)

        self.app.unhandledExceptionCaught.connect(self.exception_caught)

        qmlRegisterType(SortFilterProxyModel, "SortFilterProxyModel", 0, 1, "SortFilterProxyModel")

        self.engine = QQmlApplicationEngine()
        self.context = self.engine.rootContext()

        # qmlRegisterType(FramTreeItem, 'FramTreeItem', 1, 0, 'FramTreeItem')

        # Set Contexts
        # wfs = WindowFrameSize()
        # self.context.setContextProperty('wfs', wfs)

        fl = FramLog()
        self.context.setContextProperty('framLog', fl)

        db = HookAndLineHookCutterDB()
        self.context.setContextProperty('db', db)

        self.state_machine = StateMachine(app=self, db=db)
        self.sound_player = SoundPlayer(app=self, db=db)
        self.serial_port_manager = SerialPortManager(app=self, db=db)

        self.sites = Sites(app=self, db=db)
        self.fish_sampling = FishSampling(app=self, db=db)
        self.label_printer = LabelPrinter(app=self, db=db)
        self.notes = Notes(app=self, db=db)
        # self.qaqc = QAQC(app=self, db=db)
        self.settings = Settings(app=self, db=db)

        self.context.setContextProperty("soundPlayer", self.sound_player)
        self.context.setContextProperty("stateMachine", self.state_machine)
        self.context.setContextProperty("sites", self.sites)
        self.context.setContextProperty("fishSampling", self.fish_sampling)
        self.context.setContextProperty("serialPortManager", self.serial_port_manager)
        self.context.setContextProperty("labelPrinter", self.label_printer)
        self.context.setContextProperty("notes", self.notes)
        # self.context.setContextProperty("qaqc", self.qaqc)
        self.context.setContextProperty("settings", self.settings)

        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        try:

            self.engine.load(QUrl('qrc:/qml/survey_backdeck/main_backdeck.qml'))

            self.win = self.engine.rootObjects()[0]
            self.msg_box = self.win.findChild(QObject, "dlgUnhandledException")

            self.engine.quit.connect(self.app.quit)
            sys.exit(self.app.exec_())

        except Exception as ex:

            logging.error(f"bad stuff happening: {ex}")

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
    for filename in glob.glob(f"CutterStation_*.log"):
        try:
            if not re.match(todays_log, filename):
                if not os.path.exists(os.path.join(dst, filename)):
                    shutil.move(src=filename, dst=dst)
        except Exception as ex:
            logging.info(f"Error archiving file {filename}: {ex}")


# Main Function
if __name__ == '__main__':
    # Create main app
    # qmlRegisterType(WindowFrameSize, 'py.trawl.WindowFrameSize', 1, 0, 'WindowFrameSize')
    # logging.basicConfig(level=logging.DEBUG)

    log_filename = f"CutterStation_{arrow.now().format('YYYYMMDD_HHmm')}.log"
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
    logging.info("Starting Software")
    logging.info("-" * 100)

    archive_logfiles(todays_log=log_filename)

    bd = Backdeck()

