__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        Notes.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 11, 2016
# License:     MIT
#-------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QVariant, QThread
from py.common.FramListModel import FramListModel
import logging
from py.common.SoundPlayer import SoundPlayer
from py.trawl.TrawlBackdeckDB_model \
    import Specimen, Catch, Hauls, TypesLu, Settings, ValidationsLu, Notes as NotesTable
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
from threading import Thread
import os
import shutil
from datetime import datetime
from copy import deepcopy


class Notes(QObject):
    """
    Class for the various TrawlNoteDialog
    """
    primaryKeyChanged = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

        self._primary_key = None

    @pyqtProperty(int, notify=primaryKeyChanged)
    def primaryKey(self):
        """
        Method to return the primary key of the database item to capture in the NOTES table
        :return:
        """
        return self._primary_key

    @primaryKey.setter
    def primaryKey(self, value):
        """
        Method to set the self._primary_key
        :param value:
        :return:
        """
        if not isinstance(value, int):
            logging.error("The primary key {0} is not an integer.".format(value))
            return
        self._primary_key = value
        self.primaryKeyChanged.emit()

    @pyqtSlot(str, str, str, str, QVariant)
    def insertNote(self, note, is_haul_validation, is_data_issue, is_software_issue, data_item_id):
        """
        Method to insert a new note into the NOTES table
        :param note: str
        :param is_haul_validation: str - True / False
        :param is_data_issue: str - True / False
        :param is_software_issue: str - True / False
        :param data_item_id: int / None - primary key of hte record in question
        :return:
        """
        try:
            screen = TypesLu.get(TypesLu.category == "Screen",
                   fn.replace(fn.lower(TypesLu.type), " ", "") == self._app.state_machine.screen).type_id

            row = NotesTable.insert(note=note, screen_type=screen, haul=self._app.state_machine.haul["haul_id"],
                        date_time=datetime.now(), is_haul_validation=is_haul_validation.title(),
                        is_data_issue=is_data_issue.title(),
                        is_software_issue=is_software_issue.title(),
                        data_item=data_item_id).execute()

        except Exception as ex:
            logging.info('Error inserting note: {0}'.format(ex))

    @pyqtSlot(QVariant, result=QVariant)
    def getNote(self, data_item_id):
        """
        Method to get a note for the given screen and data item ids
        :param screen_type_id:
        :param data_item_id:
        :return:
        """
        try:
            screen = self._app.state_machine.screen
            note = NotesTable.select(NotesTable, TypesLu) \
                        .join(TypesLu, on=(TypesLu.type == NotesTable.screen_type).alias('screen')) \
                        .where(fn.replace(fn.lower(TypesLu.type), " ", "") == screen,
                               NotesTable.data_item == data_item_id).get()
            return model_to_dict(note)

        except Exception as ex:
            logging.info('Unable to retrieve the required note')

        return None

