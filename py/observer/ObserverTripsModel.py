__author__ = 'Will.Smith'
# -----------------------------------------------------------------------------
# Name:        ObserverTripsModel.py
# Purpose:     Model for Trips
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     March 14, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import QVariant, pyqtSlot, pyqtProperty, pyqtSignal
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import Trips
from playhouse.shortcuts import model_to_dict


class TripsModel(FramListModel):
    modelChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._internal_trip_id = 0  # Current TRIP_ID

        for role_name in self.trip_rolenames:
            self.add_role_name(role_name)

    @property
    def trip_rolenames(self):
        """
        :return: role names for FramListModel
        """
        rolenames = FramUtil.get_model_props(Trips)
        # Add additional roles (e.g. Vessel Name, to be acquired via FK)
        rolenames.append('user_name')
        rolenames.append('vessel_name')
        rolenames.append('vessel_id')
        return rolenames

    @pyqtSlot(result=str)
    def add_trip(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere (in ObserverTrip)
        :return: FramListModel index of new trip (int)
        """
        try:
            newtrip = self._get_tripdict(db_model)
            newidx = self.appendItem(newtrip)
            self._logger.info('Added trip #{}'.format(newtrip['trip']))
            self.modelChanged.emit()
            return newidx

        except ValueError as e:
            self._logger.error('Error adding new trip: {}'.format(e))
            return -1

    def _get_tripdict(self, db_model):
        """
        Build a dict that matches TripsModel out of a peewee model
        Purpose is for storing peewee model <-> FramListModel
        :param db_model: peewee model to convert
        :return: dict with values translated as desired to be FramListModel friendly
        """
        tripdict = model_to_dict(db_model)

        # Example for keys that we want to rename from model-> dict:
        # tripdict['renamed'] = tripdict.pop('rename_me')

        # Populate "extra" keys, as declared in trip_rolenames
        try:
            tripdict['user_name'] = db_model.user.first_name + ' ' + db_model.user.last_name
            tripdict['vessel_name'] = db_model.vessel.vessel_name
            tripdict['vessel_id'] = int(db_model.vessel.vessel)
        except Exception as e:  # thrown if vessel not defined yet
            tripdict['vessel_name'] = ''
            tripdict['vessel_id'] = None
        return tripdict
