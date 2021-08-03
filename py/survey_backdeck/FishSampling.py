__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        FishSampling.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 11, 2016
# License:     MIT
#-------------------------------------------------------------------------------
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, \
    QVariant, QSortFilterProxyModel, QByteArray, QAbstractItemModel, Q_ENUMS
from PyQt5.QtQml import QJSValue
from py.common.FramListModel import FramListModel
import logging
import unittest
import arrow


class PersonnelModel(FramListModel):

    def __init__(self, app=None):
        super().__init__()
        self._app = app
        self._rpc = self._app.rpc
        self.add_role_name(name="id")
        self.add_role_name(name="displayText")

        self.populate_model()

    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()
        sql = """
            SELECT DISTINCT p.PERSONNEL_ID, p.FIRST_NAME, p.LAST_NAME 
            FROM SETTINGS s
                INNER JOIN PERSONNEL p ON s.VALUE = p.PERSONNEL_ID
            WHERE s.TYPE = 'Personnel' and s.VALUE IS NOT NULL and p.IS_SCIENCE_TEAM = 'True'
            ORDER BY p.FIRST_NAME, p.LAST_NAME;
        """
        results = self._rpc.execute_query(sql=sql)
        for result in results:
            item = dict()
            item["id"] = result[0]
            item["displayText"] = result[1] + " " + result[2]
            self.appendItem(item)

    @pyqtSlot(name="getRecorder")
    def get_recorder(self):
        """
        method to get that recorder for the current site
        :return:
        """
        # Check if a recorder ID exists for this site yes
        sql = """
            SELECT oa.ATTRIBUTE_ALPHA 
                From operation_attributes oa
                    INNER JOIN operations o on oa.operation_id = o.operation_id
                    INNER JOIN lookups at on at.lookup_id = oa.attribute_type_lu_id
                WHERE o.OPERATION_NUMBER = ? AND at.TYPE = 'Cutter Attribute' AND at.VALUE = 'Recorder Name';
        """
        params = [self._app.state_machine.setId, ]
        results = self._app.rpc.execute_query(sql=sql, params=params)
        self._app.state_machine.recorder = results[0][0] if results else None


class SpeciesFullListModel(FramListModel):

    def __init__(self, app=None):
        super().__init__()
        self._app = app
        self._rpc = self._app.rpc
        self.add_role_name(name="id")
        self.add_role_name(name="text")
        self.partition_size = 24

        self.populate_model()

    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()
        sql = """
            SELECT DISPLAY_NAME, CATCH_CONTENT_ID 
                FROM CATCH_CONTENT_LU
                WHERE CONTENT_TYPE_LU_ID = (SELECT LOOKUP_ID FROM LOOKUPS WHERE
                    TYPE = 'Catch Content' AND VALUE = 'Taxonomy')
                ORDER BY DISPLAY_NAME asc;
        """
        results = self._rpc.execute_query(sql=sql)
        for result in results:
            item = dict()
            item["id"] = result[1]
            item["text"] = result[0]
            self.appendItem(item)

    @pyqtSlot(int, name="getSubset", result=QVariant)
    def get_subset(self, index):
        """
        Method to return a subset of the FramListModel for use in a SwipeView for the fullSpecieslist
        :param index:
        :return:
        """
        return self.items[index * self.partition_size: (index+1) * self.partition_size]


class SpecialsModel(FramListModel):

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db
        self.add_role_name(name="id")
        self.add_role_name(name="speciesSamplingPlanID")
        self.add_role_name(name="project")
        self.add_role_name(name="tagType")
        self.add_role_name(name="tagSubType")
        self.add_role_name(name="tagNumber")

    @pyqtSlot(QVariant, name="populateModel")
    def populate_model(self, specimen_id: int):
        """
        Method to populate the model.  This is used int he FishSamplingEntryDialog.qml, on the Special tab.
        It is used for all of the non-standard observations that can be captured.
        :return:
        """
        self.clear()
        try:
            sql = """
                WITH 
                    plans(PLAN_ID, PLAN_NAME, TAG_TYPE, TAG_SUBTYPE) AS
                        (SELECT ssp.SPECIES_SAMPLING_PLAN_ID AS PLAN_ID, 
                            ssp.PLAN_NAME, l.VALUE AS TAG_TYPE, l.SUBVALUE AS TAG_SUBTYPE
                            FROM SPECIES_SAMPLING_PLAN_LU ssp
                            INNER JOIN PROTOCOL_LU p ON ssp.PROTOCOL_ID = p.PROTOCOL_ID
                            INNER JOIN LOOKUPS l ON l.LOOKUP_ID = p.ACTION_TYPE_ID
                            ORDER BY TAG_TYPE asc, PLAN_NAME ASC
                        ),
                    spec(SPECIMEN_ID, ALPHA_VALUE, PLAN_ID) AS
                        (SELECT SPECIMEN_ID, ALPHA_VALUE, SPECIES_SAMPLING_PLAN_ID
                            FROM SPECIMENS
                            WHERE PARENT_SPECIMEN_ID = ?
                                AND SPECIES_SAMPLING_PLAN_ID IS NOT NULL
                        )
                SELECT spec.SPECIMEN_ID as SPECIMEN_ID, plans.PLAN_ID AS PLAN_ID, 
                    plans.PLAN_NAME AS PLAN_NAME, plans.TAG_TYPE AS TAG_TYPE, spec.ALPHA_VALUE as VALUE,
                    plans.TAG_SUBTYPE AS TAG_SUBTYPE
                FROM plans LEFT JOIN spec ON plans.PLAN_ID = spec.PLAN_ID            
            """
            params = [specimen_id, ]
            tags = self._app.rpc.execute_query(sql=sql, params=params)
            for tag in tags:
                item = dict()
                item["id"] = tag[0]
                item["speciesSamplingPlanID"] = tag[1]
                item["project"] = tag[2]
                item["tagType"] = tag[3]
                item["tagNumber"] = tag[4]
                item["tagSubType"] = tag[5]
                self.appendItem(item=item)

        except Exception as ex:

            logging.error(f"Error populating the SpecialModel: {ex}")

    @pyqtSlot(name="getSpecialTabLabel", result=str)
    def get_special_tab_label(self):
        """
        Method to return the shortened value used to populate the Special tab in the
        FishSamplingEntryDialog.qml dialog
        :return:
        """
        label = ""
        try:

            # for x in self.items:
            #     logging.info(f"item = {x}")

            sorted_items = sorted(list(set([x['tagType'] for x in self.items
                                            if x["tagNumber"] is not None and x["tagNumber"] != ""])))
            # logging.info(f"sorted_items={sorted_items}")
            sorted_abbrev = ["WS" if x == "Whole Specimen ID" else x[0:2].upper() for x in sorted_items]
            logging.info(f"sorted_abbrev for special = {sorted_abbrev}")
            label = ",".join(sorted_abbrev)
            label = label if len(label) <= 11 else label[0:11]

        except Exception as ex:
            logging.error(f"Error getting the Special tab label: {ex}")

        return label


class SpecimensModel(FramListModel):

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db
        self.add_role_name(name="ID")
        self.add_role_name(name="specimenID")
        self.add_role_name(name="species")
        self.add_role_name(name="taxonomyID")  # 96: added for LW relationship check
        self.add_role_name(name="adh")
        self.add_role_name(name="weight")
        self.add_role_name(name="length")
        self.add_role_name(name="sex")
        self.add_role_name(name="ageID")
        self.add_role_name(name="finclipID")
        self.add_role_name(name="special")
        self.add_role_name(name="disposition")
        self.add_role_name(name="tagID")

        self.add_role_name(name="stomachID")
        self.add_role_name(name="tissueID")
        self.add_role_name(name="ovaryID")
        self.add_role_name(name="intestineID")

        # CATCH table CATCH_CONTENT_ID value
        self.add_role_name(name="catchContentID")   # For the species role above

        # SPECIMEN table SPECIMEN_ID values - for each of the observation roles above
        self.add_role_name(name="weightRecID")
        self.add_role_name(name="lengthRecID")
        self.add_role_name(name="sexRecID")
        self.add_role_name(name="ageRecID")
        self.add_role_name(name="ageType")
        self.add_role_name(name="finclipRecID")
        self.add_role_name(name="dispositionRecID")

        self.add_role_name(name="stomachRecID")
        self.add_role_name(name="tissueRecID")
        self.add_role_name(name="ovaryRecID")
        self.add_role_name(name="intestineRecID")
        self.add_role_name(name="tagRecID")
        self.add_role_name(name="dispositionType")
        self.add_role_name(name="speciesSamplingPlanID")

        self.add_role_name(name="ageFinRayID")
        self.add_role_name(name="ageFinRayRecID")


        # self.add_role_name(name="samplingStatus")

        self.keys = ["specimenID", "adh", "species", "taxonomyID", "catchContentID", "sex", "sexRecID", "length",
                "lengthRecID", "weight", "weightRecID", "ageID", "ageRecID", "ageType", "stomachID", "stomachRecID",
                 "tissueID", "tissueRecID", "ovaryID", "ovaryRecID", "finclipID", "finclipRecID",
                 "intestineID", "intestineRecID", "disposition", "dispositionRecID", "tagID", "tagRecID",
                     "wholeSpecimenID", "wholeSpecimenRecID", "dispositionType", "speciesSamplingPlanID",
                     "ageFinRayID", "ageFinRayRecID"]

    @pyqtSlot()
    def populate_model(self):
        """
        Method to populate the model when the FishSamplingScreen is opened
        # 96: adding in taxonomyID to select statement for LW relationship check
        :return:
        """
        self.clear()

        try:
            sql = """
                WITH RECURSIVE 
                    ops_children(n) AS (
                        SELECT OPERATION_ID FROM OPERATIONS WHERE OPERATION_NUMBER = ?
                        UNION
                        SELECT o.OPERATION_ID FROM OPERATIONS o, ops_children
                                WHERE o.PARENT_OPERATION_ID = ops_children.n
                    ),
                    parent_specimen(SPECIMEN_ID, adh, cs_catch_content_id, species, taxonomy_id) as (
                        SELECT 
                                s.SPECIMEN_ID,
                                o.OPERATION_NUMBER ||
                                (SELECT o2.OPERATION_NUMBER FROM OPERATIONS as o2 
                                    WHERE o2.OPERATION_ID = o.PARENT_OPERATION_ID) ||
                                c.RECEPTACLE_SEQ as "adh",
                                c.CS_CATCH_CONTENT_ID,
                                (SELECT cc.DISPLAY_NAME from CATCH_CONTENT_LU cc 
                                    WHERE cc.CATCH_CONTENT_ID = c.CS_CATCH_CONTENT_ID) as Species,
                                (SELECT cc.taxonomy_id from CATCH_CONTENT_LU cc 
                                    WHERE cc.CATCH_CONTENT_ID = c.CS_CATCH_CONTENT_ID) as taxonomy_id
                        FROM OPERATIONS o
                        INNER JOIN LOOKUPS ot ON ot.LOOKUP_ID = o.OPERATION_TYPE_LU_ID
                        LEFT JOIN CATCH c ON c.OPERATION_ID = o.OPERATION_ID
                        LEFT JOIN SPECIMENS s ON s.CATCH_ID = c.CATCH_ID
                        WHERE o.OPERATION_ID IN ops_children
                                AND ot.TYPE = 'Operation' 
                                AND (ot.VALUE = 'Angler' OR ot.VALUE = 'Site')
                                AND s.PARENT_SPECIMEN_ID IS NULL
                                AND s.SPECIMEN_ID IS NOT NULL
                    )

                    SELECT ps.SPECIMEN_ID as specimenID
                        , ps.adh as adh
                        , ps.species as species
                        , ps.taxonomy_id as taxonomyID
                        , ps.cs_catch_content_id as catchContentID
                        , MAX(CASE WHEN l.VALUE = 'Sex' THEN s.ALPHA_VALUE END) AS sex
                        , MAX(CASE WHEN l.VALUE = 'Sex' THEN s.SPECIMEN_ID END) AS sexRecID
                        , MAX(CASE WHEN l.VALUE = 'Length' THEN s.NUMERIC_VALUE END) AS length
                        , MAX(CASE WHEN l.VALUE = 'Length' THEN s.SPECIMEN_ID END) AS lengthRecID
                        , MAX(CASE WHEN l.VALUE = 'Weight' THEN s.NUMERIC_VALUE END) AS weight
                        , MAX(CASE WHEN l.VALUE = 'Weight' THEN s.SPECIMEN_ID END) AS weightRecID
                        
                        -- , MAX(CASE WHEN l.VALUE = 'Age ID' AND l.SUBVALUE = 'Otolith' THEN s.ALPHA_VALUE END) AS ageID
                        -- , MAX(CASE WHEN l.VALUE = 'Age ID' AND l.SUBVALUE = 'Otolith' THEN s.SPECIMEN_ID END) AS ageRecID
                        -- , MAX(CASE WHEN l.VALUE = 'Age ID' AND l.SUBVALUE = 'Otolith' THEN l.SUBVALUE END) AS ageType

                        , MAX(CASE WHEN l.VALUE = 'Age ID' AND
                                        s.species_sampling_plan_id IS NULL THEN s.ALPHA_VALUE END) AS ageID
                        , MAX(CASE WHEN l.VALUE = 'Age ID' AND
                                        s.species_sampling_plan_id IS NULL THEN s.SPECIMEN_ID END) AS ageRecID
                        , MAX(CASE WHEN l.VALUE = 'Age ID' AND
                                        s.species_sampling_plan_id IS NULL THEN l.SUBVALUE END) AS ageType                        
                        
                        , MAX(CASE WHEN l.VALUE = 'Stomach ID' THEN s.ALPHA_VALUE END) AS stomachID
                        , MAX(CASE WHEN l.VALUE = 'Stomach ID' THEN s.SPECIMEN_ID END) AS stomachRecID
                        , MAX(CASE WHEN l.VALUE = 'Tissue ID' THEN s.ALPHA_VALUE END) AS tissueID
                        , MAX(CASE WHEN l.VALUE = 'Tissue ID' THEN s.SPECIMEN_ID END) AS tissueRecID
                        , MAX(CASE WHEN l.VALUE = 'Ovary ID' THEN s.ALPHA_VALUE END) AS ovaryID
                        , MAX(CASE WHEN l.VALUE = 'Ovary ID' THEN s.SPECIMEN_ID END) AS ovaryRecID
                        , MAX(CASE WHEN l.VALUE = 'Finclip ID' THEN s.ALPHA_VALUE END) AS finclipID
                        , MAX(CASE WHEN l.VALUE = 'Finclip ID' THEN s.SPECIMEN_ID END) AS finclipRecID
                        , MAX(CASE WHEN l.VALUE = 'Intestine ID' THEN s.ALPHA_VALUE END) AS intestineID
                        , MAX(CASE WHEN l.VALUE = 'Intestine ID' THEN s.SPECIMEN_ID END) AS intestineRecID
                        , MAX(CASE WHEN l.VALUE = 'Disposition' THEN s.ALPHA_VALUE END) AS disposition
                        , MAX(CASE WHEN l.VALUE = 'Disposition' THEN s.SPECIMEN_ID END) AS dispositionRecID
                        , MAX(CASE WHEN l.VALUE = 'Tag ID' THEN s.ALPHA_VALUE END) AS tagID
                        , MAX(CASE WHEN l.VALUE = 'Tag ID' THEN s.SPECIMEN_ID END) AS tagRecID   
                        , MAX(CASE WHEN l.VALUE = 'Whole Specimen ID' THEN s.ALPHA_VALUE END) AS wholeSpecimenID
                        , MAX(CASE WHEN l.VALUE = 'Whole Specimen ID' THEN s.SPECIMEN_ID END) AS wholeSpecimenRecID                                             
                        , MAX(CASE WHEN l.VALUE = 'Disposition' THEN l.SUBVALUE END) AS dispositionType
                        , s.species_sampling_plan_id as species_sampling_plan_id
                        , MAX(CASE WHEN l.VALUE = 'Age ID' AND l.SUBVALUE = 'Finray' AND
                                        s.species_sampling_plan_id IS NOT NULL THEN s.ALPHA_VALUE END) AS ageFinRayID                        
                        , MAX(CASE WHEN l.VALUE = 'Age ID' AND l.SUBVALUE = 'Finray' AND
                                        s.species_sampling_plan_id IS NOT NULL THEN s.SPECIMEN_ID END) AS ageFinRayRecID
                        
                    FROM parent_specimen ps 
                        LEFT JOIN SPECIMENS s on ps.SPECIMEN_ID = s.PARENT_SPECIMEN_ID
                        LEFT JOIN LOOKUPS l ON l.LOOKUP_ID = s.ACTION_TYPE_ID
                    GROUP BY specimenID
                    ORDER by specimenID
            """
            #   ORDER BY adh

            params = [self._app.state_machine.setId, ]
            results = self._app.rpc.execute_query(sql=sql, params=params)
            # template = {v.decode('utf-8'): None for k, v in self.roleNames().items()}

            logging.info(f"populating specimen model, count: {len(results)}, params: {params}")

            for i, values in enumerate(results):
                item = dict(zip(self.keys, values))
                item["ID"] = i+1
                special = list()

                # TODO Todd Hay - 2018 Hack
                try:
                    if item["ageFinRayID"] and item["speciesSamplingPlanID"]:
                        special.append("AG")
                    if item["ovaryID"]:
                        special.append("OV")
                    if item["stomachID"]:
                        special.append("ST")
                    if item["tissueID"]:
                        special.append("TI")
                    if item["intestineID"]:
                        special.append("IN")
                    if "wholeSpecimenID" in item and item["wholeSpecimenID"]:
                        special.append("WS")
                    item["special"] = ",".join(sorted(list(set(special))))
                    # if len(special) > 0:
                    #     logging.info(f"item={item}")
                    #     logging.info(f"special list = {special}")
                except Exception as ex:
                    logging.error(f"Error crafting the special list: {ex}")

                self.appendItem(item=item)

        except Exception as ex:

            logging.error(f"Error populating the fish sampling model: {ex}")


class SortFilterProxyModel(QSortFilterProxyModel):

    """
    Pulled from here:
    http://stackoverflow.com/questions/36823456/use-a-qsortfilterproxymodel-from-qml-with-pyqt5

    with reference to here:
    http://blog.qt.io/blog/2014/04/16/qt-weekly-6-sorting-and-filtering-a-tableview/

    https://stackoverflow.com/questions/26917195/how-to-get-the-row-of-an-item-in-qsortfilterproxymodel-giving-qstring

    """

    class FilterSyntax:
        RegExp, Wildcard, FixedString = range(3)

    Q_ENUMS(FilterSyntax)

    def __init__(self, parent):
        super().__init__(parent)

    @pyqtProperty(QAbstractItemModel)
    def source(self):
        return super().sourceModel()

    @source.setter
    def source(self, source):
        self.setSourceModel(source)

    @pyqtProperty(int)
    def sortOrder(self):
        return self._order

    @sortOrder.setter
    def sortOrder(self, order):
        self._order = order
        super().sort(0, order)

    @pyqtProperty(QByteArray)
    def sortRole(self):
        return self._roleNames().get(super().sortRole())

    @sortRole.setter
    def sortRole(self, role):
        super().setSortRole(self._roleKey(role))

    @pyqtProperty(QByteArray)
    def filterRole(self):
        return self._roleNames().get(super().filterRole())

    @filterRole.setter
    def filterRole(self, role):
        super().setFilterRole(self._roleKey(role))

    @pyqtProperty(str)
    def filterString(self):
        return super().filterRegExp().pattern()

    @filterString.setter
    def filterString(self, filter):
        super().setFilterRegExp(QRegExp(filter, super().filterCaseSensitivity(), self.filterSyntax))

    @pyqtProperty(int)
    def filterSyntax(self):
        return super().filterRegExp().patternSyntax()

    @filterSyntax.setter
    def filterSyntax(self, syntax):
        super().setFilterRegExp(QRegExp(self.filterString, super().filterCaseSensitivity(), syntax))

    def filterAcceptsRow(self, sourceRow, sourceParent):
        rx = super().filterRegExp()
        if not rx or rx.isEmpty():
            return True
        model = super().sourceModel()
        sourceIndex = model.index(sourceRow, 0, sourceParent)
        # skip invalid indexes
        if not sourceIndex.isValid():
            return True
        # If no filterRole is set, iterate through all keys
        if not self.filterRole or self.filterRole == "":
            roles = self._roleNames()
            for key, value in roles.items():
                data = model.data(sourceIndex, key)
                if rx.indexIn(data) != -1:
                    return True
            return False
        # Here we have a filterRole set so only search in that
        data = model.data(sourceIndex, self._roleKey(self.filterRole))
        return rx.indexIn(data) != -1

    def _roleKey(self, role):
        roles = self.roleNames()
        for key, value in roles.items():
            if value == role:
                return key
        return -1

    def _roleNames(self):
        source = super().sourceModel()
        if source:
            return source.roleNames()
        return {}

    @pyqtProperty(int)
    def getRow(self):
        """
        Method to get the current row in the QSortFilterProxy model
        :return:
        """
        # for i in self.source.items():
        #     pass
        return -1


class FishSampling(QObject):
    """
    Class for the FishSamplingScreen
    """
    specimensModelChanged = pyqtSignal()
    specialsModelChanged = pyqtSignal()
    speciesFullListModelChanged = pyqtSignal()
    personnelModelChanged = pyqtSignal()
    randomDropsChanged = pyqtSignal()

    specimenRowSelected = pyqtSignal(int, arguments=["row", ])

    specimenSelected = pyqtSignal(QVariant, name="specimenSelected", arguments=["specimen", ])
    # screenOnlySpecimenSelected = pyqtSignal(QVariant, name="screenOnlySpecimenSelected", arguments=["specimen", ])

    exceptionEncountered = pyqtSignal(str, str, arguments=["message", "action"])
    specimenConflictEncountered = pyqtSignal(QVariant, QVariant, QVariant, arguments=["adh", "hookMatrixResult", "tempValues"])

    specimenObservationUpdated = pyqtSignal(int, QVariant, int, QVariant,
                                            arguments=["speciesSamplingPlanId",
                                                       "modelType", "id", "tagNumber"])
    lwRelationshipOutlier = pyqtSignal(str, arguments=["message"])

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db

        self._specimens_model = SpecimensModel(app=self._app, db=self._db)
        self._specials_model = SpecialsModel(app=self._app, db=self._db)
        self._species_full_list_model = SpeciesFullListModel(app=self._app)
        self._personnel_model = PersonnelModel(app=self._app)
        self._current_specimen_index = None
        self._current_specimen = None  # use to track selected specimen vals

        self._random_drops = None

    @pyqtProperty(FramListModel, notify=personnelModelChanged)
    def personnelModel(self):
        """
        Method to return the self._personnel_model.  This is used by the FishSamplingScreen.qml when the
        person clicks on the RecordedBy button for populating the RecordedByDialog.qml ListView.  The person
        then selects who is the cutter form that list
        :return:
        """
        return self._personnel_model

    @pyqtProperty(FramListModel, notify=speciesFullListModelChanged)
    def speciesFullListModel(self):
        """
        Method to return the self._species_full_list_model for use in the FishSamplingEntryDialog.qml
        :return:
        """
        return self._species_full_list_model

    @pyqtProperty(FramListModel, notify=specimensModelChanged)
    def specimensModel(self):
        """
        Methohd to return the self._specimens_model
        :return:
        """
        return self._specimens_model

    @pyqtProperty(int)
    def currentSpecimenIndex(self):
        return self._current_model_index

    @currentSpecimenIndex.setter
    def currentSpecimenIndex(self, ix):
        """
        Set when user selects row from FishSampling tableview.
        Use to set current specimen model so we get most updated data from self._specimens_model
        :param ix: int, model index
        """
        self._current_specimen_index = ix
        # borrowed from FramListModel.get b/c slot IndexError suppressed
        if ix < 0 or ix >= self._specimens_model.count:
            self._current_specimen = None
        else:
            self._current_specimen = self._specimens_model.get(ix)

    @property
    def current_specimen(self):
        return self._current_specimen

    @pyqtProperty(FramListModel, notify=specialsModelChanged)
    def specialsModel(self):
        """
        Method to return the self._specimen_tags_model
        :return:
        """
        return self._specials_model

    @pyqtSlot(QVariant, str, name="upsertADH")
    def upsert_angler_drop_hook(self, dialog_specimen_id: QVariant, value: str):
        """
        Method for dealing with an update to the Angler/Drop/Hook
        :param dialog_specimen_id
        :param value: new value of the observation
        :return: None
        """
        try:
            if len(value) == 3:
                angler = value[0]
                drop = value[1]
                hook = value[2]
            else:
                return

            """
            Check to determine if a SPECIMEN table record has been created for this A/D/H.
            This would be tied to the angler operations record
            """
            catch_id = None
            specimen_id = None
            species = None

            result = self.check_if_specimen_exists(drop=drop, angler=angler, hook=hook)
            logging.info(f"\tspecimen check result: {result}")
            if result:
                specimen_id = result["specimen_id"]     # SPECIMENS.specimen_id
                catch_id = result["catch_id"]           # CATCH.catch_id
                species = result["species"]

                logging.info(f"\tspecimen record found, specimen_id={specimen_id}, catch_id={catch_id}")

            if specimen_id is not None:

                # ADH Specimen (and thus Catch) record exists....

                logging.info(f"A/D/H Use Case #1a:  Specimen record exists, Dialogue Specimen does not, "
                             f"open Specimen record it")
                self.select_specimen_record_by_adh(angler=angler, drop=drop, hook=hook)

                # TODO Todd - Is there a use case here where a cutter has entered a bunch of observations, then
                # he proceeds to type or barcode in an ADH.  We know that a specimen exists for this ADH, but if so,
                # don't we basically lose all of the specimen data that we just collected and is open/acative on the
                # various tabs?  How do we handle this situation?

                # FishSamplingEntryDialog.qml / updateLabel - under the ADH section
                #   this is where the upsertADH method is called.  Basically from that
                #   logic, we could never enter the scenario where both the
                #   Specimen_id exists and the Dialog_Specimen_ID exists.

                # FishSamplingEntryDialog.qml / serialPortDataReceived - ADH section - upsertADH is aalso called here
                #   However it is only called after a checkIfSpecimenExists is called and it returns null,
                #   meaning that, obviously, no specimen record exists and so dialog_specimen_id should be none as well

                # if dialog_specimen_id is None:
                #
                #     logging.info(f"A/D/H Use Case #1a:  Specimen record exists, Dialogue Specimen does not, "
                #                  f"open Specimen record it")
                #     self.select_specimen_record_by_adh(angler=angler, drop=drop, hook=hook)
                #
                # else:
                #
                #     # TODO Todd - Is this scenario even possible
                #     logging.info(f"A/D/H Use Case #1b:  Specimen record exists & Dialog Specimen exists for this ADH")


            else:

                # Get the operation_type
                sql = """
                    SELECT ot.VALUE FROM SPECIMENS s
                        INNER JOIN CATCH c ON s.CATCH_ID = c.CATCH_ID
                        INNER JOIN OPERATIONS o ON o.OPERATION_ID = c.OPERATION_ID
                        INNER JOIN LOOKUPS ot ON o.OPERATION_TYPE_LU_ID = ot.LOOKUP_ID
                        WHERE s.SPECIMEN_ID = ?
                """
                params = [dialog_specimen_id, ]
                operation_type = self._app.rpc.execute_query(sql=sql, params=params)
                if operation_type:
                    operation_type = operation_type[0][0]

                # Get the angler_op_id for the given site, drop, angler
                angler_op_id = self.get_angler_op_id(drop=drop, angler=angler)

                if (dialog_specimen_id is None) or \
                    (dialog_specimen_id is not None and operation_type == 'Angler'):

                    logging.info(f"A/D/H Use Case #2:  Create new specimen record, starting a new A/D/H")
                    logging.info(f"\tdialog_specimen_id={dialog_specimen_id}, operation_type={operation_type}")

                    logging.info(f"\tcatch_id does not exist for {angler}{drop}{hook}, creating one without temp_catch_content_id")
                    catch_id, species = self.get_catch_by_op_and_hook(operation_id=angler_op_id, hook=hook)
                    logging.info(f"\tcatch_id={catch_id}, species={species}")

                    # Create a new specimen record
                    sql = "INSERT INTO SPECIMENS(CATCH_ID) VALUES(?);"
                    params = [catch_id, ]
                    specimen_id = self._app.rpc.execute_query_get_id(sql=sql, params=params)

                    # Append a new SpecimenModel item and emit a signal which is caught by FishSamplingScreen.qml for
                    # updating the table with the new entry
                    item = dict(zip(self.specimensModel.keys, len(self.specimensModel.keys)*[None]))
                    item["specimenID"] = specimen_id
                    item["adh"] = angler + drop + hook
                    item["species"] = species
                    item["ID"] = self.specimensModel.count+1
                    self.specimensModel.appendItem(item=item)
                    logging.info(f"\tmodel item added, row count = {self.specimensModel.count}")

                    self.specimenRowSelected.emit(self.specimensModel.count-1)
                    logging.info(f"\tnew specimensModel item: {item}")

                    # Emit the specimen record as a signal, which is picked up by FishSamplingEntryDialog.qml
                    # to populate the Tabs in the entry dialog.  This is also picked up by FishSamplingScreen.qml
                    # to properly highlight the proper row of the tvSpecimens tables
                    specimen = {"specimenID": specimen_id,
                                "adh": angler + drop + hook,
                                "species": species}
                    logging.info(f"upsertADH")
                    self.specimenSelected.emit(specimen)


                else:
                    """
                    *********************** Use Case #3 - Realign CATCH Operation + receptacle data to proper angler op
                    
                    dialog_specimen_id exists (i.e. is not None) and operation_type != 'Angler'
                    
                    This is the case when entries have been added, yet the specimen's catch record is tied back
                    to the site operation_id.  We need to realign that catch record to the proper Angler operation_id
                    
                    A Cutter entered specimen observations before he or she entered the ADH.  So those
                        observations were created and tied to a specimen record, yet that specimen record was tied back 
                        to the set_id operation as we didn't have an Angler operation id to tie it to
                    """
                    logging.info(f"A/D/H Use Case #3:  Realign CATCH operation + receptacle data to proper angler op")
                    logging.info(f"\tdialog_specimen_id={dialog_specimen_id}")

                    # Retrieve the temp_catch_id - this also returns the CutterStation catch_id + species name, determined by
                    # the specimen_id - i.e. this is the specimen where the ADH was not entered
                    sql = """
                        SELECT c.CATCH_ID, 
                            (SELECT cc.DISPLAY_NAME from CATCH_CONTENT_LU cc 
                                WHERE cc.CATCH_CONTENT_ID = c.CS_CATCH_CONTENT_ID) as DISPLAY_NAME,
                            c.CS_CATCH_CONTENT_ID
                        FROM CATCH c
                            INNER JOIN SPECIMENS s ON s.CATCH_ID = c.CATCH_ID
                        WHERE s.SPECIMEN_ID = ?;
                    """
                    params = [dialog_specimen_id, ]
                    result = self._app.rpc.execute_query(sql=sql, params=params)
                    logging.info(f"\ttrying to find the temporary catch record, result={result}")
                    if result:
                        temp_catch_id = result[0][0]
                        temp_display_name = result[0][1]
                        temp_catch_content = result[0][2]

                        logging.info(
                            f"\tcatch_id does not exist for {angler}{drop}{hook}, creating one with temp_catch_content_id")
                        catch_id, species = self.get_catch_by_op_and_hook(operation_id=angler_op_id, hook=hook,
                                                                          temp_catch_content=temp_catch_content)
                        logging.info(f"\tcatch_id={catch_id}, cutter species={species}")

                        # Step 1 - Update the specimen + children records (found by dialog_specimen_id)
                        #    to use the permanent catch record (given by catch_id)
                        sql = """
                            UPDATE SPECIMENS 
                            SET CATCH_ID = ?
                            WHERE SPECIMEN_ID = ? or PARENT_SPECIMEN_ID = ?;
                        """
                        params = [catch_id, dialog_specimen_id, dialog_specimen_id]
                        self._app.rpc.execute_query(sql=sql, params=params)
                        logging.info(f"\tSpecimen properly realigned to permanent ADH catch record, specimen ID="
                                     f"{dialog_specimen_id} tied to catch_id={catch_id}")

                        # Step 2 - Update the permanent catch record with the CS_CATCH_CONTENT_ID from the temp_catch_id
                        sql = """
                            UPDATE CATCH
                            SET CS_CATCH_CONTENT_ID = ?
                            WHERE CATCH_ID = ?;
                        """
                        params = [temp_catch_content, catch_id]
                        adh = f"{self._app.state_machine.angler}{self._app.state_machine.drop}{self._app.state_machine.hook}"
                        notify = {
                            "speciesUpdate": {"station": "CutterStation", "set_id": self._app.state_machine.setId,
                                              "adh": adh}}
                        logging.info(f"\tNotify parameters for updating the FPC SpeciesReviewDialog = {notify}")

                        self._app.rpc.execute_query(sql=sql, params=params, notify=notify)
                        logging.info(f"\tPermanent ADH catch record (catch_id={catch_id}) updated with the proper species")

                        # Step 3 - Delete the temp_catch_id CATCH record
                        sql = """
                            DELETE FROM CATCH
                            WHERE CATCH_ID = ?;
                        """
                        params = [temp_catch_id, ]
                        self._app.rpc.execute_query(sql=sql, params=params)
                        logging.info(f"\tTemporary catch record successfully deleted, temp_catch_id={temp_catch_id}")

                        # Step 4 - Update the specimenModel record
                        idx = self._specimens_model.get_item_index(rolename="specimenID", value=dialog_specimen_id)
                        self._specimens_model.setProperty(index=idx, property="adh", value=value)

        except Exception as ex:

            logging.error(f"Error handling upsertSpecimen for A/D/H update: {ex}")

    @pyqtSlot(QVariant, name="realignCatchRecord")
    def realign_catch_record(self, temp_values):
        """
        Method to realign the catch record.  This method is initiated via the upsertADH method and gets called when the
        specimenConflictEncountered signal is emitted.  Basically this is when the HookMatrix and CutterStation species
        are different.   Not sure that we'll still need this though once I fix the upsertADH Use Case #3, which is where
        this is initiated

        :param item:
        :return:
        """
        if isinstance(temp_values, QJSValue):
            temp_values = temp_values.toVariant()

        logging.info(f"realignCatch: {temp_values}")

        found_catch_id = temp_values["found_catch_id"]
        hook = temp_values["hook"]
        angler_op_id = temp_values["angler_op_id"]
        temp_catch_id = temp_values["temp_catch_id"]
        dialog_specimen_id = temp_values["dialog_specimen_id"]
        adh = temp_values["adh"]

        # Delete the existing CATCH record first
        sql = "DELETE FROM CATCH WHERE CATCH_ID = ?;"
        params = [found_catch_id, ]
        self._app.rpc.execute_query(sql=sql, params=params)

        # Update the CATCH columns: RECEPTACLE_SEQ, RECEPTACLE_TYPE_ID, OPERATON_ID, OPERATION_TYPE_ID
        sql = """
            UPDATE CATCH SET
                RECEPTACLE_SEQ = ?,
                RECEPTACLE_TYPE_ID = 
                    (SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Receptacle Type' AND Value = 'Hook'),
                OPERATION_ID = ?,
                OPERATION_TYPE_ID = 
                    (SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Operation' AND Value = 'Angler')
            WHERE CATCH_ID = ?;
        """
        params = [hook, angler_op_id, temp_catch_id]
        logging.info(f"\trealigning catch record params, hook={hook}, angler_op_id={angler_op_id},"
                     f"temp_catch_id={temp_catch_id}")

        self._app.rpc.execute_query(sql=sql, params=params)
        logging.info(f"\tcatch record realigned successfully to angler_op_id")

        # Update the specimenModel record
        idx = self._specimens_model.get_item_index(rolename="specimenID", value=dialog_specimen_id)
        self._specimens_model.setProperty(index=idx, property="adh", value=adh)

    @pyqtSlot(QVariant, str, name="upsertSpecies")
    def upsert_species(self, dialog_specimen_id: QVariant, value: str):
        """
        Method to update the species as specified in FishSamplingEntryDialog.qml.

        This method will update an existing, or create a new, catch record with the correct
        catch_content_id and display name for the species as given in the value argument
        :param dialog_specimen_id:  int or None - represents if a specimen exists for this or not
        :param value:  name of the species that will go into the display_name column
        :return:
        """

        try:
            logging.info(f"***** UPSERT_SPECIES:  dialog_specimen_id={dialog_specimen_id}, value={value}")

            if dialog_specimen_id is not None:
                """
                Use Case #1 - Catch Record Exists.  Only update the CATCH record.  This means that the 
                    child specimen record exists as well.
                """
                logging.info(f"Species Use Case #1: Catch record exists, update the species information")

                # Update the CATCH table record
                #  , DISPLAY_NAME = (SELECT DISPLAY_NAME FROM CATCH_CONTENT_LU WHERE DISPLAY_NAME = ?)
                sql = """
                    UPDATE CATCH
                    SET 
                        CS_CATCH_CONTENT_ID = (SELECT CATCH_CONTENT_ID FROM CATCH_CONTENT_LU WHERE DISPLAY_NAME = ?)
                    WHERE 
                        CATCH_ID = 
                            (SELECT ca.CATCH_ID FROM CATCH ca
                            INNER JOIN SPECIMENS s ON s.CATCH_ID = ca.CATCH_ID
                            WHERE s.SPECIMEN_ID = ?)
                """
                params = [value, dialog_specimen_id]
                adh = f"{self._app.state_machine.angler}{self._app.state_machine.drop}{self._app.state_machine.hook}"
                notify = {
                    "speciesUpdate": {"station": "CutterStation", "set_id": self._app.state_machine.setId, "adh": adh}}

                self._app.rpc.execute_query(sql=sql, params=params, notify=notify)

                # Update the specimensModel to reflect the new species
                idx = self._specimens_model.get_item_index(rolename="specimenID", value=dialog_specimen_id)
                logging.info(f"\tparams={params} > modex index={idx}")
                if idx != -1:
                    self._specimens_model.setProperty(index=idx, property="species", value=value)

            else:
                """
                Use Case #2 - Catch Record Does Not Exists
                
                This scenario would only happen if one is examining a new specimen, and the first
                item that he or she pick on the FishSamplingEntryDialog.qml is the Species.  This is 
                a very real scenario, such as when they are missing an Angler/Drop/Hook tag, yet they
                still want to sample the fish.  
                        
                Are there two sub scenarios here:
                2.1 A/D/H has already been selected
                    In this case, a catch record would already exist, so this scenario cannot actually be encountered
                2.2 A/D/H has not been selected
                    This is the only case that can be encountered, 


                QUESTION ??? - Should we be adding in the RECEPTACLE_SEQ anad RECEPTACLE_TYPE_ID here as well
                      I wonder, is this why we have the receptacle_type_id missing for some catch records
                      
                      I added in the RECEPTACLE_TYPE_ID as we always know that ths is coming from a Hook, but I guess
                        we really don't know the RECEPTACLE_SEQ for this case and so must leave it blank for now

                """
                # TODO Todd - Consider adding in the RECEPTACLE_SEQ here as well, for otherwise the CATCH record doesn't have this

                logging.info(f"Species Use Case #2: Catch record does not exist, insert one and a Specimen record as well")

                # Insert a new CATCH table record
                # (SELECT DISPLAY_NAME FROM CATCH_CONTENT_LU WHERE DISPLAY_NAME = ?),
                sql = """
                    INSERT INTO CATCH(CS_CATCH_CONTENT_ID, RECEPTACLE_TYPE_ID, OPERATION_ID, OPERATION_TYPE_ID)
                        VALUES(
                            (SELECT CATCH_CONTENT_ID FROM CATCH_CONTENT_LU WHERE DISPLAY_NAME = ?),
                            (SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Receptacle Type' AND Value = 'Hook'),
                            ?,
                            (SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Operation' AND Value = 'Site')
                        );
                """
                params = [value, self._app.state_machine.siteOpId]
                adh = f"{self._app.state_machine.angler}{self._app.state_machine.drop}{self._app.state_machine.hook}"
                notify = {
                    "speciesUpdate": {"station": "CutterStation", "set_id": self._app.state_machine.setId, "adh": adh}}

                catch_id = self._app.rpc.execute_query_get_id(sql=sql, params=params, notify=notify)
                logging.info(f"\tcatch record inserted, catch_id={catch_id}")

                # Insert a new SPECIMENS table record
                sql = "INSERT INTO SPECIMENS(CATCH_ID) VALUES(?);"
                params = [catch_id, ]
                specimen_id = self._app.rpc.execute_query_get_id(sql=sql, params=params)
                logging.info(f"\tspecimen record inserted, specimen_id={specimen_id}")

                # Append a new record to the specimensModel to reflect the new species
                item = dict(zip(self.specimensModel.keys, len(self.specimensModel.keys) * [None]))
                item["ID"] = self.specimensModel.count + 1
                item["specimenID"] = specimen_id
                item["species"] = value
                logging.info(f"\tnew specimensModel item: {item}")
                self.specimensModel.appendItem(item=item)

                # Emit the specimen record back to the FishSamplingEntryDialog.qml interface
                logging.info(f"upsertSpecies")
                self.specimenSelected.emit(item)

        except Exception as ex:

            logging.error(f"\tError upserting the species: {ex}")

    @pyqtSlot(QVariant, QVariant, QVariant, QVariant, QVariant, name="upsertObservation")
    def upsert_observation(self, dialog_specimen_id: QVariant, model_action: QVariant,
                           value: QVariant, data_type,
                           model_action_subtype=None, species_sampling_plan_id=None,
                           is_special_project=None):
        """
        Method to update any of the observations as specified in FishSamplingEntryDialog.qml
        :param previous_dialog_specimen_id:
        :param dialog_specimen_id:
        :param model_action:
        :param value:
        :param data_type:
        :param model_action_subtype:
        :return:
        """
        logging.info(f"UPSERT_OBSERVATION:  model_action={model_action}, model_action_subtype={model_action_subtype}, value={value}")

        if data_type == "numeric":
            value_column = "NUMERIC_VALUE"
            try:
                value = float(value)
            except Exception as ex:
                message = f"Error converting to a float, value={value}"
                action = "Please try taking the value again"
                logging.error(f"{message}:  {ex}")
                self.exceptionEncountered.emit(message, action)
                return
        else:
            value_column = "ALPHA_VALUE"

        try:
            db_action = self.observation_to_db_mapping(action=model_action)

            # Determine if this observation already exists, if yes, update, if no, insert
            if model_action_subtype is None:
                if species_sampling_plan_id is None:
                    sql = """
                        SELECT s.SPECIMEN_ID, l.LOOKUP_ID FROM SPECIMENS s
                            INNER JOIN LOOKUPS l ON s.ACTION_TYPE_ID = l.LOOKUP_ID
                            WHERE s.PARENT_SPECIMEN_ID = ?
                                AND l.TYPE = 'Observation'
                                AND l.VALUE = ?
                    """
                    params = [dialog_specimen_id, db_action]
                else:
                    sql = """
                        SELECT s.SPECIMEN_ID, l.LOOKUP_ID FROM SPECIMENS s
                            INNER JOIN LOOKUPS l ON s.ACTION_TYPE_ID = l.LOOKUP_ID
                            WHERE s.PARENT_SPECIMEN_ID = ?
                                AND l.TYPE = 'Observation'
                                AND l.VALUE = ?
                                AND s.SPECIES_SAMPLING_PLAN_ID = ?
                    """
                    params = [dialog_specimen_id, db_action, species_sampling_plan_id]

            else:
                if species_sampling_plan_id is None:
                    """
                    CASE:  No species_sampling_plan_id, model_action_subtype exists
                    
                    Normal (non-special) ageID or disposition scenario where the user may have just
                    changed the type of age structure or type of disposition being collected, and the
                    value actually did not change.  Need to determine if an ageID or disposition exists
                    or not"""
                    sql = """
                        SELECT s.SPECIMEN_ID, l.LOOKUP_ID FROM SPECIMENS s
                            INNER JOIN LOOKUPS l ON s.ACTION_TYPE_ID = l.LOOKUP_ID
                            WHERE s.PARENT_SPECIMEN_ID = ?
                                AND l.TYPE = 'Observation'
                                AND l.VALUE = ?
                                AND l.SUBVALUE = ?
                                AND s.SPECIES_SAMPLING_PLAN_ID IS NULL;
                    """
                    params = [dialog_specimen_id, db_action, model_action_subtype]

                else:
                    # species_sampling_plan_id exists, model_action_subtype exists
                    sql = """
                        SELECT s.SPECIMEN_ID, l.LOOKUP_ID FROM SPECIMENS s
                            INNER JOIN LOOKUPS l ON s.ACTION_TYPE_ID = l.LOOKUP_ID
                            WHERE s.PARENT_SPECIMEN_ID = ?
                                AND l.TYPE = 'Observation'
                                AND l.VALUE = ?
                                AND l.SUBVALUE = ?
                                AND s.SPECIES_SAMPLING_PLAN_ID = ?
                    """
                    params = [dialog_specimen_id, db_action, model_action_subtype, species_sampling_plan_id]

            results = self._app.rpc.execute_query(sql=sql, params=params)
            logging.info(f"\tupsertObservation, checking if child specimen record exists > params={params}, results={results}")
            if len(results) > 0:
                """
                Use Case 1: 
                    - parent SPECIMEN_ID exists
                    - child SPECIMEN_ID exists
                """
                logging.info(f"\tObservation Use Case #1:  Child specimen record exists, update it")

                # Update the existing record
                specimen_id = results[0][0]
                if model_action_subtype:
                    # Need to update both the value as well as the action_type_id as they both may have changed
                    sql = "UPDATE SPECIMENS SET " + value_column + " = ?, " + \
                                "ACTION_TYPE_ID = " + \
                          "(SELECT LOOKUP_ID FROM LOOKUPS WHERE " + \
                                "TYPE = 'Observation' AND VALUE = ? AND SUBVALUE = ?) " + \
                          "WHERE SPECIMEN_ID = ?;"
                    params = [value, db_action, model_action_subtype, specimen_id]
                else:
                    # Only update the value
                    sql = "UPDATE SPECIMENS SET " + value_column + " = ? WHERE SPECIMEN_ID = ?"
                    params = [value, specimen_id]
                logging.info(f"\tready to update the observation record, params={params}")
                self._app.rpc.execute_query(sql=sql, params=params)

                # Update the specimenModel record
                idx = self._specimens_model.get_item_index(rolename="specimenID", value=dialog_specimen_id)
                if idx != -1:
                    self._specimens_model.setProperty(index=idx, property=model_action, value=value)
                    if model_action_subtype:
                        typesMap = {"Age ID": "ageType", "Disposition": "dispositionType"}
                        if db_action in typesMap:
                            self._specimens_model.setProperty(index=idx, property=typesMap[db_action],
                                value=model_action_subtype)

            else:

                # Need to update the SPECIMEN ACTION_TYPE_ID to the new DISPOSITION TYPE
                if model_action == "disposition":
                    logging.info(f"disposition was upserted, however the type was changed to {model_action_subtype}")
                    # if species_sampling_plan_id is None:
                    #     sql = """
                    #     SELECT s.SPECIMEN_ID, l.LOOKUP_ID FROM SPECIMENS s
                    #         INNER JOIN LOOKUPS l ON s.ACTION_TYPE_ID = l.LOOKUP_ID
                    #         WHERE s.PARENT_SPECIMEN_ID = ?
                    #             AND l.TYPE = 'Observation'
                    #             AND l.VALUE = ?
                    #             AND s.SPECIES_SAMPLING_PLAN_ID IS NULL;
                    #     """
                    #     params = [dialog_specimen_id, db_action]
                    # else:
                    #     sql = """
                    #         SELECT s.SPECIMEN_ID, l.LOOKUP_ID FROM SPECIMENS s
                    #             INNER JOIN LOOKUPS l ON s.ACTION_TYPE_ID = l.LOOKUP_ID
                    #             WHERE s.PARENT_SPECIMEN_ID = ?
                    #                 AND l.TYPE = 'Observation'
                    #                 AND l.VALUE = ?
                    #                 AND l.SUBVALUE = ?
                    #                 AND s.SPECIES_SAMPLING_PLAN_ID = ?
                    #     """
                    #     params = [dialog_specimen_id, db_action, species_sampling_plan_id]




                if dialog_specimen_id is not None:
                    """
                        Use Case 2:  
                            - parent SPECIMEN_ID exists
                            - child SPECIMEN_ID does not exist
                    """
                    logging.info(f"\tObservation Use Case #2:  Child specimen record does not exist, "
                                 f"but Parent specimen record does")

                    # Insert the new child specimen record
                    if model_action_subtype is None:
                        if species_sampling_plan_id is None:
                            sql = "INSERT INTO SPECIMENS(PARENT_SPECIMEN_ID, CATCH_ID, ACTION_TYPE_ID, " + value_column + ") " + \
                                    "VALUES(?, " + \
                                      "(SELECT CATCH_ID FROM SPECIMENS WHERE SPECIMEN_ID = ?), " \
                                      "(SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Observation' AND Value = ?), ?);"
                            params = [dialog_specimen_id, dialog_specimen_id, db_action, value]
                        else:
                            sql = "INSERT INTO SPECIMENS(PARENT_SPECIMEN_ID, CATCH_ID, ACTION_TYPE_ID, " + \
                                    value_column + ", SPECIES_SAMPLING_PLAN_ID) " + \
                                    "VALUES(?, " + \
                                      "(SELECT CATCH_ID FROM SPECIMENS WHERE SPECIMEN_ID = ?), " \
                                      "(SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Observation' AND Value = ?), ?, ?);"
                            params = [dialog_specimen_id, dialog_specimen_id, db_action, value, species_sampling_plan_id]

                    else:
                        if species_sampling_plan_id is None:
                            sql = "INSERT INTO SPECIMENS(PARENT_SPECIMEN_ID, CATCH_ID, ACTION_TYPE_ID, " + value_column + ") " + \
                                    "VALUES(?, " + \
                                      "(SELECT CATCH_ID FROM SPECIMENS WHERE SPECIMEN_ID = ?), " \
                                      "(SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Observation' AND Value = ? AND Subvalue = ?), ?);"
                            params = [dialog_specimen_id, dialog_specimen_id, db_action, model_action_subtype, value]
                        else:
                            sql = "INSERT INTO SPECIMENS(PARENT_SPECIMEN_ID, CATCH_ID, ACTION_TYPE_ID, " + \
                                    value_column + ", SPECIES_SAMPLING_PLAN_ID) " + \
                                    "VALUES(?, " + \
                                      "(SELECT CATCH_ID FROM SPECIMENS WHERE SPECIMEN_ID = ?), " \
                                      "(SELECT LOOKUP_ID FROM LOOKUPS " \
                                            "WHERE Type = 'Observation' AND Value = ? AND Subvalue = ?), ?, ?);"
                            params = [dialog_specimen_id, dialog_specimen_id, db_action,
                                      model_action_subtype, value, species_sampling_plan_id]

                    specimen_id = self._app.rpc.execute_query_get_id(sql=sql, params=params)
                    logging.info(f"\tnewly added specimen child record: {specimen_id}")

                    # Update the specimenModel record
                    idx = self._specimens_model.get_item_index(rolename="specimenID", value=dialog_specimen_id)

                    if is_special_project:

                        self.specimenObservationUpdated.emit(species_sampling_plan_id, model_action,
                                                             specimen_id, value)
                        if idx != -1:
                            special_item = self._specimens_model.get(idx)['special']
                            special_abbrev = "WS" if model_action == "wholeSpecimenID" else model_action[0:2].upper()
                            logging.info(f"\tnew abbreviation addition = {special_abbrev}, existing special item={special_item}")
                            if special_abbrev not in special_item:
                                special_list = sorted(special_item.split(",") + [special_abbrev])
                                new_special_item = ",".join(special_list).strip(",")
                                logging.info(f"new_special_item={new_special_item}")
                                self._specimens_model.setProperty(index=idx, property="special", value=new_special_item)

                    else:

                        if idx != -1:
                            self._specimens_model.setProperty(index=idx, property=model_action, value=value)
                            if model_action_subtype:
                                typesMap = {"Age ID": "ageType", "Disposition": "dispositionType"}
                                if db_action in typesMap:
                                    logging.info(f"map={typesMap[db_action]}, value={model_action_subtype}")
                                    self.specimensModel.setProperty(index=idx, property=typesMap[db_action],
                                                                    value=model_action_subtype)

                else:
                    """
                    Use Case 3:  
                        - parent SPECIMEN_ID does not exist
                        - child SPECIMEN_ID does not exist
                        
                    How do I get the catch_id ???  Need to go back to the CATCH table record
                     
                    Actually, for this case, it only occurs when we have a blank slate for the FishSamplingEntryDialog
                    and the user decides to add an observation.  As a result, since we don't have an A/D/H,
                    we need to use the sites operation_id and create a new CATCH record first that reference this
                    sites operation_id.  Note that later when this fish is assigned to an A/D/H, that this 
                    temporary CATCH table record must be deleted.
                    
                    N.B. This Use Case #3 should only happen once per a given fish, i.e. the first time when an 
                        observation is added and the parent specimen record does not exist yet
                        
                    """
                    logging.info(f"\tObservation Use Case #3:  Parent and child specimen IDs both do NOT exist, "
                                 f"must insert both")

                    # Insert a new CATCH table record, tied back to the site operation_id
                    sql = """
                        INSERT INTO CATCH(OPERATION_ID, OPERATION_TYPE_ID, RECEPTACLE_TYPE_ID)
                            VALUES(?,
                                (SELECT l.LOOKUP_ID FROM LOOKUPS l WHERE Type = 'Operation' AND Value = 'Site'),
                                (SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Receptacle Type' AND Value = 'Hook')
                            )
                    """
                    params = [self._app.state_machine.siteOpId, ]

                    # TODO Todd Hay - Notification for RpcServer when adding an observation with no ADH
                    """
                    Future item, add some notification to the RpcServer for a listing of these types
                    of fish on the FPC SpeciesReviewDialog, so the FPC can immediately see when the Cutter is working
                    with a fish that does not have an ADH designation
                    """

                    catch_id = self._app.rpc.execute_query_get_id(sql=sql, params=params)
                    logging.info(f"\tnewly added catch record: {catch_id}, precursor for adding the new observation")

                    # Insert a new parent SPECIMEN record
                    sql = "INSERT INTO SPECIMENS(CATCH_ID) VALUES (?);"
                    params = [catch_id, ]
                    parent_specimen_id = self._app.rpc.execute_query_get_id(sql=sql, params=params)
                    logging.info(f"\tnewly added parent specimen record: {parent_specimen_id}")

                    # Insert a new child SPECIMEN record
                    if model_action_subtype is None:
                        if species_sampling_plan_id is None:
                            sql = "INSERT INTO SPECIMENS(PARENT_SPECIMEN_ID, CATCH_ID, ACTION_TYPE_ID, " + value_column + ") " + \
                                    "VALUES(?, ?, " \
                                      "(SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Observation' AND Value = ?), ?);"
                            params = [parent_specimen_id, catch_id, db_action, value]
                        else:
                            sql = "INSERT INTO SPECIMENS(PARENT_SPECIMEN_ID, CATCH_ID, ACTION_TYPE_ID, " + \
                                    value_column + ", SPECIES_SAMPLING_PLAN_ID) " + \
                                    "VALUES(?, ?, " \
                                      "(SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Observation' AND Value = ?), ?, ?);"
                            params = [parent_specimen_id, catch_id, db_action, value, species_sampling_plan_id]

                    else:
                        if species_sampling_plan_id is None:
                            sql = "INSERT INTO SPECIMENS(PARENT_SPECIMEN_ID, CATCH_ID, ACTION_TYPE_ID, " + value_column + ") " + \
                                    "VALUES(?, ?, " \
                                      "(SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Observation' AND Value = ? AND Subvalue = ?), ?);"
                            params = [parent_specimen_id, catch_id, db_action, model_action_subtype, value]
                        else:
                            sql = "INSERT INTO SPECIMENS(PARENT_SPECIMEN_ID, CATCH_ID, ACTION_TYPE_ID, " + \
                                        value_column + ", SPECIES_SAMPLING_PLAN_ID) " + \
                                    "VALUES(?, ?, " \
                                      "(SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Observation' AND Value = ? AND Subvalue = ?), ?, ?);"
                            params = [parent_specimen_id, catch_id, db_action, model_action_subtype,
                                      value, species_sampling_plan_id]

                    specimen_id = self._app.rpc.execute_query_get_id(sql=sql, params=params)

                    logging.info(f"\tnewly added specimen child record: {specimen_id}")

                    # Append a new SpecimenModel item, this adds it to the FishSamplingScreen.qml Table
                    item = dict(zip(self.specimensModel.keys, len(self.specimensModel.keys)*[None]))
                    item["specimenID"] = parent_specimen_id
                    item["ID"] = self.specimensModel.count+1
                    item[model_action] = value
                    logging.info(f"\tnew specimensModel item: {item}")
                    self.specimensModel.appendItem(item=item)
                    # self.specimensModel.sort(rolename="adh")

                    # Select the specimen record, which in turn emits it back to the UI.  Do this after the
                    # specimen record has been added to the self.specimensModel as the below method call in
                    # turn emits the self.specimenSelected signal, which highlights and scrolls to the row in
                    # the FishSamplingScreen.qml If the model hasn't been updated first, then that will cause
                    # an index out of range error
                    self.select_specimen_record_by_id(specimen_id=parent_specimen_id)

        except Exception as ex:

            logging.error(f"Error upserting the specimen child record: {ex}")

    def _get_lw_relationship_params(self, taxonomy_id, sex_code):
        """
        #94: get coefficient, exponent, and tolerance from
        LENGTH_WEIGHT_RELATIONSHIP_LU and SETTINGS tables
        :param taxonomy_id: int, unique id for specimen taxonomy
        :param sex_code: str, M (Male), F (Female), U (unsexed)
        :return: dict{coeff(a): float, exponent(b): float, tolerance(t): float}
        """
        try:
            results = self._app.rpc.execute_query(
                sql='''
                        select  lw_coefficient_cmkg as coefficient_a
                                ,lw_exponent_cmkg as exponent_b
                                ,(select value from settings where parameter = 'Length Weight Relationship Tolerance') t
                        from    length_weight_relationship_lu
                        where   taxonomy_id = ?
                                and sex_code = ?
                                and lw_coefficient_cmkg is not null
                                and lw_exponent_cmkg is not null
                    ''',
                params=[taxonomy_id, sex_code]
            )
        except Exception as e:
            logging.warning(f"Unable to retrieve Length/Weight relationship params; {e}")
            return {}
        try:
            return [{'a': r[0], 'b': r[1], 't': r[2]} for r in results][0]
        except IndexError as e:
            logging.info(f"LW relationship parameters not available for taxonomy {taxonomy_id} sex {sex_code}; {e}")
            return {}

    @staticmethod
    def unabbreviate_sex(sex_abbrev):
        """
        :param sex_abbrev: string.  M, F, U
        :return: Male, Female, Unsexed
        """
        try:
            return dict([('F', 'Female'), ('M', 'Male'), ('U', 'Unsexed')])[sex_abbrev]
        except KeyError:
            return None

    @pyqtSlot(name="checkLWRelationship")
    def check_lw_relationship(self):
        """
        #94: Use length, weight, coefficient, and exponent value for current specimen species
        to determine if the two are within the tolerated range.
        Coefficient and exponent are pulled based on taxonomy_id and sex code from length_weight_relationship_lu
        Tolerance value is pulled and set in SETTINGS table

        W = aL^b
        log W = log a + b·log L
        :return: None; Emit message for display in FishSamplingEntryDialog.qml
        """
        # no current specimen, no calculation
        if not self._current_specimen:
            return
        specimen = self._current_specimen
        lw_params = self._get_lw_relationship_params(specimen['taxonomyID'], specimen['sex'])

        # parse and convert all values to float, catch and return if any fail
        try:
            l = float(specimen['length'])  # entered specimen length (cm)
            w = float(specimen['weight'])  # entered specimen weight (kg)
            a = float(lw_params['a'])  # coefficient in equation W = aL^b
            b = float(lw_params['b'])  # exponent in equation W = aL^b
            t = float(lw_params['t'])  # tolerance value pulled from SETTINGS table
        except (KeyError, TypeError) as e:
            logging.info(f"Unable to obtain len/wt/a/b/t param(s) for {specimen['species']}; {e}")
            return

        logging.info(f"Weight Entered: {w}. Length Entered: {l}, a: {a}, b: {b}")

        # calc expected values
        expected_wt = self.get_expected_wt_from_len(l, a, b)
        logging.info(f"Expected Weight using Length {l} = {expected_wt}")
        expected_len = self.get_expected_len_from_wt(w, a, b)
        logging.info(f"Expected Length Using Weight {w} = {expected_len}")

        # get ranges
        exp_wt_lower, exp_wt_upper = self.get_tolerated_range(expected_wt, t)
        exp_len_lower, exp_len_upper = self.get_tolerated_range(expected_len, t)

        # check if either is not between
        if not exp_wt_lower <= w <= exp_wt_upper or not exp_len_lower <= l <= exp_len_upper:
            logging.info(f"wt {w} not between {exp_wt_lower} and {exp_wt_upper} based on len {l}")
            logging.info(f"l {l} not between {exp_len_lower} and {exp_len_upper} based on len {l}")
            msg = f'''
                    Warning: Length-Weight Outlier!
                    ------------------------------------------
                    Species:\t\t{specimen['species']}
                    Sex:\t\t\t{self.unabbreviate_sex(specimen['sex'])}
                    Entered Weight:\t{w} kg
                    Entered Length:\t{l} cm
                    
                    Expected length at {w} kg: 
    
                        {round(exp_len_lower, 2)} - {round(exp_len_upper, 2)} cm
                    
                    Expected weight at {l} cm:
    
                        {round(exp_wt_lower, 2)} - {round(exp_wt_upper, 2)} kg
                    ------------------------------------------
                '''

            self.lwRelationshipOutlier.emit(msg)

    @staticmethod
    def get_expected_wt_from_len(length, coeff, expon):
        """
        #94: calculate expected weight from entered length
        https://www2.dnr.state.mi.us/publications/pdfs/ifr/manual/smii%20chapter17.pdf
        Fish length-weight relationship can be written as (solving for W)
        W = aL^b --> log W = log a + b·log L --> W = 10^(log a + b * log10(L)))
        *Both coefficient and exponent values are alread on log scale
        :param len: actual measured length of fish (cm)
        :param coeff: logarithmic coefficient stored in LENGHTH_WEIGHT_RELATIONSHIP_LU per taxon and sex
        :param expon: logarithmic exponent stored in LENGHTH_WEIGHT_RELATIONSHIP_LU per taxon and sex
        :return: float, expected fish weight
        """
        logging.debug(f"Calculating exp. fish weight w/ W = aL^b --> {coeff}*{length}^{expon}")
        try:
            return float(coeff) * float(length)**float(expon)
        except TypeError:  # if param of None is passed in
            return None

    @staticmethod
    def get_expected_len_from_wt(weight, coeff, expon):
        """
        #94: calculate expected length from entered weight
        https://www2.dnr.state.mi.us/publications/pdfs/ifr/manual/smii%20chapter17.pdf
        Fish length-weight relationship can be written as (solving for L)
        W = aL^b --> log W = log a + b·log L --> 10^((log10(W) - log a)/b)
        *Both coefficient and exponent values are alread on log scale
        :param len: actual measured length of fish
        :param coeff: logarithmic coefficient stored in LENGHTH_WEIGHT_RELATIONSHIP_LU per taxon and sex
        :param expon: logarithmic exponent stored in LENGHTH_WEIGHT_RELATIONSHIP_LU per taxon and sex
        :return: float, expected fish length
        """
        logging.debug(f"Calculating exp. fish length w/ L = (W/a)^(1/b) --> ({weight}/{coeff})^(1/{expon})")
        try:
            return (float(weight)/float(coeff))**(1/float(expon))
        except TypeError:  # if param of None is passed in
            return None

    @staticmethod
    def get_tolerated_range(val, tolerance):
        """
        apply tolerance to value to get upper and lower bounds
        :param val: number
        :param tolerance: float
        :return: tuple; (lower bound, upper bound)
        """
        try:
            return val * (1.0-float(tolerance)), val * (1.0+float(tolerance))
        except TypeError:  # if param of None is passed in
            return None, None

    @pyqtSlot(str, name="observationToDbMapping", result=str)
    def observation_to_db_mapping(self, action: str) -> str:
        """
        This method provides a mapping from the SpecimenModel roles to the Database Observation Lookup types
        :param action:
        :return:
        """
        mapping = {"ageID": "Age ID", "disposition": "Disposition", "finclipID": "Finclip ID",
                   "length": "Length", "sex": "Sex", "special": "Special", "species": "Species",
                   "weight": "Weight", "adh": "A-D-H", "ovaryID": "Ovary ID",
                   "stomachID": "Stomach ID", "tissueID": "Tissue ID",
                   "wholeSpecimenID": "Whole Specimen ID"}
        result = mapping[action]
        # logging.info(f"mapped result: {action} -> {result}")
        return result

    def get_angler_op_id(self, drop: object, angler: object) -> object:
        """
        Method to return the angler operation id
        :param drop:
        :param angler:
        :return:
        """
        try:
            logging.info(f"get_angler_op_id, drop={drop}, angler={angler}")

            drop = int(drop)        # TODO Todd Hay - Not sure why I'm converting to an int here, that seems wrong
            sql = """
                WITH RECURSIVE 
                    ops_children(n) AS (
                        SELECT OPERATION_ID FROM OPERATIONS WHERE OPERATION_NUMBER = ?
                        UNION
                        SELECT o.OPERATION_ID FROM OPERATIONS o, ops_children
                            WHERE o.PARENT_OPERATION_ID = ops_children.n
                    )
                SELECT OPERATION_ID FROM
                (
                    SELECT o.OPERATION_ID,
                        o.OPERATION_NUMBER as Angler,
                        (SELECT o2.OPERATION_NUMBER FROM OPERATIONS as o2
                            WHERE o2.OPERATION_ID = o.PARENT_OPERATION_ID) as DropNum
                    FROM OPERATIONS o 
                        INNER JOIN LOOKUPS ot ON ot.LOOKUP_ID = o.OPERATION_TYPE_LU_ID
                    WHERE o.OPERATION_ID IN ops_children
                        AND ot.TYPE = 'Operation' 
                        AND ot.VALUE = 'Angler'               
                        AND DropNum = ?
                        AND Angler = ?
                )        
            """
            params = [self._app.state_machine.setId, drop, angler]
            angler_op_id = self._app.rpc.execute_query(sql=sql, params=params)
            if angler_op_id:
                return angler_op_id[0][0]

            else:
                # Create a new angler_op_id if none exists.

                # Need to check if the parent Drop_ID exists first in order to do this.
                sql = """
                SELECT drops.OPERATION_ID as 'Drop ID'
                    FROM OPERATIONS as sites 
                        LEFT JOIN OPERATIONS as drops ON drops.PARENT_OPERATION_ID = sites.OPERATION_ID
                    WHERE
                        sites.OPERATION_NUMBER = ?
                        and drops.OPERATION_NUMBER = ?;
                """
                params = [self._app.state_machine.setId, drop]
                results = self._app.rpc.execute_query(sql=sql, params=params)
                logging.info(f"\tchecking if a drop_op_id exists, results = {results}")

                drop_op_id = None
                if results:
                    drop_op_id = results[0][0]
                else:
                    sql = """
                        INSERT INTO OPERATIONS
                            (PARENT_OPERATION_ID, OPERATION_NUMBER, OPERATION_TYPE_LU_ID)
                        VALUES(
                            ?,
                            ?,
                            (SELECT LOOKUP_ID FROM LOOKUPS WHERE TYPE = 'Operation' AND VALUE = 'Drop')
                        );
                    """
                    params = [self._app.state_machine.siteOpId, drop]
                    results = self._app.rpc.execute_query_get_id(sql=sql, params=params)
                    if results:
                        logging.info(f"\tinserted drop_op_id = {results}")
                        drop_op_id = results

                logging.info(f"\tdrop_op_id = {drop_op_id}")

                # Given that we now have a drop_op_id, now insert a new angler into the operations table
                if drop_op_id:
                    sql = """
                        INSERT INTO OPERATIONS
                            (PARENT_OPERATION_ID, OPERATION_NUMBER, OPERATION_TYPE_LU_ID)
                        VALUES(
                            ?,
                            ?,
                            (SELECT LOOKUP_ID FROM LOOKUPS WHERE TYPE = 'Operation' AND VALUE = 'Angler')
                        );
                    """
                    params = [drop_op_id, angler]
                    results = self._app.rpc.execute_query_get_id(sql=sql, params=params)
                    if results:
                        logging.info(f"\tinserted angler_op_id = {results}")
                        return results

        except Exception as ex:

            logging.error(f"Error retrieving the angler_op_id: {ex}")

        return None

    def get_catch_by_op_and_hook(self, operation_id: int, hook: str, temp_catch_content: int=None):
        """
        Method to retrieve or create a catch record given the angler operation_id and hook number
        :param operation_id:
        :param hook:
        :param temp_catch_content:
        :return:
        """
        try:
            catch_id = None
            species = None

            # Get the catch from the provided angler op id and hook
            sql = """
                SELECT c.CATCH_ID, 
                   (SELECT cc.DISPLAY_NAME from CATCH_CONTENT_LU cc 
                        WHERE cc.CATCH_CONTENT_ID = c.CS_CATCH_CONTENT_ID) as DISPLAY_NAME,
                   c.CS_CATCH_CONTENT_ID,
                   c.HM_CATCH_CONTENT_ID,
                  (SELECT cc.DISPLAY_NAME from CATCH_CONTENT_LU cc 
                        WHERE cc.CATCH_CONTENT_ID = c.HM_CATCH_CONTENT_ID) as HM_SPECIES
                FROM CATCH c
                WHERE
                    c.RECEPTACLE_SEQ = ? AND
                    c.RECEPTACLE_TYPE_ID = (SELECT LOOKUP_ID FROM LOOKUPS 
                                            WHERE Type = 'Receptacle Type' AND Value = 'Hook') AND
                    c.OPERATION_ID = ? AND
                    c.OPERATION_TYPE_ID = (SELECT LOOKUP_ID FROM LOOKUPS 
                                            WHERE Type = 'Operation' AND Value = 'Angler')
            """
            params = [hook, operation_id]

            logging.info(f"\tsearch for an existing catch based on the hook={hook} and operation_id={operation_id}")
            catch_result = self._app.rpc.execute_query(sql=sql, params=params)
            logging.info(f"\tcatch search result={catch_result}")

            if catch_result:
                catch_id = catch_result[0][0]
                species = catch_result[0][1]
                cs_catch_content = catch_result[0][2]
                hm_catch_content = catch_result[0][3]

                if cs_catch_content is None and hm_catch_content is not None:
                    # Update CS_CATCH_CONTENT_ID in the catch record to match the HookMatrix HM_CATCH_CONTENT_ID column
                    sql = """
                        UPDATE CATCH
                            SET CS_CATCH_CONTENT_ID = ?
                        WHERE CATCH_ID = ?;
                    """

                    # Edge case - if a temp_catch_content is provided, this means that we're in upsertADH Use Case #3
                    #   whereby the cutter had been entering some observations, to include potentially the species
                    #   and then enters the ADH.  We are about to update the CS_CATCH_CONTENT_ID so in this case, we
                    #   need to use the temp_catch_content that the user had already entered into the
                    #   FishSamplingEntryDialog.qml and that comes from the temp catch record.
                    if temp_catch_content:
                        logging.info(f"\tupdating the cs_catch_content to the temp_catch_content={temp_catch_content}")
                        params = [temp_catch_content, catch_id]
                        species = "Not retrieved, already in the Species Tab"
                    else:
                        logging.info(f"\tupdating the cs_catch_content to HookMatrix hm_catch_content_id={hm_catch_content}")
                        params = [hm_catch_content, catch_id]
                        species = catch_result[0][4]

                    adh = f"{self._app.state_machine.angler}{self._app.state_machine.drop}{self._app.state_machine.hook}"
                    notify = {
                        "speciesUpdate": {"station": "CutterStation", "set_id": self._app.state_machine.setId,
                                          "adh": adh}}
                    logging.info(f"\tnotify parameters for updating the FPC SpeciesReviewDialog = {notify}")
                    self._app.rpc.execute_query(sql=sql, params=params, notify=notify)

                logging.info(f"\texisting catch_id found: {catch_id}")
            else:
                sql = """
                    INSERT INTO CATCH (RECEPTACLE_SEQ, RECEPTACLE_TYPE_ID, OPERATION_ID, OPERATION_TYPE_ID)
                        VALUES(
                            ?,
                            (SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Receptacle Type' AND Value = 'Hook'),
                            ?,
                            (SELECT LOOKUP_ID FROM LOOKUPS WHERE Type = 'Operation' AND Value = 'Angler')
                        )
                """
                params = [hook, operation_id]

                adh = f"{self._app.state_machine.angler}{self._app.state_machine.drop}{self._app.state_machine.hook}"
                notify = {
                    "speciesUpdate": {"station": "CutterStation", "set_id": self._app.state_machine.setId, "adh": adh}}
                logging.info(f"\tnotify parameters for updating the FPC SpeciesReviewDialog = {notify}")

                catch_id = self._app.rpc.execute_query_get_id(sql=sql, params=params, notify=notify)
                logging.info(f"\tnew catch record created: {catch_id}")

        except Exception as ex:

            logging.error(f"Error retrieving the catch ID: {ex}")

        return catch_id, species

    @pyqtSlot(str, str, str, name="checkIfSpecimenExists", result=QVariant)
    def check_if_specimen_exists(self, drop: str, angler: str, hook: str):
        """
        Method to check if a SPECIMEN record exists for the provided drop/angler/hook
        :param drop: 1 - 5, representinng the drop number
        :param angler: A, B, C - representing the angler
        :param hook: 1 - 5, representing the hook number
        :return:
        """
        try:
            logging.info(f"checkIfSpecimenExists:  angler={angler}, drop={drop}, hook={hook}")
            sql = """
                WITH RECURSIVE 
                        ops_children(n) AS (
                                SELECT OPERATION_ID FROM OPERATIONS WHERE OPERATION_NUMBER = ?
                                UNION
                                SELECT o.OPERATION_ID FROM OPERATIONS o, ops_children
                                        WHERE o.PARENT_OPERATION_ID = ops_children.n
                        )
                SELECT 
                        s.SPECIMEN_ID,
                        c.CATCH_ID,
                        c.OPERATION_ID AS OPERATION_ID,
                        s.PARENT_SPECIMEN_ID,
                        o.OPERATION_NUMBER as Angler,
                        (SELECT o2.OPERATION_NUMBER FROM OPERATIONS as o2 WHERE o2.OPERATION_ID = o.PARENT_OPERATION_ID) as DropNum,
                        c.RECEPTACLE_SEQ as Hook,
                        c.CS_CATCH_CONTENT_ID,
                        (SELECT cc.DISPLAY_NAME from CATCH_CONTENT_LU cc 
                            WHERE cc.CATCH_CONTENT_ID = c.CS_CATCH_CONTENT_ID) as SPECIES,
                        c.HM_CATCH_CONTENT_ID,
                        (SELECT cc.DISPLAY_NAME from CATCH_CONTENT_LU cc 
                            WHERE cc.CATCH_CONTENT_ID = c.HM_CATCH_CONTENT_ID) as hm_species
                FROM OPERATIONS o
                INNER JOIN LOOKUPS ot ON ot.LOOKUP_ID = o.OPERATION_TYPE_LU_ID
                LEFT JOIN CATCH c ON c.OPERATION_ID = o.OPERATION_ID
                LEFT JOIN LOOKUPS rt ON rt.LOOKUP_ID = c.RECEPTACLE_TYPE_ID
                LEFT JOIN SPECIMENS s ON s.CATCH_ID = c.CATCH_ID
                WHERE o.OPERATION_ID IN ops_children
                        AND ot.TYPE = 'Operation' 
                        AND (ot.VALUE = 'Angler' OR ot.VALUE = 'Site')               
                        AND (s.PARENT_SPECIMEN_ID IS NULL AND s.SPECIMEN_ID IS NOT NULL)
                        AND DropNum = ?
                        AND Angler = ?
                        AND Hook = ?
                ORDER BY Angler, DropNum, Hook
            """
            params = [self._app.state_machine.setId, drop, angler, hook]
            results = self._app.rpc.execute_query(sql=sql, params=params)
            keys = ["specimen_id", "catch_id", "operation_id", "parent_specimen_id", "angler", "drop", "hook",
                    "cs_catch_content_id", "species", "hm_catch_content_id", "hm_species"]
            result = None
            for values in results:
                result = dict(zip(keys, values))
                break

            logging.info(f"\tparams={params}, result={result}")
            return result

        except Exception as ex:

            logging.error(f"Error determining a specimen record exists for A/D/H: {ex}")

    @pyqtSlot(str, str, str, name="selectSpecimenRecordByADH")
    def select_specimen_record_by_adh(self, angler: str, drop: str, hook: str):
        """
        Method to retrieve the specimen record based on the given drop, angler, hook
        :param drop: 1 - 5, representing the drop number
        :param angler:  A, B, or C - representing the angler letter
        :param hook:  1 - 5, representing the hook number
        :return:
        """
        logging.info(f"selectSpecimenByADH: angler={angler}, drop={drop}, hook={hook}")
        if not angler or not drop or not hook:
            logging.error(f"\tError attempting to get the specimen record, drop/angler/hook is null")
            return

        try:
            sql = """
                WITH RECURSIVE 
                    ops_children(n) AS (
                        SELECT OPERATION_ID FROM OPERATIONS WHERE OPERATION_NUMBER = ?
                        UNION
                        SELECT o.OPERATION_ID FROM OPERATIONS o, ops_children
                                                WHERE o.PARENT_OPERATION_ID = ops_children.n
                    ),
                    parent_specimen(SPECIMEN_ID, adh, cs_catch_content_id, species, taxonomy_id) as (
                        SELECT 
                            s.SPECIMEN_ID,
                            o.OPERATION_NUMBER ||
                            (SELECT o2.OPERATION_NUMBER FROM OPERATIONS as o2 
                                WHERE o2.OPERATION_ID = o.PARENT_OPERATION_ID) ||
                            c.RECEPTACLE_SEQ as "adh",
                            c.CS_CATCH_CONTENT_ID,
                            (SELECT cc.DISPLAY_NAME from CATCH_CONTENT_LU cc 
                                WHERE cc.CATCH_CONTENT_ID = c.CS_CATCH_CONTENT_ID) as Species,
                            -- c.DISPLAY_NAME as Species,
                            (SELECT cc.taxonomy_id from CATCH_CONTENT_LU cc 
                                WHERE cc.CATCH_CONTENT_ID = c.CS_CATCH_CONTENT_ID) as taxonomy_id
                        FROM OPERATIONS o
                        INNER JOIN LOOKUPS ot ON ot.LOOKUP_ID = o.OPERATION_TYPE_LU_ID
                        LEFT JOIN CATCH c ON c.OPERATION_ID = o.OPERATION_ID
                        LEFT JOIN SPECIMENS s ON s.CATCH_ID = c.CATCH_ID
                        WHERE o.OPERATION_ID IN ops_children
                                AND ot.TYPE = 'Operation' 
                                AND (ot.VALUE = 'Angler' OR ot.VALUE = 'Site')
                                AND s.PARENT_SPECIMEN_ID IS NULL
                                AND s.SPECIMEN_ID IS NOT NULL
                    )
                    SELECT ps.SPECIMEN_ID as specimenID
                        , ps.adh as adh
                        , ps.species as species
                        , ps.taxonomy_id as taxonomyID
                        , ps.cs_catch_content_id as catchContentID
                        , MAX(CASE WHEN l.VALUE = 'Sex' THEN s.ALPHA_VALUE END) AS sex
                        , MAX(CASE WHEN l.VALUE = 'Sex' THEN s.SPECIMEN_ID END) AS sexRecID
                        , MAX(CASE WHEN l.VALUE = 'Length' THEN s.NUMERIC_VALUE END) AS length
                        , MAX(CASE WHEN l.VALUE = 'Length' THEN s.SPECIMEN_ID END) AS lengthRecID
                        , MAX(CASE WHEN l.VALUE = 'Weight' THEN s.NUMERIC_VALUE END) AS weight
                        , MAX(CASE WHEN l.VALUE = 'Weight' THEN s.SPECIMEN_ID END) AS weightRecID
                        , MAX(CASE WHEN l.VALUE = 'Age ID' AND
                                        s.species_sampling_plan_id IS NULL THEN s.ALPHA_VALUE END) AS ageID
                        , MAX(CASE WHEN l.VALUE = 'Age ID' AND
                                        s.species_sampling_plan_id IS NULL THEN s.SPECIMEN_ID END) AS ageRecID
                        , MAX(CASE WHEN l.VALUE = 'Age ID' AND
                                        s.species_sampling_plan_id IS NULL THEN l.SUBVALUE END) AS ageType
                        , MAX(CASE WHEN l.VALUE = 'Stomach ID' THEN s.ALPHA_VALUE END) AS stomachID
                        , MAX(CASE WHEN l.VALUE = 'Stomach ID' THEN s.SPECIMEN_ID END) AS stomachRecID
                        , MAX(CASE WHEN l.VALUE = 'Tissue ID' THEN s.ALPHA_VALUE END) AS tissueID
                        , MAX(CASE WHEN l.VALUE = 'Tissue ID' THEN s.SPECIMEN_ID END) AS tissueRecID
                        , MAX(CASE WHEN l.VALUE = 'Ovary ID' THEN s.ALPHA_VALUE END) AS ovaryID
                        , MAX(CASE WHEN l.VALUE = 'Ovary ID' THEN s.SPECIMEN_ID END) AS ovaryRecID
                        , MAX(CASE WHEN l.VALUE = 'Finclip ID' THEN s.ALPHA_VALUE END) AS finclipID
                        , MAX(CASE WHEN l.VALUE = 'Finclip ID' THEN s.SPECIMEN_ID END) AS finclipRecID
                        , MAX(CASE WHEN l.VALUE = 'Intestine ID' THEN s.ALPHA_VALUE END) AS intestineID
                        , MAX(CASE WHEN l.VALUE = 'Intestine ID' THEN s.SPECIMEN_ID END) AS intestineRecID
                        , MAX(CASE WHEN l.VALUE = 'Disposition' THEN s.ALPHA_VALUE END) AS disposition
                        , MAX(CASE WHEN l.VALUE = 'Disposition' THEN s.SPECIMEN_ID END) AS dispositionRecID                       
                        , MAX(CASE WHEN l.VALUE = 'Tag ID' THEN s.ALPHA_VALUE END) AS tagID
                        , MAX(CASE WHEN l.VALUE = 'Tag ID' THEN s.SPECIMEN_ID END) AS tagRecID   
                        , MAX(CASE WHEN l.VALUE = 'Whole Specimen ID' THEN s.ALPHA_VALUE END) AS wholeSpecimenID
                        , MAX(CASE WHEN l.VALUE = 'Whole Specimen ID' THEN s.SPECIMEN_ID END) AS wholeSpecimenRecID                                             
                        , MAX(CASE WHEN l.VALUE = 'Disposition' THEN l.SUBVALUE END) AS dispositionType
                        , s.species_sampling_plan_id as species_sampling_plan_id
                        , MAX(CASE WHEN l.VALUE = 'Age ID' AND l.SUBVALUE = 'Finray' AND
                                        s.species_sampling_plan_id IS NOT NULL THEN s.ALPHA_VALUE END) AS ageFinRayID                        
                        , MAX(CASE WHEN l.VALUE = 'Age ID' AND l.SUBVALUE = 'Finray' AND
                                        s.species_sampling_plan_id IS NOT NULL THEN s.SPECIMEN_ID END) AS ageFinRayRecID
                    FROM parent_specimen ps
                        LEFT JOIN SPECIMENS s on ps.SPECIMEN_ID = s.PARENT_SPECIMEN_ID
                        LEFT JOIN LOOKUPS l ON l.LOOKUP_ID = s.ACTION_TYPE_ID
                    WHERE adh = ?
                    GROUP BY specimenID
                    ORDER BY adh
            """
            params = [self._app.state_machine.setId, angler + drop + hook]
            results = self._app.rpc.execute_query(sql=sql, params=params)
            for values in results:
                specimen = dict(zip(self.specimensModel.keys, values))
                logging.info(f"\tselectSpecimenByADH, params={params}, results={specimen}")
                self.specimenSelected.emit(specimen)

        except Exception as ex:

            logging.error(f"\tError retrieving the specimen record: {ex}")

    @pyqtSlot(QVariant, name="selectSpecimenRecordByID")
    def select_specimen_record_by_id(self, specimen_id: QVariant):
        """
        Method to select the parent specimen record by the primary key (specimen_id)
        and then returning a flattened dictionary containing all of the observed values.

        This method is called by the FishSamplingScreen.qml > editSpecimen function, for when a user wants to edit
            an existing specimen.

        :param specimen_id: int representing the specimen_id primary key in the SPECIMENS table
        :return:
        """
        logging.info(f"selectSpecimenRecordByID, specimen_id = {specimen_id}")

        if not isinstance(specimen_id, int) or specimen_id is None:
            logging.error(f"\tInvalid specimen_id provided for selecting the parent specimen record: {specimen_id}")
            return

        try:
            sql = """
                WITH RECURSIVE 
                    ops_children(n) AS (
                        SELECT OPERATION_ID FROM OPERATIONS WHERE OPERATION_NUMBER = ?
                        UNION
                        SELECT o.OPERATION_ID FROM OPERATIONS o, ops_children
                                                WHERE o.PARENT_OPERATION_ID = ops_children.n
                    ),
                    parent_specimen(SPECIMEN_ID, adh, cs_catch_content_id, species, taxonomy_id) as (
                        SELECT 
                            s.SPECIMEN_ID,
                            o.OPERATION_NUMBER ||
                            (SELECT o2.OPERATION_NUMBER FROM OPERATIONS as o2 
                                WHERE o2.OPERATION_ID = o.PARENT_OPERATION_ID) ||
                            c.RECEPTACLE_SEQ as "adh",
                            c.CS_CATCH_CONTENT_ID,
                            (SELECT cc.DISPLAY_NAME from CATCH_CONTENT_LU cc 
                                WHERE cc.CATCH_CONTENT_ID = c.CS_CATCH_CONTENT_ID) as Species,
                            -- c.DISPLAY_NAME as Species,
                            (SELECT cc.taxonomy_id from CATCH_CONTENT_LU cc 
                                WHERE cc.CATCH_CONTENT_ID = c.CS_CATCH_CONTENT_ID) as taxonomy_id
                        FROM OPERATIONS o
                            INNER JOIN LOOKUPS ot ON ot.LOOKUP_ID = o.OPERATION_TYPE_LU_ID
                                LEFT JOIN CATCH c ON c.OPERATION_ID = o.OPERATION_ID
                                    LEFT JOIN SPECIMENS s ON s.CATCH_ID = c.CATCH_ID
                        WHERE o.OPERATION_ID IN ops_children
                                AND ot.TYPE = 'Operation' 
                                AND (ot.VALUE = 'Angler' OR ot.VALUE = 'Site')
                                AND s.PARENT_SPECIMEN_ID IS NULL
                                AND s.SPECIMEN_ID IS NOT NULL
                    )
                SELECT ps.SPECIMEN_ID as specimenID
                    , ps.adh as adh
                    , ps.species as species
                    , ps.taxonomy_id as taxonomyID
                    , ps.cs_catch_content_id as catchContentID
                    , MAX(CASE WHEN l.VALUE = 'Sex' THEN s.ALPHA_VALUE END) AS sex
                    , MAX(CASE WHEN l.VALUE = 'Sex' THEN s.SPECIMEN_ID END) AS sexRecID
                    , MAX(CASE WHEN l.VALUE = 'Length' THEN s.NUMERIC_VALUE END) AS length
                    , MAX(CASE WHEN l.VALUE = 'Length' THEN s.SPECIMEN_ID END) AS lengthRecID
                    , MAX(CASE WHEN l.VALUE = 'Weight' THEN s.NUMERIC_VALUE END) AS weight
                    , MAX(CASE WHEN l.VALUE = 'Weight' THEN s.SPECIMEN_ID END) AS weightRecID

                    -- , MAX(CASE WHEN l.VALUE = 'Age ID' AND l.SUBVALUE = 'Otolith' THEN s.ALPHA_VALUE END) AS ageID
                    -- , MAX(CASE WHEN l.VALUE = 'Age ID' AND l.SUBVALUE = 'Otolith' THEN s.SPECIMEN_ID END) AS ageRecID
                    -- , MAX(CASE WHEN l.VALUE = 'Age ID' AND l.SUBVALUE = 'Otolith' THEN l.SUBVALUE END) AS ageType

                    , MAX(CASE WHEN l.VALUE = 'Age ID' AND
                                    s.species_sampling_plan_id IS NULL THEN s.ALPHA_VALUE END) AS ageID
                    , MAX(CASE WHEN l.VALUE = 'Age ID' AND
                                    s.species_sampling_plan_id IS NULL THEN s.SPECIMEN_ID END) AS ageRecID
                    , MAX(CASE WHEN l.VALUE = 'Age ID' AND
                                    s.species_sampling_plan_id IS NULL THEN l.SUBVALUE END) AS ageType    
                    , MAX(CASE WHEN l.VALUE = 'Stomach ID' THEN s.ALPHA_VALUE END) AS stomachID
                    , MAX(CASE WHEN l.VALUE = 'Stomach ID' THEN s.SPECIMEN_ID END) AS stomachRecID
                    , MAX(CASE WHEN l.VALUE = 'Tissue ID' THEN s.ALPHA_VALUE END) AS tissueID
                    , MAX(CASE WHEN l.VALUE = 'Tissue ID' THEN s.SPECIMEN_ID END) AS tissueRecID
                    , MAX(CASE WHEN l.VALUE = 'Ovary ID' THEN s.ALPHA_VALUE END) AS ovaryID
                    , MAX(CASE WHEN l.VALUE = 'Ovary ID' THEN s.SPECIMEN_ID END) AS ovaryRecID
                    , MAX(CASE WHEN l.VALUE = 'Finclip ID' THEN s.ALPHA_VALUE END) AS finclipID
                    , MAX(CASE WHEN l.VALUE = 'Finclip ID' THEN s.SPECIMEN_ID END) AS finclipRecID
                    , MAX(CASE WHEN l.VALUE = 'Intestine ID' THEN s.ALPHA_VALUE END) AS intestineID
                    , MAX(CASE WHEN l.VALUE = 'Intestine ID' THEN s.SPECIMEN_ID END) AS intestineRecID
                    , MAX(CASE WHEN l.VALUE = 'Disposition' THEN s.ALPHA_VALUE END) AS disposition
                    , MAX(CASE WHEN l.VALUE = 'Disposition' THEN s.SPECIMEN_ID END) AS dispositionRecID
                    , MAX(CASE WHEN l.VALUE = 'Tag ID' THEN s.ALPHA_VALUE END) AS tagID
                    , MAX(CASE WHEN l.VALUE = 'Tag ID' THEN s.SPECIMEN_ID END) AS tagRecID   
                    , MAX(CASE WHEN l.VALUE = 'Whole Specimen ID' THEN s.ALPHA_VALUE END) AS wholeSpecimenID
                    , MAX(CASE WHEN l.VALUE = 'Whole Specimen ID' THEN s.SPECIMEN_ID END) AS wholeSpecimenRecID                                             
                    , MAX(CASE WHEN l.VALUE = 'Disposition' THEN l.SUBVALUE END) AS dispositionType
                    , s.species_sampling_plan_id as species_sampling_plan_id
                    , MAX(CASE WHEN l.VALUE = 'Age ID' AND l.SUBVALUE = 'Finray' AND
                                    s.species_sampling_plan_id IS NOT NULL THEN s.ALPHA_VALUE END) AS ageFinRayID                        
                    , MAX(CASE WHEN l.VALUE = 'Age ID' AND l.SUBVALUE = 'Finray' AND
                                    s.species_sampling_plan_id IS NOT NULL THEN s.SPECIMEN_ID END) AS ageFinRayRecID
                FROM parent_specimen ps 
                    LEFT JOIN SPECIMENS s on ps.SPECIMEN_ID = s.PARENT_SPECIMEN_ID
                    LEFT JOIN LOOKUPS l ON l.LOOKUP_ID = s.ACTION_TYPE_ID
                WHERE ps.SPECIMEN_ID = ?
                GROUP BY specimenID
                ORDER BY adh            
            """
            params = [self._app.state_machine.setId, specimen_id]

            results = self._app.rpc.execute_query(sql=sql, params=params)
            for values in results:
                specimen = dict(zip(self.specimensModel.keys, values))
                logging.info(f"selectSpecimenRecordByID - specimen = {specimen}")
                self.specimenSelected.emit(specimen)

        except Exception as ex:

            logging.error(f"Error selecting the specimen record: {ex}")

    @pyqtSlot(int, name="deleteSpecimenRecord")
    def delete_specimen_record(self, id):
        """
        Method to delete the specimen record with the given ID
        :param id: SPECIMENS table primary key to be deleted
        :return:
        """
        if not isinstance(id, int):
            logging.error(f"Specimen ID not provided to delete a specimen record, returning")
            return

        logging.info(f"DELETING SPECIMEN RECORD, id={id}")

        try:

            # Check if the CATCH record has hm_catch_content_id or best_catch_content_id or if op_type = sites
            #   If any of these are true, then only update the cs_catch_content_id = null, otherwise delete the catch
            #   record
            sql = """
                SELECT c.hm_catch_content_id, c.best_catch_content_id, ot.value
                FROM CATCH c INNER JOIN LOOKUPS ot ON c.operation_type_id = ot.lookup_id
                WHERE CATCH_ID =     
                    (SELECT CATCH_ID FROM SPECIMENS WHERE SPECIMEN_ID = ?);
            """
            params = [id, ]
            results = self._app.rpc.execute_query(sql=sql, params=params)
            if results:
                hm_cc = results[0][0]
                bs_cc = results[0][1]
                op_type = results[0][2]

                # Delete the catch record
                if hm_cc is None and bs_cc is None and op_type == 'Site':
                    logging.info(f"\tdeleting the actual catch record as it has no assigned ADH")
                    sql = "DELETE FROM CATCH WHERE CATCH_ID = (SELECT CATCH_ID FROM SPECIMENS WHERE SPECIMEN_ID = ?);"

                # Update the catch record only, null out the CS_CATCH_CONTENT_ID column
                else:
                    logging.info(f"\tupdating the catch record by nulling out the CS_CATCH_CONTENT_ID")
                    sql = """
                        UPDATE CATCH
                            SET CS_CATCH_CONTENT_ID = NULL
                        WHERE CATCH_ID = 
                            (SELECT CATCH_ID FROM SPECIMENS WHERE SPECIMEN_ID = ?);
                    """

                params = [id, ]
                adh = f"{self._app.state_machine.angler}{self._app.state_machine.drop}{self._app.state_machine.hook}"
                notify = {
                    "speciesUpdate": {"station": "CutterStation", "set_id": self._app.state_machine.setId, "adh": adh}}
                logging.info(f"\tnotify parameters for updating the FPC SpeciesReviewDialog = {notify}")
                self._app.rpc.execute_query(sql=sql, params=params, notify=notify)

            # Delete specimen record from the database
            sql = """
                DELETE FROM SPECIMENS WHERE (SPECIMEN_ID = ? OR PARENT_SPECIMEN_ID = ?);
            """
            params = [id, id]
            self._app.rpc.execute_query(sql=sql, params=params)
            logging.info(f"\tSpecimen (specimen_id={id}) deleted")

            # Delete row from the SpecimensModel
            idx = self._specimens_model.get_item_index(rolename="specimenID", value=id)
            self._specimens_model.removeItem(idx)
            logging.info(f"\tindex={idx} removed from the specimensModel")

            # Emit the specimenSelected signal with no data to clear out the specimenID value in the
            # FishSamplingEntryDialog.qml
            item = dict()
            logging.info(f"deleteSpecimenRecord")
            self.specimenSelected.emit(item)

        except Exception as ex:

            logging.error(f"Error deleting a specimen record: {ex}")

    @pyqtSlot(int, str, QVariant, bool, name="deleteSpecimenObservation")
    def delete_specimen_observation(self, id, type="Age ID", subtype="Otolith", special=False):
        """
        Method to delete an individual observation for a specimen.  Typically for observations
            like AgeID, FinclipID, or Special Project
        :param type: str - indicating the type of observation to delete
        :param subtype: str - subtype, only for Age ID
        :param id:
        :return:
        """
        logging.info(f"delete_specimen_observation, id={id}, type={type}, subtype={subtype}, special={special}")

        if not("ID" in type or type == "Disposition"):
            logging.info(f"attempting to delete an improper observation type: {type}")
            return

        if not isinstance(id, int) or id < 1:
            logging.info(f"invalid specimen ID provided for deleting an observation: {id}")
            return

        if subtype is not None:
            subtype = subtype.replace("\n", " ")

        try:
            # Delete record from the database
            if special:
                sql = "SELECT PARENT_SPECIMEN_ID FROM SPECIMENS WHERE SPECIMEN_ID = ?;"
                params = [id, ]
                results = self._app.rpc.execute_query(sql=sql, params=params)
                if results:
                    spec_id = results[0][0]
                    logging.info(f"\tparent specimen id={spec_id} found for special item with id={id}")

                sql = "DELETE FROM SPECIMENS WHERE SPECIMEN_ID = ?;"
                params = [id, ]

            else:
                if type in ["Age ID", "Disposition"]:
                    if subtype is None:
                        logging.info(f"subtype required for deleting the Age ID or Disposition")
                        return

                    sql = """
                        DELETE FROM SPECIMENS
                            WHERE PARENT_SPECIMEN_ID = ?
                               AND ACTION_TYPE_ID =
                                (SELECT LOOKUP_ID FROM LOOKUPS 
                                    WHERE TYPE = 'Observation' AND 
                                    VALUE = ? AND 
                                    SUBVALUE = ?);                
                    """
                    params = [id, type, subtype]

                else:
                    sql = """
                        DELETE FROM SPECIMENS
                            WHERE PARENT_SPECIMEN_ID = ?
                                AND ACTION_TYPE_ID =
                                    (SELECT LOOKUP_ID FROM LOOKUPS 
                                        WHERE TYPE = 'Observation' AND VALUE = ?);
                    """
                    params = [id, type]
            self._app.rpc.execute_query(sql=sql, params=params)
            logging.info(f"\tspecimen successfully deleted with params={params}")

            # Update the specimenModel record
            if special:
                idx = self._specimens_model.get_item_index(rolename="specimenID", value=spec_id)
                if idx != -1:
                    item = self._specimens_model.get(idx)
                    spec_item = item['special']
                    spec_indicator = "WS" if type == "Whole Specimen ID" else type[0:2].upper()
                    logging.info(f"\tspec_indicator to remove: {spec_indicator}")
                    if spec_indicator in spec_item:
                        spec_item = spec_item.replace(spec_indicator, "").replace(",,", ",").strip(",")
                        self._specimens_model.setProperty(index=idx, property="special", value=spec_item)

            else:
                idx = self._specimens_model.get_item_index(rolename="specimenID", value=id)
                logging.info(f"\tspecimen model index={idx}")
                if idx != -1:
                    item = self._specimens_model.get(idx)
                    logging.info(f"\tspecimen to delete, item={item}")
                    propMap = {"Age ID": "ageID", "Finclip ID": "finclipID", "Disposition": "disposition"}
                    if type in propMap:
                        self._specimens_model.setProperty(index=idx, property=propMap[type], value=None)

                    recMap = {"Age ID": "ageRecID", "Finclip ID": "finclipRecID", "Disposition": "dispositionRecID"}
                    if type in recMap:
                        self._specimens_model.setProperty(index=idx, property=recMap[type], value=None)

                    if subtype:
                        typesMap = {"Age ID": "ageType", "Disposition": "dispositionType"}
                        if type in typesMap:
                            self._specimens_model.setProperty(index=idx, property=typesMap[type], value=None)

        except Exception as ex:

            logging.error(f"Error deleting a specimen observation: {ex}")

    @pyqtSlot(QVariant, str, QVariant, str, str, QVariant, QVariant, name="assignHookAndLineTagNumber", result=QVariant)
    def assign_hookandline_tag_number(self, specimen_id, project, species_sampling_plan_id,
                                      observation_type, species_indicator, finclip_id, observation_sub_type):
        """
        Method to create the Special tag number.  The format for the Hook & Line Tag is as follows:

        YY - Year (numeric)
        VV - Vessel (alpha) - i.e. TO, MI, AG
        PPP - Species Sampling Plan Number (numeric)
        OOOO - Observation Number (alphanumeric) - i.e. B101, V345, - always include leading B, V, G, or A

        :return:
        """
        if isinstance(finclip_id, QJSValue):
            finclip_id = finclip_id.toVariant()

        logging.info(f"assign_hookandline_tag_number:  specimen_id={specimen_id}, sspi={species_sampling_plan_id}, "
                     f"obs_type={observation_type}, species_ind={species_indicator}, finclip_id={finclip_id}, "
                     f"obs_sub_type={observation_sub_type}")
        tag_number = None

        try:
            if finclip_id["num"] is None or finclip_id["type"] is None:
                message = f"A 5 digit FinclipID is required for the tag number"
                action = "Please select the Finclip ID first"
                self.exceptionEncountered.emit(message, action)
                return

            year = str(arrow.now().year)[-2:]
            vessel = self._app.state_machine.vessel[0:2].upper()
            sspi = str(species_sampling_plan_id).zfill(3)

            tag_number = year + vessel + sspi + finclip_id["type"] + finclip_id["num"]  #species_indicator

            # Check if this tag_number already exists or not
            # TODO Todd Hay - In 2018, I should probably add the l.SUBVALUE = ? into the below query
            #   for I might have a special project that could be different types of Age structures
            #   where the SUBVALUE column is required to distinguish between the different types of ages
            sql = """
                SELECT s.ALPHA_VALUE FROM SPECIMENS s
                    INNER JOIN LOOKUPS l ON l.LOOKUP_ID =  s.ACTION_TYPE_ID
                    WHERE
                        l.TYPE = 'Observation' AND
                        l.VALUE = ? AND
                        l.SUBVALUE = ? AND
                        s.SPECIES_SAMPLING_PLAN_ID = ? AND
                        s.ALPHA_VALUE = ?                    
                    ORDER BY s.ALPHA_VALUE desc LIMIT 1;
            """
            # params = [observation_type, species_sampling_plan_id, tag_start + "%"]
            params = [observation_type, observation_sub_type, species_sampling_plan_id, tag_number]
            results = self._app.rpc.execute_query(sql=sql, params=params)
            logging.info(f"checking for existing special tag number: params={params}, results={results}")
            # if len(results) == 1:
            #     obs_num = results[0][0]
            #     if len(obs_num) >= 11:
            #         obs_num_size = len(obs_num) - len(tag_start)
            #         obs_num = str(int(obs_num[-obs_num_size:]) + 1).zfill(obs_num_size)
            #         tag_number = tag_start + obs_num
            # else:
            #     tag_number = tag_start + "001"

            if len(results) > 0:
                message = f"The proposed tag number ({tag_number}) already exists"
                action = "Please select a different Finclip ID number"
                self.exceptionEncountered.emit(message, action)
                return

            model_action_subtype = None
            if observation_type == "Whole Specimen ID":
                model_action = "wholeSpecimenID"
            else:
                otSplit = observation_type.split(" ")
                if len(otSplit) == 2:
                    model_action = otSplit[0].lower() + otSplit[1].upper()
                else:
                    model_action = None
                    logging.error(f"Error deriving the model action from {observation_type}")

                if observation_type == "Age ID" and observation_sub_type == "Finray": #  "Finray Age" in project:
                    # ToDo Todd Hay - 2017 Hack, fix for later - Fixed in 2018 with observation_sub_type
                    model_action_subtype = observation_sub_type

            self.upsert_observation(dialog_specimen_id=specimen_id,
                                    model_action=model_action,
                                    value=tag_number,
                                    data_type="alpha",
                                    model_action_subtype=model_action_subtype,
                                    species_sampling_plan_id=species_sampling_plan_id,
                                    is_special_project=True)

        except Exception as ex:

            logging.info(f"Error creating the Hook & Line tag number: {ex}")

        logging.info(f"tag_number={tag_number}")

        return tag_number

    @pyqtSlot(str, QVariant, name="checkIfIDExists", result=QVariant)
    def check_if_id_exists(self, id_type, value):
        """
        Method to check if the AgeID or FinclipID already exists in the database.  If so,
        return the latest ID for the given B/V/G/A
        :param id_type:
        :param value:
        :return:
        """
        if len(value) != 5 or value[0] not in ["B", "V", "A"]:
            msg = f"{id_type} should be 4 digits and B, V, or A selected"
            return {"status": "invalid", "msg": msg}

        try:
            sql = """
                SELECT ALPHA_VALUE FROM SPECIMENS s
                    INNER JOIN LOOKUPS l ON s.ACTION_TYPE_ID = l.LOOKUP_ID
                    WHERE
                        l.TYPE = 'Observation' AND l.VALUE = ? AND
                        s.ALPHA_VALUE LIKE ?
                    ORDER BY s.ALPHA_VALUE desc;
            """
            params = [id_type, f"{value[0]}%"]
            results = self._app.rpc.execute_query(sql=sql, params=params)
            logging.info(f"ID check params: {params} >>> results={results}")
            if results:
                results = [x[0] for x in results]   # currently have a list of lists, remove inner brackets
                largest_value = results[0]

                # Check if the given value already exists in the database
                if value in results:
                    next_value = f"{results[0][0]}{str(int(results[0][1:])+1).zfill(4)}"
                    msg = f"{id_type} already exists, the next available value is {next_value}"
                    return {"status": "found", "msg": msg}

                else:
                    # Check if there is a gap in the sequence
                    largest_int = int(largest_value[1:])
                    value_int = int(value[1:])
                    if value_int != largest_int + 1:
                        msg = f"{id_type} has a sequence gap, last value is {largest_value}"
                        return {"status": "sequence gap", "msg": msg}

            return {"status": "valid", "msg": ""}

        except Exception as ex:

            logging.error(f"Error retrieving the {id_type} lastest value: {ex}")

    @pyqtSlot(int, name="getHookMatrixSpecies", result=QVariant)
    def get_hook_matrix_species(self, specimen_id):
        """
        Method to obtain the Hook Matrix species, given the SPECIMEN table specimen_id
        :param specimen_id:
        :return:
        """
        if not isinstance(specimen_id, int) or specimen_id < 1:
            logging.error(f"Error getting the hook matrix species, specimen_id = {specimen_id}")
            return

        sql = """
            SELECT cc.DISPLAY_NAME 
            FROM CATCH c
            INNER JOIN CATCH_CONTENT_LU cc ON cc.CATCH_CONTENT_ID = c.HM_CATCH_CONTENT_ID
            LEFT JOIN SPECIMENS s ON s.CATCH_ID = c.CATCH_ID
            WHERE s.SPECIMEN_ID = ?;            
        """
        params = [specimen_id, ]
        result = self._app.rpc.execute_query(sql=sql, params=params)
        if len(result) == 1:
            return result[0][0]
        return None

    @pyqtSlot(int, str, name="updateRecorder")
    def update_recorder(self, recorder_id, recorder_name):
        """
        Method to update the recorder for the given the site ID specified by the state machine
        :param recorder_id:
        :return:
        """
        logging.info(f"update_recorder with values, id={recorder_id}, name={recorder_name}")

        if not isinstance(recorder_id, int) or recorder_id < 1:
            logging.error(f"Failed to update the cutter recorder, invalid recorder_id: {recorder_id}")
            return

        try:
            # Check if a recorder ID exists for this site yes
            sql = """
                SELECT oa.OPERATION_ATTRIBUTE_ID 
                    From operation_attributes oa
                        INNER JOIN operations o on oa.operation_id = o.operation_id
                        INNER JOIN lookups at on at.lookup_id = oa.attribute_type_lu_id
                    WHERE o.OPERATION_NUMBER = ? AND at.TYPE = 'Cutter Attribute' AND at.VALUE = 'Recorder Name';
            """
            params = [self._app.state_machine.setId, ]
            results = self._app.rpc.execute_query(sql=sql, params=params)

            # Recorder ID exists, just update the value
            if results:
                oa_id = results[0][0]
                sql = """
                    UPDATE OPERATION_ATTRIBUTES
                        SET ATTRIBUTE_ALPHA = ?
                        WHERE OPERATION_ATTRIBUTE_ID = ?;
                """
                params = [recorder_name, oa_id]
                results = self._app.rpc.execute_query(sql=sql, params=params)
                logging.info(f"\trecorder successfully updated")

            # Recorder ID does not exist, insert into the DB
            else:
                sql = """
                    INSERT INTO OPERATION_ATTRIBUTES(OPERATION_ID, ATTRIBUTE_ALPHA, ATTRIBUTE_TYPE_LU_ID)
                        VALUES(
                            (SELECT OPERATION_ID from operations where operation_number = ?),
                            ?,
                            (SELECT lookup_id from lookups where type = 'Cutter Attribute' and value = 'Recorder Name')
                        );
                """
                params = [self._app.state_machine.setId, recorder_name]
                results = self._app.rpc.execute_query(sql=sql, params=params)
                logging.info(f"\trecorder successfully inserted")

        except Exception as ex:
            logging.error(f"Error updating the recorder with id={recorder_id} and name={recorder_name}: {ex}")

    @pyqtSlot(str, name="getLastAgeFinclipIDs", result=QVariant)
    def get_last_age_finclip_ids(self, value):
        """
        Method to return the last age and finclip IDs for display on the Age ID and
        Finclip ID tabs in the FishSamplingEntryDialog.qml

        :return:
        """
        if len(value) != 1 or value not in ["B", "V", "A"]:
            logging.info(f"Invalid value provided for get last age/finclip IDs: {ex}")
            return None

        try:
            params = [f"{value}%", ]

            finclip_sql = """
                SELECT ALPHA_VALUE FROM SPECIMENS s
                    INNER JOIN LOOKUPS l ON s.ACTION_TYPE_ID = l.LOOKUP_ID
                    WHERE
                        l.TYPE = 'Observation' AND 
                        l.VALUE = 'Finclip ID' AND
                        s.ALPHA_VALUE LIKE ?
                    ORDER BY s.ALPHA_VALUE desc
                    LIMIT 1;
            """
            finclips = self._app.rpc.execute_query(sql=finclip_sql, params=params)
            finclip = None
            if finclips:
                finclip = finclips[0][0]

            age_sql = """
                SELECT ALPHA_VALUE FROM SPECIMENS s
                    INNER JOIN LOOKUPS l ON s.ACTION_TYPE_ID = l.LOOKUP_ID
                    WHERE
                        l.TYPE = 'Observation' AND 
                        (l.VALUE = 'Age ID' AND l.SUBVALUE = 'Otolith') AND
                        s.ALPHA_VALUE LIKE ?
                    ORDER BY s.ALPHA_VALUE desc
                    LIMIT 1;
            """
            ages = self._app.rpc.execute_query(sql=age_sql, params=params)
            age = None
            if ages:
                age = ages[0][0]

            logging.info(f"results of last finclip/age search, finclip={finclip}, age={age}")

            return {"finclip": finclip, "age": age}

        except Exception as ex:

            logging.error(f"Error retrieving the lastest finclip/age values given {value}: {ex}")

    @pyqtSlot(name="testSerialPort")
    def test_serial_port(self):
        """
        Method to test the scale weight or barcode adh serial port entries
        :return:
        """
        self._app.state_machine.currentEntryTab = "weight"
        self._app.serial_port_manager.data_received("COM20", "weight", "weight=2.3", 2.3)

    @pyqtSlot(name="getRandomDrops")
    def get_random_drops(self):
        """
        Method to retrieve the random drops for the given set id
        :param set_id:
        :return:
        """
        try:

            sql = """
                SELECT RANDOM_DROP_1, RANDOM_DROP_2 FROM OPERATIONS WHERE OPERATION_ID = ?;
            """
            params = [self._app.state_machine.siteOpId, ]
            results = self._app.rpc.execute_query(sql=sql, params=params)

            if results:
                drops = sorted(results[0])
                random_drop_1 = drops[0]
                random_drop_2 = drops[1]
                self._random_drops = [random_drop_1, random_drop_2]

        except Exception as ex:

            logging.error(f"Error getting the random drops: {ex}")

    @pyqtProperty(QVariant, notify=randomDropsChanged)
    def randomDrops(self):
        """
        Method to return the self._random_drops, used by the FishSamplingEntryDialog.qml
        :return:
        """
        return self._random_drops

if __name__ == '__main__':
    unittest.main()
