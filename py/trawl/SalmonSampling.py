__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        SalmonSampling.py
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


class SalmonSampling(QObject):
    """
    Class for the SalmonSamplingScreen.
    """
    # speciesModelChanged = pyqtSignal(str)

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db
