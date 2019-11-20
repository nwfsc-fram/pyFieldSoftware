__author__ = 'Todd.Hay'

# -------------------------------------------------------------------------------
# Name:        CommonFunctions.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     January 21, 2017
#  License:     MIT
#-------------------------------------------------------------------------------
import re, logging
from datetime import datetime
from dateutil import tz
import time
from math import modf, floor

from geographiclib.geodesic import Geodesic
# import numba

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty

from py.trawl_analyzer.TrawlAnalyzerDB_model import Lookups, Operations, OperationFiles, OperationFilesMtx, \
    VesselLu, PersonnelLu, StationInventoryLu, OperationsFlattenedVw

from py.trawl_analyzer.TrawlWheelhouseDB_model import OperationalSegment as WhOperationalSegment, PersonnelLu as WhPersonnel

from peewee import DoesNotExist, JOIN
import arrow


class CommonFunctions(QObject):

    """
    Class used for common queries across various modules
    """

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._geod = Geodesic.WGS84

    @staticmethod
    def get_cruise_id(year, vessel):
        """
        Method to return the currently selected cruise ID for Bottom Trawl Survey
        :return:
        """
        project_lu_id = Lookups.get(Lookups.type == "Project",
                                    Lookups.value == "West Coast Groundfish Slope/Shelf Bottom Trawl Survey").lookup
        try:
            cruise_op = OperationsFlattenedVw.get(
                OperationsFlattenedVw.project_lu == project_lu_id,
                OperationsFlattenedVw.operation_type == "Cruise",
                OperationsFlattenedVw.year_name == year,
                OperationsFlattenedVw.vessel_name == vessel.replace('\'', '')).operation
        except Exception as ex:
            # The cruise does not exist, so need to add in the parent year and passes
            # year_lu_id = Lookups.get(Lookups.type == 'Operation', Lookups.value == 'Year').lookup
            # pass_lu_id = Lookups.get(Lookups.type == 'Operation', Lookups.value == 'Pass').lookup
            # year_op, _ = Operations.get_or_create(operation_type_lu=year_lu_id,
            #                                       operation_name=year,
            #                                       project_lu=project_lu_id)
            # pass_1_op, _ = Operations.get_or_create(operation_type_lu=pass_lu_id,
            #                                         operation_name=1,
            #                                         project_lu=project_lu_id,
            #                                         parent_operation=year_op)
            # pass_2_op, _ = Operations.get_or_create(operation_type_lu=pass_lu_id,
            #                                         operation_name=2,
            #                                         project_lu=project_lu_id,
            #                                         parent_operation=year_op)
            cruise_op = None

        return cruise_op

    @staticmethod
    def get_personnel(op, position):
        """
        Method to return the IDs for the FPC, Scientist1, Scientist2, and Captain
        :param: op - WhOperationalSegment - represents the operational segment in the wheelhouse DB from which we're finding the FPC, etc...
        :param: position - enumerated value - FPC, Scientist1, Scientist2, Captain
        :return:
        """
        if not isinstance(op, WhOperationalSegment):
            logging.info(f'Input variable, op, is not an WhOperationalSegment data type, returning None >>> {position}')
            return None

        if position not in ["FPC", "Scientist1", "Scientist2", "Captain"]:
            logging.info(f"Position is incorrect: {position}")
            return None

        try:
            person_id = None
            first_name = ""
            last_name = ""

            op_pos = {"FPC": op.fpc, "Scientist1": op.scientist_1, "Scientist2": op.scientist_2}
            logging.info(f"op_pos = {op_pos}")

            full_name = WhPersonnel.get(WhPersonnel.person == op_pos[position]).full_name
            full_name_list = re.sub(r' .{1} ', '', re.sub(r'\([^)]*\)', '', full_name)).split(' ')
            if len(full_name_list) == 2:
                first_name = full_name_list[0]
                last_name = full_name_list[1]

            try:
                person = PersonnelLu.get(PersonnelLu.first_name == first_name,
                                         PersonnelLu.last_name == last_name)
            except DoesNotExist as ex:
                logging.error(f"User does not exist, trying fuzzy searching: {first_name[:4]} {last_name[:4]}")
                person = PersonnelLu.get(PersonnelLu.first_name.contains(first_name[:4]),
                                         PersonnelLu.last_name.contains(last_name[:4]))


            person_id = person.person

            # Aaron Chappel; Hack - should be Chappell, not misspelled Chappel that I have in the wheelhouse db for 2016
            # last_name = "Chappell" if last_name == "Chappel" else last_name

        except DoesNotExist as ex:
            # person_id = None
            logging.error('Name does not exist in FRAM Central: {0}, {1}'.format(first_name, last_name))

        except Exception as ex:
            logging.error(f"Error getting the {position}: {ex}")

        logging.info(f"person_id={person_id} >>> first_name = {first_name} >> last_name = {last_name}")

        return person_id

    @pyqtSlot(str, result=float)
    def lat_or_lon_to_dd(self, input_str):
        """
        Convert a latitude or longitude string in the form of:
        deg + u"\xb0" + " " + min + "' " + uom

        to decimal degrees

        :param input_str:
        :return:
        """
        # [dd, mm] = str.split("\xb0")
        try:
            [dd, mm] = input_str.split(" ")
        # mm = mm.translate({ord(i): None for i in " 'nsNSewEW"})

        except Exception as ex:
            return None

        if dd is None or dd == "" or mm is None or mm == "":
            return None

        if float(dd) < 0:
            return float(dd) - float(mm)/60

        return float(dd) + float(mm)/60

    def is_float(self, value):
        """
        Method to check if a value is a float or ot
        :param value:
        :return:
        """
        try:
            float(value)
            return True
        except:
            return False

    def fastStrptime(self, val):
        """
        Reference:  http://ze.phyr.us/faster-strptime/

        Samples:
        2016-05-21T14:24:30.685502+00:00    - 32
        2016-05-21T14:24:30+00:00           - 25

        Y - 0:4
        M - 5:7
        D - 8:10
        HH - 11:13
        MM - 14:16
        ss - 17:19
        SSSSSS - 20:26
        ZZ - 26:32

        :param val:
        :return:
        """

        l = len(val)

        # us = int(val[18:24])
        # If only milliseconds are given we need to convert to microseconds.
        # if l == 21:
        #     us *= 1000

        if len(val) == 32:
            return arrow.get(
                int(val[0:4]),  # %Y
                int(val[5:7]),  # %m
                int(val[8:10]),  # %d
                int(val[11:13]),  # %H
                int(val[14:16]),  # %M
                int(val[17:19]),  # %s
                int(val[20:26]),  # %f
                tzinfo=val[26:32]
            )
        elif len(val) == 25:
            return arrow.get(
                int(val[0:4]),  # %Y
                int(val[5:7]),  # %m
                int(val[8:10]),  # %d
                int(val[11:13]),  # %H
                int(val[14:16]),  # %M
                int(val[17:19]),  # %s
                tzinfo=val[19:25]
            )

        return arrow.get(val)

        #
        #
        # format = ""
        #
        # if format == '%Y%m%dT%H:%M:%S.%f' and (l == 21 or l == 24):
        #     us = int(val[18:24])
        #     # If only milliseconds are given we need to convert to microseconds.
        #     if l == 21:
        #         us *= 1000
        #     return datetime.datetime(
        #         int(val[0:4]),  # %Y
        #         int(val[4:6]),  # %m
        #         int(val[6:8]),  # %d
        #         int(val[9:11]),  # %H
        #         int(val[12:14]),  # %M
        #         int(val[15:17]),  # %s
        #         us,  # %f
        #     )
        #
        # # Default to the native strptime for other formats.
        # return datetime.datetime.strptime(val, format)

    def convert_lat_lon_to_dd(self, input_str, type, hemisphere):
        """
        Method to convert lat/lon values coming from NMEA sentences to decimal degrees
        :param input_str:
        :param type: Latitude or Longitude
        :param hemisphere: enumerated, one of NSEWnsew
        :return:
        """
        try:
            is_neg = True if hemisphere.lower() in ["w", "s"] else False
            pos = 2 if type == "Latitude" else 3

            deg = input_str[0:pos]
            min = input_str[pos:]
            dd = float(deg) + float(min)/60
            dd = -dd if is_neg else dd

            if (type == "Latitude" and (-90 <= dd <= 90)) or \
                    (type == "Longitude" and (-180 <= dd <= 180)):
                return dd

            else:

                logging.info(f'Invalid {type} value > {input_str}')
                return None

            # return dd

        except Exception as ex:
            logging.info('Error parsing position: {0} > {1}'.format(type, input_str))
            return None

    def convert_date_time(self, input_str, format):
        """
        Method to convert NMEA-formatted date-times to an ISO format with timezone
        :param input:
        :param format:
        :return:
        """
        hh = input_str[0:2]
        mm = input_str[2:4]
        ss = input_str[4:]

        return None

    def convert_julian_to_iso(self, julian_days=None, year=None):
        """
        Method to convert julian fractional days into ISO-formatted python datetime object
        :param julian_days: # of calendar julian days - include year for leap years
        :param year: year to convert for julian_days
        :return:
        """
        try:
            julian_days = float(julian_days)
        except:
            return None

        if time.daylight:
            offset_hour = -time.altzone
            # tz_name = 'PDT'
        else:
            offset_hour = -time.timezone
            # tz_name = 'PST'
        tz_name = time.tzname[time.daylight]
        tzlocal = tz.tzoffset(tz_name, offset_hour)

        frac_day, _day = modf(julian_days)
        frac_hour, _hour = modf(frac_day * 24)
        frac_min, _min = modf(frac_hour * 60)
        frac_sec, _sec = modf(frac_min * 60)
        julian_dt = datetime.strptime((str(int(year)) + str(int(_day))), '%Y%j')
        # julian_dt = arrow.get((str(int(year)) + str(int(_day))), 'YYYYDDDD')
        _month = julian_dt.month
        _day = julian_dt.day

        date_time = arrow.get(datetime(int(year), int(_month), int(_day),
                             int(_hour), int(_min), int(_sec), int(floor(frac_sec*1000000))))

        return arrow.get(date_time).replace(tzinfo="US/Pacific").isoformat()

        # date_time = datetime(int(year), int(_month), int(_day),
        #                      int(_hour), int(_min), int(_sec), int(floor(frac_sec*1000000)),
        #                      tzlocal)

        # utc_datetime = time_converter.local_to_utc(local_time=date_time.isoformat())
        # return utc_datetime.isoformat()

    def get_lat(self, lat, lon, range, bearing):
        """

        :param lat:
        :param lon:
        :param range:
        :param bearing:
        :return:
        """
        geod = Geodesic.WGS84
        g = geod.Direct(lat1=lat, lon1=lon, azi1=bearing, s12=range)
        return g['lat2']

    def get_lon(self, lat, lon, range, bearing):

        geod = Geodesic.WGS84
        g = geod.Direct(lat1=lat, lon1=lon, azi1=bearing, s12=range)
        return g['lon2']

    def get_distance(self, lat1, lon1, lat2, lon2):
        """
        Method to return the geodesic distance between two coordinates
        :param lat1: decimal degrees
        :param lon1: decimal degrees
        :param lat2: decimal degrees
        :param lon2: decimal degrees
        :return:
        """
        geod = Geodesic.WGS84
        g = geod.Inverse(lat1=lat1, lon1=lon1, lat2=lat2, lon2=lon2)
        return g["s12"]

    def get_distance_bearing(self, lat1, lon1, lat2, lon2):

        # geod = Geodesic.WGS84
        # g = geod.Inverse(lat1=lat1, lon1=lon1, lat2=lat2, lon2=lon2)

        g = self._geod.Inverse(lat1=lat1, lon1=lon1, lat2=lat2, lon2=lon2)
        return g["s12"], g["azi1"]

    def get_lat_lon(self, lat1, lon1, range, bearing):

        # geod=Geodesic.WGS84
        # g = geod.Direct(lat1=lat1, lon1=lon1, azi1=bearing, s12=range)

        g = self._geod.Direct(lat1=lat1, lon1=lon1, azi1=bearing, s12=range)
        return g["lat2"], g["lon2"]

    def newton(self, func, x0, fprime=None, args=(), tol=1.48e-8, maxiter=50, fprime2=None):
        """
        Copy of the scipy.optimize.zeros newton function as scipy wasn't working with cxFreeze

        :param x0:
        :param fprime:
        :param args:
        :param tol:
        :param maxiter:
        :param fprime2:
        :return:
        """

        """
        Find a zero using the Newton-Raphson or secant method.
        Find a zero of the function `func` given a nearby starting point `x0`.
        The Newton-Raphson method is used if the derivative `fprime` of `func`
        is provided, otherwise the secant method is used.  If the second order
        derivate `fprime2` of `func` is provided, parabolic Halley's method
        is used.
        Parameters
        ----------
        func : function
            The function whose zero is wanted. It must be a function of a
            single variable of the form f(x,a,b,c...), where a,b,c... are extra
            arguments that can be passed in the `args` parameter.
        x0 : float
            An initial estimate of the zero that should be somewhere near the
            actual zero.
        fprime : function, optional
            The derivative of the function when available and convenient. If it
            is None (default), then the secant method is used.
        args : tuple, optional
            Extra arguments to be used in the function call.
        tol : float, optional
            The allowable error of the zero value.
        maxiter : int, optional
            Maximum number of iterations.
        fprime2 : function, optional
            The second order derivative of the function when available and
            convenient. If it is None (default), then the normal Newton-Raphson
            or the secant method is used. If it is given, parabolic Halley's
            method is used.
        Returns
        -------
        zero : float
            Estimated location where function is zero.
        See Also
        --------
        brentq, brenth, ridder, bisect
        fsolve : find zeroes in n dimensions.
        Notes
        -----
        The convergence rate of the Newton-Raphson method is quadratic,
        the Halley method is cubic, and the secant method is
        sub-quadratic.  This means that if the function is well behaved
        the actual error in the estimated zero is approximately the square
        (cube for Halley) of the requested tolerance up to roundoff
        error. However, the stopping criterion used here is the step size
        and there is no guarantee that a zero has been found. Consequently
        the result should be verified. Safer algorithms are brentq,
        brenth, ridder, and bisect, but they all require that the root
        first be bracketed in an interval where the function changes
        sign. The brentq algorithm is recommended for general use in one
        dimensional problems when such an interval has been found.
        """
        if tol <= 0:
            raise ValueError("tol too small (%g <= 0)" % tol)
        if maxiter < 1:
            raise ValueError("maxiter must be greater than 0")
        if fprime is not None:
            # Newton-Rapheson method
            # Multiply by 1.0 to convert to floating point.  We don't use float(x0)
            # so it still works if x0 is complex.
            p0 = 1.0 * x0
            fder2 = 0
            for iter in range(maxiter):
                myargs = (p0,) + args
                fder = fprime(*myargs)
                if fder == 0:
                    msg = "derivative was zero."
                    warnings.warn(msg, RuntimeWarning)
                    return p0
                fval = func(*myargs)
                if fprime2 is not None:
                    fder2 = fprime2(*myargs)
                if fder2 == 0:
                    # Newton step
                    p = p0 - fval / fder
                else:
                    # Parabolic Halley's method
                    discr = fder ** 2 - 2 * fval * fder2
                    if discr < 0:
                        p = p0 - fder / fder2
                    else:
                        p = p0 - 2*fval / (fder + sign(fder) * sqrt(discr))
                if abs(p - p0) < tol:
                    return p
                p0 = p
        else:
            # Secant method
            p0 = x0
            if x0 >= 0:
                p1 = x0*(1 + 1e-4) + 1e-4
            else:
                p1 = x0*(1 + 1e-4) - 1e-4
            q0 = func(*((p0,) + args))
            q1 = func(*((p1,) + args))
            for iter in range(maxiter):
                if q1 == q0:
                    if p1 != p0:
                        msg = "Tolerance of %s reached" % (p1 - p0)
                        warnings.warn(msg, RuntimeWarning)
                    return (p1 + p0)/2.0
                else:
                    p = p1 - q1*(p1 - p0)/(q1 - q0)
                if abs(p - p1) < tol:
                    return p
                p0 = p1
                q0 = q1
                p1 = p
                q1 = func(*((p1,) + args))
        msg = "Failed to converge after %d iterations, value is %s" % (maxiter, p)
        raise RuntimeError(msg)