from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QThread, \
    QVariant
import arrow
import logging
import random
import time


class SimulatorWorker(QObject):

    dataCreated = pyqtSignal(QVariant)

    def __init__(self, kwargs=None):

        super().__init__()
        self.is_streaming = False   # Status of the data creation streaming
        self._time_delay = 5        # Time delay in seconds

    def start(self):

        self.is_streaming = True

    def stop(self):

        self.is_streaming = False

    def run(self):

        # Start the streaming
        self.start()

        # Start the data creation loop
        while True:

            # Break if told to stop streaming
            if not self.is_streaming:
                break

            # Generate bogus data
            data = dict()

            # Time
            data["time"] = arrow.now().format("HH:mm:ss")

            # Latitude
            data["latitude"] = round(random.uniform(30, 35), 6)

            # Longitude
            data["longitude"] = round(random.uniform(-123, -120), 6)

            # Speed Over Ground
            data["sog"] = round(random.uniform(0, 5), 1)

            # Drift Direction
            data["drift_dir"] = round(random.uniform(0, 359.9), 1)

            # Emit the generated data
            self.dataCreated.emit(data)

            # Pause for
            time.sleep(self._time_delay)


class SerialPortSimulator(QObject):

    dataReceived = pyqtSignal(QVariant, arguments=["data"])

    def __init__(self, app=None, db=None):

        super().__init__()
        self._app = app
        self._db = db

        self._thread = QThread()
        self._worker = SimulatorWorker()
        self._worker.moveToThread(self._thread)
        self._worker.dataCreated.connect(self.data_created)
        self._thread.started.connect(self._worker.run)

    @pyqtSlot()
    def start(self):

        if not self._thread.isRunning():
            self._thread.start()

    @pyqtSlot()
    def stop(self):

        if self._thread.isRunning():
            self._worker.stop()
            self._thread.quit()

    def data_created(self, data):
        """
        Method to catch the data from the SimulatorWorker
        :param data:
        :return:
        """
        # logging.info(f"data caught: {data}")
        self.dataReceived.emit(data)
