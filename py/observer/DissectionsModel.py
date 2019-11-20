# -----------------------------------------------------------------------------
# Name:        DissectionsModel.py
# Purpose:     Model for Dissections (Observer)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     2016
# License:     MIT
# ------------------------------------------------------------------------------


from playhouse.shortcuts import model_to_dict
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import Dissections


class DissectionsModel(FramListModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        for role_name in self.model_props:
            self.add_role_name(role_name)

    @property
    def model_props(self):
        props = FramUtil.get_model_props(Dissections)
        props.append('bio_specimen_item_id')  # store ID
        return props

    def add_item(self, db_model, index=0):
        """
        Given a peewee model item, add to FramListModel
        @param db_model: BiospecimenItemsModel object
        @param index: index in model to add
        @return: index of new item
        """
        item_dict = model_to_dict(db_model, Dissections)
        item_dict['bio_specimen_item_id'] = db_model.bio_specimen_item
        if db_model.bio_specimen_item is None:
            self._logger.warning('Biospecimen item for dissection is None')
        self.insertItem(index, item_dict)  # reverse order, new at top
        return index




