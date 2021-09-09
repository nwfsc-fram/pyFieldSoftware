__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        StateMachine.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Feb 03, 2016
# License:     MIT
#-------------------------------------------------------------------------------
from PyQt5.QtCore import pyqtProperty, pyqtSlot, QVariant, pyqtSignal, QObject
from PyQt5.QtQml import QJSValue
import logging
import arrow
import sys

from py.hookandline_hookmatrix.HookMatrixConfig import HOOKMATRIX_VERSION

APP_NAME = 'HookMatrix'

class StateMachine(QObject):
    """
    Class for handling all state machine management at the python level.  This will do things
    like initialize the screen at start time with the available hauls, the selected haul,
    the species associated with the selected haul, etc...

    It works hand in hand with teh TrawlBackdeckStateMachine.qml (which I think I'll rename to just
    StateMachine.qml
    """

    screenChanged = pyqtSignal()
    previousScreenChanged = pyqtSignal()
    vesselSelected = pyqtSignal()
    siteSelected = pyqtSignal()
    setIdChanged = pyqtSignal()
    areaChanged = pyqtSignal()
    siteDateTimeChanged = pyqtSignal()
    dropSelected = pyqtSignal()
    anglerSelected = pyqtSignal()
    anglerNameSelected = pyqtSignal()
    hookSelected = pyqtSignal()
    # specimenSelected = pyqtSignal()

    gearPerformanceLabelCreated = pyqtSignal(str, str, str, arguments=['drop', 'angler', 'label'])

    siteOpIdChanged = pyqtSignal()
    dropOpIdChanged = pyqtSignal()
    anglerAOpIdChanged = pyqtSignal()
    anglerBOpIdChanged = pyqtSignal()
    anglerCOpIdChanged = pyqtSignal()
    hookSpecimenIdChanged = pyqtSignal()

    dropTimeStateChanged = pyqtSignal()
    appNameChanged = pyqtSignal()
    swVersionChanged = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db

        self._app_name = APP_NAME
        self._software_version = HOOKMATRIX_VERSION

        logging.info(f"{self._app_name} v{self._software_version}")
        logging.info(f"Starting date/time: {arrow.now()}")

        self._screen = "sites"
        self._previous_screen = "sites"
        self._vessel = None
        self._site = None
        self._set_id = None
        self._area = None
        self._site_date_time = None
        self._drop = None
        self._angler = None
        self._angler_name = None
        self._hook = None

        self._site_op_id = None
        self._drop_op_id = None
        self._angler_a_op_id = None
        self._angler_b_op_id = None
        self._angler_c_op_id = None
        self._hook_specimen_id = None

        self._drop_time_state = "enter"

    @pyqtProperty(str, notify=swVersionChanged)
    def swVersion(self):
        """
        Method to return the swVersion
        :return:
        """
        return self._software_version

    @pyqtProperty(str, notify=appNameChanged)
    def appName(self):
        """
        Method to return the appName
        :return:
        """
        return self._app_name

    @pyqtProperty(QVariant, notify=dropTimeStateChanged)
    def dropTimeState(self):
        """
        Method to return the self._drop_time_state
        :return:
        """
        return self._drop_time_state

    @dropTimeState.setter
    def dropTimeState(self, value):
        """
        Method to set the drop time state
        :param value:
        :return:
        """
        logging.info(f"dropTimeState getting set to: {value}")
        self._drop_time_state = value
        self.dropTimeStateChanged.emit()

    @pyqtProperty(QVariant, notify=siteOpIdChanged)
    def siteOpId(self):
        """
        Method to return the self._site_op_id
        :return:
        """
        return self._site_op_id

    @siteOpId.setter
    def siteOpId(self, value):
        """
        Method to set the self._site_op_id
        :param value:
        :return:
        """
        self._site_op_id = value
        self.siteOpIdChanged.emit()

    @pyqtProperty(QVariant, notify=dropOpIdChanged)
    def dropOpId(self):
        """
        Method to return the self._drop_op_id
        :return:
        """
        return self._drop_op_id

    @dropOpId.setter
    def dropOpId(self, value):
        """
        Method to set the self._drop_op_id
        :param value:
        :return:
        """
        self._drop_op_id = value
        self.dropOpIdChanged.emit()

    @pyqtProperty(QVariant, notify=anglerAOpIdChanged)
    def anglerAOpId(self):
        """
        Method to return the self._angler_a_op_id
        :return:
        """
        return self._angler_a_op_id

    @anglerAOpId.setter
    def anglerAOpId(self, value):
        """
        Method to set the self._angler_a_op_id value
        :param value:
        :return:
        """
        self._angler_a_op_id = value
        self.anglerAOpIdChanged.emit()

    @pyqtProperty(QVariant, notify=anglerBOpIdChanged)
    def anglerBOpId(self):
        """
        Method to return the self._angler_b_op_id
        :return:
        """
        return self._angler_b_op_id

    @anglerBOpId.setter
    def anglerBOpId(self, value):
        """
        Method to set the self._angler_b_op_id value
        :param value:
        :return:
        """
        self._angler_b_op_id = value
        self.anglerBOpIdChanged.emit()

    @pyqtProperty(QVariant, notify=anglerCOpIdChanged)
    def anglerCOpId(self):
        """
        Method to return the self._angler_c_op_id
        :return:
        """
        return self._angler_c_op_id

    @anglerCOpId.setter
    def anglerCOpId(self, value):
        """
        Method to set the self._angler_c_op_id value
        :param value:
        :return:
        """
        self._angler_c_op_id = value
        self.anglerCOpIdChanged.emit()

    @pyqtProperty(QVariant, notify=hookSpecimenIdChanged)
    def hookSpecimenId(self):
        """
        Method to return self._hook_specimen_id
        :return:
        """
        return self._hook_specimen_id

    @hookSpecimenId.setter
    def hookSpecimenId(self, value):
        """
        Method to set the self._hook_specimen_id
        :param value:
        :return:
        """
        self._hook_specimen_id = value
        self.hookSpecimenIdChanged.emit()

    @pyqtProperty(QVariant, notify=screenChanged)
    def screen(self):
        """
        Method to return the current screen
        :return:
        """
        return self._screen

    @screen.setter
    def screen(self, value):
        """
        Method to set the current screen
        :param value:
        :return:
        """
        self._screen = value
        self.screenChanged.emit()

    @pyqtProperty(QVariant, notify=previousScreenChanged)
    def previousScreen(self):
        """
        Method to return the state machines previous_screen
        :return:
        """
        return self._previous_screen

    @previousScreen.setter
    def previousScreen(self, value):
        """
        Method to set the state machine's previous scene
        :param value:
        :return:
        """
        self._previous_screen = value
        self.previousScreenChanged.emit()

    @pyqtProperty(QVariant, notify=vesselSelected)
    def vessel(self):
        """
        Method to return the vessel
        :return:
        """
        return self._vessel

    @vessel.setter
    def vessel(self, value):
        """
        Method to set the vessel
        :param value:
        :return:
        """
        self._vessel = value
        self.vesselSelected.emit()

    @pyqtProperty(QVariant, notify=siteSelected)
    def site(self):
        """
        Method to return the site that is currently selected
        :return:
        """
        return self._site

    @site.setter
    def site(self, value):
        """
        Method to set the current site
        :param value:
        :return:
        """
        self._site = value
        self.siteSelected.emit()

    @pyqtProperty(QVariant, notify=setIdChanged)
    def setId(self):
        """
        Return the self._set_id property
        :return:
        """
        return self._set_id

    @setId.setter
    def setId(self, value):
        """
        Set the self._set_id value
        :param value:
        :return:
        """
        self._set_id = value
        self.setIdChanged.emit()

    @pyqtProperty(QVariant, notify=areaChanged)
    def area(self):
        """
        Method to return the self._area
        :return:
        """
        return self._area

    @area.setter
    def area(self, value):
        """
        Method to set the self._area
        :param value:
        :return:
        """
        self._area = value
        self.areaChanged.emit()

    @pyqtProperty(QVariant, notify=siteDateTimeChanged)
    def siteDateTime(self):
        """
        Method to return the self._site_date_time
        :return:
        """
        return self._site_date_time

    @siteDateTime.setter
    def siteDateTime(self, value):
        """
        Method to set the self._site_date_time
        :param value:
        :return:
        """
        self._site_date_time = value
        self.siteDateTimeChanged.emit()

    @pyqtProperty(QVariant, notify=dropSelected)
    def drop(self):
        """
        Method to return the currently selected drop
        :return:
        """
        return self._drop

    @drop.setter
    def drop(self, value):
        """
        Method to set the currently selected drop
        :param value:
        :return:
        """
        self._drop = value
        self.dropSelected.emit()

    @pyqtProperty(QVariant, notify=anglerSelected)
    def angler(self):
        """
        Method to return the currently selected angler
        :return:
        """
        return self._angler

    @angler.setter
    def angler(self, value):
        """
        Method to set the currently selected angler
        :param value:
        :return:
        """
        self._angler = value
        self.anglerSelected.emit()

    @pyqtProperty(QVariant, notify=hookSelected)
    def hook(self):
        """
        Method to return the self._hook
        :return:
        """
        return self._hook

    @hook.setter
    def hook(self, value):
        """
        Method to set the self._hook
        :param value:
        :return:
        """
        if value not in [None, "1", "2", "3", "4", "5"]:
            return

        self._hook = value
        self.hookSelected.emit()

    @pyqtProperty(QVariant, notify=anglerNameSelected)
    def anglerName(self):
        """
        Method to return the anglerName
        :return:
        """
        return self._angler_name

    @anglerName.setter
    def anglerName(self, value):
        """
        Method to set the anglerName
        :param value:
        :return:
        """
        self._angler_name = value
        self.anglerNameSelected.emit()

    @pyqtSlot(name="exitApp")
    def exitApp(self):
        logging.info("Calling exitApp to quit app")
        sys.exit()

if __name__ == '__main__':

    sm = StateMachine()
