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
from datetime import datetime
import re
from decimal import Decimal
from dateutil import parser
from xml.parsers.expat import ExpatError
from py.common.SerialDataParser import SerialDataParser
import unittest
# from py.trawl.TrawlBackdeckDB_model import DeployedEquipment, ParsingRules, TypesLu
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import *


class SerialPortsModel(FramListModel):

    def __init__(self, app=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="id")
        self.add_role_name(name="equipment")
        self.add_role_name(name="station")
        self.add_role_name(name="measurementName")
        self.add_role_name(name="unitOfMeasurement")
        self.add_role_name(name="comPort")
        self.add_role_name(name="baudRate")
        self.add_role_name(name="readerOrWriter")
        self.add_role_name(name="fixedOrDelimited")
        self.add_role_name(name="startPosition")
        self.add_role_name(name="endPosition")
        self.add_role_name(name="lineStarting")
        self.add_role_name(name="lineEnding")
        self.add_role_name(name="status")

        self.populate_model()

    def populate_model(self):
        """
        Method to populate the model
        :return:
        """
        self.clear()

        sql = "SELECT * FROM BACKDECK_SERIAL_PORTS WHERE STATION = ? ORDER BY COMPORT;"
        params = [self._app.state_machine._app_name,]
        comports = self._app.rpc.execute_query(sql=sql, params=params)
        keys = [v.decode('utf-8') for k, v in self.roleNames().items()]
        for values in comports:
            item = dict(zip(keys, values))
            self.appendItem(item=item)


class SerialPortWorker(QObject):

    exceptionEncountered = pyqtSignal(str, str)
    dataStatusChanged = pyqtSignal(int, str)
    dataReceived = pyqtSignal(str, str, str, str)

    def __init__(self, db=None, kwargs=None):
        super().__init__()

        self._db = db
        self.set_parameters(params=kwargs)

        self.ser = None

        self.is_streaming = False
        self._data_status = "red"
        self._meatball_count = 0

    def set_parameters(self, params):

        databits = {5: serial.FIVEBITS, 6: serial.SIXBITS, 7: serial.SEVENBITS, 8: serial.EIGHTBITS}
        parity = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD,
                  "Mark": serial.PARITY_MARK, "Space": serial.PARITY_SPACE}
        stopbits = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE, 2: serial.STOPBITS_TWO}
        flowcontrol = {"None": False, "Off": serial.XOFF, "On": serial.XON}

        # self.deployedEquipmentId = params["deployedEquipmentId"]
        self.comPort = params["comPort"]
        self.baudRate = params["baudRate"]
        self.measurementName = params["measurementName"]
        # self.dataBits = databits[params["dataBits"]]
        # self.parity = parity[params["parity"]]
        # self.stopBits = stopbits[params["stopBits"]]
        # self.flowControl = flowcontrol[params["flowControl"]]
        # self.measurementTypeId = params["measurementTypeId"]
        # self.equipmentId = params["equipmentId"]
        self.equipment = params["equipment"]
        self.status =  params["status"]
        self.rule = {
            "fixedOrDelimited": params["fixedOrDelimited"] if "fixedOrDelimited" in params else None,
            "startPos": params["startPosition"] if "startPosition" in params else None,
            "endPos": params["endPosition"] if "endPosition" in params else None,
            "lineStarting": params["lineStarting"] if "lineStarting" in params else None,
            # "lineEnding": params["lineEnding"] if "lineEnding" in params else None,
            "lineEnding": re.compile('\r?\n?'),
            "delimiter": params["delimiter"] if "delimiter" in params else None,
            "fieldNum": params["fieldPosition"] if "fieldPosition" in params else None,
            "uom": params["unitOfMeasurement"] if "unitOfMeasurement" in params else None
        }

        # TODO Todd Hay - why is \r\n not working for parsing the ending?
        # ending = re.compile(self.rule["line_ending"].encode().decode("unicode-escape"))
        # endingBefore = ending
        # ending = re.compile('\r?\n?')

        self.dataStatus = params["dataStatus"] if "dataStatus" in params else "red"

    @pyqtProperty(str, notify=dataStatusChanged)
    def dataStatus(self):
        return self._data_status

    @dataStatus.setter
    def dataStatus(self, value):
        self._data_status = value
        self.dataStatusChanged.emit(self.comPort, value)

    def start(self):
        self.is_streaming = True

    def stop(self):
        self.is_streaming = False

    def read(self):

        if len(self.rule) == 0:
            logging.info('rule length is 0: ' + str(self.rule))
            # logging.info("equipment: " + str(self.equipment) + " >>> measurement: " + str(self.measurementName))
            return

        self.start()
        self.dataStatus = "red"

        buffer = ""
        split_data = ""
        sentence = ""

        try:
            self.ser = Serial(baudrate=self.baudRate, timeout=5)
            self.ser.port = self.comPort
            self.ser.open()

            start_time = time.clock()
            # end_time = start_time

            while True:

                if not self.is_streaming:
                    break

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

                if self.rule["lineEnding"].search(buffer):

                    lines = self.rule["lineEnding"].split(buffer)
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
                        if self.rule["fixedOrDelimited"].lower() == "fixed":
                            value = sentence[self.rule["startPos"]:self.rule["endPos"]+1].strip()
                            # if "caliper" in self.equipmentName.lower() and \
                            #         "width (cm)" in self.measurementName.lower():
                            # logging.info('uom: ' + str(uom) + ', measurementName: ' + str(self.measurementName))
                            # if self.rule["uom"] == "mm" and "width (cm)" in self.measurementName.lower():
                            #     # Convert from mm to cm
                            #     # TODO Todd Hay - this works, but not very elegant to hardcode in code in this
                            #     # Should I store the units of measurement in PARSING_RULES as well and then
                            #     # have a converter class to call, comparing measurementName to uom, probably so
                            #     try:
                            #         value = "%.2f" % (float(value.strip())/10.0)
                            #     except Exception as ex:
                            #         logging.error('parse error, value: {0}, rule: {1}'.format(value, self.rule))
                            #         value = None

                        else:
                            value = sentence.split(self.rule["delimiter"])[self.rule["fieldNum"]].strip()

                        # Emit the sentence
                        self.dataReceived.emit(self.comPort, self.measurementName, sentence, value)

                        if self.dataStatus != "green":
                            self.dataStatus = "green"

                        self._meatball_count = 0

                    buffer = ""

                # end_time = time.clock()

        except SerialException as ex:

            msg = f"{self.comPort} SerialException error\n\n{ex}\n"
            msg = msg.replace(":", ":\n")

            if "ClearCommError" in str(ex):
                msg += "\n   Port Lost > You just lost this port"

            elif "FileNotFoundError" in str(ex):
                msg += "\n   Inactive Port > Please select a different port"

            elif "PermissionError" in str(ex):
                msg += "\n   Port Already Open > The port is open in another program"

            elif "OSError(22, 'Insufficient system resources exist" in str(ex):
                msg += "\n   Unrecognized Port > The COM port is not recognized on this system"

            self.stop()
            if self._data_status != "red":
                self.dataStatus = "red"

            self.exceptionEncountered.emit(self.comPort, msg)

            return

        except Exception as ex:

            msg = f"{self.comPort} General Exception Error\n\n{ex}"
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

            logging.info(f"exception encountered: {self.comPort}, {msg}")
            self.exceptionEncountered.emit(self.comPort, msg)

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
    comPortStatusChanged = pyqtSignal(str, str, arguments=["comPort", "status"])
    exceptionEncountered = pyqtSignal(str, str, arguments=["comPort", "msg"])
    dataReceived = pyqtSignal(str, QVariant, str, bool, arguments=["action", "value", "uom", "dbUpdate"])
    printerChanged = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db
        self._printers = {}

        self._serial_ports_model = SerialPortsModel(app=self._app)

        self._threads = {}
        self._workers = {}

        self.add_all_threads()
        self.start_all_threads()

    @pyqtProperty(QVariant, notify=modelChanged)
    def serialPortsModel(self):
        """
        Return the model
        :return:
        """
        return self._serial_ports_model

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

    def add_all_threads(self):
        """
        Method used during initialization to create all of the threads that based on data pulled from
        the database
        :return: list - of dictionaries of the threads
        """
        readers = [x for x in self._serial_ports_model.items if x["readerOrWriter"].lower() == "reader"]
        for s in readers:
            self.add_thread(s)

    @pyqtSlot(QVariant)
    def add_thread(self, serial_dict):
        """
        Method to add a new serial port thread
        :return:
        """
        if serial_dict["comPort"] in self._threads:
            logging.info('Serial port ' + str(serial_dict["comPort"]) + ' is already taken')
            return

        com_port = serial_dict["comPort"]
        self._threads[com_port] = QThread()
        self._workers[com_port] = SerialPortWorker(db=self._db, kwargs=serial_dict)
        self._workers[com_port].moveToThread(self._threads[com_port])
        self._workers[com_port].dataReceived.connect(self.data_received)
        self._workers[com_port].dataStatusChanged.connect(self.port_status)
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
                row = self._serial_ports_model.get_item_index("comPort", com_port)
                if row >= 0 and row < self._serial_ports_model.count:
                    self._serial_ports_model.setProperty(row, "status", "Started")
                    logging.info(f"started {com_port}, thread is running? {thread.isRunning()}")

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
            self._threads[com_port].exit()
            row = self._serial_ports_model.get_item_index("comPort", com_port)
            if row >= 0 and row < self._serial_ports_model.count:
                self._serial_ports_model.setProperty(row, "status", "Stopped")
                logging.info(f"stopped {com_port}, thread is running? {self._threads[com_port].isRunning()}")

    def delete_all_threads(self):
        for port in self._threads:
            self.delete_thread(com_port=port)

    @pyqtSlot(int)
    def delete_thread(self, com_port):
        """
        Method to delete a serial port thread
        :return:
        """
        if self._threads[com_port].isRunning():
            self.stop_thread(com_port=com_port)

        start_time = time.clock()
        while self._threads[com_port].isRunning():

            if end_time - start_time >= 5:
                break
            end_time = time.clock()

        self._threads.pop(com_port, None)
        self._workers.pop(com_port, None)

    @pyqtSlot(str, str, str, str, name="serialTest")
    def data_received(self, com_port, measurement, data, value):
        """
        :param com_port: int - representing the serial port on which data is received
        :param measurement: str -
        :param data: str - the actual data received
        :param value: str - parsed value - note that it is a string and has not been converted yet
        :return:
        """
        currentEntryTab = self._app.state_machine.currentEntryTab
        logging.info(f"DATA_RECEIVED: currentEntryTab={currentEntryTab} > {com_port}, {value}, {measurement}")

        try:
            idx = self._serial_ports_model.get_item_index(rolename="comPort", value=com_port)
            logging.info(f"\tcomport row in model: {idx}")
            if idx != -1:
                measurement_name = self._serial_ports_model.get(idx)["measurementName"]

                logging.info(f"\tmeasurement_name={measurement_name}, currentEntryTab={currentEntryTab}")
                if (measurement_name == "Weight" and currentEntryTab == "weight") or \
                    (measurement_name == "Barcode" and currentEntryTab == "adh"):
                    uom = ""
                    if measurement_name == "Weight":
                        uom = "kg"
                        try:
                            non_decimal = re.compile(r'[^\d.]+')
                            value = non_decimal.sub('', value)
                            # value = value.strip('kg ') # In case the parsing is off and we have the k or kg in there
                            value = float(value)
                            value = round(value, 2)
                        except Exception as ex:

                            # self.exceptionEncountered.emit(com_port, f"Unable to parse the weight as a float\nvalue = {value}")
                            logging.error(f"\terror converting the received weight ({value}) to a float: {ex}")

                    logging.info(f"\tdata emitted to entry dialog: {currentEntryTab} = {value}")
                    self.dataReceived.emit(currentEntryTab, value, uom, False)

                    # Play Sound
                    # try:
                    #     if measurement_name == "Weight":
                    #         sound_name = "takeWeight"
                    #         self._app.sound_player.play_sound(sound_name=sound_name)
                    #     elif measurement_name == "Barcode": # and currentEntryTab == "adh":
                    #         sound_name = "takeBarcode"
                    #         self._app.sound_player.play_sound(sound_name=sound_name)
                    # except Exception as ex:
                    #     logging.error(f"\tfailed to play the sound when taking a weight or adh barcode: {ex}")

        except Exception as ex:

            logging.error(f"Error receiving serial port data: {ex}")

    def port_status(self, com_port, status):
        """

        :param com_port:
        :param status:
        :return:
        """
        # Update the tvSerialPorts TableView to change actual status value
        row = self._serial_ports_model.get_item_index("comPort", com_port)
        if row >= 0 and row < self._serial_ports_model.count:
            self._serial_ports_model.setProperty(row, "status", status)

    def exception_encountered(self, com_port, msg):

        self.stop_thread(com_port=com_port)
        self.exceptionEncountered.emit(com_port, msg)
        logging.info(f"error in {com_port}, thread is running? {self._threads[com_port].isRunning()}")


    #####################################################################
    # Legacy methods, probably can delete
    #####################################################################

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
            # rule = ParsingRules.select().where((ParsingRules.measurement_type == data["measurementTypeId"]) &
            #                                    (ParsingRules.equipment == data["equipmentId"]))
            rule = None
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


class TestSPM(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        pass
        # self.s = SerialPortManager()

    # def testReadPorts(self):
    #
    #     mtypes = [178, 179]
    #     ports = DeployedEquipment.select().where(DeployedEquipment.measurement_type << mtypes)
    #     # self.assertGreaterEqual(len(ports), 10)
    #     for port in ports:
    #         self.assertIsNotNone(port)
    #
    #         logging.info(str(model_to_dict(port)))
