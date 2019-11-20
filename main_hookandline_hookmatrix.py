import sys
from PyQt5.QtCore import QUrl, qInstallMessageHandler
from PyQt5.QtQml import QQmlApplicationEngine
from py.common.QSingleApplication import QtSingleApplication
from PyQt5 import QtGui
import logging
import arrow

# Project-specific modules
from py.common.FramUtil import FramUtil
import py.hookandline_hookmatrix.hookandline_hookmatrix_qrc
from py.hookandline_hookmatrix.Sites import Sites
from py.hookandline_hookmatrix.Drops import Drops
from py.hookandline_hookmatrix.Hooks import Hooks
from py.hookandline_hookmatrix.GearPerformance import GearPerformance
from py.hookandline_hookmatrix.HookAndLineHookMatrixDB import HookAndLineHookMatrixDB
from py.hookandline_hookmatrix.StateMachine import StateMachine
from py.hookandline_hookmatrix.RpcClient import RpcClient
from py.hookandline_hookmatrix.LabelPrinter import LabelPrinter
from py.hookandline_hookmatrix.SerialPortManager import SerialPortManager
from py.hookandline_hookmatrix.Notes import Notes


class HookandlineHookMatrix:
    def __init__(self):
        qInstallMessageHandler(FramUtil.qt_msg_handler)

        self.rpc = RpcClient()

        appGuid = 'F3FF80BA-BA05-4277-8063-82A6DB9245A3'
        self.app = QtSingleApplication(appGuid, sys.argv)
        self.app.setWindowIcon(QtGui.QIcon("resources/ico/hooklogger.ico"))
        if self.app.isRunning():
            sys.exit(0)

        self.engine = QQmlApplicationEngine()
        self.context = self.engine.rootContext()

        self.context.setContextProperty('rpc', self.rpc)

        self.db = HookAndLineHookMatrixDB()
        self.context.setContextProperty('db', self.db)

        self.state_machine = StateMachine(app=self, db=self.db)
        self.context.setContextProperty('stateMachine', self.state_machine)

        self.serial_port_manager = SerialPortManager(app=self, db=self.db)
        self.context.setContextProperty('serialPortManager', self.serial_port_manager)

        self.label_printer = LabelPrinter(app=self, db=self.db)
        self.context.setContextProperty('labelPrinter', self.label_printer)

        self.sites = Sites(app=self, db=self.db)
        self.context.setContextProperty('sites', self.sites)

        self.drops = Drops(app=self, db=self.db)
        self.context.setContextProperty('drops', self.drops)

        self.hooks = Hooks(app=self, db=self.db)
        self.context.setContextProperty('hooks', self.hooks)

        self.gear_performance = GearPerformance(app=self, db=self.db)
        self.context.setContextProperty('gearPerformance', self.gear_performance)

        self.notes = Notes(app=self, db=self.db)
        self.context.setContextProperty("notes", self.notes)

        self.engine.load(QUrl('qrc:/qml/hookandline_hookmatrix/main_hookmatrix.qml'))
        self.engine.quit.connect(self.app.quit)

        sys.exit(self.app.exec_())


if __name__ == '__main__':
    # Create main app
    log_fmt = '%(levelname)s:%(filename)s:%(lineno)s:%(message)s'
    datetime = arrow.now().format("YYYYMMDD_HHMMSS")
    filename = f"HookMatrix_{datetime}.log"
    logging.basicConfig(level=logging.DEBUG, filename=filename, format=log_fmt, filemode='w')

    logger = logging.getLogger("peewee")
    logger.setLevel(logging.WARNING)

    # Also output to console (stderr)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter(log_fmt)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    hlm = HookandlineHookMatrix()
