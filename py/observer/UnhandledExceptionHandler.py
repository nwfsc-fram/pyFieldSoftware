# -----------------------------------------------------------------------------
# Name:        UnhandledExceptionHandler.py
# Purpose:     Handle Python's sys.excepthook for Observer: display and log
#               when an unhandled exception occurs.
#
# Author:      Jim Stearns <james.stearns@noaa.gov>
#
# Created:     22 March 2017
# License:     MIT
# ------------------------------------------------------------------------------

import os
import sys
import time
import traceback
from typing import List

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QMessageBox

from py.observer.ObserverConfig import optecs_version, max_text_size_trips_note_field,\
        max_text_size_unhandled_exception_comment


class UnhandledExceptionHandler:

    # Set these variables before hooking up optecs_excepthook, preferably by calling connect_to_system_excepthook()
    appstate = None
    log_filename_for_today = None
    logging = None
    module_setting_excepthook = None

    # Only one exception handling on one execution of OPTECS.
    # (Multiple exceptions are possible if multiple signal handlers each cause an exception. FIELD-1368).
    exception_has_been_handled = False

    @staticmethod
    def connect_to_system_excepthook(logging, log_filename_for_today, appstate,
                                     module_setting_excepthook ='observer_main'):
        """
        Utility method to save the context information needed by the exception handler,
        and to hook up the exception handler in this class to Python's sys.excepthook.

        :param logging:
        :param log_filename_for_today:
        :param appstate: application context. Used here for handling comment added to Trips.notes.
        :param module_setting_excepthook: name of module calling this method to establish exception hook.
        """

        # Store the constructor parameters in class (not instance) variables so they can be used in optecs_excepthook.
        UnhandledExceptionHandler.logging = logging
        UnhandledExceptionHandler.log_filename_for_today = log_filename_for_today
        UnhandledExceptionHandler.appstate = appstate
        UnhandledExceptionHandler.module_setting_excepthook = module_setting_excepthook

        sys.excepthook = UnhandledExceptionHandler.optecs_excepthook

        UnhandledExceptionHandler.exception_has_been_handled = False

    @staticmethod
    def optecs_excepthook(except_type, except_value, traceback_obj):
        """
        Function to log an unhandled exception, including its stack trace,
        to display a message box with a summary of the exception for the observer,
        and upon observer hitting OK, to exit OPTECS with a non-zero return value.

        Should be activated from main program by:
            UnhandledExceptionHandler.connect_to_system_excepthook

        Based upon https://riverbankcomputing.com/pipermail/pyqt/2009-May/022961.html

        Use class variable exception_has_been_handled to ensure only one exception message is written to comments.

        :param except_type:
        :param except_value:
        :param traceback_obj:
        :return:
        """
        # Define local variable short-hands for class variables used multiple times.
        logging = UnhandledExceptionHandler.logging
        log_filename_for_today = UnhandledExceptionHandler.log_filename_for_today

        logging.error(f"Caught an unhandled exception in {UnhandledExceptionHandler.module_setting_excepthook}.")
        error_ret_value = 1
        log_filepath = os.path.join(os.getcwd(), log_filename_for_today)
        notice_fmtstr = \
            """An unhandled exception occurred. Please report the problem.\n""" \
            """A log file has been written to "{}".\n\n"""
        notice = notice_fmtstr.format(log_filepath)
        version_info = f"OPTECS Version: {optecs_version}"
        time_string = time.strftime("Exception DateTime: %Y-%m-%d, %H:%M:%S")
        except_type_str = str(except_type)

        except_summary = f'Exception Summary: {except_type_str}: {except_value}'

        # First, to the log file, verbosely:
        try:
            logging.error(f"{time_string}")
            logging.error(f"{except_summary}")
            logging.error(f"Exception Trace:")
            logging.error("\n".join(traceback.format_tb(traceback_obj)))
            logging.error("\n".join(UnhandledExceptionHandler._format_local_variables_by_frame(traceback_obj)))
            logging.error(version_info)
        except IOError:
            pass

        # Only display dialog once. Only log to comment field once.
        if not UnhandledExceptionHandler.exception_has_been_handled:
            UnhandledExceptionHandler.exception_has_been_handled = True

            # Write as a concise trip comment so that db sync uploads the comment
            # so that we can detect the occurrence of the exception at NWFSC.
            exception_comment = UnhandledExceptionHandler._write_exception_as_trip_comment(
                    except_type_str, except_value, version_info)

            logging.error(exception_comment)
            # Now to a message box, very concisely, for the observer. No traceback.
            sections = [time_string, exception_comment, '\n', version_info, "\nHit OK to exit OPTECS"]
            window_msg = '\n'.join(sections)
            errorbox = QMessageBox()
            errorbox.setIcon(QMessageBox.Critical)
            errorbox.setText(str(notice) + str(window_msg))
            errorbox.exec_()

            # Tell PyQt to exit with an error value
            # noinspection PyCallByClass,PyArgumentList
            QCoreApplication.exit(returnCode=error_ret_value)

    @staticmethod
    def _write_exception_as_trip_comment(except_type_str, except_value, version_info):
        """

        :param except_type_str:
        :param except_value:
        :param version_info:
        :return: A possibly truncated comment
        """
        #
        # Format of the exception comment:
        # <header><user_appstate_datetime>:<exception type>//<exception description>//<version>//<log_filename><trailer>
        #
        # Example (split into multiple lines here):
        # --------------------- User jimstearns (UnhandledException) 03/21/2017 15:47  :
        #  <class 'py.observer.ObserverState.OptecsTestException'>//
        # Exception intentionally raised for testing purposes.//OPTECS Version: 0.1.2+4//observer_20170321.log
        #  ------------------
        # Line 1 is header prepended by OPTECS, as is the Line 4 trailer.

        # (Use the string UnhandledException to provide a fairly distinctive search string).
        distinctive_string_for_exception_comments = "UnhandledException"

        # Short-hands
        logging = UnhandledExceptionHandler.logging
        appstate = UnhandledExceptionHandler.appstate

        # Put in the comment itself: exception_type//exception_summary//optecs_version//log_filename (not path)
        # Double-slash chosen as delimiter because <CRLF> gets stripped and colon is used elsewhere as separator.
        trip_comment = '//'.join([except_type_str, str(except_value), version_info,
                                  UnhandledExceptionHandler.log_filename_for_today])

        return trip_comment

    @staticmethod
    def _format_local_variables_by_frame(tb: traceback) -> List[str]:
        """
        NOT YET IMPLEMENTED. DEFAULT VARIABLE DUMP IS BOTH TOO WIDE AND TOO SHALLOW.
        Too wide because it includes static information, like Peewee models.
        Too shallow because it doesn't dive into contexts such as appstate.

        TODO: Customize for logging the OPTECS data of interest to a crash analyzer.

        Starting with the innermost frame, build a list of strings describing the local variables for that frame.
        :param tb
        :return:
        """
        return ['']

        var_info = ['Locals by frame, innermost first:']
        frame = tb.tb_frame
        while frame:
            var_info.append(f'\tFrame {frame.f_code.co_name} in {frame.f_code.co_filename} at line {frame.f_lineno}')
            for key, value in frame.f_locals.items():
                # noinspection PyBroadException
                try:
                    var_info.append(f'\t\t{key:.30} = {value}')
                except:
                    var_info.append(f'\t\t{key:.30} = (Data read error)')
            frame = frame.f_back
        return var_info
