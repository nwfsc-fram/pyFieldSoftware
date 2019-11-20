# -----------------------------------------------------------------------------
# Name:        ObserverErrorReportModels.py
# Purpose:     View Models for tables on Error Reports screen
#               - TripIssuesModel: FramListModel (view model) for tripIssuesTable on screen,
#                   presenting mostly data from the TRIP_ISSUES table in Observer DB.
#               - TripErrorReportsModel: FramListModel (view model) for tripsTables on
#                   Error Reports screen, presenting data from Trips and TripIssues Observer tables.
#
# Author:      Jim Stearns <james.stearns@noaa.gov>
#
# Created:     10 March 2017
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtSignal
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from playhouse.shortcuts import model_to_dict
from py.observer.ObserverDBModels import Trips, Users
# Table created in OPTECS, not sync'ed from IFQ* DB:
from py.observer.ObserverDBErrorReportsModels import TripIssues

# For Unit Tests only
import logging
import unittest
from py.observer.ObserverDBModels import TripChecks


class TripIssuesModel(FramListModel):
    modelChanged = pyqtSignal()

    def __init__(self, parent=None):
        """
        Sort role is actually three sort keys: haul, then catch, then trip check.
        :param parent:
        """
        super().__init__(parent)

        for role_name in self.model_rolenames:
            self.add_role_name(role_name)

    @property
    def model_rolenames(self):
        """
        :return: role names for FramListModel
        """
        rolenames = FramUtil.get_model_props(TripIssues)
        # Add additional roles (e.g. trip check id, to be acquired via FK)
        rolenames.append('check_message')  # TripChecks.check_message on FK TripIssues.trip_check
        rolenames.append('check_type')  # TripChecks.check_type on FK TripIssues.trip_check
        return rolenames

    def _get_integer_key(self, field_value):
        """
        Used by the sort method to convert None to a zero.
        :param field_value: an integer, a string of integer digits, or None
        :return field_value as integer if not None else 0
        """
        return 0 if field_value is None else int(field_value)

    def _combined_trip_issue_key(self, row):
        """
        Primary key:    'fishing_activity_num' (aka haul)
        Secondary key:  'catch_num'
        Tertiary key:   'trip_check'

        Assumptions:
        - All are non-negative integer fields, but first two can be None (convert to 0)
        - Haul and catch numbers won't exceed 127 - can fit in a byte
        - Trip check number won't exceed 32K
        """
        haul = self._get_integer_key(row['fishing_activity_num'])
        catch = self._get_integer_key(row['catch_num'])
        trip_check = self._get_integer_key(row['trip_check'])

        combined_key = ((haul & 0xff) << 24) | ((catch & 0xff) << 16) | (trip_check & 0xffff)
        # self._logger.debug(
        #       f'{combined_key:x} from Haul={haul}, Catch={catch}, TripCheck={trip_check}')
        return int(combined_key)

    def _sort_trip_issues(self):
        """
        Sort the list of trip issues in place, using three levels of key:
        #1: Haul number - treat as integer (cast None to 0)
        #2: Catch number - treat as integer (cast None to 0)
        #3: Trip Check number - treat as integer (should not be None)
        """
        try:
            sorted_items = sorted(self._data_items, key=self._combined_trip_issue_key)
            self.setItems(sorted_items)
        except Exception as e:
            self._logger.error(f'Caught exception: {e}')

    def add_trip_issue(self, db_model):
        """
        :param db_model: peewee model (table instance) created elsewhere
        :return: FramListModel index of new trip issue (int)
        """
        try:
            new_issue = self._get_model_as_dict(db_model)

            newidx = self.appendItem(new_issue)
            self._logger.debug(f"Added Trip Check ID {db_model.trip_check.trip_check} for Trip #"
                              f"{db_model.trip.trip} at TripIssueModel Index #{newidx}.")

            # Sort first by haul, then catch, then trip check number
            self._sort_trip_issues()

            self.modelChanged.emit()
            return newidx

        except ValueError as e:
            self._logger.error('Error adding new trip issue: {}'.format(e))
            return -1

    def _get_model_as_dict(self, db_model):
        """
        Build a dict that matches TripIssues out of a peewee model
        Purpose is for providing values in the peewee model to the FramListModel view model.
        :param db_model: peewee model to convert
        :return: dict with values translated as desired to be FramListModel friendly
        """
        issue_dict = model_to_dict(db_model)

        # The values for the foreign keys trip and trip_check are references to dictionaries of
        # other peewee model instances. Convert (simplify) for the view model these two values to
        # the respective IDs,which are the intended values to be displayed.
        issue_dict['trip'] = issue_dict['trip']['trip']
        issue_dict['trip_check'] = issue_dict['trip_check']['trip_check']

        # Add other fields from tables other than TripIssues.
        issue_dict['check_message'] = db_model.trip_check.check_message
        issue_dict['check_type'] = db_model.trip_check.check_type

        # Display the user name rather than the user ID.
        # Keep it short: first name plus first char of second
        try:
            user_entry = Users.get(Users.user == issue_dict['created_by'])
            user_name = user_entry.first_name + user_entry.last_name[0]
        except Users.DoesNotExist:
            user_name = issue_dict['created_by']  # Shouldn't happen; if it does, use the user ID.
        issue_dict['created_by'] = user_name

        return issue_dict


class TripErrorReportsModel(FramListModel):
    """
     TripErrorReportsModel: FramListModel (view model) for tripsTables on Error Reports screen,
     presenting data from Trips and TripIssues Observer tables.
    """
    modelChanged = pyqtSignal()

    def __init__(self, parent=None, sort_role='trip', sort_reverse=True):
        super().__init__(parent)

        self._sort_role = sort_role
        self._sort_reverse = sort_reverse

        for role_name in self.model_rolenames:
            self.add_role_name(role_name)

    @property
    def model_rolenames(self):
        """
        Define "roles" (fields) for each of the TableViewColumns in tripsTables.
        :return: role names for FramListModel
        """
        rolenames = [
            'trip',            # Trip ID from the set of trip issues of interest
            'completed',       # Is trip completed. Only relevant in debriefer mode
            'program',         # Lookup: TripIssues.Trip to Trips.program to Programs.program_name
            'vessel',          # Lookup: TripIssues.Trip to Trips.vessel to Vessels.vessel_name
            'observer',        # Lookup: Use TripIssues.created_by to Users.user, then firstname and lastname initial
            'n_errors',        # Calculation: # of issues in this set of trip issues of interest
            'last_run_date',   # Created_date from the set of trip issues of interest
        ]
        return rolenames

    def _get_observer_abbrev(self, created_by: int) -> str:
        """
        Look up a user in Users using the created_by field and
        return first name plus last name initial

        :param created_by: User.user primary key value
        :return: First name concatenated with first letter of last name.
        """
        user_abbrev: str = ""
        try:
            user_entry = Users.get(Users.user == created_by)
            user_abbrev = user_entry.first_name + user_entry.last_name[0]
        except Users.DoesNotExist:
            user_abbrev = created_by  # Shouldn't happen; if it does, use the user ID.

        return user_abbrev

    def add_trip_ter(self, trip_ter_dict):
        """
        Load the key/value pairs into the view model; key is the field name, value is its value.
        One customization: if last_run_date is None or "", replace with "(TER not yet run)"
        :param trip_ter_dict: dictionary of values to be loaded.
            Not a peewee model because values come from multiple tables
        :return: FramListModel index of new trip issue (int)
        """

        try:
            if not trip_ter_dict['last_run_date']:
                trip_ter_dict['last_run_date'] = '(TER not yet run)'
            trip_ter_dict['observer'] = self._get_observer_abbrev(trip_ter_dict['created_by'])
            trip_ter_dict['completed'] = '*' if trip_ter_dict['is_completed'] else ''
            newidx = self.appendItem(trip_ter_dict)
            self._logger.info(
                    f"Added Trip #{trip_ter_dict['trip']} at TripIssueModel Index #{newidx}.")

            # Sort in descending order. Most recent trip is highest number,
            # and likely the most interesting.
            if self._sort_reverse:
                self.sort_reverse(self._sort_role)
            else:
                self.sort(self._sort_role)

            self.modelChanged.emit()
            return newidx

        except ValueError as e:
            self._logger.error('Error adding new trip issue: {}'.format(e))
            return -1


class TestTripIssuesModel(unittest.TestCase):

    def setUp(self):
        log_fmt = '%(levelname)s:%(filename)s:%(lineno)s:%(message)s'
        logging.basicConfig(level=logging.DEBUG, format=log_fmt)
        self.logger = logging.getLogger()
        """
        # Log messages to a queue
        self.logging_queue = LoggingQueue()
        q_handler = logging.handlers.QueueHandler(self.logging_queue)
        self.logger.addHandler(q_handler)
        """

        # Shut up peewee
        logger = logging.getLogger('peewee')
        logger.setLevel(logging.WARNING)

        self.testmodel = TripIssuesModel()

    def add_test_row(self, test_data):
        """ Creating test data is complicated by the expected input type of
            a peewee database table type, TripIssues, which has two foreign keys:
            Trips and TripChecks.
        """
        trip_issue = TripIssues()
        # Put the expected index of each row, after sorting, in its trip issues field
        trip_issue.trip_issue = test_data['expordnum']
        trip_issue.fishing_activity_num = int(test_data['haul']) if test_data['haul'] else None
        trip_issue.catch_num = int(test_data['catch']) if test_data['catch'] else None
        trip = Trips()
        trip.trip = 1
        trip_check = TripChecks()
        trip_check.trip_check = int(test_data['trip_check'])

        trip_issue.trip = trip
        trip_issue.trip_check = trip_check

        self.testmodel.add_trip_issue(trip_issue)
        # self.logger.debug(f'Added TripIssue with expected output index = {trip_issue.trip_issue}')

    def test_sort(self):
        """
        Test sorting with up to three levels of sort key.
        Test that None values are handled. (should be mapped to empty string for sorting).
        :return:
        """
        # Test data with some blank (empty) fields.
        # Sort Keys: haul (primary), then catch, then trip_check
        # 'expordnum' is a test convenience: expected order number of row after sorting.
        testing_data = [
            {'haul': '1', 'catch': '1', 'trip_check': '1111', 'expordnum': 3},
            {'haul': None, 'catch': None, 'trip_check': '2222', 'expordnum': 0},
            {'haul': '2', 'catch': '2', 'trip_check': '6666', 'expordnum': 5},
            {'haul': '2', 'catch': '1', 'trip_check': '3333', 'expordnum': 4},
            {'haul': '4', 'catch': None, 'trip_check': '7777', 'expordnum': 6},
            {'haul': None, 'catch': None, 'trip_check': '5555', 'expordnum': 2},
            {'haul': None, 'catch': None, 'trip_check': '4444', 'expordnum': 1},
        ]

        for row in testing_data:
            self.add_test_row(row)

        actordnum = []
        expordnum = []
        for i in range(self.testmodel.count):
            expordnum.append(i)
            actordnum.append(self.testmodel.get(i)['trip_issue'])

        self.assertEqual(expordnum, actordnum)


if __name__ == '__main__':
    unittest.main()
