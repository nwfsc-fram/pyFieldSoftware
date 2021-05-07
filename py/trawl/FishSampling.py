__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        FishSampling.py
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
import unittest
# import win32print
# from win32print import EnumPrinters, PRINTER_ENUM_NAME, PRINTER_ENUM_LOCAL
# import win32ui, win32con
import serial
from threading import Thread
from queue import Queue
from py.trawl.TrawlBackdeckDB_model import Specimen, TypesLu, SpeciesSamplingPlanLu, \
    BarcodesLu, Settings, LengthWeightRelationshipLu, Hauls, PrincipalInvestigatorLu, PiActionCodesLu
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
from py.common.SoundPlayer import SoundPlayer
from py.common.LabelPrinter import LabelPrinter

from datetime import datetime
import math
import re


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
        ser = serial.Serial(write_timeout=0, timeout=0)
        try:

            ser.port = self.comport
            ser.open()
            for row in self.rows:
                ser.write(row)
            ser.close()
            self.result["success"] = True
            self.result["message"] = "Everything printed fine"

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


class AgeTypeModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="ageTypeId")
        self.add_role_name(name="ageTypeName")
        self.add_role_name(name="text")


class StandardActionsModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="type")
        self.add_role_name(name="value")
        self.add_role_name(name="key")
        self.add_role_name(name="text")


class SpecimensModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="parentSpecimenId")
        self.add_role_name(name="parentSpecimenNumber")
        self.add_role_name(name="catchId")
        self.add_role_name(name="linealSpecimenId")
        self.add_role_name(name="linealType")
        self.add_role_name(name="linealTypeId")
        self.add_role_name(name="linealValue")
        self.add_role_name(name="sexSpecimenId")
        self.add_role_name(name="sex")
        self.add_role_name(name="ageSpecimenId")
        self.add_role_name(name="ageNumber")
        self.add_role_name(name="ageTypeName")
        self.add_role_name(name="ageTypeId")
        self.add_role_name(name="weightSpecimenId")
        self.add_role_name(name="weight")
        self.add_role_name(name="ovarySpecimenId")
        self.add_role_name(name="ovaryNumber")
        self.add_role_name(name="stomachSpecimenId")
        self.add_role_name(name="stomachNumber")
        self.add_role_name(name="tissueSpecimenId")
        self.add_role_name(name="tissueNumber")
        self.add_role_name(name="finclipSpecimenId")
        self.add_role_name(name="finclipNumber")
        self.add_role_name(name="special")
        self.add_role_name(name="speciesSamplingPlanId")


class SpecimenTagsModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="tag")
        self.add_role_name(name="specimenNumber")

    @pyqtSlot(str)
    def populate_tags(self, specimen_type="ovary"):
        """
        Method to query the database to obtain all tags of a given specimen type
        :param specimen_type: enumerated list - ovary, stomach, tissue, finclip
        :return:
        """
        if specimen_type not in ["ovary", "stomach", "tissue", "finclip", "whole specimen"]:
            return

        mapping = {"ovary": "Ovary ID", "stomach": "Stomach ID",
                   "tissue": "Tissue ID", "finclip": "Finclip ID",
                   "whole specimen": "Whole Specimen ID"}

        self.clear()

        try:

            tag_length = 20
            tags = (Specimen.select(Specimen.alpha_value)
                         .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias('types'))
                         .where((TypesLu.type == mapping[specimen_type]) &
                                (TypesLu.category == "Action"))
                    .order_by(fn.substr(Specimen.alpha_value, 18, 3).desc()))

            for tag in tags:
                if len(tag.alpha_value) >= 20:
                    specimen_number = tag.alpha_value[18:20].zfill(3)
                else:
                    specimen_number = tag.alpha_value
                item = {"tag": tag.alpha_value,
                        "specimenNumber": specimen_number}
                self.appendItem(item)

        except Exception as ex:

            logging.info('populate_tags error: ' + str(ex))


class FishSampling(QObject):
    """
    Class for the FishSamplingScreen.
    """
    modeChanged = pyqtSignal()
    speciesModelChanged = pyqtSignal(str)
    specimenCountChanged = pyqtSignal()
    actionModeChanged = pyqtSignal()
    ageStructuresModelChanged = pyqtSignal()
    valueChanged = pyqtSignal(int, str, arguments=["tabIndex", "property"])
    standardActionsModelChanged = pyqtSignal()
    # specimenRowChanged = pyqtSignal()
    specimenAdded = pyqtSignal()
    tabChanged = pyqtSignal()
    sexChanged = pyqtSignal()
    linealTypeChanged = pyqtSignal()
    ageTypeChanged = pyqtSignal()
    invalidEntryReceived = pyqtSignal(str, str, QVariant, str, arguments=["add_or_update", "property", "value", "errors"])
    errorChecksChanged = pyqtSignal()
    printerStatusReceived = pyqtSignal(str, bool, str, arguments=["comport", "success", "message"])
    sexLengthCountChanged = pyqtSignal()
    ageWeightCountChanged = pyqtSignal()

    specimenTagsModelChanged = pyqtSignal()


    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

        # Set up the models
        self._model = SpecimensModel()
        self._age_structures_model = AgeTypeModel()
        self.ageStructuresModel = None
        self._standard_actions_model = StandardActionsModel()
        self._set_standard_action_model_items()

        self._specimen_tags_model = SpecimenTagsModel()

        # Items tracked to support automatic capture by fishmeter board, scales, barcode readers
        # These are used to determine if we can take in a new value or not

        self._mode = "Sex-Length"
        self._action_mode = "add"
        self._active_tab = "Sex-Length"

        self._sex = "F"
        self._lineal_type = "Fork Length"
        self._age_type = "Otolith"

        self._specimen_count = 0
        self._sex_length_count = 0
        self._age_weight_count = 0

        self._error_checks = True

        self._specimen_row = -1

        # self._app.sound_player = SoundPlayer()

        self._printer_thread = QThread()
        self._printer_worker = None

    @pyqtProperty(int, notify=sexLengthCountChanged)
    def sexLengthCount(self):
        """
        Method to return the self._sex_length_count
        :return:
        """
        return self._sex_length_count

    @sexLengthCount.setter
    def sexLengthCount(self, value):
        """
        Method to set the self._sex_length_count variable
        :param value: int
        :return:
        """
        if not isinstance(value, int):
            logging.error('non-integer passed in for sexLengthCount')
            return

        self._sex_length_count = value
        self.sexLengthCountChanged.emit()

    @pyqtProperty(int, notify=ageWeightCountChanged)
    def ageWeightCount(self):
        """
        Method to return the self._age_weight_count
        :return:
        """
        return self._age_weight_count

    @ageWeightCount.setter
    def ageWeightCount(self, value):
        """
        Method to set the self._age_weight_count variable
        :param value: int
        :return:
        """
        if not isinstance(value, int):
            logging.error('non-integer passed in for ageWeightCount')
            return

        self._age_weight_count = value
        self.ageWeightCountChanged.emit()

    @pyqtProperty(QVariant, notify=errorChecksChanged)
    def errorChecks(self):
        """
        Method to return the self._error_check variable, indicating if error checks should be done
        :return:
        """
        return self._error_checks

    @errorChecks.setter
    def errorChecks(self, value):
        """
        Method to set the self._error_check value
        :param value: bool
        :return:
        """
        if not isinstance(value, bool):
            return

        self._error_checks = value
        self.errorChecksChanged.emit()

    @pyqtProperty(str, notify=sexChanged)
    def sex(self):
        return self._sex

    @sex.setter
    def sex(self, value):
        """
        Method to set the sex.
        :param value:
        :return:
        """
        if value.upper() not in ["F", "M", "U"]:
            return
        self._sex = value
        self.sexChanged.emit()

    @pyqtProperty(str, notify=linealTypeChanged)
    def linealType(self):
        """
        Method to return the linealType - this is used for recording if a length or width is being captured
        :return:
        """
        return self._lineal_type

    @linealType.setter
    def linealType(self, value):
        """
        Set the self._lineal_type
        :param value:
        :return:
        """
        # if value.lower() in ["length", "width", "height"]:
        self._lineal_type = value
        self.linealTypeChanged.emit()

    @pyqtProperty(str, notify=ageTypeChanged)
    def ageType(self):
        """
        Method to return the type of age structure to take
        :return:
        """
        return self._age_type

    @ageType.setter
    def ageType(self, value):
        """
        Method to set the type of age structure to take
        :param value:
        :return:
        """
        self._age_type = value
        self.ageTypeChanged.emit()

    @pyqtProperty(str, notify=tabChanged)
    def activeTab(self):
        return self._active_tab

    @activeTab.setter
    def activeTab(self, value):
        """
        Method to set the active tab in the tvActions TabView
        :param value:
        :return:
        """
        if value not in ["Sex-Length", "Age-Weight", "Ovary-Stomach"]:
            return

        self._active_tab = value
        self.tabChanged.emit()

    @pyqtProperty(str, notify=modeChanged)
    def mode(self):
        """
        Return the current mode - Sex-Length or Age-Weight
        :return:
        """
        return self._mode

    @mode.setter
    def mode(self, value):
        """
        Set the current mode
        :param value:
        :return:
        """
        if value not in ["Sex-Length", "Age-Weight"]:
            return

        self._mode = value
        self.modeChanged.emit()

    @pyqtProperty(str, notify=actionModeChanged)
    def actionMode(self):
        """
        Return the change mode, which can be either add (in mode to add a new item) or modify (to change an
        existing specmen)
        :return:
        """
        return self._action_mode

    @actionMode.setter
    def actionMode(self, value):
        """
        Method to set the action mode to either add or modify
        :param value:
        :return:
        """
        if value not in ["add", "modify"]:
            return
        self._action_mode = value
        self.actionModeChanged.emit()

    @pyqtProperty(QVariant, notify=specimenTagsModelChanged)
    def SpecimenTagsModel(self):
        """
        Method to return the self._specimen_tags_model
        :return:
        """
        return self._specimen_tags_model

    @pyqtProperty(QVariant, notify=standardActionsModelChanged)
    def StandardActionsModel(self):
        """
        Method to return the standard actions model
        :return:
        """
        return self._standard_actions_model

    @StandardActionsModel.setter
    def StandardActionsModel(self, data):
        """
        Method to update a value of the Standard Action Model which is a model for the
        tvSamples TableView that stores the ovary, stomach, tissue, and finclip numbers
        :param data_dict:
        :return:
        """
        if isinstance(data, QJSValue):
            data = data.toVariant()

        if "index" not in data or "property" not in data or "value" not in data:
            return

        self._standard_actions_model.setProperty(index=data["index"], property=data["property"],
                                                 value=data["value"])
        self.standardActionsModelChanged.emit()

    def _set_standard_action_model_items(self):
        """
        Define the types of IDs for the standard actions table view
        :return:
        """
        idList = ["ovary", "stomach", "tissue", "finclip"]
        items = [{"type": x + "Number", "value": "", "key": i, "text": x.title()} for i, x in enumerate(idList)]
        self._standard_actions_model.setItems(items)

    @pyqtProperty(QVariant, notify=ageStructuresModelChanged)
    def ageStructuresModel(self):
        """
        Return the age structure model used to populate the age types ComboBox in tabWeightAge
        :return:
        """
        return self._age_structures_model

    @ageStructuresModel.setter
    def ageStructuresModel(self, value):
        """
        Set the age structure model
        :param value:
        :return:
        """
        self._age_structures_model.setItems(self.get_age_structures())
        self.ageStructuresModelChanged.emit()

    def get_age_structures(self):
        """
        Method to get the age types that are used to populate the Age Type Combo Box in the
        tabWeightAge
        :return:
        """
        ages = []
        names = {"ageTypeId": "type_id", "ageName": "type", "text": "type"}
        for age in TypesLu.select().where(TypesLu.category == "Age Structure").order_by(TypesLu.type_id):
            age_dict = {x: model_to_dict(age)[names[x]] for x in names}
            ages.append(age_dict)

        return ages

    @pyqtProperty(int, notify=specimenCountChanged)
    def specimenCount(self):
        """
        Return the specimenCount which is used for defining the specimen id
        :return:
        """
        return self._specimen_count

    @specimenCount.setter
    def specimenCount(self, value):
        """
        Set the specimenCount
        :param value:
        :return:
        """
        self._specimen_count = value
        self.specimenCountChanged.emit()

    @pyqtProperty(QVariant, notify=speciesModelChanged)
    def model(self):
        """
        return the SpecimensModel
        :return:
        """
        return self._model

    @pyqtSlot()
    def initialize_list(self):
        """
        Method to initialize the specimens list for the given haul + species combination
        :return:
        """

        # Clear the model
        model = self._model

        # Clear the tvSpecimens list
        model.clear()
        self.specimenCount = 0

        # Mapping
        mapping = {"Sex": {"id": "sexSpecimenId", "value": "sex", "valueType": "alpha"},
                   "Age ID": {"id": "ageSpecimenId", "value": "ageNumber", "name": "ageTypeName", "typeId": "ageTypeId", "valueType": "numeric"},
                   "Length": {"id": "linealSpecimenId", "value": "linealValue", "typeId": "linealTypeId", "valueType": "numeric"},
                   "Width": {"id": "linealSpecimenId", "value": "linealValue", "typeId": "linealTypeId", "valueType": "numeric"},
                   "Weight": {"id": "weightSpecimenId", "value": "weight", "valueType": "numeric"},
                   "Ovary ID": {"id": "ovarySpecimenId", "value": "ovaryNumber", "valueType": "alpha"},
                   "Stomach ID": {"id": "stomachSpecimenId", "value": "stomachNumber", "valueType": "alpha"},
                   "Tissue ID": {"id": "tissueSpecimenId", "value": "tissueNumber", "valueType": "alpha"},
                   "Finclip ID": {"id": "finclipSpecimenId", "value": "finclipNumber", "valueType": "alpha"}
                   }

        # create the tvSpecimens rows - Get those rows that have the correct catch ID, don't have a parent specimen
        # ID, and they must either be the FRAM Standard Survey sampling plan or they should not have a plan at all

        # TODO Todd Hay - What about a project like Chris Harvey, where we have a species, where we have a
        # sampling plan, but there might not be a FRAM Standard Survey plan.
        # Actually, per below (lines 671-679 in add_list_item), when we add a new specimen, we only ever assign
        # it a sampling plan associated with FRAM Standard Survey or None, so we should be okay
        specimens = (Specimen.select(Specimen, SpeciesSamplingPlanLu)
                         .join(SpeciesSamplingPlanLu, JOIN.LEFT_OUTER,
                               on=(Specimen.species_sampling_plan == SpeciesSamplingPlanLu.species_sampling_plan)
                                       .alias("plan"))
                         .where(
                            (Specimen.catch == self._app.state_machine.species["catch_id"]) &
                            (Specimen.parent_specimen.is_null(True)) &
                            (((SpeciesSamplingPlanLu.plan_name == "FRAM Standard Survey") &
                              (SpeciesSamplingPlanLu.display_name != "Whole Specimen ID")) |
                                 (Specimen.species_sampling_plan.is_null(True)))
                        ))

        for specimen in specimens:

            logging.info(f"plan: {model_to_dict(specimen)}")

            self.specimenCount += 1

            plan_id = None
            if hasattr(specimen, "plan"):
                plan_id = specimen.plan.species_sampling_plan
            logging.info(f"{plan_id}")

            item = {"parentSpecimenId": specimen.specimen, "parentSpecimenNumber": self.specimenCount,
                    "linealSpecimenId": None, "linealValue": None,
                    "linealType": None, "linealTypeId": None,
                    "sexSpecimenId": None, "sex": None,
                    "ageSpecimenId": None, "ageNumber": None, "ageTypeName": None, "ageTypeId": None,
                    "weightSpecimenId": None, "weight": None,
                    "ovarySpecimenId": None, "ovaryNumber": None,
                    "stomachSpecimenId": None, "stomachNumber": None,
                    "tissueSpecimenId": None, "tissueNumber": None,
                    "finclipSpecimenId": None, "finclipNumber": None,
                    "special": "", "speciesSamplingPlanId": plan_id}

                    # TODD - For testing the unhandled exception handler only
                    # "special": "", "speciesSamplingPlanId": specimen.plan.species_sampling_plan}

            self._model.appendItem(item)

            # Update the rows for all of the recursive action values
            # query = (Specimen.select(Specimen, TypesLu)
            #          .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias('types'))
            #          .where(Specimen.parent_specimen == specimen.specimen))

            query = (Specimen.select(Specimen, SpeciesSamplingPlanLu, TypesLu)
                     .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias('types'))
                     .join(SpeciesSamplingPlanLu, JOIN.LEFT_OUTER,
                           on=(SpeciesSamplingPlanLu.species_sampling_plan == Specimen.species_sampling_plan).alias('plan'))
                     .where((Specimen.parent_specimen == specimen.specimen) &
                            (((SpeciesSamplingPlanLu.plan_name == "FRAM Standard Survey") &
                            (SpeciesSamplingPlanLu.display_name != "Whole Specimen ID")) |
                                 (Specimen.species_sampling_plan.is_null(True)))))

            for child in query:

                if child.types.type in mapping:

                    # Update the specimen Id
                    property = mapping[child.types.type]["id"]
                    value = child.specimen
                    self._model.setProperty(self.specimenCount-1, property, value)

                    # Update the alpha or numeric value
                    property = mapping[child.types.type]["value"]
                    if mapping[child.types.type]["valueType"] == "alpha":
                        value = child.alpha_value
                    elif mapping[child.types.type]["valueType"] == "numeric":
                        value = child.numeric_value
                    self._model.setProperty(self.specimenCount - 1, property, value)

                    if property == "linealValue":
                        sub_property = "linealType"
                        value = child.types.subtype
                        self._model.setProperty(self.specimenCount - 1, sub_property, value)
                        sub_property = "linealTypeId"
                        value = child.types.type_id
                        self._model.setProperty(self.specimenCount - 1, sub_property, value)

                    elif property == "ageNumber":
                        sub_property = "ageTypeName"
                        value = child.types.subtype
                        self._model.setProperty(self.specimenCount - 1, sub_property, value)
                        sub_property = "ageTypeId"
                        value = child.types.type_id
                        self._model.setProperty(self.specimenCount - 1, sub_property, value)

            if self._model.get(self.specimenCount-1)["special"] == "":
                special_indicator = self._get_special_actions_indicator(index=self.specimenCount-1)
                if special_indicator == "Y":
                    self._model.setProperty(self.specimenCount-1, "special", special_indicator)

        # logging.info('item initialized: ' + str(self._model.get(self.specimenCount-1)))

    @pyqtSlot(str, result=QVariant)
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

        # logging.info('specimen_type: {0}'.format(specimen_type))

        tag_id = None
        try:
            for setting in Settings.select():
                if setting.parameter == "Survey Year":
                    year = setting.value
                    try:
                        now_year = datetime.now().strftime("%Y")
                        if year != now_year:
                            year = now_year
                    except Exception as ex2:
                        logging.info(f"unable to update the year: {ex2}")

                elif setting.parameter == "Vessel ID":
                    vessel_id = setting.value

            haul_number = str(self._app.state_machine.haul["haul_number"])
            if len(haul_number) > 3:
                haul_number = haul_number[-3:]

            try:
                pi_action_code_id = \
                    PiActionCodesLu.select(PiActionCodesLu) \
                    .join(PrincipalInvestigatorLu, on=(PiActionCodesLu.principal_investigator == PrincipalInvestigatorLu.principal_investigator)) \
                    .join(TypesLu, on=(PiActionCodesLu.action_type == TypesLu.type_id).alias('types')) \
                    .where(PrincipalInvestigatorLu.full_name == "FRAM Standard Survey",
                           TypesLu.category == "Action",
                           TypesLu.type == mapping[specimen_type]["action"]).get().pi_action_code
            except DoesNotExist as ex:
                pi_action_code_id = 1

            specimen_type_id = str(pi_action_code_id).zfill(3)

            # Query for specimen number - get the latest one for the given specimen type (i.e. ovary, stomach, tissue, finclip)
            spec_num_length = 20
            # specimens = (Specimen.select(Specimen, TypesLu)
            #             .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias('types'))
            #             .where((TypesLu.type == mapping[specimen_type]["action"]) &
            #                    (TypesLu.category == "Action") &
            #                    ((fn.length(Specimen.alpha_value) == spec_num_length) |
            #                     (fn.length(Specimen.alpha_value) == spec_num_length + 1)) &
            #                    (fn.substr(Specimen.alpha_value, 1, 4) == year) &
            #                    (fn.substr(Specimen.alpha_value, 6, 3) == vessel_id)).order_by(Specimen.alpha_value.desc()))

            specimens = (Specimen.select(fn.substr(Specimen.alpha_value, 18, 3).alias('specimen_number'))
                         .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias('types'))
                         .where((TypesLu.type == mapping[specimen_type]["action"]) &
                                (TypesLu.category == "Action") &
                                ((fn.length(Specimen.alpha_value) == spec_num_length) |
                                 (fn.length(Specimen.alpha_value) == spec_num_length + 1)) &
                                (fn.substr(Specimen.alpha_value, 1, 4) == year) &
                                (fn.substr(Specimen.alpha_value, 6, 3) == vessel_id)).order_by(
                fn.substr(Specimen.alpha_value, 18, 3).desc()))

            # Get the newest specimen.  Note that one may not exist as it hasn't been created yet
            try:
                last_specimen_num = specimens.get().specimen_number
            except DoesNotExist as dne:
                last_specimen_num = None

            # logging.info('last_specimen_num: {0}'.format(last_specimen_num))

            # Compare to the existing specimen type for the selected model item
            index = self._app.state_machine.specimen["row"]
            item = self._model.get(index)

            specimen_value = item[specimen_type]
            specimen_id = item[mapping[specimen_type]["id"]]

            # logging.info('spec value / id: {0}, {1}'.format(specimen_value, specimen_id))

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
                specimen_value is None or specimen_value == "" or len(str(specimen_value)) < spec_num_length:

                # No specimen record exists for this specimen_type, so we're creating a new specimen_value
                # So one up the highest number
                if last_specimen_num:
                    specimen_num = str(int(re.sub(r'[^\d.]+', '', last_specimen_num)[-3:]) + 1).zfill(3)
                else:
                    specimen_num = "001"

            else:
                # Specimen record exists, then nothing to do here.  Clicking the print button will up the last
                # alpha character
                return specimen_value

            sep = "-"
            tag_id = year + sep + vessel_id + sep + haul_number + sep + specimen_type_id + \
                     sep + specimen_num

            # One final confirmation that this tag_id does not already exist in the database
            dup_count = Specimen.select().where(Specimen.alpha_value.contains(tag_id)).count()

            if dup_count > 0:
                logging.error("duplicate tag found: {0}, count: {1}".format(tag_id, dup_count))
                return ""

        except Exception as ex:
            logging.info('get_tag_id error: ' + str(ex))

        return tag_id

    def get_species_length_type(self, species=""):
        """
        Method to get the length type, as record in TYPES_LU of the given species, which should
        be the statemachine species
        :param species:
        :return:
        """
        if species == "":
            species = self._app.state_machine.species["taxonomy_id"]

    def _get_age_id_name(self):
        """
        Method to return the ageTypeId and ageTypeName for the currrent specimen
        :return:
        """

        # Set the default to using an Otolith age
        age_type = TypesLu.select().where(TypesLu.category == "Action", TypesLu.type == "Age ID",
                                          TypesLu.subtype == "Otolith").get()
        age_type_id = age_type.type_id
        age_type_name = age_type.subtype
        try:
            actions = self._app.state_machine.species["protocol"]["actions"]
            if actions is not None:
                age_item = next(x for x in actions if x["type"] == "Age ID")
                age_type = TypesLu.select().where(TypesLu.category == "Action",
                                                  TypesLu.type == "Age ID",
                                                  TypesLu.subtype == age_item["subType"]).get()
                age_type_id = age_type.type_id
                age_type_name = age_type.subtype
        except DoesNotExist as ex:
            pass
        except StopIteration as ex:
            pass

        return age_type_id, age_type_name

    @pyqtSlot(QVariant, str)
    def add_list_item(self, linealValue, sex):
        """
        Method to add a new specimen item
        :param linealValue: float -
        :param sex: str -
        :return:
        """
        if not isinstance(sex, str):
            return

        # Ensure the linealValue is a float
        linealValue = self._get_typed_value("linealValue", linealValue)

        if self.errorChecks:
            if self._check_for_errors(add_or_update="add", property="linealValue", value=linealValue) or \
            self._check_for_errors(add_or_update="add", property="sex", value=sex):
                return
        else:
            self.errorChecks = True

        self.specimenCount += 1

        # Common values used across parent specimen + linealValue + sex specimen record insertions
        # AB - not sure why, but the query below was looking for species_sampling_plan rather than
        # species_sampling_plan_id - changed 5/6/21
        catch_id = self._app.state_machine.species["catch_id"]
        try:
            species_sampling_plan_id = SpeciesSamplingPlanLu.get(SpeciesSamplingPlanLu.taxonomy ==
                                                                 self._app.state_machine.species["taxonomy_id"],
                                                                 SpeciesSamplingPlanLu.plan_name == "FRAM Standard Survey") \
                                            .species_sampling_plan_id
        except DoesNotExist as ex:
            # logging.info("Species sampling plan does not exist in SPECIES_SAMPLING_PLAN_LU for taxonomy_id = " +
            #              str(self._app.state_machine.species["taxonomy_id"]) + " (" +
            #              str(self._app.state_machine.species["display_name"]) + ")")
            species_sampling_plan_id = None

        # Add the parent specimen record
        specimen = Specimen.create(catch=catch_id, species_sampling_plan=species_sampling_plan_id)
        specimen.save()
        self._app.state_machine.specimen["parentSpecimenId"] = specimen.specimen
        parent_specimen_id = specimen.specimen

        if parent_specimen_id == -1:
            return

        # Get lineal_type + lineal_subtype
        protocol = self._app.state_machine.species["protocol"]
        protocol_actions = protocol["actions"]
        # logging.info('protocol actions: {0}'.format(protocol_actions))
        if "linealType" in protocol and "linealSubType" in protocol:
            lineal_type = self._app.state_machine.species["protocol"]["linealType"]
            lineal_subtype = self._app.state_machine.species["protocol"]["linealSubType"]
        else:
            # Protocol doesn't exist, set to Unspecified Length
            lineal_type = "Length"
            lineal_subtype = "Unspecified"

        # self.linealType = lineal_subtype + " " + lineal_type

        try:
            lineal_type_id = TypesLu.select().where(TypesLu.category == "Action",
                             TypesLu.type == lineal_type, TypesLu.subtype == lineal_subtype).get().type_id
        except DoesNotExist as ex:
            lineal_type_id = None

        # Add lineal value
        action_type_id = TypesLu.get(TypesLu.category == "Action",
                                     TypesLu.type == lineal_type, TypesLu.subtype == lineal_subtype).type_id
        measurement_type_id = TypesLu.get(TypesLu.category == "Measurement", TypesLu.type == lineal_type).type_id
        lineal_specimen = Specimen.create(parent_specimen=parent_specimen_id, action_type=action_type_id,
                                          measurement_type=measurement_type_id, numeric_value=linealValue,
                                          catch=catch_id, species_sampling_plan=species_sampling_plan_id)
        lineal_specimen.save()

        # Add sex value
        action_type_id = TypesLu.get(TypesLu.category == "Action", TypesLu.type == "Sex").type_id
        sex_specimen = Specimen.create(parent_specimen=parent_specimen_id, action_type=action_type_id, alpha_value=sex,
                                       catch=catch_id, species_sampling_plan=species_sampling_plan_id)
        sex_specimen.save()

        # Get Age parameters
        age_type_id, age_type_name = self._get_age_id_name()

        # Add to the model
        item = {"parentSpecimenId": parent_specimen_id, "parentSpecimenNumber": self.specimenCount,
                "linealSpecimenId": lineal_specimen.specimen, "linealValue": linealValue,
                "linealType": self.linealType, "linealTypeId": lineal_type_id,
                "sexSpecimenId": sex_specimen.specimen, "sex": sex,
                "ageSpecimenId": None, "ageNumber": None, "ageTypeName": age_type_name, "ageTypeId": age_type_id,
                "weightSpecimenId": None, "weight": None,
                "ovarySpecimenId": None, "ovaryNumber": None,
                "stomachSpecimenId": None, "stomachNumber": None,
                "tissueSpecimenId": None, "tissueNumber": None,
                "finclipSpecimenId": None, "finclipNumber": None,
                "special": "", "speciesSamplingPlanId": species_sampling_plan_id}

        # logging.info('item being added: ' + str(item))

        self._model.appendItem(item)

        self.specimenAdded.emit()

        self._app.sound_player.play_sound(sound_name="takeLength", override=False)

        if self.mode == "Age-Weight":
            self.activeTab = "Age-Weight"
            self._app.sound_player.play_sound(sound_name="ageWeightSpecimen", override=False)

    @pyqtSlot(int, result=str)
    def _get_special_actions_indicator(self, index):
        """
        Method used to determine if a special action has been accomplished for the given row
        :param index: int - row of the list model
        :return:
        """
        if not isinstance(index, int) or index == -1:
            return

        count = 0

        # if self._app.state_machine.specimen["row"] != -1:
        try:
            parent_specimen_id = self._model.get(index)["parentSpecimenId"]

            # sql = """
            #     select count(*) from specimen s
            #     inner join SPECIES_SAMPLING_PLAN_LU p ON p.SPECIES_SAMPLING_PLAN_ID = s.SPECIES_SAMPLING_PLAN_ID
            #     LEFT join TYPES_LU t on s.action_type_id = t.TYPE_ID
            #     where s.parent_specimen_id = ? and
            #     ((lower(t.type) != 'sex' AND
            #     lower(t.type) != 'length' AND
            #     lower(t.type) != 'width' AND
            #     lower(t.type) != 'weight' AND
            #     lower(t.type) != 'age id' AND
            #     p.PLAN_NAME == "FRAM Standard Survey") OR
            #     (p.PLAN_NAME != "FRAM Standard Survey"))
            # """

            sql = """
                select count(*) from specimen s
                inner join TYPES_LU t on s.action_type_id = t.TYPE_ID
                where s.parent_specimen_id = ? and
                lower(t.type) != 'sex' AND
                lower(t.type) != 'length' AND
                lower(t.type) != 'width' AND
                lower(t.type) != 'weight' AND
                lower(t.type) != 'age id';
            """
            params = [parent_specimen_id, ]
            result = self._db.execute(query=sql, parameters=params)
            if result:
                count = result.fetchall()[0][0]

            # actions = (Specimen.select(Specimen, TypesLu)
            #             .join(TypesLu, on=(TypesLu.type_id == Specimen.action_type).alias('types'))
            #             .where(Specimen.parent_specimen == parent_specimen_id,
            #                    (~(fn.Lower(TypesLu.type) % "sex")),
            #                    (~(fn.Lower(TypesLu.type) % "length")),
            #                    (~(fn.Lower(TypesLu.type) % "weight")),
            #                    (~(fn.Lower(TypesLu.type) % "age"))
            #                    ))

            # ~(fn.Lower(TypesLu.type).contains("sex")),
            #                      ~(fn.Lower(TypesLu.type).contains("length")),
            #                      ~(fn.Lower(TypesLu.type).contains("weight")),
            #                      ~(fn.Lower(TypesLu.type).contains("age"))
            #                    ))


                               # ~((fn.Lower(TypesLu.type).contains("sex")) |
                               #   (fn.Lower(TypesLu.type).contains("length")) |
                               #   (fn.Lower(TypesLu.type).contains("weight")) |
                               #   (fn.Lower(TypesLu.type).contains("age")))
                               # ))
            # count = actions.count()
            if count > 0:
                return "Y"
            # for action in actions:
            #     result = [x for x in standard_actions if x in action.types.type.lower()]
            #     logging.info('result: ' + str(result))
            #     if len(result) == 0:
            #         return "Y"
        except Exception as ex:
            pass

        return ""

    @pyqtSlot(str, QVariant)
    def update_list_item(self, property, value):

        """
        Method to update the SpecimenModel list item
        :param property:
        :param value:
        :return:
        """
        if not isinstance(property, str):
            return

        if property not in ["sex", "linealValue", "weight", "ageNumber", "ageTypeName",
                            "ovaryNumber", "stomachNumber", "tissueNumber", "finclipNumber"]:
            logging.error("Invalid property to update: " + str(property))
            return

        # Ensure that a row has been selected for making an update
        if self._app.state_machine.specimen["row"] is None:
            logging.info('row not selected')
            return

        # Convert the value into an appropriate type
        value = self._get_typed_value(property=property, value=value)

        # Error Checking - do the following protocol or other error checks if error_checking is on
        index = self._app.state_machine.specimen["row"]
        if index < 0:
            logging.info('index: ' + str(index) + ', aborting update as there is not a good row index')
            return

        model_item = self._model.get(index)

        if self.errorChecks:
            if self._check_for_errors(add_or_update="update", property=property, value=value):
                return
        else:
            self.errorChecks = True

        # Update standard actions values in the StandardActionsModel, as appropriate
        standardActions = {"ovaryNumber", "stomachNumber", "tissueNumber", "finclipNumber"}
        if property in standardActions:
            saIndex = self._standard_actions_model.get_item_index(rolename="key", value=property)
            self.StandardActionsModel = {"index": saIndex, "property": property, "value": value}

        # logging.info('updating the list with value: ' + str(value))

        # Update the model with the given property + value
        self._model.setProperty(index, property, value)

        # Update the Database
        # Check to see if this SPECIMEN child record already exists, so if we're doing an UPDATE
        action_to_id = {"linealValue": "linealSpecimenId", "sex": "sexSpecimenId",
                        "ageNumber": "ageSpecimenId", "ageTypeName": "ageSpecimenId",
                        "weight": "weightSpecimenId",
                        "ovaryNumber": "ovarySpecimenId", "stomachNumber": "stomachSpecimenId",
                        "tissueNumber": "tissueSpecimenId", "finclipNumber": "finclipSpecimenId"}
        if property in action_to_id:
            specimen_id_type = action_to_id[property]
            specimen_id = model_item[specimen_id_type]

        parent_specimen_id = self._app.state_machine.specimen["parentSpecimenId"]

        catch_id = self._app.state_machine.species["catch_id"]
        species_sampling_plan_id = model_item["speciesSamplingPlanId"]

        # Get action_type_id + measurement_type_id as these are used to create the record as needed.
        if property == "linealValue":
            action_type_id = model_item["linealTypeId"]
            action_type = TypesLu.get(TypesLu.type_id == action_type_id)
            measurement_type_id = TypesLu.get(TypesLu.category == "Measurement", TypesLu.type == action_type.type).type_id

        elif property == "ageNumber":
            age_type_id, age_type_name = self._get_age_id_name()
            action_type_id = age_type_id
            self._model.setProperty(index, "ageTypeId", action_type_id)
            measurement_type_id = TypesLu.get(TypesLu.category == "Measurement", TypesLu.type == "Barcode").type_id

        elif property == "ageTypeName":
            action_type_id = TypesLu.get(TypesLu.category == "Action", TypesLu.type == "Age ID",
                                         TypesLu.subtype == value).type_id
            measurement_type_id = TypesLu.get(TypesLu.category == "Measurement", TypesLu.type == "Barcode").type_id

            # Update the model with the new ageTypeId as well, given that we just selected a new ageTypeName
            self._model.setProperty(index, "ageTypeId", action_type_id)

        else:
            property_to_action = {"sex": "Sex", "weight": "Weight",
                                  "ovaryNumber": "Ovary ID", "stomachNumber": "Stomach ID",
                                  "tissueNumber": "Tissue ID", "finclipNumber": "Finclip ID"}
            if property in property_to_action:
                action_type = property_to_action[property]
                action_type_id = TypesLu.get(TypesLu.category == "Action", TypesLu.type == action_type).type_id
            else:
                action_type_id = None
            if property == "weight":
                measurement_type_id = TypesLu.get(TypesLu.category == "Measurement", TypesLu.type == "Weight").type_id
            else:
                measurement_type_id = None

        new_specimen, created = Specimen.get_or_create(specimen=specimen_id)
        query = Specimen.update(parent_specimen=parent_specimen_id,
                                action_type=action_type_id,
                                measurement_type=measurement_type_id,
                                catch=catch_id,
                                species_sampling_plan=species_sampling_plan_id
                                ).where(Specimen.specimen == new_specimen.specimen)
        query.execute()

        # logging.info('right before update: value: ' + str(value))
        # logging.info('new specimen: ' + str(new_specimen.specimen))
        if property in ["sex", "ovaryNumber", "stomachNumber", "tissueNumber", "finclipNumber"]:
            query = Specimen.update(alpha_value=str(value)).where(Specimen.specimen == new_specimen.specimen)
            query.execute()
        elif property in ["linealValue", "weight", "ageNumber"]:
            query = Specimen.update(numeric_value=value).where(Specimen.specimen == new_specimen.specimen)
            query.execute()

        if created:
            # Update the model with the new specimen_id for the given specimen_id_type if a new record is created
            self._model.setProperty(index, specimen_id_type, new_specimen.specimen)

        # Update the special actions indicator - this must be done after the database has been updated, otherwise
        # increments will not show up
        special_actions_indicator = self._get_special_actions_indicator(index=index)
        # logging.info('sa indicator: ' + str(special_actions_indicator))
        self._model.setProperty(index=index, property="special", value=special_actions_indicator)

        # Play the appropriate sound
        if property == "linealValue":
            if "length" in self.linealType.lower():
                self._app.sound_player.play_sound(sound_name="takeLength", override=False)
            elif "width" in self.linealType.lower():
                self._app.sound_player.play_sound(sound_name="takeWidth", override=False)
        elif property == "weight":
            self._app.sound_player.play_sound(sound_name="takeWeight", priority=10, override=False)
        elif property == "ageNumber":
            self._app.sound_player.play_sound(sound_name="takeBarcode", priority=30, override=True)

        # Update the appropriate tab values
        if property in ["linealValue", "sex"]:
            tabIndex = 0
        elif property in ["weight", "ageNumber", "ageTypeName"]:
            tabIndex = 1
        else:
            tabIndex = 2

        # Return to actionMode = add
        self.actionMode = "add"

        self.valueChanged.emit(tabIndex, property)

    def _get_typed_value(self, property, value):
        """
        Method to convert the value to an appropriate type given the property
        :param property:
        :param value:
        :return:
        """

        # Try converting value to a float
        reals = ["linealValue", "length", "width", "weight"]
        if property in reals:
            try:
                value = float(value)
            except Exception as ex:
                pass

        # Try converting value to an int
        ints = ["ageNumber", "finclipNumber", "ovaryNumber", "stomachNumber", "tissueNumber"]
        if property in ints:
            try:
                value = int(value)
            except Exception as ex:
                pass
                # value = str(value)

        # strings = []
        # if property in strings:
        #     value = str(value)

        return value

    def _check_for_errors(self, add_or_update, property, value):
        """
        Method to run a series of error checks against the given property and value
        :param property: str -
        :param value: str -
        :return:
        """
        if add_or_update not in ["add", "update"]:
            return

        if property is None:
            return

        # Convert the value into an appropriate type
        value = self._get_typed_value(property=property, value=value)

        errors = []

        # Get the currently select specimen item if a row is selected
        if self._app.state_machine.specimen["row"] != -1:
            item = self._model.get(self._app.state_machine.specimen["row"])

        # linealValue only checks
        if property == "linealValue":
            if value == 0:
                errors.append("Zero Length Value")
            elif value is None or math.isnan(value):
                errors.append("No Length Value")

            # 2019 Patch - skip checking for lengths > 100 for Longnose (47) and Big (42) skates as they happen often
            skate_taxon_ids = [42, 47]

            # logging.info(f"skates: {skate_taxon_ids}, state_machine: {self._app.state_machine.species['taxonomy_id']}")

            if "length" in self.linealType.lower() and value is not None:
                if value > 100 and self._app.state_machine.species["taxonomy_id"] not in skate_taxon_ids:
                    errors.append("Length is greater than 100cm (= board length)")

            elif "width" in self.linealType.lower() and value is not None:
                if value < 0.8:
                    errors.append("Width is less than 0.8cm, calipers set to inches?")

            # logging.info('linealType: {0}'.format(self.linealType))

        # Weight only checks
        if property == "weight":
            if value is not None:
                if value > 60:
                    errors.append("Weight is greater than 60kg (= scale maximum)")

        # ageNumber only checks
        if property == "ageNumber":
            # Updating the age barcode...a bunch of checks

            # logging.info('ageNum: ' + str(item["ageNumber"]))
            if self._app.state_machine.specimen["row"] != -1 and item["ageNumber"] is not None and \
                    item["ageNumber"] != 0:
                errors.append("barcode already populated")

            if value is None:
                errors.append("barcode value is null")

            else:
                if value < 100000000 or value > 103000000:
                    errors.append("barcode outside range:\n\t100,000,000 <= barcode <= 103,000,000")

                try:
                    count_historical = BarcodesLu.select().where(BarcodesLu.barcode == value).count()
                    count_current = Specimen.select() \
                        .join(TypesLu, on=(TypesLu.type_id == Specimen.action_type).alias('types')) \
                        .where((Specimen.numeric_value == value) &
                               (TypesLu.category == "Action") &
                               (TypesLu.type == "Age ID")) \
                        .count()
                    if (count_historical > 0 or count_current > 0) and item["ageNumber"] != 0:
                        errors.append("barcode duplicate found")
                except Exception as ex:
                    pass

        """
        Combination checks for length/weight relationships - must have a row specified to perform comparisons, thus
        check that the state machine has an identified specimen with a row value != -1.  Also only run this check
        when a new specimen row is added, (i.e. add_or_update == "update", for otherwise it can fire on a new
        length + sex entry and the highlighted row has an existing weight, which is then used for comparsion.  That's
        a no no
        """
        if add_or_update == "update" and \
            (property == "linealValue" or property == "weight" or property == "sex") and \
            self._app.state_machine.specimen["row"] != -1:

            # Check against historical length / weight ratio

            try:
                setting = Settings.select().where(Settings.parameter == "Length Weight Relationship Lower Weight Threshold").get()
                weight_lower_bound = float(setting.value)

                # logging.info('item linealValue, weight, sex: ' + str(item['linealValue']) + ', ' +
                #              str(item['weight']) + ', ' + str(item['sex']))
                # logging.info('property: ' + str(property) + ', value: ' + str(value))

                type = TypesLu.select().where(TypesLu.type_id == item["linealTypeId"]).get()
                linealType = type.type

                params = LengthWeightRelationshipLu.select().where(
                    LengthWeightRelationshipLu.taxonomy == self._app.state_machine.species["taxonomy_id"],
                    LengthWeightRelationshipLu.sex_code == item["sex"])


                if linealType == "Length" and \
                    params.count() == 1 and \
                    ((property == "linealValue" and
                              value != 0 and
                              item["weight"] is not None and
                              item["weight"] != 0 and
                              not math.isnan(item["weight"])) or
                     (property == "weight" and
                              item["linealValue"] is not None and
                              item["linealValue"] != 0 and
                              not math.isnan(item["linealValue"]))):

                    setting = Settings.select().where(Settings.parameter == "Length Weight Relationship Tolerance").get()
                    tolerance = float(setting.value)

                    params = params.get()
                    std_error = params.final_regr_stderr

                    if property == "linealValue":
                        model_weight = float(item["weight"])
                    elif property == "weight":
                        model_length = float(item["linealValue"])
                    else:
                        model_weight = float(item["weight"])
                        model_length = float(item["linealValue"])

                    # Weight changed
                    if property == "weight" and value >= weight_lower_bound:
                        exp_weight = math.exp(math.log(model_length) * float(params.lw_exponent_cmkg) + float(params.lw_coefficient_cmkg))

                        error_bound = math.exp(math.log(exp_weight) - 3*std_error)
                        lower_bound = exp_weight - error_bound
                        upper_bound = exp_weight + error_bound
                        if value < lower_bound or value > upper_bound:
                            errors.append("Length/Weight relationship outside tolerance of\n\n\t" +
                                          '{:.2f}'.format(lower_bound) + " kg <= weight <= " + '{:.2f}'.format(upper_bound) + " kg")

                        # if (math.fabs(value - exp_weight)/exp_weight) > tolerance:
                        #     errors.append("Length/Weight relationship outside tolerance of " + str(tolerance*100) + "%")

                    # LinealValue changed
                    elif property == "linealValue" and model_weight >= weight_lower_bound:
                        exp_weight = math.exp(math.log(value) * float(params.lw_exponent_cmkg) + float(params.lw_coefficient_cmkg))

                        error_bound = math.exp(math.log(exp_weight) - 3*std_error)
                        lower_bound = exp_weight - error_bound
                        upper_bound = exp_weight + error_bound
                        if model_weight < lower_bound or model_weight > upper_bound:
                            errors.append("Length/Weight relationship outside tolerance of\n\n\t" +
                                          '{:.2f}'.format(lower_bound) + " kg <= weight <= " + '{:.2f}'.format(upper_bound) + " kg")

                        # if (math.fabs(model_weight - exp_weight)/exp_weight) > tolerance:
                        #     errors.append("Length/Weight relationship outside tolerance of " + str(tolerance*100) + "%")

                    # Sex changed
                    elif property == "sex" and model_weight >= weight_lower_bound:
                        params = LengthWeightRelationshipLu.select().where(
                            LengthWeightRelationshipLu.taxonomy == self._app.state_machine.species["taxonomy_id"],
                            LengthWeightRelationshipLu.sex_code == value).get()
                        exp_weight = math.exp(math.log(model_length) * float(params.lw_exponent_cmkg) + float(params.lw_coefficient_cmkg))

                        error_bound = math.exp(math.log(exp_weight) - 3*std_error)
                        lower_bound = exp_weight - error_bound
                        upper_bound = exp_weight + error_bound
                        if model_weight < lower_bound or model_weight > upper_bound:
                            errors.append("Length/Weight relationship outside tolerance of\n\n\t" +
                                          '{:.2f}'.format(lower_bound) + " kg <= weight <= " + '{:.2f}'.format(upper_bound) + " kg")

                        # if (math.fabs(model_weight - exp_weight)/exp_weight) > tolerance:
                        #     errors.append("Length/Weight relationship outside tolerance of " + str(tolerance*100) + "%")

            except Exception as ex:
                logging.info('Error checking historical length / weight ratio: ' + str(ex))

        if len(errors) > 0:
            self._app.sound_player.play_sound(sound_name="error", priority=20, override=True)
            errorsStr = "\n".join(str(i+1) + ".  " + x for i, x in enumerate(errors))
            self.invalidEntryReceived.emit(add_or_update, property, value, errorsStr)
            return True

        else:

            return False

    @pyqtSlot(int)
    def delete_list_item(self, index):
        """
        Method to delete the list item with the given id
        :param index: int - primary key of the item to delete
        :return:
        """
        if not isinstance(index, int):
            return

        item = self._model.get(index=index)

        # Delete from the Model
        self._model.removeItem(index=index)

        # Delete from the Database
        # specimen = Specimen.get(Specimen.specimen == item["parentSpecimenId"])
        # specimen.delete_instance(recursive=True)
        delete_query = Specimen.delete().where((Specimen.parent_specimen == item["parentSpecimenId"]) |
                                               (Specimen.specimen == item["parentSpecimenId"]))
        delete_query.execute()

        # Update the specimenCount if an earlier item was deleted
        # Decrement the basketCount
        self.specimenCount -= 1

        # Decrement the specimen count appropriately (i.e. in an earlier index is deleted)
        """
        1   0
        2   1   < delete this specimen
        3   2
        4   3

        should become:
        1   0
        3   2  >  2   1
        4   3  >  3   2
        """
        if index < self._specimen_count:
            for i in range(index, self._specimen_count):
                parentSpecimenId = self._model.get(i)["parentSpecimenId"]
                self._app.state_machine.specimen = {"parentSpecimenId": parentSpecimenId, "row": i}
                self._model.setProperty(i, "parentSpecimenNumber", i+1)
                # self.update_list_item("parentSpecimenNumber", i+1)

    @pyqtSlot(QVariant)
    def delete_sub_specimen(self, specimen_id):
        """
        Method to delete a sub-specimen from the specimen table.  This is only called by numPad
        when it is cleared out and applied to one of the four items of Ovary/Stomach/Tissue/Finclip
        tab
        :param specimen_id: int - primary key in Specimen table to delete
        :return:
        """
        if not isinstance(specimen_id, int):
            return

        # This should be an individual instance of a specimen, i.e. not a whole fish
        try:
            specimen = Specimen.select().where(Specimen.specimen == specimen_id).get()
            specimen.delete_instance(recursive=True, delete_nullable=True)
        except DoesNotExist as ex:
            logging.info("Specimen does not exist > specimen_id: " + str(specimen_id) + ", " + str(ex))
        except Exception as ex:
            logging.info("Error deleting specimen: " + str(ex))

        # Update the special action indicator appropriately
        index = self._app.state_machine.specimen["row"]
        indicator = self._get_special_actions_indicator(index=index)
        self._model.setProperty(index=index, property="special", value=indicator)

    @pyqtSlot(str, str, str)
    def print_job(self, comport, action_type, specimen_number):
        """
        Great reference + example code for printing using EPL commands:
        https://www.xtuple.org/node/1083

        EPL Reference:
        https://www.zebra.com/content/dam/zebra/manuals/en-us/printer/epl2-pm-en.pdf

        :return:
        """

        if self._printer_thread.isRunning():
            return

        if action_type is None or specimen_number is None:
            return

        # Line 1 - Header
        header = "NOAA/NWFSC/FRAM - WCGBT Survey"

        # Line 2a - PI + Specimen Type (Ovary, etc)
        try:
            investigator = PrincipalInvestigatorLu.select() \
                .where(PrincipalInvestigatorLu.full_name == "FRAM Standard Survey").get().last_name
        except DoesNotExist as ex:
            investigator = "FRAM"

        # try:
        #     investigator = TypesLu.select() \
        #         .where(TypesLu.type_id == self._app.state_machine.principalInvestigator).get().type
        # except:
        #     investigator = "FRAM"

        # Line 2b
        if action_type in ["ovaryNumber", "stomachNumber", "tissueNumber", "finclipNumber",
                           "testesNumber"]:
            action = action_type.replace("Number", "").title()
        else:
            return # bogus action_type passed in - should only be one of the standard FRAM survey items

        # Line 3 - Haul #
        haul_id = self._app.state_machine.haul["haul_number"]
        if "t" in haul_id and len(haul_id) > 3:
            haul_id = "t" + haul_id[-4:]

        # Line 4 - Species Scientific Namae
        species = self._app.state_machine.species["scientific_name"]

        # Line 5 - Length / Weight / Sex
        try:
            length = weight = sex = stomach = tissue = ovary = testes = ""
            parent_specimen = self._app.state_machine.specimen["parentSpecimenId"]

            specimens = (Specimen.select(Specimen, TypesLu)
                         .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias('types'))
                         .where(Specimen.parent_specimen == parent_specimen))
            for specimen in specimens:
                if specimen.types.type == "Length":
                    length = specimen.numeric_value
                elif specimen.types.type == "Weight":
                    weight = round(specimen.numeric_value, 2)
                elif specimen.types.type == "Sex":
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
                short_specimen_number = ", SP#: " + short_specimen_number
        except Exception as ex:
            logging.error(f"Error creating the shortened specimen number: {ex}")

        # Line 6
        date = datetime.now().strftime("%Y%m%d %H%M%S")            # date = "08/16/2015"

        # Line 7
        try:
            haul = Hauls.select().where(Hauls.haul == self._app.state_machine.haul["haul_id"]).get()
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

            logging.info(f"{location}")
        except Exception as ex:
            location = "Unknown, Unknown, Unknown"
        # location = str(latitude) + ", " + str(longitude)
        # location = "47 15.54N, 126 27.55W"
        # logging.info("location: {0}".format(location))

        # Line 8 - Specimen number
        # If no character at the end, add an A, other increase the character by 1 and update the list item
        if specimen_number[-1:].isdigit():
            specimen_number += "A"
        else:
            char = chr(ord(specimen_number[-1:]) + 1)
            specimen_number = str(specimen_number[:-1]) + char
        self.update_list_item(action_type, specimen_number)

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

        # LEGACY - keep for testing purposes
        # barcode_number = 1235098082
        # vessel = self._app.state_machine.haul["vessel_name"]
        # station_number = self._app.state_machine.haul["station_number"]
        # vessel = "Excalibur"
        # station_number = "7234"

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

        # vessel_bytes = bytes("A0,10,0,4,1,1,N,\"" + "Vessel: " + vessel + suffix, "UTF-8")
        # haul_id_bytes = bytes("A0,50,0,4,1,1,N,\"" + "Haul ID: " + str(haul_id) + suffix, "UTF-8")
        # station_number_bytes = bytes("A0,90,0,4,1,1,N,\"" + "Station Number: " + str(station_number) + suffix, "UTF-8")
        # species_bytes = bytes("A0,130,0,4,1,1,N,\"" + "Species: " + species + suffix, "UTF-8")
        # barcode_number_bytes = bytes("A0,170,0,4,1,1,N,\"" + "Barcode: " + str(barcode_number) + suffix, "UTF-8")
        # length_bytes = bytes("A0,210,0,4,1,1,N,\"" + "Length: " + str(length) + " cm\"\n", "UTF-8")
        # investigator_bytes = bytes("A0,250,0,4,1,1,N,\"" + "Investigator: " + investigator + suffix, "UTF-8")
        # date_bytes = bytes("A0,290,0,4,1,1,N,\"" + "Date: " + str(date) + suffix, "UTF-8")
        # barcode_bytes = bytes("B0,330,0,1,3,3,72,N,\"" + str(barcode_number) + suffix, "UTF-8")
        #
        # rows = [lead_in_bytes, vessel_bytes, haul_id_bytes, station_number_bytes, species_bytes, barcode_number_bytes,
        #         length_bytes, investigator_bytes, date_bytes, barcode_bytes, lead_out_bytes]

        if comport is None:
            comport = "COM9"

        kwargs = {"comport": comport, "rows": rows}

        # logging.info("thread status: " + str(self._printer_thread.isRunning()))
        # if not self._printer_thread.isRunning():

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
        self._printer_thread.quit()
        # self._printer_thread.terminate()

    @pyqtSlot(str)
    def playSound(self, sound_name):
        """
        Play a sound
        :param sound_name:
        :return:
        """
        if not isinstance(sound_name, str):
            return

        self._app.sound_player.play_sound(sound_name=sound_name)


class TestPrinters(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

        self.p = Printer()
        # headers = ["uid", "scientific name", "type"]
        # data = "1\tSebastes aurora\tfish\n2\tSebastes pinniger\tfish\n3\tbangal\tinvert."
        # parent = None
        # self.testmodel = FramTreeModel(headers=headers, data=data, parent=parent)

    def test_list_printers(self):

        logging.info(str(self.p._printers))

    def test_zebra_printer(self):

        logging.info(str(self.p._printer))

if __name__ == '__main__':
    unittest.main()
