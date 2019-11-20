__author__ = ('Todd.Hay', 'David.Goldsmith')

# -------------------------------------------------------------------------------
# Name:        SeabirdReaders.py
# Purpose:     Classes to read, parse, and process data from SBE sensors'
#               output files
#
# Author:      Todd.Hay, David.Goldsmith
# Email:       Todd.Hay@noaa.gov
#
# Created:     May 10, 2015
# License:     New BSD
# -------------------------------------------------------------------------------
import os
import math
import time
# from functools import partial
from io import StringIO
from datetime import datetime, timedelta, timezone, tzinfo
from dateutil import parser, tz
# from pyCollector.Utilities import TimeConverter, get_iso_datetime
import arrow
import logging


from py.trawl_analyzer.CommonFunctions import CommonFunctions


class SeabirdReader(StringIO):

    # ToDo: refactor disk-file specific aspects into distinct methods,
    # or into methods of a derived class

    # __all__ = ['set_raw_content',
    #            'get_raw_content',
    #            'load_from_file',
    #            'validate_make_return_model',
    #            'get_iso_datetime',
    #           ]

    def __init__(self, filename=None, raw_content=None, **kwargs):
        super(SeabirdReader, self).__init__(**kwargs)

        # self.tc = TimeConverter() # need to call this before calling super for

        # if filename: # if filename is not None, assume self to be sourced from
                     # a disk file, e.g., a Sea-Bird-generated .hex or .cnv
            # self.filename = filename
        self._functions = CommonFunctions()
        self.filename = filename

        self.content_list = []
        if raw_content:
            self.raw_content = raw_content
        else:
            self.raw_content = self.load_from_file()

        # self.get_iso_datetime = partial(get_iso_datetime, time_converter=self.tc) \
        #     if hasattr(self, 'tc') \
        #     else None
        self.start_datetime = None
        self.end_datetime = None

    def set_raw_content(self, raw_content=None):
        """
        Method that sets the raw content for further processing.
        :return:
        """
        self.raw_content = raw_content

    def get_raw_content(self):
        """
        Method to return the raw_content.
        Example use: by SensorFileUploadScreen.py, when attempting to upload a
            new SBE file to the database
        :return:
        """
        return self.raw_content

    def load_from_file(self):
        """
        Method that loads the Seabird data from a file on disk
        :return:
        """
        if not self.filename:
            return

        if not os.path.exists(self.filename):
            return

        try:
            f = open(self.filename, 'r')
            raw_content = f.read()
            f.close()
            return raw_content
        except UnicodeDecodeError as ex:
            return None
        except Exception as ex:
            return None

    def validate_make_return_model(self, mak='sbe'):
        """
        Validate the make of the instrument that created the file,
        and extract and return said instrument's model number
        :return:
        """
        is_make = True
        name_count = 0
        span_count = 0
        for i, line in enumerate(self.raw_content.splitlines()):
            if i == 0:
                line = line.lower()
                if mak in line:# don't think the "'sea-bird' not in line.lower()," originally in this if, is necessary
                    model = line.split(mak)[1].split()[0]
                else:
                    is_make = False
                break

            if mak=='sbe' and '# name' in line:
                name_count += 1

            if mak=='sbe' and '# span' in line:
                span_count +=1

            if '*END*' in line:
                break

            if i == len(self.raw_content.splitlines()) - 1:
                is_make = False
                # return is_make

        if name_count != span_count:
            is_make = False

        if is_make:
            return mak + model if mak=='sbe' else mak
        else:
            return is_make


class SeabirdHEXreader(SeabirdReader):

    def __init__(self, filename=None, raw_content=None, **kwargs):
        super(SeabirdHEXreader, self).__init__(filename, raw_content, **kwargs)


class SeabirdCONreader(SeabirdReader):

    def __init__(self, filename=None, raw_content=None, **kwargs):
        super(SeabirdCONreader, self).__init__(filename, raw_content, **kwargs)


class SeabirdCNVreader(SeabirdReader):
    # ToDo: Generalize to robustly read any CNV file; presently, it's only
    #       tested on SBE39 cnv's

    # __all__ = ['parse_data',
    #            'get_temperature_and_depth',
    #            'get_start_datetime',
    #            'get_end_datetime'
    #            ]

    def __init__(self, filename=None, raw_content=None, **kwargs):
        # self.tc = TimeConverter() # need to call this before calling super for
                                  # correct assignment of get_iso_datetime
        super(SeabirdCNVreader, self).__init__(filename, raw_content, **kwargs)

    def parse_data(self, measurements=''):
        """
        Method to actually parse the data
        :return:
        """
        if not self.raw_content:
            return

        is_data = False
        is_first_data_line = True
        temp_col = -1
        pressure_col = -1
        depth_col = -1
        time_col = -1
        start_year = None
        data = []
        valid_columns = []

        temp_data = []
        depth_data = []

        for i, line in enumerate(self.raw_content.splitlines()):

            if is_data:
                # data row is detected, parse and add it to the data list
                items = line.split()

                # logging.info(f"date_time before: {items[time_col]}, {start_year}")
                date_time = self._functions.convert_julian_to_iso(julian_days=items[time_col], year=start_year)
                # logging.info(f"date_time after: {date_time}")

                # Capture the start_datetime of the data set
                if is_first_data_line:

                    self.start_datetime = parser.parse(date_time)
                    is_first_data_line = False

                # Capture the end_datetime of the data set - just keep getting the latest date_time as data exists
                # and we roll through the data
                if date_time:
                    self.end_datetime = parser.parse(date_time)

                if measurements == 'temperature' and time_col > -1 and temp_col > -1:
                    data.append([date_time, float(items[temp_col])])

                elif measurements == 'pressure' and time_col > -1 and pressure_col > -1:
                    data.append([date_time, float(items[pressure_col])])

                elif measurements == 'tempdepth' and \
                    time_col > -1 and \
                    temp_col > -1 and \
                    depth_col > -1:

                    # Format:  date-time, temperature, depth
                    data.append([date_time, float(items[temp_col]),
                                 float(items[depth_col])])

                    temp_data.append([date_time, float(items[temp_col])])
                    depth_data.append([date_time, float(items[depth_col])])

                else:
                    # if temp_col > -1 and time_col > -1 and pressure_col > -1:
                    row_items = [date_time]
                    for x in valid_columns:
                        if x > -1:
                            row_items += [float(items[x])]
                    data.append(row_items)
                    # print(row_items)
                    # data.append([date_time, float(items[temp_col]), float(items[pressure_col])])

            if "# name" in line:
                # # name indicates the column headers for the data
                key, value = line.split('=')
                col = int(key.strip('# name'))
                if 'temperature' in value.lower():
                    temp_col = col
                    valid_columns.append(temp_col)
                elif 'pressure' in value.lower():
                    pressure_col = col
                    valid_columns.append(pressure_col)
                elif 'depth' in value.lower():
                    depth_col = col
                    valid_columns.append(depth_col)
                elif 'time' in value.lower():
                    time_col = col

            if '# start_time' in line:
                start_time = line.split('=')[1]
                start_date_time = parser.parse(start_time)
                start_year = start_date_time.strftime('%Y')
                # TODO Todd Hay - If the start year does not equal the year of the haul, then should use the haul
                # start date/time + span interval to increment the time count for each data line

                # print(start_date_time, start_year)

            if '*END*' in line:
                # Data starts on the next line
                is_data = True

        if measurements == 'tempdepth':
            self.parsed_results = {'temp_data': temp_data, 'depth_data': depth_data}
        else:
            self.parsed_results = data

    def get_temperature_and_depth(self):
        """
        Method to return the temperature and depth from an SBE CNV-like
        (Python) file-like object.  This is the standard call for SBE39's, e.g.
        :return:
        """
        if self.validate_make_return_model()=='sbe39':
            self.parse_data(measurements='tempdepth')

            # Reformat:
            sbe_dict = {}
            sbe_dict['Gear Temperature'] = {
                'format': 'C',
                'priority': 1,
                'equipment': 'SBE39',
                'file': 'SBE39',
                'data': self.parsed_results['temp_data']
            }
            sbe_dict['Gear Depth'] = {
                'format': 'M',
                'priority': 1,
                'equipment': 'SBE39',
                'file': 'SBE39',
                'data': self.parsed_results['depth_data']
            }

            return sbe_dict
        else:
            return {}

    def get_start_datetime(self):
        """
        Method to return the start datetime of the sensor file data
        :return:
        """
        if not self.start_datetime:
            self.parse_data(measurements='tempdepth')
        return self.start_datetime

    def get_end_datetime(self):
        """
        Method to return the end datetime of the sensor file data
        :return:
        """
        if not self.end_datetime:
            self.parse_data(measurements='tempdepth')
        return self.end_datetime


if __name__ == '__main__':

    folder = r'..\data\samples\Excalibur_General'
    file = r'Haul_201403008012\TrawlOps\seabird39_201403008012s.cnv'		# Includes Pressure
    file = r'Haul_201403008010\TrawlOps\seabird39_201403008010s.cnv'		# Includes Depth


    filename = os.path.join(folder, file)

    s = SeabirdCNVreader(filename=filename)
    # print('raw content:', s.get_raw_content())
    valid = s.validate_sensor_make()
    print('valid:', valid)

    # data = s.get_temperature()
    data = s.get_all_data()
    for x in data:
        print(x)

