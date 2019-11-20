__author__ = 'Todd.Hay'

# -------------------------------------------------------------------------------
# Name:        ProcessCatch.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 10, 2016
# License:     MIT
#-------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QVariant, Qt, QModelIndex, \
    QAbstractItemModel, QByteArray, QAbstractListModel, QItemSelection, QPersistentModelIndex
from PyQt5.Qt import QJSValue, QQmlEngine
from py.common.FramListModel import FramListModel
from py.common.FramTreeModel import FramTreeModel
from py.common.FramTreeItem import FramTreeItem
import logging
import unittest
import pdb
from py.trawl.TrawlBackdeckDB_model import Specimen, Catch, Hauls, SpeciesSamplingPlanLu
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
from py.common.SoundPlayer import SoundPlayer

class SpeciesListModel(FramListModel):

    def __init__(self, parent=None):
        super().__init__()

        self.add_role_name(name='taxonomyId')
        self.add_role_name(name="scientificName")
        self.add_role_name(name="commonName1")
        self.add_role_name(name="commonName2")
        self.add_role_name(name="commonName3")
        self.add_role_name(name='displayName')
        self.add_role_name(name='protocol')
        self.add_role_name(name='weight')
        self.add_role_name(name='count')
        self.add_role_name(name='depthMin')
        self.add_role_name(name='depthMax')
        self.add_role_name(name='latMin')
        self.add_role_name(name='latMax')
        self.add_role_name(name='isMostRecent')
        self.add_role_name(name='isLastNOperations')
        self.add_role_name(name='type')
        self.add_role_name(name='sampleType')
        self.add_role_name(name='catchContentId')
        self.add_role_name(name='catchId')


class SpeciesTreeModel(FramTreeModel):
    """
    Class used for the SelectedSpeciesTreeView.  This is a custom FramTreeModel that allows one to add/remove
    mixes, which are hierarchical in nature
    """
    def __init__(self, headers=[], data=[]):
        super().__init__(headers=headers, data=data)

    @pyqtSlot(result=QVariant)
    def sortCatch(self):
        """
        Sort the list in-place alphabetically with the species at top, and then mixes
        occurring beneath that, and then finally debris
        """

        # List used to keep track of which items needs to be re-expanded after the sort operation is completed
        expandedList = []

        typeCol = self.getColumnNumber("type")
        displayNameCol = self.getColumnNumber("displayName")

        # Sort main list by item type using SORT_ORDER & then alphabetically within the Taxon, Mix, Debris lists
        SORT_ORDER = {"Taxon": 0, "Mix": 1, "Debris": 2}
        MIX_SORT_ORDER = {"Taxon": 0, "Submix": 1, "Debris": 2}
        SUBMIX_SORT_ORDER = {"Taxon": 0, "Debris": 1}

        # sorted_items = sorted(self._rootItem.childItems, key=lambda x: (SORT_ORDER[x.data(typeCol).value()], x.data(displayNameCol).value()))
        sorted_items = sorted(self._rootItem.childItems, key=lambda x: (SORT_ORDER[x.data(typeCol).value()], x.data(displayNameCol).value().lower()))
        self.removeRows(0, self._rootItem.childCount(), QModelIndex())
        self.setChildItems(sorted_items, QModelIndex())

        # Sort mixes by Taxon > Submix > Debris, and then alphabetically within each of those categories
        mixes = [x for x in self._rootItem.childItems if x.data(typeCol).value() == "Mix"]
        for mix in mixes:
            mixIdx = self.createIndex(0, 0, mix)

            # TODO Todd Hay - Fix sorting mixes when mix # >= 10
            # see https://arcpy.wordpress.com/2012/05/11/sorting-alphanumeric-strings-in-python/
            # logging.info('mix children: ' + str(mix.childItems))

            sorted_mix = sorted(mix.childItems, key=lambda x: (MIX_SORT_ORDER[x.data(typeCol).value()], x.data(displayNameCol).value().lower()))
            self.removeRows(0, mix.childCount(), mixIdx)
            self.setChildItems(sorted_mix, mixIdx)

            if mix.isExpanded:
                expandedList.append(mix)

            # Sort submixes by Taxon > Debris, and then alphabetically within each of those categories
            submixes = [y for y in mix.childItems if y.data(typeCol).value() == "Submix"]
            for submix in submixes:
                submixIdx = self.createIndex(0, 0, submix)

                # TODO Todd Hay - Fix sorting submixes when mix # >= 10
                # see https://arcpy.wordpress.com/2012/05/11/sorting-alphanumeric-strings-in-python/

                sorted_submix = sorted(submix.childItems, key=lambda z: (SUBMIX_SORT_ORDER[z.data(typeCol).value()], z.data(displayNameCol).value().lower()))
                self.removeRows(0, submix.childCount(), submixIdx)
                self.setChildItems(sorted_submix, submixIdx)
                if submix.isExpanded:
                    expandedList.append(submix)

        # Convert the expandedList to the current QModelIndex's
        expandedList = [self.createIndex(x.row, 0, x) for i, x in enumerate(expandedList)]
        return expandedList


class ProcessCatch(QObject):
    """
    Class for the ProcessCatchScreen.  Handles getting all of the species data
    """
    haulIdChanged = pyqtSignal()
    speciesModelChanged = pyqtSignal()
    speciesCountChanged = pyqtSignal()
    totalWeightChanged = pyqtSignal()
    selectedIndexChanged = pyqtSignal()
    activeMixChanged = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)

        self._app = app
        self._db = db

        self._mixes = dict()
        self._active_mix = {"catchId": None, "displayName": None}

        # Populate lists that are used in the tvAvailableSpecies TableView
        self._species = self._get_species()
        self._recent_species = [s for s in self._species if s["isMostRecent"].upper() == "TRUE"]
        self._debris = self._get_debris()

        # Create the models for the available + selected Table/Tree views
        self.avFullModel = SpeciesListModel()
        self.avRecentModel = SpeciesListModel()
        self.avDebrisModel = SpeciesListModel()
        self.seModel = self._set_selected_species_model()

        self._current_species_model = self.avFullModel

        self._species_count = 0
        self._total_weight = 0
        self._filter = ""

        self._corals = self.get_coral_species()
        self._salmon = self.get_salmon_species()
        self._sponges = self.get_sponge_species()
        self._rockfish = self.get_rockfish_species()

        self._sound_player = SoundPlayer()

        self._selected_index = None
        # pdb.set_trace()

    @pyqtProperty(QVariant, notify=activeMixChanged)
    def activeMix(self):
        """
        Method to return the self._active_mix.  This is the currently chosen list used in combination when a user
        want to a new species to a mix that species is added to this mix
        :return: 
        """
        return self._active_mix

    @activeMix.setter
    def activeMix(self, value):
        """
        Method to set the self._active_mix
        :param value: 
        :return: 
        """
        self._active_mix = value
        self.activeMixChanged.emit()

    @pyqtSlot()
    def initialize_lists(self):
        """
        Method to reset all of the FramListModels to their original state of items.  This is called when
        the ProcessCatch is first initialized and then also whenever the haul id is changed, as the tree
        needs to be rebuilt from the database at that point
        :return: None
        """
        # Establish working lists for available Full / Recent / Debris lists + filtered variants
        self.avFullSpecies = list(self._species)
        self.avFullSpeciesFiltered = list(self._species)
        self.avRecentSpecies = list(self._recent_species)
        self.avRecentSpeciesFiltered = list(self._recent_species)
        self.avDebris = list(self._debris)
        self.avDebrisFiltered = list(self._debris)

        # Reset the list items
        self.avFullModel.setItems(self.avFullSpeciesFiltered)
        self.avRecentModel.setItems(self.avRecentSpeciesFiltered)
        self.avDebrisModel.setItems(self.avDebrisFiltered)

    def _get_fram_protocols(self):
        """
        Method to gather the protocol display name for the FRAM protocols
        :return: dict - containing taxon_id: protocol name
        """
        protocols = []
        protocol_sql = """
            SELECT taxonomy_id, display_name FROM SPECIES_SAMPLING_PLAN_LU WHERE
            PLAN_NAME = 'FRAM Standard Survey' AND
            DISPLAY_NAME != 'Whole Specimen ID'
            """
            #  AND
            # DISPLAY_NAME != 'Coral' AND
            # DISPLAY_NAME != 'Salmon';

        protocols = self._db.execute(query=protocol_sql)
        protocols = {x[0]: x[1] for x in protocols}
        return protocols

    @pyqtSlot()
    def initialize_tree(self):
        """
        Method called when the haul id is changed that initializes the tree with the data from the database
        :return:
        """
        model = self.seModel

        # Clear the tree + it's descendants list
        model.clear()

        self.speciesCount = 0
        total_weight = 0

        # Populate the tree
        keys = ["catchId", "parentCatchId", "displayName", "isMix", "isDebris", "taxonomyId", "scientificName",
                "commonName1", "commonName2", "commonName3",
                "depthMin", "depthMax", "latMin", "latMax",
                 "weight", "count", "isMostRecent", "isLastNOperations", "catchContentId", "protocol"]
        dataKeys = ["catchId", "displayName", "taxonomyId", "scientificName",
                    "commonName1", "commonName2", "commonName3",
                    "depthMin", "depthMax", "latMin", "latMax",
                    "weight", "count", "isMostRecent", "isLastNOperations", "type", "catchContentId", "protocol"]

        # TODO Todd Hay sampleType - do I need to include this, I don't think so as I'm not using it.

        # sql = "SELECT c.CATCH_ID, c.PARENT_CATCH_ID, c.DISPLAY_NAME, c.IS_MIX, c.IS_DEBRIS, cc.TAXONOMY_ID, " + \
        #       "t.SCIENTIFIC_NAME, t.COMMON_NAME_1, t.COMMON_NAME_2, t.COMMON_NAME_3, " + \
        #       "t.HISTORICAL_DEPTH_MIN, t.HISTORICAL_DEPTH_MAX, t.HISTORICAL_LAT_MIN, t.HISTORICAL_LAT_MAX, " + \
        #       "c.weight_kg, c.sample_count_int, cc.IS_MOST_RECENT, cc.IS_LAST_N_OPERATIONS, cc.CATCH_CONTENT_ID, " + \
        #       "s.DISPLAY_NAME " + \
        #       "FROM CATCH c " + \
        #       "LEFT JOIN CATCH_CONTENT_LU cc ON c.CATCH_CONTENT_ID = cc.CATCH_CONTENT_ID " + \
        #       "LEFT JOIN TAXONOMY_LU t ON t.TAXONOMY_ID = cc.TAXONOMY_ID " + \
        #       "LEFT JOIN SPECIES_SAMPLING_PLAN_LU s ON t.TAXONOMY_ID = s.TAXONOMY_ID " + \
        #       "WHERE c.OPERATION_ID = ? AND (s.PLAN_NAME = 'FRAM Standard Survey' or s.PLAN_NAME IS NULL);"

        # Returns a dictionary of taxon_id: protocol name - these are used to compare against the sql query below
        # to set the protocol display to a FRAM Standard Survey protocol name if one exists, otherwise, use what is
        # retrieved from the query
        protocols = self._get_fram_protocols()

        sql = """
            SELECT c.CATCH_ID, c.PARENT_CATCH_ID, c.DISPLAY_NAME, c.IS_MIX, c.IS_DEBRIS, cc.TAXONOMY_ID,
            t.SCIENTIFIC_NAME, t.COMMON_NAME_1, t.COMMON_NAME_2, t.COMMON_NAME_3,
            t.HISTORICAL_DEPTH_MIN, t.HISTORICAL_DEPTH_MAX, t.HISTORICAL_LAT_MIN, t.HISTORICAL_LAT_MAX,
            c.weight_kg, c.sample_count_int, cc.IS_MOST_RECENT, cc.IS_LAST_N_OPERATIONS, cc.CATCH_CONTENT_ID,
            s.DISPLAY_NAME
            FROM CATCH c
            LEFT JOIN CATCH_CONTENT_LU cc ON c.CATCH_CONTENT_ID = cc.CATCH_CONTENT_ID
            LEFT JOIN TAXONOMY_LU t ON t.TAXONOMY_ID = cc.TAXONOMY_ID
            LEFT JOIN SPECIES_SAMPLING_PLAN_LU s ON t.TAXONOMY_ID = s.TAXONOMY_ID
            WHERE c.OPERATION_ID = ?
            GROUP BY CATCH_ID
            ORDER BY CATCH_ID
            """

        params = [self._app.state_machine._haul["haul_id"], ]
        results = self._db.execute(query=sql, parameters=params).fetchall()
        if results:
            results = [dict(zip(keys, values)) for values in results]
            for x in results:
                if x["isMix"].lower() == "false" and x["isDebris"].lower() == "false":
                    x["type"] = "Taxon"
                elif x["isMix"].lower() == "true" and x["isDebris"].lower() == "false":
                    if "submix" in x["displayName"].lower():
                        x["type"] = "Submix"
                    else:
                        x["type"] = "Mix"
                        if isinstance(self._active_mix, QJSValue):
                            self._active_mix = self._active_mix.toVariant()
                        if self._active_mix["catchId"] is None:
                            self.activeMix = {"displayName": x["displayName"], "catchId": x["catchId"]}

                elif x["isMix"].lower() == "false" and x["isDebris"].lower() == "true":
                    x["type"] = "Debris"

                # Update weights / counts
                totals = self._get_basket_weights_counts(catch_id=x["catchId"])
                x["weight"] = totals["weight"]
                x["count"] = totals["count"]

                # Update protocol display using the protocols dict obtained above
                x["protocol"] = protocols[x["taxonomyId"]] if x["taxonomyId"] in protocols else x["protocol"]

            firstLevelItems = [x for x in results if x["parentCatchId"] is None]
            for item in firstLevelItems:

                # Get the data items
                data = {x: item[x] for x in item if x in dataKeys}

                # logging.info("adding data to treeview: {0}".format(data))

                # Update the total weight
                total_weight += data["weight"]

                # Set None values to ""
                data.update((k, "") for k, v in data.items() if v is None)

                # Add to the FramTreeView
                parentIdx = self.append_tree_item(data=data, parentIdx=QModelIndex())

                # Remove from the FramListModel, i.e. the left-side ListView
                if data["type"] != "Mix" and data["type"] != "Submix":
                    self.remove_list_item(data=data)

                # For a mix, add children to the mix
                if data["type"] == "Mix":

                    # Update the FramTreeModel self._mixCount
                    model.addMixCount("Mix")

                    # Get all of the Mix children, add those, but don't get/add the Mix baskets (the last argument)
                    children = [x for x in results if x["parentCatchId"] == item["catchId"] and x["type"] != "Mix"]
                    for child in children:

                        # Add to the FramTreeView
                        childData = {x: child[x] for x in child if x in dataKeys}
                        childData.update((k, "") for k, v in childData.items() if v is None)
                        subparentIdx = self.append_tree_item(data=childData, parentIdx=parentIdx)

                        # logging.info('childData: ' + str(childData["displayName"]) + ', ' + str(childData["type"]))

                        # Remove from the FramListModel
                        if childData["type"] != "Submix" and childData["type"] != "Mix":
                            self.remove_list_item(data=childData)

                        # Add Submixes
                        if childData["type"] == "Submix":

                            # Update the running count of the submixes for the given mix
                            model.addMixCount("Submix", parentIdx)

                            # Get the submix children, but don't get/add the submix baskets (the last argument here)
                            subchildren = [x for x in results if x["parentCatchId"] == child["catchId"] and x["type"] != "Submix"]
                            for subchild in subchildren:

                                # Add to the FramTreeView
                                subchildData = {x: subchild[x] for x in subchild if x in dataKeys}
                                subchildData.update((k, "") for k, v in subchildData.items() if v is None)
                                self.append_tree_item(data=subchildData, parentIdx=subparentIdx)

                                # Remove from the FramListModel
                                self.remove_list_item(data=subchildData)

            model.sortCatch()

        self.totalWeight = total_weight

        logging.info("Initializing tree, mixes: {0}".format(self.seModel.mixCount))

    @pyqtSlot(str)
    def playSound(self, sound_name):
        """
        Play a sound
        :param sound_name:
        :return:
        """
        if not isinstance(sound_name, str):
            return

        self._sound_player.play_sound(sound_name=sound_name)

    @staticmethod
    def _filter_model(filter_text, data, type):
        """
        Method to return a filtered list of the species matching the filter_text
        :param filter_text: text against which to query
        :param species: listing of the input species to query
        :return: filtered list
        """
        if type == "Debris":
            return [d for d in data if filter_text.upper() in d['displayName'].upper()]

        else:
            filtered_list = [d for d in data
                if (filter_text.upper() in d['displayName'].upper() or
                    filter_text.upper() in d['scientificName'].upper()or
                    (d["commonName1"] is not None and filter_text.upper() in d['commonName1'].upper()) or
                    (d["commonName2"] is not None and filter_text.upper() in d['commonName2'].upper()) or
                    (d["commonName3"] is not None and filter_text.upper() in d['commonName3'].upper()))]

            if filter_text == "":
                return filtered_list

            start_match_list = [x for x in filtered_list if x['displayName'].upper().startswith(filter_text.upper())]
            # start_match_list = sorted(start_match_list, key=lambda x: x["displayName"].lower())

            remaining_list = [x for x in filtered_list if x not in start_match_list]
            # remaining_list = sorted(remaining_list, key=lambda x: x["displayName"].lower())

            sorted_list = start_match_list + remaining_list

            return sorted_list

    @pyqtSlot(str)
    def filter_species(self, filter_text=""):
        """
        Method use to filter the AvailableSpecies list model based on what the user types in the textbox
        :param filter_text: Text that the user entered to filter the species
        :return: None
        """
        self._filter = filter_text

        self.avFullSpeciesFiltered = self._filter_model(filter_text=filter_text, data=self.avFullSpecies, type="Taxon")
        self.avFullModel.setItems(self.avFullSpeciesFiltered)

        self.avRecentSpeciesFiltered = self._filter_model(filter_text=filter_text, data=self.avRecentSpecies, type="Taxon")
        self.avRecentModel.setItems(self.avRecentSpeciesFiltered)

        self.avDebrisFiltered = self._filter_model(filter_text=filter_text, data=self.avDebris, type="Debris")
        self.avDebrisModel.setItems(self.avDebrisFiltered)

    @pyqtSlot(QModelIndex, result=bool)
    def add_list_item(self, index):
        """
        Method to add a species back to the tvAvailableList FramListModel
        :param index - QModelIndex - item to add back
        :return: bool - successful or not (true/false)
        """
        if not isinstance(index, QModelIndex):
            return False

        # Add to the Full List Model
        item = self.seModel.getItem(index)
        data = item.getAllDataAsDict()

        # Clear out any weight + count data, i.e. if baskets had been taken, otherwise these could reappear
        # when the item is added back to the TreeView
        data["count"] = None
        data["weight"] = None

        type = data["type"]
        filterList = [v for k, v in data.items() if v != "" and v is not None and k in ("displayName", "scientificName", "commonName1", "commonName2", "commonName3")]

        if type == "Debris":
            data["displayName"] = data["displayName"].replace("Debris - ", "")
            self.avDebris.append(data)
            self.avDebris = sorted(self.avDebris, key=lambda k: k['displayName'].lower())

            if any(self._filter.lower() in x.lower() for x in filterList):
                self.avDebrisModel.appendItem(data)
                self.avDebrisModel.sort("displayName")
                self.avDebrisFiltered.append(data)
                self.avDebrisFiltered = sorted(self.avDebrisFiltered, key=lambda k: k['displayName'].lower())

        elif type == "Mix" or type == "Submix":
            # Need to recurse these to get all children and add back to the list
            for child in item.children:
                newIndex = self.seModel.createIndex(child.row, 0, child)
                self.add_list_item(newIndex)

        elif type == "Taxon":
            self.avFullSpecies.append(data)
            self.avFullSpecies = sorted(self.avFullSpecies, key=lambda k: k['displayName'].lower())

            # Check if the displayName exists in the self.avFullSpeciesFiltered
            if any(self._filter.lower() in x.lower() for x in filterList):
                self.avFullModel.appendItem(data)
                self.avFullModel.sort("displayName")
                self.avFullSpeciesFiltered.append(data)
                self.avFullSpeciesFiltered = sorted(self.avFullSpeciesFiltered, key=lambda k: k['displayName'].lower())

            # TODO Todd Hay - are we using isMostRecent or isLastNOperations - probably the latter
            if data["isMostRecent"] == "True":
                self.avRecentSpecies.append(data)
                self.avRecentSpecies = sorted(self.avRecentSpecies, key=lambda k: k['displayName'].lower())

                # if any(d["displayName"] == data["displayName"] for d in self.avRecentSpeciesFiltered):
                if any(self._filter.lower() in x.lower() for x in filterList):
                    self.avRecentModel.appendItem(data)
                    self.avRecentModel.sort("displayName")
                    self.avRecentSpeciesFiltered.append(data)
                    self.avRecentSpeciesFiltered = sorted(self.avRecentSpeciesFiltered, key=lambda k: k['displayName'].lower())

        return True

    @pyqtSlot(QVariant)
    def remove_list_item(self, data):
        """
        Method to remove an item from the FramListModel
        :param data: dict - dictionary of the data to delete
        :return: None
        """

        if isinstance(data, QJSValue):
            data = data.toVariant()

        rolename = "displayName"
        value = data[rolename]
        type = data["type"]

        if type == "Taxon":

            idx = self.avFullModel.get_item_index(rolename=rolename, value=value)
            if idx >= 0:
                self.avFullModel.removeItem(idx)
            self.avFullSpecies = [x for x in self.avFullSpecies if x["displayName"] != value]
            self.avFullSpeciesFiltered = [x for x in self.avFullSpeciesFiltered if x["displayName"] != value]

            if data["isMostRecent"] == "True":

                idx = self.avRecentModel.get_item_index(rolename=rolename, value=value)
                if idx >= 0:
                    self.avRecentModel.removeItem(idx)
                self.avRecentSpecies = [x for x in self.avRecentSpecies if x["displayName"] != value]
                self.avRecentSpeciesFiltered = [x for x in self.avRecentSpeciesFiltered if x["displayName"] != value]

        elif type == "Debris":

            idx = self.avDebrisModel.get_item_index(rolename=rolename, value=value)
            if idx >= 0:
                self.avDebrisModel.removeItem(idx)
            self.avDebris = [x for x in self.avDebris if x["displayName"] != value]
            self.avDebrisFiltered = [x for x in self.avDebrisFiltered if x["displayName"] != value]

    def append_tree_item(self, data, parentIdx):
        """
        Method to insert a row in the self._selected_species_model model.  This is done during the initialization
        of the TreeView only, as we don't want to insert new records into the database.  See append_tree_item_with_sql
        when a user actually chooses to add a new item to the TreeView
        :param data: QJSValue dict - data to be appended as a new row
        :param parentIdx: QModelIndex - index of the currently selected item in tvSelectedSpecies
        :return: None
        """

        model = self.seModel

        if isinstance(parentIdx, QModelIndex) and parentIdx.row() >= 0:
            parentItem = model.getItem(parentIdx)
        else:
            parentIdx = QModelIndex()
            parentItem = model._rootItem

        if isinstance(data, QJSValue):
            data = data.toVariant()     # Convert from QJSValue to dict

        status = model.insertRows(parentItem.childCount(), 1, parentIdx)
        child = parentItem.child(parentItem.childCount()-1)
        row = child.row

        # Update the speciesCount - I call the method which then emits a signal
        if data["type"] == "Taxon":
            self.speciesCount += 1

        # Update the newly created child/row data with the data from tvAvailableSpecies model
        for element in data:
            if element in model.rootData: # and data[element] is not None and data[element] != "":
                column = model.getColumnNumber(element)
                if column >= 0:
                    index = model.createIndex(row, column, child)
                    role = model.getRoleNumber(role_name=element)
                    if element == "displayName" and data["type"] == "Debris":
                        data[element] = "Debris - " + data[element]
                    status = model.setData(index, data[element], role)

        # Update the model._descendantSpecies list - do this after the data has been updated
        colNum = model.getColumnNumber("taxonomyId")
        taxonId = child.data(colNum)
        if taxonId.value():
            model.append_descendant(taxonId)

        return model.createIndex(row, 0, child)

    @pyqtProperty(int, notify=haulIdChanged)
    def haulId(self):

        self._initialize_tree()
        return self._haul_id

    @haulId.setter
    def haulId(self, value):
        self._haul_id = self._app.state_machine._haul["haul_id"]
        self.haulIdChanged.emit()

    @pyqtProperty(float, notify=totalWeightChanged)
    def totalWeight(self):
        """
        Method to return the total weight for the haul
        :return:
        """
        return self._total_weight

    @totalWeight.setter
    def totalWeight(self, value):

        if not isinstance(value, float):
            return

        self._total_weight = value
        self.totalWeightChanged.emit()

    @pyqtProperty(int, notify=speciesCountChanged)
    def speciesCount(self):
        """
        Return the species_count
        :return: int - species_count
        """
        return self._species_count

    @speciesCount.setter
    def speciesCount(self, value):
        """
        Set the self._species_count
        :param value: int - value to set it to
        :return:
        """
        if value is None:
            return

        self._species_count = value

        self.speciesCountChanged.emit()

    @pyqtProperty(QObject, notify=speciesModelChanged)
    def currentSpeciesModel(self):
        """
        Property used to know if the currently selected speciesModel is the Full List or the
        Most Recent List
        :param model:
        :return:
        """
        return self._current_species_model

    @currentSpeciesModel.setter
    def currentSpeciesModel(self, model):
        """
        Method for setting the self._speciesModel
        :param model:
        :return:
        """
        self._current_species_model = model
        self.speciesModelChanged.emit()

    @pyqtProperty(QVariant)
    def species(self):
        """
        Get the full listing of species
        :return: List of species
        """
        return self._species

    @pyqtProperty(FramListModel, notify=speciesModelChanged)
    def FullAvailableSpeciesModel(self):
        """
        Get the model for the tvAvailableSpecies TableView
        :return: AvailableSpeciesMode
        """
        return self.avFullModel

    # TODO (todd.hay) Implement NOTIFY signal per warning I'm receiving and discussion of it here:
    # http://stackoverflow.com/questions/6728615/warning-about-non-notifyable-properties-in-qml

    @pyqtProperty(FramListModel, notify=speciesModelChanged)
    def MostRecentAvailableSpeciesModel(self):
        """
        Return the model of the most recent available species
        :return:
        """
        return self.avRecentModel

    @pyqtProperty(FramTreeModel, notify=speciesModelChanged)
    def SelectedSpeciesModel(self):
        """
        Return the model of the selected species, a FramTreeModel
        :return:
        """
        return self.seModel

    @pyqtProperty(FramListModel, notify=speciesModelChanged)
    def DebrisModel(self):
        """
        Return the model of the debris, a FramListModel
        :return:
        """
        return self.avDebrisModel

    @pyqtSlot(QModelIndex, result=QVariant)
    def getParent(self, idx):

        model = self.seModel
        typeCol = model.get_role_number("type")
        type = model.data(idx, typeCol).value()

        if type and (type == "Mix" or type == "Submix"):
            parent = model.item(idx).value()
        else:
            parent = model._rootItem
        return parent

    @pyqtSlot(QModelIndex, QVariant, result=bool)
    def checkTaxonId(self, idx, selection):
        """
        Method to determine if a species with the given taxonomy id already exists in the current
        level of the tvSelectedSpecies FramTreeModel. If so, don't add it, just highlight that row
        :param idx: QModelIndex - index of the selected row in tvSelectedSpecies
        :return: bool - true or false if the taxon_id already exists
        """
        sel_model = self.seModel
        root = sel_model._rootItem
        # rootIndex = model.createIndex(root.row, 0, root)

        taxonCol = sel_model.get_role_number("taxonomyId")
        typeCol = sel_model.get_role_number("type")

        type = sel_model.data(idx, typeCol).value()
        if type and (type == "Mix" or type == "Submix"):
            parent = sel_model.item(idx).value()
        else:
            parent = root

        logging.info('selection: ' + str(selection))
        for row in selection: #self.currentSpeciesModel.selectionModel():
            logging.info("row: " + str(row))

        result = False


        return result

    @pyqtSlot(QJSValue, QModelIndex, str)
    def append_tree_item_with_sql(self, data, idx, parent_type):
        """
        Method to insert a row in the self._selected_species_model model
        :param data: QJSValue dict - data to be appended as a new row
        :param idx: QModelIndex - index of the currently selected item in tvSelectedSpecies
        :param parent_type: str - the type of entry being added:  Mix, Taxon, or Debris
        :return: None
        """

        if isinstance(data, QJSValue):
            data = data.toVariant()     # Convert from QJSValue to dict

        # Get references to key objects of interest
        model = self.seModel
        dataType = data["type"]

        # Insert a new row and get a handle to the newly inserted child + it's row position
        if (parent_type == "Mix" or parent_type == "Submix") and dataType != "Debris":     # Mix is the current type
            parent = model.getItem(idx)
            parentIdx = idx
        # elif parent_type == "Taxon" or parent_type == "Debris":   # Taxon or Debris is the current type
        #     parent = model._rootItem
        #     parentIdx = QModelIndex()
        else:                           # Type is None - nothing is selected
            parent = model._rootItem
            parentIdx = QModelIndex()

        # insertRows > position, count, parent index
        status = model.insertRows(parent.childCount(), 1, parentIdx)
        # status = model.insertRows(parent.childCount(), 1, idx.parent())
        child = parent.child(parent.childCount()-1)
        row = child.row

        # Update the speciesCount - I call the method which then emits a signal
        if dataType == "Taxon":
            self.speciesCount += 1

        # Update the newly created child/row data with the data from tvAvailableSpecies model
        for element in data:
            if element in model.rootData: # and data[element] is not None: # and data[element] != "":
                column = model.getColumnNumber(element)
                if column >= 0:
                    index = model.createIndex(row, column, child)
                    role = model.getRoleNumber(role_name=element)
                    if element == "displayName" and data["type"] == "Debris":
                        data[element] = "Debris - " + data[element]
                    status = model.setData(index, data[element], role)

        # Update the model._descendantSpecies list - do this after the data has been updated
        colNum = model.getColumnNumber("taxonomyId")
        taxonId = child.data(colNum)
        if taxonId.value():
            model.append_descendant(taxonId)

        # Insert new record in the CATCH table for the given haul
        is_debris = "False"
        is_mix = "False"
        displayName = data["displayName"]
        catchContentId = None
        if data["type"] == "Debris":
            displayName = displayName.replace("Debris - ", "")
            is_debris = "True"
            catchContentId = data["catchContentId"]
        elif data["type"] == "Mix" or data["type"] == "Submix":
            is_mix = "True"
        elif data["type"] == "Taxon":
            catchContentId = data["catchContentId"]

        # Determine if a PARENT_CATCH_ID exists for this record or not
        parentCatchId = None
        if parent.data(model.getColumnNumber("displayName")).value() != "displayName":
            parentCatchId = parent.data(model.getColumnNumber("catchId")).value()

        # TODO todd hay - remove MIX_NUMBER from CATCH table - do we need this anymore?
        # TODO todd hay - CATCH Table - Drop OPERATION_TYPE_ID
        sql = "INSERT INTO CATCH (PARENT_CATCH_ID, CATCH_CONTENT_ID, DISPLAY_NAME, IS_MIX, IS_DEBRIS, OPERATION_ID) " + \
            "VALUES(?, ?, ?, ?, ?, ?);"
        params = [parentCatchId, catchContentId, displayName, is_mix, is_debris, self._app.state_machine._haul["haul_id"]]
        # print('params: ' + str(params))
        result = self._db.execute(query=sql, parameters=params)

        if result:
            catchId = self._db.get_last_rowid()
            column = model.getColumnNumber("catchId")
            index = model.createIndex(row, column, child)
            role = model.getRoleNumber(role_name="catchId")
            status = model.setData(index, catchId, role)

    @pyqtSlot(QModelIndex)
    def remove_tree_item(self, index):
        """
        Method to retrieve a FramTreeItem from a FramTreeModel
        :param index: QModelIndex - the item to remove
        :return: None
        """
        if not isinstance(index, QModelIndex):
            return

        model = self.seModel

        # Get the existing catchId from the data - Do before deleting the actual row
        item = model.getItem(index)
        typeCol = model.getColumnNumber("type")
        catchId = item.data(model.getColumnNumber("catchId")).value()

        type = item.data(typeCol).value()
        if type == "Taxon":
            self.speciesCount -= 1

        elif type == "Mix":

            if isinstance(self._active_mix, QJSValue):
                self._active_mix = self._active_mix.toVariant()
            if catchId == self._active_mix["catchId"]:
                self.activeMix = {"displayName": None, "catchId": None}

            # recurse to check all children + subchildren
            self.speciesCount -= len([x for x in item.children if x.data(typeCol).value() == "Taxon"])
            submixes = [x for x in item.children if x.data(typeCol).value() == "Submix"]
            for submix in submixes:
                self.speciesCount -= len([x for x in submix.children if x.data(typeCol).value() == "Taxon"])

                # If the submix is the activeMix and we're removing the submix, then set the activeMix to None
                if submix.data(model.getColumnNumber('catchId')).value() == self._active_mix["catchId"]:
                    self.activeMix = {"displayName": None, "catchId": None}

        elif type == "Submix":

            if isinstance(self._active_mix, QJSValue):
                self._active_mix = self._active_mix.toVariant()
            if catchId == self._active_mix["catchId"]:
                self.activeMix = {"displayName": None, "catchId": None}

            # recurse to check all children
            self.speciesCount -= len([x for x in item.children if x.data(typeCol).value() == "Taxon"])


        # Remove the rows
        parentIdx = model.parent(index)
        status = model.removeRows(index.row(), 1, parentIdx)

        # Decrement the species count - this is shown in the upper right corner of the screen
        # self.speciesCount -= 1

        # Delete from the database
        if isinstance(catchId, int):

            catch_sql = """
                        WITH RECURSIVE subcatch(n) AS (
                          SELECT CATCH_ID FROM CATCH WHERE CATCH_ID = ?
                          UNION
                          SELECT c.CATCH_ID FROM CATCH c, subcatch
                          WHERE c.PARENT_CATCH_ID = subcatch.n
                        )
                        DELETE FROM CATCH WHERE CATCH_ID in subcatch;
                        """

            specimen_sql = """
                        WITH RECURSIVE subcatch(n) AS (
                          SELECT CATCH_ID FROM CATCH WHERE CATCH_ID = ?
                          UNION
                          SELECT c.CATCH_ID FROM CATCH c, subcatch
                          WHERE c.PARENT_CATCH_ID = subcatch.n
                        ),
                        subspecimens(n) AS (
                          SELECT SPECIMEN_ID FROM SPECIMEN s INNER JOIN CATCH c
                                    ON c.CATCH_ID = s.CATCH_ID WHERE c.CATCH_ID in subcatch
                          UNION
                          SELECT s.SPECIMEN_ID FROM SPECIMEN s, subspecimens
                          WHERE s.PARENT_SPECIMEN_ID = subspecimens.n
                        )
                        DELETE FROM SPECIMEN WHERE SPECIMEN_ID IN subspecimens;
                        """

            params = [catchId, ]
            self._db.execute(query=specimen_sql, parameters=params)
            self._db.execute(query=catch_sql, parameters=params)

    def _get_debris(self):
        """
        Method to retrieve all of the debris items from the database.  This is used to populate the list of
        possibel debris in the ProcessCatchScreen
        :return: list - containing the list of debris from CATCH_CONTENT_LU
        """
        debris = []
        sql = "SELECT * FROM CATCH_CONTENT_VW WHERE TYPE = 'Debris';"
        for d in self._db.execute(sql):
            new_debris = dict()
            new_debris["displayName"] = d[2]
            new_debris["weight"] = None
            new_debris["count"] = None
            new_debris["type"] = d[13]
            new_debris["catchContentId"] = d[14]
            debris.append(new_debris)

        debris = sorted(debris, key=lambda x: x['displayName'].upper())
        return debris

    def _get_species(self):
        """
        Method to retrieve all of the species from the database.  This is used to populate the list of
        possible species in the ProcessCatchScreen
        :return: dictionary containing the species
        """
        species = []

        # Get all of the FRAM-specific protocols, tied to the TAXONOMY_ID - this is used to update the protocol
        # display below as there might be non-FRAM PI's who have a sampling plan for a given TAXONOMY_ID
        protocols = self._get_fram_protocols()

        # TODO (todd.hay) Get the species-specific protocol information as well
        sql = "SELECT * FROM CATCH_CONTENT_VW WHERE TYPE = 'Taxon';"

        # sql = "SELECT CONTENTS_ID, SCIENTIFIC_NAME, COMMON_NAME_1, COMMON_NAME_2, COMMON_NAME_3, DISPLAY_NAME, " + \
        #       "HISTORICAL_DEPTH_MIN, HISTORICAL_DEPTH_MAX, HISTORICAL_LAT_MIN, HISTORICAL_LAT_MAX, IS_MOST_RECENT " + \
        #       "FROM CATCH_CONTENTS_LU c INNER JOIN TYPES_LU t ON c.CONTENT_TYPE_ID = t.TYPE_ID " + \
        #       "WHERE t.CATEGORY = 'Content' AND t.TYPE = 'Taxon';"

        for s in self._db.execute(sql):

            new_species = dict()
            new_species["taxonomyId"] = s[0]
            new_species["protocol"] = protocols[s[0]] if s[0] in protocols else s[1]
            new_species["displayName"] = s[2]
            new_species["scientificName"] = s[3]
            new_species["commonName1"] = s[4] if s[4] else ""
            new_species["commonName2"] = s[5] if s[5] else ""
            new_species["commonName3"] = s[6] if s[6] else ""
            new_species["weight"] = None
            new_species["count"] = None
            new_species["depthMin"] = s[7] if s[7] else None
            new_species["depthMax"] = s[8] if s[8] else None
            new_species["latMin"] = s[9] if s[9] else None
            new_species["latMax"] = s[10] if s[10] else None
            new_species["isMostRecent"] = s[11] if s[11] else "False"
            new_species["isLastNOperations"] = s[12] if s[12] else ""
            new_species["type"] = s[13] if s[13] else None
            new_species["catchContentId"] = s[14] if s[14] else None
            species.append(new_species)

        species = sorted(species, key=lambda x: x['displayName'].upper())
        return species

    @staticmethod
    def _set_selected_species_model():
        """
        Method that defines the species already selected for the self._activeHaul
        :return: FramTreeModel - the model used with the tvSelectedSpecies TreeView
        """

        # TODO Need to add sampleType (i.e. fish, salmon, coral - to drive Fish Sampling Screen)
        # headers = ["taxonomyId", "displayName", "scientificName",
        #            "protocol", "weight", "count", "depthMin", "depthMax", "latMin", "latMax",
        #            "isMostRecent", "isLastNOperations", "type", "sampleType", "catchContentId", "catchId"]
        headers = ["taxonomyId", "scientificName", "commonName1", "commonName2", "commonName3", "displayName",
                   "protocol", "weight", "count", "depthMin", "depthMax", "latMin", "latMax",
                   "isMostRecent", "isLastNOperations", "type", "sampleType", "catchContentId", "catchId"]

        data = []
        species_model = SpeciesTreeModel(headers=headers, data=data)

        return species_model

    @pyqtProperty(QVariant, notify=selectedIndexChanged)
    def selectedIndex(self):
        """
        Returns the QModelIndex of the currently selected item
        :return:
        """
        return self._selected_index

    @selectedIndex.setter
    def selectedIndex(self, value):

        # if index is None:
        #     index = QModelIndex()
        if isinstance(value, QJSValue):
            value = value.toVariant()
        self._selected_index = value
        self.selectedIndexChanged.emit()

    @pyqtSlot()
    def updateWeightCount(self):
        """
        Method called when returning from WeighBaskets to update the weights/num basket count of the
        selected species
        :return:
        """
        # Get the update weight/count data
        catch_id = self._app.state_machine.species["catch_id"]
        results = self._get_basket_weights_counts(catch_id=catch_id)

        # logging.info('selectedIndex: {0}'.format(self.selectedIndex))

        try:

            # Update the model
            model = self.seModel
            idx = self.selectedIndex["currentIndex"]
            item = model.getItem(idx)
            row = idx.row()

            for x in list(results):
                col = model.getColumnNumber(x)

                if col != -1:
                    index = model.createIndex(row, col, item)
                    value = results[x]
                    role = model.getRoleNumber(role_name=x)
                    status = model.setData(index, value, role)

                    logging.info('{0} = {1}, row: {2}, col: {3}, role: {4}, status: {5}'.
                             format(x, value, row, col, role, status))
                    # logging.info('rootData: {0}'.format(model.rootData))

        except Exception as ex:

            pass

    def _get_basket_weights_counts(self, catch_id):
        """
        Method to get the total weight + number of baskets for the given catch_id.  This is called
        by initialize_tree when entering ProcessCatch and by TrawlBackdeckStateMachine when
        returning to ProcessCatch from the WeighBaskets screen, so as to update the values for the
        currently selected species
        :param catch_id: int
        :return: dict - contains the "weight" and "count"
        """
        if not isinstance(catch_id, int):
            return

        try:
            display_name = Catch.select().where(Catch.catch == catch_id).get().display_name
        except DoesNotExist as ex:
            display_name = ""
            logging.info('Could not find the display name: ' + str(ex))

        baskets_sql = """
            WITH RECURSIVE subcatch(n) AS (
              SELECT c.CATCH_ID FROM CATCH c
                    WHERE c.CATCH_ID = ?
              UNION
              SELECT c.CATCH_ID FROM CATCH c, subcatch
              WHERE c.PARENT_CATCH_ID = subcatch.n AND c.DISPLAY_NAME = ?
            )
            select WEIGHT_KG, SAMPLE_COUNT_INT from CATCH c
                WHERE c.CATCH_ID in subcatch AND c.RECEPTACLE_SEQ IS NOT NULL
            """

        params = [catch_id, display_name]
        total_weight = 0
        num_baskets = 0
        for basket in self._db.execute(query=baskets_sql, parameters=params):
            total_weight += basket[0] if basket[0] else 0
            num_baskets += 1 if basket[0] else 0

        # logging.info('display name: ' + str(display_name) + ', weight: ' + str(total_weight) + ', count: ' + str(num_baskets))

        return {"weight": total_weight, "count": num_baskets}

    @pyqtSlot(result=QVariant)
    def checkSpeciesForData(self):
        """
        Method to determine if catch / specimen data has been collected for the species
        :return: QVariant - dict - containing counts of baskets + specimens
        """
        try:
            results = {"baskets": 0, "specimens": 0}

            catch_id = self._app.state_machine.species["catch_id"]

            baskets_sql = """
                        WITH RECURSIVE subcatch(n) AS (
                          SELECT c.CATCH_ID FROM CATCH c
                                WHERE c.CATCH_ID = ?
                          UNION
                          SELECT c.CATCH_ID FROM CATCH c, subcatch
                          WHERE c.PARENT_CATCH_ID = subcatch.n
                        )
                        select count(*) from CATCH c WHERE c.CATCH_ID in subcatch
                         AND c.RECEPTACLE_SEQ IS NOT NULL
                        """
            for basket in self._db.execute(query=baskets_sql, parameters=[catch_id,]):
                results["baskets"] = basket[0]

            specimens_sql = """
                        WITH RECURSIVE subcatch(n) AS (
                          SELECT c.CATCH_ID FROM CATCH c WHERE c.CATCH_ID = ?
                          UNION
                          SELECT c.CATCH_ID FROM CATCH c, subcatch
                          WHERE c.PARENT_CATCH_ID = subcatch.n
                        ),
                        subspecimens(n) AS (
                          SELECT SPECIMEN_ID FROM SPECIMEN s INNER JOIN CATCH c
                                    ON c.CATCH_ID = s.CATCH_ID WHERE c.CATCH_ID in subcatch
                          UNION
                          SELECT s.SPECIMEN_ID FROM SPECIMEN s, subspecimens
                          WHERE s.PARENT_SPECIMEN_ID = subspecimens.n
                        )
                        SELECT count(*) FROM SPECIMEN WHERE SPECIMEN_ID IN subspecimens
                            AND PARENT_SPECIMEN_ID IS NULL;
                        """
            for specimen in self._db.execute(query=specimens_sql, parameters=[catch_id,]):
                results["specimens"] = specimen[0]

        except Exception as ex:
            logging.info("Error getting basket and/or specimen counts: " + str(ex))
            return {"baskets": -1, "specimens": -1}

        return results

    @pyqtSlot(result=QVariant)
    def get_species_per_haul(self):
        """
        Method to return all of the selected species for the self._haul
        :return: list of dicts - containing all of the species for the given haul
        """
        species = []

        sql = "SELECT * FROM CATCH_VW WHERE HAUL_NUMBER = ?;"

        sql = "SELECT c.CATCH_ID, c.PARENT_CATCH_ID, c.WEIGHT_KG, " + \
              "c.SAMPLE_COUNT_INT, t.SCIENTIFIC_NAME, cc.DISPLAY_NAME " + \
              "FROM CATCH c " + \
              "INNER JOIN HAULS h ON c.OPERATION_ID = h.HAUL_ID " + \
              "INNER JOIN CATCH_CONTENT_LU cc ON cc.CATCH_CONTENT_ID = c.CATCH_CONTENT_ID " + \
              "INNER JOIN TAXONOMY_LU t ON cc.TAXONOMY_ID = t.TAXONOMY_ID " + \
              "WHERE h.HAUL_ID = ?;"
        params = [self._app.state_machine._haul["haul_id"], ]
        for s in self._db.execute(query=sql, parameters=params):
            new_species = {}
            new_species["catch_partition_id"] = s[0]
            new_species["parent_id"] = s[1] if s[1] else None
            new_species["weight"] = s[2] if s[2] else None
            new_species["count"] = s[3] if s[3] else None
            new_species["scientific_name"] = s[4] if s[4] else None
            new_species["display_name"] = s[5] if s[5] else None

            species.append(new_species)

        return species

    def get_salmon_species(self):
        """
        Method to return all of the salmon species.  Used to drive the salmon-based FishSamplingScreen
        selection   in ProcessCatchScreen.qml
        :return: list - all of the taxonomyId related to salmon species
        """
        salmon = []
        sql = "SELECT DISTINCT TAXONOMY_ID FROM SALMON_SPECIES_VW;"
        for row in self._db.execute(query=sql):
            salmon.append(row[0])

        return salmon

    def get_coral_species(self):
        """
        Method to return all of the coral species.  Used to drive the coral-based FishSamplingScreen
        selection in ProcessCatchScreen.qml
        :return: list - all of the taxonomyId related to salmon species
        """
        corals = []
        sql = "SELECT DISTINCT TAXONOMY_ID FROM CORAL_SPECIES_VW;"
        for row in self._db.execute(query=sql):
            corals.append(row[0])

        return corals

    def get_sponge_species(self):
        """
        Method to return all of the sponge speccies.  Used to drive the
        sponge-based selection in ProcessCatchScreen.qml to push user over to the
        SpecialActionsScreen.qml
        :return:
        """
        sponges = []
        sql = "SELECT DISTINCT TAXONOMY_ID FROM SPONGE_SPECIES_VW;"
        for row in self._db.execute(query=sql):
            sponges.append(row[0])

        return sponges

    def get_rockfish_species(self):
        """
        Method to return all of the rockfish species.  Used to drive barcode collection
        for Peter Sudmant (UC Berkeley) asking for muscle tissue for any rockfish
        during 2019 survey season
        :return:
        """
        rockfish = []
        sql = "SELECT DISTINCT TAXONOMY_ID FROM ROCKFISH_SPECIES_VW;"
        for row in self._db.execute(query=sql):
            rockfish.append(row[0])

        return rockfish

    @pyqtSlot(str, int, result=bool)
    def checkSpeciesType(self, type, taxonId):
        """
        Method to return the listing of the corals, as a pyqtProperty
        :return:
        """
        if type == "salmon":
            return taxonId in self._salmon

        elif type == "coral":
            return taxonId in self._corals

        elif type == "sponge":
            return taxonId in self._sponges

        elif type == "rockfish":
            return taxonId in self._rockfish

    # @pyqtSlot(str, str, QModelIndex)
    @pyqtSlot()
    def renameMixes(self):
        """
        Method called by ProcessCatchScreen.qml, in the removeSpecies function when a mix or
        a submix is removed from the selected species TreeView.  This does not relabel the 
        items in the TreeView, as that is handled directly by the tree view, however, it does
        update the catch.display_name's for all of the mixes and submixes that follow this
        provided mix
        :param mixType: 
        :param name: 
        :param parentIndex: 
        :return: 
        """
        # if mixType is None:
        #     return
        #
        # if not isinstance(parentIndex, QModelIndex):
        #     return

        try:
            logging.info(f"mixes: {self.seModel.mixCount}")

            type_col = self.seModel.getColumnNumber("type")

            display_name_col = self.seModel.getColumnNumber("displayName")
            display_name_role = self.seModel.getRoleNumber(role_name="displayName")

            catch_id_col = self.seModel.getColumnNumber("catchId")
            catch_id_role = self.seModel.getRoleNumber(role_name="catchId")

            mixes = [x for x in self.seModel.rootItem.children
                     if x.data(column=type_col).value() == "Mix"]

            for mix_count, mix in enumerate(mixes):
                mix_display_name = mix.data(column=display_name_col).value()

                if int(mix_display_name.strip("Mix #")) - 1 != mix_count:
                    catch_id = mix.data(column=catch_id_col).value()
                    value = f"Mix #{mix_count+1}"
                    Catch.update(display_name = value).where(Catch.catch == catch_id).execute()

                    index = self.seModel.createIndex(mix.row, display_name_col, mix)
                    self.seModel.setData(index=index, value=value, role=display_name_role)

                    logging.info(f"mix to update, catch_id: {catch_id}, {mix_display_name} > {value}")

                submixes = [x for x in mix.children
                            if x.data(column=type_col).value() == "Submix"]

                for submix_count, submix in enumerate(submixes):
                    sm_display_name = submix.data(column=display_name_col).value()

                    if int(sm_display_name.strip("Submix #")) - 1 != submix_count:
                        catch_id = submix.data(column=catch_id_col).value()
                        value = f"Submix #{submix_count+1}"
                        Catch.update(display_name=value).where(Catch.catch == catch_id).execute()

                        index = self.seModel.createIndex(submix.row, display_name_col, submix)
                        self.seModel.setData(index=index, value=value, role=display_name_role)

                        logging.info(f"submix to update, catch_id: {catch_id}, {sm_display_name} > {value}")

        except Exception as ex:
            logging.error(f"Error renaming the mixes: {ex}")
