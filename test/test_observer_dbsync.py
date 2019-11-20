import base64
import logging
import unittest

import arrow
from playhouse.apsw_ext import APSWDatabase
from playhouse.test_utils import test_database

from py.observer.ObserverDBModels import FishingActivities, Trips
from py.observer.ObserverDBSyncController import ObserverDBSyncController
from py.observer.ObserverSOAP import ObserverSoap


class TestObserverDBSync(unittest.TestCase):
    """
    Test CSV Generation (not actual syncing)
    """
    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.dbsync = ObserverDBSyncController()
        self.dbsync._initialize_soap_obj()
        self.test_trip_id = 1  # Change as appropriate in your DB for your testing
        self.test_user_id = 2027  # Change as appropriate in your DB for your testing

    def test_fishing_activities_csv(self):
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        haulfilename, hauls = self.dbsync.generate_fishing_activities_csv(trip_id, user_id=user_id)
        logging.info(hauls)
        self.assertIn('FISHING_ACTIVITIES#{}_{}'.format(trip_id, user_id), haulfilename)
        self.assertIn('"FISHING_ACTIVITY_ID","TRIP_ID","FISHING_ACTIVITY_NUM"', hauls)
        self.assertNotIn(',""', hauls)
        # 125755,23,1,100,"LB","1",,"2","1",,,,,,,1331,01/24/2017 12:45,,01/24/2017 12:45,1627,
        # ,,,,,,,,,,,,"6027mathersje",,,"2",,,"0"

    def test_fishing_locations_csv(self):
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        filename, locations = self.dbsync.generate_fishing_locations_csv(trip_id, user_id=user_id)
        logging.info(locations)
        self.assertIn('FISHING_LOCATIONS#{}_{}'.format(trip_id, user_id), filename)
        self.assertIn('"FISHING_LOCATION_ID","FISHING_ACTIVITY_ID","LOCATION_DATE"', locations)
        self.assertNotIn(',""', locations)

    def test_catches_csv(self):
        """
        @return:
        """
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        filename, catches = self.dbsync.generate_catches_csv(trip_id, user_id=user_id)
        logging.info(catches)
        self.assertIn('CATCHES#{}_{}'.format(trip_id, user_id), filename)
        self.assertIn('"CATCH_ID","FISHING_ACTIVITY_ID","CATCH_CATEGORY_ID"', catches)
        self.assertNotIn(',""', catches)
        # 659238,125755,1475,100,"LB",,"1","D",,"P",,,,,1,,1331,01/24/2017 12:47,,,,,,,,,,,,,,,,,,,,,"6027mathersje",,

    @unittest.skip
    def test_catches_nopurity_csv(self):
        """
        Semi-manual test, used to verify that CATCHES with CATCH_PURITY == NULL results in None data
        Note: trip_id should point to a trip with a "bad" catch
        """
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        filename, catches = self.dbsync.generate_catches_csv(trip_id, user_id=user_id)
        self.assertIn('CATCHES#{}_{}'.format(trip_id, user_id), filename)
        self.assertIsNone(catches)

    def test_speciescomp_csv(self):
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        filename, speciescomp = self.dbsync.generate_speciescomp_csv(trip_id, user_id=user_id)
        logging.info(speciescomp)
        self.assertIn('SPECIES_COMPOSITIONS#{}_{}'.format(trip_id, user_id), filename)
        self.assertIn('"SPECIES_COMPOSITION_ID","CATCH_ID","SAMPLE_METHOD"', speciescomp)
        self.assertNotIn(',""', speciescomp)

    def test_speciescomp_items_csv(self):
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        filename, speciescomp = self.dbsync.generate_speciescomp_items_csv(trip_id, user_id=user_id)
        logging.info(speciescomp)
        self.assertIn('SPECIES_COMPOSITION_ITEMS#{}_{}'.format(trip_id, user_id), filename)
        self.assertIn('"SPECIES_COMP_ITEM_ID","SPECIES_ID","SPECIES_COMPOSITION_ID"', speciescomp)
        self.assertNotIn(',""', speciescomp)

    def test_speciescomp_baskets_csv(self):
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        filename, speciescomp = self.dbsync.generate_speciescomp_baskets_csv(trip_id, user_id=user_id)
        logging.info(speciescomp)
        expected_field_count = 10
        for basket in filter(lambda b: len(b) > 0, speciescomp.split('\n')):  # get non-empty rows
            self.assertEqual(expected_field_count, len(basket.split(',')), 'Column count does not match expected')
        self.assertIn('SPECIES_COMPOSITION_BASKETS#{}_{}'.format(trip_id, user_id), filename)
        self.assertIn('"SPECIES_COMP_BASKET_ID","SPECIES_COMP_ITEM_ID",'
                      '"BASKET_WEIGHT_ITQ","FISH_NUMBER_ITQ"', speciescomp)
        self.assertNotIn(',""', speciescomp)
        self.assertNotIn('py.observer', speciescomp, "Class -> str conversion is bad")  # incorrect class to str

    def test_catch_additional_baskets_csv(self):
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        filename, catch_baskets = self.dbsync.generate_catch_additional_baskets_csv(trip_id, user_id=user_id)
        logging.info(catch_baskets)
        expected_field_count = 11
        for basket in filter(lambda b: len(b) > 0, catch_baskets.split('\n')):  # get non-empty rows
            self.assertEqual(expected_field_count, len(basket.split(',')), 'Column count does not match expected')
        self.assertIn('CATCH_ADDITIONAL_BASKETS#{}_{}'.format(trip_id, user_id), filename)
        self.assertIn('"CATCH_ADDTL_BASKETS_ID","CATCH_ID",'
                      '"BASKET_WEIGHT","CREATED_DATE"', catch_baskets)
        self.assertNotIn(',""', catch_baskets)
        self.assertNotIn('py.observer', catch_baskets, "Class -> str conversion is bad")  # incorrect class to str

    def test_bio_specimens_csv(self):
        # 126065,657651,10047,"7",,1331,01/09/2017 16:12,,,,,,,"13","6042-noaa-neil",,
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        filename, biospecimens = self.dbsync.generate_bio_specimens_csv(trip_id, user_id=user_id)
        logging.info(biospecimens)
        self.assertIn('BIO_SPECIMENS#{}_{}'.format(trip_id, user_id), filename)
        self.assertIn('"BIO_SPECIMEN_ID","CATCH_ID","SPECIES_ID","SAMPLE_METHOD"', biospecimens)
        self.assertNotIn(',""', biospecimens)

    def test_bio_specimen_items_csv(self):
        # 141617,126065,1.2,"LB",45,"CM",,,1331,01/09/2017 16:13,,,,,,,"6042-noaa-neil",,
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        filename, biospecimens = self.dbsync.generate_bio_specimen_items_csv(trip_id, user_id=user_id)
        logging.info(biospecimens)
        self.assertIn('BIO_SPECIMEN_ITEMS#{}_{}'.format(trip_id, user_id), filename)
        self.assertIn('"BIO_SPECIMEN_ITEM_ID","BIO_SPECIMEN_ID","SPECIMEN_WEIGHT"', biospecimens)
        self.assertNotIn(',""', biospecimens)

    def test_trip_certificates_csv(self):
        # 15269,11,"GF0008",01/14/2017 14:20,1621,01/14/2017 14:20,,,"psmfc6075lockto",,
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        filename, certs = self.dbsync.generate_trip_certificates_csv(trip_id, user_id=user_id)
        logging.info(certs)
        self.assertIn('TRIP_CERTIFICATES#{}_{}'.format(trip_id, user_id), filename)
        self.assertIn('"TRIP_CERTIFICATE_ID","TRIP_ID","CERTIFICATE_NUMBER"', certs)
        self.assertNotIn(',""', certs)

    def test_fish_tickets_csv(self):
        # 21205,"1234567",1331,01/23/2017 10:16,,,32,"C",01/23/2017 00:00,"psmfc6065stockm",,
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        filename, tickets = self.dbsync.generate_fish_tickets_csv(trip_id, user_id=user_id)
        logging.info(tickets)
        self.assertIn('FISH_TICKETS#{}_{}'.format(trip_id, user_id), filename)
        self.assertIn('"FISH_TICKET_ID","FISH_TICKET_NUMBER","CREATED_BY"', tickets)
        self.assertNotIn(',""', tickets)

    def test_trips_dissections_csv(self):
        # 13109,141690,"1",123456789,1331,01/24/2017 09:18,,,,,,,,,,,,,,,"6084sheltondebo",,
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        tripfilename, dissections = self.dbsync.generate_dissections_csv(trip_id, user_id=user_id)
        logging.info(dissections)
        if dissections:
            self.assertIn('DISSECTIONS#', tripfilename)
            self.assertIn('"DISSECTION_ID","BIO_SPECIMEN_ITEM_ID","DISSECTION_TYPE"', dissections)
            self.assertNotIn(',""', dissections)

    def test_trips_csv(self):
        trip_id = self.test_trip_id
        user_id = self.test_user_id
        tripfilename, trips = self.dbsync.generate_trips_csv(trip_id, user_id=user_id)
        logging.info(trips)
        self.assertIn('TRIPS#', tripfilename)
        self.assertIn('"TRIP_ID","VESSEL_ID","USER_ID"', trips)
        self.assertNotIn(',""', trips)
