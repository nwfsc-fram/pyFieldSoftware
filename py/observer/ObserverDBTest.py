from playhouse.apsw_ext import APSWDatabase
from playhouse.test_utils import test_database
from py.observer.ObserverDBBaseModel import connect_orm, close_orm
from py.observer.ObserverDBModels import *
import logging
import unittest

# test_database info from:
# http://stackoverflow.com/questions/15982801/custom-sqlite-database-for-unit-tests-for-code-using-peewee-orm


class TestORMTempDB(unittest.TestCase):
    """
    Uses a temporary in-memory DB, so changes won't touch actual DB
    """

    test_db = APSWDatabase(':memory:')

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def create_test_data(self):
        # Only call this within a with test_database block
        # Uses bogus values for required fields - would fail trip checks at Center.
        for i in range(10):
            Trips.create(trip=i, partial_trip='X', program=1, trip_status='X', user=1, vessel=1)

        for i in range(100, 110):
            FishingActivities.create(fishing_activity=i, fishing_activity_num=i + 1, data_quality='X',
                                     trip=1)

    def test_fakedb_select(self):
        with test_database(self.test_db, [FishingActivities, Trips, Settings]):
            self.create_test_data()
            query = FishingActivities.select().where(FishingActivities.fishing_activity == 105)
            self.assertGreater(len(query), 0)
            for q in query:
                logging.debug(str(q.fishing_activity) + ': ' + str(q.fishing_activity_num))
                self.assertGreater(int(q.fishing_activity_num), int(q.fishing_activity))

    def test_settings_get(self):

        with test_database(self.test_db, [Settings]):
            Settings.create(parameter='first_run', value='FALSE')

            fr = Settings.get(Settings.parameter == 'first_run')
            logging.info(fr)
            self.assertEqual(fr.value.lower(), 'false')

    def test_settings_set(self):

        with test_database(self.test_db, [Settings]):
            Settings.create(parameter='first_run', value='FALSE')

            fr = Settings.get(Settings.parameter == 'first_run')
            fr.value = 'TRUE'
            fr.save()

            fr2 = Settings.get(Settings.parameter == 'first_run')
            self.assertNotEqual(fr2.value.lower(), 'false')


class TestORMExistingData(unittest.TestCase):
    """
    Uses the ACTUAL observer database, so not making any permanent writes
    """

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        connect_orm()

    def tearDown(self):
        close_orm()

    def test_lookups(self):
        beaufort = Lookups.select().where(Lookups.lookup_type == 'BEAUFORT_VALUE')
        self.assertGreaterEqual(len(beaufort), 10)
        for b in beaufort:
            self.assertGreater(len(b.description), 0)

    @unittest.skip("Needed: define foreign key for join")
    def test_join(self):
        query = (Lookups
                 .select(Lookups, Users)
                 .join(Users)  # Needs defined foreign key
                 .where(Lookups.lookup_type == 'BEAUFORT_VALUE'))  # and Lookups.created_by == Users.user))
        self.assertGreaterEqual(len(query), 10)
        for q in query:
            logging.debug(q.created_by.first_name + ' ' +
                          q.created_by.last_name + ' created ' + str(q.description))
