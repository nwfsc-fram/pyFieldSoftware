__author__ = 'Will.Smith'
# -----------------------------------------------------------------------------
# Name:        Settings.py

# ------------------------------------------------------------------------------

import time

from PyQt5.QtCore import pyqtProperty, QObject, QVariant, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication
from dateutil import parser
# from py.trawl.TrawlBackdeckDB import TrawlBackdeckDB
# import win32print
# from win32print import EnumPrinters, PRINTER_ENUM_NAME, PRINTER_ENUM_LOCAL
from py.common.FramUtil import FramUtil
from py.common.FramListModel import FramListModel
import logging
import unittest
import re

# from py.observer.ObserverData import ObserverData

class SettingsModel(FramListModel):
    """
    Model used in SettingsScreen TableView to expose settings params
    """
    def __init__(self):
        super().__init__()
        self.add_role_name(name="settingsId")
        self.add_role_name(name="parameter")
        self.add_role_name(name="type")
        self.add_role_name(name="value")
        self.add_role_name(name="is_active")

class Settings(QObject):
    """
    Handles Survey Backdeck settings and related database interactions
    """
    # onPrinterChanged = pyqtSignal()
    printerChanged = pyqtSignal()
    pingStatusReceived = pyqtSignal(str, bool, arguments=['message', 'success'])
    rebootRequired = pyqtSignal(str, arguments=['param'])

    def __init__(self, app=None, db=None):
        super().__init__()
        self._logger = logging.getLogger(__name__)

        # TODO (todd.hay) Tie to the SETTINGS table values
        self._db = db
        self._app = app
        self._settings = self._initialize_settings()
        self._model = SettingsModel()
        self._build_model()

        try:
            self._wheelhouse_ip_address = self._settings["Wheelhouse IP Address"]
            self._test_wheelhouse_ip_address = self._settings["Test Wheelhouse IP Address"]
            self._wheelhouse_drive_letter = self._settings["Wheelhouse Drive Letter"]
            self._wheelhouse_rpc_server_port = self._settings["Wheelhouse RpcServer Port"]
            self._most_recent_hauls_count = self._settings["Most Recent Hauls Count"] if self._settings["Most Recent Hauls Count"] else 20
            self._current_printer = None
        except Exception as ex:
            logging.info('Failed getting settings: {0}'.format(ex))

        self._ping_thread = QThread()
        self._ping_worker = None

        # logging.info('settings: ' + str(self._settings))

    def _initialize_settings(self):
        sql = "SELECT * FROM SETTINGS WHERE IS_ACTIVE = 'True';"
        settings = {}
        for s in self._db.execute(query=sql):
            settings[s[1]] = s[3]

        return settings

    @pyqtProperty(QVariant)
    def model(self):
        return self._model

    def _build_model(self):
        """
        Load settings model using SETTINGS table
        :return: None
        """
        sql = '''
                select
                            SETTINGS_ID
                            ,PARAMETER
                            ,VALUE
                FROM        SETTINGS
                WHERE       IS_ACTIVE = 'True'
            '''
        for row in self._db.execute(query=sql):
            self._model.appendItem({'settingsId': row[0], 'parameter': row[1], 'value': row[2]})

    @pyqtSlot(QVariant, QVariant, name='updateDbParameter')
    def updateDbParameter(self, parameter, value):
        """
        PyQt wrapper for _update_db_parameter private method
        if value has changed, update in DB and model
        if param changing is IP address, signal for reboot (this value is loaded on startup)
        :param parameter: str; SETTINGS parameter value
        :param value: str; value to set parameter in SETTINGS
        :return: None
        """
        role_index = self._model.get_item_index('parameter', parameter)  # get row num in model
        cur_value = self._model.get(role_index)['value']  # get existing model value
        logging.info(f"Updating DB param {parameter} from {cur_value} to {value}")
        if cur_value != value:
            self._update_db_parameter(parameter, value)
            self._model.setProperty(role_index, 'value', value)
            if parameter == 'FPC IP Address':
                self.rebootRequired.emit(parameter)

    def _update_db_parameter(self, parameter, value):

        sql = "UPDATE SETTINGS SET VALUE = ? WHERE PARAMETER = ?;"
        params = [value, parameter]

        try:
            self._db.execute(query=sql, parameters=params)
        except Exception as ex:
            return False
        return True

    @pyqtSlot(result=str)
    def ping_test(self, debug=False):
        kwargs = {"wheelhouse_ip": self.wheelhouseIpAddress}

        self._ping_worker = PingWorker(kwargs=kwargs)
        self._ping_worker.moveToThread(self._ping_thread)
        self._ping_worker.pingStatus.connect(self._ping_status_received)
        self._ping_thread.started.connect(self._ping_worker.run)
        self._ping_thread.start()

    def _ping_status_received(self, message, success):
        # logging.info('Ping status: {0} {1}'.format(message, success))
        self.pingStatusReceived.emit(message, success)
        self._ping_thread.quit()

    @pyqtProperty(QVariant, notify=printerChanged)
    def currentPrinter(self):
        return self._current_printer

    @currentPrinter.setter
    def currentPrinter(self, value):

        if not isinstance(value, str):
            return
        self._current_printer = value
        self.printerChanged.emit()

    @pyqtProperty(int)
    def mostRecentHaulsCount(self):
        return self._most_recent_hauls_count

    @mostRecentHaulsCount.setter
    def mostRecentHaulsCount(self, value):
        if isinstance(value, int):
            self._most_recent_hauls_count = value
        else:
            self._most_recent_hauls_count = 20

    @pyqtProperty(str, notify=printerChanged)
    def printer1(self):
        return self._settings["Printer1"]

    @printer1.setter
    def printer1(self, value):

        # Update the local value
        self._settings["Printer1"] = value

        # Update the SETTINGS Table in the database
        self._update_db_parameter(parameter="Printer1", value=value)

    @pyqtProperty(str, notify=printerChanged)
    def printer2(self):
        return self._settings["Printer2"]

    @printer2.setter
    def printer2(self, value):

        # Update the local value
        self._settings["Printer2"] = value

        # Update the SETTINGS Table in the database
        self._update_db_parameter(parameter="Printer2", value=value)

    @pyqtProperty(int)
    def wheelhouseRpcServerPort(self):

        try:
            return int(self._wheelhouse_rpc_server_port)
        except Exception as ex:
            return

    @pyqtProperty(str)
    def wheelhouseIpAddress(self):
        return self._wheelhouse_ip_address

    @pyqtProperty(str)
    def testWheelhouseIpAddress(self):
        return self._test_wheelhouse_ip_address

    @pyqtProperty(str)
    def wheelhouseDriveLetter(self):
        return self._wheelhouse_drive_letter

    @pyqtProperty(str)
    def currentTime(self):
        return time.strftime("%m/%d/%Y %H:%M")

    @pyqtProperty(bool)
    def run_tests(self):
        """
        Used to run basic UI automation tests
        """
        return False

class PingWorker(QObject):
    """
    Class to run ping tests for Victor in a thread
    """
    pingStatus = pyqtSignal(str, bool)

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self._is_running = False
        self.wheelhouseIpAddress = kwargs['wheelhouse_ip']
        self.result = {'message': '', 'success': False}

    def run(self):
        self._is_running = True
        result, success = self.ping_test(wheelhouse_ip=self.wheelhouseIpAddress)
        self.pingStatus.emit(result, success)

    def ping_test(self, wheelhouse_ip, debug=False):
        """
        Pings wheelhouse, printer, access point, moxa
        :return: String with test results, success
        """
        overall_status = True
        results = ''
        try:

            dbs = [('Wheelhouse', wheelhouse_ip)]
            ip_octets = wheelhouse_ip.split('.')

            # Make Printer MOXA IP
            ip_octets[3] = '70'
            dbs.append(('Printer MOXA', '.'.join(ip_octets)))

            # Make Access Point IP
            ip_octets[3] = '254'
            dbs.append(('Access Point', '.'.join(ip_octets)))

            # Make Comm Box MOXA IP
            ip_octets[3] = '253'
            dbs.append(('Comm Box MOXA', '.'.join(ip_octets)))

            for ip in dbs:
                output = FramUtil.ping_response(ip[1], debug=debug)
                if isinstance(output, bytes):
                    output = output.decode('utf-8')
                if "reply from" in output.lower():
                    ip_status = True
                else:
                    ip_status = False
                    overall_status = False
                results += '{0} IP: {1} Ping Result: {2}\n'.format(ip[0], ip[1], 'OK' if ip_status else 'FAIL')
        except Exception as e:
            logging.error('Could not perform ping test, {0}'.format(e))
        return results, overall_status

class TestSettings(unittest.TestCase):
    """
    Test basic SQLite connectivity, properties
    TODO{wsmith} Need to enhance these tests
    """
    def setUp(self):
        # db = TrawlBackdeckDB()
        # self.s = Settings(db=db)
        pass

    def test_settings(self):
        pass
        # logging.info('settings: ' + str(self.s._settings))

    def test_printer(self):
        pass
        # logging.info('printer: ' + self.s._printer)
    #
    # def proptest_bool(self, testproperty):
    #     testval = testproperty
    #     self.assertIsNotNone(testval)
    #     testproperty = not testval
    #     self.assertEqual(testproperty, not testval)
    #     testproperty = testval
    #     self.assertEqual(testproperty, testval)
    #
    # def test_property_catchshare(self):
    #     self.proptest_bool(self.testdata.is_catchshare)
    #
    # def test_property_geartype(self):
    #     self.proptest_bool(self.testdata.is_geartype_trawl)

if __name__ == '__main__':
    unittest.main()

