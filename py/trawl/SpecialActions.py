__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        SpecialActions.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 11, 2016
# License:     MIT
#-------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QVariant, QThread
from PyQt5.QtQml import QJSValue
from py.common.FramListModel import FramListModel
import logging
from py.trawl.TrawlBackdeckDB_model import Specimen, TypesLu, SpeciesSamplingPlanLu, \
    BarcodesLu, Settings, LengthWeightRelationshipLu, Hauls, PrincipalInvestigatorLu, PiActionCodesLu, TaxonomyLu
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
from py.common.SoundPlayer import SoundPlayer
from py.common.LabelPrinter import LabelPrinter
from datetime import datetime
from copy import deepcopy
import re


class SpecialActionsModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="parentSpecimenId")         # SPECIMEN.SPECIMEN_ID for the parent specimen record
        self.add_role_name(name="parentSpecimenNumber")     # What's shown to the user / 1st column of tvSamples table
        self.add_role_name(name="specimenId")               # SPECIMEN.SPECIMEN_ID for the child specimen record
        self.add_role_name(name="specialActionId")
        self.add_role_name(name="piId")
        self.add_role_name(name="principalInvestigator")
        self.add_role_name(name="specialAction")
        self.add_role_name(name="value")
        self.add_role_name(name="widgetType")


class PiProjectModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="piId")
        self.add_role_name(name="principalInvestigator")
        self.add_role_name(name="planId")
        self.add_role_name(name="planName")


class SpecialActions(QObject):
    """
    Class for the SpecialActionsScreen
    """
    modelChanged = pyqtSignal()
    modelInitialized = pyqtSignal()
    specimenTypeChanged = pyqtSignal()
    parentSpecimenCountChanged = pyqtSignal()
    rowIndexChanged = pyqtSignal()
    rowWidgetTypeChanged = pyqtSignal()
    piProjectModelChanged = pyqtSignal()
    printerStatusReceived = pyqtSignal(str, bool, str, arguments=["comport", "success", "message"])

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

        # Set up the models
        self._model = SpecialActionsModel()
        self._pi_project_model = PiProjectModel()

        self._sound_player = SoundPlayer()
        self._label_printer = LabelPrinter(app=self._app, db=self._db)
        self._label_printer.tagIdChanged.connect(self._updated_printer_tag_received)
        self._label_printer.printerStatusReceived.connect(self._printer_status_received)

        self._standardSurveySpecimen = None
        self._parent_specimen_count = 0

        self._row_index = -1
        self._row_widget_type = None

    def _printer_status_received(self, comport, success, message):
        """
        Method to catch the message coming back from the printer
        :param comport:
        :param success:
        :param message:
        :return:
        """
        self.printerStatusReceived.emit(comport, success, message)
        # logging.info('message received: ' + str(message))

    def _updated_printer_tag_received(self, tag_id):
        """
        Method used to catch the newly updated printer tag and then use that to derive the tvSamples rowIndex in question
        and then to an upsert on that row to save the item["value"] to the database
        :param str:
        :return:
        """
        # logging.info('new tag_id: ' + str(tag_id))

        # Update the model
        previous_tag_id = None
        if not tag_id[-1:].isdigit():
            if tag_id[-1:] == "A":
                previous_tag_id = tag_id[:-1]
            else:
                char = chr(ord(tag_id[-1:]) - 1)
                previous_tag_id = str(tag_id[:-1]) + char

        # logging.info('previous_tag_id: ' + str(previous_tag_id))
        index = self._model.get_item_index(rolename="value", value=previous_tag_id)
        if index != -1:
            self._model.setProperty(index=index, property="value", value=tag_id)
            self.upsert_specimen(row_index=index)
        # logging.info('index found and upserted complete, index: ' + str(index))

    @pyqtSlot(str, int, str, str)
    def printLabel(self, comport, pi_id, action, specimen_number):
        """
        Method called from QML to print a label.  This passes a request to the self._label_printer object
        :return:
        """
        self._label_printer.print_job(comport=comport, pi_id=pi_id, action=action, specimen_number=specimen_number)

    @pyqtProperty(QVariant, notify=modelChanged)
    def model(self):
        """
        return the SpecimensModel
        :return:
        """
        return self._model

    @pyqtProperty(QVariant, notify=piProjectModelChanged)
    def piProjectModel(self):
        return self._pi_project_model

    @pyqtProperty(str)
    def rowWidgetType(self):
        """
        Method to return the widgetType of the currently selected tvSamples row.  This is used to keep track
        of what type of automatic measurement the row can take in from scales, barcode reader, etc.
        :return:
        """
        return self._row_widget_type

    @rowWidgetType.setter
    def rowWidgetType(self, value):
        """
        Method to set the self._row_widget_type
        :param value: str - enumerated values include:  id, measurement, coral, salmon, sex - same as the
        states in special actions
        :return:
        """
        # if value not in ["id", "measurement", "coral", "salmon", "sex", "sponge", "maturityLevel", "yesno"]:
        #     return

        self._row_widget_type = value
        self.rowWidgetTypeChanged.emit()

    @pyqtProperty(int)
    def rowIndex(self):
        """
        Method to return the currently selected row of the tvSamples TableView
        :return:
        """
        return self._row_index

    @rowIndex.setter
    def rowIndex(self, value):
        """
        Method to set the self._row_index to keep track of the currently selected row in tvSamples
        This is needed when taking in a measurement from the barcode scanner or an automatic
        length / weight measurement
        :param value:
        :return:
        """
        if not isinstance(value, int):
            return

        self._row_index = value
        self.rowIndexChanged.emit()

    @pyqtProperty(QVariant, notify=parentSpecimenCountChanged)
    def parentSpecimenCount(self):
        return self._parent_specimen_count

    @parentSpecimenCount.setter
    def parentSpecimenCount(self, value):
        if not isinstance(value, int):
            return
        self._parent_specimen_count = value
        self.parentSpecimenCountChanged.emit()

    @pyqtProperty(QVariant, notify=specimenTypeChanged)
    def standardSurveySpecimen(self):
        return self._standardSurveySpecimen

    @standardSurveySpecimen.setter
    def standardSurveySpecimen(self, value):
        if not isinstance(value, bool) and not isinstance(value, None):
            return

        self._standardSurveySpecimen = value
        self.specimenTypeChanged.emit()

    @pyqtSlot(int, result=str)
    def get_tag_id(self, row_index):
        """
        Method to get a new tag ID
        :return:
        """
        # mapping = {"ovaryNumber": {"type": "000", "action": "Ovary", "id": "ovarySpecimenId"},
        #            "stomachNumber": {"type": "001", "action": "Stomach", "id": "stomachSpecimenId"},
        #            "tissueNumber": {"type": "002", "action": "Tissue", "id": "tissueSpecimenId"},
        #            "finclipNumber": {"type": "003", "action": "Finclip", "id": "finclipSpecimenId"}}
        # if action not in mapping:
        #     return
        if not isinstance(row_index, int) or row_index == -1:
            return

        item = self._model.get(row_index)
        pi_id = item["piId"]
        action_type_id = item["specialActionId"]
        value = item["value"]
        specimen_id = item["specimenId"]

        try:

            # Item 1 - Year / Item 2 - Vessel
            for setting in Settings.select():
                if setting.parameter == "Survey Year":
                    year = setting.value
                    try:
                        now_year = datetime.now().strftime("%Y")
                        if year != now_year:
                            year = now_year
                    except Exception as ex2:
                        year = datetime.now().strftime("%Y")
                        logging.info(f"unable to update the year: {ex2}")
                    logging.info(f"year = {year}")

                elif setting.parameter == "Vessel ID":
                    vessel_id = setting.value

            # Item 3 - Haul ID
            haul_number = str(self._app.state_machine.haul["haul_number"])
            if len(haul_number) > 3:
                haul_number = haul_number[-3:]

            # Item 4 - Specimen Type Code
            try:
                pi_action_code_id = \
                    PiActionCodesLu.select(PiActionCodesLu) \
                        .join(PrincipalInvestigatorLu,
                              on=(PiActionCodesLu.principal_investigator == PrincipalInvestigatorLu.principal_investigator)) \
                        .join(TypesLu, on=(PiActionCodesLu.action_type == TypesLu.type_id).alias('types')) \
                        .where(PrincipalInvestigatorLu.principal_investigator == pi_id,
                               TypesLu.type_id == action_type_id).get().pi_action_code
            except DoesNotExist as ex:
                pi_action_code_id = 999     # Give it a bogus entry
            # logging.info('pi action code: ' + str(pi_action_code_id))
            specimen_type_id = str(pi_action_code_id).zfill(3)

            # Item 5 - Specimen Number
            # Query for specimen number - get the latest one for the given specimen type (i.e. ovary, stomach, tissue, finclip)
            spec_num_length = 20
            # if pi_action_code_id != 999:
                # specimens = (Specimen.select(Specimen, TypesLu)
                #          .join(SpeciesSamplingPlanLu,
                #                on=(SpeciesSamplingPlanLu.species_sampling_plan==Specimen.species_sampling_plan).alias('plan'))
                #          .join(PrincipalInvestigatorLu,
                #                on=(SpeciesSamplingPlanLu.principal_investigator==PrincipalInvestigatorLu.principal_investigator).alias('pi'))
                #          .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias('types'))
                #          .where(TypesLu.type_id == action_type_id,
                #                 PrincipalInvestigatorLu.principal_investigator==pi_id,
                #                 fn.length(Specimen.alpha_value) == spec_num_length).order_by(Specimen.alpha_value.desc()))

            # specimens = (Specimen.select(fn.substr(Specimen.alpha_value, 18, 3).alias('specimen_number'))
            #              .join(SpeciesSamplingPlanLu,
            #                    on=(SpeciesSamplingPlanLu.species_sampling_plan == Specimen.species_sampling_plan).alias('plan'))
            #              .join(PrincipalInvestigatorLu,
            #                    on=(SpeciesSamplingPlanLu.principal_investigator == PrincipalInvestigatorLu.principal_investigator).alias('pi'))
            #              .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias('types'))
            #              .where(TypesLu.type_id == action_type_id,
            #                     PrincipalInvestigatorLu.principal_investigator == pi_id,
            #                     ((fn.length(Specimen.alpha_value) == spec_num_length) |
            #                      (fn.length(Specimen.alpha_value) == spec_num_length + 1)),
            #                     (fn.substr(Specimen.alpha_value, 1, 4) == year),
            #                     (fn.substr(Specimen.alpha_value, 6, 3) == vessel_id)).order_by(
            #     fn.substr(Specimen.alpha_value, 18, 3).desc()))

            specimens = (Specimen.select(fn.substr(Specimen.alpha_value, 18, 3).alias('specimen_number'))
                .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias('types'))
                .where(TypesLu.type_id == action_type_id,
                       ((fn.length(Specimen.alpha_value) == spec_num_length) |
                        (fn.length(Specimen.alpha_value) == spec_num_length + 1)),
                       (fn.substr(Specimen.alpha_value, 1, 4) == year),
                       (fn.substr(Specimen.alpha_value, 6, 3) == vessel_id)).order_by(
                fn.substr(Specimen.alpha_value, 18, 3).desc()))

            # else:
            #
            #     where_clause = (((fn.length(Specimen.alpha_value) == spec_num_length) |
            #                      (fn.length(Specimen.alpha_value) == spec_num_length + 1)) &
            #                     (Specimen.alpha_value.contains("-999-")))
            #     specimens = (Specimen.select(Specimen)
            #             .join(SpeciesSamplingPlanLu,
            #                   on=(SpeciesSamplingPlanLu.species_sampling_plan == Specimen.species_sampling_plan).alias('plan'))
            #             .join(PrincipalInvestigatorLu,
            #                   on=(
            #                       SpeciesSamplingPlanLu.principal_investigator == PrincipalInvestigatorLu.principal_investigator).alias(
            #                   'pi'))
            #             .where(where_clause).order_by(Specimen.alpha_value.desc()))

            # Get the newest specimen.  Note that one may not exist as it hasn't been created yet
            try:
                last_specimen_num = specimens.get().specimen_number
                # last_specimen_num = specimens.get().alpha_value
            except DoesNotExist as dne:
                last_specimen_num = None
            logging.info('last specimen num: ' + str(last_specimen_num))

            """
            Use Cases
            1. No existing SPECIMEN record exists for this specimen_type - insert a new one by one-upping the
                last number for this specimen_type
            2. An existing SPECIMEN exists for this specimen_type - so a number should already be added, don't
               override then, correct?  We should only give the next number up ever after having queried the
               specimen table for the last number for this specimen_type - which is what we have in
               last_specimen_num
            """
            # logging.info('value: ' + str(value))

            if specimen_id is None or specimen_id == "" or \
                value is None or value == "" or len(value) < spec_num_length or value == "Error":
                # No specimen record exists for this specimen_type, so we're creating a new specimen_value
                # So one up the highest number and put an "a" at the end of it
                if last_specimen_num:
                    specimen_num = str(int(re.sub(r'[^\d.]+', '', last_specimen_num)[-3:]) + 1).zfill(3)
                else:
                    specimen_num = "001"
            else:
                # Specimen record exists, then nothing to do here.  Clicking the print button will up the last
                # alpha character
                return item["value"]

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
            tag_id = "Error"

        # logging.info('tag_id: ' + str(tag_id))

        return tag_id

    def _get_widget_type(self, display_name):
        """
        Method to return the type of the widget with a given display name.  This drives which UI widgets
        are displayed on the right side of SpecialActionsScreen.qml
        :param display_name: str - text of the specialAction role that is displayed in the tvSamples TableView
        :return:
        """
        if not isinstance(display_name, str):
            return

        display_name = display_name.lower()

        widget_type = "id"
        if "sex" in display_name:
            widget_type = "sex"
        elif "id" in display_name:
            widget_type = "id"
        elif "length" in display_name or \
                        "width" in display_name or \
                        "weight" in display_name:
            widget_type = "measurement"

        taxon_id = self._app.state_machine.species["taxonomy_id"]
        if self._app.process_catch.checkSpeciesType("salmon", taxonId=taxon_id):
            widget_type = "salmon"
        elif self._app.process_catch.checkSpeciesType("coral", taxonId=taxon_id):
            widget_type = "coral"
        elif self._app.process_catch.checkSpeciesType("sponge", taxonId=taxon_id):
            widget_type = "sponge"

        return widget_type

    def _get_value_type(self, value):
        """
        Method to convert the value to an appropriate type given the property
        :param value:
        :return:
        """
        try:
            value = float(value)
            return "numeric"

        except ValueError as ex:
            try:
                value = int(value)
                return "numeric"
            except ValueError as ex_int:
                pass

        return "alpha"

    @pyqtSlot()
    def initialize_pi_project_list(self):
        """
        Method to initialize the tvProjects list in the dlgSpecimen when Add Specimen is clicked
        :return:
        """
        self._pi_project_model.clear()
        taxon_id = self._app.state_machine.species["taxonomy_id"]
        plans = SpeciesSamplingPlanLu.select(SpeciesSamplingPlanLu, PrincipalInvestigatorLu) \
                    .join(PrincipalInvestigatorLu,
                          on=(SpeciesSamplingPlanLu.principal_investigator==PrincipalInvestigatorLu.principal_investigator).alias('pi')) \
                    .where((SpeciesSamplingPlanLu.parent_species_sampling_plan.is_null(True)) & \
                           (
                             (
                                 (SpeciesSamplingPlanLu.plan_name == "FRAM Standard Survey") &
                                 (
                                  (
                                    ((SpeciesSamplingPlanLu.display_name == "Salmon") |
                                    (SpeciesSamplingPlanLu.display_name == "Coral") |
                                    (SpeciesSamplingPlanLu.display_name == "Sponge")) &
                                    (SpeciesSamplingPlanLu.taxonomy == taxon_id)
                                  ) |
                                    (SpeciesSamplingPlanLu.display_name == "Whole Specimen ID"))
                             ) |
                            ((SpeciesSamplingPlanLu.taxonomy == taxon_id) &
                             (SpeciesSamplingPlanLu.plan_name != "FRAM Standard Survey")
                             )
                           )
                          ) \
                    .order_by(PrincipalInvestigatorLu.last_name)

        for plan in plans:

            is_coral = self._app.process_catch.checkSpeciesType("coral", taxon_id)
            if is_coral:
                if plan.display_name == "Whole Specimen ID":
                    continue
            is_sponge = self._app.process_catch.checkSpeciesType("sponge", taxon_id)
            if is_sponge:
                if plan.display_name == "Whole Specimen ID":
                    continue
            is_salmon = self._app.process_catch.checkSpeciesType("salmon", taxon_id)
            if is_salmon:
                pass

            plan_name = plan.plan_name
            if plan_name == "FRAM Standard Survey":
                plan_name = plan.display_name

            item = {"piId": plan.pi.principal_investigator,
                    "principalInvestigator": plan.pi.last_name,
                    "planId": plan.species_sampling_plan,
                    "planName": plan_name}
            self._pi_project_model.appendItem(item)

        self.modelInitialized.emit()

    def _create_list_template(self):
        """
        Method used to create the tvSpecimens list items that are applicable to this given species/taxonomy id
        This is used when initializing the list from either the Process Catch or the Fish Sampling Screen
        :return:
        """

        templates = []

        # Create a blank templates (i.e. no values) tableview items from existing protocols, but data is not populated
        taxon_id = self._app.state_machine.species["taxonomy_id"]
        plans = self._app.protocol_viewer.get_special_actions(taxon_id=taxon_id)
        parent_plans = [x for x in plans if x["parentPlan"] is None]

        for parent_plan in parent_plans:

            # self.parentSpecimenCount += 1

            # Have a protocol at the very top species sampling plan record, add it's actions to the list
            if parent_plan["topProtocol"] is not None:
                for action in parent_plan["actions"]:

                    is_coral = self._app.process_catch.checkSpeciesType("coral", taxon_id)
                    is_sponge = self._app.process_catch.checkSpeciesType("sponge", taxon_id)
                    if is_coral:
                        if action["displayName"] == "Whole Specimen ID":
                            # Don't include the Whole Specimen ID as an option for corals, as that is already included
                            # self.parentSpecimenCount -= 1
                            continue
                        specialAction = "Coral " + action["displayName"]
                    elif is_sponge:
                        if action["displayName"] == "Whole Specimen ID":
                            continue
                        specialAction = "Sponge " + action["displayName"]
                    else:
                        specialAction = action["displayName"]

                    item = {"parentSpecimenNumber": None,  # self.parentSpecimenCount,
                            "parentSpecimenId": None,
                            "specimenId": None,
                            "specialActionId": action["actionTypeId"],
                            "principalInvestigator": parent_plan["pi"],
                            "piId": parent_plan["piId"],
                            "specialAction": specialAction,
                            "widgetType": action["widgetType"],
                            "planId": parent_plan["plan"],
                            "value": None}
                    templates.append(item)
                    # self._model.appendItem(item)

            # Get all of the children species sampling plans and add their actions
            child_plans = [x for x in plans if x["parentPlan"] == parent_plan["plan"]]
            for child_plan in child_plans:

                for action in child_plan["actions"]:

                    is_coral = self._app.process_catch.checkSpeciesType("coral", taxon_id)
                    is_sponge = self._app.process_catch.checkSpeciesType("sponge", taxon_id)
                    if is_coral:
                        if action["displayName"] == "Whole Specimen ID":
                            continue
                        specialAction = "Coral " + action["displayName"]
                    elif is_sponge:
                        if action["displayName"] == "Whole Specimen ID":
                            continue
                        specialAction = "Sponge " + action["displayName"]
                    else:
                        specialAction = action["displayName"]

                    item = {"parentSpecimenNumber": None,  # self.parentSpecimenCount,
                            "parentSpecimenId": None,
                            "specimenId": None,
                            "specialActionId": action["actionTypeId"],
                            "principalInvestigator": parent_plan["pi"],
                            "piId": parent_plan["piId"],
                            "specialAction": specialAction,
                            "widgetType": action["widgetType"],
                            "planId": parent_plan["plan"],
                            "value": None}

                    templates.append(item)
                    # self._model.appendItem(item)

        return templates

    @pyqtSlot()
    def initialize_fish_sampling_list(self):
        """
        Method to initialize the tvSamples list when the screen is called from the FishSamplingScreen.qml screen. Query
        the database to retrieve existing specimens that have already been collected for this taxonomy_id
        for this given haul > could be at the ProcessCatch or the FishSampling level.  Will need to treat them
        differently if they come from ProcessCatchScreen v. FishSamplingScreen
        :return:
        """

        self._model.clear()

        templates = self._create_list_template()

        try:

            where_clause = (Specimen.specimen == self._app.state_machine.specimen["parentSpecimenId"])
            parent = (Specimen.select(Specimen, SpeciesSamplingPlanLu, PrincipalInvestigatorLu, TypesLu)
                       .join(SpeciesSamplingPlanLu,
                             on=(Specimen.species_sampling_plan == SpeciesSamplingPlanLu.species_sampling_plan).alias(
                                 "plan"))
                       .join(PrincipalInvestigatorLu,
                             on=(
                             SpeciesSamplingPlanLu.principal_investigator == PrincipalInvestigatorLu.principal_investigator).alias(
                                 "pi"))
                       .join(TypesLu, JOIN.LEFT_OUTER, on=(Specimen.action_type == TypesLu.type_id).alias("types"))
                       .where(where_clause)).get()

            self.parentSpecimenCount = self._app.state_machine.specimen["specimenNumber"]

            for template in templates:

                # Add the current template to the model
                current_item = deepcopy(template)
                current_item["parentSpecimenNumber"] = self.parentSpecimenCount
                current_item["parentSpecimenId"] = self._app.state_machine.specimen["parentSpecimenId"]
                self._model.appendItem(current_item)
                index = self._model.count - 1

                # Get the existing child from the database
                try:
                    child = Specimen.select(Specimen, TypesLu) \
                        .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias("types")) \
                        .where((Specimen.parent_specimen == parent.specimen) &
                               (Specimen.species_sampling_plan == current_item["planId"]) &
                               (Specimen.action_type == current_item["specialActionId"])).get()

                    # Update the value + specimenId, assuming that a record exists in the database (i.e. child exists)
                    value = None

                    # TODO - Todd Hay - might want to change the below logic when taking IDs
                    #  For instance, what if we have both a printed ID label, which has alpha
                    #  characters and then someone tries to take a barcode.  This would
                    #  continue to show the printed alpha tag ID and new show the barcode

                    if child.alpha_value is not None:
                        value = child.alpha_value
                    elif child.numeric_value is not None:
                        value = child.numeric_value
                    if index is not None:
                        self._model.setProperty(index=index, property="specimenId", value=child.specimen)
                        self._model.setProperty(index=index, property="value", value=value)
                except DoesNotExist as ex:
                    # Could not find a child record in the database, skip updating the model specimenId + value fields
                    pass
                except Exception as ex:
                    logging.info('other exception: ' + str(ex))
                    pass

        except DoesNotExist as ex:
            logging.error("record does not exist: " + str(ex))

        except Exception as ex:
            logging.error("General exception: " + str(ex))

    @pyqtSlot()
    def initialize_process_catch_list(self):
        """
        Method to initialize the tvSamples list when the screen is called from the ProcessCatchScreen.qml.
        This will list out all of the special actions for a given specimen
        :return:
        """
        self._model.clear()
        self.parentSpecimenCount = 0

        templates = self._create_list_template()

        """
        Query the database to retrieve existing specimens that have already been collected for this taxonomy_id
        for this given haul > could be at the ProcessCatch or the FishSampling level.  Will need to treat them differently
        if they come from ProcessCatchScreen v. FishSamplingScreen as follows:

        - ProcessCatchScreen.qml -

        - FishSamplingScreen.qml -
        """

        # Get All of the Parents first
        try:

            if self._app.state_machine.previousScreen == "processcatch":
                where_clause = ((Specimen.catch == self._app.state_machine.species["catch_id"]) &
                               (Specimen.parent_specimen.is_null(True)) &
                               ((SpeciesSamplingPlanLu.plan_name != "FRAM Standard Survey") |
                                ((SpeciesSamplingPlanLu.plan_name == "FRAM Standard Survey") &
                                 ((SpeciesSamplingPlanLu.display_name == "Whole Specimen ID") |
                                  (SpeciesSamplingPlanLu.display_name == "Coral") |
                                  (SpeciesSamplingPlanLu.display_name == "Salmon") |
                                  (SpeciesSamplingPlanLu.display_name == "Sponge")
                                  ))
                                ))
            elif self._app.state_machine.previousScreen == "fishsampling":
                where_clause = ((Specimen.parent_specimen == self._app.state_machine.specimen["parentSpecimenId"]) &
                                ((SpeciesSamplingPlanLu.plan_name != "FRAM Standard Survey") |
                                 ((SpeciesSamplingPlanLu.plan_name == "FRAM Standard Survey") &
                                  (SpeciesSamplingPlanLu.display_name == "Whole Specimen ID"))
                                 )
                                )

            parents = (Specimen.select(Specimen, SpeciesSamplingPlanLu, PrincipalInvestigatorLu, TypesLu)
                .join(SpeciesSamplingPlanLu,
                      on=(Specimen.species_sampling_plan == SpeciesSamplingPlanLu.species_sampling_plan).alias("plan"))
                .join(PrincipalInvestigatorLu,
                      on=(SpeciesSamplingPlanLu.principal_investigator == PrincipalInvestigatorLu.principal_investigator).alias("pi"))
                .join(TypesLu, JOIN.LEFT_OUTER, on=(Specimen.action_type == TypesLu.type_id).alias("types"))
                .where(where_clause))

            current_parent_specimen_id = -1

            for parent in parents:

                # Get all of the special actions that match this PI + Plan
                template = [x for x in templates if x["piId"] == parent.plan.pi.principal_investigator and
                                    x["planId"] == parent.plan.species_sampling_plan]

                # logging.info('template: ' + str(template))

                if current_parent_specimen_id != parent.specimen:
                    if self._app.state_machine.previousScreen == "processcatch":
                        self.parentSpecimenCount += 1
                    elif self._app.state_machine.previousScreen == "fishsampling":
                        self.parentSpecimenCount = self._app.state_machine.specimen["specimenNumber"]

                    # Add each of the items in the current template to the model.  Later we add in the actual values
                    for item in template:
                        current_item = deepcopy(item)
                        current_item["parentSpecimenNumber"] = self.parentSpecimenCount
                        if self._app.state_machine.previousScreen == "processcatch":
                            current_item["parentSpecimenId"] = parent.specimen
                        elif self._app.state_machine.previousScreen == "fishsampling":
                            current_item["parentSpecimenId"] = self._app.state_machine.specimen["parentSpecimenId"]
                        self._model.appendItem(current_item)

                # Iterate through all of the specimen children
                children = Specimen.select(Specimen, TypesLu) \
                    .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias("types")) \
                    .where(Specimen.parent_specimen == parent.specimen)

                for child in children:

                    if child.types.subtype is not None and child.types.subtype != "":
                        specialAction = child.types.subtype + " " + child.types.type
                    else:
                        specialAction = child.types.type

                    # Coral - need to prepend specialAction with Coral as appropriate, otherwise
                    # extra model rows are added.  This is a bad hack.  It deals with the fact that for our actions, we have
                    # nothing specific to corals, yet we display the term Coral in the Special Actions table, where in actions
                    # we do have the 3 specific Salmon actions...I don't like this difference at all.

                    # 05/11/2018 - added in the same issue for Sponge as for coral, as the survey team members want to start
                    # treating sponges similarly

                    # taxon_id = parent.plan.taxonomy_id
                    taxon_id = parent.plan.taxonomy.taxonomy

                    if self._app.process_catch.checkSpeciesType("coral", taxonId=taxon_id):
                        specialAction = "Coral " + specialAction
                    elif self._app.process_catch.checkSpeciesType("sponge", taxonId=taxon_id):
                        specialAction = "Sponge " + specialAction

                    # Get the proper value, i.e. alpha or numeric value
                    value = None

                    # TODO - Todd Hay - might want to change the below logic when taking IDs
                    #  For instance, what if we have both a printed ID label, which has alpha
                    #  characters and then someone tries to take a barcode.  This would
                    #  continue to show the printed alpha tag ID and new show the barcode

                    if child.alpha_value is not None:
                        value = child.alpha_value
                    elif child.numeric_value is not None:
                        value = child.numeric_value

                    """
                    Need to update 2 values in the item.  First need to find the exact item.
                    - specimenId
                    - value
                    """
                    index = [i for i, x in enumerate(self._model.items) if
                             x["piId"] == parent.plan.pi.principal_investigator and
                             x["planId"] == parent.plan.species_sampling_plan and
                             x["specialActionId"] == child.types.type_id and
                             x["parentSpecimenNumber"] == self.parentSpecimenCount]
                    if index is not None:
                        index = index[0]
                        self._model.setProperty(index=index, property="specimenId", value=child.specimen)
                        self._model.setProperty(index=index, property="value", value=value)

                    current_parent_specimen_id = parent.specimen

        except DoesNotExist as ex:
            logging.error("record does not exist: " + str(ex))

        except Exception as ex:
            logging.error("General exception: " + str(ex))

        # logging.info('model count: ' + str(self._model.count))
        # logging.info('model items: ' + str(self._model.items))

        # Add in the new template items at the bottom of the list
        if self._app.state_machine.previousScreen == "processcatch" or \
            (self._app.state_machine.previousScreen == "fishsampling" and self._model.count == 0):
            current_pi_id = -1
            current_plan_id = -1
            for template in templates:
                if template["piId"] != current_pi_id or template["planId"] != current_plan_id:
                    if self._app.state_machine.previousScreen == "processcatch":
                        self.parentSpecimenCount += 1
                    elif self._app.state_machine.previousScreen == "fishsampling":
                        self.parentSpecimenCount = self._app.state_machine.specimen["specimenNumber"]
                        template["parentSpecimenId"] = self._app.state_machine.specimen["parentSpecimenId"]
                    # self.parentSpecimenCount += 1
                    current_pi_id = template["piId"]
                    current_plan_id = template["planId"]
                template["parentSpecimenNumber"] = self.parentSpecimenCount
                self._model.appendItem(template)

        self.modelInitialized.emit()

    @pyqtSlot(int, int, int)
    def add_model_item(self, pi_id, plan_id, count):
        """

        :return:
        """
        items = [x for x in self._model.items if x["piId"] == pi_id and x["planId"] == plan_id]

        for i in range(count):
            self.parentSpecimenCount += 1
            parent_specimen_number = -1

            for item in items:
                new_item = deepcopy(item)

                if parent_specimen_number == -1:
                    parent_specimen_number = new_item["parentSpecimenNumber"]

                if new_item["parentSpecimenNumber"] == parent_specimen_number:
                    new_item["parentSpecimenNumber"] = self.parentSpecimenCount
                    new_item["specimenId"] = None
                    new_item["parentSpecimenId"] = None
                    new_item["value"] = None
                    self.model.appendItem(new_item)
                else:
                    break

    @pyqtSlot(int, result=bool)
    def if_exist_otolith_id(self, otolith_id):
        specimen = Specimen.select().where(Specimen.numeric_value == otolith_id)
        if specimen.count() > 0:
            return True
        else:
            return False

    @pyqtSlot(int)
    def upsert_specimen(self, row_index):
        """
        Method to perform an insert or replace of a given specimen, if it exists
        :paremt row_index: int - index of the row being updated in tvSamples
        :param specimen_id:
        :return:
        """

        if not isinstance(row_index, int) or row_index == -1:
            return

        logging.info("upserting row: {0}".format(row_index))

        try:

            if isinstance(row_index, QVariant) or isinstance(row_index, QJSValue):
                row_index = row_index.toVariant()

            item = self._model.get(row_index)

            value = item["value"]
            value_type = self._get_value_type(value=value)
            special_action = item["specialAction"]
            specimen_id = item["specimenId"]

            logging.info('specimen_id: ' + str(specimen_id) +
                         ', row_index: ' + str(row_index) +
                         ', item: ' + str(item))

            if specimen_id is None:
                # Inserting a new record

                # logging.info('inserting a record')

                # Check if a parent record exists in a neighbor specimen, i.e. a specimen with the same parentSpecimenNumber
                parentSpecimenId = -1
                parentSpecimenNumber = item["parentSpecimenNumber"]
                sibling_specimens = [x for x in self._model.items if x["parentSpecimenNumber"] == parentSpecimenNumber]
                for sibling in sibling_specimens:
                    if sibling["parentSpecimenId"] is not None and sibling["parentSpecimenId"] != "":
                        parentSpecimenId = sibling["parentSpecimenId"]
                        break

                species_sampling_plan = item["planId"]
                if parentSpecimenId == -1:
                    logging.info('no parent found, inserting one...')
                    try:
                        q = Specimen.insert(catch=self._app.state_machine.species["catch_id"],
                                            species_sampling_plan=species_sampling_plan,
                                            cpu=self._app.host_cpu
                                            )
                        q.execute()
                        parentSpecimenId = Specimen.select().order_by(Specimen.specimen.desc()).get().specimen

                    except DoesNotExist as ex:
                        logging.error('error inserting the parent: ' + str(ex))

                # Use INSERT OR REPLACE statement, peewee upsert statement
                if value_type == "numeric":
                    q = Specimen.insert(parent_specimen=parentSpecimenId,
                                        catch=self._app.state_machine.species["catch_id"],
                                        species_sampling_plan = species_sampling_plan,
                                        action_type=item["specialActionId"],
                                        numeric_value=item["value"],
                                        cpu=self._app.host_cpu
                                        )

                elif value_type == "alpha":

                    q = Specimen.insert(parent_specimen = parentSpecimenId,
                                    catch = self._app.state_machine.species["catch_id"],
                                    species_sampling_plan = species_sampling_plan,
                                    action_type = item["specialActionId"],
                                    alpha_value = item["value"],
                                    cpu = self._app.host_cpu
                                    )
                q.execute()
                new_specimen_id = Specimen.select().order_by(Specimen.specimen.desc()).get().specimen

                # Update the model with the new parentSpecimenId and specimenId as appropriate from the database
                self._model.setProperty(index=row_index, property="parentSpecimenId", value=parentSpecimenId)
                self._model.setProperty(index=row_index, property="specimenId", value=new_specimen_id)

                new_item = self._model.get(row_index)
                logging.info('inserted a record, new model item: ' + str(new_item))
            else:
                # Doing an update to an existing specimen record
                if value_type == "numeric":
                    q = Specimen.update(numeric_value=value, alpha_value=None).where(Specimen.specimen == specimen_id)
                elif value_type == "alpha":
                    q = Specimen.update(alpha_value=value, numeric_value=None).where(Specimen.specimen == specimen_id)
                q.execute()

            # TODO Todd Hay - Move all of the sounds to the SerialPortManager.py > data_received method
            #    as we should play a sound once a serial port feed is received

            # Play the appropriate sound
            if item["specialAction"].lower() in ["is sex length sample", "is age weight sample"]:
                return

            if "coral specimen id" in item["specialAction"].lower():
                self._sound_player.play_sound(sound_name="takeBarcode")
            elif "sponge specimen id" in item["specialAction"].lower():
                self._sound_player.play_sound(sound_name="takeBarcode")
            elif "otolith age id" in item["specialAction"].lower():
                self._sound_player.play_sound(sound_name="takeBarcode")

            elif "tissue id" in item["specialAction"].lower() and \
                "sudmant" in item["principalInvestigator"].lower():
                self._sound_player.play_sound(sound_name="takeSudmantBarcode")

            elif "length" in item["specialAction"].lower():
                self._sound_player.play_sound(sound_name="takeLength")
            elif "width" in item["specialAction"].lower():
                self._sound_player.play_sound(sound_name="takeWidth")
            elif "weight" in item["specialAction"].lower():
                self._sound_player.play_sound(sound_name="takeWeight")

        except Exception as ex:
            logging.error("Error updating the special project information: {0}".format(ex))

    @pyqtSlot(int)
    def delete_specimen(self, specimen_id):
        """
        Method to perform an insert or replace of a given specimen, if it exists
        :param specimen_id:
        :return:
        """
        if not isinstance(specimen_id, int):
            return

        # This should be an individual instance of a specimen, i.e. not a whole fish
        try:
            logging.info('deleting a record, specimen_id: {0}'.format(specimen_id))

            # Delete from the database
            specimen = Specimen.select().where(Specimen.specimen == specimen_id).get()
            parent_specimen_id = specimen.parent_specimen.specimen

            specimen.delete_instance(recursive=True, delete_nullable=True)

            # Remove the specimenId from the model
            index = self._model.get_item_index(rolename="specimenId", value=specimen_id)
            if index != -1:
                self._model.setProperty(index=index, property="specimenId", value=None)
                parent_specimen_number = self._model.get(index)["parentSpecimenNumber"]

            # Delete the parent specimen if no children exist anymore
            count = Specimen.select().where(Specimen.parent_specimen == parent_specimen_id).count()
            if count == 0:
                specimen = Specimen.select().where(Specimen.specimen == parent_specimen_id).get()
                specimen.delete_instance(recursive=True, delete_nullable=True)

                # Empty the parentSpecimenNumber from the model
                if index != -1:
                    sibling_specimens = [x for x in self._model.items if
                                         x["parentSpecimenNumber"] == parent_specimen_number]
                    for sibling in sibling_specimens:
                        sibling["parentSpecimenId"] = None

        except DoesNotExist as ex:

            logging.info('Error deleting specimen: ' + str(ex))