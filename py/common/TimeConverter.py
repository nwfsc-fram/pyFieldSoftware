__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        TimeConverter
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 30, 2016
# License:     MIT
#-------------------------------------------------------------------------------
import time
from dateutil import parser, tz		# TimeConverter class
from datetime import datetime, timedelta, tzinfo, timezone	# TimeConverter class


class TimeConverter:
    """
    TimeConverter class is used to convert between local and UTC time (in both directions). A user simply has
    to construct a TimeConverter object, and then call either local_to_utc(local_time=<datetime object>) or
    utc_to_local(utc_time=<datetime object>) and the respective time will be returned. Note that an actual datetime
    object will be returned.  Or if one wants an ISO-string formatted version returned, just call:

    my_new_utc_time = local_to_utc_as_iso(local_time=<datetime object>)

    my_new_local_time = utc_to_local_as_iso(utc_time=<datetime object>)

    instead.
    """
    def __init__(self, **kwargs):
        super(TimeConverter, self).__init__(**kwargs)

    @staticmethod
    def datetime_as_float(date_time=None, is_utc=True):
        """
        Method to convert a datetime object to a float representing the "seconds since the Epoch,"
        defined to be 1/1/1970, UTC.  Note: the fact that it's UTC is significant--if you feed this
        method 1/1/1970 00:00:00 PST, it, correctly, returns 28800.0 seconds, i.e., 08:00 hours,
        which is indeed what time it was in UTC at 1/1/1970 00:00:00 PST.
        :param datetime: datetime object.  Note: can be "aware" or "naive"; see
               https://docs.python.org/3.3/library/datetime.html?highlight=datetime
               for an explanation of the difference
        :param is_utc:  True / False - if input is naive, indicates whether or not it's UTC
        :return: float variable representing the seconds since the Epoch
        """
        if date_time is None:
            return None

        if date_time.tzinfo is None or date_time.tzinfo.utcoffset(date_time) is None:
            # naive time zone
            # Reference: http://stackoverflow.com/questions/5802108/how-to-check-if-a-datetime-object-is-localized-with-pytz

            if is_utc:
                time_zone = tz.tzutc()
            else:
                time_zone = tz.tzlocal()

            date_time = date_time.replace(tzinfo=time_zone) # convert naive to aware

        epoch_datetime = datetime(1970, 1, 1).replace(tzinfo=tz.tzutc())

        return (date_time - epoch_datetime).total_seconds()

    @staticmethod
    def local_to_utc(local_time=None):
        """
        Method to convert a local time to a UTC time
        :param local_time: a datetime object
        :return utc_time: a datetime object of the UTC time
        """
        if isinstance(local_time, str):
            # Convert to a datetime object if needed
            local_time = parser.parse(local_time)

        utc_zone = tz.tzutc()
        local_zone = tz.tzlocal()

        local_time = local_time.replace(tzinfo=local_zone)
        utc_time = local_time.astimezone(utc_zone)

        return utc_time
        # return utc_time.replace(tzinfo=simple_utc())

        # loc_time = time.localtime(start_datetime.timestamp())
        # utc_time = time.gmtime(start_datetime.timestamp())
        # timestamp = start_datetime.replace(tzinfo=timezone.utc).timestamp()

        # Old Technique
        # utc_time = time.gmtime(local_time.timestamp())
        # return time.strftime('%Y-%m-%dT%H:%M:%SZ', utc_time)

    def local_to_utc_as_iso(self, local_time=None):
        """
        Convert a local time to a UTC time and return it as a string in ISO format
        :param local_time: datetime object
        :return:
        """

        # Need to use strftime otherwise the timezone is left off as it is None because it is UTC
        # return self.local_to_utc(local_time=local_time).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        return self.local_to_utc(local_time=local_time).replace(tzinfo=simple_utc()).isoformat()
        # return self.local_to_utc(local_time=local_time).isoformat()

    @staticmethod
    def utc_to_local(utc_time=None):
        """
        Method to convert a UTC time to a local time

        Ref: http://stackoverflow.com/questions/4770297/python-convert-utc-datetime-string-to-local-datetime
        Ref: http://stackoverflow.com/questions/2331592/datetime-datetime-utcnow-why-no-tzinfo

        :param utc_time: a datetime object
        :return local_time: the UTC time converted to the local_time, as a datetime object
        """

        if isinstance(utc_time, str):
            # Convert to a datetime object if needed
            utc_time = parser.parse(utc_time)

        utc_zone = tz.tzutc()
        local_zone = tz.tzlocal()

        utc_time = utc_time.replace(tzinfo=utc_zone)
        local_time = utc_time.astimezone(local_zone)

        return local_time

        # Current UTC time
        # utc_time = datetime.utcnow()
        # utc_time = utc_time.replace(tzinfo=utc_zone)

        # or
        # utc_time = datetime.now(tz=tz.tzutc())

        # Old technique, does not include timezone on the return value
        # local_time = time.localtime(utc_time.timestamp())
        # return time.strftime('%Y-%m-%dT%H:%M:%S%z', local_time)

    def utc_to_local_as_iso(self, utc_time=None):
        """
        Method to convert a utc time to a local time and return it as a string in ISO format
        :param utc_time: a datetime object
        :return:
        """
        return self.utc_to_local(utc_time=utc_time).isoformat()

    # def local_as_float(self):
    #     """
    #     Method to convert the local system clock time to a float representing the number of seconds since the Epoch
    #     :return:
    #     """
    #     return (datetime.now() - datetime(1970, 1, 1)).total_seconds()

    # def utc_as_float(self):
    #     """
    #     Method to convert the UTC time to a float representing the number of seconds since the Epoch
    #     :return:
    #     """
    #     return (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()


if __name__ == '__main__':

    # Testing Code
    t = TimeConverter()
    dt = datetime(1970, 1, 2)
    print('\nTime Zone Info / Seconds since the Epoch / Hours since the Epoch:')

    # Local Time Zone
    dt = dt.replace(tzinfo=tz.tzlocal())
    num_secs = t.datetime_as_float(dt)
    print(dt.tzinfo, '\t/\t', num_secs, '\t/\t', num_secs/3600)

    # UTC Time Zone
    dt = dt.replace(tzinfo=tz.tzutc())
    num_secs = t.datetime_as_float(dt)
    print(dt.tzinfo, '\t/\t', num_secs, '\t/\t', num_secs/3600)

    dt = dt.replace(tzinfo=None)
    num_secs = t.datetime_as_float(dt)
    print(dt.tzinfo, '\t\t/\t',  num_secs, '\t/\t', num_secs/3600)

    t1 = datetime.now()
    print(t1.isoformat())