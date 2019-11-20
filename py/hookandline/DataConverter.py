import os
import sys
import logging
import csv
import re
from dateutil import parser, tz
from datetime import datetime, timezone
import time
import math
from math import pi, radians, sin, cos, atan2, sqrt
from PyQt5.QtCore import QVariant, pyqtProperty, pyqtSlot, pyqtSignal, QObject
from playhouse.shortcuts import model_to_dict, dict_to_model

from py.common.FramListModel import FramListModel
from py.hookandline.HookandlineFpcDB_model import database, TideStations, \
    Sites, Lookups, ParsingRules


class DataConverter(QObject):

    # siteIndexChanged = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

    @pyqtSlot(str, result=str)
    def utc_to_local_time(self, utc_time):
        """
        Method to convert a UTC time into a local time.  The UTC
        time should be in the form of hhmmss.ss, i.e. a standard
        GPS UTC time.  Good reference:

        http://stackoverflow.com/questions/4770297/python-convert-utc-datetime-string-to-local-datetime

        :param sentence:
        :return:
        """
        utc_zone = tz.tzutc()
        local_zone = tz.tzlocal()

        try:
            dt = datetime.now()
            if len(utc_time) >= 6:
                h = utc_time[0:2]
                m = utc_time[2:4]
                s = utc_time[4:6]
                dt = dt.replace(hour=int(h), minute=int(m), second=int(s))
            else:
                # Just return the local time
                return dt.strftime("%H:%M:%S")

            if "." in utc_time and len(utc_time) > 7:
                ms = utc_time[7:].ljust(6, '0')
                dt = dt.replace(microsecond=int(ms))

            # logging.info('h, m, s, ms: {0}, {1}, {2}, {3}'.format(h, m, s, ms))
            # dt = datetime.strptime(utc_time, "%H%M%S.%f")

            utc = dt.replace(tzinfo=timezone.utc)
            local = utc.astimezone(tz=None)
            return local.strftime("%H:%M:%S")

        except Exception as ex:

            logging.error("Error converting utc to local time: {0} > {1}".format(utc, ex))

        return dt.strftime("%H:%M:%S")

    @pyqtSlot(str, str, result=str)
    def format_latitude(self, latitude, uom):
        """
        Method to reformat the latitude that is received by a typical
        GPS receiver.  The input form is:

        ddmm.mmm

        but the desired output is:

        dd mm.mmm
        :param latitude:
        :return:
        """
        if len(latitude) < 5 or "." not in latitude:
            return latitude

        lat_split = latitude.split(".")
        deg = lat_split[0][0:-2]
        min = lat_split[0][-2:] + "." + lat_split[1]

        return deg + u"\xb0" + " " + min + "' " + uom

        return latitude[0:2] + u"\xb0" + " " + latitude[2:len(latitude)] + "' " + uom

    @pyqtSlot(str, str, result=str)
    def format_longitude(self, longitude, uom):
        """
        Method to reformat the latitude that is received by a typical
        GPS receiver.  The input form is:
        dddmm.mmm

        but the desired output is:
        ddd mm.mmm
        :param longitude:
        :return:
        """

        if len(longitude) < 6 or "." not in longitude:
            return longitude

        lon_split = longitude.split(".")
        deg = lon_split[0][0:-2]
        min = lon_split[0][-2:] + "." + lon_split[1]

        return deg + u"\xb0" + " " + min + "' " + uom

        return longitude[0:3] + u"\xb0" + " " + longitude[3:len(longitude)] + "' " + uom

    @pyqtSlot(str, result=float)
    def lat_or_lon_to_dd(self, value_str):
        """
        Convert a latitude or longitude string in the form of:
        deg + u"\xb0" + " " + min + "' " + uom

        to decimal degrees

        :param value_str:
        :return:
        """
        if "\xb0" in value_str:
            [dd, mm] = value_str.split("\xb0")
            mm = mm.translate({ord(i): None for i in " 'nsNSewEW"})
            output = float(dd) + float(mm)/60
            if re.search("[wWsS]", value_str):
                output = -output
            return output

        try:
            value = float(value_str)
            return value
        except Exception as ex:
            logging.error(f"Error converting DDMM.MMM to DD for lat/lon")

    @pyqtSlot(str, float, result=str)
    def dd_to_formatted_lat_lon(self, type, value):
        """
        Method to convert a latitude in decimal degrees to well-formatted string
        :param type: str - enumerate value:  latitude / longitude
        :param value:
        :return:
        """
        if not isinstance(value, float):
            logging.error("Error formatting latitude to nice format: {0}".format(value))
            return str(value)

        min, deg = math.modf(value)
        min *= 60
        deg = int(deg)

        if type == "latitude":
            uom = "S" if value < 0 else "N"
        else:
            uom = "W" if value < 0 else "E"

        if uom in ["S", "W"] and deg <= 0 and min <= 0:
            deg = -deg
            min = -min

        return f"{deg:d}\xb0 {min:6.3f}' {uom}"
        # return "{:d}".format(deg) + u"\xb0" + " " + "{:06.3f}".format(min) + "' " + uom

    @pyqtSlot(str, str, result=float)
    def gps_lat_or_lon_to_dd(self, value_str, hemispshere):
        """
        Method to convert a GPS provided latitude / longitude and associated
        hemisphere value from the following format:

        DDDMM.MMMM to DDD.DDDDDD

        These values will come from the $GPRMC or $GPGLL sentences typically
        :param value_str:
        :param hemispshere:
        :return:
        """
        idx = value_str.index(".")
        dd = value_str[:idx-2]
        mm = value_str[idx-2:]
        output = float(dd) + float(mm)/60
        if hemispshere in ["w", "W", "s", "S"]:
            output = -output
        return output

    @pyqtSlot(str, result=QVariant)
    def time_to_iso_format(self, time_str):
        """
        Method to convert local time element in the format of hh:mm:ss to an ISO-formatted
        date-time string

        :param time_str:
        :return:
        """
        return parser.parse(time_str).isoformat()

    @pyqtSlot(str, result=QVariant)
    def iso_to_common_date_format(self, iso_str):
        """
        Method to convert an ISO formatted date-time object into a
        common date format of mm/dd/yyyy
        :param iso_str:
        :return:
        """
        return parser.parse(iso_str).strftime("%m/%d/%y")

if __name__ == '__main__':

    dc = DataConverter()