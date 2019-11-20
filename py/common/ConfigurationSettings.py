__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        ConfigurationSettings.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 31, 2016
# License:     MIT
#-------------------------------------------------------------------------------
import logging
import unittest


class ConfigurationSettings:
    """


    """
    def __init__(self, db=None, **kwargs):

        super().__init__(**kwargs)
        self._db = db
        self.settings = self._get_configuration_settings()

    def _get_configuration_settings(self):
        """
        Method to get "sticky" configuration parameters to populate initial widgets upon loading.
        SELECT * FROM CONFIGURATION_SETTINGS

        :return: dict - configuration settings
        """
        sql = 'SELECT parameter, value FROM CONFIGURATION_SETTINGS WHERE IS_ACTIVE = "True" ORDER BY parameter'
        results = self._db.execute(query=sql)
        if len(results) > 0:
            return dict([(x[0], x[1]) for x in results])
        else:
            return {}

    def update(self):
        """
        Method to update configuration settings
        :return:
        """

class TestConfigSettings:
    pass

if __name__ == '__main__':

    c = ConfigurationSettings()
    for s in c.settings:
        logging.info('setting: ' + s)
