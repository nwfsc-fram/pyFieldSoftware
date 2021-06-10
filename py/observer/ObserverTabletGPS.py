
# -----------------------------------------------------------------------------
# Name:        ObserverTabletGPS.py
# Purpose:     Coordinate pull from GPS with Powershell/Serial Port
#
# Author:      Jim Fellows <james.fellows@noaa.gov>
#
# Created:     March 18, 2021  (For https://www.fisheries.noaa.gov/jira/browse/FIELD-1442)
# ------------------------------------------------------------------------------

import arrow
import logging
import subprocess
import threading
import time
import re
from serial import Serial
import serial
import pynmea2
from contextlib import suppress, contextmanager
from datetime import datetime, timedelta

from PyQt5.QtCore import pyqtProperty, QVariant, QObject, pyqtSignal, pyqtSlot
from py.observer.ObserverDBUtil import ObserverDBUtil


class TabletGPS(QObject):
    """
    Class used by ObserverFishingLocations.py and GPSEntryDialog.qml
    Core function is _get_gps_lat_lon_serial, which pulls data over serial port from tablet GPS
    Function is threaded to avoid UI freeze, and only one thread should be allowed to be alive at a time.
    Setters trickle down to associated degrees, minutes and seconds properties and emit to UI.
    Powershell was used, but changing between getting coords from Wifi/location service and actual GPS
    cause inconsistent results:
    https://stackoverflow.com/questions/46287792/powershell-getting-gps-coordinates-in-windows-10-using-windows-location-api
    """
    latitudeChanged = pyqtSignal()
    longitudeChanged = pyqtSignal()
    timestampChanged = pyqtSignal(QVariant, arguments=['ts'])
    statusChanged = pyqtSignal(QVariant, QVariant, int, arguments=['s', 'color', 'size'])  # emits to UI to display status
    focusDepthField = pyqtSignal()
    unusedSignal = pyqtSignal()

    # create/set DB setting params
    TIMEOUT = int(ObserverDBUtil.get_or_set_setting('gps_timeout_secs', default_value='10'))
    COMPORT = ObserverDBUtil.get_or_set_setting('gps_comport', default_value='COM2')

    # status / error handling for gps signal try.  "Message", "Font Color", "Font Size"
    SIGNAL_ACQUIRED = ('Signal Acquired!', "green", 18)
    ACCESS_DENIED_ERR = ('Access denied.', 'red', 18)
    TIMEOUT_ERR = (f"{TIMEOUT}s timeout.", 'red', 18)
    UNKNOWN_ERR = ("UNHANDLED ERROR: Unable to\nacquire GPS coordinates", 'red', 18)

    def __init__(
            self,
            comport=COMPORT,
            baudrate='9600',
            databits=8,
            stopbits=1,
            parity='N',
            timeout=TIMEOUT  # reuse for comport timeout (also used for signal acquisition)
    ):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._lat_dd = None
        self._lat_degrees = None
        self._lat_minutes = None
        self._lat_seconds = None
        self._lon_dd = None
        self._lon_degrees = None
        self._lon_minutes = None
        self._lon_seconds = None
        self._timestamp = None
        self._status = None
        self._signal_thread = threading.Thread()  # placeholder so we can call isAlive() on it to start

        # serial port config; error handling wasn't working right unless I created a blank Serial() first...
        self.serial_port = Serial()
        self.serial_port.port = comport
        self.serial_port.baudrate = baudrate
        self.serial_port.bytesize = databits
        self.serial_port.timeout = timeout
        self.serial_port.stopbits = stopbits

    @contextmanager
    def open(self):
        """
        Not used, havent tested yet, using open_port and close_port in try except finally for now
        :return: serial port
        """
        if self.serial_port.isOpen():
            self._logger.warning(f"Serial port {self.serial_port.name} already open")
            yield self.serial_port
        try:
            self.serial_port.open()
            self._logger.info(f"Serial port {self.serial_port.name} opened")
            yield self.serial_port
        except serial.serialutil.SerialException as e:
            self._logger.error(f"Cant open port: {str(e)}")
            self.timestamp = datetime.now()
            self.status = self.ACCESS_DENIED_ERR
        finally:
            if self.serial_port.isOpen():
                self.serial_port.close()
                self._logger.info(f"Serial port {self.serial_port.name} closed.")

    def _open_port(self):
        """
        method to manually open port
        I'll use with context manager for now instead
        :return: None
        """
        self._logger.info("Trying to open port")
        if not self.serial_port.isOpen():
            try:
                self.serial_port.open()
                self._logger.info(f"Serial port {self.serial_port.name} opened")
                return True
            except serial.serialutil.SerialException as e:
                self._logger.error(f"Cant open port: {str(e)}")
                return False
        else:
            self._logger.warning(f"Serial port {self.serial_port.name} already open.")
            return True

    def _close_port(self):
        """
        method to manually close port
        I'll use with context manager for now instead
        :return:
        """
        if self.serial_port.isOpen():
            self.serial_port.close()
            self._logger.info(f"Serial port {self.serial_port.name} closed.")

    def _reset_data(self):
        """
        Clear out data to reset
        :return:
        """
        self.latDD = None
        self.lonDD = None
        self.timestamp = None
        self.status = "", "black", 18  # default text for status label in QML

    @pyqtProperty(QVariant, notify=unusedSignal)
    def status(self):
        return self._status

    @status.setter
    def status(self, s):
        self._status = s
        self.statusChanged.emit(self._status[0], self._status[1], self._status[2])  # text, color, fontsize

    @pyqtProperty(QVariant, notify=timestampChanged)
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, ts):
        """
        Set new timestamp and signal to UI
        :param ts: timestamp (see self._generate_timestamp)
        :return:
        """
        if self._timestamp != ts:
            self._timestamp = ts
            self._logger.info(f"timestamp updated to {self._timestamp}")
            if self._timestamp:
                self.timestampChanged.emit(self._format_js_timestamp_str(ts))

    def _format_js_timestamp_str(self, ts):
        """
        format to string for QML GPSEntryDialog ingestion
        :param ts: datetime object
        :return: string
        """
        try:
            return ts.strftime('%a %b %d %H:%M:%S %Y')  # str date format that javascript likes
        except AttributeError as e:
            self._logger.error(f"Type {type(ts)} ({ts}) is not datetime, and doesnt have strftime method; {e}")

    @pyqtProperty(QVariant, notify=latitudeChanged)
    def latDD(self):
        return self._lat_dd

    @latDD.setter
    def latDD(self, dd):
        """
        Setting new lat decimal degrees value propagates to degrees, minutes, seconds
        :param dd: float (decimal degrees)
        :return: None (emits lat changed signal)
        """
        if self._lat_dd != dd:
            self._lat_dd = dd
            self._lat_degrees = self.dd_to_dms(dd)[0]
            self._lat_minutes = self.dd_to_dms(dd)[1]
            self._lat_seconds = self.dd_to_dms(dd)[2]
            self._logger.info(f"Lat changed to {dd} or {self._lat_degrees}'{self._lat_minutes}.{self._lat_seconds}")
            if self._lat_dd and isinstance(self._lat_dd, float):  # avoid emitting invalid nums to QML
                self.latitudeChanged.emit()

    @pyqtProperty(QVariant, notify=unusedSignal)
    def latDegrees(self):
        return self._lat_degrees

    @pyqtProperty(QVariant, notify=unusedSignal)
    def latMinutes(self):
        return self._lat_minutes

    @pyqtProperty(QVariant, notify=unusedSignal)
    def latSeconds(self):
        return self._lat_seconds

    @pyqtProperty(QVariant, notify=longitudeChanged)
    def lonDD(self):
        return self._lon_dd

    @lonDD.setter
    def lonDD(self, dd):
        """
        Setting new longitude decimal degrees value propagates to degrees, minutes, seconds
        :param dd: float (decimal degrees)
        :return: None (emits lon changed signal)
        """
        if self._lon_dd != dd:
            self._lon_dd = dd
            self._lon_degrees = self.dd_to_dms(dd)[0]
            self._lon_minutes = self.dd_to_dms(dd)[1]
            self._lon_seconds = self.dd_to_dms(dd)[2]
            self._logger.info(f"Lon changed to {dd} or {self._lon_degrees}'{self._lon_minutes}.{self._lon_seconds}")
            if self._lon_dd and isinstance(self._lon_dd, float):  # avoid emitting invalid nums to QML
                self.longitudeChanged.emit()

    @pyqtProperty(QVariant, notify=unusedSignal)
    def lonDegrees(self):
        return self._lon_degrees

    @pyqtProperty(QVariant, notify=unusedSignal)
    def lonMinutes(self):
        return self._lon_minutes

    @pyqtProperty(QVariant, notify=longitudeChanged)
    def lonSeconds(self):
        return self._lon_seconds

    @staticmethod
    def dd_to_dms(dd):
        """
        https://stackoverflow.com/questions/2579535/convert-dd-decimal-degrees-to-dms-degrees-minutes-seconds-in-python
        convert to degrees, minutes, seconds, handle negatives
        :param dd: float (decimal degrees)
        :return: (degrees, minutes, seconds)
        """
        try:
            negative = dd < 0
            dd = abs(dd)
            minutes, seconds = divmod(dd*3600, 60)
            degrees, minutes = divmod(minutes, 60)
            if negative:
                if degrees > 0:
                    degrees = -degrees
                elif minutes > 0:
                    minutes = -minutes
                else:
                    seconds = -seconds
            return degrees, minutes, seconds
        except TypeError as e:
            return None, None, None

    @pyqtSlot(name="getFakeData")
    def get_fake_data(self):
        """
        testing purposes
        :return: None
        """
        self._reset_data()
        self._generate_timestamp()
        self.latDD = 47.752608138733954
        self.lonDD = -122.53187533658092

    @pyqtSlot(name='getGPSLatLon')
    def get_gps_lat_lon(self):
        """
        Wrapper func to set values and signal UI.
        Thread avoids UI freezing and will kill when function returns, or when parent thread dies (daemon status)
        Recreates thread everytime and first checks if existing thread is still alive and running.  Prevents
        multiple threads being launched at once (User can click button as much as they want)
        """
        if self._signal_thread.isAlive():
            self._logger.warning(f"Thread already running, please stop clicking.")
            return
        else:
            self._signal_thread = threading.Thread(name='gpsThread', target=self._get_gps_lat_lon_serial, daemon=True)
            self._logger.info(f"Starting new thread {self._signal_thread.name}...")
            self._signal_thread.start()

    @staticmethod
    def generate_ellipsis(seconds_elapsed, max_dots=5, substr="."):
        """
        create dots based on how many seconds have gone by.
        Use to animate UI when waiting on threaded process
        :param seconds_elapsed: int; how many seconds have gone by?
        :param max_dots: int; whats the max length of your elipses?
        :return: string (e.g. ...)
        """
        return "".join([substr]*(seconds_elapsed % (max_dots+1)))

    def _get_gps_lat_lon_serial(self):
        """
        Read lines over serial port. Break while loop when lat long datetime have been pulled, or timeout reached
        1. Clear out vals (lat,lon,timestamp,status), open port, start timer
        2. Read lines while values are incomplete, parse with pynmea and populate as needed
        3. When parsed, use setters to populate values and signal to UI
        4. Timer functionality emits ellipses while running, and stops func when timeout it reached
        5. Finally statement should always close port and wrap things up
        :return: None (sets properties)
        """
        self._logger.info(f"Starting GPS lat/long pull")
        self._reset_data()
        try:
            opened = self._open_port()  # returns true if successful, or port already open (shouldnt be)
            if not opened:
                self.timestamp = datetime.now()
                self.status = self.ACCESS_DENIED_ERR
                return
            else:
                start = datetime.now()  # start time for timeout
                secs = 0  # track seconds for ellipses
                # Keep while loop open while params are not set, or timeout reached
                while not self._lat_dd or not self._lon_dd or not self._timestamp:
                    line = self.serial_port.readline().decode('ascii', errors='replace')
                    self._logger.info("Reading line " + line.replace("\n", "").strip())

                    elapsed = datetime.now() - start  # track elapsed time for timeout / ellipses
                    if elapsed.seconds > self.TIMEOUT:
                        self._logger.warning(f"GPS unable to acquire data after {self.TIMEOUT}s")
                        self.status = self.TIMEOUT_ERR
                        break  # get out of while loop, go to finally stmt

                    elif elapsed.seconds > secs:  # have we advanced a full second?
                        self.status = self.generate_ellipsis(elapsed.seconds, max_dots=3, substr=" ~ ><(((8>"), 'black', 13
                    secs = elapsed.seconds

                    # use pynmea2 to try and parse valid sentences
                    try:
                        pn = pynmea2.parse(line)
                    except pynmea2.nmea.ParseError:
                        continue

                    # suppress KeyError/Attribute (we don't know which nmea sentences have which attributes)
                    with suppress(KeyError, AttributeError):
                        self.latDD = pn.latitude
                        self.lonDD = pn.longitude

                        # datestamp is only available in GPRMC, and must be combined with GPS time
                        ds = pn.datestamp
                        ts = pn.timestamp
                        self.timestamp = datetime(
                            year=ds.year,
                            month=ds.month,
                            day=ds.day,
                            hour=ts.hour,
                            minute=ts.minute
                        ) - timedelta(hours=7)  # UTC offset, should this always be seven or seasonally 7/8?

        # general exception here to make sure close_port is hit
        except Exception as e:
            self._logger.error(f"Error streaming data over GPS serial port; {e}")
        finally:
            self._close_port()
            if self._lat_dd and self._lon_dd and self._timestamp:  # did we get everything?
                self.status = self.SIGNAL_ACQUIRED
                self.focusDepthField.emit()  # advance cursor to depth field if successful

    def _get_gps_lat_lon_powershell(self):
        """
        Use powershell to access Getac tablet internal GPS
        Powershell permissionscheck Get-ExecutionPolicy/Set-ExecutionPolicy unrestricted) must be open,
        and GPS antenna must be active

        NOTE: No longer using this due to confusion with WiFi location services. Serial Port direc access
        to GPS is more consistent

        :return: tuple of floats (latitude, longitude); units = decimal degrees
        """
        self._reset_data()
        self._logger.info(f"Trying to acquire coordinates from tablet GPS...")
        pshell_cmd = f'''
            Add-Type -AssemblyName System.Device
            $GeoWatcher = New-Object System.Device.Location.GeoCoordinateWatcher
            $GeoWatcher.Start()
            
            while (($GeoWatcher.Status -ne 'Ready') -and ($GeoWatcher.Permission -ne 'Denied')) {{
                Start-Sleep -Milliseconds 100
            }}
            
            if ($GeoWatcher.Permission -eq 'Denied') {{
                '{self.ACCESS_DENIED_ERR}'
            }} else {{
                $GeoWatcher.Position.Location.Latitude
                $GeoWatcher.Position.Location.Longitude
            }}
        '''
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # prevent pshell window from popping
        try:
            output = subprocess.run(
                ["powershell", "-Command", pshell_cmd],
                startupinfo=startupinfo,
                stdout=subprocess.PIPE,
                timeout=self.TIMEOUT  # seconds until we stop trying
            ).stdout
        except subprocess.TimeoutExpired as e:
            self.status = self.TIMEOUT_ERR
            return

        except BaseException as be:
            self.status = f"{self.UNKNOWN_ERR}; {str(be)}"
            return

        output_strs = output.decode('utf-8').strip().split('\r\n')

        if output_strs[0] == self.ACCESS_DENIED_ERR:
            self.status = self.ACCESS_DENIED_ERR
            return
        else:
            dds = tuple([float(xy) for xy in output_strs])

            # set actual pyqtProperties here to trigger signals
            self.timestamp = self._generate_timestamp()
            self.latDD = dds[0]
            self.lonDD = dds[1]
            self.status = self.SIGNAL_ACQUIRED


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        # format="%(asctime)s [%(levelname)8.8s] %(message)s",
        format='%(asctime)s %(levelname)s %(filename)s(%(lineno)s) "%(message)s"'
    )
    gps = TabletGPS()
    # gps._get_gps_lat_lon_serialtest()
