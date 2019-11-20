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


class NetworkTesting(QObject):
    """
    Class for the NetworkTestingScreen
    """
    printerStatusReceived = pyqtSignal(str, bool, str, arguments=["comport", "success", "message"])

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

        self._sound_player = SoundPlayer()
        self._label_printer = LabelPrinter(app=self._app, db=self._db)
        self._label_printer.tagIdChanged.connect(self._updated_printer_tag_received)
        self._label_printer.printerStatusReceived.connect(self._printer_status_received)

    def _printer_status_received(self, comport, success, message):
        """
        Method to catch the message coming back from the printer
        :param comport:
        :param success:
        :param message:
        :return:
        """
        self.printerStatusReceived.emit(comport, success, message)

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

    @pyqtSlot(str)
    def printTestLabel(self, comport):
        """
        Method called from QML to print a label.  This passes a request to the self._label_printer object
        :return:
        """
        self._label_printer.print_test_job(comport=comport)

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
            if pi_action_code_id != 999:
                specimens = (Specimen.select(Specimen, TypesLu)
                         .join(SpeciesSamplingPlanLu,
                               on=(SpeciesSamplingPlanLu.species_sampling_plan==Specimen.species_sampling_plan).alias('plan'))
                         .join(PrincipalInvestigatorLu,
                               on=(SpeciesSamplingPlanLu.principal_investigator==PrincipalInvestigatorLu.principal_investigator).alias('pi'))
                         .join(TypesLu, on=(Specimen.action_type == TypesLu.type_id).alias('types'))
                         .where(TypesLu.type_id == action_type_id,
                                PrincipalInvestigatorLu.principal_investigator==pi_id,
                                fn.length(Specimen.alpha_value) == spec_num_length).order_by(Specimen.alpha_value.desc()))

            else:
                # where_clause = ((PrincipalInvestigatorLu.principal_investigator == pi_id) &
                #                ((fn.length(Specimen.alpha_value) == spec_num_length) |
                #                 (fn.length(Specimen.alpha_value) == spec_num_length+1)) &
                #                (Specimen.alpha_value.contains("-999-")))
                where_clause = (((fn.length(Specimen.alpha_value) == spec_num_length) |
                                 (fn.length(Specimen.alpha_value) == spec_num_length + 1)) &
                                (Specimen.alpha_value.contains("-999-")))
                specimens = (Specimen.select(Specimen)
                        .join(SpeciesSamplingPlanLu,
                              on=(SpeciesSamplingPlanLu.species_sampling_plan == Specimen.species_sampling_plan).alias('plan'))
                        .join(PrincipalInvestigatorLu,
                              on=(
                                  SpeciesSamplingPlanLu.principal_investigator == PrincipalInvestigatorLu.principal_investigator).alias(
                              'pi'))
                        .where(where_clause).order_by(Specimen.alpha_value.desc()))

                # logging.info('specimen count: ' + str(specimens.count()))

            # Get the newest specimen.  Note that one may not exist as it hasn't been created yet
            try:
                last_specimen_num = specimens.get().alpha_value
            except DoesNotExist as dne:
                last_specimen_num = None
            # logging.info('last specimen num: ' + str(last_specimen_num))

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

        except Exception as ex:
            logging.info('get_tag_id error: ' + str(ex))
            tag_id = "Error"

        # logging.info('tag_id: ' + str(tag_id))

        return tag_id

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
