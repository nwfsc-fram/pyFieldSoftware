__author__ = 'Will.Smith'
# -----------------------------------------------------------------------------
# Name:        SampleMethod.py
# Purpose:     Model for SampleMethod
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 01, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import QObject, pyqtProperty, QVariant, pyqtSignal
from py.common.FramListModel import FramListModel
import logging


class SampleMethodModel(FramListModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_role_name('text')
        self.add_role_name('method_id')


class SampleMethod(QObject):

    def __init__(self, db):
        super().__init__()
        self._db = db
        self._trawlmodel = SampleMethodModel()
        self._gearmodel = SampleMethodModel()
        self._bsmodel = SampleMethodModel()
        self._init_model()

    modelChanged = pyqtSignal()

    @pyqtProperty(QVariant, notify=modelChanged)
    def TrawlSampleMethodModel(self):
        """
        Model for Trawl (items 1-3)
        """
        return self._trawlmodel

    @pyqtProperty(QVariant, notify=modelChanged)
    def GearSampleMethodModel(self):
        """
        Model for Fixed Gear (items 4-6)
        """
        return self._gearmodel

    def _init_model(self):
        for m in self._db.sc_sample_methods:
            if int(m['value']) < 0:  # Global things we want for both (currently just a divider)
                self._trawlmodel.items.append({'text': m['text'], 'method_id': m['value']})
                self._gearmodel.items.append({'text': m['text'], 'method_id': m['value']})
            elif int(m['value']) <= 3:  # This might change some day.
                self._trawlmodel.items.append({'text': m['text'], 'method_id': m['value']})
            else:
                self._gearmodel.items.append({'text': m['text'], 'method_id': m['value']})
