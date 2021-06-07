__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        StateMachine.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Feb 03, 2016
# License:     MIT
#-------------------------------------------------------------------------------
from PyQt5.QtCore import pyqtProperty, pyqtSlot, QVariant, pyqtSignal, QObject
from PyQt5.QtQml import QJSValue
from dateutil import parser
from py.trawl.TrawlBackdeckDB_model import TypesLu, PrincipalInvestigatorLu, Hauls, Catch, Specimen, Notes
from peewee import *
import logging


class StateMachine(QObject):
    """
    Class for handling all state machine management at the python level.  This will do things
    like initialize the screen at start time with the available hauls, the selected haul,
    the species associated with the selected haul, etc...

    It works hand in hand with teh TrawlBackdeckStateMachine.qml (which I think I'll rename to just
    StateMachine.qml
    """

    haulSelected = pyqtSignal()
    speciesSelected = pyqtSignal()
    specimenSelected = pyqtSignal()
    screenSelected = pyqtSignal()
    previousScreenChanged = pyqtSignal()
    principalInvestigatorSelected = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

        self._haul = self._initialize_selected_haul()
        self._species = {}
        self._initialize_selected_species()
        # self._protocol = {}
        self._specimen = None
        self._initialize_selected_specimen()
        self._screen = "home"
        self._previous_screen = None

        try:
            self._principal_investigator = PrincipalInvestigatorLu.select() \
                .where(PrincipalInvestigatorLu.full_name == "FRAM Standard Survey").get().principal_investigator
        except DoesNotExist as ex:
            self._principal_investigator = None

    @pyqtProperty(QVariant, notify=principalInvestigatorSelected)
    def principalInvestigator(self):
        """
        Method to return the principal investigator
        :return:
        """
        return self._principal_investigator

    @principalInvestigator.setter
    def principalInvestigator(self, value):

        if not isinstance(value, int):
            return

        self._principal_investigator = value
        self.principalInvestigatorSelected.emit()

    @pyqtProperty(str, notify=previousScreenChanged)
    def previousScreen(self):
        """
        Method to return what was the previous screen.  Used for cases like SpecialActions where it could have
        been entered from either ProcessCatchScreen or FishSamplingScreen and the return transition behaviors
        are difference
        :return:
        """
        return self._previous_screen

    @previousScreen.setter
    def previousScreen(self, value):
        """
        Set the self._previous_screen
        :param value:
        :return:
        """
        if not isinstance(value, str):
            return

        self._previous_screen = value
        self.previousScreenChanged.emit()

    @pyqtProperty(QVariant, notify=screenSelected)
    def screen(self):
        """
        Method to return the current screen.  This is used to keep track of what screen is currently being
        displayed, and thus which screen should receive any serial-port data feeds from devices such as
        scales, fishmeter boards, barcode readers, digital calipers
        :return:
        """
        return self._screen

    @screen.setter
    def screen(self, value):
        """
        Method to set what is the current screen
        :param value: str - name of the screen
        :return:
        """
        if not isinstance(value, str):
            return None

        self._screen = value
        self.screenSelected.emit()

    @pyqtProperty(QVariant, notify=haulSelected)
    def haul(self):
        return self._haul

    @haul.setter
    def haul(self, value):

        # if value is None:
        #     return
        self._haul = {"haul_id": None, "haul_number": "", "date": "", "start_time": "", "end_time": "",
                      "station_number": "", "vessel_name": "", "vessel_number": "", "pass": "", "leg": ""}

        # Populate self._haul for the currently selected haul
        sql = "SELECT HAUL_NUMBER, START_DATETIME, END_DATETIME, STATION_CODE, VESSEL_NAME, VESSEL_NUMBER, PASS_NUMBER, LEG_NUMBER, DEPTH_MIN, DEPTH_UOM FROM HAULS WHERE HAUL_ID = ?;"
        params = [value, ]
        for row in self._db.execute(query=sql, parameters=params):
            self._haul["haul_id"] = value
            self._haul["haul_number"] = row[0] if 't' in row[0] else row[0][-3:]
            self._haul["date"] = parser.parse(row[1]).strftime("%m/%d/%Y") if row[1] else ""
            self._haul["start_time"] = parser.parse(row[1]).strftime("%H:%M:%S") if row[1] else ""
            self._haul["end_time"] = parser.parse(row[2]).strftime("%H:%M:%S") if row[2] else ""
            self._haul["station_number"] = row[3] if row[3] else ""
            self._haul["vessel_name"] = row[4] if row[4] else ""
            self._haul["vessel_number"] = row[5] if row[5] else ""
            self._haul["pass"] = row[6] if row[6] else None
            self._haul["leg"] = row[7] if row[7] else None

            try:
                if row[8] and row[9]:
                    logging.info(f'haul selection: row[8] = {row[8]}, row[9] = {row[9]}')
                    if row[9] == "m":
                        self._haul["depth"] = float(row[8])
                    elif row[9] == "ftm":
                        self._haul["depth"] = float(row[8]/1.8288)
                else:
                    self._haul["depth"] = ""
                logging.info(f"haul depth = {self._haul['depth']}")

            except Exception as ex:
                self._haul["depth"] = ""
                logging.info(f"failed to get the depth: {ex}")

        self.species = None
        self.specimen = {"parentSpecimenId": None, "row": -1}

        # Update the STATE table with the new selected haul id
        sql = "UPDATE STATE SET VALUE = ? WHERE PARAMETER = 'Selected Haul ID';"
        self._db.execute(query=sql, parameters=params)

        # Update the STATE table and set the Selected Species ID and Selected Specimen ID to Null
        sql = "UPDATE STATE SET VALUE = Null WHERE PARAMETER = 'Selected Species ID';"
        self._db.execute(query=sql)

        sql = "UPDATE STATE SET VALUE = Null WHERE PARAMETER = 'Selected Specimen ID';"
        self._db.execute(query=sql)

        # logging.info('emitting haulSelected')
        self.haulSelected.emit()

    @pyqtProperty(QVariant, notify=speciesSelected)
    def species(self):
        return self._species

    @species.setter
    def species(self, value):
        """
        Method to set the currently selected species
        :param value: catch_id of the species to set as the selected species
        :return:
        """
        if not isinstance(value, int) and value is not None:
            return

        self._species = {}
        species = {"scientific_name": "", "taxonomy_id": None, "catch_id": None, "display_name": "",
                   "catch_content_id": None, "protocol": ""}

        sql = "SELECT c.CATCH_ID, c.DISPLAY_NAME, t.TAXONOMY_ID, t.SCIENTIFIC_NAME, c.CATCH_CONTENT_ID FROM CATCH c " + \
              "LEFT JOIN CATCH_CONTENT_LU cc ON c.CATCH_CONTENT_ID = cc.CATCH_CONTENT_ID " + \
              "LEFT JOIN TAXONOMY_LU t on t.TAXONOMY_ID = cc.TAXONOMY_ID WHERE CATCH_ID = ? LIMIT 1;"
        params = [value, ]

        for row in self._db.execute(query=sql, parameters=params):
            self._species["scientific_name"] = row[3] if row[3] else ""
            self._species["taxonomy_id"] = row[2] if row[2] else None
            self._species["catch_id"] = value
            self._species["display_name"] = row[1] if row[1] else ""
            self._species["catch_content_id"] = row[4] if row[4] else None

            if isinstance(self._species["taxonomy_id"], int):
                protocol = dict()
                protocol["displayName"] = self._app.protocol_viewer.get_display(taxon_id=self._species["taxonomy_id"],
                                                                                principal_investigator=self.principalInvestigator)

                protocol["actions"] = self._app.protocol_viewer.get_actions(taxon_id=self._species["taxonomy_id"],
                                                                            principal_investigator=self.principalInvestigator)

                if protocol["actions"]:
                    protocol["linealType"] = None
                    protocol["linealSubType"] = None
                    types = [x["type"] for x in protocol["actions"]]
                    if "Length" in types:
                        protocol["linealType"] = "Length"
                    elif "Width" in types:
                        protocol["linealType"] = "Width"
                    elif "Height" in types:
                        protocol["linealType"] = "Height"
                    if protocol["linealType"]:
                        protocol["linealSubType"] = [x["subType"] for x in protocol["actions"] if x["type"] == protocol["linealType"]]
                        if len(protocol["linealSubType"]) > 0:
                            protocol["linealSubType"] = protocol["linealSubType"][0]
                self._species["protocol"] = protocol

                # if "mix" in row[1].lower():
            #     self._all_species["protocol"] = ""

        # if not isinstance(self._all_species["taxonomy_id"], int):
        if not self._species:
            self._species = species

        # logging.info('value, catch_content_id: ' + str(value) + ', ' + str(self._all_species["catch_content_id"]))

        # Update the STATE table and set the Selected Species ID and Selected Specimen ID to Null
        sql = "UPDATE STATE SET VALUE = ? WHERE PARAMETER = 'Selected Species ID';"
        self._db.execute(query=sql, parameters=params)

        sql = "UPDATE STATE SET VALUE = Null WHERE PARAMETER = 'Selected Specimen ID';"
        self._db.execute(query=sql)

        self.specimen = None

        self.speciesSelected.emit()

        return self._species

    @pyqtProperty(QVariant, notify=specimenSelected)
    def specimen(self):
        return self._specimen

    @specimen.setter
    def specimen(self, value):
        """
        Set the active specimen
        :param value:
        :return:
        """
        if isinstance(value, QJSValue):
            value = value.toVariant()
        # logging.info('value: ' + str(value))

        if value is None:
            self._specimen = {"parentSpecimenId": None, "row": -1}
        else:
            self._specimen = value

        # logging.info('specimen: ' + str(self._specimen))
        self.specimenSelected.emit()

    def _initialize_selected_haul(self):
        """
        Method called on startup to initialize the self._haul information
        :return: dict - returning the selected haul information
        """
        haul = {"haul_id": "", "haul_number": "", "date": "", "start_time": "",
                "end_time": "", "station_number": "", "depth": ""}
        sql = "SELECT HAUL_ID, HAUL_NUMBER, START_DATETIME, END_DATETIME, STATION_CODE, DEPTH_MIN, DEPTH_UOM FROM HAULS " + \
            "WHERE PROCESSING_STATUS = 'Selected'"
        for row in self._db.execute(query=sql):
            haul["haul_id"] = row[0]
            haul["haul_number"] = row[1] if 't' in row[1] else row[1][-3:]
            haul["date"] = parser.parse(row[2]).strftime("%m/%d/%Y") if row[2] else ""
            haul["start_time"] = parser.parse(row[2]).strftime("%H:%M:%S") if row[2] else ""
            haul["end_time"] = parser.parse(row[3]).strftime("%H:%M:%S") if row[3] else ""
            haul["station_number"] = row[4] if row[4] else ""

            try:
                if row[6] and row[5]:
                    logging.info(f'haul selection: row[6] = {row[6]}, row[5] = {row[5]}')
                    if row[6] == "m":
                        haul["depth"] = float(row[5])
                    elif row[6] == "ftm":
                        haul["depth"] = float(row[5]/1.8288)
                else:
                    haul["depth"] = ""
                logging.info(f"haul depth = {haul['depth']}")

            except Exception as ex:
                haul["depth"] = ""
                logging.info(f"failed to get the depth uom: {ex}")

        self.haulSelected.emit()

        return haul

    def _initialize_selected_species(self):
        """
        Method called on startup to initialize
        :return: dict - containing the selected species information
        """
        if self._haul is None:
            return {}

        sql = "SELECT VALUE FROM STATE WHERE PARAMETER = 'Selected Species ID';"
        result = self._db.execute(query=sql).fetchall()
        if result and result[0]:
            value = result[0][0]
            if value:
                self.species = value

    def _initialize_selected_specimen(self):
        """
        Method called on startup to initialize the self._specimen information, identifying the currently selected
        specimen
        :return:
        """
        self._specimen = {"parentSpecimenId": None, "row": -1}

    @pyqtProperty(QVariant, notify=haulSelected)
    def haulId(self):
        return self._haul["haul_number"]

    @pyqtSlot(name="cleanDB")
    def clean_db(self):
        """
        Function to complete clear out db data colleciton tables
        :return: None
        """
        try:
            self._db.execute("delete from specimen")
            self._logger.info("Deleting all records from SPECIMEN")
            self._db.execute("delete from catch")
            self._logger.info("Deleting all records from CATCH")
            self._db.execute("delete from notes")
            self._logger.info("Deleting all records from NOTES")
            self._db.execute("delete from hauls")
            self._logger.info("Deleting all records from HAULS")
            self._db.execute("vacuum")
        except Exception as e:
            self._logger.debug(f"Unable to clean database; {e}")
            raise e

    @pyqtSlot(QVariant, name="countTableRows", result="int")
    def count_table_rows(self, table_name):
        """
        Return number of rows in the main data collection tables
        :param table_name: str; table name of
        :return:
        """
        if table_name.lower() == 'hauls':
            return Hauls.select(fn.COUNT(SQL('*'))).scalar()
        elif table_name.lower() == 'catch':
            return Catch.select(fn.COUNT(SQL('*'))).scalar()
        elif table_name.lower() == 'specimen':
            return Specimen.select(fn.COUNT(SQL('*'))).scalar()
        elif table_name.lower() == 'notes':
            return Notes.select(fn.COUNT(SQL('*'))).scalar()
        else:
            err_str = f"Table {table_name} not expected in count_table_rows method."
            self._logger.info(err_str)
            raise KeyError(err_str)

    @pyqtProperty(QVariant)
    def haulCount(self):
        return Hauls.select(fn.COUNT(SQL('*'))).scalar()


if __name__ == '__main__':

    sm = StateMachine()
