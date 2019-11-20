__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        LabelPrinter.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     May 8, 2016
# License:     MIT
#-------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QThread
import logging
from py.trawl.TrawlBackdeckDB_model import Specimen, TypesLu, Hauls, PrincipalInvestigatorLu, PiActionCodesLu, Settings
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
from datetime import datetime
import serial
import re
import arrow


class PrinterWorker(QObject):
    """
    Class to print labels on a background thread so as not to lock up the UI

    """
    printerStatus = pyqtSignal(str, bool, str)

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self.kwargs = kwargs
        self.comport = kwargs["comport"]
        self.rows = kwargs["rows"]
        # self.queue = kwargs["queue"]

        self._is_running = False
        self.result = {"comport": self.comport, "message": "", "success": False}

    def run(self):

        self._is_running = True

        # ser = serial.Serial()
        ser = serial.Serial(write_timeout=0, timeout=0)
        try:

            ser.port = self.comport
            ser.open()
            for row in self.rows:
                ser.write(row)
            ser.close()
            self.result["success"] = True
            self.result["message"] = "Everything printed fine"

            # self.queue.task_done()

        except OSError as ex:
            self.result["message"] = "Error printing: Unable to open the " + str(ser.portstr) + " port, please try another COM port"
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
    """
    Class for the LabelPrinter used to handle printing labels.
    """
    printerStatusReceived = pyqtSignal(str, bool, str, arguments=["comport", "success", "message"])
    tagIdChanged = pyqtSignal(str, arguments=["tag_id"])

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

        self._printer_thread = QThread()
        self._printer_worker = None

    @pyqtSlot(str, int, str, str)
    def print_job(self, comport, pi_id, action, specimen_number):
        """
        Great reference + example code for printing using EPL commands:
        https://www.xtuple.org/node/1083

        EPL Reference:
        https://www.zebra.com/content/dam/zebra/manuals/en-us/printer/epl2-pm-en.pdf

        :return:
        """
        if self._printer_thread.isRunning():
            return

        if specimen_number is None:
            return

        # Line 1 - Header
        header = "NOAA/NWFSC/FRAM - WCGBT Survey"

        # Line 2a - Principal Investigator
        try:
            investigator = PrincipalInvestigatorLu.select() \
                .where(PrincipalInvestigatorLu.principal_investigator == pi_id).get().last_name
        except DoesNotExist as ex:
            investigator = "PI Not Available"

        # Line 2b - Action Type
        # action - that was passed in

        # Line 3 - Haul #
        haul_id = self._app.state_machine.haul["haul_number"]
        if "t" in haul_id and len(haul_id) > 3:
            haul_id = "t" + haul_id[-4:]

        # Line 4 - Species Scientific Name
        species = self._app.state_machine.species["scientific_name"]

        # Line 5 - Length / Weight / Sex
        try:
            length = weight = sex = stomach = tissue = ovary = testes = ""
            parent_specimen = self._app.state_machine.specimen["parentSpecimenId"]
            specimens = (Specimen.select(Specimen, TypesLu)
                         .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias('types'))
                         .where(Specimen.parent_specimen == parent_specimen))
            for specimen in specimens:
                if "length" in specimen.types.type.lower():
                    length = specimen.numeric_value
                elif "weight" in specimen.types.type.lower():
                    weight = round(specimen.numeric_value, 2)
                elif "sex" in specimen.types.type.lower():
                    sex = specimen.alpha_value
                elif "stomach" in specimen.types.type.lower():
                    stomach = specimen.alpha_value
                elif "tissue" in specimen.types.type.lower():
                    tissue = specimen.alpha_value
                elif "ovary" in specimen.types.type.lower():
                    ovary = specimen.alpha_value
                elif "testes" in specimen.types.type.lower():
                    testes = specimen.alpha_value
        except DoesNotExist as ex:
            pass
        except Exception as ex:
            logging.info('Error creating the measurement line: ' + str(ex))
        measurement = "Len: " + str(length) + "cm, Wt: " + str(weight) + "kg, Sex: " + str(sex)

        # Line 3B - Shortened Specimen Number - on the same line as the haul ID
        short_specimen_number = ""
        try:
            if investigator == "FRAM":
                print_iteration = ""
                specimen_number_split = specimen_number.split("-")
                if len(specimen_number_split) == 5:
                    vessel_id = specimen_number_split[1]
                    spec_num = specimen_number_split[4]
                    if not specimen_number[-1:].isdigit():
                        print_iteration = specimen_number[-1]
                    if stomach != "" or tissue != "":
                        short_specimen_number = vessel_id + spec_num + print_iteration
                    elif ovary != "" or testes != "":
                        short_specimen_number = vessel_id + haul_id + spec_num + print_iteration
                short_specimen_number = ", Short #: " + short_specimen_number
        except Exception as ex:
            logging.error(f"Error creating the shortened specimen number: {ex}")


        # Line 7 - Latitude / Longitude / Depth             # location = "47 15.54N, 126 27.55W"
        try:
            haul = Hauls.select().where(Hauls.haul == self._app.state_machine.haul["haul_id"]).get()
            haul_start = haul.start_datetime
            latitude = haul.latitude_min
            longitude = haul.longitude_min
            depth = haul.depth_min
            depth_uom = haul.depth_uom

            if isinstance(depth, float) and depth_uom == "ftm":
                depth = 1.8288 * depth
            if latitude and longitude and depth:
                location = f"{latitude:.6f}, {longitude:.6f}, {depth:.1f}m"
            else:
                location = f"{latitude:.6f}, {longitude:.6f}, Unknown"
        except Exception as ex:
            location = "Unknown, Unknown, Unknown"

        # Line 6 - Date/Time
        try:
            date = datetime.now().strftime("%Y%m%d %H%M%S")            # date = "08/16/2015"
            date_year = datetime.now().year
            haul_dt = arrow.get(haul_start)
            haul_year = haul_dt.datetime.year
            logging.info(f"date_year={date_year}, haul_year={haul_year},     date={date} > haul_dt = {haul_dt}")
            if date_year != haul_year:
                haul_dt = haul_dt.format('YYYYMMDD HH:mm:ss')
                if haul_year > date_year:
                    date = haul_dt
            logging.info(f"new date: {date}")

        except Exception as ex:
            logging.info(f"error getting the proper date/time: {ex}")

        # Line 8 - Specimen number
        # If no character at the end, add an A, other increase the character by 1 and update the list item
        if specimen_number[-1:].isdigit():
            specimen_number += "A"
        else:
            char = chr(ord(specimen_number[-1:]) + 1)
            specimen_number = str(specimen_number[:-1]) + char

        # TODO Todd Hay Update_list_item - should I call back to special_actions.upsert here?
        # self.update_list_item(action_type, specimen_number)
        self.tagIdChanged.emit(specimen_number)

        # Line 9 - barcode_number
        # barcode_number = re.sub(r'[^\d.]+', '', specimen_number)
        # barcode_number = re.sub(r'[\W]+', '', specimen_number)      # strips the hyphens
        # barcode_number = specimen_number

        # Strip all hypens and alpha characters
        barcode_number = re.sub(r'[^\d]', '', specimen_number)

        # TODO Todd Hay - I might need to strip the - from the barcode to have it get properly encoded
        # Per p. 54 - printer specification (epl2 programming manual), hyphens may be used but they'll be ignored
        # barcode_number = int(specimen_number.strip('-'))

        # logging.info('specimen number: ' + str(specimen_number))
        # logging.info('barcode number: ' + str(barcode_number))

        suffix = "\"\n"
        lead_in = """
N
O
q500
S3
D10
ZT\n"""
        lead_in_bytes = bytes(lead_in, "UTF-8")

        count = 1
        lead_out = "\nP"+str(count)+"\n\n"  # lead out sends the label count (number to print)
        lead_out_bytes = bytes(lead_out, "UTF-8")

        header_bytes = bytes("A0,10,0,4,1,1,N,\"" + header + suffix, "UTF-8")
        investigator_bytes = bytes("A0,50,0,4,1,1,N,\"" + "PI: " + investigator + ", " + str(action) + suffix, "UTF-8")
        haul_id_bytes = bytes("A0,90,0,4,1,1,N,\"" + "Haul ID: " + str(haul_id) +
                              str(short_specimen_number) + suffix, "UTF-8")
        species_bytes = bytes("A0,130,0,4,1,1,N,\"" + "Species: " + species + suffix, "UTF-8")
        measurement_bytes = bytes("A0,170,0,4,1,1,N,\"" + measurement + suffix, "UTF-8")
        date_bytes = bytes("A0,210,0,4,1,1,N,\"" + "Date: " + str(date) + suffix, "UTF-8")
        location_bytes = bytes("A0,250,0,4,1,1,N,\"" + str(location) + suffix, "UTF-8")
        specimen_number_bytes = bytes("A0,290,0,4,1,1,N,\"" + "Spec #: " + str(specimen_number) + suffix, "UTF-8")
        barcode_bytes = bytes("B0,330,0,1,3,3,72,N,\"" + str(barcode_number) + suffix, "UTF-8")

        rows = [lead_in_bytes,
                header_bytes, investigator_bytes, haul_id_bytes, species_bytes,
                measurement_bytes, date_bytes, location_bytes, specimen_number_bytes,
                barcode_bytes,
                lead_out_bytes]

        if comport is None:
            comport = "COM9"

        kwargs = {"comport": comport, "rows": rows}

        self._printer_worker = PrinterWorker(kwargs=kwargs)
        self._printer_worker.moveToThread(self._printer_thread)
        self._printer_worker.printerStatus.connect(self._printer_status_received)
        self._printer_thread.started.connect(self._printer_worker.run)
        self._printer_thread.start()

    @pyqtSlot(str)
    def print_test_job(self, comport):
        """
        Method for printing out a test label to ensure that the printer is operational
        :return:
        """
        if not isinstance(comport, str) or comport == "":
            return

        header = "TEST TEST TEST Print"                             # Line 1 - Header
        investigator = "FRAM"                                       # Line 2a - PI
        action = "Action"                                           # Line 2b - Action
        haul_id = "210099888777"                                    # Line 3 - Haul #
        species = "Abyssal Crangon"                                 # Line 4 - Species Scientific Name
        measurement = "Len: 100cm, Wt: 60kg, Sex: M"                # Line 5 - Measurement
        date = datetime.now().strftime("%Y%m%d %H%M%S")             # Line 6 - Date/Time
        location = "Unknown, Unknown"                               # Line 7 - Latitude / Longitude
        specimen_number = "2100-001-001-001-001"                    # Line 8 - Specimen number
        barcode_number = re.sub(r'[^\d]', '', specimen_number)      # Line 9 - barcode_number

        suffix = "\"\n"
        lead_in = """
    N
    O
    q500
    S3
    D10
    ZT\n"""
        lead_in_bytes = bytes(lead_in, "UTF-8")

        count = 1
        lead_out = "\nP" + str(count) + "\n\n"  # lead out sends the label count (number to print)
        lead_out_bytes = bytes(lead_out, "UTF-8")

        header_bytes = bytes("A0,10,0,4,1,1,N,\"" + header + suffix, "UTF-8")
        investigator_bytes = bytes("A0,50,0,4,1,1,N,\"" + "PI: " + investigator + ", " + str(action) + suffix, "UTF-8")
        haul_id_bytes = bytes("A0,90,0,4,1,1,N,\"" + "Haul ID: " + str(haul_id) + suffix, "UTF-8")
        species_bytes = bytes("A0,130,0,4,1,1,N,\"" + "Species: " + species + suffix, "UTF-8")
        measurement_bytes = bytes("A0,170,0,4,1,1,N,\"" + measurement + suffix, "UTF-8")
        date_bytes = bytes("A0,210,0,4,1,1,N,\"" + "Date: " + str(date) + suffix, "UTF-8")
        location_bytes = bytes("A0,250,0,4,1,1,N,\"" + "Loc: " + str(location) + suffix, "UTF-8")
        specimen_number_bytes = bytes("A0,290,0,4,1,1,N,\"" + "Spec #: " + str(specimen_number) + suffix, "UTF-8")
        barcode_bytes = bytes("B0,330,0,1,3,3,72,N,\"" + str(barcode_number) + suffix, "UTF-8")

        rows = [lead_in_bytes,
                header_bytes, investigator_bytes, haul_id_bytes, species_bytes,
                measurement_bytes, date_bytes, location_bytes, specimen_number_bytes,
                barcode_bytes,
                lead_out_bytes]

        kwargs = {"comport": comport, "rows": rows}

        self._printer_worker = PrinterWorker(kwargs=kwargs)
        self._printer_worker.moveToThread(self._printer_thread)
        self._printer_worker.printerStatus.connect(self._printer_status_received)
        self._printer_thread.started.connect(self._printer_worker.run)
        self._printer_thread.start()

    def _printer_status_received(self, comport, success, message):
        """
        Method to catch the printer results
        :return:
        """
        self.printerStatusReceived.emit(comport, success, message)
        # logging.info('message received: ' + str(message))
        self._printer_thread.quit()

    @pyqtSlot(str, result=str)
    def get_tag_id(self, specimen_type):
        """
        Method to get a new tag ID
        :return:
        """
        mapping = {"ovaryNumber": {"type": "000", "action": "Ovary ID", "id": "ovarySpecimenId"},
                   "stomachNumber": {"type": "001", "action": "Stomach ID", "id": "stomachSpecimenId"},
                   "tissueNumber": {"type": "002", "action": "Tissue ID", "id": "tissueSpecimenId"},
                   "finclipNumber": {"type": "003", "action": "Finclip ID", "id": "finclipSpecimenId"}}
        if specimen_type not in mapping:
            return

        tag_id = None
        try:
            for setting in Settings.select():
                if setting.parameter == "Survey Year":
                    year = setting.value
                elif setting.parameter == "Vessel ID":
                    vessel_id = setting.value

            haul_number = str(self._app.state_machine.haul["haul_number"])
            if len(haul_number) > 3:
                haul_number = haul_number[-3:]

            try:
                pi_action_code_id = \
                    PiActionCodesLu.select(PiActionCodesLu) \
                        .join(PrincipalInvestigatorLu,
                              on=(PiActionCodesLu.principal_investigator == PrincipalInvestigatorLu.principal_investigator)) \
                        .join(TypesLu, on=(PiActionCodesLu.action_type == TypesLu.type_id).alias('types')) \
                        .where(PrincipalInvestigatorLu.full_name == "FRAM Standard Survey",
                               TypesLu.category == "Action",
                               TypesLu.type == mapping[specimen_type]["action"]).get().pi_action_code
            except DoesNotExist as ex:
                pi_action_code_id = 1

            specimen_type_id = str(pi_action_code_id).zfill(3)

            # Query for specimen number - get the latest one for the given specimen type (i.e. ovary, stomach, tissue, finclip)
            spec_num_length = 21
            specimens = (Specimen.select(Specimen, TypesLu)
                         .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias('types'))
                         .where(TypesLu.type == mapping[specimen_type]["action"],
                                TypesLu.category == "Action",
                                fn.length(Specimen.alpha_value) == spec_num_length).order_by(Specimen.alpha_value.desc()))

            # Get the newest specimen.  Note that one may not exist as it hasn't been created yet
            try:
                last_specimen_num = specimens.get().alpha_value
            except DoesNotExist as dne:
                last_specimen_num = None

            # Compare to the existing specimen type for the selected model item
            index = self._app.state_machine.specimen["row"]
            item = self._model.get(index)
            specimen_value = item[specimen_type]
            specimen_id = item[mapping[specimen_type]["id"]]

            """
            Use Cases
            1. No existing SPECIMEN record exists for this specimen_type - insert a new one by one-upping the
                last number for this specimen_type
            2. An existing SPECIMEN exists for this specimen_type - so a number should already be added, don't
               override then, correct?  We should only give the next number up ever after having queried the
               specimen table for the last number for this specimen_type - which is what we have in
               last_specimen_num
            """

            if specimen_id is None or specimen_id == "" or \
                            specimen_value is None or specimen_value == "" or len(specimen_value) != spec_num_length:
                # No specimen record exists for this specimen_type, so we're creating a new specimen_value
                # So one up the highest number and put an "a" at the end of it
                if last_specimen_num:
                    specimen_num = str(int(re.sub(r'[^\d.]+', '', last_specimen_num)[-3:]) + 1).zfill(3)
                else:
                    specimen_num = "001"
                print_version = "a"
            else:
                # Specimen record exists, then nothing to do here.  Clicking the print button will up the last
                # alpha character
                return specimen_value

            sep = "-"
            tag_id = year + sep + vessel_id + sep + haul_number + sep + specimen_type_id + \
                     sep + specimen_num  # + print_version

        except Exception as ex:
            logging.info('get_tag_id error: ' + str(ex))

        # logging.info('tag_id: ' + str(tag_id))

        return tag_id