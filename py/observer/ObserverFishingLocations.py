# -----------------------------------------------------------------------------
# Name:        FishingLocations.py
# Purpose:     Support class for FishingLocations
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     July 15, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from math import isclose
import logging
from typing import List  # Type hints

from PyQt5.QtCore import pyqtProperty, QVariant, QObject, pyqtSignal, pyqtSlot

from py.observer.ObserverDBUtil import ObserverDBUtil
from py.observer.FishingLocationsModel import FishingLocationsModel  # View model

# Imports for unit testing
import unittest
from py.observer.ObserverDBModels import *
from playhouse.apsw_ext import APSWDatabase
from playhouse.test_utils import test_database


# noinspection PyPep8Naming
class ObserverFishingLocations(QObject):
    modelChanged = pyqtSignal()
    locationChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._locations_model = FishingLocationsModel()
        self._current_location = None
        self._current_activity_id = None

    def load_fishing_locations(self, fishing_activity_id):
        """
        Load locations from database, build FramListModel
        """
        self._locations_model.clear()
        self._current_activity_id = fishing_activity_id
        locs_q = FishingLocations.select().where(FishingLocations.fishing_activity == fishing_activity_id)
        if len(locs_q) > 0:
            for loc in locs_q:  # Build FramListModel
                self._locations_model.add_location(loc)
        self.modelChanged.emit()

    @pyqtSlot(int, str, float, float, float)
    def update_location_by_id(self, loc_id, date, latitude, longitude, depth):

        try:
            location_item = FishingLocations.get((FishingLocations.fishing_location == loc_id))
            location_item.location_date = date
            location_item.latitude = latitude
            location_item.longitude = longitude
            location_item.depth = depth
            location_item.depth_um = 'FM'
            location_item.save()
            # Update location positions in DB and the view model to handle possible shift in position.
            self._update_location_positions()
            self._logger.debug('Location update DB id {loc_id} {date} {lat} {long} {depth}'.format(
                loc_id=loc_id, date=date, lat=latitude, long=longitude, depth=depth))

        except FishingLocations.DoesNotExist:
            self._logger.error('Could not find DB entry for location id {}'.format(loc_id))

    @pyqtSlot(int, str, float, float, float, result=int)
    def add_update_location(self, position, date, latitude, longitude, depth):  # depth_um assumed to be "ftm"
        return self.add_update_location_haul_id(self._current_activity_id, position, date, latitude, longitude, depth)

    @pyqtSlot(int, int, str, float, float, float, result=int)
    def add_update_location_haul_id(self, haul_id, position, date, latitude, longitude,
                                    depth):  # depth_um assumed to be "ftm"
        try:
            try:
                location_item = FishingLocations.get((FishingLocations.fishing_activity == haul_id) &
                                                     (FishingLocations.position == position))
                self._logger.debug(
                    'Fishing location haul ID={}, position={} found, updating.'.format(haul_id, position))
                location_item.location_date = date
                location_item.latitude = latitude
                location_item.longitude = longitude
                location_item.depth = depth
                location_item.depth_um = 'FM'
                location_item.position = position
                location_item.save()  # Update the database
                # Update location positions in DB and the view model to handle possible shift in position.
                self._update_location_positions()

            except FishingLocations.DoesNotExist:
                self._logger.debug(
                    'Create fishing location haul ID={}, position={}'.format(haul_id, position))
                user_id = ObserverDBUtil.get_current_user_id()
                location_item = FishingLocations.create(fishing_activity=haul_id,
                                                        location_date=date,
                                                        latitude=latitude,
                                                        longitude=longitude,
                                                        depth=depth,
                                                        depth_um='FM',
                                                        position=position,
                                                        created_by=user_id,
                                                        created_date=ObserverDBUtil.get_arrow_datestr())
                self._logger.debug('Fishing location position {} created.'.format(location_item.position))
                # New entry added, but position number sequence may be off, depending on datetime of new entry.
                # Update location positions in DB and the view model to handle possible insertion.
                self._update_location_positions()
        except Exception as e:
            self._logger.error(e)
        return location_item.fishing_location  ## Primary key index of location

    @pyqtSlot(int)
    def delete_location_by_position(self, position):
        try:
            try:
                haul_id = self._current_activity_id
                location_item = FishingLocations.get((FishingLocations.fishing_activity == haul_id) &
                                                     (FishingLocations.position == position))
                self._logger.debug(
                    'Fishing location haul ID={}, position={} found, deleting.'.format(haul_id, position))
                location_item.delete_instance(haul_id, position)  # DB
                # Update location positions in DB and the view model to fill a possible gap.
                self._update_location_positions()

            except FishingLocations.DoesNotExist:
                self._logger.error(
                    'Attempt to delete non-existent fishing location haul ID={}, position={}'.format(haul_id, position))
        except Exception as e:
            self._logger.error(e)

    def _get_gps_locations(self):  # Intended for internal use
        count = self._locations_model.count
        locs = []
        for i in range(count):
            locs.append({'pos': self._locations_model.get(i)['position'],
                         'lat': self._locations_model.get(i)['latitude'],
                         'long': self._locations_model.get(i)['longitude']})
        return locs

    @pyqtSlot(QVariant, QVariant, QVariant, result=bool, name='verifyNoMatchGPSPosition')
    def verify_no_match_gps_position(self, position, lat_degs, long_degs):
        if self._locations_model.count <= 0:
            return True  # Only have 0 or 1 location, can't clash with that.
        locs = self._get_gps_locations()

        for l in locs:
            self._logger.debug(f'Contemplate {position}  {lat_degs}  {long_degs} vs {l}')
            if l['pos'] != position and (isclose(l['lat'], lat_degs) or isclose(l['long'], long_degs)):
                self._logger.warning(f'Found close lat/long match {l}')
                return False
        return True  # Else, no matches

    @pyqtProperty(QVariant, notify=modelChanged)
    def CurrentFishingLocationsModel(self):
        return self._locations_model

    @pyqtProperty(QVariant, notify=locationChanged)
    def currentLocation(self):
        return self._current_location

    # TODO current (selected) location
    # _current_location
    def _set_cur_prop(self, property, value):
        """
        Helper function - set current haul properties in FramListModel
        @param property: property name
        @param value: value to store
        @return:
        """
        self._locations_model.setProperty(self._internal_haul_idx,
                                          property, value)

    @pyqtSlot(str, result='QVariant')
    def getData(self, data_name):
        """
        Shortcut to get data from the DB that doesn't deserve its own property
        (Note, tried to use a dict to simplify this, but DB cursors were not updating)
        :return: Value found in DB
        """
        if self._current_location is None:
            logging.warning('Attempt to get data with null current location.')
            return None
        data_name = data_name.lower()
        return_val = None
        if data_name == 'position':
            return_val = self._current_location.latitude
        else:
            logging.warning('Attempt to get unknown data name: {}'.format(data_name))

        return '' if return_val is None else return_val

    @pyqtSlot(str, QVariant)
    def setData(self, data_name, data_val):
        """
        Set misc data to the DB
        :return:
        """
        if self._current_location is None:
            logging.warning('Attempt to set data with null current location.')
            return
        data_name = data_name.lower()
        if data_name == 'latitude':
            self._current_location.latitude = float(data_val)
        else:
            logging.warning('Attempt to set unknown data name: {}'.format(data_name))
            return
        self._current_location.save()
        self._set_cur_prop(data_name, data_val)

        logging.debug('Set {} to {}'.format(data_name, data_val))
        self.modelChanged.emit()

    @staticmethod
    def _resequence_orm_location_positions(locations: List[FishingLocations]) -> List[FishingLocations]:
        """
        Given a list of peewee ORM FishingLocations, return a list sorted by arrow time,
        assigning position number from -1 to N-2:
        Conventions:
        - Earliest location, aka "Set" is assigned POSITION = -1
        - Latest location (in N > 1), aka "Up" is assigned POSITION 0
        - If additions locations, assign position from 0 to N-2, in ascending datetime order.
        - In case of exactly same datetime, use FISHING_LOCATION_ID as minor sort key.
        :param locations: List of Peewee ORM fishing locations with POSITION values possibly out of sequence due to a
            location being added or deleted.
        :return: List of fishing locations with POSITION set by datetime order given above.
            Note: neither SQLite FISHING_LOCATIONS table nor FishingLocationModel's model have been updated.
        """
        slocations = sorted(locations, key=lambda loc: " ".join([
            ObserverDBUtil.str_to_datetime(loc.location_date).format('DD/MM/YYYY HH:mm'),#'YMMDDHHmm'),
            str.format("{0:0>5}", loc.fishing_location)]))
        # Earliest
        if len(slocations) > 0:
            slocations[0].position = -1
        # Last
        if len(slocations) > 1:
            slocations[-1].position = 0
        # In-between
        if len(slocations) > 2:
            for i in range(1, len(slocations) - 1):
                slocations[i].position = i
        return slocations

    def _update_location_positions(self):
        """
        Acting upon both the OR model and view model of Fishing Locations,
        update the position number of all locations for this activity ID (haul)
        so that positions, sorted by datetime, are assigned the values -1, 1, 2, ... 0
        (yes, 0 is assigned to the most recent position, the "Up" position.

        Assumes that at most a few tens of locations are involved,
        so sort, clear and reloads need not be blindingly fast.

        :return: None
        """
        if (self._current_activity_id is None):
            logging.error("_update_location_positions called with null haul (activity) ID.")
            return

        logging.debug("Modifying entries for Haul #{} in FishingLocations table in database '{}' ...".format(
            self._current_activity_id, FishingLocations._meta.database.database))

        # TODO: Put these select, delete, and insert operations in a transaction.
        #       (Try#1: "with FishingLocations._meta.database:" jumped to Exception catch with "_exit_")

        # Get all the OR model locations for this haul
        locs = FishingLocations.select().where(FishingLocations.fishing_activity == self._current_activity_id)

        # Assign position number sorted by datetime
        locs_sorted = ObserverFishingLocations._resequence_orm_location_positions(locs)

        # Save (update) all the OR records
        # Position number must be unique within a haul.
        # To avoid non-unique position numbers on save, first delete all current entries for current haul.
        try:
            delete_query = FishingLocations.delete().where(
                FishingLocations.fishing_activity == self._current_activity_id)
            delete_query.execute()
            # Delete query should be faster than:
            # for loc in locs:
            #     loc.delete_instance()
        except Exception as e:
            logging.error("_update_location_positions: Delete of outdated locations failed with {}.".format(e))

        try:
            for loc_sorted in locs_sorted:
                # Force_insert: re-use each location's FISHING_LOCATION_ID primary key value
                loc_sorted.save(force_insert=True)
        except Exception as e:
            logging.error("_update_location_positions: save of updated location failed with {}.".format(e))

        # Force a reload of the view model - re-read from OR model.
        # Side-effect: Signals the ObserverTableView that locations have changed.
        self.load_fishing_locations(self._current_activity_id)


class TestOrmFishingLocationsModel(unittest.TestCase):
    """
    ObserverFishingLocations interacts with the OR model of FishingLocations in ObserverDBModels
    and with the view model FishingLocationsModels. This class tests interactions with the OR model.

    Note: any write/update interaction should be done with test_database...
    http://stackoverflow.com/questions/15982801/custom-sqlite-database-for-unit-tests-for-code-using-peewee-orm
    """

    def setUp(self):
        # TODO: Either phase out ObserverDB, or make it testable, as in ObserverDB(':memory:')
        # Tools available now are a Peewee test database context manager using an in-memory APSW database
        self.test_db = APSWDatabase(':memory:')
        self.test_tables = (
            Vessels,
            Users,
            Programs,
            Trips,
            FishingActivities,
            CatchCategories,
            FishingLocations,
        )
        self.test_vessel_id = 1
        self.test_user_id = 1
        self.test_program_id = 1
        self.test_category_id = 1
        self.test_activity_num = 1  # aka Haul

        # Only one test dataset of locations used in this test class.
        # Here are the expected position number assignments by primary key id:
        self.expected_position_assignments = {
            20: -1,  # Last-entered has earliest date
            19: 1,
            18: 2,
            17: 3,
            16: 4,
            15: 5,
            14: 6,
            13: 7,
            12: 8,
            11: 9,
            10: 10,
            9: 11,
            8: 12,
            7: 13,
            6: 14,
            5: 15,
            4: 16,
            3: 17,
            2: 18,
            1: 0,  # Location first entered has latest date
        }

        logging.basicConfig(level=logging.DEBUG)

        # Turn on peewee's SQL logging, if desired, by commenting out next two statements.
        pwlogger = logging.getLogger('peewee')
        pwlogger.setLevel(logging.WARNING)

        # Database initialization is done as part of each test, inside a context manager 'with' block.
        ##(not here)self._load_up_test_location_data()

    def tearDown(self):
        # Database teardown is done as part of the exit from the 'with' block.
        pass

    def _clear_existing_table_entries(self):
        """
        Not likely needed since each test creates its own test database, but just be on the safe side:
        """
        q = Vessels.delete()
        q.execute()
        q = Users.delete()
        q.execute()
        q = Programs.delete()
        q.execute()
        q = Trips.delete()
        q.execute()
        q = FishingActivities.delete()
        q.execute()
        q = CatchCategories.delete()
        q.execute()
        q = FishingLocations.delete()
        q.execute()

    def _create_foreign_table_entries_needed_by_locations(self):
        # From ObserverTrip.py _create_test_data()
        for t in range(3):
            Vessels.create(vessel=self.test_vessel_id + t, port=0, vessel_name='Test Vessel {}'.format(t))
            Users.create(user=self.test_user_id + t, first_name='User {}'.format(t), last_name='Last',
                         password='test', status=1)

        Programs.create(program=self.test_program_id, program_name='Test Program')

        vess = Vessels.select()
        for p in vess:
            print('Created {}'.format(p.vessel_name))

        users = Users.select()
        for u in users:
            print('Created {}'.format(u.first_name))

        p = Programs.get(Programs.program == self.test_program_id)
        test_vessel = Vessels.select().where(Vessels.vessel == self.test_vessel_id).get()
        test_program = Programs.select().where(Programs.program == self.test_program_id).get()
        self.assertIsNotNone(test_program)

        # Prerequisites for Haul (aka FishingActivity): trip, catch category
        # Trip
        a_trip = Trips.create(user=self.test_user_id, vessel=test_vessel, program=test_program,
                              partial_trip="F", trip_status="FALSE")
        self.test_trip_id = a_trip.trip

        # Catch Category
        a_catch_category = CatchCategories.create(catch_category=self.test_category_id,
                                                  catch_category_name='ccname',
                                                  catch_category_code='cc')

        # Finally - haul, which is explicitly required by location:
        self.a_haul = FishingActivities.create(trip=a_trip, fishing_activity_num=self.test_activity_num,
                                               data_quality=2)
        self.assertIsNotNone(self.a_haul)
        print("Created Haul#{}".format(self.a_haul.fishing_activity))
        print('Created Program#{} named {}'.format(p.program, p.program_name))

    def _create_test_location_set(self, haul_id):
        test_locations = []
        # Put in reverse date order, just so it isn't presented near the order desired.
        for n in reversed(range(20)):
            a_date = "11/10/2016 {:02d}:37".format(n)
            a_location = FishingLocations.create(fishing_activity=haul_id, location_date=a_date,
                                                 latitude=45 + n, longitude=123 + n, depth=60 + n, depth_um="ftm",
                                                 position=2 * (n - 2))  # Gaps in posn #s, some negative
            test_locations.append(a_location)
        return test_locations

    def _location_to_string(self, loc):
        return "ID:{0}, Haul:{1}, Date:{2}, Lat:{3}, Long:{4}, Depth:{5} {6}, Posn:{7}".format(
            loc.fishing_location, loc.fishing_activity.fishing_activity,
            loc.location_date, loc.latitude, loc.longitude, loc.depth, loc.depth_um, loc.position)

    def _load_up_test_location_data(self):
        self._clear_existing_table_entries()
        self._create_foreign_table_entries_needed_by_locations()
        test_locations = self._create_test_location_set(self.a_haul.fishing_activity)
        for test_location in test_locations:
            print(self._location_to_string(test_location))

    ##
    # End Setup. Begin Tests
    ##
    def test_query(self):
        """ Throat-clearing unit test demonstrating table data initialization is working."""
        with test_database(self.test_db, self.test_tables):
            self._load_up_test_location_data()
            t = Trips.get(Trips.trip == self.test_trip_id)
            u = Users.get(Users.user == t.user.user)
            print('Trip #{} found, captain={}.'.format(t.trip, u.user))
            self.assertEqual(self.test_user_id, t.user.user)

    def test_sort_locations_by_datetime(self):
        """
        Test that position numbers are re-assigned according to datetime sort order.
        Updates not written to test database.
        """
        n_expected = len(self.expected_position_assignments)
        with test_database(self.test_db, self.test_tables):
            self._load_up_test_location_data()
            locations = FishingLocations.select()
            self.assertEqual(n_expected, len(locations))
            # ----
            sorted_locations = ObserverFishingLocations._resequence_orm_location_positions(locations)
            # ----
            self.assertEqual(n_expected, len(sorted_locations))
            for sloc in sorted_locations:
                print("{0} {1} ({2:0>5})".format(sloc.position, sloc.location_date, sloc.fishing_location))
                self.assertEqual(self.expected_position_assignments[sloc.fishing_location], sloc.position)

    def test_locations_updated_in_database(self):
        """
        Test that position numbers are re-assigned according to datetime sort order.
        Updates tested are those written to test database.
        """
        n_expected = len(self.expected_position_assignments)

        with test_database(self.test_db, self.test_tables):
            self._load_up_test_location_data()
            fishing_locations = ObserverFishingLocations()
            fishing_locations.load_fishing_locations(self.test_activity_num)
            # ----
            fishing_locations._update_location_positions()
            # ----
            sorted_locations = FishingLocations.select().where(
                FishingLocations.fishing_activity == self.test_activity_num)
            self.assertEqual(n_expected, len(sorted_locations))
            for sloc in sorted_locations:
                print("{0} {1} ({2:0>5})".format(sloc.position, sloc.location_date, sloc.fishing_location))
                self.assertEqual(self.expected_position_assignments[sloc.fishing_location], sloc.position)


if __name__ == '__main__':
    unittest.main()
