import logging
from copy import deepcopy

import arrow
from PyQt5.QtCore import QObject, QVariant, pyqtProperty, pyqtSlot, pyqtSignal

from py.hookandline.HookandlineFpcDB_model import Operations, Catch, CatchContentLu, Lookups, \
    SpeciesReviewView, HookLoggerDropView, HookMatrixView, CutterStationView, JOIN, \
    OperationAttributes
from playhouse.shortcuts import model_to_dict, dict_to_model

from py.common.FramListModel import FramListModel


class OperationsModel(FramListModel):

    def __init__(self, angler=""):
        super().__init__()
        self.add_role_name(name="id")
        self.add_role_name(name="text")

        self.populate_model()

    @pyqtSlot(name="populateModel")
    def populate_model(self):
        """
        Method to populate the operations model
        :return:
        """
        try:
            self.clear()

            self.appendItem({"id": -1, "text": "Set ID"})
            results = Operations.select()\
                .join(Lookups, on=(Lookups.lookup == Operations.operation_type_lu))\
                .where(Lookups.type=="Operation", Lookups.value=="Site")\
                .order_by(Operations.operation_number)
            for result in results:
                self.appendItem({'id': result.operation, 'text': result.operation_number})

        except Exception as ex:
            logging.error(f"Error populating the operations model: {ex}")


class HookLoggerDropModel(FramListModel):

    def __init__(self):
        super().__init__()
        self.add_role_name(name="dropNumber")
        self.add_role_name(name="startTime")
        self.add_role_name(name="startLatitude")
        self.add_role_name(name="startLongitude")
        self.add_role_name(name="startDepth")
        self.add_role_name(name="endTime")
        self.add_role_name(name="endLatitude")
        self.add_role_name(name="endLongitude")
        self.add_role_name(name="endDepth")
        self.add_role_name(name='tideHeight')
        self.add_role_name(name='dropType')
        self.add_role_name(name='includeInSurvey')

    @pyqtSlot(str, name="populateModel")
    def populate_model(self, set_id):
        """
        Method to populate the model
        :return:
        """
        if set_id == "":
            logging.info(f"Set ID is empty: {set_id}")

        try:
            self.clear()

            results = HookLoggerDropView.select()\
                .where(HookLoggerDropView.set_id==set_id)\
                .order_by(HookLoggerDropView.drop_number)
            for result in results:
                self.appendItem({
                    'dropNumber': result.drop_number,
                    'startTime': arrow.get(result.start_time).format("HH:mm:ss"),
                    'endTime': arrow.get(result.end_time).format("HH:mm:ss"),
                    'startLatitude': result.start_latitude,
                    'endLatitude': result.end_latitude,
                    'startLongitude': result.start_longitude,
                    'endLongitude': result.end_longitude,
                    'startDepth': result.start_depth,
                    'endDepth': result.end_depth,
                    'tideHeight': result.tide_height,
                    'dropType': result.drop_type,
                    'includeInSurvey': result.include_in_survey

                })


        except Exception as ex:
            logging.error(f"Error populating the operations model: {ex}")


class HookLoggerModel(FramListModel):

    def __init__(self, angler=""):
        super().__init__()
        self.add_role_name(name="setId")
        self.add_role_name(name="siteName")
        self.add_role_name(name="recordedBy")
        self.add_role_name(name="siteType")
        self.add_role_name(name="includeInSurvey")
        self.add_role_name(name="isRca")
        self.add_role_name(name="isMpa")
        self.add_role_name(name="habitatNotes")
        self.add_role_name(name="fishfinderNotes")
        self.add_role_name(name="oceanWeatherNotes")
        self.add_role_name(name="generalNotes")

        self.populate_model()

    @pyqtSlot(name="populateModel")
    def populate_model(self):
        """
        Method to populate the operations model
        :return:
        """
        try:
            self.clear()

            self.appendItem({"id": -1, "text": "Set ID"})
            results = Operations.select()\
                .join(Lookups, on=(Lookups.lookup == Operations.operation_type_lu))\
                .where(Lookups.type=="Operation", Lookups.value=="Site")\
                .order_by(Operations.operation_number)
            for result in results:
                self.appendItem({'id': result.operation, 'text': result.operation_number})

        except Exception as ex:
            logging.error(f"Error populating the operations model: {ex}")


class HookMatrixViewModel(FramListModel):

    def __init__(self, angler=""):
        super().__init__()
        self.add_role_name(name="setId")
        self.add_role_name(name="siteName")
        self.add_role_name(name='dropDateTime')
        self.add_role_name(name='dropNumber')
        self.add_role_name(name='angler')
        self.add_role_name(name='anglerName')
        self.add_role_name(name='start')
        self.add_role_name(name='beginFishing')
        self.add_role_name(name='firstBite')
        self.add_role_name(name='retrieval')
        self.add_role_name(name='atSurface')
        self.add_role_name(name='includeInSurvey')
        self.add_role_name(name='gearPerformance')
        self.add_role_name(name='hook1')
        self.add_role_name(name='hook2')
        self.add_role_name(name='hook3')
        self.add_role_name(name='hook4')
        self.add_role_name(name='hook5')
        self.add_role_name(name='sinkerWeight')
        self.add_role_name(name="recordedBy")

    @pyqtSlot(str, name="populateModel")
    def populate_model(self, set_id):
        """
        Method to populate the model
        :return:
        """
        if set_id == "":
            logging.info(f"Set ID is empty: {set_id}")

        try:
            self.clear()

            results = HookMatrixView.select()\
                .where(HookMatrixView.set_id==set_id)\
                .order_by(HookMatrixView.drop, HookMatrixView.angler)
            logging.info(f"results size: {results.count()}")
            for result in results:
                self.appendItem({
                    'dropNumber': result.drop,
                    'angler': result.angler,
                    'anglerName': result.angler_name,
                    'start': result.start,
                    'beginFishing': result.begin_fishing,
                    'firstBite': result.first_bite,
                    'retrieval': result.retrieval,
                    'atSurface': result.at_surface,
                    'includeInSurvey': result.include_in_survey,
                    'gearPerformance': result.gear_performance,
                    'hook1': result.hook1,
                    'hook2': result.hook2,
                    'hook3': result.hook3,
                    'hook4': result.hook4,
                    'hook5': result.hook5,
                    'sinkerWeight': result.sinker_weight,
                    'recordedBy': result.recorded_by
                })

        except Exception as ex:
            logging.error(f"Error populating the operations model: {ex}")


class CutterStationViewModel(FramListModel):

    cutterRecorderChanged = pyqtSignal(str, arguments=['recordedBy'])

    def __init__(self, angler=""):
        super().__init__()
        self.add_role_name(name="setId")
        self.add_role_name(name="siteName")
        self.add_role_name(name='dropDateTime')
        self.add_role_name(name='dropNumber')
        self.add_role_name(name='angler')
        self.add_role_name(name='hook')
        self.add_role_name(name='species')
        self.add_role_name(name='length')
        self.add_role_name(name='weight')
        self.add_role_name(name='sex')
        self.add_role_name(name='finclip')
        self.add_role_name(name='otolith')
        self.add_role_name(name='disposition')
        self.add_role_name(name='tagNumber')
        self.add_role_name(name='recordedBy')

    @pyqtSlot(str, name="populateModel")
    def populate_model(self, set_id):
        """
        Method to populate the model
        :return:
        """
        if set_id == "":
            logging.info(f"Set ID is empty: {set_id}")

        try:
            self.clear()

            results = CutterStationView.select()\
                .where(CutterStationView.set_id==set_id)\
                .order_by(CutterStationView.drop, CutterStationView.angler,
                          CutterStationView.hook)
            for result in results:
                self.appendItem({
                    'dropNumber': result.drop,
                    'angler': result.angler,
                    'hook': result.hook,
                    'species': result.species,
                    'length': result.length,
                    'weight': result.weight,
                    'sex': result.sex,
                    'finclip': result.finclip,
                    'otolith': result.otolith,
                    'disposition': result.disposition,
                    'tagNumber': result.tag_number,
                    'recordedBy': result.recorded_by
                })

            cutter_oa = Lookups.get(type='Cutter Attribute', value='Recorder Name').lookup
            site_op_id = Operations.get(operation_number=set_id).operation
            cutter_recorder_results = OperationAttributes.select()\
                .where(OperationAttributes.attribute_type_lu==cutter_oa,
                       OperationAttributes.operation==site_op_id)
            if cutter_recorder_results.count() >= 1:
                for result in cutter_recorder_results:
                    self.cutterRecorderChanged.emit(result.attribute_alpha)
                    break
            else:
                self.cutterRecorderChanged.emit("")

        except Exception as ex:
            logging.error(f"Error populating the CutterStation model: {ex}")


class EndOfSiteValidation(QObject):

    operationsModelChanged = pyqtSignal()
    hookLoggerDropModelChanged = pyqtSignal()
    hookMatrixModelChanged = pyqtSignal()
    cutterStationModelChanged = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()

        self._app = app
        self._db = db

        self._selected_set_id = "Set ID"
        self._operations_model = OperationsModel()
        self._hooklogger_drop_model = HookLoggerDropModel()
        self._hookmatrix_model = HookMatrixViewModel()
        self._cutterstation_model = CutterStationViewModel()

    @pyqtProperty(FramListModel, notify=hookLoggerDropModelChanged)
    def hookLoggerDropModel(self):
        """
        Method to return the self._hooklogger_drop_model
        :return:
        """
        return self._hooklogger_drop_model

    @pyqtProperty(FramListModel, notify=hookMatrixModelChanged)
    def hookMatrixModel(self):
        """
        Method to return the self._hookmatrix_model
        :return:
        """
        return self._hookmatrix_model

    @pyqtProperty(FramListModel, notify=cutterStationModelChanged)
    def cutterStationModel(self):
        """
        Method to return the self._hookmatrix_model
        :return:
        """
        return self._cutterstation_model

    @pyqtProperty(FramListModel, notify=operationsModelChanged)
    def operationsModel(self):
        """
        Method to return the self._operations model
        :return:
        """
        return self._operations_model

    @pyqtSlot(str, name="loadOperation")
    def load_operation(self, set_id):
        """
        Method to load the site operation's species data
        :param set_id:
        :return:
        """
        if set_id == "":
            return

        self.hookLoggerDropModel.populate_model(set_id=set_id)
        self.hookMatrixModel.populate_model(set_id=set_id)
        self.cutterStationModel.populate_model(set_id=set_id)
