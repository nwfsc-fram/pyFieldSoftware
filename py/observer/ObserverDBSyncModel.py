# -----------------------------------------------------------------------------
# Name:        ObserverDBSyncModel.py
# Purpose:     OPTECS DB Sync Information
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 10, 2016
# License:     MIT
#
# ------------------------------------------------------------------------------
from py.common.FramListModel import FramListModel


class ObserverDBSyncModel(FramListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        for role_name in self.model_props:
            self.add_role_name(role_name)

    @property
    def model_props(self):
        return ['trip_id', 'external_trip_id', 'sync_status', 'user_name', 'fishery']
