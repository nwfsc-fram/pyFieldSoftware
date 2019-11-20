__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        Reports.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 11, 2016
# License:     MIT
#-------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QVariant, Qt
from py.common.FramListModel import FramListModel
import logging


class Reports(QObject):
    """
    Class for the ReportsScreen.
    """
    # speciesModelChanged = pyqtSignal(str)

    def __init__(self, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._db = db
