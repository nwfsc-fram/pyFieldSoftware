__author__ = 'Todd.Hay'
# -------------------------------------------------------------------------------
# Name:        TrawlBackdeckDB.py
# Purpose:     Provides connection to the trawl_backdeck.db SQLite database

# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 08, 2016
# License:     MIT
#-------------------------------------------------------------------------------
import unittest

from py.common import CommonDB


class TrawlBackdeckDB(CommonDB.CommonDB):
    """
    Subclass the CommonDB class, which makes the actual database connection
    """
    def __init__(self, db_filename="trawl_backdeck.db"):
        super().__init__(db_filename)


class TestTrawlBackdeckDB(unittest.TestCase):
    """
    Test basic SQLite connectivity
    """

    def setUp(self):
        self._db = TrawlBackdeckDB('trawl_backdeck.db')

    def tearDown(self):
        self._db.disconnect()

    def test_query(self):
        count = 0
        for t in self._db.execute('SELECT * FROM HAULS'):
            count += 1
        self.assertGreater(count, 200)

if __name__ == '__main__':
    unittest.main()
