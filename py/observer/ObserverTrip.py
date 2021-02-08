# -----------------------------------------------------------------------------
# Name:        ObserverTrip.py
# Purpose:     Trip object, exposed to QML, contains TripsModel
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     March 14, 2016
# License:     MIT
# ------------------------------------------------------------------------------

import unittest
import logging

from PyQt5.QtCore import pyqtProperty, QObject, QVariant, pyqtSignal, pyqtSlot

from playhouse.apsw_ext import APSWDatabase
from playhouse.test_utils import test_database

# http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#model_to_dict
# For converting peewee models to dict, and then to QVariant for QML, and all the way back again
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError

from py.observer.ObserverDBModels import Trips, Vessels, Settings, Users, Programs, \
    Contacts, Ports, FishTickets, TripCertificates, IfqDealers, FishingActivities, Lookups
from py.observer.ObserverDBSyncController import ObserverDBSyncController
from py.observer.ObserverTripsModel import TripsModel
from py.observer.FishTicketsModel import FishTicketsModel
from py.observer.TripCertsModel import TripCertsModel
from py.observer.ObserverDBUtil import ObserverDBUtil
from py.observer.HookCountsModel import HookCountsModel


class ObserverTrip(QObject):
    tripsChanged = pyqtSignal(name='tripsChanged')
    fishTicketsChanged = pyqtSignal(name='fishTicketsChanged')
    hookCountsChanged = pyqtSignal(name='hookCountsChanged')
    tripCertsChanged = pyqtSignal(name='tripCertsChanged')
    tripIdChanged = pyqtSignal(str, name='tripIdChanged')
    observerChanged = pyqtSignal(QVariant, name='observerChanged')
    debrieferModeChanged = pyqtSignal(bool, name='debrieferModeChanged')
    currentVesselNameChanged = pyqtSignal(str, name='currentVesselNameChanged')
    tripDataChanged = pyqtSignal()  # catch-all

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)

        self._trips_model = TripsModel()
        self._tickets_model = FishTicketsModel()
        self._hook_counts_model = HookCountsModel()
        self._certs_model = TripCertsModel()

        self._current_trip_model_idx = None

        self._tmp_fishticketnum = None
        self._tmp_fishticketstate = None
        self._tmp_fishticketdate = None

        self._enable_debriefer_mode = False

        if self._load_trips() == 0:
            self._logger.info('No trips loaded (likely first run.)')

        self._current_trip = None
        self.tripsChanged.connect(self._load_trips)

    @pyqtSlot(bool, name='setDebrieferMode')
    def set_debriefer_mode(self, is_set):
        self._enable_debriefer_mode = is_set
        # Make available to other python modules via Settings table:
        ObserverDBUtil.set_current_debriefer_mode(is_set)
        self._logger.info(f'Debriefer mode: {self._enable_debriefer_mode}')
        self.debrieferModeChanged.emit(is_set)

    @staticmethod
    def isTrainingMode():
        """
        @return: True if training mode
        """
        mode = ObserverDBUtil.get_setting('training')
        return True if mode == 'TRUE' else False

    @pyqtProperty(bool, notify=debrieferModeChanged)
    def debrieferMode(self):
        return self._enable_debriefer_mode

    @staticmethod
    def get_user_valid_trips(debriefer_mode: bool=False):
        """
        Return peewee query for current user, program, non-synced trips
        @param debriefer_mode: load all trips, independent of user
        @return:
        """
        completed_trip_ids = ObserverDBSyncController.get_completed_trip_ids()
        current_user_id = ObserverDBUtil.get_current_user_id()
        program_id = ObserverDBUtil.get_current_program_id()
        is_fixed_gear = ObserverTrip.get_fg_value()

        if debriefer_mode or ObserverTrip.isTrainingMode():
            logging.info('Debriefer mode set, loading ALL trips.')
            trips_query = Trips.select().where((Trips.is_fg_trip_local == is_fixed_gear))
        else:

            trips_query = Trips.select().where((Trips.trip.not_in(completed_trip_ids)) &
                                               (Trips.user == current_user_id) &
                                               (Trips.program == program_id) &
                                               (Trips.is_fg_trip_local == is_fixed_gear))
        return trips_query

    @staticmethod
    def get_user_valid_trip_ids():
        """
        Return a list of trip ID's () for current user, program, non-synced trips
        @return: list of ints e.g. [1,2,3], or None
        """
        trips_query = ObserverTrip.get_user_valid_trips()
        if trips_query.count():
            return [trip.trip for trip in trips_query]

    @pyqtSlot(name='reloadTrips')
    def _load_trips(self):
        """
        Load trips from database
        :return:
        """
        trips_query = self.get_user_valid_trips(self._enable_debriefer_mode)

        self._trips_model.clear()
        ntrips = trips_query.count()
        if ntrips > 0:
            for trip in trips_query:
                self._current_trip_model_idx = self._trips_model.add_trip(trip)

        accessible_trip_ids = [trip.trip for trip in trips_query]
        current_trip_id = ObserverDBUtil.get_setting('trip_number')
        if current_trip_id:
            if int(current_trip_id) not in accessible_trip_ids:
                # User changed (username or role) so clear current trip ID
                ObserverDBUtil.clear_setting('trip_number')
                self.tripId = None

        self._logger.debug(f'Loaded {ntrips} active (not yet synced) trip(s)')
        return ntrips

    def add_trip(self, trip):
        """
        Adds peewee model trip to the FramListModel and sets properties
        :param trip:
        """
        self._current_trip_model_idx = self._trips_model.add_trip(trip)
        self.tripId = trip.trip

    def create_trip(self, vessel_id, observer_id, program_id):
        """
        Create a new trip in the DB
        @param vessel_id: ID of vessel
        @param observer_id: ID of user
        @param program_id: ID of program
        @return: new trip cursor (peewee)
        """
        try:
            is_fixed_gear = ObserverTrip.get_fg_value()
            newtrip = Trips.create(
                user=observer_id,
                vessel=vessel_id,
                program=program_id,
                partial_trip='F',
                trip_status='FALSE',
                created_by=observer_id,
                created_date=ObserverDBUtil.get_arrow_datestr(),
                is_fg_trip_local=is_fixed_gear,
                data_source=ObserverDBUtil.get_data_source()  # FIELD-2099: setting data source initially
            )

            self.add_trip(newtrip)
            return newtrip
        except Exception as e:
            self._logger.error(e)
            return None

    @staticmethod
    def get_fg_value():
        # For IS_FG_TRIP_LOCAL
        return 1 if ObserverDBUtil.is_fixed_gear() else None

    def end_trip(self):
        """
        End current trip - TODO: other DB lock function to lock trip(TODO)
        :return:
        """
        self._logger.info("User ended trip # {}".format(self.tripId))
        self._current_trip = None
        self._certs_model.clear()  # FIELD-2084: prevent permit to carry to next trip
        self.tripsChanged.emit()
        self.tripIdChanged.emit('')
        self.currentVesselNameChanged.emit('')
        # remove current trip ID setting from DB
        try:
            tripnum = Settings.get(Settings.parameter == 'trip_number')
            tripnum.delete_instance()
        except Settings.DoesNotExist as e:
            self._logger.error('Could not delete trip_number setting: {}'.format(e))

    @pyqtProperty(QVariant, notify=tripsChanged)
    def TripsModel(self):
        self._trips_model.sort_reverse('trip')
        return self._trips_model


    @pyqtProperty(QVariant, notify=hookCountsChanged)
    def HookCountsModel(self):
        return self._hook_counts_model

    @pyqtProperty(QVariant, notify=fishTicketsChanged)
    def FishTicketsModel(self):
        return self._tickets_model

    @pyqtProperty(QVariant, notify=tripCertsChanged)
    def TripCertsModel(self):
        return self._certs_model

    @property
    def current_trip_db_id(self):
        if self._current_trip is not None:
            return self._current_trip.trip
        else:
            return None

    @pyqtProperty(str, notify=tripIdChanged)
    def tripId(self):
        if self._current_trip is not None:
            return str(self._current_trip.trip)
        else:
            return ""

    @tripId.setter
    def tripId(self, value):
        # select matching trip ID and set current trip id PK
        # does NOT change trip number in the DB
        if value is None or value == '':
            self.clear_trip_id()
            return
        try:
            current_user_id = ObserverDBUtil.get_current_user_id()
            trip_q = Trips.get((int(value) == Trips.trip) &
                               (Trips.user == current_user_id))
            self._current_trip = trip_q
            self._current_trip_model_idx = self._trips_model.get_item_index('trip', int(value))
            self._logger.info('Selected trip #{}'.format(self._current_trip.trip))
            self.tripIdChanged.emit(str(value))
            ObserverDBUtil.db_save_setting('trip_number', self._current_trip.trip)
            ObserverDBUtil.set_current_fishery_id(self._current_trip.fishery)
            if self._current_trip.vessel is not None:
                self.currentVesselNameChanged.emit(self._current_trip.vessel.vessel_name)
                self.tripsChanged.emit()

            # Load corresponding tickets
            self._tickets_model.clear()
            tickets_query = FishTickets.select().where(FishTickets.trip == trip_q.trip)
            ntickets = tickets_query.count()
            if ntickets > 0:
                for ticket in tickets_query:
                    self._tickets_model.add_ticket(ticket)

            # Load corresponding trip certificates
            self._certs_model.clear()
            certs_query = TripCertificates.select().where(TripCertificates.trip == trip_q.trip)
            ncerts = certs_query.count()
            if ncerts > 0:
                for cert in certs_query:
                    self._certs_model.add_cert(cert)

        except ValueError as e:
            self._logger.error('Error with Trip ID specified: {}, {}'.format(value, e))
            self.clear_trip_id()
        except Trips.DoesNotExist as e:
            self._logger.error('Trip ID does not exist for this user: {}, {}'.format(value, e))
            self.clear_trip_id()
        except Vessels.DoesNotExist as e:
            self._logger.error(f'Vessel ID not set... {e}')
            self.clear_trip_id()

    def clear_trip_id(self):
        self._current_trip = None
        self._current_trip_model_idx = None
        self._tickets_model.clear()
        self._certs_model.clear()
        self._logger.info('Cleared current Trip ID.')

    @pyqtProperty(QVariant, notify=tripsChanged)
    def currentTrip(self):
        # convert peewee model to dict, pass as QVariant
        if self._current_trip is not None:
            return model_to_dict(self._current_trip)
        else:
            return None

    @currentTrip.setter
    def currentTrip(self, data):
        """
        Convert QJSValue->QVariant->dict to peewee model
        :param data: QJSValue passed from QML
        """
        # Used by save_fields() in EndTripScreen
        try:
            data_dict = self._translate_dict_vessel_name(data.toVariant())
            # Save to DB. Handle the case where save fails because observer hasn't yet specified vessel.
            self._current_trip = dict_to_model(Trips, data_dict)
            try:
                if self._current_trip.vessel is not None:
                    self._current_trip.save()
                    self._logger.debug('currentTrip ({}) data assigned'.format(self._current_trip.trip))
                    self.currentVesselNameChanged.emit(self._current_trip.vessel.vessel_name)
                else:
                    self._logger.error(f'currentTrip ({self._current_trip.trip}) NOT saved: Vessel ID cannot be null.')
            except IntegrityError:
                self._logger.error(f'currentTrip ({self._current_trip.trip}) NOT saved: Vessel ID cannot be null.')
            except Vessels.DoesNotExist as e:
                self._logger.error(f'{e}')
        except AttributeError as e:
            self._logger.error('Expected QJSValue, got something else. ' + str(e))

    def load_current_trip(self, trip_id):
        """
        Given trip id, load self.currentTrip
        @param trip_id:
        @return:
        """
        try:
            self._current_trip = Trips.get(Trips.trip == trip_id)
        except Trips.DoesNotExist as e:
            self._current_trip = None
            self._logger.error(e)

    @pyqtSlot(QVariant, result=bool, name='checkTripEmpty')
    def check_trip_empty(self, trip_id):
        """
        Queries DB to see if there are data records associated with a trip
        @param trip_id: DBID
        @return: True if trip is empty and can be deleted, False otherwise
        """

        if not trip_id:
            self._logger.warning('Invalid trip ID passed to check_trip_empty.')
            return False

        hauls_q = FishingActivities.select().where(FishingActivities.trip == trip_id)
        if len(hauls_q) > 0:
            self._logger.info('Trip {} is not empty, has {} hauls associated.'.format(trip_id, len(hauls_q)))
            return False

        self._logger.info(f'Trip {trip_id} appears empty.')
        return True

    @pyqtSlot(QVariant, result=bool, name='deleteTrip')
    def delete_trip(self, trip_id):
        """
        Deletes a trip if empty
        @param trip_id: DBID
        @return: True if trip deleted, false otherwise
        """
        # double check empty
        if not self.check_trip_empty(trip_id):
            return False
        self._logger.info('Deleting empty trip {}'.format(trip_id))

        # Delete from DB
        trip = Trips.get(Trips.trip == trip_id)
        ObserverDBUtil.log_peewee_model_instance(self._logger, trip, 'Deleting trip')
        trip.delete_instance(recursive=True)

        # Delete from model
        model_idx = self._trips_model.get_item_index('trip', trip_id)
        if model_idx >= 0:
            self._trips_model.remove(model_idx)
        else:
            self._logger.error('Unable to find and remove trip {} from model.'.format(trip_id))
        return True

    def _translate_dict_vessel_name(self, dict):
        """
        Lookup up vessel FK by vessel_name, store vessel dict
        """
        # Remove vessel_name key
        try:
            vessel_name = dict.pop('vessel_name')
            vessel_id = dict['vessel']['vessel']
            vessel = Vessels.get(Vessels.vessel == vessel_id)
            dict['vessel'] = model_to_dict(vessel)
        except Vessels.DoesNotExist as e:
            self._logger.error(str(e))
        except TypeError as e:
            self._logger.error(str(e))

        return dict

    def _get_vessel_FK(self, vessel_name, registration_code):
        """
        Lookup up vessel FK by vessel_name and registration_code
        """
        try:
            return Vessels.get((fn.Lower(Vessels.vessel_name) % fn.Lower(vessel_name)) &
                               ((Vessels.state_reg_number == registration_code) |
                                (Vessels.coast_guard_number == registration_code)))
        except Vessels.DoesNotExist as e:
            self._logger.error(str(e))
            return None

    def _get_fishery_ID(self, fishery_name):
        """
        Lookup up fishery ID by fishery_name
        """
        try:
            return Lookups.get((Lookups.lookup_type == 'FISHERY') &
                               (Lookups.description == fishery_name)).lookup_value
        except Lookups.DoesNotExist as e:
            self._logger.error(str(e))
        return None

    def _get_skipper_FK(self, skipper_name):
        """
        Lookup up contacts FK by skipper_name
        """
        try:
            # FIELD-1509 this breaks when app is frozen. Just building a dict instead. [didn't work quite right.]
            # FIELD-1882 issue with multiple first names
            # FIELD-1882 rewritten to search all names, but will only return first match.
            skippers = {}
            contacts_q = Contacts.select().where(Contacts.first_name.is_null(False))

            for c in contacts_q:
                if (c.first_name + ' ' + c.last_name) == skipper_name:
                    return c.contact
            return None
        except Exception as e:
            self._logger.error('_get_skipper_FK: ' + str(e))
        return None

    def _get_port_name_FK(self, port_name):
        """
        Lookup up contacts FK by port_name
        """
        try:
            return Ports.get(fn.Lower(Ports.port_name) % fn.Lower(port_name))
        except Ports.DoesNotExist as e:
            self._logger.error(str(e))
        return None

    def _set_cur_prop(self, property, value):
        """
        Helper function - set current trip properties in FramListModel
        @param property: property name
        @param value: value to store
        @return:
        """
        if not self._current_trip_model_idx:
            return
        self._trips_model.setProperty(self._current_trip_model_idx,
                                      property, value)

    @pyqtSlot()
    def addFishTicket(self):
        if self.fishTicketNum is None or self.fishTicketDate is None or self.fishTicketState is None:
            return

        user_id = ObserverDBUtil.get_current_user_id()
        created_date = ObserverDBUtil.get_arrow_datestr()
        fish_ticket_number = FishTickets.create(fish_ticket_number=self.fishTicketNum,
                                                fish_ticket_date=self.fishTicketDate,
                                                state_agency=self.fishTicketState,
                                                trip=self._current_trip.trip,
                                                created_by=user_id,
                                                created_date=created_date)
        self._tickets_model.add_ticket(fish_ticket_number)
        self.fishTicketDate = None
        self.fishTicketNum = None
        # Leave State alone

    @pyqtSlot(str)
    def delFishTicket(self, ticket_num):
        if not ticket_num:
            return
        self._logger.info('Deleting ticket #{}'.format(ticket_num))
        doomed_ticket = FishTickets.get(FishTickets.fish_ticket_number == ticket_num,
                                        FishTickets.trip == self._current_trip.trip)
        doomed_ticket.delete_instance()
        self._tickets_model.del_ticket(ticket_num)

    @pyqtProperty(str, notify=tripDataChanged)
    def fishTicketNum(self):
        return self._tmp_fishticketnum

    @fishTicketNum.setter
    def fishTicketNum(self, ticket_num):
        """
        Accepts alpha also
        @param ticket_num: digits and values
        """
        # self._logger.info('Set fish ticket num {}'.format(ticket_num))
        self._tmp_fishticketnum = ticket_num

    @pyqtProperty(str, notify=tripDataChanged)
    def fishTicketDate(self):
        return self._tmp_fishticketdate

    @fishTicketDate.setter
    def fishTicketDate(self, ticket_date):
        """
        Accepts alpha also
        @param ticket_date: plain format date
        """
        # self._logger.info('Set fish ticket date {}'.format(ticket_date))
        self._tmp_fishticketdate = ticket_date

    @pyqtProperty(str, notify=tripDataChanged)
    def fishTicketState(self):
        return self._tmp_fishticketstate

    @fishTicketState.setter
    def fishTicketState(self, ticket_state):
        """
        Accepts alpha also
        @param ticket_state: single alpha
        """
        # self._logger.info('Set fish ticket state {}'.format(ticket_state))
        self._tmp_fishticketstate = ticket_state

    @pyqtSlot(str)
    def addTripCert(self, cert_num):
        """
        Add Trip Certificate (Permit / License #)
        @param cert_num: trip or license number
        """
        # TODO certification_id?
        if self._current_trip is not None:
            user_id = ObserverDBUtil.get_current_user_id()
            created_date = ObserverDBUtil.get_arrow_datestr()
            cert = TripCertificates.create(certificate_number=cert_num, trip=self._current_trip.trip,
                                           created_by=user_id, created_date=created_date)
            self._certs_model.add_cert(cert)

    @pyqtSlot(str)
    def delTripCert(self, cert_num):
        if not cert_num:
            return
        self._logger.info('Deleting cert #{}'.format(cert_num))
        doomed_cert = TripCertificates.get(TripCertificates.certificate_number == cert_num,
                                           TripCertificates.trip == self._current_trip.trip)
        doomed_cert.delete_instance()
        self._certs_model.del_cert(cert_num)

    @pyqtProperty(str, notify=currentVesselNameChanged)
    def currentVesselName(self):
        """
        Note: currentVesselNameChanged signal emitted when tripId is set or model set
        :return:
        """
        try:
            if self._current_trip is not None and self._current_trip.vessel is not None:
                return self._current_trip.vessel.vessel_name
        except AttributeError:
            pass
        except Vessels.DoesNotExist:
            pass
        return ''

    @pyqtSlot(str, name='setVesselNameUSCG')
    def set_vessel_name_uscg(self, name_and_uscg):
        """
        Set current vessel. Expects both a name and a USCG #
        @param name_and_uscg: Format "{name} - {uscg}"
        """
        separator_loc = name_and_uscg.find(' - ')
        if separator_loc > 0:
            vessel_name = name_and_uscg[:separator_loc]
            registration_code = name_and_uscg[separator_loc + 3:]
            self._logger.debug(f'Setting current vessel name {vessel_name}, reg # {registration_code}')
            if self._current_trip is not None:
                try:
                    # Look up by coast guard/ state reg #
                    vessel_fk = self._get_vessel_FK(vessel_name, registration_code)
                    self._current_trip.vessel = vessel_fk
                    self._current_trip.save()
                    self._set_cur_prop('vessel_name', vessel_name)
                    self._set_cur_prop('vessel_id', vessel_fk)
                    self.currentVesselNameChanged.emit(vessel_name)
                except Exception as e:
                    self._logger.warning(e)

    @pyqtProperty(str, notify=observerChanged)
    def observer(self):
        if self._current_trip is not None:
            try:
                return self._current_trip.observer
            except AttributeError:
                pass
        return ''

    @pyqtProperty(str, notify=tripDataChanged)
    def currentFisheryName(self):
        """
        Note: tripDataChanged signal emitted when data is set
        :return:
        """
        if self._current_trip is not None and self._current_trip.fishery is not None:
            try:
                return self._get_fishery_by_ID(self._current_trip.fishery)
            except AttributeError:
                pass
        return ''

    @pyqtProperty(bool, notify=tripDataChanged)
    def allowFisheryChange(self):
        trip_id = self._current_trip.trip if self._current_trip else None
        if trip_id and not self.check_trip_empty(trip_id):
            return False
        return True

    @pyqtProperty(bool, notify=tripDataChanged)
    def allowAvgHookCountChange(self):
        # TODO: Always Allow hook count change, but need to cascade changes down to all sets
        # trip_id = self._current_trip.trip if self._current_trip else None
        # if trip_id and not self.check_trip_empty(trip_id):
        #     return False
        return True

    @staticmethod
    def _get_fishery_by_ID(fishery_id):
        try:
            return Lookups.get((Lookups.lookup_type == 'FISHERY') &
                               (Lookups.lookup_value == fishery_id)).description
        except Lookups.DoesNotExist as e:
            logging.error(e)

    @currentFisheryName.setter
    def currentFisheryName(self, fishery_name):
        """
        :param fishery_name: fishery name str
        """
        if self._current_trip is not None:
            fishery_id = self._get_fishery_ID(fishery_name)
            self._current_trip.fishery = fishery_id
            self._current_trip.save()
            self._set_cur_prop('fishery', fishery_name)
            ObserverDBUtil.set_current_fishery_id(fishery_id)
            self.tripDataChanged.emit()

    @pyqtProperty(bool, notify=tripDataChanged)
    def isShrimpFishery(self):
        """
        if fishery is 8 (CA Ridgeback), 9 (CA Pink Shrimp),
        13 (OR Pink Shrimp), or 18 (WA Pink Shrimp), return true
        """
        if self._current_trip is not None:
            return self._current_trip.fishery in ['8', '9', '13', '18']

    @pyqtProperty(str, notify=tripDataChanged)
    def currentSkipperName(self):
        """
        Note: tripDataChanged signal emitted when data is set
        :return:
        """

        if self._current_trip is not None and self._current_trip.skipper is not None:
            try:
                return self._current_trip.skipper.first_name + ' ' + \
                       self._current_trip.skipper.last_name
            except AttributeError:
                pass
            except TypeError:  # empty skipper name
                pass
        return ''

    @currentSkipperName.setter
    def currentSkipperName(self, skipper_name):
        """
        :param skipper_name: skipper name str
        """
        if self._current_trip is not None:
            skipper_fk = self._get_skipper_FK(skipper_name)
            self._current_trip.skipper = skipper_fk
            self._current_trip.save()
            self._set_cur_prop('skipper_name', skipper_name)
            self.tripDataChanged.emit()

    @pyqtProperty(str, notify=tripDataChanged)
    def currentStartPortName(self):
        """
        Note: tripDataChanged signal emitted when data is set
        :return:
        """
        if self._current_trip is not None and self._current_trip.departure_port is not None:
            try:
                return self._current_trip.departure_port.port_name.title()
            except AttributeError:
                pass
        return ''

    @currentStartPortName.setter
    def currentStartPortName(self, port_name):
        """
        :param port_name: port name str
        """
        if self._current_trip is not None:
            port_fk = self._get_port_name_FK(port_name)
            self._current_trip.departure_port = port_fk
            self._current_trip.save()
            self._set_cur_prop('departure_port', port_name)
            self.tripDataChanged.emit()

    @pyqtProperty(str, notify=tripDataChanged)
    def currentEndPortName(self):
        """
        Note: tripDataChanged signal emitted when data is set
        :return:
        """
        if self._current_trip is not None and self._current_trip.return_port is not None:
            try:
                return self._current_trip.return_port.port_name.title()
            except AttributeError:
                pass

        return ''

    @currentEndPortName.setter
    def currentEndPortName(self, port_name):
        """
        :param port_name: port name str
        """
        if self._current_trip is not None:
            port_fk = self._get_port_name_FK(port_name)
            self._current_trip.return_port = port_fk
            self._current_trip.save()
            self._set_cur_prop('return_port', port_name)
            self.tripDataChanged.emit()

    @pyqtProperty(str, notify=tripDataChanged)
    def currentStartDateTime(self):
        """
        Note: tripDataChanged signal emitted when data is set
        :return:
        """
        if self._current_trip is not None:
            try:
                return ObserverDBUtil.convert_arrow_to_jscript_datetime(self._current_trip.departure_date)
            except AttributeError:
                pass
        else:
            return ''

    @currentStartDateTime.setter
    def currentStartDateTime(self, date_time):
        """
        :param date_time: start date ISO str
        """
        if self._current_trip is not None:
            date_time = ObserverDBUtil.convert_jscript_datetime(date_time)
            self._current_trip.departure_date = date_time
            self._current_trip.save()
            self._set_cur_prop('departure_date', date_time)
            self.tripDataChanged.emit()

    @pyqtProperty(str, notify=tripDataChanged)
    def currentEndDateTime(self):
        """
        Note: tripDataChanged signal emitted when data is set
        :return:
        """
        if self._current_trip is not None:
            try:
                return ObserverDBUtil.convert_arrow_to_jscript_datetime(self._current_trip.return_date)
            except AttributeError:
                pass
        return ''

    @currentEndDateTime.setter
    def currentEndDateTime(self, date_time):
        """
        :param date_time: end date ISO str
        """
        date_time = ObserverDBUtil.convert_jscript_datetime(date_time)
        self._current_trip.return_date = date_time
        self._current_trip.save()
        self._set_cur_prop('return_date', date_time)
        self.tripDataChanged.emit()

    @pyqtProperty(str, notify=tripDataChanged)
    def currentCrewCount(self):
        """
        Note: tripDataChanged signal emitted when data is set
        :return:
        """
        if self._current_trip is not None and self._current_trip.crew_size is not None:
            try:
                return str(self._current_trip.crew_size)
            except AttributeError:
                pass
        return ''

    @currentCrewCount.setter
    def currentCrewCount(self, crew_size):
        """
        :param crew_count: crew count
        """
        try:
            self._current_trip.crew_size = int(crew_size)
            self._current_trip.save()
            self._set_cur_prop('crew_size', crew_size)
            self.tripDataChanged.emit()
        except TypeError as e:
            self._logger.error('Cannot set crew count to {}, {}'.format(crew_size, e))
        except ValueError as e:
            self._logger.warning('Ignore invalid input {}, {}'.format(crew_size, e))

    @pyqtProperty(str, notify=tripDataChanged)
    def currentLogbookNum(self):
        """
        Note: tripDataChanged signal emitted when data is set
        :return:
        """
        if self._current_trip is not None and self._current_trip.observer_logbook is not None:
            try:
                return str(self._current_trip.observer_logbook)
            except AttributeError:
                pass
        return ''

    @currentLogbookNum.setter
    def currentLogbookNum(self, observer_logbook):
        """
        :param obs_logbook: logbook #
        """
        try:
            self._current_trip.observer_logbook = int(observer_logbook)
            self._current_trip.save()
            self._set_cur_prop('observer_logbook', observer_logbook)
            self.tripDataChanged.emit()
        except TypeError as e:
            self._logger.error('Cant set logbook # to {}, {}'.format(observer_logbook, e))
        except ValueError as e:
            self._logger.warning('Ignore invalid input {}, {}'.format(observer_logbook, e))

    @pyqtProperty(str, notify=tripDataChanged)
    def currentPermitNum(self):
        """
        Note: tripDataChanged signal emitted when data is set
        :return:
        """
        if self._current_trip is not None and self._current_trip.permit_num is not None:
            try:
                return str(self._current_trip.permit_num)
            except AttributeError:
                pass
        return ''

    @currentPermitNum.setter
    def currentPermitNum(self, permit_num):
        """
        :param permit_num: logbook # - maybe has alpha chars ?
        """
        self._current_trip.permit_num = permit_num
        self._current_trip.save()
        self._set_cur_prop('permit_num', permit_num)
        self.tripDataChanged.emit()

    def _query_first_receiver_join_ports(self, first_receiver_id=None):

        if not first_receiver_id:
            return IfqDealers. \
                select(IfqDealers, Ports). \
                join(Ports, on=(IfqDealers.port_code == Ports.ifq_port_code).alias('port')). \
                where(IfqDealers.active == 1)
        else:
            return IfqDealers. \
                select(IfqDealers, Ports). \
                join(Ports, on=(IfqDealers.port_code == Ports.ifq_port_code).alias('port')). \
                where(IfqDealers.ifq_dealer == first_receiver_id)

    @pyqtProperty(str, notify=tripDataChanged)
    def firstReceiver(self):
        """
        Note: tripDataChanged signal emitted when data is set
        :return:
        """
        if self._current_trip is not None and self._current_trip.first_receiver is not None:
            fr_q = self._query_first_receiver_join_ports(first_receiver_id=self._current_trip.first_receiver)
            for fr in fr_q:
                return '{} {}'.format(fr.dealer_name, fr.port.port_name)  # return first entry

        return ''

    @firstReceiver.setter
    def firstReceiver(self, first_receiver_text):
        """
        :param first_receiver_text: this is text created in the db for autocomplete
        """
        # re-query for the same string
        # TODO refactor this, duplicated in ObserverData

        fr_q = self._query_first_receiver_join_ports()
        id_lookup = None
        fr_line = None
        for fr in fr_q:
            fr_line = '{} {}'.format(fr.dealer_name, fr.port.port_name)
            if first_receiver_text == fr_line:
                id_lookup = fr.ifq_dealer
                break

        if id_lookup:
            self._current_trip.first_receiver = id_lookup
            self._current_trip.save()
            self._set_cur_prop('first_receiver', fr_line)
            self.tripDataChanged.emit()

    @pyqtProperty(QVariant, notify=tripDataChanged)
    def currentAvgHookCount(self):
        """
        Note: tripDataChanged signal emitted when data is set
        :return:
        """
        if self._current_trip is not None:
            if self._current_trip.total_hooks_kp is not None:
                try:
                    return float(self._current_trip.total_hooks_kp)
                except AttributeError:
                    pass
            return 1.0
        else:
            return None

    @currentAvgHookCount.setter
    def currentAvgHookCount(self, hook_count):
        """
        :param hook_count: hook count, sets to 1 (instead of 0)
        """
        try:
            if float(hook_count) == 0:
                hook_count = 1.0
            self._current_trip.total_hooks_kp = float(hook_count)
            self._current_trip.save()
            self._set_cur_prop('total_hooks_kp', hook_count)
            self.tripDataChanged.emit()
        except TypeError as e:
            self._logger.error('Cannot set hook count to {}, {}'.format(hook_count, e))
        except ValueError as e:
            self._logger.warning('Ignore invalid input {}, {}'.format(hook_count, e))

    @pyqtSlot(str, result='QVariant')
    def getData(self, data_name):
        """
        Shortcut to get data from the DB that doesn't deserve its own property
        (Note, tried to use a dict to simplify this, but DB cursors were not updating)
        :return: Value found in DB
        """
        if self._current_trip is None:
            self._logger.warning('Attempt to get data with null current trip.')
            return None
        data_name = data_name.lower()
        if data_name == 'partial_trip':
            return True if self._current_trip.partial_trip == 'T' else False
        elif data_name == 'fishing_days_count':
            return self._current_trip.fishing_days_count
        elif data_name == 'logbook_type':
            try:
                logbook_value = self._current_trip.logbook_type
                logbook_desc = Lookups.get((Lookups.lookup_type == 'VESSEL_LOGBOOK_NAME') &
                                           (Lookups.lookup_value == logbook_value)).description
                return logbook_desc
            except Lookups.DoesNotExist:
                return None
        elif data_name == 'logbook_number':
            return self._current_trip.logbook_number
        elif data_name == 'fish_processed':
            return self._current_trip.fish_processed
        elif data_name == 'notes':
            return self._current_trip.notes
        else:
            self._logger.warning('Attempt to get unknown data name: {}'.format(data_name))
            return None

    @pyqtSlot(str, QVariant)
    def setData(self, data_name, data_val):
        """
        Set misc data to the DB - should do this for all properties instead of individual pyqtSlots...
        :return:
        """
        if self._current_trip is None:
            self._logger.warning('Attempt to set data with null current trip.')
            return

        data_name = data_name.lower()
        if data_name == 'partial_trip':
            self._current_trip.partial_trip = 'T' if data_val else 'F'
        elif data_name == 'fishing_days_count':
            self._current_trip.fishing_days_count = int(data_val) if data_val else None
        elif data_name == 'logbook_type':
            logbook_value = Lookups.get((Lookups.lookup_type == 'VESSEL_LOGBOOK_NAME') &
                                        (Lookups.description == data_val)).lookup_value
            self._current_trip.logbook_type = logbook_value
            # data_val = logbook_value
        elif data_name == 'logbook_number':
            self._current_trip.logbook_number = data_val
        elif data_name == 'fish_processed':
            self._current_trip.fish_processed = data_val
        elif data_name == 'notes':
            self._current_trip.notes = data_val
        else:
            self._logger.warning('Attempt to set unknown data name: {}'.format(data_name))
            return
        self._set_cur_prop(data_name, data_val)
        self._current_trip.save()

        logging.debug('Set {} to {}'.format(data_name, data_val))


class TestObserverTrip(unittest.TestCase):
    """
    Note: any write/update interaction should be done with test_database...
    http://stackoverflow.com/questions/15982801/custom-sqlite-database-for-unit-tests-for-code-using-peewee-orm
    """
    test_db = APSWDatabase(':memory:')
    vessel_id_test = 12850
    user_id_test = 1241
    prog_id_test = 1

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def _create_test_trips(self):
        """
        Note: intended to run with test_db, running alone will write to real DB
        Example of updating a trip in DB and in model
        """
        for t in range(3):
            newtrip = self.test.create_trip(observer_id=self.user_id_test + t,
                                            vessel_id=self.vessel_id_test + t,
                                            program_id=self.prog_id_test)
            newtrip.save()

    def _create_test_data(self):
        """
        Intended to run with test_db, before trips created
        """
        for t in range(3):
            Vessels.create(vessel=self.vessel_id_test + t, port=0, vessel_name='Test Vessel {}'.format(t))
            Users.create(user=self.user_id_test + t, first_name='User {}'.format(t), last_name='Last',
                         password='test', status=1)

        Programs.create(program=self.prog_id_test, program_name='Test Program')

        vess = Vessels.select()
        for p in vess:
            print('Created {}'.format(p.vessel_name))

        users = Users.select()
        for u in users:
            print('Created {}'.format(u.first_name))

        p = Programs.get(Programs.program == 1)
        print('Created {}'.format(p.program_name))

    def test_create(self):
        with test_database(self.test_db, [Trips, Vessels, Users, Programs]):
            self.test = ObserverTrip()
            self._create_test_data()
            self._create_test_trips()
            q = Trips.select()
            self.assertEqual(q.count(), 3)
