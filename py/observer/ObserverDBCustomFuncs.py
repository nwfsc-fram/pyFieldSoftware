
"""
-----------------------------------------------------------------------------
Name:        ObserverDBCustomFuncs.py
Purpose:     Load custom functions into SQLite db ORM

Author:      Jim Fellows <james.fellows@noaa.gov>

Created:     Sept. 10th 2020
License:     MIT

To add new function, add static method to ObserverDBCustomFuncs
with _udf appended to method name
------------------------------------------------------------------------------
"""

import logging
import arrow
import inspect
from py.observer.ObserverDBBaseModel import database
from py.observer.ObserverDBUtil import ObserverDBUtil

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
    def get_sqlite_date_str_udf(date_str):
        """
        assumes date str will follow pattern: 'MM/DD/YYYY HH:mm'
        :param date_str: 'MM/DD/YYYY HH:mm'
        :return: 'YYYY-MM-DD HH:mm'
        """
        return arrow.get(date_str, SQLITE_DATE_STR).format('YYYY-MM-DD HH:mm')


# if __name__ == '__main__':
#     ocf = ObserverDBCustomFuncs()
#     # test_date_str = '12/30/2019 09:08'
#     # print(type(arrow.get(test_date_str, 'MM/DD/YYYY HH:mm').format('YYYY-MM-DD HH:mm')))
#     ocf.register_funcs()
#     result = database.execute_sql("select get_iso_date_str('12/30/2019 09:08')")
#     for r in result:
#         print(r)
#     # print(len(inspect.signature(ocf.add_one_udf).parameters))
