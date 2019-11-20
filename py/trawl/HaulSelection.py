__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        HaulSelection.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 11, 2016
# License:     MIT
#-------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QVariant, Qt, QModelIndex, QThread
from PyQt5.Qt import QJSValue, QQmlComponent, QWidget
from PyQt5.QtWidgets import QApplication

from py.common.FramListModel import FramListModel
from datetime import datetime, timedelta
from dateutil import tz, parser
import logging
import unittest
import inspect
import email
from xmlrpc import client as xrc

from py.trawl.TrawlBackdeckDB_model import Settings, Hauls, Catch, Specimen
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model


class HaulListModel(FramListModel):

    def __init__(self, app=None, db=None, parent=None):
        super().__init__()

        self._app = app
        self._db = db
        self.add_role_name(name="status")
        self.add_role_name(name="haulId")
        self.add_role_name(name="haulNumber")
        self.add_role_name(name="date")
        self.add_role_name(name="startTime")
        self.add_role_name(name="endTime")
        self.add_role_name(name="isTest")

    @pyqtSlot()
    def add_test_haul(self):
        """
        Method to add a test haul to the model + database
        :param haul: QJSValue - dictionary contained in a QJSValue object
        :return: None
        """
        # Add to the Database
        sql = "INSERT INTO HAULS('HAUL_NUMBER', 'START_DATETIME', 'END_DATETIME', 'PROCESSING_STATUS', 'IS_TEST') " + \
            "VALUES(?, ?, ?, ?, ?);"
        now = datetime.now()
        date = now.strftime("%m/%d/%Y")
        start = now
        start_time = start.strftime("%H:%M:%S")
        end = (now + timedelta(hours=1))
        end_time = end.strftime("%H:%M:%S")
        haul_number = "t" + str(round((now - datetime.utcfromtimestamp(0)).total_seconds() * 1000.0))

        # Get all Test Hauls - Adjust the last three digits to be 900 and greater so as to not conflict
        # with other haul numbers when we print specimen labels where we only keep the last three digits
        # of the haul
        test_hauls = Hauls.select(fn.substr(Hauls.haul_number, 12, 3).alias('test_haul_number'))\
            .where(Hauls.haul_number.contains("t"))\
            .order_by(fn.substr(Hauls.haul_number, 12, 3).desc())
        # for test_haul in test_hauls:
        #     logging.info('{0}'.format(test_haul.test_haul_number))

        try:
            last_test_haul_num = test_hauls.get().test_haul_number
            if int(last_test_haul_num) < 900:
                haul_last_three = "900"
            else:
                haul_last_three = str(int(last_test_haul_num) + 1)
        except DoesNotExist as dne:
            haul_last_three = "900"
        except Exception as ex:
            haul_last_three = "900"

        haul_number = haul_number[:-3] + haul_last_three

        # logging.info('last test haul num: {0} > {1}'.format(last_test_haul_num, haul_number))

        haul = {"haulNumber": haul_number, "date": date,
            "startTime": start_time, "endTime": end_time, "status": "Active", "isTest": "True"}

        params = [haul_number, start.isoformat(), end.isoformat(), "Active", "True"]
        self._db.execute(query=sql, parameters=params)
        haul_id = self._db.get_last_rowid()  # Return the primary key of the newly added record

        # Add to the Model - N.B. need to first get the newly added HAUL_ID and add that to haul
        haul["haulId"] = haul_id

        is_added = False
        for i in range(self.count):
            if "t" in self.get(i)["haulNumber"]:
                continue
            self.insertItem(i, haul)
            is_added = True
            break
        if not is_added:
            self.appendItem(haul)

    @pyqtSlot(int)
    def delete_test_haul(self, index):
        """
        Method to delete the test haul and associated catch_partition + specimen data from the DB
        :param index: int - representing the index location in the model
        :return:
        """
        if index is None or index == -1 or not isinstance(index, int):
            return

        item = self.get(index)
        status = item["status"]
        haul_id = item["haulId"]

        # Delete from the Model
        self.removeItem(index)

        # Update the state machine as appropriate
        if status == "Selected" or self.count == 0:
            self._app.state_machine.haul = None

        try:
            haul = Hauls.get(Hauls.haul == haul_id)
            haul.delete_instance(recursive=True, delete_nullable=True)

        except Exception as ex:
            pass

    @pyqtSlot(int, result=bool)
    def check_haul_for_data(self, index=None):
        """
        Method to determine if a given selected haul (defined by row_index) has catch or specimen data
        :param index: int - index of the hauls model selected
        :return:
        """
        if index is None or index == -1 or not isinstance(index, int):
            return

        item = self.get(index)
        haul_id = item["haulId"]

        catch = Catch.select().where(Catch.operation == haul_id)
        if catch.count() > 0:
            return True

        for species in catch:
            specimen = Specimen.select().where(Specimen.catch == species.catch)
            if specimen.count() > 0:
                return True

        return False

    @pyqtSlot(QVariant, QVariant, str)
    def set_haul_processing_status(self, current_id, haul_id, processing_status):
        """
        Method to update the status of the haul in the model + database
        :param haul_id: int - representing the haul to set as Selected
        :param row_num: int - row number in the tvHauls model
        :return: None
        """
        if haul_id is None or not isinstance(haul_id, int):
            return

        if processing_status not in ["Selected", "Completed"]:
            return

        # Update the model
        # Set currently selected row to Active
        if current_id:
            old_row_num = self.get_item_index("haulId", current_id)
            self.setProperty(old_row_num, "status", "Active")

            sql = "UPDATE HAULS SET PROCESSING_STATUS = 'Active' WHERE HAUL_ID = ?;"
            params = [current_id, ]
            self._db.execute(query=sql, parameters=params)

        # Set the new row in the model to Selected
        row_num = self.get_item_index("haulId", haul_id)
        self.setProperty(row_num, "status", processing_status)

        # Update the Database
        sql = "UPDATE HAULS SET PROCESSING_STATUS = ? WHERE HAUL_ID = ?;"
        params = [processing_status, haul_id]
        self._db.execute(query=sql, parameters=params)

        # Update Haul State
        if processing_status == "Completed":
            self._app.state_machine.haul = None
        elif processing_status == "Selected":
            self._app.state_machine.haul = haul_id


class GetHaulsWorker(QObject):

    haulsReceived = pyqtSignal(list)

    def __init__(self, app=None, db=None, args=(), kwargs=None):
        super().__init__()
        self._app = app
        self._db = db
        self._is_running = False
        self.hauls = []

        self._ip = self._app.settings.wheelhouseIpAddress
        self._port = self._app.settings.wheelhouseRpcServerPort

    def run(self):

        self._is_running = True

        haul_data = []

        # Query the wheelhouse via the RpcServer for the daily hauls
        ip = self._app.settings.wheelhouseIpAddress
        port = self._app.settings.wheelhouseRpcServerPort
        logging.info('Wheelhouse RpcServer address: ' + str(ip) + ", " + str(port))

        real_hauls = []
        try:
            server = xrc.ServerProxy('http://' + ip + ':' + str(port), allow_none=True, use_builtin_types=True)
            real_hauls = server.get_hauls()
            logging.info('Number of hauls received from wheelhouse: ' + str(len(real_hauls)))

        except Exception as ex:
            logging.info('Error contacting wheelhouse computer: ' + str(ex))

        # template = ['haul_number', 'start_datetime', 'end_datetime', 'latitude_min', 'longitude_min', 'latitude_max', 'longitude_max',
        #           'depth_min', 'depth_max', 'vessel_name', 'vessel_color', 'pass_number', 'leg_number']
        # template = {x:None for x in template}

        # For the newly retrieve haul, insert into the database if the haul doesn't exist, otherwise get the haul
        for real_haul in real_hauls:
            # logging.info('real_haul: ' + str(real_haul))
            try:
                logging.info(f"real_haul: {real_haul}")
                logging.info(f"real_haul depth data: {real_haul['depth']}, {real_haul['depth_uom']}")
            except Exception as ex:
                logging.error(f"real haul depth data is blowing up: {ex}")

            current_haul, created = Hauls.get_or_create(haul_number=real_haul["haul_number"],
                                                        defaults={'start_datetime': real_haul["start_time"] if "start_time" in real_haul else None,
                                                                  'end_datetime': real_haul["end_time"] if "end_time" in real_haul else None,
                                                                  'latitude_min': real_haul["latitude"] if "latitude" in real_haul else None,
                                                                  'longitude_min': real_haul["longitude"] if "longitude" in real_haul else None,
                                                                  'latitude_max': real_haul["latitude"] if "latitude" in real_haul else None,
                                                                  'longitude_max': real_haul["longitude"] if "longitude" in real_haul else None,
                                                                  'depth_min': real_haul["depth"] if "depth" in real_haul else None,
                                                                  'depth_max': real_haul["depth"] if "depth" in real_haul else None,
                                                                  'depth_uom': real_haul["depth_uom"] if "depth_uom" in real_haul else None,
                                                                  'vessel_name': real_haul["vessel_name"] if "vessel_name" in real_haul else None,
                                                                  'vessel_color': real_haul["vessel_color"] if "vessel_color" in real_haul else None,
                                                                  'pass_number': real_haul["pass"] if "pass" in real_haul else None,
                                                                  'leg_number': real_haul["leg"] if "leg" in real_haul else None,
                                                                  'is_test': "False"})

            if created:
                Hauls.update(processing_status="Active").where(Hauls.haul_number == real_haul["haul_number"]).execute()
            else:
                if "start_time" in real_haul:
                    # logging.info('start > db / real_haul: ' + str(real_haul["haul_number"]) + ', '+ str(current_haul.start_datetime) + ' / ' + str(real_haul["start_time"]))

                    if current_haul.start_datetime != real_haul["start_time"]:
                        Hauls.update(start_datetime = real_haul["start_time"], end_datetime = None).where(Hauls.haul_number == real_haul["haul_number"]).execute()
                else:
                    Hauls.update(start_datetime=None).where(Hauls.haul_number == real_haul["haul_number"]).execute()
                if "end_time" in real_haul:
                    if current_haul.end_datetime != real_haul["end_time"]:
                        Hauls.update(end_datetime = real_haul["end_time"]).where(Hauls.haul_number == real_haul["haul_number"]).execute()
                    # logging.info('end > db / real_haul: ' + str(real_haul["haul_number"]) + ', ' + str(
                    #         current_haul.end_datetime) + ' / ' + str(real_haul["end_time"]))
                else:
                    Hauls.update(end_datetime=None).where(Hauls.haul_number == real_haul["haul_number"]).execute()


            current_haul = Hauls.get(haul_number=real_haul["haul_number"])

            haul_data.append(model_to_dict(current_haul))

        self._is_running = False
        self.haulsReceived.emit(haul_data)


class HaulSelection(QObject):
    """
    Class for the HaulSelectionScreen.
    """
    haulsModelChanged = pyqtSignal(str)

    def __init__(self, app=None, db=None):
        super().__init__()

        # No-No way of getting a handle to the calling object, replaced by passing in the app object itself
        # self.app = inspect.currentframe().f_back.f_locals['self']
        self._app = app

        self._logger = logging.getLogger(__name__)
        self._db = db

        self._hauls_model = HaulListModel(app=self._app, db=self._db)

        self._local_hauls = []
        self._wheelhouse_hauls = []
        self._timeframe = 0

        self._get_hauls_thread = QThread()
        self._get_hauls_worker = GetHaulsWorker(app=self._app, db=self._db)
        self._get_hauls_worker.moveToThread(self._get_hauls_thread)
        self._get_hauls_worker.haulsReceived.connect(self._wheelhouse_hauls_received)
        self._get_hauls_thread.started.connect(self._get_hauls_worker.run)

        self._get_hauls_from_db()

    @pyqtProperty(FramListModel, notify=haulsModelChanged)
    def HaulsModel(self):
        """
        Method to return the self._hauls_model
        :return: FramListModel
        """
        return self._hauls_model

    @pyqtSlot(str)
    def _get_hauls_from_db(self, time_frame="today"):
        """
        Method to query the trawl_backdeck.db to retrieve all of the test hauls
        :return:
        """
        if time_frame not in ["today", "two days", "all"]:
            return
        adapter = {"today": 0, "two days": 1, "all": 1000}
        time_frame = adapter[time_frame]

        # Retrieve all test hauls from the database
        self._local_hauls = []

        # logging.info('timedelta: ' + str(timedelta(days=time_frame)))
        # start_datetime = (datetime.now() - timedelta(hours=48)).isoformat()
        start_datetime = (datetime.now().date() - timedelta(days=time_frame)).isoformat()
        # logging.info('start_datetime: ' + str(start_datetime))
        local_hauls = Hauls.select().where((Hauls.start_datetime >= start_datetime) | (Hauls.is_test == "True"))
        for haul in local_hauls:
            self._local_hauls.append(model_to_dict(haul))

        # self._local_hauls = sorted(self._local_hauls, key=lambda x: (x["haul_number"].isdigit(), x["haul_number"]))

        self._hauls_model.clear()
        self._add_model_items(hauls=self._local_hauls)

    @pyqtSlot()
    def _get_hauls_from_wheelhouse(self):
        """
        Method to query the wheelhouse RpcServer to retrieve the hauls for the past 24 hours
        :return:
        """
        if self._get_hauls_thread.isRunning():
            return

        self._get_hauls_thread.start()

    def _wheelhouse_hauls_received(self, hauls):

        self._get_hauls_thread.quit()

        self._wheelhouse_hauls = hauls
        self._add_model_items(hauls=self._wheelhouse_hauls)

    def _add_model_items(self, hauls):
        """
        Method to add a select set of hauls to the self._hauls_model
        :param hauls:
        :return:
        """
        for h in hauls:

            haulNumber = h["haul_number"]
            if "t" not in haulNumber:
                haulNumber = str(haulNumber[-3:])

            index = self._hauls_model.get_item_index(rolename="haulNumber", value=haulNumber)
            # if index != -1:
            #     logging.info('haul exists: ' + str(self._hauls_model.get(index)))
            if index == -1:
                # logging.info('missing haul: ' + str(index) + ', value: ' + str(h["haul_number"]))

                haul = dict()
                haul["haulId"] = h["haul"]
                haul["status"] = h["processing_status"]
                if 't' in h["haul_number"]:
                    haul["haulNumber"] = h["haul_number"]
                elif h["haul_number"]:
                    haul["haulNumber"] = str(h["haul_number"][-3:])
                haul["date"] = parser.parse(h["start_datetime"]).strftime("%m/%d/%Y") if h["start_datetime"] else ""
                haul["startTime"] = parser.parse(h["start_datetime"]).strftime("%H:%M:%S") if h[
                    "start_datetime"] else ""
                haul["endTime"] = parser.parse(h["end_datetime"]).strftime("%H:%M:%S") if h["end_datetime"] else ""
                if h["is_test"]:
                    haul["isTest"] = h["is_test"]
                else:
                    haul["isTest"] = "False"
                self._hauls_model.appendItem(haul)

                if haul['status'] == 'Selected':
                    self._app.state_machine.selectedHaulId = haul['haulId']

            else:
                # Haul was found in the model, update the start and end times if they are different from what is currently in the model
                if h["start_datetime"]:
                    if parser.parse(h["start_datetime"]).strftime("%H:%M:%S") != self._hauls_model.get(index)["startTime"]:
                        self._hauls_model.setProperty(index=index, property="startTime",
                                                  value=parser.parse(h["start_datetime"]).strftime("%H:%M:%S"))
                        self._hauls_model.setProperty(index=index, property="endTime", value=None)
                else:
                    self._hauls_model.setProperty(index=index, property="startTime", value=None)
                if h["end_datetime"]:
                    if parser.parse(h["end_datetime"]).strftime("%H:%M:%S") != self._hauls_model.get(index)["endTime"]:
                        self._hauls_model.setProperty(index=index, property="endTime", value=parser.parse(h["end_datetime"]).strftime("%H:%M:%S"))
                else:
                    self._hauls_model.setProperty(index=index, property="endTime", value=None)

        items = self._hauls_model.items
        items = sorted(items, key=lambda x: (x["haulNumber"].isdigit(), x["haulNumber"]))
        self._hauls_model.clear()
        self._hauls_model.setItems(items)
