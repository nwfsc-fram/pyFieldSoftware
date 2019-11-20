__author__ = 'Will.Smith'
# -----------------------------------------------------------------------------
# Name:        DiscardReason.py
# Purpose:     Model for Discard Reasons
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 01, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import QObject, pyqtProperty, QVariant, pyqtSignal
from py.common.FramListModel import FramListModel


class DiscardReasonModel(FramListModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_role_name('text')
        self.add_role_name('discard_id')


class DiscardReason(QObject):

    def __init__(self, db):
        super().__init__()
        self._db = db
        self._model = DiscardReasonModel()
        self._init_model()
        self._model.sort('discard_id')

    modelChanged = pyqtSignal()

    @pyqtProperty(QVariant, notify=modelChanged)
    def DiscardReasonModel(self):
        return self._model

    def _init_model(self):
        for m in self._db.discard_reasons:
            self._model.items.append({'text': m['text'], 'discard_id': m['value']})
