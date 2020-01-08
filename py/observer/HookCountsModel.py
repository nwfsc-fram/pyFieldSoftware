# -----------------------------------------------------------------------------
# Name:        HookCountsModel.py
# Purpose:     Model for Hook Counts (Fixed Gear)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Sept 11, 2019
# License:     MIT
# ------------------------------------------------------------------------------


from playhouse.shortcuts import model_to_dict
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import HookCounts
from PyQt5.QtCore import QVariant, pyqtSlot, pyqtProperty, pyqtSignal


class HookCountsModel(FramListModel):
    gearUnitsChanged = pyqtSignal(QVariant)
    avgHookCountChanged = pyqtSignal(QVariant)

    def __init__(self, parent=None):

        super().__init__(parent)
        for role_name in self.model_props:
            self.add_role_name(role_name)

        self._top_hc_record = None
        self._trip_id = None

    @property
    def model_props(self):
        props = FramUtil.get_model_props(HookCounts)
        # props.append('bio_specimen_id')
        # props.append('barcodes_str')
        # props.append('tags_str')
        # props.append('biosample_str')
        return props

    @pyqtSlot(int, name='initTripHookCounts')
    def init_trip_hook_counts(self, trip_id):
        """
        Only one row in HOOK_COUNTS for the TRIP_ID should have avg_hook_count and total_gear_units set.
        """
        try:
            self._trip_id = trip_id
            hookcounts_q = HookCounts.select().where(HookCounts.trip == trip_id)
            self._top_hc_record = None
            self.clear()
            if hookcounts_q.count():
                for h in hookcounts_q:
                    if h.avg_hook_count is not None:
                        self._top_hc_record = h
                        # self.gearUnitsChanged.emit(self._top_hc_record.total_gear_units)
                        # self.avgHookCountChanged.emit(self._top_hc_record.avg_hook_count)
                        self._logger.info(f'Loaded HC trip_id={self._top_hc_record.trip.trip}')

                    else:
                        new_data = model_to_dict(h, HookCountsModel)
                        self.insertItem(0, new_data)
            else:
                self._logger.info(f'Create top level HOOK_COUNTS for trip {trip_id}')
                self._top_hc_record = HookCounts.create(trip=trip_id)
                self._top_hc_record.avg_hook_count = 0  # Identify this as top hc record.
                self._top_hc_record.total_gear_units = 0
                self._top_hc_record.save()

            self.calc_avg()
            # self.modelChanged.emit()
            # return newidx

        except ValueError as e:
            self._logger.error('Error init hook counts {}'.format(e))
            return -1

    @pyqtProperty(QVariant, notify=gearUnitsChanged)
    def TotalGearUnits(self):
        return self._top_hc_record.total_gear_units if self._top_hc_record else None

    @TotalGearUnits.setter
    def TotalGearUnits(self, units):
        self._logger.info(f'Gear units now {units}')
        self._top_hc_record.total_gear_units = units
        self.calc_avg()
        self._top_hc_record.save()

    @pyqtProperty(int, notify=gearUnitsChanged)
    def RequiredHookCounts(self):
        if self._top_hc_record is not None:
            hc_val = self._top_hc_record.total_gear_units / 5.0 - self.get_current_hook_entry_count()
            return hc_val if hc_val > 0 else 0
        else:
            return 0

    @pyqtProperty(QVariant, notify=avgHookCountChanged)
    def AvgHookCount(self):
        val = self._top_hc_record.avg_hook_count if self._top_hc_record else None
        return val if val else 1.0

    @pyqtSlot(int, name='addHookCount')
    def add_hook_count(self, hook_count):
        newHC = HookCounts.create(trip=self._top_hc_record.trip,
                                  hook_count=hook_count)
        newHC.save()
        new_data = model_to_dict(newHC, HookCountsModel)
        self.insertItem(0, new_data)  # reverse order, new at top
        self.calc_avg()

    @pyqtSlot(name='deleteNewest')
    def delete_newest(self):
        if self.count > 0:
            delete_this_mdl = self.get(0)
            self._logger.info(f'Deleting {delete_this_mdl}')
            delete_this = HookCounts.get(HookCounts.hook_count_id == delete_this_mdl['hook_count_id'])
            delete_this.delete_instance()
            self.removeItem(0)
            self.calc_avg()

    def calc_avg(self):
        unitCount = 0
        sumHooks = 0
        hookcounts_q = self.get_hook_counts_query()
        for h in hookcounts_q:
            unitCount += 1
            sumHooks += h.hook_count
        self._logger.info(f'{unitCount} {sumHooks}')
        if unitCount > 0:
            self._top_hc_record.avg_hook_count = sumHooks / unitCount
        else:
            self._top_hc_record.avg_hook_count = 0.0
        avg = self._top_hc_record.avg_hook_count
        self._logger.debug(f'Emit avg HC now {avg}.')  # This is cascaded down to sets
        self.avgHookCountChanged.emit(avg)
        self.gearUnitsChanged.emit(self._top_hc_record.total_gear_units)

    def get_current_hook_entry_count(self):
        return self.get_hook_counts_query().count()

    def get_hook_counts_query(self):
        return HookCounts.select().where((HookCounts.trip == self._trip_id) &
                                         (HookCounts.avg_hook_count.is_null()))

