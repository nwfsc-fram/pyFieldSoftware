__author__ = 'Will.Smith'
# -----------------------------------------------------------------------------
# Name:        TripCertsModel.py
# Purpose:     Model for Trips
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     June 30, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import QVariant, pyqtSlot, pyqtProperty, pyqtSignal
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import Trips, TripCertificates
from playhouse.shortcuts import model_to_dict


class TripCertsModel(FramListModel):
    modelChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        for role_name in self.cert_rolenames:
            self.add_role_name(role_name)

    @property
    def cert_rolenames(self):
        """
        :return: role names for FramListModel
        """
        rolenames = FramUtil.get_model_props(TripCertificates)
        # Add additional roles (e.g. Vessel Name, to be acquired via FK)
        return rolenames

    @pyqtSlot(result=str)
    def add_cert(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        :return: FramListModel index of new cert (int)
        """
        try:
            newcert = self._get_certdict(db_model)
            newidx = self.appendItem(newcert)
            self._logger.info('Added cert #{}'.format(newcert['certificate_number']))
            self.modelChanged.emit()
            return newidx

        except ValueError as e:
            self._logger.error('Error adding new cert: {}'.format(e))
            return -1

    @pyqtSlot(str)
    def del_cert(self, cert_num):
        """
        :param cert_num: cert # to delete
        """
        try:

            idx = self.get_item_index('certificate_number', cert_num)
            self.remove(idx)
            self.modelChanged.emit()

        except ValueError as e:
            self._logger.error('Error Deleting cert: {}'.format(e))

    def _get_certdict(self, db_model):
        """
        Build a dict that matches TripCertificates out of a peewee model
        Purpose is for storing peewee model <-> FramListModel
        :param db_model: peewee model to convert
        :return: dict with values translated as desired to be FramListModel friendly
        """
        certdict = model_to_dict(db_model)

        # Example for keys that we want to rename from model-> dict:
        # tripdict['renamed'] = tripdict.pop('rename_me')

        # Populate "extra" keys if needed
        # certdict['vessel_name'] = db_model.vessel.vessel_name
        return certdict
