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
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QThread, \
    QObject, QVariant
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import QJSValue
from py.common.FramListModel import FramListModel
import logging
import os
from copy import deepcopy
import arrow
from collections import OrderedDict
from decimal import Decimal
import unittest
import cProfile
import pstats, sys
import io
import re
from dateutil import parser
from timeit import timeit, Timer
import datetime
from struct import pack
import psycopg2

# Unit Testing Support Only - START
from py.trawl_analyzer.Settings import Settings
from py.trawl_analyzer.FileManagement import FileManagement
from py.trawl_analyzer.TrawlAnalyzerDB import TrawlAnalyzerDB
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import QQmlApplicationEngine
from py.common.QSingleApplication import QtSingleApplication
# Unit Testing Support Only - END


from py.trawl_analyzer.BcsReader import BcsReader
from py.trawl_analyzer.SbeReader import SeabirdCNVreader

from py.trawl_analyzer.CommonFunctions import CommonFunctions

from py.trawl_analyzer.TrawlAnalyzerDB_model import Lookups, Operations, OperationFilesMtx, OperationFiles, VesselLu, \
    PersonnelLu, StationInventoryLu, OperationsFlattenedVw, Events, Comments, OperationMeasurements, OperationAttributes, \
    ReportingRules, PerformanceDetails, ParsingRulesVw, MeasurementStreams, \
    ParsingSentencesVw, OperationMeasurementsErr, GroupMemberVw

from py.trawl_analyzer.TrawlWheelhouseDB_model import OperationalSegment as WhOperationalSegment, TowWaypoints, \
    TypesLu as WhTypes, Project as WhProjects, PersonnelLu as WhPersonnel, VesselLu as WhVessel, TowDetails, FpcLog, \
    TowImpactFactors, DeployedEquipment

from py.trawl_analyzer.TrawlSensorsDB_model import EnviroNetRawFiles, EnviroNetRawStrings

from py.trawl_analyzer.TrawlBackdeckDB_model import Hauls as BdHauls, Catch as BdCatch, Specimen as  BdSpecimen
from peewee import fn, PeeweeException, DoesNotExist
from playhouse.shortcuts import model_to_dict

from PyQt5.QtCore import QSortFilterProxyModel, Q_ENUMS, QAbstractItemModel, QByteArray, QRegExp


DEBUG = True


class BreakIt(Exception): pass


class SortFilterProxyModel(QSortFilterProxyModel):

    """
    Pulled from here:
    http://stackoverflow.com/questions/36823456/use-a-qsortfilterproxymodel-from-qml-with-pyqt5

    with reference to here:
    http://blog.qt.io/blog/2014/04/16/qt-weekly-6-sorting-and-filtering-a-tableview/

    """

    class FilterSyntax:
        RegExp, Wildcard, FixedString = range(3)

    Q_ENUMS(FilterSyntax)

    def __init__(self, parent):
        super().__init__(parent)

    @pyqtProperty(QAbstractItemModel)
    def source(self):
        return super().sourceModel()

    @source.setter
    def source(self, source):
        self.setSourceModel(source)

    @pyqtProperty(int)
    def sortOrder(self):
        return self._order

    @sortOrder.setter
    def sortOrder(self, order):
        self._order = order
        super().sort(0, order)

    @pyqtProperty(QByteArray)
    def sortRole(self):
        return self._roleNames().get(super().sortRole())

    @sortRole.setter
    def sortRole(self, role):
        super().setSortRole(self._roleKey(role))

    @pyqtProperty(QByteArray)
    def filterRole(self):
        return self._roleNames().get(super().filterRole())

    @filterRole.setter
    def filterRole(self, role):
        super().setFilterRole(self._roleKey(role))

    @pyqtProperty(str)
    def filterString(self):
        return super().filterRegExp().pattern()

    @filterString.setter
    def filterString(self, filter):
        super().setFilterRegExp(QRegExp(filter, super().filterCaseSensitivity(), self.filterSyntax))

    @pyqtProperty(int)
    def filterSyntax(self):
        return super().filterRegExp().patternSyntax()

    @filterSyntax.setter
    def filterSyntax(self, syntax):
        super().setFilterRegExp(QRegExp(self.filterString, super().filterCaseSensitivity(), syntax))

    def filterAcceptsRow(self, sourceRow, sourceParent):
        rx = super().filterRegExp()
        if not rx or rx.isEmpty():
            return True
        model = super().sourceModel()
        sourceIndex = model.index(sourceRow, 0, sourceParent)
        # skip invalid indexes
        if not sourceIndex.isValid():
            return True
        # If no filterRole is set, iterate through all keys
        if not self.filterRole or self.filterRole == "":
            roles = self._roleNames()
            for key, value in roles.items():
                data = model.data(sourceIndex, key)
                if rx.indexIn(data) != -1:
                    return True
            return False
        # Here we have a filterRole set so only search in that
        data = model.data(sourceIndex, self._roleKey(self.filterRole))
        return rx.indexIn(data) != -1

    def _roleKey(self, role):
        roles = self.roleNames()
        for key, value in roles.items():
            if value == role:
                return key
        return -1

    def _roleNames(self):
        source = super().sourceModel()
        if source:
            return source.roleNames()
        return {}


class PopulateModelBackdeckDataThread(QObject):

    backdeckThreadCompleted = pyqtSignal(bool, str)
    haulProcessed = pyqtSignal(int, QVariant, str)

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self._is_running = False
        self._app = kwargs["app"]
        self._ordered_rolenames = kwargs["orderedNames"]
        self._functions = CommonFunctions()

    def run(self):
        self._is_running = True
        status, msg = self.query_dbs()
        self.backdeckThreadCompleted.emit(status, msg)

    def stop(self):
        """
        Method to interrupt the thread, stopping it from running
        :return:
        """
        self._is_running = False

    def query_dbs(self):
        """
        Primary method to query for all of the data to populate the Data Completeness primary model
        :return:
        """
        status = False
        msg = ""
        bd_hauls = []
        bd_test_hauls = []

        # Get the wheelhouse databases and query for all of the available hauls
        empty_item = dict((x,"") for x in self._ordered_rolenames)

        hauls = self._app.data_completeness._data_check_model.items

        # Load Backdeck information
        start = arrow.now()
        for i, bd_item in enumerate(self._app.file_management.backdeckModel.items):

            try:

                if not self._is_running:
                    raise BreakIt

                if not os.path.exists(bd_item["dstFileName"]):
                    logging.error("Wheelhouse database does not exist in the target location: {0}".format(bd_item["dstFileName"]))
                    continue

                self._app.settings.set_backdeck_proxy(db_file=bd_item["dstFileName"])
                bd_hauls = BdHauls.select().order_by(BdHauls.haul_number)
                for bd_haul in bd_hauls:

                    if not self._is_running:
                        raise BreakIt

                    elems = [[i, x] for i, x in enumerate(hauls) if x["haul"] == bd_haul.haul_number]
                    # elems = [x for x in results_hauls if x[1] == bd_haul.haul_number]
                    if "t" in bd_haul.haul_number:
                        elems = [[0, bd_haul.haul_number]]
                    for elem in elems:

                        if not self._is_running:
                            raise BreakIt

                        item = dict()
                        item["catchDatabase"] = bd_item["dstFileName"]

                        catch = BdCatch.select(BdCatch.catch).where(BdCatch.operation == bd_haul.haul,
                                                                    BdCatch.parent_catch.is_null())
                        catch_ids = [x.catch for x in catch]
                        item["catchSpeciesCount"] = catch.count()

                        # TODO Todd Hay - Slow - Improve catch zero weight count query performance
                        zero_weight_count = 0
                        for catch_id in catch_ids:
                            sql = """
                                WITH RECURSIVE
                                  basket_of(n) AS (
                                    VALUES(""" + str(catch_id) + """)
                                    UNION
                                    SELECT catch_id FROM catch, basket_of
                                     WHERE catch.parent_catch_id=basket_of.n
                                  )
                                SELECT count(*) as num FROM catch
                                 WHERE catch_id IN basket_of
                                    AND parent_catch_id is not null
                            """
                            # if isinstance(BdCatch.raw(sql), BdCatch):

                            qry_count = self._app.settings._backdeck_database.execute_sql(sql).fetchone()[0]
                            if qry_count == 0:
                                zero_weight_count += 1
                        item["zeroBasketWeightCount"] = zero_weight_count

                        # TODO Todd Hay - Slow - Improve the query performance
                        specimens = BdSpecimen.select().where(BdSpecimen.parent_specimen.is_null(),
                                                              BdSpecimen.catch << catch_ids)
                        item["specimenCount"] = specimens.count()

                        # sql = """SELECT COUNT(*) AS NUM FROM SPECIMEN WHERE PARENT_SPECIMEN_ID IS NULL
                        #         AND CATCH_ID IN """ + str(tuple(catch_ids)) + """;"""
                        # # sql = "SELECT COUNT(*) FROM SPECIMEN"
                        # try:
                        #     specimens_count = self._app.settings._backdeck_database.execute_sql(sql).fetchone()[0]
                        #     item["specimenCount"] = specimens_count
                        # except Exception as ex:
                        #     logging.info('{0}'.format(sql))
                        #     logging.info("{0}".format(ex))

                        # Insert Action
                        if "t" in bd_haul.haul_number:
                            test_item = {**deepcopy(empty_item), **item}
                            test_item["load"] = "no"
                            test_item["haul"] = bd_haul.haul_number
                            test_item["haulPerformance"] = "Not Available"

                            try:
                                start_date_time = bd_haul.start_datetime
                                if start_date_time:
                                    test_item["haulStart"] = arrow.get(start_date_time).to("US/Pacific").format("MM/DD hh:mm:ss")
                                end_date_time = bd_haul.end_datetime
                                if end_date_time:
                                    test_item["haulEnd"] = arrow.get(end_date_time).to("US/Pacific").format("MM/DD hh:mm:ss")
                            except Exception as ex:
                                logging.error("Unable to populate test haul start/end times: {0}".format(ex))

                            test_item["catchDatabase"] = os.path.basename(bd_item["dstFileName"])
                            catch_count = BdCatch.select().where(BdCatch.operation == bd_haul.haul,
                                                                 BdCatch.parent_catch.is_null()).count()

                            test_item["catchSpeciesCount"] = catch_count
                            test_item["specimenCount"] = None
                            test_item["zeroBasketWeightCount"] = None

                            # bd_test_hauls.append(test_item)

                            self.haulProcessed.emit(-1, test_item, "insert")

                        # Update Action
                        else:
                            # results[elem[0][0]] = {**results[elem[0][0]], **item}
                            # results[elem[0]] = {**results[elem[0]], **item}

                            self.haulProcessed.emit(elem[0], item, "update")

            except BreakIt:
                self._app.settings.set_backdeck_proxy(db_file=None)
                msg = "Breaking backdeck model loading"
                logging.info(msg)
                status = False
                return status, msg

            except Exception as ex:
                self._app.settings.set_backdeck_proxy(db_file=None)

                logging.info("Unable to query the backdeck database: {0} > {1}"\
                             .format(bd_item["dstFileName"], ex))

        end = arrow.now()
        logging.info('\t\tDataCompleteness Backdeck Population, Elapsed time, backdeck DBs: {0:.1f}s'.format((end - start).total_seconds()))

        # Set the status to true and return the results list, thus finishing the thread
        status = True
        return status, msg


class PopulateModelSensorDataThread(QObject):

    sensorThreadCompleted = pyqtSignal(bool, str)
    sensorDataUpdated = pyqtSignal(int, QVariant, arguments=["index", "item"])

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self._is_running = False
        self._app = kwargs["app"]
        self._ordered_rolenames = kwargs["orderedNames"]
        self._functions = CommonFunctions()

    def run(self):
        self._is_running = True
        status, msg = self.query_dbs()
        self.sensorThreadCompleted.emit(status, msg)

    def stop(self):
        """
        Method to interrupt the thread, stopping it from running
        :return:
        """
        self._is_running = False

    def query_dbs(self):
        """
        Primary method to query for all of the data to populate the Data Completeness primary model
        :return:
        """
        status = False
        msg = ""

        # Get the wheelhouse databases and query for all of the available hauls
        empty_item = dict((x,"") for x in self._ordered_rolenames)

        model_hauls = self._app.data_completeness._data_check_model.items

        cruise_id = self._functions.get_cruise_id(year=self._app.settings.year, vessel=self._app.settings.vessel)
        fc_hauls = OperationsFlattenedVw.select().where(OperationsFlattenedVw.cruise == cruise_id,
                                                        OperationsFlattenedVw.operation_type == "Tow")

        start = arrow.now()
        for i, x in enumerate(self._app.file_management.sensorsModel.items):

            logging.info(f"\t\tSensor database population: {x['dstFileName']}")

            try:
                if not os.path.exists(x["dstFileName"]):
                    logging.error("Sensor database does not exist in the target location: {0}".format(x["dstFileName"]))
                    continue

                if not self._is_running:
                    raise BreakIt

                self._app.settings.set_sensors_proxy(db_file=x["dstFileName"])

                strings = EnviroNetRawStrings.select().limit(1)
                if strings.count() > 0:

                # TODO Todd Hay - Why is count() not working against the active sensors db here when at home, 2016, MJ
                # if EnviroNetRawStrings.select().count() > 0:

                    start_date_time = EnviroNetRawStrings.select().order_by(EnviroNetRawStrings.date_time.asc()).limit(1)
                    if len(start_date_time) > 0:
                        start_date_time = arrow.get(start_date_time.get().date_time).to('US/Pacific').format("MM/DD HH:mm:ss")
                    else:
                        logging.info('start time is none: {0}'.format(x["dstFileName"]))
                        start_date_time = None

                    end_date_time = EnviroNetRawStrings.select().order_by(EnviroNetRawStrings.date_time.desc()).limit(1)
                    if len(end_date_time) > 0:
                        end_date_time = arrow.get(end_date_time.get().date_time).to('US/Pacific').format("MM/DD HH:mm:ss")
                    else:
                        logging.info('end time is none: {0}'.format(x["dstFileName"]))
                        end_date_time = None

                    # logging.info(f"{start_date_time}, {end_date_time}")
                    hauls = []
                    if start_date_time and end_date_time:
                        hauls = [[j, x] for j, x in enumerate(model_hauls) if x["haulEnd"] and x["haulStart"] and \
                             x["haulStart"] <= end_date_time and
                             x["haulEnd"] >= start_date_time]


                             # x["haulStart"] >= start_date_time and
                             # x["haulEnd"] <= end_date_time]

                    logging.info(f'\t\tNumber of hauls that match this sensor db > {len(hauls)}')

                    for haul in hauls:

                        # logging.info(f'sensors population, matching haul: {haul[1]["haul"]}')

                        if not self._is_running:
                            raise BreakIt

                        item = dict()
                        item["sensorDatabase"] = x['dstFileName']

                        try:
                            # fc_haul = fc_hauls.get(fc_hauls.tow_name == haul[1]["haul"])
                            fc_haul = OperationsFlattenedVw.get(OperationsFlattenedVw.cruise == cruise_id,
                                                                 OperationsFlattenedVw.operation_type == "Tow",
                                                                 OperationsFlattenedVw.tow_name == haul[1]["haul"])

                            item["sensorsLoadStatus"] = arrow.get(fc_haul.sensor_load_date).format("MM/DD HH:mm:ss") \
                                if fc_haul.sensor_load_date else None
                        except Exception as ex:
                            # logging.info('Unable to match a haul in OperationsFlattenedVw')
                            pass

                        # logging.info(f"Sensor data parsed for table population: row {haul[0]}, haul {haul[1]['haul']}, info: {item}")
                        self.sensorDataUpdated.emit(int(haul[0]), item)

            except BreakIt:
                self._app.settings.set_sensors_proxy(db_file=None)
                msg = "Breaking model loading"
                logging.info(msg)
                status = False
                return status, msg

            except Exception as ex:
                self._app.settings.set_sensors_proxy(db_file=None)
                logging.error("Error loading the sensors data: {0} > {1}".format(x["dstFileName"], ex))
                status = False
                return status, msg

        end = arrow.now()
        logging.info('\t\tDataCompleteness Sensors DB Population, Elapsed time, sensor DBs: {0:.1f}s'.format((end - start).total_seconds()))

        self._app.settings.set_sensors_proxy(db_file=None)

        return status, msg


class PopulateModelThread(QObject):

    queryStatus = pyqtSignal(bool, str, QVariant)
    haulDataUpdated = pyqtSignal(QVariant, arguments=["item"])
    breakItEncountered = pyqtSignal(str, arguments=["msg"])

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self._is_running = False
        self._app = kwargs["app"]
        self._ordered_rolenames = kwargs["orderedNames"]
        self._functions = CommonFunctions()

    def run(self):
        self._is_running = True
        status, msg, results = self.query_dbs()
        self.queryStatus.emit(status, msg, results)

    def stop(self):
        """
        Method to interrupt the thread, stopping it from running
        :return:
        """
        self._is_running = False

    def query_dbs(self):
        """
        Primary method to query for all of the data to populate the Data Completeness primary model
        :return:
        """
        status = False
        msg = ""
        results = []
        bd_hauls = []
        bd_test_hauls = []

        # Get the wheelhouse databases and query for all of the available hauls
        empty_item = dict((x,"") for x in self._ordered_rolenames)

        cruise_id = self._functions.get_cruise_id(year=self._app.settings.year, vessel=self._app.settings.vessel)

        fc_hauls = OperationsFlattenedVw.select().where(OperationsFlattenedVw.cruise == cruise_id,
                                                        OperationsFlattenedVw.operation_type == "Tow").dicts()

        # Load Wheelhouse information
        start = arrow.now()
        for db in self._app.file_management.wheelhouseModel.items:

            logging.info(f"\t\tWheelhouse database population: {db['dstFileName']}")

            try:
                if not os.path.exists(db["dstFileName"]):
                    logging.error("Wheelhouse database does not exist in the target location: {0}".format(db["dstFileName"]))
                    continue

                if not self._is_running:
                    msg = "Breaking model loading"
                    raise BreakIt

                self._app.settings.set_wheelhouse_proxy(db_file=db["dstFileName"])

                vessel_id = WhVessel.get(WhVessel.vessel_name == self._app.settings.vessel).vessel

                try:
                    logging.info(f"before project_id")
                    project_id = WhProjects.get(WhProjects.name == "Trawl Survey",
                                WhProjects.year == self._app.settings.year).project
                    logging.info(f"after project_id = {project_id}")
                except DoesNotExist as ex:
                    msg = f"Unable to find the project ID in the\nwheelhouse DB for Trawl Survey for year = " \
                          f"{self._app.settings.year}\n\nPlease correct the Wheelhouse SQLite DB"
                    raise BreakIt

                haul_type_id = WhTypes.get(WhTypes.category == "Operational Segment",
                                           WhTypes.type == "Tow").type_id
                hauls = WhOperationalSegment.select().where(WhOperationalSegment.vessel == vessel_id,
                                                            WhOperationalSegment.project == project_id,
                                                            WhOperationalSegment.operational_segment_type == haul_type_id)

                logging.info(f"\t\tHauls count = {hauls.count()}")

                for haul in hauls:

                    if not self._is_running:
                        msg = "Breaking model loading"
                        raise BreakIt

                    item = deepcopy(empty_item)
                    item["load"] = "no"

                    # fc_haul = OperationsFlattenedVw.select().where(OperationsFlattenedVw.tow_name == haul.name).first()
                    fc_haul = [x for x in fc_hauls if x["tow_name"] == haul.name]
                    if len(fc_haul) > 0:
                        fc_haul = fc_haul[0]
                        item["opsLoadStatus"] = arrow.get(fc_haul["operation_load_date"]).format("MM/DD HH:mm:ss") if fc_haul["operation_load_date"] else None
                        item["catchLoadStatus"] = arrow.get(fc_haul["catch_load_date"]).format("MM/DD HH:mm:ss") if fc_haul["catch_load_date"] else None
                        item["sensorsLoadStatus"] = arrow.get(fc_haul["sensor_load_date"]).format("MM/DD HH:mm:ss") if fc_haul["sensor_load_date"] else None
                        item["linked"] = fc_haul["alternate_operation_name"] if fc_haul["alternate_operation_name"] else None

                    item["haul"] = haul.name
                    item["haulDatabase"] = db["dstFileName"]

                    tow = TowDetails.get(TowDetails.tow_number == haul.name)
                    if tow.is_satisfactory:
                        if tow.is_satisfactory.lower() == "y":
                            item["haulPerformance"] = "Satisfactory"
                        else:
                            item["haulPerformance"] = "Unsatisfactory"

                    # Get the datetime of the first waypoint
                    waypoints = TowWaypoints.select().where(TowWaypoints.tow == haul.operational_segment).order_by(
                        TowWaypoints.date_time.asc()).limit(1)
                    if len(waypoints) == 1:
                        start_date_time = waypoints.first().date_time
                        item["haulStart"] = arrow.get(start_date_time).to('US/Pacific').format("MM/DD HH:mm:ss")
                    else:
                        if tow.activation_datetime:
                            item["haulStart"] = arrow.get(tow.activation_datetime).to('US/Pacific').format("MM/DD HH:mm:ss")

                    # Get the datetime of the last waypoint
                    waypoints = TowWaypoints.select().where(TowWaypoints.tow == haul.operational_segment).order_by(
                        TowWaypoints.date_time.desc())
                    if len(waypoints) > 1:
                        end_date_time = waypoints.first().date_time
                        item["haulEnd"] = arrow.get(end_date_time).to('US/Pacific').format("MM/DD HH:mm:ss")
                    else:
                        if tow.deactivation_datetime:
                            item["haulEnd"] = arrow.get(tow.deactivation_datetime).to('US/Pacific').format(
                                "MM/DD HH:mm:ss")

                    msg = ""
                    self.haulDataUpdated.emit(item)
                    # results.append(item)

            except BreakIt:
                self._app.settings.set_wheelhouse_proxy(db_file=None)
                logging.info(f"BreakIt error: {msg}")
                status = False
                self.breakItEncountered.emit(msg)
                return status, msg, results

            except Exception as ex:
                self._app.settings.set_wheelhouse_proxy(db_file=None)
                msg = f"{ex}"
                logging.info(f'Error loading the Data Completeness wheelhouse data: {msg}')
                status = False
                return status, msg, results

        end = arrow.now()
        logging.info('\t\tDataCompleteness Wheelhouse DB Population, Elapsed time, wheelhouse DBs: {0:.1f}s'.format((end - start).total_seconds()))

        # Set the status to true and return the results list, thus finishing the thread
        status = True
        return status, msg, results


class LoadHaulsThread(QObject):

    loadingCompleted = pyqtSignal(bool, str)
    haulLoaded = pyqtSignal(int, QVariant, arguments=["index", "loadDate"])

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self._is_running = False
        self._app = kwargs["app"]
        self._functions = CommonFunctions()
        self._items = kwargs["items"]

    def stop(self):
        """
        Method to interrupt the thread, stopping it from running
        :return:
        """
        self._is_running = False

    def run(self):
        self._is_running = True
        status, msg = self._load_hauls()
        self.loadingCompleted.emit(status, msg)

    def _load_hauls(self):
        """
        Method to actually load the haul into the database
        :return:
        """
        """
        Method to load new haul data to the FRAM_CENTRAL database.  This will gather all of the hauls that have a load
        column = yes and then load those into the database.  This loads data into the following tables:
            OPERATIONS
            OPERATION_DETAILS
            EVENTS
            COMMENTS

        :param item:
        :return:
        """
        if isinstance(self._items, QJSValue):
            self._items = self._items.toVariant()

        logging.info(f"\titems = {self._items}")

        hauls_dict = OrderedDict(sorted(self._items.items(), key=lambda x: x[0]))

        # TODO Todd Hay - Consider prompting the user if the opsLoadStatus is populated to see if she/he wants to
        # perform a reload operation or skip reloading
        hauls_dict = OrderedDict({int(k): v for k, v in hauls_dict.items() if (v["opsLoadStatus"] is None or v["opsLoadStatus"] == "")})



        logging.info(f"\thauls_dict = {hauls_dict}")

        status = False
        msg = ""

        # op_pt_meas_dict = {"Surface Temperature degs C": }

        # List to keep track of which hauls are actually loaded, so we can roll these back out if something fails
        hauls_loaded = []

        # Get parent operation leg record from Wheelhouse DB and link back to FRAM_CENTRAL
        # items_only = [x["item"] for x in self._items]
        # indexes = [x["index"] for x in self._items]
        # dbs = list(set([x["haulDatabase"] for x in items]))

        dbs = list(set([v["haulDatabase"] for k, v in hauls_dict.items()]))

        logging.info(f"\tdbs = {dbs}")
        for db_file in dbs:

            try:

                logging.info(f"\tLoading hauls, examining database: {os.path.basename(db_file)}, {arrow.now().format('HH:mm:ss')}")

                self._app.settings.set_wheelhouse_proxy(db_file=db_file)
                cruise_id = self._functions.get_cruise_id(vessel=self._app.settings.vessel, year=self._app.settings.year)
                legs = OperationsFlattenedVw.select().where(OperationsFlattenedVw.operation_type == "Leg",
                                                            OperationsFlattenedVw.cruise == cruise_id)
                logging.info(f"\tcruise_id={cruise_id}")

                project_lu_id = Lookups.get(Lookups.type == "Project",
                                            Lookups.value == "West Coast Groundfish Slope/Shelf Bottom Trawl Survey").lookup
                haul_lu_id = Lookups.get(Lookups.type == "Operation", Lookups.value == "Tow").lookup

                hauls = {k: v for k, v in hauls_dict.items() if v["haulDatabase"] == db_file}
                for k, v in hauls.items():

                    if not self._is_running:
                        raise BreakIt

                    # Insert Haul record into OPERATIONS table -- DONE
                    logging.info(f"\tLoading haul {v['haul']}, {arrow.now().format('HH:mm:ss')}")
                    try:

                        if not self._is_running:
                            msg = "Broke running at haul information for haul {0}".format(v["haul"])
                            raise BreakIt

                        wh_haul = WhOperationalSegment.get(WhOperationalSegment.name == v["haul"])
                        leg_name = wh_haul.parent_segment.name.strip("Leg ")
                        leg = legs.select().where(OperationsFlattenedVw.leg_name == leg_name).first()
                        logging.info(f"\tleg_name = {leg_name}, leg = {leg}")
                        leg_id = None
                        if leg:
                            leg_id = leg.leg
                        else:
                            status = False
                            msg = "Failed loading hauls as a leg was not found"
                            return status, msg

                        fpc_id = self._functions.get_personnel(op=wh_haul, position="FPC")
                        logging.info(f"Haul level FPC_ID: {fpc_id}, op fpc: {wh_haul.fpc}, op seg id: {wh_haul.operational_segment}")

                        if fpc_id is None:
                            fpc_id = self._functions.get_personnel(op=wh_haul.parent_segment, position="FPC")
                            logging.info(f"Haul level FPC not found, selecting cruise FPC: {fpc_id}")

                        sci1_id = self._functions.get_personnel(op=wh_haul.parent_segment, position="Scientist1")
                        logging.info(f"sci1 = {sci1_id}")

                        sci2_id = self._functions.get_personnel(op=wh_haul.parent_segment, position="Scientist2")
                        logging.info(f"sci2 = {sci2_id}")

                        if v["linked"] == "":
                            v["linked"] = None

                        haul_op, _ = Operations.get_or_create(
                            parent_operation=leg_id,
                            operation_type_lu=haul_lu_id,
                            operation_name=v["haul"],
                            vessel=leg.vessel,
                            project_lu=project_lu_id,
                            defaults = {
                                "fpc": fpc_id,
                                "scientist_1": sci1_id,
                                "scientist_2": sci2_id,
                                "alternate_operation_name": v["linked"]
                            }
                        )
                    except Exception as ex:
                        msg = 'Error inserting the haul: {0} > {1}'.format(v["haul"], ex)
                        logging.error(msg)
                        return status, msg
                    logging.info(f"\toperations table loaded, {arrow.now().format('HH:mm:ss')}")

                    # Insert Waypoints into EVENTS table -- DONE
                    try:
                        if not self._is_running:
                            msg = "Broke running at waypoints for haul {0}".format(v["haul"])
                            raise BreakIt

                        if wh_haul:
                            waypoints = TowWaypoints.select().where(TowWaypoints.tow == wh_haul.operational_segment)

                            for wp in waypoints:
                                # wp_type = Lookups.get(Lookups.type == "Event",
                                #                       Lookups.value == "Bottom Trawl Waypoint",
                                #                       Lookups.subvalue == wp.tow_waypoint_type.type)
                                wp_type = GroupMemberVw.get(
                                    GroupMemberVw.lookup_type_grp == 'Event',
                                    GroupMemberVw.group_name == 'Bottom Trawl Waypoint',
                                    GroupMemberVw.lookup_value_member == wp.tow_waypoint_type.type).lookup_id_member

                                event_op, _ = Events.get_or_create(
                                    operation=haul_op.operation,
                                    event_type_lu=wp_type,
                                    defaults = {
                                        "event_datetime": wp.date_time,
                                        "event_latitude": self._functions.lat_or_lon_to_dd(wp.latitude),
                                        "event_longitude": self._functions.lat_or_lon_to_dd(wp.longitude)
                                    }
                                )
                    except Exception as ex:
                        msg = 'Error inserting the waypoints: {0} > {1}'.format(v["haul"], ex)
                        logging.info(msg)
                        return status, msg
                    logging.info(f"\tevents table loaded, {arrow.now().format('HH:mm:ss')}")

                    # Insert Haul Details into OPERATION_ATTRIBUTES + COMMENTS table -- DONE
                    try:
                        if not self._is_running:
                            msg = "Broke running at haul details for haul {0}".format(v["haul"])
                            raise BreakIt

                        if wh_haul:

                            rules = ReportingRules.select().where(ReportingRules.rule_type == "atsea")

                            template = {"operation": haul_op.operation, "is_best_value": True,
                                        "attribute_numeric": None, "attribute_alpha": None}

                            details = TowDetails.select().where(TowDetails.tow == wh_haul.operational_segment)
                            for detail in details:
                                # logging.info('keys: {0}'.format(detail._meta.fields.keys()))
                                fc_inserts = []

                                for rule in rules:

                                    if rule.source_db_field_name.lower() in detail._meta.fields.keys():
                                        new_dict = deepcopy(template)
                                        new_dict["reporting_rules"] = rule.reporting_rule
                                        attribute_type = "attribute_numeric" if rule.is_numeric else "attribute_alpha"
                                        if getattr(detail, rule.source_db_field_name.lower()) is not None and \
                                                getattr(detail, rule.source_db_field_name.lower()) != "":
                                            new_dict[attribute_type] = Decimal(str(getattr(detail, rule.source_db_field_name.lower()))) \
                                                if attribute_type == "attribute_numeric" \
                                                else getattr(detail, rule.source_db_field_name.lower())

                                            # logging.info('insert: {0}'.format(new_dict))

                                            if new_dict:
                                                fc_inserts.append(new_dict)

                                if fc_inserts:
                                    with self._app.settings._database.atomic():
                                        OperationAttributes.insert_many(fc_inserts).execute()

                                # Insert PERFORMANCE_COMMENTS
                                if getattr(detail, "performance_comments") is not None and \
                                                getattr(detail, "performance_comments") != "":
                                    tow_comment_id = Lookups.get(Lookups.type == "Comment",
                                                                 Lookups.value == "Operation",
                                                                 Lookups.subvalue == "Tow").lookup

                                    comment, _ = Comments.get_or_create(
                                                    operation=haul_op.operation,
                                                    comment=getattr(detail, "performance_comments"),
                                                    date_time=arrow.get(detail.deactivation_datetime).to("US/Pacific").isoformat(),
                                                    comment_type_lu=tow_comment_id
                                                )
                    except Exception as ex:
                        msg = 'Error inserting the haul details: {0} > {1}'.format(v["haul"], ex)
                        logging.info(msg)
                        return status, msg
                    logging.info(f"\toperations_attribute table loaded, {arrow.now().format('HH:mm:ss')}")

                    # Insert Haul Impact Factors into OPERATION_PERFORMANCE table -- DONE
                    try:
                        if not self._is_running:
                            msg = "Broke running at haul impact factors for haul {0}".format(v["haul"])
                            raise BreakIt

                        if wh_haul:
                            factors = TowImpactFactors.select().where(
                                TowImpactFactors.tow == wh_haul.operational_segment
                            )
                            for factor in factors:
                                fc_factor_id = Lookups.get(
                                    Lookups.type == "Tow Performance",
                                    Lookups.bottom_trawl == factor.impact_factor
                                ).lookup
                                is_unsat = True if factor.is_unsat_factor.lower() == "y" else False

                                pd, _ = PerformanceDetails.get_or_create(
                                    operation=haul_op.operation,
                                    performance_type_lu=fc_factor_id,
                                    defaults = {
                                        "is_unsat_factor": is_unsat
                                    }
                                )
                                # PerformanceDetails.insert(
                                #     operation=haul_op.operation,
                                #     is_unsat_factor=is_unsat,
                                #     performance_type_lu=fc_factor_id
                                # ).execute()
                    except Exception as ex:
                        msg = 'Error inserting the haul impact factors: {0} > {1}'.format(v["haul"], ex)
                        logging.info(msg)
                        return status, msg
                    logging.info(f"\tperformance_details table loaded, {arrow.now().format('HH:mm:ss')}")

                    # Insert Comments into the COMMENTS table -- DONE
                    try:
                        if not self._is_running:
                            msg = "Broke running at comments for haul {0}".format(v["haul"])
                            raise BreakIt

                        if wh_haul:
                            comments = FpcLog.select()\
                                .where(FpcLog.operational_segment == wh_haul.operational_segment)

                            tow_comment_id = Lookups.get(Lookups.type == "Comment",
                                                         Lookups.value == "Operation",
                                                         Lookups.subvalue == "Tow").lookup
                            for comment in comments:

                                    fc_comment, _ = Comments.get_or_create(
                                        operation=haul_op.operation,
                                        comment=comment.entry,
                                        date_time=arrow.get(comment.date_time).to("US/Pacific").isoformat(),
                                        comment_type_lu=tow_comment_id
                                    )
                    except Exception as ex:
                        msg = 'Error inserting the comments: {0} > {1}'.format(v["haul"], ex)
                        logging.info(msg)
                        return status, msg
                    logging.info(f"\tcomments table loaded, {arrow.now().format('HH:mm:ss')}")

                    logging.info(f'Haul successfully loaded and signal emitted: {v["haul"]}, {arrow.now().format("HH:mm:ss")}')
                    self.haulLoaded.emit(k, arrow.now().format("MM/DD HH:mm:ss"))
                    hauls_loaded.append(haul_op.operation)

            except BreakIt:

                # Delete the current haul data
                try:

                    self._app.settings.set_wheelhouse_proxy(db_file=None)

                    if haul_op:

                        # Delete Comments
                        Comments.delete().where(Comments.operation == haul_op.operation).execute()

                        # Delete Performance Details
                        PerformanceDetails.delete().where(PerformanceDetails.operation == haul_op.operation).execute()

                        # Delete Operation_Attributes
                        OperationAttributes.delete().where(OperationAttributes.operation == haul_op.operation).execute()

                        # Delete Events
                        Events.delete().where(Events.operation == haul_op.operation).execute()

                        # Delete Operation
                        Operations.delete().where(Operations.operation == haul_op.operation).execute()

                    self.haulLoaded.emit(int(k), None)

                    haul_op = None
                    return False, "Processing halted"

                    break

                except Exception as ex:

                    msg = f"Unable to delete the current working haul from the data, please remove manually: {haul_op.operation}"
                    logging.error(msg)
                    return False, msg


        status = True
        if msg == "":
            msg = "Success in loading all of the hauls"
        return status, msg


class LoadSensorSerialDataThread(QObject):

    loadingCompleted = pyqtSignal(bool, str, QVariant, str, QVariant)
    # haulLoaded = pyqtSignal(int, QVariant, arguments=["index", "loadDate"])
    haulSensorSerialDataLoaded = pyqtSignal(int, QVariant, arguments=["index", "loadDate"])
    updateHaulSerialStatus = pyqtSignal(str, arguments=["msg"])
    # loadingError = pyqtSignal(str, arguments=["msg",])

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self._is_running = False
        self._app = kwargs["app"]
        self._functions = CommonFunctions()
        self._items = kwargs["items"].toVariant() if isinstance(kwargs["items"], QJSValue) else kwargs["items"]
        self._load_status = kwargs["loadStatus"]

    def stop(self):
        """
        Method to interrupt the thread, stopping it from running
        :return:
        """
        self._is_running = False

    def run(self):
        self._is_running = True
        status, msg, elapsed_time = self._load_data()
        self.loadingCompleted.emit(status, msg, self._items, self._load_status, elapsed_time)

    def _load_data(self):
        """
        Method to actually load the haul into the database
        :return:
        """
        """
        Method to load new haul-level sensor data to the FRAM_CENTRAL database.  This will gather all of the sensor
        data for given hauls that have a load
        column = yes and then load those into the database.  This loads data into the following tables:
            MEASUREMENT_STREAM
            OPERATION_MEASUREMENTS

        :param item:
        :return:
        """

        # TEST TEST TEST - Only for trying to load the Logger data only
        # status = True
        # msg = "success"
        # return status, msg, None
        logging.info(f"Data loading commenced")

        if isinstance(self._items, QJSValue):
            self._items = self._items.toVariant()

        items = self._items.items()

        haul_op = None

        # TODO Todd Hay Check load status to determine if I should only load new data, or drop old and reload

        method_start = arrow.now()

        status = False
        msg = ""

        insert_template = {"raw_string": None, "date_time": None, "reading_numeric": None,
                           "reading_alpha": None, "measurement_stream": None, "is_not_valid": False}

        # Get all of the serial parsing rules
        # parsing_rules = ParsingRulesVw.select() \
        #     .distinct([ParsingRulesVw.equipment, ParsingRulesVw.line_starting,
        #                ParsingRulesVw.reading_type, ParsingRulesVw.reading_basis,
        #                ParsingRulesVw.reading_type_code]) \
        #     .where(ParsingRulesVw.is_parsed)\
        #     .order_by(ParsingRulesVw.equipment, ParsingRulesVw.line_starting)

        # TODO Todd Hay - Add in where clause or serial_or_logger=="Serial" once Beth has added to parsing_rules_vw

        # .distinct([ParsingRulesVw.equipment, ParsingRulesVw.line_starting,
        #            ParsingRulesVw.reading_type, ParsingRulesVw.reading_basis,
        #            ParsingRulesVw.reading_type_code]) \
        parsing_rules = ParsingRulesVw.select() \
            .where(ParsingRulesVw.is_parsed,
                   ParsingRulesVw.logger_or_serial == "serial")\
            .order_by(ParsingRulesVw.equipment, ParsingRulesVw.line_starting, ParsingRulesVw.reading_type,
                      ParsingRulesVw.reading_basis, ParsingRulesVw.reading_type_code)\
            .distinct()

        logging.info(f"\t\tParsing rules retrieved")

        if DEBUG:
            try:
                logging.info(f"\t\tparsing_rules count: {parsing_rules.count()}")
            except Exception as ex:
                logging.info(f"\t\tError in retrieving parsing rules: {ex}")

        db_count = 0
        for k, v in sorted(items):
            if "sensorDatabase" in v and v["sensorDatabase"] != "":
                self._app.settings.set_sensors_proxy(db_file=v["sensorDatabase"])
                self._app.settings.set_wheelhouse_proxy(db_file=v["haulDatabase"])

                try:

                    update_msg = "Sensor Serial Data Loading, haul: {0}".format(v["haul"])
                    logging.info(f"{update_msg}")
                    self.updateHaulSerialStatus.emit(update_msg)

                    try:
                        haul_op = OperationsFlattenedVw.get(OperationsFlattenedVw.tow_name == v["haul"])
                        if DEBUG:
                            logging.info(f"\t\thaul_op retrieved from OperationsFlattenedVw")

                    except Exception as ex:
                        msg = f"\t\tHaul {v['haul']} has not been loaded, please load hauls before loading sensor data"
                        logging.info(msg)
                        status = False
                        return status, msg, None

                    if not self._is_running:
                        raise BreakIt

                    op_file_mtx = OperationFilesMtx.select(OperationFilesMtx)\
                        .join(OperationFiles)\
                        .where(OperationFilesMtx.operation == haul_op.cruise,
                               OperationFiles.final_path_name == v["sensorDatabase"]).first()

                    if DEBUG:
                        logging.info(f"\t\top_file_mtx found successfully")

                    """
                    If we're reloading the data for this haul, then delete all of the associated measurement_streams
                    and operation_measurements
                    """

                    logging.info(f"\t\tload status = {self._load_status}")
                    if self._load_status == "reload":
                        if DEBUG:
                            logging.info(f"\t\treloading data, checking for measurement streams")

                        ms = MeasurementStreams.select()\
                            .join(ParsingRulesVw, on=(ParsingRulesVw.parsing_rules==MeasurementStreams.equipment_field))\
                            .where(MeasurementStreams.operation == haul_op.operation,
                                   ParsingRulesVw.logger_or_serial == "serial")
                        OperationMeasurements.delete().where(OperationMeasurements.measurement_stream << ms).execute()
                        OperationMeasurementsErr.delete().where(OperationMeasurementsErr.measurement_stream << ms).execute()
                        MeasurementStreams.delete().where(MeasurementStreams.measurement_stream << ms).execute()

                        if DEBUG:
                            logging.info(f"\t\told measurement streams found and deleted")

                    """
                    Create all of the required measurement_streams

                    Key elements to populate:
                    - operation_id - haul_op.operation
                    - equipment_id - parsing_rules_vw
                    - data_field_id - parsing_rules_vw
                    - operation_files_mtx_id - op_file_mtx object above

                    Iterate through all of the parsing rules, and create measurement streams for each one of them for
                    every haul.  Gosh, that seems really verbose.
                    """
                    streams = []

                    if DEBUG:
                        logging.info(f"\t\tbefore for statement for parsing_rules, the count is: {parsing_rules.count()}")
                        logging.info(f"\t\tparsing_rules = {parsing_rules}")
                    for rule in parsing_rules:

                        update_msg = "Gathering parsing rules into streams"
                        if DEBUG:
                            logging.info(f"\t\t{update_msg} > {model_to_dict(rule)}")

                        self.updateHaulSerialStatus.emit(update_msg)

                        if not self._is_running:
                            raise BreakIt

                        # TODO Todd Hay - Fix by removing attachment position, but adding what for PSIMP measurements?  channel # ?
                        stream = {"operation": haul_op.operation,
                                  "equipment_field": rule.parsing_rules,
                                  "operation_files_mtx": op_file_mtx.operation_files_mtx}
                        streams.append(stream)

                    if DEBUG:
                        logging.info(f"\t\tBefore reading/creating the measurement streams, streams count = {len(streams)}")
                    if streams:
                        with self._app.settings._database.atomic():

                            update_msg = "Inserting measurement streams"
                            if DEBUG:
                                logging.info(f"\t\t{update_msg}")
                            self.updateHaulSerialStatus.emit(update_msg)

                            ms_count = MeasurementStreams.select().where(MeasurementStreams.operation == haul_op.operation).count()

                            if self._load_status == "reload" or ms_count == 0:
                                MeasurementStreams.insert_many(streams).execute()
                            else:
                                for stream in streams:

                                    if not self._is_running:
                                        raise BreakIt

                                    MeasurementStreams.get_or_create(**stream)

                    # Return all of the measurement_streams for this particular operation that were just inserted
                    update_msg = "Retrieving measurement streams"
                    if DEBUG:
                        logging.info(f"\t\t{update_msg}")
                    self.updateHaulSerialStatus.emit(update_msg)

                    streams = MeasurementStreams.select(MeasurementStreams,ParsingRulesVw)\
                        .join(ParsingRulesVw, on=(MeasurementStreams.equipment_field == ParsingRulesVw.parsing_rules).alias('rules'))\
                        .where(MeasurementStreams.operation == haul_op.operation,
                               ParsingRulesVw.logger_or_serial == "serial",
                               ParsingRulesVw.is_parsed)

                    """
                    Get the mapping from the wheelhouse database between the wheelhouse deployed_equipment_id and equipment_id
                    as the FRAM_CENTRAL database only retains the equipment_id
                    """
                    update_msg = "Gathering deployed equipment IDs"
                    if DEBUG:
                        logging.info(f"\t\t{update_msg}")
                    self.updateHaulSerialStatus.emit(update_msg)

                    deployed_equipment = DeployedEquipment.select(DeployedEquipment.equipment, DeployedEquipment.deployed_equipment).dicts()
                    deployed_equipment = {x["deployed_equipment"]: x["equipment"] for x in deployed_equipment}
                    logging.info(f'\t\tdeployed equipment: {deployed_equipment}')

                    # Get the haul_start and haul_end
                    update_msg = "Getting the haul start and end date/times"
                    self.updateHaulSerialStatus.emit(update_msg)

                    haul_start = arrow.get(v["haulStart"], 'MM/DD HH:mm:ss').replace(year=int(self._app.settings.year), tzinfo="US/Pacific").shift(minutes=-1)
                    haul_end = arrow.get(v["haulEnd"], 'MM/DD HH:mm:ss').replace(year=int(self._app.settings.year), tzinfo="US/Pacific").shift(minutes=+1) \
                        if "haulEnd" in v and v["haulEnd"] != "" else haul_start.shift(minutes=+32)

                    """
                    Get one string from EnviroNetRawStrings, check time zone and adjust haul_start/haul_end to the same time zone
                    for selection
                    """
                    sample = EnviroNetRawStrings.select().limit(1)
                    if sample.count() == 1:
                        sample = sample.first()
                        sample_tz = arrow.get(sample.date_time).tzinfo
                        haul_start = haul_start.to(sample_tz)
                        haul_end = haul_end.to(sample_tz)

                        if not self._is_running:
                            raise BreakIt

                        update_msg = "Gathering raw strings"
                        if DEBUG:
                            logging.info(f"\t\t{update_msg}")
                        self.updateHaulSerialStatus.emit(update_msg)

                        logging.info(f"\t\thaul_start = {haul_start.isoformat()}, haul_end = {haul_end.isoformat()}")

                        # Gather all of the strings that fall within the haul start/end timeframe, returning as a list of dicts
                        logging.info(f"\t\tretrieving serial data")
                        strings = EnviroNetRawStrings.select().where(EnviroNetRawStrings.date_time >= haul_start.isoformat(),
                                                                     EnviroNetRawStrings.date_time <= haul_end.isoformat()).dicts()

                        logging.info(f"strings count = {len(strings)}")

                        sents = list(set([x.rules.line_starting for x in streams]))
                        logging.info(f"streams = {sents}")

                        # Start working through groups of the strings, grouped by the line_starting
                        current_line_starting = ""
                        current_equipment_id = -1

                        for stream in streams:

                            if not self._is_running:
                                raise BreakIt

                            update_msg = "Haul {0}, Parsing {1}, {2}, {3}".format(v["haul"],
                                                                        stream.rules.line_starting,
                                                                        stream.rules.equipment,
                                                                        stream.rules.reading_type)
                            # logging.info(f"\t\t{update_msg}")

                            if DEBUG:
                                logging.info("\t\t" + update_msg)
                            self.updateHaulSerialStatus.emit(update_msg)

                            # inner_start = arrow.now()

                            # Check if the load status is "load new" - if so, skip this iteration if any
                            # operation_measurements exist for this stream
                            # logging.info(f"\t\tload_status = {self._load_status}")

                            if self._load_status == "load new":

                                om_count = OperationMeasurements.select().where(OperationMeasurements.measurement_stream == stream.measurement_stream).count()

                                logging.info(f"\t\top_meas_count = {om_count}")

                                if om_count > 0:
                                    continue

                            fast_list = []
                            insert_list = []
                            template = deepcopy(insert_template)
                            template["measurement_stream"] = stream.measurement_stream

                            if current_line_starting != stream.rules.line_starting or \
                                current_equipment_id != stream.rules.equipment:

                                if not self._is_running:
                                    raise BreakIt

                                # logging.info(f"\t\tbefore getting lines:  {stream.rules.line_starting}, {stream.rules.equipment}")

                                # d_equip = list(set([x["deployed_equipment"] for x in strings]))
                                # logging.info(f"\t\td_equip = {d_equip}")
                                # logging.info(f"\t\ttop 5 = {strings[:5]}")

                                lines = [x for x in strings if x["raw_strings"] is not None and \
                                         stream.rules.line_starting in x["raw_strings"] and \
                                         x["deployed_equipment"] is not None and \
                                         stream.rules.equipment == deployed_equipment[x["deployed_equipment"]]
                                         ]

                                # logging.info(f"\t\tafter getting lines")

                                # TODO Todd Hay - the issue is that the stream.rules.equipment != deployed_equipment[x['deployed_equipment']]
                                # lines = [x for x in strings if stream.rules.line_starting in x["raw_strings"]]

                                logging.info(f"{stream.rules.line_starting} > stream eqp: {stream.rules.equipment} "
                                             f" > {len(lines)} sentences")

                            # Now I have all of the lines for the given stream + equipment ID, time to parse
                            if len(lines) > 0:

                                # Get the proper field
                                if stream.rules.fixed_or_delimited.lower() == "delimited":

                                    update_msg += ", Sentence Count: {0}".format(len(lines))
                                    self.updateHaulSerialStatus.emit(update_msg)

                                    delim = stream.rules.delimiter

                                    if delim == "[Space]":
                                        delim = " "

                                    pos = stream.rules.field_position

                                    # insert_list = [deepcopy(template) for x in lines]

                                    if not self._is_running:
                                        raise BreakIt

                                    # VALUES
                                    start = arrow.now()
                                    # raw_split = [x["raw_strings"].split(delim) for x in lines]

                                    if delim == " " or delim == "[Space]" or delim.lower() == "[space]":
                                        raw_split = [[x["enviro_net_raw_strings"], x["date_time"],
                                                  x["raw_strings"].split()]
                                                 for x in lines]
                                    else:
                                        raw_split = [[x["enviro_net_raw_strings"], x["date_time"],
                                                  x["raw_strings"].split(delim)]
                                                 for x in lines]

                                    # logging.info(f"\t\traw_split = {raw_split}")

                                    # Remove the checksum at the end of the string if it exists
                                    for x in raw_split:
                                        x[2][-1] = x[2][-1].split('*')[0] if "*" in x[2][-1] else x[2][-1]

                                    logging.info(f"\t\tReading type = {stream.rules.reading_type}, Field_format = {stream.rules.field_format}")

                                    # TODO Todd Hay - Why is the boolean not working, have Beth fix parsing_rules_vw is_numeric
                                    # if "0" in stream.rules.field_format:
                                    if stream.rules.is_numeric:

                                        # PI44 - Further reduce sentences based on the channel number and reading_type_code
                                        reading_code_pos = stream.rules.reading_type_position
                                        channel_pos = stream.rules.channel_position
                                        if stream.rules.line_starting == "$PSIMP,D1" and channel_pos and reading_code_pos:
                                            # logging.info(f'\t\t\tbefore channel: {len(raw_split)}')
                                            raw_split = [x for x in raw_split if reading_code_pos-1 < len(x[2]) and channel_pos-1 < len(x[2]) \
                                                         and x[2][reading_code_pos-1] == stream.rules.reading_type_code \
                                                         and x[2][channel_pos-1] == stream.rules.channel]
                                            # logging.info(f'\t\t\tafter channel: {len(raw_split)}')

                                        # logging.info('\t\tfinished channel/reading_code')

                                        # Quality Indicator - Only get those with a value of 22 (per quality_status field) for PI44
                                        if self._functions.is_float(stream.rules.quality_status) and stream.rules.line_starting == "$PSIMP,D1":
                                            # logging.info(f"{haul_start} >>> {haul_end}")

                                            stat_pos = stream.rules.quality_status_position
                                            # logging.info(f'raw_split length: {len(raw_split)}')
                                            raw_split = [x for x in raw_split if stat_pos - 1 < len(x[2]) and x[2][stat_pos - 1] == stream.rules.quality_status]
                                            # logging.info(f'raw_split length: {len(raw_split)}')

                                        # PX - Further parsing - Added 20191106
                                        if stream.rules.line_starting == "$PSIMTV80":

                                            if stream.rules.reading_type_code\
                                                and stream.rules.measurement_to\
                                                and stream.rules.measurement_to_position\
                                                and stream.rules.measurement_from\
                                                and stream.rules.measurement_from_position:

                                                reading_type_pos = stream.rules.reading_type_position
                                                meas_from_pos = stream.rules.measurement_from_position
                                                meas_to_pos = stream.rules.measurement_to_position
                                                raw_split = [x for x in raw_split
                                                    if reading_type_pos - 1 < len(x[2])
                                                    and meas_from_pos-1 < len(x[2])
                                                    and meas_to_pos-1 < len(x[2])
                                                    and x[2][reading_type_pos - 1] == stream.rules.reading_type_code
                                                    and x[2][meas_from_pos - 1] == stream.rules.measurement_from
                                                    and x[2][meas_to_pos - 1] == stream.rules.measurement_to]
                                                logging.info(f"\t\tPX Spread Distance raw_split for $PSIMTV80 > {stream.rules.reading_basis} > "
                                                             f"{stream.rules.measurement_from}, {stream.rules.measurement_to}")

                                            elif stream.rules.reading_type_code\
                                                    and stream.rules.measurement_from\
                                                    and stream.rules.measurement_from_position:
                                                # Only the measurement_from_position exists, i.e. measurement_to is blank

                                                reading_type_pos = stream.rules.reading_type_position
                                                meas_from_pos = stream.rules.measurement_from_position
                                                raw_split = [x for x in raw_split
                                                    if reading_type_pos - 1 < len(x[2])
                                                    and meas_from_pos-1 < len(x[2])
                                                    and x[2][reading_type_pos - 1] == stream.rules.reading_type_code
                                                    and x[2][meas_from_pos - 1] == stream.rules.measurement_from]
                                                logging.info(f"\t\tPX Spread Distance raw_split for $PSIMTV80 > "
                                                             f"{stream.rules.reading_basis} > "
                                                             f"{stream.rules.measurement_from}")

                                        # Convert to a floating point value data type
                                        clean_data = [{"raw_string": x[0], "date_time": x[1], "reading_numeric": float(x[2][pos-1])}
                                                      for x in raw_split
                                                      if pos - 1 < len(x[2]) and self._functions.is_float(x[2][pos - 1])]

                                    else:
                                        if "DDMM.MM" in stream.rules.field_format:

                                            if stream.rules.hemisphere_position:
                                                clean_data = [{"raw_string": x[0], "date_time": x[1],
                                                               "reading_numeric": self._functions.convert_lat_lon_to_dd(
                                                            x[2][pos-1],
                                                            stream.rules.reading_type,
                                                            x[2][stream.rules.hemisphere_position-1])}
                                                              for x in raw_split
                                                          if pos - 1 < len(x[2]) and stream.rules.hemisphere_position-1 < len(x[2])]
                                            else:
                                                clean_data = [{"raw_string": x[0], "date_time": x[1],
                                                               "reading_numeric": self._functions.convert_lat_lon_to_dd(
                                                                                    input_str=x[2][pos-1],
                                                                                    type=stream.rules.reading_type,
                                                                                    hemisphere=x[2][pos])}
                                                              for x in raw_split if pos - 1 < len(x[2]) and pos < len(x[2])]
                                            clean_data = [x for x in clean_data if x["reading_numeric"] is not None]

                                        # TODO Todd Hay - How do we actually want to store a time only item???
                                        elif "hhmmss" in stream.rules.field_format.lower():
                                            clean_data = [{"raw_string": x[0], "date_time": x[1], "reading_alpha": x[2][pos-1]}
                                                          for x in raw_split
                                                          if pos-1 < len(x[2]) and self._functions.is_float(x[2][pos-1])]
                                            clean_data = [x for x in clean_data if x["reading_alpha"] is not None]

                                        else:
                                            clean_data = [{"raw_string": x[0], "date_time": x[1], "reading_alpha": x[2][pos-1]}
                                                          for x in raw_split
                                                          if pos-1 < len(x[2])]
                                            clean_data = [x for x in clean_data if x["reading_alpha"] is not None]

                                    end = arrow.now()
                                    if DEBUG:
                                        logging.info(f"\t\tclean_data just created, size = {len(clean_data)}")

                                    if not self._is_running:
                                        raise BreakIt

                                    if len(clean_data) > 0:

                                        # logging.info(f"\t\tclean_data samples:\n\t\t{clean_data[0]}\n\t\t{clean_data[1]}\n\t\t{clean_data[2]}")
                                        # logging.info(f"raw_split[0]: {raw_split[0]}")

                                        # DATE_TIMES
                                        for cd in clean_data:
                                            if cd is not None:
                                                cd["date_time"] = self._functions.fastStrptime(cd["date_time"]).to("US/Pacific").isoformat() if "date_time" in cd else None

                                        if not self._is_running:
                                            raise BreakIt

                                        insert_list = [deepcopy(template)] * len(clean_data)
                                        insert_list = [{**insert_list[i], **clean_data[i]} for i in range(len(clean_data)) if clean_data[i] is not None]

                                        # logging.info(f"\t\tinsert_list len: {len(insert_list)}")
                                        # if len(insert_list) > 0:
                                        #     logging.info(f"\t\tinsert_list[0]: {insert_list[0]}")

                                        insert_list = [x for x in insert_list if x["reading_numeric"] is not None or x["reading_alpha"] is not None]

                                    # for d, value, dt, raw_string_id in zip(insert_list, values, date_times, raw_string_ids):
                                    #     # TODO Todd Hay - Fix the reading_numeric + reading_alpha once the boolean fields are fixed
                                    #     d["reading_numeric"] = value if isinstance(value, float) else None
                                    #     d["reading_alpha"] = value if isinstance(value, str) else None
                                    #     d["is_not_valid"] = True if not value else False
                                    #     d["date_time"] = dt
                                    #     d["raw_string"] = raw_string_id

                                    # logging.info(f'insert_list sample:\n{insert_list[0]}\n{insert_list[1]}\n{insert_list[-1]}')
                                    # logging.info(f"{len(insert_list)}")


                                    # logging.info('\t\tElapsed time, merging: {0:.1f}s'.format((end - start).total_seconds()))
                                    # return

                                    # BULK INSERTS
                                    start = arrow.now()
                                    with self._app.settings._database.atomic():
                                        # OperationMeasurements.insert_many(insert_list).execute()

                                        for idx in range(0, len(insert_list), 5000):

                                            if not self._is_running:
                                                raise BreakIt

                                            OperationMeasurements.insert_many(insert_list[idx:idx+5000]).execute()

                                    # BULK INSERT TESTING - psycopg copy_expert test
                                    # ---------------------------------------------------------------------------------
                                    # TEST
                                    # ---------------------------------------------------------------------------------
                                    # insert_template = {"raw_file": None, "raw_string": None, "date_time": None,
                                    #                    "reading_numeric": None,
                                    #                    "reading_alpha": None, "measurement_stream": None,
                                    #                    "is_not_valid": False}

                                    # rawfileid = OperationFiles.get(
                                    #     OperationFiles.final_path_name == v["sensorDatabase"]).operation_file
                                    # rawfile = [rawfileid] * len(values)
                                    # mstream = [stream.measurement_stream] * len(values)
                                    # reading_numerics = [x if stream.rules.is_numeric else None for x in values]
                                    # reading_alpha = [x if not stream.rules.is_numeric else None for x in values]
                                    # valids = [True if not x else False for x in values]
                                    # val_lu_id = [None] * len(values)
                                    #
                                    # # Ref: http://stackoverflow.com/questions/10592674/updating-a-list-of-python-dictionaries-with-a-key-value-pair-from-another-list
                                    # params = list(zip(rawfile, raw_string_ids, date_times, reading_numerics,
                                    #                 reading_alpha, mstream, valids, val_lu_id))
                                    # for i in range(3):
                                    #     logging.info('params[{0}]: {1}'.format(i, params[i]))
                                    #
                                    # sql = """
                                    #     INSERT INTO OPERATION_MEASUREMENTS(raw_file_id, raw_string_id,
                                    #         date_time, reading_numeric, reading_alpha, measurement_stream_id,
                                    #         is_not_valid) VALUES (%s, %s, %s, %s, %s, %s, %s);
                                    #       """
                                    # sql = """
                                    #         INSERT INTO operation_measurements
                                    #         (raw_file_id, raw_string_id, date_time, reading_numeric, reading_alpha,
                                    #         measurement_stream_id, is_not_valid, validation_lu_id)
                                    #         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    #         """
                                    # logging.info('sql: {0}'.format(sql))
                                    # self._app.settings._database.execute_sql(sql, params, False)


                                    # Ref: http://stackoverflow.com/questions/8144002/use-binary-copy-table-from-with-psycopg2/8150329#8150329

                                    # curs.execute("SELECT nextval('operation_measurements_operation_measurement_id_seq')")
                                    # id_seq = curs.fetchone()[0]
                                    #
                                    # cpy = io.BytesIO()
                                    # cpy.write(pack('!11sii', b'PGCOPY\n\377\r\n\0', 0, 0))
                                    #
                                    # row_format = list(zip(range(-1, 6),
                                    #                     ('i', 'i', 'i', ?, ?, 'i', ?, 'd'),
                                    #                     (4, 4, 4, 8, ?, 4, 1, 4, ?)))
                                    # for i, row in enumerate(params):
                                    #
                                    #     # Number of columns/fields (always 7)
                                    #     cpy.write(pack('!h', 7))
                                    #     if i < 3:
                                    #         logging.info('{0}'.format(row))
                                    #     for col, fmt, size in row_format:
                                    #         value = (id_seq if col == -1 else row[col])
                                    #
                                    #         cpy.write(pack('!i' + fmt, size, value))
                                    #         id_seq += 1
                                    #
                                    # # File trailer
                                    # cpy.write(pack('!h', -1))
                                    #
                                    # curs = self._app.settings._connection.cursor()
                                    # cpy.seek(0)
                                    # curs.copy_expert("COPY OPERATION_MEASUREMENTS FROM STDIN WITH BINARY", cpy)
                                    #
                                    # # Update sequence on database
                                    # curs.execute("SELECT setval('operation_measurements_operation_measurement_id_seq', %s, false)", (id_seq,))
                                    # self._app.settings._connection.commit()


                                    # ---------------------------------------------------------------------------------
                                    # TEST - END
                                    # --------------------------------------------------------------------------------- #
                                    end = arrow.now()
                                    logging.info(f'\t\tElapsed time inserting {stream.rules.line_starting}, {stream.rules.reading_type}, count = {len(clean_data)}: {(end - start).total_seconds():.1f}s')

                                    # TODO Todd Hay - Add signal emissions for updating the statusbar telling what has been parsed/inserted
                                    update_msg += " > Done"
                                    self.updateHaulSerialStatus.emit(update_msg)

                            # If no lines exist for this stream, then just delete this particular stream from measurement_streams
                            else:
                                stream.delete_instance()

                            current_line_starting = stream.rules.line_starting
                            current_equipment_id = stream.rules.equipment

                    # Emit signal to update the DataCompleteness model as well as update the Operations table
                    load_date = arrow.now()
                    self.haulSensorSerialDataLoaded.emit(int(k), load_date.format("MM/DD HH:mm:ss"))

                    if haul_op:
                        load_date = load_date.isoformat()
                        Operations.update(sensor_load_date=load_date).where(Operations.operation==haul_op.operation).execute()

                except BreakIt:
                    # Delete the current haul measurement streams and operation_measurements data
                    try:

                        self._app.settings.set_sensors_proxy(db_file=None)

                        ms = MeasurementStreams.select().where(MeasurementStreams.operation == haul_op.operation)
                        OperationMeasurements.delete().where(OperationMeasurements.measurement_stream << ms).execute()
                        OperationMeasurementsErr.delete().where(OperationMeasurementsErr.measurement_stream << ms).execute()
                        MeasurementStreams.delete().where(MeasurementStreams.operation == haul_op.operation).execute()

                        Operations.update(sensor_load_date=None).where(Operations.operation==haul_op.operation).execute()
                        self.haulSensorSerialDataLoaded.emit(int(k), None)

                        haul_op = None
                        return False, "Processing halted", None

                        break

                    except Exception as ex:

                        self._app.settings.set_sensors_proxy(db_file=None)
                        logging.error("Error deleting the aborted haul sensor data: {0} > {1}".format(haul_op))

                except Exception as ex:

                    logging.error("Error in loading sensor data, haul: {0} > {1}".format(v["haul"], ex))
                    continue

                db_count += 1

        self._app.settings.set_sensors_proxy(db_file=None)

        method_end = arrow.now()
        elapsed_time = (method_end - method_start).total_seconds()
        if db_count == 0:
            status = False
            msg = "No sensor data was loaded as no sensor databases were found"
            logging.info(msg)

        else:
            msg = '\t\tElapsed time: {0:.1f}s'.format((method_end - method_start).total_seconds())
            logging.info(msg)
            status = True

        return status, msg, elapsed_time


class LoadSensorFileDataThread(QObject):

    loadingCompleted = pyqtSignal(bool, str)
    # haulLoaded = pyqtSignal(int, QVariant, arguments=["index", "loadDate"])
    haulSensorFileDataLoaded = pyqtSignal(int, QVariant, arguments=["index", "loadDate"])
    updateHaulFileStatus = pyqtSignal(str, arguments=["msg"])
    # loadingError = pyqtSignal(str, arguments=["msg",])

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self._is_running = False
        self._app = kwargs["app"]
        self._functions = CommonFunctions()
        self._items = kwargs["items"].toVariant() if isinstance(kwargs["items"], QJSValue) else kwargs["items"]
        self._load_status = kwargs["loadStatus"]
        self._elapsed_time = kwargs["elapsed_time"] if kwargs["elapsed_time"] else 0
        self._bcs_reader = BcsReader()
        self._sbe_reader = SeabirdCNVreader()

    def stop(self):
        """
        Method to interrupt the thread, stopping it from running
        :return:
        """
        self._is_running = False

    def run(self):
        self._is_running = True
        status, msg = self._load_data()
        self.loadingCompleted.emit(status, msg)

    def _load_data(self):
        """
        Method to actually load the haul into the database
        :return:
        """
        """
        Method to load new haul-level sensor data to the FRAM_CENTRAL database.  This will gather all of the sensor
        data for given hauls that have a load
        column = yes and then load those into the database.  This loads data into the following tables:
            MEASUREMENT_STREAM
            OPERATION_MEASUREMENTS

        :param item:
        :return:
        """
        if isinstance(self._items, QJSValue):
            self._items = self._items.toVariant()

        items = self._items.items()

        haul_op = None
        method_start = arrow.now()

        status = False
        msg = ""

        insert_template = {"raw_string": None, "date_time": None, "reading_numeric": None,
                           "reading_alpha": None, "measurement_stream": None, "is_not_valid": False}

        db_count = 0
        for k, v in sorted(items):
            if "sensorDatabase" in v and v["sensorDatabase"] != "":
                self._app.settings.set_sensors_proxy(db_file=v["sensorDatabase"])
                self._app.settings.set_wheelhouse_proxy(db_file=v["haulDatabase"])

                try:

                    update_msg = "Sensor File Processing, haul: {0}".format(v["haul"])
                    logging.info(update_msg)
                    self.updateHaulFileStatus.emit(update_msg)

                    # Get the haul operation
                    try:
                        haul_op = OperationsFlattenedVw.get(OperationsFlattenedVw.tow_name == v["haul"])

                    except Exception as ex:
                        logging.info(f'haul_op: {haul_op}')
                        msg = f"Haul {v['haul']} has not been loaded, please load hauls before loading sensor data"
                        logging.info(msg)
                        status = False
                        return status, msg

                    if not self._is_running:
                        raise BreakIt

                    # Get the OperationFilesMtx ID
                    op_file_mtx = OperationFilesMtx.select(OperationFilesMtx)\
                        .join(OperationFiles)\
                        .where(OperationFilesMtx.operation == haul_op.cruise,
                               OperationFiles.final_path_name == v["sensorDatabase"]).first()

                    """
                    Iterate through all of the files for this given tow_name

                    I might need to be smarter about how I do this.  I've run across the following two scenarios that
                    deviate from merely being able to look into the sensors db and search the EnviroNetRawFiles table
                    by the haul number:

                    (1) haul number = Select Haul ID - in other words, the user never actually specified the haul ID when
                        uploading the BCS and/or SBE39 files
                    (2) BCS and/or SBE39 are in a nearby sensor db file, i.e. in the previous or the following day's sensor
                        db file

                    So I think if I don't find any files by haul number, I should start searching the current
                    and the nearby DBs by the activation / deactivation date-times.

                    """
                    # Get the haul start/end date/times
                    haul_start = arrow.get(v["haulStart"], "MM/DD HH:mm:ss").replace(year=int(self._app.settings.year),
                                                                                     tzinfo="US/Pacific").to("utc")
                    haul_end = arrow.get(v["haulEnd"], "MM/DD HH:mm:ss").replace(year=int(self._app.settings.year),
                                                                                 tzinfo="US/Pacific").to("utc")
                    if DEBUG:
                        logging.info(f"\t\thaul start + end: {haul_start} > {haul_end}")

                    # Get the files associated with the tow_name or within the time range
                    files = EnviroNetRawFiles.select().where((EnviroNetRawFiles.haul == haul_op.tow_name) |
                                                             ((EnviroNetRawFiles.haul == "Select Haul ID") &
                                                              (EnviroNetRawFiles.deactivation_datetime >= haul_start) &
                                                              (EnviroNetRawFiles.activation_datetime <= haul_end))
                                                             )
                    if DEBUG:
                        logging.info(f"\t\tfiles count in the current database: {files.count()}")

                    # If no files found in the current db, search the next day's db if one exists
                    if files.count() == 0:

                        update_msg = "\t\tCurrent day database does not have the sensor files, trying the next day"
                        logging.info(update_msg)
                        self.updateHaulFileStatus.emit(update_msg)

                        # Get tomorrow's database, if it exists
                        today_db = v["sensorDatabase"]
                        tomorrow_db = os.path.splitext(os.path.basename(today_db))
                        if re.search('sensors_\d{8}', tomorrow_db[0]):
                            tomorrow_db = tomorrow_db[0].split("_")[1]
                            _year = int(tomorrow_db[0:4])
                            _month = int(tomorrow_db[4:6])
                            _day = int(tomorrow_db[6:8])
                            tomorrow_db = "sensors_" + arrow.get(_year, _month, _day).shift(days=1).format("YYYYMMDD") + ".db"
                            tomorrow_db = os.path.join(os.path.dirname(today_db), tomorrow_db)
                            if not os.path.exists(tomorrow_db):
                                logging.info(f"\t\tThe next day database does not exist to check for possible sensor files, db would be: {tomorrow_db}")
                            else:
                                # Get the OperationFilesMtx ID
                                op_file_mtx = OperationFilesMtx.select(OperationFilesMtx) \
                                    .join(OperationFiles) \
                                    .where(OperationFilesMtx.operation == haul_op.cruise,
                                           OperationFiles.final_path_name == tomorrow_db).first()

                                # Set the sensor db proxy to the tomorrow_db
                                self._app.settings.set_sensors_proxy(db_file=tomorrow_db)

                                # Search for files for this db
                                files = EnviroNetRawFiles.select().where((EnviroNetRawFiles.haul == haul_op.tow_name) |
                                                                 ((EnviroNetRawFiles.haul == "Select Haul ID") &
                                                                  (EnviroNetRawFiles.deactivation_datetime >= haul_start) &
                                                                  (EnviroNetRawFiles.activation_datetime <= haul_end))
                                                                 )

                                if DEBUG:
                                    logging.info(f"\t\tfiles count in tomorrow's database: {files.count()}")

                    for file in files:

                        if not self._is_running:
                            raise BreakIt

                        try:

                            # Get the deployed_equipment for this particular file deployed_equipment
                            deployed_equipment = DeployedEquipment.get(DeployedEquipment.deployed_equipment == file.deployed_equipment)

                            logging.info(f"\tProcessing file, type: {deployed_equipment.position}, ID: {file.enviro_net_raw_files}")

                            # If reloading, delete associated measurement_streams and operation_measurements
                            if self._load_status == "reload":
                                ms = MeasurementStreams.select() \
                                    .join(ParsingRulesVw,
                                          on=(ParsingRulesVw.parsing_rules == MeasurementStreams.equipment_field)) \
                                    .where(MeasurementStreams.operation == haul_op.operation,
                                           MeasurementStreams.attachment_position == deployed_equipment.position,
                                           ParsingRulesVw.logger_or_serial == "logger")
                                OperationMeasurements.delete().where(
                                    OperationMeasurements.measurement_stream << ms).execute()
                                OperationMeasurementsErr.delete().where(
                                    OperationMeasurementsErr.measurement_stream << ms).execute()
                                OperationAttributes.delete().where(
                                    OperationAttributes.measurement_stream << ms).execute()
                                MeasurementStreams.delete().where(MeasurementStreams.measurement_stream << ms).execute()

                            # Find all parsing_rules for this deployed_equipment
                            # .distinct([ParsingRulesVw.equipment, ParsingRulesVw.reading_type]) \
                            rules = ParsingRulesVw.select() \
                                .where(ParsingRulesVw.is_parsed,
                                       ParsingRulesVw.logger_or_serial == "logger",
                                       ParsingRulesVw.equipment == deployed_equipment.equipment) \
                                .order_by(ParsingRulesVw.equipment, ParsingRulesVw.reading_type) \
                                .distinct()

                            # Create the measurement_streams for the rules that were just found
                            for rule in rules:
                                stream, _ = MeasurementStreams.get_or_create(
                                    operation_id=haul_op.operation,
                                    attachment_position=deployed_equipment.position,
                                    operation_files_mtx=op_file_mtx.operation_files_mtx,
                                    equipment_field=rule.parsing_rules,
                                    raw_files=file.enviro_net_raw_files,
                                    defaults={
                                        "stream_offset_seconds": 0
                                    }
                                )

                            # Process BCS data
                            if 'bcs' in deployed_equipment.position.lower():

                                # Handle BCS data processing
                                self._bcs_reader.set_raw_content(raw_content=file.raw_file, position=deployed_equipment.position)

                                update_msg = f'\t\tBCS Sensor File Type: {self._bcs_reader.sensor_type}'
                                logging.info(update_msg)
                                self.updateHaulFileStatus.emit(update_msg)

                                bcs_data = self._bcs_reader.parse_data(angles="xy")
                                if bcs_data is not None:

                                    key, values = bcs_data

                                    # Get the X Tilt measurement stream, applies to both AFSC + NWFSC BCS's
                                    x_stream = MeasurementStreams.select(MeasurementStreams) \
                                        .join(ParsingRulesVw,
                                              on=(
                                                  MeasurementStreams.equipment_field == ParsingRulesVw.parsing_rules).alias(
                                                  'rules')) \
                                        .where(MeasurementStreams.operation == haul_op.operation,
                                               MeasurementStreams.attachment_position == deployed_equipment.position,
                                               ParsingRulesVw.logger_or_serial == "logger",
                                               ParsingRulesVw.equipment == deployed_equipment.equipment,
                                               ParsingRulesVw.reading_type == "X Tilt Angle").first()
                                    template = deepcopy(insert_template)
                                    template["measurement_stream"] = x_stream.measurement_stream
                                    if DEBUG:
                                        logging.info(f"\t\tstream: {model_to_dict(x_stream)}")

                                    # Get the X Tilt Values - this applies to both AFSC + NWFSC BCS sensors
                                    # Sample values:  ['2016-05-21T05:11:45-07:00', 87]
                                    x_parsed_data = [{"date_time": x[0], "reading_numeric": x[1]}
                                                     for x in values["data"] if x[1] is not None]
                                    insert_list = [deepcopy(template)] * len(x_parsed_data)
                                    insert_list = [{**insert_list[i], **x_parsed_data[i]} for i in
                                                   range(len(x_parsed_data))]

                                    if DEBUG:
                                        logging.info(f"\t\tinsert_list len: {len(insert_list)}")
                                        if len(insert_list) > 0:
                                            logging.info(f"\t\tinsert_list[0]: {insert_list[0]}")

                                    # Insert the X Tilt Values
                                    insert_list = [x for x in insert_list if x["reading_numeric"] is not None]
                                    with self._app.settings._database.atomic():
                                        # OperationMeasurements.insert_many(insert_list).execute()
                                        for idx in range(0, len(insert_list), 5000):
                                            if not self._is_running:
                                                raise BreakIt
                                            OperationMeasurements.insert_many(insert_list[idx:idx + 5000]).execute()

                                    if self._bcs_reader.sensor_type == "nwfsc_txt":
                                        # We have both an X Tilt Angle and Y Tilt Angle for the NWFSC BCS

                                        # Get the Y Tilt Measurement stream
                                        y_stream = MeasurementStreams.select(MeasurementStreams) \
                                            .join(ParsingRulesVw,
                                                  on=(
                                                      MeasurementStreams.equipment_field == ParsingRulesVw.parsing_rules).alias(
                                                      'rules')) \
                                            .where(MeasurementStreams.operation == haul_op.operation,
                                                   MeasurementStreams.attachment_position == deployed_equipment.position,
                                                   ParsingRulesVw.logger_or_serial == "logger",
                                                   ParsingRulesVw.equipment == deployed_equipment.equipment,
                                                   ParsingRulesVw.reading_type == "Y Tilt Angle").first()
                                        if DEBUG:
                                            logging.info(f"\t\tstream: {model_to_dict(y_stream)}")

                                        # Y Tilt Values - Retrieve from the data structure
                                        y_parsed_data = [{"date_time": x[0], "reading_numeric": x[2]}
                                                       for x in values["data"] if x[2] is not None]

                                        # Create the insert_list
                                        template = deepcopy(insert_template)
                                        template["measurement_stream"] = y_stream.measurement_stream
                                        insert_list = [deepcopy(template)] * len(y_parsed_data)
                                        insert_list = [{**insert_list[i], **y_parsed_data[i]} for i in range(len(y_parsed_data))]
                                        insert_list = [x for x in insert_list if x["reading_numeric"] is not None]

                                        # Insert the actual data
                                        with self._app.settings._database.atomic():
                                            # OperationMeasurements.insert_many(insert_list).execute()
                                            for idx in range(0, len(insert_list), 5000):
                                                if not self._is_running:
                                                    raise BreakIt
                                                OperationMeasurements.insert_many(insert_list[idx:idx + 5000]).execute()

                            # Process SBE39 Data
                            elif 'sbe39' in deployed_equipment.position.lower():

                                # Handle SBE39 data processing
                                logging.info('\t\tSBE39 Sensor File Type')
                                self._sbe_reader.set_raw_content(raw_content=file.raw_file)
                                sbe_data = self._sbe_reader.get_temperature_and_depth()
                                if sbe_data is not None:

                                    for sbe_k, sbe_v in sbe_data.items():

                                        if DEBUG:
                                            logging.info(f"SBE39 key/value: {sbe_k} > {sbe_v}")

                                        # Get the measurement stream associated with the key (sbe_k)
                                        stream = MeasurementStreams.select(MeasurementStreams) \
                                            .join(ParsingRulesVw,
                                                  on=(
                                                      MeasurementStreams.equipment_field == ParsingRulesVw.parsing_rules).alias(
                                                      'rules')) \
                                            .where(MeasurementStreams.operation == haul_op.operation,
                                                   MeasurementStreams.attachment_position == deployed_equipment.position,
                                                   ParsingRulesVw.logger_or_serial == "logger",
                                                   ParsingRulesVw.equipment == deployed_equipment.equipment,
                                                   ParsingRulesVw.reading_type == sbe_k.replace("Gear", "").strip()).first()
                                        template = deepcopy(insert_template)
                                        template["measurement_stream"] = stream.measurement_stream
                                        if DEBUG:
                                            logging.info(f"\t\tstream: {model_to_dict(stream)}")

                                        # Get the Values associated with the values (sbe_v)
                                        parsed_data = [{"date_time": x[0], "reading_numeric": x[1]}
                                                         for x in sbe_v["data"] if x[1] is not None]
                                        insert_list = [deepcopy(template)] * len(parsed_data)
                                        insert_list = [{**insert_list[i], **parsed_data[i]} for i in
                                                       range(len(parsed_data))]

                                        if DEBUG:
                                            logging.info(f"\t\tinsert_list len: {len(insert_list)}")
                                            if len(insert_list) > 0:
                                                logging.info(f"\t\tinsert_list[0]: {insert_list[0]}")

                                        # Insert the Values
                                        insert_list = [x for x in insert_list if x["reading_numeric"] is not None]
                                        with self._app.settings._database.atomic():
                                            # OperationMeasurements.insert_many(insert_list).execute()
                                            for idx in range(0, len(insert_list), 5000):
                                                if not self._is_running:
                                                    raise BreakIt
                                                OperationMeasurements.insert_many(insert_list[idx:idx + 5000]).execute()

                            load_date = arrow.now()
                            self.haulSensorFileDataLoaded.emit(int(k), load_date.format("MM/DD HH:mm:ss"))

                        except Exception as ex:
                            logging.error(f"Error in loading sensor file data, haul: {v['haul']} > {os.path.basename(v['sensorDatabase'])} > {ex}")

                    if haul_op:
                        load_date = arrow.now().isoformat()
                        Operations.update(sensor_load_date=load_date).where(Operations.operation==haul_op.operation).execute()

                # except psycopg2.DatabaseError

                except BreakIt:
                    # Delete the current haul measurement streams and operation_measurements data
                    try:

                        self._app.settings.set_sensors_proxy(db_file=None)

                        ms = MeasurementStreams.select().where(MeasurementStreams.operation == haul_op.operation)
                        OperationMeasurements.delete().where(OperationMeasurements.measurement_stream << ms).execute()
                        OperationMeasurementsErr.delete().where(OperationMeasurementsErr.measurement_stream << ms).execute()
                        MeasurementStreams.delete().where(MeasurementStreams.operation == haul_op.operation).execute()

                        Operations.update(sensor_load_date=None).where(Operations.operation==haul_op.operation).execute()
                        self.haulSensorFileDataLoaded.emit(int(k), None)

                        haul_op = None
                        return False, "Processing halted"

                        break

                    except Exception as ex:

                        self._app.settings.set_sensors_proxy(db_file=None)
                        logging.error("Error deleting the aborted haul sensor data: {0} > {1}".format(haul_op))

                except Exception as ex:

                    logging.error("Error in loading sensor file data, haul: {0} > {1}".format(v["haul"], ex))
                    continue

                db_count += 1

        self._app.settings.set_sensors_proxy(db_file=None)

        method_end = arrow.now()

        if db_count == 0:
            status = False
            msg = "No sensor data was loaded as no sensor databases were found"
            logging.info(msg)

        else:
            elapsed_time = self._elapsed_time + (method_end - method_start).total_seconds()
            msg = f'Elapsed time: {elapsed_time:.1f}s'
            logging.info(msg)
            status = True

        return status, msg


class RemoveHaulSensorDataThread(QObject):

    jobCompleted = pyqtSignal(bool, str, QVariant)
    haulCompleted = pyqtSignal(int, arguments=["index",])

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self._is_running = False
        self._app = kwargs["app"]
        self._functions = CommonFunctions()
        self._hauls = kwargs["hauls"].toVariant() if isinstance(kwargs["hauls"], QJSValue) else kwargs["hauls"]

    def stop(self):
        """
        Method to interrupt the thread, stopping it from running
        :return:
        """
        self._is_running = False

    def run(self):
        self._is_running = True
        status, msg, elapsed_time = self._remove_data()
        self.jobCompleted.emit(status, msg, elapsed_time)

    def _remove_data(self):
        """
        Method to remove the haul and sensor data for the items in the self._items variable
        :return:
        """
        if isinstance(self._hauls, QJSValue):
            self._hauls = self._hauls.toVariant()

        start = arrow.now()
        status = False
        msg = ""

        try:
            for index, row in self._hauls.items():
                haul_number = row["haul"]
                op_id = Operations.get(Operations.operation_name == haul_number).operation
                if not op_id:
                    continue

                logging.info(f"removing haul {row['haul']} >>>  op_id = {op_id}")

                # Performance Details
                try:
                    PerformanceDetails.delete().where(PerformanceDetails.operation == op_id).execute()
                except Exception as ex:
                    logging.info(f"Error deleting performance details for {haul_number}")

                try:
                    op_file_mtx = OperationFilesMtx.select().where(OperationFilesMtx.operation == op_id)
                    op_meas_streams = MeasurementStreams.select() \
                        .where(MeasurementStreams.operation_files_mtx.in_(op_file_mtx))
                except Exception as ex:
                    logging.info(f"Error retrieving op_file_mtx or op_meas_streams for {haul_number}: {ex}")

                # Operation_Measurement_Err
                try:
                    OperationMeasurementsErr.delete()\
                        .where(OperationMeasurementsErr.measurement_stream.in_(op_meas_streams)).execute()

                except Exception as ex:
                    logging.info(f"Error deleting operation_measurement_err for {haul_number}: {ex}")

                # Operation_Measurement
                try:
                    OperationMeasurements.delete()\
                        .where(OperationMeasurements.measurement_stream.in_(op_meas_streams)).execute()

                except Exception as ex:
                    logging.info(f"Error deleting operation_measurement for {haul_number}: {ex}")

                # Remove Comments - from Operations or Events
                try:
                    # Operations Comments
                    Comments.delete().where(Comments.operation == op_id).execute()

                    # Events Comments
                    op_events = Events.select().where(Events.operation == op_id)
                    Comments.delete().where(Comments.event.in_(op_events)).execute()

                except Exception as ex:
                    logging.info(f"Error deleting comments for {haul_number}: {ex}")

                # Remove Events
                try:
                    Events.delete().where(Events.operation == op_id).execute()
                except Exception as ex:
                    logging.info(f"Error deleting events for {haul_number}: {ex}")

                # Remove Operation_Attributes
                try:
                    # Measurement Stream Level
                    OperationAttributes.delete()\
                        .where(OperationAttributes.measurement_stream.in_(op_meas_streams)).execute()

                    # Operation Level
                    OperationAttributes.delete().where(OperationAttributes.operation == op_id).execute()

                except Exception as ex:
                    logging.info(f"Error deleting operation_attributes for {haul_number}: {ex}")

                # Measurement_Stream
                try:
                    MeasurementStreams.delete()\
                        .where(MeasurementStreams.measurement_stream.in_(op_meas_streams)).execute()

                except Exception as ex:
                    logging.info(f"Error deleting measurement_stream for {haul_number}: {ex}")

                # Operation_File_Mtx
                try:
                    OperationFilesMtx.delete()\
                        .where(OperationFilesMtx.operation_files_mtx.in_(op_file_mtx)).execute()
                except Exception as ex:
                    logging.info(f"Error deleting operation_file_mtx for {haul_number}: {ex}")

                # Remove Operations
                try:
                    Operations.delete().where(Operations.operation_name == haul_number).execute()
                except Exception as ex:
                    logging.info(f"Error deleting operations for {haul_number}: {ex}")

                self.haulCompleted.emit(index)

        except Exception as ex:

            end = arrow.now()
            elapsed_time = (end - start).total_seconds()
            msg = f"Error removing the haul + sensor data: {ex}"
            logging.error(msg)
            return status, msg, elapsed_time


        end = arrow.now()

        elapsed_time = (end - start).total_seconds()
        msg = f"Elapsed time: {elapsed_time:.1f}s"
        logging.info(msg)
        status = True

        return status, msg, elapsed_time


class DataCheckModel(FramListModel):

    sensorDataUpdated = pyqtSignal(int, QVariant, arguments=["index", "item"])
    sensorThreadCompleted = pyqtSignal()
    breakItEncountered = pyqtSignal(str, arguments=["msg"])

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="load")
        self.add_role_name(name="linked")
        self.add_role_name(name="opsLoadStatus")
        self.add_role_name(name="catchLoadStatus")
        self.add_role_name(name="sensorsLoadStatus")
        self.add_role_name(name="haul")
        self.add_role_name(name="haulStart")
        self.add_role_name(name="haulEnd")
        self.add_role_name(name="haulDatabase")
        self.add_role_name(name="catchDatabase")
        self.add_role_name(name="sensorDatabase")
        self.add_role_name(name="haulPerformance")
        self.add_role_name(name="catchSpeciesCount")
        self.add_role_name(name="specimenCount")
        self.add_role_name(name="zeroBasketWeightCount")

        self._populate_model_thread = QThread()
        self._populate_model_worker = None

        self._populate_model_sensor_thread = QThread()
        self._populate_model_sensor_worker = None

        self._populate_model_backdeck_thread = QThread()
        self._populate_model_backdeck_worker = None

    def _sensor_data_updated(self, index, item):
        """
        Method that catches the output of the sensorDataThread that is used to populate the sensor data information
        of the model in the background
        :param index:
        :param item:
        :return:
        """
        if index >= 0 and index < len(self.items):
            self._app.settings.statusBarMessage = f"Sensor data matched > haul: {self.items[index]['haul']}, data: {item}"
            for k, v in item.items():
                self.setProperty(index=index, property=k, value=v)

    def _sensor_thread_completed(self, status, msg):
        """
        Method caught at the end of the sensor update thread
        :param status:
        :param msg:
        :return:
        """

        # Stop the thread
        if self._populate_model_sensor_thread:
            self._populate_model_sensor_thread.quit()

        # Clear the status bar
        self._app.settings.statusBarMessage = ""

        # Emit the signal
        self.sensorThreadCompleted.emit()

        msg = "DataCompleteness - starting backdeck data model population"
        logging.info(msg)
        self._app.settings.statusBarMessage = msg

        # Start the backdeck thread
        kwargs = {"app": self._app,
                  "orderedNames": deepcopy(self.ordered_rolenames)}
        self._populate_model_backdeck_worker = PopulateModelBackdeckDataThread(kwargs=kwargs)
        self._populate_model_backdeck_worker.moveToThread(self._populate_model_backdeck_thread)
        self._populate_model_backdeck_worker.backdeckThreadCompleted.connect(self._backdeck_thread_completed)
        self._populate_model_backdeck_worker.haulProcessed.connect(self._backdeck_haul_processed)
        self._populate_model_backdeck_thread.started.connect(self._populate_model_backdeck_worker.run)
        self._populate_model_backdeck_thread.start()

    def _thread_results_received(self, status, msg, results):
        """
        Method to catch the results coming back from the populate model thread.  This is then used to actually
        populate the model in the GUI
        :param status:
        :param msg:
        :param results:
        :return:
        """
        # Clear the status bar
        self._app.settings.statusBarMessage = ""

        # Stop the thread
        if self._populate_model_thread:
            self._populate_model_thread.quit()

        # Populate the model
        # if status:
        #     self.setItems(results)

        # Start the sensor thread
        msg = "DataCompleteness - starting sensor data model population"
        logging.info(msg)
        self._app.settings.statusBarMessage = msg

        kwargs = {"app": self._app,
                  "orderedNames": deepcopy(self.ordered_rolenames)}
        self._populate_model_sensor_worker = PopulateModelSensorDataThread(kwargs=kwargs)
        self._populate_model_sensor_worker.moveToThread(self._populate_model_sensor_thread)
        self._populate_model_sensor_worker.sensorThreadCompleted.connect(self._sensor_thread_completed)
        self._populate_model_sensor_worker.sensorDataUpdated.connect(self._sensor_data_updated)
        self._populate_model_sensor_thread.started.connect(self._populate_model_sensor_worker.run)
        self._populate_model_sensor_thread.start()

    def _haul_data_updated(self, item):
        """
        Method to catch individual haul updates from the background thread
        """
        self._app.settings.statusBarMessage = f"Wheelhouse data found > {item}"
        self.appendItem(item)

    def _backdeck_thread_completed(self, status, msg):
        """
        Method to catch the result from the background thread to update the columns related to the backdeck
        :param status:
        :param msg:
        :return:
        """
        self._app.settings.statusBarMessage = ""

        if self._populate_model_backdeck_thread:
            self._populate_model_backdeck_thread.quit()

    def _backdeck_haul_processed(self, index, item, action):
        """
        Method to catch the result from the background thread to update the columns related to the backdeck
        :param index:
        :param item:
        :param action:
        :return:
        """
        if index >=0 and index < len(self.items):
            self._app.settings.statusBarMessage = \
                f"Backdeck data matched > haul: {self.items[index]['haul']}, action: {action}, data: {item}"
        else:
            self._app.settings.statusBarMessage = \
                f"Backdeck data matched > action: {action}, data: {item}"

        if action == "update":
            if index >= 0 and index < len(self.items):
                for k, v in item.items():
                    # logging.info("{0}, {1}, {2}".format(index, k, v))
                    self.setProperty(index=index, property=k, value=v)

        elif action == "insert":
            self.appendItem(item)

    def populate_model(self):
        """
        Method to initialize the model upon starting the application
        :return:
        """
        self.clear()

        msg = "DataCompleteness - starting wheelhouse data model population"
        logging.info(msg)
        self._app.settings.statusBarMessage = msg

        # Create + Start Thread
        kwargs = {"app": self._app,
                  "orderedNames": deepcopy(self.ordered_rolenames)}
        self._populate_model_worker = PopulateModelThread(kwargs=kwargs)
        self._populate_model_worker.moveToThread(self._populate_model_thread)
        self._populate_model_worker.queryStatus.connect(self._thread_results_received)
        self._populate_model_worker.haulDataUpdated.connect(self._haul_data_updated)
        self._populate_model_worker.breakItEncountered.connect(self._breakit_encountered)
        self._populate_model_thread.started.connect(self._populate_model_worker.run)
        self._populate_model_thread.start()

    def _breakit_encountered(self, msg):
        """
        Method called from the Populate Model worker when a BreakIt command is found indicating
        that an error has been encountered
        :param msg:
        :param action:
        :return:
        """
        logging.info(f"BreakIt info: msg={msg}")
        self.breakItEncountered.emit(msg)

    @pyqtSlot()
    def stop_model_population(self):
        """
        Method to stop the model population threads:
        :return:
        """
        # Stop the backdeck thread
        if self._populate_model_backdeck_worker:
            self._populate_model_backdeck_worker.stop()
            msg = "Stopped backedck DataCompleteness model population thread"
            logging.info(msg)
            self._app.settings.statusBarMessage = msg

        # Stop the sensor thread
        if self._populate_model_sensor_worker:
            self._populate_model_sensor_worker.stop()
            msg = "Stopped sensors DataCompleteness model population thread"
            logging.info(msg)
            self._app.settings.statusBarMessage = msg

        # Stop the wheelhouse + sensor thread
        if self._populate_model_worker:
            self._populate_model_worker.stop()
            msg = "Stopped wheelhouse DataCompleteness model population thread"
            logging.info(msg)
            self._app.settings.statusBarMessage = msg

        self._app.settings.statusBarMessage = ""

    @pyqtSlot(QVariant)
    def add_item(self, item):
        """
        Method to add a new item to the model
        :param item:
        :return:
        """
        if isinstance(item, QJSValue):
            item = item.toVariant()

        if "fileName" in item:
            item["fileName"] = os.path.realpath(item["fileName"].strip("file:///"))
            self.appendItem(item=item)

    @pyqtSlot(QVariant)
    def remove_item(self, item):
        """
        Method to remove an item from the model
        :param item:
        :return:
        """
        if isinstance(item, QJSValue):
            item = item.toVariant()

        if "fileName" in item:
            index = self.get_item_index(rolename="fileName", value=item["fileName"])
            if index >= 0:
                self.removeItem(index=index)

    @pyqtSlot()
    def selectAll(self):
        """
        This turns the Load column to selected for all of the items
        :return:
        """
        for i, v in enumerate(self.items):
            if "t" not in v["haul"]:
                self.setProperty(index=i, property="load", value="yes")

    @pyqtSlot()
    def deselectAll(self):
        """
        This deselects all of the Load column items
        :return:
        """
        for i, v in enumerate(self.items):
            self.setProperty(index=i, property="load", value="no")


class DataCompleteness(QObject):
    """
    Class for the FishSamplingScreen.
    """
    # valueChanged = pyqtSignal(int, str, arguments=["tabIndex", "property"])
    dataCheckModelChanged = pyqtSignal()

    haulLoaded = pyqtSignal(int, QVariant, arguments=["index", "loadDate"])
    loadingFinished = pyqtSignal(bool, str, arguments=["status", "msg"])

    haulSensorSerialDataLoaded = pyqtSignal(int, QVariant, arguments=["index", "loadDate"])
    sensorSerialLoadingFinished = pyqtSignal(bool, str, arguments=["status", "msg"])

    haulSensorFileDataLoaded = pyqtSignal(int, QVariant, arguments=["index", "loadDate"])
    sensorFileLoadingFinished = pyqtSignal(bool, str, arguments=["status", "msg"])

    # Used for removing haul + sensor data
    showMessage = pyqtSignal(str, bool, str, arguments=["job", "status", "msg"])
    haulDataRemoved = pyqtSignal(int, arguments=["index",])

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db
        self._functions = CommonFunctions()

        # Set up the models
        self._data_check_model = DataCheckModel(self._app)

        self._load_hauls_thread = QThread()
        self._load_hauls_worker = None

        self._load_sensor_serial_data_thread = QThread()
        self._load_sensor_serial_data_worker = None

        self._load_sensor_file_data_thread = QThread()
        self._load_sensor_file_data_worker = None

        self._remove_haul_sensor_data_thread = QThread()
        self._remove_haul_sensor_data_worker = None

    @pyqtProperty(FramListModel, notify=dataCheckModelChanged)
    def dataCheckModel(self):
        """
        Method to return the self._data_check_model model
        :return:
        """
        return self._data_check_model

    @pyqtSlot(QVariant)
    def load_hauls(self, items):
        """
        Method to load new haul data to the FRAM_CENTRAL database.  This will gather all of the hauls that have a load
        column = yes and then load those into the database.  This loads data into the following tables:
            OPERATIONS
            OPERATION_DETAILS
            EVENTS
            COMMENTS

        :param item:
        :return:
        """

        # self.loadingFinished = False

        logging.info('Starting haul loading thread')

        # Create + Start Thread
        kwargs = {"app": self._app, "items": items}
        self._load_hauls_worker = LoadHaulsThread(kwargs=kwargs)
        self._load_hauls_worker.moveToThread(self._load_hauls_thread)
        self._load_hauls_worker.loadingCompleted.connect(self._loading_thread_completed)
        self._load_hauls_worker.haulLoaded.connect(self._haul_loaded)
        self._load_hauls_thread.started.connect(self._load_hauls_worker.run)
        self._load_hauls_thread.start()

    def _haul_loaded(self, index, load_date):
        """
        Method use to catch a return from the LoadHaulsThread that indicates if an individual haul was loaded or not
        :return:
        """
        try:
            logging.info(f"index = {index}, load_date = {load_date}")

            index = int(index)
            haul = self._data_check_model.get(index)["haul"]
            msg = "Haul " + haul + " loaded at " + load_date
            self._app.settings.statusBarMessage = "Haul " + haul + " loaded at " + load_date
            logging.info(msg)
            self.haulLoaded.emit(index, load_date)
        except Exception as ex:
            logging.error(f"Error emitting the haulLoaded signal: {ex}")

    def _loading_thread_completed(self, status, msg):
        """
        Method use to catch the final return from teh LoadHaulsThread that indicates that the overall loading is finished
        :return:
        """
        if self._load_hauls_thread:
            self._load_hauls_thread.quit()
        self._app.settings.statusBarMessage = ""
        self.loadingFinished.emit(status, msg)

    @pyqtSlot(str, QVariant)
    def load_sensor_data(self, load_status, items):
        """
        Method to load new haul sensor data to the FRAM_CENTRAL database.  This loads data into the following tables:
            MEASUREMENT_STREAMS
            OPERATION_MEASUREMENTS

        This calls a background thread to actually perform the data loading.  Note that this will laod both the
        stream and the logger (BCS / SBE39) sensor data.  The logger loading is called in the
        _sensor_serial_loading_thread_completed method, at which time it calls the load_sensor_files method that in
        turn launches a second background thread for loading the sensor file data.

        :param items:
        :return:
        """

        # Create + Start Thread for Loading Serial NMEA data
        kwargs = {"app": self._app, "items": items, "loadStatus": load_status}
        self._load_sensor_serial_data_worker = LoadSensorSerialDataThread(kwargs=kwargs)
        self._load_sensor_serial_data_worker.moveToThread(self._load_sensor_serial_data_thread)

        self._load_sensor_serial_data_worker.loadingCompleted.connect(self._sensor_serial_loading_thread_completed)
        self._load_sensor_serial_data_worker.haulSensorSerialDataLoaded.connect(self._sensor_data_loaded)
        self._load_sensor_serial_data_worker.updateHaulSerialStatus.connect(self._sensor_update_message_received)

        self._load_sensor_serial_data_thread.started.connect(self._load_sensor_serial_data_worker.run)
        self._load_sensor_serial_data_thread.start()

    @pyqtSlot(str, QVariant, QVariant)
    def load_sensor_files(self, load_status, items, elapsed_time):
        """
        Method to load a BCS or SBE39 file that was not loaded into the original sensors database
        :param load_status:
        :param item:
        :param file_type:
        :return:
        """

        # Start the Sensor Files Loading Thread
        kwargs = {"app": self._app, "items": items, "loadStatus": load_status, "elapsed_time": elapsed_time}
        self._load_sensor_file_data_worker = LoadSensorFileDataThread(kwargs=kwargs)
        self._load_sensor_file_data_worker.moveToThread(self._load_sensor_file_data_thread)

        self._load_sensor_file_data_worker.loadingCompleted.connect(self._sensor_file_loading_thread_completed)
        self._load_sensor_file_data_worker.haulSensorFileDataLoaded.connect(self._sensor_data_loaded)
        self._load_sensor_file_data_worker.updateHaulFileStatus.connect(self._sensor_update_message_received)

        self._load_sensor_file_data_thread.started.connect(self._load_sensor_file_data_worker.run)
        self._load_sensor_file_data_thread.start()

    def _sensor_data_loaded(self, index, load_date):
        """
        Method use to catch a return from the LoadHaulSensorDataThread that indicates if an individual haul sensor
        data was loaded or not
        :param index:
        :param load_date:
        :return:
        """

        # TODO Todd Hay - Fix indexing error, why?  Also, need to update the database, oops, don't have a spot
        #   therefore need to do what with this???? - query on initialization and see if it was loaded.
        if index >= 0 and index < len(self._data_check_model.items):
            haul = self._data_check_model.get(index)["haul"]
            load_date = "" if load_date is None else load_date
            msg = "\t\tHaul " + haul + " sensor serial data loaded at " + load_date
            self._app.settings.statusBarMessage = msg
            logging.info(msg)
            self.haulSensorSerialDataLoaded.emit(index, load_date)

    def _sensor_update_message_received(self, msg):
        """
        Method to catch an update message from the haul sensor loading thread to display data to the statusbar
        :param msg:
        :return:
        """
        self._app.settings.statusBarMessage = msg

    def _sensor_serial_loading_thread_completed(self, status, msg, items, load_status, elapsed_time):
        """
        Method called that catches the final return from the LoadSensorDataThread that indicates that the overall
        loading is finished
        :param status:
        :param msg:
        :return:
        """

        # Stop the Thread
        if self._load_sensor_serial_data_thread:
            self._load_sensor_serial_data_thread.quit()

        # Clear the status bar
        self._app.settings.statusBarMessage = ""

        # Signal the results
        self.sensorSerialLoadingFinished.emit(status, msg)

        # TEST TEST TEST - only for Beth to do her stress testing
        # self.sensorFileLoadingFinished.emit(status, msg)

        # Start the Sensor Files Loading Thread
        self.load_sensor_files(load_status=load_status, items=items, elapsed_time=elapsed_time)

    def _sensor_file_loading_thread_completed(self, status, msg):
        """
        Method called that catches the final return from the LoadSensorDataThread that indicates that the overall
        loading is finished
        :param status:
        :param msg:
        :return:
        """

        # Stop the Thread
        if self._load_sensor_file_data_thread:
            self._load_sensor_file_data_thread.quit()

        # Clear the status bar
        self._app.settings.statusBarMessage = ""

        # Signal the results
        self.sensorFileLoadingFinished.emit(status, msg)

    @pyqtSlot(QVariant, name="removeHaulSensorData")
    def remove_haul_and_sensor_data(self, hauls):
        """
        Method to remove the give hauls and all of their sensor data.  This will completely remove all information
        assocated with the haul(s).  I implemented this as some of the waypoints were failing to load for the
        201703010100 (only loaded up through Start Haulback) and I needed to figure out why those were failing
        :param hauls:
        :return:
        """
        if isinstance(hauls, QJSValue):
            hauls = hauls.toVariant()

        # Create + Start Thread for Loading Serial NMEA data
        kwargs = {"app": self._app, "hauls": hauls}
        self._remove_haul_sensor_data_worker = RemoveHaulSensorDataThread(kwargs=kwargs)
        self._remove_haul_sensor_data_worker.moveToThread(self._remove_haul_sensor_data_thread)

        self._remove_haul_sensor_data_worker.jobCompleted.connect(self._remove_haul_sensor_data_thread_completed)
        self._remove_haul_sensor_data_worker.haulCompleted.connect(self._remove_haul_sensor_data_thread_haul_completed)

        self._remove_haul_sensor_data_thread.started.connect(self._remove_haul_sensor_data_worker.run)
        self._remove_haul_sensor_data_thread.start()

    def _remove_haul_sensor_data_thread_haul_completed(self, index):
        """
        Method called when an individual haul + its sensor data has been removed
        :param index:
        :return:
        """
        if index >= 0 and index < len(self._data_check_model.items):
            haul = self._data_check_model.get(index)["haul"]
            msg = "\t\tHaul " + haul + " data has been removed"
            self._app.settings.statusBarMessage = msg
            logging.info(msg)
            self.haulDataRemoved.emit(index)

    def _remove_haul_sensor_data_thread_completed(self, status, msg, elapsed_time):
        """
        Method called when the removing haul + sensor data thread is completed.
        :return:
        """

        # Stop the Thread
        if self._remove_haul_sensor_data_thread:
            self._remove_haul_sensor_data_thread.quit()

        # Clear the status bar
        self._app.settings.statusBarMessage = ""

        # Signal the results
        job = "Removing haul + sensor data job: "
        self.showMessage.emit(job, status, msg)

    @pyqtSlot()
    def stop_data_loading(self):
        """
        Method called to stop any data loading processing
        :return:
        """

        # Stop the wheelhouse data loading thread
        if self._load_hauls_worker:
            self._load_hauls_worker.stop()
            logging.info('hauls loading stopped')

        # Stop the sensor data loading thread
        if self._load_sensor_serial_data_worker:
            self._load_sensor_serial_data_worker.stop()
            logging.info('sensor serial streams loading stopped')

        if self._load_sensor_file_data_worker:
            self._load_sensor_file_data_worker.stop()
            logging.info('sensor file loading stopped')

        # TODO Todd Hay - Activate once the catch data worker is in place
        # Stop the catch data loading thread
        # if self._load_catch_data_worker:
        #     self._load_catch_data_worker.stop()
        #     logging.info('catch loading stopped')

        self._app.settings.statusBarMessage = ""


class TestDataCompleteness(unittest.TestCase):

    # def __init__(self, *args, **kwargs):
    #     super(TestDataCompleteness, self).__init__(*args, **kwargs)
    #     # self.TEST_SETTINGS_PARAMETER_NAME = TrawlFrequentCatchCategories.SETTINGS_PARAMETER_NAME + "_TESTING123"
    #     self._logger = logging.getLogger(__name__)
    #     logging.basicConfig(level=logging.INFO)

    def setUp(self):

        logger = logging.getLogger()
        logger.level = logging.DEBUG
        stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(stream_handler)

        appGuid = 'F3FF80BA-BA05-4277-8063-82A6DB9245A2'
        self.app = QtSingleApplication(appGuid, sys.argv)
        if self.app.isRunning():
            sys.exit(0)
    
        self.engine = QQmlApplicationEngine()
        self.context = self.engine.rootContext()

        self.db = TrawlAnalyzerDB()
        self.context.setContextProperty('db', self.db)

        self.settings = Settings(app=self)
        self.context.setContextProperty("settings", self.settings)

        self.settings._vessel = "Excalibur"
        self.settings._year = "2016"

        self.file_management = FileManagement(app=self, db=self.db)
        self.context.setContextProperty("fileManagement", self.file_management)

        self.data_completeness = DataCompleteness(app=self, db=self.db)
        self.context.setContextProperty("dataCompleteness", self.data_completeness)

        # Actually login
        self.settings._get_credentials()
        self.settings.login(user=self.settings.username, password=self.settings.password)

    def tearDown(self):
        pass

    def test_convert_haul_timezone(self):

        haul_start = arrow.get("2016-05-21T17:56:03-07:00")
        sample = arrow.get("2016-05-21T00:34:51.930167+00:00")
        haul_start = haul_start.to(sample.tzinfo)
        # haul_start.to('utc')
        # , "YYYY-MM-DDTHH:mm:ss.SSSSSSZZ")

        self.assertEqual(sample.tzinfo, haul_start.tzinfo)

    def test_arrow_time_zone_conversion(self):

        pr = cProfile.Profile()
        pr.enable()
        thing = arrow.utcnow()
        for i in range(0, 10000):
            test = arrow.get(str(thing)).to("US/Pacific").isoformat()
        pr.disable()
        s = io.StringIO()
        sortby = 'cumtime'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())

    def test_fast_time(self):

        dt = "2016-05-21T18:14:30.538808+00:00"
        cf = CommonFunctions()

        t=Timer(lambda: arrow.get(dt))
        print("arrow: {0:.6f}s".format(t.timeit(number=27000)))

        t=Timer(lambda: cf.fastStrptime(dt))
        print("fastStrptime: {0:.6f}s".format(t.timeit(number=27000)))

        t=Timer(lambda: cf.fastStrptime(dt).to("US/Pacific"))
        print("fastStrptime + shift time zone: {0:.6f}s".format(t.timeit(number=27000)))

        t=Timer(lambda: cf.fastStrptime(dt).to("US/Pacific").isoformat())
        print("fastStrptime + shift time zone + isoformat: {0:.6f}s".format(t.timeit(number=27000)))

    def test_load_sensor_data(self):

        path = "C:\\2016\\Excalibur"
        item = {"sensorDatabase": os.path.join(path, "sensors_20160521.db"),
                "haulDatabase": os.path.join(path, "trawl_wheelhouse.db"),
                "haul": "201603008001"}
        items = {0: item}
        self.data_completeness.load_sensor_data(items=items)
        print('done')


if __name__ == '__main__':

    unittest.main()