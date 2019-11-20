# -----------------------------------------------------------------------------
# Name:        ObserverBasketsModel.py
# Purpose:     Model for SpeciesCompositionBaskets

# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     November 30, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from playhouse.shortcuts import model_to_dict
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import SpeciesCompositionBaskets


class ObserverBasketsModel(FramListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        for role_name in self.model_props:
            self.add_role_name(role_name)

    @property
    def model_props(self):
        props = FramUtil.get_model_props(SpeciesCompositionBaskets)
        props.append('extrapolated_number')  # Add model-only (not persisted) temp field
        # Allow primary key for species basket or for catch basket to be stored in same field
        props.append('basket_primary_key')  # Add model-only (not persisted) temp field
        return props

    def add_basket(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        :return: FramListModel index of new species item (int)
        """
        try:
            new_basket = self._get_basket_dict(db_model)
            newidx = self.insertItem(0, new_basket)  # Newest at top
            # self._logger.debug('Added basket {}'.format(new_basket['species_comp_basket']))
            return newidx

        except ValueError as e:
            self._logger.error('Error adding new species item: {}'.format(e))
            return -1

    def del_basket(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        :return: FramListModel index of new species item (int)
        """
        try:
            del_idx = self.get_item_index('basket_primary_key', db_model.basket_primary_key)
            self.remove(del_idx)
        except ValueError as e:
            self._logger.error('Error deleting new species item: {}'.format(e))
            return -1

    def _get_basket_dict(self, db_model):
        """
        Build a dict out of a peewee model
        :param db_model: peewee model to convert
        :return: dict with values translated as desired to be FramListModel friendly
        """
        model_dict = model_to_dict(db_model)

        # Put the table's primary key in extra field 'basket_primary_key', handling both species and catch baskets.
        primary_key_alternatives = ('species_comp_basket', 'catch_addtl_baskets')
        field_holding_primary_key = None
        for primary_key_alternative in primary_key_alternatives:
            if primary_key_alternative in model_dict.keys():
                field_holding_primary_key = primary_key_alternative
                break
        if not field_holding_primary_key:
            raise IndexError(f"None of the following supported primary key fields" +
                             f" were found in peewee model: {primary_key_alternatives}")
        model_dict['basket_primary_key'] = model_dict[field_holding_primary_key]
        # self._logger.debug(f'Using {field_holding_primary_key} for basket primary key')

        # Name for basket weight field is slightly different for catch additional baskets,
        # and fish_number_itq doesn't exist.
        # Decided: QML view will use basket_weight_itq, the field for species composition baskets.
        # So if this is a catch additional basket, set basket_weight_itq, and set fish_number_itq to zero.
        if field_holding_primary_key == 'catch_addtl_baskets':
            model_dict['basket_weight_itq'] = model_dict['basket_weight']
            model_dict['fish_number_itq'] = 0

        if 'extrapolated_number' not in model_dict.keys():
            model_dict['extrapolated_number'] = None
        return model_dict
