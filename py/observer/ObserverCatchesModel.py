# -----------------------------------------------------------------------------
# Name:        ObserverCatchesModel.py
# Purpose:     Model for CATCHES table(Observer)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     July 5, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from py.common.FramListModel import FramListModel
from py.common.FramUtil import FramUtil
from py.observer.ObserverDBModels import BioSpecimens, Catches, SpeciesCompositions
from playhouse.shortcuts import model_to_dict

from py.observer.ObserverDBUtil import ObserverDBUtil


class CatchesModel(FramListModel):
    modelChanged = pyqtSignal()

    def __init__(self, parent=None, sort_role='catch', sort_reverse=True):
        super().__init__(parent)
        self._activity_id = None  # Current FISHING_ACTIVITY_ID
        self._sort_role = sort_role
        self._sort_reverse = sort_reverse

        for role_name in self.model_rolenames:
            self.add_role_name(role_name)

    @property
    def SM_IS_SPECIES_COMP(self):
        """Convention for catches.sampleMethod value when No Species Composition button is clicked."""
        return "YES"

    @property
    def SM_NO_SPECIES_COMP(self):
        """Convention for catches.sampleMethod value when No Species Composition button is clicked."""
        return "NSC"

    @property
    def SPECIES_NSC_DEFAULT(self):
        """
        Species that are NSC by default
        TODO: this list may be incomplete; setting halibut for FIELD-1317
        @return: tuple of species code strings
        """
        return 'PHLB', 'CHLB'

    @property
    def model_rolenames(self):
        """
        :return: role names for FramListModel
        """
        rolenames = FramUtil.get_model_props(Catches)
        # Add additional roles (e.g. Vessel Name, to be acquired via FK)
        rolenames.append('catch_category_code')  # look up by FK
        rolenames.append('catch_category_name')  # look up by FK
        rolenames.append('sample_method')  # look up by FK

        rolenames.append('catch_or_sample_weight')
        rolenames.append('catch_or_sample_count')

        return rolenames

    def add_catch(self, db_model):
        """
        :param db_model: peewee model object (cursor) created elsewhere
        :param activity_id: Fishing Activity ID (Primary key, not fishing_activity_num!)
        :return: FramListModel index of new ticket (int)
        """
        try:
            self._activity_id = db_model.fishing_activity.fishing_activity
            newcatch = self._get_modeldict(db_model)
            if newcatch['catch_weight_method'] == '15':
                # Load Ratio
                newcatch['density'] = ObserverDBUtil.get_current_catch_ratio_from_notes(newcatch['notes'])
            # add code and name (useful for UI)
            newcatch['catch_category_code'] = db_model.catch_category.catch_category_code
            newcatch['catch_category_name'] = db_model.catch_category.catch_category_name
            # Not used any more, but might be useful
            newcatch['catch_or_sample_weight'] = db_model.sample_weight if db_model.sample_weight else db_model.catch_weight
            newcatch['catch_or_sample_count'] = db_model.sample_count if db_model.sample_count else db_model.catch_count

            try:
                sm_q = SpeciesCompositions.get(SpeciesCompositions.catch == db_model.catch)
                newcatch['sample_method'] = sm_q.sample_method
            except SpeciesCompositions.DoesNotExist:
                # Catches with sample method of No Species Composition will come here.
                # If a biospecimen has been entered, set sample method to NSC.
                try:
                    bs_q = BioSpecimens.get(BioSpecimens.catch == db_model.catch)
                    newcatch['sample_method'] = self.SM_NO_SPECIES_COMP
                    self._logger.info("Setting SM to NSC because no SpecComp record and at least one BioSpecimens.")
                except BioSpecimens.DoesNotExist:
                    # TODO: This code duplicates ObserverCatches._glean_sample_method_from_context.
                    #   Any way to re-use that?

                    # It's possible to come here with an empty NSC CatchCategory - no biospecimens yet, or ever.
                    # Except for two last corner cases, there is insufficient data to distinguish
                    # from a newly added CatchCategory with no SM specified.
                    # Except for halibut, we get here also, so handle that case specifically
                    if newcatch['catch_category_code'] in self.SPECIES_NSC_DEFAULT:
                        newcatch['sample_method'] = self.SM_NO_SPECIES_COMP

                    if newcatch['catch_weight_method']:  # Corner cases only come into play if weight meth. specified.
                        # NSC Corner Case 1: if the specified weight method stores weight and count information
                        # at the catch level - and has done so without any spec comp records - then SM=NSC.
                        if newcatch['catch_weight_method'] in ['2', '6', '7', '9', '14', '19'] and \
                                newcatch['catch_weight'] or newcatch['catch_count']:
                            self._logger.debug("Setting SM to NSC because CC with WM with weight/count info in CC Details.")
                            newcatch['sample_method'] = self.SM_NO_SPECIES_COMP

                        # NSC Corner Case 2: If has no species comp or biospecimen records (already shown by being in this
                        # context), and if catch's weight method is WM7 (vessel est.) or WM14 (viz exp.), then SM=NSC.
                        elif newcatch['catch_weight_method'] in ['7', '14']:
                            newcatch['sample_method'] = self.SM_NO_SPECIES_COMP
                except Exception as e:
                    self._logger.error("Unexpected exception selecting BioSpecimens: {}".format(e))
                    newcatch['sample_method'] = ''

            newidx = self.appendItem(newcatch)
            self._logger.info('Added CatchModel #{} for haul #{} at model list index #{}'.format(
                    newcatch['catch'], self._activity_id, newidx))
            if self._sort_reverse:
                self.sort_reverse(self._sort_role)
            else:
                self.sort(self._sort_role)
            self.modelChanged.emit()
            return newidx

        except ValueError as e:
            self._logger.error('Error adding new trip: {}'.format(e))
            return -1

    def _get_modeldict(self, db_model):
        """
        Build a dict that matches FishTickets out of a peewee model
        Purpose is for storing peewee model <-> FramListModel
        :param db_model: peewee model to convert
        :return: dict with values translated as desired to be FramListModel friendly
        """
        modeldict = model_to_dict(db_model)

        # Example for keys that we want to rename from model-> dict:
        # tripdict['renamed'] = tripdict.pop('rename_me')

        # Populate "extra" keys if needed
        modeldict['sample_method'] = ''  # Note: this is set in add_catch
        return modeldict
