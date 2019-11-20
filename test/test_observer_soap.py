import base64
import logging
import unittest

import arrow
from playhouse.apsw_ext import APSWDatabase
from playhouse.test_utils import test_database

from py.observer.ObserverDBSyncController import ObserverDBSyncController
from py.observer.ObserverSOAP import ObserverSoap
from py.observer.ObserverUsers import ObserverUsers


class TestObserverSOAP(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.soap = ObserverSoap()
        self.user = 'willsmith'
        self.unhashed_pw = ''  # DO NOT COMMIT PW
        self.hashed_pw = self.soap.hash_pw(self.user, self.unhashed_pw)
        
        self.test_db = APSWDatabase('../data/observer.db')

        self.dbsync = ObserverDBSyncController()
        self.test_trip_id = 1
        self.test_user_id = ObserverUsers.get_user_id(self.user)

    def test_get_pw(self):
        pw = self.soap._get_dbsync_pw()
        self.assertIsNotNone(pw)

    # @unittest.skip  # skip unless user and pw are valid
    def test_download(self):
        updates = self.soap.action_download(transaction_id=self.soap.default_transaction_id)
        self.assertIsNotNone(updates)
        # self.assertGreater(len(updates), 100)
        last = -1
        for r in updates:  # check sort order by trans id
            self.assertGreater(r['transaction_id'], last)
            last = r['transaction_id']
            print(r['transaction_ddl'])

    @unittest.skip
    def test_upload_fishing_locations(self):
        filename, csvdata = self.dbsync.generate_fishing_locations_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_upload_fishing_activities(self):
        filename, csvdata = self.dbsync.generate_fishing_activities_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_upload_catches(self):
        filename, csvdata = self.dbsync.generate_catches_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_species_compositions(self):
        filename, csvdata = self.dbsync.generate_speciescomp_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_species_compositions_items(self):
        filename, csvdata = self.dbsync.generate_speciescomp_items_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_species_compositions_baskets(self):
        filename, csvdata = self.dbsync.generate_speciescomp_baskets_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_catch_additional_baskets(self):
        filename, csvdata = self.dbsync.generate_catch_additional_baskets_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_bio_specimens(self):
        filename, csvdata = self.dbsync.generate_bio_specimens_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_bio_specimen_items(self):
        filename, csvdata = self.dbsync.generate_bio_specimen_items_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_upload_brd(self):
        """
        Not implemented in OPTECS...
        @return:
        """
        unenc_data = b'"BRD_ID","TRIP_ID","FISHING_ACTIVITY_ID","NOTES","CREATED_BY","CREATED_DATE",' \
                     b'"MODIFIED_BY","MODIFIED_DATE","DATA_SOURCE","ROW_STATUS","ROW_PROCESSED"\n' \
                     b'3571,16,"125536,125537","this is a test...",1761,12/29/2015 13:59,,,"psmfc6079brende",,'

        filename = self.soap.get_filename(tablename='BRD',
                                          trip_id=16,
                                          user_id=self.test_user_id)
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_fish_tickets(self):
        filename, csvdata = self.dbsync.generate_fish_tickets_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_upload_trip_certificates(self):
        # unenc_data = b'"TRIP_CERTIFICATE_ID","TRIP_ID","CERTIFICATE_NUMBER","CREATED_DATE","CREATED_BY",' \
        #              b'"MODIFIED_DATE","MODIFIED_BY","CERTIFICATION_ID","DATA_SOURCE","ROW_PROCESSED","ROW_STATUS"\n' \
        #              b'15269,15,"GF0002",12/29/2015 13:15,1761,12/29/2015 13:15,,,"psmfc6079brende",,\n'
        # filename = self.soap.get_filename(tablename='TRIP_CERTIFICATES',
        #                                   trip_id=39,
        #                                   user_id=self.test_user_id)
        filename, csvdata = self.dbsync.generate_trip_certificates_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_upload_dissections(self):
        unenc_data = b'"DISSECTION_ID","BIO_SPECIMEN_ITEM_ID","DISSECTION_TYPE","DISSECTION_BARCODE","CREATED_BY",' \
                     b'"CREATED_DATE","MODIFIED_BY","MODIFIED_DATE","RACK_ID","RACK_POSITION","BS_RESULT",' \
                     b'"CWT_CODE","CWT_STATUS","CWT_TYPE","AGE","AGE_READER","AGE_DATE","AGE_LOCATION",' \
                     b'"AGE_METHOD","BAND_ID","DATA_SOURCE","ROW_PROCESSED","ROW_STATUS"\n'
        # b'13109,141690,"1",123456789,1331,01/24/2017 09:18,,,,,,,,,,,,,,,"6084sheltondebo",,'
        filename, csvdata = self.dbsync.generate_dissections_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    @unittest.skip
    def test_upload_trips(self):
        filename, csvdata = self.dbsync.generate_trips_csv(self.test_trip_id, user_id=self.test_user_id)
        unenc_data = csvdata.encode('utf-8')
        updated, trip_id = self.soap.action_upload(self.user, self.hashed_pw, filename=filename, unenc_data=unenc_data)
        self.assertTrue(updated)

    def test_get_trip_id_from_result(self):
        test_strs = [(None, '<br>SUCCESS:  Parsed 1 SOMETHING row.'),
                     (None, None),
                     (30135,
                      '<br>SUCCESS:  Parsed 1 TRIPS row.<div style="font-size:2em;color:#990000">'
                      'Your Online Trip ID is <b>30135</b></div>. <br><div style="font-size:2em;'
                      'color:#006600">Online transfer complete.</div>'),
                     (12345,
                      '<br>SUCCESS:  Parsed 1 TRIPS row.<div style="font-size:2em;color:#990000">'
                      'Your Online Trip ID is <b>12345</b></div>. <br><div style="font-size:2em;'
                      'color:#006600">Online transfer complete.</div>'),
                     ]
        for expected, teststr in test_strs:
            self.assertEqual(expected, self.soap._get_trip_id_from_result(teststr))

    def test_get_filename(self):
        testdate = arrow.get('2017-01-01 23:00')
        testfilename = self.soap.get_filename(tablename='testing',
                                              trip_id=1234,
                                              user_id=4321,
                                              date_time=testdate)
        expected = 'TESTING#1234_4321_01JAN2017_2300.csv'
        self.assertEqual(testfilename, expected)
        currenttestdate = arrow.now().format('DDMMMYYYY_HHmm').upper()
        testfilename = self.soap.get_filename(tablename='testing',
                                              trip_id=1234,
                                              user_id=4321)
        expected = 'TESTING#1234_4321_{dt}.csv'.format(dt=currenttestdate)
        self.assertEqual(testfilename, expected)

    def test_pw_hash(self):
        testvals = [
            {'username': 'FAKEUSER',
             'pw': 'FakePw2344@#$#@:',
             'test_hashed_pw': '3947EC6D6FF9459399BC3A2B3AC6ED990B49B3CC'},
            {'username': 'OTHERFAKEUSER',
             'pw': 'FakePw2344@#$#@:',
             'test_hashed_pw': '4FD4CB5F08F1E1B3181EA47010BCF7C1A424F13A'},
            {'username': 'otherfakeuser',
             'pw': 'FakePw2344@#$#@:',
             'test_hashed_pw': '4FD4CB5F08F1E1B3181EA47010BCF7C1A424F13A'},
        ]
        self.assertRaises(ValueError, self.soap.hash_pw, None, 'badtest')
        self.assertRaises(ValueError, self.soap.hash_pw, 'badtest', None)
        for testval in testvals:
            hashed = self.soap.hash_pw(testval['username'], testval['pw'])
            self.assertEqual(hashed, testval['test_hashed_pw'])

    def test_remove_to_date(self):
        tests = (('asdf', 'asdf'),
                 ("'blah', TO_DATE('27-APR-17 12:25:36' ,'DD-MON-YY HH24:MI:SS')", "'blah', '27-APR-17 12:25:36' "),
                 ("BAD TO_DATE('27-APR-17 12:25:36' ,'DD-MON-YY HH24:MI:SS'",  # missing paren
                  "BAD TO_DATE('27-APR-17 12:25:36' ,'DD-MON-YY HH24:MI:SS'"))
        for test_in, test_out in tests:
            result = self.soap.remove_sql_to_date(test_in)
            self.assertEqual(result, test_out, 'Did not remove TO_DATE function')