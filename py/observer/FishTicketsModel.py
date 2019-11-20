# -----------------------------------------------------------------------------
# Name:        FishTicketsModel.py
# Purpose:     Model for Fish Tickets
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     March 30, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import QVariant, pyqtSlot, pyqtProperty, pyqtSignal
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import FishTickets
from playhouse.shortcuts import model_to_dict


class FishTicketsModel(FramListModel):
    modelChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._internal_trip_id = 0  # Current TRIP_ID

        for role_name in self.ticket_rolenames:
            self.add_role_name(role_name)

    @property
    def ticket_rolenames(self):
        """
        :return: role names for FramListModel
        """
        rolenames = FramUtil.get_model_props(FishTickets)
        # Add additional roles (e.g. Vessel Name, to be acquired via FK)
        # rolenames.append('vessel_name')
        return rolenames

    @pyqtSlot(result=str)
    def add_ticket(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        :return: FramListModel index of new ticket (int)
        """
        try:
            newticket = self._get_ticketdict(db_model)
            newidx = self.appendItem(newticket)
            self._logger.info('Added ticket #{}'.format(newticket['fish_ticket_number']))
            self.modelChanged.emit()
            return newidx

        except ValueError as e:
            self._logger.error('Error adding new ticket: {}'.format(e))
            return -1

    @pyqtSlot(str)
    def del_ticket(self, ticket_num):
        """
        :param ticket_num: ticket # to delete
        """
        try:

            idx = self. get_item_index('fish_ticket_number', ticket_num)
            self.remove(idx)
            self.modelChanged.emit()

        except ValueError as e:
            self._logger.error('Error Deleting ticket: {}'.format(e))

    def _get_ticketdict(self, db_model):
        """
        Build a dict that matches FishTickets out of a peewee model
        Purpose is for storing peewee model <-> FramListModel
        :param db_model: peewee model to convert
        :return: dict with values translated as desired to be FramListModel friendly
        """
        ticketdict = model_to_dict(db_model)

        # Example for keys that we want to rename from model-> dict:
        # tripdict['renamed'] = tripdict.pop('rename_me')

        # Populate "extra" keys if needed
        # ticketdict['vessel_name'] = db_model.vessel.vessel_name
        return ticketdict
