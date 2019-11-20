__author__ = 'Todd.Hay'

# -------------------------------------------------------------------------------
# Name:        FileManagement.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     November 14, 2016
# License:     MIT
#-------------------------------------------------------------------------------
import logging
import unittest
import os
import re
import shutil
from datetime import datetime
import arrow
from collections import OrderedDict
from py.trawl_analyzer.CommonFunctions import CommonFunctions

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QVariant, Qt, QThread, QMetaType
from PyQt5.QtQml import QJSValue

from py.common.FramListModel import FramListModel
from py.trawl_analyzer.TrawlAnalyzerDB_model import Lookups, Operations, OperationFiles, OperationFilesMtx, \
    VesselLu, PersonnelLu, StationInventoryLu, OperationsFlattenedVw, MeasurementStreams, OperationMeasurements

from py.trawl_analyzer.TrawlWheelhouseDB_model import OperationalSegment as WhOperationalSegment, TowWaypoints, \
    TypesLu as WhTypes, Project as WhProjects, PersonnelLu as WhPersonnel
from py.trawl_analyzer.TrawlSensorsDB_model import EnviroNetRawFiles, EnviroNetRawStrings
from py.trawl_analyzer.TrawlBackdeckDB_model import Hauls, Catch, Specimen
from peewee import fn
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict


class BreakIt(Exception): pass


class WheelhouseModel(FramListModel):

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="srcFileName")
        self.add_role_name(name="dstFileName")
        self.add_role_name(name="copyStatus")

        self._functions = CommonFunctions()

    def populate_model(self):

        """
        Method to initialize the model upon starting the application
        :param year: str
        :param vessel: str
        :return:
        """
        self.clear()

        logging.info(f"start populating the Wheelhouse model, first interaction with LOOKUPS is next")

        file_type_lu_id = Lookups.get(Lookups.type=="Operation File",
                                      Lookups.value == "Wheelhouse Database").lookup
        cruise_id = self._functions.get_cruise_id(year=self._app.settings.year, vessel=self._app.settings.vessel)
        items = OperationFiles.select(OperationFiles)\
            .join(OperationFilesMtx).where(OperationFilesMtx.operation == cruise_id,
                                           OperationFiles.operation_file_type_lu == file_type_lu_id)

        logging.info(f"Wheelhouse model items count: {items.count()}")

        for item in items:
            item_dict = dict()
            item_dict["srcFileName"] = None
            item_dict["dstFileName"] = item.final_path_name
            item_dict["copyStatus"] = None
            if os.path.exists(item.final_path_name):
                item_dict["copyStatus"] = "Yes"
            self.appendItem(item_dict)

    @pyqtSlot(result=int)
    def check_haul_count(self):
        """
        Method to determine how many hauls, if any, have actually been loaded for this cruise
        :return:
        """
        cruise_id = self._functions.get_cruise_id(self._app.settings.year, self._app.settings.vessel)
        count = OperationsFlattenedVw.select().where(
            OperationsFlattenedVw.cruise == cruise_id,
            OperationsFlattenedVw.operation_type == "Tow"
        ).count()
        return count

    @pyqtSlot(QVariant)
    def add_item(self, item):
        """
        Method to add a new item to the model
        :param item:
        :return:
        """
        if isinstance(item, QJSValue):
            item = item.toVariant()

        if "srcFileName" in item:
            item["srcFileName"] = os.path.realpath(item["srcFileName"].strip("file:///"))
            item["dstFileName"] = None
            item["copyStatus"] = None
            if not self.is_item_in_model(rolename="srcFileName", value=item["srcFileName"]):
                self.appendItem(item=item)

    @pyqtSlot(int)
    def remove_item(self, idx):
        """
        Method to remove an item from the model, but also to remove it from the database.  The item is only removed if
        the hauls for the cruise/leg associated with this database have not already been loaded.  To check this,
        I query the operations_flattened_vw looking for any haul children of the current cruise
        :param item:
        :return:
        """
        item = self.items[idx]
        if "dstFileName" not in item:
            self.removeItem(index=idx)
            return
        if item["dstFileName"] == "" or item["dstFileName"] is None:
            self.removeItem(index=idx)
            return

        cruise_id = self._functions.get_cruise_id(self._app.settings.year, self._app.settings.vessel)
        logging.info('cruise_id: {0}'.format(cruise_id))

        count = OperationsFlattenedVw.select().where(
            OperationsFlattenedVw.cruise == cruise_id,
            OperationsFlattenedVw.operation_type == "Tow"
        ).count()
        if count == 0:
            # Go ahead and remove the item from the model and the database as no hauls have been loaded
            item = self.items[idx]

            # Delete the database records
            try:
                op_file = OperationFiles.get(OperationFiles.final_path_name == item["dstFileName"]).operation_file
                OperationFilesMtx.delete().where(OperationFilesMtx.operation == cruise_id,
                                                 OperationFilesMtx.operation_file == op_file).execute()
                OperationFiles.delete().where(OperationFiles.operation_file == op_file).execute()

                # Delete Leg children operations first
                Operations.delete().where(Operations.parent_operation == cruise_id).execute()

                # Delete Cruise operation
                Operations.delete().where(Operations.operation == cruise_id).execute()
            except Exception as ex:
                logging.info('Wheelhouse database, error deleting database records: {0}'.format(ex))

            # Delete the copied SQLite database file
            try:
                self._app.settings.set_wheelhouse_proxy(None)
                os.remove(item["dstFileName"])

                # Delete the model item
                self.removeItem(index=idx)

                logging.info(f"Wheelhouse database deleted: {item['dstFileName']}")

            except Exception as ex:
                logging.info(f"Wheelhouse Database, unable to delete file: {item['dstFileName']} > {ex}")


            # Repopulate the Data Completeness Table as well
            # self._app.data_completeness._data_check_model.clear()
            self._app.data_completeness.dataCheckModel.populate_model()


class SensorsModel(FramListModel):

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="srcFileName")
        self.add_role_name(name="dstFileName")
        self.add_role_name(name="fileSize")
        self.add_role_name(name="copyStatus")

        self._functions = CommonFunctions()

        # self.temp_items = []

    def populate_model(self):
        """
        Method to initialize the model upon starting the application
        :param year: str
        :param vessel: str
        :return:
        """
        self.clear()

        file_type_lu_id = Lookups.get(Lookups.type=="Operation File",
                                      Lookups.value == "Sensor Database").lookup
        cruise_id = self._functions.get_cruise_id(year=self._app.settings.year, vessel=self._app.settings.vessel)

        items = OperationFiles.select(OperationFiles)\
            .join(OperationFilesMtx).where(OperationFilesMtx.operation == cruise_id,
                                           OperationFiles.operation_file_type_lu == file_type_lu_id)

        for item in items:
            item_dict = dict()
            item_dict["srcFileName"] = None
            item_dict["dstFileName"] = item.final_path_name
            item_dict["copyStatus"] = None
            if os.path.exists(item.final_path_name):
                item_dict["fileSize"] = os.path.getsize(item.final_path_name) / (1024.0 * 1024.0)
                item_dict["copyStatus"] = "Yes"
            self.appendItem(item_dict)

    @pyqtSlot(QVariant)
    def add_item(self, item):
        """
        Method to add a new item to the model
        :param item:
        :return:
        """
        if isinstance(item, QJSValue):
            item = item.toVariant()

        if "srcFileName" in item:
            item["srcFileName"] = os.path.realpath(item["srcFileName"].strip("file:///"))
            item["dstFileName"] = None
            item["copyStatus"] = None
            item["fileSize"] = os.path.getsize(item["srcFileName"]) / (1024.0 * 1024.0)
            if not self.is_item_in_model(rolename="srcFileName", value=item["srcFileName"]):
                self.appendItem(item=item)

    @pyqtSlot(int, result=int)
    def check_operation_measurements_count(self, idx):
        """
        Method to determine how many operation_measurements, if any, have been loaded for this cruise
        :return:
        """
        item = self.items[idx]
        if "dstFileName" not in item:
            return 0

        if item["dstFileName"] == "" or item["dstFileName"] is None:
            return 0

        try:
            cruise_id = self._functions.get_cruise_id(self._app.settings.year, self._app.settings.vessel)
            count = MeasurementStreams.select(MeasurementStreams)\
                .join(OperationFilesMtx, on=(OperationFilesMtx.operation_files_mtx == MeasurementStreams.operation_files_mtx).alias('mtx'))\
                .join(OperationFiles, on=(OperationFiles.operation_file == OperationFilesMtx.operation_file).alias('files'))\
                .where(OperationFilesMtx.operation == cruise_id,
                       OperationFiles.final_path_name == item["dstFileName"]).count()

            return count

        except Exception as ex:
            logging.error(f"Error checking to determine if any measurement streams exist for this sensor db: {item['dstFileName']} > {ex}")
            return 1

    @pyqtSlot(int)
    def remove_item(self, idx):
        """
        Method to delete an item from the sensors model
        :param idx: int - the Index of the item to delete
        :return:
        """
        item = self.items[idx]
        if "dstFileName" not in item:
            self.removeItem(index=idx)
            return
        if item["dstFileName"] == "" or item["dstFileName"] is None:
            self.removeItem(index=idx)
            return

        cruise_id = self._functions.get_cruise_id(self._app.settings.year, self._app.settings.vessel)

        # Delete the database records
        try:
            # Delete all of the Operation Measurements and Measurement Streams
            streams = MeasurementStreams.select(MeasurementStreams.measurement_stream) \
                .join(OperationFilesMtx,
                      on=(OperationFilesMtx.operation_files_mtx == MeasurementStreams.operation_files_mtx)) \
                .join(OperationFiles,
                      on=(OperationFiles.operation_file == OperationFilesMtx.operation_file)) \
                .where(OperationFilesMtx.operation == cruise_id,
                       OperationFiles.final_path_name == item["dstFileName"])

            # If there is at least one stream, then need to delete all of the operation_measurements + measurement_streams
            if streams.count() > 0:
                logging.info(f'file to delete: {item["dstFileName"]}')
                file = OperationFiles.get(OperationFiles.final_path_name==item["dstFileName"])
                haul_ops = OperationsFlattenedVw.select(OperationsFlattenedVw.operation) \
                    .join(OperationFilesMtx, on=(OperationFilesMtx.operation == OperationsFlattenedVw.cruise)) \
                    .where(OperationFilesMtx.operation == cruise_id,
                           OperationFilesMtx.operation_file == file.operation_file,
                           OperationsFlattenedVw.operation_type == "Tow",
                           OperationsFlattenedVw.sensor_load_date.is_null(False))
                logging.info(f'number of hauls whose sensor data was just deleted: {haul_ops.count()}')
                Operations.update(sensor_load_date=None).where(Operations.operation << haul_ops).execute()

            OperationMeasurements.delete().where(OperationMeasurements.measurement_stream << streams).execute()
            MeasurementStreams.delete().where(MeasurementStreams.measurement_stream << streams).execute()
            logging.info('measurement_streams and operation_measurements records deleted')

            # Delete all of the Operation Files Matrix and Operation Files
            op_file = OperationFiles.get(OperationFiles.final_path_name == item["dstFileName"]).operation_file
            OperationFilesMtx.delete().where(OperationFilesMtx.operation == cruise_id,
                                             OperationFilesMtx.operation_file == op_file).execute()
            OperationFiles.delete().where(OperationFiles.operation_file == op_file).execute()
            logging.info('operation files and operation_mtx_files records deleted')

            # Clear the proxy
            self._app.settings.set_sensors_proxy(None)

            # Delete the copied SQLite database file
            os.remove(item["dstFileName"])

            # Delete the model item
            self.removeItem(index=idx)
            logging.info(f"Sensor database deleted: {item['dstFileName']}")

        except Exception as ex:
            logging.info(f"Sensor Database, unable to delete file: {item['dstFileName']} > {ex}")

        # Clear the Data Completeness model fields dealing with the sensors data
        self._app.data_completeness.dataCheckModel.populate_model()


class BackdeckModel(FramListModel):

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="srcFileName")
        self.add_role_name(name="dstFileName")
        self.add_role_name(name="copyStatus")

        self._functions = CommonFunctions()

    def populate_model(self):
        """
        Method to initialize the model upon starting the application
        :param year: str
        :param vessel: str
        :return:
        """
        self.clear()

        file_type_lu_id = Lookups.get(Lookups.type=="Operation File",
                                      Lookups.value == "Backdeck Meta-Database")
        cruise_id = self._functions.get_cruise_id(year=self._app.settings.year, vessel=self._app.settings.vessel)
        items = OperationFiles.select(OperationFiles)\
            .join(OperationFilesMtx).where(OperationFilesMtx.operation == cruise_id,
                                           OperationFiles.operation_file_type_lu == file_type_lu_id)

        for item in items:
            item_dict = dict()
            item_dict["srcFileName"] = None
            item_dict["dstFileName"] = item.final_path_name
            item_dict["copyStatus"] = None
            if os.path.exists(item.final_path_name):
                item_dict["copyStatus"] = "Yes"
            self.appendItem(item_dict)

    @pyqtSlot(QVariant)
    def add_item(self, item):
        """
        Method to add a new item to the model
        :param item:
        :return:
        """
        if isinstance(item, QJSValue):
            item = item.toVariant()

        if "srcFileName" in item:
            item["srcFileName"] = os.path.realpath(item["srcFileName"].strip("file:///"))
            item["dstFileName"] = None
            item["copyStatus"] = None
            if not self.is_item_in_model(rolename="srcFileName", value=item["srcFileName"]):
                self.appendItem(item=item)

    @pyqtSlot(int)
    def remove_item(self, idx):
        """
        Method to delete an item from the backdeck model
        :param idx: int - the Index of the item to delete
        :return:
        """
        item = self.items[idx]
        if "dstFileName" not in item:
            self.removeItem(index=idx)
            return
        if item["dstFileName"] == "" or item["dstFileName"] is None:
            self.removeItem(index=idx)
            return

        cruise_id = self._functions.get_cruise_id(self._app.settings.year, self._app.settings.vessel)

        # Delete the database records
        try:
            op_file = OperationFiles.get(OperationFiles.final_path_name == item["dstFileName"]).operation_file
            OperationFilesMtx.delete().where(OperationFilesMtx.operation == cruise_id,
                                             OperationFilesMtx.operation_file == op_file).execute()
            OperationFiles.delete().where(OperationFiles.operation_file == op_file).execute()
        except Exception as ex:
            logging.info('Backdeck database, unable to delete database record: {0}'.format(ex))

        # Delete the copied SQLite database file
        try:
            self._app.settings.set_backdeck_proxy(None)

            os.remove(item["dstFileName"])

            # Delete the model item
            self.removeItem(index=idx)
            logging.info(f"Backdeck database deleted: {item['dstFileName']}")

        except Exception as ex:
            logging.info(f"Backdeck Database, unable to delete file: {item['dstFileName']} > {ex}")


        # Clear the Data Completeness model fields dealing with the catch data
        # TODO Todd Hay - Update the data completeness model fields dealing with catch accordingly when a backdeck database is removed
        # self._app.data_completeness._data_check_model.clear()
        self._app.data_completeness.dataCheckModel.populate_model()


class FileManagement(QObject):
    """
    Class for the FileManagement
    """
    wheelhouseModelChanged = pyqtSignal()
    sensorsModelChanged = pyqtSignal()
    backdeckModelChanged = pyqtSignal()

    folderCreationError = pyqtSignal(bool, str, arguments=["status", "msg"])

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

        # Set up the models
        self._wheelhouse_model = WheelhouseModel(self._app)
        self._sensors_model = SensorsModel(self._app)
        self._backdeck_model = BackdeckModel(self._app)

        self._copy_files_thread = QThread()
        self._copy_files_worker = None

        self._functions = CommonFunctions()

    @pyqtProperty(FramListModel, notify=wheelhouseModelChanged)
    def wheelhouseModel(self):
        """
        Method to return the self._wheelhouse_model model
        :return:
        """
        return self._wheelhouse_model

    @pyqtProperty(FramListModel, notify=sensorsModelChanged)
    def sensorsModel(self):
        """
        Method to return the self._sensors_model model
        :return:
        """
        return self._sensors_model

    @pyqtProperty(FramListModel, notify=backdeckModelChanged)
    def backdeckModel(self):
        """
        Method to return the self._backdeck_model model
        :return:
        """
        return self._backdeck_model

    @pyqtSlot(str, str,  str)
    def copy_files(self, dst, year, vessel):
        """
        Method to copy the wheelhouse, sensor, and backdeck files to the file directory
        structure.  This will look at all three of the models, iterate through their
        current lists, and copy the files to the appropriate target destination folder.
        The target destination folder will be as follows:

        \<destination path>
            \<year>
                \<vessel>
                    wheelhouse db files
                    sensor db files
                    backdeck db files
        :param dst: str - the destination path
        :param year: str - the year of the data, a four digit year
        :param vessel: str - the name of the vessel
        :return:
        """
        if not isinstance(dst, str) or \
            not isinstance(year, str) or \
            not isinstance(vessel, str):
            return

        # Create + Start Thread
        kwargs = {"dst": dst, "year": year, "vessel": vessel,
                  "wheelhouse": self._wheelhouse_model.items,
                  "sensors": self._sensors_model.items,
                  "backdeck": self._backdeck_model.items,
                  "app": self._app}
        self._copy_files_worker = CopyFilesWorker(kwargs=kwargs)
        self._copy_files_worker.moveToThread(self._copy_files_thread)
        self._copy_files_worker.copyStatus.connect(self._copy_status_received)
        self._copy_files_worker.fileCopyStatus.connect(self._file_copy_status_received)
        self._copy_files_thread.started.connect(self._copy_files_worker.run)
        self._copy_files_thread.start()

    def _file_copy_status_received(self, model, index, dst):
        """
        Method called when a file has been successfully copied, used to update the copyStatus column to
        indicate that the file was successfully copied
        :param model:
        :param index:
        :param dst: str - destination path for the given file
        :return:
        """
        if model not in ["wheelhouse", "sensors", "backdeck"] or \
                index < 0:
            return

        models = {"wheelhouse": self._wheelhouse_model,
                  "sensors": self._sensors_model,
                  "backdeck": self._backdeck_model}
        models[model].setProperty(index=index, property="copyStatus", value="Yes")
        models[model].setProperty(index=index, property="dstFileName", value=dst)

    def _copy_status_received(self, status, msg):
        """
        Method called when returning from the CopyFilesWorker background thread.  This
        gives the final results of the copy operations, were they successful or not.
        :return:
        """
        # Quit the thread
        if self._copy_files_thread:
            self._copy_files_thread.quit()

        # Emit signal to tell the user that the copying is finished
        self.folderCreationError.emit(status, msg)

        # TODO Todd Hay - Should I first check if the status == True before calling populate_model ?
        # Repopulate the Data Completeness model to incorporate the newly copied information
        self._app.data_completeness.dataCheckModel.populate_model()

    @pyqtSlot(str, str, str)
    def refresh_copy_status(self, dst, year, vessel):
        """
        Method called to refresh the copyStatus column of each of the three TableViews.  This is done
        so that a user can determine if there have been any underlying changes in the files in the
        target location, in particular if they've been deleted, moved, or renamed.
        :return:
        """
        full_path = os.path.join(dst, "Survey" + year, re.sub("[ \.\'\"]", "", vessel))

        for model in [self._wheelhouse_model, self._sensors_model, self._backdeck_model]:
            for i, item in enumerate(model.items):
                value = None
                if "fileName" in item:
                    if os.path.exists(os.path.join(full_path, os.path.basename(item["fileName"]))):
                        value = "Yes"
                    model.setProperty(index=i, property="copyStatus", value=value)

    def stop_background_threads(self):
        """
        Method to stop all of the background threads
        :return:
        """
        if self._copy_files_worker:
            self._copy_files_worker.stop()


class CopyFilesWorker(QObject):

    """
    Class to copy files to final destination location in the background
    """
    copyStatus = pyqtSignal(bool, str)
    fileCopyStatus = pyqtSignal(str, int, str)

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self._is_running = False
        self._app = kwargs["app"]
        self.wheelhouse_dbs = kwargs["wheelhouse"]
        self.sensor_dbs = kwargs["sensors"]
        self.backdeck_dbs = kwargs["backdeck"]
        self.dst = kwargs["dst"]
        self.year = kwargs["year"]
        self.vessel = kwargs["vessel"].replace('\'', '')

        self.result = {'status': False, 'msg': ''}

        self._functions = CommonFunctions()

    def run(self):
        self._is_running = True
        status, msg = self.copy_files()
        self.copyStatus.emit(status, msg)

    def stop(self):
        """
        Stop the current thread from running
        :return:
        """
        self._is_running = False

    def copy_files(self):
        """
        Copies files from the src to the dst folder
        :return:
        """

        # Get the vessel_id.  Note that the year is already stored in self.year
        vessel_id = VesselLu.get(VesselLu.vessel_name == self.vessel).vessel

        # FRAM_CENTRAL LOOKUPS - values for different operation types
        project_lu_id = Lookups.get(Lookups.type == "Project",
                                    Lookups.value == "West Coast Groundfish Slope/Shelf Bottom Trawl Survey").lookup
        year_lu_id = Lookups.get(Lookups.type == "Operation", Lookups.value == "Year").lookup
        pass_lu_id = Lookups.get(Lookups.type == "Operation", Lookups.value == "Pass").lookup
        cruise_lu_id = Lookups.get(Lookups.type == "Operation", Lookups.value == "Cruise").lookup
        leg_lu_id = Lookups.get(Lookups.type == "Operation", Lookups.value == "Leg").lookup

        # GET the relevant cruise op given the year, vessel
        try:

            logging.info(f"year = {self._app.settings.year}")

            cruise_id = self._functions.get_cruise_id(self._app.settings.year, self._app.settings.vessel)

            logging.info(f"cruise_id = {cruise_id}")
        except Exception as ex:
            cruise_id = None

        status = True
        msg = "Not started"

        """
        1. Check that the destination path / year / vessel folder structure exists,
        if not create it
        """
        full_path = os.path.join(self.dst, "Survey" + self.year, re.sub("[ \.\'\"]", "", self.vessel))
        if not os.path.isdir(full_path) or not os.path.exists(full_path):
            try:
                os.makedirs(full_path)
            except OSError as ex:
                status = False
                msg = "Error creating the destination path: {0}".format(full_path)
                return status, msg

        """
        2. Begin copying the files, by iterating over the wheelhouse,
            sensors, and background lists
        """
        model = OrderedDict()
        model["wheelhouse"] = {"listModel": self.wheelhouse_dbs, "fileType": "Wheelhouse Database"}
        model["backdeck"] = {"listModel": self.backdeck_dbs, "fileType": "Backdeck Meta-Database"}
        model["sensors"] = {"listModel": self.sensor_dbs, "fileType": "Sensor Database"}

        for key, value in model.items():

            file_type = model[key]["fileType"]
            file_type_lu_id, _ = Lookups.get_or_create(type="Operation File", value=file_type)

            for k, v in value.items():

                try:

                    if k == "listModel":

                        for i, x in enumerate(v):

                            if not self._is_running:
                                raise BreakIt

                            copy_status = x["copyStatus"]
                            file_name = x["srcFileName"]

                            logging.info(f"key: {key}, item: {x}")
                            self._app.settings.statusBarMessage = "Copying {0}".format(file_name)

                            if copy_status is None and file_name is not None:

                                dst_file = os.path.join(full_path, os.path.basename(file_name))

                                if key == "wheelhouse":

                                    logging.info(f"Copying wheelhouse DB file to: {dst_file}")

                                    self._app.settings.set_wheelhouse_proxy(db_file=file_name)
                                    if re.match('trawl_wheelhouse.*\.db', os.path.basename(file_name)) and WhOperationalSegment.table_exists():

                                        # WHEELHOUSE DB - Types lookups for various operations types
                                        wh_cruise_type_id = WhTypes.get(WhTypes.category == "Operational Segment",
                                                                WhTypes.type == "Cruise").type_id
                                        wh_pass_type_id = WhTypes.get(WhTypes.category == "Operational Segment",
                                                                      WhTypes.type == "Pass").type_id
                                        wh_leg_type_id = WhTypes.get(WhTypes.category == "Operational Segment",
                                                                     WhTypes.type == "Leg").type_id
                                        project_type_id = WhTypes.get(WhTypes.category == "Project",
                                                                      WhTypes.type == "Trawl Survey").type_id
                                        project_ids = WhProjects.select(WhProjects.project).where(
                                            WhProjects.project_type == project_type_id)

                                        # FRAM_CENTRAL - OPERATION_FILES - Insert record
                                        start_date_time = TowWaypoints.select().order_by(TowWaypoints.date_time.asc()).limit(1).get().date_time
                                        start_date_time = arrow.get(start_date_time).to('US/Pacific').isoformat()
                                        end_date_time = TowWaypoints.select().order_by(TowWaypoints.date_time.desc()).limit(1).get().date_time
                                        end_date_time = arrow.get(end_date_time).to('US/Pacific').isoformat()
                                        op_file, _ = OperationFiles.get_or_create(database_name=os.path.basename(file_name),
                                                                              final_path_name=dst_file,
                                                                              defaults={
                                                                                  "operation_file_type_lu": file_type_lu_id,
                                                                                  "project_lu": project_lu_id,
                                                                                  "start_date_time": start_date_time,
                                                                                  "end_date_time": end_date_time,
                                                                                  "load_completed_datetime": arrow.now().isoformat()})

                                        logging.info(f"\tinserted op_file: {op_file.operation_file}")

                                        """ FRAM_CENTRAL - Order of operations is as follows:
                                            Year+Project > Pass > Cruise > Leg > Haul

                                        Wheelhouse DB are as follows:
                                            Year + Project + Vessel (= Cruise) > Pass > Leg > Haul


                                        INSERT THE YEAR
                                        """
                                        year_op, _ = Operations.get_or_create(
                                            operation_type_lu=year_lu_id,
                                            project_lu=project_lu_id,
                                            operation_name=self.year
                                            # defaults={
                                            #     "operation_name": self.year     # TODO Fix hard coding
                                            # }
                                        )
                                        logging.info(f"year_op = {year_op}")

                                        # WHEELHOUSE DB - Iterate through all of the cruises, passes, legs and insert into FRAM_CENTRAL recursively
                                        cruises = WhOperationalSegment.select().where(WhOperationalSegment.operational_segment_type==wh_cruise_type_id,
                                                                                       WhOperationalSegment.project<<project_ids)
                                        for cruise in cruises:
                                            passes = WhOperationalSegment.select().where(WhOperationalSegment.operational_segment_type == wh_pass_type_id,
                                                                                         WhOperationalSegment.project << project_ids,
                                                                                         WhOperationalSegment.parent_segment == cruise)

                                            if not self._is_running:
                                                raise BreakIt

                                            for p in passes:

                                                # FRAM_CENTRAL - INSERT THE PASS
                                                pass_op, _ = Operations.get_or_create(
                                                    parent_operation_id=year_op.operation,
                                                    operation_type_lu=pass_lu_id,
                                                    project_lu=project_lu_id,
                                                    operation_name=p.name.lower().strip("pass")
                                                )

                                                # FRAM_CENTRAL - INSERT THE CRUISE
                                                cruise_op, _ = Operations.get_or_create(
                                                    parent_operation_id=pass_op.operation,
                                                    operation_type_lu=cruise_lu_id,
                                                    project_lu=project_lu_id,
                                                    vessel_id=vessel_id,
                                                    defaults={
                                                        "operation_name": VesselLu.get(VesselLu.vessel == vessel_id).vessel_name
                                                    }
                                                )

                                                legs = WhOperationalSegment.select().where(WhOperationalSegment.operational_segment_type == wh_leg_type_id,
                                                                                           WhOperationalSegment.project << project_ids,
                                                                                           WhOperationalSegment.parent_segment == p)

                                                for l in legs:

                                                    if not self._is_running:
                                                        raise BreakIt

                                                    # WHEELHOUSE DB - Get the Person IDs

                                                    try:
                                                        fpc_id = None
                                                        fpc_first = ""
                                                        fpc_last = ""
                                                        full_name = WhPersonnel.get(
                                                            WhPersonnel.person == l.fpc).full_name
                                                        fpc_list = re.sub(r' .{1} ', '',
                                                                          re.sub(r'\([^)]*\)', '', full_name)).split(
                                                            ' ')
                                                        if len(fpc_list) == 2:
                                                            fpc_first = fpc_list[0]
                                                            fpc_last = fpc_list[1]
                                                        fpc_id = PersonnelLu.get(PersonnelLu.first_name == fpc_first,
                                                                                PersonnelLu.last_name==fpc_last).person
                                                    except DoesNotExist as ex:
                                                        fpc_id = None
                                                        logging.error('FPC name does not exist in FRAM Central: {0}, {1} > {2}'.format(fpc_first, fpc_last, file_name))
                                                    try:
                                                        sci1_id = None
                                                        sci1_first = ""
                                                        sci1_last = ""
                                                        full_name = WhPersonnel.get(
                                                            WhPersonnel.person == l.scientist_1).full_name
                                                        sci1_list = re.sub(r' .{1} ', '',
                                                                           re.sub(r'\([^)]*\)', '', full_name)).split(
                                                            ' ')
                                                        if len(sci1_list) == 2:
                                                            sci1_first = sci1_list[0]
                                                            sci1_last = sci1_list[1]
                                                        sci1_id = PersonnelLu.get(PersonnelLu.first_name == sci1_first,
                                                                              PersonnelLu.last_name == sci1_last).person
                                                    except DoesNotExist as ex:
                                                        sci1_id = None
                                                        logging.error("Scientist 1 name does not exist in FRAM Central: {0}, {1} > {2}".format(sci1_first, sci1_last, file_name))
                                                    try:
                                                        sci2_id = None
                                                        sci2_first = ""
                                                        sci2_last = ""
                                                        full_name = WhPersonnel.get(
                                                            WhPersonnel.person == l.scientist_2).full_name
                                                        sci2_list = re.sub(r' .{1} ', '',
                                                                           re.sub(r'\([^)]*\)', '', full_name)).split(
                                                            ' ')
                                                        if len(sci2_list) == 2:
                                                            sci2_first = sci2_list[0]
                                                            sci2_last = sci2_list[1]
                                                        sci2_id = PersonnelLu.get(PersonnelLu.first_name == sci2_first,
                                                                              PersonnelLu.last_name == sci2_last).person
                                                    except DoesNotExist as ex:
                                                        sci2_id = None
                                                        logging.error("Scientist 2 name does not exist in FRAM Central: {0}, {1} > {2}".format(sci2_first, sci2_last, file_name))

                                                    # INSERT THE LEG
                                                    leg_op, _ = Operations.get_or_create(
                                                        parent_operation_id=cruise_op.operation,
                                                        operation_type_lu=leg_lu_id,
                                                        operation_name=l.name.lower().strip('leg'),
                                                        vessel_id=vessel_id,
                                                        project_lu=project_lu_id,
                                                        defaults={
                                                            "captain_id": None,
                                                            "fpc_id": fpc_id,
                                                            "scientist_1_id": sci1_id,
                                                            "scientist_2_id": sci2_id
                                                        }
                                                    )

                                                    # INSERT THE OPERATION_FILES_MTX RECORD
                                                    op_mtx, _ = OperationFilesMtx.get_or_create(
                                                        operation=cruise_op,
                                                        operation_file=op_file
                                                    )


                                        if not self._is_running:
                                            raise BreakIt

                                        # copy to the destination path
                                        shutil.copyfile(src=file_name, dst=dst_file)
                                        logging.info(f"Wheelhouse DB file successfully copied to: {dst_file}")

                                        self.fileCopyStatus.emit(key, i, dst_file)

                                elif key == "sensors":

                                    logging.info(f"Copying sensors DB file to: {dst_file}")

                                    # Get the year from the sensors file, if it doesn't align with the self.year, don't even bother with it
                                    if "sensors_" in os.path.basename(file_name):
                                        year = os.path.splitext(os.path.basename(file_name))[0].split('_')[1][:4]
                                    else:
                                        continue

                                    self._app.settings.set_sensors_proxy(db_file=file_name)

                                    if re.match('sensors_\d{8}\.db', os.path.basename(file_name)) and \
                                            EnviroNetRawFiles.table_exists() and EnviroNetRawStrings.table_exists() and \
                                            year == self.year:

                                        # update the database - operation_files
                                        start_date_time = EnviroNetRawStrings.select().order_by(EnviroNetRawStrings.date_time.asc()).limit(1)
                                        if len(start_date_time) > 0:
                                            start_date_time = arrow.get(start_date_time.get().date_time).to('US/Pacific').isoformat()
                                        else:
                                            start_date_time = None

                                        end_date_time = EnviroNetRawStrings.select().order_by(EnviroNetRawStrings.date_time.desc()).limit(1)
                                        if len(end_date_time) > 0:
                                            end_date_time = arrow.get(end_date_time.get().date_time).to('US/Pacific').isoformat()
                                        else:
                                            end_date_time = None

                                        sensors_file, _ = OperationFiles.get_or_create(database_name=os.path.basename(file_name),
                                                                              final_path_name=dst_file,
                                                                              defaults={
                                                                                  "operation_file_type_lu": file_type_lu_id,
                                                                                  "project_lu": project_lu_id,
                                                                                  "start_date_time": start_date_time,
                                                                                  "end_date_time": end_date_time,
                                                                                  "load_completed_datetime": arrow.now().isoformat()})

                                        # if not isinstance(cruise_op, Operations):
                                        cruise_id = self._functions.get_cruise_id(self._app.settings.year, self._app.settings.vessel)

                                        if not self._is_running:
                                            raise BreakIt

                                        # INSERT THE OPERATION_FILES_MTX RECORD
                                        op_mtx, _ = OperationFilesMtx.get_or_create(
                                            operation=cruise_id,
                                            operation_file=sensors_file.operation_file
                                        )

                                        # copy to the destination path
                                        shutil.copyfile(src=file_name, dst=dst_file)

                                        logging.info(f"Sensors DB file successfully copied to: {dst_file}")
                                        self.fileCopyStatus.emit(key, i, dst_file)

                                elif key == "backdeck":

                                    logging.info(f"Copying backdeck DB file to: {dst_file}")

                                    self._app.settings.set_backdeck_proxy(db_file=file_name)
                                    if re.match('trawl_backdeck.*\.db', os.path.basename(file_name)) and \
                                            Hauls.table_exists() and Catch.table_exists() and Specimen.table_exists():

                                        # update the database - operation_files
                                        start_date_time = Hauls.select().order_by(Hauls.start_datetime.asc()).limit(1).get().start_datetime
                                        start_date_time = arrow.get(start_date_time).to('US/Pacific').isoformat()
                                        end_date_time = Hauls.select().order_by(Hauls.end_datetime.desc()).limit(1).get().end_datetime
                                        end_date_time = arrow.get(end_date_time).to('US/Pacific').isoformat()

                                        backdeck_file, _ = OperationFiles.get_or_create(database_name=os.path.basename(file_name),
                                                                              final_path_name=dst_file,
                                                                              defaults={
                                                                                  "operation_file_type_lu": file_type_lu_id,
                                                                                  "project_lu": project_lu_id,
                                                                                  "start_date_time": start_date_time,
                                                                                  "end_date_time": end_date_time,
                                                                                  "load_completed_datetime": arrow.now().isoformat()})

                                        logging.info(f"backdeck_file = {backdeck_file.operation_file}")

                                        cruise_id = self._functions.get_cruise_id(self._app.settings.year, self._app.settings.vessel)

                                        if not self._is_running:
                                            raise BreakIt

                                        # INSERT THE OPERATION_FILES_MTX RECORD
                                        op_mtx, _ = OperationFilesMtx.get_or_create(
                                            operation=cruise_id,
                                            operation_file=backdeck_file.operation_file
                                        )

                                        # copy to the destination path
                                        shutil.copyfile(src=file_name, dst=dst_file)
                                        logging.info(f"Backdeck DB file successfully copied to: {dst_file}")

                                        self.fileCopyStatus.emit(key, i, dst_file)


                                        # operation_file = OperationFiles()
                                # operation_file.operation_file_type_lu = file_type_lu_id
                                # operation_file.project_lu = project_lu_id
                                # operation_file.database_name = os.path.basename(file_name)
                                # operation_file.final_path_name = dst_file
                                # operation_file.start_date_time = None       # ToDo - Interrogate the wheelhouse db
                                # operation_file.end_date_time = None         # ToDo - Interrogate the wheelhouse db
                                # operation_file.load_completed_datetime = datetime.now().isoformat()
                                # operation_file.save()

                                # emit a signal to update the UI, indicating that it has been copied

                except BreakIt:
                    # Close out all of the proxies
                    self._app.settings.set_wheelhouse_proxy(db_file=None)
                    self._app.settings.set_sensors_proxy(db_file=None)
                    self._app.settings.set_backdeck_proxy(db_file=None)

                    msg = "File Copying stopped prematurely"
                    self._app.settings.statusBarMessage = msg
                    logging.info(msg)
                    return status, msg

                except Exception as ex:
                    status = False
                    msg = "Error copying files to destination:\n\n{0}".format(str(ex))
                    return status, msg

        # Close out all of the proxies
        self._app.settings.set_wheelhouse_proxy(db_file=None)
        self._app.settings.set_sensors_proxy(db_file=None)
        self._app.settings.set_backdeck_proxy(db_file=None)

        msg = "Finished copying files"
        self._app.settings.statusBarMessage = msg
        logging.info(msg)
        return status, msg


if __name__ == '__main__':

    pass
