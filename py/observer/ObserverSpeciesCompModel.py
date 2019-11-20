# -----------------------------------------------------------------------------
# Name:        ObserverSpeciesModel.py
# Purpose:     Model for SpeciesCompositionItems

# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 22, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtProperty, QVariant, QObject, pyqtSignal, pyqtSlot

from playhouse.shortcuts import model_to_dict
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import SpeciesCompositionItems, BioSpecimens, BioSpecimenItems

import logging


class ObserverSpeciesCompModel(FramListModel):
    modelChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        for role_name in self.model_props:
            self.add_role_name(role_name)

    @property
    def model_props(self):
        props = FramUtil.get_model_props(SpeciesCompositionItems)
        props.append('common_name')
        props.append('weighed_and_tallied_count')
        props.append('avg_weight')
        props.append('bio_count')
        return props

    def add_species_item(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        :return: FramListModel index of new species item (int)
        """
        try:
            new_species_item = self._get_species_item_dict(db_model)
            newidx = self.insertItem(0, new_species_item)  # Newest at top
            self._logger.info('Added species item {}'.format(new_species_item['common_name']))
            self.modelChanged.emit()
            return newidx

        except ValueError as e:
            self._logger.error('Error adding new species item: {}'.format(e))
            return -1

    def del_species_item(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        :return: FramListModel index of new species item (int)
        """
        try:
            del_idx = self.get_item_index('species_comp_item', db_model.species_comp_item)
            self.remove(del_idx)
        except ValueError as e:
            self._logger.error('Error deleting species item: {}'.format(e))
            return -1
        finally:
            self.modelChanged.emit()


    @staticmethod
    def _get_species_item_dict(db_model):
        """
        Build a dict out of a peewee model
        Purpose is for storing peewee model <-> FramListModel
        :param db_model: peewee model to convert
        :return: dict with values translated as desired to be FramListModel friendly
        """
        species_dict = model_to_dict(db_model)

        # Example for keys that we want to rename from model-> dict:
        # tripdict['renamed'] = tripdict.pop('rename_me')

        # Populate "extra" keys if needed
        species_dict['common_name'] = db_model.species.common_name

        # Create temp column for weighed_and_tallied_count
        weighed_count = db_model.species_number if db_model.species_number else 0
        tallied_count = db_model.total_tally if db_model.total_tally else 0
        weighed_and_tallied_count = weighed_count + tallied_count
        species_dict['weighed_and_tallied_count'] = weighed_and_tallied_count
        # Create temp column for avg_weight
        avg_weight = db_model.species_weight / db_model.species_number if db_model.species_number and db_model.species_weight else None
        species_dict['avg_weight'] = avg_weight

        # This is inefficient, but required to get an accurate count of bios for now...
        # Get biospecimen item count from DB
        catch_id = db_model.species_composition.catch.catch
        species_id = db_model.species.species
        discard_reason = db_model.discard_reason
        logging.info(f'Getting biospecimen items catch id is {catch_id} and species_id is {species_id}')

        bios_q = BioSpecimens.select().where((BioSpecimens.catch == catch_id) &
                                             (BioSpecimens.species == species_id) &
                                             (BioSpecimens.discard_reason == discard_reason))

        total_bio_items_count = 0
        for b in bios_q:
            items_q = BioSpecimenItems.select().where((BioSpecimenItems.bio_specimen == b.bio_specimen))
            total_bio_items_count += items_q.count()
        species_dict['bio_count'] = total_bio_items_count

        return species_dict



