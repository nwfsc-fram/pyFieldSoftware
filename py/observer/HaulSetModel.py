# -----------------------------------------------------------------------------
# Name:        HaulsModel.py
# Purpose:     Model for Hauls and Sets (Observer)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Feb 24, 2016
# License:     MIT
# ------------------------------------------------------------------------------


import textwrap

from playhouse.shortcuts import model_to_dict
from PyQt5.QtCore import pyqtSlot

from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import FishingActivities, FishingLocations


class HaulSetModel(FramListModel):
    """
    Contains multiple FishingActivities
    """

    GEAR_TYPE_TRAWL = "Trawl"
    GEAR_TYPE_FIXED_GEAR = "Fixed Gear"

    def __init__(self, parent=None):
        super().__init__(parent)
        for role_name in self.haul_set_rolenames:
            self.add_role_name(role_name)

    @property
    def haul_set_rolenames(self):
        """
        :return:
        """
        rolenames = FramUtil.get_model_props(FishingActivities)
        # Add additional roles not specified in DB (e.g. Vessel Name, to be acquired via FK)
        rolenames.append('trip_id')
        rolenames.append('target_strategy_code')
        rolenames.append('location_start_end')
        rolenames.append('errors')
        return rolenames

    def most_recent_haul_set_id(self):
        """
        Get empty haul if empty, or newest haul in the list
        Useful for deletions
        TODO db ID instead?
        :return: string '-1' if no hauls, haul_id otherwise
        """
        if self.count == 0:
            return '-1'
        else:
            lastitem = self.items[-1]
            return lastitem['fishing_activity_num']

    def add_haul(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere (in Hauls)
        :return: FramListModel index of new trip (int)
        """
        try:
            newhaul = self._get_haul_set_dict(db_model)
            newidx = self.appendItem(newhaul)
            self._logger.debug('Added haul #' + str(newhaul['fishing_activity_num']))
            return newidx

        except ValueError as e:
            self._logger.error('Error adding new haul ' + str(e))
            return -1

    def add_set(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere (in Hauls)
        :return: FramListModel index of new trip (int)
        """
        try:
            newset = self._get_haul_set_dict(db_model)
            newidx = self.appendItem(newset)
            self._logger.debug('Added set #' + str(newset['fishing_activity_num']))
            return newidx

        except ValueError as e:
            self._logger.error('Error adding new set ' + str(e))
            return -1

    def remove_haul_set(self, activity_id):
        """
        :param activity_id: ID of haul or set (int) to axe
        """
        try:
            # Delete from FramListModel
            model_idx = self.get_item_index('fishing_activity', activity_id)
            if model_idx >= 0:
                self.remove(model_idx)
                return True
            else:
                self._logger.error('Unable to find and remove haul/set {} from model.'.format(activity_id))
        except ValueError as e:
            self._logger.error('Error deleting haul/set: ' + str(e))
        return False

    def get_fishing_num_index(self, fishing_num):
        return self.get_item_index('fishing_activity_num', fishing_num)

    def get_haul_set_index(self, activity_id):
        return self.get_item_index('fishing_activity', activity_id)

    def _get_haul_set_dict(self, db_model):
        """
        Build a dict that matches HaulsModel out of a peewee model
        Purpose is for storing peewee model <-> FramListModel
        :param db_model: peewee model to convert
        :return: dict with values translated as desired to be FramListModel friendly
        """
        haul_set_dict = model_to_dict(db_model)

        # Rename from model-> dict:
        # hauldict['new_thing'] = hauldict.pop('old_thing')
        # Add ID's for reference, if needed...
        # hauldict['trip_id'] = db_model.trip.trip
        haul_set_dict['target_strategy_code'] = \
            db_model.target_strategy.catch_category_code if db_model.target_strategy else None
        start, end = self._get_haul_set_start_end(db_model.fishing_activity)
        haul_set_dict['location_start_end'] = textwrap.fill('{} to {}'.format(start, end), width=20)
        haul_set_dict['errors'] = ''

        return haul_set_dict

    @pyqtSlot(int, result='QVariant', name='getLocationData')
    def get_location_data(self, activity_id):
        """
        Get Set/Up/Location info
        @param activity_id: DB ID
        @return: 2D Array built from Set/Up/# locations
        """
        self._logger.info('Loading FishingLocationsModel for haul ID {}'.format(activity_id))
        location_data_var = []
        locs_q = FishingLocations.select().where(FishingLocations.fishing_activity == activity_id)
        if len(locs_q) > 0:
            for loc in locs_q:  # Build FramListModel
                date_str, time_str = loc.location_date.split(' ')
                lat_deg, lat_min = FramUtil.convert_decimal_degs(loc.latitude)
                long_deg, long_min = FramUtil.convert_decimal_degs(loc.longitude)
                location_data_var.append({
                    'haul_db_id': loc.fishing_activity.fishing_activity,  # id
                    'loc_id': loc.fishing_location,
                    'position': loc.position,  # position -1, 0, ... (Set, Up, etc)
                    'date_str': date_str,
                    'time_str': time_str,
                    'lat_deg': lat_deg,
                    'lat_min': lat_min,
                    'long_deg': long_deg,
                    'long_min': long_min,
                    'depth': loc.depth
                })

        return location_data_var

    def _get_haul_set_start_end(self, activity_id):
        # locs_q = FishingLocations.select().where(FishingLocations.fishing_activity == haul_id)

        start_loc = self.get_loc_set(activity_id)
        end_loc = self.get_loc_up(activity_id)
        set_str = '{}'.format(start_loc.location_date) if start_loc else '-'
        # FIELD-846, use start date if no end date
        up_str = '{}'.format(end_loc.location_date) \
            if end_loc else ('({})'.format(set_str) if start_loc else '-')
        return set_str, up_str

    @staticmethod
    def _get_haul_set_loc(activity_id, position):
        try:
            loc = FishingLocations.get(FishingLocations.fishing_activity == activity_id,
                                       FishingLocations.position == position)
        except FishingLocations.DoesNotExist:
            loc = None
        return loc

    @pyqtSlot(int, result='QVariant', name='getLocationSet')
    def get_loc_set(self, haul_id):  # start of haul
        return self._get_haul_set_loc(haul_id, -1)

    @pyqtSlot(int, result='QVariant', name='getLocationUp')
    def get_loc_up(self, haul_id):  # end of haul
        return self._get_haul_set_loc(haul_id, 0)
