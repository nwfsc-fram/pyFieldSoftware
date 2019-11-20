from PyQt5.QtQml import QJSValue

__author__ = 'Will.Smith'
# -----------------------------------------------------------------------------
# Name:        FramListModel.py
# Purpose:     Implementation of QAbstractListModel
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 4, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import QAbstractListModel, QVariant, QModelIndex, pyqtSlot, \
    pyqtProperty, Qt, pyqtSignal, QByteArray

import logging
import unittest
import random
from py.common.FramTestUtil import LoggingQueue


class FramListModel(QAbstractListModel):
    countChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._data_items = []
        self._roles = {}
        self._ordered_rolenames = []  # For use by ObserverData queries
        self._auto_role_id = Qt.UserRole + 1  # For use by "automatic" role adding

    @pyqtSlot(result=int)
    def rowCount(self, parent=None):
        """
        Override from QAbstractListModel
        :param parent:
        :return: # of items
        """
        return len(self._data_items)

    @pyqtProperty(int, notify=countChanged)
    def count(self):
        """
        Override from QAbstractListModel
        :return: # of items
        """
        return self.rowCount()

    @pyqtSlot(str)
    def add_role_name(self, name, role=None):
        """
        Add roles, used by Qt
        :param role: id for role
        :param name: string name for role
        """
        self._ordered_rolenames.append(name)
        if role is not None:
            self._roles[role] = name.encode('utf-8')  # convert to QByteArray
            self._auto_role_id = role + 1  # In case someone adds auto-role later
        else:
            self._roles[self._auto_role_id] = name.encode('utf-8')
            self._auto_role_id += 1

    # @pyqtProperty(QVariant)
    def roleNames(self):
        """
        Override from QAbstractListModel
        :return: role name dict
        """
        return self._roles

    def data(self, index, role):
        """
        Access data from _data_items
        NOTE: expects _data_items to be of subscriptable (dict) type
        Thus, all inserts must handle conversion (see append, insert)
        :param index:
        :param role:
        :return: dict item indicated by index
        """
        if not index.isValid():
            return QVariant()

        try:
            result = self._data_items[index.row()][self._roles[role].decode("utf-8")]
            return result
        except KeyError as e:
            self._logger.error('Are you accessing the correct model type? Could not find key {}'.format(e))
        except TypeError as te:
            self._logger.error('Is Type subscriptable? Details: {0}'.format(te))

    @pyqtSlot(str)
    def sort(self, rolename):
        """
        Sort the list in-place, using rolename as the key
        :param rolename: Key for sorting
        """
        # sorted_items = sorted(self._data_items, key=itemgetter(rolename))
        # Fixed to support case-insensitivity sorting
        try:
            # sorted_items = sorted(self._data_items, key=lambda x: x[rolename])
            sorted_items = sorted(self._data_items, key=lambda x: self.none_sorter(x[rolename]))
            self.setItems(sorted_items)
        except Exception as e:
            logging.error(e)

    @pyqtSlot(str)
    def none_sorter(self, input):
        """
        Used by the sort method to determine if the current value is None or not
        :param input: input to determine if it is none or not
        """
        if input is None:
            return ""
        return input

    @pyqtSlot(str)
    def sort_reverse(self, rolename):
        """
        Sort the list in-place, using rolename as the key
        :param rolename: Key for sorting
        """
        # sorted_items = sorted(self._data_items, key=itemgetter(rolename))
        # Fixed to support case-insensitivity sorting
        try:
            sorted_items = sorted(self._data_items, key=lambda x: x[rolename], reverse=True)
            self.setItems(sorted_items)
        except Exception as e:
            logging.error(e)

    @pyqtSlot(int, result="QVariantMap")
    def get(self, index):
        """
        Direct access for an item
        :param index: integer index
        :return:
        """
        try:
            if index < 0 or index >= len(self._data_items):
                raise IndexError('Index out of range for model get(): ' + str(index))
            return self._data_items[index]
        except IndexError as e:
            self._logger.error(e)
            return QVariant()

    @pyqtProperty("QVariantList")
    def items(self):
        """
        List of all items in model
        :return: list of items
        """
        return self._data_items

    @pyqtSlot()
    def clear(self):
        """
        Delete all items in list
        """
        self.beginResetModel()
        self._data_items.clear()
        self.endResetModel()

    @pyqtSlot()
    def setItems(self, items):
        """
        Set all of the items at once
        :param items: list of dictionary element items
        :return:
        """
        self.clear()  # Careful - this will clear the items param, if set earlier (reference)
        self.beginInsertRows(QModelIndex(), 0, len(items) - 1)
        # del self._data_items[:]
        self._data_items = items
        self.endInsertRows()
        self.countChanged.emit(self.rowCount())

    # @pyqtSlot(dict)
    def appendItem(self, item):
        """
        Insert item at end of list
        :param item: item to insert (dict)
        :return: index of item
        """
        append_idx = len(self._data_items)
        self.insertItem(append_idx, item)
        return append_idx

    @pyqtSlot(QJSValue)
    def append(self, item):
        """
        For consistency with ListModel
        :param item: item to insert (dict)
        :return: index of item
        """
        # Need to convert to dict, since QJSValue not subscriptable (?)
        return self.appendItem(item.toVariant())

    # @pyqtSlot(int, dict)
    def insertItem(self, index, item):
        """
        Insert item in list by index
        :param index: array pos (int)
        :param item: item dict
        """
        # beginInsertRows from QAbstractListModel:
        self.beginInsertRows(QModelIndex(), index, index)
        self._data_items.insert(index, item)
        self.endInsertRows()
        self.countChanged.emit(self.rowCount())

    @pyqtSlot(int, QJSValue)
    def insert(self, index, item):
        """
        For consistency with ListModel
        :param index: index for insertion (int)
        :param item: item to insert (converted to)
        """
        # Need to convert to dict, since QJSValue not subscriptable
        self.insertItem(index, item.toVariant())

        # Don't believe that we need to emit a dataChanged signal here as
        # a countChanged signal is emitted by the insertItem method
        self.dataChanged.emit(self.index(index, 0), self.index(index, 0))

    @pyqtSlot(int, QJSValue)
    def replace(self, index, item):
        """
        Replace an item at index
        :param index: index for replacement (int)
        :param item: item data
        """
        if isinstance(item, QJSValue):
            item = item.toVariant()

        # Did not find a beginReplaceRows function, so apparently not needed
        try:
            self._data_items[index] = item
        except Exception as e:
            self._logger.error(e)
        self.dataChanged.emit(self.index(index, 0), self.index(index, 0))

    @pyqtSlot(int)
    def removeItem(self, index):
        """
        Delete item at index
        :param index:
        """
        try:
            if index < 0 or index >= len(self._data_items):
                raise IndexError('Index out of range for model removeItem(): ' + str(index))
            # self._logger.debug("Index of item to remove = {}".format(index))
            self.beginRemoveRows(QModelIndex(), index, index)
            del self._data_items[index]
            self.endRemoveRows()
            self.countChanged.emit(self.rowCount())
        except IndexError as e:
            self._logger.error(e)

    @pyqtSlot(int)
    def remove(self, index):
        """
        Implemented to be consistent with QML ListModel methods
        :param index: index of the row to remove
        :return:
        """

        self.removeItem(index)

    @pyqtSlot(int, str, QVariant)
    def setProperty(self, index, property, value):
        """
        Override from QAbstractListModel
        :param index: index of property to set (int)
        :param property: name of property
        :param value: value to set
        """
        try:
            self._data_items[index][property] = value
            # self._logger.debug(f"data_items[{index}]['{property}'] = {value}")
            self.dataChanged.emit(self.index(index, 0), self.index(index, 0))
        except IndexError as ie:
            self._logger.error(f"Caught Exception: {type(ie).__name__}: {ie}. " +
                    f"Property='{property}', index={index}, value={value}.")

    @pyqtSlot(str, result=int)
    def get_role_number(self, role_name):
        """
        Method to return the role number given the role_name
        :param role_name: str - role_name
        :return:
        """
        qba = QByteArray(role_name.encode('utf-8'))
        return list(self._roles.keys())[list(self._roles.values()).index(qba)]

    @property
    def ordered_rolenames(self):
        return self._ordered_rolenames

    @pyqtSlot(QVariant, QVariant, result=bool)
    def is_item_in_model(self, rolename, value):
        """
        Check if a value with the given role is in the model
        (Does a string compare.)
        :param rolename: rolename for search
        :param value: value to look for
        :return: True if item in the model
        """
        if isinstance(rolename, QJSValue):
            rolename = rolename.toVariant()
        if isinstance(value, QJSValue):
            value = value.toVariant()

        value = str(value)
        for item in self.items:
            if str(item[rolename]) == str(value):
                # logging.info(rolename + ' item in model: ' + str(value))
                return True

        # logging.info(rolename + ' item NOT in model: ' + str(value))
        return False

    @pyqtSlot(QVariant, QVariant, result=int)
    def get_item_index(self, rolename, value):
        """
        Does order n search,
        Find index of a value with the given role is in the model (via string compare.)
        TODO faster way to do this?

        :param rolename: rolename for search
        :param value: value to look for
        :return: integer index of item, -1 if not found
        """
        if isinstance(rolename, QJSValue):
            rolename = rolename.toVariant()
        if isinstance(value, QJSValue):
            value = value.toVariant()

        value = str(value)
        for idx in range(0, self.count):
            if str(self.items[idx][rolename]) == str(value):
                return idx
        return -1

    @pyqtSlot(QVariant, QVariant, result=QVariant)
    def where(self, rolename, value):
        """
        Does order n search,
        Find item of a value with the given role is in the model (via string compare.)
        This is an extension of the get_item_index method above, in that this will
        return a list of all of the items that match the rolename/value query.  Note that
        this returns the indexes + actual items

        :param rolename: rolename for search
        :param value: value to look for
        :return: list of indexes and items found, or an empty list if none are found
        """
        if isinstance(rolename, QJSValue):
            rolename = rolename.toVariant()
        if isinstance(value, QJSValue):
            value = value.toVariant()

        list_items = [{"index": i, "item": x} for i, x in enumerate(self.items) if x[rolename] == str(value)]
        return list_items if list_items else (None, None)



class TestFramListModel(unittest.TestCase):
    """
    Unit tests: Test basic FramListModel functionality - not comprehensive
    """

    testRole = Qt.UserRole + 1
    testRole2 = Qt.UserRole + 2
    testRole3 = Qt.UserRole + 3

    testing_data = [{'testrole': 'testing one', 'testrole2': 'testing two'},
                    {'testrole': 'testing three', 'testrole2': 'testing four'}]

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        # Log messages to a queue
        self.logger = logging.getLogger()
        self.logging_queue = LoggingQueue()
        q_handler = logging.handlers.QueueHandler(self.logging_queue)
        self.logger.addHandler(q_handler)

        self.testmodel = FramListModel()

    def addroles(self):
        self.testmodel.add_role_name('testrole', self.testRole)
        self.testmodel.add_role_name('testrole2', self.testRole2)
        self.testmodel.add_role_name('testrole3', self.testRole3)

    def addroles_auto(self):
        self.testmodel.add_role_name('testrole')
        self.testmodel.add_role_name('testrole2')
        self.testmodel.add_role_name('testrole3')

    def test_addroles(self):
        self.addroles()

    def test_addroles(self):
        self.addroles_auto()

    def adddata(self):
        for data in self.testing_data:
            self.testmodel.appendItem(data)

    def test_appendItem(self):
        self.addroles()
        self.adddata()

    def test_appendItemAutorole(self):
        self.addroles_auto()
        self.adddata()

    def test_data(self):
        self.addroles()
        self.adddata()
        testidx = self.testmodel.index(0, 0)
        self.assertEqual(self.testmodel.data(testidx, self.testRole), 'testing one')
        self.assertEqual(self.testmodel.data(testidx, self.testRole2), 'testing two')
        testidx = self.testmodel.index(1, 0)
        self.assertEqual(self.testmodel.data(testidx, self.testRole), 'testing three')
        self.assertEqual(self.testmodel.data(testidx, self.testRole2), 'testing four')

    def test_data_autorole(self):
        self.addroles_auto()
        self.adddata()
        testidx = self.testmodel.index(0, 0)
        self.assertEqual(self.testmodel.data(testidx, self.testRole), 'testing one')
        self.assertEqual(self.testmodel.data(testidx, self.testRole2), 'testing two')
        testidx = self.testmodel.index(1, 0)
        self.assertEqual(self.testmodel.data(testidx, self.testRole), 'testing three')
        self.assertEqual(self.testmodel.data(testidx, self.testRole2), 'testing four')

    def test_set_property(self):
        self.addroles()
        self.adddata()
        item = self.testmodel.get(0)
        self.assertEqual(item['testrole2'], 'testing two')
        self.testmodel.setProperty(0, 'testrole2', 'changed')
        self.testmodel.setProperty(1, 'testrole2', 'changed2')
        item = self.testmodel.get(0)
        self.assertEqual(item['testrole2'], 'changed')
        item2 = self.testmodel.get(1)
        self.assertEqual(item2['testrole2'], 'changed2')

    def test_set_property_badindex(self):
        """ Fail without app crash, but with a logger error message,
            if index given is out of range.
        """
        expected_error_msg = "Caught Exception: IndexError: list index out of range. " + \
                "Property='testrole', index=100, value=456."
        self.addroles_auto()
        self.adddata()
        self.testmodel.setProperty(100, 'testrole', 456)

        self.assertEqual(expected_error_msg, self.logging_queue.messages[0])

    def test_append_item(self):
        self.addroles()
        self.adddata()
        item = self.testmodel.get(0)
        self.assertEqual(item['testrole2'], 'testing two')
        self.assertEqual(self.testmodel.count, 2, 'Expected initial test data to have 2 items in it')
        testitem = {'testrole': 'testing app', 'testrole2': 'testing app two'}
        self.testmodel.appendItem(testitem)
        self.assertEqual(self.testmodel.count, 3, 'Expected append to grow count')
        item = self.testmodel.get(2)
        self.assertEqual(item['testrole2'], 'testing app two')

    def test_get(self):
        self.addroles_auto()
        self.adddata()
        self.assertEqual(self.testmodel.get(0), self.testing_data[0])
        self.assertEqual(self.testmodel.get(1), self.testing_data[1])

    def test_get_badindex(self):
        self.addroles_auto()
        self.adddata()
        self.assertEqual(self.testmodel.get(-1), QVariant())
        self.assertEqual(self.testmodel.get(100), QVariant())

    def test_rolenames(self):
        self.addroles()
        ordered = self.testmodel.ordered_rolenames
        test = ['testrole', 'testrole2', 'testrole3']
        self.assertEqual(ordered, test)

    def randword(self):
        return ''.join(random.choice('abcdefg') for _ in range(10))

    def test_add_delete_loop(self):
        self.addroles_auto();
        test_count = 100
        for i in range(0, test_count):
            fakename = self.randword()
            self.testmodel.appendItem({'testrole': fakename, 'testrole2': fakename})

        for i in range(0, test_count):
            self.testmodel.remove(i)

    def test_bad_index(self):
        # Fix bug for FIELD-410
        self.addroles_auto();
        test_count = 3
        for i in range(0, test_count):
            fakename = self.randword()
            self.testmodel.appendItem({'testrole': fakename, 'testrole2': fakename})

        for i in range(-3, test_count + 3):  # Bad Indices
            self.testmodel.remove(i)

    def test_is_item_in_model(self):
        self.addroles_auto()
        self.adddata()
        self.assertTrue(self.testmodel.is_item_in_model('testrole', 'testing one'))
        self.assertTrue(self.testmodel.is_item_in_model('testrole2', 'testing two'))
        self.assertTrue(self.testmodel.is_item_in_model('testrole', 'testing three'))
        self.assertTrue(self.testmodel.is_item_in_model('testrole2', 'testing four'))

    def test_get_item_index(self):
        self.addroles_auto()
        self.adddata()
        self.assertEqual(self.testmodel.get_item_index('testrole', 'testing three'), 1)
        self.assertEqual(self.testmodel.get_item_index('testrole2', 'testing two'), 0)

    def test_remove(self):
        self.addroles_auto()
        self.adddata()
        self.assertEqual(self.testmodel.get_item_index('testrole', 'testing three'), 1)
        self.assertEqual(self.testmodel.get_item_index('testrole2', 'testing two'), 0)
        orig_length = self.testmodel.count
        self.testmodel.remove(0)
        # Test we have one fewer item now
        self.assertEqual(self.testmodel.count, orig_length - 1)
        # Test that it shifted up
        self.assertEqual(self.testmodel.get_item_index('testrole', 'testing three'), 0)
        self.testmodel.remove(0)
        # Test we have two fewer items now
        self.assertEqual(self.testmodel.count, orig_length - 2)

    def test_get_role_number(self):
        self.addroles_auto()
        self.adddata()

        self.assertEqual(258, self.testmodel.get_role_number("testrole2"))

        # Decided: don't catch exception if get_role_number called with non-existent rolename.
        # Rolenames are entered by developers, not by observers, so this exception should not be caught.
        with self.assertRaises(ValueError):
            self.testmodel.get_role_number("NoSuchRoleName_xxxx")

if __name__ == '__main__':
    unittest.main()
