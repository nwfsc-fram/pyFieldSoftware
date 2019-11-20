__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        FramTreeModel.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 20, 2016
# License:     MIT
#-------------------------------------------------------------------------------
from PyQt5.QtQml import QJSValue, QJSValueIterator
from PyQt5.QtCore import QVariant, QModelIndex, pyqtSlot, pyqtProperty, Qt, \
                        QAbstractItemModel, QByteArray, QObject, QPersistentModelIndex
# pyqtWrapperType

from PyQt5.Qt import QQmlListProperty
from PyQt5.Qt import QQmlEngine

from operator import itemgetter
import logging
import unittest
import random
from py.common.FramTreeItem import FramTreeItem
from copy import deepcopy


class FramTreeModel(QAbstractItemModel):
    """
    Example models out on the Internet:
    PyQt - http://ftp.ics.uci.edu/pub/centos0/ics-custom-build/BUILD/PyQt-x11-gpl-4.7.2/examples/itemviews/editabletreemodel/editabletreemodel.py
    PyQt - https://github.com/klusta-team/klustaviewa/blob/master/klustaviewa/views/treemodel.py
    PyQt - http://rowinggolfer.blogspot.it/2010/05/qtreeview-and-qabractitemmodel-example.html
    C++ - http://doc.qt.io/qt-5/qtwidgets-itemviews-editabletreemodel-example.html
    C++ - roleNames method - http://stackoverflow.com/questions/21270969/using-a-qabstracttablemodel-with-a-qml-tableview-only-displays-the-1st-column

    """
    def __init__(self, headers=[], data=[], parent=None):
        super().__init__(parent)

        self.rootData = []
        # self.headers = {i: header for i, header in enumerate(headers)}
        self.headers = headers


        # for header in headers:
        #     self.rootData.append(header)
        self.rootData = deepcopy(self.headers)


        self._ordered_rolenames = []
        self._roles = self.createRoles()        # depends on self.headers

        self._rootItem = FramTreeItem(data=self.rootData, parent=None, headers=self._ordered_rolenames)

        self._descendantSpecies = []   # List of all of the descendants of the tvSelectedSpecies._rootItem

        self._mixCount = {}     # Keeps track of the Mix / Submix numbers

    @pyqtProperty(QVariant)
    def mixCount(self):
        """
        Method to return the self._mixCount dictionary that contains a listing of all of the mixes and submixes
        :return: 
        """
        return self._mixCount

    @pyqtSlot(str, QModelIndex, result=int)
    def addMixCount(self, mixType, parentIndex=None):
        """
        Add a mix to the mixCount
        :param mixType - str - either Mix or Submix representing the type of mix to append
        :param parentIndex - QModelIndex - the parent to which the mix is being attached
        :return: int - number for the new mix
        """
        if mixType is None:
            return

        if mixType == "Mix":
            if self._mixCount:
                maxKey = int(max(self._mixCount.keys(), key=int))
            else:
                maxKey = 0

            self._mixCount[maxKey+1] = []

            return maxKey+1

        elif mixType == "Submix":
            parentItem = self.getItem(parentIndex)
            col = self.getColumnNumber("displayName")
            displayName = parentItem.data(col).value()
            mixKey = int(displayName.replace("Mix #", ""))

            if mixKey in self._mixCount and self._mixCount[mixKey]:
                maxSubKey = max(self._mixCount[mixKey])
            else:
                maxSubKey = 0

            if mixKey in self._mixCount:
                self._mixCount[mixKey].append(maxSubKey+1)
            return maxSubKey+1

    @pyqtSlot(str, str, QModelIndex)
    def subtractMixCount(self, mixType, name, parentIndex):
        """
        Remove a mix from the self._mixCount
        :param mixType - str - if a Mix or Submix
        :param name - str - Name of the mix to remove
        :param parentIndex - QModelIndex - parent from which to reduce the mix count
        :return:
        """
        if mixType is None:
            return

        if not isinstance(parentIndex, QModelIndex):
            return

        try:
            nameCol = self.getColumnNumber("displayName")
            nameRole = self.getRoleNumber("displayName")
            typeCol = self.getColumnNumber("type")
            mixes = [[int(x.data(nameCol).value().replace("Mix #", "")), x] for x in self.rootItem.children if x.data(typeCol).value() == "Mix"]

            if mixType == "Mix":
                key = int(name.replace("Mix #", ""))

                # Remove the key
                if key in self._mixCount:
                    self._mixCount.pop(key)

                    # Relabel higher numbered mixes, one less, first get all of the higher numbered keys
                    keys = [x for x in self._mixCount if x > key]

                    finalKey = -1
                    for k in keys:

                        # Fix the dictionary, i.e. drop the key values down one key
                        self._mixCount[k-1] = self._mixCount[k]

                        # Next relabel the FramTreeItem mix items to one less, i.e. Mix #3 becomes Mix #2 if we deleted Mix #2
                        mix = [x[1] for x in mixes if x[0] == k]
                        if mix and len(mix) == 1:
                            assert isinstance(self, FramTreeModel), "Not a FramTreeModel"
                            idx = self.createIndex(mix[0].row, nameCol, mix[0])
                            assert(isinstance(idx, QModelIndex))
                            # status = self.setData(idx, "Mix #" + str(k-1), nameRole)

                        finalKey = k

                    # Finally remove the last key as it is now obsolete as it now has a key = finalKey - 1
                    if finalKey in self._mixCount:
                        self._mixCount.pop(finalKey, None)

            elif mixType == "Submix":
                key = int(name.replace("Submix #", ""))
                parentItem = self.getItem(parentIndex)
                parentKey = int(parentItem.data(nameCol).value().replace("Mix #", ""))
                submixes = [[int(x.data(nameCol).value().replace("Submix #", "")), x]
                            for x in parentItem.children if x.data(typeCol).value() == "Submix"]
                if parentKey in self._mixCount:

                    if key in self._mixCount[parentKey]:

                        # Get a list of the remaining keys that we need to adjust
                        keys = [x for x in self._mixCount[parentKey] if x >= key]

                        finalValue = -1
                        for k in keys:

                            # Fix the dictionary list, drop the list values down one
                            self._mixCount[parentKey][k-2] = k-1

                            # Next relabel the FramTreeItem submix items to one less, i.e. Submix #3 becomes Submix #2 if we deleted Submix #2
                            submix = [x[1] for x in submixes if x[0] == k]
                            if submix and len(submix) == 1:
                                idx = self.createIndex(submix[0].row, nameCol, submix[0])
                                # status = self.setData(idx, "Submix #" + str(k-1), nameRole)

                            finalValue = k

                        # Finally remove the last list element as it is now obsolete
                        if finalValue in self._mixCount[parentKey]:
                            self._mixCount[parentKey].remove(finalValue)

        except Exception as ex:
            logging.info('subtractMixCount Exception: ' + str(ex))

    @pyqtProperty(QVariant)
    def descendants(self):
        """
        Return a list of all of the descendants of the self._rootItem
        :return: list - of all of the descendants
        """
        return self._descendantSpecies

    @pyqtSlot(QVariant)
    def append_descendant(self, taxonId):
        """
        Add a new descendant to the self._allDescendants list
        :param taxonId - int - representing the taxonId of the child
        :return:
        """
        if isinstance(taxonId, QVariant):
            taxonId = taxonId.value()

        if taxonId is None:
            return

        self._descendantSpecies.append(taxonId)

    @pyqtSlot(QModelIndex)
    def remove_descendant(self, index):
        """
        Remove the given child from the self._allDescendants list
        :param taxonId - int - taxonId to remove
        :return:
        """
        if not isinstance(index, QModelIndex):
            return

        item = self.getItem(index)
        typeCol = self.getColumnNumber("type")
        taxonCol = self.getColumnNumber("taxonomyId")
        type = item.data(typeCol).value()
        taxonId = item.data(taxonCol).value()

        if type == "Taxon":
            if taxonId:
                for descendant in self._descendantSpecies:
                    if taxonId == descendant:
                        self._descendantSpecies.remove(taxonId)
                        break

        elif type == "Mix" or type == "Submix":
            for child in item.children:
                newIndex = self.createIndex(child.row, 0, child)
                self.remove_descendant(newIndex)

    @pyqtProperty(QVariant)
    def rootItem(self):
        QQmlEngine.setObjectOwnership(self._rootItem, QQmlEngine.CppOwnership)
        return self._rootItem

    @pyqtSlot(QModelIndex, result=int)
    def columnCount(self, parent=None):
        """

        :param parent: QModelIndex - parent from which to find the columnCount
        :return: int - number of columns for the given parent
        """
        if parent and parent.isValid():
            if parent.internalPointer():
                return parent.internalPointer().columnCount()
            else:
                return self._rootItem.columnCount()
        else:
            return len(self.headers)

    def get_index_recursively(self, item, col_num, value):
        """
        Recursive method to all of the items children's role for the given value
        :param item: FramTreeItem - the parent item to search
        :param col_num: int - column number to search
        :param value: QVariant - value of the role to search
        :return:
        """
        index = QModelIndex()

        if item.data(column=col_num).value() == value:
            index = self.createIndex(item.row, col_num, item)
            return index

        for child_item in item.children:
            result = self.get_index_recursively(item=child_item, col_num=col_num, value=value)
            if result != QModelIndex():
                index = result
                break

        return index

        # if item.childCount() == 0:
        #     logging.info('displayName: {0}, item: {1}, value: {2}'
        #                  .format(item.data(column=displayName).value(), item.data(column=col_num).value(), value))
        #     if item.data(column=col_num).value() == value:
        #         index = self.createIndex(item.row, col_num, item)
        # else:
        #     for child_item in item.children:
        #         result = self.get_index_recursively(item=child_item, col_num=col_num, value=value)
        #         if result != QModelIndex():
        #             index = result
        #             break
        #
        # return index

    @pyqtSlot(str, QVariant, result=QModelIndex)
    def get_index_by_role_value(self, role, value):
        """
        Method to find the QModelIndex corresponding to the role with the specified value
        :param role: str - representing the role in the FramTreeModel
        :param value: QVariant - value of the role to search for
        :return: QModelIndex - return the index of the newly found role + value
        """
        col_num = self.getColumnNumber(role)
        if isinstance(value, QJSValue):
            value = value.toVariant()
        return self.get_index_recursively(self._rootItem, col_num=col_num, value=value)

    @pyqtSlot(str, QVariant, result=QModelIndex)
    def get_row_index_by_role_value(self, role, value):
        item_idx = self.get_index_by_role_value(role=role, value=value)
        logging.info("item_idx: {0}".format(item_idx))

        idx = self.createIndex(item_idx.row(), 0, item_idx.parent())

        return idx;

    @pyqtSlot(QModelIndex, int, result=QVariant)
    def data(self, index, role):
        """

        :param index: QModelIndex - index from which to retrieve the data
        :param role: int - custom role for the data to retrieve
        :return: QVariant - data itself
        """

        if not index.isValid():
            return QVariant()

        # if index.column() < 0 or self.columnCount() < index.column() or \
        #     index.row() < 0 or self.rowCount() < index.row():
        #     return QVariant()

        item = self.getItem(index)

        try:
            if role in self._roles:
                role = self._roles[role].decode('utf-8')

                column = self.rootData.index(role)
                value = item.data(column)

                return QVariant(value)

        except ValueError as ex:

            return QVariant()

        return QVariant()

        # from FramListModel
        # return self._data_items[index.row()][self._roles[role].decode("utf-8")]

    @pyqtSlot(int, QVariant, int, result=QVariant)
    def headerData(self, column, orientation, role):
        """

        """
        # logging.info('Qt.DisplayRole: ' + str(Qt.DisplayRole))
        # if orientation == Qt.Horizontal and role == Qt.DisplayRole:
        if orientation == Qt.Horizontal and role in self._roles:
            try:
                return QVariant(self.headers[column])
            # return self._rootItem.itemData(column)
            except IndexError:
                pass

        return QVariant()

    @pyqtSlot(int, int, QModelIndex, result=QModelIndex)
    def index(self, row, column, parent):
        """

        :param row:
        :param column:
        :param parent:
        :return:
        """

        # if parent is None:
        #     return QModelIndex()
        #
        # if parent == self._rootItem:
        #     return QModelIndex()
        #
        # if not isinstance(parent, QModelIndex):
        #     return QModelIndex()
        #
        # if not self.hasIndex(row, column, parent):
        #     return QModelIndex()

        if parent.isValid() and parent.column() != 0:
            return QModelIndex()

        if parent.isValid():
            parentItem = parent.internalPointer()
            if not parentItem:
                parentItem = self._rootItem
        else:
            parentItem = self._rootItem

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    @pyqtSlot(QModelIndex, result=QModelIndex)
    def parent(self, index):
        """

        :param index:
        :return:
        """
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        if not childItem:
            return QModelIndex()

        parentItem = childItem.parent
        if parentItem is None or parentItem == self._rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row, 0, parentItem)

    @pyqtSlot(QModelIndex, result=QVariant)
    def getItem(self, index):

        if index.isValid():
            item = index.internalPointer()
            if item:
                QQmlEngine.setObjectOwnership(item, QQmlEngine.CppOwnership)
                return item

        QQmlEngine.setObjectOwnership(self._rootItem, QQmlEngine.CppOwnership)
        return self._rootItem

    @pyqtSlot(QModelIndex, result=int)
    def rowCount(self, parent=QModelIndex()):
        """
        Method to return the number of rows / children for the given parent
        :param parent: QModelIndex - representing the index to the parentItem to count the rows
        :return: int - number of rows for the given parent
        """
        parentItem = self.getItem(parent)
        return parentItem.childCount()

    @pyqtSlot(str, result=int)
    def getColumnNumber(self, role):

        try:

            return self.rootData.index(role)

        except ValueError as ex:

            return -1

    @pyqtSlot(QModelIndex, QVariant, int, result=bool)
    def setData(self, index, value, role):
        """

        :rtype: object
        :param index: QModelIndex - index of the FramTreeItem for setting data
        :param value: QVariant - new data to set
        :param role: int - int representing the role of data to set
        :return: success - bool - true/false if the data update was successful or not
        """
        if not index.isValid():
            return False

        item = self.getItem(index)
        result = item.setData(index.column(), value)
        if result:

            # self.dataChanged.emit(index, index, [])
            self.dataChanged.emit(index, index, [role])

        return result

    @pyqtSlot(int, int, QModelIndex, result=bool)
    def insertRows(self, position, count, parent):
        """

        :param position: int - position of where to start inserting the rows
        :param count: int - number of rows to insert
        :param parent: QModelIndex - parent object index for inserting the rows
        :return: true/false if successful or not
        """
        parentItem = self.getItem(parent)

        self.beginInsertRows(parent, position, position + count - 1)
        # self.beginInsertRows(QModelIndex(), position, position + count - 1)
        success = parentItem.insertChildren(position, count, self.columnCount(parent), self._ordered_rolenames)
        self.endInsertRows()

        return success

    @pyqtSlot(int, int, QModelIndex, result=bool)
    def removeRows(self, position, count, parent):
        """

        :param position:  int - position of where to start deleting the rows
        :param count: int - number of rows to delete
        :param parent: QModelIndex - parent FramTreeItem from which to delete children
        :return: bool - true/false indicating if the removal was successful or not
        """
        if position is None or count is None or parent is None:
            return False

        parentItem = self.getItem(parent)

        self.beginRemoveRows(parent, position, position + count - 1)
        success = parentItem.removeChildren(position, count)
        self.endRemoveRows()

        return success

    @pyqtSlot(list, QModelIndex)
    def setChildItems(self, items, parent):
        """
        Set all of the items at once
        :param items: list - of FramTreeItems to add as children
        :param parent: QModelIndex - of the parent to which to add the children
        :return:
        """
        parentItem = self.getItem(parent)

        self.removeRows(0, parentItem.childCount()-1, parent)

        self.beginInsertRows(parent, 0, len(items)-1)
        parentItem.childItems = items
        self.endInsertRows()

        # logging.info('setChildItems: {0}'.format(parentItem.childCount()))

    @pyqtSlot()
    def clear(self):
        """
        Method to clear the FramTreeModel of all children
        :return:
        """
        parent = QModelIndex()
        parentItem = self.rootItem
        self.beginRemoveRows(parent, 0, parentItem.childCount()-1)
        parentItem.clear()
        self.endRemoveRows()

        # Clear the list of all of the type = Taxon descendants as well.  This list is used for checking
        # when trying to add a new species to see if that species already exists in the tree
        del self._descendantSpecies[:]

        # Empty the _mixCount which keeps track of our mix/submix numbering.  Need to clear this out and
        # then rebuild it from the data in the database otherwise will get out of sync in the numbering
        self._mixCount.clear()

    @pyqtSlot(QModelIndex, result=Qt.ItemFlags)
    def flags(self, index):
        """

        :param index:
        :return:
        """
        if not isinstance(index, QModelIndex):
            return 0

        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

        # return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren
        # return Qt.ItemIsEditable | QAbstractItemModel.flags(index)

    def createRoles(self):
        """
        Method to set and return the roleNames
        :return:
        """
        # roles = QAbstractItemModel.roleNames(self)
        roles = {}
        for i, header in enumerate(self.headers):
            # roles[Qt.UserRole + i + 1] = QByteArray(header.encode('utf-8'))
            roles[Qt.UserRole + i + 1] = header.encode('utf-8')
            self._ordered_rolenames.append(header)

        # for i in range(0, len(self.headers)):
        #     roles[Qt.UserRole + i] = QByteArray(self.headers[i].encode('utf-8'))
        return roles

    @pyqtSlot(result=QVariant)
    def roleNames(self):
        """
        Method to set and return the roleNames.  Needed to override this as a pyqtSlot
        to get it to work.  N.B. MUST HAVE THIS METHOD TO GET DATA TO UPDATE as noted here:

        First link is the best, then second, and finally third has some insight as well

        http://stackoverflow.com/questions/25700014/cant-display-data-from-qsqlquerymodel-in-a-qml-tableview
        http://stackoverflow.com/questions/21270969/using-a-qabstracttablemodel-with-a-qml-tableview-only-displays-the-1st-column
        http://stackoverflow.com/questions/34683783/modeldata-is-not-defined-for-qml-combobox-with-more-than-one-role-in-qabstractli

        :return:
        """
        # return QQmlListProperty(self, self._roles)
        return self._roles

    @pyqtSlot(str, result=int)
    def getRoleNumber(self, role_name):
        """
        Method to return the role number given the role_name
        :param role_name: str - role_name
        :return:
        """
        # qba = QByteArray(role_name.encode('utf-8'))
        # return list(self._roles.keys())[list(self._roles.values()).index(qba)]
        role = role_name.encode('utf-8')
        return list(self._roles.keys())[list(self._roles.values()).index(role)]

    @pyqtSlot(int, result=str)
    def getRoleName(self, role_number):
        """

        :param role_number:
        :return:
        """
        return self._roles[role_number].decode('utf-8')
        # return self._roles[role_number].data().decode('utf-8')


class TestFramTreeModel(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

        headers = ["uid", "scientific name", "type"]
        data = "1\tSebastes aurora\tfish\n2\tSebastes pinniger\tfish\n3\tbangal\tinvert."
        parent = None
        self.testmodel = FramTreeModel(headers=headers, data=data, parent=parent)

    def test_adddata(self):
        pass

    def test_showdata(self):
        for child in self.testmodel._rootItem.children:
            logging.info(child._m_itemData)

        logging.info('self.rootItem childrenCount: ' + str(self.testmodel._rootItem.childCount))


if __name__ == '__main__':
    unittest.main()
