__author__ = 'Todd.Hay'
# -----------------------------------------------------------------------------
# Name:        rSettings.py
# Purpose:     Global settings data (Observer)
#
# Author:      Todd Hay <todd.haynoaa.gov>
#
# Created:     Aug 26, 2016
# License:     MIT
# ------------------------------------------------------------------------------

import time

from PyQt5.QtCore import pyqtProperty, QObject, QVariant, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtQml import QJSValue
from dateutil import parser
import logging
import unittest

from py.common.FramListModel import FramListModel
from py.hookandline.HookandlineFpcDB_model import Settings as SettingsTable, Personnel, Lookups
from py.hookandline.HookandlineFPCConfig import HOOKLOGGER_VERSION
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict, dict_to_model
from py.hookandline.DataConverter import DataConverter

SOFTWARE_VERSION = HOOKLOGGER_VERSION

class ComPortsModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="displayText")

        self.populate_model()

    def populate_model(self):

        for i in range(1,256):
            item = dict()
            item["displayText"] = "COM" + str(i)
            self.appendItem(item)


class BaudRatesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="displayText")

        self.populate_model()

    def populate_model(self):

        for x in [1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 56000, 57600, 115200]:
            item = dict()
            item["displayText"] = x
            self.appendItem(item)


class ScientistsModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="personnel")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()
        results = Personnel.select().where(Personnel.is_active == "True",
                                           Personnel.is_science_team == "True")\
            .order_by(Personnel.last_name.asc(), Personnel.first_name.asc())
        for result in results:
            item = dict()
            item["personnel"] = result.personnel
            item["text"] = result.last_name + ", " + result.first_name
            self.appendItem(item)


class CrewModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="personnel")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()
        results = Personnel.select().where(Personnel.is_active == "True",
                                           Personnel.is_science_team == "False")\
            .order_by(Personnel.last_name.asc(), Personnel.first_name.asc())
        for result in results:
            item = dict()
            item["personnel"] = result.personnel
            item["text"] = result.last_name + ", " + result.first_name
            self.appendItem(item)


class VesselsModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="id")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()
        results = Lookups.select().where(Lookups.is_active == "True",
                                         Lookups.type == "Vessel Number") \
            .order_by(Lookups.value.asc())

        for result in results:
            item = dict()
            item["id"] = result.lookup
            item["text"] = result.description
            self.appendItem(item)


class SettingsModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="settings")
        self.add_role_name(name="parameter")
        self.add_role_name(name="type")
        self.add_role_name(name="value")
        self.add_role_name(name="is_active")
        self.add_role_name(name="new_value")
        self.add_role_name(name="delegate_type")
        self.add_role_name(name="model_type")

        self._dc = DataConverter()

        self.populate_model()

    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()
        results = SettingsTable.select().where(SettingsTable.is_active == "True")\
            .order_by(SettingsTable.parameter.asc())

        for result in results:
            # item = dict()
            # item["settings_id"] = result.settings
            # item["parameter"] = result.parameter
            # item["value"] = result.value
            item = model_to_dict(result)

            item["delegate_type"] = "TextField"

            if item["parameter"] in ["Leg 1 Start", "Leg 1 End", "Leg 2 Start", "Leg 2 End"]:
                # Convert to mm/dd/yyyy format
                item["value"] = self._dc.iso_to_common_date_format(item["value"])

            elif any(substring in item["parameter"] for substring in ["Leg 1 FPC", "Leg 2 FPC",
                                                                      "Scientist 1", "Scientist 2",
                                      "Scientist 3", "Captain", "Second Captain", "Cook", "Deckhand 1",
                                      "Deckhand 2", "Deckhand 3"]):

                item["delegate_type"] = "ComboBox"
                if any(substring in item["parameter"] for substring in ["FPC", "Scientist 1",
                                        "Scientist 2", "Scientist 3"]):
                    item["model_type"] = "Scientists"
                    is_science_team = "True"

                else:
                    item["model_type"] = "Crew"
                    is_science_team = "False"
                try:
                    person = Personnel.get(Personnel.personnel == item["value"],
                                           Personnel.is_science_team == is_science_team)
                    item["value"] = person.last_name + ", " + person.first_name

                except Exception as ex:
                    item["value"] = ""

            elif item["parameter"] in ["Vessel"]:
                item["delegate_type"] = "ComboBox"
                item["model_type"] = "Vessels"
                try:
                    lookup = Lookups.get(Lookups.lookup == item["value"])
                    item["value"] = lookup.description
                except Exception as ex:
                    item["value"] = ""

            elif item["parameter"] in ["Backup Folder"]:
                item["delegate_type"] = "FolderBrowser"

            elif item["parameter"] == "Depth Output Serial Port":
                item["model_type"] = "ComPorts"
                item["delegate_type"] = "DialogListView"

            elif item["parameter"] == "Depth Output Serial Port Baud Rate":
                item["model_type"] = "BaudRates"
                item["delegate_type"] = "DialogListView"

            elif item["parameter"] == "Depth Output Serial Port Status":
                item["delegate_type"] = "Switch"

            item["new_value"] = item["value"]

            self.appendItem(item)

    @pyqtSlot(int, QVariant)
    def update_row(self, index, value):
        """
        Method to update one of the settings rows
        :param index:
        :param value:
        :return:
        """
        if not isinstance(index, int) or index < 0 or index >= self.count:
            logging.error("Error updating a settings row: {0}".format(value))
            return

        if isinstance(value, QJSValue):
            value = value.toVariant()

        # Convert all boolean objects to strings
        value = str(value) if isinstance(value, bool) else value

        # Set to empty string as need and then update the model
        value = value if value else ""

        # Update the model - two fields to update
        self.setProperty(index=index, property="value", value=value)
        self.setProperty(index=index, property="new_value", value=value)

        # Database Storage Conversions
        parameter = self.get(index=index)["parameter"]

        # Set update_db flag
        update_db = True

        # Database Storage Conversions - Dates/Times
        if parameter in ["Leg 1 Start", "Leg 1 End", "Leg 2 Start", "Leg 2 End"]:
            if "end" in parameter.lower():
                value += " 23:59:59"
            value = self._dc.time_to_iso_format(value)

        # Names to Foreign Keys in Personnel Table
        elif any(substring in parameter for substring in ["Leg 1 FPC", "Leg 2 FPC", "Scientist 1", "Scientist 2",
                                      "Scientist 3", "Captain", "Second Captain", "Deckhand 1",
                                      "Deckhand 2", "Deckhand 3"]):

            try:
                if value:
                    logging.info(f"Personnel found: {parameter} >>> value: {value}")

                    last_name, first_name = value.split(",")
                    person = Personnel.get(Personnel.first_name == first_name,
                                           Personnel.last_name == last_name)
                    value = person.personnel
                else:
                    update_db = False
            except Exception as ex:
                value = None
                update_db = False
                logging.error("Error getting the proper personnel name: {0}".format(ex))

        # Names to Foreign Keys in Lookups Table
        elif parameter in ["Vessel"]:
            try:
                if value:
                    vessel = Lookups.get(Lookups.description == value)
                    value = vessel.lookup
                else:
                    update_db = False
            except Exception as ex:
                value = None
                update_db = False
                logging.error("Error getting the proper vessel name: {0}".format(ex))

        # Update the database
        try:
            if update_db:
                settings_id = self.get(index=index)["settings"]
                SettingsTable.update(value=value).where(SettingsTable.settings == settings_id).execute()

        except Exception as ex:
            logging.error("Exception updating the settings table: {0}".format(ex))


class Settings(QObject):

    settingsModelChanged = pyqtSignal()
    vesselsModelChanged = pyqtSignal()
    scientistsModelChanged = pyqtSignal()
    crewModelChanged = pyqtSignal()
    comPortsModelChanged = pyqtSignal()
    baudRatesModelChanged = pyqtSignal()
    depthRebroadcastInfoChanged = pyqtSignal()
    softwareVersionChanged = pyqtSignal()

    def __init__(self, db):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._db = db

        self._settings_model = SettingsModel()
        self._vessels_model = VesselsModel()
        self._scientists_model = ScientistsModel()
        self._crew_model = CrewModel()
        self._com_ports_model = ComPortsModel()
        self._baud_rates_model = BaudRatesModel()

        self._software_version = SOFTWARE_VERSION

        logging.info(f"HookLogger v{self._software_version}")

        # Specify the depth rebroadcast details
        try:
            settings = \
               SettingsTable.select().where(SettingsTable.parameter % "Depth Output Serial Port")

            item = dict()
            for setting in settings:
                if setting.parameter == "Depth Output Serial Port Status":
                    item["status"] = setting.value
                elif setting.parameter == "Depth Output Serial Port":
                    item["com_port"] = setting.value
                elif setting.parameter == "Depth Output Serial Port Baud Rate":
                    item["baud_rate"] = setting.value

            self._depth_rebroadcast_info = item

        except Exception as ex:
            logging.error('unable to specify depth rebroadcast status: {0}'.format(ex))
            self._depth_rebroadcast_info = {"status": "Off", "com_port": None, "baud_rate": None}

    @pyqtProperty(str, notify=softwareVersionChanged)
    def softwareVersion(self):
        """
        Method to return the self._software_version
        :return:
        """
        return self._software_version

    @pyqtProperty(QVariant, notify=depthRebroadcastInfoChanged)
    def depthRebroadcastInfo(self):

        return self._depth_rebroadcast_info

    @depthRebroadcastInfo.setter
    def depthRebroadcastInfo(self, value):

        if isinstance(value, QJSValue):
            value = value.toVariant()

        if not isinstance(value, dict):
            logging.info('Unable to set the depthRebroadcastInfo: {0}'.format(value))
            return

        if "baud_rate" in value:
            value["baud_rate"] = int(value["baud_rate"])

        self._depth_rebroadcast_info = value
        self.depthRebroadcastInfoChanged.emit()

    @pyqtProperty(FramListModel, notify=comPortsModelChanged)
    def comPortsModel(self):

        return self._com_ports_model

    @pyqtProperty(FramListModel, notify=baudRatesModelChanged)
    def baudRatesModel(self):
        return self._baud_rates_model

    @pyqtProperty(FramListModel, notify=settingsModelChanged)
    def settingsModel(self):
        """
        Method to return the self._settings_model
        :return:
        """
        return self._settings_model

    @pyqtProperty(FramListModel, notify=vesselsModelChanged)
    def vesselsModel(self):
        """
        Method to return the self._vessels_model
        :return:
        """
        return self._vessels_model

    @pyqtProperty(FramListModel, notify=scientistsModelChanged)
    def scientistsModel(self):
        """
        Method to return the self._scientists_model
        :return:
        """
        return self._scientists_model

    @pyqtProperty(FramListModel, notify=crewModelChanged)
    def crewModel(self):
        """
        Method to return the self._vessels_model
        :return:
        """
        return self._crew_model



if __name__ == '__main__':
    unittest.main()

