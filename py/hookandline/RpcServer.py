#-------------------------------------------------------------------------------
# Name:        RpcServer
# Purpose:
#
# Author:      Todd Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Oct 23, 2014
# License:     New BSD
#-------------------------------------------------------------------------------

from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from xmlrpc.client import Binary

# Testing purposes
import xmlrpc.client as xrc
import multiprocessing as mp
import time
import logging

import types
import apsw as sqlite
import os
import sys
import socket
import shutil

from PyQt5.QtCore import QObject, QVariant, pyqtProperty, pyqtSlot, pyqtSignal

DB_NAME = "hookandline_fpc.db"


def get_fpc_ip(db_addresses):
    """
    Method to grab the FPC IP address to determine if it's a legitimate 192.254... IP or just localhost, 127.0.0.1
    :param db_addresses:
    :return:
    """
    ip_address = socket.gethostbyname(socket.gethostname())
    ip_octets = ip_address.split('.')
    db_octets = db_addresses["FPC IP Address"].split('.')
    if ip_octets[0] == db_octets[0] and ip_octets[1] == db_octets[1]:
        hostname = db_addresses["FPC IP Address"]
    elif "Test FPC IP Address" in db_addresses:
        hostname = db_addresses["Test FPC IP Address"]
    else:
        hostname = ip_address

    return hostname


# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


class ThreadedRpcServer(SimpleXMLRPCServer, ThreadingMixIn):

    # pass
    def __init__(self):

        # super(ThreadedRpcServer, self).__init__()
        self.conn = None
        self.cursor = None
        self.datastrings_conn = None
        self.datastrings_cursor = None
        self.sensorsdb_name = None
        self.sensorsdb_path = None
        self.ext_wheelhouse_db_alias = 'extwheelhousedb'

        if os.path.exists(os.path.join(os.getcwd(), '../data', DB_NAME)):
            db_root_path = '../data'
        elif os.path.exists(os.path.join(os.getcwd(), 'data', DB_NAME)):
            db_root_path = 'data'
        else:
            logging.info(f"RpcServer: error connecting to the database")
            return

        db_full_path = os.path.join(db_root_path, DB_NAME)

        self.conn = sqlite.Connection(db_full_path)
        self.conn.setbusytimeout(5000)
        self.cursor = self.conn.cursor()

        sql = """
            SELECT PARAMETER, VALUE FROM SETTINGS
            WHERE PARAMETER IN ('FPC IP Address', 'Test FPC IP Address');
            """
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        db_addresses = {}
        if results:
            db_addresses = {x[0]: x[1] for x in results}

        self._hostname = get_fpc_ip(db_addresses)
        logging.info(f"RpcServer: IP Address: {self._hostname}")

        self._port = 9000
        SimpleXMLRPCServer.__init__(self, addr=(self._hostname, self._port),
                                         requestHandler=RequestHandler,
                                         logRequests=False,
                                         allow_none=True,
                                         use_builtin_types=True)

        # self.connect_sensor_db(db_root_path, db_wheelhouse_path=db_full_path)

    def _create_opseg_db_table(self, db_cursor, alias):
        """
        Create table OPERATIONAL_SEGMENT_DB_FILES if it doesn't exist
        :param cursor: database cursor
        :param alias: externally attached wheelhouse DB
        """

        try:
            sql = 'CREATE TABLE IF NOT EXISTS "{0}"."OPERATIONAL_SEGMENT_DB_FILES" ('.format(alias) + \
                  """
                  "ID"  INTEGER NOT NULL,
                  "SEGMENT_ID"  INTEGER,
                  "SENSORS_DB"  TEXT,
                  PRIMARY KEY ("ID" ASC),
                  CONSTRAINT "fkOPSEG_ID" FOREIGN KEY ("SEGMENT_ID") REFERENCES "OPERATIONAL_SEGMENT" ("OPERATIONAL_SEGMENT_ID"));
                  """
            db_cursor.execute(sql)
            Logger.info('_create_opseg_db_table: Created OPERATIONAL_SEGMENT_DB')
        except sqlite.SQLError as e:
            Logger.error('_create_opseg_db_table: Create OPERATIONAL_SEGMENT_DB {0}'.format(e))

    def connect_sensor_db(self, db_root_path, db_wheelhouse_path):
        if self.datastrings_conn is not None:
            self.datastrings_conn.close()  # Close existing connection if it exists

        clean_db_path = os.path.join(db_root_path, 'clean_sensors.db')
        if not os.path.isfile(clean_db_path):
            errmsg = 'Could not find clean sensors DB file to copy: ' + clean_db_path
            Logger.error(errmsg)
            raise FileNotFoundError(errmsg)

        self.sensorsdb_name = generate_sensordb_name()
        self.sensorsdb_path = os.path.join(db_root_path, self.sensorsdb_name)
        if not os.path.isfile(self.sensorsdb_path):
            Logger.info('Copying {0} to {1}.'.format(clean_db_path, self.sensorsdb_path))
            shutil.copyfile(clean_db_path, self.sensorsdb_path)
        else:
            Logger.info('Found sensors DB ' + self.sensorsdb_path)

        self.datastrings_conn = sqlite.Connection(self.sensorsdb_path)
        self.datastrings_conn.setbusytimeout(5000)
        self.datastrings_cursor = self.datastrings_conn.cursor()

        # Connect wheelhouse DB externally
        try:
            sql = "ATTACH DATABASE '" + db_wheelhouse_path + "' As '{0}';".format(self.ext_wheelhouse_db_alias)
            self.datastrings_cursor.execute(sql)
            self._create_opseg_db_table(db_cursor=self.datastrings_cursor, alias=self.ext_wheelhouse_db_alias)
        except Exception as ex:
            Logger.error('connect_sensor_db: Could not attach ' + db_wheelhouse_path + ' externally.')


# class RpcServer(ThreadingMixIn, SimpleXMLRPCServer):
class RpcServer(QObject):

    speciesChanged = pyqtSignal(str, str, str, arguments=['station', 'set_id', 'adh'])

    def __init__(self, *args, **kwargs):

        super().__init__()

        self._is_started = False

        if "queue" in kwargs:
            self._queue = kwargs["queue"]

        self._server = ThreadedRpcServer()

        self._register_functions()
        self._server.register_introspection_functions()

        # Run the server's main loop
        # self._server.serve_forever()

    def _register_functions(self):

        def get_table_column_count(db, tableName):

            cursor = self._server.cursor
            # cursor = self._get_cursor(db)
            columnsQuery = 'PRAGMA table_info(%s)' % tableName
            cursor.execute(columnsQuery)
            numberOfColumns = len(cursor.fetchall())
            return numberOfColumns

        self._server.register_function(get_table_column_count, 'get_table_column_count')

        def get_server_path():

            return os.path.abspath(__file__)

        self._server.register_function(get_server_path, 'get_server_path')

        def get_server_cwd():

            return os.getcwd()

        self._server.register_function(get_server_cwd, 'get_server_cwd')

        def get_last_row_id(db='wheelhouse'):

            if db == 'datastrings':
                conn = self._server.datastrings_conn
            else:
                conn = self._server.conn
            return conn.last_insert_rowid()

        self._server.register_function(get_last_row_id, 'get_last_row_id')

        def execute_many_query(db='wheelhouse', sql=None, params=None):

            if db == 'datastrings':
                cursor = self._server.datastrings_cursor
            else:
                cursor = self._server.cursor

            # Get the string out of the binary data that was sent
            if type(sql) is bytes:
                sql = sql.decode('utf-8')

            if params is None:
                cursor.executemany(sql)
            else:
                # Subsets of the params are binary elements, need to convert them
                if type(params) is bytes:
                    params = params.decode('utf-8')
                cursor.executemany(sql, params)

            results = cursor.fetchall()

            # NMEA RawData Issue - replace all of the RawData columns (i.e. the last column)
            #   to Binary format for transfer back to the client as they data
            #   that is not compatible with XML
            # Pass everything back as binary - prevents problem with NMEA raw data, ints, and other
            #   non-string/buffer data types
            if results is None:
                results = []

            else:
                for row in results:
                    row = [x.encode('utf-8') if isinstance(x, bytes) else x for x in row]

            return results

        self._server.register_function(execute_many_query, 'execute_many_query')

        def insert_many_query(db='wheelhouse', sql=None, params=None):

            if db == 'datastrings':
                cursor = self._server.datastrings_cursor
            else:
                cursor = self._server.cursor

            # Get the string out of the binary data that was sent
            if type(sql) is bytes:
                sql = sql.decode('utf-8')

            if params is None:
                cursor.executemany(sql)
            else:
                # Subsets of the params are binary elements, need to convert them
                if type(params) is bytes:
                    params = params.decode('utf-8')
                cursor.executemany(sql, params)
        #
        # with self._app.settings._database.atomic():
        #     # OperationMeasurements.insert_many(insert_list).execute()
        #
        #     for idx in range(0, len(insert_list), 5000):
        #
        #         if not self._is_running:
        #             raise BreakIt
        #
        #         OperationMeasurements.insert_many(insert_list[idx:idx + 5000]).execute()

        self._server.register_function(insert_many_query, 'insert_many_query')

        def execute_query_get_id(db='wheelhouse', sql=None, params=None, notify=None):

            results = execute_query(db=db, sql=sql, params=params, notify=notify)
            # conn = self._get_conn(db)
            if db == 'datastrings':
                return self._server.datastrings_conn.last_insert_rowid()
            else:
                return self._server.conn.last_insert_rowid()

        self._server.register_function(execute_query_get_id, 'execute_query_get_id')

        def set_sensor_db_filename(operational_id):
            sql = 'INSERT INTO OPERATIONAL_SEGMENT_DB_FILES(SEGMENT_ID, SENSORS_DB) ' \
                  'VALUES(?, ?);'
            params = (operational_id, self._server.sensorsdb_name)
            execute_query(sql=sql, params=params)

        self._server.register_function(set_sensor_db_filename, 'set_sensor_db_filename')

        def execute_query(db='fpc', sql=None, params=None, notify=None):

            if db == 'datastrings':
                cursor = self._server.datastrings_cursor
            else:
                cursor = self._server.cursor

            # Get the string out of the binary data that was sent
            if type(sql) is bytes:
                sql = sql.decode('utf-8')

            try:
                if params is None:
                    cursor.execute(sql)
                else:
                    # Subsets of the params are binary elements, need to convert them
                    if type(params) is bytes:
                        params = params.decode('utf-8')
                        # logging.info(f"just decoded a binary piece of data on the RpcServer")

                    cursor.execute(sql, params)

                results = cursor.fetchall()

            except Exception as ex:

                logging.error(f"Error in executing the query: {ex}")

            if notify and "speciesUpdate" in notify:

                # TODO - Todd - This notifies us that a species was updated, so need to emit
                # a signal for the SpeciesReviewDialog.qml to update itself with the latest information
                try:
                    station = notify["speciesUpdate"]["station"]
                    set_id = notify["speciesUpdate"]["set_id"]
                    adh = notify["speciesUpdate"]["adh"]
                    self.speciesChanged.emit(station, set_id, adh)
                except Exception as ex:
                    logging.error(f"Error attempting to signal the update for a species change: {ex}")


            # NMEA RawData Issue - replace all of the RawData columns (i.e. the last column)
            #   to Binary format for transfer back to the client as they data
            #   that is not compatible with XML
            # Pass everything back as binary - prevents problem with NMEA raw data, ints, and other
            #   non-string/buffer data types
            if results is None:
                results = []

            else:
                for row in results:
                    row = [x.encode('utf-8') if isinstance(x, bytes) else x for x in row]

            return results

        self._server.register_function(execute_query, 'execute_query')

        def get_hauls():
            """
            Method used by trawl_backdeck software to query for the daily haul information
            :param self:
            :return:
            """
            results = []
            sql_haul = """
                SELECT os.NAME AS HAUL_NUMBER, substr(os.NAME, -3) as HAUL_ID, wp.NAME AS WAYPOINT_NAME,
                    DATETIME(wp.DATE_TIME, 'localtime') AS DATE_TIME, wp.LATITUDE, wp.LONGITUDE,
                    IFNULL(wp.GEAR_DEPTH_M, wp.SOUNDER_DEPTH_FTM) AS DEPTH,
                    v.VESSEL_NAME,
                    (SELECT CASE v.VESSEL_NAME
                            WHEN "Excalibur" THEN "Orange"
                            WHEN "Last Straw" THEN "Blue"
                            WHEN "Noah\'s Ark" THEN "Blue"
                            WHEN "Ms. Julie" THEN "Orange"
                        END) AS VESSEL_COLOR,
                    (select substr('000' || v.VESSEL_ID, -3, 3)) AS VESSEL_ID
                FROM TOW_WAYPOINTS wp
                INNER JOIN OPERATIONAL_SEGMENT os ON wp.TOW_ID = os.OPERATIONAL_SEGMENT_ID
                INNER JOIN VESSEL_LU v ON os.VESSEL_ID = v.VESSEL_ID
                WHERE DATE(wp.DATE_TIME, 'localtime') = DATE('now','localtime')
            """

            sql_pass_leg = """
                WITH RECURSIVE parents(n) AS (
                    SELECT OPERATIONAL_SEGMENT_ID from OPERATIONAL_SEGMENT WHERE NAME IN (?)
                    UNION
                    SELECT o.PARENT_SEGMENT_ID FROM OPERATIONAL_SEGMENT o, parents
                    WHERE o.OPERATIONAL_SEGMENT_ID = parents.n
                )
                SELECT o.NAME, t.TYPE
                FROM OPERATIONAL_SEGMENT o
                INNER JOIN TYPES_LU t ON o.OPERATIONAL_SEGMENT_TYPE_ID = t.TYPE_ID
                WHERE OPERATIONAL_SEGMENT_ID IN parents AND
                    t.CATEGORY = "Operational Segment" AND
                    (t.TYPE = 'Leg' or t.TYPE = 'Pass')
            """
            cursor = self._server.cursor
            cursor.execute(sql_haul)
            items = cursor.fetchall()
            if items is not None:
                current_haul_number = -1
                for i, item in enumerate(items):

                    # Add the previous haul to results.  We know we're at a new haul when the haul_number changes from the last item
                    if current_haul_number != -1 and item[0] != current_haul_number:
                        # if "end_time" not in new_dict:
                        #     new_dict["end_time"] = new_dict["start_time"]
                        results.append(new_dict)

                    if item[2] in ["Start Haul", "Set Doors", "Doors Fully Out", "Begin Tow"]:
                        current_haul_number = item[0]
                        new_dict = dict()
                        new_dict["haul_number"] = item[0]
                        new_dict["haul_id"] = item[1]
                        new_dict["start_time"] = item[3]

                        # Convert latitude / longitude strings to proper floats
                        if item[4]:
                            try:
                                lat_deg, lat_min = item[4].split(' ')
                                lat_deg = float(lat_deg)
                                lat_min = float(lat_min)
                                if lat_deg < 0:
                                    lat_min = -lat_min

                                new_dict["latitude"] = lat_deg + (lat_min/60.0)
                            except Exception as ex:
                                Logger.info('failed to convert haul latitude to float values')
                                new_dict["latitude"] = 10000
                        if item[5]:
                            try:
                                lon_deg, lon_min = item[5].split(' ')
                                lon_deg = float(lon_deg)
                                lon_min = float(lon_min)
                                if lon_deg < 0:
                                    lon_min = -lon_min

                                new_dict["longitude"] = lon_deg + (lon_min / 60.0)
                            except Exception as ex:
                                Logger.info('failed to convert haul latitude to float values')
                                new_dict["longitude"] = 10000

                        new_dict["depth"] = item[6]
                        new_dict["vessel_name"] = item[7]
                        new_dict["vessel_color"] = item[8]
                        new_dict["vessel_id"] = item[9]

                        cursor.execute(sql_pass_leg, [new_dict["haul_number"],])
                        pass_leg = cursor.fetchall()
                        for element in pass_leg:
                            if element[1] == "Pass":
                                new_dict["pass"] = element[0]
                            elif element[1] == "Leg":
                                new_dict["leg"] = element[0]

                    # elif item[2] in ["Start Haulback", "Net Off Bottom", "Doors At Surface", "End Of Haul"] \
                    #     and item[0] == current_haul_number:
                    elif item[2] in ["Start Haulback", "Net Off Bottom"] \
                         and item[0] == current_haul_number:
                        new_dict["end_time"] = item[3]
                    # item = [x.encode('utf-8') if isinstance(x, bytes) else x for x in item]

                    # Need to add the latest haul to the results
                    if i == len(items)-1:
                        results.append(new_dict)

            return results

        self._server.register_function(get_hauls, 'get_hauls')

    def _get_cursor(self, dbName):

        if len(dbName.split('.')) == 1:
            dbName = dbName + '.db'

        if dbName in (DB_NAME):
            return self._sensorsCursor
        else:
            return None

    def _get_conn(self, db):

        if len(db.split('.')) == 1:
            db = db + '.db'

        if db in (DB_NAME):
            return self._sensorsConn
        else:
            return None

    def _connect_to_databases(self):

        if os.path.exists(os.path.join(os.getcwd(),'../data', DB_NAME)):
            path = '../data'
        elif os.path.exists(os.path.join(os.getcwd(),'data', DB_NAME)):
            path = 'data'
        else:
            print ('Error connecting to databases')
            return

        sensorsDb = os.path.join(path, DB_NAME)

        self._sensorsConn = sqlite.Connection(sensorsDb)
        self._sensorsCursor = self._sensorsConn.cursor()



    def start(self):
        """
        start the thread
        :return:
        """
        self._is_started = True

    def stop(self):
        """
        stop the thread
        :return:
        """
        self._is_started = False

    def run(self):
        """
        Method to start the RpcServer
        :return:
        """
        self._is_started = True
        while self._is_started:
            self._server.serve_forever()


class Launcher:

    def __init__(self):

        self._rpcServer = RpcServer()


if __name__ == "__main__":

    print('*************************\nRpcServer Startup\n**************************')
    start = time.clock()
    mp = mp.Process(target=RpcServer)
    mp.start()
    end = time.clock()
    print('Elapsed Time - RpcServer Startup: %.3f\n' % (end - start))
    time.sleep(1)

    hostname = '127.0.0.1'
    port = 9000
    server = xrc.ServerProxy('http://' + hostname + ':' + str(port),
                             allow_none=True,
                             use_builtin_types=True)

    print('*************************\nGetHauls\n**************************')
    start = time.clock()
    hauls = server.get_hauls()
    if hauls:
        print('count: ' + str(len(hauls)))
    for haul in hauls:
            # haul = [x.decode('utf-8') if isinstance(x, bytes) else x for x in haul]
        print(str(haul))
    end = time.clock()
    print('Elapsed Time - GetHauls: %.3f\n' % (end - start))

    # RpcServer - Shutdown
    print('*************************\nRpcServer Shutdown\n**************************')
    start = time.clock()
    try:
        mp.terminate()
    except:
        pass
    end = time.clock()
    print('Elapsed Time - RpcServer Shutdown: %.3f\n' % (end - start))
