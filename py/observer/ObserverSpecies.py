# -----------------------------------------------------------------------------
# Name:        ObserverSpecies.py
# Purpose:     Support class for ObserverSpeciesModel (Observer)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 11, 2016
# License:     MIT
# ------------------------------------------------------------------------------
import re
from decimal import Decimal, ROUND_HALF_UP

from PyQt5.QtCore import pyqtProperty, QVariant, QObject, pyqtSignal, pyqtSlot

from playhouse.shortcuts import model_to_dict
from peewee import fn

from py.observer.CatchCategory import CatchCategory
from py.observer.CountsWeights import CountsWeights
from py.observer.ObserverConfig import display_decimal_places
from py.observer.ObserverDBModels import Catches, FishingActivities, ProtocolGroups, Settings, \
    Species, SpeciesCompositions, SpeciesCompositionItems, SpeciesCorrelation, SpeciesSamplingPlanLu, \
    SpeciesCatchCategories, Lookups, GeartypeStratumGroupMtx, BioSpecimens, StratumLu, SpeciesCompositionBaskets
from py.observer.ObserverDBUtil import ObserverDBUtil
from py.observer.ObserverLookups import RockfishCodes

from py.observer.ObserverSpeciesModel import ObserverSpeciesModel
from py.observer.ObserverSpeciesCompModel import ObserverSpeciesCompModel

import json
import logging
from operator import itemgetter
from typing import List, Dict
import unittest


class TrawlFrequentSpecies:
    """
    The Species tab screen has a Frequent List of numeric species codes.
    This helper class returns that list, first looking for an entry in the SETTINGS table
    of Observer.db, then the default default list given in this class.

    Side-effect: this class, if it doesn't find a SETTINGS entry for trawl frequent species,
    will create one.

    List is not sorted. Sort will likely occur on a field other than code (common or scientific name).
    """
    # Species code of 30 most frequently referenced Species. From Neil Riley.
    # Store as text rather than integers because that's how they're stored in SPECIES table of Observer.db.
    DEFAULT_TRAWL_FREQUENT_SPECIES = [
        "206",  # Pacific Hake (CNT=39242)
        "250",  # Eelpout Unid (CNT=30762)
        "554",  # Longnose Skate (CNT=27163)
        "111",  # Slender Sole (CNT=25903)
        "141",  # Arrowtooth Flounder (CNT=25580)
        "20",  # Sea Star Unid (CNT=24875)
        "555",  # Sandpaper Skate (CNT=23894)
        "55",  # Anemone Unid (CNT=23540)
        "105",  # Rex Sole (CNT=23218)
        "99",  # Spotted Ratfish (CNT=22475)
        "68",  # Brown Cat Shark (CNT=21748)
        "66",  # Pacific Spiny Dogfish (CNT=19873)
        "18",  # Tanneri Tanner Crab (CNT=19304)
        "112",  # Petrale Sole (CNT=16828)
        "311",  # Darkblotched Rockfish (CNT=16460)
        "12",  # Dungeness Crab (CNT=15673)
        "601",  # Eulachon (CNT=14211)
        "137",  # Pacific Sanddab (CNT=13434)
        "1264",  # Non Humboldt Squid Unid (CNT=12323)
        "107",  # Dover Sole (CNT=12262)
        "108",  # English Sole (CNT=11166)
        "110",  # Deepsea Sole (CNT=10796)
        "70",  # Shrimp Unid (CNT=10632)
        "82",  # Giant Grenadier (CNT=9709)
        "83",  # Pacific Grenadier (CNT=9056)
        "500",  # Snailfish Unid (CNT=9051)
        "603",  # Lingcod (CNT=8876)
        "352",  # Longspine Thornyhead (CNT=8555)
        "350",  # Shortspine Thornyhead (CNT=8493)
        "60",  # Octopus Unid (CNT=8462)
    ]

    SETTINGS_PARAMETER_NAME = 'trawl_frequent_species'

    def __init__(self, parameter_name=SETTINGS_PARAMETER_NAME):
        self._logger = logging.getLogger(__name__)
        self._parameter_name = parameter_name
        if self._parameter_name != TrawlFrequentSpecies.SETTINGS_PARAMETER_NAME:
            self._logger.info("Not using default parameter name {}, but {}".format(
                TrawlFrequentSpecies.SETTINGS_PARAMETER_NAME, parameter_name))

        self._frequent_species_codes = ObserverDBUtil.db_load_save_setting_as_json(
            self._parameter_name,
            TrawlFrequentSpecies.DEFAULT_TRAWL_FREQUENT_SPECIES)

        self.verify_freq_species(self._frequent_species_codes)

    def get_species_codes(self):
        return self._frequent_species_codes

    def verify_freq_species(self, freq_species_list):
        species_q = Species.select(). \
            where(Species.active.is_null(True) | Species.active == 1). \
            order_by(Species.common_name)

        full_species_list = [s.species_code for s in species_q]
        for species_num in freq_species_list:
            if species_num not in full_species_list:
                self._logger.info(f'Unable to find species code {species_num}, removing from frequent list.')
                freq_species_list.remove(species_num)


class TrawlAssociatedSpecies:
    """
    Species associated with a Catch Category
    """

    def __init__(self, catch_category_id=None):
        self._logger = logging.getLogger(__name__)
        self._assoc_species_codes = self.get_cc_species(catch_category_id)

    @staticmethod
    def get_cc_species(cc_id):
        return [s.species.species for s in SpeciesCatchCategories.select(SpeciesCatchCategories.species).where(
            SpeciesCatchCategories.catch_category == cc_id)] if cc_id else []

    def set_catch_category(self, cc_id):
        self._assoc_species_codes = self.get_cc_species(cc_id)

    def get_species_ids(self):
        return self._assoc_species_codes


class WeightMethod3Helper:
    """
    Helper in calculating catches with a weight method of 3 ("WM3"), which calls for weighing a sub-sample
    of the discard baskets and estimating the catch weight by applying the average to the
    unweighed baskets.
    
    Basket data for WM3 is stored in a different table than SPECIES_COMPOSITION_BASKETS because
    not all baskets weighed using WM3 are speciated. CATCHES_ADDITIONAL_BASKETS is used.
    
    Not sub-classed from QObject because it's not clear it will define and send signals.
    """

    def __init__(self, logger, observer_catches):
        """
        :param logger: 
        :param observer_catches: Use to get weight method of current catch.
        """
        self._logger = logger
        self._observer_catches = observer_catches

    @property
    def currentWeightMethod(self):
        return self._observer_catches.weightMethod


class ObserverSpecies(QObject):
    availModelChanged = pyqtSignal(name='availModelChanged')
    selectedModelChanged = pyqtSignal(name='selectedModelChanged')
    selectedItemChanged = pyqtSignal(name='selectedItemChanged')
    currentProtocolsChanged = pyqtSignal(str, arguments=['protocols'], name='currentProtocolsChanged')
    currentBiolistChanged = pyqtSignal(name='currentBiolistChanged')
    currentFGBiolistChanged = pyqtSignal(QVariant, name='currentFGBiolistChanged')
    isRetainedChanged = pyqtSignal(name='isRetainedChanged')
    unusedSignal = pyqtSignal(name='unusedSignal')  # quiet warnings
    discardReasonChanged = pyqtSignal(QVariant, arguments=['discard_reason'], name='discardReasonChanged')
    totalCatchWeightChanged = pyqtSignal(QVariant, arguments=['weight'], name='totalCatchWeightChanged')
    totalCatchWeightFGChanged = pyqtSignal(QVariant, arguments=['weight'], name='totalCatchWeightFGChanged')
    totalCatchCountChanged = pyqtSignal(QVariant, arguments=['count'], name='totalCatchCountChanged')
    totalCatchCountFGChanged = pyqtSignal(QVariant, arguments=['count'], name='totalCatchCountFGChanged')

    species_list_types = (
        'Full',  # Full list from SPECIES table of observer.db
        'Frequent',  # List of most often used species.
        'Trip',  # List of species used on any haul of current trip.
        'AssocSpecies',  # List of species associated with Catch Category
    )

    def __init__(self, observer_catches):
        """
        :param observer_catches: Limited use: Used to determine if current catch's Weight Method is 3.
        """
        super().__init__()
        self._logger = logging.getLogger(__name__)

        # Lists of full, frequent, and trip species entries.
        # Used to reload corresponding species models - helpful during and after filtering.
        # These always contain the complete set of species for each list. That's not always
        # the case with the corresponding models these are loaded from: the models may hold
        # a subset if keyboard autocomplete filtering is in progress.
        # All these lists are sorted by species code.
        self._rockfish_codes = RockfishCodes().codes

        self._current_trip_id = ObserverDBUtil.db_load_setting("trip_number")

        # Full: Populate from DB - once. Read-only.
        self.load_species_full()

        # Frequent: Populate once from DB (SETTINGS entry). Read-only.
        self.load_species_frequent()

        # Trip: Build from scan of previous hauls this trip.
        #       Add species newly added species on current haul.
        #
        # Use empty list if current trip ID is not defined.
        self.load_species_trip()

        # The four alternative models for the lists of species
        # Instantiate once here and nowhere else: references are being used.
        # Contents change with autocomplete keyboard filtering.
        # To reset, clear rather than re-instantiate.
        # Complete set of values are loaded from the _{full,frequent,trip}_list_species above.
        self._full_list_species_model = ObserverSpeciesModel()
        self._frequent_list_species_model = ObserverSpeciesModel()
        self._trip_list_species_model = ObserverSpeciesModel()
        self.create_species_models()

        # Associated species, once we have a CC selected
        self._assoc_species_model = ObserverSpeciesModel()
        self._assoc_species = TrawlAssociatedSpecies()
        self._assoc_species_list = None

        # "Available" is the list of species displayed in tvAvailableSpecies, including filtering.
        # It is set equal to one of _{full,frequent,trip}_list_species_model.
        # Default: the full
        self._available_species_model = self._full_list_species_model
        self._available_species_model_type = "Full"

        self._current_species_comp = None
        self._current_species_comp_id = None  # set by currentSpeciesCompId

        self._current_speciescomp_item = None
        self._current_speciescomp_item_name = None  # set by currentSpeciesItemId

        self._species_comp_items = None  # set by _get_species_comp_items()

        self._species_comp_items_model = ObserverSpeciesCompModel()

        self._counts_weights = CountsWeights()
        self._filter_name = ''  # Filter both by common_name and by scientific_name

        self.current_protocol_str = ''  # store protocol lookup, e.g. 'FL, WS'
        self.current_protocol_set = None  # list of protocols ['FL', etc]
        self.current_biolist = None  # 'Always' 'Biospecimen List 1' etc

        self.current_fg_biolist = None  # User's biolist (4 or 5 for FG) - corresponds to stratum depth

        self._current_common_name = None
        self._is_retained = False

        self._total_haul_weight = None
        self._total_haul_count = None

        self._total_set_weight = None
        self._total_set_count = None

        self._is_fixed_gear = False

        # Signals from counts/weights screen
        # Handler to update the view model of the species screen with the actual not extrapolated weight:
        self._counts_weights.actualWeightChanged.connect(self._handle_actual_weight_changed)
        self._counts_weights.extrapolatedWeightChanged.connect(self._handle_extrapolated_weight_changed)
        self._counts_weights.speciesWeightChanged.connect(self._handle_species_weight_changed)
        self._counts_weights.speciesFishCountChanged.connect(self._handle_species_count_changed)
        self._counts_weights.tallyFishCountChanged.connect(self._handle_trawl_tally_fish_count_changed)
        self._counts_weights.discardReasonSelected.connect(self._handle_discard_reason_selected)
        self._counts_weights.totalTallyChanged.connect(self._handle_tally_count_changed)
        self._counts_weights.tallyFGFishCountChanged.connect(self._handle_tally_fg_count_changed)
        self._counts_weights.tallyTimesAvgWeightChanged.connect(self._handle_tally_times_avg_weight_changed)
        self._counts_weights.tallyAvgWeightChanged.connect(self._handle_tally_avg_weight_changed)

        # protocol sets
        self.slw_protocols = {'AL', 'FL', 'TL', 'CL', 'W', 'VL', 'CW', 'S', 'SD', 'WT'}
        self.viability_protocols = {'A', 'E', 'V'}
        self.etag_protocols = {'ET', 'P'}  # Existing Tag protocols: Existing Tag, Photograph.
        self.otag_protocols = {'OT', 'T'}  # Observer Tag. 'T' is deprecated - use 'OT' instead.
        self.tag_protocols = self.etag_protocols.union(self.otag_protocols)
        self.barcode_protocols = {'WS', 'FC', 'FR', 'O', 'SS', 'SC', 'TS'}

        # Helper class with Weight Method 3
        self._weight_method_3_helper = WeightMethod3Helper(self._logger, observer_catches)

    @pyqtSlot(name='reloadSpeciesDatabase')
    def reload_species_database(self):
        """
        Repopulate species models (intended to be run post-sync)
        """
        self._logger.info('Reloading Species from Database.')
        self._current_trip_id = ObserverDBUtil.db_load_setting("trip_number")
        self.load_species_full()
        self.load_species_frequent()
        self.load_species_trip()
        self.create_species_models()

    def create_species_models(self):
        self._load_full_list_model()
        self._load_frequent_list_model()
        self._load_trip_list_model()

    def load_species_trip(self):
        self._trip_list_species = list()
        if self._current_trip_id is not None:
            trip_species_codes = self._get_trip_species_codes(self._current_trip_id)
            if trip_species_codes is not None:
                self._trip_list_species = [entry for entry in self._full_list_species
                                           if entry['species_code'] in trip_species_codes]
            self._trip_list_species = ObserverSpecies._sort_species(self._trip_list_species)
            common_names = [entry['common_name'] for entry in self._trip_list_species]
            self._logger.debug("Common species names for this trip so far: {}".format(common_names))

    def load_species_frequent(self):
        frequent_species_codes = TrawlFrequentSpecies().get_species_codes()
        self._frequent_list_species = [entry for entry in self._full_list_species
                                       if entry['species_code'] in frequent_species_codes]
        self._frequent_list_species = ObserverSpecies._sort_species(self._frequent_list_species)
        # common_names = [entry['common_name'] for entry in self._frequent_list_species]
        # self._logger.debug("Frequent species Common names: {}".format(common_names))

    def load_species_full(self):
        self._full_list_species = self._get_species_dict()
        self._full_list_species = ObserverSpecies._sort_species(self._full_list_species)

    def _get_catch_models(self, fishing_activity_id):
        """
        Load add catch table models for a given haul from DB.

        TODO: Cloned from CatchCategory.py. This method belongs in a commonly accessible location.

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

    def _get_gear_groups(self) -> list():
        if not self._current_trip_id:
            return None

        try:
            gear_type = FishingActivities.get(FishingActivities.trip == self._current_trip_id).gear_type
            if self.isFixedGear:
                gear_type_id = Lookups.get(Lookups.lookup_type == 'FG_GEAR_TYPE',
                                           Lookups.lookup_value == gear_type).lookup
            else:
                gear_type_id = Lookups.get(Lookups.lookup_type == 'TRAWL_GEAR_TYPE',
                                           Lookups.lookup_value == gear_type).lookup
            gear_type_group = GeartypeStratumGroupMtx.select().where(
                GeartypeStratumGroupMtx.geartype_lu == gear_type_id)
            gear_type_groups = [g.group.group for g in gear_type_group]
            gear_type_group_names = [g.group.name for g in gear_type_group]

            self._logger.debug(f'Looked up gear type groups {gear_type_groups} => {gear_type_group_names}')
            return gear_type_groups

        except Exception as e:
            self._logger.error(f'{e}: Cannot get gear type for trip {self._current_trip_id}')
            return None

    def _get_trip_species_codes(self, current_trip_id):
        """ For the current trip,
            return a list of species codes that have been used
            on at least one of the hauls of that trip.

            Include species codes from the current haul.
        """
        trip_species_ids = []
        # "haul" == "fishing activity"
        activities_q = FishingActivities.select().where(FishingActivities.trip == current_trip_id)
        if activities_q.count() > 0:
            self._logger.debug("Found {} Fishing Activities (Hauls/Sets).".format(activities_q.count()))
        for a in activities_q:
            catches = self._get_catch_models(a.fishing_activity)
            if not catches:
                continue
            catch_ids = []
            for catch in catches:
                catch_ids.append(catch.catch)
            species_compositions_q = SpeciesCompositions.select().where(
                SpeciesCompositions.catch << catch_ids)
            for species_composition in species_compositions_q:
                species_composition_items = self.get_species_comp_items(species_composition.species_composition)
                for species_composition_item in species_composition_items:
                    if species_composition_item.species not in trip_species_ids:
                        trip_species_ids.append(species_composition_item.species.species)
        trip_species_codes = \
            [entry['species_code'] for entry in self._full_list_species
             if entry['species'] in trip_species_ids]
        self._logger.debug("Species codes on this trip so far: {}".format(trip_species_codes))
        return trip_species_codes

    @staticmethod
    def _sort_species(species: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """ Sort species entries (id, code, common name, scientific name, etc)
            alphabetically by common name.
        """
        sort_field = 'common_name'

        species_sorted = sorted(species, key=itemgetter(sort_field))

        return species_sorted

    def _load_full_list_model(self):
        """
        Stuff sorted list of species entries as dicts into view model.
        """
        self._full_list_species_model.clear()
        self._full_list_species_model.setItems(self._full_list_species.copy())

    def _load_frequent_list_model(self):
        self._frequent_list_species_model.clear()
        self._frequent_list_species_model.setItems(self._frequent_list_species.copy())

    def _load_assoc_species_model(self, catch_category_id=None):
        """
        If no cc id specified, just use whatever was last set (used in reload)
        @param catch_category_id: 
        @return: 
        """
        self._assoc_species_model.clear()
        if catch_category_id:
            self._assoc_species.set_catch_category(cc_id=catch_category_id)
        assoc_species_codes = self._assoc_species.get_species_ids()
        self._assoc_species_list = [entry for entry in self._full_list_species
                                    if entry['species'] in assoc_species_codes]
        self._assoc_species_list = ObserverSpecies._sort_species(self._assoc_species_list)
        self._assoc_species_model.setItems(self._assoc_species_list.copy())

    def _load_trip_list_model(self):
        self._trip_list_species_model.clear()
        self._trip_list_species_model.setItems(self._trip_list_species.copy())

    @pyqtSlot(QVariant, QVariant, name='setAvailableListModel')
    def set_available_list_model(self, model_type, catch_category_id):
        """ 
        Set the available list of species presented to the user.
        CC is ignored unless AssocSpecies type
        """
        if model_type in ObserverSpecies.species_list_types:
            self._available_species_model_type = model_type
            if model_type == 'Full':
                self._available_species_model = self._full_list_species_model
            elif model_type == 'Frequent':
                self._available_species_model = self._frequent_list_species_model
            elif model_type == 'AssocSpecies' and catch_category_id:
                self._load_assoc_species_model(catch_category_id)
                self._available_species_model = self._assoc_species_model
            else:
                self._available_species_model = self._trip_list_species_model
        else:
            raise Exception('Unexpected species model type {}.'.format(model_type))

        self.reload_available_list_model()

        fmt_str = "Switching active catch category model to {} List with {} items."
        self._logger.info(fmt_str.format(model_type, len(self._available_species_model.items)))

    @pyqtSlot(name='reloadAvailableListModel')
    def reload_available_list_model(self):
        """
        Reload (reinitialize) the active catch category model.
        TODO: Use instance comparision instead of tracking with separate model type.
        :return: None
        """
        if self._available_species_model_type == "Full":
            self._load_full_list_model()
        elif self._available_species_model_type == "Frequent":
            self._load_frequent_list_model()
        elif self._available_species_model_type == "Trip":
            self._load_trip_list_model()
        elif self._available_species_model_type == "AssocSpecies":
            self._load_assoc_species_model()
        else:
            raise Exception("Available catch category type '{}' is not one of four expected.".format(
                self._available_species_model_type))

        self._logger.info("Model type reloaded = {}.".format(self._available_species_model_type))
        self.availModelChanged.emit()  # Let the tvAvailableSpecies TableView know the model has changed.

    @pyqtSlot(str, name='addSpeciesToTrip')
    def add_species_to_trip(self, species_code):
        self._current_trip_id = ObserverDBUtil.db_load_setting("trip_number")  # fix first-run bug
        trip_species_codes = [entry['species_code'] for entry in self._trip_list_species]
        if species_code in trip_species_codes:
            self._logger.info("Species code ({}) already in trip list.".format(species_code))
        else:
            # Get the entry from the full list and add it to trip list
            entry_to_add = [entry for entry in self._full_list_species
                            if species_code == entry['species_code']]
            if len(entry_to_add) < 1:
                self._logger.error("Could not find record for species code '{}'".format(species_code))
                return
            if len(entry_to_add) > 1:
                fmt_str = "Found more than one record ({} records) for species code '{}'"
                self._logger.error(fmt_str.format(len(entry_to_add), species_code))
                return
            self._trip_list_species.append(entry_to_add[0].copy())
            self._trip_list_species = self._sort_species(self._trip_list_species)
            fmt_str = "Added record for species code '{}' to trip's species list."
            self._logger.info(fmt_str.format(species_code))



    def _handle_tally_count_changed(self, total_tally: int):
        if not self.isFixedGear:
            if self._current_speciescomp_item:
                self._current_speciescomp_item.total_tally = total_tally
                self._current_speciescomp_item.save()

    def _handle_tally_fg_count_changed(self, tally_count: int):
        # Fixed Gear Tally is different than Trawl tally
        if self._current_speciescomp_item:
            # self._logger.debug(f'FG Tally {tally_count}')

            idx = self._get_cur_species_comp_item_idx()

            self._species_comp_items_model.setProperty(
                idx, 'species_number', tally_count)
            # self._logger.debug(f'Species Number updated to {tally_count}')

            self._calculate_total_catch_weight_current()

    def _handle_tally_times_avg_weight_changed(self, tally_weight: float):
        # Fixed Gear Tally is different than Trawl tally
        if self.isFixedGear and self._current_speciescomp_item:
            # self._logger.debug(f'FG Tally species Weight {tally_weight}')
            idx = self._get_cur_species_comp_item_idx()

            self._species_comp_items_model.setProperty(
                idx, 'species_weight', tally_weight)
            # self._logger.debug(f'Species Weight updated to {tally_weight}')

    def _handle_tally_avg_weight_changed(self, avg_weight: float):
        if self.isFixedGear and self._current_speciescomp_item:
            # This seems to be setting wrong values for index??
            self._logger.debug(f'FG Tally avg Weight {avg_weight}')
            idx = self._get_cur_species_comp_item_idx()

            self._species_comp_items_model.setProperty(
                idx, 'avg_weight', avg_weight)
            self._logger.debug(f'Avg Weight updated to {avg_weight}')

    def _handle_actual_weight_changed(self, actual_wt: float):
        """
        For weight on the Species screen, show the actual weight of baskets weighed.
        For most weight methods, that's the same as the species weight.
        But some weight methods, in particular WM15, employ a ratio - a multiplier.
        Example WM15 ratio of 0.5 means actual weight may be 50 Lbs but species weight is 100.
        Here, use actual.

        Update view model with actual weight update (cf. extrapolated species weight of WM15).

        Note: a peer handler, _handle_species_weight_changed(), handles updating the peewee data model
        with the species weight (including the extrapolated values provided by WM15 ratio).

        :param actual_wt:
        :return:
        """
        if self._current_speciescomp_item:
            self._logger.debug(f'HANDLE ACTUAL WEIGHT {actual_wt}')
            # update view model
            idx = self._get_cur_species_comp_item_idx()
            # Return float value. QML will handle formatting via toFixed()
            actual_wt = actual_wt if actual_wt else None  # remove zero weights
            # For Fixed Gear, this is different, handled in CountsWeights
            if not self._is_fixed_gear:
                self._species_comp_items_model.setProperty(
                           idx, 'species_weight', actual_wt)
                self._logger.debug(f'Sample Weight #{idx} updated to {actual_wt}')

    def _handle_extrapolated_weight_changed(self, extrap_wt: float):
        if self._current_speciescomp_item and not self.isFixedGear:
            self._current_speciescomp_item.extrapolated_species_weight = extrap_wt
            self._current_speciescomp_item.save()
            self._calculate_total_catch_weight_current()
            idx = self._get_cur_species_comp_item_idx()
            extrap_wt = extrap_wt if extrap_wt else None  # remove zero weights
            self._species_comp_items_model.setProperty(
                idx, 'extrapolated_species_weight', extrap_wt)

    def _handle_species_weight_changed(self, wt):
        """
        Update database model with species weight update (cf. actual species weight of WM15).
        In other words, use the extrapolated weight in the calculation.
        
        Do NOT update the view model for the Species screen; its weight column shows actual, not extrapolated weight.
        :param wt:
        :return: 
        """
        if self._current_speciescomp_item:
            db_wt_val = wt if wt else None
            self._current_speciescomp_item.species_weight = db_wt_val
            # TODO get unit of measurement from somewhere
            
            if not self.isFixedGear:
                if self._current_speciescomp_item.species_weight is not None:
                    self._current_speciescomp_item.species_weight_um = 'LB'
                self._current_speciescomp_item.save()

            self._calculate_total_catch_weight_current()

            # Do NOT update the Species view model. Use the actual weight changed signal for that.

    @pyqtProperty(QVariant, notify=selectedItemChanged)
    def currentHandlingMethod(self):
        idx = self._get_cur_species_comp_item_idx()

        # [index][property]
        if idx is not None:
            item = self._species_comp_items_model.get(idx)
            return item['handling']

    @currentHandlingMethod.setter
    def currentHandlingMethod(self, method):
        self._logger.info(f'currentHandlingMethod -> {method}')
        idx = self._get_cur_species_comp_item_idx()
        self._species_comp_items_model.setProperty(idx, 'handling', method)
        self._current_speciescomp_item.handling = method
        self._current_speciescomp_item.save()
        self.selectedItemChanged.emit()

    @pyqtSlot(QVariant, name='updateBioCount')
    def _handle_bio_count(self, bio_count):
        idx = self._get_cur_species_comp_item_idx()
        if idx is None:
            return

        self._logger.debug(f'Model update {idx} Got bio count changed: {bio_count}')
        self._species_comp_items_model.setProperty(idx, 'bio_count', bio_count)

    @pyqtProperty(int, notify=unusedSignal)
    def totalFishCounted(self):
        """
        Gets physically counted number of fish from DB
        :return: INT (sum of counts within baskets)
        """
        return SpeciesCompositionBaskets.select(
            fn.sum(SpeciesCompositionBaskets.fish_number_itq)
        ).where(
            SpeciesCompositionBaskets.species_comp_item == self._current_speciescomp_item
        ).scalar()

    def _handle_trawl_tally_fish_count_changed(self, ct):
        if self.isFixedGear:  # we only use this table count on the c/w screen for FG
            return
        if not ct or not self._current_speciescomp_item:
            return
        self._current_speciescomp_item.total_tally = self._current_speciescomp_item.species_number = ct
        self._current_speciescomp_item.save()

        # Update model
        idx = self._get_cur_species_comp_item_idx()
        self._species_comp_items_model.setProperty(idx, 'species_number', ct)
        self._species_comp_items_model.setProperty(idx, 'total_fish_counted', self.totalFishCounted)  # field-2040

        # Update avg_weight view model for CURRENT_SPECIES_ITEM
        spec_wt = self._current_speciescomp_item.species_weight
        spec_num = self._current_speciescomp_item.species_number
        self._species_comp_items_model.setProperty(idx, 'species_weight', spec_wt)
        # DISABLED, incorrect calculation
        # avg_wt = spec_wt / spec_num if spec_wt and spec_num else None  # this is wrong
        # self._species_comp_items_model.setProperty(idx, 'avg_weight', avg_wt)
        # END DISABLE
        self._calculate_total_catch_weight_current()

    def _handle_species_count_changed(self, ct, tally_ct):
        """

        :param ct: Total fish count, including tally_ct. I.e. a count of weighed and unweighed fish
        :param tally_ct: count of unweighed fish
        :return: None
        """
        if self._current_speciescomp_item:
            # self._logger.debug('HANDLE COUNT {}'.format(ct))
            db_ct_val = ct if ct else None
            if self._current_species_comp.catch.catch_weight_method == '8' and \
                    db_ct_val is not None and tally_ct is not None:
                # Convention: with tally counting Weight Method 8, do NOT include tally counts of
                # unweighed fish in current_species_item.species_number.
                self._logger.debug(f"WM8: Subtracting tally ct {tally_ct} " +
                                   f"from species number {db_ct_val}.")
                db_ct_val -= tally_ct
            if self.isFixedGear:
                return
            # FG is in _handle_tally_fish_count_changed
            # Update the species composition record with weighed count and tally count.
            self._current_speciescomp_item.species_number = db_ct_val
            self._current_speciescomp_item.total_tally = tally_ct
            self._current_speciescomp_item.save()
            self._logger.debug(f"SCI updates: species_num={db_ct_val}, total_tally={tally_ct}.")

            # Update model
            idx = self._get_cur_species_comp_item_idx()
            self._species_comp_items_model.setProperty(idx, 'species_number', db_ct_val)
            self._species_comp_items_model.setProperty(idx, 'total_fish_counted', self.totalFishCounted)  # field-2040

            # Parameter 'ct' includes tally of unweighed fish as well as weighed.
            # For SpeciesScreen column, use extrapolated 'ct' for the fish count, even for WM8.
            # Having the extended count (of weighed and of tallied) in the Count column of the Species
            # Screen matches its contribution to the Catches count. I.e. less surprise to user.
            self._species_comp_items_model.setProperty(idx, 'weighed_and_tallied_count', ct)

            # Update avg_weight view model
            spec_wt = self._current_speciescomp_item.species_weight
            spec_num = self._current_speciescomp_item.species_number
            avg_wt = spec_wt / spec_num if spec_wt and spec_num else None
            self._species_comp_items_model.setProperty(idx, 'avg_weight', avg_wt)

            self._calculate_total_catch_weight_current()

    def _handle_discard_reason_selected(self, dr):
        if self._current_speciescomp_item and dr:
            # self._logger.debug('HANDLE DR {}'.format(dr))
            if dr != self._current_speciescomp_item.discard_reason:
                old_dr = self._current_speciescomp_item.discard_reason
                self._current_speciescomp_item.discard_reason = dr
                self._current_speciescomp_item.save()
                if old_dr:
                    bios_q = BioSpecimens.select().where(
                        (BioSpecimens.catch == self._current_species_comp.catch) &
                        (BioSpecimens.species == self._current_speciescomp_item.species) &
                        (BioSpecimens.discard_reason == old_dr))
                else:
                    bios_q = BioSpecimens.select().where(
                        (BioSpecimens.catch == self._current_species_comp.catch) &
                        (BioSpecimens.species == self._current_speciescomp_item.species) &
                        (BioSpecimens.discard_reason.is_null()))
                for b in bios_q:
                    b.discard_reason = dr
                    b.save()
                    self._logger.debug(f'Updated Biospecimen {b.bio_specimen} DR to {dr}')

            # update model
            idx = self._get_cur_species_comp_item_idx()
            self._species_comp_items_model.setProperty(idx, 'discard_reason', dr)

    def _get_cur_species_comp_item_idx(self):
        if not self._current_speciescomp_item:
            return None
        return self._species_comp_items_model.get_item_index('species_comp_item',
                                                             self._current_speciescomp_item.species_comp_item)


    @staticmethod
    def get_wm15_ratio(notes):
        wm15_ratio = ObserverDBUtil.get_current_catch_ratio_from_notes(notes)
        if wm15_ratio:
            return wm15_ratio
        return 1.0

    def _calculate_catch_weight(self, species_comp_item):
        current_weight_method = species_comp_item.catch.catch_weight_method

        if current_weight_method == '15':
            agg_species_weight = SpeciesCompositionItems. \
                select(). \
                where(SpeciesCompositionItems.species_composition == species_comp_item.species_composition). \
                aggregate(fn.Sum(SpeciesCompositionItems.species_weight))
            # FIELD-2013 changed this to use species_weight instead of extrapolated weight for WM15

            notes = species_comp_item.catch.notes
            if notes and agg_species_weight:
                wm15_ratio = self.get_wm15_ratio(notes)

                wm15_weight = (Decimal(agg_species_weight) /
                      Decimal(wm15_ratio)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
                self._total_haul_weight = float(wm15_weight)
            else:
                self._total_haul_weight = None
        else:
            self._total_haul_weight = SpeciesCompositionItems. \
                select(). \
                where(SpeciesCompositionItems.species_composition == species_comp_item.species_composition). \
                aggregate(fn.Sum(SpeciesCompositionItems.extrapolated_species_weight))

        self.totalCatchWeightChanged.emit(self._total_haul_weight)

        self._total_haul_count = None
        if current_weight_method in CatchCategory.WEIGHT_METHODS_WITH_NO_COUNT:
            self._logger.debug(f'No count, this is WM {current_weight_method}, '
                               f'which is in {CatchCategory.WEIGHT_METHODS_WITH_NO_COUNT}')
        else:
            self._total_haul_count = SpeciesCompositionItems. \
                select(). \
                where(SpeciesCompositionItems.species_composition == species_comp_item.species_composition). \
                aggregate(fn.Sum(SpeciesCompositionItems.species_number))

            # If Weight Method 8 with its tally counts is involved,
            # include its tally counts as well.
            if self._total_haul_count and current_weight_method == '8':
                total_haul_tally_count: int = SpeciesCompositionItems. \
                    select(). \
                    where(
                    SpeciesCompositionItems.species_composition == species_comp_item.species_composition). \
                    aggregate(fn.Sum(SpeciesCompositionItems.total_tally))
                if total_haul_tally_count:
                    self._logger.debug(f"WM8: Adding tally counts of {total_haul_tally_count} " +
                                       f"to weighed catch count of {self._total_haul_count}.")
                    self._total_haul_count += total_haul_tally_count

        self.totalCatchCountChanged.emit(self._total_haul_count)

    def _calculate_catch_weight_fg(self, species_comp):
            # Calculations are for Catch:

            current_weight_method = species_comp.catch.catch_weight_method

            if current_weight_method == '6':
                self._total_set_weight = None
            else:
                self._total_set_weight = SpeciesCompositionItems. \
                    select(). \
                    where(SpeciesCompositionItems.species_composition == species_comp.species_composition). \
                    aggregate(fn.Sum(SpeciesCompositionItems.species_weight))

            self.totalCatchWeightFGChanged.emit(self._total_set_weight)

            self._total_set_count = None
            if current_weight_method in CatchCategory.WEIGHT_METHODS_WITH_NO_COUNT:
                self._logger.debug(f'No count, this is WM {current_weight_method}, '
                                   f'which is in {CatchCategory.WEIGHT_METHODS_WITH_NO_COUNT}')
            else:
                self._total_set_count = SpeciesCompositionItems. \
                    select(). \
                    where(SpeciesCompositionItems.species_composition == species_comp.species_composition). \
                    aggregate(fn.Sum(SpeciesCompositionItems.species_number))

            self.totalCatchCountFGChanged.emit(self._total_set_count)


    def _calculate_total_catch_weight_current(self):
        if not self._current_species_comp:
            return
        elif self.isFixedGear:
            self._calculate_catch_weight_fg(self._current_species_comp)
        else:
            self._calculate_catch_weight(self._current_species_comp)

    @staticmethod
    def _get_species_dict():
        """
        Load Active Species from DB
        """
        db_species = []
        species_q = Species.select(). \
            where(Species.active.is_null(True) | Species.active == 1). \
            order_by(Species.common_name)

        for species in species_q:
            db_species.append(model_to_dict(species))
        return db_species

    @property
    def species(self):
        """
        This is used by many python classes, including ObserverAutoComplete, which uses it as the list
        upon which to apply the filter. Return the list of species entries for the active aka available list
        (full, frequent, or trip).
        :return:
        """
        return self._available_species_model.items

    @pyqtProperty(QVariant, notify=availModelChanged)
    def filter(self):
        return self._filter_name

    @filter.setter
    def filter(self, name_value):
        self._filter_name = name_value
        self._logger.info("Species filter set to '{}'.".format(self._filter_name))
        self._filter_models(self._filter_name)


    @pyqtProperty(bool, notify=unusedSignal)
    def isFixedGear(self):
        return self._is_fixed_gear

    @isFixedGear.setter
    def isFixedGear(self, is_fixed):
        self._logger.debug(f'Is fixed gear: {is_fixed}')
        self._is_fixed_gear = is_fixed

    def _filter_models(self, common_name):
        """
        Filter the available list.
        # TODO{wsmith} filtering could be way more efficient
        # TODO{jstearns} filter on scientific name as well.
        :param common_name: common name for species
        :return:
        """

        # Before filtering, get the unfiltered list as a starting point, not the pared down one.
        # This handles the case where bkspc key has been hit and filter widens.
        self.reload_available_list_model()

        avail_copy = self.species.copy()
        filtered_avail = self._filter_species_list(avail_copy, common_name)
        self._available_species_model.setItems(filtered_avail)

        self.availModelChanged.emit()

    @staticmethod
    def _strip_nonalphanum(orig):
        """
        Remove non-alphanumeric text from string
        @param orig: input string
        @return: stripped string
        """
        if orig:
            return re.sub(r'\W+', '', orig)

    @staticmethod
    def _filter_species_list(species_list, code_or_common_name):
        """
        Filter a species list by common name or species_code
        (include item in species list matches if the filter code matches:
        1.  A substring of the common name (first letter)
        2.  A substring of the species code, beginning with the first digit.
        3.  A substring of one of the words of the common name, beginning with the
            first letter of that word.

        {wsmith} FIELD-1377 Fixed #3, and now stripping non-alphanumeric chars,
        to fix search for items like 'Chum [Silver] Salmon'

        :param species_list: the list of possible species.
        :param code_or_common_name: species_code or common name
        :return: list of dict catch categories
        """
        filtered = list()
        code_or_common_name = code_or_common_name.upper()
        for s in species_list:
            species_common_name = s['common_name'].upper()

            if species_common_name.startswith(code_or_common_name):
                filtered.append(s)
                continue

            species_code = s['species_code']

            if species_code.startswith(code_or_common_name):
                filtered.append(s)
                continue

            names = list([s['common_name']])
            names.extend(species_common_name.split(' '))
            for n in names:
                n = ObserverSpecies._strip_nonalphanum(n)
                if n.upper().startswith(code_or_common_name):
                    filtered.append(s)
                    break
        return filtered

    @pyqtProperty(QVariant, notify=availModelChanged)
    def filter_matches_code(self):
        """
        Does the list of filtered items contain a species code
        that's an exact case-insensitive match of the filter?
        :return: True if match, else False
        """
        filter_upper = self._filter_name.upper()
        for candidate in self._available_species_model.items:
            candidate_code = candidate['species_code'].upper()
            if candidate_code == filter_upper:
                self._logger.info("Filter to candidate_code match ({})".format(self._filter_name))
                return True
        return False

    @pyqtProperty(QVariant, notify=selectedItemChanged)
    def counts_weights(self):
        return self._counts_weights

    @property
    def current_species_comp(self):
        return self._current_species_comp

    @pyqtProperty(QVariant, notify=availModelChanged)
    def currentSpeciesCompID(self):  # Primary Key
        return self._current_species_comp_id

    @currentSpeciesCompID.setter
    def currentSpeciesCompID(self, comp_id):
        try:
            # FIELD-1808: This caused a race condition, but seems fixed by FIELD-1828 now
            # FIELD-1959: Same issue? Trying to disable below
            # if comp_id == self._current_species_comp_id:
            #     self._logger.debug(f'currentSpeciesCompID: Already set to current species comp item ID {comp_id}')
            #     return
            self._current_species_comp_id = comp_id
            if comp_id is None:  # clear it
                self._logger.debug('Cleared currentSpeciesCompID')
                self._species_comp_items_model.clear()
                return
            self._current_species_comp = SpeciesCompositions.get(SpeciesCompositions.species_composition == comp_id)
            self._logger.info('Set Species Comp ID to {}'.format(self._current_species_comp_id))
            self._species_comp_items = self.get_species_comp_items(comp_id=comp_id)  # Load species
            item_count = len(self._species_comp_items)
            if item_count == 0:
                common_name = self._current_species_comp.catch.catch_category.catch_category_name
                self._logger.debug('Species comp item count is zero. Try to auto-add {}'.format(common_name))
                self.add_species_auto(self._current_species_comp.catch.catch_category)

            self._build_species_comp_items_model()
            self._counts_weights.currentSpeciesCompId = comp_id
        except SpeciesCompositionItems.DoesNotExist:
            self._logger.warning('No matching species composition id, no items in model.')
        finally:
            if self._current_species_comp_id is not None:
                self._logger.debug("Current species comp ID is not none: calculating total catch weight.")
                self._calculate_total_catch_weight_current()
            else:
                self._logger.debug("Current species comp ID is none: NOT calculating total catch weight.")

            self.availModelChanged.emit()

    @staticmethod
    def get_species_comp_items(comp_id):
        """
        Load species_composition_items from DB
        """
        return SpeciesCompositionItems.select(). \
            where((SpeciesCompositionItems.species_composition == comp_id))

    def _build_species_comp_items_model(self):
        self._logger.debug('Rebuilding CompositionItems (Species) model')
        comp_items = self.get_species_comp_items(comp_id=self._current_species_comp_id)
        self._species_comp_items_model.clear()
        for comp_item in comp_items:
            self._species_comp_items_model.add_species_item(comp_item)

    @pyqtProperty(QVariant, notify=selectedItemChanged)
    def currentSpeciesItemName(self):
        if self._current_speciescomp_item and self._current_speciescomp_item.species:
            return self._current_speciescomp_item.species.common_name
        else:
            return "None Selected"

    @pyqtSlot(name='clearCurrentSpeciesItemID')
    def clear_current_species_item_id(self):
        self._logger.debug(f'Cleared current species item ID, was {self.currentSpeciesCompID}')
        self._current_speciescomp_item = None
        self.counts_weights.currentSpeciesCompItem = None

    @property
    def current_species_item(self):
        return self._current_speciescomp_item

    @pyqtProperty(QVariant, notify=selectedItemChanged)
    def isRockfish(self):
        species_code = self.currentSpeciesItemCode
        if species_code in self._rockfish_codes:
            return True
        else:
            return False

    @pyqtProperty(QVariant, notify=selectedItemChanged)
    def currentSpeciesItemCode(self):
        return self._current_speciescomp_item.species.species_code \
            if self._current_speciescomp_item is not None and self._current_speciescomp_item.species is not None else None

    @pyqtProperty(QVariant, notify=selectedItemChanged)
    def currentSpeciesItemSpeciesID(self):
        """
        :return: The species ID for the current species item.
        """
        if self._current_speciescomp_item and self._current_speciescomp_item.species:
            return self._current_speciescomp_item.species.species
        else:
            return None

    @pyqtProperty(QVariant, notify=selectedItemChanged)
    def currentSpeciesCompItemID(self):
        return self._current_speciescomp_item.species_comp_item if self._current_speciescomp_item else None

    @currentSpeciesCompItemID.setter
    def currentSpeciesCompItemID(self, item_id):
        try:
            if item_id == self.currentSpeciesCompItemID:
                self._logger.debug(f'Already set to current species comp item ID {item_id}')
                return

            self._logger.debug(f'Set species item {item_id}, currently {self.currentSpeciesCompItemID}')
            self._current_speciescomp_item = SpeciesCompositionItems.get(
                SpeciesCompositionItems.species_comp_item == item_id)

            self._logger.info('Set species item {}'.format(self._current_speciescomp_item.species_comp_item))
            self.counts_weights.currentSpeciesCompItem = item_id
        except SpeciesCompositionItems.DoesNotExist:
            self.clear_current_species_item_id()
        except ValueError:
            self.clear_current_species_item_id()
        finally:
            self.selectedItemChanged.emit()

    @pyqtProperty(QVariant, notify=unusedSignal)
    def currentSpeciesLengthMeasuredFractionally(self):
        """
        Biospecimens of certain species (currently only one: Dungeness Crab)
        measure length in fractions of inches rather than the standard whole number of inches.

        TODO: Put list of fractionally measured species in LOOKUPS.
		
        :return: True if species does measure in fractions of inches else false (measure in whole inches).
        """
        dungeness_crab_species_id = 10061
        species_measured_fractionally = (dungeness_crab_species_id,)
        return self.currentSpeciesItemSpeciesID in species_measured_fractionally

    @pyqtProperty(QVariant, notify=availModelChanged)
    def observerSpeciesAvailableModel(self):
        return self._available_species_model

    @pyqtProperty(QVariant, notify=selectedModelChanged)
    def observerSpeciesSelectedModel(self):
        return self._species_comp_items_model

    @pyqtSlot(QVariant, name='addSpeciesCompItem')
    def add_species_comp_item(self, species_id):
        """
        Add species comp item to DB and model
        @param species_id: PK
        """
        if species_id is None:
            self._logger.error('Species ID is None')
            return
        if self._current_species_comp_id is None:
            self._logger.error('Current Species Comp ID is None')
            return
        try:
            user_id = ObserverDBUtil.get_current_user_id()
            current_date = ObserverDBUtil.get_arrow_datestr()
            SpeciesCompositionItems.create(species=species_id,
                                           species_composition=self._current_species_comp_id,
                                           created_by=user_id,
                                           created_date=current_date)
            self._build_species_comp_items_model()
        except Exception as e:
            self._logger.error('Add species comp item: {}'.format(e))
        finally:
            self.selectedModelChanged.emit()

    @pyqtSlot(QVariant, QVariant, result=bool, name='speciesWithDiscardReasonInSelected')
    def species_comp_item_exists(self, species, discard_reason):
        """ In the list of species selected for this catch,
            is there already an entry for the given species with the specified discard reason?

            Note: discard_reason can be None (not yet assigned).
        """
        if discard_reason is None:
            entry = [selectedSpecies for selectedSpecies in self._species_comp_items_model.items
                     if selectedSpecies["species"]["species"] == species and
                     selectedSpecies["discard_reason"] is None]
        else:
            entry = [selectedSpecies for selectedSpecies in self._species_comp_items_model.items
                     if selectedSpecies["species"]["species"] == species and
                     selectedSpecies["discard_reason"] == discard_reason]

        return len(entry) > 0

    @pyqtSlot(QVariant, name='addSpeciesAuto')
    def add_species_auto(self, catch_category):
        """
        Add species comp item to DB and model
        If it's the first item, this will be the first basket
        @param catch_category: catch category DB entry
        """
        species_common_name = catch_category.catch_category_name
        pacfin_code = catch_category.catch_category_code
        if species_common_name is None or self._current_species_comp_id is None:
            self._logger.error('Species Common Name / Current Species Comp ID is None')
            return
        try:
            fish_match = Species.get((fn.Lower(Species.common_name) == species_common_name.lower()) |
                                     (Species.pacfin_code == pacfin_code))
            user_id = ObserverDBUtil.get_current_user_id()
            current_date = ObserverDBUtil.get_arrow_datestr()
            SpeciesCompositionItems.create(species=fish_match.species,
                                           species_composition=self._current_species_comp_id,
                                           created_by=user_id,
                                           created_date=current_date)
            self._build_species_comp_items_model()
        except Species.DoesNotExist:
            self._logger.warning('No matching common name for {}, cannot auto-add.'.format(species_common_name))
        finally:
            self.selectedModelChanged.emit()

    @pyqtSlot(QVariant, name='delSpeciesCompItem')
    def del_species_comp_item(self, comp_item_id):
        ObserverDBUtil.del_species_comp_item(comp_item_id)
        self._build_species_comp_items_model()
        self.selectedModelChanged.emit()

    @pyqtSlot(name='clearDiscardReasons')
    def clear_discard_reasons(self):
        if not self._current_species_comp_id:
            self._logger.error(f'Tried to clear DR with no current ID.')
            return

        if self.counts_weights.dataExists:
            self._logger.error(f'Data exists, not clearing discard reasons.')
            return
        else:
            num = self._species_comp_items_model.count
            items = self.get_species_comp_items(comp_id=self._current_species_comp_id)
            if num != len(items):
                self._logger.error('Mismatch between DB item count and model count, abort.')
                return
            for i in items:
                self._logger.info(f'{i.species.common_name} discard reason to None')
                i.discard_reason = None
                i.save()
            self._logger.warning(f'Cleared discard items for {num} species')

    @pyqtProperty(bool, notify=isRetainedChanged)
    def isRetained(self):
        return self._is_retained

    @isRetained.setter
    def isRetained(self, is_retained):
        if is_retained is not None and self._is_retained != is_retained:
            self._is_retained = is_retained
            # self._logger.debug('isRetained set to {}'.format(self._is_retained))
            self.isRetainedChanged.emit()
            self.lookup_protocols_by_species_name(self._current_common_name)  # Reload

    @pyqtSlot(str, result=QVariant, name='lookupProtocolsBySpeciesName')
    def lookup_protocols_by_species_name(self, common_name):
        """
        Get protocol by Species Name, current disposition, stratum group
        TODO: Depth Stratum
        @param common_name: Common species name
        @return: str of protocols, comma separated e.g. 'FL,FC', notfound_value if not found
        """
        self._current_common_name = common_name
        self._logger.info('Looking up protocols for species {}'.format(common_name))
        notfound_value = '-'
        try:
            self._current_trip_id = ObserverDBUtil.db_load_setting("trip_number")
            species = Species.get(fn.lower(Species.common_name) == common_name.lower())
            disposition = 'R' if self._is_retained else 'D'
            self.isRetained = True if disposition == 'R' else False
            sampling_plans = SpeciesSamplingPlanLu.select().where(
                (SpeciesSamplingPlanLu.species == species.species_code) &
                (SpeciesSamplingPlanLu.disposition == disposition))

            num_plans = len(sampling_plans)
            if num_plans == 0:
                self._logger.info('Sampling plan returned no items for this species name')
                raise Species.DoesNotExist()
            elif num_plans > 1:

                self._logger.info(f'Sampling plan returned multiple ({num_plans}) items for this species. '
                                  f'Looking for fishery {ObserverDBUtil.get_current_fishery_id()}.')

            selected_plan = None
            biolist = None
            fishery_group_name = None
            my_fishery_id = ObserverDBUtil.get_current_fishery_id()
            my_gear_groups = self._get_gear_groups()
            for plan in sampling_plans:
                fishery_group_name = plan.stratum.fishery_group.name  # doing this a weird way with string parsing
                gear_type_group_id = plan.stratum.gear_type_group.group  # doing this the right way, but slow?
                fish_list = fishery_group_name[
                            fishery_group_name.find('(') + 1:
                            fishery_group_name.find(')')]
                fisheries = fish_list.split(',') if fish_list else None
                biolist = plan.biosample_list_lu.name.title() if plan.biosample_list_lu else None
                protocol = ProtocolGroups.get(ProtocolGroups.group == plan.protocol_group)
                stratum = StratumLu.get(StratumLu.stratum == plan.stratum)
                is_nearshore = True if stratum.range_min < 30 else False
                is_biolist_nearshore = self.is_biolist_nearshore()
                ignore_nearshore = True if (stratum.range_max <= 0 and stratum.range_min <= 0) or \
                                           (stratum.range_min < 0 and stratum.range_max < 0) else False
                self._logger.debug(f'Evaluating {plan.plan_name} -> {protocol.name} stratum {stratum.name}')
                if str(my_fishery_id) in fisheries and gear_type_group_id in my_gear_groups:
                    self._logger.debug(f'Fishery and gear type match. Evaluating depth strata.')
                    if self.isFixedGear:
                        if ignore_nearshore or is_nearshore == is_biolist_nearshore:
                            self._logger.debug(f'Matched stratum {stratum.name}')
                            selected_plan = protocol.name
                            break
                    else:
                        # If All, this is OK for Trawl
                        selected_plan = protocol.name
                        break

            if selected_plan:
                self._logger.debug(f'Returning protocol {selected_plan} for {fishery_group_name}, biolist {biolist}')
            else:
                self._logger.debug(f'No protocol found for {fishery_group_name}, biolist {biolist}')
            result = selected_plan if selected_plan else notfound_value
            self.currentProtocols = result
            self.currentBiolist = biolist if selected_plan else None
            return result

        except Species.DoesNotExist:
            self._logger.debug('Did not find {} for protocol lookup'.format(common_name))
            self.currentProtocols = notfound_value
            self.currentBiolist = None
            return self.currentProtocols
        except Exception as e:
            self._logger.error('Unexpected error in protocols: {}'.format(e))
            self.currentProtocols = notfound_value
            self.currentBiolist = None
            return notfound_value

    def is_biolist_nearshore(self):
        return self.current_fg_biolist == 4

    @pyqtProperty(str, notify=currentProtocolsChanged)
    def currentProtocols(self):
        return self.current_protocol_str

    @currentProtocols.setter
    def currentProtocols(self, value):
        # self._logger.debug('Current protocols set to {}.'.format(value))
        self.current_protocol_str = value
        self.current_protocol_set = set(value.split(',')) if value else None
        if self.current_protocol_set:
            if 'T' in self.current_protocol_set:  # note: T is the same as OT
                self.current_protocol_set.remove('T')
                self.current_protocol_set.add('OT')
            if 'FD' in self.current_protocol_set:  # same as FR (but dead-only)
                self.current_protocol_set.remove('FD')
                self.current_protocol_set.add('FR')
        # Currently 'SD' is handled in QML-land.
        self.currentProtocolsChanged.emit(value)

    @pyqtProperty(QVariant, notify=currentBiolistChanged)
    def currentBiolist(self):
        # Be aware this is for the current sampling plan, not the user's biolist
        return self.current_biolist

    @currentBiolist.setter
    def currentBiolist(self, value):
        self.current_biolist = value
        self.currentBiolistChanged.emit()

    @pyqtProperty(QVariant, notify=currentFGBiolistChanged)
    def currentFGBiolist(self):
        # Be aware this is for user's biolist
        return self.current_fg_biolist

    @currentFGBiolist.setter
    def currentFGBiolist(self, value):
        self.current_fg_biolist = value
        self.currentFGBiolistChanged.emit(value)

    @pyqtProperty(QVariant)
    def requiredProtocolsSLW(self):
        wt_vals = {'AL', 'FL', 'TL', 'CL', 'W', 'VL', 'CW'}

        need_length = bool(wt_vals & self.current_protocol_set)
        req_protocols = self.current_protocol_set - wt_vals
        if need_length:  # simplify all lengths to just FL
            req_protocols = {'FL'} | req_protocols
        return list(self.slw_protocols & req_protocols)

    @pyqtProperty(QVariant)
    def requiredProtocolsViability(self):
        if self.viability_protocols and self.current_protocol_set:
            return list(self.viability_protocols & self.current_protocol_set)
        else:
            return None

    @pyqtProperty(QVariant)
    def requiredProtocolsET(self):
        return list({'ET'} & self.current_protocol_set)

    @pyqtProperty(QVariant)
    def requiredProtocolsOT(self):
        return list({'OT'} & self.current_protocol_set)

    @pyqtProperty(QVariant)
    def requiredProtocolsTags(self):
        return list(self.tag_protocols & self.current_protocol_set)

    @pyqtProperty(QVariant)
    def requiredProtocolsBarcodes(self):
        return list(self.barcode_protocols & self.current_protocol_set) \
            if self.barcode_protocols and self.current_protocol_set else None

    # Biospecies Items boolean flags automatically set via lookup_protocols_by_species_name
    @pyqtProperty(bool, notify=currentProtocolsChanged)
    def bio_SLW_enabled(self):  # Sex/ Length/ Weight
        if self.current_protocol_set is not None:
            return bool(self.slw_protocols & self.current_protocol_set)
        else:
            return False

    @pyqtProperty(bool, notify=currentProtocolsChanged)
    def bio_VP_enabled(self):  # Viability/ Presence
        if self.current_protocol_set is not None:
            return bool(self.viability_protocols & self.current_protocol_set)
        else:
            return False

    @pyqtProperty(bool, notify=currentProtocolsChanged)
    def bio_ET_enabled(self):  # Existing Tags / Photos
        if self.current_protocol_set is not None:
            return bool(self.etag_protocols & self.current_protocol_set)
        else:
            return False

    @pyqtProperty(bool, notify=currentProtocolsChanged)
    def bio_BC_enabled(self):  # Barcodes & Tags
        if self.current_protocol_set is not None:
            return bool(self.barcode_protocols & self.current_protocol_set)
        else:
            return False

    # Slot to check for specific buttons or controls via protocol, e.g. WS
    @pyqtSlot(str, result=bool, name='bioControlEnabled')
    def bio_control_enabled(self, short_name):
        if self.current_protocol_set is not None:
            is_in = short_name in self.current_protocol_set
            # self._logger.debug(f"Protocol '{short_name}' is in protocol set {self.current_protocol_set}.")
            return bool(is_in)
        else:
            return False

    # Enable visibility for sex-related protocols
    @pyqtProperty(bool, notify=currentProtocolsChanged)
    def bio_sex_enabled(self):
        if self.current_protocol_set is not None:
            return bool({'S', 'SD'} & self.current_protocol_set)
        else:
            return False

    # Enable visibility for length-related protocols
    @pyqtProperty(bool, notify=currentProtocolsChanged)
    def bio_length_enabled(self):
        if self.current_protocol_set is not None:
            return bool({'AL', 'FL', 'TL', 'CL', 'W', 'VL', 'CW'} & self.current_protocol_set)
        else:
            return False

    # Enable visibility for weight-related protocols
    @pyqtProperty(bool, notify=currentProtocolsChanged)
    def bio_weight_enabled(self):
        if self.current_protocol_set is not None:
            return bool({'WT'} & self.current_protocol_set)
        else:
            return False

    @pyqtProperty(QVariant, notify=discardReasonChanged)
    def discardReason(self):
        if self._current_speciescomp_item:
            return self._current_speciescomp_item.discard_reason

    @discardReason.setter
    def discardReason(self, value):
        self._handle_discard_reason_selected(value)
        self.discardReasonChanged.emit(value)

    @pyqtProperty(QVariant, notify=totalCatchWeightChanged)
    def totalCatchWeight(self):
        return self._total_haul_weight

    @pyqtProperty(QVariant, notify=totalCatchWeightFGChanged)
    def totalCatchWeightFG(self):
        return self._total_set_weight

    @pyqtProperty(QVariant, notify=totalCatchCountChanged)
    def totalCatchCount(self):
        return self._total_haul_count


class TestObserverSpecies(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.obs = ObserverSpecies(None)

    def test_lookup_protocols(self):
        tests = [['Pacific Cod', 'FL'],
                 ['Shortraker Rockfish', 'FL'],
                 ['Unknown Fish Name', '-'],
                 ['unknown Rockfish', 'FL'],
                 ]

        for testcase in tests:
            species_name = testcase[0]
            expected = testcase[1]
            protocols = self.obs.lookup_protocols_by_species_name(species_name)
            self.assertEqual(protocols, expected, '{} expected protocol {}, got {}'.format(species_name,
                                                                                           expected, protocols))

    def test_species_correlation(self):
        """
        Tests that there are records in SPECIES_CORRELATION, make sure we have continuous entries for weights
        @return:
        """
        species_q = SpeciesCorrelation.select().order_by(SpeciesCorrelation.species_correlation)
        logging.debug('Test got {} items for SPECIES_CORRELATION table.'.format(len(species_q)))
        self.assertGreater(len(species_q), 240)
        next_expected_val = None
        for sc in species_q:
            self.assertEqual(sc.species, 10141)
            if not next_expected_val:
                next_expected_val = sc.length
            self.assertEqual(sc.length, next_expected_val)
            next_expected_val = sc.length + 1  # verify we cover continuous range            )


class TestTrawlFrequentSpecies(unittest.TestCase):
    """ Use a different setting value parameter name than SETTINGS_PARAMETER_NAME,
        Observer.db here may be being used for dev work.
    """

    def __init__(self, *args, **kwargs):
        super(TestTrawlFrequentSpecies, self).__init__(*args, **kwargs)
        self.TEST_SETTINGS_PARAMETER_NAME = TrawlFrequentSpecies.SETTINGS_PARAMETER_NAME + "_TESTING123"
        self._logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    def setUp(self):
        self._delete_test_record()
        self._insert_default_test_record()
        # Use the optional __init__ parameter to specify the key value for the setting.
        self.tfs = TrawlFrequentSpecies(self.TEST_SETTINGS_PARAMETER_NAME)

    def _delete_test_record(self):
        """ Remove the test setting."""
        delete_q = Settings.delete().where(Settings.parameter == self.TEST_SETTINGS_PARAMETER_NAME)
        delete_q.execute()

    def _insert_default_test_record(self):
        test_list_as_json = json.dumps(TrawlFrequentSpecies.DEFAULT_TRAWL_FREQUENT_SPECIES)
        self._logger.debug("Default test list as JSON = {}".format(test_list_as_json))
        insert_q = Settings.insert(parameter=self.TEST_SETTINGS_PARAMETER_NAME,
                                   value=test_list_as_json)
        insert_q.execute()

    def tearDown(self):
        pass
        self._delete_test_record()

    def test_list_is_default(self):
        self.assertEqual(list(TrawlFrequentSpecies.DEFAULT_TRAWL_FREQUENT_SPECIES),
                         self.tfs.get_species_codes())

    def test_entry_from_db_is_read(self):
        # Get the current entry, if any, ready to restore at conclusion
        select_q = Settings.select().where(
            Settings.parameter == self.TEST_SETTINGS_PARAMETER_NAME)
        orig_list = json.loads(select_q.get().value)
        self._logger.debug("Orig list = {}".format(orig_list))

        test_value = None
        for candidate_test_value in range(900, 1000):
            if candidate_test_value not in orig_list:
                test_value = candidate_test_value
                break

        self.assertIsNotNone(test_value, "Unexpectedly, every value from 900 to 1000 was in orig. list")
        self._logger.info("Adding {} to value field.".format(test_value))

        # Add a species code to the db entry
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

        # 2. Verify that the pre-existing frequent species code does NOT get updated value -
        #   that it doesn't do a re-pull from the db on every get of its property
        self.assertNotIn(test_value, self.tfs.get_species_codes())

        # 3. Instantiate a new copy of frequent species code and verify it DOES have the
        #   new value in the list.
        newtfs = TrawlFrequentSpecies(self.TEST_SETTINGS_PARAMETER_NAME)
        self.assertIn(test_value, newtfs.get_species_codes())


class TestSpeciesFilter(unittest.TestCase):
    def test_multiple_word_match(self):

        test_list = [
            {'species_code': '0000',
             'common_name': 'abc def ghi'}
        ]
        matches = ObserverSpecies._filter_species_list(test_list, 'abc de')
        self.assertEqual(1, len(matches))

    def test_matches_code(self):
        test_list = [
            {'species_code': '1234',
             'common_name': 'Abyssal Grenadier'}
        ]
        matches = ObserverSpecies._filter_species_list(test_list, '12')
        self.assertEqual(1, len(matches))
        self.assertEqual(test_list[0], matches[0])

    def test_matches_later_word_of_common_name(self):
        test_list = [
            {'species_code': '0000',
             'common_name': 'Abyssal Grenadier'}
        ]
        matches = ObserverSpecies._filter_species_list(test_list, 'gren')
        self.assertEqual(1, len(matches))
        self.assertEqual(test_list[0], matches[0])

    def test_empty_string_matches_all(self):
        test_list = [
            {'species_code': '0000',
             'common_name': 'Abyssal Grenadier'},
            {'species_code': '0001',
             'common_name': 'abc def ghi'},
            {'species_code': '0002',
             'common_name': 'A weird name - should not matter'},
        ]
        matches = ObserverSpecies._filter_species_list(test_list, '')
        self.assertEqual(3, len(matches))
        self.assertEqual(test_list, matches)

    def test_species_cc_list(self):
        test_list = [(None, []),
                     (1523, [10511]),
                     (1434, [10454, 10071, 10057])
                     ]

        # test object instantiation
        for t in test_list:
            assoc = TrawlAssociatedSpecies(catch_category_id=t[0])
            self.assertEqual(sorted(assoc.get_species_ids()), sorted(t[1]))

        # test setting cc_id
        assoc = TrawlAssociatedSpecies()
        for t in test_list:
            assoc.set_catch_category(t[0])
            self.assertEqual(sorted(assoc.get_species_ids()), sorted(t[1]))
