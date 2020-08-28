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
import socket

from PyQt5.QtCore import QUrl, qInstallMessageHandler
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt5.Qt import QQmlComponent
from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject
from PyQt5 import QtCore
from PyQt5.QtQuick import *
from py.common.QSingleApplication import QtSingleApplication

from py.common.FramUtil import FramUtil
from py.common.FramLog import FramLog
from py.common.FramTreeItem import FramTreeItem
from py.trawl.WindowFrameSize import WindowFrameSize
from py.trawl.TrawlBackdeckDB import TrawlBackdeckDB
from py.trawl.Home import Home
from py.trawl.HaulSelection import HaulSelection
from py.trawl.ProcessCatch import ProcessCatch
from py.trawl.WeighBaskets import WeighBaskets
from py.trawl.FishSampling import FishSampling
from py.trawl.SalmonSampling import SalmonSampling
from py.trawl.CoralsSampling import CoralsSampling
from py.trawl.SpecialActions import SpecialActions
from py.trawl.QAQC import QAQC
from py.trawl.Reports import Reports
from py.trawl.SerialPortManager import SerialPortManager
from py.trawl.Settings import Settings
from py.trawl.StateMachine import StateMachine
from py.trawl.ProtocolViewer import ProtocolViewer
from py.trawl.Notes import Notes
from py.common.SoundPlayer import SoundPlayer
from py.common.LabelPrinter import LabelPrinter
from py.trawl.NetworkTesting import NetworkTesting
import py.trawl.trawl_backdeck_qrc


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
    if QApplication.instance():
        app = QApplication.instance()
        app.unhandledExceptionCaught.emit(except_type, except_value, traceback_obj)

    else:
        logging.info("not a QApplication")


sys.excepthook = exception_hook


class TrawlBackdeck:

    def __init__(self):

        qInstallMessageHandler(FramUtil.qt_msg_handler)

        # self.app = QApplication(sys.argv)

        appGuid = 'F3FF80BA-BA05-4277-8063-82A6DB9245A2'
        self.app = QtSingleApplication(appGuid, sys.argv)
        self.host_cpu = socket.gethostname()
        if self.app.isRunning():
            sys.exit(0)

        self.app.unhandledExceptionCaught.connect(self.exception_caught)

        self.engine = QQmlApplicationEngine()
        self.context = self.engine.rootContext()

        qmlRegisterType(FramTreeItem, 'FramTreeItem', 1, 0, 'FramTreeItem')

        # Set Contexts
        wfs = WindowFrameSize()
        self.context.setContextProperty('wfs', wfs)

        fl = FramLog()
        self.context.setContextProperty('framLog', fl)

        db = TrawlBackdeckDB()
        self.context.setContextProperty('db', db)

        self.sound_player = SoundPlayer()
        self.label_printer = LabelPrinter(app=self, db=db)
        self.settings = Settings(db=db)
        self.state_machine = StateMachine(app=self, db=db)
        self.serial_port_manager = SerialPortManager(app=self, db=db)
        self.network_testing = NetworkTesting(app=self, db=db)
        self.protocol_viewer = ProtocolViewer(app=self, db=db)
        self.home = Home(app=self, db=db)
        self.haul_selection = HaulSelection(app=self, db=db)
        self.process_catch = ProcessCatch(app=self, db=db)
        self.weigh_baskets = WeighBaskets(app=self, db=db)
        self.fish_sampling = FishSampling(app=self, db=db)
        self.salmon_sampling = SalmonSampling(app=self, db=db)
        self.corals_sampling = CoralsSampling(app=self, db=db)
        self.special_actions = SpecialActions(app=self, db=db)
        self.qaqc = QAQC(app=self, db=db)
        self.reports = Reports(db=db)
        self.notes = Notes(app=self, db=db)

        self.context.setContextProperty("soundPlayer", self.sound_player)
        self.context.setContextProperty("settings", self.settings)
        self.context.setContextProperty("home", self.home)
        self.context.setContextProperty("haulSelection", self.haul_selection)
        self.context.setContextProperty('processCatch', self.process_catch)
        self.context.setContextProperty("weighBaskets", self.weigh_baskets)
        self.context.setContextProperty("fishSampling", self.fish_sampling)
        self.context.setContextProperty("salmonSampling", self.salmon_sampling)
        self.context.setContextProperty("coralsSampling", self.corals_sampling)
        self.context.setContextProperty("specialActions", self.special_actions)
        self.context.setContextProperty("qaqc", self.qaqc)
        self.context.setContextProperty("reports", self.reports)
        self.context.setContextProperty("serialPortManager", self.serial_port_manager)
        self.context.setContextProperty("stateMachine", self.state_machine)
        self.context.setContextProperty("protocolViewer", self.protocol_viewer)
        self.context.setContextProperty("networkTesting", self.network_testing)
        self.context.setContextProperty("notes", self.notes)

        self.engine.load(QUrl('qrc:/qml/trawl/main_backdeck.qml'))

        self.win = self.engine.rootObjects()[0]
        self.msg_box = self.win.findChild(QObject, "dlgUnhandledException")

        self.engine.quit.connect(self.app.quit)
        sys.exit(self.app.exec_())

    def exception_caught(self, except_type, except_value, traceback_obj):

        # Stop all background threads
        # self.file_management.stop_background_threads()
        # self.data_completeness.stop_data_loading()
        # self.time_series.stop_background_threads()

        tbinfofile = io.StringIO()
        traceback.print_tb(traceback_obj, None, tbinfofile)
        tbinfofile.seek(0)
        tbinfo = tbinfofile.read()

        log_filename = "trawl_backdeck_debug.log"
        log_filepath = os.path.join(os.getcwd(), log_filename)

        msg = f"Exception occurred at {arrow.now().format('MM/DD/YYYY HH:mm:ss')}\n\n Please check log file at:\n{log_filepath}\n\n{except_type}: {except_value}\n\n{tbinfo}"
        logging.info(f"{msg}")
        self.msg_box.show(msg)
        logging.info(f"Trawl Backdeck is quitting at {arrow.now().format('MM/DD/YYYY HH:mm:ss')}")


# Main Function
if __name__ == '__main__':
    # Create main app
    # qmlRegisterType(WindowFrameSize, 'py.trawl.WindowFrameSize', 1, 0, 'WindowFrameSize')
    # logging.basicConfig(level=logging.DEBUG)

    log_fmt = '%(levelname)s:%(filename)s:%(lineno)s:%(message)s'
    logging.basicConfig(level=logging.DEBUG, filename='trawl_backdeck_debug.log', format=log_fmt, filemode='w')

    logger = logging.getLogger("peewee")
    logger.setLevel(logging.WARNING)

    # Also output to console (stderr)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter(log_fmt)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    tbd = TrawlBackdeck()




    # app = QApplication(sys.argv)
    # engine = QQmlApplicationEngine()
    #
    # context = engine.rootContext()
    #
    # context.setContextProperty('appEngine', engine)
    #
    # wfs = WindowFrameSize()
    # context.setContextProperty('wfs', wfs)
    #
    # fl = FramLog()
    # context.setContextProperty('framLog', fl)
    #
    # db = TrawlBackdeckDB()
    # context.setContextProperty('db', db)
    #
    # settings = TrawlBackdeckSettings(db=db)
    # haul_selection = HaulSelection(db=db)
    # process_catch = ProcessCatch(db=db)
    # weigh_baskets = WeighBaskets(db=db)
    # fish_sampling = FishSampling(db=db)
    # salmon_sampling = SalmonSampling(db=db)
    # corals_sampling = CoralsSampling(db=db)
    # special_actions = SpecialActions(db=db)
    # qaqc = QAQC(db=db)
    # reports = Reports(db=db)
    # serial_port_manager = SerialPortManager(db=db)
    #
    # context.setContextProperty("settings", settings)
    # context.setContextProperty("haulSelection", haul_selection)
    # context.setContextProperty('processCatch', process_catch)
    # context.setContextProperty("weighBaskets", weigh_baskets)
    # context.setContextProperty("fishSampling", fish_sampling)
    # context.setContextProperty("salmonSampling", salmon_sampling)
    # context.setContextProperty("coralsSampling", corals_sampling)
    # context.setContextProperty("specialActions", special_actions)
    # context.setContextProperty("qaqc", qaqc)
    # context.setContextProperty("reports", reports)
    # context.setContextProperty("serialPortManager", serial_port_manager)
    #
    # engine.load(QUrl('qrc:/qml/trawl/main_ashop.qml'))
    #
    # engine.quit.connect(app.quit)
    # sys.exit(app.exec_())
