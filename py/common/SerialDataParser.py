__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        SerialDataParser
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Mar 16, 2016
# License:     MIT
#-------------------------------------------------------------------------------
import logging


class SerialDataParser:
    """
    Class used to parse serial data.  This started with the new trawl survey backdeck software, but will be
    adapted for the trawl wheelhouse sofwtare as well
    """

    def __init__(self, rule=None, equipment_id=None, measurement_type_id=None, **kwargs):
        super().__init__()

        self.rule = rule
        self.equipment_id = equipment_id
        self.measurement_type_id = measurement_type_id



if __name__ == '__main__':

    SerialDataParser()
