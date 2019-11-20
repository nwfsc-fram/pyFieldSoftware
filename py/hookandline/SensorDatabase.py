import os
import sys
import logging
import re
from PyQt5.QtCore import QObject, QVariant, pyqtProperty, pyqtSlot, pyqtSignal, QThread
import arrow
import apsw as sqlite
from py.hookandline.HookandlineFpcDB_model import Lookups, ParsingRules, database, fn, JOIN
from playhouse.shortcuts import model_to_dict, dict_to_model
from py.hookandline.DataConverter import DataConverter


class SensorDatabase(QObject):

    errorReceived = pyqtSignal(str, arguments=["msg",])

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db
        self._dc = DataConverter()

        self._database_path = None
        self._conn = None
        self._cursor = None

    def get_sensor_database_old(self, datetime=None):
        """
        Method to retrieve the current sensors database.  Look backwards up to 10 days to try and find a sensors
        database that mataches the given datetime.  Note that a user could start HookLogger and leaving it running
        for multiple days and a sensors database is only created when HookLogger is launched.
        :return:
        """
        if not datetime:
            return

        db_found = False
        datetime = arrow.get(datetime)

        try:

            i = 0
            while i > -10:

                test_day = datetime.shift(days=i)
                file_name = f"sensors_{test_day.format('YYYYMMDD')}.db"

                dir = os.path.abspath(os.path.dirname(sys.argv[0]))
                full_path = os.path.join(dir, "data", file_name)
                logging.info(f"trying to find sensors db at: {full_path}")

                if os.path.exists(full_path):

                    logging.info(f"\t\tsensors db found: {full_path}")
                    self._dbpath = full_path
                    db_found = True
                    break

                i -= 1

        except Exception as ex:

            logging.info(f"Error is getting the date: {ex}")

        if db_found:
            self._conn = sqlite.Connection(self._dbpath)
            self._conn.setbusytimeout(10000)
            self._cursor = self._conn.cursor()

        else:
            logging.info(f"sensor database was not found")

    def get_sensor_database(self, datetime=None):
        """
        Method to retrieve the current sensors database.  Look backwards up to 10 days to try and find a sensors
        database that mataches the given datetime.  Note that a user could start HookLogger and leaving it running
        for multiple days and a sensors database is only created when HookLogger is launched.
        :return:
        """
        if not datetime:
            return

        try:
            status = False
            datetime = arrow.get(datetime).format('YYYYMMDD')
            file_name = f"sensors_{datetime}.db"
            dir = os.path.abspath(os.path.dirname(sys.argv[0]))
            full_path = os.path.join(dir, "data", file_name)
            logging.info(f"trying to find sensors db at: {full_path}")

            if os.path.exists(full_path):

                logging.info(f"\t\tsensors db found: {full_path}")
                self._database_path = full_path
                self._conn = sqlite.Connection(self._database_path)
                self._conn.setbusytimeout(10000)
                self._cursor = self._conn.cursor()
                status = True

        except Exception as ex:

            logging.info(f"Error is getting the date: {ex}")

        return status

    def query_by_datetime(self, datetime, sentences):
        """
        Method to get the given sentence closest to the datetime provided.
        :param datetime:
        :param sentence:
        :return:
        """
        if not self._cursor or not datetime or not sentences:
            logging.info(f"cursor does not exist, returning...")
            return

        try:
            results = []
            msg = ""

            # Craft the sql
            clause = "AND ("
            for i in range(len(sentences)):
                clause += f"RAW_SENTENCE LIKE ? OR "
            clause = f"{clause[:-4]})"
            # sql = f"SELECT * FROM RAW_SENTENCES WHERE STRFTIME('%Y-%m-%dT%H:%M:%S', DATE_TIME) = ? {clause}"
            sql = f"SELECT * FROM RAW_SENTENCES WHERE DATE_TIME BETWEEN ? AND ? {clause} ORDER BY DATE_TIME ASC;"

            # Craft the parameters
            if isinstance(datetime, str):
                datetime = arrow.get(datetime).replace(tzinfo='US/Pacific')  # 20190921 - Added the replace clause
            start_date_time = datetime.isoformat()
            end_date_time = datetime.shift(seconds=+10).isoformat()
            sentences = [f"{x}%" for x in sentences]
            params = [start_date_time, end_date_time] + sentences

            logging.info(f"sql = {sql}")
            logging.info(f"params = {params}")

            results = list(self._cursor.execute(sql, params))
            status = True

        except Exception as ex:

            msg = f"Error querying the sensors db: {ex}"
            logging.error(msg)
            self.errorReceived.emit(msg)

        return results

    def get_updated_event_data(self, datetime):
        """
        Method to retrieve new data for an event.  An event is a drop and this method is called when a user
        decides that the start or end time of a drop is incorrect and it needs to be updated.  This method
        will then find the appropriate sensor database that contains latitude, longitude, and depth information
        corresponding to this provided datetime
        :param datetime:
        :return:
        """
        if not datetime:
            return

        logging.info(f"new datetime for getting sensor data: {datetime}")

        status = False

        # Define the measurements that will be updated by the change in the event start/end time
        measurement_list = ["Latitude - Vessel", "Longitude - Vessel", "Depth"]
        values = {x: {} for x in measurement_list}

        # Get the parsing rules for these particular measurements, i.e. which sentences to retrieve from the sensors db
        measurements = ParsingRules.select(ParsingRules, Lookups) \
            .join(Lookups, on=(ParsingRules.measurement_lu == Lookups.lookup).alias('types')) \
            .where(Lookups.value << measurement_list)

        # Get a unique list of the sentences required to get the items listed in measurement_list
        sentences = []
        for measurement in measurements:
            # logging.info(f"measurement = {measurement.types.value} > {measurement.line_starting}")
            values[measurement.types.value]["sentence"] = measurement.line_starting
            values[measurement.types.value]["position"] = measurement.field_position
            if measurement.line_starting not in sentences:
                sentences.append(measurement.line_starting)

        """
        Find the relevant sensor database for the given datetime.  Remember, sensor databases are daily sqlite files
        with the naming convention sensors_YYYYMMDD.db, however, if someone has left HookLogger running for multiple
        days without shutting it down, the current sensor database could have a name from many days ago, i.e. when
        HookLoggger was last started.  I have actually corrected for this situation such that the database is
        shifted to a new one at midnight       
        """

        dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        data_path = os.path.join(dir, "data")

        db_search_str = r'sensors_.*\.(db)$'
        available_dbs = [f for f in os.listdir(data_path) if re.search(db_search_str, f)]
        available_dbs = sorted(available_dbs, reverse=True)

        date_of_interest = arrow.get(datetime).replace(hour=0, minute=0, second=0, tzinfo="US/Pacific")
        for file in available_dbs:

            current_day = arrow.get(file.strip("sensors_").strip(".db"), "YYYYMMDD").replace(tzinfo="US/Pacific")
            diff = current_day - date_of_interest
            logging.info(f"current_day = {current_day},   DOI = {date_of_interest}  >>>> diff.days = {diff.days}")
            if diff.days > 0:
                continue

            full_path = os.path.join(dir, "data", file)
            self._database_path = full_path
            self._conn = sqlite.Connection(self._database_path)
            self._conn.setbusytimeout(10000)
            self._cursor = self._conn.cursor()

            # Query the current sensor database for the sentences listed in sentences
            results = self.query_by_datetime(datetime=datetime, sentences=sentences)
            logging.info(f"results count = {len(results)}")
            if results:
                results = [x[1] for x in results]       #  only need the sentences from the results

                # Populate values to be returned
                for k, v in values.items():
                    result = [x for x in results if v["sentence"] in x]
                    if len(result) > 0:
                        logging.info(f"{k} > {result[0]}")
                        fields = result[0].split(",")
                        v["text value"] = fields[v["position"] - 1]
                        if k in ["Latitude - Vessel", "Longitude - Vessel"]:
                            v["hemisphere"] = fields[v["position"]]
                            v["value"] = self._dc.gps_lat_or_lon_to_dd(value_str=v["text value"],
                                                                       hemispshere=v["hemisphere"])
                        else:
                            v["value"] = float(v["text value"])

                status = True
                break

        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()

        return status, values
