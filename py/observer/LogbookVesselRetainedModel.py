# -----------------------------------------------------------------------------
# Name:        LogbookVesselRetainedModel.py
# Purpose:     Model for Vessel Ret entries in Logbook Mode
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
from PyQt5.QtQml import QJSValue
from playhouse.shortcuts import model_to_dict
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverCatches import ObserverCatches
from py.observer.ObserverDBModels import Dissections, Catches, CatchCategories
from py.observer.ObserverDBUtil import ObserverDBUtil


class VesselRetainedModel(FramListModel):
    """
    CATCHES: match FISHING_ACTIVITY_ID and CATCH_DISPOSITION='R' and NOTES='LOGBOOK_VESSEL_RETAINED'
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        for role_name in self.model_props:
            self.add_role_name(role_name)

    @property
    def model_props(self):
        return ['cc_code', 'weight']

    @pyqtSlot(str, result=QVariant)
    def load_vessel_retained(self, fishing_activity_id):
        """
        Load catches from database
        :return: list of catch codes (strings)
        """
        vessel_retained_catches_query = Catches.select().where((Catches.fishing_activity == fishing_activity_id) &
                                                               (Catches.catch_disposition == 'R') &
                                                               (Catches.catch_weight_method == '7'))

        v_ret_catches = vessel_retained_catches_query.count()

        catch_codes = list()
        self.clear()
        if v_ret_catches > 0:
            for c in vessel_retained_catches_query:
                self.appendItem({'cc_code': c.catch_category.catch_category_code, 'weight': c.catch_weight})

        return catch_codes

    @pyqtSlot(str, QVariant)
    def add_vessel_ret(self, haul_id, vessel_ret):
        """
        Add a vessel retained ListElement to our model and save to DB
        @param haul_id: Haul DB Id (Fishing Activity)
        @param vessel_ret: ListElement QJSValue
        @return:
        """
        if isinstance(vessel_ret, QJSValue):  # convert QJSValue to QVariant (then to dict)
            vessel_ret = vessel_ret.toVariant()
        found_cc_code = CatchCategories.get(CatchCategories.catch_category_code == vessel_ret['cc_code'])

        catch_num = ObserverCatches.get_next_catch_num_for_this_haul(haul_id, self._logger)
        Catches.create(fishing_activity=haul_id,
                       catch_category=found_cc_code.catch_category,
                       catch_weight=vessel_ret['weight'],
                       catch_weight_method='7',
                       catch_purity=None,
                       catch_weight_um='LB',
                       catch_disposition='R',
                       catch_num=catch_num,
                       created_by=ObserverDBUtil.get_current_user_id(),
                       created_date=ObserverDBUtil.get_arrow_datestr(),
                       )
        self.appendItem(vessel_ret)
