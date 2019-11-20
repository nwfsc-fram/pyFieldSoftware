__author__ = 'Todd.Hay'
# -----------------------------------------------------------------------------
# Name:        Settings.py
# Purpose:     Global settings
#
# Author:      Todd Hay <todd.hay@noaa.gov>
#
# Created:     Dec 12, 2016
# License:     MIT
# ------------------------------------------------------------------------------

import time

from PyQt5.QtCore import pyqtProperty, QObject, pyqtSignal, pyqtSlot, QVariant, QThread
from py.trawl_analyzer.TrawlAnalyzerDB import TrawlAnalyzerDB
# from py.trawl_analyzer.CommonFunctions import CommonFunctions
# from py.trawl_analyzer.TrawlAnalyzerDB_model import OperationsFlattenedVw
# from py.common.FramListModel import FramListModel

import os
import logging
import unittest

from peewee import *
from playhouse.shortcuts import Proxy
from playhouse.apsw_ext import APSWDatabase

database_proxy = Proxy()
wheelhouse_db_proxy = Proxy()
sensors_db_proxy = Proxy()
backdeck_db_proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


class WheelhouseModel(Model):
    class Meta:
        database = wheelhouse_db_proxy


class SensorsModel(Model):
    class Meta:
        database = sensors_db_proxy


class BackdeckModel(Model):
    class Meta:
        database = backdeck_db_proxy


class Settings(QObject):
    """
    Handles Trawl Backdeck settings and related database interactions
    """
    # onPrinterChanged = pyqtSignal()
    # printerChanged = pyqtSignal()
    # pingStatusReceived = pyqtSignal(str, bool, arguments=['message', 'success'])
    loggedInStatusChanged = pyqtSignal()
    passwordFailed = pyqtSignal()
    yearChanged = pyqtSignal()
    vesselChanged = pyqtSignal()
    haulChanged = pyqtSignal()
    wheelhouseDbChanged = pyqtSignal()
    sensorsDbChanged = pyqtSignal()
    backdeckDbChanged = pyqtSignal()
    modeChanged = pyqtSignal()
    statusBarMessageChanged = pyqtSignal()
    isLoadingChanged = pyqtSignal()
    scanFilesChanged = pyqtSignal()

    def __init__(self, app=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app

        self._host = 'nwcdbp24.nwfsc.noaa.gov'
        self._port = 5433
        self._database_name = 'fram'
        self._database = None
        self._connection = None
        self.mode = "Prod"

        self._backdeck_database = None

        self._database_proxy = database_proxy

        self._wheelhouse_proxy = wheelhouse_db_proxy
        self._sensors_proxy = sensors_db_proxy
        self._backdeck_proxy = backdeck_db_proxy

        self._year = None
        self._vessel = None
        self._haul = None

        self._logged_in_status = False

        self._get_credentials()

        self._load_management_files_thread = QThread()
        self._load_management_files_worker = None

        self._status_bar_msg = ""

        self._scan_files = False
        self._is_loading = False

    @pyqtProperty(bool, notify=scanFilesChanged)
    def scanFiles(self):
        """
        Method to return the self._scan_files variable
        :return:
        """
        return self._scan_files

    @scanFiles.setter
    def scanFiles(self, value):
        """
        Method to set the self._scan_files variable
        :param value:
        :return:
        """
        if not isinstance(value, bool):
            logging.error(f"trying to set the self._scan_files variable, but it is not a bool: {value}")
            return

        self._scan_files = value
        self.scanFilesChanged.emit()

        logging.info(f"scanFiles = {self._scan_files}")

    @pyqtProperty(bool, notify=isLoadingChanged)
    def isLoading(self):
        """
        Method to keep track of whether data is being load or not.  If it is, disable changing of various items such
        as vessel, year, etc.
        :return:
        """
        return self._is_loading

    @isLoading.setter
    def isLoading(self, value):
        """
        Method to set the _is_loading variable
        :param value:
        :return:
        """
        if not isinstance(value, bool):
            return

        self._is_loading = value
        self.isLoadingChanged.emit()

    def _get_credentials(self):
        """
        Testing method to auto-fill credentials
        :return:
        """
        self._username = ""
        self._password = ""

        path = os.path.expanduser("~/Desktop/credential.txt")
        if os.path.exists(path):
            file = open(path)
            self._username = file.readline().strip("\r\n")
            self._password = file.readline().strip("\r\n")
            file.close()

    @pyqtProperty(str, notify=passwordFailed)
    def password(self):
        """
        Return a password
        :return:
        """
        return self._password

    @pyqtProperty(str, notify=passwordFailed)
    def username(self):
        """
        Return a username
        :return:
        """
        return self._username

    @pyqtSlot(str, str)
    def login(self, user, password):
        """
        Method to login to the Postgresql database
        :param user: str - the user
        :param password: str - the password
        :return:
        """
        try:
            self._username = user

            self._database = PostgresqlDatabase(self._database_name,
                                            user=self._username,
                                            password=password,
                                            host=self._host,
                                            port=self._port)
                                            # autorollback=True)
            self._connection = self._database.connect()
            self._database_proxy.initialize(self._database)

            logging.info(f"db closed? = {self._database.is_closed()}")

            self.loadFileManagementModels()

            self.loggedInStatus = True

        except Exception as ex:
            if self._connection:
                self._database.close()
                self._connection = None
            logging.info(f'Error logging in: {ex}')
            self.loggedInStatus = False

            if "password authentication failed" in str(ex) or \
                    ("FATAL:  role" in str(ex) and "does not exist" in str(ex)):
                self.passwordFailed.emit()

    @pyqtSlot()
    def logout(self):
        """
        Method to logout of the Postgresql database
        :return:
        """
        try:
            result = self._database.close()
            # TODO Todd Hay - result returns None, as opposed to returning False per the docs, why?
            logging.info(f"connection was closed: {result} >> db = {self._database}")
            self._connection = None
            self.loggedInStatus = False

            logging.info(f"db closed? = {self._database.is_closed()}")  #  returns false, why?

        except Exception as ex:
            pass

    @pyqtProperty(bool, notify=loggedInStatusChanged)
    def loggedInStatus(self):
        """
        Method that returns the loggedInStatus of the user.
        This keeps track of whether the user has established
        a valid connection the Postgresql database
        :return:
        """
        return self._logged_in_status

    @loggedInStatus.setter
    def loggedInStatus(self, value):
        """
        Setting the self._logged_in_status value
        :param value:
        :return:
        """

        if not isinstance(value, bool):
            return

        self._logged_in_status = value
        self.loggedInStatusChanged.emit()

    @pyqtProperty(str, notify=yearChanged)
    def year(self):
        """
        Method to return the self._year variable
        :return:
        """
        return self._year

    @year.setter
    def year(self, value):
        """
        Method to set the year variable.  This is used for keeping track of what year was
        chosen for uploading/QA/QCing the survey data
        :param value: str
        :return:
        """
        if not isinstance(value, str):
            return

        self._year = value
        self.yearChanged.emit()

    @pyqtProperty(str, notify=vesselChanged)
    def vessel(self):
        """
        Method to return the self._vessel variable
        :return:
        """
        return self._vessel

    @vessel.setter
    def vessel(self, value):
        """
        Method to set the vessel variable
        :param value: str
        :return:
        """
        if not isinstance(value, str):
            return

        self._vessel = value
        self.vesselChanged.emit()

    @pyqtProperty(QVariant, notify=haulChanged)
    def haul(self):
        """
        Method to return the currently selected haul
        """
        return self._haul

    @haul.setter
    def haul(self, value):
        """
        Method to set the self._haul value
        :param value:
        :return:
        """
        self._haul = value
        self.haulChanged.emit()

    @pyqtProperty(str, notify=statusBarMessageChanged)
    def statusBarMessage(self):
        """
        Message for returning the self._status_bar_msg
        :return:
        """
        return self._status_bar_msg

    @statusBarMessage.setter
    def statusBarMessage(self, value):
        """
        Method use to set the self._status_bar_msg.  This object is used to control the message of the overall window
        status bar
        :param value:
        :return:
        """
        if not isinstance(value, str):
            return

        self._status_bar_msg = value
        self.statusBarMessageChanged.emit()

    @pyqtProperty(str, notify=modeChanged)
    def mode(self):
        """
        Method to return the mode of the application, which is either set to test or real
        :return:
        """
        return self._mode

    @mode.setter
    def mode(self, value):
        """
        Method to set the mode of the operation
        :param value:
        :return:
        """
        if value not in ["Dev", "Stage", "Prod"]:
            return

        # Change the FRAM_CENTRAL database connection settings
        if value == "Dev":
            self._database_name = "framdev"
            self._port = 5432
        elif value == "Stage":
            self._database_name = "framstg"
            self._port = 5433
        elif value == "Prod":
            self._database_name = "fram"
            self._port = 5433

        self._mode = value

        logging.info(f"mode = {self._mode}, db = {self._database_name}, port = {self._port}")

        self.logout()

        self.modeChanged.emit()

    @pyqtProperty(QVariant, notify=wheelhouseDbChanged)
    def wheelhouseProxy(self):
        """
        Method to return the self._wheelhouse_model
        :return:
        """
        return self._wheelhouse_proxy

    def set_wheelhouse_proxy(self, db_file):
        """
        Method to to set the value of self._wheelhouse_proxy.  This is used for attaching to a
        wheelhouse database for interrogating it to populate fram_central tables such as operations, operations_files_mtx,
        etc.
        :return:
        """
        if db_file is None or db_file == "":
            self._wheelhouse_proxy.initialize("")
            self.wheelhouseDbChanged.emit()
            return

        if not isinstance(db_file, str):
            return

        database = SqliteDatabase(db_file, **{})
        self._wheelhouse_proxy.initialize(database)
        self.wheelhouseDbChanged.emit()

    @pyqtProperty(QVariant, notify=sensorsDbChanged)
    def sensorsProxy(self):
        """
        Method to return the self._sensors_proxy.
        :return:
        """
        return self._sensors_proxy

    def set_sensors_proxy(self, db_file):
        """
        Method to set the value of self._sensors_proxy
        :param db:
        :return:
        """
        if db_file is None or db_file == "":
            self._sensors_proxy.initialize("")
            self.sensorsDbChanged.emit()
            return

        if not isinstance(db_file, str):
            return

        try:
            # database = SqliteDatabase(db_file, **{})
            database = APSWDatabase(db_file, **{})
            # database = APSWDatabase(db_file, timeout=5000)   # Sets the setbusytimeout keyword
            self._sensors_proxy.initialize(database)
            self.sensorsDbChanged.emit()
        except Exception as ex:
            logging.info('Error setting the sensor db proxy: {0} > {1}'.format(db_file, ex))
            self._sensors_proxy.initialize("")
            self.sensorsDbChanged.emit()

    @pyqtProperty(QVariant, notify=backdeckDbChanged)
    def backdeckProxy(self):
        """
        Method to return self._backdeck_proxy
        :return:
        """
        return self._backdeck_proxy

    def set_backdeck_proxy(self, db_file):
        """
        Methohd to set the value of self._backdeck_proxy
        :param db_file:
        :return:
        """
        if db_file is None or db_file == "":
            self._backdeck_proxy.initialize("")
            self.backdeckDbChanged.emit()
            return

        if not isinstance(db_file, str):
            return

        self._backdeck_database = SqliteDatabase(db_file, **{})
        self._backdeck_proxy.initialize(self._backdeck_database)

        # database = SqliteDatabase(db_file, **{})
        # self._backdeck_proxy.initialize(database)
        self.backdeckDbChanged.emit()

    @pyqtSlot()
    def loadFileManagementModels(self):
        """
        Method called once a user has successfully logged in that populates the three TableViews on the
        FileManagementScreen and the single TableView on the DataCompletenessScreen
        :return:
        """

        # kwargs = {"app": self._app, "year": self._year, "vessel": self._vessel}
        # self._load_management_files_worker = LoadFilesWorker(kwargs=kwargs)
        # self._load_management_files_worker.moveToThread(self._load_management_files_thread)
        # self._load_management_files_worker.loadStatus.connect(self._load_status_received)
        # self._load_management_files_thread.started.connect(self._load_management_files_worker.run)
        # self._load_management_files_thread.start()
        #
        # return

        if not self._scan_files:
            return

        logging.info(f"start populating the file management screen, interacts a lot with LOOKUPS")
        self._app.file_management.wheelhouseModel.populate_model()
        logging.info(f"finished wheelhouse")
        self._app.file_management.backdeckModel.populate_model()
        logging.info(f"finished backdeck")
        self._app.file_management.sensorsModel.populate_model()
        logging.info(f"finished sensors")

        self._app.data_completeness.dataCheckModel.populate_model()
        logging.info(f"finished dataCheck")

    def _load_status_received(self, status, msg):
        """
        Method called from the LoadFilesWorkers thread with information about the status of loading the files
        to populate the tables on the FileManagementScreen
        :return:
        """
        logging.info('status, msg: {0}, {1}'.format(status, msg))
        if status:
            logging.info('populating...')
            self._app.file_management.wheelhouseModel.populate_model()
            self._app.file_management.backdeckModel.populate_model()
            self._app.file_management.sensorsModel.populate_model()

        if self._load_management_files_thread.isRunning():
            self._load_management_files_thread.quit()


class LoadFilesWorker(QThread):

    loadStatus = pyqtSignal(bool, str)

    def __init__(self, args=(), kwargs=None):
        super().__init__()

        self._is_running = False
        self._app = kwargs["app"]
        self._year = kwargs["year"]
        self._vessel = kwargs["vessel"]

    def run(self):
        self._is_running = True
        status, msg = self.load_records()
        self.loadStatus.emit(status, msg)

    def load_records(self):
        """
        Method called by run.  This actually populates the TableViews in the FileManagementScreen and the
        DataCompletenessScreen.  It is run as a background though so as to be UI responsive when a user  changes
        the year / vessel comboboxes
        :return:
        """

        status = True
        msg = ""

        self._app.file_management.wheelhouseModel.retrieve_items()
        self._app.file_management.backdeckModel.retrieve_items()
        self._app.file_management.sensorsModel.retrieve_items()

        # self._app.data_completeness.dataCheckModel.populate_model()

        msg = "Finished processing records"
        logging.info('finishehd retrieving')
        return status, msg


class TestSettings(unittest.TestCase):
    """
    Test basic SQLite connectivity, properties
    TODO{wsmith} Need to enhance these tests
    """
    def setUp(self):
        db = TrawlAnalyzerDB()
        self.s = Settings(db=db)

    def test_settings(self):

        logging.info('settings: ' + str(self.s._settings))

    def test_printer(self):

        logging.info('printer: ' + self.s._printer)

if __name__ == '__main__':
    unittest.main()

