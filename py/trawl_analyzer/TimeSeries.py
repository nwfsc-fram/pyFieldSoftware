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
from random import randrange, random, uniform
from collections import OrderedDict
import math
from geographiclib.geodesic import Geodesic

import arrow
from datetime import datetime, timedelta
import time
import numpy as np
from peewee import JOIN, fn
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QThread, QObject, QVariant, QDateTime, QPointF
from PyQt5.QtQuick import QQuickItem
from PyQt5.QtQml import QJSValue, QQmlComponent
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis
from PyQt5.QtGui import QPolygonF, QPainter, QCursor
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

import decimal
import unittest
import cProfile
import pstats, sys
# from scipy.signal import argrelextrema

from py.trawl_analyzer.CommonFunctions import CommonFunctions
from py.trawl_analyzer.TrawlAnalyzerDB_model import OperationsFlattenedVw, \
    MeasurementStreams, OperationMeasurements, ParsingRulesVw, Events, Lookups, EquipmentLu, Comments, Operations, \
    OperationAttributes, ReportingRules, PerformanceDetails, OperationTracklines, LookupGroups, GroupMemberVw

from  py.common.FramListModel import FramListModel
from playhouse.shortcuts import model_to_dict
from copy import deepcopy

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import gridspec
import matplotlib.dates as mdates
from matplotlib import animation
from matplotlib.widgets import Cursor
from matplotlib.patches import Rectangle
from matplotlib import ticker
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter, AutoLocator, AutoMinorLocator
from matplotlib.widgets import RectangleSelector

import pandas as pd
import arrow
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QMainWindow, QSizePolicy
from dateutil.tz import tzlocal
from _collections import OrderedDict

from py.trawl_analyzer.DistanceFished import DistanceFished

# import seaborn as sns
# sns.set(style="white", palette="Set2")

# Constants
FTM_PER_M = 1.8288              # Fathoms Per Meters
N_PER_M = 0.000539957           # Nautical Miles Per Meter
SEC_PER_DAY = 86400             # Seconds Per Day
EPSILON = 0.000001              # Used to compare float values

MIN_LAT = 32.0
MAX_LAT = 49.0
MIN_LON = -127.0
MAX_LON = -116.0
LAT_LON_BUFFER = 0.01       # Degrees to buffer around min/max lat/lon values

# Technique Types
TECHNIQUES = ["Catenary", "Vessel + Trig", "GCD + Trig", "ITI R/B", "ITI $IIGLL", "ITI R/B + Trig"]
                # "Range Ext + Trig", "Range Ext + Cat + Trig",

TECHNIQUES_MAPPING = {
    "Catenary": {"value": "Catenary", "subvalue": "Catenary"},
    "Vessel + Trig": {"value": "Vessel gear track", "subvalue": "trig method"},
    "GCD + Trig": {"value": "Vessel gcd", "subvalue": "trig method"},
    "ITI R/B": {"value": "Smoothed GPS/Range/Bearing Generated Track", "subvalue": "GPS/Range/Bearing"},
    "ITI $IIGLL": {"value": "Smoothed IIGLL gear track", "subvalue": "Smoothed IIGLL gear track"},
    "ITI R/B + Trig": {"value": "Smoothed GPS/Range/Bearing Generated Track", "subvalue": "trig method"}
}

MEANS_TYPES = {"Depth": {"basis": "Headrope", "type": "Depth", "default equipment": "(SBE39)"},
               "Doorspread": {"basis": "Doors", "type": "Spread Distance", "default equipment": "(PI44) ($PSIMP,D1)"},
               "Latitude": {"basis": "Gear", "type": "Latitude", "default equipment": "Catenary"},
               "Longitude": {"basis": "Gear", "type": "Longitude", "default equipment": "Catenary"},
               "Net Height": {"basis": "Seafloor", "type": "Headrope Height", "default equipment": "(PI44) ($PSIMP,D1)"},
               "Temperature": {"basis": "Headrope", "type": "Temperature", "default equipment": "(SBE39)"},
               "Wingspread": {"basis": "Wings", "type": "Spread Distance", "default equipment": "(PI44) ($PSIMP,D1)"}
             }


class HaulsModel(FramListModel):

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="haul")

        self._functions = CommonFunctions()

    @pyqtSlot()
    def populate_model(self):
        """
        Method to populate the model
        :return:
        """
        self.clear()

        try:
            # .distinct(OperationsFlattenedVw.tow_name) \
            ops = OperationsFlattenedVw.select()\
                .join(Events, on=(Events.operation == OperationsFlattenedVw.operation)).alias('events')\
                .where(OperationsFlattenedVw.cruise == self._functions.get_cruise_id(year=self._app.settings.year,
                                                                                     vessel=self._app.settings.vessel),
                       OperationsFlattenedVw.operation_type == "Tow")\
                .order_by(OperationsFlattenedVw.tow_name) \
                .distinct()
            items = [{"haul": "Select Haul"}] + [{"haul": x.tow_name} for x in ops]
            for item in items:
                self.appendItem(item)

        except Exception as ex:

            logging.info('Error populating the TimeSeries HaulsModel: {0}'.format(ex))


class DataPointsModel(FramListModel):

    timeSeriesUpdated = pyqtSignal(str, QVariant, QVariant, QVariant, arguments=["time_series", "df", "valid_ids",
                                                                                "invalid_ids"])

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="id")
        self.add_role_name(name="datetime")
        self.add_role_name(name="reading_numeric")
        self.add_role_name(name="status")
        self.add_role_name(name="change")

        self._functions = CommonFunctions()

        self._valid_filter = False
        self._invalid_filter = True

        self._time_series = None
        self._df = None

    @pyqtSlot(QVariant)
    def populate_model(self, time_series, df_time_series):
        """
        Method to populate the model
        :param time_series: dict - the time series, as defined in the time series data loading
        :return:
        """
        if not isinstance(df_time_series, pd.DataFrame) or df_time_series.empty:
            return

        self._time_series = time_series

        df_time_series = df_time_series.rename(columns={"times": "datetime",
                                                        "values": "reading_numeric",
                                                        "invalid": "status"})
        df_time_series["datetime"] = df_time_series["datetime"].apply(lambda x: arrow.get(x).isoformat())
        df_time_series.loc[:, "change"] = ""
        self._df = df_time_series

        self.filter_values()

    def toggle_rows_validity(self, ids, value):
        """
        Method to set rows, defined by the operation_measurement_id values in ids to be invalid.  This is called when
        a user enters the invalidData tool mode and then starts selecting points on the time series or map displays.
        These values are then considered invalid, so we need to update this model accordingly
        :param ids: list - contains operation_measurement_id values that have beeen set to invalid
        :param value: bool - True = set to invalid, False = set to valid
        :return:
        """
        if not isinstance(ids, list) or len(self.items) == 0 or not isinstance(value, bool):
            return

        logging.info(f"dataPointsModel updating IDs: {ids} >>> {value}")

        for id in ids:
            idx = self.get_item_index(rolename="id", value=id)
            if idx != -1:
                self.setProperty(index=idx, property="status", value=value)
                self.setProperty(index=idx, property="change", value="")

    @pyqtSlot()
    def save_validity_changes(self):
        """
        Method called by InvalidDataDialog.qml that toggles the status role of the tvDataPoints
        :param rows: list of row numbers to toggle
        :return:
        """

        # Get rows that have Yes in change column
        rows = self.where(rolename="change", value="Yes")
        logging.info(f"rows = {rows}")


        if rows is None or rows[0] is None:
            return

        invalid_ids = [x["item"]["id"] for x in rows if x["item"]["status"]]
        valid_ids = [x["item"]["id"] for x in rows if not x["item"]["status"]]
        logging.info(f"invalid_ids: {invalid_ids},    valid_ids: {valid_ids}")

        try:

            # Update the database in two separate operations, first change the invalid_ids to is_not_valid=True
            # and then changing the valid_ids to is_not_valid=False

            # with self._app.settings._database.atomic():
                # OperationMeasurements.insert_many(insert_list).execute()

            # Change the invalid IDs to valid IDs
            if len(invalid_ids) > 0:
                OperationMeasurements.update(is_not_valid=False)\
                    .where(OperationMeasurements.operation_measurement << invalid_ids).execute()
                mask = (self._df["id"].isin(invalid_ids))
                self._df.loc[mask, "status"] = False
                self.toggle_rows_validity(ids=invalid_ids, value=False)

            # Change the valid IDs to invalid IDs
            if len(valid_ids) > 0:
                OperationMeasurements.update(is_not_valid=True)\
                    .where(OperationMeasurements.operation_measurement << valid_ids).execute()
                mask = (self._df["id"].isin(valid_ids))
                self._df.loc[mask, "status"] = True
                self.toggle_rows_validity(ids=valid_ids, value=True)

            self._df.loc[:, "change"] = ""

            # Update the Model
            self.filter_values()

            # Emit a signal to time series class, which will then do updates to the graph + map + time_series dict
            self.timeSeriesUpdated.emit(self._time_series, self._df, invalid_ids, valid_ids)

        except Exception as ex:
            logging.error(f"Error updating the validity status of points: {ex}")

    @pyqtSlot(str, bool)
    def filter_values(self, type=None, status=None):
        """
        Method to filter values, i.e. turn on/off valid or invalid values.  Combinations include:

        valid + true
        valid + false
        invalid + true
        invalid + false

        :param type: str - enumeratation - valid / invalid
        :param status: bool - true / false - turn on or off
        :return:
        """
        if type == "valid":
            self._valid_filter = status
        elif type == "invalid":
            self._invalid_filter = status

        if self._valid_filter and self._invalid_filter:
            mask = (self._df["status"]) | (~self._df["status"])
        elif self._invalid_filter:
            mask = (self._df["status"])
        elif self._valid_filter:
            mask = (~self._df["status"])
        else:
            mask = (self._df["id"] == -1)

        df_active = self._df.loc[mask]
        df_dict = df_active.to_dict('records')
        self.setItems(df_dict)


class TimeSeriesModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="text")

    def reset_model(self):
        """
        Method to clear the model for new loading
        :return:
        """
        self.clear()
        item = {"text": "Select Time Series"}
        self.appendItem(item)


class BreakIt(Exception): pass


class AvailableImpactFactors(FramListModel):

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="factor_group")
        self.add_role_name(name="factor")
        self.add_role_name(name="factor_lu_id")
        self.add_role_name(name="is_unsat_factor")

        self._functions = CommonFunctions()

    @pyqtSlot()
    def populate(self):
        """
        Method to populate the model
        :return:
        """
        self.clear()

        try:
            factors = Lookups.select()\
                .where(Lookups.type == "Tow Performance")\
                .order_by(Lookups.value.asc(), Lookups.subvalue.asc())

            for factor in factors:
                item = dict()
                item["factor_group"] = factor.value if factor.value else ""
                item["factor"] = factor.subvalue if factor.subvalue else ""
                item["factor_lu_id"] = factor.lookup
                item["is_unsat_factor"] = "No"
                self.appendItem(item)

        except Exception as ex:

            logging.info('Error populating the TimeSeries Available Impact Factors Model: {0}'.format(ex))

    # @pyqtSlot(QVariant)
    # def add_item(self, item):
    #     """
    #     Method to remove an entire item
    #     :param item:
    #     :return:
    #     """
    #     if isinstance(item, QJSValue):
    #         item = item.toVariant()
    #
    #     self.appendItem(item=item)
    #
    # @pyqtSlot(int)
    # def remove_item(self, factor_id):
    #     """
    #     Method to remove the item with the given factor_id
    #     :param factor_id:
    #     :return:
    #     """
    #     if not isinstance(factor_id, int):
    #         return
    #
    #     logging.info(f"remove_item factor_id: {factor_id}")
    #
    #     index = self.get_item_index(rolename="factor_id", value=factor_id)
    #     if index:
    #         self.removeItem(index=index)

    @pyqtSlot()
    def sort(self):
        """
        Method to sort by two factors
        :return:
        """
        try:
            sorted_items = sorted(self._data_items, key=lambda x: (x["factor_group"], x["factor"]))
            self.setItems(sorted_items)

        except Exception as ex:

            logging.info(f"Error sorting: {ex}")


class SelectedImpactFactors(FramListModel):

    factorAdded = pyqtSignal(QVariant, arguments=["item",])

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="factor_group")
        self.add_role_name(name="factor")
        self.add_role_name(name="factor_lu_id")
        self.add_role_name(name="is_unsat_factor")

        self._functions = CommonFunctions()

    @pyqtSlot()
    def populate(self):
        """
        Method to populate the model
        :return:
        """
        self.clear()

        try:
            factors = PerformanceDetails.select()\
                        .join(OperationsFlattenedVw, on=(OperationsFlattenedVw.operation == PerformanceDetails.operation).alias("operation"))\
                        .where(OperationsFlattenedVw.tow_name == self._app.settings.haul,
                               PerformanceDetails.is_postseason)

            for factor in factors:
                item = dict()
                item["factor_group"] = factor.performance_type_lu.value
                item["factor"] = factor.performance_type_lu.subvalue
                item["factor_lu_id"] = factor.performance_type_lu.lookup
                item["is_unsat_factor"] = "Yes" if factor.is_unsat_factor else "No"
                self.appendItem(item)

                # Emit signal to remove these items from the available list model
                # logging.info(f"item: {item}")
                self.factorAdded.emit(item)

        except Exception as ex:

            logging.info('Error populating the TimeSeries Selected Impact Factors Model: {0}'.format(ex))

    # @pyqtSlot(QVariant)
    # def add_item(self, item):
    #     """
    #     Method to remove an entire item
    #     :param item:
    #     :return:
    #     """
    #     if isinstance(item, QJSValue):
    #         item = item.toVariant()
    #
    #     self.appendItem(item=item)
    #
    # @pyqtSlot(int)
    # def remove_item(self, factor_id):
    #     """
    #     Method to remove the item with the given factor_id
    #     :param factor_id:
    #     :return:
    #     """
    #     if not isinstance(factor_id, int):
    #         return
    #
    #     index = self.get_item_index(rolename="factor_id", value=factor_id)
    #     if index:
    #         self.removeItem(index=index)


class DistanceFishedModel(FramListModel):

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="technique")
        self.add_role_name(name="distance")
        self.add_role_name(name="speed")
        self.add_role_name(name="saved")

        self._functions = CommonFunctions()

        self.populate_model()

    @pyqtSlot()
    def populate_model(self):
        """
        Method to populate the model
        :return:
        """
        self.clear()

        try:
            template = {"distance": "", "speed": "", "saved": ""}
            for technique in TECHNIQUES:
                item = deepcopy(template)
                item["technique"] = technique
                self.appendItem(item)

        except Exception as ex:

            logging.info('Error populating the TimeSeries HaulsModel: {0}'.format(ex))


class MeansModel(FramListModel):

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self.add_role_name(name="meanType")
        self.add_role_name(name="timeSeries")
        self.add_role_name(name="mean")
        self.add_role_name(name="saved")
        self.add_role_name(name="basis")
        self.add_role_name(name="type")

        self._functions = CommonFunctions()

        self.populate_model()

    @pyqtSlot()
    def populate_model(self):
        """
        Method to populate the model
        :return:
        """
        self.clear()

        try:
            template = {"meanType": "", "timeSeries": "", "mean": "", "saved": ""}
            for k, v in MEANS_TYPES.items():
                item = deepcopy(template)
                item["meanType"] = k
                # if k in ["Latitude", "Longitude"]:
                #     item["timeSeries"] = v
                # else:
                item["timeSeries"] = f"{v['basis']} {v['type']} {v['default equipment']}"
                item["basis"] = v['basis']
                item["type"] = v['type']
                self.appendItem(item)

        except Exception as ex:

            logging.info(f'Error populating the TimeSeries MeansModel: {ex}')

    @pyqtSlot(QVariant)
    def update_model(self, entries):
        """
        Method to update the model.  This is called from the ChangeTimeSeriesDialog.qml where
        a user can select alternative time series to use for the mean calculations
        :param items:
        :return:
        """
        if isinstance(entries, QJSValue):
            entries = entries.toVariant()

        logging.info(f"Entries to update: {entries}")

        for k, v in entries.items():
            index = self.get_item_index(rolename="meanType", value=k)
            self.setProperty(index=index, property="timeSeries", value=v)


class DistanceFishedWorker(QObject):

    calculationsCompleted = pyqtSignal(QVariant, arguments=["gear_tracklines",])

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self._is_running = False
        self._df = DistanceFished()
        self.track_lines = kwargs["track_lines"]
        self.scope = kwargs["scope"]
        self.span = kwargs["span"]
        self.df_depth = kwargs["df_depth"]
        self.df_headrope = kwargs["df_headrope"]

    def run(self):
        self._is_running = True
        gear_tracklines = self.calculate_distance_fished()
        self.calculationsCompleted.emit(gear_tracklines)

    def stop(self):
        self._is_running = False

    def calculate_distance_fished(self):
        """
        Method to call the DistanceFished instance to calculate the distances fished
        :return:
        """
        return self._df.calculate_all_distances_fished(tracklines=self.track_lines, scope=self.scope, span=self.span,
                                                                  df_depth=self.df_depth, df_headrope=self.df_headrope)


class MplMap(QObject):

    distanceCalculated = pyqtSignal(str, QVariant, QVariant, arguments=["technique", "distance", "speed"])
    distanceFishedModelChanged = pyqtSignal()
    distanceFishedChanged = pyqtSignal()
    gearLinePlotted = pyqtSignal(str, bool, arguments=["technique", "created"])
    distanceFishedCompleted = pyqtSignal()
    tracklineSaved = pyqtSignal(str, arguments=['technique',])
    invalidDataPointsFound = pyqtSignal(str, QVariant, arguments=["legend_name", "invalid_ids"])

    def __init__(self, app=None):
        super().__init__()
        self._app = app                         # Handle to the overall application
        self._functions = CommonFunctions()     # Common Utility Functions
        self._distance_fished_model = DistanceFishedModel()

        self.qml_item = None                    # QML Item
        self.figure = None                      # Matplotlib Figure
        self.canvas = None                      # Matplitlib Canvas
        self.axes = []                          # List of matplotlib axes
        self.track_lines = dict()               # Tracklines, i.e. matplotlib lines
        self._zoom_scale = 1.2                  # Controls the rate for zooming in on_scroll event

        self._is_pressed = False                # Used for panning in the map
        self.cur_xlim = None
        self.cur_ylim = None
        self.xpress = None
        self.ypress = None
        self._pick_event = False                # Used for on_pick MPL event
        self._is_drawing = False
        self.cur_rect = None

        self.lat_min = 10000
        self.lat_max = -10000
        self.lon_min = 10000
        self.lon_max = -10000

        self._waypoint_styles = {
                "Start Haul": {"color": "b", "style": "o"},
                "Set Doors": {"color": "b", "style": "d"},
                "Doors Fully Out": {"color": "b", "style": "h"},
                "Begin Tow": {"color": "g", "style": "v"},
                "Start Haulback": {"color": "b", "style": "p"},
                "Net Off Bottom": {"color": "r", "style": "^"},
                "Doors At Surface": {"color": "b", "style": "D"},
                "End Of Haul": {"color": "b", "style": "s"}
            }

        self._df = DistanceFished()

        self._calculate_distance_fished_thread = QThread()
        self._calculate_distance_fished_worker = None

        self._show_invalids = False
        self._tool_mode = "pan"
        self._show_medians = False

    @pyqtProperty(QObject, notify=distanceFishedChanged)
    def distanceFished(self):
        """
        Method to return the self._df (i.e. handle to the distance fished object instance
        :return:
        """
        return self._df

    @pyqtProperty(FramListModel, notify=distanceFishedModelChanged)
    def distanceFishedModel(self):
        """
        Method to return the self._distance_fished_model
        :return:
        """
        return self._distance_fished_model

    def set_qml_item(self, item):
        """
        Method to set the qml_item
        :param item:
        :return:
        """
        self.qml_item = item
        self.figure = self.qml_item.getFigure()

        # Need to set the height to something other than 0, otherwise get a Singular Matrix matplotlib error
        self.figure.set_size_inches(self.figure.get_size_inches()[0], 0.01)

        self._create_axes()

    def _create_axes(self):
        """
        Method to create thea axes for the tracklines MPL figure
        :return:
        """
        # self.scale = 1.1
        # self.gs = gridspec.GridSpec(len(self.graphs), 1)
        # self.gs.update(wspace=0, hspace=0)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        ax = self.figure.add_subplot(111) #, facecolor='lightblue')
        # ax = self.figure.add_subplot(self.gs[i, :], label=k)
        # ax.xaxis_date("US/Pacific")
        # minutes = mdates.MinuteLocator()
        # seconds = mdates.SecondLocator()
        # ax.xaxis.set_major_locator(minutes)
        # ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S\n%m/%d/%y', tz=tzlocal()))
        # ax.xaxis.set_minor_locator(seconds)

        # ax.get_xaxis().get_major_formatter().set_scientific(False)
        ax.xaxis.set_major_formatter(FormatStrFormatter('%.5f'))
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.5f'))
        ax.tick_params(labelsize=7)

        ax.yaxis.grid(True)
        ax.xaxis.grid(True)
        # ax.set_xlim(-124.8, -124.6)
        # ax.set_ylim(45.5, 45.6)
        ax.set_xlim(MIN_LON, MAX_LON)
        ax.set_ylim(MIN_LAT, MAX_LAT)

        # ax.xaxis.set_ticklabels([])
        self.axes.append(ax)

        self.figure.subplots_adjust(left=0.1, right=0.99, top=1.0, bottom=0.05)

        self.qml_item.mpl_connect('button_press_event', self.on_press)
        self.qml_item.mpl_connect('button_release_event', self.on_release)
        self.qml_item.mpl_connect("motion_notify_event", self.on_motion)
        self.qml_item.mpl_connect('scroll_event', self.on_scroll)
        self.qml_item.mpl_connect('figure_leave_event', self.on_figure_leave)
        # self.qml_item.mpl_connect('pick_event', self.on_pick)

    def on_press(self, event):
        """
        Matplotlib button_press_event
        :param event:
        :return:
        """
        # if self._pick_event:
        #     self._pick_event = False
        #     logging.info(f"pick event is false")
        #     return
        # if self.canvas.widgetlock.locked(): return

        if event.inaxes is None: return

        gca = event.inaxes
        self.xpress = event.xdata
        self.ypress = event.ydata

        if self._tool_mode == "pan":
            QApplication.setOverrideCursor(QCursor(Qt.OpenHandCursor))
            self._is_pressed = True
            self.cur_xlim = gca.get_xlim()
            self.cur_ylim = gca.get_ylim()

        elif self._tool_mode == "invalidData":
            QApplication.setOverrideCursor(QCursor(Qt.CrossCursor))
            self._is_drawing = True
            self.cur_rect = Rectangle((0, 0), 1, 1, color='lightblue', zorder=100, visible=True, alpha=0.7)
            gca.add_patch(self.cur_rect)

    def on_release(self, event):
        """
        Matplotlib button_release_event
        :param event:
        :return:
        """
        QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))

        if self._tool_mode == "pan":

            self._is_pressed = False

        elif self._tool_mode == "invalidData":

            if event.inaxes is None: return

            gca = event.inaxes

            self._is_drawing = False
            if self.cur_rect.get_x() != 0 and self.cur_rect.get_width() != 1:

                # Patches = drawing rectangle, Lines = Time Series + Waypoint vertical lines

                # Get the x/y min/max of the currently drawn selection rectangle
                x_min, x_max = sorted([self.cur_rect.get_x(), self.cur_rect.get_x() + self.cur_rect.get_width()])
                y_min, y_max = sorted([self.cur_rect.get_y(), self.cur_rect.get_y() + self.cur_rect.get_height()])

                logging.info(f"Invalid data rectangle boundaries:  xmin: {x_min}, xmax: {x_max} >>> ymin: {y_min}, ymax: {y_max}")

                # Iterate through all of the time series lines, but don't consider the waypoint lines (_line),
                # gear lines (Gear), or invalid lines (_nolegend_ or invalid)
                # or the invalid data points lines
                invalid_ids = []

                lines = [[x.get_label(), x.get_gid()] for x in gca.lines]
                logging.info(f"lines: {lines}")

                lines = [x for x in gca.lines if "_line" not in x.get_label() and
                                                  x.get_label() != "_nolegend_" and
                                                 "Gear" not in x.get_label()]
                for line in lines:

                    label = line.get_label()
                    xy_data = line.get_xydata()
                    ids = line.get_gid()

                    logging.info(f"\n")
                    logging.info(f"line label: {label}")

                    if not line.get_visible():
                        logging.info(f"line is invisible, skipping: {line.get_label()}")
                        continue

                    # Find the newly selected invalid points for the current time series line, within the selection rectangle
                    invalid_pts = [[i, pt[0], pt[1]] for i, pt in enumerate(xy_data)
                                   if (x_min <= pt[0] <= x_max) and (y_min <= pt[1] <= y_max)]
                    idx = set([x[0] for x in invalid_pts])
                    lon_lat_values = [[x[1], x[2]] for x in invalid_pts]

                    # Find all of the points that don't include the invalid_pts and reset the line to use these data
                    if len(xy_data) > 0:
                        xy_data_clean = np.array([pt for i, pt in enumerate(xy_data) if i not in idx])
                        xy_data_clean = xy_data_clean.T     # Transpose to be a 2 x N array for use with set_data later
                        line.set_data(xy_data_clean)

                    # Reset the xy_data for the invalid line as well
                    if len(invalid_pts) > 0:

                        logging.info(f"\tinvalid_pts: {len(invalid_pts)} >>> {invalid_pts}")

                        invalid_lines = [x for x in gca.lines if x.get_gid() == f"{label} invalid"]
                        if len(invalid_lines) == 1:
                            invalid_line = invalid_lines[0]
                            invalid_xy = invalid_line.get_xydata()
                            logging.info(f"invalid_xy data: {invalid_xy}")
                            np_lon_lat = np.array(lon_lat_values)

                            logging.info(f"np_lon_lat: {np_lon_lat}")
                            invalid_xy = np.vstack((invalid_xy, np.array(lon_lat_values)))
                            invalid_xy = invalid_xy.T
                            invalid_line.set_data(invalid_xy)

                    # Update the track line dataframe to set these new points as invalid - Find the invalid_pts in dataframe
                    df = self.track_lines[label]["dataframe"]
                    mask = df.apply(lambda x: [x["longitude"], x["latitude"]] in lon_lat_values, axis=1)

                    if label in ["vessel", "iti $iigll"]:
                        df.loc[mask, "longitude_invalid"] = True
                        df.loc[mask, "latitude_invalid"] = True

                        # Having changed the vessel latitude/longitude values to invalid, we now need to modify the iti r/b line as well
                        # as it still is potentially using these invalid vessel lat/lon values to derive it's range/bearing values
                        if label == "vessel":

                            rb_label = "iti r/b"

                            # Update the rb line dataframe with the correct invalid lat/lon values
                            if rb_label in self.track_lines:

                                df_rb = self.track_lines[rb_label]["dataframe"]
                                logging.info(f"df_rb columns: {df_rb.columns}")
                                logging.info(f"df_rb head: {df_rb.head(3)}")

                                df_invalid_lat_ids = df.loc[df["latitude_invalid"], "latitude_id"].tolist()
                                df_invalid_lon_ids = df.loc[df["longitude_invalid"], "longitude_id"].tolist()
                                logging.info(f"Map Selection, df_invalid_lat_ids: {df_invalid_lat_ids}")
                                logging.info(f"Map Selection, df_invalid_lon_ids: {df_invalid_lon_ids}")

                                rb_lon_mask = (df_rb["longitude_id"].isin(df_invalid_lon_ids))
                                rb_lat_mask = (df_rb["latitude_id"].isin(df_invalid_lat_ids))

                                logging.info(f"rb lon to update invalid to True: {df_rb.loc[rb_lon_mask]}")
                                logging.info(f"rb lat to update invalid to True: {df_rb.loc[rb_lat_mask]}")

                                df_rb.loc[rb_lon_mask, "longitude_invalid"] = True
                                df_rb.loc[rb_lat_mask, "latitude_invalid"] = True
                                self.track_lines[rb_label]["dataframe"] = df_rb

                                rb_valid_mask = (~df_rb["longitude_invalid"]) & (~df_rb["latitude_invalid"])
                                rb_invalid_mask = (~rb_valid_mask)

                                # TODO Todd Hay - Update the iti r/b line when returning from the invalid dialog in TimeSeries

                    elif label == "iti r/b":
                        df.loc[mask, "range_invalid"] = True
                        df.loc[mask, "bearing_invalid"] = True

                    self.track_lines[label]["dataframe"] = df

                    # Update the df_components, i.e. df_latitude / df_longitude or df_range / df_bearing and then
                    #   emit these back to the main TimeSeries to update the dataframes there
                    if self.track_lines[label]["source_type"] == "latitude_longitude":

                        invalid_lon_ids = df.loc[mask, 'longitude_id'].tolist()
                        invalid_lat_ids = df.loc[mask, "latitude_id"].tolist()
                        new_invalid_ids = invalid_lon_ids + invalid_lat_ids

                        logging.info(f"\tbad lat_ids: {invalid_lat_ids}, lon_ids: {invalid_lon_ids}")

                        lat_legend = self.track_lines[label]["latitude_legend"]
                        if len(invalid_lat_ids) > 0:
                            self.invalidDataPointsFound.emit(lat_legend, invalid_lat_ids)

                        lon_legend = self.track_lines[label]["longitude_legend"]
                        if len(invalid_lon_ids) > 0:
                            self.invalidDataPointsFound.emit(lon_legend, invalid_lon_ids)

                    elif self.track_lines[label]["source_type"] == "range_bearing":
                        invalid_range_ids = df.loc[mask, "range_id"].tolist()
                        invalid_bearing_ids = df.loc[mask, "bearing_id"].tolist()
                        new_invalid_ids = invalid_range_ids + invalid_bearing_ids

                        logging.info(f"\tbad range_ids: {invalid_range_ids}, bearing ids: {invalid_bearing_ids}")

                        range_legend = self.track_lines[label]['range_legend']
                        if len(invalid_range_ids) > 0:
                            self.invalidDataPointsFound.emit(range_legend, invalid_range_ids)

                        bearing_legend = self.track_lines[label]['bearing_legend']
                        if len(invalid_bearing_ids) > 0:
                            self.invalidDataPointsFound.emit(bearing_legend, invalid_bearing_ids)

                    # Grow the invalid_ids to include all invalid_pts from all of the time series for this graph
                    invalid_ids += new_invalid_ids

                    # if invalid_ids:
                    #     invalid_ids.extend(new_invalid_ids)
                    # else:
                    #     invalid_ids = new_invalid_ids

                logging.info(f"invalid_ids: {invalid_ids}")

                # Update the OperationMeasurements Table to set these new invalid points to is_not_valid=True
                try:
                    if len(invalid_ids) > 0:
                        OperationMeasurements.update(is_not_valid=True).where(
                            OperationMeasurements.operation_measurement << invalid_ids).execute()
                except Exception as ex:
                    logging.error(f"Error updating the database with invalid points info: {ex}")

                # Delete the selection rectangle and refresh the map display
                del gca.patches[:]
                self.qml_item.draw_idle()

    def on_motion(self, event):
        """
        Matplotlib motion_notify_event
        :param event:
        :return:
        """
        gca = event.inaxes

        if self._tool_mode == "pan":

            if self._is_pressed:
                # Pan the Map

                if event.inaxes is None or self.xpress is None or self.ypress is None: return
                dx = event.xdata - self.xpress
                dy = event.ydata - self.ypress
                self.cur_xlim -= dx
                self.cur_ylim -= dy
                gca.set_xlim(self.cur_xlim)
                gca.set_ylim(self.cur_ylim)
                self.qml_item.draw_idle()

            else:
                # OnHover, read out value of data to statusbar

                for line in self.axes[0].get_lines():
                    if line.contains(event)[0]:
                        pass
                        # logging.info(f"lat: {event.ydata}, lon: {event.xdata}")

                        # df_line = self.track_lines[line.get_label()]["dataframe"]
                        # mask = (df_line["latitude"] == float("%6.f" % event.xdata)) & (df_line["longitude"] == float("%6.f" % event.ydata))
                        # row = df_line.loc[mask]

        elif self._tool_mode == "invalidData":

            if self._is_drawing and event.xdata and event.ydata:

                self.cur_rect.set_width(event.xdata- self.xpress)
                self.cur_rect.set_height(event.ydata - self.ypress)
                self.cur_rect.set_xy((self.xpress, self.ypress))
                self.qml_item.draw_idle()

    def on_scroll(self, event):
        """
        Matplotlib scroll_event
        :param event:
        :return:
        """
        gca = event.inaxes
        if not gca: return

        cur_xlim = gca.get_xlim()
        cur_ylim = gca.get_ylim()

        xdata = event.xdata  # get event x location
        ydata = event.ydata  # get event y location

        if event.button == 'down':
            # deal with zoom out
            scale_factor = self._zoom_scale
        elif event.button == 'up':
            # deal with zoom in
            scale_factor = 1 / self._zoom_scale
        else:
            # deal with something that should never happen
            scale_factor = 1
            # print (event.button)

        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

        gca.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * (relx)])
        gca.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * (rely)])

        self.qml_item.draw()

    def on_figure_leave(self, event):

        QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))

    def _clear_map(self):

        del self.axes[0].lines[:]
        del self.axes[0].patches[:]
        del self.axes[0].collections[:]
        self.track_lines.clear()

        self.lat_min = 10000
        self.lat_max = -10000
        self.lon_min = 10000
        self.lon_max = -10000

        self.qml_item.draw_idle()

    def _clear_gear_items(self):
        """
        Method to clear out the gear track lines and waypoints
        :return:
        """
        # Remove Gear MPL Lines
        remove_items = []
        for i, line in enumerate(self.axes[0].lines):
            if "gear" in line.get_label().lower():
                remove_items.append(i)
        remove_items = sorted(remove_items, reverse=True)
        for i in remove_items:
            del self.axes[0].lines[i]

        # Remove Gear Line Dictionary
        remove_items = []
        for k, v in self.track_lines.items():
            if "gear" in k.lower():
                remove_items.append(k)
        remove_items = sorted(remove_items, reverse=True)
        for i in remove_items:
            self.track_lines.pop(i, None)

        # Remove Gear MPL Waypoints
        remove_items = []
        for i, collection in enumerate(self.axes[0].collections):
            if "gear" in collection.get_label().lower():
                remove_items.append(i)
        remove_items = sorted(remove_items, reverse=True)
        for i in remove_items:
            del self.axes[0].collections[i]

        self.qml_item.draw_idle()

    def plot_track_line(self, type, df, start_haul, end_of_haul, source_type, legend_names):
        """
        Method to plot the actual trackline
        :param type: str - representing the type to plot
        :param legend_name: str - the legend name of the given time series
        :param df: DataFrame containing the latitude and longitude of the track line
        :return:
        """
        types = {"vessel": "b",
                 "iti $iigll": "g",
                 "iti r/b": "brown"}

        # logging.info(f"plot trackline df: {df.columns}")

        # ["ITI R/B", "ITI R/B + Trig", "Slope/Distance + Trig", "ITI $IIGLL", "GCD + Trig"]

        if type not in types:
            logging.error(f"Track line to plot is not a valid type: {type}")
            return

        # Test #1 - Filter points outside of the start_haul and end_of_haul times.  Buffer these ones out entirely, i.e.
        #           they will not even show up in the df_invalids dataframe as we will never care about these points
        if start_haul and end_of_haul:
            mask = (df["times"] >= start_haul) & (df["times"] <= end_of_haul)
            df = df.loc[mask].copy(deep=True)
        else:
            df = df.copy(deep=True)

        size_before_filter = len(df)

        # Test #2 - Egregious Outlier Test - Discard latitude/longitude values not along the West Coast
        mask = (df["latitude"] >= MIN_LAT) & (df["latitude"] <= MAX_LAT) & \
               (df["longitude"] >= MIN_LON) & (df["longitude"] <= MAX_LON)
        df_valids = df.loc[mask]

        size_after_filter = len(df_valids)
        logging.info(f"\tTest #2 Filter - West Coast Outliers, size before / after: {size_before_filter} / {size_after_filter}")

        # logging.info(f"\tVESSEL track data, after filters #1/#2, start/end: {df.iloc[0]} > {df.iloc[-1]}")

        if type == "vessel":

            # Test #3 - Median Test - Get the vessel lat/lon median values and add a buffer around those to mask df
            lat_median = df_valids["latitude"].median()
            lon_median = df_valids["longitude"].median()
            median_buffer = 5 * LAT_LON_BUFFER
            self.lat_min = lat_median - median_buffer
            self.lat_max = lat_median + median_buffer
            self.lon_min = lon_median - median_buffer
            self.lon_max = lon_median + median_buffer

            size_before_filter = len(df_valids)

            mask = (df_valids["latitude"] >= self.lat_min) & (df_valids["latitude"] <= self.lat_max) & \
               (df_valids["longitude"] >= self.lon_min) & (df_valids["longitude"] <= self.lon_max)
            df_valids = df_valids.loc[mask]

            # logging.info(f"\tVESSEL track data, after median filter, start/end: {df_valids.iloc[0]} > "
            #              f"{df_valids.iloc[-1]}")

            size_after_filter = len(df_valids)
            logging.info(f"\tTest #3 Filter - median filtering, size before / after: {size_before_filter} / {size_after_filter}")
            # logging.info(f"\t\tlat_median={lat_median}, lon_median={lon_median}")

            # Test #4 - latitude_invalid / longitude_invalid Test - mask items that have already been marked invalid
            size_before_filter = len(df_valids)
            valid_mask = (~df_valids["latitude_invalid"]) & (~df_valids["longitude_invalid"])
            df_valids = df_valids.loc[valid_mask]
            size_after_filter = len(df_valids)

            logging.info(f"\tTest #4 Filter - existing invalid items, size before / after: "
                         f"{size_before_filter} / {size_after_filter}")

            # TODO Todd Hay - Should we do a Test #5 - Minimum Bounding Rectangle Mask ?

            # Find the Minimum Bounding Rectangle + Buffer and use this to set the axes xlim and ylim (viewable extent)
            self.lat_min = df_valids["latitude"].min(skipna=True) - LAT_LON_BUFFER
            self.lat_max = df_valids["latitude"].max(skipna=True) + LAT_LON_BUFFER
            self.lon_min = df_valids["longitude"].min(skipna=True) - LAT_LON_BUFFER
            self.lon_max = df_valids["longitude"].max(skipna=True) + LAT_LON_BUFFER

            # logging.info(f"\tMBR viewing extent: lat min/max: "
            #              f"{self.lat_min}, {self.lat_max} >>> lon:  {self.lon_min}, {self.lon_max}")

            self.axes[0].set_xlim(left=self.lon_min, right=self.lon_max)
            self.axes[0].set_ylim(bottom=self.lat_min, top=self.lat_max)

        else:
            """
            Mask the gear lat/lon values based on the lat/lon mix/max values, i.e. get rid of the really bogus outliers

            My overall filter is 0.03 decimal degrees (above the self._lat_lon_buffer is set to 0.01 already to adjust
            the sizes of self.lat_min, lat_max, etc...

            Maximum scope is 1225 fathoms ~ 2300 meters.  0.01 decimal degrees = ~770m @ 45 degrees Latitude, so
            0.03 decimal degrees = ~2400m @ 45 degrees Latitude.  So we shouldn't be cutting out any data if the full
            scope is let out.
            """
            filter = 0.03 - LAT_LON_BUFFER
            mask = (df_valids["latitude"] >= self.lat_min - filter) & \
                   (df_valids["latitude"] <= self.lat_max + filter) & \
                   (df_valids["longitude"] >= self.lon_min - filter) & \
                   (df_valids["longitude"] <= self.lon_max + filter)
            df_valids = df_valids.loc[mask]

            if type == "iti r/b":
                valid_mask = (~df_valids["range_invalid"]) & (~df_valids["bearing_invalid"])
                df_valids = df_valids.loc[valid_mask]

            else:
                valid_mask = (~df_valids["latitude_invalid"]) & (~df_valids["longitude_invalid"])
                df_valids = df_valids.loc[valid_mask]

        lines = [i for i, x in enumerate(self.axes[0].lines) if x.get_label() == type or \
                 x.get_gid() == f"{type} invalid"]

        # Get the visibility of the line
        visible = True
        if len(lines) > 0:
            visible = self.axes[0].lines[lines[0]].get_visible()
        lines = sorted(lines, reverse=True)
        for idx in lines:
            del self.axes[0].lines[idx]

        # Plot the valid track line
        line = self.axes[0].plot(df_valids["longitude"], df_valids["latitude"], label=type, visible=visible,
                                 marker='o', markersize=3, color=types[type], zorder=1, picker=True)

        # Plot the invalid track line
        invalid_mask = (~df.index.isin(df_valids.index))
        df_invalids = df.loc[invalid_mask]
        visible = self._show_invalids & visible
        invalid_line = self.axes[0].plot(df_invalids["longitude"], df_invalids["latitude"], label="_nolegend_",
                                         gid=f"{type} invalid",
                                         marker='x', markersize=20, color=types[type], zorder=1, linewidth=0,
                                         visible=visible)

        # logging.info(f"\ttype: {type},     sizes:  df: {len(df)},    df_valids: {len(df_valids)},    df_invalids: {len(df_invalids)}")

        # Refresh the map to draw the new track line
        self.qml_item.draw_idle()

        # Save newly identified invalid points that have not already been saved to FRAM_CENTRAL
        if isinstance(df_invalids, pd.DataFrame) and not df_invalids.empty:

            try:
                # Drop invalids that have already been saved to the database
                invalid_mask = (df["latitude_invalid"]) | (df["longitude_invalid"])
                df_invalids = df_invalids.loc[~invalid_mask]

                # Find the invalid latitude values
                df_bad_lat = df_invalids.loc[:, ["latitude_id", "latitude"]].copy(deep=True)
                lat_mask = (df_bad_lat["latitude"] < self.lat_min) | (df_bad_lat["latitude"] > self.lat_max)
                df_bad_lat = df_bad_lat.loc[lat_mask]
                df_bad_lat.rename(columns={"latitude_id": "operation_measurement",
                                           "latitude": "reading_numeric"}, inplace=True)

                # Find the invalid longitude values
                df_bad_lon = df_invalids.loc[:, ["longitude_id", "longitude"]].copy(deep=True)
                size_before = len(df_bad_lon)
                lon_mask = (df_bad_lon["longitude"] < self.lon_min) | (df_bad_lon["longitude"] > self.lon_max)
                df_bad_lon = df_bad_lon.loc[lon_mask]
                size_after = len(df_bad_lon)
                logging.info(f"df_bad_lon before/after: {size_before} / {size_after}")
                df_bad_lon.rename(columns={"longitude_id": "operation_measurement",
                                           "longitude": "reading_numeric"}, inplace=True)

                # Gather all of the bad IDs and update the database with these
                df_bad = df_bad_lat.append(df_bad_lon)
                logging.info(f"length of invalids to save to the database: {len(df_bad)}")

                # Update the overall dataframe
                logging.info(f"setting items to invalid=True, lat = {df_bad_lat.index}, lon = {df_bad_lon.index}")
                df.loc[df_bad_lat.index, "latitude_invalid"] = True
                df.loc[df_bad_lon.index, "longitude_invalid"] = True

                # Update the FRAM_CENTRAL database
                om_invalid = df_bad.loc[:, "operation_measurement"].tolist()
                om_invalid = [int(x) for x in om_invalid]
                with self._app.settings._database.atomic():
                    OperationMeasurements.update(is_not_valid=True) \
                        .where(OperationMeasurements.operation_measurement << om_invalid).execute()
                logging.info(f"df_bad items to update to invalid: {om_invalid}")


                # Update the entries in the database
                # sql = 'CREATE TEMP TABLE tmp_source (id int);'
                # self._app.settings._database.execute_sql(sql=sql)
                #
                # sql = 'UPDATE OPERATION_MEASUREMENTS om SET is_not_valid = True WHERE om.operation_measurement_id = tmp_source.id;'

                # with self._app.settings._database.atomic():
                # records = OperationMeasurements.select().where(OperationMeasurements.operation_measurement << om_invalid)
                # for record in records:
                #     record.is_not_valid = True
                #     record.save()
                #     logging.info(f"updating: {record.operation_measurement}")

                # Drop the temporary table
                # sql = 'DROP TABLE tmp_source;'
                # self._app.settings._database.execute_sql(sql=sql)

                    # for x in om_invalid:
                    #     OperationMeasurements.update(is_not_valid=True) \
                    #         .where(OperationMeasurements.operation_measurement == x).execute()
                    #     logging.info(f"{x} updated")



                logging.info(f"done updating the invalid values in the database")

                # for k, v in df_bad.iterrows():
                #     OperationMeasurements.update(is_not_valid=True) \
                #         .where(OperationMeasurements.operation_measurement == int(v["operation_measurement"])).execute()

            except Exception as ex:
                logging.error(f"Error updating vessel/gear invalid points in DB: {ex}")

        # logging.info(f"\tVESSEL track data, after all filters, start/end: {df.iloc[0]} > {df.iloc[-1]}")

        # Add the track line to our dictionary of all track lines
        if type not in self.track_lines:
            self.track_lines[type] = dict()
        self.track_lines[type]["line"] = line
        self.track_lines[type]["dataframe"] = df
        self.track_lines[type]["source_type"] = source_type
        for k, v in legend_names.items():
            self.track_lines[type][k] = v

        for wp in self.axes[0].collections:
            wp.set_zorder(10)

    def _redraw_track_line(self, time_series, start_haul, end_of_haul, valid_ids, invalid_ids):
        """
        Method to draw the valid/invalid lines for vessel + gear tracklines, but not the distance fished lines.  This
        is called when one of the components of the given track line have been modified, i.e. either the latitude,
        longitude, range, or bearing.  Note that there is a special case when the vessel latitude or longitude is
        changed in that we then need to also update the gear range/bearing line as it uses the vessel latitude/
        longitude values to derive the gear range/bearing line.

        Regarding determining if a point is valid or invalid, this method only does masking for the start_haul
        and end_of_haul times and does not do all of the initial plot masking of looking for lat/lon outliers beyond
        the west coast, beyond the vessel median, etc.  Those are handled in the intial plotting and the invalids are
        set for those instances at that time.

        :param time_series: str - name of time series legend
        :param start_haul: date-time of the start of the haul in datetime format
        :param end_of_haul: date-time of the end of the haul in datetime format
        :param valid_ids: list - contains the time series IDs that were changed from invalid to valid
        :param invalid_ids: list - contains the time series IDs that were changed from valid to invalid
        :return:
        """


        # Get the measurement type from the overall type (which is really just the legend_name
        measurement = time_series.split("(")[0].strip()

        # Provide a measurement from the measurement to the color and the name of the track line
        types = {"Gear Bearing to Target": {"color": "brown", "track_line": "iti r/b"},
                 "Gear Horizontal Range to Target": {"color": "brown", "track_line": "iti r/b"},
                 "Gear Latitude": {"color": "g", "track_line": "iti $iigll"},
                 "Gear Longitude": {"color": "g", "track_line": "iti $iigll"},
                 "Vessel Latitude": {"color": "b", "track_line": "vessel"},
                 "Vessel Longitude": {"color": "b", "track_line": "vessel"}}

        logging.info(f"_redraw_track_line, measurement = {measurement}")

        if measurement not in types:
            # self.qml_item.draw_idle()
            return

        logging.info(f"\n\nMapping time_series found, updating the map, type: {time_series}")

        # Retrieve the desired color for plotting the track line
        if measurement in types:
            color = types[measurement]["color"]
        else:
            color = "purple"

        # Get the existing trackline dataframe, if it exists
        track_line = types[measurement]["track_line"]
        df_track = None
        if track_line in self.track_lines:
            df_track = self.track_lines[track_line]["dataframe"]

        logging.info(f"\t\tMeasurement: {measurement}, Color: {color}, Track Line: {track_line}")

        # Mask the input dataframe, df, by the start_haul and end_of_haul times, to create the df_plot dataframe
        if isinstance(df_track, pd.DataFrame) and not df_track.empty:
            mask = (df_track["times"] >= start_haul) & (df_track["times"] <= end_of_haul)
            df_plot = df_track.loc[mask].copy(deep=True)                    # TODO Todd Hay Range/Bearing failing here

        else:
            logging.info(f"df_track problem, returning from redrawing: {df_track}")
            return

        # Flip the items to invalid, given the input df dataframe, which is the individual time series data frame.  So
        # the invalid item will be stored in the invalid column
        logging.info(f"new valid_ids: {valid_ids}")
        logging.info(f"new invalid_ids: {invalid_ids}")

        # Using those invalid_ids, now find those same invalid_ids in the df_track dataframe and set invalid to True, for
        # the given measurement
        if track_line == "vessel":
            if measurement == "Vessel Latitude":
                mask = (df_plot["latitude_id"].isin(valid_ids))
                df_plot.loc[mask, "latitude_invalid"] = False

                mask = (df_plot["latitude_id"].isin(invalid_ids))
                df_plot.loc[mask, "latitude_invalid"] = True

            elif measurement == "Vessel Longitude":
                mask = (df_plot["longitude_id"].isin(valid_ids))
                df_plot.loc[mask, "longitude_invalid"] = False

                mask = (df_plot["longitude_id"].isin(invalid_ids))
                df_plot.loc[mask, "longitude_invalid"] = True

            valid_mask = (~df_plot["latitude_invalid"]) & (~df_plot["longitude_invalid"])
            invalid_mask = (df_plot["latitude_invalid"]) | (df_plot["longitude_invalid"])

            # Redraw the iti r/b track line as well since it is dependent upon the vessel line
            # TODO Todd Hay - Implement this redrawing of the iti r/b track line
            rb_label = "iti r/b"
            df_rb = self.track_lines[rb_label]["dataframe"]
            logging.info(f"df_rb columns: {df_rb.columns}")
            logging.info(f"df_rb: {df_rb.head(3)}")

            # Get the index IDs of the valid and invalid lat/lon points and then find the related iti r/b line IDs
            valid_lat_ids = df_plot.loc[~df_plot["latitude_invalid"], "latitude_id"].tolist()
            invalid_lat_ids = df_plot.loc[df_plot["latitude_invalid"], "latitude_id"].tolist()
            valid_lon_ids = df_plot.loc[~df_plot["longitude_invalid"], "longitude_id"].tolist()
            invalid_lon_ids = df_plot.loc[df_plot["longitude_invalid"], "longitude_id"].tolist()

            logging.info(f"invalid lats: {invalid_lat_ids} >>>>\n\t\t\tvalid lats: {valid_lat_ids}")
            logging.info(f"invalid lons: {invalid_lon_ids} >>>>\n\t\t\tvalid lons: {valid_lon_ids}")

            # Redraw the valid line, i.e. reset the xydata
            rb_valid_lines = [x for x in self.axes[0].lines if x.get_label() == rb_label]
            if len(rb_valid_lines) == 1:
                rb_valid_line = rb_valid_lines[0]
                rb_valid_mask = (df_rb["latitude_id"].isin(valid_lat_ids)) & (df_rb["longitude_id"].isin(valid_lon_ids))
                np_rb_valid = df_rb.loc[rb_valid_mask, ["longitude", "latitude"]].values.T

                logging.info(f"len of np_rb_valid: {len(np_rb_valid)} >>> {np_rb_valid}")

                rb_valid_line.set_data(np_rb_valid)

            # Redraw the invalid line, i.e. reset the xydata
            rb_invalid_lines = [x for x in self.axes[0].lines if x.get_gid() == f"{rb_label} invalid"]
            if len(rb_invalid_lines) == 1:
                rb_invalid_line = rb_invalid_lines[0]
                rb_invalid_mask = (df_rb["latitude_id"].isin(invalid_lat_ids)) | (df_rb["longitude_id"].isin(invalid_lon_ids))

                logging.info(f"rb_invalid_mask: {rb_invalid_mask}")
                np_rb_invalid = df_rb.loc[rb_invalid_mask, ["longitude", "latitude"]].values.T

                logging.info(f"np_rb_invalid: {np_rb_invalid}")
                rb_invalid_line.set_data(np_rb_invalid)

        elif track_line == "iti $iigll":
            if measurement == "Gear Latitude":
                mask = (df_plot["latitude_id"].isin(valid_ids))
                df_plot.loc[mask, "latitude_invalid"] = False

                mask = (df_plot["latitude_id"].isin(invalid_ids))
                df_plot.loc[mask, "latitude_invalid"] = True

            elif measurement == "Gear Longitude":
                mask = (df_plot["longitude_id"].isin(valid_ids))
                df_plot.loc[mask, "longitude_invalid"] = False

                mask = (df_plot["longitude_id"].isin(invalid_ids))
                df_plot.loc[mask, "longitude_invalid"] = True

            valid_mask = (~df_plot["latitude_invalid"]) & (~df_plot["longitude_invalid"])
            invalid_mask = (df_plot["latitude_invalid"]) | (df_plot["longitude_invalid"])

        elif track_line == "iti r/b":
            if measurement == "Gear Horizontal Range to Target":

                mask = (df_plot["range_id"].isin(valid_ids))
                df_plot.loc[mask, "range_invalid"] = False

                mask = (df_plot["range_id"].isin(invalid_ids))
                df_plot.loc[mask, "range_invalid"] = True

            elif measurement == "Gear Bearing to Target":

                mask = (df_plot["bearing_id"].isin(valid_ids))
                df_plot.loc[mask, "bearing_invalid"] = False

                mask = (df_plot["bearing_id"].isin(invalid_ids))
                df_plot.loc[mask, "bearing_invalid"] = True

            # path = r"C:\Users\Todd.Hay\Desktop\df_plot.csv"
            # df_plot.to_csv(path)

            valid_mask = (~df_plot["range_invalid"]) & (~df_plot["bearing_invalid"])
            invalid_mask = (~valid_mask)
            # invalid_mask = (df_plot["range_invalid"]) | (df_plot["bearing_invalid"])

        # logging.info(f"df_plot, showing the invalids: {df_plot.loc[invalid_mask]}")

        # Delete the existing valid and invalid lines if they exist
        lines = [i for i, x in enumerate(self.axes[0].lines) if x.get_label() == track_line or \
                                                                x.get_gid() == f"{track_line} invalid"]
        lines = sorted(lines, reverse=True)
        for idx in lines:
            del self.axes[0].lines[idx]

        logging.info(f"plotting track lines: {color}")

        # Plot the valid track line
        df_valids = df_plot.loc[valid_mask].copy(deep=True)
        valid_line = self.axes[0].plot(df_valids["longitude"], df_valids["latitude"], label=track_line,
                                       marker='o', markersize=3, color=color, zorder=1)

        # Plot the invalid track line
        df_invalids = df_plot.loc[invalid_mask].copy(deep=True)
        invalid_line = self.axes[0].plot(df_invalids["longitude"], df_invalids["latitude"], label="_nolegend_",
                                         gid=f"{track_line} invalid",
                                         marker='x', markersize=20, color=color, zorder=1, linewidth=0,
                                         visible=self._show_invalids)

        # Refresh the map to draw the new track line
        self.qml_item.draw_idle()

        # Update the track line dataframe
        self.track_lines[track_line]["dataframe"] = df_plot

    def plot_waypoints(self, waypoints):
        """
        Method to plot the waypoints
        :param waypoints:
        :return:
        """

        try:
            # Clear the existing waypoints from the display
            # del self.axes[0].collections[:]
            logging.info(f"collections len = {len(self.axes[0].collections)}")

            delete_list = list()
            for i, c in enumerate([x for x in self.axes[0].collections if x.get_label() == "Vessel"]):
                delete_list.append(i)
            delete_list = sorted(delete_list, reverse=True)
            for i in delete_list:
                del self.axes[0].collections[i]

            styles = {
                "Start Haul": {"color": "b", "style": "o"},
                "Set Doors": {"color": "b", "style": "d"},
                "Doors Fully Out": {"color": "b", "style": "h"},
                "Begin Tow": {"color": "g", "style": "v"},
                "Start Haulback": {"color": "b", "style": "p"},
                "Net Off Bottom": {"color": "r", "style": "^"},
                "Doors At Surface": {"color": "b", "style": "D"},
                "End Of Haul": {"color": "b", "style": "s"}
            }

            mpl_points = dict()

            # Need to set the height to something other than 0, otherwise get a Singular Matrix matplotlib error
            figure_height = self.figure.get_size_inches()[1]
            if figure_height == 0:
                self.figure.set_size_inches(self.figure.get_size_inches()[0], 0.01)

            for wp in waypoints.itertuples():
                idx = wp.Index
                lon = wp.best_longitude if wp.best_longitude else wp.longitude
                lat = wp.best_latitude if wp.best_latitude else wp.latitude

                logging.info(f"PLOT WAYPOINTS: {idx}, datetime={wp.datetime} >> best_datetime={wp.best_datetime}, {lat}, {lon}")
                # logging.info(f"\t{idx}, lat type ={type(lat)}, lon type = {type(lon)}")

                if isinstance(lat, decimal.Decimal) and isinstance(lon, decimal.Decimal):
                    point = self.axes[0].scatter(lon, lat, color=styles[idx]["color"], marker=styles[idx]["style"],
                                                 s=150, zorder=10, label="Vessel")
                    mpl_points[idx] = point

            self.track_lines["vessel"]["waypoints"] = waypoints
            self.track_lines["vessel"]["mpl_waypoints"] = mpl_points

        except Exception as ex:
            logging.info(f"Exception drawing waypoints: {ex}")

        self.qml_item.draw()

    def plot_gear_trackline(self, type, created, df_gear, start_haul, end_of_haul):
        """
        Method to plot the df_gear trackline
        :param df_gear:
        :param begin_tow:
        :param net_off_bottom:
        :return:
        """
        visibility = False
        if created:
            if type == "Gear Catenary":
                visibility = True
        else:
            visibility = True

        if start_haul and end_of_haul:
            mask = (df_gear["times"] >= start_haul) & (df_gear["times"] <= end_of_haul)
            df_plot = df_gear.loc[mask].copy(deep=True)
        else:
            df_plot = df_gear.copy(deep=True)

        line = self.axes[0].plot(df_plot["gear_lon"], df_plot["gear_lat"], visible=visibility,
                                 marker='o', markersize=3, zorder=1, label=type)

        self.qml_item.draw_idle()

        return line

    def plot_gear_waypoints(self, label_type, created, waypoints):

        if waypoints is None:
            return None

        visible = False
        if created:
            if label_type == "Gear Catenary":
                visible = True
        else:
            visible = True

        # Need to set the height to something other than 0, otherwise get a Singular Matrix matplotlib error
        figure_height = self.figure.get_size_inches()[1]
        if figure_height == 0:
            self.figure.set_size_inches(self.figure.get_size_inches()[0], 0.01)

        mpl_waypoints = dict()
        for k, v in waypoints.items():
            color = self._waypoint_styles[k]["color"]
            marker = self._waypoint_styles[k]["style"]

            if isinstance(v["gear_lon"], pd.Series) and not v["gear_lon"].empty and \
                    isinstance(v["gear_lat"], pd.Series) and not v["gear_lat"].empty:
                lon = v["gear_lon"].iloc[0]
                lat = v["gear_lat"].iloc[0]

            elif isinstance(v["gear_lon"], float) and isinstance(v["gear_lat"], float):
                lon = v["gear_lon"]
                lat = v["gear_lat"]

            else:
                continue

            # logging.info(f'PLOTTING GEAR WAYPOINT: {lon}, {lat}, {color}, {marker}, {visible}, {label_type}')
            point = self.axes[0].scatter(lon, lat, visible=visible,
                                     color=color, marker=marker, s=150, zorder=10, label=label_type)

            mpl_waypoints[k] = point

        return mpl_waypoints

    def _distance_fished_calculations_completed(self, gear_tracklines):
        """
        Method to catch the return from the DistanceFishedWorker thread
        :return:
        """
        if self._calculate_distance_fished_thread:
            self._calculate_distance_fished_thread.quit()

        if gear_tracklines is not None:
            logging.info(f"gear tracklines retrieved, count: {len(gear_tracklines)}")
            for k, v in gear_tracklines.items():

                gear_name = f"Gear {k}"

                distance_N = v["distance_M"] * N_PER_M if v["distance_M"] else None
                speed = v["speed"] if v["speed"] else None
                self.distanceCalculated.emit(k, distance_N, speed)

                # logging.info(f"Emitting {k} > {distance}, {speed}")

                # Skip trying to plot the Vessel GCD as there is no gearline for this as we have the real vessel line
                if k == "Vessel GCD":
                    continue

                # Plot Gear Trackline
                start_haul = None
                end_of_haul = None
                if "dataframe" in v:
                    df_gear = v["dataframe"]
                    if "waypoints" in v:
                        start_haul = v["start_haul"]
                        end_of_haul = v["end_of_haul"]

                    v["line"] = self.plot_gear_trackline(type=gear_name, created=True,
                                                         df_gear=df_gear, start_haul=start_haul, end_of_haul=end_of_haul)
                    self.gearLinePlotted.emit(gear_name, True)

                # Plot Waypoints on Gear Trackline
                if "waypoints" in v:
                    waypoints = v["waypoints"]
                    v["mpl_waypoints"] = self.plot_gear_waypoints(label_type=gear_name, created=True, waypoints=waypoints)

                # Add the Gear Trackline + Data to self.gear_lines
                self.track_lines[gear_name] = v

        self.distanceFishedCompleted.emit()

    def calculate_all_distances_fished(self, span, df_depth, df_headrope):
        """
        Method to calculate all of the distances fished for all of the various methods available
        :return:
        """
        # Get the scope - used for all of the Trig Methods + Scope/Distance method + catenary method
        try:
            scope = None
            op_att = OperationAttributes.select(OperationAttributes)\
                        .join(OperationsFlattenedVw, on=(OperationsFlattenedVw.operation == OperationAttributes.operation))\
                        .switch(OperationAttributes)\
                        .join(ReportingRules, on=(ReportingRules.reporting_rule == OperationAttributes.reporting_rules))\
                        .join(Lookups, on=(Lookups.lookup == ReportingRules.reading_type_lu))\
                        .where(OperationsFlattenedVw.tow_name == self._app.settings.haul,
                               Lookups.type == "Reading Type",
                               Lookups.value == "Scope (ftm)")
            logging.info(f"scope record count {op_att.count()}")
            if op_att.count() == 1:
                scope = float(op_att.first().attribute_numeric) * FTM_PER_M        # Convert Fathoms to Meters

        except Exception as ex:
            scope = None

        self._clear_gear_items()

        logging.info("calling DistanceFished instance")

        kwargs = {"track_lines": self.track_lines, "scope": scope, "span": span, "df_depth": df_depth,
                  "df_headrope": df_headrope}
        self._calculate_distance_fished_worker = DistanceFishedWorker(kwargs=kwargs)
        self._calculate_distance_fished_worker.moveToThread(self._calculate_distance_fished_thread)

        self._calculate_distance_fished_worker.calculationsCompleted.connect(self._distance_fished_calculations_completed)

        self._calculate_distance_fished_thread.started.connect(self._calculate_distance_fished_worker.run)
        self._calculate_distance_fished_thread.start()

    @pyqtSlot(str, str, bool)
    def save_gearline_to_db(self, haul=None, technique=None, override=True, trackline=None):
        """
        Method to save the provided gear line to the FRAM_CENTRAL database
        :param technique: str
        :param override: boolean - set to true to delete any existing tracks for this operation
        :return:
        """
        if haul is None or technique is None:
            return

        logging.info(f"Saving gear line to the database: {technique}")

        # Check if a gearline already exists for this haul, if so, delete it
        try:
            if override:
                op_id = OperationsFlattenedVw.get(OperationsFlattenedVw.tow_name == haul).operation
                OperationTracklines.delete().where(OperationTracklines.operation == op_id).execute()

        except Exception as ex:
            logging.error(f"Error deleting an existing trackline: {ex}")

        # Save the gear line to Operation_Tracklines
        try:
            trackname = f"Gear {technique}"
            if trackname in self.track_lines:

                # Get the Reporting Rule ID
                derivation_id = Lookups.get(Lookups.type == "Derivation Type",
                                            Lookups.value.contains(TECHNIQUES_MAPPING[technique]["value"]),
                                            Lookups.subvalue.contains(TECHNIQUES_MAPPING[technique]["subvalue"])).lookup
                reading_type_id = Lookups.get(Lookups.type == "Reading Type",
                                               Lookups.value == "Latitude-Longitude Pair").lookup
                rule_id = ReportingRules.get(ReportingRules.reading_type_lu == reading_type_id,
                                            ReportingRules.derivation_type_lu == derivation_id,
                                            ReportingRules.rule_type == "postseason",
                                            ReportingRules.is_numeric).reporting_rule

                # Insert the Gear Trackline into Operation_Tracklines
                trackline = self.track_lines[trackname]
                df_trackline = trackline["dataframe"]
                df_trackline = df_trackline.loc[:, ["times", "gear_lat", "gear_lon"]]
                df_trackline = df_trackline.rename(columns={"times": "date_time", "gear_lat": "latitude",
                                                            "gear_lon": "longitude"})
                df_trackline.loc[:, "date_time"] = df_trackline.apply(lambda x: arrow.get(x["date_time"]).isoformat(), axis=1)
                df_trackline.loc[:, "operation"] = op_id
                df_trackline.loc[:, "reporting_rule"] = rule_id
                df_trackline_dict = df_trackline.to_dict('records')

                logging.info(f"trackline to insert, size: {len(df_trackline_dict)}")
                # logging.info(f"samples: {df_trackline_dict[0:3]}")

                # times / gear_lat / gear_lon > operation_id, datetime, latitude, longitude, reporting_rule_id
                with self._app.settings._database.atomic():
                    OperationTracklines.insert_many(df_trackline_dict).execute()

                logging.info(f"saved distance fished")

                # Save the Pre/Post Haulback and Total Distance, as well as the Speed
                distance_pre_M = trackline["distance_pre_M"]
                distance_post_M = trackline["distance_post_M"]
                distance_M = trackline["distance_M"]

                dist_reading_type_id = Lookups.get(Lookups.type == "Reading Type",
                                                   Lookups.value == "Fished Distance").lookup
                dist_reading_basis_id = Lookups.get(Lookups.type == "Reading Basis",
                                                    Lookups.value == "net touchdown to liftoff").lookup

                # Change all of the other distances fished for this op_id to is_best_value = False
                rules = ReportingRules.select().where(
                    ReportingRules.reading_type_lu == dist_reading_type_id,
                    ReportingRules.reading_basis_lu == dist_reading_basis_id,
                    ReportingRules.rule_type == "postseason",
                    ReportingRules.is_numeric
                )
                OperationAttributes.update(is_best_value=False).where(
                    OperationAttributes.operation == op_id,
                    OperationAttributes.reporting_rules << rules
                ).execute()

                # op_atts = OperationAttributes.select()\
                #     .join(ReportingRules, on=(OperationAttributes.reporting_rules == ReportingRules.reporting_rule))\
                #     .where(ReportingRules.reading_type_lu == dist_reading_type_id,
                #             ReportingRules.reading_basis_lu == dist_reading_basis_id,
                #             ReportingRules.rule_type == "postseason",
                #             ReportingRules.is_numeric,
                #             OperationAttributes.operation == op_id)
                # for op_att in op_atts:
                #     op_att.is_best_value = False
                #     op_att.save()
                    # OperationAttributes.update(is_best_value=False)\
                    #     .where(OperationAttributes.operation_attribute == op_att.operation_attribute).execute()

                # Get or Create the operation attribute for the current distance fished type
                rule_id = ReportingRules.get(ReportingRules.reading_type_lu == dist_reading_type_id,
                                             ReportingRules.reading_basis_lu == dist_reading_basis_id,
                                             ReportingRules.derivation_type_lu == derivation_id,
                                             ReportingRules.rule_type == "postseason",
                                             ReportingRules.is_numeric).reporting_rule

                op_att, created = OperationAttributes.get_or_create(
                                    operation=op_id,
                                    reporting_rules=rule_id,
                                    defaults={"attribute_numeric": distance_M, "is_best_value": True}
                                )

                logging.info(f"new distance fished op_attribute created status: {created}")
                if not created:
                    OperationAttributes.update(attribute_numeric=distance_M, is_best_value=True)\
                        .where(OperationAttributes.operation == op_id,
                               OperationAttributes.reporting_rules == rule_id).execute()

                self.tracklineSaved.emit(technique)


        except Exception as ex:
            logging.error(f"Error saving a new trackline: {ex}")

        # Save the distance fished (pre, post, total) to Operation_Attributes, check if they exist first
        try:
            pass
        except Exception as ex:
            logging.error(f"Error saving a distance fished to Operation Attributes: {ex}")

    def stop_background_threads(self):

        if self._calculate_distance_fished_worker:
            self._calculate_distance_fished_worker.stop()

    @pyqtSlot(str, bool)
    def toggle_trackline_visibility(self, trackline, visibility):
        """
        Method to change the visibility of the given trackline
        :param trackline:
        :return:
        """

        # logging.info(f"toggling tracklines: {trackline} > {visibility}....keys: {self.track_lines.keys()}")
        if trackline in self.track_lines:
            lines = [x for i, x in enumerate(self.axes[0].lines) if x.get_label() == trackline or \
                                                                    x.get_gid() == f"{trackline} invalid"]

            for line in lines:
                if line.get_label() == "_nolegend_":
                    if self._show_invalids:
                        line.set_visible(visibility)
                    else:
                        line.set_visible(False)
                else:
                    line.set_visible(visibility)

            if "mpl_waypoints" in self.track_lines[trackline]:
                points = self.track_lines[trackline]["mpl_waypoints"]
                for k, v in points.items():
                    v.set_visible(visibility)
            self.qml_item.draw_idle()

    def toggle_invalids(self, value):
        """
        Method to toggle the invalids on/off
        :param value: bool - True - show them / False - hide them
        :return:
        """
        if not isinstance(value, bool):
            return

        self._show_invalids = value

        # Toggle all of the invalid time series graph lines
        for ax in self.figure.axes:
            invalid_lines = [x for x in ax.lines if "_nolegend_" in x.get_label()]
            logging.info(f"toggling map invalids, count: {len(invalid_lines)}, value: {value}")
            for line in invalid_lines:
                line.set_visible(value)

        # Refresh the graphs
        self.qml_item.draw_idle()

    def plot_median_point(self, latitude, longitude):
        """
        Method to plot the median point of the gear track line
        :param latitude:
        :param longitude:
        :return:
        """
        if latitude is None or longitude is None:
            return

        self.axes[0].scatter(longitude, latitude, color="blue", marker="+", s=150, zorder=10, label="Gear median",
                             visible=self._show_medians)
        self.qml_item.draw_idle()

    def toggle_median_point(self, value):
        """
        Method to toggle on/off the median gear point
        :param value: bool - True/False too show/hide the median gear point
        :return:
        """
        if not isinstance(value, bool):
            return

        self._show_medians = value

        # Toggle the gear median point
        for i, collection in enumerate(self.axes[0].collections):
            if "gear median" in collection.get_label().lower():
                collection.set_visible(value)

                # Refresh the map display
                self.qml_item.draw_idle()

                break


class TimeSeries(QObject):
    """
    Class for the TimeSeriesScreen
    """
    haulsModelChanged = pyqtSignal()
    availableImpactFactorsModelChanged = pyqtSignal()
    selectedImpactFactorsModelChanged = pyqtSignal()
    mplMapChanged = pyqtSignal()

    haulNumberChanged = pyqtSignal()
    xMinChanged = pyqtSignal()
    xMaxChanged = pyqtSignal()
    timeSeriesThreadCompleted = pyqtSignal(bool, str, arguments=["status", "msg"])
    # timeSeriesLoaded = pyqtSignal(QVariant, arguments=["timeSeriesDict",])
    timeSeriesCleared = pyqtSignal(str, arguments=["reading_type",])
    allTimeSeriesCleared = pyqtSignal()
    displaySeriesChanged = pyqtSignal()

    # waypointsLoaded = pyqtSignal(QVariant, arguments=["waypoints",])
    toolModeChanged = pyqtSignal()
    # timeSeriesDataChanged = pyqtSignal()
    showInvalidsChanged = pyqtSignal()
    showMeansChanged = pyqtSignal()

    timeMeasuredChanged = pyqtSignal()
    commentsPerformanceRetrieved = pyqtSignal(str, str, str, str, str,
                                              arguments=["comments", "performance_field", "minimum_time_met_field",
                                                         "performance_qaqc", "minimum_time_met_qaqc"])
    impactFactorsRetrieved = pyqtSignal(str, arguments=["impact_factors",])
    haulDetailsRetrieved = pyqtSignal(str, str, str, str, arguments=["haul_date", "haul_start", "haul_end", "fpc"])
    commentAdded = pyqtSignal(str, arguments=["comment",])
    towPerformanceAdjusted = pyqtSignal(str, bool, bool, arguments=["status", "tow_performance", "minimum_time_met"])

    activeWaypointTypeChanged = pyqtSignal()

    errorEncountered = pyqtSignal(str, arguments=["msg",])
    mouseReleased = pyqtSignal()

    bcsPExistsChanged = pyqtSignal()
    bcsSExistsChanged = pyqtSignal()
    bcsCExistsChanged = pyqtSignal()

    showLegendsChanged = pyqtSignal()

    haulLoading = pyqtSignal()
    haulLoadingFinished = pyqtSignal(str, QVariant, QVariant, arguments=["technique", "distance", "speed"])

    # Invalid Points
    dataPointsModelChanged = pyqtSignal()      # For the Invalids dialog
    timeSeriesModelChanged = pyqtSignal()      # For the Invalids selection of which time series to modify

    activeTimeSeriesChanged = pyqtSignal()     # For the Time Series Shifting (i.e. adjusting temporal offset)

    # Distance Fished Actions
    clearDistancesFished = pyqtSignal()

    # Calculate Means Actions
    meansModelChanged = pyqtSignal()
    meansCalculated = pyqtSignal(str, str, float, arguments=["mean_type", "legend_name", "mean"])
    meansSaved = pyqtSignal(QVariant, arguments=["mean_types", ])
    meansLoaded = pyqtSignal(str, QVariant, arguments=["mean_type", "mean"])
    meansSeriesChanged = pyqtSignal(str, str, arguments=['mean_type', 'series'])

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db
        self._functions = CommonFunctions()

        self._time_series_model = TimeSeriesModel()
        self._hauls_model = HaulsModel(app=self._app)
        self._available_impact_factors_model = AvailableImpactFactors(app=self._app)
        self._selected_impact_factors_model = SelectedImpactFactors(app=self._app)

        self._mpl_map = MplMap(app=self._app)
        self._mpl_map.invalidDataPointsFound.connect(self._mpl_map_invalid_data_found)

        self._x_min = QDateTime()
        self._x_max = QDateTime()

        self._load_time_series_thread = QThread()
        self._load_time_series_worker = None

        self._display_series = True
        self._haul_number = None
        self._tool_mode = "pan"
        self._show_invalids = False
        self._show_means = False

        self._time_series_data = []
        self.figure = None

        # Mouse Navigation Items
        self._is_pressed = False
        self.cur_xlim = None
        self.cur_ylim = None
        # self.x0 = None
        # self.y0 = None
        # self.x1 = None
        # self.y1 = None
        self.xpress = None
        self.ypress = None
        self._zoom_scale = 1.2
        self._ylim_max_buffer = 1.05
        self.cur_rect = None

        # measureTime Tool
        self._is_drawing = False
        self._measure_time_rects = []
        self._time_measured = "00:00:00"
        self._time_segments = []

        # addWaypoints - used when a user is manually adjusting the Begin Tow and Net Off Bottom waypoints
        self._active_waypoint_type = None
        self._waypoints = None
        self._postseason_waypoints = {"Begin Tow": [], "Net Off Bottom": [], "Doors At Surface": []}

        # shiftTimeSeries
        self._total_offset = 0
        self._cur_offset = 0
        self.xlim_min = None
        self.last_xpress = None

        self._cur_line = None
        self._cur_invalid_line = None
        self._df_time_shift = None
        self._df_time_shift_invalid = None

        """
        Graphs are:  Bearing, Depth, Net_Dimension, Range, Speed, Temperature, Tilt, Waypoints
        """
        self._to_graphs = OrderedDict({"Tilt": "Deg", "Depth": "M", "Temperature": "C", "Range": "M", "Speed": "K",
                                       "Net_Dimension": "M", "Bearing": "Deg"}) #"""Waypoints": None})
        # self.graphs = ["X Tilt Angle (Deg)", "Depth (M)", "Temperature (C)", "Horizontal Range to Target (M)",
        #                "Speed Over Ground (", "Waypoints"]
        # "Bearing to Target (Deg)", "Headrope Height (M)", "Spread Distance (M)", "Track Made Good", ]

        """
        Mapping data sets:  SC50 Vessel Latitude/Longitude, ITI Latitude/Longitude, Field Waypoints, Center Waypoints
        """
        # self._to_map = ["Latitude", "Longitude"]
        self._to_map = ["Position"]

        self._bcs_p_exists = False
        self._bcs_s_exists = False
        self._bcs_c_exists = False

        self._show_legends = False

        self._data_points_model = DataPointsModel(app=self._app)
        self._data_points_model.timeSeriesUpdated.connect(self._update_time_series)

        self._means_model = MeansModel(app=self._app)

        self._last_invalid_points = None

        self._active_time_series = None
        self._active_equipment = None

        self.df_vessel = None

    def set_qml_item(self, item=None):
        self.qml_item = item
        self.figure = self.qml_item.getFigure()
        self.create_graphes_axes()

    def create_graphes_axes(self):
        """
        Method to create all of the axes once the figure has been created
        :return:
        """
        self.scale = 1.1
        self.gs = gridspec.GridSpec(len(self._to_graphs), 1)
        self.gs.update(wspace=0, hspace=0)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        self.axes = []
        i = 0

        auto = mdates.AutoDateLocator()
        auto_minor = AutoMinorLocator()
        fmt = mdates.DateFormatter('%H:%M:%S\n%m/%d/%y', tz=tzlocal())

        for k, v in self._to_graphs.items():
            if i == 0:
                ax = self.figure.add_subplot(self.gs[i, :], label=k)
            else:
                ax = self.figure.add_subplot(self.gs[i, :], sharex=self.axes[0], label=k)

            ax.xaxis_date("US/Pacific")
            # ax.fmt_data = fmt

            ax.xaxis.set_major_locator(auto)
            ax.xaxis.set_major_formatter(fmt)
            ax.xaxis.set_minor_locator(auto_minor)

            datemin = datetime(year=int(self._app.settings.year), month=1, day=1)
            datemax = datetime(year=int(self._app.settings.year) + 1, month=1, day=1)
            ax.set_xlim(datemin, datemax)

            if v:
                ax.set_ylabel(f"{k}\n({v})", fontweight='bold', fontsize=10)
            else:
                ax.set_ylabel(f"{k}", fontweight='bold', fontsize=10)
            ax.yaxis.grid(True)
            ax.xaxis.grid(True)
            ax.set_ylim(0, 1)

            if i >= len(self._to_graphs) - 1:
                ax.xaxis.set_visible(True)

            self.axes.append(ax)
            i += 1

        self.figure.subplots_adjust(left=0.15, right=1.0, top=1.0, bottom=0.05)

        self.qml_item.mpl_connect('button_press_event', self.on_press)
        self.qml_item.mpl_connect('button_release_event', self.on_release)
        self.qml_item.mpl_connect("motion_notify_event", self.on_motion)
        self.qml_item.mpl_connect('scroll_event', self.on_scroll)
        self.qml_item.mpl_connect('figure_leave_event', self.on_figure_leave)
        # self.qml_item.mpl_connect('key_press_event', self.on_key_press)

        # logging.info(f"before draw_idle")
        # self.qml_item.draw_idle()
        # logging.info(f"after draw_idle")

    def on_key_press(self, event):
        logging.info(f"key: {event.key}")

        if self.toolMode in ["pan", "zoomVertical"]:

            sys.stdout.flush()
            if event.key == 'x':
                self.on_scroll(event)
                pass

    def on_figure_leave(self, event):

        QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))

    def on_press(self, event):

        if event.inaxes is None: return

        gca = event.inaxes
        self.xpress = event.xdata
        self.ypress = event.ydata

        if self.toolMode in ["pan", "zoomVertical"]:

            QApplication.setOverrideCursor(QCursor(Qt.OpenHandCursor))
            self._is_pressed = True
            self.cur_xlim = gca.get_xlim()
            self.cur_ylim = gca.get_ylim()

            if event.dblclick:
                # logging.info(f"{event.button}")
                self.on_scroll(event=event)

        elif self.toolMode == "measureTime":
            QApplication.setOverrideCursor(QCursor(Qt.CrossCursor))
            self._is_drawing = True

            self.cur_rect = Rectangle((0, 0), 1, 1, color='lightblue', zorder=100, visible=True, alpha=0.7)
            gca.add_patch(self.cur_rect)
            gca.patches = sorted(gca.patches, key=lambda v: v.get_x())

        elif self.toolMode == "addWaypoint":
            QApplication.setOverrideCursor(QCursor(Qt.SizeHorCursor))
            self._is_pressed = True
            if event.inaxes and event.xdata and event.ydata:

                if self._active_waypoint_type is None:
                    self.errorEncountered.emit("Please select which waypoint to manually adjust first")
                    QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
                    self._is_pressed = False
                    return

                line_exists = True if len(self._postseason_waypoints[self._active_waypoint_type]) > 0 else False
                if self._active_waypoint_type == "Begin Tow":
                    width = 2
                    color = 'g'
                elif self._active_waypoint_type == "Net Off Bottom":
                    width = 2
                    color = 'r'
                else:
                    width = 1
                    color = 'm'
                for i, ax in enumerate(self.axes):
                    if line_exists:
                        self._postseason_waypoints[self._active_waypoint_type][i].set_xdata(event.xdata)
                    else:
                        line = ax.axvline(event.xdata, linewidth=width, color=color, linestyle="dashed")
                        self._postseason_waypoints[self._active_waypoint_type].append(line)
                self.qml_item.draw()

        elif self.toolMode == "invalidData":

            QApplication.setOverrideCursor(QCursor(Qt.CrossCursor))
            self._is_drawing = True
            self.cur_rect = Rectangle((0, 0), 1, 1, color='lightblue', zorder=100, visible=True, alpha=0.7)
            gca.add_patch(self.cur_rect)

        elif self.toolMode == "shiftTimeSeries":

            QApplication.setOverrideCursor(QCursor(Qt.SizeHorCursor))
            self._is_pressed = True

            # Get the total offset
            time_series = [x for x in self._time_series_data if x["legend_name"] == self._active_time_series]
            if len(time_series) == 1:
                time_series_dict = time_series[0]
                self._total_offset = time_series_dict["offset"]

            self._all_lines = [x.lines for x in self.axes]
            self._all_lines = [item for sublist in self._all_lines for item in sublist]     # Collapse the list of lists
            self._all_lines = [x for x in self._all_lines if "_line" not in x.get_label()]

            # self.xlim_min = gca.get_xlim()[0]

            # Get the valid line
            # lines = [x for x in gca.lines if x.get_label() == self._active_time_series]
            # if len(lines) == 1:
            #     line = lines[0]
            #     xy_data = line.get_xydata()
            #     self._df_time_shift = pd.DataFrame(data=xy_data, columns=["original_time", "value"])
            #     self._df_time_shift["time"] = None
            #
            # # Get the invalid lines
            # invalid_lines = [x for x in gca.lines if x.get_label() == "_nolegend_" and x.get_gid() == f"{self._active_time_series} invalid"]
            # if len(invalid_lines) == 1:
            #     self._cur_invalid_line = invalid_lines[0]
            #     xy_data = self._cur_invalid_line.get_xydata()
            #     self._df_time_shift_invalid = pd.DataFrame(data=xy_data, columns=["original_time", "value"])
            #     self._df_time_shift_invalid["time"] = None

    def on_release(self, event):

        QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))

        if self.toolMode in ["pan", "zoomVertical"]:
            self._is_pressed = False

        elif self.toolMode == "measureTime":
            self._is_drawing = False

            if self.cur_rect.get_x() != 0 and self.cur_rect.get_width() != 1:
                start_time = mdates.num2date(self.cur_rect.get_x())
                end_time = mdates.num2date(self.cur_rect.get_x() + self.cur_rect.get_width())
                start_time, end_time = sorted([start_time, end_time])
                self._time_segments.append([start_time, end_time])

                self._calculate_total_time()

            # gca = event.inaxes
            # mouse_rect = gca.patches[0]
            # mouse_rect.set_visible(self._is_drawing)
            # self.qml_item.draw()

        elif self.toolMode == "addWaypoint":
            self._update_event_datetime(event=self._active_waypoint_type, date_time=mdates.num2date(event.xdata))
            self._is_pressed = False
            self.activeWaypointType = None

        elif self.toolMode == "invalidData":

            if event.inaxes is None: return

            gca = event.inaxes

            self._is_drawing = False
            if self.cur_rect.get_x() != 0 and self.cur_rect.get_width() != 1:

                # Patches = drawing rectangle, Lines = Time Series + Waypoint vertical lines

                # Get the x/y min/max of the currently drawn selection rectangle
                x_min, x_max = sorted([self.cur_rect.get_x(), self.cur_rect.get_x() + self.cur_rect.get_width()])
                y_min, y_max = sorted([self.cur_rect.get_y(), self.cur_rect.get_y() + self.cur_rect.get_height()])

                logging.info(f"Invalid rectangle boundaries:  xmin: {x_min}, xmax: {x_max} >>> ymin: {y_min}, ymax: {y_max}")

                # Iterate through all of the time series lines, but don't consider the waypoint lines or the invalid data points lines
                invalid_ids = []
                # lines = [x for x in gca.lines if "_line" not in x.get_label() and "invalid" not in x.get_label()]

                # items = [[x.get_label(), x.get_gid()] for x in gca.lines]
                # logging.info(f"lines in the time series graph, checking to set invalid: {items}")

                lines = [x for x in gca.lines if "_line" not in x.get_label() and x.get_label() != "_nolegend_" and
                                                    "mean" not in x.get_label()]
                logging.info(f"Lines in the time series graph, checking to set invalid, count: {len(lines)}")
                for line in lines:
                    label = line.get_label()
                    logging.info(f"Mark as invalid from Time Series: {label}")

                    xy_data = line.get_xydata()
                    ids = line.get_gid()

                    # Find the newly selected invalid points for the current time series line, within the selection rectangle
                    invalid_pts = [(i, [mdates.num2date(pt[0]), pt[1]]) for i, pt in enumerate(xy_data)
                                   if (x_min <= pt[0] <= x_max) and (y_min <= pt[1] <= y_max)]
                    idx = set([x[0] for x in invalid_pts])

                    # Update the time series points dataframe to set these new points as invalid
                    time_series = [i for i, x in enumerate(self._time_series_data) if x["legend_name"] == label]
                    if len(time_series) == 1:
                        ts_idx = time_series[0]
                        df = self._time_series_data[ts_idx]["points"]
                        df.loc[df["id"].isin(ids.loc[idx]), "invalid"] = True
                        self._time_series_data[ts_idx]["points"] = df

                        # Redraw the valid and invalid lines
                        self._draw_time_series_graph(idx=ts_idx)

                    # Find all of the points that don't include the invalid_pts
                    # xy_data_clean = np.array([pt for i, pt in enumerate(xy_data) if i not in idx])
                    # xy_data_clean = xy_data_clean.T     # Transpose to be a 2 x N array for use with set_data later
                    # line.set_data(xy_data_clean)

                    # Grow the invalid_ids to include all invalid_pts from all of the time series for this graph
                    if invalid_ids:
                        invalid_ids.extend(ids.loc[idx].tolist())
                    else:
                        invalid_ids = ids.loc[idx].tolist()

                    logging.info(f"Number of invalid pts: {len(invalid_pts)}")

                logging.info(f"invalid_ids selected:\t{invalid_ids}")

                # Capture the invalid_ids into an instance variable to enable undo against these points
                # self._last_invalid_points = invalid_ids

                # Update the map display as well:
                start_haul = self._waypoints.loc["Start Haul", "best_datetime"]
                end_of_haul = self._waypoints.loc["End Of Haul", "best_datetime"]
                valid_ids = []
                self._mpl_map._redraw_track_line(time_series=label, start_haul=start_haul, end_of_haul=end_of_haul,
                                                 valid_ids=valid_ids, invalid_ids=invalid_ids)

                self._toggle_points_validity(data=invalid_ids, status=True)

                del gca.patches[:]
                logging.info(f"before draw_idle")
                # self.qml_item.draw()
                self.qml_item.draw_idle()
                logging.info(f"after draw_idle")

        elif self.toolMode == "shiftTimeSeries":

            self._is_pressed = False

            # Update the time_series_dict offset value
            try:
                time_series = [x for x in self._time_series_data if x["legend_name"] == self._active_time_series]
                if len(time_series) == 1:
                    time_series_dict = time_series[0]

                    # Set the total offset, do this just once
                    dx = event.xdata - self.xpress
                    dx_sec = int(math.ceil(dx * SEC_PER_DAY))
                    self._total_offset += dx_sec

                    # Update the database for the self._active_time_series
                    stream_id = time_series_dict["stream_id"]
                    MeasurementStreams.update(stream_offset_seconds=self._total_offset) \
                        .where(MeasurementStreams.measurement_stream == stream_id).execute()
                    time_series_dict["offset"] = self._total_offset

                    # Get the equipment of the active_time_series, and then find all time series that have the same equipment
                    # These should all be offsetted similarly. We only do this if it equals ITI or SBE39
                    active_equipment = time_series_dict["equipment"]
                    time_series = [x for x in self._time_series_data if x["equipment"] == active_equipment and \
                                                                        active_equipment in ["ITI", "SBE39"]]
                    for series in time_series:

                        # Update the database for all of the assoociated time series related to the self._active_time_series
                        # but do not update (again) the data for the self._active_time_series as that was just done above
                        if series["legend_name"] != self._active_time_series:
                            stream_id = series["stream_id"]
                            MeasurementStreams.update(stream_offset_seconds=self._total_offset) \
                                .where(MeasurementStreams.measurement_stream == stream_id).execute()
                            series["offset"] = self._total_offset

                        start_haul = self._waypoints.loc["Start Haul", "best_datetime"]
                        end_of_haul = self._waypoints.loc["End Of Haul", "best_datetime"]

                        # Update the MplMap time_series data as well, for range/bearing only - TODO - Todd Hay
                        if "Gear Horizontal Range to Target" in series["legend_name"] or \
                            "Gear Bearing to Target" in series["legend_name"]:

                            source_type = "range_bearing"
                            df_rb, legend_names = self.create_rb_gear_df(df_vessel=self.df_vessel)

                            if isinstance(df_rb, pd.DataFrame) and not df_rb.empty:
                                self._mpl_map.plot_track_line(type="iti r/b", df=df_rb, start_haul=start_haul,
                                                          end_of_haul=end_of_haul,
                                                          source_type=source_type, legend_names=legend_names)

                        # If the Gear Latitude / Longitude are found, update the mpl map gear iti $iigll line
                        elif "Gear Latitude" in series["legend_name"] or \
                             "Gear Longitude" in series["legend_name"]:

                            gear_types = ["Latitude", "Longitude"]
                            # gear_series = [x for x in self._time_series_data if
                            #                    x["reading_type"] in gear_types and x["reading_basis"] == "Gear"]
                            # gear_series = sorted(gear_series, key=lambda x: (x["priority"], x["reading_type"]))
                            # data, legend_names = self.create_lat_lon_df(data_type="iti $iigll", time_series=gear_series)
                            # source_type = "latitude_longitude"
                            #
                            # if isinstance(data, pd.DataFrame) and not data.empty:
                            #     self._mpl_map.plot_track_line(type="iti $iigll", df=data, start_haul=start_haul,
                            #                               end_of_haul=end_of_haul,
                            #                               source_type=source_type, legend_names=legend_names)

                self._total_offset = 0
                self._cur_offset = 0
                self._cur_line = None
                self._cur_invalid_line = None
                self._df_time_shift = None
                self._df_time_shift_invalid = None

                self.last_xpress = None

            except Exception as ex:
                logging.error(f"Error updating the time series offset: {time_series_dict['legend_name']} >>> {ex}")

        self.mouseReleased.emit()

    def on_motion(self, event):
        """
        Method to capture mouse movements
        :param event:
        :return:

        """
        gca = event.inaxes

        if self.toolMode == "pan":
            if not self._is_pressed: return

            if event.inaxes is None or self.xpress is None or self.ypress is None: return
            dx = event.xdata - self.xpress
            # dy = event.ydata - self.ypress
            self.cur_xlim -= dx
            # self.cur_ylim -= dy
            gca.set_xlim(self.cur_xlim)
            # gca.set_ylim(self.cur_ylim)
            self.qml_item.draw_idle()

        elif self.toolMode == "zoomVertical":
            if not self._is_pressed: return

            if event.inaxes is None or self.xpress is None or self.ypress is None: return
            dx = event.xdata - self.xpress
            dy = event.ydata - self.ypress
            self.cur_xlim -= dx
            self.cur_ylim -= dy
            gca.set_xlim(self.cur_xlim)
            gca.set_ylim(self.cur_ylim)
            self.qml_item.draw_idle()

        elif self.toolMode == "measureTime":
            if self._is_drawing and event.xdata and event.ydata:

                self.cur_rect.set_width(event.xdata - self.xpress)
                self.cur_rect.set_height(event.ydata - self.ypress)
                self.cur_rect.set_xy((self.xpress, self.ypress))
                self.qml_item.draw()

        elif self.toolMode == "addWaypoint":
            if self._is_pressed and event.inaxes and event.xdata and event.ydata:
                for i, ax in enumerate(self.axes):
                    self._postseason_waypoints[self._active_waypoint_type][i].set_xdata(event.xdata)
                self.qml_item.draw()

        elif self.toolMode == "invalidData":

            if self._is_drawing and event.xdata and event.ydata:

                self.cur_rect.set_width(event.xdata- self.xpress)
                self.cur_rect.set_height(event.ydata - self.ypress)
                self.cur_rect.set_xy((self.xpress, self.ypress))
                self.qml_item.draw_idle()

        elif self.toolMode == "shiftTimeSeries":

            if event.xdata and self._is_pressed: # and self._cur_line:

                if self.last_xpress is None:
                    self.last_xpress = self.xpress

                dx = event.xdata - self.last_xpress

                # Calculate the overall offset from the initial press and convert to seconds
                # dx = event.xdata - self.xpress
                # dx_current = event.xdata - self.xlim_min
                # dx = dx_current - self.dx_init
                # self._cur_offset = int(math.ceil(dx * SEC_PER_DAY))

                # logging.info(f"dx: {dx} >>> sec: {dx * SEC_PER_DAY}")

                # Valid Lines
                valid_lines = [x for x in self._all_lines if f"({self._active_equipment})" in x.get_label()]
                for line in valid_lines:
                    xy_data = line.get_xydata()
                    df = pd.DataFrame(data=xy_data, columns=["time", "value"])
                    df.loc[:, "time"] = df.loc[:, "time"] + dx
                    line.set_data(df["time"], df["value"])

                invalid_lines = [x for x in self._all_lines if x.get_label() == "_nolegend_" and "invalid" in x.get_gid()]
                for line in invalid_lines:
                    xy_data = line.get_xydata()
                    df = pd.DataFrame(data=xy_data, columns=["time", "value"])
                    df.loc[:, "time"] = df.loc[:, "time"] + dx
                    line.set_data(df["time"], df["value"])

                # Valid Line
                # self._df_time_shift.loc[:, "time"] = self._df_time_shift.loc[:, "original_time"] + dx
                # self._cur_line.set_data(self._df_time_shift["time"], self._df_time_shift["value"])

                # Invalid Line
                # self._df_time_shift_invalid.loc[:, "time"] = self._df_time_shift_invalid.loc[:, "original_time"] + dx
                # self._cur_invalid_line.set_data(self._df_time_shift_invalid["time"], self._df_time_shift_invalid["value"])

                self.last_xpress = event.xdata

                # Redraw the lines
                self.qml_item.draw_idle()

    def on_scroll(self, event):
        # gca = self.figure.gca()
        gca = event.inaxes
        cur_xlim = gca.get_xlim()
        cur_ylim = gca.get_ylim()

        xdata = event.xdata  # get event x location
        ydata = event.ydata  # get event y location

        if event.button == 'down':
            # deal with zoom out
            scale_factor = self._zoom_scale
        elif event.button == 'up':
            # deal with zoom in
            scale_factor = 1 / self._zoom_scale
        else:
            # deal with something that should never happen
            scale_factor = 1/2
            # print (event.button)

        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

        if self.toolMode in ["pan", "shiftTimeSeries"]:
            gca.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * (relx)])
        elif self.toolMode == "zoomVertical":
            gca.set_ylim([ydata - new_height * (1-rely), ydata + new_height * (rely)])

        self.qml_item.draw()


    @pyqtSlot(result=QVariant)
    def getMeanTypeTimeSeries(self):
        """
        Method to get a dictionary of the available timeSeries for a meanType
        :return:
        """
        results = {"Depth": [], "Doorspread": [], "Latitude": [], "Longitude": [],
                    "Net Height": [], "Temperature": [], "Wingspread": []}

        for x in self._time_series_data:
            if x["reading_type"] == "Depth":
                results["Depth"].append(x["legend_name"])
            elif x["reading_type"] == "Spread Distance" and x["reading_basis"] == "Doors":
                results["Doorspread"].append(x["legend_name"])
            elif x["reading_type"] == "Headrope Height":
                results["Net Height"].append(x["legend_name"])
            elif x["reading_type"] == "Temperature":
                results["Temperature"].append(x["legend_name"])
            elif x["reading_type"] == "Spread Distance" and x["reading_basis"] == "Wings":
                results["Wingspread"].append(x["legend_name"])

        lat_values = [f"Gear Latitude {k.replace('Gear', '').strip()}" for k, v in self._mpl_map.track_lines.items() if "Gear" in k]
        lon_values = [f"Gear Longitude {k.replace('Gear', '').strip()}" for k, v in self._mpl_map.track_lines.items() if "Gear" in k]
        results["Latitude"] = lat_values
        results["Longitude"] = lon_values

        results = {k: sorted(v) for k, v in results.items()}
        for k, v in results.items():
            results[k] = ["Do Not Calculate"] + v

        return results

    @pyqtSlot(str, str)
    def calculate_means(self, range_bottom, range_top):
        """
        Method to calculate the means for a number of time series
        :param range_bottom: str -
        :param range_top:
        :return:
        """
        try:
            bottom_pct = int(range_bottom) / 100
            top_pct = int(range_top) / 100

            begin_tow = self._waypoints.loc["Begin Tow", "best_datetime"] if \
                self._waypoints.loc["Begin Tow", "best_datetime"] is not None and \
                self._waypoints.loc["Begin Tow", "best_datetime"] is not pd.NaT else \
                self._waypoints.loc["Begin Tow", "datetime"]
            begin_tow = arrow.get(begin_tow).isoformat()
            net_off_bottom = self._waypoints.loc["Net Off Bottom", "best_datetime"] if \
                self._waypoints.loc["Net Off Bottom", "best_datetime"] is not None and \
                self._waypoints.loc["Net Off Bottom", "best_datetime"] is not pd.NaT else \
                self._waypoints.loc["Net Off Bottom", "datetime"]
            net_off_bottom = arrow.get(net_off_bottom).isoformat()

            logging.info(f"begin_tow={begin_tow}, net_off_bottom={net_off_bottom}")

            lat_lon_found = False

            gear_lines = {k: v for k, v in self._mpl_map.track_lines.items() if "vessel" not in k.lower() and
                         "gear" in k.lower()}
                # legend_name.lower() == k.lower()}
            gear_keys = list(gear_lines.keys())
            logging.info(f"gear_line keys = {gear_keys}")

            for row in self.meansModel.items:

                legend_name = row["timeSeries"]
                # gear_name = f"Gear {legend_name}"
                mean_type = row["meanType"]

                logging.info(f"calculating {mean_type} mean > {legend_name}")

                if legend_name == "Do Not Calculate":
                    logging.info(f"\tskipping mean calculation")
                    continue

                if row["meanType"] in ["Latitude", "Longitude"] and not lat_lon_found:

                    gear_time_series = "Gear " + legend_name.replace(f"Gear {row['meanType']}", "").strip()
                    logging.info(f"\tgear_time_series = {gear_time_series}")
                    if gear_time_series in gear_lines:
                        gear_line = gear_lines[gear_time_series]
                        df = gear_line["dataframe"].copy(deep=True)

                        logging.info(f"\t\tfound the time series in gear lines, calculating the lat and lon medians")

                        logging.info(f"\t\tgear line cols: {df.columns.values}")

                        # Mask the dataframe by only getting items when net is on bottom
                        mask = (df["times"] >= begin_tow) & (df["times"] <= net_off_bottom)
                        df = df.loc[mask]

                        # Calculate the medians
                        lat_median = df.loc[:, "gear_lat"].median()
                        lon_median = df.loc[:, "gear_lon"].median()

                        # Emit the meansCalculated signal to populate the tvCalculateMeans table in TimeSeriesScreen.qml
                        self.meansCalculated.emit("Latitude", legend_name, lat_median)
                        self.meansCalculated.emit("Longitude", legend_name, lon_median)

                        # Set lat_lon_found to true so as to not process this data again
                        lat_lon_found = True

                else:

                    time_series = [x for x in self._time_series_data if x["legend_name"] == legend_name]
                    if len(time_series) == 1:
                        series = time_series[0]

                        # Get the series data frame
                        df = series["points"].copy(deep=True)

                        # Adjust it per the offset
                        offset = series["offset"]
                        df.loc[:, "times"] = df.loc[:, "times"].apply(lambda x: arrow.get(x).shift(seconds=offset).datetime)

                        # Mask the dataframe by throwing out invalids and only getting items when net is on bottom
                        mask = (~df["invalid"]) & (df["times"] >= begin_tow) & (df["times"] <= net_off_bottom)
                        df = df.loc[mask]

                        # Get the portion of the signal specified by the user (i.e. using the bottom / top of the range)
                        size = len(df)
                        bottom = math.floor(size * bottom_pct)
                        top = math.ceil(size * top_pct)

                        # Calculate the mean
                        mean = df.iloc[bottom:top].loc[:, "values"].mean()
                        logging.info(f"\tmean: {mean}")

                        self.meansCalculated.emit(mean_type, legend_name, mean)

            # Draw the actual mean lines and median points
            self.draw_means()

        except Exception as ex:
            logging.error(f"Error calculating the means: {ex}")

    @pyqtSlot()
    def save_means(self):
        """
        Method to save the means
        :return:
        """

        # Get the Operation ID
        op_id = OperationsFlattenedVw.get(OperationsFlattenedVw.tow_name == self._app.settings.haul).operation

        # Get tow mean and median derivation id (from Lookups)
        try:
            mean_id = Lookups.get(
                Lookups.type == "Derivation Type",
                Lookups.value == "tow",
                Lookups.name == "mean").lookup
            median_id = Lookups.get(
                Lookups.type == "Derivation Type",
                Lookups.name == "median",
                Lookups.value.is_null(True),
                Lookups.subvalue.is_null(True)).lookup
        except Exception as ex:
            logging.error(F"Error retrieving the mean or median lookup type: {ex}")
            return

        # Delete all of the existing means / medians for the given haul
        try:
            rules = ReportingRules.select().where(ReportingRules.derivation_type_lu << [mean_id, median_id],
                                                  ReportingRules.rule_type == "postseason")
            rule_ids = []
            for rule in rules:
                rule_ids.append(rule.reporting_rule)
            OperationAttributes.delete()\
                .where(OperationAttributes.operation == op_id, OperationAttributes.reporting_rules << rule_ids).execute()

        except Exception as ex:
            logging.error(f"Error deleting the means/medians: {ex}")

        results = []

        ReadingTypes = Lookups.alias()
        ReadingBasis = Lookups.alias()
        DerivationTypes = Lookups.alias()

        # Iterate through each of the mean items
        for item in self.meansModel.items:

            if item["timeSeries"] == "Do Not Calculate":
                continue

            rule_id = None
            mean_type = item["meanType"]

            # Save the latitude and longitude items
            if mean_type in ["Latitude", "Longitude"]:
                stream_id = None
                derivation_type_id = median_id
                rules = ReportingRules.select()\
                            .join(ReadingTypes, on=(ReadingTypes.lookup == ReportingRules.reading_type_lu).alias('type'))\
                            .switch(ReportingRules)\
                            .join(ReadingBasis, on=(ReadingBasis.lookup == ReportingRules.reading_basis_lu).alias('basis'))\
                            .switch(ReportingRules)\
                            .join(DerivationTypes, on=(DerivationTypes.lookup == ReportingRules.derivation_type_lu).alias('derivation'))\
                            .where(
                                ReadingTypes.type == "Reading Type", ReadingTypes.value == mean_type,
                                ReadingBasis.type == "Reading Basis", ReadingBasis.value == "Gear",
                                DerivationTypes.type == "Derivation Type", DerivationTypes.name == "median",
                                ReportingRules.rule_type == "postseason"
                            )
                if len(rules) == 1:
                    rule_id = rules.first().reporting_rule

            else:

                series_list = [x for x in self._time_series_data if x["legend_name"] == item["timeSeries"]]
                if len(series_list) == 1:
                    series = series_list[0]
                    stream_id = series["stream_id"]

                    try:
                        reading_basis_id = Lookups.get(Lookups.type == "Reading Basis",
                                                       Lookups.value == series["reading_basis"]).lookup
                        reading_type_id = Lookups.get(Lookups.type == "Reading Type",
                                                      Lookups.value == series["reading_type"]).lookup
                        derivation_type_id = mean_id

                        # logging.info(f"basis={reading_basis_id}, type={reading_type_id}, derivation={derivation_type_id}")

                        # TODO Todd Hay - There is no post-seasaon surface temperature reporting rule FYI, so can
                        # never use the =SBE38 to calculate a temperature, even if no bottom temp exists
                        # Perhaps not an issue

                        # Get the relevant reporting rule id
                        rule_id = ReportingRules.get(ReportingRules.reading_basis_lu==reading_basis_id,
                                                 ReportingRules.reading_type_lu==reading_type_id,
                                                 ReportingRules.derivation_type_lu==derivation_type_id,
                                                 ReportingRules.rule_type == "postseason").reporting_rule
                    except Exception as ex:
                        logging.info(f"Error retrieving the reporting rule for the mean calculation "
                                     f"of {item['timeSeries']}: {ex}")

            # Convert the mean or median value to a float
            try:
                value = float(item["mean"])
            except Exception as ex:
                value = None

            if rule_id:

                # Get or create the OperationAttributes record for this mean or median
                op_att, created = OperationAttributes.get_or_create(
                    operation=op_id,
                    measurement_stream=stream_id,
                    reporting_rules=rule_id,
                    defaults={
                        "attribute_numeric": value,
                        "is_best_value": True
                    }
                )

                # If the record already existed, then just update the record with the latest mean value
                if not created:
                    op_att.attribute_numeric = value
                    op_att.is_best_value = True
                    op_att.save()

                results.append(mean_type)

        logging.info(f"mean_types saved: {results}")

        self.meansSaved.emit(results)

    def _load_means(self, haul_number):
        """
        Method to load the means calculations for the given haul_number
        :param haul_number:
        :return:
        """
        # Re-populate the MeansModel
        self._means_model.populate_model()

        # Get the Operation ID
        op_id = OperationsFlattenedVw.get(OperationsFlattenedVw.tow_name == haul_number).operation

        # Get tow mean and median derivation id (from Lookups)
        mean_id = Lookups.get(
            Lookups.type == "Derivation Type",
            Lookups.value == "tow",
            Lookups.name == "mean").lookup
        median_id = Lookups.get(
            Lookups.type == "Derivation Type",
            Lookups.name == "median",
            Lookups.value.is_null(True),
            Lookups.subvalue.is_null(True)).lookup

        # Iterate through each of the mean items
        for item in self.meansModel.items:

            logging.info(f"mean loading:  basis = {item['basis']}, type = {item['type']} >>"
                         f" default time series = {item['timeSeries']}")

            # Get the basis, type, and derivations for the latitude, longitude, and other mean values
            reading_basis_id = Lookups.get(Lookups.type == "Reading Basis", Lookups.value == item["basis"]).lookup
            reading_type_id = Lookups.get(Lookups.type == "Reading Type", Lookups.value == item['type']).lookup
            derivation_type_id = median_id if item["meanType"] in ["Latitude", "Longitude"] else mean_id

            try:
                # Find the reporting rule_id for the given basis, type, and derivation
                rule_id = ReportingRules.get(ReportingRules.reading_basis_lu == reading_basis_id,
                                             ReportingRules.reading_type_lu == reading_type_id,
                                             ReportingRules.derivation_type_lu == derivation_type_id,
                                             ReportingRules.rule_type == "postseason").reporting_rule

                # Get all of the operation attributes that match this operation and reporting_rule
                op_att = OperationAttributes.select(OperationAttributes, MeasurementStreams, \
                                                    ParsingRulesVw, EquipmentLu) \
                    .join(MeasurementStreams, on=(MeasurementStreams.measurement_stream == \
                                                  OperationAttributes.measurement_stream).alias('stream')) \
                    .join(ParsingRulesVw, \
                          on=(ParsingRulesVw.parsing_rules == MeasurementStreams.equipment_field).alias('rules')) \
                    .join(EquipmentLu, on=(EquipmentLu.equipment == ParsingRulesVw.equipment).alias('equipment')) \
                    .where(
                    OperationAttributes.operation == op_id,
                    OperationAttributes.reporting_rules == rule_id,
                    OperationAttributes.is_best_value
                )

                if op_att:
                    record = op_att.first()
                    logging.info(f"\t\tmean value = {record.attribute_numeric}")

                    # Load the mean value from the database
                    try:
                        value = float(record.attribute_numeric)
                    except Exception as ex:
                        value = None
                    self.meansLoaded.emit(item['meanType'], value)

                    # If the time series of the measurement stream used to calculate the mean value is
                    # different than the default mean time series, then update the model
                    equipment_model = record.stream.rules.equipment.model
                    line_starting = record.stream.rules.line_starting
                    if record.stream.rules.logger_or_serial == "serial":
                        new_time_series = f"{item['basis']} {item['type']} ({equipment_model}) ({line_starting})"
                    else:
                        new_time_series = f"{item['basis']} {item['type']} ({equipment_model})"

                    if item["timeSeries"] != new_time_series:
                        logging.info(f"\t\tchanging mean time series, old = {item['timeSeries']}  >>>  "
                                     f"new ts = {new_time_series}")
                        self.meansSeriesChanged.emit(item['meanType'], new_time_series)

            except Exception as ex:
                logging.error(f"Error getting the operation attributes: {item['basis']}, {item['type']} > {ex}")

        # Draw the means
        self.draw_means()

    def draw_means(self):
        """
        Method to draw the mean lines on the appropriate time series graphs and on the map display
        :return:
        """

        # Remove all existing mean lines
        # lines = [x.lines for x in self.axes]
        # lines = [item for sublist in lines for item in sublist]
        # mean_lines = [x for x in lines if "mean" in x.get_label()]
        # logging.info(f"existing mean lines count: {len(mean_lines)}")
        # logging.info(f"mean lines: {[x.get_label() for x in mean_lines]}")

        for ax in self.axes:
            to_remove = []
            for i, line in enumerate(ax.lines):
                if "mean" in line.get_label():
                    to_remove.append(i)
            to_remove = sorted(to_remove, reverse=True)
            for x in to_remove:
                l = ax.lines.pop(x)
                del l

        gear_lat = None
        gear_lon = None
        for item in self.meansModel.items:
            mean_type = item["meanType"]
            mean = item["mean"]
            try:
                if mean:
                    mean = float(mean)
                else:
                    continue

                if mean_type == "Latitude":
                    gear_lat = mean
                elif mean_type == "Longitude":
                    gear_lon = mean
                else:

                    time_series_list = [x for x in self._time_series_data if x["legend_name"] == item["timeSeries"]]
                    if len(time_series_list) == 1:
                        time_series = time_series_list[0]
                        if time_series["graph_type"] in self._to_graphs.keys():
                            axes_index = list(self._to_graphs.keys()).index(time_series["graph_type"])
                            ax = self.figure.axes[axes_index]
                            line = ax.axhline(y=mean, linewidth=3, color="black", linestyle="dashdot", visible=self.showMeans,
                                              label=f"{mean_type} mean")
                            # logging.info(f"ax: {ax} > line: {line} > mean: {mean} > showMeans: {self.showMeans}")

            except Exception as ex:
                logging.error(f"Error converting the mean to a float when plotting {mean_type}: {ex}")

        self.qml_item.draw_idle()

        logging.info(f"Plotting means, gear_lat: {gear_lat}, gear_lon: {gear_lon}")

        # Draw the median gear latitude/longitude on the map display
        if gear_lat and gear_lon:
            self._mpl_map.plot_median_point(latitude=gear_lat, longitude=gear_lon)

    @pyqtProperty(FramListModel, notify=meansModelChanged)
    def meansModel(self):
        """
        Method to return the self._means_model used for populataing the Means Table
        :return:
        """
        return self._means_model

    @pyqtProperty(bool, notify=showMeansChanged)
    def showMeans(self):
        """
        Method to return the self._show_means variable, used to control if we're showing the mean lines/points
        in the graph and map displays
        :return:
        """
        return self._show_means

    @showMeans.setter
    def showMeans(self, value):
        """
        Method to set the self._show_means variable
        :param value:
        :return:
        """
        if not isinstance(value, bool):
            return

        self._show_means = value

        lines = [x.lines for x in self.axes]
        lines = [item for sublist in lines for item in sublist]
        mean_lines = [x for x in lines if "mean" in x.get_label()]
        for line in mean_lines:
            line.set_visible(self._show_means)
        self.qml_item.draw_idle()

        self._mpl_map.toggle_median_point(value=value)

        self.showMeansChanged.emit()

    @pyqtProperty(str, notify=activeTimeSeriesChanged)
    def activeTimeSeries(self):
        """
        Method to return the self._active_time_series
        :return:
        """
        return self._active_time_series

    @activeTimeSeries.setter
    def activeTimeSeries(self, value):
        """
        Method to set the self._active_time_series
        :param value:
        :return:
        """
        if not isinstance(value, str) and value is not None:
            return

        self._active_time_series = value

        time_series = [x for x in self._time_series_data if x["legend_name"] == self._active_time_series]
        if len(time_series) == 1:
            ts_dict = time_series[0]
            self._active_equipment = ts_dict["equipment"]

        self.activeTimeSeriesChanged.emit()

    def _mpl_map_invalid_data_found(self, legend_name, invalid_ids):
        """
        Method to catch the signal from mplMap signal that is emitted when new invalid_ids are found when a user
        swipes on the map to identify invalid data points
        :param legend_name: str - legend name of the time series to update
        :param invalid_ids: list - contains all of the operation_measurement IDs to update to be invalid
        :return:
        """
        logging.info(f"\tupdating points in TimeSeries: {legend_name} >>> {invalid_ids}")

        indexes = [i for i, x in enumerate(self._time_series_data) if x["legend_name"] == legend_name]
        if len(indexes) == 1:
            idx = indexes[0]

            # Update the self._time_series_data dataframe
            mask = (self._time_series_data[idx]["points"]["id"].isin(invalid_ids))
            self._time_series_data[idx]["points"].loc[mask, "invalid"] = True
            df = self._time_series_data[idx]["points"]
            logging.info(f"just set to True back in TimeSeries: {legend_name}, count: {len(df.loc[df['invalid']])}")

            # Update the drawing of the time series as well, i.e. move points from valid -> invalid and invalid -> valid
            self._draw_time_series_graph(idx=idx)

    def _update_time_series(self, time_series, df, valid_ids, invalid_ids):
        """
        Method to update the given time series.  This catches a signal emitted by the self._data_points_model
        which deals with setting points as valid or invalid.  This method will then update a series of items
        to reflect these changes:

        Graph
        Map
        TimeSeries dictionary

        :param time_series:
        :param df:
        :param valid_ids: list - contains the time series IDs that were changed from invalid to valid
        :param invalid_ids: list - contains the time series IDs that were changed from valid to invalid
        :return:
        """
        logging.info(f"\n")
        logging.info(f"Ready to update the time series: {time_series}")

        idx_list = [i for i, x in enumerate(self._time_series_data) if x["legend_name"] == time_series]
        if len(idx_list) == 1:
            idx = idx_list[0]

            # Update the time series dataframe record
            df = df.rename(columns={"datetime": "times", "reading_numeric": "values", "status": "invalid"})
            df["times"] = df["times"].apply(lambda x: arrow.get(x).datetime)
            df.drop("change", inplace=True, axis=1)
            self._time_series_data[idx]["points"] = df

            # Update the time series graph (i.e. split out the valid v. invalid points)
            if "Latitude" not in time_series and "Longitude" not in time_series:
                self._draw_time_series_graph(idx=idx)

            # Update the map (i.e. split out the valid v. invalid points)
            if "Latitude" in time_series or "Longitude" in time_series or \
                "Horizontal Range to Target" in time_series or "Bearing to Target" in time_series:
                start_haul = self._waypoints.loc["Start Haul", "best_datetime"]
                end_of_haul = self._waypoints.loc["End Of Haul", "best_datetime"]
                self._mpl_map._redraw_track_line(time_series=time_series, valid_ids=valid_ids, invalid_ids=invalid_ids,
                                                 start_haul=start_haul, end_of_haul=end_of_haul)

    @pyqtSlot(str)
    def populate_data_points_model(self, time_series):
        """
        Method to populate the dataPointsModel with the provided time_series.
        :param time_series: str - representing the time series legend
        :return:
        """
        ts = [x for x in self._time_series_data if x["legend_name"] == time_series]
        if len(ts) == 1:
            df = ts[0]["points"]
            self._data_points_model.populate_model(time_series=time_series, df_time_series=df)

    @pyqtProperty(FramListModel, notify=dataPointsModelChanged)
    def dataPointsModel(self):
        """
        Method to return the self._invalid_data_model which is used by the
        InvalidDataDialog.qml for adjusting whether points are valid or invalid
        :return:
        """
        return self._data_points_model

    @pyqtProperty(FramListModel, notify=timeSeriesModelChanged)
    def timeSeriesModel(self):
        """
        Method to return the self._time_series_model used by the itmInvalidData section to select which time series
        data to modify as valid or invalid
        :return:
        """
        return self._time_series_model

    @pyqtProperty(bool, notify=showLegendsChanged)
    def showLegends(self):
        """
        Method to return the self._show_legends variable
        :return:
        """
        return self._show_legends

    @showLegends.setter
    def showLegends(self, value):
        """
        Method to set the self._show_legends variable
        :param value:
        :return:
        """
        if not isinstance(value, bool):
            return

        self._show_legends = value
        self.showLegendsChanged.emit()

    @pyqtProperty(QObject, notify=mplMapChanged)
    def mplMap(self):
        """
        Method to return a handle to the matplotlib map for use with drawing tracklines.  For use by QML
        :return:
        """
        return self._mpl_map

    @pyqtSlot(int, str)
    def calculateDistanceFished(self, span, depth):

        logging.info(f"span = {span}, depth = {depth}")

        self.clearDistancesFished.emit()

        if self._mpl_map:

            # Update the waypoints if the Doors Fully Out is later than the Begin Tow waypoint
            # doors_fully_out = arrow.get(self._waypoints.loc["Doors Fully Out", "best_datetime"]).isoformat() \
            #     if self._waypoints.loc["Doors Fully Out", "best_datetime"] is not None and \
            #        self._waypoints.loc["Doors Fully Out", "best_datetime"] is not pd.NaT else \
            #     arrow.get(self._waypoints.loc["Doors Fully Out", "datetime"]).isoformat()
            # begin_tow = arrow.get(self._waypoints.loc["Begin Tow", "best_datetime"]).isoformat() \
            #     if self._waypoints.loc["Begin Tow", "best_datetime"] is not None and \
            #        self._waypoints.loc["Begin Tow", "best_datetime"] is not pd.NaT else \
            #     arrow.get(self._waypoints.loc["Begin Tow", "datetime"]).isoformat()
            #
            # if doors_fully_out > begin_tow:
            #     self._update_event_datetime(event="Doors Fully Out", date_time=begin_tow)

            depth_items = [x["legend_name"] for x in self._time_series_data if x["graph_type"] == "Depth"]
            logging.info(f"depth time series: {depth_items}")

            depth_time_series = [x for x in self._time_series_data if x["graph_type"] == "Depth" and \
                          depth in x["legend_name"]]
            logging.info(f"matching depth item found: {depth_time_series[0]['legend_name']}")
            depth_data = None
            if len(depth_time_series) >= 1:
                depth_data = depth_time_series[0]["points"]
                offset = depth_time_series[0]["offset"]
                if offset != 0 and isinstance(depth_data, pd.DataFrame) and not depth_data.empty:
                    depth_data.loc[:, "times"] = depth_data.loc[:, "times"].apply(lambda x: arrow.get(x).shift(seconds=offset).datetime)

                logging.info(f"size of depth data: {len(depth_data)}")
                logging.info(f"depth data offset: {offset}")
                path = r"C:\Users\Todd.Hay\Desktop\depth.csv"
                # depth_data.to_csv(path)
                # logging.info(f"{depth_data.loc[1720:1750]}")

            headrope_height_time_series = [x for x in self._time_series_data if x["reading_type"] == "Headrope Height" and \
                          x["reading_basis"] == "Headrope"]
            headrope_data = None
            if len(headrope_height_time_series) == 1:
                headrope_data = headrope_height_time_series[0]["points"]

            logging.info(f"Calling MplMap distance fished calculations")
            self._mpl_map.calculate_all_distances_fished(span=span, df_depth=depth_data, df_headrope=headrope_data)

    @pyqtSlot(str, bool)
    def toggleTracklineVisiblity(self, trackline, visibility):
        if self._mpl_map:
            self._mpl_map.toggle_trackline_visibility(trackline=trackline, visibility=visibility)

    @pyqtProperty(bool, notify=bcsPExistsChanged)
    def bcsPExists(self):
        """
        Method to return the self._bcs_p_exists variable use in the AddWaypoints actions section
        :return:
        """
        return self._bcs_p_exists

    @bcsPExists.setter
    def bcsPExists(self, value):
        """
        Method to set the self._bcs_p_exists variable used in the AddWaypoints actions section
        :param value:
        :return:
        """
        if not isinstance(value, bool):
            logging.error("Error setting the existance value of the BCS-P signal")
            return

        self._bcs_p_exists = value
        self.bcsPExistsChanged.emit()

    @pyqtProperty(bool, notify=bcsSExistsChanged)
    def bcsSExists(self):
        """
        Method to return the self._bcs_s_exists variable use in the AddWaypoints actions section
        :return:
        """
        return self._bcs_s_exists

    @bcsSExists.setter
    def bcsSExists(self, value):
        """
        Method to set the self._bcs_s_exists variable used in the AddWaypoints actions section
        :param value:
        :return:
        """
        if not isinstance(value, bool):
            logging.error("Error setting the existance value of the BCS-S signal")
            return

        self._bcs_s_exists = value
        self.bcsSExistsChanged.emit()

    @pyqtProperty(bool, notify=bcsCExistsChanged)
    def bcsCExists(self):
        """
        Method to return the self._bcs_c_exists variable use in the AddWaypoints actions section
        :return:
        """
        return self._bcs_c_exists

    @bcsCExists.setter
    def bcsCExists(self, value):
        """
        Method to set the self._bcs_c_exists variable used in the AddWaypoints actions section
        :param value:
        :return:
        """
        if not isinstance(value, bool):
            logging.error("Error setting the existance value of the BCS-C signal")
            return

        self._bcs_c_exists = value
        self.bcsCExistsChanged.emit()

    @pyqtProperty(FramListModel, notify=availableImpactFactorsModelChanged)
    def availableImpactFactorsModel(self):
        """
        Method to return the self._available_impact_factors model for use by the AdjustPerformanceDialog.qml
        :return:
        """
        return self._available_impact_factors_model

    @pyqtProperty(FramListModel, notify=selectedImpactFactorsModelChanged)
    def selectedImpactFactorsModel(self):
        """
        Method to return the self._selected_impact_factors
        :return:
        """
        return self._selected_impact_factors_model

    @pyqtProperty(QVariant, notify=haulsModelChanged)
    def haulsModel(self):
        """
        Methohd to return the _hauls_model that is used to populate the hauls pulldown
        :return:
        """
        return self._hauls_model

    @pyqtProperty(str, notify=activeWaypointTypeChanged)
    def activeWaypointType(self):
        """
        Method to set the self._active_waypoint
        :return:
        """
        return self._active_waypoint_type

    @activeWaypointType.setter
    def activeWaypointType(self, value):
        """
        Method to set the value of the self._active_waypoint, used for manually adjusting some of the waypoints
        :param value:
        :return:
        """
        if value not in ["Begin Tow", "Net Off Bottom", "Doors At Surface", None]:
            logging.error(f"An invalid waypoint was choosen for manually adjusting: {value}")
            return

        self._active_waypoint_type = value
        self.activeWaypointTypeChanged.emit()

    @pyqtProperty(str, notify=timeMeasuredChanged)
    def timeMeasured(self):
        """
        Method to return the self._time_measured variable
        :return:
        """
        return self._time_measured

    @timeMeasured.setter
    def timeMeasured(self, value):
        """
        Method to set the self._time_measured variable
        :param value:
        :return:
        """
        self._time_measured = value
        self.timeMeasuredChanged.emit()

    def _update_event_datetime(self, event, date_time):
        """
        Method called during the toolMode = addWaypoint action when a user is manually adjusting waypoints.  This
        takes in the event type and the new data_just and adjusts the appropriate record in the EVENTS table, in the
        best_event_datetime column
        :param event: str - representing the event type, e.g. Begin Tow, Net Off Bottom, etc.
        :param date_time: Datetime as a string
        :return: None
        """
        if event not in [None, "Begin Tow", "Net Off Bottom", "Doors At Surface", "Doors Fully Out"]:
            logging.error(f"Error updating the event datetime information, event type not recognized: {event}")
            return

        try:

            # Get the event type and op_id
            event_type_lu_id = GroupMemberVw.get(
                GroupMemberVw.lookup_type_grp == 'Event',
                GroupMemberVw.group_name == 'Bottom Trawl Waypoint',
                GroupMemberVw.lookup_value_member == event).lookup_id_member
            op_id = OperationsFlattenedVw.get(OperationsFlattenedVw.tow_name == self._app.settings.haul).operation

            # Get the best event datetime
            if date_time is None:
                best_event_datetime = Events.get(Events.operation == op_id,
                                                 Events.event_type_lu == event_type_lu_id).event_datetime
            else:
                best_event_datetime = arrow.get(date_time).to('US/Pacific').isoformat()

            # Update the self._waypoints so this update is reflected for the current session
            self._waypoints.loc[event, "best_datetime"] = arrow.get(best_event_datetime).datetime

        except Exception as ex:
            logging.error(f"Error updating the event date time: {ex}")

        # Update the latitude and longitude of this new waypoint, based on the new best_event_datetime
        try:
            # Round the datetime to the nearest second
            rounded_datetime = arrow.get(best_event_datetime)
            if rounded_datetime.datetime.microsecond >= 500000:
                rounded_datetime = rounded_datetime.shift(seconds=+1).replace(microsecond=0).datetime
            else:
                rounded_datetime = rounded_datetime.floor('second').datetime
            logging.info(f"datetime rounding, before = {best_event_datetime}, after = {rounded_datetime}")

        except Exception as ex:
            logging.error(f"Error calculating the rounded datetime: {ex}")

        # Find the vessel times to the nearest 1s
        df_vessel = self._mpl_map.track_lines["vessel"]["dataframe"].copy(deep=True)
        df_vessel["times"] = df_vessel["times"].dt.round('1s')
        logging.info(f"df_vessel:\n{df_vessel.loc[0:5, 'times']}")

        # Find points in the vessel track that match those of the waypooint
        exact_lat_lon = False
        best_event_latitude = best_event_longitude = None

        # Exact point found, use it
        df_waypoints = df_vessel.loc[df_vessel["times"].isin([rounded_datetime])]
        if len(df_waypoints) >= 1:
            best_event_latitude = df_waypoints.iloc[0]["latitude"]
            best_event_longitude = df_waypoints.iloc[0]["longitude"]
            exact_lat_lon = True

        # Exact point not found, need to interpolate for it
        else:
            idx = df_vessel["times"].searchsorted(rounded_datetime)
            # WS - throws ValueError Timezones don't match https://github.com/pandas-dev/pandas/blob/master/pandas/core/arrays/datetimes.py#L576
            if idx:
                best_event_latitude = df_vessel["latitude"].iloc[idx[0]-1]
                best_event_longitude = df_vessel["longitude"].iloc[idx[0]-1]
            else:
                if idx == 0:
                    best_event_latitude = df_vessel["latitude"].iloc[0]
                    best_event_longitude = df_vessel["longitude"].iloc[0]

        logging.info(f"best coords = {best_event_latitude}, {best_event_longitude}, exact coord = {exact_lat_lon}")

        self._waypoints.loc[event, "best_latitude"] = decimal.Decimal(f"{best_event_latitude:.14f}")
        self._waypoints.loc[event, "best_longitude"] = decimal.Decimal(f"{best_event_longitude:.14f}")

        # Update the events table in the database
        try:
            Events.update(best_event_datetime=best_event_datetime,
                          best_event_latitude=best_event_latitude,
                          best_event_longitude=best_event_longitude) \
                .where(Events.event_type_lu == event_type_lu_id,
                       Events.operation == op_id).execute()
        except Exception as ex:
            logging.error(f"Error updating the database with the new datetime, latitude, or longitude: {ex}")

        # Update the vessel waypoints plotting as well
        self._mpl_map.plot_waypoints(waypoints=self._waypoints)

        logging.info(f"updated waypoint datetime:  {event} >>> {best_event_datetime}")

    def _toggle_points_validity(self, data, status):
        """
        Method that sets the provided points as either valid or invalid.  This sets the flag in
        operation_measurements called is_not_valid.  Note that when retrieving a haul and plotting it,
        I should check to determine if the show invalid data button is pressed to determine whether or
        not to plot the invalid data points
        :param data: List of operation_measurements IDs
        :param status: bool - True/False indicating if the points should be marked as invalid or not
        :return:
        """
        if data is None or not isinstance(status, bool):
            return

        try:
            OperationMeasurements.update(is_not_valid=status).where(OperationMeasurements.operation_measurement << data).execute()
            self._data_points_model.toggle_rows_validity(ids=data, value=True)
        except Exception as ex:
            logging.error(f"Error updating operation measurements to be invalid: {ex}")

    @pyqtSlot(str)
    def clearManualWaypoint(self, waypoint):
        """
        Method to remove the provided manual waypoint
        :param waypoint:
        :return:
        """
        if waypoint not in ["Begin Tow", "Net Off Bottom", "Doors At Surface"]:
            logging.error(f"Invalid waypoint provided for clearing it: {waypoint}")
            self.errorEncountered.emit("Please select which waypoint you want to clear")
            return

        self._update_event_datetime(event=waypoint, date_time=None)

        for line in self._postseason_waypoints[waypoint]:
            line.remove()
        self.qml_item.draw_idle()
        del self._postseason_waypoints[waypoint][:]
        self._active_waypoint_type = None
        self.mouseReleased.emit()

    def _calculate_total_time(self):
        """
        Method to calculate the total time of all of the segments
        :return:
        """
        if not self._time_segments:
            return

        # Sort by their starting times
        self._time_segments = sorted(self._time_segments, key=lambda x: x[0])
        is_first_rect = True
        time_total = timedelta()
        last_segment = None
        for i, segment in enumerate(self._time_segments):

            self._previous_segments = self._time_segments[:i + 1]

            # Case - First segment
            if is_first_rect:
                time_total = segment[1] - segment[0]
                is_first_rect = False
                last_segment = segment
                continue

            # Case: No Overlap
            if last_segment[1] < segment[0]:
                time_total += segment[1] - segment[0]

            # Case: Some Overlap part 1
            elif segment[0] < last_segment[1] < segment[1]:
                overlap = segment[1] - last_segment[1]
                time_total += overlap

            # Case: Some Overlap part 2 - SHOULD NEVER HAPPEN AS self._time_segments is sorted by the start times, segment[0] >= last_segment[0]
            # elif segment[0] < last_segment[0] < segment[1]:
            #     overlap = last_segment[0] - segment[0]
            #     time_total += overlap

            # Case: Complete Overlap - SHOULD NEVER HAPPEN AS self._time_segments is sorted by the start times, segment[0] >= last_segment[0]
            # elif segment[0] < last_segment[0] and segment[1] > last_segment[0]:
            #     overlap = (last_segment[0] - segment[0]) + (segment[1] - last_segment[1])
            #     time_total += overlap

            last_segment = segment

        time_total = str(timedelta(seconds=time_total.seconds))
        # logging.info(f"total_time: {time_total}")
        self.timeMeasured = time_total

    @pyqtSlot()
    def clearTimeMeasurement(self):
        """
        Method called from QML Clear button to clear out the existing time measurement spans
        :return:
        """
        for ax in self.axes:
            del ax.patches[:]
            del self._time_segments[:]
            self.timeMeasured = ""
        self.qml_item.draw_idle()

    @pyqtProperty(bool, notify=showInvalidsChanged)
    def showInvalids(self):
        """
        Method to return the self._show_invalids property
        :return:
        """
        return self._show_invalids

    @showInvalids.setter
    def showInvalids(self, value):
        """
        Method to set the self._show_invalids.  This determines if invalid data points are shown or not
        :param value:
        :return:
        """
        if not isinstance(value, bool):
            return

        self._show_invalids = value
        self.showInvalidsChanged.emit()

        # Toggle all of the invalid time series graph lines
        for ax in self.figure.axes:
            invalid_lines = [x for x in ax.lines if x.get_label() == "_nolegend_" and "invalid" in x.get_gid()]
            for line in invalid_lines:
                line.set_visible(value)

        # Refresh the graphs
        self.qml_item.draw_idle()

        # Toggle all of the map invalid points as well
        self.mplMap.toggle_invalids(value=value)

    @pyqtProperty(QVariant)
    def toolMode(self):
        """
        Method to return the self._tool_mode
        :return:
        """
        return self._tool_mode

    @toolMode.setter
    def toolMode(self, value):
        """
        Method to set the tool mode
        :param value:
        :return:
        """
        if not isinstance(value, str):
            return

        self._tool_mode = value
        self.mplMap._tool_mode = value
        self.toolModeChanged.emit()

    @pyqtSlot(QVariant)
    def setTime(self, value):
        # logging.info(f"{value.x()/1000}, {value.y()}")
        self._app.settings.statusBarMessage = arrow.get(value.x()/1000).to("US/Pacific").format("MM/DD HH:mm:ss")

    @pyqtProperty(bool, notify=displaySeriesChanged)
    def displaySeries(self):
        """
        Methhod to get theh self._clear_series boolean variable.  This is used by TimeSeriesScreen.qml to know whether
        or not to draw charts or not.
        :return:
        """
        return self._display_series

    @displaySeries.setter
    def displaySeries(self, value):
        """
        Method to set the self._display_series variable
        :param value:
        :return:
        """
        if not isinstance(value, bool):
            return

        self._display_series = value
        self.displaySeriesChanged.emit()

    @pyqtProperty(str, notify=haulNumberChanged)
    def haulNumber(self):
        return self._haul_number

    @haulNumber.setter
    def haulNumber(self, value):
        """
        Method to set the self._haul_number
        :param value:
        :return:
        """
        if not isinstance(value, str):
            return

        self._haul_number = value
        self.haulNumberChanged.emit()

    def _clear_haul(self):
        """
        Method called at the beginning of the load_haul method that clears out all of the existing data
        :return:
        """
        # Remove all of the time series and waypoints from the charts + from self._time_series_data dictionary
        # for k, v in self._time_series_data.items():
        #     del self._time_series_data[k][:]
        del self._time_series_data[:]
        self._postseason_waypoints = {"Begin Tow": [], "Net Off Bottom": [], "Doors At Surface": []}
        self._active_waypoint_type = None
        self.bcsPExists = False
        self.bcsSExists = False
        self.bcsCExists = False

        self._time_series_model.reset_model()

        # Clear the time series axes
        for ax in self.axes:
            ax.set_ylim(0, 1)
            del ax.lines[:]
            del ax.patches[:]
            del self._time_segments[:]
            self.timeMeasured = ""

        # Refresh the time series axes
        self.qml_item.draw_idle()

        # Clear the map
        self._mpl_map._clear_map()

    @pyqtSlot(bool)
    def toggleLegends(self, status):
        """
        Method to turnn the legends on and off
        :param status:
        :return:
        """
        if not isinstance(status, bool):
            return

        self.showLegends = status

        for ax in self.axes:
            leg = ax.get_legend()
            if leg:
                leg.set_visible(status)

        self.qml_item.draw_idle()

    @pyqtSlot(str)
    def load_haul(self, haul_number):
        """
        Method to retrieve data from the database based on the haul_number.  There are multiple components
        involved here to include:
        1. Retrieve Haul waypoints
        2. Retrieve BCS / SBE39 start/end date/times - between 1. and 2. we'll have the overall temporal extent
        3. Retrieve Time Series data

        :param haul_number:
        :return:
        """
        if not haul_number:
            return

        self.haulLoading.emit()

        self._time_series_count = 0

        self._clear_haul()

        # Check to ensure that the database connection is still open
        if self._app.settings._database.is_closed():
            msg = f"database connection is closed, please login again"
            logging.info(msg)
            self.errorEncountered.emit(msg)
            return

        self._haul_number = haul_number
        logging.info(f"####### STARTING NEW LOAD: haul_number: {haul_number}, display: {self.displaySeries}   #########")

        # 1. Stop any existing load operations, if underway.  Need to wait for this to fully stop running
        # if self._load_time_series_thread.isRunning():
        #     self.stopLoadingTimeSeries()

        # self.displaySeries = True
        # start = arrow.now()
        # while not self.displaySeries:
        #     logging.info(f'waiting...{(arrow.now()-start).total_seconds()}')
        #     time.sleep(0.1)

        # 2. Retrieve Haul Waypoints, this also gets me the start and end times of the haul

        self._mpl_map.track_lines["vessel"] = dict()

        self._load_waypoints(haul_number=haul_number)

        self._load_haul_details(haul_number=haul_number)

        self._load_comments_performance(haul_number=haul_number)

        self._load_impact_factors(haul_number=haul_number)

        self._load_time_series(haul_number=haul_number)

        self._load_gear_trackline(haul_number=haul_number)

    def _load_waypoints(self, haul_number):
        """
        Method to retrieve the waypoints for the given haul_number
        :param haul_number:
        :return:
        """
        if not haul_number:
            return

        try:
            start = arrow.now()
            events = Events.select(Events, Lookups)\
                .join(OperationsFlattenedVw, on=(OperationsFlattenedVw.operation == Events.operation))\
                .switch(Events)\
                .join(Lookups, on=(Lookups.lookup == Events.event_type_lu).alias('types'))\
                .where(OperationsFlattenedVw.operation_type == "Tow",
                       OperationsFlattenedVw.tow_name == haul_number)\
                .order_by(Events.event_datetime.asc())

            if events.count() > 0:

                buffer = 60
                self.xMin = arrow.get(events[0].event_datetime).shift(seconds=-buffer).datetime
                self.xMax = arrow.get(events[-1].event_datetime).shift(seconds=buffer).datetime

                waypoints = [{"type": x.types.value, "datetime": arrow.get(x.event_datetime).datetime,
                              "latitude": x.event_latitude, "longitude": x.event_longitude,
                              "best_datetime": arrow.get(x.best_event_datetime).datetime if x.best_event_datetime else None,
                              "best_latitude": x.best_event_latitude,
                              "best_longitude": x.best_event_longitude} for x in events]

                self._waypoints = pd.DataFrame(waypoints)
                self._waypoints = self._waypoints.set_index("type")

                logging.info(f"waypoints created, count: {len(self._waypoints)}")
                logging.info(f"waypoint times: {self._waypoints['datetime']}")
                # logging.info(f"waypoints: {self._waypoints.head(5)}")

                for idx, wp in self._waypoints.iterrows():
                    for ax in self.axes:
                        if idx == "Begin Tow":
                            width = 2
                            color = 'g'
                        elif idx == "Net Off Bottom":
                            width = 2
                            color = 'r'
                        else:
                            width = 1
                            color = 'm'
                        ax.axvline(wp["datetime"], linewidth=width, color=color)

                    self.axes[0].set_xlim(self.xMin, self.xMax)
                logging.info("waypoint vertical lines all drawn")

                #######################################
                # Draw the postseason waypoints as well
                #######################################

                # Get which postseason waypoints have been added
                postseason_waypoints = {x.types.value: x.best_event_datetime for x in events
                                    if x.event_datetime != x.best_event_datetime and
                                    x.types.value in self._postseason_waypoints}
                logging.info(f"postseason_waypoints: {postseason_waypoints}")

                # Iterate through them and actually draw them
                for k, v in postseason_waypoints.items():
                    if k == "Begin Tow":
                        width = 2
                        color = 'g'
                    elif k == "Net Off Bottom":
                        width = 2
                        color = 'r'
                    else:
                        width = 1
                        color = 'm'
                    if v:
                        for i, ax in enumerate(self.axes):
                            line = ax.axvline(v, linewidth=width, color=color, linestyle="dashed")
                            self._postseason_waypoints[k].append(line)

                logging.info('postseason waypoints drawn')

                self.qml_item.draw_idle()

                # Plot waypoints on the map as well
                self._mpl_map.plot_waypoints(waypoints=self._waypoints)
                logging.info('after mpl map plotting')
                end = arrow.now()

                msg = f"Waypoints loaded, elapsed time: {(end-start).total_seconds():.1f}s"
                logging.info(msg)
                self._app.settings.statusBarMessage = msg

        except Exception as ex:
            logging.error(f"Error retrieving waypoints, {ex}")

    def _load_haul_details(self, haul_number):
        """
        Method to load haul details
        :param haul_number:
        :return:
        """
        if not isinstance(haul_number, str):
            return

        try:
            op = Operations.get(Operations.operation_name == haul_number)
            ev_start = Events.select().where(Events.operation == op.operation).order_by(Events.event_datetime.asc()).limit(1)
            ev_end = Events.select().where(Events.operation == op.operation).order_by(Events.event_datetime.desc()).limit(1)
            fpc = f"{op.fpc.first_name} {op.fpc.last_name}" if op.fpc else "-"
            haul_start = arrow.get(ev_start.get().event_datetime)
            haul_date = haul_start.format("MM/DD/YYYY")
            haul_start = haul_start.format("HH:mm:ss")
            haul_end = arrow.get(ev_end.get().event_datetime).format("HH:mm:ss")

            self.haulDetailsRetrieved.emit(haul_date, haul_start, haul_end, fpc)

        except Exception as ex:
            logging.error(f"Unable to retrieve haul details: {ex}")

    def _load_comments_performance(self, haul_number):
        """
        Method to load the comments and tow performance information
        :param haul_number:
        :return:
        """
        if not isinstance(haul_number, str):
            return

        logging.info(f"loading comments/performance")
        try:
            comment_block = ""
            comments = Comments.select(Comments)\
                        .join(OperationsFlattenedVw, on=(OperationsFlattenedVw.operation == Comments.operation))\
                        .where(OperationsFlattenedVw.tow_name == haul_number)\
                        .order_by(Comments.date_time.desc())
            for comment in comments:
                comment_block += arrow.get(comment.date_time).format("MM/DD/YYYY HH:mm:ss") + ":  " + comment.comment + "\n\n"
        except Exception as ex:
            logging.error(f"Haul {haul_number} > Error retrieving haul comments: {ex}")

        try:
            performance_field = "-"
            minimum_time_met_field = "-"
            performance_qaqc = "-"
            minimum_time_met_qaqc = "-"
            impact_factors = ""

            # perf_rules = ["IS_SATISFACTORY", "IS_MINIMUM_TIME_MET"]
            reading_values = ["Is Tow Satisfactory", "Was Minimum Time Met"]
            op_atts = OperationAttributes.select(OperationAttributes, ReportingRules, Lookups)\
                            .join(OperationsFlattenedVw, on=(OperationsFlattenedVw.operation == OperationAttributes.operation))\
                            .switch(OperationAttributes)\
                            .join(ReportingRules, on=(ReportingRules.reporting_rule == OperationAttributes.reporting_rules).alias("rule"))\
                            .join(Lookups, on=(Lookups.lookup == ReportingRules.reading_type_lu).alias("lookup"))\
                            .where(OperationsFlattenedVw.tow_name == haul_number,
                                   Lookups.type == "Reading Type",
                                   Lookups.value << reading_values)
                                   # Lookups.subvalue == "Manual Entry")

            for op_att in op_atts:
                if op_att.rule.lookup.value == "Is Tow Satisfactory":
                    if op_att.rule.rule_type == "atsea":
                        performance_field = "Satisfactory" if op_att.attribute_alpha.lower() == "y" else "Unsatisfactory"
                    else:
                        performance_qaqc = "Satisfactory" if op_att.attribute_alpha.lower() == "y" else "Unsatisfactory"
                elif op_att.rule.lookup.value == "Was Minimum Time Met":
                    if op_att.rule.rule_type == "atsea":
                        minimum_time_met_field = "Yes" if op_att.attribute_alpha.lower() == "y" else "No"
                    else:
                        minimum_time_met_qaqc = "Yes" if op_att.attribute_alpha.lower() == "y" else "No"

        except Exception as ex:
            logging.error(f"Haul {haul_number} > Error retrieving haul performance details: {ex}")

        logging.info(f"{performance_qaqc}, {performance_field}")

        self.commentsPerformanceRetrieved.emit(comment_block, performance_field, minimum_time_met_field,
                                               performance_qaqc, minimum_time_met_qaqc)

    def _load_impact_factors(self, haul_number):
        """
        Method to load the impact factors for the given haul
        :param haul_number:
        :return:
        """
        try:
            impact_factors = ""
            perf_details = PerformanceDetails.select() \
                .join(OperationsFlattenedVw, on=(OperationsFlattenedVw.operation == PerformanceDetails.operation)) \
                .where(OperationsFlattenedVw.tow_name == haul_number) \
                .order_by(PerformanceDetails.is_postseason.asc())
            for perf_detail in perf_details:
                impact_factors += perf_detail.performance_type_lu.subvalue + " (field)\n" \
                    if not perf_detail.is_postseason else \
                    perf_detail.performance_type_lu.subvalue + " (postseason)\n"

            self.impactFactorsRetrieved.emit(impact_factors)

        except Exception as ex:

            logging.error(f"Error loading the impact factors: {ex}")

    def _load_gear_trackline(self, haul_number):
        """
        Method to load a previously saved gear trackline for the given haul number.  This will plot it to the map
        well as indicate in the tvDistanceFished TableView that it has been saved
        :param haul_number:
        :return:
        """
        technique = None
        distance_M = None
        distance_pre_M = None
        distance_post_M = None
        distance_N = None
        speed = None

        try:
            op_track_line_pts = OperationTracklines.select()\
                                .join(OperationsFlattenedVw, on=(OperationsFlattenedVw.operation==OperationTracklines.operation))\
                                .where(OperationsFlattenedVw.tow_name == haul_number)\
                                .order_by(OperationTracklines.date_time.asc())

            # Get the technique used to generate the track line
            if op_track_line_pts.count() > 0:
                first_rec = op_track_line_pts[0]
                DerivationType = Lookups.alias()
                der_type = DerivationType.select()\
                                .join(ReportingRules, on=(ReportingRules.derivation_type_lu == DerivationType.lookup))\
                                .where(ReportingRules.reporting_rule == first_rec.reporting_rule).first()

                # Update the tvDistanceFished TableView that a gear trackline has been saved
                value = der_type.value.lower()
                subvalue = der_type.subvalue.lower()
                technique = None
                if "catenary" in value and "catenary" in subvalue:
                    technique = "Catenary"
                elif "smoothed iigll gear track" in value and "smoothed iigll gear track" in subvalue:
                    technique = "ITI $IIGLL"
                elif "smoothed vessel gear track" in value and "trig method" in subvalue:
                    technique = "Vessel + Trig"
                elif "smoothed gps/range/bearing generated track" in value and \
                    "smoothed gps/range/bearing generated track" in subvalue:
                    technique = "ITI R/B"
                elif "smoothed gps/range/bearing generated track" in value and "trig method" in subvalue:
                    technique = "ITI R/B + Trig"
                elif "vessel gcd" in value and "trig method" in subvalue:
                    technique = "GCD + Trig"

                gear_name = f"Gear {technique}"

                logging.info(f"gear tech = {gear_name}")

                # Get the distance and pre haulback speed of the trackline

                # Retrieve the Distance Fished
                dist_reading_type_id = Lookups.get(Lookups.type == "Reading Type",
                                                   Lookups.value == "Fished Distance").lookup
                dist_reading_basis_id = Lookups.get(Lookups.type == "Reading Basis",
                                                    Lookups.value == "net touchdown to liftoff").lookup
                rule_id = ReportingRules.get(ReportingRules.reading_type_lu == dist_reading_type_id,
                                             ReportingRules.reading_basis_lu == dist_reading_basis_id,
                                             ReportingRules.derivation_type_lu == der_type.lookup,
                                             ReportingRules.rule_type == "postseason",
                                             ReportingRules.is_numeric).reporting_rule

                op_att = OperationAttributes.select()\
                    .join(OperationsFlattenedVw, on=(OperationsFlattenedVw.operation == OperationAttributes.operation))\
                    .where(OperationsFlattenedVw.tow_name == haul_number,
                           OperationAttributes.reporting_rules == rule_id,
                           OperationAttributes.is_best_value)

                if op_att.count() > 0:
                    distance_M = float(op_att.first().attribute_numeric)
                    distance_N = distance_M * N_PER_M

                    # Get the begin_tow and net_off_bottom times // self._waypoints["Be
                    start_haul = self._waypoints.loc["Start Haul", "best_datetime"] if \
                        self._waypoints.loc["Start Haul", "best_datetime"] is not None and \
                        self._waypoints.loc["Start Haul", "best_datetime"] is not pd.NaT else \
                        self._waypoints.loc["Start Haul", "datetime"]
                    begin_tow = self._waypoints.loc["Begin Tow", "best_datetime"] if \
                        self._waypoints.loc["Begin Tow", "best_datetime"] is not None and \
                        self._waypoints.loc["Begin Tow", "best_datetime"] is not pd.NaT else \
                        self._waypoints.loc["Begin Tow", "datetime"]
                    start_haulback = self._waypoints.loc["Start Haulback", "best_datetime"] if \
                        self._waypoints.loc["Start Haulback", "best_datetime"] is not None and \
                        self._waypoints.loc["Start Haulback", "best_datetime"] is not pd.NaT else \
                        self._waypoints.loc["Start Haulback", "datetime"]
                    net_off_bottom = self._waypoints.loc["Net Off Bottom", "best_datetime"] if \
                        self._waypoints.loc["Net Off Bottom", "best_datetime"] is not None and \
                        self._waypoints.loc["Net Off Bottom", "best_datetime"] is not pd.NaT else \
                        self._waypoints.loc["Net Off Bottom", "datetime"]
                    end_of_haul = self._waypoints.loc["End Of Haul", "best_datetime"] if \
                        self._waypoints.loc["End Of Haul", "best_datetime"] is not None and \
                        self._waypoints.loc["End Of Haul", "best_datetime"] is not pd.NaT else \
                        self._waypoints.loc["End Of Haul", "datetime"]

                    pts = [x for x in op_track_line_pts if begin_tow <= x.date_time <= net_off_bottom]
                    time_diff = (arrow.get(pts[-1].date_time) - arrow.get(pts[0].date_time)).total_seconds() / 3600
                    if time_diff > 0:
                        speed = distance_N / time_diff

                # Plot the MPL gear line
                # df_gear - need gear_lat and gear_lon to plot properly
                df_dict = [{"times": x.date_time, "gear_lat": x.latitude, "gear_lon": x.longitude} for x in op_track_line_pts]
                df_gear = pd.DataFrame(df_dict)

                line = self.mplMap.plot_gear_trackline(type=gear_name, created=False,
                                                df_gear=df_gear,
                                                start_haul=start_haul,
                                                end_of_haul=end_of_haul)

                logging.info(f"technique: {technique} >>> {value}, {subvalue}")

                # Plot the gear waypoints
                gear_waypoints = dict()
                wps = {"Begin Tow": begin_tow, "Start Haulback": start_haulback,
                       "Net Off Bottom": net_off_bottom}
                for k, v in wps.items():
                    mask = df_gear["times"] == v
                    df_rec = df_gear.loc[mask]

                    point_dict = dict()
                    point_dict["type"] = k
                    point_dict["datetime"] = df_rec.loc[:, "times"]
                    point_dict["gear_lat"] = df_rec.loc[:, "gear_lat"]
                    point_dict["gear_lon"] = df_rec.loc[:, "gear_lon"]
                    gear_waypoints[k] = point_dict
                mpl_waypoints = self.mplMap.plot_gear_waypoints(label_type=gear_name, created=False, waypoints=gear_waypoints)

                # Save to self.mplMap.track_lines
                gear_dict = {"dataframe": df_gear, "distance_M": distance_M,
                             "distance_pre_M": distance_pre_M, "distance_post_M": distance_post_M,
                             "speed": speed, "waypoints": gear_waypoints,
                             "start_haul": start_haul, "end_of_haul": end_of_haul, "line": line,
                             "mpl_waypoints": mpl_waypoints}

                self.mplMap.track_lines[gear_name] = gear_dict

                self.mplMap.gearLinePlotted.emit(gear_name, False)

        except Exception as ex:
            logging.error(f"Failed to load an existing gear trackline: {ex}")

        # Emit values to update the tvDistanceFished TableView
        self.haulLoadingFinished.emit(technique, distance_N, speed)

    @pyqtSlot(str, bool, bool)
    def adjustTowPerformance(self, status, tow_performance, minimum_time_met):
        """
        Method to update the performance of the tow
        :param tow_performance:
        :param minimum_time_met:
        :return:
        """
        logging.info(f"status: {status} >>> tow_perf: {tow_performance} >>> min_time: {minimum_time_met}")

        tow_perf_changed = False
        min_time_changed = False

        if not isinstance(tow_performance, bool) or not isinstance(minimum_time_met, bool):
            logging.error(f"Tow_performance ({tow_performance}) or minimum_time_met ({minimum_time_met}) are not booleans, not modifying the tow performance")
            return

        try:

            reading_values = ["Is Tow Satisfactory", "Was Minimum Time Met"]
            op_atts_field = OperationAttributes.select(OperationAttributes, ReportingRules, Lookups)\
                            .join(OperationsFlattenedVw, on=(OperationsFlattenedVw.operation == OperationAttributes.operation))\
                            .switch(OperationAttributes)\
                            .join(ReportingRules, on=(ReportingRules.reporting_rule == OperationAttributes.reporting_rules).alias("rule"))\
                            .join(Lookups, on=(Lookups.lookup == ReportingRules.reading_type_lu).alias("lookup"))\
                            .where(OperationsFlattenedVw.tow_name == self._app.settings.haul,
                                   Lookups.type == "Reading Type",
                                   Lookups.value << reading_values,
                                   ReportingRules.rule_type == "atsea")
                                    # Lookups.subvalue == "Manual Entry",

            logging.info(f"adjustTowPerformance, op_atts_field count: {op_atts_field.count()}")

            if op_atts_field.count() > 0:

                # Iterate through the field values
                for op_att_field in op_atts_field:

                    if op_att_field.rule.lookup.value == "Is Tow Satisfactory":
                        value = "Y" if tow_performance else "N"

                    elif op_att_field.rule.lookup.value == "Was Minimum Time Met":
                        value = "Y" if minimum_time_met else "N"

                    # Get the postreason reporting_rule
                    # rule = ReportingRules.get(ReportingRules.reading_type_lu == op_att_field.rule.reading_type_lu,
                    #                           ReportingRules.rule_type == "postseason")
                    rule = ReportingRules.select(ReportingRules, Lookups)\
                            .join(Lookups, on=(Lookups.lookup == ReportingRules.reading_type_lu).alias("lookup"))\
                            .where(ReportingRules.reading_type_lu == op_att_field.rule.reading_type_lu,
                                              ReportingRules.rule_type == "postseason").first()

                    # Check if a postseason record exists for this same reading_type_lu_id
                    op_att_postseason = OperationAttributes.select()\
                        .where(OperationAttributes.operation==op_att_field.operation,
                               OperationAttributes.reporting_rules==rule.reporting_rule)

                    logging.info(f"op att postseason count: {op_att_postseason.count()}")

                    if op_att_postseason.count() == 1:
                        # A postseason record exists, see if the new value is different than the previous postseason value

                        if op_att_postseason.first().attribute_alpha != value:
                            # Values are different, so update the postseason record with the new value

                            logging.info(f'updating...{value}')
                            # Update the postseason record with this current value
                            OperationAttributes.update(attribute_alpha=value)\
                                .where(OperationAttributes.operation_attribute == op_att_postseason.first().operation_attribute).execute()

                            if rule.lookup.value == "Was Minimum Time Met":
                                min_time_changed = True
                            elif rule.lookup.value == "Is Tow Satisfactory":
                                tow_perf_changed = True

                    elif op_att_postseason.count() == 0:
                        # No postseason record, so see if new value is different than the field value, if so, insert record

                        if op_att_field.attribute_alpha != value:
                            # Insert a new postseason record

                            logging.info(f'inserting...{value}')
                            op_att_postseason, created = OperationAttributes.get_or_create(
                                operation=op_att_field.operation,
                                reporting_rules=rule.reporting_rule,
                                defaults={
                                    "is_best_value": True,
                                    "attribute_alpha": value
                                }
                            )

                            if rule.lookup.value == "Was Minimum Time Met":
                                min_time_changed = True
                            elif rule.lookup.value == "Is Tow Satisfactory":
                                tow_perf_changed = True

                           # New post season record just created, update the field record is_best_value to False
                            if op_att_field.is_best_value:
                                OperationAttributes.update(is_best_value=False) \
                                    .where(OperationAttributes.operation_attribute == op_att_field.operation_attribute).execute()

                    else:
                        # For some reason we have more than one postseason record, this is an error, report it as such
                        logging.error(f"Postseason count > 1, why: {op_att_postseaon.count()}")
                        continue

            else:
                # No field values exist, so just check if postseason records exists and insert/update postseason values as appropriate

                # Get the postreason reporting_rules
                rules = ReportingRules.select(ReportingRules, Lookups)\
                            .join(Lookups, on=(ReportingRules.reading_type_lu == Lookups.lookup).alias("lookup"))\
                            .where(ReportingRules.rule_type == "postseason",
                                   Lookups.type == "Reading Type",
                                   Lookups.value << reading_values)
                                   # Lookups.subvalue == "Manual Entry",)

                # Iterate through the rules and insert/update as needed for postseaon records
                for rule in rules:

                    # Check if a postseason record exists for this same reading_type_lu_id
                    op_att_postseason = OperationAttributes.select(OperationAttributes) \
                        .join(OperationsFlattenedVw, on=(OperationsFlattenedVw.operation == OperationAttributes.operation))\
                        .where(OperationsFlattenedVw.tow_name == self._app.settings.haul,
                               OperationAttributes.reporting_rules == rule.reporting_rule)

                    # Set the appropriate values for the rules
                    if rule.lookup.value == "Is Tow Satisfactory":
                        value = "Y" if tow_performance else "N"

                    elif rule.lookup.value == "Was Minimum Time Met":
                        value = "Y" if minimum_time_met else "N"

                    if op_att_postseason.count() == 1:
                        # A postseason record exists, see if the new value is different than the previous postseason value

                        if op_att_postseason.first().attribute_alpha != value:
                            # Values are different, so update the postseason record with the new value

                            logging.info(f'updating postseason value...{value}')
                            # Update the postseason record with this current value
                            OperationAttributes.update(attribute_alpha=value)\
                                .where(OperationAttributes.operation_attribute == op_att_postseason.first().operation_attribute).execute()

                            if rule.lookup.value == "Was Minimum Time Met":
                                min_time_changed = True
                            elif rule.lookup.value == "Is Tow Satisfactory":
                                tow_perf_changed = True

                    elif op_att_postseason.count() == 0:
                        # No postseason record, insert record

                        op_id = OperationsFlattenedVw.get(OperationsFlattenedVw.tow_name == self._app.settings.haul).operation

                        logging.info(f'inserting postseason value...{value}')
                        output, created = OperationAttributes.get_or_create(
                            operation=op_id,
                            reporting_rules=rule.reporting_rule,
                            defaults={
                                "is_best_value": True,
                                "attribute_alpha": value
                            }
                        )

                        if rule.lookup.value == "Was Minimum Time Met":
                            min_time_changed = True
                        elif rule.lookup.value == "Is Tow Satisfactory":
                            tow_perf_changed = True


                    else:
                        # For some reason we have more than one postseason record, this is an error, report it as such
                        logging.error(f"Postseason count > 1, why: {op_att_postseason.count()}")
                        continue

            status = None
            if min_time_changed and tow_perf_changed:
                status = "both"
            elif min_time_changed:
                status = "minimum_time_met"
            elif tow_perf_changed:
                status = "tow_performance"

            logging.info(f"status of changing performance: {status}")

            self.towPerformanceAdjusted.emit(status, tow_performance, minimum_time_met)


        except Exception as ex:

            logging.error(f"Error updating the tow performance: {ex}")

    @pyqtSlot()
    def adjustImpactFactors(self):
        """
        Method to add / remove items from the Tow Impact Factors
        :return:
        """

        try:
            # Iterate through all of the SelectedImpactFactorsModel and see if records exist for them or not
            factors = [x for x in self._selected_impact_factors_model.items]
            factor_ids = [x["factor_lu_id"] for x in self._selected_impact_factors_model.items]

            op_id = OperationsFlattenedVw.get(OperationsFlattenedVw.tow_name == self._app.settings.haul).operation

            perf_details = PerformanceDetails.select()\
                .where(PerformanceDetails.operation == op_id,
                       PerformanceDetails.is_postseason)

            # logging.info(f"perf details count {perf_details.count()}")
            # logging.info(f"factor_ids: {factor_ids}")

            for detail in perf_details:
                # logging.info(f"id: {detail.performance_type_lu.lookup}")
                if detail.performance_type_lu.lookup not in factor_ids:
                    # Delete the record as it is no longer considered a factor
                    PerformanceDetails.delete().where(PerformanceDetails.performance_detail == detail.performance_detail).execute()

                else:
                    # logging.info(f"removing id: {detail.performance_type_lu.lookup}")

                    # Remove the record from the factors_id, this will do nothing to the existing DB record
                    factor_ids.remove(detail.performance_type_lu.lookup)

                    # May need to update it however if the is_unsat_factor has changed, so check for a difference
                    factor = [x for x in factors if x["factor_lu_id"] == detail.performance_type_lu.lookup]
                    # logging.info(f"factor is: {factor} >>> {detail.performance_type_lu.lookup}")

                    if len(factor) == 1:
                        is_unsat_factor = factor[0]["is_unsat_factor"]
                        is_unsat_factor = True if is_unsat_factor == "Yes" else False
                        # logging.info(f"new unsat: {is_unsat_factor} >>> old unsat: {detail.is_unsat_factor}")
                        if is_unsat_factor != detail.is_unsat_factor:
                            PerformanceDetails.update(is_unsat_factor=is_unsat_factor)\
                                .where(PerformanceDetails.performance_detail == detail.performance_detail).execute()

                            # logging.info('updating the is_unsat_factor value')

            # Create the list for inserting the remaining factor_ids into the database
            template = {"performance_type_lu": None, "operation": op_id, "is_postseason": True, "is_unsat_factor": False}
            insert_list = []
            for factor_id in factor_ids:
                insert_dict = deepcopy(template)
                insert_dict["performance_type_lu"] = factor_id
                insert_list.append(insert_dict)

            # Insert new records into the database
            if insert_list:
                with self._app.settings._database.atomic():
                    PerformanceDetails.insert_many(insert_list).execute()

            self._load_impact_factors(haul_number=self._app.settings.haul)

        except Exception as ex:

            logging.error(f"Error inserting new performance details: {ex}")

    @pyqtSlot(str)
    def addComment(self, comment):
        """
        Method to add a new comment to the database when reviewing the performance
        :param comment:
        :return:
        """
        if not comment:
            return

        try:
            current_time = arrow.now()
            user = self._app.settings.username
            comment += " (" + user + ")"

            # comment_type_lu = Lookups.get(Lookups.type == "Comment",
            #                               Lookups.value == "Processing", Lookups.subvalue == "Tow").lookup
            comment_type_lu = Lookups.get(Lookups.type == "Comment",
                                          Lookups.value == "Operation", Lookups.subvalue == "Tow").lookup

            op_id = OperationsFlattenedVw.get(OperationsFlattenedVw.tow_name == self._app.settings.haul).operation
            Comments.insert(
                operation=op_id,
                comment_type_lu=comment_type_lu,
                comment=comment,
                date_time=current_time.isoformat()
            ).execute()

            comment_str = current_time.format("MM/DD/YYYY HH:mm:ss") + ": " + comment + "\n\n"
            self.commentAdded.emit(comment_str)

        except Exception as ex:

            logging.info(f"Error adding a new comment: {ex}")

    @pyqtSlot(str, result=bool)
    def seriesExists(self, series):
        """
        Method to check if the provided series actually exists or not
        :param series:
        :return:
        """
        series = [x for x in self._time_series_data if series in x["equipment"]]
        logging.info(series)

        if series:
            return True

        return False

    @pyqtSlot(str)
    def autoCalculateWaypoints(self, bcs_signal, is_test=False):
        """
        Gather data to pass to the self._calculate_multiple_change_times method for auto-calculating the
        Begin Tow and Net Off Bottom waypoints from the provided bcs_signal

        :param bcs_signal: str - enumerated - one of BCS-P, BCS-P, BCS-C
        :param is_test: bool
        :return:
        """
        if bcs_signal not in ["BCS-P", "BCS-S", "BCS-C"]:
            logging.error(f"Error auto-calculating the begin tow and net off bottom waypoints, " +
                          "BCS signal identifier is not correct: {bcs_signal}")
            return

        # Get the BCS signal data points, which is a Pandas data frame
        time_series = [ts for ts in self._time_series_data if ts["equipment"] == bcs_signal]
        if len(time_series) == 1:
            time_series = time_series[0]
            # logging.info(f"time series: {time_series} >>> {time_series['mpl_plot']}")

            # Pandas data frame
            points = time_series["points"]
            # logging.info(f"original length: {len(points)}")

            # Get the temporal boundaries within which we will auto-calculate the waypoints from the given BCS signal
            begin_tow = self._waypoints.loc["Begin Tow", "datetime"]
            net_off_bottom = self._waypoints.loc["Net Off Bottom", "datetime"]
            doors_fully_out = self._waypoints.loc["Doors Fully Out", "datetime"]

            start_time = arrow.get(doors_fully_out).shift(minutes=-2).isoformat()
            end_time = arrow.get(net_off_bottom).shift(minutes=5).isoformat()

            # Set the data frame date/time field to a pandas date-time format
            points['times'] = pd.to_datetime(points['times'])

            # Make a boolean mask for restricting the times to between the field doors_fully_out and 5 mins after
            # the field net_off_bottom waypoint
            # mask = (points['times'] >= start_time) & (points['times'] <= end_time) & (points["valid"] != True)
            mask = (points['times'] >= start_time) & (~points["invalid"])

            # Reassign to the subset dataset - now we have the working set of data with which to perform the Multiple
            # Change Times algorithm
            points = points.loc[mask]
            values = points["values"].tolist()

            # Pickling for testing
            # filename = r"C:\Users\Todd.Hay\Desktop\test.pickle"
            # points.to_pickle(filename)
            # return

            y = self._calculate_bayesian_change_point_detection(points=values)
            # results = self._calculate_multiple_change_times(points=points)

            # Get the initial best Begin Tow and Net Off Bottom times
            # maxm = argrelextrema(np.asarray(y), np.greater, order=10)

            maxm = self._get_extrema(np.asarray(y), np.greater, order=10)

            results = dict()

            try:
                results["Begin Tow"] = arrow.get(points["times"].iloc[maxm[0][0]]).datetime
                results["Net Off Bottom"] = arrow.get(points["times"].iloc[maxm[0][1]]).datetime
            except Exception as ex:
                logging.info(f"maxm: {maxm} >>> shape: {maxm[0].shape}")
                logging.error(f"Error getting auto-calculated waypoints: {ex}, likely that the Doors Fully Out is after the BCS signal change")


            # Take the second point, and walk back step_back secconds in time looking for smaller values,
            # take the first smallest value.  In a good tow, this would be the first 87 value encountered
            # step_back = 60  # Seconds
            # start_time = results["Net Off Bottom"].shift(seconds=-step_back).datetime  # Window for looking
            # end_time = results["Net Off Bottom"].datetime
            # mask = (points['times'] >= start_time) & (points['times'] <= end_time) & (points["valid"] != True)
            # ending_points = points.loc[mask]

            # Reverse the ending points & Find the first instance of the maximum value within this step_back seconds time window
            # ending_points = ending_points.iloc[::-1]
            # maxidx = ending_points["values"].idxmax()
            # results["Net Off Bottom"] = arrow.get(points["times"].loc[maxidx]).datetime

        # Empty out the self._manual_waypoints for storing the newly generated waypoints for Begin Tow and Net Off Bottom
        # Structure looks like: self._manual_waypoints = {"Begin Tow": [], "Net Off Bottom": [], "Doors At Surface": []}
        # self._manual_waypoints = {k: [] for k, v in self._manual_waypoints.items() if k in ["Begin Tow", "Net Off Bottom"]}
        # for k, v in self._manual_waypoints.items():
        #     for line in v:
        #         line.remove()
        #     self._manual_waypoints[k] = []

        # Create the actual waypoint lines and add them to self._manual_waypoints
        for k, v in results.items():
            line_exists = True if len(self._postseason_waypoints[k]) > 0 else False
            if k == "Begin Tow":
                width = 2
                color = 'g'
            elif k == "Net Off Bottom":
                width = 2
                color = 'r'
            if v:
                for i, ax in enumerate(self.axes):
                    if line_exists:
                        self._postseason_waypoints[k][i].set_xdata(v)
                    else:
                        line = ax.axvline(v, linewidth=width, color=color, linestyle="dashed")
                        self._postseason_waypoints[k].append(line)
                self._update_event_datetime(event=k, date_time=v)

        # Draw the new lines
        self.qml_item.draw_idle()

    def _get_extrema(self, data, comparator, axis=0, order=1, mode='clip'):
        """
        Method adapted from scipy to determine the extrema of a dataset.  Used here instead of importing scipy
        due to failing of importing scipy when using cxFreeze.  Here is the error that I'm tracking on jira, and once
        it is resolved, I should be able to revert to using the scipy technique:

        Scipy method:  scipy.signal.argrelextrema

        Code copied from:  https://github.com/scipy/scipy/blob/master/scipy/signal/_peak_finding.py, _boolrelextrema method

        cxFreeze jira ticket:  https://github.com/anthony-tuininga/cx_Freeze/issues/233

        :return:
        """

        if((int(order) != order) or (order < 1)):
            raise ValueError('Order must be an int >= 1')

        datalen = data.shape[axis]
        locs = np.arange(0, datalen)

        results = np.ones(data.shape, dtype=bool)
        main = data.take(locs, axis=axis, mode=mode)
        for shift in range(1, order + 1):
            plus = data.take(locs + shift, axis=axis, mode=mode)
            minus = data.take(locs - shift, axis=axis, mode=mode)
            results &= comparator(main, plus)
            results &= comparator(main, minus)
            if(~results.any()):
                break
                # return results

        # return results

        return np.where(results)

    def _calculate_bayesian_change_point_detection(self, points):

        n = len(points)
        dbar = np.mean(points)
        dsbar = np.mean(np.multiply(points, points))

        fac = dsbar - np.square(dbar)

        summ = 0
        summup = []

        for z in range(n):
            summ += points[z]
            summup.append(summ)

        y = []

        for m in range(n - 1):
            pos = m + 1
            mscale = 4 * (pos) * (n - pos)
            Q = summup[m] - (summ - summup[m])
            U = -np.square(dbar * (n - 2 * pos) + Q) / float(mscale) + fac
            y.append(-(n / float(2) - 1) * math.log(n * U / 2) - 0.5 * math.log((pos * (n - pos))))

        return y

    def _calculate_multiple_change_times(self, points):
        """
        Method to perform the actual Multiple Change Times Calculation, given a set of points in a pandas data frame

        Method to auto-calculate the begin tow and net off bottom waypoints, provided the BCS signal of choice. This method
        uses the Multiple Change Times method as described by:

        References:
        - Kay, Steven (1998) Fundamentals of Statistical Signal Processing, Volume II, Detection Theory, Prentice-Hall, pp. 449-455, 471-472
        - www.eit.lth.se/fileadmin/eit/courses/phd009/ChapterModelChangeDetection.pptx

        It assumes that you have a time series that has multiple constant values (termed DCs = direct currents, ala signal processing),
        with time jumps between them.  Each of the DCs is also embedded within White Gaussian Noise (WGN).  An actual MATLAB
        example implementing this using Dynamic Programming is shown on pp. 471-472.

        We are assuming that we have three DCs, k.e. three constant time levels engulfed in WGN, k.e. 0, ~90, 0, in other
        words when the net is descending (0), when it is on bottom (~90), and when it is ascending (0)

        :param points: pandas DataFrame with columns of values and times
        :return: results = dictionary of times for Begin Tow and Net Off Bottom waypoints
        """

        # Results Dictionary
        results = {"Begin Tow": None, "Net Off Bottom": None}

        # Size of data set (# of rows)
        N = len(points)

        # Number of DCs (constant time values), and so number of time changes is DC-1
        DC = 3

        ############################################################################################################
        # Multiple Change Times Algorithm - starts here
        ############################################################################################################

        # Initialize I
        columns = [i for i in range(DC)]
        I = pd.DataFrame(columns=columns, index=[i for i in range(N)])
        Idx = pd.DataFrame(columns=columns, index=[i for i in range(N)])

        # Find the initial means
        for n in range(N - DC):
            A = points["values"].iloc[n:N-DC].mean()
            I[0][n] = np.sum(np.square(points["values"].iloc[n:N-DC] - A))

            # logging.info(f"I.iloc[0][{n}]: {I.iloc[n,0]}")

        # logging.info(f"I: {I}")
        # logging.info(f"I.iloc[:20]: {I.iloc[:20]}")

        N = 100

        start = arrow.now()
        for k in range(DC):
            if k < DC - 1:

                # Compute for all of the intermediary stages
                for L in range(k, N - DC + k):

                    logging.info(f"k: {k}, L: {L}")

                    # Load in large number to prevent minimizing value of J to occur for value of J(0:k-1)
                    # which is not computed
                    # J = pd.DataFrame(10000 * np.ones((k, 1)))
                    # J = pd.DataFrame(index=[i for i in range(N-DC+k)])
                    # J = pd.DataFrame(10000 * np.ones((L-k,1)))
                    J = pd.DataFrame(10000 * np.ones((k, 1)))

                    # Compute least squares error for all possible change times
                    delta = None
                    for n in range(k, L):
                        delta = np.sum(np.square(points["values"].iloc[n:L] - points["values"].iloc[n:L].mean()))
                        J[n] = I.iloc[n, k] + delta
                        # logging.info(f"k: {k}, L: {L}, n: {n} >>>> delta: {delta}  >>>> mean: {points['values'].iloc[n:L].mean()}" + \
                        #              f" >>> points size: {points['values'].iloc[n:L].shape} >>>> I.iloc[{k},{n}]: {I.iloc[n,k]}")
                        # logging.info(f"J: {J.iloc[n]}")
                        # logging.info(f"k: {k}, L: {L}, n: {n}, J[{n}]: {J[n]}")

                    # Determine minimum of least squares error and change time that yields this minimum
                    I[k+1][L] = J.iloc[0:L].min()
                    if not J.empty:
                        Idx[k+1][L] = J.iloc[0:L].idxmin()
                    # logging.info(f"I[{k+1}][{L}]: {I[k+1][L]}")

            else:
                # Final stage computation
                L = N-1
                J = pd.DataFrame(10000 * np.ones((k, 1)))
                for n in range(DC, N):
                    delta = np.sum(np.square(points["values"].iloc[n:L] - points["values"].iloc[n:L].mean()))
                    J[n] = I.iloc[n, k] + delta

                # Determine minimum of least squares error and change time that yields this minimum
                Imin = J.iloc[0:N].min()
                Iminidx = J.iloc[0:N].idxmin()

        # Retrieve the times when the changes occur

        logging.info(f"{Imin}")
        # logging.info(f"I: {I.iloc[:100]}")
        # logging.info(f"Iminidx: {Iminidx}")

        end = arrow.now()
        logging.info(f"Elapsed time: {(end-start).total_seconds():.2f}")

        return results

    def _plot_track_lines(self):
        """
        Method called at the end of the self._time_series_thread_completed method that plots the tracklines of the
        data and the gear.  This passes data and gear latitude/longitude groupings to the MplMap object for plotting
        :return:
        """
        logging.info(f"PLOTTING TRACK LINES...")

        series = OrderedDict({"vessel": None, "iti $iigll": None})
        vessel_types = ["Latitude", "Longitude", "Track Made Good", "Speed Over Ground"]
        vessel_series = [x for x in self._time_series_data if x["reading_type"] in vessel_types and x["reading_basis"] == "Vessel"]
        vessel_series = sorted(vessel_series, key=lambda x: (x["priority"], x["reading_type"]))
        series["vessel"] = vessel_series

        gear_types = ["Latitude", "Longitude"]
        gear_iti_series = [x for x in self._time_series_data if x["reading_type"] in gear_types and x["reading_basis"] == "Gear"]
        gear_iti_series = sorted(gear_iti_series, key=lambda x: (x["priority"], x["reading_type"]))
        series["iti $iigll"] = gear_iti_series

        # gear_types = ["Bearing to Target", "Horizontal Range to Target"]
        # gear_rb_series = [x for x in self._time_series_data if x["reading_type"] in gear_types and x["reading_basis"] == "Gear"]
        # gear_rb_series = sorted(gear_rb_series, key=lambda x: (x["priority"], x["reading_type"]))

        # Get the start and end of the haul date/times
        start_haul_dict = self._waypoints.loc['Start Haul'].to_dict()
        start_haul = arrow.get(start_haul_dict["datetime"]).datetime

        last_waypoint_name = self._waypoints.iloc[-1:].index.values[0]

        last_waypoint_dict = self._waypoints.loc[last_waypoint_name].to_dict()
        last_waypoint = arrow.get(last_waypoint_dict["datetime"]).datetime

        if start_haul_dict["best_datetime"] is not None and start_haul_dict["best_datetime"] is not pd.NaT:
            start_haul = arrow.get(start_haul_dict["best_datetime"]).datetime
        if last_waypoint_dict["best_datetime"] is not None and last_waypoint_dict["best_datetime"] is not pd.NaT:
            last_waypoint = arrow.get(last_waypoint_dict["best_datetime"]).datetime

        logging.info(f"Start Haul={start_haul}, last waypoint: {last_waypoint_name}={last_waypoint}")

        # DataFrame:  id, times, valid, values

        # Gather the best latitude/longitude data - for the vessel + gear iti lat/lon data
        try:

            # Vessel
            data, legend_names = self.create_lat_lon_df(data_type="vessel", time_series=series["vessel"])
            source_type = "latitude_longitude"

            if isinstance(data, pd.DataFrame) and not data.empty:
                logging.info(f"Plotting vessel trackline")
                self._mpl_map.plot_track_line(type="vessel", df=data, start_haul=start_haul, end_of_haul=last_waypoint,
                                          source_type=source_type, legend_names=legend_names)

            # ITI $IIGLL
            data, legend_names = self.create_lat_lon_df(data_type="iti $iigll", time_series=series["iti $iigll"])
            source_type = "latitude_longitude"
            if isinstance(data, pd.DataFrame) and not data.empty:
                logging.info(f"Plotting ITI $IIGLL trackline")
                self._mpl_map.plot_track_line(type="iti $iigll", df=data, start_haul=start_haul, end_of_haul=last_waypoint,
                                          source_type=source_type, legend_names=legend_names)

            # ITI R/B Line - Create the dataframe and plot it
            df_rb, legend_names = self.create_rb_gear_df(df_vessel=self.df_vessel)
            source_type = "range_bearing"
            if isinstance(df_rb, pd.DataFrame) and not df_rb.empty:
                logging.info(f"Plotting ITI R/B trackline")
                self._mpl_map.plot_track_line(type="iti r/b", df=df_rb, start_haul=start_haul, end_of_haul=last_waypoint,
                                          source_type=source_type, legend_names=legend_names)

        except Exception as ex:
            logging.error(f"Error plotting the track line: {ex}")

    def create_lat_lon_df(self, data_type, time_series):
        """
        Method to create the dataframe for a latitude / longitude-based track line
        """
        try:
            # logging.info(f"time_series = {time_series}")

            source_type = "latitude_longitude"
            legend_names = dict()

            offset = 0
            data = None
            lat_found = False
            lon_found = False
            track_made_good_found = False
            speed_found = False
            for i, x in enumerate(time_series):

                offset = x["offset"]

                if data_type == "vessel" and lat_found and lon_found and track_made_good_found and speed_found:
                    break
                elif data_type == "iti $iigll" and lat_found and lon_found:
                    break

                if x["reading_type"] == "Latitude" and lat_found:
                    continue
                elif x["reading_type"] == "Longitude" and lon_found:
                    continue
                elif x["reading_type"] == "Track Made Good" and track_made_good_found:
                    continue
                elif x["reading_type"] == "Speed Over Ground" and speed_found:
                    continue

                df = x["points"]
                df["times"] = df["times"].dt.round('1s')

                if i == 0:
                    data = df.copy(deep=True)
                else:
                    data = pd.merge(data, df, on="times", how="inner")

                data = data.rename(columns={"values": x["reading_type"].lower(),
                                            "invalid": x["reading_type"].lower() + "_invalid",
                                            "id": x["reading_type"].lower() + "_id"})

                if x["reading_type"] == "Latitude":
                    legend_names["latitude_legend"] = x["legend_name"]
                    lat_found = True
                elif x["reading_type"] == "Longitude":
                    legend_names["longitude_legend"] = x["legend_name"]
                    lon_found = True
                elif x["reading_type"] == "Track Made Good":
                    track_made_good_found = True
                elif x["reading_type"] == "Speed Over Ground":
                    speed_found = True

                if data_type == "vessel":
                    self.df_vessel = data

            # Adjust the times by the current offset value.  Note that this values is in seconds
            if isinstance(data, pd.DataFrame) and not data.empty:
                data.loc[:, "times"] = data.loc[:, "times"].apply(lambda x: arrow.get(x).shift(seconds=offset).datetime)

            return data, legend_names

        except Exception as ex:
            logging.error(f"Error plotting the {data_type} track line: {ex}")

    def create_rb_gear_df(self, df_vessel):
        """
        Method to create the range/bearing dataframe that is then passed to self._mpl_map for plotting.  This is called
        at two possible times:

        (1) On initial loading of the haul
        (2) Following a temporal shifting of the time series involving the range or bearing time series, which requires
            a redraw of the iti r/b gear line

        :param df_vessel:
        :return: df_rb:  dataframe of the iti r/b gear line
        """
        # Gather the iti gear range/bearing data
        gear_types = ["Bearing to Target", "Horizontal Range to Target"]
        gear_rb_series = [x for x in self._time_series_data if x["reading_type"] in gear_types and x["reading_basis"] == "Gear"]
        gear_rb_series = sorted(gear_rb_series, key=lambda x: (x["priority"], x["reading_type"]))

        try:

            legend_names = dict()
            rb = None
            range_found = False
            bearing_found = False
            offset = 0

            df_vessel["times"] = df_vessel["times"].dt.round('1s')

            for i, x in enumerate(gear_rb_series):

                offset = x["offset"]

                logging.info(f"{x['legend_name']} offset: {offset}")

                if range_found and bearing_found:
                    break

                if range_found and x["reading_type"] == "Horizontal Range to Target":
                    continue
                elif bearing_found and x["reading_type"] == "Bearing to Target":
                    continue

                df = x["points"]
                df["times"] = df["times"].dt.round('1s')
                if i == 0:
                    rb = df.copy(deep=True)
                else:
                    rb = pd.merge(rb, df, on="times", how="inner")

                rename = "range" if x["reading_type"] == "Horizontal Range to Target" else "bearing"
                rb = rb.rename(columns={"values": rename,
                                        "invalid": rename + "_invalid",
                                        "id": rename + "_id"})

                if x["reading_type"] == "Horizontal Range to Target":
                    legend_names["range_legend"] = x["legend_name"]
                    range_found = True
                elif x["reading_type"] == "Bearing to Target":
                    legend_names["bearing_legend"] = x["legend_name"]
                    bearing_found = True

            if isinstance(rb, pd.DataFrame) and not rb.empty:

                # Adjust the times by the current offset value.  Note that this values is in seconds
                rb.loc[:, "times"] = rb.loc[:, "times"].apply(lambda x: arrow.get(x).shift(seconds=offset).datetime)
                rb["times"] = rb["times"].dt.round('1s')

                # Merge the vessel lat/lon values, based on the time
                rb = pd.merge(rb, df_vessel, on="times", how="inner")

                if not rb.empty:

                    # Calculate gear lat/lon valuesv
                    rb.loc[:, "gear_lat"] = rb.apply(lambda x: self.get_gear_lat(x["latitude"], x["longitude"], x["range"], x["bearing"]), axis=1)
                    rb.loc[:, "gear_lon"] = rb.apply(lambda x: self.get_gear_lon(x["latitude"], x["longitude"], x["range"], x["bearing"]), axis=1)

                    # Drop the existing vessel lat/lon and rename the gear lat/lon columns
                    rb = rb.drop("latitude", 1)
                    rb = rb.drop("longitude", 1)
                    rb = rb.rename(columns={"gear_lat": "latitude", "gear_lon": "longitude"})

            return rb, legend_names

        except Exception as ex:
            logging.error(f"Error plotting the gear range/bearing track line: {ex}")

    def get_gear_lat(self, lat, lon, range, bearing):
        """

        :param lat:
        :param lon:
        :param range:
        :param bearing:
        :return:
        """
        geod = Geodesic.WGS84
        g = geod.Direct(lat, lon, bearing, range)
        return g['lat2']

    def get_gear_lon(self, lat, lon, range, bearing):

        geod = Geodesic.WGS84
        g = geod.Direct(lat, lon, bearing, range)
        return g['lon2']

    def is_same_time_sec(self, time1, time2):
        a, b = math.modf((time2 - time1).total_seconds())
        return True if b == 0 else False

    def _load_time_series(self, haul_number):
        """
        Method to retrieve time series data from the database based on the haul_number
        :param haul_number:
        :return:
        """
        if not haul_number:
            return

        kwargs = {"app": self._app, "haul": haul_number}
        self._load_time_series_worker = LoadTimeSeriesThread(kwargs=kwargs)
        self._load_time_series_worker.moveToThread(self._load_time_series_thread)
        self._load_time_series_worker.timeSeriesThreadCompleted.connect(self._time_series_thread_completed)
        self._load_time_series_worker.timeSeriesLoaded.connect(self._time_series_loaded)
        self._load_time_series_worker.timeSeriesCleared.connect(self._time_series_cleared)
        self._load_time_series_thread.started.connect(self._load_time_series_worker.run)
        self._load_time_series_thread.start()

    def _time_series_thread_completed(self, haul_number, status, msg):
        """
        Method used to catch the loadingCompleted signal from the _load_data_worker background thread for
        retrieving haul information to plot in TimeSeries
        :param status:
        :param msg:
        :return:
        """
        logging.info('#################         Final signal from the background Thread       ########################')
        if self._load_time_series_thread.isRunning():
            self._load_time_series_thread.quit()

        self.displaySeries = True
        logging.info(f"haul_number: {haul_number} >>>  self._haul_number: {self._haul_number}")
        if haul_number == self._haul_number:
            self._haul_number = None
        else:
            logging.info(f"LOADING, displaySeries: {self.displaySeries}")
            self.load_haul(self._haul_number)

        logging.info(f"###### display: {self.displaySeries} #########")

        # time.sleep(2)

        # Call method to plot the vessel and gear track lines
        self._plot_track_lines()

        self.timeSeriesModel.removeItem(index=0)
        self.timeSeriesModel.sort(rolename="text")
        self.timeSeriesModel.insertItem(index=0, item={"text": "Select Time Series"})

        # Load the Calculated Means - must do this once all of the time series are loaded
        self._load_means(haul_number=haul_number)

        msg = "Finished Loading Time Series"
        self._app.settings.statusBarMessage = msg
        self.timeSeriesThreadCompleted.emit(status, msg)

    @pyqtSlot()
    def stopLoadingTimeSeries(self):
        """
        Method to halt the loading of the current time series data
        :return:
        """
        if self._load_time_series_worker:
            logging.info('############################    STOPPING     ############################')
            self.displaySeries = False
            self._load_time_series_worker.stop()
            self.allTimeSeriesCleared.emit()

    def _time_series_cleared(self, reading_type):
        """
        Method to clear a graph of the given reading_type
        :param reading_type:
        :return:
        """
        self.timeSeriesCleared.emit(reading_type)

    def _draw_time_series_graph(self, idx=None, ax=None, color=None):
        """
        Method to draw the provided time_series to the appropriate time series graph
        :param idx: index of the time series in self._time_series_data to draw
        :return: None
        """

        # Retrieve the time series dictionary
        time_series_dict = self._time_series_data[idx]

        # logging.info(f"Drawing the time series: {time_series_dict['legend_name']}")

        # Axes - Get a handle to the proper axes for drawing, if one is not provided
        if ax is None:
            if time_series_dict["graph_type"] in self._to_graphs.keys():
                axes_index = list(self._to_graphs.keys()).index(time_series_dict["graph_type"])
                ax = self.figure.axes[axes_index]
            else:
                # The given graph_type is not one to be plotted, so return
                return

        # Color - Set the drawing color is one is not provided
        if color is None:
            color_dict = {"BCS-P": "r", "BCS-S": "g"}
            if time_series_dict["equipment"] in color_dict:
                color = color_dict[time_series_dict["equipment"]]
            else:
                # color = np.random.rand(3, 1)
                color = np.random.rand(3)

        # Line - Replace the existing matplotlib line with the new line
        label = time_series_dict["legend_name"]

        # Delete the existing valid line if it exists
        valid_lines = [i for i, x in enumerate(ax.lines) if x.get_label() == label]
        if len(valid_lines) == 1:
            idx = valid_lines[0]
            del ax.lines[idx]

        # Delete the existing invalid line if it exists
        # invalid_lines = [i for i, x in enumerate(ax.lines) if x.get_label() == f"{label} invalid"]
        invalid_lines = [i for i, x in enumerate(ax.lines) if x.get_label() == "_nolegend_" and \
                                                              x.get_gid() == f"{label} invalid"]
        # logging.info(f"invalid lines to delete for time series graph: {len(invalid_lines)}")
        if len(invalid_lines) == 1:
            idx = invalid_lines[0]
            del ax.lines[idx]

        df = time_series_dict["points"]
        mask = (~df["invalid"])
        df_valids = df.loc[mask].copy(deep=True)
        df_invalids = df.loc[~mask].copy(deep=True)

        # Adjust the times by the current offset value.  Note that this values is in seconds
        offset = time_series_dict["offset"]
        logging.info(f"{label} offset: {offset}")
        if offset is not None:
            df_valids.loc[:, "times"] = df_valids.loc[:, "times"].apply(lambda x: arrow.get(x).shift(seconds=offset).datetime)
            df_invalids.loc[:, "times"] = df_invalids.loc[:, "times"].apply(lambda x: arrow.get(x).shift(seconds=offset).datetime)

        # logging.info(f"df_invalids size: {len(df_invalids)}")

        # Draw the valid line
        valid_line = ax.plot(df_valids["times"], df_valids["values"], gid=df_valids["id"],
                    marker='o', markersize=3, linewidth=1, color=color, label=label)

        # Draw the invalid line, er, really just points
        # invalid_line = ax.plot(df_invalids["times"], df_invalids["values"], marker='x', color=color, markersize=5,
        #                          linewidth=0, gid=df_invalids["id"], visible=self._show_invalids, label=f"{label} invalid")
        invalid_line = ax.plot(df_invalids["times"], df_invalids["values"], marker='x', color=color, markersize=5,
                                 linewidth=0, gid=f"{label} invalid", visible=self._show_invalids, label="_nolegend_")

        # Add the newly updated line back to the time_series_data
        # self._time_series_data[idx]["mpl_plot"] = valid_line
        # self._time_series_data[idx]["invalids_plot"] = invalid_line

        # Refresh the graph axes
        self.qml_item.draw_idle()

    def _time_series_loaded(self, time_series_dict):

        """
        Method used to catch the timeSeriesLoadingCompleted signal from the haul data background thread.  This is called
        each time that an individual time series has been retrieved from the database
        :param index:
        :param load_date_time:
        :return:
        """

        # Add to the overall list for storing the time series information
        # logging.info(f"time_series_dict = {time_series_dict['legend_name']}, size = {len(time_series_dict['points'])}")

        if time_series_dict["legend_name"] in [x["legend_name"] for x in self._time_series_data]:
            logging.info(f"\t\t{time_series_dict['legend_name']} has already been loaded, skipping reloading it.")
            return

        self._time_series_data.append(time_series_dict)
        idx = len(self._time_series_data)-1

        # Add to the TimeSeriesModel used in the invalidData section
        self.timeSeriesModel.appendItem({"text": time_series_dict["legend_name"]})

        # Graph Data Found, plot
        if time_series_dict["graph_type"] in self._to_graphs:

            # If one of the BCS signals exists, set it's existence flag to true,
            # which then enables the associated button in AddWaypoint in the QML screen
            if time_series_dict["equipment"] == "BCS-P":
                self.bcsPExists = True
            elif time_series_dict["equipment"] == "BCS-S":
                self.bcsSExists = True
            elif time_series_dict["equipment"] == "BCS-C":
                self.bcsCExists = True

            axes_index = list(self._to_graphs.keys()).index(time_series_dict["graph_type"])
            ax = self.figure.axes[axes_index]
            min_value, max_value = ax.get_ylim()

            if time_series_dict["max_value"] > max_value:
                max_value = time_series_dict["max_value"]

            # Invert the BCS and Depth signals
            if time_series_dict["graph_type"] == "Depth":
                ax.set_ylim(bottom=max_value * self._ylim_max_buffer, top=0)
            elif time_series_dict["graph_type"] == "Tilt":
                ax.set_ylim(bottom=90, top=0)
            else:
                ax.set_ylim(top=max_value * self._ylim_max_buffer, bottom=0)

            color_dict = {"BCS-P": "r", "BCS-S": "g"}
            if time_series_dict["equipment"] in color_dict:
                color = color_dict[time_series_dict["equipment"]]
            else:
                # color = np.random.rand(3, 1)
                color = np.random.rand(3)

            # series = ax.plot(time_series_dict["points"]["times"], time_series_dict["points"]["values"],
            #                  gid=time_series_dict["points"]["id"],
            #                  marker='o', markersize=3, linewidth=1, color=color, label=time_series_dict["legend_name"])

            self._draw_time_series_graph(idx=idx, ax=ax, color=color)

            ax.legend(loc='upper left', facecolor='white', frameon=True, edgecolor='b')
            ax.get_legend().set_visible(self._show_legends)

            # time_series_dict["mpl_plot"] = series
            # self.qml_item.draw_idle()

        msg = f"Time Series loaded: {time_series_dict['legend_name']}, count: {len(time_series_dict['points'])}"
        self._app.settings.statusBarMessage = msg

    # @pyqtSlot(QVariant, QVariant)
    # def addPoints(self, series, points):
    #     """
    #     Method to add all of hte points to a time series in bulk.  Only QChartView technique for adding points
    #     :param series:
    #     :param points:
    #     :return:
    #     """
    #     if not isinstance(series, QLineSeries):
    #         return
    #
    #     if isinstance(points, QJSValue):
    #         points = points.toVariant()
    #
    #     points = [QPointF(x[0].toMSecsSinceEpoch(), x[1]) for x in points]
    #     series.replace(points)

    def stop_background_threads(self):

        if self._load_time_series_worker:
            self._load_time_series_worker.stop()


class LoadTimeSeriesThread(QObject):

    timeSeriesThreadCompleted = pyqtSignal(str, bool, str, arguments=["haul_number", "status", "msg"])
    timeSeriesLoaded = pyqtSignal(QVariant, arguments=["time_series_dict",])
    timeSeriesCleared = pyqtSignal(str, arguments=["reading_type",])

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self._is_running = False
        self._app = kwargs["app"]
        self._functions = CommonFunctions()
        self._haul = kwargs["haul"]

        """
        Graphs are:  Bearing, Depth, Net_Dimension, Range, Speed, Temperature, Tilt, Waypoints
        """
        self._to_graph = ["Bearing to Target", "Depth", "Headrope Height", "Horizontal Range to Target",
                         "Speed Over Ground", "Spread Distance", "Temperature", "Track Made Good", "X Tilt Angle"]

        """
        Mapping data sets:  SC50 Vessel Latitude/Longitude, ITI Latitude/Longitude, Field Waypoints, Center Waypoints
        """
        self._to_map = ["Latitude", "Longitude"] #, "Heading"]

    def stop(self):
        """
        Method to interrupt the thread, stopping it from running
        :return:
        """
        self._is_running = False

    def run(self):
        self._is_running = True
        status, msg = self._load_data()
        self.timeSeriesThreadCompleted.emit(self._haul, status, msg)

    def _load_data(self):
        """
        Method to retrieve time series data from FRAM_CENTRAL for a given haul that is defined by self._haul, in the
        __init__ section
        :return:
        """
        status = False
        msg = ""

        self._is_running = True

        # Create the time series data structure
        timeSeriesTemplate = {"graph_type": None, "series_number": None, "legend_name": None, "reading_type": None,
                              "stream_id": None, "min_value": None, "max_value": None, "points": None, "equipment": None}
        try:

            # Get the haul operation ID
            haul_op = OperationsFlattenedVw.get(OperationsFlattenedVw.tow_name == self._haul)

            if not self._is_running:
                raise BreakIt

            # Get all of the measurement streams associated with this haul ID
            start = arrow.now()
            streams = MeasurementStreams.select(MeasurementStreams, ParsingRulesVw, EquipmentLu, Lookups)\
                .join(ParsingRulesVw, on=(ParsingRulesVw.parsing_rules == MeasurementStreams.equipment_field).alias('rules'))\
                .join(EquipmentLu, on=(EquipmentLu.equipment == ParsingRulesVw.equipment).alias('equipment'))\
                .join(Lookups, on=(EquipmentLu.organization_type_lu == Lookups.lookup).alias('org'))\
                .where(MeasurementStreams.operation == haul_op.operation,
                       ParsingRulesVw.reading_type << self._to_graph + self._to_map)
                    # ParsingRulesVw.graph_type.is_null(False),

            logging.info(f'Time Series streams count {streams.count()}')


            if not self._is_running:
                raise BreakIt

            # Get all of the measurement streams, grouped by reading_type
            reading_types = list(set([x.rules.reading_type for x in streams]))
            for reading_type in reading_types:
                self.timeSeriesCleared.emit(reading_type)

            logging.info(f"Time Series reading types: {reading_types}")

            # Create all of the stream attributes, used for displaying on the TimeSeries legends
            start = arrow.now()
            # stream_ids = [x.measurement_stream for x in streams]
            # logging.info(f"stream_ids = {stream_ids}")

            for stream in streams:

                if not self._is_running:
                    raise BreakIt

                timeSeriesDict = deepcopy(timeSeriesTemplate)
                timeSeriesDict["graph_type"] = stream.rules.graph_type
                timeSeriesDict["reading_type"] = stream.rules.reading_type
                timeSeriesDict["reading_basis"] = stream.rules.reading_basis
                timeSeriesDict["priority"] = stream.rules.parsing_priority
                timeSeriesDict["stream_id"] = stream.measurement_stream
                timeSeriesDict["offset"] = stream.stream_offset_seconds
                timeSeriesDict["equipment_id"] = stream.rules.equipment.equipment

                if stream.rules.logger_or_serial == "serial":
                    timeSeriesDict["legend_name"] = f"{stream.rules.reading_basis} {stream.rules.reading_type} ({stream.rules.equipment.model}) " + \
                        f"({stream.rules.line_starting})"
                    timeSeriesDict["equipment"] = stream.rules.equipment.model
                else:
                    timeSeriesDict["legend_name"] = f"{stream.rules.reading_basis} {stream.rules.reading_type} ({stream.attachment_position})"
                    timeSeriesDict["equipment"] = stream.attachment_position

                points = OperationMeasurements.select(OperationMeasurements.date_time,
                                                      OperationMeasurements.reading_numeric,
                                                      OperationMeasurements.is_not_valid,
                                                      OperationMeasurements.operation_measurement) \
                                    .where(OperationMeasurements.measurement_stream == stream.measurement_stream,
                                           OperationMeasurements.reading_numeric.is_null(False))\
                                    .order_by(OperationMeasurements.date_time.asc())

                logging.info(f"\tRetrieved data: {timeSeriesDict['legend_name']} > "
                             f"basis = {timeSeriesDict['reading_basis']}, type = {timeSeriesDict['reading_type']}, "
                             f"stream_id = {stream.measurement_stream}, {len(points)} points")

                if len(points) > 0:
                    timeSeriesDict["max_value"] = float(max([x.reading_numeric for x in points]))
                    timeSeriesDict["min_value"] = float(min([x.reading_numeric for x in points]))

                    times = [arrow.get(x.date_time).datetime for x in points]
                    values = [float(x.reading_numeric) for x in points]
                    valids = [x.is_not_valid for x in points]
                    ids = [x.operation_measurement for x in points]
                    timeSeriesDict["points"] = (pd.DataFrame({"times": times, "values": values,
                                                              "invalid": valids, "id": ids}))

                    # if "Vessel Latitude" in timeSeriesDict['legend_name']:
                    #     logging.info(f"\tVessel latitude start/end date/time: {times[0]} > {times[-1]}")
                    # if "Vessel Longitude" in timeSeriesDict['legend_name']:
                    #     logging.info(f"\tVessel longitude start/end date/time: {times[0]} > {times[-1]}")


                    # timeSeriesDict["points"] = [[arrow.get(x.date_time).datetime, float(x.reading_numeric), x.is_not_valid, x.operation_measurement]
                    #                             for x in points]     # WORKS WORKS WORKS
                    # timeSeriesDict["points"] = [[QDateTime(x.date_time), float(x.reading_numeric), x.is_not_valid, x.operation_measurement]
                    #                             for x in points]     # WORKS WORKS WORKS - QChartView
                    self.timeSeriesLoaded.emit(timeSeriesDict)

            end = arrow.now()
            logging.info(f"Finished time series background thread, elapsed time: {(end-start).total_seconds():.2f}")

        except BreakIt:
            status = False
            msg = "Time Series loading halted"
            logging.info(msg)
            return status, msg

        except Exception as ex:
            status = False
            msg = f"Error retrieving time series data: {self._haul} > {ex}"
            logging.info(msg)
            return status, msg

        end = arrow.now()
        msg = f"Time Series data retrieval completed, elapsed time {(end-start).total_seconds():.3}s"
        logging.info(msg)

        status = True
        return status, msg


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

        # appGuid = 'F3FF80BA-BA05-4277-8063-82A6DB9245A2'
        # self.app = QtSingleApplication(appGuid, sys.argv)
        # if self.app.isRunning():
        #     sys.exit(0)
        #
        # self.engine = QQmlApplicationEngine()
        # self.context = self.engine.rootContext()
        #
        # self.db = TrawlAnalyzerDB()
        # self.context.setContextProperty('db', self.db)
        #
        # self.settings = Settings(app=self)
        # self.context.setContextProperty("settings", self.settings)
        #
        # self.settings._vessel = "Excalibur"
        # self.settings._year = "2016"
        #
        # self.file_management = FileManagement(app=self, db=self.db)
        # self.context.setContextProperty("fileManagement", self.file_management)
        #
        # self.data_completeness = DataCompleteness(app=self, db=self.db)
        # self.context.setContextProperty("dataCompleteness", self.data_completeness)
        #
        # # Actually login
        # self.settings._get_credentials()
        # self.settings.login(user=self.settings.username, password=self.settings.password)

    def tearDown(self):
        pass

    def test_calculate_multiple_change_times(self):



        start = arrow.get("2016-05-21T16:44:00-07:00").datetime
        end = arrow.get("2016-05-21T17:03:00-07:00").datetime

        results = {"Begin Tow": start, "Net Off Bottom": end}

        filename = r"C:\Users\Todd.Hay\Desktop\time_series.pickle"
        points = pd.read_pickle(filename)

        ts = TimeSeries()
        # results = ts._calculate_multiple_change_times(points=points)

        r = points["values"].rolling(window=10)
        logging.info(f"{r}")

        # Plot Results
        logging.info('plotting')
        import matplotlib.pyplot as plt
        f, ax = plt.subplots()
        ax.plot(points["times"], -points["values"])
        ax.xaxis_date("US/Pacific")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S\n%m/%d/%y', tz=tzlocal()))

        for k, v in results.items():
            if v:
                color = 'g' if k == "Begin Tow" else 'r'
                ax.axvline(v, linewidth=2, color=color, linestyle="dashed")
        f.show()

        try:
            input("Please enter to continue")
        except SyntaxError:
            pass


if __name__ == '__main__':

    # unittest.main()

    start = arrow.get("2016-05-21T16:44:00-07:00").datetime
    end = arrow.get("2016-05-21T17:03:00-07:00").datetime

    results = {"Begin Tow": start, "Net Off Bottom": end}

    filename = r"C:\Users\Todd.Hay\Desktop\time_series.pickle"
    points = pd.read_pickle(filename)
    ts = TimeSeries()
    # results = ts._calculate_multiple_change_times(points=points)
    # df = pd.Series(data=points["values"], index=points["times"])
    # df["values"] = points["values"]
    # print(df)
    # r = df.rolling(window=10)

    series = points.copy(deep=True)
    series = series.drop("id", 1)
    series = series.drop("invalid", 1)
    series = series.set_index("times")
    series["values"] = -series["values"]
    r = series.rolling(window=10)
    print(series.iloc[0:5])

    # mask = (points['times'] >= start_time) & (points['times'] <= end_time) & (points["valid"] != True)
    # points = points.loc[mask]

    delta = 10
    window = 10
    change = series.pct_change(periods=window)
    mask = ((change["values"] > delta) | (change["values"] < -delta))
    print(change[mask])
    print(change[mask].index.tolist())

    mask = (points["times"] >= '2016-05-21 16:45:00-07:00') & (points["times"] <= '2016-05-21 16:45:35-07:00')
    print(points[mask])

    mask = (points["times"] >= '2016-05-21 17:03:15-07:00') & (points["times"] <= '2016-05-21 17:04:00-07:00')
    print(points[mask])


    # Plot Results
    logging.info('plotting')
    import matplotlib.pyplot as plt

    f, ax = plt.subplots()
    ax.plot(points["times"], -points["values"])
    ax.xaxis_date("US/Pacific")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S\n%m/%d/%y', tz=tzlocal()))

    for k, v in results.items():
        if v:
            color = 'g' if k == "Begin Tow" else 'r'
            ax.axvline(v, linewidth=2, color=color, linestyle="dashed")

    # print(r.mean())
    ax.plot(r.mean())

    f.show()

    input('test')
