# -----------------------------------------------------------------------------
# Name:        ObserverSOAP.py
# Purpose:     OPTECS SOAP support for db syncing, using zeep
# http://docs.python-zeep.org/en/master/
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Dec 20, 2016
# License:     MIT
#
# Install notes:
#   * Python 3.6: use requirements.txt for zeep, lxml (refer to older versions of this file for python 3.5)
#
#   FIXED with new tomcat endpoint wsdl, no longer required patch to Lib/site-packages/zeep/xsd/schema.py:
#   In def _get_instance, (zeep 0.27.0: line 374, zeep 2.4.0: line 498)
#   (after try:)
#   if qname.localname == 'arrayList':
#     return self._types['{http://www.oracle.com/webservices/internal/literal}list']

#
#
# ------------------------------------------------------------------------------

# python -mzeep https://www.webapps.nwfsc.noaa.gov/obclientsyncdev21/ObclientsyncWSSoapHttpPort?WSDL#
import csv
import re
import sys
import math
import hashlib
import textwrap
import logging
import logging.config
import socket
import io
import unittest

import arrow
import keyring
import zeep
from zeep.wsse.username import UsernameToken
from zeep.wsdl.utils import etree_to_string

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtCore import QVariant
from PyQt5.QtCore import pyqtProperty
from PyQt5.QtCore import pyqtSignal

from apsw import SQLError

from py.observer.ObserverDBUtil import ObserverDBUtil
from py.observer.ObserverDBBaseModel import database
from py.observer.ObserverDBModels import Users, fn, Settings

# Enable DEBUG for dump of SOAP header
logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'zeep.transports': {
            'level': 'INFO',
            'propagate': True,
            'handlers': ['console'],
        },
    }
})


class ObserverSoap(QObject):
    mode_urls = {
        'ifq': ObserverDBUtil.get_setting('ifq_wsdl_url'),  # IFQ (Prod)
        'ifqdev': ObserverDBUtil.get_setting('ifqdev_wsdl_url'),  # IFQDEV (Test)
        'ifqadmin': ObserverDBUtil.get_setting('ifqadmin_wsdl_url')  # IFQADMIN (Test)
    }

    observer_mode = ObserverDBUtil.get_setting('optecs_mode')
    wsdl = mode_urls[observer_mode]

    obs_username = 'obsclient'
    oracle_salt_keyname = 'optecs_oracle_pwsalt'
    default_transaction_id = ObserverDBUtil.get_setting('last_db_transaction', 83775)
    obs_version = ObserverDBUtil.get_setting('seahag_version', 2019)

    obs_credentials_namespace = 'OPTECS v1'  # for stored salt and pw
    skip_pw_error = True

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)

        self.client = \
            zeep.Client(
                wsdl=self.wsdl,
                wsse=UsernameToken(username=self.obs_username, password=self._get_dbsync_pw(), ))

    def _get_dbsync_pw(self):
        # PW for Java API sync
        pw = keyring.get_password(self.obs_credentials_namespace, self.obs_username)
        if not pw:
            logging.error('Password for observer client sync not set.')
            logging.error('Please run set_optecs_sync_pw.py (not in src control) to set it.')
            if not self.skip_pw_error:
                sys.exit(-1)
        return pw

    @staticmethod
    def get_oracle_salt():
        # Salt for oracle password
        salt_value = keyring.get_password(ObserverSoap.obs_credentials_namespace, ObserverSoap.oracle_salt_keyname)
        if not salt_value:
            raise Exception('Salt for password hashing not set. '
                            'Please run set_optecs_sync_pw.py (not in src control) to set it.')
        return salt_value

    @staticmethod
    def hash_pw(username, pw):
        """
        This routine is adapted from SDM_CUSTOM_BUILT_NEW_SHA1 in Oracle
        @param username: first+last - should be uppercase (e.g. WILLSMITH)
        @param pw: password to encode
        @return: custom SHA1 hash that matches how the Oracle DB currently stores passwords.
        """
        if not username or not pw:
            raise ValueError('Invalid/blank username or pw.')
        username = username.upper()

        salt_value = ObserverSoap.get_oracle_salt().encode('utf-8')
        pw_hash_len = len(username) + len(pw)
        padding = 10 * math.ceil(pw_hash_len / 8)
        pw_hash_len = padding - pw_hash_len + 40
        if pw_hash_len > len(salt_value):
            pw_hash_len = len(salt_value)

        salt_substr = salt_value[:pw_hash_len]

        hash_obj = hashlib.sha1(salt_substr)
        hashed_salt = hash_obj.hexdigest()

        final_pw = str(hashed_salt).upper() + pw + username  # composite hashed salt + pw + username
        hash_obj = hashlib.sha1(final_pw.encode('utf-8'))
        pw_hashed = hash_obj.hexdigest().upper()

        return pw_hashed

    @staticmethod
    def get_filename(tablename, trip_id, user_id, date_time=None):
        """
        Returns filename in the format Table#Export Version_UserID_date_time.csv
        e.g. CATCHES#20148_1760_10SEP2014_1356.csv
        @param tablename: TRIPS
        @param trip_id: Export version? Internal temp trip ID
        @param user_id: USER_ID
        @param date_time: arrow object
        @return: Table#Export Version_UserID_date_time.csv
        """
        if not date_time:
            date_time = arrow.now()
        formatted_dt = date_time.format('DDMMMYYYY_HHmm').upper()
        return '{table}#{exp}_{uid}_{dt}.csv'.format(table=tablename.upper(),
                                                     exp=trip_id,
                                                     uid=user_id,
                                                     dt=formatted_dt)

    def _get_user_id(self, username):
        try:
            user_check = Users.get((fn.Lower(Users.first_name.concat(Users.last_name))) == username.lower())
            self._logger.debug('ID {} found for user {}'.format(user_check.user, username))
            return user_check.user
        except Users.DoesNotExist:
            self._logger.warning('Name not found: {}'.format(username))

    def action_upload(self, username, hashed_pw, filename, unenc_data):
        """
        Upload binary blob to web service for parsing
        @param username: user for auth
        @param hashed_pw: hashed pw for auth
        @param filename:  filename from get_filename
        @param unenc_data: UN-encoded data of csv table data (base64 encoding is automatic.)
        @return: is_successful, new_trip_id (if TRIPS, else None)
        """
        # http://impl.webservices.obofflinesync.sdm.nwfsc.nmfs.noaa.gov//uploadClientData1
        self._logger.info('Upload client scripts to virtual filename {}'.format(filename))
        user_id = self._get_user_id(username)
        if not user_id:
            return False
        laptop_name = ObserverDBUtil.get_data_source()

        # soap_etree = self.client.create_message(self.client.service, 'uploadClientData1', userName=username,
        #                                                password=hashed_pw,
        #                                                fileName=filename,
        #                                                data=unenc_data,
        #                                                version=self.obs_version,
        #                                                var1=user_id,
        #                                                var2=laptop_name,
        #                                                var3='',
        #                                                var4='')
        #
        # soap_msg = etree_to_string(soap_etree).decode()
        # self._logger.info(f'XML Message: {soap_msg}')

        # with self.client.settings(raw_response=True):
        result = self.client.service.uploadClientData1(userName=username,
                                                       password=hashed_pw,
                                                       fileName=filename,
                                                       data=unenc_data,
                                                       version=self.obs_version,
                                                       var1=user_id,
                                                       var2=laptop_name,
                                                       var3='',
                                                       var4=''
                                                       )

        new_trip_id = self._get_trip_id_from_result(result)
        is_success = 'SUCCESS' in result
        return is_success, new_trip_id

    def _get_trip_id_from_result(self, result_string):
        # '<br>SUCCESS:  Parsed 1 TRIPS row.<div style="font-size:2em;color:#990000">
        # Your Online Trip ID is <b>30135</b> </div>.
        # <br><div style="font-size:2em;color:#006600">Online transfer complete.</div>'

        if not result_string or 'TRIPS' not in result_string:
            return None
        m = re.search(r"Your Online Trip ID is <b>(?P<trip_id>[0-9]*)", result_string)
        trip_id = int(m.group('trip_id'))
        self._logger.debug(f'Parsed new TRIP ID from result string, got {trip_id}')
        return trip_id

    def action_download(self, transaction_id, username=None, hashed_pw=None):
        """
        Download transactions from APPLIED_TRANSACTIONS.
        @param transaction_id: from DB
        @param username: defaults to Admin
        @param hashed_pw: defaults to Admin
        @return:
        """
        # Defaults to admin user, which is how current offline system works.
        # http://impl.webservices.obofflinesync.sdm.nwfsc.nmfs.noaa.gov//updateClientScripts
        hardcoded_admin_id = 1155
        self._logger.info(f'Downloading client scripts from transaction ID {transaction_id}')
        if not username or not hashed_pw:
            user_q = Users.get(Users.user == hardcoded_admin_id)
            username = user_q.first_name + user_q.last_name
            hashed_pw = user_q.password

        # soap_etree = self.client.create_message(self.client.service, 'updateClientScripts', userName=username,
        #                                                  password=hashed_pw,
        #                                                  transaction_id=transaction_id,
        #                                                  version=self.obs_version,
        #                                                  var1='',
        #                                                  var2='',
        #                                                  var3='',
        #                                                  var4='')
        #
        # soap_msg = etree_to_string(soap_etree).decode()
        # self._logger.info(f'XML Message: {soap_msg}')

        results = self.client.service.updateClientScripts(userName=username,
                                                          password=hashed_pw,
                                                          transaction_id=transaction_id,
                                                          version=self.obs_version,
                                                          var1='',
                                                          var2='',
                                                          var3='',
                                                          var4=''
                                                          )

       # Sort results by transaction_id
        if results:
            sorted_results = sorted(results, key=lambda k: k['transaction_id'])
            return sorted_results
        else:
            return None
        # return None

    def _check_user_pw_enc(self, username):
        """
        Check if PASSWORD_ENCRYPTED flag is set for user.
        @return: True if PASSWORD_ENCRYPTED and user exists, False otherwise
        """
        try:
            user_check = Users.get((fn.Lower(Users.first_name.concat(Users.last_name))) == username.lower())
            return user_check.password_encrypted == 1
        except Users.DoesNotExist:
            self._logger.warning('Name not found: {}'.format(username))
            return False

    def perform_sync(self):
        """
        @return: sync_result: bool, sync_output: str
        """
        return self.update_client_pull()

    def retrieve_updates(self):
        """
        Only does a pull, not a full sync
        @return: sync_result: bool, sync_output: str
        """
        return self.update_client_pull()

    def update_client_pull(self):
        """
        Currently uses admin user to pull down data
        @return: bool, string: Success (T/F), Message describing the result
        """
        success_count, fail_count = 0, 0
        try:
            ddl_results = self.action_download(self.db_sync_transaction_id)
            if ddl_results:
                success_count, fail_count = self.perform_ddl(ddl_results)
                self._logger.info('Successes: {}, Failures: {}'.format(success_count, fail_count))
        except Exception as e:
            error_msg = 'DB Sync error: {}'.format(e)
            return False, error_msg

        ObserverDBUtil.db_fix_empty_string_nulls(self._logger)
        final_result = f'Update Successful.\nRetrieved {success_count} updates from DB.\n' \
                       f'Ignored: {fail_count}'
        return True, final_result, success_count

    def perform_ddl(self, ddl_results):
        """
        Perform DDL on database
        @param ddl_results: List of dicts from CLOB
        @return: successes, errors (counts)
        """
        expected_transaction_types = {'U', 'I'}
        success_count = 0
        error_count = 0
        last_transaction_id = None
        for ddl in ddl_results:
            transaction = ddl['transaction_ddl'].decode('utf-8', errors='ignore').rstrip('\0')  # axe \x00
            if ddl['transaction_type'] in expected_transaction_types:
                transaction = self.remove_sql_to_date(transaction)
                self._logger.info(f'TXid {ddl.transaction_id}: {transaction[:15]}...')
                self._logger.debug(f'Performing: {transaction}')
                database.set_autocommit(True)
                try:
                    database.execute_sql(str(transaction))
                    success_count += 1
                    last_transaction_id = ddl['transaction_id']
                except SQLError as e:
                    self._logger.error(e)
                    error_count += 1
                except Exception as e:  # might be reinserting the same record etc
                    self._logger.error(e)
                    error_count += 1
            else:
                self._logger.warning('Unexpected transaction type {}'.format(ddl['transaction_type']))
                self._logger.warning(ddl['transaction_ddl'])

        if last_transaction_id:
            self.db_sync_transaction_id = last_transaction_id

        return success_count, error_count

    @staticmethod
    def remove_sql_to_date(transaction: str) -> str:
        """
        Remove all occurrences of oracle's TO_DATE(x, y) function from transaction
        @param transaction: DDL with possible TO_DATE(x,y) function (one or more)
        @return: transaction x without TO_DATE(...) (remove y)
        """
        find_str = 'TO_DATE('
        while transaction.find(find_str) >= 0:
            start_idx = transaction.find(find_str)

            comma_idx = transaction.find(',', start_idx)
            if comma_idx == -1:  # malformed
                return transaction

            end_idx = transaction.find(')', start_idx)
            if end_idx == -1:  # malformed
                return transaction

            # Remove TO_DATE( x, y ) -> x
            before_to_date = transaction[:start_idx]
            date_param = transaction[start_idx + len(find_str):comma_idx]
            after_to_date = transaction[end_idx + 1:]
            transaction = before_to_date + date_param + after_to_date

        return transaction

    @property
    def db_sync_transaction_id(self):
        # TODO Temporarily always get all transactions. For production, comment out line below.
        # return self.default_transaction_id

        try:
            last_id = Settings.get(Settings.parameter == 'last_db_transaction')
            return last_id.value
        except Settings.DoesNotExist:
            return self.default_transaction_id

    @db_sync_transaction_id.setter
    def db_sync_transaction_id(self, transaction_id):
        try:
            last_id = Settings.get(Settings.parameter == 'last_db_transaction')
            last_id.value = transaction_id
            last_id.save()
        except Settings.DoesNotExist:
            new_setting = Settings.create(parameter='last_db_transaction',
                                          value=transaction_id)
            new_setting.save()

    def getCSV(self, db_table_name):
        """
        NOTE: Obsolete, see DBSyncController
        Does a raw SQL query and pipes to CSV
        @param db_table_name: table name, e.g. "TRIPS"
        @return: string of csv representation
        """
        output = io.StringIO()
        table_query = database.execute_sql('SELECT * FROM {}'.format(db_table_name))

        try:
            fields = [h[0] for h in table_query.getdescription()]

            writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(fields)  # Header
            for row in table_query:
                writer.writerow(row)
            return output.getvalue()
        except Exception as e:
            self._logger.warning(e)
            return None


class TestObserverSOAP(unittest.TestCase):
    def test_variety_of_to_dates_and_not_to_dates(self):
        test_cases = (
            ("Not_2_date", "Not_2_date"),
            ("TO_DATE('1-Jun-2017', 'd-mmm-yyyy')", "'1-Jun-2017'"),
            ("TO_DATE('', 'd-mmm-yyyy')", "''"),
            ("TO_DATE('','DD-MON-YY HH24:MI:SS')", "''"),
            # Handle multiple occurrences of TO_DATE
            ("""UPDATE TRIP_CHECKS  SET TRIP_CHECK_GROUP_ID = 41, CHECK_CODE = 104100, CHECK_MESSAGE = 'Permit Number is missing or does not start with ''BT''', CHECK_DESCRIPTION = '', CHECK_TYPE = 'E', CHECK_SQL = 'INSERT INTO TRIP_ISSUES (TRIP_CHECK_ID,TRIP_ID, ERROR_ITEM, ERROR_VALUE, CREATED_BY)        SELECT :TRIP_CHECK_ID, T.TRIP_ID,  ''Certificate #'' ITEM, TC.CERTIFICATE_NUMBER VALUE,:created_by        FROM trips t LEFT OUTER JOIN trip_certificates tc ON T.TRIP_ID = TC.TRIP_ID    WHERE t.trip_id = :trip_id  AND t.fishery IN (''4'') AND (TC.CERTIFICATE_NUMBER IS NULL OR TC.CERTIFICATE_NUMBER NOT LIKE ''%BT%'' OR length(TC.CERTIFICATE_NUMBER) <> 6) AND TRUNC(t.return_date)>=TO_DATE(''01/01/2015'',''MM/DD/YYYY'')', CHECK_MODULE = '', VALUE_COLUMN = '', PROGRAM_ID = null, FISHERY_ID = null, FIXED_GEAR_TYPE = null, TRAWL_GEAR_TYPE = null, ALLOW_ACK = 'N', STATUS = 1, MODIFIED_BY = '', MODIFIED_DATE = TO_DATE('','DD-MON-YY HH24:MI:SS') WHERE  TRIP_CHECK_ID  = 2602 ;
            """, """UPDATE TRIP_CHECKS  SET TRIP_CHECK_GROUP_ID = 41, CHECK_CODE = 104100, CHECK_MESSAGE = 'Permit Number is missing or does not start with ''BT''', CHECK_DESCRIPTION = '', CHECK_TYPE = 'E', CHECK_SQL = 'INSERT INTO TRIP_ISSUES (TRIP_CHECK_ID,TRIP_ID, ERROR_ITEM, ERROR_VALUE, CREATED_BY)        SELECT :TRIP_CHECK_ID, T.TRIP_ID,  ''Certificate #'' ITEM, TC.CERTIFICATE_NUMBER VALUE,:created_by        FROM trips t LEFT OUTER JOIN trip_certificates tc ON T.TRIP_ID = TC.TRIP_ID    WHERE t.trip_id = :trip_id  AND t.fishery IN (''4'') AND (TC.CERTIFICATE_NUMBER IS NULL OR TC.CERTIFICATE_NUMBER NOT LIKE ''%BT%'' OR length(TC.CERTIFICATE_NUMBER) <> 6) AND TRUNC(t.return_date)>=''01/01/2015''', CHECK_MODULE = '', VALUE_COLUMN = '', PROGRAM_ID = null, FISHERY_ID = null, FIXED_GEAR_TYPE = null, TRAWL_GEAR_TYPE = null, ALLOW_ACK = 'N', STATUS = 1, MODIFIED_BY = '', MODIFIED_DATE = '' WHERE  TRIP_CHECK_ID  = 2602 ;
            """)
        )
        for test_input, expected_output in test_cases:
            actual_output = ObserverSoap.remove_sql_to_date(test_input)
            self.assertEqual(expected_output, actual_output)
