# -----------------------------------------------------------------------------
# Name:        SyncDBDBWorker.py
# Purpose:     Sync Database in a thread
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Oct 4, 2017
# License:     MIT
# ------------------------------------------------------------------------------
import textwrap
from random import randint
from time import sleep

from enum import Enum

import logging
from PyQt5.QtCore import pyqtSignal, QObject, QThread

# Database models
from py.observer.ObserverDBBaseModel import database
from py.observer import ObserverDBBaseModel
from py.observer.ObserverDBModels import Trips, DbSync
from py.observer.ObserverDBUtil import ObserverDBUtil
from py.observer.ObserverSOAP import ObserverSoap


class DBSyncStatusEnum(Enum):
    SYNC_READY = 0
    TRIP_IN_PROGRESS = 1
    SYNC_ERROR = 2
    SYNC_COMPLETED = 3


class SyncDBWorker(QThread):
    """
    Run a thread to perform downloading of the database DDL and uploading of trip data
    Either pulls down only, or pushes to DB (upload_trips flag.)
    """
    pullComplete = pyqtSignal(bool, str, int)  # Success/Fail, Result Description, record count
    pushComplete = pyqtSignal(bool, str)  # Success/Fail, Result Description
    readyForPush = pyqtSignal()
    is_running = False
    new_trip_ids = []

    def __init__(self, *args, **kwargs):
        QThread.__init__(self, None)
        self.trip_ids = kwargs.get('trip_ids', None)
        self.upload_trips = kwargs.get('upload_trips', False)
        self.sync_controller = kwargs.get('sync_controller', None)
        self.send_push_signal = kwargs.get('send_push_signal', None)
        self.soap = kwargs.get('soap', False)
        self._logger = None
        SyncDBWorker.is_running = False

    def runSync(self, logger):
        self._logger = logger
        self.start()

    def run(self):

        if ObserverDBBaseModel.use_encrypted_database:
            ObserverDBBaseModel.activate_encryption(database)

        self._logger.info(f'Starting thread. upload_trips = {self.upload_trips}')
        if SyncDBWorker.is_running:
            raise RuntimeError("A run is in progress. Only one SyncDBWorker thread at a time.")

        SyncDBWorker.is_running = True
        try:
            sync_ok, sync_msg, records_updated = self.soap.update_client_pull()
            if not self.upload_trips:
                if self.send_push_signal and sync_ok:
                    self.readyForPush.emit()
                else:
                    self.pullComplete.emit(sync_ok, sync_msg, records_updated)
            else:
                push_ok, push_msg = self.perform_upload()
                self.pushComplete.emit(push_ok, push_msg)
        except Exception as e:
            #self.syncStatusChanged.emit(False, f'ERROR: {e}')
            self.pullComplete.emit(False, f'ERROR: {e}', 0)
        SyncDBWorker.is_running = False

        while True:
            # To prevent python crashing issue, need to wait to be terminated
            # as discovered by jstearns (see ObserverErrorReports.py)
            sleep(0.5)

    def perform_upload(self) -> (bool, str):
        if len(self.trip_ids) == 0:
            return True, 'No Trips to upload.'

        ok_trips = []
        bad_trips = []
        self.new_trip_ids = []
        success = True

        for t in self.trip_ids:
            try:
                new_trip_id = self.upload_trip(t)
                ok_trips.append(t)
                self.new_trip_ids.append(new_trip_id)
            except (Exception) as e:
                self._logger.error(e)
                bad_trips.append(str(e))
                success = False

        if len(self.new_trip_ids) > 1:
            status_msg = f'Successful uploads: (Trip, New ID): {ok_trips}, {self.new_trip_ids}'
        elif len(self.new_trip_ids) == 1:
            status_msg = f'Sync Successful. Trip ID assigned: {self.new_trip_ids[0]}'
        else:
            status_msg = 'Failed to upload. '
        if bad_trips:
            status_msg += f' Errors syncing: {bad_trips}'
        return success, textwrap.fill(status_msg, 40)

    def upload_trip(self, trip_id):
        """
        Assume currentSOAPUsername and currentSOAPPassword are set
        Throw Exception on error
        @param trip_id: trip to upload
        @return: new trip ID on success, else None
        """
        if not self.sync_controller.currentSOAPPassword or not self.sync_controller.currentSOAPUsername:
            raise Exception('Need to set currentSOAPPassword and currentSOAPUsername')

        user_id = ObserverDBUtil.get_current_user_id()
        self._logger.info('Uploading trip {}...'.format(trip_id))

        # FISHING_ACTIVITIES
        filename, csvdata = self.sync_controller.generate_fishing_activities_csv(trip_id=trip_id, user_id=user_id)
        self.perform_sync_operation(csvdata, filename, description='FISHING_ACTIVITIES')

        # FISHING_LOCATIONS
        filename, csvdata = self.sync_controller.generate_fishing_locations_csv(trip_id=trip_id, user_id=user_id)
        self.perform_sync_operation(csvdata, filename, description='FISHING_LOCATIONS')

        # FISH_TICKETS
        filename, csvdata = self.sync_controller.generate_fish_tickets_csv(trip_id=trip_id, user_id=user_id)
        self.perform_sync_operation(csvdata, filename, description='FISH_TICKETS')

        # TRIP_CERTIFICATES
        filename, csvdata = self.sync_controller.generate_trip_certificates_csv(trip_id=trip_id, user_id=user_id)
        self.perform_sync_operation(csvdata, filename, description='TRIP_CERTIFICATES')

        # CATCHES
        filename, csvdata = self.sync_controller.generate_catches_csv(trip_id=trip_id, user_id=user_id)
        self.perform_sync_operation(csvdata, filename, description='CATCHES')

        # SPECIES_COMPOSITIONS
        filename, csvdata = self.sync_controller.generate_speciescomp_csv(trip_id=trip_id, user_id=user_id)
        self.perform_sync_operation(csvdata, filename, description='SPECIES_COMPOSITIONS')

        # SPECIES_COMPOSITION_ITEMS
        filename, csvdata = self.sync_controller.generate_speciescomp_items_csv(trip_id=trip_id, user_id=user_id)
        self.perform_sync_operation(csvdata, filename, description='SPECIES_COMPOSITION_ITEMS')

        # SPECIES_COMPOSITION_BASKETS
        filename, csvdata = self.sync_controller.generate_speciescomp_baskets_csv(trip_id=trip_id, user_id=user_id)
        self.perform_sync_operation(csvdata, filename, description='SPECIES_COMPOSITION_BASKETS')

        # CATCH_ADDITIONAL_BASKETS
        filename, csvdata = self.sync_controller.generate_catch_additional_baskets_csv(trip_id=trip_id, user_id=user_id)
        self.perform_sync_operation(csvdata, filename, description='CATCH_ADDITIONAL_BASKETS')

        # BIOSPECIMENS
        filename, csvdata = self.sync_controller.generate_bio_specimens_csv(trip_id=trip_id, user_id=user_id)
        self.perform_sync_operation(csvdata, filename, description='BIOSPECIMENS')

        # BIOSPECIMEN_ITEMS
        filename, csvdata = self.sync_controller.generate_bio_specimen_items_csv(trip_id=trip_id, user_id=user_id)
        self.perform_sync_operation(csvdata, filename, description='BIOSPECIMEN_ITEMS')

        # DISSECTIONS
        filename, csvdata = self.sync_controller.generate_dissections_csv(trip_id=trip_id, user_id=user_id)
        self.perform_sync_operation(csvdata, filename, description='DISSECTIONS')

        # TRIPS - Triggers OBSPROD.EXTRACT_TRIPS_v2017 on DB
        new_trip_id = None
        filename, csvdata = self.sync_controller.generate_trips_csv(trip_id=trip_id, user_id=user_id)
        fake_failure = False  # For debugging - True to fake a failed Sync Upload, False for production
        if not fake_failure:
            uploaded_trip, new_trip_id = self.perform_sync_operation(csvdata, filename, description='TRIPS')
            self._logger.info(f'New TRIP ID: {new_trip_id}')
            self._store_external_trip_id(local_trip_id=trip_id, external_trip_id=new_trip_id)
        else:
            uploaded_trip = False
            self._logger.error('Faked sync TRIPS failure for testing.')

        if uploaded_trip:
            self._logger.info('Trip {} upload success.'.format(trip_id))
            self._mark_trip_sync_complete(trip_id)
        else:
            # TODO more error handling, mark trip as error state
            err_msg = 'Unspecified trip {} sync error'.format(trip_id)
            self._logger.error(err_msg)
            self._mark_trip_sync_error(trip_id)
            raise Exception(err_msg)

        return new_trip_id

    def _mark_trip_sync_complete(self, trip_id):
        self._logger.info('Marking Trip {} as completed sync.'.format(trip_id))
        try:
            trip_q = DbSync.get(DbSync.trip == trip_id)
            trip_q.status = DBSyncStatusEnum.SYNC_COMPLETED.value
            trip_q.save()
            self.sync_controller.update_db_sync_table()
        except DbSync.DoesNotExist:
            if trip_id:
                self._logger.error('Could not find trip {}'.format(trip_id))

    def _mark_trip_sync_error(self, trip_id):
        self._logger.info('Marking Trip {} in error state for sync.'.format(trip_id))
        try:
            trip_q = DbSync.get(DbSync.trip == trip_id)
            trip_q.status = DBSyncStatusEnum.SYNC_ERROR.value
            trip_q.save()
            self.sync_controller.update_db_sync_table()
        except DbSync.DoesNotExist:
            if trip_id:
                self._logger.error('Could not find trip {}'.format(trip_id))

    def _store_external_trip_id(self, local_trip_id, external_trip_id):
        if not local_trip_id or not external_trip_id:
            self._logger.error(f'Invalid Local {local_trip_id} or External trip {external_trip_id} passed')
        try:
            trip_q = Trips.get(Trips.trip == local_trip_id)
            trip_q.external_trip = external_trip_id
            trip_q.save()
            self._logger.debug(f'Saved local trip ID {local_trip_id} as external trip ID {external_trip_id}')
        except Trips.DoesNotExist as e:
            self._logger.error(f'Bad {local_trip_id} passed: {e}')

    def perform_sync_operation(self, csvdata, filename, description):
        if not csvdata:
            self._logger.info('No data for {} ({}), skipping.'.format(filename, description))
            return True, None
        unenc_data = csvdata.encode('utf-8')
        soapusername = self.sync_controller.currentSOAPUsername
        hashed_pw = self.sync_controller.currentSOAPPassword

        simulation_debug_mode = False  # True for testing, False for production
        if simulation_debug_mode:
            self._logger.error('SYNC DISABLED FOR TEST: {}'.format(filename))
            self._logger.debug(unenc_data)
            sleep(1)
            return True, randint(666000, 666999)  # fake trip id for testing
        else:
            try:
                updated, new_trip_id = self.soap.action_upload(username=soapusername,
                                                               hashed_pw=hashed_pw,
                                                               filename=filename,
                                                               unenc_data=unenc_data)
            except Exception as e:
                updated = False
                description = description + ': ' + str(e)
        if not updated:
            raise Exception('Error syncing {}'.format(description))
        else:
            return updated, new_trip_id
