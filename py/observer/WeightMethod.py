__author__ = 'Will.Smith'
# -----------------------------------------------------------------------------
# Name:        WeightMethod.py
# Purpose:     Model for Weight Methods
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 01, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import QObject, pyqtProperty, QVariant, pyqtSignal
from py.common.FramListModel import FramListModel


class WeightMethodModel(FramListModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_role_name('text')
        self.add_role_name('method_id')


class WeightMethod(QObject):

    def __init__(self, db):
        super().__init__()
        self._db = db
        self._model = WeightMethodModel()
        self._init_model()

    modelChanged = pyqtSignal()

    @pyqtProperty(QVariant, notify=modelChanged)
    def WeightMethodModel(self):
        return self._model

    def _init_model(self):
        for m in self._db.weight_methods:
            self._model.items.append({'text': m['text'], 'method_id': m['value']})
