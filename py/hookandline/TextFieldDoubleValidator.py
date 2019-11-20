from PyQt5.QtGui import QDoubleValidator, QValidator
from PyQt5.QtQml import QQmlEngine
from PyQt5.QtCore import QObject
import logging
from sys import float_info


class TextFieldDoubleValidator(QDoubleValidator):

    def __init__(self, *args, bottom=float_info.min, top=float_info.max, decimals=float_info.dig,
                 parent=None, **kwargs):
        super().__init__(bottom=bottom, top=top, decimals=decimals, parent=parent)

        self.setNotation(QDoubleValidator.StandardNotation)
        # logging.info('bottom: {0}'.format(bottom))

        # QQmlEngine.setObjectOwnership(parent, QQmlEngine.CppOwnership)

    def validate(self, s, pos):
        """
        Overriding the validate method per:
        http://stackoverflow.com/questions/35178569/doublevalidator-is-not-checking-the-ranges-properly
        http://pyqt.sourceforge.net/Docs/PyQt4/qdoublevalidator.html#QDoubleValidator

        Samples of PyQt5 subclassing the QDoubleValidator
        http://codereview.stackexchange.com/questions/110304/pyqt5-validator-for-decimal-numbers-v2
        http://learnwithhelvin.blogspot.com/2010/01/qdoublevalidator.html

        qmlRegisterType - good reference:
        https://qmlbook.github.io/en/ch16/index.html
        http://nullege.com/codes/show/src%40p%40y%40pyqt5-HEAD%40examples%40qml%40referenceexamples%40binding.py/50/PyQt5.QtQml.qmlRegisterType/python

        :param s: input textfield string
        :param pos: position of the decimal in the textfield string
        :return:
        """

        # Allow empty field or minus sign
        if not s or s[:1] == "-":
            return QValidator.Intermediate

        # Check length of decimal places
        decimal_point = self.locale().decimalPoint()
        if decimal_point in s:
            decimal_length = len(s) - s.index(decimal_point) - 1
            if decimal_length > self.decimals():
                return QValidator.Invalid

        # Check range of value
        value, ok = self.locale().toDouble(s)
        if ok and self.bottom() <= value <= self.top():
            return QValidator.Acceptable

        return QValidator.Invalid
