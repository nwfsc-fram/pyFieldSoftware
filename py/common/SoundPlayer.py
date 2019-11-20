__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        SoundPlayer
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Apr 04, 2016
# License:     MIT
#-------------------------------------------------------------------------------
from PyQt5.QtCore import pyqtSlot, QThread, QObject, QVariant, pyqtSignal, QUrl
from PyQt5.QtMultimedia import QSound, QMediaPlayer, QMediaContent, QMediaPlaylist
import logging
import winsound
import os
from datetime import datetime
from copy import deepcopy

class SoundPlayerWorker(QObject):

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self.media_player = QMediaPlayer(flags = QMediaPlayer.LowLatency)
        self.playlist = QMediaPlaylist()
        self.media_player.setPlaylist(self.playlist)
        self._priority = 0

    def play_sound(self, file="", priority=0, override=False):
        """
        Method to add a new sound to play
        :param file: str
        :param override:
        :return:
        """

        # logging.info(f"file: {file}, priority: {priority}, self._priority: {self._priority}")

        if priority > self._priority:
            self.media_player.stop()
            self.playlist.clear()
            self._priority = priority

        # if override:
        #     self.media_player.stop()
        #     self.playlist.clear()

        # logging.info(f"request to play: {file}, override set to: {override}, mediaCount: {self.playlist.mediaCount()}")

        self.playlist.addMedia(QMediaContent(QUrl(file)))

        # logging.info(f"request to play, after adding file: {file}, override set to: {override}, mediaCount: {self.playlist.mediaCount()}")

        if self.media_player.state() == 0:
            self.media_player.play()

    def state_changed(self):
        """
        Method called when the media_player state is changed
        :return: 
        """
        if self.media_player.state() == 0:
            self._priority = 0

    def check_playlist_index(self):
        """
        Method to check to see if we've reached the end of the playlist or not
        :return:
        """
        if self.playlist.currentIndex() == -1:
            self.playlist.clear()

    def stop(self):
        """
        Method to stop the sound from playing any further
        :return:
        """
        self.media_player.stop()


class SoundPlayer(QObject):

    def __init__(self, app=None, db=None, **kwargs):
        super().__init__()
        self._app = app
        self._db = db

        self._threads_workers = {}

        self._thread = QThread()
        self._worker = SoundPlayerWorker()
        self._worker.moveToThread(self._thread)
        # self._worker.playlist.mediaInserted.connect(self._worker.play_sound)
        # self._worker.media_player.stateChanged.connect(self._player_state_changed)
        self._worker.playlist.currentIndexChanged.connect(self._worker.check_playlist_index)
        self._worker.media_player.stateChanged.connect(self._worker.state_changed)

        # self._thread.started.connect(self._worker.run)
        # self._thread.finished.connect(self._thread_finished)
        self._thread.start()

    @pyqtSlot()
    def stop_thread(self):
        """
        Method to stop the thread when the application is being shutdown
        :return:
        """
        if self._thread.isRunning():
            self._worker.stop()
            self._thread.exit()

    @pyqtSlot(str, int, bool, name="playSound")
    def play_sound(self, sound_name, priority=0, override=False):
        """
        Method to play a sound
        :param sound_name: str - name indicating which action was taken and thus the associated sound to play
        :param priority: int
        :param override: bool - whether to override any existing playing sounds or not - True/False
        :return:
        """
        if not isinstance(sound_name, str) or sound_name == "":
            return

        sound_file = ""
        if sound_name == "takeSubsample":
            sound_file = "resources/sounds/weighbaskets_buzzer.wav"

        elif sound_name == "takeWeight":
            sound_file = "resources/sounds/weighbaskets_donuts.wav"

        elif sound_name == "takeLength":
            sound_file = "resources/sounds/fishsampling_phonering.wav"

        elif sound_name == "takeWidth":
            sound_file = "resources/sounds/fishsampling_coffeebreak.wav"

        elif sound_name == "ageWeightSpecimen":
            sound_file = "resources/sounds/fishsampling_vikinghorn.wav"

        elif sound_name == "takeBarcode":
            sound_file = "resources/sounds/fishsampling_shotgun.wav"

        elif sound_name == "takeSudmantBarcode":
            sound_file = "resources/sounds/specialproject_sudmant.wav"

        elif sound_name == "deleteItem":
            sound_file = "resources/sounds/delete_item.wav"

        elif sound_name == "error":
            sound_file = "resources/sounds/fishsampling_undoundo.wav"

        elif sound_name == "jukebox":
            sound_file = f"resources/sounds/jukebox/{file_name}"

        elif sound_name == "hlHookMatrix15secs":
            sound_file = "resources/sounds/hookmatrix_15secs.wav"

        elif sound_name == "hlCutterStationNextFish":
            sound_file = "resources/sounds/cutterstation_nextfish.wav"

        if sound_file == "" or sound_file is None:
            return

        # logging.info(f"playing sound = {sound_file}, priority={priority}, override={override}")
        try:
            self._worker.play_sound(file=sound_file, priority=priority, override=override)

        except Exception as ex:
            logging.info(f"Exception occurred when attempting to play a sound: {ex}")

    def _player_state_changed(self):
        """
        Method called when the media player state is changed.
        :param key:
        :return:
        """
        if self._worker.media_player.state() == 0:
            logging.info('clearing playlist')
            self._worker.playlist.clear()
        return

        if key in self._threads_workers:
            item = self._threads_workers[key]
            if item["worker"].media_player.state() == 0:
                if item["thread"].isRunning():
                    item["thread"].exit()

    def _thread_finished(self, key):
        """
        Method called when the thread is finished
        :param key: str - key to remove from the self._threads_worker dictionary
        :return:
        """
        if key in self._threads_workers:
            item = self._threads_workers[key]
            self._threads_workers.pop(key, None)

    def _play_sound_thread(self, sound=None, loop=False):
        """
        Method to play a sound in the background
        :param sound:
        :param loop:
        :return:
        """
        try:
            while loop:

                if self.stop_sound:
                    winsound.PlaySound(None)
                    self.stop_sound = False
                    break
                winsound.PlaySound(sound, winsound.SND_FILENAME)

            else:
                if self.stop_sound:
                    winsound.PlaySound(None)
                    self.stop_sound = False
                    return
                winsound.PlaySound(sound, winsound.SND_FILENAME)

        except Exception as ex:

            print('Playing sound exception:', str(ex))


if __name__ == '__main__':
    s = SoundPlayer()
