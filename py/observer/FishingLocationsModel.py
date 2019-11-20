# -----------------------------------------------------------------------------
# Name:        FishTicketsModel.py
# Purpose:     Model for Fish Tickets
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     July 15, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import QVariant, pyqtSlot, pyqtProperty, pyqtSignal
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import FishingLocations
from playhouse.shortcuts import model_to_dict


class FishingLocationsModel(FramListModel):
    """
    Note: POSITION field is:
    -1 = Set
    0 = Up
    1,2,... = Additional Locations
    """

    modelChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._internal_trip_id = 0  # Current TRIP_ID

        for role_name in self.locations_rolenames:
            self.add_role_name(role_name)

    @property
    def locations_rolenames(self):
        """
        :return: role names for FramListModel
        """
        rolenames = FramUtil.get_model_props(FishingLocations)
        # Add additional roles (e.g. Vessel Name, to be acquired via FK)
        # rolenames.append('vessel_name')


        return rolenames

    @pyqtSlot(result=QVariant)
    def add_location(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        :return: FramListModel index of new ticket (int)
        """
        try:
            newlocation = self._get_locationdict(db_model)
            newidx = self.appendItem(newlocation)
            haul_id = db_model.fishing_activity.fishing_activity_num + 1  # Fishing Activities are 0-based
            self._logger.info(
                'Haul #{haul_id}, added location #{loc}/ position {pos}'.format(haul_id=haul_id,
                                                                                loc=newlocation['fishing_location'],
                                                                                pos=newlocation['position']))
            self.modelChanged.emit()
            return newidx

        except ValueError as e:
            self._logger.error('Error adding new location: {}'.format(e))
            return -1
        except Exception as e:
            self._logger.error('Critical Error adding location, did schema change? {}'.format(e))
            return -1

    @pyqtSlot(result=QVariant)
    def update_location(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        :return: FramListModel index of new ticket (int)
        """
        try:
            location = self._get_locationdict(db_model)
            # newidx = self.appendItem(location)
            update_idx = self.get_item_index('position', db_model.position)
            self.replace(update_idx, location)
            self._logger.info('Updated location #{}/ position {}'.
                              format(location['fishing_location'], location['position']))
            self.modelChanged.emit()
            return None
            # return newidx

        except ValueError as e:
            self._logger.error('Error updating location: {}'.format(e))
            return -1

    @pyqtSlot(str)
    def del_location(self, model_location_item):
        """
        :param model_location_item: location to delete
        """
        try:
            # TODO assert NOT position -1 or 0 (set and up),
            # or not, depending on user preference on whether "Set" or "Up" can be deleted.
            location_idx = self. get_item_index('position', model_location_item.position)
            self.remove(location_idx)
            self.modelChanged.emit()

        except ValueError as e:
            self._logger.error('Error Deleting ticket: {}'.format(e))

    def _get_locationdict(self, db_model):
        """
        Build a dict that matches FishTickets out of a peewee model
        Purpose is for storing peewee model <-> FramListModel
        :param db_model: peewee model to convert
        :return: dict with values translated as desired to be FramListModel friendly
        """
        locationdict = model_to_dict(db_model)

        # Example for keys that we want to rename from model-> dict:
        # tripdict['renamed'] = tripdict.pop('rename_me')

        # Populate "extra" keys if needed
        # ticketdict['vessel_name'] = db_model.vessel.vessel_name
        return locationdict
