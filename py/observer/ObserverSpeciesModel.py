# -----------------------------------------------------------------------------
# Name:        ObserverSpeciesModel.py
# Purpose:     Model for Species (Observer)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 22, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtProperty, QVariant, QObject, pyqtSignal, pyqtSlot

from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import Species


class ObserverSpeciesModel(FramListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        for role_name in self.model_props:
            self.add_role_name(role_name)

    @property
    def model_props(self):
        props = FramUtil.get_model_props(Species)
        return props
