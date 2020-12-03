# -------------------------------------------------------------------------------
# Name:        SoundPlayer
# Purpose:     Customized audio for OPTECS Trawl
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
from py.observer.ObserverUtility import ObserverUtility
from pygame import mixer  # Currently used only on non-Windows platforms
from datetime import datetime
from copy import deepcopy

class SoundPlayerWorker(QObject):

    def __init__(self, args=(), kwargs=None):
        super().__init__()
        self.media_player = QMediaPlayer(flags = QMediaPlayer.LowLatency)
        self.playlist = QMediaPlaylist()
        self.media_player.setPlaylist(self.playlist)
        self._priority = 0
        # For play on non-Windows platforms:
        mixer.init()
        self.pygame_player = mixer.music

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

        if override:
            self.media_player.stop()
            self.playlist.clear()

        # logging.info(f"request to play: {file}, override set to: {override}, mediaCount: {self.playlist.mediaCount()}")

        if ObserverUtility.platform_is_windows():
            self.playlist.addMedia(QMediaContent(QUrl(file)))

            # logging.info(f"request to play, after adding file: {file}, override set to: {override}, mediaCount: {self.playlist.mediaCount()}")

            if self.media_player.state() == 0:
                self.media_player.play()
        else:
            # Note: Sound play on non-Windows is not using QMediaPlayer, which does not appear
            # to work on MacOS, at least not out of the box. Using python package pygame instead.
            self._pygame_play_sound(file)

    def _pygame_play_sound(self, sound_file):
        """ Play a WAV or MP3 sound file using the pygame python package. """
        self.pygame_player.load(sound_file)
        self.pygame_player.play()

        logging.info(f"Pygame: played sound file {sound_file}. ")

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

    def __init__(self, **kwargs):
        super().__init__()
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

    @pyqtSlot(str, bool)
    def play_sound(self, sound_name, priority=0, override=True):
        """
        Method to play a sound
        :param sound_name: str - name indicating which action was taken and thus the associated sound to play
        :param priority: priority
        :param override: bool - whether to override any existing playing sounds or not - True/False
        :return:
        """
        if not isinstance(sound_name, str) or sound_name == "":
            return

        sounds = {'keyInput': 'resources/sounds/minimal-ui-sounds/clack.wav',
                  'numpadInput': 'resources/sounds/minimal-ui-sounds/clack.wav',
                  'numpadDecimal': 'resources/sounds/minimal-ui-sounds/tinyclick.wav',
                  'numpadBack': 'resources/sounds/minimal-ui-sounds/click3.wav',
                  'numpadOK': 'resources/sounds/minimal-ui-sounds/beep.mp3',
                  'matrixWtSel': 'resources/sounds/minimal-ui-sounds/beep.mp3',
                  'keyOK': 'resources/sounds/minimal-ui-sounds/beep.mp3',
                  'click': 'resources/sounds/minimal-ui-sounds/click2.wav',
                  'saveRecord': 'resources/sounds/minimal-ui-sounds/funnyclick.wav',
                  'login': 'resources/sounds/minimal-ui-sounds/funnyclick.wav',
                  'noCount':  'resources/sounds/minimal-ui-sounds/spaceyclick.wav',
                  'reject':  'resources/sounds/minimal-ui-sounds/coarse.wav'
                  }

        sound_file = sounds.get(sound_name, None)

        if sound_file:
            self._worker.play_sound(file=sound_file, priority=priority, override=override)
        else:
            logging.warning(f'Sound not found: {sound_name}')

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


if __name__ == '__main__':
    s = SoundPlayer()
