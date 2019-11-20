__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        Specimens.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     April 15, 2016
# License:     MIT
#-------------------------------------------------------------------------------
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QVariant
import logging
import unittest
from py.trawl.TrawlBackdeckDB_model import Specimen, TypesLu, SpeciesSamplingPlanLu
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
from datetime import datetime


class Specimens:
    """
    Class for the Specimens.  This handles interactions (adding / updating / deleting) records from the SPECIMEN
    table.  As this table is used by four different screen for capturing specimen data, I thought it prudent to
    abstract the interactions with it out to a different class.  The four screens are:

    - FishSamplingScreen.qml
    - SpecialActionsScreen.qml
    - SalmonSamplingScreen.qml
    - CoralSamplingScreen.qml

    """
    parentSpecimenAdded = pyqtSignal()
    specimenAdded = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db

    @pyqtSlot(result=int)
    def add_parent_specimen(self):
        """
        Method that adds a new specimen the specimen table
        :return:
        """
        catch_id = self._app.state_machine.species["catch_id"]
        if isinstance(catch_id, int):
            specimen = Specimen.create(catch=catch_id)
            specimen.save()

            logging.info('primary key: ' + str(specimen.specimen))
            self._app.state_machine.specimen["specimenId"] = specimen.specimen

            self.parentSpecimenAdded.emit()
            return specimen.specimen

        return -1

    @pyqtSlot(float)
    def add_child_specimen(self, parent_specimen_id, action_type_id, action_value, plan_name="FRAM Standard Survey", measurement_type="Length"):
        """
        Generic method for adding a child specimen for the given parent specimen
        :param value:
        :return:
        """
        if not isinstance(parent_specimen_id, int) or not isinstance(action_type_id, int):
            return -1

        # Gather values from the state machine
        catch_id = self._app.state_machine.species["catch_id"]
        species_sampling_plan_id = SpeciesSamplingPlanLu.get(SpeciesSamplingPlanLu.taxonomy ==
                                                             self._app.state_machine.species["taxonomy_id"],
                                                             SpeciesSamplingPlanLu.plan_name == plan_name)

        # Add action_value
        measurement = TypesLu.get(TypesLu.category == "Measurement", TypesLu.type == measurement_type)
        if measurement:
            measurement_type_id = measurement.type_id
        else:
            logging.info('bogus measurement_type passed in: ' + str(measurement_type))
            return -1

        if isinstance(action_value, str):
            specimen = Specimen.create(parent_specimen=parent_specimen_id, action_type=action_type_id,
                                   measurement_type=measurement_type_id, alpha_value=action_value,
                                   catch=catch_id, species_sampling_plan=species_sampling_plan_id)
        elif isinstance(action_value, float) or isinstance(action_value, int):
            specimen = Specimen.create(parent_specimen=parent_specimen_id, action_type=action_type_id,
                                       measurement_type=measurement_type_id, numeric_value=action_value,
                                       catch=catch_id, species_sampling_plan=species_sampling_plan_id)

        specimen.save()
        return specimen.specimen
