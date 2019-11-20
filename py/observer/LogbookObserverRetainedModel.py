# -----------------------------------------------------------------------------
# Name:        LogbookObserverRetainedModel.py
# Purpose:     Model for Obs Ret entries in Logbook Mode
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Oct 21, 2016
# License:     MIT
# ------------------------------------------------------------------------------
from PyQt5.QtCore import QAbstractListModel, pyqtSlot
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QStandardItem
from PyQt5.QtGui import QStandardItemModel
from playhouse.shortcuts import model_to_dict
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import Dissections, Catches


class ObserverRetainedModel(FramListModel):
    """
    CATCHES: match FISHING_ACTIVITY_ID and CATCH_DISPOSITION='R'
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        for role_name in self.model_props:
            self.add_role_name(role_name)

    @property
    def model_props(self):
        return ['cc_code', 'weight']

    @pyqtSlot(str, result=QVariant)
    def load_observer_retained(self, fishing_activity_id, is_fixed_gear=False):
        """
        Load catches from database
        :return: list of catch codes (strings)
        """
        observer_retained_catches_query = Catches.select().where((Catches.fishing_activity == fishing_activity_id) &
                                                                 (Catches.catch_disposition == 'R') &
                                                                 ~((Catches.catch_weight_method.is_null(False)) &
                                                                   (Catches.catch_weight_method == '7')))

        ret_catches = observer_retained_catches_query.count()

        catch_codes = list()
        self.clear()
        if ret_catches > 0:
            for c in observer_retained_catches_query:
                if is_fixed_gear:
                    self.appendItem({'cc_code': c.catch_category.catch_category_code, 'weight': c.sample_weight})
                else:
                    self.appendItem({'cc_code': c.catch_category.catch_category_code, 'weight': c.catch_weight})

        return catch_codes