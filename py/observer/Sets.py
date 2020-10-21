# -----------------------------------------------------------------------------
# Support class for Set (OPTECS FG)

import random
from typing import Dict, Iterable

from PyQt5.QtCore import pyqtProperty, QVariant, QObject, Qt, pyqtSignal, pyqtSlot


from py.observer.LogbookObserverRetainedModel import ObserverRetainedModel
from py.observer.LogbookVesselRetainedModel import VesselRetainedModel
from py.observer.HaulSetModel import HaulSetModel
from py.observer.ObserverDBModels import FishingActivities, CatchCategories, Catches, Trips
from py.observer.ObserverDBUtil import ObserverDBUtil
from py.observer.ObserverErrorReports import ThreadTER, TripChecksOptecsManager
from py.observer.ObserverFishingLocations import ObserverFishingLocations
from py.observer.ObserverCatches import ObserverCatches
import logging


class Sets(QObject):
    modelChanged = pyqtSignal(name='modelChanged')
    currentSetIdChanged = pyqtSignal(str, name='currentSetIdChanged')
    parameterChanged = pyqtSignal(name='parameterChanged')
    obsRetModelChanged = pyqtSignal(name='obsRetModelChanged')
    maxObsRetModelLengthChanged = pyqtSignal(int, name='maxObsRetModelLengthChanged')
    maxVesselRetModelLengthChanged = pyqtSignal(int, name='maxVesselRetModelLengthChanged')
    currentBiolistNumChanged = pyqtSignal(name='currentBiolistNumChanged')
    otcWeightMethodChanged = pyqtSignal(QVariant, name='otcWeightMethodChanged')
    otcFGWeightChanged = pyqtSignal(QVariant, name='otcFGWeightChanged', arguments=['otc'])
    unusedSignal = pyqtSignal(name='unusedSignal')  # quiet warnings

    def __init__(self, db):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._data = db
        self._sets_model = HaulSetModel()  # SetModel == HaulModel
        self._current_set = None
        self._internal_set_idx = None  # FramListModel index
        self._sets_count = 0
        self._trip_id = None
        self._current_trip = None
        self._fishing_locations = ObserverFishingLocations()

        self._beaufort = db.beaufort
        self._gearperf_fg = db.gearperf_fg

        self._otc_weight_method = None
        self._obs_ret_models = dict()
        self._obs_ret_max_count = 0
        self._vessel_ret_models = dict()
        self._vessel_ret_max_count = 0
        self._seabird_geartypes = ['7', '9', '19', '20']
        self._current_biolist_num = self._default_biolist_num = 0

        # TODO sets fields that must be specified in UI (can't be left empty)
        self._required_field_names = (  # As known in peewee
            'otc_weight_method',
            'gear_type',
            'beaufort_value',
            'deterrent_used',  # seabird
        )
        self._thread_ter = None  # Runs TER in background

        self._trip_seed = 0

    @pyqtSlot(name="youAreUp")
    def you_are_up(self):
        """
        Called by ObserverSM.qml when context switches to Sets screen.
        Used to pull counts of haul-level issues from the current trip's last Trip Error Report, if any.
        :return: None
        """
        self._logger.info(f"Screen is active. Current TripID={self._trip_id}.")
        self._logger.info(f"Count of sets (from SetsModel)={self._sets_model.count}.")
        current_user_id = ObserverDBUtil.get_current_user_id()

        # If a Trip Error Report has been run for this trip, get the latest run's haul-level error counts, per-haul.
        trip_issues, run_date = TripChecksOptecsManager.get_issues_from_last_ter_run(self._trip_id, self._logger)
        if not trip_issues:
            for row in range(self._sets_model.count):
                self._sets_model.setProperty(row, "errors", "N/A")
            self._logger.debug("No Trip Error Report has been run for this trip yet. Set-level error counts to N/A.")
        else:
            set_error_counts = self._calculate_per_set_errors(trip_issues)

            view_model_rows = self._sets_model.items
            # Update view model with haul-level errors, on a haul-by-haul basis
            for row_idx in range(self._sets_model.count):
                view_model_row = view_model_rows[row_idx]
                haul_num = int(view_model_row["fishing_activity_num"])
                errors_this_haul = set_error_counts[haul_num] \
                    if haul_num in set_error_counts else 0
                self._sets_model.setProperty(row_idx, "errors", str(errors_this_haul))
            self._logger.debug(f"Updated view model with Trip Error Report with run date {run_date}.")

    @staticmethod
    def _calculate_per_set_errors(trip_issues: Iterable) -> Dict[int, int]:
        per_set_errors = {}  # Key: haul number. TODO: Use default dict
        for issue in trip_issues:
            # TODO: only count haul-level errors or below
            # Perhaps done. If there's no haul number, is the issue not haul-related?
            if issue.fishing_activity_num is None:
                pass
            elif issue.fishing_activity_num not in per_set_errors:
                per_set_errors[int(issue.fishing_activity_num)] = 1
            else:
                per_set_errors[int(issue.fishing_activity_num)] += 1
        return per_set_errors

    def load_sets(self, trip_id):
        """
        Load sets from database, build FramListModel
        :return:
        """
        self._sets_model.clear()
        sets_q = FishingActivities.select().where(FishingActivities.trip == trip_id)
        self._sets_count = sets_q.count()
        self._logger.info(f'Loading {self._sets_count} sets')
        if self._sets_count > 0:
            for s in sets_q:  # Build FramListModel
                self._sets_model.add_set(s)
        self.modelChanged.emit()
        self._trip_id = trip_id
        self._current_trip = Trips.get(Trips.trip == trip_id)
        return self._sets_count

    @pyqtSlot(name='reset')
    def reset(self):
        """
        Clear sets, reset states
        """
        self._current_set = None
        self._sets_model = HaulSetModel()

    @pyqtProperty(QVariant, notify=modelChanged)
    def SetsModel(self):
        return self._sets_model

    @pyqtProperty(QVariant, notify=currentSetIdChanged)
    def locations(self):
        return self._fishing_locations

    @pyqtProperty(int, notify=modelChanged)
    def set_count(self):
        return self._sets_count

    @pyqtProperty(bool, notify=modelChanged)
    def requireSeabird(self):
        if self._current_set.gear_type in self._seabird_geartypes:
            return True
        else:
            return False

    @property
    def current_set(self):
        return self._current_set

    @pyqtProperty(QVariant, notify=currentSetIdChanged)
    def currentGearType(self):
        return self._current_set.gear_type if self._current_set else None

    @pyqtProperty(str)
    def current_fishing_activity_id(self):
        return str(self._current_set.fishing_activity) if self._current_set else None

    @pyqtProperty(str, notify=currentSetIdChanged)
    def currentSetId(self):
        return str(self._current_set.fishing_activity_num) if self._current_set else None

    @pyqtProperty(QVariant, notify=currentSetIdChanged)
    def currentSetDBId(self):
        return self._current_set.fishing_activity if self._current_set else None

    @pyqtSlot(int, float, name='updateTripHookCounts')
    def update_trip_hook_counts(self, trip_id, avg_hook_count):
        # The below line is a hacky fix, can't figure out what
        # is resetting total_hooks_kp to an incorrect value
        # right before this is run
        self._current_trip.total_hooks_kp = avg_hook_count
        sets_q = self.get_all_sets_with_gear_segments(trip_id)
        for s in sets_q:
            self._update_set_hook_counts(s, avg_hook_count)

    @pyqtProperty(str, notify=otcWeightMethodChanged)
    def otcWeightMethod(self):
        return self._otc_weight_method

    @pyqtSlot(float, int, name="updateModelOTC")
    def update_model_otc(self, otc_fg, fishing_activity_num):
        self._set_cur_prop('observer_total_catch', otc_fg)

    def _update_set_hook_counts(self, set_rec, avg_hook_count):
        if not avg_hook_count:  # None or 0
            avg_hook_count = 1

        if set_rec.tot_gear_segments is not None:
            new_total_hooks = round(avg_hook_count * set_rec.tot_gear_segments)
            if set_rec.total_hooks != new_total_hooks:
                set_rec.total_hooks = new_total_hooks
                self._logger.debug(f'Set {set_rec.fishing_activity_num} new total hooks {new_total_hooks}')
                set_rec.save()
                self._recalculate_catches_hooks_sampled(set_rec, avg_hook_count)
                new_total_hooks_unrounded = avg_hook_count * set_rec.tot_gear_segments
                new_otc = ObserverCatches.calculate_OTC_FG(self._logger, set_rec, new_total_hooks_unrounded)
                self.update_model_otc(new_otc, set_rec.fishing_activity_num)
                self.otcFGWeightChanged.emit(new_otc)

        if set_rec.gear_segments_lost is not None:
            new_lost_hooks = round(avg_hook_count * set_rec.gear_segments_lost)
            if set_rec.total_hooks_lost != new_lost_hooks:
                set_rec.total_hooks_lost = new_lost_hooks
                self._logger.debug(f'Set {set_rec.fishing_activity_num} new total lost hooks {new_lost_hooks}')
                set_rec.save()


    def _recalculate_catches_hooks_sampled(self, set_rec, avg_hook_count):
        catches_q = Catches.select().where(Catches.fishing_activity == set_rec.fishing_activity)

        for c in catches_q:
            if avg_hook_count and c.gear_segments_sampled:
                old_hooks = c.hooks_sampled
                new_hooks = round(avg_hook_count * c.gear_segments_sampled)
                self._logger.info(f'Catch {c.catch} Hooks sampled {old_hooks} -> {new_hooks}')
                c.hooks_sampled = new_hooks
                c.save()



    @pyqtSlot()
    def refresh(self):
        """
        Called to reload haul info (currently used for changes in Locations model)
        @return:
        """
        self.load_sets(self._trip_id)

    @currentSetId.setter
    def currentSetId(self, current_id):
        self._logger.debug('Set currentSet using ID {}'.format(current_id))
        try:
            self._current_set = FishingActivities.get(FishingActivities.trip == self._trip_id,
                                                       FishingActivities.fishing_activity_num == current_id)
            self._internal_set_idx = self._sets_model.get_item_index('fishing_activity_num',
                                                                     self._current_set.fishing_activity_num)
            self._fishing_locations.load_fishing_locations(fishing_activity_id=self._current_set.fishing_activity)
            if self._current_set.biolist_localonly is None:
                self._current_set.biolist_localonly = self._default_biolist_num
                self._save_notes_biolist_num()
        except FishingActivities.DoesNotExist:
            self._logger.info("Can't get set ID for trip {}, num {}".format(self._trip_id, current_id))
            self._current_set = None
            return

        self.modelChanged.emit()

    @pyqtSlot(str, result=bool, name='removeSet')
    def removeSet(self, set_id):
        result = self.SetsModel.remove_haul_set(set_id)
        self.currentSetId = self.SetsModel.most_recent_haul_set_id()
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
        @param value: '1' - '8'
        @return: str description
        """
        return self._gearperf_fg.get(value, 'No Description')

    def _set_cur_prop(self, model_prop, value):
        """
        Helper function - set current haul properties in FramListModel
        @param model_prop: property name
        @param value: value to store
        @return:
        """
        if self._internal_set_idx is not None:
            self._sets_model.setProperty(self._internal_set_idx,
                                         model_prop, value)
        else:
            self._logger.warning(f'_internal_set_idx is None, skipping prop update {model_prop}: {value}')

    @pyqtSlot(str, result='QVariant', name='getDataOrSetDefault')
    def get_data_or_default(self, data_name):
        """
        If a Set #1 has set this data, then get that (and set it.)
        @param data_name: name of data
        @return: db value or default
        """

        set_data = self.getData(data_name=data_name)
        if set_data is not None and set_data != '':
            return set_data
        elif self._current_set.fishing_activity_num == 1 and data_name != 'efp':
            self._logger.debug(f'First set, not retrieving default for {data_name}')
            return None
        else:  # Get defaults from first_set
            try:
                first_set = FishingActivities.get((FishingActivities.trip == self._current_set.trip),
                                                   (FishingActivities.fishing_activity_num == 1))
                if data_name == 'target_strategy':
                    default_data = self._get_target_code(first_set.target_strategy)
                    self.setData(data_name, default_data)
                    return default_data
                elif data_name == 'gear_type':
                    default_data = first_set.gear_type
                    self.setData(data_name, default_data)
                    return default_data
                elif data_name == 'efp':
                    default_data = self._get_efp(first_set)
                    efp_data = True if default_data else None  # For DB EFP special case
                    self.setData(data_name, efp_data)
                    return default_data
                elif data_name == 'deterrent_used':
                    default_data = self._get_deterrent_used(first_set)
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

    @staticmethod
    def _get_deterrent_used(fishing_activity):
        if fishing_activity.deterrent_used is not None:
            return True if fishing_activity.deterrent_used == '1' else False
        else:
            return None


    @pyqtSlot(str, result='QVariant', name='getData')
    def getData(self, data_name):
        """
        Shortcut to get data from the DB that doesn't deserve its own property
        (Note, tried to use a dict to simplify this, but DB cursors were not updating)
        :return: Value found in DB
        """
        if self._current_set is None:
            logging.warning('Attempt to get data with null current haul.')
            return None
        data_name = data_name.lower()
        return_val = None
        if data_name == 'observer_total_catch':
            return_val = self._current_set.observer_total_catch
        elif data_name == 'otc_weight_method':
            return_val = self._current_set.otc_weight_method
        elif data_name == 'fit':
            return_val = self._current_set.fit
        elif data_name == 'brd_present':
            return self._get_brd_present(self._current_set)
        elif data_name == 'efp':
            # Center IFQ Database (target of DB Sync) convention: 'EFP' or null.
            efp_val = self._get_efp(self._current_set)
            local_efp_val = self._get_efp_local(self._current_set)
            return local_efp_val if local_efp_val is not None else efp_val  # tristate bool
        elif data_name == 'cal_weight':
            return_val = self._current_set.cal_weight
        elif data_name == 'beaufort_value':
            return_val = self._current_set.beaufort_value
        elif data_name == 'avg_soak_time':
            return_val = self._current_set.avg_soak_time
        elif data_name == 'tot_gear_segments':
            return_val = self._current_set.tot_gear_segments
        elif data_name == 'gear_segments_lost':
            return_val = self._current_set.gear_segments_lost
        elif data_name == 'total_hooks':
            return_val = self._current_set.total_hooks
        elif data_name == 'total_hooks_lost':
            return_val = self._current_set.total_hooks_lost
        elif data_name == 'deterrent_used':  # seabird
            return_val = self._current_set.deterrent_used
        elif data_name == 'gear_performance':
            return_val = self._current_set.gear_performance
        elif data_name == 'target_strategy':
            return_val = self._get_target_code(self._current_set.target_strategy)
        elif data_name == 'gear_type':
            return_val = self._current_set.gear_type
        else:
            logging.warning('Attempt to get unknown data name: {}'.format(data_name))

        return '' if return_val is None else return_val

    @pyqtSlot(str, QVariant, name='setData')
    def setData(self, data_name, data_val):
        """
        Set misc data to the DB
        :return:
        """
        if self._current_set is None:
            logging.warning('Attempt to set data with null current haul.')
            return
        data_name = data_name.lower()
        if data_name == 'observer_total_catch':
            self._current_set.observer_total_catch = float(data_val) if data_val else 0.0
        elif data_name == 'otc_weight_method':
            self._current_set.otc_weight_method = int(data_val) if data_val else 0
        elif data_name == 'fit':
            # FIELD-1374: Numpad Backspace (<-) key returns empty string rather than 0. Treat as '0'.
            fit_val = data_val if data_val != "" else '0'
            self._current_set.fit = str(fit_val)
        elif data_name == 'brd_present':
            if data_val:
                self._current_set.brd_present = 'TRUE'
            else:
                self._current_set.brd_present = 'FALSE'
        elif data_name == 'deterrent_used':
            if data_val:
                self._current_set.deterrent_used = '1'
            else:
                self._current_set.deterrent_used = '0'
        elif data_name == 'efp':
            # Center IFQ Database (target of DB Sync) convention: 'EFP' or ''.
            if data_val:
                self._current_set.efp = 'EFP'
                self._current_set.efp_localonly = 1
            else:
                self._current_set.efp = None  # NULL in Database, but False for model prop
                self._current_set.efp_localonly = 0
        elif data_name == 'cal_weight':
            self._current_set.cal_weight = data_val
        elif data_name == 'beaufort_value':
            self._current_set.beaufort_value = data_val
        elif data_name == 'tot_gear_segments':
            self._current_set.tot_gear_segments = int(data_val) if data_val else None
        elif data_name == 'gear_segments_lost':
            self._current_set.gear_segments_lost = int(data_val) if data_val else None
        elif data_name == 'total_hooks':
            self._current_set.total_hooks = int(data_val) if data_val else None
        elif data_name == 'total_hooks_unrounded':
            self._current_set.total_hooks_unrounded = float(data_val) if data_val else None
        elif data_name == 'total_hooks_lost':
            self._current_set.total_hooks_lost = int(data_val) if data_val else None
        elif data_name == 'gear_performance':
            self._current_set.gear_performance = data_val
        elif data_name == 'target_strategy':
            self._current_set.target_strategy = self._lookup_target_strat_id(data_val) \
                if data_val else None
            # Translate for listview on HaulsScreen
            self._set_cur_prop('target_strategy_code',
                               self._get_target_code(self._current_set.target_strategy))
        elif data_name == 'gear_type':
            if ' ' in data_val:
                data_val = data_val.split(' ')[0]  # Extract value
                data_val = str(int(data_val))  # remove leading zero
            self._current_set.gear_type = data_val
        elif data_name == 'avg_soak_time':
            if ' ' in data_val:
                data_val = data_val.split(' ')[0]  # Extract value
                data_val = str(int(data_val))  # remove leading zero
            self._current_set.avg_soak_time = data_val
        else:
            logging.warning('Attempt to set unknown data name: {}'.format(data_name))
            return
        self._current_set.save()
        self._set_cur_prop(data_name, data_val)
        logging.debug('Set {} to {}'.format(data_name, data_val))

        if data_name in ['tot_gear_segments']:
            self._update_set_hook_counts(self._current_set, self._current_trip.total_hooks_kp)
        self.modelChanged.emit()

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
    def requiredSetsFieldsAreSpecified(self):
        """
        Have all the prerequisite fields in the Haul Details screen been filled in for the current haul
        so that navigation to Catch screen is allowed?

        :return: True if gear type is not empty.
                False otherwise.
        """
        if not self.requireSeabird:
            req_fields = filter(lambda x: x != 'deterrent_used', self._required_field_names)
        else:
            req_fields = self._required_field_names
        is_filled = [self.required_set_field_is_specified(f) for f in req_fields]

        result = all(is_filled)

        # self._logger.debug("{}OK to navigate to Catch tab.".format("" if result else "Not "))

        return result and self.currentBiolistNum > 0

    @pyqtSlot(QVariant, result=QVariant, name='requiredSetFieldIsSpecified')
    def required_set_field_is_specified(self, field_name):
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

        # self._logger.debug(f'{field_name} -> {field_data} is {"" if field_ok else "not "}specified.')
        return field_ok

    @pyqtProperty(QVariant, notify=unusedSignal)
    def isCalWeightSpecified(self):
        cal_wt = self.getData('cal_weight')
        if cal_wt:
            return True

        return False

    @pyqtSlot(QVariant, result=QVariant, name='getObserverRetModel')
    def getObserverRetModel(self, haul_db_id):
        """
        Load observer retained model
        @param haul_db_id: Database ID
        @return:
        """
        new_model = ObserverRetainedModel()
        new_model.load_observer_retained(haul_db_id, is_fixed_gear=True)
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

    @pyqtSlot(QVariant, result=bool, name='checkSetEmpty')
    def check_set_empty(self, haul_id):
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

    @pyqtSlot(QVariant, result=int, name='createSet')
    def create_set(self, set_num):
        """
        @param set_num: ID local to this trip
        @return: haul db ID
        """
        self.load_sets(trip_id=self._trip_id)
        observer_id = ObserverDBUtil.get_current_user_id()
        newset = FishingActivities.create(trip=self._trip_id,
                                           fishing_activity_num=set_num,
                                           created_by=observer_id,
                                           created_date=ObserverDBUtil.get_arrow_datestr())
        logging.info(
            'Created FishingActivities (set {}) for trip={}'.format(newset.fishing_activity_num, self._trip_id))

        self.SetsModel.add_set(newset)
        self.currentSetId = newset.fishing_activity_num
        self._save_notes_biolist_num()
        return int(newset.fishing_activity)

    @pyqtSlot(QVariant, result=bool, name='deleteSet')
    def delete_set(self, set_id):
        if set_id is None or not self.check_set_empty(set_id):
            return

        trip_id = self._trip_id
        self._current_set = None  # FIELD-1817 always clear current haul ID if deleting


        # Delete from DB
        set = FishingActivities.get(FishingActivities.fishing_activity == set_id)
        ObserverDBUtil.log_peewee_model_instance(self._logger, set, 'Deleting haul')
        set.delete_instance(recursive=True)

        # Delete from model
        result = self._sets_model.remove_haul_set(set_id)

        # Check for hauls with greater fishing_activity_num # than this one, and if found, decrement them.
        renumber_hauls = FishingActivities.select().where(
            (FishingActivities.fishing_activity > set_id) & (FishingActivities.trip == trip_id))
        for h in renumber_hauls:
            old_num = h.fishing_activity_num
            h.fishing_activity_num -= 1
            h.save()
            fishing_number_row = self._sets_model.get_haul_set_index(h.fishing_activity)
            self._logger.info(f'Renumbered FISHING_ACTIVITY_NUM {old_num} to {h.fishing_activity_num} for haul {h.fishing_activity}')
            self._sets_model.setProperty(fishing_number_row, 'fishing_activity_num', h.fishing_activity_num)

        return result

    @pyqtProperty(QVariant, notify=currentBiolistNumChanged)
    def currentBiolistNum(self):
        return self._get_biolist_num()

    @currentBiolistNum.setter
    def currentBiolistNum(self, bio_num):
        self._current_biolist_num = bio_num
        self._default_biolist_num = bio_num  # this is used as new default
        if self._current_set:
            self._current_set.biolist_localonly = bio_num
            self._current_set.save()
        self._save_notes_biolist_num()

    @pyqtSlot(name='updateBiolistNote')
    def _save_notes_biolist_num(self):
        """
        Store BIOLIST num to notes
        :return:
        """
        if not self._current_set:
            self._logger.error('Tried to save biolist num, but current set not indicated.')
            return
        notes = self._current_set.notes if self._current_set.notes else ''
        BIOLIST_NOTE_PREFIX = 'Biolist #'
        bio_location = notes.find(BIOLIST_NOTE_PREFIX)
        if bio_location == -1:
            notes = f'{notes} {BIOLIST_NOTE_PREFIX}{self.currentBiolistNum}'
            self._current_set.notes = notes
            self._current_set.save()
            self._logger.debug(f'Saved Notes: {notes}')
        else:
            # exists... update with right number
            if notes.find(BIOLIST_NOTE_PREFIX + str(self.currentBiolistNum)) == -1:
                newnotes = notes[:bio_location] + 'Biolist #' + str(self.currentBiolistNum)
                self._current_set.notes = newnotes
                self._current_set.save()
                self._logger.debug(f'Updated Notes: {newnotes}')
            pass

    def _get_biolist_num(self):
        """
        For Sets,
        4 = Nearshore Fixed Gear (NSFG)
        5 = Non-Nearshort Fixed Gear (Non-NSFG)
        """
        if self._current_set and self._current_set.biolist_localonly:
            self._default_biolist_num = self._current_set.biolist_localonly  # this is used as new default
            return self._current_set.biolist_localonly
        else:
            return self._current_biolist_num

    @staticmethod
    def get_all_sets_with_gear_segments(trip_id):
        return FishingActivities.select().where((FishingActivities.trip == trip_id) &
                                                (FishingActivities.tot_gear_segments.is_null(False) |
                                                 FishingActivities.gear_segments_lost.is_null(False)))