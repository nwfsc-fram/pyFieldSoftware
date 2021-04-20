
# -----------------------------------------------------------------------------
# Name:        ObserverTabletGPS.py
# Purpose:     Coordinate pull from GPS with Powershell
#
# Author:      Jim Fellows <james.fellows@noaa.gov>
#
# Created:     March 18, 2021  (For https://www.fisheries.noaa.gov/jira/browse/FIELD-1442)
# ------------------------------------------------------------------------------

import arrow
import logging
import subprocess
import threading

from PyQt5.QtCore import pyqtProperty, QVariant, QObject, pyqtSignal, pyqtSlot


class TabletGPS(QObject):
    """
    Class used by ObserverFishingLocations.py and GPSEntryDialog.qml
    Core function is _get_gps_lat_lon, which runs a powershell command to access tablets built-in GPS
    https://stackoverflow.com/questions/46287792/powershell-getting-gps-coordinates-in-windows-10-using-windows-location-api

    GPS must first be enabled/started on Getac tablet using G-Manager app.
    Powershell might need to have Set-ExecutionPolicy changed.

    Function spins up on thread to avoid UI freeze while acquiring signal, then sets lat and long in decimal degrees.
    Setters trickle down to associated degrees, minutes and seconds properties.
    """
    latitudeChanged = pyqtSignal()
    longitudeChanged = pyqtSignal()
    timestampChanged = pyqtSignal(QVariant, arguments=['ts'])
    statusChanged = pyqtSignal(QVariant, arguments=['s'])  # emits to UI to display status
    unusedSignal = pyqtSignal()

    TIMEOUT = 10  # used in subprocess for powershell timeout when getting coordinates
    TIMESTAMP_STR_FMT = '%a %b %d %H:%M:%S %Y'  # str date format that javascript likes

    # status / error handling for gps signal try
    GPS_AVAILABLE = 'Signal Acquired'
    ACCESS_DENIED_ERR = 'Tablet GPS access denied.'
    TIMEOUT_ERR = f"{TIMEOUT}s timeout\nsignal not acquired."
    UNKNOWN_ERR = "UNHANDLED ERROR: Unable to\nacquire GPS coordinates"

    def __init__(self):
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

    def _reset_data(self):
        """
        Clear out data to reset
        :return:
        """
        self.latDD = None
        self.lonDD = None
        self.timestamp = None
        self.status = None

    @pyqtProperty(QVariant, notify=unusedSignal)
    def status(self):
        return self._status

    @status.setter
    def status(self, s):
        self._status = s
        self.statusChanged.emit(self._status)
        if self._status != self.GPS_AVAILABLE and self._status:
            self._logger.warning(self._status.replace('\n', ' '))

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
                self.timestampChanged.emit(self._timestamp)

    def _generate_timestamp(self):
        """
        Format defined above is in a format the javascripts new Date(date_string) can handle
        Do we need to specify timezone?
        :return: set timestamp_str
        """
        self.timestamp = arrow.now().strftime(self.TIMESTAMP_STR_FMT)

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
        :return: Object with lat/lon info
        """
        self.t = threading.Thread(name='gpsThread', target=self._get_gps_lat_lon, daemon=True)
        self.t.start()

    def _get_gps_lat_lon(self):
        """
        Use powershell to access Getac tablet internal GPS
        Powershell permissionscheck Get-ExecutionPolicy/Set-ExecutionPolicy unrestricted) must be open,
        and GPS antenna must be active
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
            self.status = self.GPS_AVAILABLE
