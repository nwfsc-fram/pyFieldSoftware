# Python Standard Library
import sys
import logging
import winreg, itertools, glob
from datetime import datetime
import re
from copy import deepcopy

# Third Party Libraries
from PyQt5.QtCore import QVariant, pyqtProperty, pyqtSlot, pyqtSignal, QObject
from playhouse.shortcuts import model_to_dict, dict_to_model
from PyQt5.QtQml import QJSValue
import arrow

# Project Libraries
from py.common.FramListModel import FramListModel


class PersonnelModel(FramListModel):

    def __init__(self, app=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="personName")
        self.add_role_name(name="personId")

    def populate_model(self):
        """
        Method to initialize the personnel based on who is on the vessel
        :return:
        """
        self.clear()
        sql = """
            
        """

class SitesModel(FramListModel):

    def __init__(self, app=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="setId")
        self.add_role_name(name="siteName")
        self.add_role_name(name="area")
        self.add_role_name(name="dateTime")
        self.add_role_name(name="opId")
        self.add_role_name(name="processingStatus")

        self.retrieveSites("today")

    @pyqtSlot(str)
    def retrieveSites(self, filter=None):
        """
        Method to retrieve sites from the FPC database
        :return:
        """
        self.clear()
        sql = """
            SELECT o.operation_number, s.name, o.area, e.event_type_lu_id, 
                CASE WHEN e.start_date_time THEN e.start_date_time
                     ELSE o.date END AS date_time, o.operation_id, o.processing_status               
            FROM OPERATIONS o 
            LEFT JOIN SITES s ON o.site_id = s.site_id
            LEFT JOIN EVENTS e ON o.operation_id = e.operation_id
            WHERE date_time >= ?
            	AND (e.EVENT_TYPE_LU_ID IS NULL OR e.EVENT_TYPE_LU_ID = 97)
            ORDER BY date_time desc, o.operation_number desc
        """
        if filter == "today":
            today = arrow.now('US/Pacific').replace(hour=0, minute=0, second=0, microsecond=0).format('YYYY-MM-DDTHH:mm:ss')
            params = [today, ]
        elif filter == "yesterday":
            yesterday = arrow.now('US/Pacific').shift(days=-1).replace(hour=0, minute=0, second=0, microsecond=0).format('YYYY-MM-DDTHH:mm:ss')
            params = [yesterday, ]
        elif filter == "all":
            params = [arrow.now('US/Pacific').shift(years=-100).format('YYYY-MM-DDTHH:mm:ss'),]
        logging.info(f"params: {params}")
        results = self._app.rpc.execute_query(sql=sql, params=params)
        header = ["setId", "siteName", "area", "eventTypeLuId", "dateTime", "opId", "processingStatus"]

        for row in results:
            row_dict = dict(zip(header, row))
            row_dict["dateTime"] = arrow.get(row_dict["dateTime"]).format("MM/DD/YYYY HH:mm:ss")
            self.appendItem(row_dict)

        # Get the Vessel Name
        sql = """
            SELECT l.Description FROM LOOKUPS l 
                INNER JOIN SETTINGS s ON s.VALUE = l.LOOKUP_ID
                WHERE s.PARAMETER = 'Vessel'
        """
        vessel_name = self._app.rpc.execute_query(sql=sql)
        if vessel_name:
            vessel_name = vessel_name[0][0]
            self._app.state_machine.vessel = vessel_name
            logging.info(f"vessel: {self._app.state_machine.vessel}")

class Sites(QObject):

    sitesModelChanged = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db
        self._sites_model = SitesModel(app=app)

    @pyqtProperty(FramListModel, notify=sitesModelChanged)
    def sitesModel(self):
        """
        Method to return the self._sites_model to QML
        :return:
        """
        return self._sites_model

    @pyqtSlot(name="finishedAndValidate")
    def finished_and_validate(self):
        """
        Method called by DropsScreen.qml when the Finished & Validate button is clicked.
        This will run any validations as well as mark the site as completed
        :return:
        """
        # Mark the site as completed
        try:
            # Update the database
            sql = """
                UPDATE OPERATIONS SET PROCESSING_STATUS = 'finished'
                WHERE OPERATION_ID = ?
            """
            params = [self._app.state_machine.siteOpId, ]
            self._app.rpc.execute_query(sql=sql, params=params)

            # Update the sitesModel
            idx = self.sitesModel.get_item_index(rolename="setId",
                                                 value=self._app.state_machine.setId)
            if idx != -1:
                self.sitesModel.setProperty(index=idx, property="processingStatus",
                                            value="finished")

        except Exception as ex:

            logging.error(f"Error marking the site as finsihed: {ex}")

        # Run any validations
        try:

            pass

        except Exception as ex:

            logging.error(f"Error running site-level validations: {ex}")

    @pyqtSlot(int, int, name="reopenSite")
    def reopen_site(self, model_index, site_op_id):
        """
        Method to reopen an existing site.  This changes the OPERATIONS table
        PROCESSING_STATUS column from finished to NULL
        :param site_op_id: int, primary key of the site operation_id
        :return:
        """
        try:

            # Update the database record
            sql = """
                UPDATE OPERATIONS SET PROCESSING_STATUS = NULL
                    WHERE OPERATION_ID = ?;
            """
            params = [site_op_id, ]
            self._app.rpc.execute_query(sql=sql, params=params)

            # Update the model
            self.sitesModel.setProperty(index=model_index, property="processingStatus", value=None)

        except Exception as ex:

            logging.error(f"Error reopening the site: {ex}")
