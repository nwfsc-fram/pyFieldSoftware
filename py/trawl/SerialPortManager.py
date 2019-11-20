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
# from py.common.SoundPlayer import SoundPlayer
import logging
from threading import Thread, Timer
from queue import Queue
from serial import Serial, SerialException
import serial
import time
from datetime import datetime
import re
from decimal import Decimal
from dateutil import parser
from xml.parsers.expat import ExpatError
from py.common.SerialDataParser import SerialDataParser
import unittest
from py.trawl.TrawlBackdeckDB_model import DeployedEquipment, ParsingRules, TypesLu
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import *


class EquipmentModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="equipmentId")
        self.add_role_name(name="equipmentName")
        self.add_role_name(name="text")


class MeasurementsModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="measurementTypeId")
        self.add_role_name(name="measurementName")
        self.add_role_name(name="text")


class MessagesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="measurement")
        self.add_role_name(name="value")
        self.add_role_name(name="sentence")


class SerialPortsModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="deployedEquipmentId")
        self.add_role_name(name="serialPort")
        self.add_role_name(name="equipmentId")
        self.add_role_name(name="equipmentName")
        self.add_role_name(name="settings")
        self.add_role_name(name="measurementTypeId")
        self.add_role_name(name="measurementName")
        self.add_role_name(name="baudRate")
        self.add_role_name(name="dataBits")
        self.add_role_name(name="parity")
        self.add_role_name(name="stopBits")
        self.add_role_name(name="flowControl")
        self.add_role_name(name="dataStatus")
        self.add_role_name(name="playControl")
        self.add_role_name(name="readerOrWriter")


class SerialPortWorker(QObject):

    # portClosed = pyqtSignal(int)
    exceptionEncountered = pyqtSignal(int, str)
    dataStatusChanged = pyqtSignal(int, str)
    dataReceived = pyqtSignal(int, str, str, str)

    def __init__(self, db=None, kwargs=None):
        super().__init__()

        self._db = db
        self.set_parameters(params=kwargs)

        self.ser = None

        self.is_streaming = False
        self._data_status = "red"
        self._meatball_count = 0

        # self._queue = Queue()

    def set_parameters(self, params):

        databits = {5: serial.FIVEBITS, 6: serial.SIXBITS, 7: serial.SEVENBITS, 8: serial.EIGHTBITS}
        parity = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD,
                  "Mark": serial.PARITY_MARK, "Space": serial.PARITY_SPACE}
        stopbits = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE, 2: serial.STOPBITS_TWO}
        flowcontrol = {"None": False, "Off": serial.XOFF, "On": serial.XON}

        self.deployedEquipmentId = params["deployedEquipmentId"]
        self.serialPort = params["serialPort"]
        self.baudRate = params["baudRate"]
        self.dataBits = databits[params["dataBits"]]
        self.parity = parity[params["parity"]]
        self.stopBits = stopbits[params["stopBits"]]
        self.flowControl = flowcontrol[params["flowControl"]]
        self.measurementTypeId = params["measurementTypeId"]
        self.measurementName = params["measurementName"]
        self.equipmentId = params["equipmentId"]
        self.equipmentName = params["equipmentName"]
        self.playControl = params["playControl"] if "playControl" in params else "play"
        self.dataStatus = params["dataStatus"] if "dataStatus" in params else "red"
        self.rule = params["rule"] if "rule" in params else ""

        self.parsingKey = str(self.equipmentId) + "+" + str(self.measurementTypeId)

    @pyqtProperty(str, notify=dataStatusChanged)
    def dataStatus(self):
        return self._data_status

    @dataStatus.setter
    def dataStatus(self, value):
        self._data_status = value
        self.dataStatusChanged.emit(self.serialPort, value)

    def start(self):
        self.is_streaming = True
        self.playControl = "play"

    def stop(self):
        self.is_streaming = False
        self.playControl = "stop"

    def read(self):

        if len(self.rule) == 0:
            logging.info('rule length is 0: ' + str(self.rule))
            logging.info("equipment: " + str(self.equipmentName) + " >>> measurement: " + str(self.measurementName))
            return

        self.start()
        self.dataStatus = "red"

        # TODO Todd Hay - why is \r\n not working for parsing the ending?
        ending = re.compile(self.rule["line_ending"].encode().decode("unicode-escape"))
        endingBefore = ending
        ending = re.compile('\r?\n?')

        # logging.info(str(endingBefore) + ' >>> ' + str(ending))

        fixedOrDelimited = self.rule["fixed_or_delimited"] if "fixed_or_delimited" in self.rule else None
        startPos = self.rule["start_position"] if "start_position" in self.rule else None
        endPos = self.rule["end_position"] if "end_position" in self.rule else None
        delimiter = self.rule["delimiter"] if "delimiter" in self.rule else None
        fieldNum = self.rule["field_position"] if "field_position" in self.rule else None
        uom = self.rule["units_of_measurement"] if "units_of_measurement" in self.rule else None

        buffer = ""
        split_data = ""
        sentence = ""

        try:
            self.ser = Serial(baudrate=self.baudRate, bytesize=self.dataBits,
                  parity=self.parity, stopbits=self.stopBits,
                  xonxoff=self.flowControl, timeout=5)
            self.ser.port = "COM" + str(self.serialPort)
            self.ser.open()

            start_time = time.clock()
            # end_time = start_time

            while True:

                if not self.is_streaming:
                    break

                # time_diff = end_time - start_time
                #
                # if time_diff >= 60:
                #     # red meatball time
                #     if self._data_status != "red":
                #         self.dataStatus = "red"
                #
                # elif time_diff >= 5 and self._data_status != "red":
                #     # yellow meatball time
                #     if self._data_status != "yellow":
                #         self.dataStatus = "yellow"

                if self.ser.in_waiting > 10000:
                    # clear the buffer if it has gotten too large
                    self.ser.reset_input_buffer()

                # This will apparently block until 1 byte received - but I set timeout=5 (5 seconds) above, so
                # it will break out of this read operation after 5 seconds.  self._meatball_count is used to
                # keep track of the 5s timeouts that occur, so if we get to 12 (i.e. 0-11) that means that
                # 60s has elapsed and we should turn the meatball red
                buffer += self.ser.read(1).decode("ISO-8859-1")
                if buffer == "":
                    if self._meatball_count < 12 and self.dataStatus != "red":
                        if self.dataStatus != "yellow":
                            self.dataStatus = "yellow"
                    elif self.dataStatus != "red":
                        self.dataStatus = "red"
                    self._meatball_count += 1
                buffer += self.ser.read(self.ser.in_waiting).decode("ISO-8859-1")

                # Original - worked, but went to 30% of CPU in pilot plant when having 7 open serial ports
                # buffer += self.ser.read(self.ser.inWaiting()).decode("ISO-8859-1")

                if ending.search(buffer):
                    # logging.info('found ending')
                    lines = ending.split(buffer)
                    if split_data != "":
                        lines[0] = split_data + lines[0]
                        split_data = ""

                    if lines[-1] != "\r\n" and lines[-1] != "":
                        # Line split across buffers, hold on to data
                        split_data = lines[-1]
                        del lines[-1]

                    lines = [x for x in lines if x != "\r\n" and x != ""]

                    for sentence in lines:

                        # Clean out any control characters
                        # Remove ASCII Control Characters before entering into the database
                        # References:
                        #  ASCII Control Characters - http://ascii.cl/control-characters.htm
                        #  ISO-8859-1 - http://en.wikipedia.org/wiki/ISO/IEC_8859-1
                        #  How to remove them:  http://chase-seibert.github.io/blog/2011/05/20/stripping-control-characters-in-python.html
                        #  Reference - ftp://ftp.unicode.org/Public/MAPPINGS/ISO8859/8859-1.TXT
                        #  sentence = re.sub(r"[\x01-\x1F\x7F]", "", sentence)
                        sentence = re.sub(r"[\x01-\x1F\x7F\x80-\x9F]", "", sentence)

                        # Parse the value
                        if fixedOrDelimited.lower() == "fixed":
                            value = sentence[startPos:endPos+1].strip()
                            # if "caliper" in self.equipmentName.lower() and \
                            #         "width (cm)" in self.measurementName.lower():
                            # logging.info('uom: ' + str(uom) + ', measurementName: ' + str(self.measurementName))
                            if uom == "mm" and "width (cm)" in self.measurementName.lower():
                                # Convert from mm to cm
                                # TODO Todd Hay - this works, but not very elegant to hardcode in code in this
                                # Should I store the units of measurement in PARSING_RULES as well and then
                                # have a converter class to call, comparing measurementName to uom, probably so
                                try:
                                    value = "%.2f" % (float(value.strip())/10.0)
                                except Exception as ex:
                                    logging.error('parse error, value: {0}, rule: {1}'.format(value, self.rule))
                                    value = None

                        else:
                            value = sentence.split(delimiter)[fieldNum].strip()

                        # Emit the sentence
                        self.dataReceived.emit(self.serialPort, self.measurementName, sentence, value)

                        if self.dataStatus != "green":
                            self.dataStatus = "green"

                        self._meatball_count = 0

                    buffer = ""

                # end_time = time.clock()

        except SerialException as ex:

            msg = "Error: COM" + str(self.serialPort) + " > " + str(ex)

            if "ClearCommError" in str(ex):
                msg += "\n   Port Lost > You just lost this port"

            self.stop()
            if self._data_status != "red":
                self.dataStatus = "red"

            self.exceptionEncountered.emit(self.serialPort, msg)

            return

        except Exception as ex:

            msg = "Error: COM" + str(self.serialPort) + " > " + str(ex)
            # msg = msg[0:60]    # Method to truncate the msg

            if "ClearCommError" in str(ex):
                msg += "\n   Port Lost > You just lost this port"

            elif "FileNotFoundError" in str(ex):
                msg += "\n   Inactive Port > Please select a different port"

            elif "PermissionError" in str(ex):
                msg += "\n   Port Already Open > The port is open in another program"

            elif "OSError(22, 'Insufficient system resources exist" in str(ex):
                msg += "\n   Unrecognized Port > The COM port is not recognized on this system"

            elif sentence and \
                ("UnicodeDecodeError" in str(ex) or "ExpatError" in str(ex) or "ValueError" in str(ex)):
                msg += "\n   Parsing Error: " + sentence

            self.exceptionEncountered.emit(self.serialPort, msg)

        self.stop()
        if self.ser.is_open:
            self.ser.close()
        if self._data_status != "red":
            self.dataStatus = "red"


class SerialPortManager(QObject):
    """
    Class for the SerialPortManagerScreen.
    """
    modelChanged = pyqtSignal()
    portStatusChanged = pyqtSignal(int, str)
    playStatusChanged = pyqtSignal()
    requestedPortChanged = pyqtSignal()
    printerChanged = pyqtSignal()

    equipmentChanged = pyqtSignal()
    measurementsChanged = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db
        self._printers = {}

        self._serial_ports = self.get_serial_ports()
        self._serial_ports_model = SerialPortsModel()
        self._serial_ports_model.setItems(self._serial_ports)

        self._equipment = self.get_equipment()
        self._equipment_model = EquipmentModel()
        self._equipment_model.setItems(self._equipment)

        self._measurements_model = MeasurementsModel()
        self.measurementsModel = None

        # self._measurements = self.get_measurements()
        # self._measurements_model.setItems(self._measurements)

        self._messages_model = MessagesModel()

        # self.add_data_pusher()

        self._threads = {}
        self._workers = {}
        self._port_status = {}
        self._play_status = {}
        self._requested_port = None

        self.add_all_threads()
        self.start_all_threads()

    @pyqtSlot()
    def initialize_serial_ports(self):
        """
        Method called when entering the screen to initialize the model for the tvSerialPorts TableView
        :return:
        """
        return

        # Clear the model
        self._serial_ports_model.clear()

        # Rebuild the list from the active serial ports
        databits = {serial.FIVEBITS: 5, serial.SIXBITS: 6, serial.SEVENBITS: 7, serial.EIGHTBITS: 8}
        parity = {serial.PARITY_NONE: "None", serial.PARITY_EVEN: "Even", serial.PARITY_ODD: "Odd",
                  serial.PARITY_MARK: "Mark", serial.PARITY_SPACE: "Space"}
        stopbits = {serial.STOPBITS_ONE: 1, serial.STOPBITS_ONE_POINT_FIVE: 1.5,
                    serial.STOPBITS_TWO: 2}
        flowcontrol = {False: "None", serial.XOFF: "Off", serial.XON: "On"}

        # Add all of the readers
        ports = []
        for port in self._workers:
            worker = self._workers[port]
            newport = {"deployedEquipmentId": worker.deployedEquipmentId,
                       "serialPort": worker.serialPort,
                       "baudRate": worker.baudRate,
                       "dataBits": databits[worker.dataBits],
                       "parity": parity[worker.parity],
                       "stopBits": stopbits[worker.stopBits],
                       "flowControl": flowcontrol[worker.flowControl],
                       "measurementTypeId": worker.measurementTypeId,
                       "measurementName": worker.measurementName,
                       "equipmentId": worker.equipmentId,
                       "equipmentName": worker.equipmentName,
                       "status": worker.dataStatus,
                       "readerOrWriter": worker.readerOrWriter}

            if newport["readerOrWriter"].lower() == "reader":
                if worker.is_streaming:
                    newport["playControl"] = "stop"
                else:
                    newport["playControl"] = "play"
            else:
                newport["playControl"] = None

            logging.info(str(newport))
            ports.append(newport)

        self._serial_ports_model.setItems(ports)

    def get_serial_ports(self):
        """
        Return the serial ports from the database
        :return:
        """
        serialports = []
        serialport = {0: "deployedEquipmentId", 1: "serialPort", 2: "baudRate",
                      3: "dataBits", 4: "parity", 5: "stopBits", 6: "flowControl",
                      11: "measurementTypeId", 12: "measurementName",
                      10: "equipmentId", 14: "equipmentName", 15: "readerOrWriter"}
        settings = ["baudRate", "dataBits", "parity", "stopBits", "flowControl"]

        # sql = "SELECT * FROM SERIAL_PORTS_VW WHERE lower(READER_OR_WRITER) = 'reader';"
        sql = "SELECT * FROM SERIAL_PORTS_VW;"
        printer_count = 1
        for row in self._db.execute(query=sql):
            newport = {serialport[i]: row[i] for i in serialport}
            if row[13]:
                newport["measurementName"] += " (" + row[13] + ")"
            # newport["settings"] = "-".join([str(newport[i]) for i in settings])

            if row[15].lower() == "reader":
                newport["dataStatus"] = "red"
                newport["playControl"] = "play"
            else:
                newport["measurementName"] = "None"
                newport["dataStatus"] = None
                newport["playControl"] = None
                newport["equipmentName"] += " (Printer " + str(printer_count) + ")"
                self.printers = {"Printer " + str(printer_count): "COM" + str(newport["serialPort"])}
                printer_count += 1

            serialports.append(newport)

        return serialports

    @pyqtProperty(QVariant, notify=printerChanged)
    def printers(self):
        """
        Return the printers
        :return:
        """
        return self._printers

    @printers.setter
    def printers(self, key_value):
        """
        Set the printers
        :return:
        """
        if isinstance(key_value, QJSValue):
            key_value = key_value.toVariant()

        for key, value in key_value.items():
            self._printers[key] = value

        self.printerChanged.emit()

    @pyqtProperty(QVariant, notify=modelChanged)
    def serialPortsModel(self):
        """
        Return the model
        :return:
        """
        return self._serial_ports_model

    @pyqtSlot()
    def serialPortSort(self):
        """
        Method to sort the tvSerialPorts tableview by the COM Ports, i.e. an integer, as FramListModel
        lacks such an integer based sorting capability
        :return:
        """

        sorted_items = sorted(self._serial_ports_model.items, key=lambda x: int(x["serialPort"]))
        self._serial_ports_model.setItems(sorted_items)

    @pyqtProperty(QVariant, notify=modelChanged)
    def messagesModel(self):
        return self._messages_model

    @pyqtProperty(QVariant, notify=measurementsChanged)
    def measurementsModel(self):
        """
        Method to get the measurementsModel
        :return:
        """
        return self._measurements_model

    @measurementsModel.setter
    def measurementsModel(self, equipment_id=None):

        measurementList = []

        try:
            if equipment_id is None:
                measurements = TypesLu.select().\
                    where(TypesLu.category == 'Measurement')
            else:
                measurements = TypesLu.select().\
                    join(ParsingRules, on=(TypesLu.type_id == ParsingRules.measurement_type)). \
                    where((ParsingRules.equipment == equipment_id) &
                          (TypesLu.category == 'Measurement'))

            if measurements.count() > 0:
                for measurement in measurements:
                    item = {"measurementTypeId": measurement.type_id,
                            "measurementName": measurement.type + " (" + measurement.subtype + ")",
                            "text": measurement.type + " (" + measurement.subtype + ")"}
                    measurementList.append(item)
            else:
                # Add in a None value for the Printers
                item = {"measurementTypeId": None, "measurementName": "None", "text": "None"}
                measurementList.append(item)

        except Exception as ex:
            pass

        self._measurements_model.setItems(measurementList)
        self.measurementsChanged.emit()

    @pyqtProperty(QVariant)
    def threads(self):
        return self._threads

    def get_equipment(self):
        """
        Method to get all of the equipment listings and use that list to
        :return:
        """
        equipment = []
        sql = "SELECT EQUIPMENT_ID, NAME FROM EQUIPMENT WHERE lower(IS_ACTIVE) = 'true' AND " + \
              "(DEACTIVATION_DATE IS NULL OR DEACTIVATION_DATE = '') " + \
              " AND IS_BACKDECK = 'True' ORDER BY NAME;"
        equipment = self._db.execute(query=sql).fetchall()
        equipment = [{"equipmentId": x[0], "equipmentName": x[1],
                      "text": x[1]} for x in equipment]

        self.equipmentChanged.emit()

        return equipment

    @pyqtProperty(QVariant, notify=equipmentChanged)
    def equipmentModel(self):
        """
        pyqtProperty to return the listing of equipment names
        :return:
        """
        return self._equipment_model

    @pyqtProperty(str, notify=requestedPortChanged)
    def requestedPort(self):
        return self._requested_port

    @requestedPort.setter
    def requestedPort(self, value):
        try:
            self._requested_port = int(value)
            self.requestedPortChanged.emit()
        except Exception as ex:
            logging.error('value is not an int: ' + str(value))

    @pyqtProperty(str, notify=playStatusChanged)
    def playStatus(self):
        if self._requested_port in self._play_status:
            return self._play_status[self._requested_port]
        return None

    @playStatus.setter
    def playStatus(self, status_dict):
        for k, v in status_dict.items():
            self._play_status[k] = v
        # self._play_status[self._requested_port] = value
        self.playStatusChanged.emit()

    @pyqtProperty(str, notify=portStatusChanged)
    def portStatus(self):
        if self._requested_port in self._port_status:
            return self._port_status[self._requested_port]
        return None

    @portStatus.setter
    def portStatus(self, value):
        self._port_status[self._requested_port] = value
        self.portStatusChanged.emit(self._requested_port, value)

    def add_all_threads(self):
        """
        Method used during initialization to create all of the threads that based on data pulled from
        the database
        :return: list - of dictionaries of the threads
        """
        readers = [x for x in self._serial_ports if x["readerOrWriter"].lower() == "reader"]
        for s in readers:
            self.add_thread(s)

    @pyqtSlot(QVariant)
    def add_thread(self, serial_dict):
        """
        Method to add a new serial port thread
        :return:
        """
        if serial_dict["serialPort"] in self._threads:
            logging.info('Serial port ' + str(serial_dict) + ' is already taken')
            return

        params = ["deployedEquipmentId",
                  "serialPort", "baudRate", "dataBits", "stopBits", "parity", "flowControl",
                  "measurementTypeId", "measurementName", "equipmentId", "equipmentName",
                  "dataStatus", "playControl"]
        kwargs = {x: serial_dict[x] for x in params}

        rule = ParsingRules.select().where((ParsingRules.measurement_type == kwargs["measurementTypeId"]) &
                                           (ParsingRules.equipment == kwargs["equipmentId"]))
        if rule.count() == 1:
            for r in rule:
                rule_dict = model_to_dict(r)
                kwargs["rule"] = rule_dict

        serial_port = kwargs["serialPort"]

        self._threads[serial_port] = QThread()
        self._workers[serial_port] = SerialPortWorker(db=self._db, kwargs=kwargs)
        self._workers[serial_port].moveToThread(self._threads[serial_port])
        self._workers[serial_port].dataReceived.connect(self.data_received)
        self._workers[serial_port].dataStatusChanged.connect(self.port_status)
        self._workers[serial_port].exceptionEncountered.connect(self.exception_encountered)
        self._threads[serial_port].started.connect(self._workers[serial_port].read)

    @pyqtSlot()
    def start_all_threads(self):
        """
        Method to activate all of the serial port threads
        :return:
        """
        for port in self._threads:
            self.start_thread(serial_port=port)
            if not self._threads[port].isRunning():
                time.sleep(0.05)

    @pyqtSlot(int)
    def start_thread(self, serial_port):
        """
        Method to start the passed thread
        :return:
        """
        if serial_port is None:
            return

        if serial_port in self._threads:

            thread = self._threads[serial_port]
            if not thread.isRunning():
                thread.start()
                # self._requested_port = serial_port
                # self.playStatus = "stop"
                self.playStatus = {serial_port: "stop"}

                row = self._serial_ports_model.get_item_index("serialPort", serial_port)
                if row >= 0 and row < self._serial_ports_model.count:
                    self._serial_ports_model.setProperty(row, "playControl", "stop")

    @pyqtSlot()
    def stop_all_threads(self):
        for port in self._threads:
            self.stop_thread(serial_port=port)
            if self._threads[port].isRunning():
                time.sleep(0.05)

    @pyqtSlot(int)
    def stop_thread(self, serial_port):
        """
        Method to stop the passed thread
        :return:
        """
        if serial_port is None:
            return

        if serial_port in self._workers and serial_port in self._threads:
            self._workers[serial_port].stop()
            self._threads[serial_port].exit()
            # self._requested_port = serial_port
            # self.playStatus = "play"
            self.playStatus = {serial_port: "play"}

            row = self._serial_ports_model.get_item_index("serialPort", serial_port)
            if row >= 0 and row < self._serial_ports_model.count:
                self._serial_ports_model.setProperty(row, "playControl", "play")

    # TODO Todd Hay
    def delete_all_threads(self):
        for port in self._threads:
            self.delete_thread(serial_port=port)

    @pyqtSlot(int)
    def delete_thread(self, serial_port):
        """
        Method to delete a serial port thread
        :return:
        """
        if self._threads[serial_port].isRunning():
            self.stop_thread(serial_port=serial_port)

        start_time = time.clock()
        while self._threads[serial_port].isRunning():

            if end_time - start_time >= 5:
                break
            end_time = time.clock()

        self._threads.pop(serial_port, None)
        self._workers.pop(serial_port, None)

    @pyqtSlot(int, QVariant)
    def update_port(self, index, data):
        """
        Method to update the serial port with the given index
        :param index: int - index in tvSerialPorts to update
        :param data: QVariant - data used to upload the row
        :return: None
        """
        if index is None or data is None:
            return None

        data = data.toVariant()

        # For some reason, when the data comes over as a QVariant, the ints are getting turned into floats
        data["dataBits"] = int(data["dataBits"])
        data["baudRate"] = int(data["baudRate"])
        data["stopBits"] = float(data["stopBits"])
        data["serialPort"] = int(data["serialPort"])
        new_key = data["serialPort"]

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
        item = self._serial_ports_model.get(index)
        old_key = item["serialPort"]
        reader_or_writer = item["readerOrWriter"].lower()

        # Update the database
        paramItems = ["serialPort", "baudRate", "dataBits", "parity", "stopBits",
                      "flowControl", "equipmentId", "measurementTypeId"]
        params = [data[x] for x in paramItems]
        item = self._serial_ports_model.get(index)
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
            self.stop_thread(serial_port=old_key)

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
            self.start_thread(serial_port=new_key)

    def data_received(self, serial_port, measurement, data, value):
        """
        :param serial_port: int - representing the serial port on which data is received
        :param measurement: str -
        :param data: str - the actual data received
        :param value: str - parsed value - note that it is a string and has not been converted yet
        :return:
        """
        # Append to the tvMessages tableview
        item = {"measurement": measurement, "value": value, "sentence": data}
        self._messages_model.appendItem(item)

        # Update the current screen
        screen = self._app.state_machine.screen

        # logging.info('screen: ' + str(screen) + ', measurement: ' + str(measurement) + \
        #              ', activeTab: ' + str(self._app.fish_sampling.activeTab))

        if screen == "weighbaskets":
            if measurement == "Weight (kg)":
                try:
                    logging.info(f"weight received, value = {value}, mode = {self._app.weigh_baskets._mode}")

                    value = float(value)
                    if isinstance(value, float):
                        # if self._app.weigh_baskets._mode == "takeWeight" and \
                        # self._app.weigh_baskets._weight_type == "scaleWeight":

                        if self._app.weigh_baskets._mode == "takeWeight":
                            logging.info(f"adding the new weight value")
                            self._app.weigh_baskets.add_list_item(value)
                except ValueError as ex:
                    pass

        elif screen == "fishsampling":

            if (measurement == "Length (cm)" or measurement == "Width (cm)") and \
                            self._app.fish_sampling.activeTab == "Sex-Length":
                try:
                    value = float(value)

                    if measurement == "Length (cm)":
                        lineal_type = "length"
                    elif measurement == "Width (cm)":
                        lineal_type = "width"
                    else:
                        lineal_type = "length"
                    self._app.fish_sampling.linealType = lineal_type

                    if self._app.fish_sampling.actionMode == "add":
                        self._app.fish_sampling.add_list_item(value, self._app.fish_sampling.sex)
                    elif self._app.fish_sampling.actionMode == "modify":
                        self._app.fish_sampling.update_list_item(property="linealValue", value=value)
                except ValueError as ex:
                    pass

            elif (measurement == "Weight (kg)" or measurement == "Barcode (number)") and \
                    (self._app.fish_sampling.activeTab == "Age-Weight" or
                    self._app.fish_sampling.activeTab == "Ovary-Stomach"):
                try:
                    if measurement == "Weight (kg)":
                        property = "weight"
                        value = float(value)

                    elif measurement == "Barcode (number)":
                        value = int(value)
                        property = "ageNumber"
                    self._app.fish_sampling.update_list_item(property=property, value=value)

                except ValueError as ex:
                    pass

        elif screen == "specialactions":

            rowIndex = self._app.special_actions.rowIndex

            if measurement == "Barcode (number)":
                try:
                    value = int(value)

                    is_coral = self._app.process_catch.checkSpeciesType("coral", self._app.state_machine.species["taxonomy_id"])
                    is_sponge = self._app.process_catch.checkSpeciesType("sponge", self._app.state_machine.species["taxonomy_id"])
                    is_rockfish = self._app.process_catch.checkSpeciesType("rockfish", self._app.state_machine.species["taxonomy_id"])

                    logging.info(f"isCoral: {is_coral}, isSponge: {is_sponge}, isRockfish: {is_rockfish}")
                    logging.info('rowIndex: ' + str(self._app.special_actions.rowIndex) + ', widgetType: ' + \
                                 str(self._app.special_actions.rowWidgetType))

                    model = self._app.special_actions.model

                    if is_coral or is_sponge:
                        # Coral / Sponge - find all of the sibling items, and in particular find the Parent Specimen ID item

                        if rowIndex != -1:
                            # A row is selected
                            parent_specimen_number = self._app.special_actions._model.get(rowIndex)["parentSpecimenNumber"]
                            for i in range(model.count):
                                if model.get(i)["parentSpecimenNumber"] == parent_specimen_number and \
                                        (model.get(i)["specialAction"] == "Coral Specimen ID" or \
                                                model.get(i)["specialAction"] == "Sponge Specimen ID"):
                                    model.setProperty(index=i, property="value", value=value)
                                    self._app.special_actions.upsert_specimen(row_index=i)
                                    break

                    else:

                        # 2019 Special Project - Peter Sudmant - Muscle Tissue Barcodes
                        if value > 500000000 and is_rockfish:
                            for i in range(model.count):
                                if model.get(i)["principalInvestigator"] == "Sudmant" and \
                                        model.get(i)["specialAction"] == "Tissue ID":
                                    model.setProperty(index=i, property="value", value=value)
                                    self._app.special_actions.upsert_specimen(row_index=i)
                                    break

                        # 2019 Pass 2 Special Project - John Wallace - Excision Site / Dry Vial Age Otolith
                        # WS - bug "QVariant" Object is not subscriptable - added rowIndex check
                        elif rowIndex != -1 and model.get(rowIndex)["principalInvestigator"] == "Wallace" and \
                            model.get(rowIndex)["specialAction"] == "Otolith Age ID":
                            if self._app.special_actions.if_exist_otolith_id(otolith_id = value):
                                pass # error - do not update UI
                            else:
                                model.setProperty(index=rowIndex, property="value", value=value)
                                self._app.special_actions.upsert_specimen(row_index=rowIndex)
                        else:

                            # Push to fish sampling screen
                            property = "ageNumber"
                            self._app.fish_sampling.update_list_item(property=property, value=value)

                except ValueError as ex:
                    pass

            elif measurement == "Length (cm)" or measurement == "Width (cm)" or measurement == "Weight (kg)":
                try:
                    value = float(value)
                    if rowIndex != -1 and self._app.special_actions.rowWidgetType == "measurement":
                        model = self._app.special_actions.model
                        model.setProperty(index=rowIndex, property="value", value=value)
                        self._app.special_actions.upsert_specimen(row_index=rowIndex)

                except ValueError as ex:
                    pass

    def port_status(self, serial_port, status):
        """

        :param serial_port:
        :param status:
        :return:
        """
        # Update the messages in the tvMessages tableview
        current_time = datetime.now().strftime("%Y%m%d %H:%M:%S")
        item = {"measurement": None, "value": None, "sentence": "COM" + str(serial_port) + \
                                                                ": " + status + \
                                                                " at " + str(current_time)}
        self._messages_model.appendItem(item)

        # Update the tvSerialPorts TableView to change actual status value
        row = self._serial_ports_model.get_item_index("serialPort", serial_port)
        if row >= 0 and row < self._serial_ports_model.count:
            self._serial_ports_model.setProperty(row, "status", status)

        # Update the portStatus, which emits a signals
        self._requested_port = serial_port
        self.portStatus = status            # This emits a portStatusChanged signal

    def exception_encountered(self, serial_port, msg):

        msgSplit = msg.split("\n")
        for m in msgSplit:
            self._messages_model.appendItem({"measurement": None, "value": None, "sentence": m})


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
