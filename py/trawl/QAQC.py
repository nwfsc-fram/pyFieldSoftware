__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        QAQC.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 11, 2016
# License:     MIT
#-------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QVariant, QThread
from py.common.FramListModel import FramListModel
import logging
from py.common.SoundPlayer import SoundPlayer
from py.trawl.TrawlBackdeckDB_model \
    import Specimen, Catch, Hauls, TypesLu, Settings, ValidationsLu, CatchContentLu, LengthWeightRelationshipLu
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
from threading import Thread
import os
import shutil
from datetime import datetime
from copy import deepcopy
import sys
from functools import reduce
import subprocess
import textwrap
import math


class BackupFilesWorker(QObject):

    backupStatus = pyqtSignal(bool, str)

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):

        msg = "Backing up trawl_backdeck.db\n\n"
        success = False

        # Stop SerialPortManager from writing to DB while we back it up
        try:
            logging.info("Backup: Stopping SerialPortManager collection...")
            self._app.serial_port_manager.stop_all_threads()
            # self.backup_result_msgs.put('OK: Stopped SerialPortManager data collection.')
        except Exception as ex:
            msg = 'Could not stop SerialPortManager: ' + str(ex)
            logging.warning('Backup: {0}'.format(msg))
            # self.backup_result_msgs.put('WARNING: ' + warnmsg)

        # Copy trawl_backdeck.db to W:\PyCollector\data folder (i.e. Wheelhouse copy)
        try:

            # TODO Todd Hay - Modify to get the current working directory and then append \\data\\
            # src_folder = "C:\\Todd.Hay\\code\\pyqt5-framdata"
            # src_file = "data\\trawl_backdeck.db"
            # src = os.path.join(src_folder, src_file)
            # src = "C:\\trawl_backdeck\\data\\trawl_backdeck.db"

            src = "data\\trawl_backdeck.db"
            src = os.path.join(os.getcwd(), src)
            logging.info('src filename: {0}'.format(src))

            wheelhouse_drive_letter = Settings.get(Settings.parameter == "Wheelhouse Drive Letter").value
            database_exports_folder = Settings.get(Settings.parameter == "Database Exports Folder").value
            dst_folder = os.path.join(wheelhouse_drive_letter, database_exports_folder)
            dst = os.path.join(dst_folder, 'trawl_backdeck_' + datetime.today().strftime('%Y%m%d_%H%M%S') + '.db')
            logging.info('dst filename: {0}'.format(dst))

            if src is None:
                raise Exception('ERROR: Could not find trawl_backdeck.db database named')
            if not os.path.isdir(dst_folder) or not os.path.exists(dst_folder):
                os.makedirs(dst_folder)
                logging.info('created dst folder: {0}'.format(dst_folder))
                # raise Exception('ERROR: Could not find the {0} folder' + dst_folder)

        except Exception as ex:
            pass
            # msg += "Status: {0}\n\n".format("Success" if success else "Failed")
            # msg += "Error: {0}".format(ex)

        try:
            shutil.copyfile(src=src, dst=dst)

            success = True
            src_size = round(os.path.getsize(src) / 1024)
            dst_size = round(os.path.getsize(dst) / 1024)
            diff = round(dst_size - src_size)
            msg += "src: {0}\ndst: {1}\n\n".format(src, dst)
            msg += "File Sizes:  src: {0:,} KB,  dst: {1:,} KB\ndiff: {2} KB (diff should be 0)\n\n".format(src_size, dst_size, diff)
            msg += "Status: {0}".format("Success" if success else "Failed")

        except Exception as ex:
            msg += "src: {0}\ndst: {1}\n\n".format(src, dst)
            msg += "Status: {0}\n\n".format("Success" if success else "Failed")
            # wrapped_ex = textwrap.wrap("Error: {0}".format(ex), width=50)
            msg += "Error: {0}".format(ex)
            # msg += str(wrapped_ex)

        # Restart all ports in SerialPortManager
        try:
            self._app.serial_port_manager.start_all_threads()
        except Exception as ex:
            msg += "Unable to restart the SerialPortManager COM Ports"

        self._is_running = False
        self.backupStatus.emit(success, msg)

        # Open Windows Explorer and Highlight the newly copied trawl_backdeck.db file
        if success:
            subprocess.Popen('explorer /select, "{0}"'.format(dst))


class ValidationModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="name")
        self.add_role_name(name="description")
        self.add_role_name(name="type")
        self.add_role_name(name="errors")
        self.add_role_name(name="errorCount")
        self.add_role_name(name="comment")
        self.add_role_name(name="status")
        self.add_role_name(name="commentAdded")
        self.add_role_name(name="validationId")


class QAQC(QObject):
    """
    Class for the QAQCScreen.
    """
    validationModelChanged = pyqtSignal()
    backupStatusChanged = pyqtSignal(bool, str, arguments=["success", "msg"])

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

        self._backup_thread = QThread()
        self._backup_worker = None

        self._sound_player = SoundPlayer()

        self._validation_model = ValidationModel()
        self._initialize_validation_model()

        self._haul_level_validations = HaulLevelValidations(app=self._app, db=self._db)
        self._on_entry_validations = OnEntryValidations(app=self._app, db=self._db)

    def _initialize_validation_model(self):
        """
        Method to initialize the validation model
        :return:
        """
        self._validations = []
        validation_template = {"name": "", "description": "", "type": "",
                               "comments": "", "commentAdded": "", "status": "", "errors": "",
                               "errorCount": None, "object": "", "method": "",
                               "validationId": None}
        try:
            validations = ValidationsLu.select(ValidationsLu, TypesLu).join(TypesLu,
                                                                            on=(
                                                                            TypesLu.type_id == ValidationsLu.validation_type).alias(
                                                                                "types")) \
                .where(TypesLu.category == "Validation",
                       TypesLu.type == "Haul Level",
                       ValidationsLu.is_active == "True")
            for validation in validations:
                new_validation = deepcopy(validation_template)
                new_validation["name"] = validation.name
                new_validation["description"] = validation.description
                new_validation["type"] = validation.types.type
                new_validation["object"] = validation.object
                new_validation["method"] = validation.method
                new_validation["validationId"] = validation.validation

                self._validations.append(new_validation)

        except Exception as ex:
            logging.error("validations table query failed: " + str(ex))

        self._validation_model.setItems(self._validations)

    @pyqtProperty(QVariant)
    def haulLevelValidations(self):
        """
        Return the self._haul_level_validations
        :return:
        """
        return self._haul_level_validations

    @pyqtProperty(QVariant)
    def onEntryValidations(self):
        """
        Return the self._on_entry_validations
        :return:
        """
        return self._on_entry_validations

    def _backup_status_received(self, success, msg):
        """
        Method to catch the pyqtSignal from the BackupFilesWorker that indicates if the backup was successful
        or not and a message about the backup
        :param success: bool - True = successful backup / False = unsuccesful backup
        :param msg:
        :return:
        """
        self._backup_thread.quit()
        self.backupStatusChanged.emit(success, msg)

    @pyqtSlot()
    def backup_files(self):

        if self._backup_thread and self._backup_thread.isRunning():
            # Show a dialog popup saying hold on, we're still backing up the database
            success = False
            msg = "Backing up trawl_backdeck.db\n\n"
            msg += "Backup is still in progress, please be patient"
            self.backupStatusChanged.emit(success, msg)
        else:
            self._backup_worker = BackupFilesWorker(app=self._app)
            self._backup_worker.moveToThread(self._backup_thread)
            self._backup_worker.backupStatus.connect(self._backup_status_received)
            self._backup_thread.started.connect(self._backup_worker.run)
            self._backup_thread.start()

    @pyqtProperty(QVariant, notify=validationModelChanged)
    def ValidationModel(self):
        """
        return the ValidationModel
        :return:
        """
        return self._validation_model

    @pyqtSlot(result=bool)
    def fishSamplingSameSexCheck(self):
        """
        Method to check if fish sampling has at least 10 fish and they're all of the same sex
        :return:
        """
        model = self._app.fish_sampling.model
        sexes = [x["sex"] for x in model.items]
        if model.count >= 10 and sexes.count(sexes[0]) == len(sexes):
            self._sound_player.play_sound(sound_name="error")
            return False
        return True

    @pyqtSlot(result=bool)
    def fishSamplingRepetitiveLengthsCheck(self, index):
        """
        Method to check if fish sampling has 7 fish in a row with the same length values.  If so,
        might be due to the fishmeter board buffer overflowing
        :param: index - int - current length that was added
        :return: bool - success - whether the test is passed or not
        """
        model = self._app.fish_sampling.model
        if model.count >= 7 and index-6 > 0:
            lengths = [x["linealValue"] for x in model.items[index-6:index]]
            if lengths.count(lengths[0]) == len(lengths):
                self._sound_player.play_sound(sound_name="error")
                return False
        return True

    @pyqtSlot(QVariant, QVariant, result=bool)
    def fishSamplingLeaveAgeWeightTabCheck(self, weight, age):
        """
        Method to check when in fish sampling and the user attempts to leave the Age-Weight tab.  This checks
        to see if the weight or age value is blank.  If one of them is blank, it fails
        :param weight: QVariant - should be a float, but could be None or an empty string
        :param age: QVariant - should be an int, but could be None or an empty string
        :return:
        """

        # 2019 Patch - Tanner crab - do not do a age check - Taxonomy IDs: 1011, 1012, 1013, 1014
        tanner_crabs = [1011, 1012, 1013, 1014]
        # logging.info(f"taxonomy_id = {self._app.state_machine.species['taxonomy_id']}")
        if self._app.state_machine.species["taxonomy_id"] not in tanner_crabs:
            if weight is None or weight == "" or age is None or age == "":
                return False
        return True

    @pyqtSlot(result=QVariant)
    def runHaulLevelValidations(self):
        """
        Method called by the TrawlValidateDialog.qml to run Haul-level validations.  This method in turn
        calls a series of individual haul-level validations methods
        :return: dict - dictionary of the results of the validations
        """
        if self._app.state_machine.haul["haul_id"] is None or self._app.state_machine.haul["haul_id"] == "":
            return

        for validation in self._validations:

            try:

                object = getattr(self, validation["object"])
                method = getattr(object, validation["method"])
                result = method()

                for x in ["status", "errors", "errorCount"]:
                    if x in result:
                        validation[x] = result[x]

            except Exception as ex:
                logging.error('Haul Level Validation Error: {0}'.format(ex))

        return self._validations


class HaulLevelValidations:
    """
    HaulLevelValidations - This class handles all of the Haul-Level validations.  These are called from either the
    ProcessCatchScreen.qml screen or the HomeScreen.qml screen.
    """
    SORT_ORDER = {"Taxon": 0, "Mix": 1}
    MIX_SORT_ORDER = {"Taxon": 0, "Submix": 1}

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

    def missing_weighed_baskets_check(self):
        """
        Method that checks if there are any species that do not have at least one weighed basket
        :return:
        """
        result = {"status": "Passed", "errors": "Success", "errorCount": 0}
        errors = []

        try:
            catch = Catch.select().where(Catch.operation == self._app.state_machine.haul["haul_id"],
                                             Catch.parent_catch.is_null(True))
            for species in catch:
                child_baskets = Catch.select().where(Catch.parent_catch == species.catch)
                if child_baskets.count() == 0:
                    errors.append(species.display_name)

                # Mixes
                if "mix" in species.display_name.lower():
                    for mix_species in child_baskets:
                        mix_child_baskets = Catch.select().where(Catch.parent_catch == mix_species.catch)
                        if "mix #" not in mix_species.display_name.lower() and mix_child_baskets.count() == 0:
                            errors.append(species.display_name + " > " + mix_species.display_name)

                        # Submixes
                        if "submix" in mix_species.display_name.lower():
                            submix_catch = Catch.select(Catch, CatchContentLu, TypesLu) \
                                .join(CatchContentLu,
                                      on=(CatchContentLu.catch_content == Catch.catch_content).alias("content")) \
                                .join(TypesLu, on=(CatchContentLu.content_type == TypesLu.type_id).alias("types")) \
                                .where(Catch.parent_catch == mix_species.catch, \
                                       TypesLu.category == "Content", \
                                       TypesLu.type == "Taxon")
                            for submix_species in submix_catch:
                                submix_child_baskets = Catch.select().where(Catch.parent_catch == submix_species.catch)
                                if submix_child_baskets.count() == 0:
                                    errors.append(species.display_name + " > " + mix_species.display_name + " > " +
                                                                       submix_species.display_name)

        except Exception as ex:
            logging.info("error in query: " + str(ex))

        if len(errors) > 0:
            result["status"] = "Failed"
            result["errorCount"] = len(errors)
            errors = "\n".join(sorted(errors))
            result["errors"] = errors

        return result

    def single_basket_subsample_check(self):
        """
        Method that checks to see if there is only one weighed basket for a species whether
        it is listed as a subsample or not.  It should not be listed as a subsample
        :return:
        """
        result = {"status": "Passed", "errors": "Success", "errorCount": 0}
        errors = []

        try:
            catch = Catch.select().where(Catch.operation == self._app.state_machine.haul["haul_id"],
                                         Catch.parent_catch.is_null(True))
            for species in catch:
                child_baskets = Catch.select().where(Catch.parent_catch == species.catch)
                if child_baskets.count() == 1:
                    child_basket = child_baskets.get()
                    # if child_basket.is_subsample is None or child_basket.is_subsample == "False":
                    if child_basket.is_subsample == "True":
                        errors.append(species.display_name)

                # Mixes
                if "mix" in species.display_name.lower():
                    for mix_species in child_baskets:
                        mix_child_baskets = Catch.select().where(Catch.parent_catch == mix_species.catch)
                        if "mix #" not in mix_species.display_name.lower():
                            if mix_child_baskets.count() == 1:
                                mix_child_basket = mix_child_baskets.get()
                                # if mix_child_basket.is_subsample is None or mix_child_basket.is_subsample == "False":
                                if mix_child_basket.is_subsample == "True":
                                    errors.append(species.display_name + " > " + mix_species.display_name)

                        # Submixes
                        if "submix" in mix_species.display_name.lower():
                            submix_catch = Catch.select(Catch, CatchContentLu, TypesLu) \
                                .join(CatchContentLu,
                                      on=(CatchContentLu.catch_content == Catch.catch_content).alias("content")) \
                                .join(TypesLu, on=(CatchContentLu.content_type == TypesLu.type_id).alias("types")) \
                                .where(Catch.parent_catch == mix_species.catch, \
                                       TypesLu.category == "Content", \
                                       TypesLu.type == "Taxon")
                            for submix_species in submix_catch:
                                submix_child_baskets = Catch.select().where(Catch.parent_catch == submix_species.catch)
                                if submix_child_baskets.count() == 1:
                                    submix_child_basket = submix_child_baskets.get()
                                    # if submix_child_basket.is_submsample is None or \
                                    #                 submix_child_basket.is_subsample == "False":
                                    if submix_child_basket.is_subsample == "True":
                                            errors.append(species.display_name + " > " +
                                                          mix_species.display_name + " > " +
                                                  submix_species.display_name)

        except Exception as ex:
            logging.info("error in query: " + str(ex))

        if len(errors) > 0:
            result["status"] = "Failed"
            result["errorCount"] = len(errors)
            errors = "\n".join(sorted(errors))
            result["errors"] = errors

        return result

    def aggregate_specimen_weight_check(self):
        """
        Method that sums the weights of the individual specimens for a given species and makes sure that matches the
        sum of the baskets marked as subsamples
        :return:
        """
        result = {"status": "Passed", "errors": "Success", "errorCount": 0}
        errors = []

        try:

            sexes = ["M", "F", "U"]
            tolerance = float(Settings.get(Settings.parameter == "Aggregate Specimen Weight Tolerance").value)

            catch = Catch.select(Catch, CatchContentLu) \
                .join(CatchContentLu, JOIN.LEFT_OUTER, on=(CatchContentLu.display_name == Catch.display_name).alias('cc')) \
                .where(Catch.operation == self._app.state_machine.haul["haul_id"],
                                         Catch.parent_catch.is_null(True))

            specimen_sql = """
                SELECT PARENT_SPECIMEN_ID
                    , MAX(CASE WHEN TYPE = 'Sex' THEN VALUE END) AS sex
                    , MAX(CASE WHEN TYPE = 'Length' THEN VALUE END) AS length
                    , MAX(CASE WHEN TYPE = 'Weight' THEN VALUE END) AS weight
                    FROM (
                        WITH RECURSIVE actions(id) AS (
                            SELECT SPECIMEN_ID FROM SPECIMEN WHERE CATCH_ID = ?
                            UNION	
                            SELECT s.SPECIMEN_ID FROM SPECIMEN s, actions WHERE s.PARENT_SPECIMEN_ID = actions.id
                        )
                        SELECT s.PARENT_SPECIMEN_ID, t.TYPE,
                            CASE 
                                WHEN ALPHA_VALUE IS NOT NULL THEN ALPHA_VALUE
                                WHEN NUMERIC_VALUE IS NOT NULL THEN NUMERIC_VALUE
                                END AS VALUE
                         FROM SPECIMEN s INNER JOIN TYPES_LU t ON s.ACTION_TYPE_ID = t.TYPE_ID 
                            WHERE s.PARENT_SPECIMEN_ID in actions

                    ) GROUP BY PARENT_SPECIMEN_ID ORDER BY sex
            """

            for species in catch:

                explicit_weight = 0
                non_explicit_weight = 0

                agg_basket_weight = Catch.select(fn.SUM(Catch.weight_kg)).where(Catch.parent_catch == species.catch,
                                                                                Catch.is_subsample == "True").scalar()

                logging.info(f"species: {species.display_name}, agg wt: {agg_basket_weight}")

                # If no basket weights, then add an error for this species and continue
                if agg_basket_weight is None or agg_basket_weight == 0:
                    continue

                if "mix" not in species.display_name.lower():
                    params = [species.catch, ]
                    specimens = self._db.execute(query=specimen_sql, parameters=params)
                    if specimens:
                        keys = ["specimen_id", "sex", "length", "weight"]
                        specimens = [dict(zip(keys, values)) for values in specimens]

                        params = dict()
                        for sex in sexes:
                            param = LengthWeightRelationshipLu.select().where(
                            LengthWeightRelationshipLu.taxonomy == species.cc.taxonomy,
                            LengthWeightRelationshipLu.sex_code == sex)

                            params[sex] = None
                            if param.count() == 1:
                                params[sex] = param.first()

                    for specimen in specimens:
                        if specimen["weight"]:
                            explicit_weight += specimen["weight"]

                        elif specimen["sex"] and specimen["length"] and params[specimen["sex"]]:
                            current_param = params[specimen["sex"]]
                            exp_weight = math.exp(math.log(specimen["length"]) * float(current_param.lw_exponent_cmkg) +
                                float(current_param.lw_coefficient_cmkg))
                            non_explicit_weight += exp_weight

                    total_specimen_weight = explicit_weight + non_explicit_weight

                    agg_basket_weight_lower_bound = agg_basket_weight * (1 - tolerance)
                    agg_basket_weight_upper_bound = agg_basket_weight * (1 + tolerance)

                    if total_specimen_weight < agg_basket_weight_lower_bound or \
                        total_specimen_weight > agg_basket_weight_upper_bound:
                        errors.append(species.display_name)

        except Exception as ex:
            logging.info("error in query: " + str(ex))

        if len(errors) > 0:
            result["status"] = "Failed"
            result["errorCount"] = len(errors)
            errors = "\n".join(sorted(errors))
            result["errors"] = errors
        return result

    def mix_aggregate_weight_check(self):
        """
        Method that checks that the mix weight is equal to the weight of the individual mix species + submix weights + tolerance
        :return:
        """

        result = {"status": "Passed", "errors": "Success", "errorCount": 0}
        errors = []

        try:
            tolerance = float(Settings.get(Settings.parameter == "Mix Aggregate Weight Tolerance").value)
            catch = Catch.select().where(Catch.operation == self._app.state_machine.haul["haul_id"],
                                         Catch.parent_catch.is_null(True))
            for species in catch:

                # Mixes
                if "mix" in species.display_name.lower():

                    # Get mix weight + set children agg to 0
                    mix_basket_weight = Catch.select(fn.TOTAL(Catch.weight_kg)) \
                        .where(Catch.parent_catch == species.catch,
                               Catch.display_name == species.display_name).scalar()
                    mix_children_agg_weight = 0

                    # Get all of the mix children
                    mix_child_baskets = Catch.select().where(Catch.parent_catch == species.catch)
                    for mix_species in mix_child_baskets:

                        mix_children_agg_weight += Catch.select(fn.TOTAL(Catch.weight_kg)) \
                                                        .where(Catch.parent_catch == mix_species.catch).scalar()
                        # logging.info('species: {0}, mix_children_agg_weight: {1}'.format(mix_species.display_name, mix_children_agg_weight))


                        # Submixes
                        if "submix" in mix_species.display_name.lower():

                            # Get submix weight + set submix children agg to 0
                            submix_basket_weight = Catch.select(fn.TOTAL(Catch.weight_kg)) \
                                .where(Catch.parent_catch == mix_species.catch,
                                       Catch.display_name == mix_species.display_name).scalar()
                            submix_child_agg_weight = 0

                            submix_child_taxon_baskets = Catch.select() \
                                .where(Catch.parent_catch == mix_species.catch,
                                       Catch.display_name != species.display_name)
                            for submix_species in submix_child_taxon_baskets:

                                submix_child_agg_weight += Catch.select(fn.TOTAL(Catch.weight_kg)) \
                                    .where(Catch.parent_catch == submix_species.catch).scalar()

                            # logging.info('submix_basket_weight: {0}, submix_child_agg_weight: {1}'.format(submix_basket_weight,
                            #                                                                           submix_child_agg_weight))

                            if submix_basket_weight is not None and submix_child_agg_weight is not None:
                                upper_bound = submix_basket_weight * (1 + tolerance)
                                lower_bound = submix_basket_weight * (1 - tolerance)
                                if submix_child_agg_weight > upper_bound or submix_child_agg_weight < lower_bound:
                                    errors.append(species.display_name + " > " + mix_species.display_name)

                    # logging.info('mix weight: {0}, children agg weight: {1}'.format(mix_basket_weight, mix_children_agg_weight))

                    if mix_basket_weight is not None and mix_children_agg_weight is not None:
                        upper_bound = mix_basket_weight * (1 + tolerance)
                        lower_bound = mix_basket_weight * (1 - tolerance)
                        if mix_children_agg_weight > upper_bound or mix_children_agg_weight < lower_bound:
                            errors.append(mix_species.display_name)


        except Exception as ex:
            logging.info("error in query: " + str(ex))

        if len(errors) > 0:
            result["status"] = "Failed"
            result["errorCount"] = len(errors)
            # errors = sorted(errors, key=lambda x:
            #         (SORT_ORDER[x.data(typeCol).value()], x.data(displayNameCol).value().lower()))

            errors = "\n".join(sorted(errors))
            result["errors"] = errors

        return result

    def mix_nonsubsample_basket_check(self):
        """
        Method that ensures that every mix (including each of both tiers, if nested) has at least one non-sample basket weight
        :return:
        """
        result = {"status": "Passed", "errors": "Success", "errorCount": 0}
        errors = []

        try:
            catch = Catch.select().where(Catch.operation == self._app.state_machine.haul["haul_id"],
                                         Catch.parent_catch.is_null(True))
            for species in catch:

                # Mixes
                if "mix" in species.display_name.lower():

                    # Get mix number of subsampled baskets
                    mix_subsample_count = Catch.select() \
                        .where(Catch.parent_catch == species.catch,
                               Catch.display_name == species.display_name,
                               Catch.is_subsample == "True").count()
                    if mix_subsample_count == 0:
                        errors.append(species.display_name)

                    # Get all of the mix children
                    mix_child_baskets = Catch.select().where(Catch.parent_catch == species.catch)
                    for mix_species in mix_child_baskets:

                        # Submixes
                        if "submix" in mix_species.display_name.lower():

                            # Get submix number of subsampled baskets
                            mix_subsample_count = Catch.select() \
                                .where(Catch.parent_catch == mix_species.catch,
                                       Catch.display_name == mix_species.display_name,
                                       Catch.is_subsample == "True").count()
                            if mix_subsample_count == 0:
                                errors.append(mix_species.display_name)

        except Exception as ex:
            logging.info("error in query: " + str(ex))

        if len(errors) > 0:
            result["status"] = "Failed"
            result["errorCount"] = len(errors)
            # errors = sorted(errors, key=lambda x:
            #         (SORT_ORDER[x.data(typeCol).value()], x.data(displayNameCol).value().lower()))
            result["errors"] = "\n".join(sorted(errors))

        return result

    def all_subsample_basket_check(self):
        """
        Check for a species if all baskets are counted or none are counted, none should be marked as a subsample
        :return:
        """
        result = {"status": "Passed", "errors": "Success", "errorCount": 0}
        errors = []

        try:
            catch = Catch.select().where(Catch.operation == self._app.state_machine.haul["haul_id"],
                                         Catch.parent_catch.is_null(True))
            for species in catch:

                species_baskets = Catch.select().where(Catch.parent_catch == species.catch)
                num_baskets = species_baskets.count()
                num_baskets_counted = species_baskets.where(Catch.sample_count_int.is_null(False) &
                                                            Catch.sample_count_int != 0).count()
                num_baskets_subsampled = species_baskets.where(Catch.is_subsample == "True").count()

                # logging.info('species: {3}, num_baskets: {0}, count: {1}, subsampled: {2}'.format(num_baskets, num_baskets_counted,
                #                                                                     num_baskets_subsampled,
                #                                                                                   species.display_name))

                if num_baskets_subsampled == num_baskets:
                    errors.append(species.display_name)

                # Mixes
                if "mix" in species.display_name.lower():

                    mix_children = Catch.select() \
                        .where(Catch.parent_catch == species.catch, Catch.display_name != species.display_name)
                    for mix_species in mix_children:

                        mix_species_baskets = Catch.select().where(Catch.parent_catch == mix_species.catch)
                        num_baskets = mix_species_baskets.count()
                        num_baskets_counted = mix_species_baskets.where(Catch.sample_count_int.is_null(False) &
                                                                        Catch.sample_count_int != 0).count()
                        num_baskets_subsampled = mix_species_baskets.where(Catch.is_subsample == "True").count()

                        if num_baskets_subsampled == num_baskets:
                            errors.append(species.display_name + " > " + mix_species.display_name)

                        # Submixes
                        if "submix" in mix_species.display_name.lower():

                            submix_children = Catch.select() \
                                .where(Catch.parent_catch == mix_species.catch, Catch.display_name != mix_species.display_name)
                            for submix_species in submix_children:

                                submix_species_baskets = Catch.select().where(Catch.parent_catch == submix_species.catch)
                                num_baskets = submix_species_baskets.count()
                                num_baskets_counted = submix_species_baskets.where(
                                    Catch.sample_count_int.is_null(False) &
                                    Catch.sample_count_int != 0).count()
                                num_baskets_subsampled = submix_species_baskets.where(Catch.is_subsample == "True").count()

                                if num_baskets_subsampled == num_baskets:
                                    errors.append(species.display_name + " > " + mix_species.display_name + " > " +
                                                  submix_species.display_name)

        except Exception as ex:
            logging.info("error in query: " + str(ex))

        if len(errors) > 0:
            result["status"] = "Failed"
            result["errorCount"] = len(errors)
            # errors = sorted(errors, key=lambda x:
            #         (SORT_ORDER[x.data(typeCol).value()], x.data(displayNameCol).value().lower()))

            errors = "\n".join(sorted(errors))
            result["errors"] = errors

        return result

    def counts_or_protocol_check(self):
        """
        Method that ensures that for a given species that it either has counts in Weigh Baskets or specimens in Fish Sampling
        :return:
        """

        result = {"status": "Passed", "errors": "Success", "errorCount": 0}
        errors = []

        try:
            catch = Catch.select().where(Catch.operation == self._app.state_machine.haul["haul_id"],
                                         Catch.parent_catch.is_null(True))
            for species in catch:

                if "mix #" in species.display_name.lower() or "submix #" in species.display_name.lower():
                    continue

                species_baskets = Catch.select().where(Catch.parent_catch == species.catch)
                num_baskets = species_baskets.count()
                num_baskets_counted = species_baskets.where(Catch.sample_count_int.is_null(False) &
                                                            Catch.sample_count_int != 0).count()

                # logging.info(f"num_baskets_counted: {num_baskets_counted}")

                if num_baskets_counted > 0:
                    continue

                specimens = Specimen.select().where(Specimen.catch == species.catch)
                num_specimens = specimens.count()

                # logging.info(f"num_specimens: {num_specimens}")

                if num_specimens > 0:
                    continue

                errors.append(species.display_name)

        except Exception as ex:
            logging.error(f"error in query: {ex}")

        if len(errors) > 0:
            result["status"] = "Failed"
            result["errorCount"] = len(errors)
            errors = "\n".join(sorted(errors))
            result["errors"] = errors

        return result

    def counts_as_subsamples_basket_check(self):
        """
        Check for a species if there is at least one counted and one non-counted basket, that all
        of the counted baskets are marked as subsamples
        :return:
        """
        result = {"status": "Passed", "errors": "Success", "errorCount": 0}

        return result


class OnEntryValidations:
    """
    HaulLevelValidations - This class handles all of the Haul-Level validations.  These are called from either the
    ProcessCatchScreen.qml screen or the HomeScreen.qml screen.
    """
    onEntryValidationProcessed = pyqtSignal(str, str, QVariant, bool, str,
                                            arguments=["add_or_update", "property", "value", "success", "message"])

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

    def maximum_weight_check(self):
        """
        Method to check that the weight entered is not greater than the maximum allowable weight (current set to 60kg)
        :return:
        """
        result = {}
        result["status"] = ""
        result["errors"] = ""
        result["errorCount"] = None
        return result
