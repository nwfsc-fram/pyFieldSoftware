import os
import sys
import logging
from dateutil import parser
from datetime import datetime, timedelta
from math import pi, radians, sin, cos, atan2, sqrt, isnan
from copy import deepcopy
from PyQt5.QtCore import QVariant, pyqtProperty, pyqtSlot, pyqtSignal, QObject, QThread
from PyQt5.QtQml import QJSValue
from playhouse.shortcuts import model_to_dict, dict_to_model
import shutil
import glob
import arrow
import subprocess
import random

from py.common.FramListModel import FramListModel
from py.hookandline.HookandlineFpcDB_model import database, fn, TideStations, \
    Sites, Lookups, ParsingRules, Personnel, Operations, OperationDetails, \
    Events, EventMeasurements, Settings, JOIN
from peewee import DoesNotExist
from py.hookandline.DataConverter import DataConverter

from py.hookandline.SensorDatabase import SensorDatabase


DATE_TIME_FORMATS = ["M/DD/YY HH:mm:ss", "MM/DD/YY HH:mm:ss", "M/DD/YYYY HH:mm:ss", "MM/DD/YYYY HH:mm:ss",
                     "M/D/YY HH:mm:ss", "M/D/YYYY HH:mm:ss"]


class OperationsModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="id")
        self.add_role_name(name="set_id")
        self.add_role_name(name="date")
        self.add_role_name(name="start_date_time")
        self.add_role_name(name="day_of_cruise")
        self.add_role_name(name="site")
        self.add_role_name(name="event_count")
        self.add_role_name(name="area")

        self.populate_model()

    @pyqtSlot()
    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()

        try:
            site_type_lu_id = Lookups.get(type="Operation", value="Site").lookup
            results = Operations.select(Operations, Events, Sites, Lookups) \
                .join(Sites, JOIN.LEFT_OUTER)\
                .switch(Operations)\
                .join(Events, JOIN.LEFT_OUTER, on=(Events.operation == Operations.operation).alias("events")) \
                .join(Lookups, JOIN.LEFT_OUTER, on=(Events.event_type_lu == Lookups.lookup).alias('event_types'))\
                .where(Operations.operation_type_lu==site_type_lu_id)\
                .order_by(Operations.operation_number.desc(),
                          Events.start_date_time.asc())

            previous_op = ""
            event_count = 1

            for result in results:

                if previous_op != result.operation_number:

                    if previous_op != "":
                        index = self.get_item_index(rolename="set_id", value=previous_op)
                        if index != -1:
                            self.setProperty(index=index, property="event_count", value=event_count)

                    item = dict()
                    item["id"] = result.operation
                    item["set_id"] = result.operation_number

                    item["start_date_time"] = ""
                    if result.events:
                        if result.events.start_date_time:
                            item["start_date_time"] = result.events.start_date_time
                    elif result.date:
                        item["start_date_time"] = parser.parse(result.date).strftime("%Y-%m-%d")

                    item["day_of_cruise"] = result.day_of_cruise
                    item["site"] = result.site.name if result.site else ""

                    if result.events:
                        if result.events.start_date_time:
                            event_count = 1
                        else:
                            event_count = 0
                    else:
                        event_count = 0
                    item["event_count"] = event_count

                    item["area"] = result.area if result.site else ""
                    self.appendItem(item)

                    previous_op = result.operation_number

                else:
                    if result.events.start_date_time is None:
                        event_count = 0
                    else:
                        event_count += 1

            index = self.get_item_index(rolename="set_id", value=previous_op)
            if index != -1:
                self.setProperty(index=index, property="event_count", value=event_count)

        except Exception as ex:

            logging.error("Error populate operations model: {0}".format(ex))

    def delete_record(self, set_id):
        """
        Method to delete the record with the given site_id
        :param set_id:
        :return:
        """
        if set_id == "" or set_id is None:
            return

        idx = self.get_item_index(rolename="set_id", value=set_id)
        self.removeItem(index=idx)


class DropTypesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="id")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()
        results = Lookups.select().where(Lookups.type == "Drop Type",
                                         Lookups.is_active == "True") \
                                         .order_by(Lookups.lookup.asc())
        for result in results:
            item = dict()
            item["text"] = result.value
            item["id"] = result.lookup
            self.appendItem(item)


class SiteTypesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="id")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()
        site_types = Lookups.select().where(Lookups.type == "Site Type",
                                            Lookups.is_active == "True") \
                                    .order_by(Lookups.lookup.asc())
        for site_type in site_types:
            item = dict()
            item["text"] = site_type.value
            item["id"] = site_type.lookup
            self.appendItem(item)
        self.insertItem(0, item={"text": "Select Site Type"})


class TideTypesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="id")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()
        tide_types = Lookups.select().where(Lookups.type == "Tide Type",
                                            Lookups.is_active == "True") \
                                    .order_by(Lookups.lookup.asc())
        for tide_type in tide_types:
            item = dict()
            item["text"] = tide_type.value
            item["id"] = tide_type.lookup
            self.appendItem(item)
        self.insertItem(0, item={"text": "Select Tide Type"})


class TideStatesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="id")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()
        tide_states = Lookups.select().where(Lookups.type == "Tide State",
                                            Lookups.is_active == "True") \
                                    .order_by(Lookups.lookup.asc())
        for tide_state in tide_states:
            item = dict()
            item["text"] = tide_state.value
            item["id"] = tide_state.lookup
            self.appendItem(item)
        self.insertItem(0, item={"text": "Select Tide State"})


class PersonnelModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="id")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """
        Method to populate the model when it is first initialized.  Merely gets all of the
        active personnel
        :return:
        """
        self.clear()
        persons = Personnel.select().where(Personnel.is_active == "True",
                                           Personnel.is_science_team == "True")\
            .order_by(Personnel.last_name.asc(), Personnel.first_name.asc())
        for person in persons:
            item = dict()
            item["text"] = person.last_name + ", " + person.first_name
            item["id"] = person.personnel
            self.appendItem(item)
        self.insertItem(index=0, item={"text": "Select Recorder"})


class EventsModel(FramListModel):

    eventsRowAdded = pyqtSignal(int, int, arguments=["index", "id"])
    eventsRowDeleted = pyqtSignal(int, arguments=["index"])
    noneValuesObtained = pyqtSignal(str, arguments=["msg"])
    errorReceived = pyqtSignal(str, arguments=["msg"])

    def __init__(self):
        super().__init__()
        self.add_role_name(name="event_id")
        self.add_role_name(name="start")
        self.add_role_name(name="adjustTime")
        self.add_role_name(name="end")
        self.add_role_name(name="delete")
        self.add_role_name(name="event")
        self.add_role_name(name="event_type_lu_id")
        self.add_role_name(name="start_date_time")
        self.add_role_name(name="start_latitude")
        self.add_role_name(name="start_longitude")
        self.add_role_name(name="start_depth_ftm")
        self.add_role_name(name="tide_height_m")
        self.add_role_name(name="end_date_time")
        self.add_role_name(name="end_latitude")
        self.add_role_name(name="end_longitude")
        self.add_role_name(name="end_depth_ftm")
        self.add_role_name(name="surface_temperature_avg_c")
        self.add_role_name(name="true_wind_speed_avg_kts")
        self.add_role_name(name="true_wind_direction_avg_deg")
        self.add_role_name(name="drift_speed_kts")
        self.add_role_name(name="drift_direction_deg")
        self.add_role_name(name="drift_distance_nm")
        self.add_role_name(name="drop_type")
        self.add_role_name(name="drop_type_index")
        self.add_role_name(name="drop_type_lu_id")
        self.add_role_name(name="include_in_results")
        self.add_role_name(name="operation_id")

        self._dc = DataConverter()
        self._sensor_database = SensorDatabase()
        self._sensor_database.errorReceived.connect(self.error_received)

        self.populate_list()

    def error_received(self, msg):
        """
        Error received when attempting to query the underlying sensors database
        :param msg:
        :return:
        """
        logging.info(msg)
        self.errorReceived.emit(msg)

    def populate_list(self):
        """
        Method to initially populate the events
        :return:
        """
        self.clear()

        event_item = {self._roles[x].decode('utf-8'): "" for x in self._roles}
        event_item["drop_type_index"] = 0
        event_item["include_in_results"] = True

        for key in event_item:
            if key in ["start", "adjustTime", "end", "delete"]:
                event_item[key] = "disabled"
            # elif key in ["adjustTime"]:
            #     event_item[key] = "enabled"
        events = ["Drop " + str(x) for x in range(1,6)] + ["CTD"]

        # Get the event_type_lu_id for each of the events
        event_types = Lookups.select(Lookups.lookup, Lookups.value).where(Lookups.type == "Event Type")
        types = dict()
        for event_type in event_types:
            types[event_type.value] = event_type.lookup

        for event in events:
            item = deepcopy(event_item)
            item["event"] = event
            item["event_type_lu_id"] = types[event]
            if event == "Drop 1":
                item["start"] = "enabled"

            self.appendItem(item)

    @pyqtSlot(int, QVariant)
    def update_row(self, index, item):
        """
        Method to update a model row and the corresponding table record
        :param index: int - index of the tvEvents table view row being updated
        :param item:
        :return:
        """
        if not isinstance(index, int) or index < 0 or index >= self.count:
            logging.error("Error updating the tvEvents row: {0}".format(item))
            return

        if isinstance(item, QJSValue):
            item = item.toVariant()

        logging.info('Model update: {0}'.format(item))

        # Update the model elements
        lu_id_dict = dict()

        for elem in item:

            value = item[elem] if item[elem] is not None else ""

            self.setProperty(index=index, property=elem, value=value)

            # Prepare records for database updates

            # Convert all boolean objects to strings
            if isinstance(item[elem], bool):
                item[elem] = str(item[elem])

            if "latitude" in elem or "longitude" in elem:
                item[elem] = self._dc.lat_or_lon_to_dd(item[elem])
            if "time" in elem:
                item[elem] = self._dc.time_to_iso_format(item[elem])

            # logging.info(f"elem: {elem}, value: {value} >> db value: {item[elem]}")

            if elem[-3:] == "_id":
                lu_id_dict[elem[:-3]] = item[elem]

        # Drop items that have the _id at the end and instead at those items without that (peewee to db column names diff)
        item = {elem: item[elem] for elem in item if elem[-3:] != '_id'}
        item = {**item, **lu_id_dict}

        # Remove elements not found in the database
        item.pop("drop_type", None)
        item.pop("drop_type_index", None)

        logging.info(f"DB insert: {item}")

        # Add to the database if the event_id is missing or blank
        try:

            # Starting new event, so insert a record into the data
            event_id = self.get(index)["event_id"]

            logging.info('event_id: {0}'.format(event_id))

            if not event_id:

                logging.info(f"adding a new event, index={index}, item={item}")

                # Insert a new Event row
                event_id = Events.insert(**item).execute()

                # Upon successful insertion, update the current model row to set the event_id and
                # change the status of the action buttons
                self.setProperty(index=index, property="event_id", value=event_id)

                self.eventsRowAdded.emit(index, event_id)

            # Ending an event, i.e. when the Stop button has been pressed
            else:

                logging.info(f"updating an event, item = {item}")

                Events.update(**item).where(Events.event == event_id).execute()

            # Update the action model properties if a Start action was submitted, i.e.
            # don't want this to fire when a tide_height_m, drop_type, or include_in_results
            # are submitted
            if "start_date_time" in item and "start_latitude" in item and "start_longitude" in item:

                self.setProperty(index=index, property="start", value="disabled")
                self.setProperty(index=index, property="adjustTime", value="enabled")
                self.setProperty(index=index, property="end", value="enabled")
                self.setProperty(index=index, property="delete", value="enabled")

                # Disable the previous adjustTime and delete buttons if not the first tvEvents row
                if index > 0:
                    self.setProperty(index=index-1, property="delete", value="disabled")

            # Update the action model proprties if an End action was submitted, i.e.
            # don't want this to fire when a tide_height_m, drop_type, or include_in_results
            # are submitted
            if "end_date_time" in item and "end_latitude" in item and "end_longitude" in item:
                self.setProperty(index=index, property="end", value="disabled")
                self.setProperty(index=index, property="adjustTime", value="enabled")
                self.setProperty(index=index, property="delete", value="enabled")

                # Enable the next start button for capturing the next start event, which
                # in turn will enable the tide_height_m, drop_type, and include_in_results
                # columns for manual data entry
                if index+1 < self.count:
                    self.setProperty(index=index+1, property="start", value="enabled")

        except Exception as ex:
            logging.error("Error adding a new event to the database: {0}, {1}".format(item, ex))
            return

    @pyqtSlot(int, str)
    def delete_row(self, index, start_or_end):
        """
        Method to delete an Event row from the database and model
        :param index:
        :param event_id:
        :param start_or_end: str - enumerate list:  start / end
        :return:
        """
        if not isinstance(index, int) or index < 0 or index >= self.count or \
                start_or_end not in ["start", "end"]:
            logging.error("Error deleting a tvEvents row: {0}, {1}"
                          .format(index, start_or_end))
            return

        if start_or_end == "start":

            if self.get(index)["start"] == "enabled":
                return

            item = {"start_date_time": None,
                    "start_latitude": None,
                    "start_longitude": None,
                    "start_depth_ftm": None,
                    "tide_height_m": None
                    }

        elif start_or_end == "end":

            if self.get(index)["end"] == "enabled":
                return

            item = {"end_date_time": None,
                    "end_latitude": None,
                    "end_longitude": None,
                    "end_depth_ftm": None,
                    "surface_temperature_avg_c": None,
                    "true_wind_speed_avg_kts": None,
                    "true_wind_direction_avg_deg": None,
                    "drift_speed_kts": None,
                    "drift_direction_deg": None,
                    "drift_distance_nm": None
                    }

        # Update the model
        for elem in item:
            self.setProperty(index=index, property=elem, value=item[elem])

        # Update the database
        try:
            event_id = self.get(index)["event_id"]

            if start_or_end == "start":
                Events.delete().where(Events.event == event_id).execute()

                self.setProperty(index=index, property="event_id", value=None)
                self.setProperty(index=index, property="start", value="enabled")
                self.setProperty(index=index, property="end", value="disabled")
                self.setProperty(index=index, property="delete", value="disabled")

                if index > 0:
                    self.setProperty(index=index-1, property="delete", value="enabled")

                self.eventsRowDeleted.emit(index)

            elif start_or_end == "end":
                for elem in item:
                    if elem[-3:] == "_id":
                        item[elem[:-3]] = item.pop(elem)
                Events.update(**item).where(Events.event == event_id).execute()

                self.setProperty(index=index, property="end", value="enabled")
                if index+1 < self.count:
                    self.setProperty(index=index+1, property="start", value="disabled")

        except Exception as ex:
            logging.error("Error deleting row from the event model: {0}, {1}"
                          .format(index, start_or_end))

    @pyqtSlot(int, str, bool, bool, QVariant, QVariant)
    def update_times(self, row, date, start_changed, end_changed, new_start_time, new_end_time):
        """
        Method to update a waypoint start time and/or end time
        :param row: int representing the row of the model
        :param date: str representing the date in %m/%d/%y format
        :param start_changed: bool - did the start time change or not
        :param end_changed: bool - did the end time change or not
        :param new_start_time:
        :param new_end_time:
        :return:
        """
        if row < 0 or row >= self.count:
            logging.info(f"row is incorrect: {row}")

        logging.info(f"row={row}, date={date}, start={new_start_time}, end={new_end_time}")

        if not start_changed and not end_changed:
            return

        event_id = self.get(row)["event_id"]
        event = self.get(row)["event"]
        logging.info(f"event_id={event_id} > {event}")
        item = dict()

        logging.info(f"start_changed = {start_changed}, end_changed = {end_changed}")

        if start_changed:

            # Create the start time
            new_start = None
            for f in DATE_TIME_FORMATS:
                try:
                    new_start = arrow.get(f"{date} {new_start_time}", f).replace(tzinfo='US/Pacific')
                    logging.info(f"success parsing start with format = {f} > {new_start.isoformat()}")
                    break
                except Exception as ex:
                    logging.info(f"Failed to parse start date/time using {f} format, start date = {date}, start time = {new_start_time}")

            if new_start:
                item["start_date_time"] = new_start.isoformat()

                # Retrieve the new latitude, longitude, and depth values
                start_status, values = self._sensor_database.get_updated_event_data(datetime=new_start)
                logging.info(f"new_start = {values}")
                item["start_latitude"] = values["Latitude - Vessel"]["value"] if "Latitude - Vessel" in values \
                    and "value" in values["Latitude - Vessel"] else None
                item["start_longitude"] = values["Longitude - Vessel"]["value"] if "Longitude - Vessel" in values \
                    and "value" in values["Longitude - Vessel"] else None
                item["start_depth_ftm"] = values["Depth"]["value"] if "Depth" in values and "value" in values["Depth"] else None

        if end_changed:

            # Create the end time
            new_end = None
            for f in DATE_TIME_FORMATS:
                try:
                    new_end = arrow.get(f"{date} {new_end_time}", f).replace(tzinfo='US/Pacific')
                    logging.info(f"success parsing end with format = {f} > {new_end.isoformat()}")
                    break
                except Exception as ex:
                    logging.info(f"Failed to parse end date/time using {f} format, end date = {date}, end time = {new_start_time}")

            if new_end:

                item["end_date_time"] = new_end.isoformat()

                # Retrieve the new latitude, longitude, and depth values
                end_status, values = self._sensor_database.get_updated_event_data(datetime=new_end)
                item["end_latitude"] = values["Latitude - Vessel"]["value"] if "Latitude - Vessel" in values \
                    and "value" in values["Latitude - Vessel"] else None
                item["end_longitude"] = values["Longitude - Vessel"]["value"] if "Longitude - Vessel" in values \
                    and "value" in values["Longitude - Vessel"] else None
                item["end_depth_ftm"] = values["Depth"]["value"] if "Depth" in values \
                    and "value" in values["Depth"] else None

        """
        Stop if both the start_status and end_status are false.  This means that there were
        errors for both queries against the selected sensor database.  The errorReceived signal
        should have been emitted already
        """
        if start_changed and end_changed:
            if not start_status and not end_status:
                return
        elif start_changed:
            if not start_status:
                return
        elif end_changed:
            if not end_status:
                return

        # Emit the noneValuesObtained signal if None values are obtained for any of the lat/lon/depth values
        msg = ""
        for k, v in item.items():
            if v is None:
                msg += f"{k}, "
        if len(msg) > 2:
            msg = msg[:-2]
            msg = f"{event} time adjuster values were not obtained for the following:\n\n{msg}"
            self.noneValuesObtained.emit(msg)

        # Update the database EVENTS table
        try:
            Events.update(**item).where(Events.event == event_id).execute()
        except Exception as ex:
            logging.error(f"error updating the events table: {ex}")
            return

        # Update the model
        try:
            item["start_date_time"] = new_start_time
            item["end_date_time"] = new_end_time
            for elem in item:
                value = item[elem] if item[elem] is not None else ""
                if "latitude" in elem:
                    value = self._dc.dd_to_formatted_lat_lon(type="latitude", value=value)
                elif "longitude" in elem:
                    value = self._dc.dd_to_formatted_lat_lon(type="longitude", value=value)
                self.setProperty(index=row, property=elem, value=value)
        except Exception as ex:
            logging.error(f"error updating the events model: {ex}")


class SitesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="site")
        self.add_role_name(name="latitude")
        self.add_role_name(name="longitude")
        self.add_role_name(name="is_active")
        self.add_role_name(name="area_description")
        self.add_role_name(name="is_cowcod_conservation_area")
        self.add_role_name(name="name")
        self.add_role_name(name="tide_station")
        self.add_role_name(name="text")

        self.populate_sites()

    def populate_sites(self):
        """
        Method to retrieve all of the sites from the database
        and use these to populate the cbSite combobox on the corresponding
        QML page
        :return:
        """
        self.clear()
        sites = Sites.select().order_by(Sites.name.asc())
        for site in sites:
            site_dict = model_to_dict(site)
            site_dict["text"] = site_dict["name"] + " - " + site_dict["abbreviation"]
            site_dict["name"] = int(site_dict["name"])
            self.appendItem(site_dict)
        self.sort(rolename="name")
        self.insertItem(index=0, item={"text": "Select Site"})


class VesselsModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="lookup_id")
        self.add_role_name(name="text")
        self.add_role_name(name="vessel_number")

        self.populate_vessels()

    def populate_vessels(self):
        """
        Method to retrieve all of the vessels from the database Lookups table
        and use them to populate the cbVesselNumber combobox on the SetIdDialog.qml page
        that is called from MainForm.qml
        :return:
        """
        self.clear()
        vessels = Lookups.select(Lookups.value, Lookups.description, Lookups.lookup)\
            .where(Lookups.type == "Vessel Number",
                   Lookups.is_active == "True")\
            .order_by(Lookups.value.asc())
        for vessel in vessels:
            vessel_record = dict()
            vessel_record["lookup_id"] = vessel.lookup
            vessel_record["vessel_number"] = vessel.value
            vessel_record["text"] = vessel.value + " - " + \
                                  vessel.description if vessel.description else vessel.value + " -"
            self.appendItem(vessel_record)


class SamplingTypesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="lookup_id")
        self.add_role_name(name="text")
        self.add_role_name(name="sampling_type_number")

        self.populate_sampling_types()

    def populate_sampling_types(self):
        """
        Method to retrieve all of the sampling types form the database lookups table
        and use them to populate the cbSamplingTypes combobox on the SetIdDialog.qml page
        that is called from the MainForm.qml
        :return:
        """
        self.clear()
        sampling_types = Lookups.select(Lookups.value, Lookups.description, Lookups.lookup)\
            .where(Lookups.type == "Sampling Type", Lookups.is_active == "True")\
            .order_by(Lookups.value.asc())
        for sampling_type in sampling_types:
            sampling_type_record = dict()
            sampling_type_record["lookup_id"] = sampling_type.lookup
            sampling_type_record["sampling_type_number"] = sampling_type.value
            sampling_type_record["text"] = sampling_type.value + " - " + sampling_type.description \
                if sampling_type.description else sampling_type.value
            self.appendItem(sampling_type_record)


class BackupWorker(QObject):

    serialPortsToggled = pyqtSignal(str)
    jobCompleted = pyqtSignal(bool, str)

    def __init__(self, app=None, backup_path=None, kwargs=None):
        super().__init__()

        self._app = app
        self._backup_path = backup_path
        self._is_running = False
        self._msg = ""
        self._status = True

    def update_path(self, path):
        """
        Method to update the backup path
        :param path:
        :return:
        """
        if not os.path.exists(path):
            logging.error("Unable to update the path as it does not exist: {0}".format(path))
            return

        self._backup_path = path

    def stop(self):
        """
        Method to stop the worker
        :return:
        """
        self._is_running = False

    def backup(self):
        """
        Method to copy the database files to the backup folder
        :return:
        """
        self._msg = ""

        self._is_running = True


        # Stop all of the serial port writing so as to not corrupt the sensors_<daily>.db database
        self.serialPortsToggled.emit("stop")

        # Create backup directory if it does not exist
        try:
            # Check if path exists
            if not os.path.isdir(self._backup_path) or not os.path.exists(self._backup_path):
                os.makedirs(self._backup_path)
        except Exception as ex:
            self._msg += '\nCould not create backup directory {0}, {1}'.format(self._backup_path, ex)
            self._status = False

        # Copy the sensor_<daily>.db database file for the day
        try:
            sensor_db_file_name = self._app.serial_port_manager._sensors_db_path.split("\\")[1]
            src = os.path.join(os.getcwd(), "data", sensor_db_file_name)
            dst = os.path.join(self._backup_path, sensor_db_file_name)
            if src is None:
                self._status = False
                raise Exception("\nERROR: Could not find hookandline_fpc.db database")

            shutil.copy(src=src, dst=dst)

        except Exception as ex:
            self._msg += "\nFailed to copy the current sensor_<daily>.db to {0}".format(self._backup_path)
            self._msg += "\nError: {0}".format(ex)
            self._status = False

        # Copy the hookandline_fpc.db database file
        try:
            # num_files_to_keep = 5
            src = os.path.join(os.getcwd(), "data", "hookandline_fpc.db")
            dst = os.path.join(self._backup_path,
                               "hookandline_fpc_" +
                               datetime.today().strftime('%Y%m%d_%H%M%S') + ".db")
            if src is None:
                self._status = False
                raise Exception('\nERROR: Could not find hookandline_fpc.db database')

            shutil.copy(src=src, dst=dst)

            # Remove files where count of db files is greater than  num_files_to_keep
            # db_files = sorted(glob.glob(self._backup_path + r'\hookandline_fpc_*.db'), reverse=True)
            # if len(db_files) > num_files_to_keep:
            #     for i, file in enumerate(db_files):
            #         if i >= num_files_to_keep:
            #             os.remove(file)

        except Exception as ex:
            self._msg += "\nFailed to copy the hookandline_fpc.db to {0}".format(self._backup_path)
            self._msg += "\nError: {0}".format(ex)

        # Open Windows Explorer and Highlight the newly copied hookandline_fpc.db file
        if self._status:
            subprocess.Popen('explorer /select, "{0}"'.format(dst))
            self._msg += "All files successfully backed up"

        self.jobCompleted.emit(self._status, self._msg)


class FpcMain(QObject):

    operationsModelChanged = pyqtSignal()
    eventsModelChanged = pyqtSignal()
    siteIndexChanged = pyqtSignal()
    sitesModelChanged = pyqtSignal()
    siteTypesModelChanged = pyqtSignal()
    dropTypesModelChanged = pyqtSignal()
    personnelModelChanged = pyqtSignal()
    vesselsModelChanged = pyqtSignal()
    tideTypesModelChanged = pyqtSignal()
    tideStatesModelChanged = pyqtSignal()
    samplingTypesModelChanged = pyqtSignal()
    operationsRowAdded = pyqtSignal(int, int, QVariant, arguments=["id", "details_id", "random_drops"])
    duplicateSetIdFound = pyqtSignal(str, arguments=["set_id"])
    vesselChanged = pyqtSignal()
    fpcChanged = pyqtSignal()
    dayOfCruiseChanged = pyqtSignal()
    backupStatusChanged = pyqtSignal(bool, str, arguments=["status", "msg"])
    softwareTestDeleted = pyqtSignal(str, arguments=['setId'])

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

        self._sites_model = SitesModel()
        self._site_types_model = SiteTypesModel()
        self._drop_types_model = DropTypesModel()
        self._personnel_model = PersonnelModel()
        self._vessels_model = VesselsModel()
        self._tide_types_model = TideTypesModel()
        self._tide_states_model = TideStatesModel()
        self._sampling_types_model = SamplingTypesModel()
        self._events_model = EventsModel()
        self._operations_model = OperationsModel()

        self._vessel_id = -1
        self._vessel_name = ""
        self._vessel_number = ""
        self._get_vessel()

        self._day_of_cruise = self._get_day_of_cruise()
        self._fpc = self._get_fpc_name()    # Necessary to get the day_of_cruise and the cruise_leg first

        self._parsing_rules = self._get_parsing_rules()

        self._dc = DataConverter()

        self._create_backup_thread()

    @pyqtSlot()
    def stop_all_threads(self):
        """
        Method called when the main ApplicationWindow is closing to stop all
        of the threads.  The threads include

            - self._app.serial_port_manager._threads
            - self._backup_thread / self._backup_worker

        :return:
        """

        # Stop the Serial Port Reader Threads
        self._app.serial_port_manager.delete_all_threads()
        # logging.info('serial port threads stopped')

        # Stop the Rebroadcasting of the SBE39 data
        self._app.serial_port_manager.stop_all_serial_port_writers()

        # Stop the Serial Port Database Writer Thread
        if self._app.serial_port_manager._db_thread.isRunning():
            self._app.serial_port_manager._db_worker.stop()
            self._app.serial_port_manager._db_thread.quit()
            self._app.serial_port_manager._db_thread.wait()
        # logging.info('database writer thread stopped')

        if self._app.serial_port_simulator._thread.isRunning():
            self._app.serial_port_simulator._worker.stop()
            self._app.serial_port_simulator._thread.quit()

        # Stop the Backup Thread
        if self._backup_thread.isRunning():
            self._backup_worker.stop()
            self._backup_thread.quit()
            self._backup_thread.wait()
        # logging.info('database backup thread stopped')

    def _create_backup_thread(self):
        """
        Method to create the DatabaseWorker thread that is used
        :return:
        """
        try:
            path = r"C:"
            setting = Settings.get(Settings.parameter == "Backup Folder",
                                Settings.is_active == "True")
            path = setting.value
        except Exception as ex:
            logging.error("Settings backup folder not found: {0}".format(ex))

        self._backup_thread = QThread()
        self._backup_worker = BackupWorker(app=self._app, backup_path=path)
        self._backup_worker.moveToThread(self._backup_thread)
        self._backup_worker.serialPortsToggled.connect(self.toggle_serial_ports)
        self._backup_worker.jobCompleted.connect(self.show_backup_results)
        self._backup_thread.started.connect(self._backup_worker.backup)

    def show_backup_results(self, status=False, msg=""):
        """
        Method to show an Okay dialog
        :param status:
        :param msg:
        :return:
        """
        self.backupStatusChanged.emit(status, msg)
        if self._backup_thread.isRunning():
            self._backup_worker.stop()
            self._backup_thread.quit()

        # Restart all of the serial port manager threads.
        self._app.serial_port_manager.start_all_threads()

    def toggle_serial_ports(self, action=None):
        """
        Method to turn on/off all of the serial ports, used by the BackupWorker when backing up
        the databases
        :return:
        """
        if action == "start":
            self._app.serial_port_manager.start_all_threads()
        else:
            self._app.serial_port_manager.stop_all_threads()

    @pyqtSlot()
    def start_backup(self):
        """
        Method to start the actual backup
        :return:
        """
        if not self._backup_thread.isRunning():

            # Stop all of the serial ports first, otherwise can get database corruption in the sensors database
            self._app.serial_port_manager.stop_all_threads()

            # Start the backup thread
            self._backup_thread.start()
        else:
            status = False
            msg = "The backup is still in progress, please be patient..."
            self.backupStatusChanged.emit(status, msg)

    def stop_backup(self):

        if self._backup_thread.isRunning():
            self._backup_worker.stop()
            self._backup_thread.quit()

    def _get_day_of_cruise(self):
        """
        Method to set the day of the cruise via the start day of the cruise from the Settings table
        :return:
        """
        try:
            today = datetime.now()
            # today = parser.parse("2016-10-07")    # Testing purposes only
            settings = Settings.select()
            for setting in settings:
                if setting.parameter == "Leg 1 Start":
                    leg_1_start = parser.parse(setting.value)
                elif setting.parameter == "Leg 1 End":
                    leg_1_end = parser.parse(setting.value)
                elif setting.parameter == "Leg 2 Start":
                    leg_2_start = parser.parse(setting.value)
                elif setting.parameter == "Leg 2 End":
                    leg_2_end = parser.parse(setting.value)

            # Still in leg 1
            if leg_1_start <= today <= leg_1_end:
                diff = (today - leg_1_start + timedelta(days=1)).days
                self._current_leg = 1
            elif leg_2_start <= today <= leg_2_end:
                leg_1_diff = (leg_1_end - leg_1_start + timedelta(days=1))
                diff = (today - leg_2_start + timedelta(days=1) + leg_1_diff).days
                self._current_leg = 2
            else:
                diff = -1
                self._current_leg = 1

            return diff

        except DoesNotExist as ex:
            logging.error("Start of the cruise date is not defined in the Settings table")
            return -1

    def _get_vessel(self):
        """
        Method to get the vessel_name from the Settings Table
        :return:
        """
        try:
            lookup = Lookups.select(Lookups) \
                .join(Settings, on=(Settings.value == Lookups.lookup).alias('settings')) \
                .where(Settings.parameter == "Vessel").get()
            self._vessel_id = lookup.lookup
            self._vessel_name = lookup.description
            self._vessel_number = lookup.value

        except DoesNotExist as ex:

            logging.error("Default vessel not defined in the Settings table")

    def _get_fpc_name(self):
        """
        Method to retrieve the fpc from the Settings Table
        :return:
        """
        try:
            fpc_param = "Leg 1 FPC" if self._current_leg == 1 else "Leg 2 FPC"
            fpc = Personnel.select(Personnel) \
                .join(Settings, on=(Personnel.personnel == Settings.value).alias("settings")) \
                .where(Settings.parameter == fpc_param).get()
            return fpc.last_name + ", " + fpc.first_name

        except DoesNotExist as ex:
            logging.error("Default FPC not defined in the Settings table")
            return ""

    @pyqtSlot(int, result=QVariant)
    def get_site_data(self, operation_id):
        """
        Method to get all of the Operations, OperationDetails, and Events data to
        repopulate the MainForm.qml
        :param operation_id:
        :return:
        """
        if not isinstance(operation_id, int) or \
            operation_id <= 0:
            logging.error('Error opening previous set id: {0}'.format(operation_id))

        data = dict()

        # Retrieve the operations data
        try:

            Vessels = Lookups.alias()
            operation = Operations.select(Operations, Sites, Vessels)\
                .join(Vessels, on=(Vessels.lookup == Operations.vessel_lu).alias("vessel"))\
                .switch(Operations)\
                .join(Sites, JOIN.LEFT_OUTER, on=(Sites.site == Operations.site).alias("sites"))\
                .where(Operations.operation == operation_id).get()

            try:
                site_type = Lookups.get(Lookups.lookup == operation.site_type_lu)
                site_value = site_type.value
            except Exception as ex:
                site_value = "Fixed"

            op_dict = model_to_dict(operation)

            op_dict["date"] = parser.parse(op_dict["date"]).strftime("%m/%d/%y")
            op_dict["vessel_name"] = operation.vessel.description

            op_dict["site_name"] = ""
            if hasattr(operation, "sites"):
                if operation.sites != {} and operation.sites is not None:
                    op_dict["site_name"] = operation.sites.name + " - " + \
                                           operation.sites.abbreviation

            op_dict["site_type"] = site_value
            if hasattr(operation, "site_types"):
                if operation.site_types != {} and operation.site_types is not None:
                   op_dict["site_type"] = operation.site_types.value

            op_dict["recorder"] = ""
            if hasattr(operation, "recorder"):
                if operation.recorder != {} and operation.recorder is not None:
                    op_dict["recorder"] = operation.recorder.last_name + ", " + \
                                            operation.recorder.first_name

            # 20190915 - Populate the Random Drops (1/2)
            op_dict["random_drop_1"] = ""
            if hasattr(operation, "random_drop_1"):
                if operation.random_drop_1 is not None:
                    op_dict["random_drop_1"] = operation.random_drop_1
            op_dict["random_drop_2"] = ""
            if hasattr(operation, "random_drop_2"):
                if operation.random_drop_2 is not None:
                    op_dict["random_drop_2"] = operation.random_drop_2

            for elem in ["include_in_survey", "is_rca", "is_mpa"]:
                op_dict[elem] = True if op_dict[elem].lower() == "true" else False
            data["operation"] = op_dict

            # logging.info('operation in py: {0}'.format(data["operation"]))

        except Exception as ex:
            logging.error("Error opening previous site, operations error: {0}".format(ex))


        # Retrieve the operation_details data
        try:
            TideTypes = Lookups.alias()
            TideStates = Lookups.alias()
            operation_details = OperationDetails.select(OperationDetails, TideStations, TideTypes, TideStates)\
                .join(TideStations, JOIN.LEFT_OUTER, on=(TideStations.tide_station == OperationDetails.tide_station).alias('tide_stations')) \
                .switch(OperationDetails) \
                .join(TideTypes, JOIN.LEFT_OUTER, on=(TideTypes.lookup == OperationDetails.tide_type_lu).alias('tide_types')) \
                .switch(OperationDetails) \
                .join(TideStates, JOIN.LEFT_OUTER, on=(TideStates.lookup == OperationDetails.tide_state_lu).alias("tide_states"))\
                .where(OperationDetails.operation == operation_id).get()

            data["operation_details"] = model_to_dict(operation_details)

            data["operation_details"].pop("operation", None)
            data["operation_details"] = {k: v if v is not None else "" for k, v in data["operation_details"].items()}

            data["operation_details"]["tide_station"] = ""
            if hasattr(operation_details, "tide_stations"):
                if operation_details.tide_stations is not None:
                    data["operation_details"]["tide_station"] = operation_details.tide_stations.station_name

            data["operation_details"]["tide_type"] = ""
            if hasattr(operation_details, "tide_types"):
                if operation_details.tide_types is not None:
                    data["operation_details"]["tide_type"] = operation_details.tide_types.value

            data["operation_details"]["tide_state"] = ""
            if hasattr(operation_details, "tide_states"):
                if operation_details.tide_states is not None:
                    data["operation_details"]["tide_state"] = operation_details.tide_states.value

            # logging.info('{0}'.format(data["operation_details"]))

        except Exception as ex:
            logging.error("Error opening previous site, operation_details: {0}".format(ex))


        # Retrieve the events data
        try:
            EventTypes = Lookups.alias()
            DropTypes = Lookups.alias()
            events = Events.select(Events, EventTypes, DropTypes)\
                .join(EventTypes, on=(EventTypes.lookup == Events.event_type_lu).alias("event_type"))\
                .switch(Events)\
                .join(DropTypes, on=(DropTypes.lookup == Events.drop_type_lu).alias("drop_type"))\
                .where(Events.operation == operation_id)
            event_list = dict()

            for event in events:
                event_dict = model_to_dict(event)
                event_dict.pop("operation", None)

                # Convert to well-formatted values
                event_dict["start_date_time"] = parser.parse(event_dict["start_date_time"]).strftime("%H:%M:%S")
                event_dict["start_latitude"] = self._dc.dd_to_formatted_lat_lon(type="latitude",
                                                                                value=event_dict["start_latitude"])
                event_dict["start_longitude"] = self._dc.dd_to_formatted_lat_lon(type="longitude",
                                                                                 value=event_dict["start_longitude"])

                if event_dict["end_date_time"] is not None:
                    event_dict["end_date_time"] = parser.parse(event_dict["end_date_time"]).strftime("%H:%M:%S")

                if event_dict["end_latitude"] is not None:
                    event_dict["end_latitude"] = self._dc.dd_to_formatted_lat_lon(type="latitude",
                                                                                  value=event_dict["end_latitude"])
                if event_dict["end_longitude"] is not None:
                    event_dict["end_longitude"] = self._dc.dd_to_formatted_lat_lon(type="longitude",
                                                                                   value=event_dict["end_longitude"])

                event_dict["drop_type_index"] = self._drop_types_model.get_item_index(rolename="id",
                                                                                      value=event_dict["drop_type_lu"])

                event_dict["include_in_results"] = True if event.include_in_results.lower() == "true" else False

                event_list[event.event_type.value] = event_dict

            data["events"] = event_list

        except Exception as ex:
            logging.error("Error opening previous site, events: {0}".format(ex))

        return data

    @pyqtProperty(QVariant, notify=vesselChanged)
    def vesselId(self):
        """
        Method to return the vesselId when the vessel is actually changed
        :return:
        """
        return self._vessel_id

    @pyqtProperty(QVariant, notify=vesselChanged)
    def vesselNumber(self):
        """
        Method to return the self._vessel_number variable
        :return:
        """
        return self._vessel_number

    @pyqtProperty(QVariant, notify=vesselChanged)
    def vesselName(self):
        """

        :return:
        """
        return self._vessel_name

    @vesselName.setter
    def vesselName(self, value):

        try:
            lookup = Lookups.select().where(Lookups.description == value,
                                            Lookups.type == "Vessel Number").get()
            self._vessel_id = lookup.value
            self._vessel_name = value

        except DoesNotExist as ex:
            logging.error('Vessel ID does not exists: {0}'.format(ex))

        self.vesselChanged.emit()

    @pyqtProperty(str, notify=fpcChanged)
    def fpcName(self):
        """
        Method to return the self._fpc variable
        :return:
        """
        return self._fpc

    @fpcName.setter
    def fpcName(self, value):
        """
        Method to set the value of the self._fpc variable
        :param value:
        :return:
        """
        if not isinstance(value, str):
            return

        self._fpc = value
        self.fpcChanged.emit()

    @pyqtProperty(int, notify=dayOfCruiseChanged)
    def dayOfCruise(self):
        """
        Method to return the day of cruise
        :return:
        """
        return self._day_of_cruise

    @pyqtSlot(result=QVariant)
    def get_set_id_sequences(self):
        """
        Method to get the last set_id values for both camera drops and all of the other
        drops and then use these to populate the running sequences in MainForm.qml
        :return:
        """
        try:

            # Get the vessel and leg 1 start settings
            settings = Settings.select().where(Settings.is_active == "True",
                                               Settings.parameter << ["Vessel", "Leg 1 Start"])
            for setting in settings:
                if setting.parameter == "Vessel":
                    lookup = Lookups.get(Lookups.lookup == setting.value)
                    vessel_number = lookup.value
                elif setting.parameter == "Leg 1 Start":
                    cruise_year = datetime.strftime(parser.parse(setting.value), "%y")

            # Get the camera drop value
            camera_drop_model = Lookups.get(Lookups.type == "Sampling Type",
                                            Lookups.description == "Camera Drop")
            camera_drop_value = camera_drop_model.value

            # Get the test drop value
            test_drop_model = Lookups.get(Lookups.type == "Sampling Type",
                                            Lookups.description == "Test Drop")
            test_drop_value = test_drop_model.value

            # Get the software test value
            software_test_model = Lookups.get(Lookups.type == "Sampling Type",
                                              Lookups.description == "Software Test")
            software_test_value = software_test_model.value


            # Retrieve all of the operations records for this vessel / year combo
            operations = Operations.select(Operations.operation_number)\
                .where(fn.Substr(Operations.operation_number, 1, 2) == cruise_year,
                       fn.Substr(Operations.operation_number, 5, 2) == vessel_number)\
                .order_by(fn.Substr(Operations.operation_number, 7,3))

            set_id = []
            for operation in operations:
                set_id.append(operation.operation_number)

            logging.info(f"full set_id: {set_id}")

            camera_set_id = [x for x in set_id if x[2:4] == camera_drop_value]
            test_set_id = [x for x in set_id if x[2:4] == test_drop_value]
            software_test_id = [x for x in set_id if x[2:4] == software_test_value]
            combined_list = camera_set_id + test_set_id
            set_id = [x for x in set_id if x not in combined_list]

            logging.info(f"camera_set_id: {camera_set_id}\ntest_set_id: {test_set_id}"
                         f"\nset_id: {set_id}\nsoftware_test_id: {software_test_id}")

            """
            Set ID is of the following form:
                YY - Year
                TT - Sampling Type - Hook & Line, Camera, Experimental,
                    01 = Hook & Line
                    02 = Camera Drop
                    03 = Genetic Drop
                    04 = Experimental
                    05 = Test Drop
                    06 = Software Test
                VV - Vessel ID
                SSS - Sequence Number - Two different sequences for different Sampling Types
            """
            set_seq = "000"
            if len(set_id) > 0:
                set_seq = set_id[-1][-3:].zfill(3)

            camera_seq = "000"
            if len(camera_set_id) > 0:
                camera_seq = camera_set_id[-1][-3:].zfill(3)

            test_seq = "000"
            if len(test_set_id) > 0:
                test_seq = test_set_id[-1][-3:].zfill(3)

            software_test_seq = "000"
            if len(software_test_id) > 0:
                software_test_seq = software_test_id[-1][-3:].zfill(3)

            logging.info(f"last values found for:   seq: {set_seq}, camera seq: {camera_seq}, "
                         f"test_seq: {test_seq}, software_test_seq: {software_test_seq}")

        except Exception as ex:
            logging.info(f'Error getting valid sequences: {ex}')
            set_seq = "000"
            camera_seq = "000"
            test_seq = "000"

        return {"sequence": set_seq, "camera_sequence": camera_seq, "test_sequence": test_seq,
                "software_test_sequence": software_test_seq}

    @pyqtSlot(QVariant, result=bool)
    def check_sequence_type(self, value):
        """
        Method to check the type of sequence being used.  This is used in the MainForm.qml > toggleLiveDataStream
        to determine if the stream is a Software Test (06) type of data stream
        :param value:
        :return:
        """
        if isinstance(value, str):

            try:

                software_test_model = Lookups.get(Lookups.type == "Sampling Type",
                                                  Lookups.description == "Software Test")
                software_test_value = software_test_model.value
                return software_test_value == value

            except Exception as ex:

                pass

        return False

    @pyqtSlot(str, result=bool)
    def check_for_duplicate_operation(self, set_id):
        """
        Method to check if the given set_id already exists in the database.  If so, return True, if not,
        return False
        :param set_id:
        :return:
        """
        try:
            operation = Operations.get(operation_number=set_id)
            return True

        except DoesNotExist as ex:
            return False

        except Exception as ex:
            return False

    @pyqtSlot(str, int, str, bool, bool, bool)
    def add_operations_row(self, set_id=None, day_of_cruise=None, date=None,
                           include_in_survey=None, is_mpa=None, is_rca=None):
        """
        Method to insert a new record in the OPERATIONS table.  This method is called by
        the onAccept for the user specifying the new set id and occurs when a vessel arrives
        at a new site and is ready to start sampling
        :param set_id: str
        :param day_of_cruise: int
        :param date: str
        :return:
        """
        if set_id is None:
            logging.error('set_id is None: {0}'.format(set_id))
            return

        try:
            fpc_param = "Leg 1 FPC" if self._current_leg == 1 else "Leg 2 FPC"
            fpc = Settings.get(Settings.parameter == fpc_param)
            site_type_lu_id = Lookups.get(type="Operation", value="Site").lookup

            # Select 2 of the 5 drops as being random
            try:
                random_drop_1 = random.randint(1, 5)
                remaining_drops = list(range(1,6))
                remaining_drops.remove(random_drop_1)
                random_drop_2 = random.choice(remaining_drops)
                random_drops = sorted([random_drop_1, random_drop_2])
                logging.info(f"Random drops: {random_drops}")

            except Exception as ex:
                logging.error(f"Error picking the random drops: {ex}")

            operation, status = Operations.get_or_create(operation_number=set_id,
                                                     vessel_lu=self._vessel_id,
                                                     day_of_cruise=day_of_cruise,
                                                     fpc=fpc.value,
                                                     date=parser.parse(date).isoformat(),
                                                     include_in_survey=str(include_in_survey),
                                                     is_mpa=str(is_mpa),
                                                     is_rca=str(is_rca),
                                                     operation_type_lu=site_type_lu_id,
                                                     random_drop_1=random_drop_1,
                                                     random_drop_2=random_drop_2)
            operation_details = OperationDetails.create(operation = operation.operation)
            self._events_model.setProperty(index=0, property="start", value="enabled")
            self._events_model.setProperty(index=self._events_model.count-1, property="start", value="enabled")

            if status:
                # 20190915 - Added the random_drops to the signal
                self.operationsRowAdded.emit(operation.operation, operation_details.operation_details, random_drops)
            else:
                self.duplicateSetIdFound.emit(set_id)

        except DoesNotExist as ex:
            logging.error("Error inserting new operation: {0}".format(ex))

    @pyqtSlot(str, int, QVariant)
    def update_table_row(self, table, primary_key, items):
        """
        Method to update the OPERATIONS table for the given primary key operation_id and
        the field with the given value
        :param table:
        :param primary_key:
        :param item:
        :return:
        """
        if isinstance(items, QJSValue):
            items = items.toVariant()

        for item in items:
            if isinstance(item["value"], bool):
                item["value"] = str(item["value"])

        # logging.info('pk: {0}, table: {1}'.format(primary_key, table))

        if not isinstance(primary_key, int) or primary_key < 1 or not isinstance(table, str):
            logging.error("Unable to update the operation row, invalid parameters: {0}, {1}, {2}"
                          .format(table, primary_key, items))
            return

        update_dict = dict()
        for item in items:
            update_dict[item["field"]] = item["value"]

        # logging.info(f"updating: {update_dict}")

        if table == "Operations":
            for item in items:
                if item["field"] not in Operations._meta.fields:
                    logging.error("Unable to update the row, field not found in the table: {0}, {1}".format(table, item))
                    return
            try:
                Operations.update(**update_dict).where(Operations.operation == primary_key).execute()
            except Exception as ex:
                logging.error("Error updating Operations table: {0}".format(ex))

        elif table == "OperationDetails":
            for item in items:
                if item["field"] not in OperationDetails._meta.fields:
                    logging.error("Unable to update the row, field not found in the table: {0}, {1}".format(table, item))
                    return
                # if isnan(item["value"]) and not isinstance(item["value"], str):
                try:
                    if (isinstance(item["value"], str) and item["value"] == "") or \
                        ((isinstance(item["value"], float) or isinstance(item["value"], int)) and isnan(item["value"])):
                        item["value"] = None
                except Exception as ex:
                    logging.error(f"Error setting the value ({item['value']}) to none: {ex}")

            try:
                OperationDetails.update(**update_dict).where(OperationDetails.operation_details == primary_key).execute()
            except Exception as ex:
                logging.error("Error updating OperationDetails table: {0}".format(ex))

    def _get_parsing_rules(self):
        """
        Method to return all of the active parsing rules from the database
        parsing_rules table
        :return:
        """
        self.rules = []
        rules = ParsingRules.select().order_by(ParsingRules.priority.asc())
        for rule in rules:
            self.rules.append(model_to_dict(rule))

    @pyqtSlot(QVariant, str, result=QVariant)
    def getTideStation(self, site_index, result_type):
        """
        Method to get the tide station associated with the given site index.
        The site index is the index of the self._sites_model
        :param site_index: int
        :param result_type: str - enumerated as:  name, id
        :return:
        """

        # We have "Select Site" at index = 0, so discard a tide station for that selection
        if site_index == -1 or site_index == 0:
            return None

        if result_type not in ["name", "id"]:
            logging.error("Unable to get tide station, invalid result_type: {0}".format(result_type))
            return

        try:
            model_item = self._sites_model.get(site_index)["tide_station"]
            tide_station = TideStations.get(tide_station=model_item["tide_station"])

        except Exception as ex:
            logging.error('{0}'.format(ex))
            return None

        if result_type == "name":
            return tide_station.station_name
        elif result_type == "id":
            return tide_station.tide_station

    @pyqtSlot(QVariant, result=QVariant)
    def getDistanceToTideStation(self, site_index):
        """
        Method to calculate the distance using the haversine formula to calculate
        the distance from the current site to the nearest tide station.  This method
        uses the haversine formulas as articulated here:
        http://www.movable-type.co.uk/scripts/latlong.html

        :param site_index:
        :return:
        """

        # We have "Select Site" for site_index == 0, so discard a distance calculation for that index
        if site_index == -1 or site_index == 0:
            return None

        try:
            model_item = self._sites_model.get(site_index)
            site_lat = model_item["latitude"]
            site_lon = model_item["longitude"]

            tide_station = model_item["tide_station"]
            tide_station = TideStations.get(tide_station=tide_station["tide_station"])
            tide_station_lat = float(tide_station.latitude)
            tide_station_lon = float(tide_station.longitude)

            lon1, lat1, lon2, lat2 = map(radians, [site_lon, site_lat, tide_station_lon, tide_station_lat])
            dlon = lon2 - lon1
            dlat = lat2 - lat1

            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            arc = 6371 * c

            # Convert from KM to NM
            arc = 0.539957 * arc

            # logging.info('{0}, {1} ---> {2}, {3} --> {4}'.format(
            #     site_lon, site_lat, tide_station_lon, tide_station_lat, arc))

        except Exception as ex:
            logging.error('{0}'.format(ex))
            return None

        return '{:.1f}'.format(arc)

    @pyqtSlot(str, name="deleteSoftwareTestSite")
    def delete_software_test_site(self, set_id):
        """
        Method to delete a Software Test Site
        :param set_id:
        :return:
        """
        logging.info(f"deleting software test site_id = {set_id} > {set_id[2:4]}")

        try:
            if self.check_sequence_type(set_id[2:4]):
                logging.info(f"go ahead and nuke it")

                # Delete the operations record, and this cascade down through all of the data collection tables
                Operations.delete().where(Operations.operation_number == set_id).execute()

                # Delete the operations model record
                self.operationsModel.delete_record(set_id=set_id)
                logging.info(f"it is done...")

                # Emit a signal in order to potentially clear the MainForm.qml screen
                # TODO Todd Hay - we should also send this to HookMatrix + CutterStation
                self.softwareTestDeleted.emit(set_id)

        except Exception as ex:

            logging.error(f"Error attempting to delete the software test site {set_id} > {ex}")


    @pyqtProperty(FramListModel, notify=personnelModelChanged)
    def personnelModel(self):
        """
        Method to return the self._personnel_model
        :return:
        """
        return self._personnel_model

    @pyqtProperty(FramListModel, notify=samplingTypesModelChanged)
    def samplingTypesModel(self):
        """
        Method to return the self._sampling_types_model that is used by the
        SetIdDialog.qml cbSiteName combobox that lists out the sampling types
        for the FPC to select during the SetID determination
        :return:
        """
        return self._sampling_types_model

    @pyqtProperty(FramListModel, notify=vesselsModelChanged)
    def vesselsModel(self):
        """
        Method to return the self._vessel_model that is used by the
        SetIdDialog.qml cbSiteName combobox that lists out the vessel
        numbers and names for the FPC to select during the SetID determination
        :return:
        """
        return self._vessels_model

    @pyqtProperty(FramListModel, notify=sitesModelChanged)
    def sitesModel(self):
        """
        Method to return the self._sites_model model
        :return:
        """
        return self._sites_model

    @pyqtProperty(FramListModel, notify=siteTypesModelChanged)
    def siteTypesModel(self):
        """
        Method to return the self._site_types_model
        :return:
        """
        return self._site_types_model

    @pyqtProperty(FramListModel, notify=dropTypesModelChanged)
    def dropTypesModel(self):
        """
        Method to return the self._drop_types_model
        :return:
        """
        return self._drop_types_model

    @pyqtProperty(FramListModel, notify=tideTypesModelChanged)
    def tideTypesModel(self):
        """
        Method to return the self._tide_types_model
        :return:
        """
        return self._tide_types_model

    @pyqtProperty(FramListModel, notify=tideStatesModelChanged)
    def tideStatesModel(self):
        """
        Method to return the self._tide_types_model
        :return:
        """
        return self._tide_states_model

    @pyqtProperty(FramListModel, notify=eventsModelChanged)
    def eventsModel(self):
        """
        Method to return the self._events_model used by the tvEvents table in MainForm.qml
        :return:
        """
        return self._events_model

    @pyqtProperty(FramListModel, notify=operationsModelChanged)
    def operationsModel(self):
        """
        Method to return the self._operations_model used by the OpenOperationDialog.qml dialog
        :return:
        """
        return self._operations_model


if __name__ == '__main__':

    fm = FpcMain()
