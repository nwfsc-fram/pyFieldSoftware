__author__ = 'james.fellows'
# -------------------------------------------------------------------------------
# Name:         ClockUpdater
# Purpose:      Threaded timer for updating system time with GPS time
#
# Author:      Jim Fellows
# Email:       james.fellows@noaa.gov
#
# Created:     Sep 15, 2021
# -------------------------------------------------------------------------------

import arrow
import logging
import pywintypes
from threading import Timer
import win32api

from PyQt5.QtCore import QObject, QVariant, pyqtProperty


class ClockUpdater(Timer, QObject):
    """
    Class inherits threaded timer and QObject for PyQt

    Steps to update system clock
    1. Pass GPS time to class whenever it changes
    2. Thread interval just resets "ready_to_update" to True whenever triggered
    3. setter for gpsTime checks to see if ready_to_update = True
    4. If ready_to_update, update system clock with the newly passed gpsTime
    """

    def __init__(self, interval=10):
        self.check_interval = interval  # how often should we check
        self._gps_time = None
        self._ready_to_update = False

        # init super Timer class with interval land target function
        Timer.__init__(self, self.check_interval, self._prepare_for_update)
        QObject.__init__(self)
        self.daemon = True  # thread dies when app closes

    def run(self):
        """
        Called by self.start()
        while not finished, wait over interval
        self.function = func passed in during thread init
        :return:
        """
        while not self.finished.wait(self.check_interval):
            self.function(*self.args, **self.kwargs)

    @pyqtProperty(QVariant)
    def gpsTime(self):
        """
        Expose property, comes in as string from QML
        :return: date string
        """
        return self._gps_time

    @gpsTime.setter
    def gpsTime(self, time_str):
        """
        Set onTextChanged for MainForm.tfTime when new GPS time becomes available
        If we're ready for an update, update computer/system clock
        :param time_str: time string
        """
        self._gps_time = time_str
        if self._ready_to_update:
            self._update_computer_clock()

    def _prepare_for_update(self):
        """
        mark ClockUpdater as "ready" over defined interval
        e.g. every 5 minutes set as ready for update to system clock
        :return:
        """
        self._ready_to_update = True

    def _update_computer_clock(self):
        """
        Take the latest GPS time and update system clock
        Need to set to GMT/UTC, not local
        https://stackoverflow.com/questions/12110748/in-python-using-win32api-doesnt-set-the-correct-date
        TODO: Update sys time with full datestamp from GPS
        """
        if not self._gps_time:
            return

        # borrow year, month, day from system time until better option found
        sys_utc = arrow.utcnow()
        try:
            gps_time = arrow.get(self._gps_time, 'HH:mm:ss')
        except Exception as e:
            logging.warning(f"Failed to convert gps time to HH:mm:ss datetime; {e}")
            return

        logging.info(f"Updating computer clock, existing sys time = {sys_utc}, gps time = {self._gps_time}")

        try:
            yr = sys_utc.year
            mo = sys_utc.month
            dow = sys_utc.isoweekday()  # win32api expects ISO (1-7) int
            day = sys_utc.day
            hr = gps_time.hour
            mins = gps_time.minute
            secs = gps_time.second

            win32api.SetSystemTime(yr, mo, dow, day, hr, mins, secs, 0)
            logging.info(f"System time reset to UTC {yr}-{mo}-{day} {hr}:{mins}:{secs}, day of week int --> {dow}")
        except pywintypes.error as pe:
            logging.warning(f"Admin privs needed to update system clock; {pe}")
        except Exception as e:
            logging.warning(f"System clock update failed; {e}")

        self._ready_to_update = False


if __name__ == '__main__':
    systime = arrow.utcnow()
    t = arrow.now().format("HH:mm:ss")
    # print(type(t))
    dt = arrow.get(t, 'HH:mm:ss')
    print('Sys Year: ', systime.year)
    print('Sys Month: ', systime.month)
    print('Sys Weekday: ', systime.weekday())
    print('Sys ISO Weekday: ', systime.isoweekday())
    print('Sys Day: ', systime.day)
    print('dt minute: ', dt.minute)
    print('dt sec: ', dt.second)
    print('dt hr: ', dt.hour)
