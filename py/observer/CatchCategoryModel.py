# -----------------------------------------------------------------------------
# Name:        CatchCategory.py
# Purpose:     Model for Catch Category (Observer)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 22, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import QVariant, pyqtSlot
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import CatchCategories

class CatchCategoryModel(FramListModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        for role_name in self.model_props:
            self.add_role_name(role_name)


    @property
    def model_props(self):
        props = FramUtil.get_model_props(CatchCategories)
        return props

    @pyqtSlot(QVariant, result=bool)
    def is_ccid_in_model(self, ccid):
        """
        Specific to CatchCategory Models:
        Check if a CC ID code already in the model.
        (Does a string compare.)
        :param ccid: Catch Category ID
        :return: JS compatible bool
        """
        return self.is_item_in_model('catch_category', ccid)

    @pyqtSlot(QVariant)
    def remove_by_id(self, ccid):
        """
        Specific to CatchCategory Models: remove first matching ID
        (Does a string compare.)
        :param ccid: Catch Category ID
        :return: JS compatible bool
        """

        if ccid is None:
            self._logger.error('Remove by ID {}'.format(ccid))
            return
        remove_index = self.get_item_index('catch_category', ccid)
        if remove_index >= 0:
            self.remove(remove_index)

    @pyqtSlot(QVariant)
    def remove_by_code(self, cc_code):
        """
        Specific to CatchCategory Models: remove first matching ID
        (Does a string compare.)
        :param ccid: Catch Category ID
        :return: JS compatible bool
        """

        if cc_code is None:
            self._logger.error('Remove by CC Code {}'.format(cc_code))
            return
        remove_index = self.get_item_index('catch_category_code', cc_code)
        if remove_index >= 0:
            self.remove(remove_index)