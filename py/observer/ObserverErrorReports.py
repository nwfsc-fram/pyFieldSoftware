# -----------------------------------------------------------------------------
# Name:        ObserverErrorReports.py
# Purpose:     OPTECS Error Reports (Trip, and perhaps at other levels as well).
#
# Author:      Jim Stearns <james.stearns@noaa.gov>
#
# Created:     8 March 2017
# License:     MIT
#
# ------------------------------------------------------------------------------

from enum import IntEnum, unique
from logging import getLogger, Logger
import os
import re
import sqlparse
import time
from typing import Any, Dict, Optional

from apsw import BindingsError, BusyError, SQLError
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model

# Database models
from py.observer import ObserverDBBaseModel
from py.observer.ObserverDBUtil import ObserverDBUtil
from py.observer.ObserverDBModels import TripChecks, Trips, Vessels
from py.observer.ObserverDBErrorReportsModels import TripChecksOptecs, TripIssues
from py.observer.ObserverDBBaseModel import database, DATABASE_TIMEOUT
from py.observer.ObserverDBSyncController import ObserverDBSyncController

from py.observer.ObserverTrip import ObserverTrip   # For getting list of user's valid trips.

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, Qt, QThread, QVariant

# View models
from py.observer.ObserverErrorReportModels import TripIssuesModel, TripErrorReportsModel


class ObserverErrorReportException(Exception):
    pass


@unique
class TripCheckEvaluationStatus(IntEnum):
    """
    The result when running every TRIP_CHECKS sql through the evaluation process of its go/no-go state
    on OPTECS. This value is stored in TRIP_CHECKS_OPTECS.CHECK_STATUS_OPTECS.
    """
    NOT_RUN_DISABLED_IN_OBSPROD = 0     # Disabled even on OBSPROD - no SELECT statement in CHECK_SQL field.
    NOT_RUN_DISABLED_IN_OPTECS = 1      # Disabled in OPTECS - datatype difference or other problem.
    NOT_RUN_ONLY_RUN_AT_CENTER = 2      # Key punch checks
    NOT_RUN_ORACLE_PLUS_JOIN = 3        # "(+)" for OUTER JOIN
    NOT_RUN_HAVING_BEFORE_GROUP = 4
    NOT_RUN_UNRECOGNIZED_MACRO = 5
    NOT_RUN_REQUIRES_OBSPROD_DATA = 6
    NOT_RUN_SQL_EXCEPTION = 7
    NOT_RUN_BINDING_EXCEPTION = 8
    NOT_RUN_INTEGRITY_EXCEPTION = 9

    # Convention: if value of enum is 100 or greater, then it's runnable on OPTECS
    RUN_AS_IS = 100
    RUN_AFTER_STATIC_MODS = 101         # Look to TripChecksOptecs.check_sql_optecs
    RUN_AFTER_DYNAMIC_MODS = 102        # Replace macros dynamically every run


@unique
class TripCheckExecutionStatus(IntEnum):
    NOT_RUN = 0
    RUN = 1
    RUN_FAILED_UNEXPECTEDLY = 2


class IntEnumCounter:
    """
    Maintain a count of how many times each enumeration value is tallied.

    TODO: Consider moving to an ObserverUtil.py file.
    """

    def __init__(self, int_enum_subclass_type, num_spaces_to_indent=4):
        # print(f'Type of IntEnum is {intenum_subclass_type}')
        if not issubclass(int_enum_subclass_type, IntEnum):
            msg = f'Class {int_enum_subclass_type} is not a subclass of IntEnum'
            print(msg)
            raise Exception(msg)
        self._int_enum_subclass_type = int_enum_subclass_type
        self._num_spaces_to_indent = num_spaces_to_indent
        self._counts = {}
        for name in self._int_enum_subclass_type.__members__.keys():
            self._counts[name] = 0
        self._ntallies = 0

    def tally(self, int_enum_subclass_instance):
        self._ntallies += 1
        self._counts[int_enum_subclass_instance.name] += 1

    def __repr__(self):
        output = []
        indent = ' ' * self._num_spaces_to_indent
        max_value_len = self._max_count_length()
        # Display in ascending value order.
        values = [class_and_value.value for class_and_value in
                  self._int_enum_subclass_type.__members__.values()]
        values = sorted(values)
        output.append(f'{indent}Summary of counts (Total = {self._ntallies}):')
        for enum_value in values:
            enum_name = self._int_enum_subclass_type(enum_value).name
            output.append(f'{indent}{indent}{self._counts[enum_name]:{max_value_len}}: {enum_name}')
        return '\n'.join(output)

    def _max_count_length(self):
        max_len = 0
        for name in self._int_enum_subclass_type.__members__.keys():
            this_int_as_str = str(self._counts[name])
            this_len = len(this_int_as_str)
            if this_len > max_len:
                max_len = this_len
        # print(f"Max count length (digits)={max_len}.")
        return max_len


class ThreadTER(QThread):
    """
    Class to do a TER on a background thread.
    """
    done_signal = pyqtSignal(QVariant)
    cancel_requested_signal = pyqtSignal()
    check_chunk_completed_signal = pyqtSignal(int, int)

    run_in_progress = False  # Class-level variable ensures only one ThreadTER at a time
    cancel_requested = False

    def __init__(self, parent=None):
        QThread.__init__(self, parent)

        ThreadTER.cancel_requested = False
        ThreadTER.run_in_progress = False

        self._run_datetime = None
        self._trip_id = None
        self._user_id = None
        self._logger = None

    def __del__(self):
        if self:
            self.wait()

    def run_TER(self, trip_id, user_id, logger):
        self._trip_id = trip_id
        self._user_id = user_id
        self._logger = logger
        self.start()

    def run(self):
        if ThreadTER.run_in_progress:
            raise ObserverErrorReportException("A run is in progress. Only one ThreadTER thread at a time.")

        ThreadTER.cancel_requested = False
        ThreadTER.run_in_progress = True
        check_chunk_size = 25
        self._logger.info("Starting run of Trip Error Report checks.")

        self._run_datetime = TripChecksOptecsManager.run_checks_on_trip(
                self._trip_id,
                self._user_id,
                self._logger,
                callback_check_chunk=self._callback_check_chunk_completed,
                callback_check_chunk_size=check_chunk_size,
                callback_cancel_processed=self._callback_cancel_processed)

        # Done: either completed or canceled. Either way, this run is done.
        done_status = "completed" if not ThreadTER.cancel_requested else "canceled"
        self._logger.info(f"Done with {done_status} background thread run of Trip Error Report checks.")
        ThreadTER.run_in_progress = False

        self.done_signal.emit(self._run_datetime)

        # Handshake is a bit fundamental: Wait to be terminated by handler of Done signal.
        while True:
            time.sleep(0.5)

    def cancel(self):
        ThreadTER.cancel_requested = True

    def _callback_check_chunk_completed(self, n_checks_completed, check_chunk_size):
        if ThreadTER.run_in_progress and not ThreadTER.cancel_requested:
            self._logger.debug(f"Checks completed = {n_checks_completed} " +
                               f"(in chunks of {check_chunk_size} checks).")
            self.check_chunk_completed_signal.emit(n_checks_completed, check_chunk_size)

    def _callback_cancel_processed(self):
        self._logger.debug(f"Cancel request received - TER run canceled.")
        self.cancel_requested_signal.emit()

class TripChecksDisabledInOptecs:
    """
    There are three categories of trip checks disabled in OPTECS
    (i.e. checks that continue to be run at Center but for one reason or another,
    can't be run in OPTECS):
    * Checks that use a macro defined in Oracle but not implemented in Sqlite.
    * Checks that use data defined in the Center's OBSPROD database, but not in OPTECS's
        observer.db. Most are related to keypunch fields.
    * Checks that can't be run in their Center form.

    Members of the first two categories are added by evaluating the trip check SQL.
    Members of this third category are added manually upon discovering a gotcha.
    """

    # List of trip checks disabled in OPTECS, beyond missing data or use of Oracle macros.
    # Example: a trip check that computes a time interval by subtracting one date from another.
    trip_checks_disabled_in_optecs = None

    # Trip checks that are disabled in this category are manually added, not from evaluation.
    # Store this list of manually disabled trip checks in the SETTINGS table
    # so that they may be modified without need to modify the code.
    TRAWL_ERROR_REPORTS_DISABLED_CHECKS_SETTING = 'trawl_error_reports_disabled_checks'

    # If no entry in SETTINGS, use these values (and store in SETTINGS)
    TRAWL_ERROR_REPORTS_DISABLED_CHECKS_DEFAULT = [
        1829,   # "﻿Soak time for set is than 15 minutes. Check for accuracy."
                # FIELD-1331
                # This check performs date-to-date subtraction. OK for Oracle date type,
                # not in sqlite where dates are of type text.

        1496,   # "﻿PHLB catch category exists and viabilities are missing."
                # FIELD-1332
                # With Weight Method 19 (specific to Pacific Halibut),
                # OPTECS creates "tally" records for PHLB that are counted but not length-measured.
                # (Tally records are assigned the average weight of "real" PHLB biospecimen records)
                # These entries have neither length nor weight nor viability.

        2347,   # "﻿PHLB catch category exists and bio specimen length is missing"
                # FIELD-1332
                # See description for TC 1496 above. PHLB tally records have no length entry.

        1482,   # "﻿Biospecimen length is missing (E), negative (E), zero (E) or greater than 200 (W)"
                # FIELD-1332
                # See description for TC 1496 above. PHLB tally records have no length entry.

        1848,   # "﻿Catch weight does not equal the sum of the species comp weights - whole haul"
                # FIELD-1329
                # TRIP ERROR REPORT TRIP_CHECK 1848 will fail (falsely report an error)
                # is MIX species is part of the catch. For example, if MIX species has a catch
                # weight of 10, TRIP_CHECK will report an error value of the actual catch weight,
                # plus 10 pounds.
                #
                # The double-counting is not the fault of the trip check, but due to Observer
                # placing a record in SPECIES_COMPOSITION_ITEMS for MIX species.
                # This SCI record is filtered out before a DB sync upload,
                # so TRIP CHECK 1848 will be performed, and pass, at Center in IFQ database.
        1917,   # FIELD-1553
                # "Sum of the species weights > 100 lbs (single basket sample)"
        1918,   # FIELD-1553
                # "Sample method 2 was used and Catch Weight = Sample Weight"
        1922,   # "﻿Species count is blank, negative or zero"
                # FIELD-1329
                # False positive triggered by a MIX species composition item. It has no count;
                # its purpose is to capture weights.
                # This MIX SCI records are NOT uploaded to Center, so OBSPROD will run, and pass,
                # TC1922. But OPTECS will not catch non-MIX species comp items with an empty count.
        3781,   # FIELD-1726
                # BRD Error, invalid in OPTECS
        3821,   # FIELD-1703
                # Species weight not ending in 0 or 5, invalid check for OPTECS
        3221,   # FIELD-1961, a KP we use internally
        2137,   # FIELD-1965 PHLB
        2139,   # FIELD-1965 PHLB
        1498,   # FIELD-1965 PHLB
        1847,   # FIELD-1985 TER on KP
    ]



    @staticmethod
    def trip_check_is_disabled_in_optecs(trip_check_id, logger):
        """ The main method of this class. Called during a TER run to determine whether
            a particular trip check needs to be disabled (not run on OPTECS).
        """
        if not TripChecksDisabledInOptecs.trip_checks_disabled_in_optecs:
            TripChecksDisabledInOptecs.trip_checks_disabled_in_optecs = \
                TripChecksDisabledInOptecs._build_list_of_trip_checks_disabled_in_optecs(logger)
        return trip_check_id in TripChecksDisabledInOptecs.trip_checks_disabled_in_optecs

    @staticmethod
    def _build_list_of_trip_checks_disabled_in_optecs(logger):
        """
        Get list of trip checks disabled in OPTECS as stored in SETTINGS table.

        If not found in SETTINGS, use the defaults defined above in this class,
        and save to SETTINGS as well.

        WS - Updated this, because updating the DB is less convenient than updating the code for this.

        :return: list of disabled trip checks.
        """
        settings_key = TripChecksDisabledInOptecs.TRAWL_ERROR_REPORTS_DISABLED_CHECKS_SETTING
        logger.info(f'Setting list of trip checks disabled in OPTECS to ' +
                    f'{TripChecksDisabledInOptecs.TRAWL_ERROR_REPORTS_DISABLED_CHECKS_DEFAULT}.')
        ObserverDBUtil.db_save_setting_as_json(
            TripChecksDisabledInOptecs.TRAWL_ERROR_REPORTS_DISABLED_CHECKS_SETTING,
            TripChecksDisabledInOptecs.TRAWL_ERROR_REPORTS_DISABLED_CHECKS_DEFAULT)
        disabled_checks = ObserverDBUtil.db_load_setting_as_json(
            TripChecksDisabledInOptecs.TRAWL_ERROR_REPORTS_DISABLED_CHECKS_SETTING)
        return disabled_checks


class ErrorFreeRunTracker:
    """
    Track the run dates of trips whose last TER run had no errors.
    Use to distinguish between a trip for which a TER has never been run and one run without error.

    Attempt to persist the error-free runs as a { <trip_id> : <run_date> } dictionary entry stored
    in Settings table. Note: key value <trip_id> is converted from int to string so that
    it can be an immutable key value for a Python dict.

    "Attempt": do attempt to write the trip ID and run date to this entry in the SETTINGS table,
    but if the write fails due to a database BusyError, skip the write: it's not worth
    crashing the application for the sake of a settings write whose only purpose is
    to display "No errors" in a TER entry.

    All static methods - state persisted in Settings table.
    """
    settings_parameter_name = "error_reports_no_error_trips"

    @staticmethod
    def add(trip_id: int, run_date: str, logger: Logger):
        key = ErrorFreeRunTracker.settings_parameter_name

        noerr_trip_dict: Dict[str, str] = ObserverDBUtil.db_load_setting_as_json(key)
        if not noerr_trip_dict:
            noerr_trip_dict = {}
        elif trip_id in noerr_trip_dict:
            # A previous no-error entry should have been removed at the beginning of the new TER run
            raise DataError("Attempt to add TripID that already exists in error_reports_no_error_trips")

        noerr_trip_dict[str(trip_id)] = run_date  # Convert key value to str (immutable)
        try:
            ObserverDBUtil.db_save_setting_as_json(key, noerr_trip_dict)
            logger.debug(f"Error-free entry added for Trip ID {trip_id} w/run date={run_date}.")
        except BusyError:
            # Take a chance writing an error-level log message that will go to the
            # OPTECS_LOG_MESSAGES table (ERROR-level log messages are written to the database):
            # Log message writes to DB provide ample retries.
            logger.error(f'Unable to write error-free entry for Trip ID {trip_id}; DB BusyError.')

    @staticmethod
    def remove(trip_id: int, logger: Logger):
        """
        Remove, if present, entry in no error trip dictionary for the specified trip_id
        :param trip_id:
        :param logger:
        :return: None
        """
        key = ErrorFreeRunTracker.settings_parameter_name
        noerr_trip_dict: Dict[str, str] = ObserverDBUtil.db_load_setting_as_json(key)
        if not noerr_trip_dict or str(trip_id) not in noerr_trip_dict:
            logger.debug(f"No entry in error in Settings['{key}'] to remove for TripID {trip_id}.")
            return

        del noerr_trip_dict[str(trip_id)]
        ObserverDBUtil.db_save_setting_as_json(key, noerr_trip_dict)

        logger.debug(f"Error-free trip entry for Trip ID {trip_id} removed.")

    @staticmethod
    def lookup(trip_id, logger: Logger) -> Optional[str]:
        """
        Was the last TER run for a trip error-free?
        If so, return its run date, else None
        """
        key = ErrorFreeRunTracker.settings_parameter_name
        noerr_trip_dict: Dict[str, str] = ObserverDBUtil.db_load_setting_as_json(key)
        if not noerr_trip_dict or str(trip_id) not in noerr_trip_dict:
            logger.debug(f"No entry in error in Settings['{key}'] for TripID {trip_id}.")
            return None

        logger.debug(f"Error-free entry found for Trip {trip_id}.")
        return noerr_trip_dict[str(trip_id)]


class TripChecksOptecsManager:
    """
    Manage the TRIP_CHECKS_OPTECS table and its synchronization with the TRIP_CHECKS table.
    Manage the execution of trip checks.

    A class composed entirely of static methods. It need not be instantiated.
    
    TRIP_CHECKS_OPTECS is a table only in OPTECS - no counterpart in OBSPROD at Center.
    TRIP_CHECKS is a table originating in OBSPROD, and its definition, at the least, is downloaded to OPTECS.

    The purpose of TRIP_CHECKS_OPTECS is to keep track of the trip checks as run in OPTECS:
    - Are the trip checks, modified if necessary to run in OPTECS, loaded into OPTECS?
    - If not, load the OPSPROD TRIP_CHECKS into OPTECS with customizations noted in TRIP_CHECKS_OPTECS.
    """
    TRIP_CHECKS_TABLE_CHECKSUM_SETTING = 'last_trip_checks_table_checksum'
    unrecognized_macros = None

    # Obsolete, but left as backstop in case TRIP_CHECKS empty.
    # Created using Navicat Export in JSON format:
    # - all fields in TRIP_CHECKS except RECORD_* fields.
    # - Date Order: YMD, Date Delimiter: '/", Zero Padding Date: No, Time Delimiter: ':", Binary Encoding: Base64.
    TRIP_CHECK_JSON_FILEPATH = 'data/OBSPROD_TRIP_CHECKS.json'

    @staticmethod
    def get_debriefer_checks():
        """
        trip checks only visible in debriefer mode
        FIELD-2101: use to hide TERs from non-debriefers
        :return: list of trip_check_ids; int[]
        """
        return [t.trip_check for t in TripChecks.select().where(TripChecks.debriefer_only == 1)]

    @staticmethod
    def get_unrecognized_macros():
        if not TripChecksOptecsManager.unrecognized_macros:
            TripChecksOptecsManager.unrecognized_macros = TripChecksOptecsManager._build_list_of_all_unknown_macros()
        return TripChecksOptecsManager.unrecognized_macros

    @staticmethod
    def _build_list_of_all_unknown_macros():
        unrecognized_macros = [
            'TO_CHAR',          # Oracle Conversion function
            'TO_DATE',          # Oracle Conversion function
            'SYSTIMESTAMP',     # Oracle Date/Time function
            'DECODE',           # Oracle Advanced function - an IF-THEN-ELSE statement
            'TRUNC',            # Oracle Date/Time function
            'TRANSLATE',        # Oracle String function - multiple single-character replacements
            'REGEXP_LIKE',      # Oracle Condition - regular expression matching in WHERE clause of INSERT (et al)
            'ROWNUM',           # Oracle Numeric/Match function for current row number
            'ROW_NUMBER',       # Oracle Analytic function - assigns a unique number to each row.
            'NVL',              # Oracle - replace null value with a string
            'CHECK_CC',
            'CHECK_CC_UNSAMPLED',
            'Find_All_Trps',
            'F_MISSING_SALMON_BIOS',
            'isalphanumeric']
        unrecognized_macros_lowercase = []
        unrecognized_macros_uppercase = []
        for macro in unrecognized_macros:
            unrecognized_macros_lowercase.append(macro.lower())
            unrecognized_macros_uppercase.append(macro.upper())
        unrecognized_macros_all_cases = unrecognized_macros + unrecognized_macros_lowercase + \
                unrecognized_macros_uppercase
        return unrecognized_macros_all_cases

    @staticmethod
    def _load_trip_checks_from_json(json_filepath, logger):
        """
        Before late March 2017, OPTECS's Observer DB Table TRIP_CHECKS was not
        synchronized with Observer OBSPROD; TRIP_CHECKS is defined, but empty.

        If TRIPS_CHECKS is empty, load the values from a JSON file created by
        manually exporting TRIP_CHECKS from OBSPROD.

        :return: number of trip checks loaded into TRIP_CHECKS.
        """
        return ObserverDBUtil.load_peewee_model_from_json_file(
                TripChecks, json_filepath, logger)

    @staticmethod
    def _json_trip_checks_file_exists(json_filepath):
        return os.path.isfile(json_filepath)

    @staticmethod
    def _no_trips_yet_in_database():
        try:
            Trips.select().get()
            return False
        except Trips.DoesNotExist:
            return True

    @staticmethod
    def _trip_checks_table_is_empty():
        try:
            TripChecks.select().get()
            return False
        except TripChecks.DoesNotExist:
            return True

    @staticmethod
    def get_last_trip_checks_table_checksum():
        """
        Get the last checksum calculated for Table TRIP_CHECKS as persisted in the SETTINGS table.
        
        :return: SHA1 checksum or None if not yet checksummed.
        """
        sha1_checksum = ObserverDBUtil.db_load_setting(
                TripChecksOptecsManager.TRIP_CHECKS_TABLE_CHECKSUM_SETTING)
        return sha1_checksum

    @staticmethod
    def set_last_trip_checks_table_checksum(new_sha1_checksum):
        ObserverDBUtil.db_save_setting(
                TripChecksOptecsManager.TRIP_CHECKS_TABLE_CHECKSUM_SETTING, new_sha1_checksum)

    @staticmethod
    def get_trip_checks_count():
        if not TripChecksOptecs.table_exists():
            return 0
        return TripChecksOptecs.select().count()

    ####
    # TRIP CHECK EVALUATION - CAN A TRIP CHECK BE RUN BY OPTECS?
    ####
    @staticmethod
    def trip_checks_have_been_evaluated_for_use_in_optecs(logger) -> bool:
        """
            Return True iff:
            - Table TripChecksOptecs exists and is not empty.
            - Table TripChecks hasn't changed since the last time they were
              loaded into OPTECS.
              Technique: check that the checksum on the CHECK_TRIPS table
              hasn't changed since the last evaluation.
            - The number of records matches that in TripChecks.
            - Every TripChecksOptecs record has a unique CheckTrip ID
              (i.e., a 1:1 mapping)
            - Default SETTINGS is identical to stored Skipped Checks
            
            Made a static method so that it can be called by the Hauls screen
            with less concern of affecting ObserverErrorReport's internal state.
           
        :param logger
        :return: True if all conditions above met else False
        """
        if not TripChecksOptecs.table_exists():
            logger.info("Table TRIP_CHECKS_OPTECS does not exist.")
            return False

        last_checksum = TripChecksOptecsManager.get_last_trip_checks_table_checksum()
        if not last_checksum:
            logger.info("Checksum for Table TRIP_CHECKS has not yet been calculated.")
            return False

        current_checksum = ObserverDBUtil.checksum_peewee_model(TripChecks, logger)
        if last_checksum != current_checksum:
            logger.info("Checksum for Table TRIP_CHECKS has changed since last trip check evaluation.")
            return False
        logger.info("Table TRIP_CHECKS has not changed since last trip check evaluation.")

        try:
            TripChecksOptecs.select().get()
        except TripChecksOptecs.DoesNotExist:
            logger.info("Table TRIP_CHECKS_OPTECS is empty.")
            return False

        n_trip_checks_records = TripChecks.select().count()
        n_trip_checks_optecs_records = TripChecksOptecs.select().count()
        if n_trip_checks_records != n_trip_checks_optecs_records:
            logger.info(f"Number of records in table TRIP_CHECKS_OPTECS ({n_trip_checks_optecs_records}) " +
                    f"does not match number in table TRIP_CHECKS ({n_trip_checks_records}).")
            return False

        n_distinct_trips_ids = TripChecksOptecs.select(TripChecksOptecs.trip_check).distinct().count()
        if n_distinct_trips_ids != n_trip_checks_optecs_records:
            logger.info(f"There are {n_trip_checks_optecs_records} records in table TRIP_CHECKS_OPTECS " +
                    f"but only {n_distinct_trips_ids} distinct TRIP_CHECKS IDs.")
            return False

        settings_key = TripChecksDisabledInOptecs.TRAWL_ERROR_REPORTS_DISABLED_CHECKS_SETTING
        disabled_checks = ObserverDBUtil.db_load_setting_as_json(settings_key)
        if disabled_checks:  # verify count is identical to stored in DB
            if disabled_checks != TripChecksDisabledInOptecs.TRAWL_ERROR_REPORTS_DISABLED_CHECKS_DEFAULT:
                logger.info('Default disabled checks changed. Need to re-run TER analysis.')
                return False

        logger.info("TRIP_CHECKS_OPTECS is loaded.")
        return True

    @staticmethod
    def evaluate(logger, force=True):
        """
        Evaluate every trip check in TRIP_CHECKS. Should the check be run on OPTECS?
        If so, can it be run as-is, or will it need some kind of modification?
        If not, why can't it be run(e.g. disabled in OBSPROD, uses Oracle-specific syntax).

        This should be run if TRIP_CHECKS_OPTECS doesn't exist (after a new install of OPTECS) or after a change to
        the TRIP_CHECKS during a DB sync download.

        The evaluation result of each trip check is stored in TRIP_CHECKS_OPTECS.CHECK_STATUS_OPTECS.
        
        The checksum of the TRIP_CHECKS table is stored in the Settings table,
        for comparision in subsequent runs.

        :param trip_id: The SQL of each check that's evaluated by trying to
        run it on a trip. Use this trip.
        :param logger:
        :param force: If a non-empty TripChecksOptecs table exists, clear it.
        If no force, and non-empty, raise exception.
        :return: None.
        """
        if TripChecksOptecs.table_exists():
            if TripChecksOptecs.select().count() > 0 and not force:
                raise ObserverErrorReportException(
                    "Evaluation aborted - non-empty TRIP_CHECKS_OPTECS exists, w/no force.")
            TripChecksOptecs.drop_table()

        TripChecksOptecs.create_table()
        logger.debug("TRIP_CHECKS_OPTECS Table created.")

        # Neither trip ID nor user ID need exist for evaluation of SQL for syntax. Pick a number.
        dummy_user_id = dummy_trip_id = 1

        TripChecksOptecsManager._evaluate_checks_on_trip(dummy_user_id, dummy_trip_id, logger)

        # Evaluation completed. Save the checksum on the TRIP_CHECKS table.
        # Will be used in later runs to detect change.
        TripChecksOptecsManager.set_last_trip_checks_table_checksum(
                ObserverDBUtil.checksum_peewee_model(TripChecks, logger))

    @staticmethod
    def _evaluate_checks_on_trip(user_id, trip_id, logger):
        """
        Run the checks contained in TRIP_CHECKS on the specified trip,
        building in TRIP_CHECK_OPTECS the corresponding check when run on OPTECS
        (not run, run as-is, run with mods).

        Throw an exception if the trip_id doesn't exist.
                    
        Made less prone to triggering a database timeout on the UI by specifying
        a sleep between successive DB operations. Combined with a database
        timeout larger than the time to execute a single DB operation here,
        DB timeout on the UI thread should be avoided.
 
        :return:
        """
        if trip_id is None or trip_id < 0:
            logger.warning(f"Invalid trip ID ({trip_id}). Trip check evaluation not run.")
            return

        # Assumptions: TRIP_CHECK_OPTECS table exists, empty.
        if not TripChecksOptecs.table_exists():
            raise ObserverErrorReportException("evaluate_on_trip expects TripChecksOptecs table to exist.")
        if TripChecksOptecs.select().count() > 0:
            raise ObserverErrorReportException("evaluate_on_trip expects TripChecksOptecs table to be empty.")

        start_evaluation_time = time.time()
        logger.info(f"CHECK_TRIP SQL Evaluation Started ...")

        created_date = TripChecksOptecsManager._get_current_datetime_for_ter_rundate()
        logger.info(f"Run datetime for this check of Trip#{trip_id}: {created_date}")

        trip_check_dict = TripChecksOptecsManager._build_trip_check_dictionary_from_trip_checks()
        counter = IntEnumCounter(TripCheckEvaluationStatus)
        for check_id, (check_message, sql) in trip_check_dict.items():
            replace_parameters = {  # Key value is parameter as contained in PL SQL (namely, a leading colon)
                ':trip_id': trip_id,
                ':trip_check_id': check_id,
                ':created_by': user_id,
                ':created_date': created_date,
            }
            # logger.info(f'---- CHECK_ID {check_id} ({check_message}):')
            execution_result = TripChecksOptecsManager._evaluate_one_check(
                    check_message, sql, replace_parameters, logger)

            # This may be running on a background thread. Allow for possibility
            # of concurrent UI thread DB access # by yielding after after every
            # SQL access (avoids timeout if operation less than database.timeout)
            time.sleep(0.01)

            counter.tally(execution_result)

            # Create a row in TRIP_CHECKS_OPTECS for this check:
            TripChecksOptecs.create(trip_check=check_id,
                                    check_status_optecs=execution_result.value,
                                    check_sql_optecs=sql)

        # Delete any trip issues added. This is just a trial run, so don't leave clutter.
        # Relies upon on created_date being non-null for all non-trial-run trip checks.
        trial_run_issues = TripIssues.select().where(TripIssues.created_date >> None)
        if trial_run_issues:
            logger.debug(f"Deleting {trial_run_issues.count()} null date trip issue record(s).")
            for trip_issue in trial_run_issues:
                trip_issue.delete_instance()
        else:
            logger.warning("No trial run issues added during trip check evaluation.")

        elapsed_time = time.time() - start_evaluation_time
        logger.info(f"CHECK_TRIP SQL Evaluation Results({elapsed_time:.0f} seconds):\n{counter}")

    @staticmethod
    def _build_trip_check_dictionary_from_trip_checks(): # -> Dict[int, Tuple[str, str]]:
        """
        On a normal TER run, the checks are pulled from TRIP_CHECKS_OPTECS table.
        But here, we're building the list from TRIP_CHECKS and doing the run in
        order to build TRIP_CHECKS_OPTECS.

        Read all the rows of TRIP_CHECKS into a dictionary keyed by trip check id.
        Include in the value tuple the check message and check sql.

        :return: A dictionary of trip checks. Each entry is a trip check, key id,
         with a tuple of message and sql.

        TODO: Consider converting to a trip check list. Is access to dictionary
        via index useful?
        """
        check_dict = {}
        # noinspection SqlNoDataSourceInspection,SqlResolve
        cursor = database.execute_sql(
                'SELECT TRIP_CHECK_ID, CHECK_MESSAGE, CHECK_SQL FROM TRIP_CHECKS;')
        for trip_check_id, check_message, plsql in cursor:
            check_dict[trip_check_id] = (check_message, plsql)
        return check_dict

    @staticmethod
    def _evaluate_one_check(
            chk_msg: str,
            sql: str,
            replace_parameters: Dict[str, Any],
            logger) -> TripCheckEvaluationStatus:
        """
        Execute a single trip_check on a single trip. The trip id and the
        check id are included in replace_parameters.
        
        No output, except a new entry in TRIP_ISSUES.

        :param chk_msg: CHECK_MESSAGE string for this check.
        :param sql: the sql to execute. Return if empty string w/o attempting to run.
        :param replace_parameters: Replace query variables (dictionary key) with dictionary value.
            Using format of PL SQL: ':<variable>' (i.e. name preceded by colon).
        :return: The categorization of the check: OK as-is, disabled, contains Oracle syntax, ...
        """
        check_id = replace_parameters[':trip_check_id']

        # Replace query variables with actual values from replace_parameters,
        # allowing for upper or lower case.
        for query_parm, value in replace_parameters.items():
            sql = sql.replace(query_parm.lower(), str(value))
            sql = sql.replace(query_parm.upper(), str(value))
        sql_formatted = sqlparse.format(sql, reindent=True, keyword_case='upper')

        execution_result = None
        if len(sql) == 0 or sql.startswith("DISABLED") or sql.startswith("IGNORED") or \
                sql.startswith("SEE PROCEDURE") or sql.startswith("TEMP"):
            execution_result = TripCheckEvaluationStatus.NOT_RUN_DISABLED_IN_OBSPROD
            logger.debug(f"Check {check_id} is disabled - not run")
        elif 'key punch' in chk_msg and '_kp' in sql.lower():
            execution_result = TripCheckEvaluationStatus.NOT_RUN_ONLY_RUN_AT_CENTER
            logger.debug(f"Check {check_id} not run: uses a key punch field (entered at center).")
        elif '(+)' in sql:
            execution_result = TripCheckEvaluationStatus.NOT_RUN_ORACLE_PLUS_JOIN
            logger.debug(f"Check {check_id} not run - known problem - (+) OUTER JOIN syntax")
        elif TripChecksOptecsManager.sql_check_having_is_before_groupby(sql):
            execution_result = TripCheckEvaluationStatus.NOT_RUN_HAVING_BEFORE_GROUP
            logger.debug(f"Check {check_id} not run - known problem - HAVING clause before GROUP BY")
        elif any(macro in sql for macro in TripChecksOptecsManager.get_unrecognized_macros()):
            execution_result = TripCheckEvaluationStatus.NOT_RUN_UNRECOGNIZED_MACRO
            logger.debug(f"Check {check_id} not run - known problem - unrecognized macro")
            logger.debug(f"Check {check_id}: SQL w/unknown macro:\n{sql_formatted}")
        elif TripChecksDisabledInOptecs.trip_check_is_disabled_in_optecs(check_id, logger):
            execution_result = TripCheckEvaluationStatus.NOT_RUN_DISABLED_IN_OPTECS
            logger.debug(f"Check {check_id} not run - known problem - disabled in OPTECS")
        else:
            try:
                n_trip_issues_before = TripIssues.select().count()
                database.execute_sql(sql)
                n_trip_issues_after = TripIssues.select().count()
                issue_added = n_trip_issues_after > n_trip_issues_before
                issue_added_text = " ISSUE ADDED" if issue_added else "no issue"
                logger.debug(f"Check {check_id} ran without exception: {issue_added_text}")
                execution_result = TripCheckEvaluationStatus.RUN_AS_IS
            except SQLError as e:
                # Special-case: SQL error due to referencing table or column in OBSPROD
                # but not in Observer.db:
                table_or_column_is_missing, missing_data = \
                        TripChecksOptecsManager._check_uses_data_not_in_optecs(e.args[0])
                if table_or_column_is_missing:
                    execution_result = TripCheckEvaluationStatus.NOT_RUN_REQUIRES_OBSPROD_DATA
                    logger.debug(f"Check {check_id} uses table or column not in OPTECS: '{missing_data}'.")
                else:
                    execution_result = TripCheckEvaluationStatus.NOT_RUN_SQL_EXCEPTION
                    logger.error(f"Check {check_id}: {e}")
                    logger.debug(f"Check {check_id}: SQL causing exception:\n{sql_formatted}")
            except BindingsError as e:
                execution_result = TripCheckEvaluationStatus.NOT_RUN_BINDING_EXCEPTION
                logger.error(f"Check {check_id}: {e}")
                logger.debug(f"Check {check_id}: SQL causing exception:\n{sql_formatted}")
            except IntegrityError as e:
                execution_result = TripCheckEvaluationStatus.NOT_RUN_INTEGRITY_EXCEPTION
                logger.error(f"Check {check_id}: {e}")
                logger.debug(f"Check {check_id}: SQL causing exception:\n{sql_formatted}")

        return execution_result

    @staticmethod
    def sql_check_having_is_before_groupby(sql):
        """
        SQLite insists that HAVING clause be after GROUP BY clause.
        PL SQL apparently accepts either order.
        
        A bit braindead: only tests for first occurrence of each. But this is
        temporary check, and seems to work for SQL in TRIP_CHECKS.
        
        :param sql:
        :return:
        """
        idx_having = sql.find('HAVING')
        if idx_having < 0:
            idx_having = sql.find('having')
        if idx_having < 0:
            return False

        idx_groupby = sql.find('GROUP BY')
        if idx_groupby < 0:
            idx_groupby = sql.find('group by')
        if idx_groupby < 0:
            return False

        return idx_having < idx_groupby

    @staticmethod
    def _check_uses_data_not_in_optecs(sql_error_message):
        """
        Parse a SQL error message for
        :param sql_error_message:
        :return: tuple (boolean, matching string)
            True if message contains "no such table"
            or "no such column <table_alias>.<field_name>"
            (The column check excludes not finding a macro,
            as in "no such column: rownum"
        """
        missing_table_pattern = re.compile("no such table: [\w_]+")
        match = missing_table_pattern.search(sql_error_message)
        if match:
            return True, match.group()

        missing_column_pattern = re.compile("no such column: [\w_]+\.[\w_]+")
        match = missing_column_pattern.search(sql_error_message)
        if match:
            return True, match.group()

        return False, ""

    @staticmethod
    def _get_current_datetime_for_ter_rundate():
        # Use Will's OPTECS-wide format for run datetime, with the addition of
        # seconds. Justification for adding seconds: Observer could click
        # Run TER multiple times a minute.
        date_format = 'MM/DD/YYYY HH:mm:ss'
        return ObserverDBUtil.get_arrow_datestr(date_format)

    ####
    # TRIP CHECK EXECUTION - EXECUTING THE SQL IN EACH TRIP CHECK AGAINST
    # OBSERVER.DB, ADDING ENTRIES TO TRIP_ISSUES.
    ####
    @staticmethod
    def run_checks_on_trip(trip_id, user_id, logger,
                           callback_check_chunk=None,
                           callback_check_chunk_size=25,
                           callback_cancel_processed=None):
        """
        Run set of check on the specified trip, using TripChecksOptecs's
        classification to run checks that have been vetted to run on OPTECS.
        
        Does not use local user_id. Does not update Error Reports screen's view models.
        What is does do is run the TER on the trip specified and for the user specified,
        inserting any trip issues into TRIP_ISSUES.
        
        Specified as @staticmethod to reduce dependencies - easier to run on
        a background thread. 
        
        Intended to be used by Error Reports screen (calling through
        run_checks_for_error_reports_screen()).
        
        Possible future use: use by Hauls screen (calling from the python model,
        supplying trip id and user id).

        :param trip_id:
        :param user_id:
        :param logger:
        :param callback_check_chunk: callback method to call when a chunk of N trip checks are done, N being ...
        :param callback_check_chunk_size: size of a chunk
        :param callback_cancel_processed: callback method to call when finished processing a cancel request.
        :return: TER run datetime
        """
        if ObserverDBBaseModel.use_encrypted_database:
            ObserverDBBaseModel.activate_encryption(database)

        if trip_id is None or trip_id < 0 or Trips.select().where(Trips.trip == trip_id).count() == 0:
            logger.warning(f"Invalid trip ID ({trip_id}). TER not run.")
            return None

        # (ThreadTER.run_in_progress has already been set True by calling run() method. Don't set or check here.

        # This background thread accesses observer.db. So may the UI thread, if navigation away from
        # from the ErrorReports screen is supported.
        # DB operations on ThreadTER should interleave sleep() with DB operations.
        # This check makes sure that the expected database timeout has been specified.
        if database.timeout < DATABASE_TIMEOUT:
            msg = f"Database timeout is {database.timeout}. Should be {DATABASE_TIMEOUT}."
            logger.error(msg)
            raise ObserverErrorReportException(msg)

        # This is a backstop in case the GUI forgets to evaluate trip checks before running a Error Report.
        # Not optimal to be run here - the evaluation takes about 15 seconds and give the impression OPTECS is hung.
        if not TripChecksOptecsManager.trip_checks_have_been_evaluated_for_use_in_optecs(logger):
            logger.warning("TER run requested without trip check evaluation having been performed.")
            logger.warning("Performing the trip check evaluation.")
            TripChecksOptecsManager.evaluate(logger)

        created_date = TripChecksOptecsManager._get_current_datetime_for_ter_rundate()
        logger.info(f"Run datetime for this check of Trip#{trip_id}: {created_date}")
        results_counter = IntEnumCounter(TripCheckExecutionStatus)

        start_time = time.time()

        categorized_trip_checks_q = TripChecksOptecs.select().order_by(TripChecksOptecs.trip_check).asc()
        n_checks = 0
        n_checks_this_chunk = 0
        n_busyerror_exceptions = 0
        for trip_check_optecs_record in categorized_trip_checks_q:
            # This may be running on a background thread. Allow for possibility
            # of concurrent UI thread DB access by yielding after after every
            # SQL access (less than database.timeout)
            time.sleep(0.01)    # Allow context switch to UI thread before every DB operation

            check_id = trip_check_optecs_record.trip_check.trip_check
            # TODO: If support for OPTECS-specifics SQL is add, will want to
            # use check_sql_optecs for checks needing mods to run in OPTECS.
            # For now...
            check_sql = trip_check_optecs_record.trip_check.check_sql
            check_status_optecs = TripCheckEvaluationStatus(
                trip_check_optecs_record.check_status_optecs)  # Run/Don't run

            replace_parameters = {  # Key value is parameter as contained in PL SQL (namely, a leading colon)
                ':trip_id': trip_id,
                ':trip_check_id': check_id,
                ':created_by': user_id,
                ':created_date': created_date,
            }
            new_issue_field_updates = {  # Key value is peewee field name
                'created_date': created_date
            }
            result = None
            while result is None:
                try:
                    result = TripChecksOptecsManager._execute_one_check(
                            check_status_optecs, check_sql, replace_parameters,
                            new_issue_field_updates, logger)
                except BusyError:
                    n_busyerror_exceptions += 1

            results_counter.tally(result)

            if ThreadTER.cancel_requested:
                logger.info(f'Received cancel request')
                TripChecksOptecsManager.delete_issues_from_ter_run(trip_id, created_date, logger)
                if callback_cancel_processed:
                    callback_cancel_processed()
                return created_date

            n_checks += 1
            n_checks_this_chunk += 1
            if callback_check_chunk and n_checks_this_chunk >= callback_check_chunk_size:
                callback_check_chunk(n_checks, callback_check_chunk_size)
                n_checks_this_chunk = 0

        # Update any lingering trip checks less than a chunk.
        if callback_check_chunk and n_checks_this_chunk >= 0:
            callback_check_chunk(n_checks, callback_check_chunk_size)

        elapsed_time = time.time() - start_time
        logger.info(f"CHECK_TRIP SQL Execution Results\n" +
                    f"\t(Run Date: '{created_date}', Elapsed Seconds: {elapsed_time:.1f}):\n" +
                    f"{results_counter}")
        if n_busyerror_exceptions > 0:
            logger.info(f"\tTrip checks completed with {n_busyerror_exceptions} BusyErrors.")

        # Remove earlier TER runs for this trip.
        TripChecksOptecsManager.delete_issues_from_superceded_ter_runs(trip_id, created_date, logger)
        return created_date

    @staticmethod
    def _execute_one_check(check_status_optecs: TripCheckEvaluationStatus,
                           sql: str, replace_parameters: Dict[str, Any],
                           new_issue_field_updates: Dict[str, Any],
                           logger) -> TripCheckExecutionStatus:
        """
        Execute a single trip_check on a single trip. The trip id and the check
        id are included in replace_parameters. No output, except a new entry in
        TRIP_ISSUES.

        :param check_status_optecs: Categorization of the check - can it be run
        on OPTECS? Use to skip no-ops.
        :param sql: the sql to execute. Return if empty string w/o attempting to run.
        :param replace_parameters: Replace query variables (dictionary key)
        with dictionary value. Using format of PL SQL: ':<variable>'
        (i.e. name preceded by colon).
        :param new_issue_field_updates: name/value pairs of fields in TRIP_ISSUES
        whose value should be set after an issue is inserted. A bit of a fixup,
        first used for created_date.
        :return: TripCheckExecutionStatus (enumeration). Only method
        (i.e. not evaluation) where RUN_FAILED_UNEXPECTEDLY can be returned.
        """
        trip_id = replace_parameters[':trip_id']
        check_id = replace_parameters[':trip_check_id']
        sql_formatted = sqlparse.format(sql, reindent=True, keyword_case='upper')

        # Replace query variables with actual values from replace_parameters,
        # allowing for upper or lower case.
        for query_parm, value in replace_parameters.items():
            sql = sql.replace(query_parm.lower(), str(value))
            sql = sql.replace(query_parm.upper(), str(value))

        if check_status_optecs.value < TripCheckEvaluationStatus.RUN_AS_IS:
            logger.debug(f"Check {check_id} ({check_status_optecs.name}): not run.")
            return TripCheckExecutionStatus.NOT_RUN

        try:
            n_trip_issues_before = TripIssues.select().count()
            database.execute_sql(sql)
            n_trip_issues_after = TripIssues.select().count()
            issue_added = n_trip_issues_after > n_trip_issues_before
            if issue_added:
                # Update the created_date field and any others in new_issue_field_updates.
                TripChecksOptecsManager._perform_new_issue_field_updates(
                        trip_id, check_id, new_issue_field_updates, logger)
                logger.info(f"Check {check_id} ({check_status_optecs.name}): triggered.")
            return TripCheckExecutionStatus.RUN
        except (SQLError, BindingsError, IntegrityError) as e:
            logger.error(f"Check {check_id}: Unexpected exception {e}")
            logger.debug(f"Check {check_id}: SQL causing exception:\n{sql_formatted}")
            return TripCheckExecutionStatus.RUN_FAILED_UNEXPECTEDLY

    @staticmethod
    def _perform_new_issue_field_updates(trip_id: int, check_id: int,
                                         fields_to_update: Dict[str, Any], logger):
        """
        Assumes that a trip issue has just been added for the specified trip
        and and check. Updates to some null fields are desired.

        Raises exception if field name doesn't exist. Raises exception if
        pre-existing field value is not null.

        :param fields_to_update: key is Peewee field name, value is the value to be set.
        :return:
        """
        # The just-completed run will have generated trip issues without a created_date.
        # These are the ones to update.
        # Most trip checks will generate at most only one trip issue.
        # But some TCs (e.g. check for location in each haul of a trip) can generate multiple.
        issues_to_update = TripIssues.select().where(
            (TripIssues.trip == trip_id) &
            (TripIssues.trip_check == check_id) &
            (TripIssues.created_date.is_null(True)))
        for issue_to_update in issues_to_update:
            model_as_dict = model_to_dict(issue_to_update)
            for field_name, new_value in fields_to_update.items():
                if model_as_dict[field_name] is not None:
                    msg = f'Attempt to overwrite a non-null value' \
                          f' {field_name}={model_as_dict[field_name]}.'
                    logger.error(msg)
                    raise ObserverErrorReportException(
                            f"TripID:{trip_id}, CheckID:{check_id}: {msg}")
                model_as_dict[field_name] = new_value
                logger.debug(f"TC{check_id}: Set TripIssues.{field_name}={new_value}.")
            dict_as_model = dict_to_model(TripIssues, model_as_dict)
            dict_as_model.save()

    @staticmethod
    def get_issues_from_last_ter_run(trip_id, logger):
        """
        Multiple TER runs on a given trip is possible, even likely.

        :param trip_id:
        :param logger:
        :return: list of TripIssue model instances from the most recent run, and the last run date.
        """
        all_trip_issues = TripIssues.select().where(TripIssues.trip == trip_id)
        run_dates = [x.created_date for x in
                     all_trip_issues.select(TripIssues.created_date).distinct().order_by(
                         TripIssues.created_date.desc())]
        if not run_dates:
            return None, None
        last_run_date = run_dates[0]
        # logger.debug(f"Run dates = {run_dates}, latest = '{last_run_date}'")
        try:
            latest_trip_issues = all_trip_issues.select().where(TripIssues.created_date == last_run_date)
            return latest_trip_issues, last_run_date
        except TripIssues.DoesNotExist:
            return None, None

    @staticmethod
    def delete_issues_from_ter_run(trip_id: int, run_date: str, logger):
        """
        Called by cancel to remove partial set of trip issues from canceled run.
        :param trip_id: 
        :param run_date:
        :param logger: 
        :return: 
        """

        last_ter_issues = TripIssues.select().where((TripIssues.trip == trip_id) &
                                                    (TripIssues.created_date == run_date))
        n_last_ter_issues = last_ter_issues.count() if last_ter_issues else 0
        if n_last_ter_issues > 0:
            for issue in last_ter_issues:
                issue.delete_instance()
                time.sleep(0.01)    # Allow context switch to UI thread before every DB operation
            logger.info(f"Deleted {n_last_ter_issues} issues")
        else:
            logger.info("No issues to delete.")

    @staticmethod
    def delete_issues_from_superceded_ter_runs(trip_id: int, keep_this_date: str, logger):
        """
        Called when a TER has been completed to remove sets of trip issues from prior TER run(s).
        :param trip_id: 
        :param keep_this_date: date of last TER run completed. Don't delete these.
        :param logger: 
        :return: 
        """

        all_trip_issues = TripIssues.select().where(TripIssues.trip == trip_id)
        logger.debug(f"Trip {trip_id} has {all_trip_issues.count()} issues (including latest trip)")
        n_superceded_issues = 0
        for trip_issue in all_trip_issues:
            if trip_issue.created_date != keep_this_date:
                trip_issue.delete_instance()
                n_superceded_issues += 1
                time.sleep(0.01)    # Allow context switch to UI thread before every DB operation

        logger.info(f"Deleted {n_superceded_issues} superceded issues")


class ObserverErrorReports(QObject):
    terCheckChunkCompleted = pyqtSignal(
            int, int, name='terCheckChunkCompleted',
            arguments=['checksCompleted', 'chunkSize'])
    terRunCompleted = pyqtSignal(name='terRunCompleted')
    terRunCanceled = pyqtSignal(name='terRunCanceled')

    unusedSignal = pyqtSignal(name='unusedSignal')  # To suppress pyqtProperty warning

    def __init__(self):
        super().__init__()
        self._logger = getLogger(__name__)

        # Get these values every time this screen becomes active (receives youAreUp())
        self._current_user_id = None
        self._current_program_id = None
        self._current_trip_id = None
        self._current_user_valid_trip_ids = None
        self._current_debriefer_mode = None
        self._thread_TER = None

        # The TRIP_CHECKS table exists in the initial Observer.db and is updated as part of DB sync download.

        # The TRIP_CHECKS_OPTECS table is NOT part of the initial Observer.db. If it doesn't exist,
        # create it here. But don't do the evaluation of trip checks that fills TRIP_CHECKS_OPTECS:
        # it takes about 15 seconds. Defer initializing the TRIP_CHECKS_OPTECS table until a TER is requested.
        if not TripChecksOptecs.table_exists():
            TripChecksOptecs.create_table()

        # TripIssues table of Observer DB is not part of the models in ObserverDBModels:
        # it's not part of the database modeled upon OBSPROD. This could change in the future,
        # but in the meantime, instantiate the TRIP_ISSUES table here if it doesn't exist.
        if not TripIssues.table_exists():
            self._logger.info("Observer DB does not yet have TRIP_ISSUES table; creating it.")
            TripIssues.create_table()
        else:
            self._logger.info("Observer DB has TRIP_ISSUES table.")

        # View models, one each for the two tables in TripErrorReportsScreen.
        # Load them on entry into screen if user, program, or valid trips have changed.
        self._trip_error_reports_view_model = TripErrorReportsModel()
        self._trip_issues_view_model = TripIssuesModel()

    def _load_trip_issues_view_model(self):
        if not self._current_trip_id:
            self._logger.info("No current trip specified, so not loading trip issues.")
            self._trip_issues_view_model.clear()
            return

        self._logger.info(f"Loading issues for Trip {self._current_trip_id}.")

        self._trip_issues_view_model.clear()

        issues, _ = TripChecksOptecsManager.get_issues_from_last_ter_run(
                self._current_trip_id, self._logger)

        if not issues:
            self._logger.info("No TER issues for this trip.")
            self._trip_issues_view_model.clear()
            return

        # FIELD-2101: Hide debriefer_only TERs if not a debriefer
        is_debriefer = ObserverDBUtil.get_current_debriefer_mode()
        debriefer_checks = TripChecksOptecsManager.get_debriefer_checks()

        for issue in issues:
            trip_check_id = issue.trip_check.trip_check
            if not is_debriefer and trip_check_id in debriefer_checks:
                self._logger.debug(f"Hiding debriefer TER {trip_check_id}")
                continue
            else:
                self._trip_issues_view_model.add_trip_issue(issue)  # TODO: speed up by group append.

        self._logger.info(f"Loading {len(issues)} TER issues for Trip {self._current_trip_id}.")

    def _load_trip_error_reports_view_model(self):
        """
        The view model for the table of trip error reports
        for current user and current program.

        :return: None
        """
        if not self._current_user_id:
            self._logger.info("No current user specified, so not loading trip error reports.")
            return

        if not self._current_program_id:
            self._logger.info("No current program specified, so not loading trip error reports.")

        self._trip_error_reports_view_model.clear()

        # Get all the current user's trips, or if in debriefer mode, get all users' trips
        debriefer_mode = ObserverDBUtil.get_current_debriefer_mode()
        self._logger.info(f'Debriefer mode = {debriefer_mode}.')
        checkable_trips = ObserverTrip.get_user_valid_trips(debriefer_mode=debriefer_mode)
        completed_trip_ids = ObserverDBSyncController.get_completed_trip_ids()
        if checkable_trips is None:
            self._logger.info("No checkable trips")
        else:
            for checkable_trip in checkable_trips:
                try:
                    if not checkable_trip.vessel or not checkable_trip.vessel.vessel_name:
                        self._logger.debug(f"Skipping Trip ID {checkable_trip.trip} because no vessel name.")
                        continue
                except Vessels.DoesNotExist:
                    self._logger.debug(f"Skipping Trip ID {checkable_trip.trip} because no vessel name.")
                    continue

                trip_dict = {
                    'trip': checkable_trip.trip,
                    'program': checkable_trip.program.program_name,
                    'vessel': checkable_trip.vessel.vessel_name,
                    'created_by': checkable_trip.created_by,
                    'is_completed': checkable_trip.trip in completed_trip_ids
                }

                issues, last_run_date = TripChecksOptecsManager.get_issues_from_last_ter_run(
                        checkable_trip.trip, self._logger)
                if not issues:  # TER not yet run, or last run was without error
                    error_free_run_date: str = ErrorFreeRunTracker.lookup(
                            checkable_trip.trip, self._logger)
                    if  error_free_run_date:
                        trip_dict['n_errors'] = 'No errors'
                        trip_dict['last_run_date'] = error_free_run_date
                    else:
                        trip_dict['n_errors'] = None
                        trip_dict['last_run_date'] = None
                else:
                    trip_dict['n_errors'] = len(issues)
                    trip_dict['last_run_date'] = last_run_date

                self._trip_error_reports_view_model.add_trip_ter(trip_dict)

            self._logger.info("Loaded list of checkable trips.")

    @pyqtProperty(QVariant, notify=unusedSignal)
    def tripIssuesViewModel(self):
        return self._trip_issues_view_model

    # noinspection PyPep8Naming
    @pyqtProperty(QVariant, notify=unusedSignal)
    def tripErrorReportsViewModel(self):
        return self._trip_error_reports_view_model

    @pyqtProperty(int, notify=unusedSignal)
    def currentTripId(self):
        return self._current_trip_id if self._current_trip_id else -1

    @currentTripId.setter
    def currentTripId(self, new_trip_id):
        self._current_trip_id = new_trip_id
        self._load_trip_issues_view_model()

    @pyqtProperty(int, notify=unusedSignal)
    def currentTripChecksCount(self):
        return TripChecksOptecsManager.get_trip_checks_count()

    @pyqtSlot(name="tripChecksAreEvaluated", result=bool)
    def trip_checks_are_evaluated(self):
        """
        The GUI should call this method, and if it returns false, evaluate_trip_checks() as well
        before calling run_checks_from_error_reports_screen.
        :return:
        """
        return TripChecksOptecsManager.trip_checks_have_been_evaluated_for_use_in_optecs(self._logger)

    @pyqtSlot(name="evaluateTripChecks")
    def evaluate_trip_checks(self):
        """
        If trip checks haven't been evaluated, the GUI should call this method before requesting a Trip Error Report.
        This dependency on the GUI was introduced because the evaluation takes about 15 seconds
        and the GUI can present the user with the option to cancel the operation.
        :return:
        """
        if not self.trip_checks_are_evaluated():
            TripChecksOptecsManager.evaluate(self._logger)

    @pyqtSlot(QVariant, name='runChecksOnTrip')
    def run_checks_from_error_reports_screen(self, trip_id):
        """
        Called from the Error Report screen. Uses instance's user id. Updates Error Report's view models.
        Runs trip error checks on a background thread.
        Any DB operation must be less than database.timeout.
        Break up long DB operations into smaller chunks, broken up by a call to sleep(0.01).
        Be resilient to the UI thread taking more than database.timeout time - catch BusyError.
        TODO: Eventually give up after N BusyErrors? (For now, open-ended retry).

        Assumes that the GUI has checked that the trip checks are ready to be run;
        i.e., their ability to run on OPTECS to a SQLite database has been evaluated.
        Raise exception if not the case.

        :param trip_id: 
        :return: None
        """

        if not self.trip_checks_are_evaluated():
            raise ObserverErrorReportException("Trip checks have not evaluated for use on OPTECS")
        self._logger.info("Trip checks ready to run (have been evaluated).")

        current_user_id = ObserverDBUtil.get_current_user_id()
        self._thread_TER = ThreadTER()
        if not ThreadTER.run_in_progress:
            self._thread_TER.cancel_requested_signal.connect(self._handle_cancel_signal, Qt.QueuedConnection)
            self._thread_TER.done_signal.connect(self._handle_done_signal, Qt.QueuedConnection)
            self._thread_TER.check_chunk_completed_signal.connect(
                    self._handle_check_chunk_completed_signal, Qt.QueuedConnection)

            # Clear possible flag that last run was error-free.
            ErrorFreeRunTracker.remove(trip_id, self._logger)

            self._thread_TER.run_TER(trip_id, current_user_id, self._logger)
            self._logger.info("TER requested - will run in background.")
        else:
            self._logger.info("TER request denied - TER run already in progress.")

    def _handle_cancel_signal(self):
        self._logger.info("Received TER CANCEL signal.")
        # ThreadTER is terminated on Done signal, not here.
        self.terRunCanceled.emit()

    def _give_WAL_checkpoint_a_chance_to_complete(self):
        """
        This is not elegant, but waiting a fraction of a second before handling the end of a TER
        run appears to reduce the chance of a WAL checkpoint causing a hang by starting
        in the midst of wrapping up a TER run.

        :return: None
        """
        time.sleep(0.3)

    def _handle_done_signal(self, run_date):
        self._give_WAL_checkpoint_a_chance_to_complete()
        self._logger.info(f"Received TER DONE signal (run date={run_date}).")
        if ThreadTER.cancel_requested:
            self._logger.debug("ThreadTER background run is done - canceled, not completed. " +
                               "Not sending UI Done signal.")
        else:
            issues, _ = TripChecksOptecsManager.get_issues_from_last_ter_run(
                    self._current_trip_id, self._logger)
            # If run was error free, save that.
            if not issues:
                ErrorFreeRunTracker.add(self._current_trip_id, run_date, self._logger)

            # View Model Updates:
            # Run date and number of errors may change with report run. Re-load the trip list view model
            self._load_trip_error_reports_view_model()

            # Re-load the issues view model.
            self._load_trip_issues_view_model()

            self.terRunCompleted.emit()

        if self._thread_TER:
            # Convention: run method in ThreadTER is sleeping, waiting to be terminated.
            # By this point, ThreadTER is done (done is emitted just before sleep),
            # as are other signals (chunk or cancel). End this instance of ThreadTER.
            self._thread_TER.terminate()
            self._thread_TER = None
            self._logger.debug("Thread TER ended on Done signal.")
        else:
            self._logger.warning("Thread TER unexpectedly already gone - no need to terminate.")

    def _handle_check_chunk_completed_signal(self, n_checks_completed, chunk_size):
        self._logger.info("Received TER check chunk signal.")
        self.terCheckChunkCompleted.emit(n_checks_completed, chunk_size)

    @pyqtSlot(name='cancelChecksOnTrip')
    def cancel_checks_from_error_reports_screen(self):
        if ThreadTER.run_in_progress:
            self._logger.info("Received TER CANCEL signal and passed on to TER thread.")
            self._thread_TER.cancel()

    @pyqtSlot(name="youAreUp")
    def you_are_up(self):
        """
        Called by ObserverSM.qml when context switches to Trip Errors screen.
        :return: None
        """
        self._logger.info("Screen is active.")
        reload_view_models = False
        if self._current_user_id != ObserverDBUtil.get_current_user_id():
            self._logger.info("Change in User ID detected on entry to this screen.")
            self._current_user_id = ObserverDBUtil.get_current_user_id()
            reload_view_models = True
        if self._current_program_id != ObserverDBUtil.get_current_program_id():
            self._logger.info("Change in User's Program ID detected on entry to this screen.")
            self._current_program_id = ObserverDBUtil.get_current_program_id()
            reload_view_models = True
        if self._current_trip_id != ObserverDBUtil.get_current_trip_id():
            self._logger.info("Change in Current Trip ID detected on entry to this screen.")
            self._current_trip_id = ObserverDBUtil.get_current_trip_id()
            reload_view_models = True
        report_trip_id_set = self._current_user_valid_trip_ids \
                if bool(self._current_user_valid_trip_ids) else set()
        system_trip_id_set = ObserverTrip.get_user_valid_trip_ids() \
                if bool(ObserverTrip.get_user_valid_trip_ids()) else set()
        if report_trip_id_set != system_trip_id_set:
            self._logger.info("Change in User's list of valid trips detected on entry to this screen.")
            self._current_user_valid_trip_ids = system_trip_id_set
            reload_view_models = True
        if self._current_debriefer_mode != ObserverDBUtil.get_current_debriefer_mode():
            self._logger.info("Change in debriefer mode detected on entry to this screen.")
            self._current_debriefer_mode = ObserverDBUtil.get_current_debriefer_mode()
            reload_view_models = True

        if reload_view_models:
            self._logger.info("Reloading view models for tables on Error Reports screen.")
            self._load_trip_error_reports_view_model()
            self._load_trip_issues_view_model()
        else:
            self._logger.info("No changes to user, program, or trips since last entry.")


class PlSqlToSqlTranslator:
    """
    NOT YET USED
    """

    def __init__(self, logger):
        self._logger = logger

    def translate(self, trip_check_id: int, plsql_in: str) -> str:
        """ Oracle PL SQL in, SQLite SQL out

        Fix-up of Oracle SQL for SQLite SQL.
        Does NOT replace query parameter values (":trip_id") with value - that's done elsewhere.

        Notes on query format:
            All appear to follow the form
                INSERT INTO TRIP_ISSUES (<field>, ...)
                SELECT [DISTINCT] <db_value_or_paramter_or_literal>, ...
                FROM <table_as_prefix>, ...
                WHERE t.trip_id = :trip_id [AND comparison] ...
        Wrinkles
            SELECT values

                macros
                    to_char()
                    length()
                    decode()

            WHERE clause
                (+) is LEFT OUTER JOIN or RIGHT OUTER JOIN
                Example:
                    FROM Table1, Table2
                    WHERE (Table1.PrimaryKey = Table2.ForeignKey(+))

                    translates to:

                    FROM Table1
                        LEFT OUTER JOIN Table2 ON (Table1.PrimaryKey = Table2.ForeignKey)

        """
        # For time being, just return the PL SQL
        if '(+)' in plsql_in:
            # self._logger.warning(f"TRIP CHECK {trip_check_id} contains Oracle outer join syntax (+).")
            pass
        if 'OUTER JOIN' in plsql_in:
            # self._logger.info(f"Good news: TRIP CHECK {trip_check_id} contains SQL std OUTER JOIN syntax.")
            pass
        return plsql_in
