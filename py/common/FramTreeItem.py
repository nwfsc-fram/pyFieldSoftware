__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        FramTreeItem.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Jan 20, 2016
# License:     MIT
#-------------------------------------------------------------------------------
from PyQt5.QtQml import QJSValue, QJSValueIterator, QQmlListProperty
from PyQt5.QtCore import QAbstractListModel, QVariant, pyqtSlot, pyqtProperty, Qt, QModelIndex, \
    QObject, QPersistentModelIndex # pyqtWrapperType
from PyQt5.Qt import QQmlEngine

from operator import itemgetter
import logging
import unittest
import random
from collections import OrderedDict


class FramTreeItem(QObject):
    """
    Some important links that discuss returning custom objects (i.e. FramTreeItems in this case) from python
    back to QML.  Python should retain ownership of these objects.  Discussion can be found here:

    References
    - http://doc.qt.io/qt-5/qtqml-cppintegration-data.html#data-ownership
    - http://doc.qt.io/qt-5/qqmlengine.html#ObjectOwnership-enum
    - http://doc.qt.io/qt-5/objecttrees.html

    Calls for help on the Internet
    - https://riverbankcomputing.com/pipermail/pyqt/2014-July/034531.html
    - http://stackoverflow.com/questions/24558264/qml-not-taking-ownership-of-object-received-from-pyqt-slot/24696295#24696295

    """

    def __init__(self, data=[], headers=None, parent=None):
        super().__init__()

        self.itemData = data
        self.headers = headers
        self.parentItem = parent
        self.childItems = []
        # self.mixes = []

        self.is_expanded = False

        # self._index = QPersistentModelIndex()

    # @pyqtProperty(QPersistentModelIndex)
    # def index(self):
    #     """
    #     Returns the index
    #     :return:
    #     """
    #     return self._index
    #
    # @index.setter
    # def index(self, index):
    #
    #     if isinstance(index, QModelIndex):
    #         index = QPersistentModelIndex(index)
    #     if not isinstance(index, QPersistentModelIndex):
    #         return
    #
    #     self._index = index

    @pyqtProperty(bool)
    def isExpanded(self):
        """
        Defines whether the FramTreeItem is expanded or not
        :param state: bool - True/False
        :return:
        """
        return self.is_expanded

    @isExpanded.setter
    def isExpanded(self, state):
        self.is_expanded = state

    @pyqtSlot(QVariant, result=bool)    # FramTreeItem
    def appendChild(self, item):
        """
        Appending a child to the tree
        :param child:
        :return:
        """
        # if item is not None:
        if isinstance(item, FramTreeItem):
            self.childItems.append(item)
            return True

        return False

    @pyqtSlot(int, result=QVariant)   # result=FramTreeItem
    def child(self, row):
        """
        Get the child of the given row
        :param row:
        :return:
        """
        if row is not None and 0 <= row < len(self.childItems):
            QQmlEngine.setObjectOwnership(self.childItems[row], QQmlEngine.CppOwnership)
            return self.childItems[row]

        return None

    @pyqtSlot(result=int)
    def childCount(self):
        """
        Return the number of children of the TreeItem
        :return:
        """
        return len(self.childItems)

    @pyqtSlot(result=int)
    def columnCount(self):
        """
        Return the number of columns of data in the TreeItem
        :return:
        """
        if self.itemData:
            return len(self.itemData)
        else:
            return 0

    # @pyqtSlot(str, result=QVariant)
    @pyqtSlot(int, result=QVariant)
    def data(self, column):
        """
        Return data for a given column
        :param column: int - representing the column number within the data to return
        :return:
        """
        if isinstance(column, int):
            if column >= len(self.itemData) or column < 0:
                return QVariant()
            # elif isinstance(self.itemData[column], pyqtWrapperType):
                return QVariant()
            else:
                return QVariant(self.itemData[column])

        return QVariant()

    @pyqtProperty(QVariant)     # FramTreeItem
    def parent(self):
        """
        Return the parent of the item
        :return:
        """
        if self.parentItem is not None and isinstance(self.parentItem, FramTreeItem):
            QQmlEngine.setObjectOwnership(self.parentItem, QQmlEngine.CppOwnership)
            return self.parentItem

        return None

    @pyqtProperty(int)
    def row(self):
        """
        Return the item's location within its parent's list of items
        :return:
        """
        if self.parentItem is not None:
            if self in self.parentItem.childItems:
                return self.parentItem.childItems.index(self)
        return 0

    @pyqtSlot(int, int, int, result=bool)
    def insertChildren(self, position, count, columns, headers):
        """
        Insert children into the TreeItem
        :param position: int - position in the FramTreeModel for inserting the children
        :param count: int - number of children to insert
        :param columns: int - number of columns per children to insert
        :return:
        """
        if position < 0 or position > len(self.childItems):
            return False

        for row in range(0, count):
            data = [None] * columns
            newItem = FramTreeItem(data=data, parent=self, headers=headers)
            self.childItems.insert(position + row, newItem)

        return True

    @pyqtSlot(int, QVariant, result=bool)
    def setData(self, column, value):
        """
        Used to set the actual data
        :param column:
        :param value:
        :return:
        """
        if self.itemData is None:
            return False

        if column < 0 or column >= len(self.itemData):
            return False

        self.itemData[column] = value
        return True

    @pyqtSlot(int, int, result=bool)
    def removeChildren(self, position, count):
        """
        Remove children from the TreeItem
        :param position:
        :param count:
        :return:
        """
        if position < 0 or position >= len(self.childItems):
            return False

        for row in range(position+count-1, position-1, -1):
            del self.childItems[row]

        return True

    @pyqtSlot()
    def clear(self):
        """
        Remove all of the children
        :return: None
        """
        for row in range(self.childCount()-1, -1, -1):
            del self.childItems[row]

    @pyqtSlot(int, result=bool)
    def hasChild(self, row_number):
        """
        Determine if the parent has a child at this row_number
        :param row_number: int - row_number
        :return: bool - success - true/false
        """
        try:
            if isinstance(self.childItems[row_number], FramTreeItem):
                return True
        except IndexError as ex:
            logging.info('FramTreeItem.hasChild > IndexError exception')
        except Exception as ex:
            logging.info('FramTreeItem.hasChild > exception: ' + str(ex))
        return False

    @pyqtSlot(result=QVariant)
    def getAllDataAsDict(self):
        """
        Return all of the data
        :return:
        """
        return OrderedDict(zip(self.headers, self.itemData))

        # return self.itemData

    @pyqtProperty(QVariant)
    def children(self):
        """
        Return the children to the FramTreeItem
        :return:
        """
        return self.childItems

    # def __del__(self):
    #     """
    #     Destructor method
    #     :return:
    #     """
    #     # TODO Modify to recursively delete all of the children.  This will only do the first layer
    #     #  currently
    #     for row in range(len(self.childItems) - 1, -1, -1):
    #         del self.childItems[row]


    #
    # @pyqtSlot(int, int, result=bool)
    # def removeColumns(self, position, columns):
    #     """
    #
    #     :param position:
    #     :param columns:
    #     :return:
    #     """
    #     if position < 0 or position > len(self.itemData):
    #         return False
    #
    #     for column in range(0, columns):
    #         self.itemData.remove(position)
    #
    #     for child in self.childItems:
    #         child.removeColumns(position, columns)
    #
    #     return True
    #
    # @pyqtSlot(int, int, result=bool)
    # def insertColumns(self, position, columns):
    #     """
    #
    #     :param position:
    #     :param columns:
    #     :return:
    #     """
    #     if position < 0 or position > len(self.itemData):
    #         return False
    #
    #     for row in range(0, columns):
    #         self.itemData.insert(position, QVariant())
    #
    #     for child in self.childItems:
    #         child.insertColumns(position, columns)
    #
    #     return True
    #
    # # @pyqtProperty(QQmlListProperty)

    #
    # @pyqtProperty(int)
    # def childNumber(self):
    #     """
    #     Returns the index of the child in its parent's list of children
    #     :return:
    #     """
    #     if self.parentItem:
    #         return self.parentItem.children.index(self)
    #
    #     return 0


if __name__ == '__main__':
    FramTreeItem()
