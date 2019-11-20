# -----------------------------------------------------------------------------
# Name:        CatchCategory.py
# Purpose:     Helper class for Catch Category (Observer)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 11, 2016
# License:     MIT
# ------------------------------------------------------------------------------

import json
import logging
from operator import itemgetter
from typing import Dict, List
import unittest

from PyQt5.QtCore import QObject, QVariant, pyqtProperty, pyqtSignal, pyqtSlot

from playhouse.shortcuts import model_to_dict

from py.observer.CatchCategoryModel import CatchCategoryModel
from py.observer.ObserverDBModels import CatchCategories, Catches, FishingActivities, Settings
from py.observer.ObserverDBUtil import ObserverDBUtil

class TrawlFrequentCatchCategories:
    """
    The Catch Categories tab screen has a Frequent List of catch category codes.
    This helper class returns that list, first looking for an entry in the SETTINGS table
    of Observer.db, then the default default list given in this class.

    Side-effect: this class, if it doesn't find a SETTINGS entry for trawl frequent catch categories,
    will create one.

    List is not sorted. Sort will likely occur on a field other than code (common or scientific name).
    """
    # PacFIN codes of 30 most frequently referenced Catch Categories. From Neil Riley.
    DEFAULT_TRAWL_FREQUENT_CATCH_CATEGORIES = [
            "ZMIS",
            "SABL",
            "DOVR",
            "SSPN",
            "PTRL",
            "ARTH",
            "REX",
            "PHLB",
            "SRMP",
            "EGLS",
            "LSPN",
            "LCOD",
            "LSKT",
            "PWHT",
            "NSLP",
            "PCOD",
            "MBOT",
            "DBRK",
            "POP",
            "CNRY",
            "YTRK",
            "INVT",
            "SSOL",
            "PDAB",
            "CHLB",
            "THDS",
            "CLPR",
            "STRY",
        ]
    SETTINGS_PARAMETER_NAME = 'trawl_frequent_catch_categories'

    def __init__(self, parameter_name=SETTINGS_PARAMETER_NAME):
        self._logger = logging.getLogger(__name__)
        self._parameter_name = parameter_name
        if self._parameter_name != TrawlFrequentCatchCategories.SETTINGS_PARAMETER_NAME:
            self._logger.info("Not using default parameter name {}, but {}".format(
                TrawlFrequentCatchCategories.SETTINGS_PARAMETER_NAME, parameter_name))

        self._frequent_catch_category_codes = ObserverDBUtil.db_load_save_setting_as_json(
                self._parameter_name,
                TrawlFrequentCatchCategories.DEFAULT_TRAWL_FREQUENT_CATCH_CATEGORIES)

        self.verify_freq_cc_codes(self._frequent_catch_category_codes)

    @property
    def catch_category_codes(self):
        return self._frequent_catch_category_codes

    def verify_freq_cc_codes(self, code_list):
        catch_category_q = CatchCategories.select().where(CatchCategories.active >> None). \
            order_by(CatchCategories.catch_category_code)
        full_cc_list = [c.catch_category_code for c in catch_category_q]
        for code in code_list:
            if code not in full_cc_list:
                self._logger.info(f'Unable to find CC {code}, removing from frequent list.')
                code_list.remove(code)


class CatchCategory(QObject):
    modelChanged = pyqtSignal(name='modelChanged')

    WEIGHT_METHODS_WITH_NO_COUNT = ('3', '6', '7', '15', '20', '21')

    catch_category_list_types = (
        'Full',         # Full list from CATCH_CATEGORIES table of observer.db
        'Frequent',     # List of most often used categories.
        'Trip',         # List of categories used on any haul of current trip.
    )

    def __init__(self, db):
        super().__init__()
        self._logger = logging.getLogger(__name__)

        self._data = db

        # The three alternative models for the lists of catch categories
        # Instantiate here and nowhere else: references are being used.
        # To reset, clear rather than re-instantiate.
        self._full_list_cc_model = CatchCategoryModel()
        self._frequent_list_cc_model = CatchCategoryModel()
        self._trip_list_cc_model = CatchCategoryModel()

        # The Full catch category is initialized from Observer.db table CATCH_CATEGORIES.
        # The Frequent catch category is initialized from a list stored in the SETTINGS table of Observer.db.
        # The TrawlFrequentCatchCategories instance gets from the db or uses a default.
        self._frequent_catch_category_codes = TrawlFrequentCatchCategories().catch_category_codes
        # The Trip catch category is initialized here.
        self._trip_list_catch_category_codes = list()

        self._filter_code = ''  # Filter by PACFIN code

        self._is_fixed_gear = ObserverDBUtil.is_fixed_gear()

        self.load_full_list()
        self.load_frequent_list()
        self.load_trip_list()

        # Default model associated with tvAvailableCC TableView: full
        self._active_cc_model = self._full_list_cc_model
        self._active_cc_model_type = "Full"

    @pyqtSlot(name='resetActiveList')
    def reset_active_list(self):
        """
        Reset (reinitialize) the active catch category model.
        :return: None
        """
        if self._active_cc_model_type == "Full":
            self.load_full_list()
        elif self._active_cc_model_type == "Frequent":
            self.load_frequent_list()
        elif self._active_cc_model_type == "Trip":
            self.load_trip_list()
        elif self._active_cc_model_type == "AssocSpecies":
            self.load_full_list()  # ?
        else:
            raise Exception("Active catch category type '{}' is not one of four expected.".format(
                    self._active_cc_model_type))

        self.modelChanged.emit()    # Let the tvAvailableCC TableView know the model has changed.

    def set_trip_list_codes(self, catch_cat_codes: List[str]):
        """ With respect to the trip list of catch categories, use this method to:
            Empty (when trip is ended).
            Load with specific values (when logging in anew with trip in progress).
        """
        self._trip_list_catch_category_codes = catch_cat_codes
        self.load_trip_list()

    def _get_trip_cccs(self, trip_id):
        """ For the given trip (typically the current trip),
            return a list of catch category codes that have been used
            on at least one of the hauls of that trip.

            Include category codes from the current haul.
        """
        unique_cccs = []
        # "haul" == "fishing activity"
        hauls_q = FishingActivities.select().where(FishingActivities.trip == trip_id)
        if hauls_q.count() > 0:
            self._logger.debug("Found {} Hauls.".format(hauls_q.count()))
        for haul in hauls_q:
            catches = self._get_catch_models(haul.fishing_activity)
            if not catches:
                continue
            for catch in catches:
                catch_category_code = catch.catch_category.catch_category_code
                if catch_category_code not in unique_cccs:
                    unique_cccs.append(catch_category_code)
        return unique_cccs

    @pyqtSlot(QVariant, name='initializeTripListCccs')
    def initialize_trip_list_cccs(self, trip_id):
        """
        Initialize this trip's list of catch category codes.
        Scan all the catches for the current trip. Add unique catch categories used on any haul, even the current haul.
        to the object instance holding the trip list's category codes.

        :return: None
        """
        self._logger.debug("Trip ID supplied = {}".format(trip_id))

        trip_list_cccs = self._get_trip_cccs(trip_id)
        trip_list_cccs = CatchCategory._sort_catch_category_codes(trip_list_cccs)
        self.set_trip_list_codes(trip_list_cccs)

    @staticmethod
    def _sort_catch_category_codes(catch_category_codes: List[str]) -> List[str]:
        """ Sort catch category codes alphabetically, with one exception:
            if code 'ZMIS' (a special code for miscellaneous) is present, put it first. It's commonly used.
        """
        sorted_cccs = sorted(catch_category_codes)
        if 'ZMIS' in sorted_cccs:
            sorted_cccs.remove('ZMIS')
            sorted_cccs.insert(0, 'ZMIS')
        return sorted_cccs

    @staticmethod
    def _sort_catch_categories(catch_categories: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """ Sort catch category entries (id, code, description) alphabetically by code, with one exception:
            if code 'ZMIS' (a special code for miscellaneous) is present, put it first. It's commonly used.
        """
        sort_field = 'catch_category_code'
        zmis_value = 'ZMIS'

        zmis_entry = [entry for entry in catch_categories if entry[sort_field] == zmis_value ]
        if len(zmis_entry) > 1:
            raise IndexError('Found more than one occurrence of code ZMIS')

        all_but_zmis = [entry for entry in catch_categories if entry[sort_field] != zmis_value ]

        ccs_sorted = sorted(all_but_zmis, key=itemgetter(sort_field))
        if len(zmis_entry) == 1:
            ccs_sorted.insert(0, zmis_entry[0])

        return ccs_sorted

    def load_full_list(self):
        """
        Clear catch category data, reset states
        """
        self._logger.info('Loading full catch categories')
        full_list_ccs = self._get_catch_categories_from_db()  # Populate from  DB
        full_list_ccs = CatchCategory._sort_catch_categories(
                full_list_ccs)

        # Only instantiate once: reference is being passed around. Clear, don't re-instantiate.
        if self._full_list_cc_model is None:
            raise Exception('Expected full catch category model to have been instantiated.')
        self._full_list_cc_model.clear()
        self._full_list_cc_model.setItems(full_list_ccs.copy()) # TODO: Is copy necessary?

    def _add_category_by_code(self, cc_model, cat_code):
        """ Given a category code and a frequent or trip category model,
            load the full entry (id, code, description) into that model.
            Assumes category code exists in full category code model; raises exception if not.
        """
        code_idx_in_full = self._full_list_cc_model.get_item_index('catch_category_code', cat_code)
        if code_idx_in_full < 0:
            errorstr = f"Unexpectedly could not find category code '{cat_code}' in full catch category list"
            self._logger.error(errorstr)  # Log error, but don't crash
        else:
            entry_to_add = self._full_list_cc_model.get(code_idx_in_full)
            cc_model.appendItem(entry_to_add)

    def load_frequent_list(self):
        """
        Load the _frequent_list_cc_model using the initialized list of frequent catch category codes.
        Raise exception if a supplied frequent category code isn't in full list of catch categories.
        """
        if (self._full_list_cc_model is None):
            self.load_full_list()

        sorted_frequent_list_cccs = CatchCategory._sort_catch_category_codes(
                self._frequent_catch_category_codes)
        if self._frequent_list_cc_model is None:
            raise Exception('Expected frequent catch category model to have been instantiated.')
        self._frequent_list_cc_model.clear()
        for code in sorted_frequent_list_cccs:
            self._add_category_by_code(self._frequent_list_cc_model, code)

    def load_trip_list(self):
        """
        Caller will have scanned hauls completed in the current trip and
        built the used-on-trip list of cat_codes.
        """
        # Pulls the category entries from the full model:
        if (self._full_list_cc_model is None):
            self.load_available()

        if self._trip_list_cc_model is None:
            raise Exception('Expected trip catch category model to have been instantiated.')
        self._trip_list_cc_model.clear()

        if not self._trip_list_catch_category_codes:
            self._logger.info('Initialized empty trip catch category model.')
        else:
            for ccc in self._trip_list_catch_category_codes:
                self._add_category_by_code(self._trip_list_cc_model, ccc)
            self._logger.info('Initialized non-empty trip catch category model.')

    @staticmethod
    def _get_catch_categories_from_db():
        """
        Load add catch categories from DB
        :return: list of dict
        """
        active_catch_categories = []

        catch_category_q = CatchCategories.select().where(CatchCategories.active >> None). \
            order_by(CatchCategories.catch_category_code)

        for cc in catch_category_q:
            active_catch_categories.append(model_to_dict(cc))
        return active_catch_categories

    def _get_catch_models(self, fishing_activity_id):
        """
        Load catch table models for a given haul from DB.
        :param fishing_activity_id: haul ID
        :return: list of catch ORM models
        """
        if fishing_activity_id is None:
            self._logger.error('Activity ID none')
            return

        catch_category_q = Catches.select(). \
            where(Catches.fishing_activity == fishing_activity_id). \
            order_by(Catches.catch_num)

        return catch_category_q

    def is_recent(self, code):
        """
        Check if code already added to recent list
        :param code: Value of role
        :return: True if already in recent list
        """
        return self.search_dict(self._recent_catch_categories, 'catch_category_code',
                                code, set_recent=False) is not None

    def search_code(self, code):
        """
        Search catch categories by role
        :param code: Value of code to look for
        :return: None if no match, otherwise dict result
        """
        return self.search_dict(self._catch_categories, 'catch_category_code',
                                code, set_recent=True)

    def search_id(self, cc_id):
        """
        Search catch categories by CC ID
        Note: ID must be converted to str for search compare
        :param cc_id: Value of ID to look for
        :return: None if no match, otherwise dict result
        """
        return self.search_dict(self._catch_categories, 'catch_category_id',
                                str(cc_id), set_recent=True)

    @staticmethod
    def search_dict(src_dict, role, value, set_recent=False):
        """
        Search dict by role
        :param src_dict: dict to search in
        :param role: Role to look for
        :param value: Value of role
        :param set_recent: Set recent flag if found
        :return: None if no match, otherwise dict result
        """
        for cat_entry in src_dict:
            if role in cat_entry and cat_entry[role] == value:
                # self._logger.info("Found " + str(cat_entry))
                if set_recent:
                    cat_entry['isMostRecent'] = 'TRUE'
                return cat_entry

        return None

    @pyqtProperty(QVariant, notify=modelChanged)
    def catchCategoryFullModel(self):
        return self._full_list_cc_model

    @pyqtProperty(QVariant, notify=modelChanged)
    def catchCategoryFrequentModel(self):
        return self._frequent_list_cc_model

    @pyqtProperty(QVariant, notify=modelChanged)
    def catchCategoryTripModel(self):
        return self._trip_list_cc_model

    @pyqtProperty(QVariant, notify=modelChanged)
    def catchCategorySelectedModel(self):
        return self._selected_catches

    @property
    def catch_categories(self):
        # This is used by ObserverAutoComplete as the list on which to apply the filter.
        # Return the catch categories for the active list (full, frequent, or trip).
        return self._active_cc_model.items

    @pyqtSlot(QVariant, name='setActiveListModel')
    def set_active_list_model(self, model_type):
        """ Set the available list of catch categories presented to the user
            to either the full list from the CATCH_CATEGORIES or a shorter list of frequently used categories
            or a list of categories used earlier on this trip.
        """
        if model_type in CatchCategory.catch_category_list_types:
            self._active_cc_model_type = model_type
            if model_type == 'Full':
                self._active_cc_model = self._full_list_cc_model
            elif model_type == 'Frequent':
                self._active_cc_model = self._frequent_list_cc_model
            else:
                self._active_cc_model = self._trip_list_cc_model
        else:
            raise Exception('Unexpected catch category model type {}.'.format(model_type))

        fmt_str = "Switching active catch category model to {} List with {} items."
        self._logger.info(fmt_str.format(model_type, len(self._active_cc_model.items)))

    @pyqtProperty(QVariant, notify=modelChanged)
    def filter(self):
        return self._filter_code

    @filter.setter
    def filter(self, code_value):
        self._filter_code = code_value
        self._logger.info("CC filter set to '{}'".format(self._filter_code))
        self._filter_models(self._filter_code)

    def _filter_models(self, code):
        """
        Filter active category list
        # TODO{jim} currently only filtering on full. Consider filtering on frequent and trip as well.
        # TODO{wsmith, jim} filtering could be way more efficient
        :param code: PACFIN code
        :return:
        """

        # Before filtering, get the unfiltered list as a starting point, not the pared down one. Handle bkspc key.
        self.reset_active_list()

        active_copy = self.catch_categories.copy()
        filtered_active = self._filter_cclist(active_copy, code)
        self._active_cc_model.setItems(filtered_active)

        self.modelChanged.emit()    # Let the tvAvailableCC TableView know the model has changed.

    @pyqtProperty(QVariant, notify=modelChanged)
    def filter_matches_code(self):
        """
        Does the list of filtered items contain a code that's an exact case-insensitive match of the filter?
        :return: True if match, else False
        """
        filter_upper = self._filter_code.upper()
        for candidate in self._active_cc_model.items:
            candidate_code = candidate['catch_category_code'].upper()
            if candidate_code == filter_upper:
                self._logger.info("Filter to candidate_code match ({})".format(self._filter_code))
                return True
        return False

    @staticmethod
    def _filter_cclist(cclist, code):
        """
        Filter a catch category list by PACFIN code
        :param code: PACFIN code
        :return: list of dict catch categories
        """
        return [c for c in cclist
                if code.upper() in c['catch_category_code'].upper() or
                code.upper() in c['catch_category_name'].upper()]

    @pyqtSlot(QVariant, name='addCodeToTrip')
    def add_code_to_trip(self, selected_code):
        """
        Add item to catchCategoryTripModel based on PACFIN code, if not already added.

        This implementation clears the trip model and re-adds all the previous categories codes
        plus the new one. Not at all efficient, but acceptable for a model with a
        low tens of categories.

        :param selected_code: pacfin code
        :return: item added, otherwise None
        """
        if self._trip_list_catch_category_codes is None:
            self._trip_list_catch_category_codes = list()

        if selected_code not in self._trip_list_catch_category_codes:
            # Filter may have been in place. Load back full list so earlier trip codes will be found.
            self.load_full_list()    # TODO: This is side-effect. Earlier, better, place to restore this state?
            self._trip_list_catch_category_codes.append(selected_code)
            self._trip_list_catch_category_codes = CatchCategory._sort_catch_category_codes(
                    self._trip_list_catch_category_codes)
            # Clear trip list of cccs and re-initialize.
            # Inefficient to do all for one new, but OK-ish for short list.
            self.load_trip_list()


class TestTrawlFrequentCatchCategories(unittest.TestCase):
    """ Use a different setting value parameter name than SETTINGS_PARAMETER_NAME,
        Observer.db here may be being used for dev work.
    """
    def __init__(self, *args, **kwargs):
        super(TestTrawlFrequentCatchCategories, self).__init__(*args, **kwargs)
        self.TEST_SETTINGS_PARAMETER_NAME = TrawlFrequentCatchCategories.SETTINGS_PARAMETER_NAME + "_TESTING123"
        self._logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    def setUp(self):
        self._delete_test_record()
        self._insert_default_test_record()
        # Use the optional __init__ parameter to specify the key value for the setting.
        self.tfcc = TrawlFrequentCatchCategories(self.TEST_SETTINGS_PARAMETER_NAME)

    def _delete_test_record(self):
        """ Remove the test setting."""
        delete_q = Settings.delete().where(Settings.parameter == self.TEST_SETTINGS_PARAMETER_NAME)
        delete_q.execute()

    def _insert_default_test_record(self):
        test_list_as_json = json.dumps(TrawlFrequentCatchCategories.DEFAULT_TRAWL_FREQUENT_CATCH_CATEGORIES)
        self._logger.debug("Default test list as JSON = {}".format(test_list_as_json))
        insert_q = Settings.insert(parameter=self.TEST_SETTINGS_PARAMETER_NAME,
                                   value=test_list_as_json)
        insert_q.execute()

    def tearDown(self):
        pass
        self._delete_test_record()

    def test_list_is_default(self):
        self.assertEqual(list(TrawlFrequentCatchCategories.DEFAULT_TRAWL_FREQUENT_CATCH_CATEGORIES),
                         self.tfcc.catch_category_codes)

    def test_entry_from_db_is_read(self):
        # Get the current entry, if any, ready to restore at conclusion
        select_q = Settings.select().where(
            Settings.parameter == self.TEST_SETTINGS_PARAMETER_NAME)
        orig_list = json.loads(select_q.get().value)
        self._logger.debug("Orig list = {}".format(orig_list))

        test_value = None
        test_candidates = ('NSCC', 'XYZA', 'XXXX')  # Unlikely real catch category codes
        for candidate_test_value in test_candidates:
            if candidate_test_value not in orig_list:
                test_value = candidate_test_value
                break

        errFmtStr = "Unexpectedly, every value in test value list ({}) was in orig. list"
        self.assertIsNotNone(test_value, errFmtStr.format(test_candidates))
        self._logger.info("Adding {} to value field.".format(test_value))


        # Add a catch category code to the db entry
        test_list = orig_list.copy()
        test_list.append(test_value)
        test_list_as_json = json.dumps(test_list)
        fr_update = Settings.update(value=test_list_as_json).where(
            Settings.parameter == self.TEST_SETTINGS_PARAMETER_NAME)
        fr_update.execute()

        # Test that newly instantiated class returns list with new entry. Three parts:

        # 1. Check that the db has the right updated list
        fr_query = Settings.select().where(
            Settings.parameter == self.TEST_SETTINGS_PARAMETER_NAME)
        updated_list = json.loads(fr_query.get().value)
        self.assertEqual(test_list, updated_list)
        self._logger.debug("updated_list = {}".format(test_list))
        self.assertIsNotNone(updated_list)

        # 2. Verify that the pre-existing frequent catch category code does NOT get updated value -
        #   that it doesn't do a re-pull from the db on every get of its property
        self.assertNotIn(test_value, self.tfcc.catch_category_codes)

        # 3. Instantiate a new copy of frequent catch_category_codes and verify it DOES have the
        #   new value in the list.
        newtfcc = TrawlFrequentCatchCategories(self.TEST_SETTINGS_PARAMETER_NAME)
        self.assertIn(test_value, newtfcc.catch_category_codes)

    def test_top_catch_categories(self):
        """ Expecting a Python list of 3 or 4 character strings.
            Can't assume value equals the default value. Values could have been changed in the Observer db.
        """
        top_cccs = self.tfcc.catch_category_codes

        # Type is a list
        self.assertTrue(isinstance(top_cccs, list))

        # Every member of list is a three or four-character string
        min_expected_length = 3
        max_expected_length = 4
        for ccc in top_cccs:
            self.assertTrue(isinstance(ccc, str))
            self.assertTrue(len(ccc) in range(min_expected_length, max_expected_length+1))
