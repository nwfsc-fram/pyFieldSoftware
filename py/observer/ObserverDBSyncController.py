# -----------------------------------------------------------------------------
# Name:        ObserverDBSyncController.py
# Purpose:     OPTECS DB Utility
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 10, 2016
# License:     MIT
#
# ------------------------------------------------------------------------------
import csv
import logging
import re
import textwrap

import io
from time import sleep

from PyQt5.QtCore import QObject, pyqtSlot, QThread
from PyQt5.QtCore import QVariant
from PyQt5.QtCore import pyqtProperty
from PyQt5.QtCore import pyqtSignal
import arrow

from py.observer.ObserverData import ObserverData
from py.observer.ObserverDBModels import Trips, DbSync, FishingActivities, FishingLocations, Catches, \
    SpeciesCompositions, SpeciesCompositionItems, BioSpecimens, BioSpecimenItems, TripCertificates, FishTickets, \
    Dissections, SpeciesCompositionBaskets, CatchAdditionalBaskets, Lookups
from py.observer.ObserverDBSyncModel import ObserverDBSyncModel
from py.observer.ObserverDBUtil import ObserverDBUtil
from py.observer.ObserverSOAP import ObserverSoap
from py.observer.SyncDBWorker import SyncDBWorker, DBSyncStatusEnum
from py.observer.ObserverDBModels import Settings


class SyncFailedException(Exception):
    pass


class ObserverDBSyncController(QObject):
    SyncInfoModelChanged = pyqtSignal(name='SyncInfoModelChanged')
    syncStarted = pyqtSignal(name='syncStarted')
    abortSync = pyqtSignal(QVariant, name='abortSync', arguments=['reason'])
    pullComplete = pyqtSignal(bool, QVariant, name='pullComplete', arguments=['success', 'result'])
    pushComplete = pyqtSignal(bool, QVariant, name='pushComplete', arguments=['success', 'result'])
    readyToPush = pyqtSignal(name='readyToPush')
    dbSyncTimeChanged = pyqtSignal(name='dbSyncTimeChanged')
    userInfoChanged = pyqtSignal(name='userInfoChanged')

    desc = {DBSyncStatusEnum.TRIP_IN_PROGRESS: 'Trip in Progress',
            DBSyncStatusEnum.SYNC_READY: 'Ready to Sync',
            DBSyncStatusEnum.SYNC_ERROR: 'Partially Synced - Retry',
            DBSyncStatusEnum.SYNC_COMPLETED: 'Sync Completed'}

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)

        self._sync_info_model = ObserverDBSyncModel()

        self._soap_username = None
        self._soap_password = None

        self._soap = None

        # DB Sync Thread
        self._sync_thread = QThread()
        self._sync_worker = None

        self.update_db_sync_table()

    def _initialize_soap_obj(self):
        """
        Handle offline mode/ failures gracefully
        @return:
        """
        try:
            if not self._soap:
                self._soap = ObserverSoap()
            return True
        except Exception as e:
            self._logger.error(f'SOAP is not available, offline mode? {e}')
            return False

    @pyqtSlot(name='updateDBSyncInfo')
    def update_db_sync_table(self):
        """
        Loads DB_SYNC table from database and builds model
        TODO: Automatically determine if trip is "Ended" (currently, QML End Trip sets this.)
        """
        self._logger.debug('Updating DB Sync table...')
        self._sync_info_model.clear()
        trips_q = Trips.select()
        for trip in trips_q:
            try:
                DbSync.get(DbSync.trip == trip.trip)
            except DbSync.DoesNotExist:
                status = DBSyncStatusEnum.TRIP_IN_PROGRESS
                DbSync.create(trip=trip, status=status.value)
        try:
            dbsync_q = DbSync.select().order_by(DbSync.status)
            for syncitem in dbsync_q:
                if syncitem and syncitem.trip:
                    status = DBSyncStatusEnum(syncitem.status)
                    try:
                        cur_trip = Trips.get(Trips.trip == syncitem.trip.trip)
                        user_name = ' '.join((cur_trip.user.first_name, cur_trip.user.last_name))
                        fishery_name = self.find_fishery_name(cur_trip.fishery)
                        self._sync_info_model.appendItem({'trip_id': syncitem.trip.trip,
                                                          'external_trip_id': syncitem.trip.external_trip,
                                                          'sync_status': self.desc[status],
                                                          'user_name': user_name,
                                                          'fishery': fishery_name})
                    except Exception as e:
                        self._logger.error(f'Skipping DB sync item - {e}')
                else:
                    self._logger.warning('Skipping DB sync item - Null Trip')
        except Trips.DoesNotExist as e:  # Handle FIELD-1283 weird error
            self._logger.error(f'Error updating DB sync info for trip, {e}')
        except Exception as e:
            self._logger.error(f'Error updating DB sync info, {e}')

        self.SyncInfoModelChanged.emit()
        self._logger.debug('DB Sync table updated')

    @staticmethod
    def find_fishery_name(fishery_id: str) -> str:
        """
        Find LOOKUPS entry for fishery ID
        @param fishery_id: lookup_value in LOOKUPS
        @return: LOOKUPS.DESCRIPTION for fishery
        """
        try:
            fishery = Lookups.get(Lookups.lookup_type == 'FISHERY',
                                  Lookups.lookup_value == fishery_id)
            return fishery.description

        except Lookups.DoesNotExist:
            return '?'

    @pyqtSlot(int, name='markTripForSync')
    def mark_trip_for_sync(self, trip_id):
        self._logger.info('Marking Trip {} ready for sync.'.format(trip_id))
        try:
            trip_q = DbSync.get(DbSync.trip == trip_id)
            trip_q.status = DBSyncStatusEnum.SYNC_READY.value
            trip_q.save()
            self.update_db_sync_table()
        except DbSync.DoesNotExist:
            self._logger.error('Could not find trip {}'.format(trip_id))

    @pyqtSlot(int, name='markTripInProgress')
    def mark_trip_in_progress(self, trip_id):
        """
        TODO: When user selects a previously ended trip (for editing,) mark as In Progress until Ended again
        @param trip_id:
        @return:
        """
        self._logger.info('Marking Trip {} as in progress.'.format(trip_id))
        try:
            trip_q = DbSync.get(DbSync.trip == trip_id)
            trip_q.status = DBSyncStatusEnum.TRIP_IN_PROGRESS.value
            trip_q.save()
            self.update_db_sync_table()
        except DbSync.DoesNotExist:
            if trip_id:
                self._logger.info(f'Could not find DB sync status for trip {trip_id}, creating.')
                status = DBSyncStatusEnum.TRIP_IN_PROGRESS
                DbSync.create(trip=trip_id, status=status.value)

    @pyqtSlot(int, name='cycleTripSyncStatus')
    def cycle_trip_sync_status(self, trip_id):
        """
        TODO: When user selects a previously ended trip (for editing,) mark as In Progress until Ended again
        @param trip_id:
        @return:
        """
        if trip_id:
            self._logger.info(f'Cycling Trip {trip_id} status.')
        else:
            self._logger.warning(f'Trip {trip_id} does not exist, skip cycling.')
        try:
            trip_q = DbSync.get(DbSync.trip == trip_id)
            cycle_status_dict = {  # Cycle to next status
                DBSyncStatusEnum.SYNC_ERROR.value: DBSyncStatusEnum.SYNC_READY.value,  # hopefully rare
                DBSyncStatusEnum.TRIP_IN_PROGRESS.value: DBSyncStatusEnum.SYNC_READY.value,
                DBSyncStatusEnum.SYNC_READY.value: DBSyncStatusEnum.SYNC_COMPLETED.value,
                DBSyncStatusEnum.SYNC_COMPLETED.value: DBSyncStatusEnum.TRIP_IN_PROGRESS.value,
            }
            trip_q.status = cycle_status_dict.get(trip_q.status, DBSyncStatusEnum.TRIP_IN_PROGRESS.value)
            trip_q.save()
            self.update_db_sync_table()
        except DbSync.DoesNotExist:
            if trip_id:
                self._logger.info(f'Could not find DB sync status for trip {trip_id}, creating.')
                status = DBSyncStatusEnum.TRIP_IN_PROGRESS
                DbSync.create(trip=trip_id, status=status.value)

    @staticmethod
    def get_completed_trip_ids():
        trip_q = DbSync.select().where(DbSync.status == DBSyncStatusEnum.SYNC_COMPLETED.value)
        trip_ids = [t.trip.trip for t in trip_q]
        return trip_ids

    @staticmethod
    def get_ready_to_sync_trip_ids():
        trip_q = DbSync.select().where((DbSync.status == DBSyncStatusEnum.SYNC_READY.value) |
                                       (DbSync.status == DBSyncStatusEnum.SYNC_ERROR.value))
        trip_ids = [t.trip.trip for t in trip_q]
        return trip_ids

    @pyqtProperty(QVariant, notify=SyncInfoModelChanged)
    def SyncInfoModel(self):
        return self._sync_info_model

    @pyqtSlot(result=bool)
    def isOnline(self):
        return self._initialize_soap_obj()

    @pyqtProperty(QVariant, notify=userInfoChanged)
    def currentSOAPUsername(self):
        return self._soap_username

    @currentSOAPUsername.setter
    def currentSOAPUsername(self, username):
        self._soap_username = username

    @pyqtProperty(QVariant, notify=userInfoChanged)
    def currentSOAPPassword(self):
        if self._soap_username and self._soap_password:
            return self._soap.hash_pw(self._soap_username, self._soap_password)

    @currentSOAPPassword.setter
    def currentSOAPPassword(self, password):
        self._soap_password = password

    @staticmethod
    def get_now_datestr():
        """
        Get date str for DB
        @return:Form of 12/23/2015 23:07 - timezone naiive
        """
        return arrow.now().format('M/D/YYYY HH:mm')

    @staticmethod
    def make_csv_api_friendly(csvtext):
        """
        Modify CSV strings to match what API expects
        @param csvtext: input csv
        @return: fixed csv
        """
        new_csv = csvtext.replace(',""', ',')  # replace ,"","" with ,,
        new_csv = new_csv.replace('"FALSE"', '"F"')  # Shorten bool
        new_csv = new_csv.replace('"TRUE"', '"T"')  # Shorten bool

        # use regex to find dates and remove quotes
        # format is "01/20/2017 19:16"
        datestr_found = re.findall('\"[01][0-9]\/[0123][0-9]\/20.{2} .{2}:.{2}\"', new_csv)
        for d in datestr_found:
            noquotes = d.replace('"', '')
            new_csv = new_csv.replace(d, noquotes)
        return new_csv

    @pyqtSlot(name='performSync')
    def perform_sync(self):
        """"
        Does a pull then emits readyToPush signal to do a push
        TODO: collapse this into one
        """
        self.retrieve_db_update_threaded(send_push_signal=True)

    @pyqtSlot(name='performRetrieveUpdates')
    def retrieve_updates(self):
        """
        Only does a pull, not a full sync
        """
        self.retrieve_db_update_threaded()

    @pyqtSlot(name='uploadTrips', result=str)
    def upload_trips(self):
        """
        Tries to sync trips
        @return: result message string
        """
        if not self._initialize_soap_obj():
            return 'Offline, cannot sync.'

        trip_ids = self.get_ready_to_sync_trip_ids()

        if not trip_ids:
            self.pushComplete.emit(False, "No trips are Ready to Sync.")
        else:
            self.db_push_threaded(trip_ids)

    @pyqtProperty(QVariant, notify=dbSyncTimeChanged)
    def dbSyncTime(self):
        """
        Returns string representation of last DB sync.
        @return: string value
        """
        try:
            last_sync = Settings.get(Settings.parameter == 'last_db_sync')

            last_time = arrow.get(last_sync.value)
            return last_time.humanize()
        except Settings.DoesNotExist:
            return 'Never'

    @dbSyncTime.setter
    def dbSyncTime(self, new_time):
        """
        Set last DB sync time, emits changed signal
        @param new_time: arrow time
        """
        try:
            last_sync = Settings.get(Settings.parameter == 'last_db_sync')
            last_sync.value = new_time
            last_sync.save()
        except Settings.DoesNotExist:
            new_setting = Settings.create(parameter='last_db_sync',
                                          value=new_time)
            new_setting.save()
        self.dbSyncTimeChanged.emit()

    def _update_db_sync_time(self, new_time=arrow.now()):
        self.dbSyncTime = new_time

    def retrieve_db_update_threaded(self, send_push_signal=False) -> (bool, str):
        try:
            if not self._sync_thread.isRunning():
                self._sync_worker = SyncDBWorker(upload_trips=False, send_push_signal=send_push_signal,
                                                 soap=self._soap)
                self._sync_worker.moveToThread(self._sync_thread)
                self._sync_worker.pullComplete.connect(self._pull_complete)
                self._sync_worker.readyForPush.connect(self._ready_for_push)
                self._sync_worker.runSync(logger=self._logger)
            self.syncStarted.emit()
            return True, f'Retrieving DB updates...'
        except Exception as e:
            return False, textwrap.fill(f'FAIL:\nCould not retrieve DB updates:\n{e}', 60)

    def db_push_threaded(self, trip_ids) -> (bool, str):
        try:
            if not self._sync_thread.isRunning():
                self._sync_worker = SyncDBWorker(upload_trips=True,
                                                 soap=self._soap, sync_controller=self,
                                                 trip_ids=trip_ids)
                self._sync_worker.moveToThread(self._sync_thread)
                self._sync_worker.pushComplete.connect(self._push_complete)
                self._sync_worker.runSync(logger=self._logger)
            return True, f'Pushing trip(s) to DB...'
        except Exception as e:
            return False, textwrap.fill(f'FAIL:\nCould not push to DB:\n{e}', 60)

    def _ready_for_push(self):
        """
        Emitted by thread when completed pull, and flag to push is set
        """
        self.readyToPush.emit()

    def _pull_complete(self, success, message):
        """
        Method to catch the DB pulldown results
        @param success: True/False if succeeded
        @param message: Description of status
        @return:
        """
        self._logger.info(f'Got {success} {message}')
        if success:
            self.pullComplete.emit(success, message)
            self._update_db_sync_time()
        else:
            self.abortSync.emit(message)
        self._sync_thread.quit()

    def _push_complete(self, success, message):
        """
        Method to catch the DB upload results
        @param success: True/False if succeeded
        @param message: Description of status
        @return:
        """
        self._logger.info(f'Got {success} {message}')
        if success:
            self.pushComplete.emit(success, message)
        else:
            self.abortSync.emit(message)
        self._sync_thread.quit()

    def _translate_bool_to_binary_str(self, bool_str):
        """
        DB helper
        @return: convert 'TRUE' to '1' and 'FALSE' to '0', else None
        """
        if bool_str in ('0', '1'):
            return bool_str
        binary_lookup = {'TRUE': '1', 'FALSE': '0'}
        if bool_str in binary_lookup.keys():
            return binary_lookup[bool_str]

    # <editor-fold desc="Generate TRIPS">
    def generate_trips_csv(self, trip_id, user_id):
        """
        Generate TRIPS CSV for upload. We seemingly only do this 1 trip at a time.
        @param trip_id: trip ID
        @param user_id: uid
        @return: csv
        """

        table_name = 'TRIPS'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "TRIP_ID", "VESSEL_ID", "USER_ID", "PROGRAM_ID", "DEBRIEFING_ID",
            "TRIP_STATUS", "DEPARTURE_PORT_ID", "DEPARTURE_DATE",
            "RETURN_PORT_ID", "RETURN_DATE", "LOGBOOK_NUMBER", "NOTES",
            "DATA_QUALITY", "CREATED_BY", "CREATED_DATE", "MODIFIED_BY",
            "MODIFIED_DATE", "OTC_KP", "TOTAL_HOOKS_KP", "OBSERVER_LOGBOOK",
            "EVALUATION_ID", "PARTIAL_TRIP", "SKIPPER_ID", "FISHERY", "CREW_SIZE",
            "PERMIT_NUMBER", "LICENSE_NUMBER", "LOGBOOK_TYPE", "FIRST_RECEIVER",
            "EXPORT", "EXTERNAL_TRIP_ID", "DO_EXPAND", "RUN_TER", "DATA_SOURCE",
            "ROW_PROCESSED", "ROW_STATUS", "FISH_PROCESSED", "NO_FISHING_ACTIVITY",
            "INTENDED_GEAR_TYPE", "TOTAL_FISHING_DAYS"
        ]
        # Get trips
        activities_q = Trips.select().where(Trips.trip == trip_id)
        output = io.StringIO()

        if not len(activities_q):
            return filename, None

        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in activities_q:
            return_port = row.return_port.port if row.return_port else None
            departure_port = row.departure_port.port if row.departure_port else None
            first_receiver = row.first_receiver.first_receiver if row.first_receiver else None
            fishing_days = row.fishing_days_count if row.fishing_days_count else None
            skipper = row.skipper.contact if row.skipper else None
            trip_status = "1"  # TODO what is this
            program_id = row.program.program
            row_values = [
                row.trip, row.vessel.vessel, row.user.user, program_id, row.debriefing,
                # "TRIP_ID", "VESSEL_ID", "USER_ID", "PROGRAM_ID", "DEBRIEFING_ID",
                trip_status, departure_port, row.departure_date,
                # "TRIP_STATUS", "DEPARTURE_PORT_ID", "DEPARTURE_DATE",
                return_port, row.return_date, row.logbook_number, row.notes,
                # "RETURN_PORT_ID", "RETURN_DATE", "LOGBOOK_NUMBER", "NOTES",
                row.data_quality, row.created_by, row.created_date, None,
                # "DATA_QUALITY", "CREATED_BY", "CREATED_DATE", "MODIFIED_BY",
                None, row.otc_kp, row.total_hooks_kp, row.observer_logbook,
                # "MODIFIED_DATE", "OTC_KP", "TOTAL_HOOKS_KP", "OBSERVER_LOGBOOK",
                row.evaluation, row.partial_trip, skipper, row.fishery, row.crew_size,
                # "EVALUATION_ID", "PARTIAL_TRIP", "SKIPPER_ID", "FISHERY", "CREW_SIZE",
                None, None, row.logbook_type, first_receiver,  # TODO: PERMIT_NUMBER, LICENSE_NUMBER
                # "PERMIT_NUMBER", "LICENSE_NUMBER", "LOGBOOK_TYPE", "FIRST_RECEIVER",
                None, None, None, None, ObserverDBUtil.get_data_source(),
                # "EXPORT", "EXTERNAL_TRIP_ID", "DO_EXPAND", "RUN_TER", "DATA_SOURCE",
                None, None, row.fish_processed, None,
                # "ROW_PROCESSED", "ROW_STATUS", "FISH_PROCESSED", "NO_FISHING_ACTIVITY",
                None, fishing_days
                # "INTENDED_GEAR_TYPE", "TOTAL_FISHING_DAYS"
            ]
            writer.writerow(row_values)
        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)
        return filename, csv_output

    # </editor-fold>

    # <editor-fold desc="Generate FISHING_ACTIVITIES">
    def generate_fishing_activities_csv(self, trip_id, user_id):
        """
        Generate CSV for upload
        @return: filename, CSV unencoded
        """
        table_name = 'FISHING_ACTIVITIES'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "FISHING_ACTIVITY_ID", "TRIP_ID", "FISHING_ACTIVITY_NUM", "OBSERVER_TOTAL_CATCH",
            "OTC_WEIGHT_UM", "OTC_WEIGHT_METHOD", "TOTAL_HOOKS", "GEAR_TYPE", "GEAR_PERFORMANCE",
            "BEAUFORT_VALUE", "VOLUME", "VOLUME_UM", "DENSITY", "DENSITY_UM", "NOTES", "CREATED_BY",
            "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE", "TARGET_STRATEGY_ID", "CATCH_WEIGHT_KP",
            "CATCH_COUNT_KP", "HOOKS_SAMPLED_KP", "EFP", "SAMPLE_WEIGHT_KP", "SAMPLE_COUNT_KP",
            "DETERRENT_USED", "AVG_SOAK_TIME", "TOT_GEAR_SEGMENTS", "GEAR_SEGMENTS_LOST",
            "EXCLUDER_TYPE", "TOTAL_HOOKS_LOST", "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS",
            "DATA_QUALITY", "CAL_WEIGHT", "FIT", "BRD_PRESENT"
        ]
        # Get hauls/ sets
        activities_q = FishingActivities.select().where(FishingActivities.trip == trip_id)
        output = io.StringIO()

        if not len(activities_q):
            return filename, None

        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in activities_q:
            target_strategy = row.target_strategy.catch_category if row.target_strategy else None
            brd_present = self._translate_bool_to_binary_str(row.brd_present)
            deterrent_used = self._translate_bool_to_binary_str(row.deterrent_used)
            row_values = [
                row.fishing_activity,
                # "FISHING_ACTIVITY_ID",
                row.trip.trip, row.fishing_activity_num, row.observer_total_catch,
                # "TRIP_ID", "FISHING_ACTIVITY_NUM", "OBSERVER_TOTAL_CATCH",
                'LB', row.otc_weight_method,
                # "OTC_WEIGHT_UM", "OTC_WEIGHT_METHOD",
                row.total_hooks, row.gear_type, row.gear_performance,
                # "TOTAL_HOOKS", "GEAR_TYPE", "GEAR_PERFORMANCE",
                row.beaufort_value, row.volume, row.volume_um, row.density, row.density_um, row.notes,
                # "BEAUFORT_VALUE", "VOLUME", "VOLUME_UM", "DENSITY", "DENSITY_UM", "NOTES",
                row.created_by, row.created_date, None, None, target_strategy, row.catch_weight_kp,
                # "CREATED_BY", "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE", "TARGET_STRATEGY_ID", "CATCH_WEIGHT_KP",
                row.catch_count_kp, row.hooks_sampled_kp, row.efp, row.sample_weight_kp, row.sample_count_kp,
                # "CATCH_COUNT_KP", "HOOKS_SAMPLED_KP", "EFP", "SAMPLE_WEIGHT_KP", "SAMPLE_COUNT_KP",
                deterrent_used, row.avg_soak_time, row.tot_gear_segments, row.gear_segments_lost, None,
                # "DETERRENT_USED", "AVG_SOAK_TIME", "TOT_GEAR_SEGMENTS", "GEAR_SEGMENTS_LOST", "EXCLUDER_TYPE",
                row.total_hooks_lost, ObserverDBUtil.get_data_source(),
                # "TOTAL_HOOKS_LOST", "DATA_SOURCE",
                None, None, row.data_quality,
                # "ROW_PROCESSED", "ROW_STATUS", "DATA_QUALITY",
                row.cal_weight, row.fit, brd_present
                # "CAL_WEIGHT", "FIT", "BRD_PRESENT"
            ]
            writer.writerow(row_values)
        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)
        return filename, csv_output

    # </editor-fold>

    # <editor-fold desc="Generate FISHING_LOCATIONS">
    def generate_fishing_locations_csv(self, trip_id, user_id):
        """
        Generate CSV for upload
        @return: filename, CSV unencoded
        """
        table_name = 'FISHING_LOCATIONS'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "FISHING_LOCATION_ID", "FISHING_ACTIVITY_ID", "LOCATION_DATE",
            "LATITUDE", "LONGITUDE", "DEPTH", "DEPTH_UM", "POSITION",
            "CREATED_BY", "CREATED_DATE", "MODIFIED_BY",
            "MODIFIED_DATE", "NOTES", "DATA_SOURCE",
            "ROW_PROCESSED", "ROW_STATUS"
        ]

        # Get activities
        activities_q = FishingActivities.select(FishingActivities.fishing_activity).where(
            FishingActivities.trip == trip_id)
        fishing_activity_ids = [q.fishing_activity for q in activities_q]
        # Get related locations
        locations_q = FishingLocations.select().where(FishingLocations.fishing_activity << fishing_activity_ids)  # IN

        if not len(locations_q):
            return filename, None

        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in locations_q:
            row_values = [
                row.fishing_location, row.fishing_activity.fishing_activity, row.location_date,
                # "FISHING_LOCATION_ID", "FISHING_ACTIVITY_ID", "LOCATION_DATE",
                row.latitude, row.longitude, row.depth, row.depth_um, row.position,
                # "LATITUDE", "LONGITUDE", "DEPTH", "DEPTH_UM", "POSITION",
                row.created_by, row.created_date, None, None,
                # "CREATED_BY", "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE",
                row.notes, ObserverDBUtil.get_data_source(),
                # "NOTES", "DATA_SOURCE",
                None, None
                # "ROW_PROCESSED", "ROW_STATUS"
            ]
            writer.writerow(row_values)

        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)

        return filename, csv_output

    # </editor-fold>

    # <editor-fold desc="Generate CATCHES">
    def generate_catches_csv(self, trip_id, user_id):
        """
        Generate CSV for upload
        @return: filename, CSV unencoded
        """
        table_name = 'CATCHES'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "CATCH_ID", "FISHING_ACTIVITY_ID", "CATCH_CATEGORY_ID",
            "CATCH_WEIGHT", "CATCH_WEIGHT_UM", "CATCH_COUNT", "CATCH_WEIGHT_METHOD",
            "CATCH_DISPOSITION", "DISCARD_REASON", "CATCH_PURITY", "VOLUME", "VOLUME_UM",
            "DENSITY", "DENSITY_UM", "CATCH_NUM", "NOTES", "CREATED_BY", "CREATED_DATE",
            "MODIFIED_BY", "MODIFIED_DATE", "HOOKS_SAMPLED", "SAMPLE_WEIGHT",
            "SAMPLE_WEIGHT_UM", "SAMPLE_COUNT", "CATCH_WEIGHT_ITQ", "LENGTH_ITQ",
            "DENSITY_BASKET_WEIGHT_ITQ", "WIDTH_ITQ", "DEPTH_ITQ", "BASKETS_WEIGHED_ITQ",
            "TOTAL_BASKETS_ITQ", "PARTIAL_BASKET_WEIGHT_ITQ", "UNITS_SAMPLED_ITQ",
            "TOTAL_UNITS_ITQ", "GEAR_SEGMENTS_SAMPLED", "BASKET_WEIGHT_KP",
            "ADDL_BASKET_WEIGHT_KP", "BASKET_WEIGHT_COUNT_KP", "DATA_SOURCE",
            "ROW_PROCESSED", "ROW_STATUS"
        ]

        # Get activities
        activities_q = FishingActivities.select(FishingActivities.fishing_activity).where(
            FishingActivities.trip == trip_id)
        fishing_activity_ids = [q.fishing_activity for q in activities_q]
        # Get related catches
        catches_q = Catches.select().where((Catches.fishing_activity << fishing_activity_ids))

        if not len(catches_q):
            return filename, None

        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in catches_q:
            row_values = [
                row.catch, row.fishing_activity.fishing_activity, row.catch_category.catch_category,
                # "CATCH_ID", "FISHING_ACTIVITY_ID", "CATCH_CATEGORY_ID",
                row.catch_weight, row.catch_weight_um,
                # "CATCH_WEIGHT", "CATCH_WEIGHT_UM",
                row.catch_count, row.catch_weight_method, row.catch_disposition, row.discard_reason,
                # "CATCH_COUNT", "CATCH_WEIGHT_METHOD", "CATCH_DISPOSITION", "DISCARD_REASON",
                row.catch_purity, row.volume, row.volume_um, row.density, row.density_um, row.catch_num,
                # "CATCH_PURITY", "VOLUME", "VOLUME_UM", "DENSITY", "DENSITY_UM", "CATCH_NUM",
                row.notes, row.created_by, row.created_date, None, None, row.hooks_sampled,
                # "NOTES", "CREATED_BY", "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE", "HOOKS_SAMPLED",
                row.sample_weight, row.sample_weight_um, row.sample_count, None, None,
                # "SAMPLE_WEIGHT", "SAMPLE_WEIGHT_UM", "SAMPLE_COUNT", "CATCH_WEIGHT_ITQ", "LENGTH_ITQ",
                None, None, None, None,
                # "DENSITY_BASKET_WEIGHT_ITQ", "WIDTH_ITQ", "DEPTH_ITQ", "BASKETS_WEIGHED_ITQ",
                None, None, None, None,
                # "TOTAL_BASKETS_ITQ", "PARTIAL_BASKET_WEIGHT_ITQ", "UNITS_SAMPLED_ITQ", "TOTAL_UNITS_ITQ",
                row.gear_segments_sampled, row.basket_weight_kp, row.addl_basket_weight_kp, row.basket_weight_count_kp,
                # "GEAR_SEGMENTS_SAMPLED", "BASKET_WEIGHT_KP", "ADDL_BASKET_WEIGHT_KP", "BASKET_WEIGHT_COUNT_KP",
                ObserverDBUtil.get_data_source(), None, None
                # "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS"
            ]
            writer.writerow(row_values)

        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)

        return filename, csv_output

    # </editor-fold>

    # <editor-fold desc="Generate SPECIES_COMPOSITIONS">
    def generate_speciescomp_csv(self, trip_id, user_id):
        """
        Generate CSV for upload
        @return: filename, CSV unencoded
        """
        table_name = 'SPECIES_COMPOSITIONS'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "SPECIES_COMPOSITION_ID", "CATCH_ID", "SAMPLE_METHOD", "NOTES", "CREATED_BY",
            "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE", "SPECIES_WEIGHT_KP", "SPECIES_NUMBER_KP",
            "BASKET_NUMBER", "DATA_QUALITY", "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS"
        ]

        # Get activity id's
        activities_q = FishingActivities.select(FishingActivities.fishing_activity).where(
            FishingActivities.trip == trip_id)
        fishing_activity_ids = [q.fishing_activity for q in activities_q]

        # Get related catch id's
        catches_q = Catches.select().where(Catches.fishing_activity << fishing_activity_ids)  # IN
        catch_ids = [q.catch for q in catches_q]

        # Get related species comp id's
        species_q = SpeciesCompositions.select().where(SpeciesCompositions.catch << catch_ids)  # IN

        if not len(species_q):
            return filename, None

        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in species_q:
            row_values = [
                row.species_composition, row.catch.catch, row.sample_method, row.notes, row.created_by,
                # "SPECIES_COMPOSITION_ID", "CATCH_ID", "SAMPLE_METHOD", "NOTES", "CREATED_BY",
                row.created_date, None, None, row.species_weight_kp, row.species_number_kp,
                # "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE", "SPECIES_WEIGHT_KP", "SPECIES_NUMBER_KP",
                row.basket_number, row.data_quality, ObserverDBUtil.get_data_source(), None, None
                # "BASKET_NUMBER", "DATA_QUALITY", "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS"
            ]
            writer.writerow(row_values)

        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)

        return filename, csv_output

    # </editor-fold>

    # <editor-fold desc="Generate SPECIES_COMPOSITION_ITEMS">
    def generate_speciescomp_items_csv(self, trip_id, user_id):
        """
        Generate CSV for upload
        @return: filename, CSV unencoded
        """
        table_name = 'SPECIES_COMPOSITION_ITEMS'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "SPECIES_COMP_ITEM_ID", "SPECIES_ID", "SPECIES_COMPOSITION_ID", "SPECIES_WEIGHT",
            "SPECIES_WEIGHT_UM", "SPECIES_NUMBER", "NOTES", "DISCARD_REASON", "CREATED_BY",
            "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE", "HANDLING", "TOTAL_TALLY",
            "SPECIES_WEIGHT_KP_ITQ", "SPECIES_NUMBER_KP_ITQ", "DATA_SOURCE",
            "ROW_PROCESSED", "ROW_STATUS"
        ]

        # Get activity id's
        activities_q = FishingActivities.select(FishingActivities.fishing_activity).where(
            FishingActivities.trip == trip_id)
        fishing_activity_ids = [q.fishing_activity for q in activities_q]

        # Get related catch id's
        catches_q = Catches.select().where(Catches.fishing_activity << fishing_activity_ids)  # IN
        catch_ids = [q.catch for q in catches_q]

        # Get related species comp id's
        species_q = SpeciesCompositions.select().where(SpeciesCompositions.catch << catch_ids)  # IN
        species_comp_ids = [q.species_composition for q in species_q]

        # Get species comp items
        species_comp_items_q = SpeciesCompositionItems.select(). \
            where(SpeciesCompositionItems.species_composition << species_comp_ids)

        # Exclude items for OPTECS-only Species MIX, a pseudo-species used to collect catch-level basket data.
        species_comp_items_q = self._filter_mix_species_comp_items(species_comp_items_q)

        if not len(species_comp_items_q):
            return filename, None

        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in species_comp_items_q:
            row_values = [
                row.species_comp_item, row.species.species, row.species_composition.species_composition,
                # "SPECIES_COMP_ITEM_ID", "SPECIES_ID", "SPECIES_COMPOSITION_ID",
                row.species_weight, row.species_weight_um, row.species_number, row.notes,
                # "SPECIES_WEIGHT", "SPECIES_WEIGHT_UM", "SPECIES_NUMBER", "NOTES",
                row.discard_reason, row.created_by, row.created_date, None, None,
                # "DISCARD_REASON", "CREATED_BY", "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE",
                row.handling, row.total_tally, None, None, ObserverDBUtil.get_data_source(),
                # "HANDLING", "TOTAL_TALLY", "SPECIES_WEIGHT_KP_ITQ", "SPECIES_NUMBER_KP_ITQ", "DATA_SOURCE",
                None, None
                # "ROW_PROCESSED", "ROW_STATUS"
            ]
            writer.writerow(row_values)

        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)

        return filename, csv_output

    def _filter_mix_species_comp_items(self, species_comp_items_q):
        """
        Exclude items for OPTECS-only Species MIX, a pseudo-species used to collect catch-level basket data.
        Because MIX baskets are stored in CATCH_ADDITIONAL_BASKETS, not SPECIES_COMPOSITION_BASKETS, and
        because IFQ has no entry for this OPTECS-only MIX species, exclude any MIX species comp items from upload.
        """
        species_comp_items_filtered_q = species_comp_items_q.select(). \
            where(SpeciesCompositionItems.species != ObserverData.MIX_SPECIES_CODE)

        n_mix_species_comp_item_records = species_comp_items_q.count() - species_comp_items_filtered_q.count()
        if n_mix_species_comp_item_records > 0:
            self._logger.info(f"Filtered out {n_mix_species_comp_item_records} MIX spec comp items")
            return species_comp_items_filtered_q

        return species_comp_items_q

    # </editor-fold>

    # <editor-fold desc="Generate SPECIES_COMPOSITION_BASKETS">
    def generate_speciescomp_baskets_csv(self, trip_id, user_id):
        """
        Generate CSV for upload
        @return: filename, CSV unencoded
        """
        table_name = 'SPECIES_COMPOSITION_BASKETS'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "SPECIES_COMP_BASKET_ID", "SPECIES_COMP_ITEM_ID",
            "BASKET_WEIGHT_ITQ", "FISH_NUMBER_ITQ",
            "CREATED_DATE", "CREATED_BY", "MODIFIED_BY",
            "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS"
        ]

        # Get activity id's
        activities_q = FishingActivities.select(FishingActivities.fishing_activity).where(
            FishingActivities.trip == trip_id)
        fishing_activity_ids = [q.fishing_activity for q in activities_q]

        # Get related catch id's
        catches_q = Catches.select().where(Catches.fishing_activity << fishing_activity_ids)  # IN
        catch_ids = [q.catch for q in catches_q]

        # Get related species comp id's
        species_q = SpeciesCompositions.select().where(SpeciesCompositions.catch << catch_ids)  # IN
        species_comp_ids = [q.species_composition for q in species_q]

        # Get species comp items
        species_comp_items_q = SpeciesCompositionItems.select(). \
            where(SpeciesCompositionItems.species_composition << species_comp_ids)  # IN
        species_comp_item_ids = [q.species_comp_item for q in species_comp_items_q]

        # Get species comp baskets
        species_baskets_q = SpeciesCompositionBaskets.select(). \
            where((SpeciesCompositionBaskets.species_comp_item << species_comp_item_ids) &
                  (SpeciesCompositionBaskets.basket_weight_itq.is_null(False)) &  # omit trawl tallies
                  (SpeciesCompositionBaskets.is_fg_tally_local.is_null(True)))  # omit fg tallies

        if not len(species_baskets_q):
            return filename, None

        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in species_baskets_q:
            row_values = [
                row.species_comp_basket, row.species_comp_item.species_comp_item,
                # "SPECIES_COMP_BASKET_ID", "SPECIES_COMP_ITEM_ID",
                row.basket_weight_itq, row.fish_number_itq,
                # "BASKET_WEIGHT_ITQ", "FISH_NUMBER_ITQ",
                row.created_date, row.created_by, None,
                # "CREATED_DATE", "CREATED_BY", "MODIFIED_BY",
                ObserverDBUtil.get_data_source(), None, None
                # "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS"
            ]
            writer.writerow(row_values)

        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)

        return filename, csv_output

    # </editor-fold>

    # <editor-fold desc="Generate CATCH_ADDITIONAL_BASKETS">
    def generate_catch_additional_baskets_csv(self, trip_id, user_id):
        """
        Generate CSV for upload
        @return: filename, CSV unencoded
        """
        table_name = 'CATCH_ADDITIONAL_BASKETS'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "CATCH_ADDTL_BASKETS_ID", "CATCH_ID",
            "BASKET_WEIGHT",
            "CREATED_DATE", "CREATED_BY",
            "MODIFIED_DATE", "MODIFIED_BY",
            "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS",
            "BASKET_TYPE"
        ]

        # Get activity id's
        activities_q = FishingActivities.select(FishingActivities.fishing_activity).where(
            FishingActivities.trip == trip_id)
        fishing_activity_ids = [q.fishing_activity for q in activities_q]

        # Get related catch id's
        catches_q = Catches.select().where(Catches.fishing_activity << fishing_activity_ids)  # IN
        catch_ids = [q.catch for q in catches_q]

        # Get related catch additional baskets
        addl_baskets_q = CatchAdditionalBaskets.select().where(CatchAdditionalBaskets.catch << catch_ids)  # IN

        if not len(addl_baskets_q):
            return filename, None

        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in addl_baskets_q:
            row_values = [
                # "CATCH_ADDTL_BASKETS_ID", "CATCH_ID",
                row.catch_addtl_baskets, row.catch.catch,
                # "BASKET_WEIGHT",
                row.basket_weight,
                # "CREATED_DATE", "CREATED_BY",
                row.created_date, row.created_by,
                # "MODIFIED_DATE", "MODIFIED_BY",
                None, None,
                # "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS",
                ObserverDBUtil.get_data_source(), None, None,
                # "BASKET_TYPE"
                row.basket_type
            ]
            writer.writerow(row_values)

        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)

        return filename, csv_output
        # </editor-fold>

    # <editor-fold desc="Generate BIO_SPECIMENS">
    def generate_bio_specimens_csv(self, trip_id, user_id):
        """
        Generate CSV for upload
        @return: filename, CSV unencoded
        """
        table_name = 'BIO_SPECIMENS'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "BIO_SPECIMEN_ID", "CATCH_ID", "SPECIES_ID", "SAMPLE_METHOD", "NOTES", "CREATED_BY",
            "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE", "SPECIMEN_LENGTH_KP", "SPECIMEN_WEIGHT_KP",
            "LF_LENGTH_KP", "FREQUENCY_KP", "DISCARD_REASON", "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS"
        ]

        # Get activity id's
        activities_q = FishingActivities.select(FishingActivities.fishing_activity).where(
            FishingActivities.trip == trip_id)
        fishing_activity_ids = [q.fishing_activity for q in activities_q]

        # Get related catch id's
        catches_q = Catches.select().where(Catches.fishing_activity << fishing_activity_ids)  # IN
        catch_ids = [q.catch for q in catches_q]

        # Get related bio specimens
        biospecimens_q = BioSpecimens.select().where(BioSpecimens.catch << catch_ids)  # IN

        if not len(biospecimens_q):
            return filename, None

        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in biospecimens_q:
            row_values = [
                row.bio_specimen, row.catch.catch, row.species.species, row.sample_method, row.notes,
                # "BIO_SPECIMEN_ID", "CATCH_ID", "SPECIES_ID", "SAMPLE_METHOD", "NOTES",
                row.created_by, row.created_date, None, None, row.specimen_length_kp,
                # "CREATED_BY", "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE", "SPECIMEN_LENGTH_KP",
                row.specimen_weight_kp, row.lf_length_kp, row.frequency_kp, row.discard_reason,
                ObserverDBUtil.get_data_source(),
                # "SPECIMEN_WEIGHT_KP", "LF_LENGTH_KP", "FREQUENCY_KP", "DISCARD_REASON", "DATA_SOURCE",
                None, None
                # "ROW_PROCESSED", "ROW_STATUS"
            ]
            writer.writerow(row_values)

        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)

        return filename, csv_output

    # </editor-fold>

    # <editor-fold desc="Generate BIO_SPECIMEN_ITEMS">
    def generate_bio_specimen_items_csv(self, trip_id, user_id):
        """
        Generate CSV for upload
        @return: filename, CSV unencoded
        """
        table_name = 'BIO_SPECIMEN_ITEMS'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "BIO_SPECIMEN_ITEM_ID", "BIO_SPECIMEN_ID", "SPECIMEN_WEIGHT",
            "SPECIMEN_WEIGHT_UM", "SPECIMEN_LENGTH", "SPECIMEN_LENGTH_UM", "SPECIMEN_SEX",
            "NOTES", "CREATED_BY", "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE", "VIABILITY",
            "ADIPOSE_PRESENT", "MATURITY", "BAND_ID", "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS"
        ]

        # Get activity id's
        activities_q = FishingActivities.select(FishingActivities.fishing_activity).where(
            FishingActivities.trip == trip_id)
        fishing_activity_ids = [q.fishing_activity for q in activities_q]

        # Get related catch id's
        catches_q = Catches.select().where(Catches.fishing_activity << fishing_activity_ids)  # IN
        catch_ids = [q.catch for q in catches_q]

        # Get related bio specimens
        biospecimens_q = BioSpecimens.select().where(BioSpecimens.catch << catch_ids)  # IN
        bio_specimen_ids = [q.bio_specimen for q in biospecimens_q]

        # Get related biospecimen items
        biospecimen_items_q = BioSpecimenItems.select(). \
            where((BioSpecimenItems.bio_specimen.in_(bio_specimen_ids)))
        # Could not get string operations to work.

        if not len(biospecimen_items_q):
            return filename, None

        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in biospecimen_items_q:
            if row.notes == 'Tally':
                continue
            row_values = [
                row.bio_specimen_item, row.bio_specimen.bio_specimen, row.specimen_weight,
                # "BIO_SPECIMEN_ITEM_ID", "BIO_SPECIMEN_ID", "SPECIMEN_WEIGHT",
                row.specimen_weight_um, row.specimen_length, row.specimen_length_um, row.specimen_sex,
                # "SPECIMEN_WEIGHT_UM", "SPECIMEN_LENGTH", "SPECIMEN_LENGTH_UM", "SPECIMEN_SEX",
                row.notes, row.created_by, row.created_date, None, None, row.viability,
                # "NOTES", "CREATED_BY", "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE", "VIABILITY",
                row.adipose_present, row.maturity, row.band, ObserverDBUtil.get_data_source(), None, None
                # "ADIPOSE_PRESENT", "MATURITY", "BAND_ID", "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS"
            ]
            writer.writerow(row_values)

        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)

        return filename, csv_output

    # </editor-fold>

    # <editor-fold desc="Generate DISSECTIONS">
    def generate_dissections_csv(self, trip_id, user_id):
        """
        Generate CSV for upload
        @return: filename, CSV unencoded
        """
        table_name = 'DISSECTIONS'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "DISSECTION_ID", "BIO_SPECIMEN_ITEM_ID", "DISSECTION_TYPE", "DISSECTION_BARCODE",
            "CREATED_BY", "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE", "RACK_ID",
            "RACK_POSITION", "BS_RESULT", "CWT_CODE", "CWT_STATUS", "CWT_TYPE", "AGE",
            "AGE_READER", "AGE_DATE", "AGE_LOCATION", "AGE_METHOD", "BAND_ID", "DATA_SOURCE",
            "ROW_PROCESSED", "ROW_STATUS"
        ]

        # Get activity id's
        activities_q = FishingActivities.select(FishingActivities.fishing_activity).where(
            FishingActivities.trip == trip_id)
        fishing_activity_ids = [q.fishing_activity for q in activities_q]

        # Get related catch id's
        catches_q = Catches.select().where(Catches.fishing_activity << fishing_activity_ids)  # IN
        catch_ids = [q.catch for q in catches_q]

        # Get related bio specimens
        biospecimens_q = BioSpecimens.select().where(BioSpecimens.catch << catch_ids)  # IN
        bio_specimen_ids = [q.bio_specimen for q in biospecimens_q]

        # Get related biospecimen items
        biospecimen_items_q = BioSpecimenItems.select(). \
            where(BioSpecimenItems.bio_specimen << bio_specimen_ids)  # IN
        bio_specimen_item_ids = [q.bio_specimen_item for q in biospecimen_items_q]

        # Get Dissections
        dissections_q = Dissections.select().where(Dissections.bio_specimen_item << bio_specimen_item_ids)  # IN

        if not len(dissections_q):
            return filename, None

        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in dissections_q:
            row_values = [
                row.dissection, row.bio_specimen_item.bio_specimen_item, row.dissection_type, row.dissection_barcode,
                # "DISSECTION_ID", "BIO_SPECIMEN_ITEM_ID", "DISSECTION_TYPE", "DISSECTION_BARCODE",
                row.created_by, row.created_date, None, None, row.rack,
                # "CREATED_BY", "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE", "RACK_ID",
                row.rack_position, row.bs_result, row.cwt_code, row.cwt_status, row.cwt_type, row.age,
                # "RACK_POSITION", "BS_RESULT", "CWT_CODE", "CWT_STATUS", "CWT_TYPE", "AGE",
                row.age_reader, row.age_date, row.age_location, row.age_method, row.band,
                ObserverDBUtil.get_data_source(),
                # "AGE_READER", "AGE_DATE", "AGE_LOCATION", "AGE_METHOD", "BAND_ID", "DATA_SOURCE",
                None, None
                # "ROW_PROCESSED", "ROW_STATUS"
            ]
            writer.writerow(row_values)
        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)
        return filename, csv_output

    # </editor-fold>

    # <editor-fold desc="Generate TRIP_CERTIFICATES">
    def generate_trip_certificates_csv(self, trip_id, user_id):
        """
        Generate CSV for upload.
        @param trip_id: trip ID
        @param user_id: uid
        @return: csv
        """

        table_name = 'TRIP_CERTIFICATES'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "TRIP_CERTIFICATE_ID", "TRIP_ID", "CERTIFICATE_NUMBER", "CREATED_DATE", "CREATED_BY",
            "MODIFIED_DATE", "MODIFIED_BY", "CERTIFICATION_ID", "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS"
        ]
        # Get certs
        certs_q = TripCertificates.select().where(TripCertificates.trip == trip_id)
        output = io.StringIO()

        if not len(certs_q):
            return filename, None

        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in certs_q:
            row_values = [
                row.trip_certificate, row.trip.trip, row.certificate_number, row.created_date, row.created_by,
                # "TRIP_CERTIFICATE_ID", "TRIP_ID", "CERTIFICATE_NUMBER", "CREATED_DATE", "CREATED_BY",
                None, None, row.certification, ObserverDBUtil.get_data_source(), None, None
                # "MODIFIED_DATE", "MODIFIED_BY", "CERTIFICATION_ID", "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS"
            ]
            writer.writerow(row_values)
        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)
        return filename, csv_output

    # </editor-fold>

    # <editor-fold desc="Generate FISH_TICKETS">
    def generate_fish_tickets_csv(self, trip_id, user_id):
        """
        Generate CSV for upload.
        @param trip_id: trip ID
        @param user_id: uid
        @return: csv
        """
        table_name = 'FISH_TICKETS'
        filename = ObserverSoap.get_filename(table_name, trip_id, user_id, arrow.now())
        required_headers = [
            "FISH_TICKET_ID", "FISH_TICKET_NUMBER", "CREATED_BY", "CREATED_DATE",
            "MODIFIED_BY", "MODIFIED_DATE", "TRIP_ID", "STATE_AGENCY", "FISH_TICKET_DATE",
            "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS"
        ]
        certs_q = FishTickets.select().where(FishTickets.trip == trip_id)
        output = io.StringIO()

        if not len(certs_q):
            return filename, None

        writer = csv.writer(output, lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(required_headers)  # Header

        for row in certs_q:
            row_values = [
                row.fish_ticket, row.fish_ticket_number, row.created_by, row.created_date,
                # "FISH_TICKET_ID", "FISH_TICKET_NUMBER", "CREATED_BY", "CREATED_DATE",
                None, None, row.trip.trip, row.state_agency, row.fish_ticket_date,
                # "MODIFIED_BY", "MODIFIED_DATE", "TRIP_ID", "STATE_AGENCY", "FISH_TICKET_DATE",
                ObserverDBUtil.get_data_source(), None, None
                # "DATA_SOURCE", "ROW_PROCESSED", "ROW_STATUS"
            ]
            writer.writerow(row_values)
        csv_output = output.getvalue()
        csv_output = self.make_csv_api_friendly(csv_output)
        return filename, csv_output
        # </editor-fold>
