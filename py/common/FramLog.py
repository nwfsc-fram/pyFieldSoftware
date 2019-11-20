
# FramLog: wrap google logging so it can be called from QML
from PyQt5.QtCore import pyqtSlot, QObject, QVariant
import logging


class FramLog(QObject):
    def __init__(self):
        super().__init__()

    @pyqtSlot(QVariant)
    def info(self, logstr):
        logging.info(logstr)

    @pyqtSlot(QVariant)
    def log(self, logstr):
        logging.info(logstr)

    @pyqtSlot(QVariant)
    def debug(self, logstr):
        logging.debug(logstr)

    @pyqtSlot(QVariant)
    def warning(self, logstr):
        logging.warning(logstr)

    @pyqtSlot(QVariant)
    def error(self, logstr):
        logging.error(logstr)
