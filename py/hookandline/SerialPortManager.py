__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        SerialPortManager.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 11, 2016
# License:     MIT
#-------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, \
    QObject, QVariant, Qt, QThread, QMetaType
from PyQt5.QtQml import QJSValue

from py.common.FramListModel import FramListModel
import logging
from threading import Thread, Timer
from queue import Queue
from serial import Serial, SerialException
import serial
import time
from datetime import datetime, timedelta, tzinfo, timezone
import re
import os
import apsw as sqlite
import shutil
import arrow
from decimal import Decimal
from dateutil import parser
from xml.parsers.expat import ExpatError
from py.common.SerialDataParser import SerialDataParser
import unittest
from py.hookandline.HookandlineFpcDB_model import DeployedEquipment, ParsingRules
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import *


class DatabaseWorker(QObject):

    def __init__(self, sensors_db_path=None, kwargs=None):
        super().__init__()

        self._is_running = False
        self._is_writing = False   # Used to pause actual writing while the database connection is being changed
        self._active_list = 0
        self._sql =\
            """
            INSERT INTO RAW_SENTENCES (RAW_SENTENCE, DATE_TIME, DEPLOYED_EQUIPMENT_ID)
                VALUES (?, ?, ?);
            """
        self.connect_to_db(sensor_db_path=sensors_db_path)
        self._values = {0: [], 1: []}

    def connect_to_db(self, sensor_db_path=None):
        """
        Method to connect to the new sensor database file and create a connection and cursor object
        :param path:
        :return:
        """
        if sensor_db_path is None:
            logging.error("Unable to connect to the database.")
            return

        if not self._is_writing:

            # Create the database connection and cursor
            self.conn = sqlite.Connection(sensor_db_path)
            self.conn.setbusytimeout(5000)
            self.cursor = self.conn.cursor()

            self._is_writing = True

    def change_db_path(self, new_path=None):
        """
        Method to change the database path.  This happens at midnight when a new sensors database is created
        and we start writing to that new database
        :param new_path:
        :return:
        """
        if not new_path or not os.path.exists(new_path):
            logging.error(f"A valid DB path was not provided: {new_path}")
            return

        self._is_writing = False

        try:
            logging.info(f"changing database to {new_path}")
            self.cursor = None
            self.conn.close()
            self.conn = sqlite.Connection(new_path)
            self.conn.setbusytimeout(5000)
            self.cursor = self.conn.cursor()

            logging.info(f"successful")

        except Exception as ex:

            logging.error(f"Unable to reset the database path due to the following error: {ex}")

        self._is_writing = True

    def add_values(self, sentence, datetime_str, deployed_equipment_id):
        """
        Method to add data to the self._values list that is then pushed to the database
        :param sentence:
        :param datetime_str:
        :param deployed_equipment_id:
        :return:
        """
        self._values[self._active_list].append((sentence, datetime_str, deployed_equipment_id))

    def stop(self):
        """
        Method to stop the worker
        :return:
        """
        self._is_running = False

    def write(self):
        """
        Method call to actually write the data to the database.  Basically once a second, it takes all of the sentences in the
        self._values list and writes these in bulk to the SQLite database
        :return:
        """
        self._is_running = True

        while True:

            if not self._is_running:
                break


            if self._is_writing:

                if len(self._values[self._active_list]) > 0:
                    self._active_list = 0 if self._active_list == 1 else 1
                    inactive_list = 0 if self._active_list == 1 else 1

                    # logging.info(f"active: {len(self._values[self._active_list])}, {len(self._values[inactive_list])}")

                    with self.conn:
                        self.cursor.executemany(self._sql, self._values[inactive_list])
                    del self._values[inactive_list][:]

                time.sleep(1)


class SerialPortWorker(QObject):

    # portClosed = pyqtSignal(int)
    portPlayStatusChanged = pyqtSignal(str, str)
    exceptionEncountered = pyqtSignal(str, str, str, str)
    dataStatusChanged = pyqtSignal(str, str)
    dataReceived = pyqtSignal(str, str)
    dataReceivedForDatabase = pyqtSignal(str, str, int)

    def __init__(self, sensors_db_path=None, kwargs=None):
        super().__init__()

        self.set_parameters(params=kwargs)

        # TESTED
        # self.connect_to_db(sensor_db_path=sensors_db_path)

        self.ser = None

        self.is_streaming = False
        self._data_status = "red"
        self._meatball_count = 0
        self._timeout = 0.1

    def set_parameters(self, params):

        databits = {5: serial.FIVEBITS, 6: serial.SIXBITS, 7: serial.SEVENBITS, 8: serial.EIGHTBITS}
        parity = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD,
                  "Mark": serial.PARITY_MARK, "Space": serial.PARITY_SPACE}
        stopbits = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE, 2: serial.STOPBITS_TWO}
        flowcontrol = {"None": False, "Off": serial.XOFF, "On": serial.XON}

        self.com_port = params["com_port"]
        self.baud_rate = params["baud_rate"]
        self.data_bits = databits[params["data_bits"]] if params["data_bits"] in databits else serial.EIGHTBITS
        self.parity = parity[params["parity"]] if params["parity"] in parity else serial.PARITY_NONE
        self.stop_bits = stopbits[params["stop_bits"]] if params["stop_bits"] in stopbits else serial.STOPBITS_ONE
        self.flow_control = flowcontrol[params["flow_control"]] if params["flow_control"] in flowcontrol \
            else False

        self.dataStatus = params["data_status"] if "data_status" in params else "red"


        self.deployed_equipment_id = params["deployed_equipment_id"] if "deployed_equipment_id" in params else None

        """
        TODO - Todd - LineEnding - Need to think if we should be passing this in as well, or just default to this
            This is actually going to need to be a variable, as the SBE39 depth sentence looks like the
            following:

             # 22.6802,   -1.426, 24 Jun 2004, 10:02:24<CR><LF>Ó<CR><LF>

             So we'll need an ending that looks something like the following:

             \r\n.{1}\r\n
        """

        self.ending = re.compile("(\r|\n|\r\n)")
        # self.ending = re.compile("\r?\n?")

        # if self.deployed_equipment_id:
        #     self.ending = re.compile("\r?\n?")
        # else:
        #     self.ending = re.compile("(\r?\n?)")

        """
        TODO Todd - Parsing Rules - The question is what should we be writing to the database.  Currently I will remove
        all of the control characters that come along before inserting into the database.
        """

        # self.rule = params["rule"] if "rule" in params else ""

    def connect_to_db(self, sensor_db_path=None):
        """
        Method to connect to the new sensor database file and create a connection and cursor object
        :param path:
        :return:
        """
        if sensor_db_path is None:
            logging.error("Unable to connect to the database.")
            return

        # Create the database connection and cursor
        self.conn = sqlite.Connection(sensor_db_path)
        self.conn.setbusytimeout(5000)
        self.cursor = self.conn.cursor()

    @pyqtProperty(str, notify=dataStatusChanged)
    def dataStatus(self):
        return self._data_status

    @dataStatus.setter
    def dataStatus(self, value):
        self._data_status = value
        self.dataStatusChanged.emit(self.com_port, value)

    def start(self):
        self.is_streaming = True

    def stop(self):
        self.is_streaming = False

    def read(self):

        self.start()
        self.dataStatus = "red"

        # sql = """
        #     INSERT INTO ENVIRO_NET_RAW_STRINGS (RAW_STRINGS, DATE_TIME, DEPLOYED_EQUIPMENT_ID)
        #         VALUES (?, ?, ?);
        #     """
        sql = """
            INSERT INTO RAW_SENTENCES (RAW_SENTENCE, DATE_TIME, DEPLOYED_EQUIPMENT_ID)
                VALUES (?, ?, ?);
            """

        buffer = ""
        split_data = ""
        sentence = ""

        try:
            self.ser = Serial(baudrate=self.baud_rate, bytesize=self.data_bits,
                              parity=self.parity, stopbits=self.stop_bits,
                              xonxoff=self.flow_control, timeout=self._timeout)
            self.ser.port = self.com_port
            self.ser.open()

            start_time = time.clock()
            # end_time = start_time

            self.portPlayStatusChanged.emit(self.com_port, "started")

            """
            Encoding - The data coming from NMEA sentences is printable ASCII per:
            http://nmeatools.com/NMEA-Tools-Blog/PostId/24/what-makes-a-valid-nmea-sentence
            
            https://www.nmea.org/content/nmea_standards/nmea_0183_v_410.asp (not available anymore)

            Printable ASCII is defined here:
            ASCII Characters - http://www.ascii-code.com/

            Therefore we will use the ASCII decoding when we read from the serial port.

            However, the problem is that not all of our data streams are NMEA, and thus only printable ASCII.
            In particular, the Seabird 39 (SBE39) streaming data contains extended ASCII characters, i.e.
            from 128-255.  For instance, a sample SBE39 stream looks like the following:

            # 22.6802,   -1.426, 24 Jun 2004, 10:02:24<CR><LF>Ó<CR><LF>

            Notice the Ó character which is charcter # 211, or hex d3. Therefore we must use the ISO-8859-1
            standard for our encoding.  However we'll just throw away all of the characters from 128-255
            """
            self.encoding = "ISO-8859-1"
            # self.encoding = "ASCII"

            while True:

                if not self.is_streaming:
                    break

                if self.ser.in_waiting > 10000:
                    # clear the buffer if it has gotten too large
                    self.ser.reset_input_buffer()

                """
                This will apparently block until 1 byte received - but I set self._timeout=0.1 (100 milliseconds) above, so
                it will break out of this read operation after 0.1 seconds.  self._meatball_count is used to
                keep track of the 0.1s timeouts that occur.  So dividing 5 / self._timeout gives the number of iterations
                to cover 5 seconds.

                """
                buffer += self.ser.read(1).decode(self.encoding)

                """
                New logic - 20160901 - I set the timeout to be 100 msec to enable a very responsive
                UI when a user tries to start and stop a given com_port.  However in so doing this,
                I had to create explicit timeout parameters for to get the various meatball
                colors.  The logic below appears to be working fine.
                """
                if buffer == "":

                    if self.dataStatus != "red":

                        if (5 / self._timeout) <= self._meatball_count < (60 / self._timeout):

                            if self.dataStatus != "yellow":
                                self.dataStatus = "yellow"

                        elif self._meatball_count >= (60 / self._timeout):

                            self.dataStatus = "red"

                    self._meatball_count += 1

                buffer += self.ser.read(self.ser.in_waiting).decode(self.encoding)

                # Original - worked, but went to 30% of CPU in pilot plant when having 7 open serial ports
                # buffer += self.ser.read(self.ser.inWaiting()).decode("ISO-8859-1")

                # logging.info('buffer length: {0} > {1}'.format(len(buffer), buffer))

                if self.ending.search(buffer): # and len(buffer) > 0:

                    if self.deployed_equipment_id:
                        lines = self.ending.split(buffer)
                    else:
                        lines = buffer.splitlines(keepends=True)

                    # logging.info('lines: {0}, lines[-1]: {1}'.format(lines, lines[-1]))

                    if split_data != "":
                        lines[0] = split_data + lines[0]
                        split_data = ""

                    if len(lines) > 0:
                        if lines[-1][-2:] != "\r\n" and lines[-1] != "":
                        # if lines[-1] != "\r\n" and lines[-1] != "":
                            # Line split across buffers, hold on to data
                            split_data = lines[-1]
                            del lines[-1]

                    lines[:] = (x for x in lines if x not in ["", "\r", "\n", "\r\n"])
                    # lines[:] = (x for x in lines if x != "\r\n" and
                    #             x != "\r" and x != "\n" and x != "")
                    # lines = [x for x in lines if x != "\r\n" and
                    #          x != "\r" and x != "\n" and x != ""]

                    # Original logic
                    # lines = [x for x in lines if x != "\r\n" and x != ""]

                    # logging.info('lines, after merging: {0}, split_data: {1}'.format(lines, split_data))

                    for sentence in lines:

                        """
                        Clean out any control characters
                        Remove ASCII Control Characters before entering into the database
                        References:
                        ASCII Control Characters - http://ascii.cl/control-characters.htm
                        ASCII Characters - http://www.ascii-code.com/
                        ISO-8859-1 - http://en.wikipedia.org/wiki/ISO/IEC_8859-1
                        How to remove them:  http://chase-seibert.github.io/blog/2011/05/20/stripping-control-characters-in-python.html
                        Reference - ftp://ftp.unicode.org/Public/MAPPINGS/ISO8859/8859-1.TXT
                        sentence = re.sub(r"[\x01-\x1F\x7F]", "", sentence)

                        """
                        # Write the sentence to the daily sensor database file if a deployed_equipment_id exists
                        if self.deployed_equipment_id:

                            # Logic when the encoding is ISO-8859-1
                            # sentence = re.sub(r"[\x01-\x1F\x7F\x80-\x9F]", "", sentence)

                            """
                            Remove all of the control characters before writing to the database
                            Since we're using a ISO-8859-1 encoding, which supports extended ASCII from 128-255,
                            strip out those 128-255 characters as they're likely bogus.  This is to work around
                            the SBE39 data which returns characters in the 128-255 range.
                            """
                            # sentence = re.sub(r"[\x01-\x1F\x7F-\xFF]", "", sentence)

                            try:

                                # Removes only the control characters, the delete character, and undefined characters in ISO-8859-1
                                # 20191001 - Added the \x00 (NUL) and \x80-\x9F (undefined in ISO-8859-1) characters to this list as well
                                sentence = re.sub(r"[\x00-\x1F\x7F\x80-\x9F]", "", sentence)

                            except Exception as ex:

                                logging.info(f"Error removing control characters from sentence: {sentence} > {ex}")

                            if sentence not in ["", "\r", "\n", "\r\n"]:

                                # TESTING - to overcome BusyError: database is locked issue
                                self.dataReceivedForDatabase.emit(sentence, datetime.now().isoformat(), self.deployed_equipment_id)
                                # self.cursor.execute(sql, (sentence, datetime.now().isoformat(), self.deployed_equipment_id))


                            else:
                                if self.dataStatus != "green":
                                    self.dataStatus = "green"

                                self._meatball_count = 0
                                continue

                        else:
                            sentence = sentence.replace("\n", "<LF>")
                            sentence = sentence.replace("\r", "<CR>")

                        # Emit the sentence
                        self.dataReceived.emit(self.com_port, sentence)

                        if self.dataStatus != "green":
                            self.dataStatus = "green"

                        self._meatball_count = 0

                    buffer = ""

                # end_time = time.clock()

        except SerialException as ex:

            # Special exception here as we must return from this without further touching self.ser
            if "ClearCommError" in str(ex):
                msg = "Port Lost"
                resolution = "Check your wiring"

                self.stop()
                if self._data_status != "red":
                    self.dataStatus = "red"

                self.portPlayStatusChanged.emit(self.com_port, "stopped")
                self.exceptionEncountered.emit(self.com_port, msg, resolution, str(ex))

                return

            elif "FileNotFoundError" in str(ex):
                msg = "Port not registered"
                resolution = "Register or select a different port"

            elif "PermissionError" in str(ex):
                msg = "Port already open"
                resolution = "Check if another program is using this port"

            elif "OSError(22, 'Insufficient system resources exist" in str(ex):
                msg = "Port registered, but inactive"
                resolution = "Reactivate port (plug in moxa, keyspan, etc.)"

            elif "OSError(22, 'The parameter is incorrect" in str(ex):
                msg = "Incorrect parameter"
                resolution = "None"

            else:
                msg = "Unknown Error"
                resolution = "None"

            if self.is_streaming:
                self.exceptionEncountered.emit(self.com_port, msg, resolution, str(ex))

        except Exception as ex:

            if sentence and \
                ("UnicodeDecodeError" in str(ex) or "ExpatError" in str(ex) or "ValueError" in str(ex)):
                msg = "Parsing Error: " + sentence
                resolution = "Unknown"
            elif "codec can't decode byte" in str(ex):
                msg = "Decoding error"
                resolution = "File a bug report with the developers"
            else:
                msg = "Unknown issue"
                resolution = "Unknown"

            if self.is_streaming:
                self.exceptionEncountered.emit(self.com_port, msg, resolution, str(ex))

        self.stop()
        if self.ser.is_open:
            self.ser.close()
        if self._data_status != "red":
            self.dataStatus = "red"

        self.portPlayStatusChanged.emit(self.com_port, "stopped")


class SerialPortWriter(QObject):

    writerStatusStopped = pyqtSignal(str)
    exceptionEncountered = pyqtSignal(str, str, str, str)

    def __init__(self, kwargs=None):
        super().__init__()

        self.set_parameters(params=kwargs)
        self.ser = None
        self._is_running = False
        self._active_list = 0
        self._sentences = {0: [], 1: []}
        # self._values = {0: [], 1: []}

    def set_parameters(self, params):

        if "com_port" not in params:
            logging.error("Please provide a com_port when setting serial port paramsters")
            return

        databits = {5: serial.FIVEBITS, 6: serial.SIXBITS, 7: serial.SEVENBITS, 8: serial.EIGHTBITS}
        parity = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD,
                  "Mark": serial.PARITY_MARK, "Space": serial.PARITY_SPACE}
        stopbits = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE, 2: serial.STOPBITS_TWO}
        flowcontrol = {"None": False, "Off": serial.XOFF, "On": serial.XON}

        self.com_port = params["com_port"]

        self.baud_rate = 9600
        if "baud_rate" in params:
            self.baud_rate = int(params["baud_rate"])

        self.data_bits = serial.EIGHTBITS
        if "data_bits" in params:
            self.data_bits = databits[params["data_bits"]] if params["data_bits"] in databits else serial.EIGHTBITS

        self.parity = serial.PARITY_NONE
        if "parity" in params:
            self.parity = parity[params["parity"]] if params["parity"] in parity else serial.PARITY_NONE

        self.stop_bits = serial.STOPBITS_ONE
        if "stop_bits" in params:
            self.stop_bits = stopbits[params["stop_bits"]] if params["stop_bits"] in stopbits else serial.STOPBITS_ONE

        self.flow_control = False
        if "flow_control" in params:
            self.flow_control = flowcontrol[params["flow_control"]] if params["flow_control"] in flowcontrol else False

    def start(self):
        self._is_running = True

    def stop(self):
        self._is_running = False

    @pyqtSlot(str)
    def add_sentence(self, sentence):
        """
        Method to add a new sentence to be written to the associated serial port
        :param sentence:
        :return:
        """
        if sentence is None:
            return

        # self._values[self._active_list].append((sentence, datetime_str, deployed_equipment_id))
        self._sentences[self._active_list].append(sentence + "\r\n")

    def write(self):
        """
        Method to write content out to a serial port
        :return:
        """
        self.start()

        try:
            self.ser = Serial(baudrate=self.baud_rate, bytesize=self.data_bits,
                              parity=self.parity, stopbits=self.stop_bits,
                              xonxoff=self.flow_control)
            self.ser.port = self.com_port
            self.ser.open()

            while True:

                if not self._is_running:
                    break

                if self.ser.out_waiting > 10000:
                    # clear the buffer if it has gotten too large
                    self.ser.reset_output_buffer()

                # logging.info('before:  active > {0} \t\t\t {1}'.format(self._active_list, self._sentences))
                if len(self._sentences[self._active_list]) > 0:
                    self._active_list = 0 if self._active_list == 1 else 1
                    inactive_list = 0 if self._active_list == 1 else 1

                    self.ser.write(''.join(self._sentences[inactive_list]).encode("ISO-8859-1"))

                    del self._sentences[inactive_list][:]

                # logging.info('after:  active > {0} \t\t\t {1}'.format(self._active_list, self._sentences))

                time.sleep(1)

        except SerialException as ex:
            logging.error("Error writing to serial port: {0}".format(ex))

            if "ClearCommError" in str(ex):
                msg = "Port Lost"
                resolution = "Check your wiring"

                self.stop()

                self.writerStatusStopped.emit(self.com_port)
                self.exceptionEncountered.emit(self.com_port, msg, resolution, str(ex))

                return

            elif "FileNotFoundError" in str(ex):
                msg = "Port not registered"
                resolution = "Register or select a different port"

            elif "PermissionError" in str(ex):
                msg = "Port already open"
                resolution = "Check if another program is using this port"

            elif "OSError(22, 'Insufficient system resources exist" in str(ex):
                msg = "Port registered, but inactive"
                resolution = "Reactivate port (plug in moxa, keyspan, etc.)"

            if self._is_running:
                self.exceptionEncountered.emit(self.com_port, msg, resolution, str(ex))

        except Exception as ex:
            logging.error("Error writing to serial port: {0}".format(ex))

        self.stop()
        if self.ser:
            if self.ser.is_open:
                self.ser.close()

        self.writerStatusStopped.emit(self.com_port)


class SerialPortManager(QObject):
    """
    Class for the SerialPortManagerScreen.
    """
    dataReceived = pyqtSignal(str, str, arguments=["com_port", "data"])
    portPlayStatusChanged = pyqtSignal(str, str, arguments=["com_port", "status"])
    duplicatePortFound = pyqtSignal(str, arguments=["com_port"])
    portDataStatusChanged = pyqtSignal(str, str, arguments=["com_port", "status"])
    exceptionEncountered = pyqtSignal(str, str, str, str, arguments=["com_port", "msg", "resolution", "exception"])

    def __init__(self, app=None, db=None, sensor_config_model=None):
        super().__init__()

        self._app = app
        self._db = db
        self._logger = logging.getLogger(__name__)

        self._threads = {}
        self._workers = {}

        self._sensors_db_path = self.get_sensors_db()

        self._today = arrow.now(tz="US/Pacific")
        self._midnight = arrow.now(tz="US/Pacific").replace(hour=0, minute=0, second=0, microsecond=0).shift(days=1)

        logging.info(f"today = {self._today} >>> midnight = {self._midnight}")

        # TEST TEST TEST
        # self._test = arrow.now(tz="US/Pacific").shift(seconds=15)

        self._create_db_thread()

        self._serial_port_writers = {}

    @pyqtProperty(QVariant)
    def serialPortWriters(self):
        """
        Method to return self._serial_port_writers
        :return:
        """
        return self._serial_port_writers

    @pyqtSlot(QVariant)
    def add_serial_port_writer(self, com_port_dict):
        """
        Method to create a new SerialPortWriter thread/objects.  Note that this won't actually create
        the new thread, but it does create the Worker class.  The thread is started when the actual
        serial_port_writer is started
        :param com_port_dict:
        :return:
        """
        if isinstance(com_port_dict, QJSValue):
            com_port_dict = com_port_dict.toVariant()

        if com_port_dict["com_port"] in self._threads or \
            com_port_dict["com_port"] in self._serial_port_writers:
            logging.info("Serial port {0} is already taken".format(com_port_dict))
            self.duplicatePortFound.emit(com_port_dict["com_port"])
            return

        params = ["com_port", "baud_rate", "data_bits", "stop_bits", "parity", "flow_control",
                  "data_status", "deployed_equipment_id"]

        kwargs = {x: com_port_dict[x] for x in params if x in com_port_dict}

        if "baud_rate" in kwargs:
            kwargs["baud_rate"] = int(kwargs["baud_rate"])
        if "data_bits" in kwargs:
            kwargs["data_bits"] = int(kwargs["data_bits"])
        if "stop_bits" in kwargs:
            kwargs["stop_bits"] = float(kwargs["stop_bits"])

        com_port = kwargs["com_port"]

        self._serial_port_writers[com_port] = {"worker": None, "thread": None}
        self._serial_port_writers[com_port]["worker"] = SerialPortWriter(kwargs=kwargs)

    @pyqtSlot(str)
    def start_serial_port_writer(self, com_port):
        """
        Start the actual serial_port_writer thread
        :param com_port:
        :return:
        """
        if com_port is None:
            return

        if com_port in self._serial_port_writers:
            self._serial_port_writers[com_port]["thread"] = QThread()
            self._serial_port_writers[com_port]["worker"].moveToThread(self._serial_port_writers[com_port]["thread"])
            self._serial_port_writers[com_port]["worker"].writerStatusStopped.connect(self.writer_status_stopped)
            self._serial_port_writers[com_port]["worker"].exceptionEncountered.connect(self.writer_exception_encountered)
            self._serial_port_writers[com_port]["thread"].started.connect(
                self._serial_port_writers[com_port]["worker"].write
            )
            if not self._serial_port_writers[com_port]["thread"].isRunning():
                self._serial_port_writers[com_port]["thread"].start()

    @pyqtSlot()
    def stop_all_serial_port_writers(self):
        """
        Method to stop all of the serial port writers.  This will actually stop the threads
        :return:
        """
        keys = [k for k, v in self._serial_port_writers.items()]
        for com_port in keys:
            self.stop_serial_port_writer(com_port=com_port)

    @pyqtSlot(str)
    def stop_serial_port_writer(self, com_port=None):
        """
        Method to stop an individual serial port writer.  This actually stops the thread
        :param com_port:
        :return:
        """
        if com_port is None:
            return

        if com_port in self._serial_port_writers:

            if self._serial_port_writers[com_port]["thread"].isRunning():
                self._serial_port_writers[com_port]["worker"].stop()
                self._serial_port_writers[com_port]["thread"].quit()
                self._serial_port_writers[com_port]["thread"].wait()  # wait until the thread is done

            self._serial_port_writers.pop(com_port, None)

    def _create_db_thread(self):
        """
        Method to create the DatabaseWorker thread that is used
        :return:
        """
        self._db_thread = QThread()
        self._db_worker = DatabaseWorker(sensors_db_path=self._sensors_db_path)
        self._db_worker.moveToThread(self._db_thread)
        self._db_thread.started.connect(self._db_worker.write)
        if not self._db_thread.isRunning():
            self._db_thread.start()

    def get_sensors_db(self, days_delta=0, db_date=datetime.now()):

        """
        Method to get the path to the current daily sensor database file and create a
        :return:
        """

        # Find the path to the data directory where the databases are held
        if os.path.exists(os.path.join(os.getcwd(), '../data/hookandline_fpc.db')):
            db_root_path = '../data'
        elif os.path.exists(os.path.join(os.getcwd(), 'data/hookandline_fpc.db')):
            db_root_path = 'data'
        else:
            logging.error('Error finding the data folder')
            return

        # Find the clean_sensors.db path and ensure that it exists
        clean_db_path = os.path.join(db_root_path, 'clean_sensors.db')
        if not os.path.isfile(clean_db_path):
            msg = 'Could not find clean sensors DB file to copy: {0}'.format(clean_db_path)
            logging.error(msg)
            raise FileNotFoundError(msg)

        # Copy the clean_sensors.db to the new daily sensors_YYYYMMDD.db file
        logging.info('db_date: {0}'.format(db_date))
        db_date = db_date + timedelta(days=days_delta)
        datestr = db_date.strftime('%Y%m%d')
        sensors_db_path = os.path.join(db_root_path, 'sensors_' + datestr + '.db')
        if not os.path.isfile(sensors_db_path):
            logging.info('Copying {0} to {1}.'.format(clean_db_path, sensors_db_path))
            shutil.copyfile(clean_db_path, sensors_db_path)
        else:
            logging.info('Found sensors DB {0}'.format(sensors_db_path))

        # Return the path to the new sensors db file
        return sensors_db_path

    @pyqtSlot(QVariant)
    def add_thread(self, com_port_dict):
        """
        Method to add a new serial port thread
        :return:
        """
        if isinstance(com_port_dict, QJSValue):
            com_port_dict = com_port_dict.toVariant()

        if com_port_dict["com_port"] in self._threads:
            logging.info('Serial port ' + str(com_port_dict) + ' is already taken')
            self.duplicatePortFound.emit(com_port_dict["com_port"])
            return

        params = ["com_port", "baud_rate", "data_bits", "stop_bits", "parity", "flow_control",
                  "data_status", "deployed_equipment_id"]

        kwargs = {x: com_port_dict[x] for x in params if x in com_port_dict}
        kwargs["baud_rate"] = int(kwargs["baud_rate"])
        kwargs["data_bits"] = int(kwargs["data_bits"])
        kwargs["stop_bits"] = float(kwargs["stop_bits"])

        com_port = kwargs["com_port"]

        self._threads[com_port] = QThread()
        self._workers[com_port] = SerialPortWorker(sensors_db_path=self._sensors_db_path,
                                                   kwargs=kwargs)
        self._workers[com_port].moveToThread(self._threads[com_port])
        self._workers[com_port].portPlayStatusChanged.connect(self.port_play_status)
        self._workers[com_port].dataReceived.connect(self.data_received)

        # Testing to overcome BusyError
        self._workers[com_port].dataReceivedForDatabase.connect(self.write_data_to_database)

        self._workers[com_port].dataStatusChanged.connect(self.port_data_status)
        self._workers[com_port].exceptionEncountered.connect(self.exception_encountered)
        self._threads[com_port].started.connect(self._workers[com_port].read)

    @pyqtSlot()
    def start_all_threads(self):
        """
        Method to activate all of the serial port threads
        :return:
        """

        for port in self._threads:
            self.start_thread(com_port=port)
            if not self._threads[port].isRunning():
                time.sleep(0.05)

    @pyqtSlot(str)
    def start_thread(self, com_port):
        """
        Method to start the passed thread
        :return:
        """
        if com_port is None:
            return

        if com_port in self._threads:

            thread = self._threads[com_port]
            if not thread.isRunning():
                thread.start()

    @pyqtSlot()
    def stop_all_threads(self):
        for port in self._threads:
            self.stop_thread(com_port=port)
            if self._threads[port].isRunning():
                time.sleep(0.05)

    @pyqtSlot(str)
    def stop_thread(self, com_port):
        """
        Method to stop the passed thread
        :return:
        """
        if com_port is None:
            return

        if com_port in self._workers and com_port in self._threads:
            self._workers[com_port].stop()

            # self._threads[com_port].exit()
            self._threads[com_port].quit()
            # self._threads[com_port].wait(msecs=100)
            # self._threads[com_port].wait()  # wait until the thread is done

    def delete_all_threads(self):

        keys = [k for k, v in self._threads.items()]
        for port in keys:
            self.delete_thread(com_port=port)

        # for port in self._threads:
        #     self.delete_thread(com_port=port)

    @pyqtSlot(str)
    def delete_thread(self, com_port):
        """
        Method to delete a serial port thread
        :return:
        """

        if com_port not in self._threads:
            return

        if self._threads[com_port].isRunning():
            self.stop_thread(com_port=com_port)
            self._threads[com_port].wait()  # wait until the thread is done
            # self._threads[com_port].wait(msecs=5000)

        # start_time = time.clock()
        # end_time = start_time
        # while self._threads[com_port].isRunning():
        #
        #     if end_time - start_time >= 5:
        #         break
        #     end_time = time.clock()

        self._threads.pop(com_port, None)
        self._workers.pop(com_port, None)

    # TODO Todd - Fix  update_port code - remove rules, use peewee, change slot to str, etc.
    @pyqtSlot(int, QVariant)
    def update_port(self, index, data):
        """
        Method to update the serial port with the given index
        :param index: int - index of the row of the tvSensorConfiguration tableview to update
        :param data: QVariant - data used to upload the row
        :return: None
        """
        if data is None:
            return None

        data = data.toVariant()

        # For some reason, when the data comes over as a QVariant, the ints are getting turned into floats
        data["data_bits"] = int(data["data_bits"])
        data["baud_rate"] = int(data["baud_rate"])
        data["stop_bits"] = float(data["stop_bits"])
        new_key = data["com_port"]

        # Get the new rule
        try:
            rule = ParsingRules.select().where((ParsingRules.measurement_type == data["measurementTypeId"]) &
                                               (ParsingRules.equipment == data["equipmentId"]))
            if rule.count() == 1:
                for r in rule:
                    rule_dict = model_to_dict(r)
                    data["rule"] = rule_dict
        except Exception as ex:
            pass

        # Get the current serialPort, which also acts as the key for self._threads + self._workers
        item = self._sensor_config_model.get(index)
        old_key = item["com_port"]
        reader_or_writer = item["readerOrWriter"].lower()

        # Update the database
        # paramItems = ["com_port", "baud_rate", "data_bits", "parity", "stop_bits",
        #               "flow_control", "equipmentId", "measurementTypeId"]
        paramItems = ["com_port", "baud_rate", "data_bits", "parity",
                      "stop_bits", "flow_control"]
        params = [data[x] for x in paramItems]
        item = self._sensor_config_model.get(index)
        deployed_equipment_id = item["deployedEquipmentId"]
        params.append(deployed_equipment_id)

        sql = "UPDATE DEPLOYED_EQUIPMENT " + \
            "SET COM_PORT = ?, BAUD_RATE = ?, DATA_BITS = ?, " + \
            "PARITY = ?, STOP_BITS = ?, FLOW_CONTROL = ?, " + \
            "EQUIPMENT_ID = ?, MEASUREMENT_TYPE_ID = ? " + \
            "WHERE DEPLOYED_EQUIPMENT_ID = ?;"
        self._db.execute(query=sql, parameters=params)

        # Modify the thread/workers for readers
        if reader_or_writer == "reader":

            # Stop the thread
            self.stop_thread(com_port=old_key)

            # Update the thread with the new parameters
            self._workers[old_key].set_parameters(params=data)

            # Change the key in self._threads and self._workers
            self._threads[new_key] = self._threads.pop(old_key)
            self._workers[new_key] = self._workers.pop(old_key)
            self._play_status[new_key] = self._play_status.pop(old_key)

        # Update the model
        for k, v in data.items():
            self._serial_ports_model.setProperty(index, k, v)

        # If a printer is found, update the self._printers dictionary
        if "printer" in data["equipmentName"].lower():
            try:
                found = re.search("\(Printer \d\)", data["equipmentName"])
                if found:
                    printer = found.group(0).strip("()")
                    self.printers = {printer: "COM" + str(data["serialPort"])}
            except Exception as ex:
                pass

        # Start the thread for readers
        if reader_or_writer == "reader":

            # Start the thread - Update this at the end, as we need to search across self._threads
            # properly find this new_key, so we need to have updated self._threads and the model first
            self.start_thread(com_port=new_key)

    def data_received(self, com_port, data):
        """
        Method to emit the dataReceived signal which is caught by the
        SensorDataFeeds.py 6tg
        :param com_port:
        :param data:
        :return:
        """
        self.dataReceived.emit(com_port, data)

    def write_data_to_database(self, sentence, datetime_str, deployed_equipment_id):
        """
        Method to capture
        :param sentence:
        :param datetime_str:
        :param deployed_equipment_id:
        :return:
        """
        now = arrow.now(tz="US/Pacific")
        if now.timestamp > self._midnight.timestamp:

        # TEST TEST TEST
        # if now.timestamp > self._test.timestamp:

            sensor_db_path = self.get_sensors_db(days_delta=0, db_date=self._midnight.datetime)
            self._db_worker.change_db_path(new_path=sensor_db_path)

            self._midnight = self._midnight.shift(days=1)

            logging.info(f"new midnight = {self._midnight}")

            # TEST TEST TEST
            # self._test = self._midnight

        self._db_worker.add_values(sentence=sentence, datetime_str=datetime_str,
                                   deployed_equipment_id=deployed_equipment_id)

    def port_data_status(self, com_port, status):
        """
        Method called when a port's dataStatusChanged signal is emitted, indicating that a
        meatball has changed
        :param com_port:
        :param status:
        :return:
        """
        self.portDataStatusChanged.emit(com_port, status)

    def port_play_status(self, com_port, status):
        """

        :param com_port:
        :param status:
        :return:
        """
        self.portPlayStatusChanged.emit(com_port, status)
        if status == "stopped" and com_port in self._threads:
            if self._threads[com_port].isRunning():
                self.stop_thread(com_port=com_port)

    def exception_encountered(self, com_port, msg, resolution, exception):

        logging.error("{0}: {1}, {2} > {3}".format(com_port, msg, resolution, exception))
        self.exceptionEncountered.emit(com_port, msg, resolution, exception)
        try:
            if com_port in self._threads:
                if self._threads[com_port].isRunning():
                    self.stop_thread(com_port=com_port)

        except Exception as ex:
            logging.info("exception reporting error: {0}".format(ex))

    def writer_exception_encountered(self, com_port, msg, resolution, exception):
        """
        Method to catch an exception from the Serial Port Writer, to relay a message back via a Dialog to the user
        that something failed
        :param com_port:
        :param msg:
        :param resolution:
        :param exception:
        :return:
        """
        self.exceptionEncountered.emit(com_port, msg, resolution, exception)

    def writer_status_stopped(self, com_port):
        """
        Method to receive the message from the Serial Port Writer that the port has closed
        :param com_port:
        :return:
        """
        if com_port in self._serial_port_writers:
            if self._serial_port_writers[com_port]["thread"].isRunning():
                self.stop_serial_port_writer(com_port=com_port)


class TestSPM(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        pass
        # self.s = SerialPortManager()

    def testReadPorts(self):

        mtypes = [178, 179]
        ports = DeployedEquipment.select().where(DeployedEquipment.measurement_type << mtypes)
        # self.assertGreaterEqual(len(ports), 10)
        for port in ports:
            self.assertIsNotNone(port)

            logging.info(str(model_to_dict(port)))
