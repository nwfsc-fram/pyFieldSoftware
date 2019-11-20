# -----------------------------------------------------------------------------
# Name:        BiospecimenItemsModel.py
# Purpose:     Model for Biospecimens for Species (Observer)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     July 11, 2016
# License:     MIT
# ------------------------------------------------------------------------------


from PyQt5.QtCore import QVariant, pyqtSlot, pyqtProperty, pyqtSignal

from playhouse.shortcuts import model_to_dict
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import BioSpecimens, \
    BioSpecimenItems, Dissections


class BiospecimenItemsModel(FramListModel):
    lookup_bc = {
        '1': 'O',
        '2': 'SC',
        '3': 'SS',
        '4': 'FC',  # for old DB's
        '5': 'FR',
        '6': 'TS',  # for old DB's
        '7': 'WS',
        '8': 'ET',
        '9': 'OT',
        '10': 'FC',
        '11': 'TS',
    }

    def __init__(self, parent=None):

        super().__init__(parent)
        for role_name in self.model_props:
            self.add_role_name(role_name)

    @property
    def model_props(self):
        props = FramUtil.get_model_props(BioSpecimenItems)
        props.append('bio_specimen_id')
        props.append('barcodes_str')
        props.append('tags_str')
        props.append('biosample_str')
        return props

    def add_biospecimen_item(self, db_model, index=0, add_to_end=False, phlb_temp_weight=None):
        """
        Given a peewee model item, add to FramListModel
        @param db_model: BiospecimenItemsModel object
        @param index: index in model to add
        @param add_to_end: add to end instead of using index
        @param phlb_temp_weight: if PHLB, supply weight for user display (not saved to DB)
        @return: index of new item
        """
        item_dict = model_to_dict(db_model, BioSpecimenItems)
        item_dict['bio_specimen_id'] = db_model.bio_specimen_item
        item_dict['barcodes_str'] = self.build_barcodes_str(db_model)
        item_dict['tags_str'] = self.build_barcodes_str(db_model, tag=True)
        item_dict['biosample_str'] = db_model.bio_specimen.sample_method
        if phlb_temp_weight:
            item_dict['specimen_weight'] = phlb_temp_weight
        if add_to_end:
            index = self.count - 1

        self.insertItem(index, item_dict)  # reverse order, new at top
        return index

    def update_barcodes(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        """
        idx = self.get_item_index('bio_specimen_id', db_model.bio_specimen_item)
        if idx >= 0:
            self.setProperty(idx, 'barcodes_str', self.build_barcodes_str(db_model))

    def update_tag(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        """
        idx = self.get_item_index('bio_specimen_id', db_model.bio_specimen_item)
        if idx >= 0:
            self.setProperty(idx, 'tags_str', self.build_barcodes_str(db_model, tag=True))

    def update_biosample_method(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere

        """
        idx = self.get_item_index('bio_specimen_id', db_model.bio_specimen_item)
        if idx >= 0:
            self.setProperty(idx, 'biosample_str', db_model.bio_specimen.sample_method)

    def build_barcodes_str(self, db_model, tag=False):
        """
        Query DB for all barcodes associated with this biospecimen item
        :param db_model: peewee model object (cursor) created elsewhere
        :param tag: query for ET(8) or OT(9)
        @return:
        """

        if not tag:
            dissections = Dissections.select().where((Dissections.bio_specimen_item == db_model.bio_specimen_item) &
                                                     (Dissections.dissection_type.not_in(('8','9')))
                                                     )
        else:
            dissections = Dissections.select().where((Dissections.bio_specimen_item == db_model.bio_specimen_item) &
                                                     (Dissections.dissection_type << ('8','9'))
                                                     )
        barcodes = []
        for d in dissections:
            if d.dissection_type == '9' or d.dissection_type == '8':
                # Don't include empty bands
                if not d.band:
                    continue
                if d.dissection_type == '9':  # Put single OT tag at top of list
                    barcodes.insert(0, '{} {}'.format(self.lookup_bc[d.dissection_type], d.band))
                else:
                    barcodes.append('{} {}'.format(self.lookup_bc[d.dissection_type], d.band))
            else:
                if d.dissection_type in self.lookup_bc:
                    barcodes.append(f'{self.lookup_bc[d.dissection_type]} {d.dissection_barcode}')
                else:
                    barcodes.append(f'? {d.dissection_barcode}')
                    self._logger.error(f'Dissection type {d.dissection_type} could not be determined for this barcode.')



        self._logger.debug(f"Barcode string for {'Tags' if tag else 'Barcodes'} column: {barcodes}.")
        return '\n'.join(barcodes)
