"""
-----------------------------------------------------------------------------
Name:        ObserverDBCustomFuncs.py
Purpose:     Load custom functions into SQLite db ORM

Author:      Jim Fellows <james.fellows@noaa.gov>
Created:     Sept. 10th 2020

To add new function, add static method to ObserverDBCustomFuncs
with _udf appended to method name.  Idea is to write equivalent functions
in Oracle's OBSPROD schema, so that two functions with the same name
can run logic specific to their environment, and produce the same result, for TER purposes

https://www.fisheries.noaa.gov/jira/browse/FIELD-2093
------------------------------------------------------------------------------
"""

import logging
import arrow
import inspect
from py.observer.ObserverDBBaseModel import database
from py.observer.ObserverDBUtil import ObserverDBUtil
from geopy.distance import geodesic

SQLITE_DATE_STR = ObserverDBUtil().default_dateformat  # current format being inserted to SQLite, used below


class ObserverDBCustomFuncs:
    """
    Class used to organize methods together
    No init setup at this time
    """
    def __init__(self):
        pass

    def register_funcs(self):
        """
        loop through _udf methods and register to db
        :return: None
        """
        log_list = []
        for m in self.get_funcs_to_register():
            name = m.replace('_udf', '')
            method_obj = getattr(self, m)
            param_ct = self.get_param_count(method_obj)
            database.register_function(method_obj, name, num_params=param_ct)
            log_list.append(name)
        logging.info(f'The following custom SQL functions are loaded: {str(log_list)}')

    def get_funcs_to_register(self):
        """
        loop through class methods with 'udf' in name
        :return: str[]
        """
        return [f for f in dir(self) if 'udf' in f]

    @staticmethod
    def get_param_count(method):
        """
        pass method/func, use inspect.signature to count func params
        :param method: method/function
        :return: int
        """
        return len(inspect.signature(method).parameters)

    @staticmethod
    def optecs_get_unixtime_udf(date_str):
        """
        Takes optecs date str and converts it to seconds since
        1970 (unix time).
        Mirrors OBSPROD.OPTECS_GET_SECONDS func
        :param date_str: str with format 'MM/DD/YYYY HH:mm' (see ObserverDBUtil)
        :return: int
        """
        try:
            return arrow.get(date_str, SQLITE_DATE_STR).timestamp
        except TypeError:
            logging.debug(f"Invalid date_str dtype: {type(date_str)}")
            return None
        except BaseException:
            logging.debug('Unknown function error, review parameters.')
            return None

    @staticmethod
    def optecs_get_year_udf(date_str):
        """
        Extract year int from optecs datestr
        :param date_str: str with format 'MM/DD/YYYY HH:mm' (see ObserverDBUtil)
        :return: int (YYYY)
        """
        try:
            return arrow.get(date_str, SQLITE_DATE_STR).year
        except TypeError:
            logging.debug(f"Invalid date_str dtype: {type(date_str)}")
            return None
        except BaseException:
            logging.debug('Unknown function error, review parameters.')
            return None

    @staticmethod
    def optecs_get_month_udf(date_str):
        """
        Extract month int from optecs datestr
        :param date_str: str with format 'MM/DD/YYYY HH:mm' (see ObserverDBUtil)
        :return: int (MM)
        """
        try:
            return arrow.get(date_str, SQLITE_DATE_STR).month
        except TypeError:
            logging.debug(f"Invalid date_str dtype: {type(date_str)}")
            return None
        except BaseException:
            logging.debug('Unknown function error, review parameters.')
            return None

    @staticmethod
    def optecs_get_day_udf(date_str):
        """
        Extract day int from optecs datestr
        :param date_str: str with format 'MM/DD/YYYY HH:mm' (see ObserverDBUtil)
        :return: int (DD)
        """
        try:
            return arrow.get(date_str, SQLITE_DATE_STR).day
        except TypeError:
            logging.debug(f"Invalid date_str dtype: {type(date_str)}")
            return None
        except BaseException:
            logging.debug('Unknown function error, review parameters.')
            return None

    @staticmethod
    def optecs_get_hour_udf(date_str):
        """
        Extract hour int from optecs datestr
        :param date_str: str with format 'MM/DD/YYYY HH:mm' (see ObserverDBUtil)
        :return: int (HR24)
        """
        try:
            return arrow.get(date_str, SQLITE_DATE_STR).hour
        except TypeError:
            logging.debug(f"Invalid date_str dtype: {type(date_str)}")
            return None
        except BaseException:
            logging.debug('Unknown function error, review parameters.')
            return None

    @staticmethod
    def optecs_parse_date_udf(date_str):
        """
        Takes optecs date str and converts it to a format
        that SQLite can recognize as a date
        Mirors function OBSPROD.OPTECS_PARSE_DATE
        :param date_str: str with format 'MM/DD/YYYY HH:mm' (see ObserverDBUtil)
        :return: str with format 'YYYY-MM-DD HH:mm' (see https://sqlite.org/lang_datefunc.html)
        """
        try:
            return arrow.get(date_str, SQLITE_DATE_STR).format('YYYY-MM-DD HH:mm')
        except TypeError:
            logging.debug(f"Invalid date_str dtype: {type(date_str)}")
            return None
        except BaseException:
            logging.debug('Unknown function error, review parameters.')
            return None

    @staticmethod
    def optecs_unix_to_datestr_udf(seconds, fmt):
        """
        parse unix time into string of choice format
        :param seconds: unix time, int
        :param fmt: string date format (e.g. 'YYYY-MM-DD HH:mm')
        :return: date string
        """
        try:
            return arrow.get(seconds).format(fmt)
        except arrow.parser.ParserError:
            logging.debug(f'Error with seconds arg, unable to parse val f{seconds}')
            return None
        except TypeError:
            logging.debug(f'Error with format arg, invalid type: f{type(fmt)}')
            return None
        except BaseException:
            logging.debug('Unknown function error, review parameters.')
            return None

    @staticmethod
    def optecs_get_distance_udf(lat1, lon1, lat2, lon2, um='mi', sr='WGS-84'):
        """
        Calc geodesic dist (mi) between two coordinates
        ellipsoid WGS-84 is default, but calling explicitly
        https://geopy.readthedocs.io/en/stable/#module-geopy.distance
        :param lat1: float (decimal degrees)
        :param lon1: float (decimal degrees)
        :param lat2: float (decimal degrees)
        :param lon2: float (decimal degrees)
        :param um: units str
        :param sr: spatial reference string
        :return: miles
        """
        try:
            if um.lower() == 'mi':
                return geodesic((lat1, lon1), (lat2, lon2), ellipsoid=sr).miles
            elif um.lower() == 'km':
                return geodesic((lat1, lon1), (lat2, lon2), ellipsoid=sr).km
            else:
                logging.debug(f'Invalid units:{um}; specify either mi or km')
                return None
        except ValueError:
            logging.debug(f'Invalid lat/lon vals:({lat1},{lon1}),({lat1},{lon1})')
            return None
        except BaseException:
            logging.debug('Unknown function error, review parameters.')
            return None

    @staticmethod
    def reformat_date_str_udf(date_str, old_format, new_format):
        """
        allows conversion from one date str to another
        :param date_str: str of date
        :param old_format: format of date_str
        :param new_format: new format e.g YYYY-MM-DD HH:mm
        :return: reformatted date str
        """
        return arrow.get(date_str, old_format).format(new_format)

# if __name__ == '__main__':
#     ocf = ObserverDBCustomFuncs()
#     # test_date_str = '12/30/2019 09:08'
#     # print(type(arrow.get(test_date_str, 'MM/DD/YYYY HH:mm').format('YYYY-MM-DD HH:mm')))
#     ocf.register_funcs()
#     result = database.execute_sql("select get_iso_date_str('12/30/2019 09:08')")
#     for r in result:
#         print(r)
#     # print(len(inspect.signature(ocf.add_one_udf).parameters))