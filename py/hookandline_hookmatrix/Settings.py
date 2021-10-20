__author__ = 'James.Fellows'
# -----------------------------------------------------------------------------
# Name:        Settings.py
# Purpose:     Global settings data (HookMatrix)
#
# Author:      Jim Fellows <james.fellows@noaa.gov>
#
# Created:     Sep 9, 2021

# Copied over from SurveyBackdeck Settings.py
# https://github.com/nwfsc-fram/pyFieldSoftware/issues/259
# TODO: consolidate settings files between survey backdeck and here
# ------------------------------------------------------------------------------

import logging

from PyQt5.QtCore import pyqtProperty, QObject, QVariant, pyqtSignal, pyqtSlot
from py.common.FramListModel import FramListModel


class SettingsModel(FramListModel):
    """
    Model used in SettingsScreen TableView to expose settings params
    """
    def __init__(self):
        super().__init__()
        self.add_role_name(name="settingsId")
        self.add_role_name(name="parameter")
        self.add_role_name(name="type")
        self.add_role_name(name="value")
        self.add_role_name(name="is_active")


class Settings(QObject):

    rebootRequired = pyqtSignal(str, arguments=['param'])
    unusedSignal = pyqtSignal()  # use to eliminate QML warnings about non-notifyable properties

    def __init__(self, app=None, db=None):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db
        self._model = SettingsModel()
        self._build_model()

    @pyqtProperty(QVariant, notify=unusedSignal)
    def model(self):
        return self._model

    def _build_model(self):
        """
        Load settings model using SETTINGS table
        Current only the pararm and value columns are needed to load
        :return: None (set _model)
        """
        sql = '''
                    select
                                SETTINGS_ID
                                ,PARAMETER
                                ,VALUE
                    FROM        SETTINGS
                    WHERE       IS_ACTIVE = 'True'
                '''
        for row in self._db.execute(query=sql):
            self._model.appendItem({'settingsId': row[0], 'parameter': row[1], 'value': row[2]})

    @pyqtSlot(QVariant, QVariant, name='updateDbParameter')
    def updateDbParameter(self, parameter, value):
        """
        PyQt wrapper for _update_db_parameter private method
        if value has changed, update in DB and model
        if param changing is IP address, signal for reboot (this value is loaded on startup)
        :param parameter: str; SETTINGS parameter value
        :param value: str; value to set parameter in SETTINGS
        :return: None
        """
        role_index = self._model.get_item_index('parameter', parameter)  # get row num in model
        cur_value = self._model.get(role_index)['value']  # get existing model value
        logging.info(f"Updating DB param {parameter} from {cur_value} to {value}")
        if cur_value != value:
            self._update_db_parameter(parameter, value)
            self._model.setProperty(role_index, 'value', value)
            if parameter == 'FPC IP Address':
                self.rebootRequired.emit(parameter)

    def _update_db_parameter(self, parameter, value):
        sql = "UPDATE SETTINGS SET VALUE = ? WHERE PARAMETER = ?;"
        params = [value, parameter]

        try:
            self._db.execute(query=sql, parameters=params)
        except Exception as ex:
            return False
        return True
