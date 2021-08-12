# -----------------------------------------------------------------------------
# Name:        Hauls.py
# Purpose:     Support class for Haul (Observer)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     July, 2016
# License:     MIT
# ------------------------------------------------------------------------------
import random
from typing import Dict, Iterable

from peewee import fn, JOIN
from PyQt5.QtCore import pyqtProperty, QVariant, QObject, Qt, pyqtSignal, pyqtSlot

from py.observer.LogbookObserverRetainedModel import ObserverRetainedModel
from py.observer.LogbookVesselRetainedModel import VesselRetainedModel
from py.observer.HaulSetModel import HaulSetModel
from py.observer.ObserverDBModels import FishingActivities, CatchCategories, Catches, Comment
from py.observer.ObserverDBUtil import ObserverDBUtil
from py.observer.ObserverDBErrorReportsModels import TripIssues
from py.observer.ObserverErrorReports import ThreadTER, TripChecksOptecsManager
from py.observer.ObserverFishingLocations import ObserverFishingLocations

import logging


class Hauls(QObject):
    modelChanged = pyqtSignal(name='modelChanged')
    currentHaulIdChanged = pyqtSignal(str, name='currentHaulIdChanged')
    parameterChanged = pyqtSignal(name='parameterChanged')
    obsRetModelChanged = pyqtSignal(name='obsRetModelChanged')
    maxObsRetModelLengthChanged = pyqtSignal(int, name='maxObsRetModelLengthChanged')
    maxVesselRetModelLengthChanged = pyqtSignal(int, name='maxVesselRetModelLengthChanged')
    currentBiolistNumChanged = pyqtSignal(name='currentBiolistNumChanged')
    unusedSignal = pyqtSignal(name='unusedSignal')  # quiet warnings
    otcWeightChanged = pyqtSignal(name='otcWeightChanged')

    def __init__(self, db):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._data = db
        self._hauls_model = HaulSetModel()
        self._current_haul = None
        self._internal_haul_idx = None  # FramListModel index
        self._hauls_count = 0
        self._trip_id = None
        self._fishing_locations = ObserverFishingLocations()

        self._beaufort = db.beaufort
        self._gearperf = db.gearperf

        self._obs_ret_models = dict()
        self._obs_ret_max_count = 0
        self._vessel_ret_models = dict()
        self._vessel_ret_max_count = 0
        # Hauls fields that must be specified in UI (can't be left empty)
        self._required_field_names = (  # As known in peewee
            'observer_total_catch',  # Visual OTC
            'otc_weight_method',
            'brd_present',
            # No: 'fit',
            # No: 'cal_weight',  # Has 'No Scale' value if not-calibrated.
            'gear_type',
            'gear_performance',
            'beaufort_value',
        )
        self._thread_ter = None  # Runs TER in background

        random.seed()  # ensure device_random_seed is randomly seeded
        self._device_random_seed = int(ObserverDBUtil.get_or_set_setting('biolist_rng_seed', random.randint(1, 10000)))
        self._trip_seed = 0

    @pyqtSlot(name="youAreUp")
    def you_are_up(self):
        """
        Called by ObserverSM.qml when context switches to Hauls screen.
        Used to pull counts of haul-level issues from the current trip's last Trip Error Report, if any.
        :return: None
        """
        self._logger.info(f"Screen is active. Current TripID={self._trip_id}.")
        self._logger.info(f"Count of hauls (from HaulsModel)={self._hauls_model.count}.")
        current_user_id = ObserverDBUtil.get_current_user_id()

        # If a Trip Error Report has been run for this trip, get the latest run's haul-level error counts, per-haul.
        trip_issues, run_date = TripChecksOptecsManager.get_issues_from_last_ter_run(self._trip_id, self._logger)
        if not trip_issues:
            for row in range(self._hauls_model.count):
                self._hauls_model.setProperty(row, "errors", "N/A")
            self._logger.debug("No Trip Error Report has been run for this trip yet. Haul-level error counts to N/A.")
        else:
            haul_error_counts = self._calculate_per_haul_errors(trip_issues)

            view_model_rows = self._hauls_model.items
            # Update view model with haul-level errors, on a haul-by-haul basis
            for row_idx in range(self._hauls_model.count):
                view_model_row = view_model_rows[row_idx]
                haul_num = int(view_model_row["fishing_activity_num"])
                errors_this_haul = haul_error_counts[haul_num] \
                    if haul_num in haul_error_counts else 0
                self._hauls_model.setProperty(row_idx, "errors", str(errors_this_haul))
            self._logger.debug(f"Updated view model with Trip Error Report with run date {run_date}.")

    @staticmethod
    def _calculate_per_haul_errors(trip_issues: Iterable) -> Dict[int, int]:
        per_haul_errors = {}  # Key: haul number. TODO: Use default dict
        for issue in trip_issues:
            # TODO: only count haul-level errors or below
            # Perhaps done. If there's no haul number, is the issue not haul-related?
            if issue.fishing_activity_num is None:
                pass
            elif issue.fishing_activity_num not in per_haul_errors:
                per_haul_errors[int(issue.fishing_activity_num)] = 1
            else:
                per_haul_errors[int(issue.fishing_activity_num)] += 1
        return per_haul_errors

    def load_hauls(self, trip_id):
        """
        Load hauls from database, build FramListModel
        :return:
        """
        self._hauls_model.clear()
        hauls_q = FishingActivities.select().where(FishingActivities.trip == trip_id)
        self._hauls_count = hauls_q.count()
        if self._hauls_count > 0:
            for haul in hauls_q:  # Build FramListModel
                self._hauls_model.add_haul(haul)
        self.modelChanged.emit()
        self._trip_id = trip_id
        self._set_trip_biolist_seed(trip_id)
        return self._hauls_count

    @pyqtSlot(name='reset')
    def reset(self):
        """
        Clear hauls, reset states
        """
        self._current_haul = None
        self._hauls_model = HaulSetModel()

    @pyqtProperty(QVariant, notify=modelChanged)
    def HaulsModel(self):
        return self._hauls_model

    @pyqtProperty(QVariant, notify=modelChanged)
    def SetsModel(self):
        """
        TODO Fixed Gear
        """
        return self._sets_model

    @pyqtProperty(QVariant, notify=currentHaulIdChanged)
    def locations(self):
        return self._fishing_locations

    @pyqtProperty(int, notify=modelChanged)
    def haul_count(self):
        return self._hauls_count

    @property
    def current_haul(self):
        return self._current_haul

    @pyqtProperty(str)
    def current_fishing_activity_id(self):
        return str(self._current_haul.fishing_activity) if self._current_haul else None

    @pyqtProperty(str, notify=currentHaulIdChanged)
    def currentHaulId(self):
        return str(self._current_haul.fishing_activity_num) if self._current_haul else None

    @pyqtProperty(QVariant, notify=currentHaulIdChanged)
    def currentHaulDBId(self):
        return self._current_haul.fishing_activity if self._current_haul else None

    @pyqtSlot()
    def refresh(self):
        """
        Called to reload haul info (currently used for changes in Locations model)
        @return:
        """
        self.load_hauls(self._trip_id)

    @currentHaulId.setter
    def currentHaulId(self, current_id):
        """
        Assigned in HaulsScreen.  Also sets current_haulset_id with dbid here
        :param current_id: haul number (not DB ID)
        :return: None
        """
        self._logger.debug('Set currentHaul using ID {}'.format(current_id))
        try:
            self._current_haul = FishingActivities.get(
                FishingActivities.trip == self._trip_id,
                FishingActivities.fishing_activity_num == current_id
            )
            # FIELD-1471: setting db id for downstream use in baskets
            ObserverDBUtil.db_save_setting('current_haulset_id', self._current_haul.fishing_activity)
            self._logger.debug(f"Setting current_haulset_id to {self._current_haul.fishing_activity}")
            self._internal_haul_idx = self._hauls_model.get_item_index('fishing_activity_num',
                                                                       self._current_haul.fishing_activity_num)
            self._fishing_locations.load_fishing_locations(fishing_activity_id=self._current_haul.fishing_activity)
        except FishingActivities.DoesNotExist:
            self._logger.info("Can't get haul ID for trip {}, num {}".format(self._trip_id, current_id))
            self._current_haul = None
            return

        self.modelChanged.emit()

    @pyqtSlot(str, result=bool, name='removeHaul')
    def removeHaul(self, haul_id):
        result = self.HaulsModel.remove_haul(haul_id)
        self.currentHaulId = self.HaulsModel.most_recent_haul_id()
        return result

    @pyqtSlot(str, result=str, name='getBeaufortDesc')
    def getBeaufortDesc(self, value):
        """
        Given a single digit value, get description of beaufort scale value
        @param value: '0' - '9'
        @return: str description
        """
        return self._beaufort.get(value, 'No Description')

    @pyqtSlot(str, result=str, name='getGearPerfDesc')
    def getGearPerfDesc(self, value):
        """
        Given a single digit value, get description of gear perf value
        @param value: '1' - '7'
        @return: str description
        """
        return self._gearperf.get(value, 'No Description')

    def _set_cur_prop(self, model_prop, value):
        """
        Helper function - set current haul properties in FramListModel
        @param model_prop: property name
        @param value: value to store
        @return:
        """
        self._hauls_model.setProperty(self._internal_haul_idx,
                                      model_prop, value)

    @pyqtSlot(str, result='QVariant', name='getDataOrHaulDefault')
    def get_data_or_default(self, data_name):
        """
        If a Haul #1 has set this data, then get that (and set it.)
        @param data_name: name of data
        @return: db value or default
        """

        haul_data = self.getData(data_name=data_name)
        if haul_data is not None and haul_data != '':
            return haul_data
        elif self._current_haul.fishing_activity_num == 1 and data_name != 'efp':
            self._logger.debug(f'First haul, not retrieving default for {data_name}')
            return None
        else:  # Get defaults from first_haul
            try:
                first_haul = FishingActivities.get((FishingActivities.trip == self._current_haul.trip),
                                                   (FishingActivities.fishing_activity_num == 1))
                if data_name == 'target_strategy':
                    default_data = self._get_target_code(first_haul.target_strategy)
                    self.setData(data_name, default_data)
                    return default_data
                elif data_name == 'gear_type':
                    default_data = first_haul.gear_type
                    self.setData(data_name, default_data)
                    return default_data
                elif data_name == 'efp':
                    default_data = self._get_efp(first_haul)
                    efp_data = True if default_data else None  # For DB EFP special case
                    self.setData(data_name, efp_data)
                    return default_data
                elif data_name == 'brd_present':
                    default_data = self._get_brd_present(first_haul)
                    self.setData(data_name, default_data)
                    return default_data
                else:
                    self._logger.error(f'Get Default requested, but field {data_name} is not default-approved.')
                    return ''
            except Exception as e:
                self._logger.error(f'Cannot get default {data_name}: {e}')
                return ''

    @staticmethod
    def _get_efp(fishing_activity):
        return True if fishing_activity.efp == 'EFP' else None

    @staticmethod
    def _get_efp_local(fishing_activity):
        # tri-state: 1, 0, None
        val = fishing_activity.efp_localonly
        if val == 1:
            return True
        elif val == 0:
            return False
        else:
            return None

    @staticmethod
    def _get_brd_present(fishing_activity):
        if fishing_activity.brd_present is not None:
            return True if fishing_activity.brd_present == 'TRUE' else False
        else:
            return None

    @pyqtSlot(str, result='QVariant', name='getData')
    def getData(self, data_name):
        """
        Shortcut to get data from the DB that doesn't deserve its own property
        (Note, tried to use a dict to simplify this, but DB cursors were not updating)
        :return: Value found in DB
        """
        if self._current_haul is None:
            logging.warning('Attempt to get data with null current haul.')
            return None
        data_name = data_name.lower()
        return_val = None
        if data_name == 'observer_total_catch':
            return_val = self._current_haul.observer_total_catch
        elif data_name == 'otc_weight_method':
            return_val = self._current_haul.otc_weight_method
        elif data_name == 'fit':
            return_val = self._current_haul.fit
        elif data_name == 'brd_present':
            return self._get_brd_present(self._current_haul)
        elif data_name == 'efp':
            # Center IFQ Database (target of DB Sync) convention: 'EFP' or null.
            efp_val = self._get_efp(self._current_haul)
            local_efp_val = self._get_efp_local(self._current_haul)
            return local_efp_val if local_efp_val is not None else efp_val  # tristate bool
        elif data_name == 'cal_weight':
            return_val = self._current_haul.cal_weight
        elif data_name == 'beaufort_value':
            return_val = self._current_haul.beaufort_value
        elif data_name == 'gear_performance':
            return_val = self._current_haul.gear_performance
        elif data_name == 'target_strategy':
            return_val = self._get_target_code(self._current_haul.target_strategy)
        elif data_name == 'gear_type':
            return_val = self._current_haul.gear_type
        else:
            logging.warning('Attempt to get unknown data name: {}'.format(data_name))

        return '' if return_val is None else return_val

    @pyqtProperty(int, notify=unusedSignal)
    def retainedHaulWeight(self):
        """
        assumes fishing_activity_id is loaded, catch if not???
        left joins, should always return a number, even if no retained
        :return: int (sum of retained catch weights for haul)
        """
        return FishingActivities.select(fn.COALESCE(fn.sum(Catches.catch_weight), 0))\
            .join(Catches, JOIN.LEFT_OUTER).where(
            (Catches.fishing_activity == self._current_haul.fishing_activity) &
            (Catches.catch_disposition == 'R')
        ).scalar()

    @pyqtSlot(str, QVariant, name='setData')
    def setData(self, data_name, data_val):
        """
        Set misc data to the DB
        :return:
        """
        if self._current_haul is None:
            logging.warning('Attempt to set data with null current haul.')
            return
        data_name = data_name.lower()
        if data_name == 'observer_total_catch':
            self._current_haul.observer_total_catch = float(data_val) if data_val else 0.0
        elif data_name == 'otc_weight_method':
            self._current_haul.otc_weight_method = int(data_val) if data_val else 0
        elif data_name == 'fit':
            # FIELD-1374: Numpad Backspace (<-) key returns empty string rather than 0. Treat as '0'.
            fit_val = data_val if data_val != "" else '0'
            self._current_haul.fit = str(fit_val)
        elif data_name == 'brd_present':
            if data_val:
                self._current_haul.brd_present = 'TRUE'
            else:
                self._current_haul.brd_present = 'FALSE'
        elif data_name == 'efp':
            # Center IFQ Database (target of DB Sync) convention: 'EFP' or ''.
            if data_val:
                self._current_haul.efp = 'EFP'
                self._current_haul.efp_localonly = 1
            else:
                self._current_haul.efp = None  # NULL in Database, but False for model prop
                self._current_haul.efp_localonly = 0
        elif data_name == 'cal_weight':
            self._current_haul.cal_weight = data_val
        elif data_name == 'beaufort_value':
            self._current_haul.beaufort_value = data_val
        elif data_name == 'gear_performance':
            self._current_haul.gear_performance = data_val
        elif data_name == 'target_strategy':
            self._current_haul.target_strategy = self._lookup_target_strat_id(data_val)
            # Translate for listview on HaulsScreen
            self._set_cur_prop('target_strategy_code',
                               self._get_target_code(self._current_haul.target_strategy))
        elif data_name == 'gear_type':
            if ' ' in data_val:
                data_val = data_val.split(' ')[0]  # Extract value
                data_val = str(int(data_val))  # remove leading zero
            self._current_haul.gear_type = data_val
        else:
            logging.warning('Attempt to set unknown data name: {}'.format(data_name))
            return
        self._current_haul.save()
        self._set_cur_prop(data_name, data_val)

        logging.debug('Set {} to {}'.format(data_name, data_val))
        self.modelChanged.emit()

        if data_name == 'observer_total_catch':
            self.otcWeightChanged.emit()

    def _lookup_target_strat_id(self, strat: str):
        """
        Use first 4 chars as a code and look up CATCH_CATEGORY_ID
        @param strat: code + optional text
        @return: int ID
        """
        if strat is None or len(strat) < 3:
            self._logger.debug('Got bad strat ID to look up: {}'.format(strat))
            return

        find_code = strat.split(' ')[0]
        try:
            found = CatchCategories.get(CatchCategories.catch_category_code % find_code)
            self._logger.info('Found ID {} for {}'.format(found.catch_category, find_code))
            return found.catch_category
        except CatchCategories.DoesNotExist:
            self._logger.warning('Did not find ID for {}'.format(find_code))
            return None

    def _get_target_code(self, target_id: int):
        """
        Find pacfic code for id
        @param target_id: catch_category_id
        @return: int ID
        """
        if target_id is None:
            return ''
        try:
            found = CatchCategories.get(CatchCategories.catch_category == target_id)
            return found.catch_category_code
        except CatchCategories.DoesNotExist:
            self._logger.warning('Did not find code for {}'.format(target_id))
            return None

    @pyqtProperty(int, notify=maxObsRetModelLengthChanged)
    def maxObsRetModelLength(self):
        return self._obs_ret_max_count

    @pyqtProperty(int, notify=maxVesselRetModelLengthChanged)
    def maxVesselRetModelLength(self):
        return self._vessel_ret_max_count

    @pyqtProperty(QVariant, notify=unusedSignal)
    def requiredHaulFieldsAreSpecified(self):
        """
        Have all the prerequisite fields in the Haul Details screen been filled in for the current haul
        so that navigation to Catch screen is allowed?

        :return: True if gear type is not empty.
                False otherwise.
        """
        is_filled = [self.required_haul_field_is_specified(f) for f in self._required_field_names]

        result = all(is_filled)

        self._logger.debug("{}OK to navigate to Catch tab.".format("" if result else "Not "))
        return result

    @pyqtSlot(QVariant, result=QVariant, name='requiredHaulFieldIsSpecified')
    def required_haul_field_is_specified(self, field_name):
        """
            Expecting peewee Hauls field name, not name of text field in QML
            Return True if the field has a value, False otherwise.
            Raise exception if unknown field name.
        """
        if field_name not in self._required_field_names:
            raise Exception(f'Unexpected peewee Hauls field name: {field_name}')
        field_data = self.getData(field_name)
        if field_data is None:
            field_ok = False
        else:
            if isinstance(field_data, str):
                field_ok = len(field_data) > 0
            else:
                field_ok = True

        self._logger.debug(f'{field_name} -> {field_data} is {"" if field_ok else "not "}specified.')
        return field_ok

    @pyqtProperty(QVariant, notify=unusedSignal)
    def isCalWeightSpecified(self):
        cal_wt = self.getData('cal_weight')
        if cal_wt:
            return True

        return False

    @pyqtProperty(bool, notify=unusedSignal)
    def isShrimpGear(self):
        return self.getData('gear_type') in ['12', '13']

    @pyqtSlot(QVariant, result=QVariant, name='getObserverRetModel')
    def getObserverRetModel(self, haul_db_id):
        """
        Load observer retained model
        @param haul_db_id: Database ID
        @return:
        """
        new_model = ObserverRetainedModel()
        new_model.load_observer_retained(haul_db_id)
        if new_model.count > self._obs_ret_max_count:
            self._obs_ret_max_count = new_model.count
            self.maxObsRetModelLengthChanged.emit(self._obs_ret_max_count)
        self._obs_ret_models[haul_db_id] = new_model
        return self._obs_ret_models[haul_db_id]

    @pyqtSlot(QVariant, str, result=bool, name='ccIsInObserverRetModel')
    def ccIsInObserverRetModel(self, haul_db_id, catch_category_code):
        """
        Given a catch category and a haul ID, return whether
        this catch category is in the list of Observer-Retained catch categories.
        @param haul_db_id: Database ID
        @param catch_category_code: string (category code such as 'ALBC')
        @return: True if  catch_category_code is in list of observer-retained categories.
        """
        if haul_db_id not in self._obs_ret_models:
            self._logger.debug('ccIsInObserverRetModel unexpectedly called before getObserverRetModel')
            new_model = ObserverRetainedModel()
            new_model.load_observer_retained(haul_db_id)
            self._obs_ret_models[haul_db_id] = new_model

        observer_retained_model = self._obs_ret_models[haul_db_id]
        return observer_retained_model.is_item_in_model('cc_code', catch_category_code)

    @pyqtSlot(QVariant, result=QVariant, name='getVesselRetModel')
    def getVesselRetModel(self, haul_db_id):
        new_model = VesselRetainedModel()
        new_model.load_vessel_retained(haul_db_id)
        self._update_vessel_ret_max(new_model)
        self._vessel_ret_models[haul_db_id] = new_model

        return self._vessel_ret_models[haul_db_id]

    @pyqtSlot(QVariant, QVariant, name='addVesselRetained')
    def addVesselRetained(self, haul_db_id, vessel_info):
        self._vessel_ret_models[haul_db_id].add_vessel_ret(haul_db_id, vessel_info)
        self._update_vessel_ret_max(self._vessel_ret_models[haul_db_id])

    def _update_vessel_ret_max(self, model):
        if model.count > self._vessel_ret_max_count:
            self._vessel_ret_max_count = model.count
            # self._logger.info('Vessel ret max now{}'.format(self._vessel_ret_max_count))
            self.maxVesselRetModelLengthChanged.emit(self._vessel_ret_max_count)

    @pyqtSlot(QVariant, result=bool, name='checkHaulEmpty')
    def check_haul_empty(self, haul_id):
        """
        Queries DB to see if there are data records associated with a haul
        @param haul_id: DBID
        @return: True if haul is empty and can be deleted, False otherwise
        """
        if not haul_id:
            self._logger.warning('Invalid haul ID passed to check_haul_empty.')
            return False

        catches_q = Catches.select().where(Catches.fishing_activity == haul_id)
        if len(catches_q) > 0:
            self._logger.debug('Haul {} is not empty, has {} catches associated.'.format(haul_id, len(catches_q)))
            return False
        return True

    @pyqtSlot(QVariant, result=int)
    def create_haul(self, haul_num):
        """
        @param haul_num: ID local to this trip
        @return: haul db ID
        """
        self.load_hauls(trip_id=self._trip_id)
        observer_id = ObserverDBUtil.get_current_user_id()
        newhaul = FishingActivities.create(trip=self._trip_id,
                                           fishing_activity_num=haul_num,
                                           created_by=observer_id,
                                           created_date=ObserverDBUtil.get_arrow_datestr())
        logging.info(
            'Created FishingActivities (haul {}) for trip={}'.format(newhaul.fishing_activity_num, newhaul.trip))

        self.HaulsModel.add_haul(newhaul)
        self.currentHaulId = newhaul.fishing_activity_num
        self._create_biolist_comment()
        return int(newhaul.fishing_activity)

    @pyqtSlot(QVariant, result=bool, name='deleteHaul')
    def delete_haul(self, haul_id):
        if haul_id is None or not self.check_haul_empty(haul_id):
            return

        trip_id = self._trip_id
        self._current_haul = None  # FIELD-1817 always clear current haul ID if deleting


        # Delete from DB
        haul = FishingActivities.get(FishingActivities.fishing_activity == haul_id)
        ObserverDBUtil.log_peewee_model_instance(self._logger, haul, 'Deleting haul')
        haul.delete_instance(recursive=True)

        # Delete from model
        result = self._hauls_model.remove_haul_set(haul_id)

        # Check for hauls with greater fishing_activity_num # than this one, and if found, decrement them.
        renumber_hauls = FishingActivities.select().where(
            (FishingActivities.fishing_activity > haul_id) & (FishingActivities.trip == trip_id))
        for h in renumber_hauls:
            old_num = h.fishing_activity_num
            h.fishing_activity_num -= 1
            h.save()
            fishing_number_row = self._hauls_model.get_haul_set_index(h.fishing_activity)
            self._logger.info(f'Renumbered FISHING_ACTIVITY_NUM {old_num} to {h.fishing_activity_num} for haul {h.fishing_activity}')
            self._hauls_model.setProperty(fishing_number_row, 'fishing_activity_num', h.fishing_activity_num)

        return result

    # TODO: Create setter like in FG?
    @pyqtProperty(QVariant, notify=currentBiolistNumChanged)
    def currentBiolistNum(self):
        return self._get_biolist_num()

    def _create_biolist_comment(self):
        """
        Replaces _save_notes_biolist_num func
        Adds biolist string to comment table instead of saving directly to fishing_activity.notes.
        Comment record is picked up for comment parsing later (FIELD-2071)
        :return: None
        """
        if not self._current_haul:
            self._logger.error('Tried to save biolist num, but current haul not set.')
            return
        BIOLIST_NOTE_PREFIX = 'Biolist #'
        APPSTATE = f"haul_details_state::Haul {self.currentHaulId} Details"  # could make a param, but shouldn't change

        # check if biolist comment already exists
        existing_comments = Comment.select().where(
            (Comment.trip == self._current_haul.trip) &
            (Comment.fishing_activity == self._current_haul.fishing_activity) &
            (fn.Lower(Comment.comment).contains(BIOLIST_NOTE_PREFIX.lower()))
        )

        if not existing_comments:
            Comment.create(
                username=ObserverDBUtil.get_setting('current_user'),
                comment_date=ObserverDBUtil.get_arrow_datestr(),
                comment=f"{BIOLIST_NOTE_PREFIX}{self.currentBiolistNum}",
                appstateinfo=APPSTATE,
                trip=self._current_haul.trip,
                fishing_activity=self._current_haul.fishing_activity
            )
            self._logger.debug(f"{BIOLIST_NOTE_PREFIX}{self.currentBiolistNum} comment created.")
        else:  # not sure if this will ever get used for trawl, but will update if necessary
            query = Comment.update(
                username=ObserverDBUtil.get_setting('current_user'),
                comment_date=ObserverDBUtil.get_arrow_datestr(),
                comment=f"{BIOLIST_NOTE_PREFIX}{self.currentBiolistNum}",
                appstateinfo=APPSTATE,
            ).where(
                (Comment.fishing_activity == self._current_haul.fishing_activity) &
                (Comment.trip == self._current_haul.trip) &
                (Comment.comment.regexp('^' + BIOLIST_NOTE_PREFIX + '\d+$'))  # starts with Biolist #, ends with nums
            )
            query.execute()
            self._logger.debug(f"{BIOLIST_NOTE_PREFIX}{self.currentBiolistNum} comment updated.")

    @pyqtSlot(name='updateBiolistNote')
    def _save_notes_biolist_num(self):
        """
        Store BIOLIST num to notes
        NOTE: most functionality here has been replaced by self._create_biolist_comment
        :return:
        """
        if not self._current_haul:
            self._logger.error('Tried to save biolist num, but current haul not set.')
            return
        notes = self._current_haul.notes if self._current_haul.notes else ''
        BIOLIST_NOTE_PREFIX = 'Biolist #'
        if notes.find(BIOLIST_NOTE_PREFIX) == -1:
            notes = f'{notes} {BIOLIST_NOTE_PREFIX}{self.currentBiolistNum}'
            self._current_haul.notes = notes
            self._current_haul.save()
            self._logger.debug(f'Saved Notes: {notes}')

    def _get_biolist_num(self):
        """
        Each device will have a static random seed stored in observersettings database.
        When a new trip ID is set, then we use that as a seed too.
        Auto-increments when new hauls are added, and is random when new trip starts
        @return:
        """
        haul_num = self._current_haul.fishing_activity_num if self._current_haul else 0
        return (self._trip_seed + haul_num) % 3 + 1

    def isTrainingMode(self):
        """
        @return: True if training mode
        """
        mode = ObserverDBUtil.get_setting('training')
        return True if mode == 'TRUE' else False

    def _set_trip_biolist_seed(self, trip_id):
        """
        For new trip, get a new biolist num seed
        @param trip_id: used as int to seed RNG
        @return:
        """
        if trip_id is None:
            self._logger.warning(f'Warn, None trip id passed to RNG.')
            return

        if not self.isTrainingMode():
            random.seed(self._device_random_seed + int(trip_id))  # repeatable RNG seed
            self._trip_seed = random.randint(1, 1000)
            self._logger.debug(f'RNG seed {self._device_random_seed} with trip id {trip_id} -> {self._trip_seed} trip seed')
        else:
            random.seed(self._device_random_seed)
            self._trip_seed = 2
            self._logger.info(f'TRAINING MODE: SET BIOLIST SEED')
