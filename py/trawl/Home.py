__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        Home.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Feb 01, 2016
# License:     MIT
#-------------------------------------------------------------------------------
from PyQt5.QtCore import QVariant, pyqtProperty, pyqtSlot, QObject
import logging
from py.common.SoundPlayer import SoundPlayer
from random import randint
import os
import re

class Home(QObject):

    def __init__(self, app=None, db=None):
        super().__init__()

        self._app = app

        self._logger = logging.getLogger(__name__)
        self._db = db

        self._sound_player = SoundPlayer()

    @pyqtSlot()
    def feelingLucky(self):

        try:

            jukebox = [f for f in os.listdir(r"resources/sounds/jukebox") if re.search(r'.*\.(wav)$', f)]
            value = randint(0, len(jukebox)-1)
            file_name = jukebox[value]
            self._app.sound_player.play_sound(sound_name="jukebox", file_name=file_name)

        except Exception as ex:

            logging.error(f"Error playing a sound file: {ex}")


if __name__ == '__main__':
    h = Home()
