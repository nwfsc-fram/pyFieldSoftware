__author__ = 'Will.Smith'
# -----------------------------------------------------------------------------
# Name:        CommonDB.py
# Purpose:     Generic Common Database Routines for PyQt5 Framework
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 4, 2016
# License:     MIT
# ------------------------------------------------------------------------------


import os
import logging
import apsw


class CommonDB:
    def __init__(self, db_filename):
        self._logger = logging.getLogger(__name__)
        self._logger.debug('APSW version ' + apsw.apswversion())
        self._logger.debug('SQLite version ' + apsw.sqlitelibversion())
        self._conn = None
        self._connect_to_db(db_filename)

    def connect(self, db_filename):
        self._connect_to_db(db_filename)

    def _connect_to_db(self, db_filename):
        """
        Method to connect to the sensors.db SQLite database and provide both a connection and a cursor instance
        :param db_filename: Bare filename, e.g. observer.db
       """
        # logger = logging.getLogger('__main__')
        if os.path.exists(os.path.join(os.getcwd(), '../data/' + db_filename)):
            path = '../data'
        elif os.path.exists(os.path.join(os.getcwd(), 'data/' + db_filename)):
            path = 'data'
        elif os.path.exists(os.path.join(os.getcwd(), '../../data/' + db_filename)):
            path = '../../data'  # Unit tests
        else:
            errmsg = 'Error locating database ' + db_filename
            self._logger.error(errmsg)
            raise FileNotFoundError(errmsg)

        db = os.path.join(path, db_filename)
        self._conn = apsw.Connection(db)
        self._conn.setbusytimeout(10000)
        cursor = self._conn.cursor()
        if self._conn is not None and cursor is not None:
            self._logger.info('Connected to ' + db_filename)
        else:
            self._logger.error('Error connecting to ' + db_filename)

    def disconnect(self):
        self._disconnect_from_db()

    def _disconnect_from_db(self):
        """
        Method to disconnect from the SQLite database
        :return:
        """
        self._logger.info('Disconnecting from database')
        if self._conn is not None:
            self._conn.close()
        else:
            self._logger.warn('Closing nonexistent DB connection.')

    @property
    def connection(self):
        return self._conn

    # def execute(self, query):
    #     cursor = self._conn.cursor()
    #     return cursor.execute(query)

    def execute(self, query, parameters=None):
        """
        Method to execute a query that includes the SQL query and separately the parameters to prevent SQL injection attacks
        :param query: SQL string that has been parameterized
        :param parameters: Parameters as a python list
        :return: resultset from the query, as a python list
        """
        cursor = self._conn.cursor()
        if parameters is not None:
            return cursor.execute(query, parameters)
        else:
            return cursor.execute(query)

    def get_last_rowid(self):
        """
        Method to return the rowid of the last row that was inserted
        :return: int - last rowid inserted
        """
        return self._conn.last_insert_rowid()