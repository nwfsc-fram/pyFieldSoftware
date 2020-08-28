__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        WeighBaskets.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 11, 2016
# License:     MIT
#-------------------------------------------------------------------------------
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QVariant, QModelIndex
from py.common.FramListModel import FramListModel
import logging
from peewee import *
from py.trawl.TrawlBackdeckDB_model import Catch, TypesLu


class BasketsListModel(FramListModel):

    def __init__(self, parent=None):
        super().__init__()

        self.add_role_name(name='basketNumber')
        self.add_role_name(name='weight')
        self.add_role_name(name='count')
        self.add_role_name(name='subsample')
        self.add_role_name(name='catchId')
        self.add_role_name(name='isWeightEstimated')
        self.add_role_name(name='isFishingRelated')
        self.add_role_name(name='isMilitaryRelated')


class WeighBaskets(QObject):
    """
    Class for the WeighBasketsScreen.
    """
    speciesChanged = pyqtSignal(QVariant, arguments=["taxonomy_id",])
    basketCountChanged = pyqtSignal()
    totalWeightChanged = pyqtSignal()
    subsampleCountChanged = pyqtSignal()
    lastSubsampleBasketChanged = pyqtSignal()
    basketAdded = pyqtSignal()
    modeChanged = pyqtSignal()
    # weightTypeChanged = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

        self._baskets = []
        self._basket_count = 0
        self._total_weight = 0
        self._model = BasketsListModel()
        self._subsample_count = 0
        self._last_subsample_basket = -1
        # self._mode = "takeWeight"
        self._weight_type = "scaleWeight"

    # @pyqtProperty(str, notify=weightTypeChanged)
    # def weightType(self):
    #     """
    #     Return the current weightType
    #     :return:
    #     """
    #     return self._weight_type
    #
    # @weightType.setter
    # def weightType(self, value):
    #     """
    #     Method to set the weightType
    #     :param value:
    #     :return:
    #     """
    #     if not isinstance(value, str):
    #         return
    #
    #     self._weight_type = value
    #     self.weightTypeChanged.emit()

    @pyqtProperty(str, notify=modeChanged)
    def mode(self):
        """
        Return the current mode the screen is in
        :return:
        """
        return self._mode

    @mode.setter
    def mode(self, value):
        """
        Set the current mode
        :param value: str - the mode
        :return:
        """
        if not isinstance(value, str):
            return

        self._mode = value
        self.modeChanged.emit()

    @pyqtProperty(int, notify=lastSubsampleBasketChanged)
    def lastSubsampleBasket(self):
        """

        :return:
        """
        return self._last_subsample_basket

    @lastSubsampleBasket.setter
    def lastSubsampleBasket(self, value):
        """
        Method to set the self._last_subsample_basket - This is used for keeping track of when the last
        subsample was taken, so as to notify the user if the next basket should be a subsample
        :param value:
        :return:
        """
        self._last_subsample_basket = value
        self.lastSubsampleBasketChanged.emit()

    @pyqtProperty(int, notify=basketCountChanged)
    def basketCount(self):
        """
        Returns the basketCount
        :return: int - basketCount
        """
        return self._basket_count

    @basketCount.setter
    def basketCount(self, value):

        if not isinstance(value, int):
            return

        self._basket_count = value
        self.basketCountChanged.emit()

    @pyqtProperty(float, notify=totalWeightChanged)
    def totalWeight(self):
        """
        Method for getting the total weight of all baskets
        :return:
        """
        return self._total_weight

    @totalWeight.setter
    def totalWeight(self, value):

        # if not isinstance(value, float) and not isinstance(value, int):
        #     return
        try:
            value = float(value)
        except Exception as ex:
            return

        self._total_weight = value
        self.totalWeightChanged.emit()

    @pyqtProperty(int, notify=subsampleCountChanged)
    def subsampleCount(self):
        """
        Return the subsample count.  This is used to ensure that the user sets aside a subsample
        after N number of baskets
        :return: int - subsample_countt
        """
        return self._subsample_count

    @subsampleCount.setter
    def subsampleCount(self, value):
        """
        Set the subsample_count
        :return:
        """
        self._subsample_count = value
        self.subsampleCountChanged.emit()

    @pyqtProperty(QVariant, notify=speciesChanged)
    def model(self):
        """
        Return the model for the TableView
        :return:
        """
        return self._model

    @pyqtSlot()
    def initialize_list(self):
        """
        Method to reset all of the FramListModels to their original state of items.  This is called when
        the ProcessCatch is first initialized and then also whenever the haul id is changed, as the tree
        needs to be rebuilt from the database at that point
        :return: None
        """
        # Clear the list
        self._model.clear()

        # Establish working lists for available Full / Recent / Debris lists + filtered variants
        self._baskets = self.get_baskets()
        self.basketCount = len(self._baskets)
        total_weight = 0

        baskets = list(self._baskets)

        valuesSwap = {"True": "Yes", "False": "", }
        for i, basket in enumerate(baskets):
            basket["subsample"] = valuesSwap[basket["subsample"]] if basket["subsample"] else ""
            basket["isWeightEstimated"] = valuesSwap[basket["isWeightEstimated"]] if basket["isWeightEstimated"] else ""
            basket["isFishingRelated"] = valuesSwap[basket["isFishingRelated"]] if basket["isFishingRelated"] else ""
            basket["isMilitaryRelated"] = valuesSwap[basket["isMilitaryRelated"]] if basket["isMilitaryRelated"] else ""
            if basket["subsample"] == "Yes":
                self._last_subsample_basket = i+1
            total_weight += basket["weight"] if basket["weight"] else 0

        self.totalWeight = total_weight

        # Reset the list items
        if self._basket_count > 0:
            self._model.setItems(baskets)

    def get_baskets(self):
        """
        Get all of the existing baskets for the currently selected species.  This species is identified
        in the stateMachine
        :return: list of dictionaries of the baskets
        """
        baskets = []
        catch = Catch.select().where(Catch.parent_catch == self._app.state_machine.species["catch_id"])
        parent_name = self._app.state_machine.species["display_name"]

        self.speciesChanged.emit(self._app.state_machine.species["taxonomy_id"])

        for basket in catch:

            if basket.display_name == parent_name:
                basketDict = dict()
                basketDict["basketNumber"] = basket.receptacle_seq
                basketDict["weight"] = basket.weight_kg
                basketDict["count"] = basket.sample_count_int
                basketDict["subsample"] = basket.is_subsample
                basketDict["catchId"] = basket.catch
                basketDict["isWeightEstimated"] = basket.is_weight_estimated
                basketDict["isFishingRelated"] = basket.is_fishing_related
                basketDict["isMilitaryRelated"] = basket.is_military_related
                baskets.append(basketDict)

        baskets = sorted(baskets, key=lambda x: int(x["basketNumber"]))

        return baskets

    @pyqtSlot(QVariant)
    def add_list_item(self, weight):
        """
        Add an item to the baskets model
        :param weight: str - representing the weight to be added
        :return:
        """
        if weight is None:
            return

        is_int = False
        is_float = False

        try:
            weight = float(weight)
            is_float = True

        except ValueError:
            pass

        if not is_float:
            try:
                weight = int(weight)
            except ValueError:
                pass
            except Exception as ex:
                pass

        if not self._app.state_machine.species:
            return

        # Increase the basket count
        self.basketCount += 1
        self.totalWeight += weight

        # Insert into the database
        sql = "INSERT INTO CATCH (PARENT_CATCH_ID, CATCH_CONTENT_ID, DISPLAY_NAME, WEIGHT_KG, SAMPLE_COUNT_INT, " + \
              "IS_SUBSAMPLE, IS_WEIGHT_ESTIMATED, OPERATION_ID, IS_MIX, IS_DEBRIS, RECEPTACLE_SEQ) " + \
              "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        parent_catch_id = self._app.state_machine._species["catch_id"]
        catch_content_id = self._app.state_machine._species["catch_content_id"]
        display_name = self._app.state_machine._species["display_name"]
        operation_id = self._app.state_machine._haul["haul_id"]

        is_mix = "False"
        is_debris = "False"
        if "mix" in self._app.state_machine.species["display_name"].lower():
            is_mix = "True"
        elif "debris" in self._app.state_machine.species["display_name"].lower():
            is_debris = "True"
        params = [parent_catch_id, catch_content_id, display_name, weight, None,
                    None, "False", operation_id, is_mix, is_debris, self.basketCount]
        self._db.execute(query=sql, parameters=params)

        catchId = self._db.get_last_rowid()

        # Add to the model
        item = {"basketNumber": self.basketCount,
                "weight": weight,
                "count": "",
                "subsample": "",
                "catchId": catchId,
                "isWeightEstimated": "",
                "isFishingRelated": "",
                "isMilitaryRelated": ""}
        self._model.appendItem(item)

        self.basketAdded.emit()

    @pyqtSlot(int, str, QVariant)
    def update_list_item(self, index, property, value):
        """
        Method to update property of a list item
        :param index: int - index of the list item
        :param property: str - property to update
        :param value: str - new value
        :return:
        """

        if index is None or property is None:
            return

        if property not in ["weight", "count", "subsample", "basketNumber", "isWeightEstimated", "isFishingRelated",
                            "isMilitaryRelated"]:
            return

        fields = {"weight": "WEIGHT_KG", "count": "SAMPLE_COUNT_INT",
                  "subsample": "IS_SUBSAMPLE", "basketNumber": "RECEPTACLE_SEQ",
                  "isWeightEstimated": "IS_WEIGHT_ESTIMATED", "isFishingRelated": "IS_FISHING_RELATED",
                  "isMilitaryRelated": "IS_MILITARY_RELATED"}
        field = fields[property]

        if property == "weight":
            if value:
                try:
                    value = float(value)
                except ValueError as ex:
                    value = None
                except Exception as ex:
                    value = None
        elif property == "count":
            if value:
                try:
                    value = int(value)
                except ValueError as ex:
                    value = None
                except Exception as ex:
                    value = None
        elif property in ["subsample", "isWeightEstimated", "isFishingRelated", "isMilitaryRelated"]:
            if value:
                value = "True" if value.lower() == "yes" else None

        # Update the Database
        sql = "UPDATE CATCH SET " + field + " = ? WHERE CATCH_ID = ?;"
        params = [value, self.model.get(index)["catchId"]]
        self._db.execute(query=sql, parameters=params)

        #  Update the Model
        if property in ["subsample", "isWeightEstimated", "isFishingRelated", "isMilitaryRelated"]:
            if value:
                value = "Yes" if value.lower() == "true" else None

        # Update the totalWeight
        if property == "weight":
            previousWeight = self._model.get(index)["weight"]
            self.totalWeight -= previousWeight if previousWeight else 0
            self.totalWeight += value if value else 0

        self._model.setProperty(index, property, value)

        if property == "weight":
            self._app.sound_player.play_sound("takeWeight")

        # Reset the last subsample count
        self.reset_last_subsample_basket()

    @pyqtSlot(int)
    def delete_list_item(self, index):
        """
        Method to delete an item from the tvBaskets list
        :param index: int - index of the item to delete
        :return: None
        """

        # Delete from the database
        catchId = self.model.get(index)["catchId"]
        if isinstance(catchId, int):
            sql = "DELETE FROM CATCH WHERE CATCH_ID = ?;"
            params = [catchId, ]
            self._db.execute(query=sql, parameters=params)

        # Decrement the totalWeight +  basketCount
        self.basketCount -= 1
        self.totalWeight -= self.model.get(index)["weight"] if self.model.get(index)["weight"] else 0

        # Delete from the model
        self.model.removeItem(index)

        # Decrement the basket count appropriately (i.e. in an earlier index is deleted)
        """
        1   0
        2   1   < delete this basket
        3   2
        4   3

        should become:
        1   0
        3   2  >  2   1
        4   3  >  3   2
        """
        if index < self.basketCount:
            for i in range(index, self.basketCount):
                self.update_list_item(i, "basketNumber", i+1)

        self.reset_last_subsample_basket()

    def reset_last_subsample_basket(self):
        """
        Method called when basket row subsample values are added/updated/deleted that resets what is the current
        last subsample basket.  This is used for counting purposes to notify the user when to take another
        subsample
        :return:
        """
        subsamples = [i for i, x in enumerate(self._model.items) if x["subsample"] == "Yes"]
        if len(subsamples) > 0:
            self.lastSubsampleBasket = max(subsamples) + 1
        else:
            self.lastSubsampleBasket = 0

