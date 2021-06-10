# -----------------------------------------------------------------------------
# Name:        ObserverDBUtil.py
# Purpose:     Utility functions for peewee based DB
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     March 18, 2016
# License:     MIT
# ------------------------------------------------------------------------------

import arrow
import hashlib
import json
import logging
import time
import filecmp
import os
import socket
import shutil
import re

from decimal import *
from typing import Any, Dict, List, Type, Union

from apsw import BusyError
from peewee import Model, BigIntegerField, BooleanField, DoubleField, FloatField, ForeignKeyField, IntegerField, \
    PrimaryKeyField, SmallIntegerField, TextField, TimestampField
from py.observer.ObserverDBBaseModel import BaseModel, database
from py.observer.ObserverDBModels import Settings, Programs, TripChecks, SpeciesCompositionItems
from playhouse.apsw_ext import APSWDatabase
from playhouse.shortcuts import dict_to_model
from playhouse.test_utils import test_database

import unittest


class ObserverDBUtil:
    default_dateformat = 'MM/DD/YYYY HH:mm'  # Updated for arrow
    javascript_dateformat = 'YYYY-MM-DDTHH:mm:ss'  # For QML interactions
    oracle_date_format = 'DD-MMM-YYYY'  # 01-MAY-2017

    def __init__(self):
        pass

    @staticmethod
    def db_load_setting(parameter):
        try:
            return Settings.get(Settings.parameter == parameter).value
        except Settings.DoesNotExist as e:
            logging.info('DB Setting does not exist: ' + parameter)
        return None

    @staticmethod
    def db_save_setting(parameter, value):
        """
        Save Setting to DB.

        :param parameter: PARAMETER to match
        :param value: Value to save as Str
        :return: True if saved
        """
        id_query = Settings.select().where(Settings.parameter == parameter)
        if not id_query.exists():
            Settings.create(parameter=parameter)
        setting = id_query.get()
        setting.value = str(value)

        # Handle a BusyError attempting to write to Settings by retrying up to five times.
        n_retries = 0
        max_retries = 5
        while True:
            try:
                setting.save()
                break
            except BusyError as be:
                n_retries += 1
                if n_retries > max_retries:
                    raise be
                sleep_time_secs = 0.1 * n_retries
                time.sleep(sleep_time_secs)
                # Don't log at INFO level or above - these are typically written to
                # OPTECS_LOG_MESSAGES table, adding to database contention.
                logging.debug(f'Trip.save() Try#{n_retries} failed w/BusyError. " +'
                              f'Sleeping {sleep_time_secs} seconds before retrying.')
        logging.debug('Save ' + parameter + ' -> ' + str(value))
        return True

    @staticmethod
    def db_load_setting_as_json(parameter: str) -> Union[List, Dict[str, Any]]:
        """
        Load a Settings table entry that is a JSON string, returning a Python list or dictionary.
        :param parameter:
        :return: Python list of values or dictionary with (immutable) string key and any value type.
        """
        structure_as_json_string = ObserverDBUtil.db_load_setting(parameter)
        if structure_as_json_string is None:
            return None
        return json.loads(structure_as_json_string)

    @staticmethod
    def db_save_setting_as_json(parameter: str, value: Union[List, Dict]) -> None:
        """
        Save a python list in the value field of an entry of Settings table as a JSON string.

        Note: json.dumps will convert non-string keys into a string (python dict keys
        must be immutable).

        From https://stackoverflow.com/questions/1450957/pythons-json-module-converts-int-dictionary-keys-to-strings:
        "In Python ... the keys to a mapping (dictionary) are object references. In Python
        they must be immutable types, or they must be objects which implement a __hash__ method"

        (Brought up because first key in dictionary held in JSON string was Trip ID (integer))

        :param parameter:
        :param value:
        :return:
        """
        return ObserverDBUtil.db_save_setting(parameter, json.dumps(value))

    @staticmethod
    def db_fix_empty_string_nulls(logger: logging.Logger) -> None:
        # FIELD-1261 If we have bad data in VESSELS ('' instead of NULL) fix that:
        database.execute_sql(
            "update VESSELS set REGISTERED_LENGTH = NULL where REGISTERED_LENGTH = ''")

        # TRIP_CHECKS may have empty strings in the numeric field MODIFIED_BY. Possibly other fields as well.
        # Convert empty strings in all numeric fields to null or zero, depending on whether field is nullable.
        ObserverDBUtil.db_coerce_empty_strings_in_number_fields(TripChecks, logger)

    @staticmethod
    def db_coerce_empty_strings_in_number_fields(db_table: Type[BaseModel], logger: logging.Logger) -> Dict[str, int]:
        """
        Oracle and SQLite both allow a number field to have a value of empty string.
        Peewee, however, does not: it throws a ValueError exception.
        
        Avoid peewee ValueError exceptions by coercing in db_table any empty string in any number field
        to null (if field is nullable) or 0 (if field is not nullable).
        
        :param db_table: 
        :param logger: 
        :return: a dictionary of field_name: empty_string_count
        """
        numeric_field_types = (
            IntegerField,
            FloatField,
            BooleanField,
            DoubleField,
            BigIntegerField,
            SmallIntegerField,
            TimestampField
        )
        db = db_table._meta.database
        numeric_fields = []
        for field in db_table._meta.declared_fields:
            if type(field) in numeric_field_types and \
                    not (isinstance(field, PrimaryKeyField) or isinstance(field, ForeignKeyField)):
                numeric_fields.append(field)

        numeric_field_empty_string_cnts = {}
        fields_to_coerce = []
        for numeric_field in numeric_fields:
            # Do a SELECT to determine which columns have any empty strings. Not strictly necessary - could just do the
            # update, but a log of counts of empty string values by field could be useful for tracking its frequency.
            # Use execute_sql to avoid peewee's problem handling an empty string in a numeric field.
            select_sql_query = f"SELECT {numeric_field.db_column} FROM {db_table._meta.db_table} " + \
                               f"WHERE {numeric_field.db_column} = ''"
            # logger.debug(select_sql_query)
            cursor = db.execute_sql(select_sql_query)
            n_empty_string_values = len(cursor.fetchall())
            numeric_field_empty_string_cnts[numeric_field.db_column] = n_empty_string_values
            if n_empty_string_values > 0:
                fields_to_coerce.append(numeric_field)

        for field_to_coerce in fields_to_coerce:
            coerced_value = "NULL" if field_to_coerce.null else "0"
            update_sql = f"UPDATE {db_table._meta.db_table} set {field_to_coerce.db_column} = {coerced_value} " + \
                         f"WHERE {field_to_coerce.db_column} = ''"
            logger.debug(update_sql)
            db.execute_sql(update_sql)

        # Log the results. Also return the results for possible use by the caller.
        if len(fields_to_coerce) == 0:
            logger.info(f"Found no occurrences of empty strings in numeric fields in Table {db_table._meta.db_table}.")
        else:
            logger.info(
                f"Found {len(fields_to_coerce)} field(s) with at least one empty string value. Counts by field:")
            for key, value in numeric_field_empty_string_cnts.items():
                logger.info(f"\t{key}: {value}")
        return numeric_field_empty_string_cnts

    @staticmethod
    def db_load_save_setting_as_json(parameter: str, default_value: Union[List, Dict]) -> Union[List, Dict]:
        """
        If present in Settings table, return the entry with key = 'parameter' as a Python list
        or dict (whichever of the two data structures the json defines).

        If not present, add an entry with the default_value and return default_value.

        :param parameter: string - key value
        :param default_value: List or Dict
        :return: List or Dict
        """
        value_in_settings = ObserverDBUtil.db_load_setting_as_json(parameter)
        if value_in_settings is not None:
            return value_in_settings

        ObserverDBUtil.db_save_setting_as_json(parameter, default_value)
        return default_value

    @staticmethod
    def get_arrow_datestr(date_format=default_dateformat):
        """
        Get current time in string format. If oracle_date_format, 3-character month will be uppercase
        @param date_format: arrow date format
        @return: Arrow formatted datestring
        """
        result = arrow.now().format(date_format)
        return result if date_format != ObserverDBUtil.oracle_date_format else result.upper()

    @staticmethod
    def get_external_drive_letters():
        """
        Enumerate drive letters for thumb drive. Win32 only
        Adapted from https://stackoverflow.com/questions/827371/\
        is-there-a-way-to-list-all-the-available-drive-letters-in-python
        @return: None or list of non-C drives in format 'D:\\', ...
        """
        if os.name == 'nt':
            import win32api
            drives = win32api.GetLogicalDriveStrings()
            drives = drives.split('\000')[:-1]
            if 'C:\\' in drives:
                drives.remove('C:\\')
            return drives
        else:  # TODO 'posix', 'mac' etc
            return None

    @staticmethod
    def get_current_catch_ratio_from_notes(cur_notes):
        if not cur_notes:
            return None
        ratio_re = re.compile('Ratio=([\S_]+)')
        match = ratio_re.search(cur_notes)
        ratio = None
        if match:
            ratio = float(match.group(1))
        return ratio

    @staticmethod
    def datetime_to_str(indate):
        """
        Updated for arrow
        @param indate:
        @return:
        """
        return indate.format(ObserverDBUtil.default_dateformat)

    @staticmethod
    def str_to_datetime(datestr):
        return arrow.get(datestr, ObserverDBUtil.default_dateformat)

    @staticmethod
    def convert_jscript_datetime(datestr):
        """
        Given 2017-01-24T16:30:00 local time, convert to arrow UTC
        @param datestr: javascript format datetime
        @return:
        """
        if datestr:
            arrow_time = arrow.get(datestr, ObserverDBUtil.javascript_dateformat)
            return arrow_time.format(ObserverDBUtil.default_dateformat)

    @staticmethod
    def convert_arrow_to_jscript_datetime(datestr):
        """
        Given standard datestr, basically just add a T
        @param datestr: arrow format datestr
        @return:
        """
        if datestr:
            arrow_time = arrow.get(datestr, ObserverDBUtil.default_dateformat)
            return arrow_time.format(ObserverDBUtil.javascript_dateformat)

    @staticmethod
    def convert_datestr(datestr, existing_fmt, desired_fmt):
        """
        pass in datestr, parse into datetime, then reformat back to string
        :param datestr: str
        :param existing_fmt: str (e.g. default_dateformat)
        :param desired_fmt: str (e.g. oracle_date_format)
        :return: str (new format)
        """
        return arrow.get(datestr, existing_fmt).format(desired_fmt)

    @staticmethod
    def log_peewee_model_dependencies(logger, dependencies, context_message=None):
        """
        Log the non-null fields of records in the list of dependencies.
        http://docs.peewee-orm.com/en/latest/peewee/api.html#Model.dependencies

        :param logger: where to logk
        :param dependencies: from Peewee model_instance.dependencies()
        :context_message: optional message to include in first log line.
        :return: None
        """
        logger.info('Peewee dependency information. Context: {}:'.format(
            context_message if not None else "(None supplied)"))
        dependency_found = False
        for (query, fk) in dependencies:
            model = fk.model_class
            query_result = model.select().where(query).execute()
            if query_result:
                dependency_found = True
                try:
                    for row in query_result:
                        ObserverDBUtil.log_peewee_model_instance(logger, row)

                except Exception as e:
                    logger.error(e)
        if not dependency_found:
            logger.info('No dependencies.')

    @staticmethod
    def log_peewee_model_instance(logger, db_record, context_message=None):
        if not isinstance(db_record, BaseModel):
            logger.error("Expected db_record to be an Observer BaseModel type.")
            return

        logger.info("Non-null Fields of Record from Table {}:".format(db_record._meta.db_table))
        if context_message is not None:
            logger.info("\t(Context: {})".format(context_message))
        for field_name, field_value in db_record._data.items():
            if field_value is not None:
                logger.info("\t\t{}: {}".format(field_name, field_value))

    @staticmethod
    def load_peewee_model_from_json_file(peewee_model: Type[BaseModel],
                                         json_filepath: str,
                                         logger: logging.Logger) -> int:
        """
        Load a Navicat-created JSON dump of a SQL table into Observer DB using the peewee model for that table.

        Format of a Navicat JSON file:
        {
            "RECORDS":[
                {
                    "FIELD_1_NAME" : "row1_field1_value",
                    ...
                    "FIELD_N_NAME": 'row1_fieldM_value"
                },
                ...
                {
                    "FIELD_1_NAME": "rowN_field1_value",
                    ...
                    "FIELD_N_NAME": "rowN_fieldM_value"
                }
            ]
        }

        The basic technique is to use the Playhouse extension, dict_to_model, to load the dictionary values into
        a peewee record.

        The only wrinkle: Navicat field names are database columns. Playhouse expects Peewee field names.

        Limitation: Expects an empty destination table. This isn't required, just simplest implementation
        for what's currently needed.

        :return: number of model instances (rows) loaded into peewee_model (table)
        """

        # Column names in Navicat JSON are the database column names (uppercase with underscore separator).
        # The corresponding field names in Peewee are pythonic variable names.
        # Prepare a map from DB column names to Peewee field names.
        dbcol_to_field = {}
        for field in peewee_model._meta.declared_fields:
            dbcol_to_field[field.db_column] = field.name

        query = peewee_model.select()
        nrows = query.count()
        if nrows > 0:
            logger.info(f'Table {peewee_model._meta.db_table} is NOT empty (contains {nrows} rows). ' +
                        f'NOT reloading from JSON.')
            return nrows
        else:
            logger.debug(f'Destination table {peewee_model._meta.db_table} is empty. Proceeding with load.')

        with open(json_filepath) as data_file:
            data = json.load(data_file)
            json_records_with_dbcolumn_names = data['RECORDS']

            # Load each JSON record into destination table.
            for json_record in json_records_with_dbcolumn_names:

                model_instance_dict = {}

                # Convert database column names (e.g. TRIP_CHECK_ID) to peewee field name (e.g. trip_check)
                for dbcol_name in json_record.keys():
                    field_name = dbcol_to_field[dbcol_name]
                    model_instance_dict[field_name] = json_record[dbcol_name]

                peewee_model_instance = dict_to_model(peewee_model, model_instance_dict)
                peewee_model_instance.save(force_insert=True)

            nrows = peewee_model.select().count()
            logger.info(f'Loaded {nrows} rows into Table {peewee_model._meta.db_table} from JSON file {json_filepath}')

        return nrows

    @staticmethod
    def checksum_peewee_model(peewee_model: Type[BaseModel], logger: logging.Logger) -> str:
        """
        Can help answer the question: have the contents of a SQLite table changed at all?
        
        Unlike some other DBMSs like SQL Server, SQLite does not provide a CHECKSUM function.
        
        Performs a SHA1 checksum over every field of every row of the peewee table.
        
        The plan:
            1.  Create a hash for each row by hashing a concatenation of hashes for each field.
                Each field is treated as string.
            2.  Create a hash for the table by hashing the concatenation of hashes for each row.
            
        Justification for technique:
            From http://crypto.stackexchange.com/questions/10058/how-to-hash-a-list-of-multiple-items
        
            "[I]nstead of just encoding the inputs into a single string and hashing it, it's also possible to modify the
            hashing method to directly support multiple inputs. One general way to do that is to use a hash list,
            in which every input value is first hashed separately, and the resulting hashes (which have a fixed length,
            and can thus be safely concatenated) are then concatenated and hashed together."
            
        :param peewee_model: The table to checksum. Must have a primary key field
                (the case for all Peewee-based tables).
        :param logger: 
        :return: 
        """
        start_time = time.time()

        # Oracle and SQLite allow a value of empty string in numeric fields. Peewee takes exception: ValueError.
        # Empty string values could be added to TRIP_CHECKS by a DB Sync download.
        # Before running a checksum, convert any empty string values in a numeric field to null or zero,
        # depending on whether the field is nullable or not.
        empty_string_counts = ObserverDBUtil.db_coerce_empty_strings_in_number_fields(peewee_model, logger)
        n_flds_empty_str = len([x for x in empty_string_counts if empty_string_counts[x] > 0])
        logger.info(f"Found {'no' if n_flds_empty_str == 0 else n_flds_empty_str} fields with empty strings.")

        table_name = peewee_model._meta.name
        n_fields = len(peewee_model._meta.fields)
        primary_key_field = peewee_model._meta.primary_key
        # There will always be a primary key when using Peewee. But just in case:
        if not primary_key_field:
            raise Exception("checksum_peewee_model requires a primary key field by which to sort.")

        all_rec_query = peewee_model.select().order_by(primary_key_field)
        n_rows = all_rec_query.count()
        row_sha1_concatenations = ""
        for record in all_rec_query:
            field_sha1_concatenations = ""
            for name, value in record._data.items():
                # print(f'{name}={value}')
                field_sha1_concatenations += hashlib.sha1(str(value).encode()).hexdigest()

            row_sha1_concatenations += hashlib.sha1(field_sha1_concatenations.encode()).hexdigest()

        table_sha1 = hashlib.sha1(row_sha1_concatenations.encode()).hexdigest()
        logger.info(f"SHA1 checksum for Table {table_name} of {n_rows} rows by {n_fields} fields: {table_sha1}.")
        logger.info(f"\tTime to calculate table's SHA1: {time.time() - start_time:.2f} seconds.")
        return table_sha1

    @staticmethod
    def get_setting(setting_name, fallback_value=None):
        """
        Load setting from SETTINGS
        @param setting_name: e.g. 'current_user_id'
        @param fallback_value: value to return if value not found
        @return: value or fallback_value or None
        """
        try:
            return Settings.get(Settings.parameter == setting_name).value
        except Settings.DoesNotExist:
            return fallback_value

    @staticmethod
    def get_or_set_setting(setting_name, default_value):
        """
        Load setting from SETTINGS. If not found, then set to default_value
        @param setting_name: e.g. 'current_user_id'
        @param default_value: value to set if setting not found
        @return: found value or default_value
        """
        try:
            return Settings.get(Settings.parameter == setting_name).value
        except Settings.DoesNotExist:
            ObserverDBUtil.db_save_setting(setting_name, default_value)
            return default_value

    @staticmethod
    def clear_setting(setting_name):
        """
        Delete setting from SETTINGS
        @param setting_name: e.g. 'current_user_id'
        @return: True or None
        """
        try:
            Settings.get(Settings.parameter == setting_name).delete_instance()
            return True
        except Settings.DoesNotExist:
            return None

    @staticmethod
    def get_current_user_id():
        try:
            return int(ObserverDBUtil.get_setting('current_user_id'))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def set_current_user_id(user_id):
        try:
            ObserverDBUtil.db_save_setting('current_user_id', user_id)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_current_program_id():
        try:
            return int(ObserverDBUtil.get_setting('current_program_id'))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_current_program_name():
        try:
            program_id = int(ObserverDBUtil.get_setting('current_program_id'))
            return Programs.get(Programs.program == program_id).program_name
        except Programs.DoesNotExist:
            return None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def set_current_program_id(program_id):
        try:
            ObserverDBUtil.db_save_setting('current_program_id', program_id)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_current_fishery_id() -> int:
        try:
            return int(ObserverDBUtil.get_setting('current_fishery_id'))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def is_fixed_gear():
        return True if ObserverDBUtil.get_setting('gear_type') == 'FALSE' else False

    @staticmethod
    def set_current_fishery_id(program_id: int):
        try:
            ObserverDBUtil.db_save_setting('current_fishery_id', program_id)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def set_current_username(username):
        """
        Eventually we're probably not going to persist the last username.
        @param username: first+last
        @return:
        """
        try:
            ObserverDBUtil.db_save_setting('current_user', username)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_current_trip_id():
        try:
            # TODO: Rename Setting name from 'trip_number' to 'current_trip_id'?
            return int(ObserverDBUtil.get_setting('trip_number'))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_current_debriefer_mode() -> bool:
        try:
            debriefer_mode = ObserverDBUtil.get_setting('current_debriefer_mode', fallback_value=False)
            return debriefer_mode == 'True'
        except (TypeError, ValueError):
            return False

    @staticmethod
    def set_current_debriefer_mode(debriefer_mode: bool) -> None:
        try:
            ObserverDBUtil.db_save_setting('current_debriefer_mode', debriefer_mode)
        except (TypeError, ValueError):
            pass

    @staticmethod
    def escape_linefeeds(input_str):
        """
        Replace linefeed with <br> for future formatting, removes quotes
        @param input_str: original
        @return: string with no linefeeds
        """
        no_lfs = input_str.replace('\r', '')
        no_lfs = no_lfs.replace('\n', '<br>')
        no_lfs = no_lfs.replace('"', '')
        return no_lfs

    @staticmethod
    def get_data_source() -> str:
        return'optecs ' + socket.gethostname()

    @staticmethod
    def del_species_comp_item(comp_item_id, delete_baskets=True):
        try:
            del_item = SpeciesCompositionItems.get(SpeciesCompositionItems.species_comp_item == comp_item_id)
            ObserverDBUtil.log_peewee_model_instance(logging, del_item, 'About to delete')
            del_item.delete_instance(recursive=delete_baskets)  # delete baskets associated with this species comp id
        except SpeciesCompositionItems.DoesNotExist:
            logging.error(f'Could not delete species comp item ID {comp_item_id}')

    @staticmethod
    def round_up(val, precision='.01'):
        """
        https://stackoverflow.com/questions/56820/round-doesnt-seem-to-be-rounding-properly#56833
        function to properly round up

        TODO: replace the Decimal rounding functionality throughout the app, using this in Sets.
        TODO: replace in CountsWeights.tallyTimesAvgWeight, CountsWeights._calculate_totals...
        :return: rounded float (defaults to two points of precision)
        """
        try:
            return float(Decimal(val).quantize(Decimal(precision), rounding=ROUND_HALF_UP))
        except TypeError:
            return None

class TestObserverDBUtil(unittest.TestCase):
    """
    Note: any write/update interaction should be done with test_database...
    http://stackoverflow.com/questions/15982801/custom-sqlite-database-for-unit-tests-for-code-using-peewee-orm
    """
    test_db = APSWDatabase(':memory:')

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self._logger = logging.getLogger(__name__)

        # Shut up peewee debug and info messages. Comment out setLevel below to get them
        peewee_logger = logging.getLogger('peewee')
        peewee_logger.setLevel(logging.WARNING)

    def test_save_get_setting(self):
        with test_database(self.test_db, [Settings]):
            self.assertTrue(ObserverDBUtil.db_save_setting('TestSettingParam', '1234'))
            self.assertTrue(ObserverDBUtil.db_save_setting('TestSettingParam2', '12345'))
            self.assertTrue(ObserverDBUtil.db_save_setting('TestSettingParam', '4321'))
            retval = ObserverDBUtil.db_load_setting('TestSettingParam')
            self.assertEqual(retval, '4321')
            retval2 = ObserverDBUtil.db_load_setting('TestSettingParam2')
            self.assertEqual(retval2, '12345')

    def test_failcase(self):
        with test_database(self.test_db, [Settings]):
            retval = ObserverDBUtil.db_load_setting('TestSettingParam')
            self.assertIsNone(retval)

    def test_load_list_setting(self):
        with test_database(self.test_db, [Settings]):
            self.assertTrue(ObserverDBUtil.db_save_setting_as_json('TestSettingParam', ['1234', '4567']))
            self.assertTrue(ObserverDBUtil.db_save_setting_as_json('TestSettingParam2', [12345, 67891]))
            self.assertTrue(ObserverDBUtil.db_save_setting_as_json('TestSettingParam', ['4321', '7654']))
            retval = ObserverDBUtil.db_load_setting_as_json('TestSettingParam')
            self.assertEqual(retval, ['4321', '7654'])
            retval2 = ObserverDBUtil.db_load_setting_as_json('TestSettingParam2')
            self.assertEqual(retval2, [12345, 67891])

            # Load/Save
            test_parameter = 'TestSettingParam3'
            default_value = 'This value is not in Settings'.split(" ")
            self.assertIsNone(ObserverDBUtil.db_load_setting(test_parameter))
            actual_value = ObserverDBUtil.db_load_save_setting_as_json(test_parameter, default_value)
            self.assertEqual(default_value, actual_value)

    def test_load_dict_setting(self):
        """ Use 'list' load/save for a dictionary.
            Drawbacks:
            - non-string keys are returned as strings (immutable type required for dict key)
        """
        with test_database(self.test_db, [Settings]):
            test_dict = {1: '2017-09-16', 2: 2.0, 3.0: 3.0}
            setting_name = "trips_with_last_TER_error_free"
            self.assertTrue(ObserverDBUtil.db_save_setting_as_json(setting_name, test_dict))
            retval = ObserverDBUtil.db_load_setting_as_json(setting_name)
            expected_dict = { str(k):v for k, v in test_dict.items()}
            self.assertEqual(retval, expected_dict)

    def test_load_tuple_setting_as_json(self):
        """ Use json load/save for a tuple. Drawbacks:
            - Returned as List, not Tuple
        """
        with test_database(self.test_db, [Settings]):
            test_tuple = ('2017-09-16', '2017-09-17', 3, 4.0)
            setting_name = "tuple_of_strings"
            self.assertTrue(ObserverDBUtil.db_save_setting_as_json(setting_name, test_tuple))
            retval = ObserverDBUtil.db_load_setting_as_json(setting_name)
            self.assertEqual(retval, list(test_tuple))

    def test_datefuncs(self):
        # Create two datetime objects, convert back and forth to string, compare
        nowdate = arrow.now()
        nowdatestr = ObserverDBUtil.get_arrow_datestr()
        nowdatestr_test = ObserverDBUtil.datetime_to_str(nowdate)

        date_from_str = ObserverDBUtil.str_to_datetime(nowdatestr)
        date2_from_str = ObserverDBUtil.str_to_datetime(nowdatestr_test)
        deltat = date_from_str - date2_from_str
        # check within 1 second of each other
        self.assertLess(abs(deltat.seconds), 1)

        nowdate = ObserverDBUtil.get_arrow_datestr(date_format='DD-MMM-YYYY')
        self.assertEqual(len('00-MMM-0000'), len(nowdate))

    def test_escapelf(self):
        test_str = 'this\nline has "things" and various\nfeeds'
        new_str = ObserverDBUtil.escape_linefeeds(test_str)
        self.assertTrue('\n' not in new_str)
        self.assertTrue('<br>' in new_str)
        self.assertTrue('"' not in new_str)

    def test_checksum_peewee_model(self):
        expected_sha1 = "689327755da6658627c0f015c25796a5cdc98c0c"
        with test_database(self.test_db, [Settings]):
            # Use Settings as test data table. Seed with two rows.
            self.assertTrue(ObserverDBUtil.db_save_setting('TestSettingParam1', '1234'))
            self.assertTrue(ObserverDBUtil.db_save_setting('TestSettingParam2', '4321'))

            actual_sha1 = ObserverDBUtil.checksum_peewee_model(Settings, logging)
            self.assertEqual(expected_sha1, actual_sha1)

            # Change a digit: SHA1 should change.
            self.assertTrue(ObserverDBUtil.db_save_setting('TestSettingParam2', '4221'))
            actual_sha1 = ObserverDBUtil.checksum_peewee_model(Settings, logging)
            self.assertNotEquals(expected_sha1, actual_sha1)

            # Restore the original digit: SHA1's should match.
            self.assertTrue(ObserverDBUtil.db_save_setting('TestSettingParam2', '4321'))
            actual_sha1 = ObserverDBUtil.checksum_peewee_model(Settings, logging)
            self.assertEqual(expected_sha1, actual_sha1)

    def test_checksum_peewee_model_exception_not_possible_with_peewee(self):
        clean_test_db = APSWDatabase(':memory:')
        with test_database(clean_test_db, [NoPrimaryKeyTable]):
            self.assertTrue(NoPrimaryKeyTable.table_exists())

            ObserverDBUtil.checksum_peewee_model(NoPrimaryKeyTable, logging)

            """
            No exception. That's because:
            
            "Because we have not specified a primary key, peewee will automatically add
            an auto-incrementing integer primary key field named id."
            (http://docs.peewee-orm.com/en/latest/peewee/models.html)
            """
            peewee_default_primary_key_field_name = 'id'
            primary_key_field = NoPrimaryKeyTable._meta.primary_key
            self.assertIsNotNone(primary_key_field)
            self.assertEqual(peewee_default_primary_key_field_name, primary_key_field.name)

    def test_empty_string_coerce(self):
        with test_database(self.test_db, [TripChecks]):
            # Demonstrate peewee's problem with empty string in integer field, on a save of new record.
            expected_exception_msg = "invalid literal for int() with base 10: ''"
            try:
                test_record_1 = TripChecks(
                    allow_ack="N",
                    check_code="",  # Integer field!
                    check_message="A msg",
                    check_sql="Insert something",
                    check_type="E",
                    created_by=100,
                    created_date="12/05/2017",
                    status=0,
                    trip_check_group=456)
                test_record_1.save()
                self.fail("Should have objected to invalid literal")
            except ValueError as ve:
                self.assertEqual(expected_exception_msg, ve.args[0])

            # Demonstrate peewee's problem with empty string in integer field, on a read of a record.
            expected_exception_msg = "invalid literal for int() with base 10: ''"
            try:
                test_record_2 = TripChecks(
                    allow_ack="N",
                    check_code=0,
                    check_message="A msg",
                    check_sql="Insert something",
                    check_type="E",
                    created_by=101,
                    created_date="12/05/2017",
                    status=0,
                    trip_check_group=456)
                test_record_2.save()
                self._logger.debug(f"TRIP_CHECK_ID={test_record_2.trip_check}.")
                # Introduce an empty string in an integer string - outside of peewee model.
                ret_val = self.test_db.execute_sql(
                    f"update TRIP_CHECKS set CREATED_BY = '' where CREATED_BY = {test_record_2.created_by}")

                # Now try to access record with empty string in integer field.
                trip_check_record = TripChecks.get(TripChecks.trip_check == test_record_2.trip_check)

                self.fail("Should have objected to invalid literal")
            except ValueError as ve:
                self.assertEqual(expected_exception_msg, ve.args[0])

            # Run utility to clear empty strings from numeric fields.
            empty_field_count_dict = ObserverDBUtil.db_coerce_empty_strings_in_number_fields(TripChecks, self._logger)
            self.assertEqual(1, empty_field_count_dict["CREATED_BY"])

            # Now try to access record with formerly empty string in integer field - now should be zero.
            trip_check_record = TripChecks.get(TripChecks.trip_check == test_record_2.trip_check)
            self.assertEqual(0, trip_check_record.created_by, "Empty string in non-nullable integer field should be 0.")


class NoPrimaryKeyTable(Model):
    field1 = TextField()
    field2 = TextField()
