#-------------------------------------------------------------------------------
# Name:        RpcClient
# Purpose:
#
# Author:      Todd Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Oct 24, 2014
# License:     New BSD
#-------------------------------------------------------------------------------
import xmlrpc.client as xrc
import time
import apsw


class RpcClient():

    def __init__(self):

        self._hostname = "127.0.0.1"
        self._port = 9000

        self.server = xrc.ServerProxy('http://' + self._hostname + ':' + str(self._port),
                                       allow_none=True,
                                       use_builtin_types=True)

        # TODO - Test that the server is actually operating, if not, close RpcClient
        if self.server is None:
            print('Server is not responding, closing')

    def execute_query_get_id(self, db='sensors', sql=None, params=None):

        if type(sql) is not bytes:
            sql = sql.encode('utf-8')

        if params is not None:
            params = [x.encode('utf-8') if isinstance(x, bytes) else x for x in params]

        try:
            return self.server.execute_query_get_id(db, sql, params)
        except apsw.BusyError as ex:
            print('Database is opened outside of PyCollector', ex)

    def execute_query(self, db='sensors', sql=None, params=None):

        if type(sql) is not bytes:
            sql = sql.encode('utf-8')

        if params is not None:
            # params = tuple([x if isinstance(x, str) else bytes(x, 'utf-8') for x in params])
            # params = tuple([bytes(x, 'utf-8') if isinstance(x, bytes) else x for x in params])
            # print(params)
            params = [x.encode('utf-8') if isinstance(x, bytes) else x for x in params]
            # print(params)

        results = []
        try:
            results = self.server.execute_query(db, sql, params)
        except apsw.BusyError as ex:
            print('Database is opened outside of PyCollector', ex)
        except Exception as ex:
            print('RpcClient.py, line 58 > execute_query > Exception:', ex)

        for row in results:
            row = [x.decode('utf-8') if isinstance(x, bytes) else x for x in row]
        # if type(results) is bytes:
        # 	results = results.decode('utf-8')

        return results

    def get_last_row_id(self, db='sensors'):

        return self.server.get_last_row_id(db)

    def get_table_column_count(self, db='sensors', table=None):

        if table is not None:
            return self.server.get_table_column_count(db, table)

    def test_queries(self):

        print('Testing the RpcClient')

        start = time.clock()

        # List RPC Server Functions
        print('\n\t1. Server Functions:\n\t\t', '\n\t\t'.join(self.server.system.listMethods()))

        # Miscellaneous Functions
        print('\n\t2. Miscellaneous Functions')
        print('\t\tget_server_path(): ', str(self.server.get_server_path()))
        print('\t\tget_server_cwd(): ', str(self.server.get_server_cwd()))
        print('\t\tget_table_column_count(): $SDDBT -> ',
              self.get_table_column_count('sensors', '"$SDDBT"'))

        # SELECT Query Example - No Parameters
        sql = 'SELECT * FROM "$SDDBT"'
        results = self.execute_query(db='sensors', sql=sql)
        sql = 'SELECT count(*) FROM "$SDDBT"'
        count = self.execute_query(db='sensors', sql=sql)

        print('\n\t3. SELECT Sample Query, No Parameters')
        print('\t\texecute_query(db=\'sensors\', sql=\'', sql, '\')', sep='')
        print('\t\tQuery Results Count: ', count[0][0], 'rows')
        print('\t\tQuery Results: ', results)
        print('\t\tQuery Individual Value [0][11]: ', results[0][11])

        # SELECT Query Example - With Parameters
        sql = 'SELECT * FROM "$SDDBT" WHERE SDDBT_ID > ? AND RawData LIKE ?' #SDDBT_ID = ?'
        # params = (30,)
        # params = (30, "$SDDBT")
        params = [30, "%$SDDBT%"]
        results = self.execute_query(db='sensors', sql=sql, params=params)
        sql = 'SELECT count(*) FROM "$SDDBT" WHERE SDDBT_ID > ? AND RawData LIKE ?' #SDDBT_ID = ?'
        count = self.execute_query(db='sensors', sql=sql, params=params)
        print('\n\t4. SELECT Sample Query, With Parameters')
        print('\t\texecute_query(db=\'sensors\', sql=\'', sql,
              '\', params=', params, ')', sep='')
        print('\t\tQuery Results Count: ', count[0][0], 'rows')
        print('\t\tQuery Results: ', results)
        if len(results) > 0:
            print('\t\tQuery Individual Value [0][11]: ', results[0][11])


        # INSERT Query Example - With Parameters
        sql = 'INSERT INTO EquipmentDeployment VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'

        startDate = time.strftime('%m/%d/%Y', time.localtime(time.time()))
        equipmentInstanceID = 123
        equipmentTypeID = 12

        params = (
            None,                    # EquipmentDeploymentID - NULL gives autoincrement for this PrimaryKey INT field
            '',                      # Cruise
            '2014',                  # Year
            'Excalibur',             # Vessel
            startDate,               # StartDate - Reformat as MM/DD/YY
            '',                      # EndDate
            '',                      # Name
            '',                      # Comment
            equipmentTypeID,         # EquipmentTypeID
            equipmentInstanceID,     # EquipmentInstanceID
            '',                      # MountPointID - necessary?
            '1',                     # ComPort
            '4800',                  # BitsPerSecond
            '8',                     # DataBits
            'None',                  # Parity
            '1',                     # StopBits
            'None'                   # FlowControl
        )

        end = time.clock()
        print('\nTime to Complete Queries: %.2gs' % (end - start))

        # **************************************************************************************************************
        # LEGACY CODE - From Python 2.7 PySide Prototyping effort - likely can remove once we're convinced that the
        #               binary data transport is handled properly
        # **************************************************************************************************************

        # Encode the SQL string as binary (for those NMEA sentences that have ASCII characters 0 -> 31)
        # Not necessary for generic string-based sql queries, will be required for NMEA sentence inserts however
        #  for the raw data column

        # Convert all str or subclasses of strings (i.e. unicode instances) to xmlrpclib.Binary
        # params = tuple([x if isinstance(x,basestring) else xrl.Binary(x) for x in params])

        # Converts only the str class (i.e. no subclasses to xmlrpclib.Binary)
        # params = (x if type(x) is str else xrl.Binary(x) for x in params)

        #sql = xrl.Binary(sql)
        #params = xrl.Binary(str(params))


# class Launcher():
#
# 	def __init__(self):
#
# 		self._rpcClient = RpcClient()


if __name__ == "__main__":

    client = RpcClient()
    # client.test_queries()