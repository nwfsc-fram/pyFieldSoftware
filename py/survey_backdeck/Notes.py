from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QVariant
from py.common.FramListModel import FramListModel
import logging
import unittest
import arrow
import os
import glob
import ntpath
from pathlib import Path


class Notes(QObject):

    notesPathChanged = pyqtSignal()
    noteSaved = pyqtSignal(str, arguments=['imageNameStr'])

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db

        self._notes_path = "notes"
        if not os.path.exists(path=self._notes_path):
            os.makedirs(self._notes_path, 777)

    @pyqtProperty(str, notify=notesPathChanged)
    def notesPath(self):
        """
        Method to return the self._notes_path
        :return:
        """
        return self._notes_path

    @pyqtSlot(name="getNextNoteName", result=str)
    def get_next_note_name(self):
        """
        Method to return the name of the next note in the self._notes_path folder
        :return:
        """
        next_file = "note_1.png"
        try:
            note_files = [int(x.split("note_")[1].strip(".png")) for x in
                          glob.glob(self._notes_path + "/note_*.png")]
            note_files = sorted(note_files, reverse=True)
            if len(note_files) > 0:
                last_file_number = note_files[0]
                next_file = f"note_{last_file_number+1}.png"
        except Exception as ex:
            logging.error(f"Error getting the name note image filename: {ex}")

        next_path = os.path.join(self._notes_path, next_file)
        return next_path

    @pyqtSlot(str, str, str, QVariant, QVariant, QVariant, QVariant, QVariant, QVariant, name="insertNote")
    def insert_note(self, app_name, screen, value, site_op_id=None, drop=None, angler=None, hook=None,
                    observation=None, imageNameStr=None):
        """
        Method to insert a note into the NOTES table
        :param value:
        :return:
        """

        try:
            if value == "" or value is None:
                return

            sql = """
                INSERT INTO NOTES(APP_NAME, SCREEN_NAME, NOTE, OPERATION_ID, HL_DROP, HL_ANGLER, HL_HOOK, 
                                    CUTTER_OBSERVATION_NAME, DATE_TIME, IMAGE_NAME_STR, IMAGE_NAME_BLOB)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            date_time = arrow.now().to("US/Pacific").isoformat()

            # Read in the image into memory for insertion into the blob
            if os.path.exists(imageNameStr):
                # with open(imageNameStr, mode='rb') as file:
                #     image = file.read()
                image = Path(imageNameStr).read_bytes()

            params = [app_name, screen, value, site_op_id, drop, angler, hook, observation, date_time,
                      imageNameStr, image]

            logging.info(f"Saving note: app_name={app_name}, screen={screen}, value={value}, "
                         f"site_op_id={site_op_id}, drop={drop}, angler={angler}, hook={hook}, "
                         f"observation={observation}, date_time={date_time}, imageNameStr={imageNameStr}")

            results = self._app.rpc.execute_query(sql=sql, params=params)

            # image.close()
            logging.info(f"emitting noteSaved")
            self.noteSaved.emit(imageNameStr)

        except Exception as ex:

            logging.info(f"Error inserting a new note: {ex}")

