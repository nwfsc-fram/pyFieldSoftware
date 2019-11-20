__author__ = 'Todd.Hay'

# -------------------------------------------------------------------------------
# Name:        WindowFrameSize
# Purpose:     Returns the true size of the application window to include the titlebar
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Dec 14, 2015
# License:     MIT
#-------------------------------------------------------------------------------
from PyQt5.QtCore import QObject, QVariant, QRect, pyqtProperty, pyqtSlot
from PyQt5.QtQuick import QQuickWindow
from PyQt5.QtWidgets import QApplication


class WindowFrameSize(QObject):
    def __init__(self, win=None, **kwargs):
        super().__init__()
        # QObject.__init__(self)
        # print("__init__")
        self.win = win

    @pyqtSlot(QQuickWindow)
    def set_window(self, win):
        # print("set_window method")
        # print("\twin:", win)

        if win:
            self.win = win
            # print('\twin set')

    # @pyqtSlot(result=QRect)
    @pyqtProperty(QRect)
    def frame_size(self):
        """
        Method to get the true size of the window, to include the titlebar
        :return:
        """
        if self.win:
            rect = self.win.frameGeometry()
            # print('\trect: ', rect, '\n\twidth: ', rect.width(), '\n\theight: ', rect.height())
            return rect
        return QRect()


