# -----------------------------------------------------------------------------
# Name:        ObserverData.py
# Purpose:     Observer Database routines
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan - July, 2016
# License:     MIT
# ------------------------------------------------------------------------------

# Python implementation of Observer data class
from operator import itemgetter

from PyQt5.QtCore import pyqtProperty, QObject, QVariant

from py.observer.ObserverDBUtil import ObserverDBUtil

from py.observer.ObserverDBModels import Lookups, Users, Vessels, \
    Programs, Contacts, VesselContacts, Ports, CatchCategories, IfqDealers, Species

from py.observer.ObserverUsers import ObserverUsers

import logging
import unittest


class ObserverData(QObject):
    """
    Handles details of various Observer data
    (from database, etc)
    """

    # A special MIX species for use within OPTECS.
    # Used to divert MIX baskets, which are unspeciated, to CATCH_ADDITIONAL_BASKETS rather than
    # SPECIES_COMPOSITION_BASKETS.
    MIX_PACFIN_CODE = 'MIX'
    MIX_SPECIES_CODE = 99999

    def __init__(self):
        super(ObserverData, self).__init__()
        self._logger = logging.getLogger(__name__)

        self._observers = None
        self._observers_keys = None
        self._vessels = None
        self._lookup_fisheries = None  # Fisheries in LOOKUPS table - purpose unclear
        self._captains = None  # Skippers
        self._captain_vessel_id = None
        self._ports = None
        self._catch_categories = None
        self._trawl_gear_types = None
        self._fg_gear_types = None
        self._first_receivers = None
        self._species = None

        self._lookups = None

        # Get data tables
        self._get_observers_orm()
        self._get_vessels_orm()
        self._get_captains_orm()
        self._get_ports_orm()
        self._get_catch_categories_orm()
        self._get_first_receivers_orm()
        self._get_species_orm()

        # Data from LOOKUPS table
        self._get_lookups_orm()
        self._weightmethods = self._build_lookup_data('WEIGHT_METHOD')
        self._sc_samplemethods = self._build_lookup_data('SC_SAMPLE_METHOD')
        self._discardreasons = self._build_lookup_data('DISCARD_REASON', values_in_text=False)
        self._vesseltypes = self._build_lookup_data('VESSEL_TYPE')

        self._beaufort = self._get_beaufort_dict()
        self._gearperf = self._get_gearperf_trawl_dict()
        self._gearperf_fg = self._get_gearperf_fg_dict()

        self._trawl_gear_types = self._get_trawl_gear_list()  # Single field, key + desc concatenated
        self._fg_gear_types = self._get_fg_gear_list()  # Single field, key + desc concatenated
        self._soaktimes = self._get_avg_soaktimes_list()
        self._bs_samplemethods = sorted(self._list_lookup_desc('BS_SAMPLE_METHOD', values_in_text=True))
        self._vessellogbooknames = self._list_lookup_desc('VESSEL_LOGBOOK_NAME')

        self._create_mix_species_if_not_present()

    def _create_mix_species_if_not_present(self):
        """
        Check SPECIES table for 'MIX' pacfin code, if not there, create it.
        Scientific name, commmon name, and PacFIN code are all 'MIX'.
        Species ID and species code are both 99999.
        """
        current_user_id = ObserverDBUtil.get_current_user_id()
        created_date = ObserverDBUtil.get_arrow_datestr(date_format=ObserverDBUtil.oracle_date_format)
        mix_species_info = {
            'species': ObserverData.MIX_SPECIES_CODE,
            'scientific_name': ObserverData.MIX_PACFIN_CODE,
            'common_name': ObserverData.MIX_PACFIN_CODE,
            'species_code': ObserverData.MIX_SPECIES_CODE,
            'pacfin_code': ObserverData.MIX_PACFIN_CODE,
            'created_by': current_user_id if current_user_id else 1,
            'created_date': created_date,
        }
        try:
            Species.get(Species.pacfin_code == 'MIX')
            self._logger.info('MIX exists in SPECIES table.')
        except Species.DoesNotExist:
            self._logger.info('Adding MIX to SPECIES table (one-time operation)')
            Species.create(**mix_species_info)

    @staticmethod
    def make_username(user_model):
        return user_model.first_name + ' ' + user_model.last_name

    def _get_observers_orm(self, rebuild=False):
        """
        Get observers from database via ORM, store DB keys
        """
        if self._observers is not None and not rebuild:  # only build this once
            return
        self._observers = list()
        self._observers_keys = dict()

        obs_q = Users.select()
        for obs in obs_q:
            username = self.make_username(obs)
            self._observers.append(username)
            self._observers_keys[username] = obs
        self._observers = sorted(self._observers)  # Sort Alphabetically - should we do this by last name instead?

    def _get_vessels_orm(self, rebuild=False):
        """
        Get vessels from database via ORM, store DB keys
        """
        if self._vessels is not None and not rebuild:  # only build this once
            return

        self._vessels = list()

        vess_q = Vessels.select()
        for vessel in vess_q:
            vessel_number = vessel.coast_guard_number
            if not vessel_number or len(vessel_number) < 1:
                vessel_number = vessel.state_reg_number
            vessel_entry = '{} - {}'.format(vessel.vessel_name.upper(), vessel_number)
            self._vessels.append(vessel_entry)
        self._vessels = sorted(self._vessels)  # Don't Remove Duplicates + Sort Alphabetically

    def _get_programs_orm(self, rebuild=False):
        """
        Get programs from database via ORM, store DB keys
        """
        if self._programs is not None and not rebuild:  # only build this once
            return

        self._programs = list()

        fish_q = Programs.select()
        for fishery in fish_q:
            self._programs.append(fishery.program_name)
        self._programs = sorted(set(self._programs))  # Remove Duplicates + Sort Alphabetically

    def _get_captains_orm(self, rebuild=False):
        """
        Get skippers from database via ORM, store DB keys
        """
        if self._captains is not None and not rebuild:  # only build this once
            return

        self._captains = list()

        if self._captain_vessel_id:
            captains_q = Contacts.select(). \
                join(VesselContacts, on=(Contacts.contact == VesselContacts.contact)). \
                where(
                (Contacts.contact_category == 3) &  # Vessel category
                (VesselContacts.contact_status != 'NA') &
                (VesselContacts.vessel == self._captain_vessel_id) &  # Vessel ID
                ((VesselContacts.contact_type == 1) |  # Skipper
                 (VesselContacts.contact_type == 3)))  # Skipper/ Owner
        else:
            captains_q = Contacts.select(). \
                join(VesselContacts, on=(Contacts.contact == VesselContacts.contact)). \
                where(
                (VesselContacts.contact_status != 'NA') &
                (Contacts.contact_category == 3) &  # Vessel
                ((VesselContacts.contact_type == 1) |  # Skipper
                 (VesselContacts.contact_type == 3)))  # Skipper/ Owner

        for captain in captains_q:
            if len(captain.first_name) > 0:
                self._captains.append(captain.first_name + ' ' + captain.last_name)
        self._captains = sorted(set(self._captains))  # Remove Duplicates + Sort Alphabetically

    def _get_first_receivers_orm(self, rebuild=False):
        """
        Get first receivers from database via ORM, store DB keys
        @return: dict of values and PK
        """
        if self._first_receivers is not None and not rebuild:  # only build this once
            return

        self._first_receivers = list()

        fr_q = IfqDealers. \
            select(IfqDealers, Ports). \
            join(Ports, on=(IfqDealers.port_code == Ports.ifq_port_code).alias('port')). \
            where(IfqDealers.active == 1)

        for fr in fr_q:
            fr_line = '{} {}'.format(fr.dealer_name, fr.port.port_name)
            # self._logger.info(fr_line)
            self._first_receivers.append(fr_line)

        self._first_receivers = sorted(self._first_receivers)

    def _get_catch_categories_orm(self, rebuild=False):
        """
        To support autocomplete, get catch categories from database via ORM, store DB keys
        """
        if self._catch_categories is not None and not rebuild:  # only build this once
            return

        self._catch_categories = list()

        catch_q = CatchCategories.select().where(CatchCategories.active.is_null(True))

        for cc in catch_q:
            self._catch_categories.append('{} {}'.format(cc.catch_category_code, cc.catch_category_name))
        self._catch_categories = sorted(self._catch_categories)  # Sort Alphabetically

    def _get_ports_orm(self, rebuild=False):
        """
        Get ports from database via ORM, store DB keys
        """
        if self._ports is not None and not rebuild:  # only build this once
            return

        self._ports = list()

        port_q = Ports.select()
        for port in port_q:
            self._ports.append(port.port_name.title())  # Title case
        self._ports = sorted(set(self._ports))  # Remove Duplicates + Sort Alphabetically

    def _get_species_orm(self, rebuild=False):
        """
        To support autocomplete, get catch categories from database via ORM, store DB keys
        """
        if self._species is not None and not rebuild:  # only build this once
            return

        self._species = list()

        species_q = Species.select().where(Species.active.is_null(True))

        for s in species_q:
            self._species.append('{}'.format(s.common_name))
        self._species = sorted(self._species)  # Sort Alphabetically

    def get_observer_id(self, observer_name):
        if observer_name in self._observers_keys:
            return self._observers_keys[observer_name].user  # USER_ID
        else:
            return None

    def get_observer_name(self, observer_id):
        obs = Users.get(Users.user == observer_id)
        return self.make_username(obs)

    @pyqtProperty(QVariant)
    def catch_categories(self):  # for autocomplete
        return self._catchcategories

    @pyqtProperty(QVariant)
    def observers(self):
        return self._observers

    @pyqtProperty(QVariant)
    def vessels(self):
        return self._vessels

    @pyqtProperty(QVariant)
    def vessel_logbook_names(self):
        return self._vessellogbooknames

    @property
    def weight_methods(self):
        return self._weightmethods

    @property
    def sc_sample_methods(self):
        return self._sc_samplemethods

    @property
    def species(self):
        return self._species

    @property
    def bs_sample_methods(self):
        return self._bs_samplemethods

    @property
    def vessel_types(self):
        return self._vesseltypes

    @property
    def discard_reasons(self):
        return self._discardreasons

    @property
    def catch_categories(self):  # For AutoComplete
        return self._catch_categories

    @property
    def trawl_gear_types(self):  # For AutoComplete
        return self._trawl_gear_types

    @property
    def fg_gear_types(self):  # For AutoComplete
        return self._fg_gear_types

    @property
    def beaufort(self):
        return self._beaufort

    @property
    def soaktimes(self):
        return self._soaktimes

    @property
    def gearperf(self):
        return self._gearperf

    @property
    def gearperf_fg(self):
        return self._gearperf_fg

    @property
    def first_receivers(self):
        return self._first_receivers

    @staticmethod
    def get_fisheries_by_program_id(program_id, is_fg):
        return ObserverUsers.get_fisheries_by_program_id(program_id, is_fg)

    def _get_lookups_orm(self, rebuild=False):
        """
        Get lookups via peewee ORM
        :return:
        """
        if self._lookups is not None and not rebuild:  # only build this once unless rebuilt
            return

        self._lookups = dict()  # of lists

        # http://peewee.readthedocs.org/en/latest/peewee/querying.html#query-operators
        lookups_q = Lookups.select().where((Lookups.active >> None) | (Lookups.active == 1))
        for lu in lookups_q:
            key = lu.lookup_type
            if key in self._lookups:
                self._lookups[key].append({'desc': lu.description, 'value': lu.lookup_value})
            else:
                self._lookups[key] = [{'desc': lu.description, 'value': lu.lookup_value}]

        if len(self._lookups) == 0:
            raise ConnectionError('Unable to get LOOKUPS from database, check observer DB')

        # Build fisheries list
        self._lookup_fisheries = list()
        for fishery in self._lookups['FISHERY']:
            self._lookup_fisheries.append(fishery['desc'])
        self._lookup_fisheries = sorted(self._lookup_fisheries)

    @pyqtProperty(QVariant)
    def lookup_fisheries(self):
        return self._lookup_fisheries

    @pyqtProperty(QVariant)
    def fisheries(self):  # TODO do we want these or the lookup table entries?
        return self._programs

    @pyqtProperty(QVariant)
    def captains(self):
        return self._captains

    @pyqtProperty(QVariant)
    def captain_vessel_id(self):
        return self._captain_vessel_id

    @captain_vessel_id.setter
    def captain_vessel_id(self, vessel_id):
        self._logger.debug(f'Set Captain Vessel ID to {vessel_id}')
        if vessel_id != self._captain_vessel_id:
            self._captain_vessel_id = vessel_id
            self._get_captains_orm(rebuild=True)

    @pyqtProperty(QVariant)
    def ports(self):
        return self._ports

    def _build_lookup_data(self, lookup_type, include_empty=True, values_in_text=True):
        """
        Get values and descriptions from LOOKUPS
        :param lookup_type: primary name of lookup
        :param include_empty: include an extra empty item, useful for combo box with no default
        :param values_in_text: include the value in the text descriptions returned
        :return: list of dicts of the format [{'text': 'asf', 'value' 'somedata'}]
        """
        if self._lookups is None:
            self._get_lookups_orm()

        lookupdata = list()
        if include_empty:
            lookupdata.append({'text': '-', 'value': '-1'})  # Create empty selection option

        for data in self._lookups[lookup_type]:
            if values_in_text:
                lookupdata.append({'text': data['value'].zfill(2) + ' ' + data['desc'],  # zfill for 0-padding
                                   'value': data['value']})
            else:
                lookupdata.append({'text': data['desc'],
                                   'value': data['value']})

        lookupdata = sorted(lookupdata, key=itemgetter('text'))  # Sort Alphabetically
        return lookupdata

    def _get_beaufort_dict(self):
        """
        Build beaufort description dict
        @return: dict of format {'0':'Description', ...}
        """
        bvals = self._build_lookup_data('BEAUFORT_VALUE', include_empty=False, values_in_text=False)
        return {b['value']: b['text'] for b in bvals}

    def _get_soaktime_dict(self):
        """
        Build avg soak time range description dict
        @return: dict of format {'0':'Description', ...}
        """
        bvals = self._build_lookup_data('AVG_SOAK_TIME_RANGE', include_empty=False, values_in_text=False)
        return {b['value']: b['text'] for b in bvals}

    def _get_gearperf_trawl_dict(self):
        """
        Build gear performance description dict
        @return: dict of format {'1':'Description', ...}
        """
        gvals = self._build_lookup_data('GEAR_PERFORMANCE', include_empty=False, values_in_text=False)
        return {b['value']: b['text'] for b in gvals}

    def _get_gearperf_fg_dict(self):
        """
        Build gear performance description dict for FG
        NOTE The description for #5 is trawl based, so hardcoded the alternate text here
        @return: dict of format {'1':'Description', ...}
        """
        gvals = self._build_lookup_data('GEAR_PERFORMANCE', include_empty=False, values_in_text=False)
        # FG - manually change this one value
        for g in gvals:
            if g['value'] == '5':
                g['text'] = 'Problem - Pot(s) or other gear lost'
                break
        return {b['value']: b['text'] for b in gvals}

    def _list_lookup_desc(self, lookup_type, values_in_text=False):
        """
        Get simple list of values from LOOKUPS given a list created by _build_lookup_data
        """
        lookup_data = self._build_lookup_data(lookup_type, include_empty=False, values_in_text=values_in_text)

        lookuplistdata = list()

        for datum in lookup_data:
            lookuplistdata.append(datum['text'])

        return sorted(lookuplistdata)

    def _get_trawl_gear_list(self):
        """
        Get the list of trawl gear types and descriptions, concatenated.
        Sort by trawl type treated as integer.
        
        :return: a list of strings of gear type value, space, and gear type description.
        """
        gvals = self._build_lookup_data('TRAWL_GEAR_TYPE', include_empty=False, values_in_text=False)

        # Sort by gear type - numerically, not alphabetically.
        lookupdata = []
        for entry in gvals:
            entry['value_as_int'] = int(entry['value'])
            lookupdata.append(entry)
        lookupdata = sorted(lookupdata, key=itemgetter('value_as_int'))  # Sort numerically by gear number.

        return [str(entry['value_as_int']) + ' ' + entry['text'] for entry in lookupdata]

    def _get_fg_gear_list(self):
        """
        Get the list of fg gear types and descriptions, concatenated.
        Sort by trawl type treated as integer.

        :return: a list of strings of gear type value, space, and gear type description.
        """
        gvals = self._build_lookup_data('FG_GEAR_TYPE', include_empty=False, values_in_text=False)

        # Sort by gear type - numerically, not alphabetically.
        lookupdata = []
        for entry in gvals:
            entry['value_as_int'] = int(entry['value'])
            lookupdata.append(entry)
        lookupdata = sorted(lookupdata, key=itemgetter('value_as_int'))  # Sort numerically by gear number.

        return [str(entry['value_as_int']) + ' ' + entry['text'] for entry in lookupdata]

    def _get_avg_soaktimes_list(self):
        """
        Get the list of avg soak times descriptions, concatenated.
        Sort by # type treated as integer.

        :return: a list of strings of soak time value, space, and soak time description.
        """
        gvals = self._build_lookup_data('AVG_SOAK_TIME_RANGE', include_empty=False, values_in_text=False)

        # Sort by gear type - numerically, not alphabetically.
        lookupdata = []
        for entry in gvals:
            entry['value_as_int'] = int(entry['value'])
            lookupdata.append(entry)
        lookupdata = sorted(lookupdata, key=itemgetter('value_as_int'))  # Sort numerically by gear number.

        return [str(entry['value_as_int']) + ' ' + entry['text'] for entry in lookupdata]

class TestObserverData(unittest.TestCase):
    """
    Test basic SQLite connectivity
    """

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.testdata = ObserverData()

    def test_connection(self):
        self.assertIsNotNone(self.testdata.db_connection)
        cursor = self.testdata.db_connection.cursor()
        self.assertIsNotNone(cursor)

    def test_beaufort(self):
        beef = self.testdata._get_beaufort_dict()
        self.assertGreater(len(beef['0']), 5)
        self.assertGreater(len(beef['9']), 5)

    def test_gearperf(self):
        beef = self.testdata._get_gearperf_trawl_dict()
        self.assertGreater(len(beef['1']), 5)
        self.assertGreater(len(beef['7']), 5)

    def test_observers(self):
        logging.debug(self.testdata.observers)
        self.assertGreater(len(self.testdata.observers), 10)

    def test_vessels(self):
        logging.debug(self.testdata.vessels)
        self.assertGreater(len(self.testdata.vessels), 10)

    def test_weightmethods(self):
        logging.debug(self.testdata.weight_methods)
        self.assertGreater(len(self.testdata.weight_methods), 10)

    def test_vesseltypes(self):
        logging.debug(self.testdata.vessel_types)
        self.assertGreater(len(self.testdata.vessel_types), 5)

    def test_vessellogbooknames(self):
        logging.debug(self.testdata.vessel_logbook_names)
        self.assertGreater(len(self.testdata.vessel_logbook_names), 5)

    def test_discardreasons(self):
        logging.debug(self.testdata.discard_reasons)
        self.assertGreater(len(self.testdata.discard_reasons), 5)

    def test_catchcategories(self):
        logging.debug(self.testdata.catch_categories)
        self.assertGreater(len(self.testdata.catch_categories), 200)

    def test_trawlgeartypes(self):
        logging.debug(self.testdata.trawl_gear_types)
        self.assertEqual(len(self.testdata.trawl_gear_types), 12)

    def test_lookups_orm(self):
        """
        Compares old and new LOOKUPS select
        :return:
        """
        self.testdata._get_lookups()
        copylookups = dict(self.testdata._lookups)
        self.testdata._get_lookups_orm(rebuild=True)
        self.assertGreater(len(copylookups), 0)
        self.assertEqual(len(copylookups), len(self.testdata._lookups))

    @unittest.skip("ObserverData no longer has a 'programs' attribute.")
    def test_fisheries(self):
        self.assertGreater(len(self.testdata.programs), 10)
        logging.debug(self.testdata.programs)

    def test_observers_orm(self):
        """
        Compares old and new LOOKUPS select
        :return:
        """
        self.testdata._get_observers()
        copyobs = list(self.testdata._observers)
        self.testdata._get_observers_orm(rebuild=True)
        self.assertGreater(len(copyobs), 0)
        self.assertEqual(len(copyobs), len(self.testdata._observers))

    def test_get_observer(self):
        self.assertEqual(self.testdata.get_observer_id('Eric Brasseur'), 1484)
        self.assertEqual(self.testdata.get_observer_name(1471), 'Amos Cernohouz')


if __name__ == '__main__':
    unittest.main()
