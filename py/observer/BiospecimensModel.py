# -----------------------------------------------------------------------------
# Name:        BiospecimensModel.py
# Purpose:     Model for Biospecimens for Species (Observer)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     July 11, 2016
# License:     MIT
# ------------------------------------------------------------------------------
import logging

from PyQt5.QtCore import QVariant, pyqtSlot, pyqtProperty

from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import BioSpecimens


class BiospecimensModel(FramListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        for role_name in self.model_props:
            self.add_role_name(role_name)

    @property
    def model_props(self):
        props = FramUtil.get_model_props(BioSpecimens)
        props.append('species_name')  # Get from FK
        return props

    @pyqtProperty(int)
    def newest_specimen_id(self):
        pass

    @pyqtProperty(int)
    def newest_specimen_index(self):
        pass

    @pyqtSlot(result=int)
    def add_specimen(self):
        """
        :return: ID of new specimen (int)
        """
        #populate species_name
        pass

    @pyqtSlot(QVariant, result=bool)
    def remove_specimen(self, specimen_id):
        """
        :param specimen_id: ID of specimen (int) to axe
        """
        pass

    @pyqtSlot(QVariant, result=dict)
    def get_specimen_index(self, specimen_id):
        return self.get_item_index('specimen_id', specimen_id)

    @pyqtSlot(QVariant, QVariant, QVariant, result=bool)
    def set_specimen_value(self, specimen_id, value_name, value):
        """
        :param specimen_id: ID of specimen (int)
        :param value_name: name of value (e.g. 'weight_kg')
        :param value: value to set
        """
        logging.error('biospecimens set_specimen_value not implemented')
        pass
        # if value_name == 'species_id' or value_name not in self.specimen_rolenames:
        #     self._logger.error('set_specimen_value: unknown value_name ' + str(value_name))
        #     return False
        # try:
        #     specimen_id = int(specimen_id)
        #     self._logger.debug('Set specimen #' + str(specimen_id) + ' ' + value_name + ': ' + str(value))
        #     bidx = self.get_item_index('specimen_id', specimen_id)
        #     if -1 != bidx:
        #         self.setProperty(bidx, value_name, value)
        #     else:
        #         raise ValueError('Specimen ID does not exist: ' + str(specimen_id))
        #
        #     return True
        # except ValueError as e:
        #     self._logger.error('set_specimen_value: Error setting value: ' + str(e))
        #     return False
