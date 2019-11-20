__author__ = 'Will.Smith'
# -----------------------------------------------------------------------------
# Name:        ModelStore.py
# Purpose:     Store for models
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 22, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtProperty, QVariant, QObject, pyqtSignal, pyqtSlot
import logging

from py.observer.ObserverSpeciesModel import ObserverSpeciesModel
import unittest


class ModelStore(QObject):
    """
    Create or return handle to a model, indexed by name
    """

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._models = dict()  # of dict
        # Example: {'ANEM': {'recent': {...}, 'available': {...}}}
        self._key = 'default'  # This is appended to the model_name passed, used as a primary key (and is optional)

    def reset(self):
        """
        Clear model store
        """
        self._models = dict()

    @property
    def key(self):
        # primary key (optional)
        return self._key

    @key.setter
    def key(self, value):
        # This is appended to the model_name passed, used as a primary key (and is optional)
        self._key = value
        self._logger.debug('ModelStore key set to ' + self._key)

    def make_key(self, name):
        return str(name) + '_' + str(self._key)

    def _name_exists(self, model_name):
        return self.make_key(model_name) in self._models

    def _key_exists(self, key_name):
        return key_name in self._models

    def _check_name(self, model_name):
        if not model_name or len(model_name) == 0:
            raise Exception('Empty model_name passed')

    def has_model(self, model_name, label=None):
        keyname = self.make_key(model_name)
        if self._key_exists(keyname):
            if label is None or label in self._models[keyname].keys():
                return True
        return False

    def set_model(self, model, model_name, label='default'):
        """
        Catch category models, stored in a dict, indexed by PACFIN
        If doesn't exist, create a new one
        :param model: model to store
        :param model_name: name for model (e.g. pacfin code)
        :param label: optional label such as 'recent', 'available', 'selected'
        """
        try:
            keyname = self.make_key(model_name)
            self._check_name(model_name)
        except NameError as e:
            self._logger.warning(e)

        if self._name_exists(model_name):
            self._logger.debug('Set existing model pool: ' + keyname + ': ' + label)
            self._models[keyname][label] = model
        else:
            self._logger.debug('NEW model pool for ' + keyname + ': ' + label)
            self._models[keyname] = dict()
            self._models[keyname][label] = model

    def get_model(self, model_name, label='default'):
        """
        Models, stored in a dict
        :param model_name: name of model
        :param label: optional label such as 'recent'
        :return: Model, if doesn't exist, return None
        """
        try:
            keyname = self.make_key(model_name)
            self._check_name(model_name)
        except NameError as e:
            self._logger.warning(e)

        if self.has_model(model_name, label):
            self._logger.debug('Got existing model: ' + keyname + ', ' + label)
            return self._models[keyname][label]
        else:
            self._logger.error('Model of this name not set yet: ' + keyname + ', ' + label)
            return None


class TestModelStore(unittest.TestCase):

    names_to_test = ['ANEM', 'GBAS', 'LONGNAME', 'S']
    badnames_to_test = [None, '', 0]

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.ccsf = ModelStore()

    def test_model_creation(self):
        for name in self.names_to_test:
            model = ObserverSpeciesModel()
            newmodel = self.ccsf.get_model(name, 'available')
            self.assertIsNone(newmodel)
            self.ccsf.set_model(model, name, 'available')
            self.assertTrue(self.ccsf._name_exists(name))
            newmodel2 = self.ccsf.get_model(name, 'potato')
            self.assertIsNone(newmodel2)
            newmodel = self.ccsf.get_model(name, 'available')
            self.assertIsNotNone(newmodel)

            self.ccsf.set_model(model, name)
            newmodel3 = self.ccsf.get_model(name)
            self.assertEqual(model, newmodel3)

        for name in self.badnames_to_test:
            tst = None
            with self.assertRaises(Exception):
                tst = self.ccsf.get_model(name, 'asdf')
            self.assertIsNone(tst)

    def test_hasmodel(self):
        model = ObserverSpeciesModel()
        self.ccsf.set_model(model, '1234')
        self.assertTrue(self.ccsf.has_model('1234'))
        self.assertTrue(self.ccsf.has_model(1234))  # check string conversion

    def test_hasmodel_key(self):
        model = ObserverSpeciesModel()
        self.ccsf.key = 'test1'
        self.ccsf.set_model(model, '1234')
        self.assertTrue(self.ccsf.has_model('1234'))
        self.ccsf.key = 'test2'
        self.assertFalse(self.ccsf.has_model('1234'))
        self.ccsf.key = 'test1'
        self.assertTrue(self.ccsf.has_model('1234'))

    def test_reset(self):
        model = ObserverSpeciesModel()
        self.ccsf.set_model(model, '1234')
        self.assertTrue(self.ccsf.has_model('1234'))
        self.ccsf.reset()
        self.assertFalse(self.ccsf.has_model('1234'))
