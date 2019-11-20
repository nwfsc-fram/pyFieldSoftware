# -----------------------------------------------------------------------------
# Name:        ObserverUsers.py
# Purpose:     User info (programs & roles) and related model utilities
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Dec 2016
# License:     MIT
# ------------------------------------------------------------------------------
import logging

import arrow
from arrow.parser import ParserError
from peewee import fn

from PyQt5.QtCore import QStringListModel
from PyQt5.QtCore import pyqtProperty, QObject, pyqtSignal, QVariant, pyqtSlot

from py.observer.ObserverDBModels import Users, UserProgramRoles, ProgramRoles, Programs, Lookups, PasswordHistory
from py.observer.ObserverDBUtil import ObserverDBUtil
from py.observer.ObserverSOAP import ObserverSoap

import unittest


class ObserverUsers(QObject):
    user_changed = pyqtSignal(name='userChanged')
    current_user_is_debriefer_changed = pyqtSignal(name='userIsDebrieferChanged')
    currentUserPwExpiresChanged = pyqtSignal(name='currentUserPwExpiresChanged')
    program_model_changed = pyqtSignal(name='programModelChanged')
    fisheries_model_changed = pyqtSignal(name='fisheriesModelChanged')
    current_program_changed = pyqtSignal(name='currentProgramChanged')

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._current_user_info = {'username': None,
                                   'userid': None,
                                   'password': None,
                                   'roles': None}

        self._current_user_roles = []
        self._current_user_programs = QStringListModel()  # Programs available to this user
        self._current_fisheries = QStringListModel()  # Fisheries available to this user

        self._current_program = None
        self._is_fixed_gear = False

    @pyqtProperty(QVariant, notify=user_changed)
    def currentUserID(self):
        return self._current_user_info.get('userid', None)

    @pyqtProperty(QVariant, notify=user_changed)
    def currentUserName(self):
        return self._current_user_info.get('username', None)

    @pyqtProperty(QVariant, notify=user_changed)
    def currentUserPassword(self):
        return self._current_user_info.get('password', None)

    @pyqtProperty(bool, notify=current_user_is_debriefer_changed)
    def currentUserIsDebriefer(self):
        if not self._current_user_roles:
            return False
        allowed_debriefer_roles = ['Debriefer', 'System Admin']
        for allowed in allowed_debriefer_roles:
            if allowed in self._current_user_roles:
                return True
        return False

    @pyqtProperty(QVariant, notify=currentUserPwExpiresChanged)
    def currentUserPwExpires(self):
        user_id = self._current_user_info.get('userid', None)
        if user_id:
            exp_datestr = self._get_pw_expiry(user_id)
            try:
                expiry = arrow.get(exp_datestr, 'DD-MMM-YY')
            except ParserError:
                try:
                    expiry = arrow.get(exp_datestr, 'M/D/YYYY HH:mm:ss')  # '3/6/2017 21:27:59'
                except ParserError:
                    try:
                        expiry = arrow.get(exp_datestr)
                    except ParserError:
                        self._logger.error('Could not parse date string {}, giving up.'.format(exp_datestr))
                        return '-'

            return expiry.humanize()
        else:
            return '-'

            # self._get_pw_expiry(self._get_user_id())
            # self._current_user_info.get('pw_expiry', None)

    @pyqtProperty(QVariant, notify=current_program_changed)
    def currentProgramName(self):
        if self._current_program:
            return self._current_program.program_name

    @currentProgramName.setter
    def currentProgramName(self, program_name):
        if program_name:
            try:
                self._current_program = Programs.get(Programs.program_name == program_name)
                prog_id = self._current_program.program
                ObserverDBUtil.set_current_program_id(prog_id)
                self._logger.debug(f'Current Program ID set to {prog_id}')
                fisheries = self.get_fisheries_by_program_id(self._current_program.program, self._is_fixed_gear)

                self._current_fisheries.setStringList(fisheries)
                self.fisheries_model_changed.emit()
            except Programs.DoesNotExist as e:
                self._logger.error(e)
                self._current_program = None
        else:
            self._current_program = None
        self.current_program_changed.emit()

    @pyqtProperty(QVariant, notify=current_program_changed)
    def currentProgramID(self):
        return self._current_program.program if self._current_program else None

    @pyqtProperty(QVariant, notify=current_program_changed)
    def isFixedGear(self):
        return self._is_fixed_gear

    @isFixedGear.setter
    def isFixedGear(self, is_fixed):
        self._is_fixed_gear = is_fixed

    @pyqtSlot(name='logOut')
    def log_out(self):
        self._logger.info('Logged out user {}'.format(self.currentUserName))
        self._current_user_info = dict()
        self.user_changed.emit()
        self.currentUserPwExpiresChanged.emit()

    @pyqtSlot(str, str, result='bool', name='isPasswordInHistory')
    def pw_in_history(self, username, password):
        user_id = self.get_user_id(username)
        try:
            users_q = Users.get(Users.user == user_id)
            return self._check_insert_db_pw_history(username, user_id, password)
        except Exception as e:
            self._logger.error(e)
            return False

    @staticmethod
    def _check_insert_db_pw_history(username, user_id, password):
        """
        Check DB for old pw, if not in history, insert it
        @param user_id: Users USER_ID
        @param password: un-hashed pw
        @return: True if in DB, False if not
        """
        # Check for PASSWORD_HISTORY table if existing (note: not updated via APPLIED_TRANACTIONS)
        pw_hashed = ObserverSoap.hash_pw(username.upper(), password)
        try:
            PasswordHistory.get((PasswordHistory.user == user_id) &
                                (PasswordHistory.password == pw_hashed))
            return True
        except PasswordHistory.DoesNotExist:  # entry not found, insert
            PasswordHistory.create(user=user_id,
                                   created_by=user_id,
                                   created_date=ObserverDBUtil.get_arrow_datestr(),
                                   password=pw_hashed)
            return False
        except:
            return False

    @pyqtSlot(str, result='bool', name='userExists')
    def user_exists(self, username):
        """
        Check first+last username
        @param username: e.g. willsmith
        @return: True if exists, false otherwise
        """
        if self.get_user_id(username) is not None:
            return True
        else:
            return False

    @pyqtSlot(str, str, result='bool', name='userLogin')
    def user_login(self, username, password):
        """
        Performs user login
        @param username: username in form of firstlast
        @param password: local db pw
        @return: True if logged in successfully, False otherwise
        """
        self._logger.info('Attempt login for user {}'.format(username))
        success, user_id = self._check_username_pw(username, password)
        if user_id:
            self._current_user_info = {'username': username, 'userid': user_id, 'password': password}
            ObserverDBUtil.set_current_user_id(user_id)
            ObserverDBUtil.set_current_username(username)
            ObserverDBUtil.set_current_program_id(self.currentProgramID)
            prog_name = ObserverDBUtil.get_current_program_name()
            self._logger.debug(f'Set username to {username}, ID to {user_id}, program to {prog_name}')
            self._current_user_info['roles'] = self._get_user_roles(user_id)
            self._current_user_info['programs'] = self._get_user_program_names(user_id)
            self._logger.debug('Roles: {}'.format(self._current_user_info['roles']))
            self._logger.debug('Programs: {}'.format(self._current_user_info['programs']))
            self._current_user_roles = self._current_user_info['roles']
            self._current_user_programs.setStringList(self._current_user_info['programs'])
            self.program_model_changed.emit()
            return success
        else:
            self._logger.error('Error setting current username.')
            self._current_user_info = dict()
            return False

    @pyqtSlot(str, str, str, result='bool', name='userChangePassword')
    def user_change_password(self, username, old_pw, new_pw):
        """
        Change user's local password.
        @param username: username in form of firstlast
        @param old_pw: local db pw
        @param new_pw: local db pw
        @return: True if changed, False otherwise
        """
        self._logger.info(f'Change password for user {username} to new pw of length {len(new_pw)}')
        success, user_id = self._check_username_pw(username, old_pw)
        if success:
            return self._change_pw(username, user_id, new_pw)
        else:
            return False

    def _change_pw(self, username, user_id, password):
        try:
            user_pw_query = Users.get(Users.user == user_id)
            pw_hashed = ObserverSoap.hash_pw(username.upper(), password)
            user_pw_query.password = pw_hashed
            user_pw_query.save()
            self._logger.info('PW change successful.')
            return True
        except Users.DoesNotExist as e:
            self._logger.error(e)
        except Exception as e:
            self._logger.error(e)
        return False

    @staticmethod
    def _get_pw_expiry(user_id):
        try:
            user = Users.get(Users.user == user_id)
            return user.password_expiration_date
        except Users.DoesNotExist:
            return None

    @staticmethod
    def _get_user_roles(user_id):
        try:
            roles = UserProgramRoles.select().where(UserProgramRoles.user == user_id)
            return [r.program_role.role.role_name for r in roles]
        except UserProgramRoles.DoesNotExist:
            return None

    @staticmethod
    def _get_user_program_names(user_id):
        try:
            # User might be in multiple programs roles:
            program_roles = UserProgramRoles. \
                select(UserProgramRoles.program_role). \
                distinct(). \
                where(UserProgramRoles.user == user_id)

            roles = ProgramRoles. \
                select(ProgramRoles.program). \
                distinct(). \
                where(ProgramRoles.program_role << program_roles)  # "IN PROGRAM_ROLES"

            program_names = [r.program.program_name for r in roles]

            program_names.sort()
            return program_names
        except UserProgramRoles.DoesNotExist:
            return None

    def _check_username_pw(self, username, password):
        """
        Check for username match in DB, concatenated and lowercase, e.g. toddhay
        @param username: username to check for in DB
        @param password: password to check for in DB
        @return: Success, ID if username is in the DB, otherwise None
        """

        user_id = self.get_user_id(username)
        if not password or not user_id:
            self._logger.warning(f'Invalid username {username[:3]}**** or password.')
            return False, user_id
        try:
            pw_hashed = ObserverSoap.hash_pw(username.upper(), password)
            pw_user = Users.get(Users.user == user_id).password
            if pw_hashed == pw_user:
                return True, user_id
            else:
                return False, user_id
        except ValueError:
            self._logger.warning(f'Invalid username {username[:3]}****')
        except Exception as e:
            self._logger.error(f'Checking username/password username error. {e}')
        return False, None

    @staticmethod
    def get_user_id(username):
        """
        Check username for existing ID
        @param username: first+last e.g. willsmith
        @return: None if no user ID, int value otherwise
        """
        try:
            user_check = Users.get((fn.Lower(Users.first_name.concat(Users.last_name))) == username.lower())
            # self._logger.debug('ID {} found for user {}'.format(user_check.user, username))
            return user_check.user
        except Users.DoesNotExist:
            # self._logger.warning('Name not found: {}'.format(username))
            return None

    @staticmethod
    def get_program_ids_for_user(username):
        user_id = ObserverUsers.get_user_id(username)
        if user_id:
            programs = ObserverUsers._get_user_program_names(user_id)
            program_ids = [Programs.get(Programs.program_name == program_name).program for program_name in programs]
            return program_ids

    @pyqtSlot(str, name='updateProgramsForUser')
    def update_programs_for_user(self, username):
        """
        Sets the AvailablePrograms model appropriately
        @param username: username to look up
        """
        user_id = self.get_user_id(username)
        self._current_user_info['userid'] = user_id  # this will be set again at login
        if user_id:
            self._logger.debug('Retrieving programs and roles for user {}'.format(username[:3] + '****'))
            programs = self._get_user_program_names(user_id)
            roles = self._get_user_roles(user_id)
            self._current_user_programs.setStringList(programs)
            self._current_user_roles = roles
            current_progname = ObserverDBUtil.get_current_program_name()
            if current_progname in programs:
                self.currentProgramName = current_progname
            elif programs:  # set default program for user
                self.currentProgramName = programs[0]
            else:
                self.currentProgramName = None

        self.program_model_changed.emit()
        self.currentUserPwExpiresChanged.emit()
        self.current_user_is_debriefer_changed.emit()

    @staticmethod
    def get_fisheries_by_program_id(program_id, is_fixed_gear=False):
        fisheries = Lookups. \
            select(). \
            where((Lookups.lookup_type == 'FISHERY') &
                  (Lookups.program == program_id) &
                  (Lookups.active.is_null(True)))
        fishery_names = [f.description for f in fisheries]
        fishery_names.sort()

        if is_fixed_gear:
            fishery_names = list(filter(lambda f: 'rawl' not in f, fishery_names))

        logging.debug('Fisheries for program id {}: {}'.format(program_id, fishery_names))
        return fishery_names

    @pyqtProperty(QStringListModel, notify=program_model_changed)
    def AvailablePrograms(self):
        return self._current_user_programs

    @pyqtProperty(QStringListModel, notify=fisheries_model_changed)
    def AvailableFisheries(self):
        return self._current_fisheries


class TestObserverUsers(unittest.TestCase):
    """
    Note: any write/update interaction should be done with test_database...
    http://stackoverflow.com/questions/15982801/custom-sqlite-database-for-unit-tests-for-code-using-peewee-orm
    """

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def test_get_program_ids_for_username(self):
        username_tests = {'willsmith': [14],
                          'jasoneibner': [14, 17, 1, 3],
                          'badusername': None}
        for username in username_tests.keys():
            logging.info(f'Username {username} programs:')
            expected_program_ids = username_tests[username]
            program_ids = ObserverUsers.get_program_ids_for_user(username)
            logging.info(program_ids)
            if program_ids:
                for ef in program_ids:
                    self.assertTrue(ef in program_ids)
            else:
                self.assertIsNone(expected_program_ids)
