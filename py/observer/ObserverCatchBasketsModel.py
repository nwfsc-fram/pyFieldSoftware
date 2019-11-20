# -----------------------------------------------------------------------------
# Name:        ObserverCatchBasketsModel.py
# Purpose:     View Model for Observer DB Table CatchAdditionalBaskets
#              (Table used only for Weight Method 3 estimation of catch weight from
#               a subset of unspeciated baskets).
# Author:      Jim Stearns
#
# Created:     27 April 2017
# License:     MIT
# ------------------------------------------------------------------------------

from playhouse.shortcuts import model_to_dict
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import CatchAdditionalBaskets


class CatchAdditionalBasketsViewModel(FramListModel):
    def __init__(self, parent=None, sort_role='catch_addtl_baskets', sort_reverse=True):
        super().__init__(parent)
        self._sort_role = sort_role
        self._sort_reverse = sort_reverse

        for role_name in self.model_props:
            self.add_role_name(role_name)

    @property
    def model_props(self):
        props = FramUtil.get_model_props(CatchAdditionalBaskets)

        return props

    def add_basket(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        :return: FramListModel index of new species item (int)
        """
        try:
            new_basket = self._get_basket_dict(db_model)
            newidx = self.insertItem(0, new_basket)  # Newest at top
            ## TODO: Exclude unweighed full baskets (weight == null). But what weight does a newly added basket have?
            if self._sort_reverse:
                self.sort_reverse(self._sort_role)
            else:
                self.sort(self._sort_role)
            self._logger.debug(f"Added basket {new_basket['catch_addtl_baskets']}")
            ## TODO: CatchesModel.add_catch() emits a modelChanged signal. Is that needed here?
            return newidx

        except ValueError as e:
            self._logger.error('Error adding new catch basket item: {}'.format(e))
            return -1

    def del_basket(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        :return: FramListModel index of new species item (int)
        """
        try:  ##TODO
            del_idx = self.get_item_index('catch_addtl_baskets', db_model.catch_addtl_baskets)
            self.remove(del_idx)
        except ValueError as e:
            self._logger.error('Error deleting new catch basket item: {}'.format(e))
            return -1

    @staticmethod
    def _get_basket_dict(db_model):
        """
        Build a dict out of a peewee model
        :param db_model: peewee model to convert
        :return: dict with values translated as desired to be FramListModel friendly
        """
        return model_to_dict(db_model)
