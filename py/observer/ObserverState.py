# -----------------------------------------------------------------------------
# Name:        ObserverState.py
# Purpose:     Global state data, collections
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Feb 2, 2016
# License:     MIT
# ------------------------------------------------------------------------------

import json
import logging
import textwrap
import unittest

import arrow
from PyQt5.QtCore import pyqtProperty, QObject, QVariant, pyqtSlot, pyqtSignal, QThread

from peewee import fn

from py.observer.ObserverConfig import max_text_size_observer_comments
from py.observer.ObserverUsers import ObserverUsers
from py.observer.ObserverData import ObserverData
from py.observer.ObserverTrip import ObserverTrip
from py.observer.ObserverCatches import ObserverCatches
from py.observer.Hauls import Hauls
from py.observer.Sets import Sets
from py.observer.ObserverDBUtil import ObserverDBUtil

from py.observer.ObserverDBModels import Settings, FishingActivities, Comment, DoesNotExist, Vessels, Trips, Catches
from py.observer.ObserverConfig import optecs_version, display_decimal_places
from py.observer.BackupDBWorker import BackupDBWorker


class DefaultDefaultSettings:
    """ If the SETTINGS table of the Observer database doesn't contain a particular setting,
        to what value should a new entry in SETTINGS be set to?
    """
    trawl_max_depth_fathoms = 700  # Constant from Neil Riley
    trawl_max_basket_weight_lbs = 150

    # If a basket weight exceeds 100 lbs but is not more than 150, throw up a confirmation dialog
    trawl_confirm_basket_weight_lbs = 100

    # Minimum and maximum allowed latitudes, in degrees, for OPTECS locations.
    # Enforces the limits defined in OPSPROD.TRIP_CHECKS WHERE TRIP_CHECK_ID = 1883:
    # "Gear latitude(s) not between 31 and 49"
    trawl_minimum_latitude_degrees = 31
    trawl_maximum_latitude_degrees = 49


class ObserverState(QObject):
    """
    Handles Observer state (current trip info, current haul info, Gear Type, etc)
    and related database interactions
    """

    modelChanged = pyqtSignal()
    currentHaulChanged = pyqtSignal(QVariant)
    currentTripChanged = pyqtSignal(QVariant)
    tripsChanged = pyqtSignal(QVariant)
    haulsChanged = pyqtSignal(QVariant)
    setsChanged = pyqtSignal(QVariant)
    catchesChanged = pyqtSignal(QVariant)
    trawlMaxDepthFathomsChanged = pyqtSignal(QVariant)
    trawlMaxBasketWeightLbsChanged = pyqtSignal(QVariant)
    trawlConfirmBasketWeightLbsChanged = pyqtSignal(QVariant)
    isGearTypeTrawlChanged = pyqtSignal(bool)
    currentObserverChanged = pyqtSignal(QVariant)
    driveLettersChanged = pyqtSignal(QVariant)
    lastBackupTimeChanged = pyqtSignal()
    backupStatusChanged = pyqtSignal(bool, QVariant, arguments=["success", "message"])
    unusedSignal = pyqtSignal(name='unusedSignal')  # For properties without a signal; use to avoid QML warning.

    currentCatchCatChanged = pyqtSignal(QVariant)
    catchCatNameChanged = pyqtSignal(str)
    speciesNameChanged = pyqtSignal(str)
    commentsChanged = pyqtSignal(str)
    wm5WeightChanged = pyqtSignal(int, QVariant, arguments=["catchId", "new_wt"])  # tell CC page to update tableView

    # If we are in these appstates, always save comments to Trips.notes
    # (instead of haul level: FishingActivities.notes)
    trip_comment_states = ('home_state',
                           'start_trawl_state',
                           'end_trawl_state',
                           'start_fg_state',
                           'end_fg_state',
                           'hauls_state',
                           'sets_state',
                           'trip_errors_state',
                           'logbook_state',
                           'backup_state',
                           'select_trip_state')

    def __init__(self, db):
        super().__init__()
        self._logger = logging.getLogger(__name__)

        self._db = db

        # These data will also get saved into (new) Trips
        cs_query = Settings.select().where(Settings.parameter == 'catch_share')
        if not cs_query.exists():
            Settings.create(parameter='catch_share', value='TRUE')
        self._catchshare = cs_query.get()

        gt_query = Settings.select().where(Settings.parameter == 'gear_type')
        if not gt_query.exists():
            Settings.create(parameter='gear_type', value='TRUE')
        self._geartype_trawl_default = gt_query.get()

        self._users = ObserverUsers()

        self._trips = ObserverTrip()
        self._hauls = Hauls(db=db)
        self._sets = Sets(db=db)
        self._catches = ObserverCatches(db=db)

        self._current_cc = None

        self._current_cc_name = ""  # for display
        self._current_spec_name = ""  # for display

        fr_query = Settings.select().where(Settings.parameter == 'first_run')
        if not fr_query.exists():
            Settings.create(parameter='first_run', value='TRUE')
        self._firstrun = fr_query.get()

        cu_query = Settings.select().where(Settings.parameter == 'current_user')
        if not cu_query.exists():
            Settings.create(parameter='current_user')
        self._current_user = cu_query.get()

        cu_query = Settings.select().where(Settings.parameter == 'current_user_id')
        if not cu_query.exists():
            Settings.create(parameter='current_user_id')
        self._current_user_id = cu_query.get()

        # Type max depth as integer
        self._trawl_max_depth_fathoms = int(self.getset_setting(
            'trawl_max_depth_fathoms',
            DefaultDefaultSettings.trawl_max_depth_fathoms))
        self.trawlMaxDepthFathomsChanged.emit(self._trawl_max_depth_fathoms)

        # Confirmation-required basket weight, typed as integer
        self._trawl_confirm_basket_weight_lbs = int(self.getset_setting(
            'trawl_confirm_basket_weight_lbs',
            DefaultDefaultSettings.trawl_confirm_basket_weight_lbs))
        self.trawlConfirmBasketWeightLbsChanged.emit(self._trawl_confirm_basket_weight_lbs)

        # Max basket weight as integer, typed as integer
        self._trawl_max_basket_weight_lbs = int(self.getset_setting(
            'trawl_max_basket_weight_lbs',
            DefaultDefaultSettings.trawl_max_basket_weight_lbs))
        self.trawlMaxBasketWeightLbsChanged.emit(self._trawl_max_basket_weight_lbs)

        # Minimum and maximum degrees latitude as integer.
        # No emits necessary: this value will not change during a run.
        self._trawl_min_latitude_degrees = int(self.getset_setting(
            'trawl_minimum_latitude_degrees',
            DefaultDefaultSettings.trawl_minimum_latitude_degrees))
        self._trawl_max_latitude_degrees = int(self.getset_setting(
            'trawl_maximum_latitude_degrees',
            DefaultDefaultSettings.trawl_maximum_latitude_degrees))

        # DB Backup Thread
        self._backup_thread = QThread()
        self._backup_worker = None

        self._comments_all = ''
        self._comments_trip = ''
        self._comments_haul = dict()
        self._db_formatted_comments_trip = ''
        self._db_formatted_comments_haul = dict()

        self.currentTripId = ObserverDBUtil.db_load_setting('trip_number')  # Current Trip ID if set
        self.update_comments()

        self._catches.retainedCatchWeightChanged.connect(self.update_wm5_catch_weights)  # ret. catch changes --> WM5 updates
        self._hauls.otcWeightChanged.connect(self.update_wm5_catch_weights)  # otc changes --> WM5 updates

    @staticmethod
    def getset_setting(parm_name, default_val):
        """ Get parm_name setting from SETTINGS table.
            If setting not in SETTINGS, use default_val.
            Side-effect: also add default_val to SETTINGS table.
        """
        fr_query = Settings.select().where(Settings.parameter == parm_name)
        if not fr_query.exists():
            Settings.create(parameter=parm_name, value=default_val)
        return fr_query.get().value

    @pyqtSlot()
    def reset(self):
        # self._logger.warn('RESETTING STATE - TODO')

        self._current_cc = None

        self._current_cc_name = ""  # for display
        self._current_spec_name = ""  # for display

    @staticmethod
    def pad_trip_id(id_value):
        """
        Returns padded string from int
        :param id_value: int ID
        :return:
        """
        return '{0:05d}'.format(id_value)

    @pyqtProperty(str, notify=unusedSignal)  # Specify notify to avoid "depends on non-NOTIFYable properties" warning
    def optecsVersion(self):
        return optecs_version

    @pyqtProperty(str, notify=unusedSignal)  # Specify notify to avoid "depends on non-NOTIFYable properties" warning
    def dbVersion(self):
        return ObserverDBUtil.get_setting('database_revision', 'unknown')

    @pyqtProperty(int, notify=unusedSignal)  # Specify notify to avoid "depends on non-NOTIFYable properties" warning
    def displayDecimalPlaces(self):
        """
        :return: Number of floating point decimal places to use in display text boxes.
        """
        return display_decimal_places

    @pyqtProperty(bool)
    def firstRun(self):
        return self._firstrun.value.lower() == 'true'

    @firstRun.setter
    def firstRun(self, value):
        self._firstrun.value = 'TRUE' if value else 'FALSE'
        self._firstrun.save()

    @pyqtProperty(QVariant, notify=currentObserverChanged)
    def currentObserver(self):
        return self._current_user.value

    @pyqtProperty(QVariant, notify=trawlMaxDepthFathomsChanged)
    def trawlMaxDepthFathoms(self):
        return self._trawl_max_depth_fathoms

    @pyqtProperty(QVariant, notify=trawlMaxBasketWeightLbsChanged)
    def trawlMaxBasketWeightLbs(self):
        """ Used in Catch Counts/Weights.
            A basket can't weigh more than this amount.
        """
        return self._trawl_max_basket_weight_lbs

    @pyqtProperty(QVariant, notify=trawlConfirmBasketWeightLbsChanged)
    def trawlConfirmBasketWeightLbs(self):
        """ Used in Catch Counts/Weights.
            A basket that weighs no more than trawlMaxBasketWeightLbs
            yet weighs more than this amount should prompt a confirmation window.
        """
        return self._trawl_confirm_basket_weight_lbs

    @pyqtProperty(QVariant, notify=unusedSignal)
    def trawlMinLatitudeDegrees(self):
        return self._trawl_min_latitude_degrees

    @pyqtProperty(QVariant, notify=unusedSignal)
    def trawlMaxLatitudeDegrees(self):
        return self._trawl_max_latitude_degrees

    @currentObserver.setter
    def currentObserver(self, value):
        """
        Set username for convenience, ties to appstate.users.currentUserName
        @param value: username
        @return:
        """
        self._logger.info('Current observer set to {0}'.format(value))
        self._current_user.value = value
        self._current_user.save()
        self._current_user_id.value = ObserverUsers.get_user_id(value)
        self._current_user_id.save()

    @pyqtProperty(bool)
    def defaultCatchShare(self):
        return self._catchshare.value.lower() == 'true'

    @defaultCatchShare.setter
    def defaultCatchShare(self, value):
        self._catchshare.value = 'TRUE' if value else 'FALSE'
        self._catchshare.save()

    @pyqtProperty(bool, notify=isGearTypeTrawlChanged)
    def isGearTypeTrawl(self):
        return self._geartype_trawl_default.value.lower() == 'true'

    @isGearTypeTrawl.setter
    def isGearTypeTrawl(self, value):
        self._geartype_trawl_default.value = 'TRUE' if value else 'FALSE'
        self._geartype_trawl_default.save()
        self.isGearTypeTrawlChanged.emit(value)

    @pyqtProperty(bool, notify=isGearTypeTrawlChanged)
    def isFixedGear(self):
        return self._geartype_trawl_default.value.lower() != 'true'

    @pyqtProperty(QVariant, notify=haulsChanged)
    def hauls(self):
        return self._hauls

    @pyqtProperty(QVariant, notify=setsChanged)
    def sets(self):
        return self._sets

    @pyqtProperty(str, notify=tripsChanged)
    def currentTripId(self):
        return self._trips.tripId

    @pyqtProperty(QVariant, notify=currentObserverChanged)
    def users(self):
        return self._users

    @currentTripId.setter
    def currentTripId(self, trip_id):
        """
        Set Trip ID (currently same as db pk)
        @param trip_id: DB PK ID
        """
        if trip_id is None:
            self._logger.info('Current trip ID is not set.')
            return
        # this is also being set in ObserverTrips.tripId.setter, but fails if in debriefer mode (user mismatch).
        # adding here to ensure trip_number param is definitely set when selecting trip
        # TODO: consolidate logic for setting trip_number here, or rework ObserverTrip.tripId setter
        ObserverDBUtil.db_save_setting('trip_number', trip_id)
        self._logger.debug(f"setting SETTINGS parameter trip_number to {trip_id}")
        trip_id = int(trip_id)  # ensure integer key
        self._trips.tripId = trip_id
        self._hauls.reset()
        self._trips.load_current_trip(trip_id)
        if self.isFixedGear:
            self._sets.load_sets(trip_id=trip_id)
        else:
            self._hauls.load_hauls(trip_id=trip_id)

    @pyqtSlot(str, result='QVariant')
    def create_trip(self, vessel_name):
        """
        Create trip, looks up vessel_name by ID
        @param vessel_name: vessel name as seen in DB
        @return: new trip
        """
        if self.currentObserver is None or vessel_name is None:
            self._logger.error('No Observer/ Vessel Selected, abort create trip')
            return None
        vessel_id = self.get_vessel_id(vessel_name)
        observer_id = self.users.currentUserID
        program_id = self.users.currentProgramID
        self._logger.info(
            'Creating trip with observer ID {}, vessel ID {} TODO PROGRAM ID'.format(observer_id, vessel_id))
        newtrip = self._trips.create_trip(vessel_id, observer_id, program_id)
        self.modelChanged.emit()
        return newtrip

    @pyqtSlot(str, result='QVariant')
    def create_catch(self, catch_category_id):
        """
        Create catch
        @param catch_category_id:
        @return: new catch model (dict)
        """
        if catch_category_id is None:
            self._logger.error('Bad catch category ID passed to create_catch, abort.')
            return None

        current_haul_set_id = self.sets.current_set.fishing_activity if self.isFixedGear \
            else self.hauls.current_haul.fishing_activity
        if current_haul_set_id is None:
            self._logger.error('No current haul/set ID, abort create_catch')
            return None

        try:
            catch_category_id = int(catch_category_id)
        except ValueError as ve:
            self._logger.error(f'catch_category_id "{catch_category_id}" is not int, aborting create_catch ({ve}).')
            return None

        self._logger.info(
            'Creating catch with catch category ID {}, haul id {}'
                .format(catch_category_id, current_haul_set_id))
        newcatch_model = self._catches.create_catch(catch_category_id=catch_category_id,
                                                    fishing_activity_pk=current_haul_set_id)
        self.modelChanged.emit()
        return newcatch_model

    @pyqtSlot()
    def end_trip(self):
        self._trips.end_trip()
        self.hauls.reset()
        self.sets.reset()
        self.modelChanged.emit()

    @pyqtProperty(QVariant, notify=catchesChanged)
    def catches(self):
        return self._catches

    @pyqtProperty(QVariant, notify=modelChanged)
    def TripsModel(self):
        return self._trips.TripsModel

    @pyqtProperty(QVariant, notify=tripsChanged)
    def trips(self):
        return self._trips

    #  Properties for display (in header, etc)
    @pyqtProperty(str, notify=catchCatNameChanged)
    def catchCatName(self):
        return self._current_cc_name

    @catchCatName.setter
    def catchCatName(self, value):
        self._current_cc_name = value
        self.catchCatNameChanged.emit(value)

    @pyqtProperty(str, notify=speciesNameChanged)
    def speciesName(self):
        return self._current_spec_name

    @speciesName.setter
    def speciesName(self, value):
        self._current_spec_name = value
        self.speciesNameChanged.emit(value)

    @pyqtProperty(str, notify=commentsChanged)
    def comments(self):
        return self._comments_all

    @pyqtProperty(str, notify=commentsChanged)
    def db_formatted_comments(self):
        return self._db_formatted_comments_trip

    @pyqtSlot(name='updateComments')
    def update_comments(self):
        if not self.currentTripId or not self.currentObserver:
            # self._logger.info(f'No trip, skip saving comments: {self.currentTripId}')
            return

        trip_id = int(self.currentTripId)
        self._logger.info(f'Updating comments for TRIP ID {trip_id}')
        self._comments_all = ''
        self._comments_trip = ''
        self._comments_haul = dict()  # { haul_id: "comment" }
        self._db_formatted_comments_trip = ''
        self._db_formatted_comments_haul = dict()
        comments_q = Comment.select().where(Comment.trip == trip_id).order_by(Comment.comment_id)
        if not comments_q.count():
            self._logger.debug(f'No comments found for trip: {trip_id}')
            return
        for comment in comments_q:
            # Removed starting dash comment delimiter to adhere to IFQ TRIP_CHECK convention that
            # notes start with an alphanumeric. But continuing to use trailing dash separator.
            new_comment_string = f'{comment.username} ({comment.appstateinfo}) ' \
                                  f'{comment.comment_date} ---\n{comment.comment}\n\n'
            self._comments_all += new_comment_string

            try:
                # Only want first half of appstateinfo, that variable now also holds the page title text
                if comment.fishing_activity is None or comment.appstateinfo.split("::")[0] in self.trip_comment_states:
                    self._comments_trip += new_comment_string

                    self._db_formatted_comments_trip += self._db_format_one_comment(comment)
                else:
                    haul_id = comment.fishing_activity.fishing_activity
                    if haul_id not in self._comments_haul.keys():
                        self._comments_haul[haul_id] = new_comment_string
                        self._db_formatted_comments_haul[haul_id] = self._db_format_one_comment(comment)
                    else:  # append
                        self._comments_haul[haul_id] += new_comment_string
                        self._db_formatted_comments_haul[haul_id] += self._db_format_one_comment(comment)
            except Exception as e:  # Handle load of bad previous comment weirdness
                self._logger.error(e)

        # now save to NOTES for Trip
        try:
            trip_q = Trips.get(Trips.trip == trip_id)
            trip_q.notes = ObserverDBUtil.escape_linefeeds(self._db_formatted_comments_trip)
            trip_q.save()
            self._logger.info(f"Wrote {len(trip_q.notes)} characters to Trips.notes.")
            for haul_id in self._comments_haul.keys():
                haul_q = FishingActivities.get((FishingActivities.trip == trip_id) &
                                               (FishingActivities.fishing_activity == haul_id))
                haul_q.notes = ObserverDBUtil.escape_linefeeds(self._db_formatted_comments_haul[haul_id])
                haul_q.save()
                self._logger.info(f"Wrote {len(haul_q.notes)} characters to FishingActivities.notes.")

        except Trips.DoesNotExist as e:
            self._logger.warning(f'Cannot save comment, {e}')
        except FishingActivities.DoesNotExist as e:
            self._logger.warning(f'Cannot save comment, {e}')

        self.commentsChanged.emit(self._comments_trip)
        # logging.debug('Comments now {}'.format(self._comments))

    @staticmethod
    def strip_db_comment(comment):
        remove_text = ['\r', '\n']
        replace_text = [(',', '|')]
        for r in remove_text:
            comment = comment.replace(r, '')
        for r in replace_text:
            comment = comment.replace(r[0], r[1])
        return comment

    def _db_format_one_comment(self, comment):
        db_format_comment = self.strip_db_comment(comment.comment)
        # Removed starting dash comment delimiter to adhere to IFQ TRIP_CHECK convention that
        # notes start with an alphanumeric. But continuing to use trailing dash separators (but only 4).
        # also need some smarts for the deleting the first half of the app state string if it's not
        # blank

        newappstate = comment.appstateinfo if len(comment.appstateinfo.split("::")) < 2 else \
                      comment.appstateinfo.split("::", maxsplit=1)[1]

        db_formatted_comment = f'{comment.username} ' \
                               f'({newappstate}) {comment.comment_date} ' \
                               f': {db_format_comment} -- '
        return db_formatted_comment

    def _get_size_of_existing_comments(self):
        """ How many characters are currently in Trips.note for this trip? Ignores haul-level comments"""
        if not self.currentTripId or not self.currentObserver:
            self._logger.warning(f'Invalid trip or observer to save comments: {self.currentTripId}')
            return 0
        else:
            trip_id = int(self.currentTripId)
            self._logger.info(f'Calculating size of existing comments for TRIP ID {trip_id}')

        db_formatted_comments = ''
        # Ignore haul-level comments
        comments_q = Comment. \
            select(). \
            where((Comment.trip == trip_id) & (Comment.fishing_activity.is_null(True))). \
            order_by(Comment.comment_id)
        if not comments_q.count():
            self._logger.info(f'No comments found for trip: {trip_id}')
            return 0

        for comment in comments_q:
            db_formatted_comments += self._db_format_one_comment(comment)

        return len(db_formatted_comments)

    @pyqtProperty(int, notify=unusedSignal)  # Specify notify to avoid "depends on non-NOTIFYable properties" warning
    def maxTextSizeOfObserverComments(self):
        return max_text_size_observer_comments

    @pyqtSlot(str, str, result=int, name='getFreeCommentSpaceAfterProposedAdd')
    def get_free_observer_comment_space_after_proposed_add(self, proposed_comment, proposed_appstate):

        total_size_after, _ = self.get_free_comment_space_after_proposed_add(
            proposed_comment, proposed_appstate, max_text_size_observer_comments)

        return total_size_after

    def get_free_comment_space_after_proposed_add(self, proposed_comment, proposed_appstate, max_text_allowed):

        size_before = self._get_size_of_existing_comments()

        # Instantiate a new model instance in memory, but don't add to database (no create, no save)
        newcomment = Comment(username=self.currentObserver,
                             comment_date=ObserverDBUtil.get_arrow_datestr(),
                             appstateinfo=proposed_appstate,
                             comment=proposed_comment,
                             trip=self.currentTripId)

        size_of_new_comment = 0 if newcomment is None else len(self._db_format_one_comment(newcomment))
        size_after = size_before + size_of_new_comment

        return max_text_allowed - size_after, size_of_new_comment

    def update_wm5_catch_weights(self):
        """
        Go to DB directly and find catches w. WM5.
        Update catch_weight with OTC-RET., then EMIT to signal QML
        func lives here so it can interact with both _hauls and _catches signals

        NOTE: catch_weight cant be negative in DB, so if negative set to null / None
        :return: None
        """
        if self.isFixedGear:  # wm5 doesn't exist w. FG
            return

        wm5_catches = Catches.select(Catches.catch, Catches.catch_num).where(
            (Catches.fishing_activity == self._hauls.currentHaulDBId) &
            (Catches.catch_weight_method == '5')
        ).execute()
        new_wt = self._hauls.getData('observer_total_catch') - self._hauls.retainedHaulWeight
        new_wt = new_wt if new_wt > 0 else None  # wt can't be negative in DB, set to None/Null
        for c in wm5_catches:  # there shouldn't be more than one, but just in case
            Catches.update(catch_weight=new_wt).where(
                (Catches.catch == c.catch)
            ).execute()

            logging.info(f"CatchNum {c.catch_num} (ID: {c.catch}) WM5 weight updated to {new_wt}")
            self.wm5WeightChanged.emit(c.catch, new_wt)  # tell CC QML page to update too

    @pyqtSlot(str, str, name='addComment')
    def add_comment(self, comment, appstate):
        """
        Adds date, username, and comment to Comments
        :return:
        """
        if not self.currentTripId:
            self._logger.error('No trip selected, comment NOT saved: {}'.format(comment))
            return
        self._logger.info(f'Adding comment "{comment}" to current trip {self.currentTripId}')
        # TODO Add to trips, not Comment
        if self.isFixedGear:
            haul_db_id = self.sets.currentSetDBId if self.sets else None
        else:
            haul_db_id = self.hauls.currentHaulDBId if self.hauls else None

        newcomment = Comment.create(username=self.currentObserver,
                                    comment_date=ObserverDBUtil.get_arrow_datestr(),
                                    appstateinfo=appstate,
                                    comment=comment,
                                    trip=self.currentTripId,
                                    fishing_activity=haul_db_id)
        newcomment.save()
        self.update_comments()

    @pyqtSlot(str, result=int)
    def get_vessel_id(self, vessel_name):
        """
        Check for vessel name
        @param vessel_name: vessel to check for in DB
        @return: Returns ID if vessel is in the DB, otherwise 0
        """
        try:
            vessel_name = vessel_name.lower()
            try:
                vessel = Vessels.get(fn.Lower(Vessels.vessel_name) == vessel_name)
                logging.info('ID {} found for vessel {}'.format(vessel.vessel, vessel_name))
                return vessel.vessel
            except DoesNotExist:
                logging.warning('Vessel not found: {}'.format(vessel_name))
                return 0
        except ValueError:
            logging.warning('Invalid vessel name {}'.format(vessel_name))
            return 0

    @pyqtSlot(name='raiseException')
    def raise_exception(self):
        """
        QML code can call this to raise an exception in order to test the unhandled exception handler.
        Should be only called by a developer or product proxy (Newport Team).
        Should be triggered only by an obscure keystroke sequence in the UI
        (currently 10 mouse clicks in a row on the label (not text box) of Visual OTC of the Haul Details screen).
        :return:
        """
        msgStart = "Exception intentionally raised for testing. "
        msgEnd = "End of intentionally long exception msg"
        filler = "abcdefghijklmnopqrstuvwxyz " * 200
        raise OptecsTestException(msgStart + filler + msgEnd)

    @pyqtProperty(bool, notify=unusedSignal)
    def isTestMode(self):
        """
        if DB is pointing at IFQADMIN or IFQDEV, True else False (production!)
        @return: True if Test mode
        """
        mode = ObserverDBUtil.get_setting('optecs_mode')
        return False if mode == 'ifq' else True

    @pyqtProperty(bool, notify=unusedSignal)
    def isTrainingMode(self):
        """
        @return: True if training mode
        """
        mode = ObserverDBUtil.get_setting('training')
        return True if mode == 'TRUE' else False

    @pyqtProperty(QVariant, notify=unusedSignal)
    def optecsMode(self):
        """
        @return: optecs mode, e.g. ifqadmin
        """
        return ObserverDBUtil.get_setting('optecs_mode', 'ifqadmin').upper()

    @pyqtSlot(str, name='backupToPath', result=str)
    def backup_db_to_path(self, path):
        try:
            if not self._backup_thread.isRunning():
                self._backup_worker = BackupDBWorker(dest_path=path)
                self._backup_worker.moveToThread(self._backup_thread)
                self._backup_worker.backupStatus.connect(self._backup_status_received)
                self._backup_thread.started.connect(self._backup_worker.run)
                self._backup_thread.start()
            return f'Backup started to\n{path}...'
        except Exception as e:
            return textwrap.fill(f'FAIL:\nCould not back up DB:\n{e}', 60)

    def _backup_status_received(self, success, message):
        """
        Method to catch the backup results
        @param success: True/False if succeeded
        @param message: Description of status
        @return:
        """
        if success:
            self._update_backup_time()
        self.backupStatusChanged.emit(success, message)
        self._backup_thread.quit()

    @pyqtProperty(QVariant, notify=lastBackupTimeChanged)
    def lastBackupTime(self):
        """
        Returns string representation of last DB backup.
        @return: string value
        """
        try:
            last_sync = Settings.get(Settings.parameter == 'last_backup_time')
            last_time = arrow.get(last_sync.value)
            return last_time.humanize()
        except Settings.DoesNotExist:
            return 'Never'

    def _update_backup_time(self):
        """
        Set most recent backup time to now.
        @return:
        """
        try:
            last_sync = Settings.get(Settings.parameter == 'last_backup_time')
            last_sync.value = arrow.now()
            last_sync.save()
        except Settings.DoesNotExist:
            new_setting = Settings.create(parameter='last_backup_time',
                                          value=arrow.now())
            new_setting.save()
        self.lastBackupTimeChanged.emit()

    @pyqtSlot(name='updateDriveLetters')
    def update_drive_letters(self):
        """
        Send new drive letters signal
        @return:
        """
        self.driveLettersChanged.emit(ObserverDBUtil.get_external_drive_letters())

    @pyqtProperty(QVariant, notify=driveLettersChanged)
    def driveLetters(self):
        return ObserverDBUtil.get_external_drive_letters()


class OptecsTestException(Exception):
    pass


class TestObserverState(unittest.TestCase):
    """
    Test basic SQLite connectivity, properties
    TODO{wsmith} Need to enhance these tests
    """

    def setUp(self):
        self.testdata = ObserverState(db=ObserverData())

    def proptest_bool(self, testproperty):
        testval = testproperty
        self.assertIsNotNone(testval)
        testproperty = not testval
        self.assertEqual(testproperty, not testval)
        testproperty = testval
        self.assertEqual(testproperty, testval)

    def test_property_catchshare(self):
        self.proptest_bool(self.testdata.defaultCatchShare)

    def test_property_geartype(self):
        self.proptest_bool(self.testdata.isGearTypeTrawl)

    def test_firstrun(self):
        fr = self.testdata.firstRun
        origval = fr
        self.testdata.firstRun = not origval
        self.assertEqual(self.testdata.firstRun, not origval)
        self.testdata.firstRun = origval
        self.assertEqual(self.testdata.firstRun, origval)


if __name__ == '__main__':
    unittest.main()
