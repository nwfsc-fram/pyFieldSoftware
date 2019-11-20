import logging
import serial
from datetime import datetime
import re
import time
import arrow
import math
from queue import Queue

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QVariant, QThread
from PyQt5.QtQml import QJSValue


class PrinterWorker(QObject):
    """
    Class to print labels on a background thread so as not to lock up the UI

    """
    printerStatus = pyqtSignal(str, bool, str)

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self.kwargs = kwargs
        self.comport = kwargs["comport"]
        self.rows = kwargs["rows"] if "rows" in kwargs else None
        self.queue = kwargs["queue"] if "queue" in kwargs else None

        self._is_running = False
        self.result = {"comport": self.comport, "message": "", "success": False}

    def run(self):

        self._is_running = True
        ser = serial.Serial(write_timeout=0, timeout=0)
        try:

            ser.port = self.comport
            ser.open()
            while not self.queue.empty():
                rows = self.queue.get()
                for row in rows:
                    logging.info(f"row={row}")
                    ser.write(row)

            # OLD cold that works one at a time
            # ser.port = self.comport
            # ser.open()
            # for row in self.rows:
            #     ser.write(row)

            ser.close()
            self.result["success"] = True
            self.result["message"] = "Everything printed fine"

        except OSError as ex:
            self.result["message"] = "Error printing: Unable to open " + str(ser.portstr) + " port, please try another COM port"
            self.result["success"] = False
            logging.info(self.result["message"])
            if ser.isOpen():
                ser.close()

        except Exception as ex:
            self.result["message"] = "Error printing to " + str(ser.portstr) + ": " + str(ex)
            self.result["success"] = False
            logging.info(self.result["message"])
            if ser.isOpen():
                ser.close()

        self._is_running = False
        self.printerStatus.emit(self.comport, self.result["success"], self.result["message"])


class LabelPrinter(QObject):

    printerStatusReceived = pyqtSignal(str, bool, str, arguments=["comport", "success", "message"])

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db
        self._printer_thread = QThread()
        self._printer_worker = None
        self._queue = Queue()

        self._is_running = False

    @pyqtSlot()
    def stopPrintJobs(self):
        """
        Method to stop the print jobs when the application is trying to be closed
        :return:
        """
        self._is_running = False

    def _print_job(self, equipment=None, rows=None):
        """
        Method to start the printing thread
        :param equipment: Name of the printer equipment, as found in the Serial Port Manager serialPortsModel
        :param rows: List of rows to print
        :return:
        """
        # if self._printer_thread.isRunning():
        #     logging.info(f"The printer thread is already running, waiting for it to conclude")
        self._is_running = True

        # start_time = time.clock()
        # while self._printer_thread.isRunning():
        #     if not self._is_running:
        #         return
        #
        #     current_time = time.clock()
        #     if current_time - start_time > 5:
        #         logging.error(f"Printer thread is taking too long to complete, exiting printing")
        #         return

        try:
            if self._printer_thread.isRunning():
                self._queue.put(rows)

            else:

                model = self._app.serial_port_manager.serialPortsModel
                idx = model.get_item_index(rolename="equipment", value=equipment)
                if idx != -1:
                    comport = model.get(idx)["comPort"]

                    logging.info(f"Printing to comport={comport}")

                    self._queue.put(rows)
                    kwargs = {"comport": comport, "rows": rows, "queue": self._queue}

                    self._printer_worker = PrinterWorker(kwargs=kwargs)
                    self._printer_worker.moveToThread(self._printer_thread)
                    self._printer_worker.printerStatus.connect(self._printer_status_received)
                    self._printer_thread.started.connect(self._printer_worker.run)
                    self._printer_thread.start()

        except Exception as ex:

            logging.error(f"Error getting the comport: {ex}")

    def _printer_status_received(self, comport, success, message):
        """
        Method to catch the printer results
        :return:
        """
        self.printerStatusReceived.emit(comport, success, message)
        self._printer_thread.quit()

    @pyqtSlot(str, str, str, str, str, name="printADHLabel")
    def print_hookandline_angler_drop_hook(self, equipment: str, angler: str, drop: str, hook: str, species: str):
        """
        Method for printing an Angler/Drop/Hook tag
        :param angler:
        :param drop:
        :param hook:
        :return:
        """
        # Lines of Data to Print
        site = self._app.state_machine.site.zfill(3) if self._app.state_machine.site else ""
        set_id = self._app.state_machine.setId if self._app.state_machine.setId else ""
        # species also used, from the input variable
        barcode_number = angler + drop + hook
        lead_in = """
N
O
q500
S3
D10
ZT\n"""
        lead_out = "\nP" + str(1) + "\n\n"  # lead out sends the label count (number of labels to print)

        # suffix = "\"\n"

        # Convert all of the rows to bytes
        lead_in_bytes = bytes(lead_in, "UTF-8")
        site_bytes = bytes("A0,10,0,4,1,1,N,\"Site Name: " + site + "\"\n", "UTF-8")
        set_id_bytes = bytes("A0,50,0,4,1,1,N,\"Set ID: " + set_id + "\"\n", "UTF-8")
        species_bytes = bytes("A0,90,0,4,1,2,N,\"" + species + "\"\n", "UTF-8")
        angler_drop_hook_bytes = bytes("A0,150,0,5,1,2,N,\"" + str(barcode_number) + "\"\n", "UTF-8")
        barcode_bytes = bytes("B0,250,0,1,3,3,100,N,\"" + str(barcode_number) + "\"\n", "UTF-8")
        lead_out_bytes = bytes(lead_out, "UTF-8")

        rows = [lead_in_bytes,
                site_bytes, set_id_bytes, species_bytes, angler_drop_hook_bytes, barcode_bytes,
                lead_out_bytes]

        if equipment is None:
            equipment = "Zebra Printer Aft"

        # logging.info(f"print ADH: {equipment}")
        # for row in rows:
        #     logging.info(f"row={row}")

        self._print_job(equipment=equipment, rows=rows)

    @pyqtSlot(str, str, QVariant, str, name="printHookAndLineTagNumber")
    def print_hookandline_tag_number(self, tag_number, observation, species_observations, project):
        """
        Great reference + example code for printing using EPL commands:
        https://www.xtuple.org/node/1083

        EPL Reference:
        https://www.zebra.com/content/dam/zebra/manuals/en-us/printer/epl2-pm-en.pdf

        :return:
        """

        if isinstance(species_observations, QJSValue):
            species_observations = species_observations.toVariant()

        # Lines of Data to Print
        date_time = arrow.now().to("US/Pacific").format("YYYYMMDD_HHmmss")
        site = self._app.state_machine.site.zfill(3) if self._app.state_machine.site else ""
        set_id = self._app.state_machine.setId if self._app.state_machine.setId else ""
        vessel = self._app.state_machine.vessel if self._app.state_machine.vessel else ""

        try:
            sql = """
                SELECT s.LATITUDE, s.LONGITUDE from SITES s
                    INNER JOIN OPERATIONS o ON o.SITE_ID = s.SITE_ID
                    WHERE o.OPERATION_ID = ?;
            """
            params = [self._app.state_machine.siteOpId, ]
            results = self._app.rpc.execute_query(sql=sql, params=params)
            latitude = longitude = ""
            if len(results) == 1:
                result = results[0]
                latitude = self.dd_to_formatted_lat_lon(type="latitude", value=result[0])
                longitude = self.dd_to_formatted_lat_lon(type="longitude", value=result[1])
        except Exception as ex:
            logging.error(f"Error retrieving the latitude and longitude: {ex}")

        depth = " m"
        species = species_observations["species"] if species_observations["species"] else ""
        length = species_observations["length"] + " cm" if species_observations["length"] else ""
        weight = species_observations["weight"] + " kg" if species_observations["weight"] else ""
        sex = species_observations["sex"] if species_observations["sex"] else ""
        pi = ""

        row1 = f"{date_time}    Site: {site}"
        row2 = f"SetID: {set_id}    {vessel}"
        row3 = f"{latitude}    {longitude}"
        # row4 = f"{depth}    {species}"
        row4 = f"{species}"
        row5 = f"{project}   {observation}"
        row6 = f"{length}   {weight}   {sex}"
        # row7 = f"{pi}    Barcode: {tag_number}"
        row7 = f"Barcode: {tag_number}"

        lead_in = """
N
O
q500
S3
D10
ZT\n"""
        lead_out = "\nP" + str(1) + "\n\n"  # lead out sends the label count (number of labels to print)

        # Convert all of the rows to bytes
        lead_in_bytes = bytes(lead_in, "UTF-8")
        row1_bytes = bytes("A0,10,0,4,1,1,N,\"" + row1 + "\"\n", "UTF-8")
        row2_bytes = bytes("A0,50,0,4,1,1,N,\"" + row2 + "\"\n", "UTF-8")
        row3_bytes = bytes("A0,90,0,4,1,1,N,\"" + row3 + "\"\n", "UTF-8")
        row4_bytes = bytes("A0,130,0,4,1,1,N,\"" + row4 + "\"\n", "UTF-8")
        row5_bytes = bytes("A0,170,0,4,1,1,N,\"" + row5 + "\"\n", "UTF-8")
        row6_bytes = bytes("A0,210,0,4,1,1,N,\"" + row6 + "\"\n", "UTF-8")
        row7_bytes = bytes("A0,250,0,4,1,1,N,\"" + row7 + "\"\n", "UTF-8")
        barcode_bytes = bytes("B0,290,0,1,3,3,90,N,\"" + str(tag_number) + "\"\n", "UTF-8")
        lead_out_bytes = bytes(lead_out, "UTF-8")

        rows = [lead_in_bytes,
                row1_bytes, row2_bytes, row3_bytes, row4_bytes, row5_bytes, row6_bytes, row7_bytes,
                barcode_bytes,
                lead_out_bytes]

        for row in rows:
            logging.info(f"label row: {row}")

        self._print_job(equipment="Zebra Printer Cutter", rows=rows)

    def dd_to_formatted_lat_lon(self, type, value):
        """
        Method to convert a latitude in decimal degrees to well-formatted string
        :param type: str - enumerate value:  latitude / longitude
        :param value:
        :return:
        """
        if not isinstance(value, float):
            logging.error("Error formatting latitude to nice format: {0}".format(value))
            return str(value)

        min, deg = math.modf(value)
        min *= 60
        deg = int(deg)

        if type == "latitude":
            uom = "S" if value < 0 else "N"
        else:
            uom = "W" if value < 0 else "E"

        if uom in ["S", "W"] and deg <= 0 and min <= 0:
            deg = -deg
            min = -min

        return f"{deg:d} {min:6.3f}' {uom}"

        return f"{deg:d}\xb0 {min:6.3f}' {uom}"


        # return "{:d}".format(deg) + u"\xb0" + " " + "{:06.3f}".format(min) + "' " + uom