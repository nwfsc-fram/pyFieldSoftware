import sys
import logging
import winreg, itertools, glob
from datetime import datetime
import re
from copy import deepcopy

from PyQt5.QtCore import QVariant, pyqtProperty, pyqtSlot, pyqtSignal, QObject
from playhouse.shortcuts import model_to_dict, dict_to_model
from PyQt5.QtQml import QJSValue

from py.common.FramListModel import FramListModel
from py.hookandline.HookandlineFpcDB_model import database, TideStations, Sites, Lookups, \
    Equipment, DeployedEquipment, ParsingRules, JOIN


class ParsedSentencesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="column1")
        self.add_role_name(name="column2")
        self.add_role_name(name="column3")
        self.add_role_name(name="column4")
        self.add_role_name(name="column5")
        self.add_role_name(name="column6")
        self.add_role_name(name="column7")
        self.add_role_name(name="column8")
        self.add_role_name(name="column9")
        self.add_role_name(name="column10")
        self.add_role_name(name="column11")
        self.add_role_name(name="column12")


class RawSentencesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="sentence")


class TestSentencesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="sentence")


class ErrorMessagesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="date_time")
        self.add_role_name(name="com_port")
        self.add_role_name(name="message")
        self.add_role_name(name="resolution")
        self.add_role_name(name="exception")


class SensorConfigurationModel(FramListModel):

    def __init__(self, app=None):
        super().__init__()

        self._app = app
        self.add_role_name(name="data_status")
        self.add_role_name(name="start_stop_status")
        self.add_role_name(name="com_port")
        self.add_role_name(name="moxa_port")
        self.add_role_name(name="equipment")
        self.add_role_name(name="delete_row")
        self.add_role_name(name="baud_rate")
        self.add_role_name(name="data_bits")
        self.add_role_name(name="stop_bits")
        self.add_role_name(name="parity")
        self.add_role_name(name="flow_control")
        self.add_role_name(name="deployed_equipment_id")

        self.populate_model()

    def populate_model(self):
        """
        Method to retrieve all of the sensor configurations from the database
        deployed_equipment table and use them to populate the tvSensorConfiguration
         tableview on the SensorDataFeeds.qml screen
        :return:
        """
        self.clear()
        Organization = Lookups.alias()
        records = DeployedEquipment.select(DeployedEquipment, Equipment, Organization)\
            .join(Equipment)\
            .join(Organization, on=(Organization.lookup == Equipment.organization).alias('org'))\
            .where(DeployedEquipment.deactivation_date.is_null())\
            .order_by(DeployedEquipment.com_port.asc())
        for record in records:
            item = dict()
            item["equipment"] = record.equipment.org.value + " " + record.equipment.model
            # item["com_port"] = "COM{0}".format(record.com_port)
            item["com_port"] = record.com_port
            item["moxa_port"] = record.moxa_port
            item["data_status"] = "red"
            item["start_stop_status"] = "stopped"
            item["delete_row"] = ""
            item["baud_rate"] = record.baud_rate if record.baud_rate else 9600
            item["data_bits"] = record.data_bits if record.data_bits else 8
            item["parity"] = record.parity if record.parity else "None"
            item["stop_bits"] = record.stop_bits if record.stop_bits else 1
            item["flow_control"] = record.flow_control if record.flow_control else "None"
            item["deployed_equipment_id"] = record.deployed_equipment
            self.appendItem(item)
            self._app.serial_port_manager.add_thread(com_port_dict=item)

        self.setItems(sorted(self.items, key=lambda x: int(x["com_port"].strip("COM"))))

    @pyqtSlot(int, str, str, int, int, int, str, float, str)
    def add_row(self, equipment_id=None, equipment=None, com_port=None, moxa_port=None,
                baud_rate=9600, data_bits=8, parity="None", stop_bits=1, flow_control="None"):
        """
        Method called by the AddComportDialog.qml to add a new equipment/comport/moxaport
        entry into the tvSensorConfiguration tableview
        :param equipment_id: int
        :param equipment: str
        :param com_port: str - of the form:  COM4, COM5, etc.
        :param moxa_port: int
        :return:
        """
        if not isinstance(equipment_id, int) or \
            not re.search(r"^COM\d{1,3}$", com_port):
            logging.error("require equipment and comport to add a new row: {0}, {1}"
                          .format(equipment, com_port))
            return

        # Add to the database
        try:
            DeployedEquipment.insert(equipment=equipment_id,
                                 com_port=com_port,
                                 moxa_port=moxa_port,
                                 baud_rate=baud_rate,
                                 data_bits=data_bits,
                                 stop_bits=stop_bits,
                                 parity=parity,
                                 flow_control=flow_control,
                                 activation_date=datetime.now()).execute()
            deployed_equipment_id = DeployedEquipment.select()\
                .order_by(DeployedEquipment.deployed_equipment.desc()).get().deployed_equipment
        except Exception as ex:
            logging.info('Error inserting new sensor configuration: {0}'.format(ex))
            return

        # Add to the model
        item = dict()
        item["data_status"] = "red"
        item["start_stop_status"] = "stopped"
        item["delete_row"] = ""
        item["equipment"] = equipment
        item["com_port"] = com_port
        item["moxa_port"] = moxa_port
        item["deployed_equipment_id"] = deployed_equipment_id
        item["baud_rate"] = baud_rate
        item["data_bits"] = data_bits
        item["stop_bits"] = stop_bits
        item["parity"] = parity
        item["flow_control"] = flow_control
        self.appendItem(item)

        self.setItems(sorted(self.items, key=lambda x: int(x["com_port"].strip("COM"))))

        # Add to Serial Port Manager threads
        self._app.serial_port_manager.add_thread(com_port_dict=item)

    @pyqtSlot(str)
    def remove_row(self, com_port=None):
        """
        Method to remove the sensor configuration row from the SensorDataFeeds.qml
        tvSensorConfigurations tableview.  The comport to be removed is required
        :param comport: str
        :return:
        """
        if not re.search(r"^COM\d{1,3}$", com_port):
            return

        # Delete the thread - com_port should be of the form:  COM5
        self._app.serial_port_manager.delete_thread(com_port=com_port)

        # Remove from the model - com_port should be of the form:  COM5
        self.removeItem(index=self.get_item_index(rolename="com_port", value=com_port))

        # Delete from the database deployed_equipment table
        DeployedEquipment.update(deactivation_date=datetime.now()).where(DeployedEquipment.com_port == com_port).execute()

    @pyqtSlot(QVariant)
    def update_row(self, item=None):
        """
        Method to update the serial port settings for the given com_port.  Note that item is a dictionary
        of the following format:
            item = {"com_port": "COM3", "baud_rate": 9600, "data_bits": 8, "parity": "None",
                    "stop_bits": 1, "flow_control": "None"}

        :param item:
        :return:
        """
        if isinstance(item, QJSValue):
            item = item.toVariant()

        # Ensure that the newly proposed com_port doesn't already exist in this model
        # Logic for checking this is handled in the btnUpdate onClicked method

        # Convert to appropriate data types
        item["deployed_equipment_id"] = int(item["deployed_equipment_id"])
        item["baud_rate"] = int(item["baud_rate"])
        item["data_bits"] = int(item["data_bits"])
        item["stop_bits"] = float(item["stop_bits"])

        # Update the Database
        try:
            DeployedEquipment.update(com_port=item["com_port"], baud_rate=item["baud_rate"],
                                     data_bits=item["data_bits"], parity=item["parity"],
                                     stop_bits=item["stop_bits"], flow_control=item["flow_control"])\
                .where(DeployedEquipment.deployed_equipment == item["deployed_equipment_id"]).execute()
        except Exception as ex:
            logging.info('Error updating DeployedEquipment table: {0}'.format(ex))
            return

        # Update the model
        index = self.get_item_index(rolename="deployed_equipment_id", value=item["deployed_equipment_id"])

        if index != -1:
            old_com_port = self.get(index)["com_port"]
            old_start_stop_status = self.get(index)["start_stop_status"]

            for key in item:
                self.setProperty(index=index, property=key, value=item[key])
        else:
            logging.info('Unable to find the deployed_equipment_id in the model: {0}'.format(item["deployed_equipment_id"]))
            return

        self.setItems(sorted(self.items, key=lambda x: int(x["com_port"].strip("COM"))))

        # Delete the old thread
        self._app.serial_port_manager.delete_thread(com_port=old_com_port)

        # Add the new thread
        self._app.serial_port_manager.add_thread(com_port_dict=item)

        # Check if thread was previously started, if so, stop and restart it
        if old_start_stop_status == "started":
            self._app.serial_port_manager.start_thread(com_port=item["com_port"])


class ComportModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="lookup_id")
        self.add_role_name(name="com_port")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """
        Method to retrieve all of the equipment from the database equipment table
        and use them to populate the lvEquipment Listiew on the AddComportDialog.qml
        called from the SensorDataFeeds.qml screen
        :return:
        """
        self.clear()

        records = self.get_available_serial_ports()
        records = sorted(records, key=lambda port: int(port.strip("COM")))
        for record in records:
            item = dict()
            item["lookup_id"] = record
            item["com_port"] = record
            item["text"] = record
            self.appendItem(item)

    @staticmethod
    def get_available_serial_ports():
        """Lists serial ports

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of available serial ports
        """
        if sys.platform.startswith('win'):
            # ports = ['COM' + str(i + 1) for i in range(256)]
            ports = [i + 1 for i in range(256)]

        elif sys.platform.startswith('linux'):
            # this is to exclude your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')

        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')

        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        # for port in ports:
        # 	try:
        # 		print("Port Number: COM", str(port))
        # 		# s = serial.Serial(port)
        # 		s = serial.Serial(port='COM' + str(port), timeout=0.01)
        # 		s.close()
        # 		result.append(port)
        # 	except (OSError, serial.SerialException):
        # 		print('\tError occurred: ', str(serial.SerialException))
        # 		pass

        path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
            for i in itertools.count():
                try:
                    val = winreg.EnumValue(key, i)
                    # yield str(val[1])
                    # print(str(val[1].strip('COM')))
                    # result.append(int(val[1].strip('COM')))
                    result.append(val[1])
                except EnvironmentError:
                    break

        except WindowsError:
            logging.info(f"Error accessing serial ports in registry: {ex}")
            # raise WindowsError

        # print('Ports: ', str(result))

        return result


class EquipmentModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="equipment_id")
        self.add_role_name(name="equipment")
        self.add_role_name(name="equipment_type")

        self.populate_model()

    def populate_model(self):
        """
        Method to retrieve all of the equipment from the database equipment table
        and use them to populate the lvEquipment Listiew on the AddComportDialog.qml
        called from the SensorDataFeeds.qml screen
        :return:
        """
        self.clear()

        Make = Lookups.alias()
        Category = Lookups.alias()
        records = Equipment.select(Equipment, Make, Category)\
            .join(Make, on=(Make.lookup == Equipment.organization).alias('make'))\
            .switch(Equipment)\
            .join(Category, on=(Category.lookup == Equipment.equipment_category).alias('category'))\
            .where(Equipment.is_active == "True")\
            .order_by(Make.value.asc(), Equipment.name.asc(), Category.value.asc())
        for record in records:
            item = dict()
            item["equipment_id"] = record.equipment
            item["equipment"] = " ".join([record.make.value, record.model])
            item["equipment_type"] = record.category.value
            self.appendItem(item)


class MeasurementsModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="lookup_id")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """
        Method to retrieve all of the measurements form the database lookups table
        and use them to populate the cbMeasurement combobox on the NewMeasurementDialog.qml
        called from the SensorDataFeeds.qml screen
        :return:
        """
        self.clear()

        records = Lookups.select(Lookups.value, Lookups.lookup) \
            .where(Lookups.type == "Measurement", Lookups.is_active == "True")\
            .order_by(Lookups.value.asc()) \
            .group_by(Lookups.value)
        for record in records:
            item = dict()
            item["lookup_id"] = record.lookup
            item["text"] = record.value
            self.appendItem(item)

    def add_row(self, lookup_id, value):
        """
        Method to add a new measurement value to the model
        :param lookup_id:
        :param value:
        :return:
        """
        if not isinstance(lookup_id, int) or \
                not isinstance(value, str):
            return

        # First check if the value already exists in the model or not
        if self.get_item_index(rolename="text", value=value) == -1:

            item = dict()
            item["lookup_id"] = lookup_id
            item["text"] = value
            self.appendItem(item)
            self.sort(rolename="text")


class UnitsOfMeasurementModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="lookup_id")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """
        Method to retrieve all of the units of measurement from the database lookups table
        and use them to populate the cbUnitOfMeasurement combobox on the
        NewMeasurementDialog.qml that is called from the SensorDataFeeds.qml page
        :return:
        """
        self.clear()

        # TODO - Ensure that the units of measurement returned are unique
        records = Lookups.select(Lookups.subvalue, Lookups.lookup) \
            .where(Lookups.type == "Measurement", Lookups.is_active == "True") \
            .order_by(Lookups.subvalue.asc()) \
            .group_by(Lookups.subvalue)
        for record in records:
            item = dict()
            item["lookup_id"] = record.lookup
            item["text"] = record.subvalue
            self.appendItem(item)

    def add_row(self, lookup_id, subvalue):
        """
        Method to add a new row to UOM model that includes the lookup_id as well
        as the various units of measurement
        :param lookup_id:
        :param subvalue:
        :return:
        """
        if not isinstance(lookup_id, int) or \
            not isinstance(subvalue, str):
            return

        # First check if the subvalue already exists in the model or not
        if self.get_item_index(rolename="text", value=subvalue) == -1:
            item = dict()
            item["lookup_id"] = lookup_id
            item["text"] = subvalue
            self.appendItem(item)
            self.sort(rolename="text")


class MeasurementsUnitsOfMeasurementModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="lookup_id")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """
        Method to retrieve all of measurements + units of measurement from the database lookups table
        and use them to populate the cbMeasurement combobox on the SensorDataFeeds.qml page
        :return:
        """
        self.clear()
        records = Lookups.select(Lookups.value, Lookups.subvalue, Lookups.lookup)\
            .where(Lookups.type == "Measurement", Lookups.is_active == "True")\
            .order_by(Lookups.value.asc()) \
            .group_by(Lookups.value, Lookups.subvalue)
        for record in records:
            item = dict()
            item["lookup_id"] = record.lookup
            item["text"] = record.value + ", " + record.subvalue \
                if record.subvalue else record.value
            self.appendItem(item)

    def add_row(self, lookup_id, value, subvalue):
        """
        Method to add a new row to the model that includes the Lookup table components
        for a measurement type, i.e. the lookup_id, value (= measurement) and
        subvalue (= unit of measurement)
        :param lookup_id: int
        :param value: str
        :param subvalue: str
        :return:
        """
        if not isinstance(lookup_id, int) or \
            not isinstance(value, str) or \
            not isinstance(subvalue, str):
            return

        value_str = value + ", " + subvalue if subvalue else value
        if self.get_item_index(rolename="text", value=value_str) == -1:

            item = dict()
            item["lookup_id"] = lookup_id
            item["text"] = value_str
            self.appendItem(item)
            self.sort(rolename="text")


class MeasurementConfigurationModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="parsing_rules_id")
        self.add_role_name(name="equipment")
        self.add_role_name(name="line_starting")
        self.add_role_name(name="is_line_starting_substr")
        self.add_role_name(name="field_position")
        self.add_role_name(name="line_ending")
        self.add_role_name(name="measurement")
        self.add_role_name(name="priority")

        self.populate_model()

    def populate_model(self):
        """
        Method to populate the model by pull all active parsing methods from the
        ParsingRules table in the database
        :return:
        """
        self.clear()
        Measurements = Lookups.alias()
        Organizations = Lookups.alias()
        rules = ParsingRules.select(ParsingRules, Equipment, Measurements, Organizations)\
            .join(Measurements, JOIN.LEFT_OUTER, on=(Measurements.lookup == ParsingRules.measurement_lu).alias("measurement"))\
            .switch(ParsingRules)\
            .join(Equipment)\
            .join(Organizations, on=(Equipment.organization == Organizations.lookup).alias("org"))\
            .order_by(ParsingRules.priority.asc())

        for rule in rules:
            item = dict()
            item["parsing_rules_id"] = rule.parsing_rules
            item["equipment"] = "{0} {1}".format(rule.equipment.org.value, rule.equipment.model)
            item["line_starting"] = rule.line_starting
            item["is_line_starting_substr"] = rule.is_line_starting_substr
            item["field_position"] = rule.field_position
            item["line_ending"] = rule.line_ending
            item["measurement"] = "{0}, {1}".format(rule.measurement.value, rule.measurement.subvalue)
            item["priority"] = rule.priority
            self.appendItem(item)

    @pyqtProperty(QVariant)
    def line_startings(self):
        """
        Method to return all of the line_startings.  This is used to identify
        which sentences are needed for parsing values of interest, as defined
        by this model
        :return:
        """
        return list(set(x["line_starting"] for x in self.items))

    @pyqtSlot(str, result=QVariant)
    def sentence_rules(self, sentence):
        """
        Method to get all of the rules for the given sentence string
        :param sentence: str - the name of the sentence, e.g. $GPRMC, $IIGLL, etc.
        :return:
        """
        return [x for x in self.items if x["line_starting"] == sentence]

    @pyqtSlot(QVariant)
    def add_row(self, item):
        """
        Method to add a new row to the ParsingRules table
        :param item: dictionary containing the items used to populate ParsingRules and the model
        :return: None
        """

        if isinstance(item, QJSValue):
            item = item.toVariant()

        # Must have at least the following fields:
        if "equipment_id" not in item or \
                        "line_starting" not in item or \
                        "measurement_lu_id" not in item:
            logging.error("Failed to add a new measurement configuration, missing necessary keys: {0}".format(item))
            return

        for key in ["field_position", "start_position", "end_position",
                    "equipment_id", "measurement_lu_id"]:
            item[key] = int(item[key])

        # Insert into the ParsingRules tables of the database
        db_item = deepcopy({k: item[k] for k in item.keys() & {"equipment_id",
                                                      "line_starting",
                                                      "is_line_starting_substr",
                                                      "fixed_or_delimited",
                                                      "delimiter",
                                                      "field_position",
                                                      "start_position",
                                                      "end_position",
                                                      "line_ending",
                                                      "measurement_lu_id",
                                                      "priority"}})
        db_item["equipment"] = db_item.pop("equipment_id")
        db_item["measurement_lu"] = db_item.pop("measurement_lu_id")
        db_item["field_position"] = int(db_item["field_position"])

        try:
            new_rule = ParsingRules.create(**db_item)
        except Exception as ex:
            logging.error("Error adding a new measurement configuration: {0}".format(ex))
            return

        # Insert into the model
        model_item = deepcopy({k: item[k] for k in item.keys() & {"equipment", "line_starting", "is_line_starting_substr",
                                                         "field_position", "line_ending", "measurement", "priority"}})
        model_item["parsing_rules_id"] = new_rule.parsing_rules
        self.appendItem(model_item)
        self.sort(rolename="priority")

    @pyqtSlot(QVariant)
    def update_row(self, item):
        """
        Method to update a measurement configuration row in the model.  The input, an item, will contain the
        updated elements as well as the primary key to support an update
        :param item:
        :return:
        """
        if isinstance(item, QJSValue):
            item = item.toVariant()

        # Must have at least the following fields:
        if "equipment_id" not in item or \
                        "line_starting" not in item or \
                        "measurement_lu_id" not in item or \
                        "parsing_rules_id" not in item:
            logging.error("Failed to update an exist measurement configuration, missing necessary keys: {0}".format(item))
            return

        for key in ["field_position", "start_position", "end_position",
                    "equipment_id", "measurement_lu_id", "parsing_rules_id"]:
            item[key] = int(item[key])


        # Update the database
        db_item = deepcopy({k: item[k] for k in item.keys() & {"equipment_id",
                                                      "line_starting",
                                                      "is_line_starting_substr",
                                                      "fixed_or_delimited",
                                                      "delimiter",
                                                      "field_position",
                                                      "start_position",
                                                      "end_position",
                                                      "line_ending",
                                                      "measurement_lu_id",
                                                      "priority",
                                                      "parsing_rules_id"}})
        db_item["equipment"] = db_item.pop("equipment_id")
        db_item["measurement_lu"] = db_item.pop("measurement_lu_id")
        db_item["parsing_rules"] = db_item.pop("parsing_rules_id")


        try:
            ParsingRules.update(**db_item).where(ParsingRules.parsing_rules == db_item["parsing_rules"]).execute()
        except Exception as ex:
            logging.error("Error updating the measurement configuration: {0}".format(ex))
            return

        # Update the model
        model_item = deepcopy({k: item[k] for k in item.keys() & {"equipment", "line_starting", "is_line_starting_substr",
                                                         "field_position", "line_ending", "measurement", "priority",
                                                         "parsing_rules_id"}})
        index = self.get_item_index(rolename="parsing_rules_id", value=model_item["parsing_rules_id"])
        if index != -1:
            self.replace(index=index, item=model_item)
        self.sort(rolename="priority")

    @pyqtSlot(int)
    def delete_row(self, parsing_rules_id):
        """
        Method to delete a row from the model and ParsingRules tables
        :param item:
        :return:
        """
        if not isinstance(parsing_rules_id, int):
            logging.error("Failed to delete the parsing rule: {0}".format(parsing_rules_id))
            return

        # Remove from database
        ParsingRules.delete().where(ParsingRules.parsing_rules == parsing_rules_id).execute()

        # Remove from model
        index = self.get_item_index(rolename="parsing_rules_id", value=parsing_rules_id)
        if index != -1:
            self.removeItem(index=index)


class SensorDataFeeds(QObject):

    displayModeChanged = pyqtSignal()
    measurementsModelChanged = pyqtSignal()
    unitsOfMeasurementModelChanged = pyqtSignal()
    measurementsUomModelChanged = pyqtSignal(str, arguments=["value"])
    equipmentModelChanged = pyqtSignal()
    comportModelChanged = pyqtSignal()
    sensorConfigurationModelChanged = pyqtSignal()
    testSentencesModelChanged = pyqtSignal()
    rawSentencesModelChanged = pyqtSignal()
    parsedSentencesModelChanged = pyqtSignal()
    errorMessagesModelChanged = pyqtSignal()
    measurementConfigurationModelChanged = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

        self._display_mode = "operations"

        # Set up the various List Models used throughout the screen
        self._measurements_model = MeasurementsModel()
        self._units_of_measurement_model = UnitsOfMeasurementModel()
        self._measurements_uom_model = MeasurementsUnitsOfMeasurementModel()
        self._equipment_model = EquipmentModel()
        self._comport_model = ComportModel()
        self._sensor_configuration_model = SensorConfigurationModel(app=self._app)
        self._test_sentences_model = TestSentencesModel()
        self._raw_sentences_model = RawSentencesModel()
        self._parsed_sentences_model = ParsedSentencesModel()
        self._error_messages_model = ErrorMessagesModel()
        self._measurement_configuration_model = MeasurementConfigurationModel()

        # self._app.serial_port_manager.add_all_threads(sensor_config_model=self._sensor_configuration_model.items)

    @pyqtSlot(str, str)
    def add_new_measurement(self, measurement, unit_of_measurement):
        """
        Method called by the NewMeasurementDialog.qml via SensorDataFeeds.qml when a
        user wants to add a new measurement type.  This consists of the measurement name
        as well as the unit of measurement
        :param measurement: str - should be in the form:  Latitude - Vessel,  Time - UTC, etc.
        :param unit_of_measurement:  str - abbreviated unit of measurements, e.g. m, kg, km, etc.
        :return:
        """
        if not isinstance(measurement, str) or not isinstance(unit_of_measurement, str) or \
            measurement == "" or unit_of_measurement == "":
            logging.error("Invalid measurement of unit of measurement provided: {0}, {1}"
                          .format(measurement, unit_of_measurement))
            return

        # Insert into the Lookups table in the database
        try:
            # Lookups.insert(type="Measurement", value=measurement, subvalue=unit_of_measurement,
            #                is_active="True").execute()
            # lookup_id = Lookups.select().order_by(Lookups.lookup.desc()).get().lookup

            lookup, created = Lookups.get_or_create(
                type="Measurement", value=measurement, subvalue=unit_of_measurement, is_active="True"
            )
            lookup_id = lookup.lookup

        except Exception as ex:
            logging.error("failed to insert new measurement type: {0}".format(ex))

        # Add to the various models - measurements, uom, and measurementsUofm
        self._measurements_model.add_row(lookup_id=lookup_id, value=measurement)
        self._units_of_measurement_model.add_row(lookup_id=lookup_id, subvalue=unit_of_measurement)
        self._measurements_uom_model.add_row(lookup_id=lookup_id, value=measurement,
                                             subvalue=unit_of_measurement)

        # Emit a signal - this is used to auto-select this newly added measurement in SensorDataFeeds.qml
        self.measurementsUomModelChanged.emit("{0}, {1}".format(measurement, unit_of_measurement))

    @pyqtProperty(str, notify=displayModeChanged)
    def displayMode(self):
        """
        Method to return the self._display_mode.  This keeps track of what
        is display in SensorDataFeeds.qml, in the rightPanel.  Options include:

        - raw sentences
        - identify measurements

        :return:
        """
        return self._display_mode

    @displayMode.setter
    def displayMode(self, value):
        """
        Method to set the self._display_mode
        :param value:
        :return:
        """
        self._display_mode = value
        self.displayModeChanged.emit()

    @pyqtProperty(FramListModel, notify=measurementsModelChanged)
    def measurementsModel(self):
        """
        Method to return the self._measurements_model that is used by the
        SensorDataFeeds.qml cbMeasurement combobox that lists out the measurements
        to select when adding in NMEA sentence parsing instructions
        :return:
        """
        return self._measurements_model

    @pyqtProperty(FramListModel, notify=unitsOfMeasurementModelChanged)
    def unitsOfMeasurementModel(self):
        """
        Method to return the self._units_of_measurement_model that is used by the
        SensorDataFeeds.qml NewMeasurementDialog.qml cbUnitOfMeasurement combobox
        that lists out the units of measurement to select when adding a new
        measurement
        :return:
        """
        return self._units_of_measurement_model

    @pyqtProperty(FramListModel, notify=measurementsUomModelChanged)
    def measurementsUnitsOfMeasurementModel(self):
        """
        Method to return the self._measurements_uom_model that is used by the
        SensorDataFeeds.qml cbMeasurement combobox
        that lists out the measurements + units of measurement to
        select when adding a new matching item
        :return:
        """
        return self._measurements_uom_model

    @pyqtProperty(FramListModel, notify=equipmentModelChanged)
    def equipmentModel(self):
        """
        Method to return the self._equipment_model that is used by the
        SensorDataFeeds.qml AddComportDialog.qml lvEquipment listview
        that lists out the equipment from which to select when adding a new
        com port
        :return:
        """
        return self._equipment_model

    @pyqtProperty(FramListModel, notify=comportModelChanged)
    def comportModel(self):
        """
        Method to return the self._comport_model that is used by the
        SensorDataFeeds.qml AddComportDialog.qml tvComport tableview
        that lists out the comports from which to select when adding a new
        com port
        :return:
        """
        return self._comport_model

    @pyqtProperty(FramListModel, notify=sensorConfigurationModelChanged)
    def sensorConfigurationModel(self):
        """
        Method to return the self._sensor_configuration_model that is used by the
        SensorDataFeeds.qml tvSensorConfiguration tableview
        that lists out the equipment / comport / moxaport settings and is the primary
        tableview for the operations views
        :return:
        """
        return self._sensor_configuration_model

    @pyqtProperty(FramListModel, notify=testSentencesModelChanged)
    def testSentencesModel(self):
        """
        Method to return the self._test_sentences_model that is used by the
        SensorDataFeeds.qml tvTestSentences tableview
        that lists out raw sentence data in the Testing mode
        :return:
        """
        return self._test_sentences_model

    @pyqtProperty(FramListModel, notify=rawSentencesModelChanged)
    def rawSentencesModel(self):
        """
        Method to return the self._raw_sentences_model that is used by the
        SensorDataFeeds.qml tvRawSentences tableview
        that lists out raw sentence data in the Testing and Operations modes
        :return:
        """
        return self._raw_sentences_model

    @pyqtProperty(FramListModel, notify=parsedSentencesModelChanged)
    def parsedSentencesModel(self):
        """
        Method to return the self._parsed_sentences_model that is used by the
        SensorDataFeeds.qml tvParsedSentences tableview
        that lists out parsed sentence data in the Measurement mode
        :return:
        """
        return self._parsed_sentences_model

    @pyqtProperty(FramListModel, notify=errorMessagesModelChanged)
    def errorMessagesModel(self):
        """
        Method to return the self._error_messages_model that is used by the
        SensorDataFeeds.qml tvErrorMessages tableview
        that lists out serial port exceptions
        :return:
        """
        return self._error_messages_model

    @pyqtProperty(FramListModel, notify=measurementConfigurationModelChanged)
    def measurementConfigurationModel(self):
        """
        Return the self._measurement_configuration_model for use in
        SensorDataFeeds.qml
        :return:
        """
        return self._measurement_configuration_model