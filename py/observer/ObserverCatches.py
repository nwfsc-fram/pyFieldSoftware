# -----------------------------------------------------------------------------
# Name:        ObserverCatches.py
# Purpose:     Catches object, exposed to QML, contains CatchesModel, and contains SpeciesModel
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     July 5, 2016
# License:     MIT
# ------------------------------------------------------------------------------

import unittest
import logging
import re

from PyQt5.QtCore import pyqtProperty, QObject, QVariant, pyqtSignal, pyqtSlot, QStringListModel
from peewee import fn, IntegrityError

from playhouse.apsw_ext import APSWDatabase
from playhouse.test_utils import test_database

# http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#model_to_dict
# For converting peewee models to dict, and then to QVariant for QML, and all the way back again
from playhouse.shortcuts import model_to_dict, dict_to_model

from py.observer.Biospecimens import Biospecimens
from py.observer.CatchCategory import CatchCategory

from py.observer.ObserverDBModels import BioSpecimens, Catches, CatchCategories, FishingActivities, \
    Species, SpeciesCatchCategories, SpeciesCompositions

from py.observer.ObserverCatchBaskets import ObserverCatchBaskets
from py.observer.ObserverCatchesModel import CatchesModel
from py.observer.ObserverDBUtil import ObserverDBUtil
from py.observer.ObserverLookups import WeightMethodDescs, CatchVals, SampleMethodDescs, RockfishHandlingDescs
from py.observer.ObserverSpecies import ObserverSpecies


class ObserverCatches(QObject):
    catchIdChanged = pyqtSignal(name='catchIdChanged')
    sampleMethodChanged = pyqtSignal(QVariant, name='sampleMethodChanged', arguments=['sample_method'])
    smDescChanged = pyqtSignal(str, name='smDescChanged')
    speciesCompChanged = pyqtSignal(name='speciesCompChanged')
    biosChanged = pyqtSignal(name='biosChanged')
    weightMethodChanged = pyqtSignal(name='weightMethodChanged')
    catchRatioChanged = pyqtSignal(float, name='catchRatioChanged', arguments=['ratio'])
    discardReasonChanged = pyqtSignal(name='discardReasonChanged')
    dispositionChanged = pyqtSignal(name='dispositionChanged')
    handlingMethodChanged = pyqtSignal(QVariant, name='handlingMethodChanged')
    unusedSignal = pyqtSignal(name='unusedSignal')  # Make QML warning go away
    otcFGWeightChanged = pyqtSignal(QVariant, QVariant, name='otcFGWeightChanged', arguments=['otc_fg', 'fishing_activity_num'])

    PACIFIC_HALIBUT_CATCH_CATEGORY_CODE = 'PHLB'
    CATCH_DISCARD_REASON_UNKNOWN = '?'

    def __init__(self, db):
        super().__init__()
        self._logger = logging.getLogger(__name__)

        # Sort catches by order in which entered (primary key value), most recent first
        self._catch_model = CatchesModel(sort_role='catch', sort_reverse=True)
        self._current_catch_model_idx = None  # index in framlistmodel

        self._current_catch = None
        self._current_activity = None

        # Species uses some values in ObserverCatches (e.g. weight method); pass self as parm.
        self._species = ObserverSpecies(self)

        self._biospecimens = Biospecimens(self, db)  # Biospecimens uses some values in ObserverCatches; pass as parm.

        self._is_species_comp = None
        self._is_fixed_gear = None
        self._wm_descs = {}
        self._rockfish_release_methods = RockfishHandlingDescs()
        self._rockfish_release_list = QStringListModel()
        self._rockfish_release_list.setStringList(self._rockfish_release_methods.release_method_codes)
        self.load_weight_methods()
        self._current_handling_method = None
        self._species.totalCatchCountChanged.connect(self._handle_species_total_count_changed)
        self._species.totalCatchWeightChanged.connect(self._handle_species_total_weight_changed)

        self._species.totalCatchCountFGChanged.connect(self._handle_fg_total_count_changed)
        self._species.totalCatchWeightFGChanged.connect(self._handle_fg_total_weight_changed)
        self._biospecimens.totalPHLBWeightChanged.connect(self._handle_fg_PHLB_weight_changed)

        # ObserverCatchBaskets (instance that handles Weight Method 3 catch weight calculation)
        # uses some values in ObserverCatches (e.g. weight method); pass self as parm.
        # TODO: Consider dropping self as parm in favor of signals.
        self._observer_catch_baskets = ObserverCatchBaskets(self)

    @pyqtProperty(QVariant, notify=speciesCompChanged)
    def species(self):
        return self._species

    @pyqtProperty(QVariant, notify=biosChanged)
    def biospecimens(self):
        return self._biospecimens

    @pyqtProperty(QVariant, notify=unusedSignal)
    def catchBaskets(self):
        return self._observer_catch_baskets

    def load_weight_methods(self):
        self._is_fixed_gear = ObserverDBUtil.is_fixed_gear()
        self._wm_descs = WeightMethodDescs().wm_fg_descriptions if self._is_fixed_gear \
            else WeightMethodDescs().wm_trawl_descriptions

    @pyqtSlot(str, result=QVariant, name='load_catches')
    def load_catches(self, fishing_activity_id):
        """
        Load catches from database
        :return: list of catch codes (strings)
        """
        self.load_weight_methods()

        catches_query = Catches.select().where(Catches.fishing_activity == fishing_activity_id)
        ncatches = catches_query.count()
        catch_codes = list()
        self._catch_model.clear()
        if ncatches > 0:
            for c in catches_query:
                self._current_catch_model_idx = self._catch_model.add_catch(c)
                catch_codes.append(c.catch_category.catch_category_code)  # Look up FK

        return catch_codes

    @pyqtSlot(str, result=QVariant, name='deleteCatch')
    def deleteCatch(self, catch_id):
        """
        Delete any SpeciesCompositions records for this catch category
        (Checking for "empty" catch category is performed prior to calling this function)

        @param catch_id: CATCH_ID in CATCHES
        """
        try:
            doomed_catch = Catches.get(Catches.catch == catch_id)
            doomed_catch.delete_instance(recursive=True)
            self._logger.info('Deleted catch_id {}'.format(catch_id))

            # Delete any SpeciesCompositions records for this catch, non-recursively (see comment above).
            orphan_spec_comps = SpeciesCompositions.select().where(SpeciesCompositions.catch == catch_id)
            if orphan_spec_comps.count() == 0:
                self._logger.info("No SpeciesCompositions records for this deleted catch.")
            else:
                for spec_comp in orphan_spec_comps:
                    spec_comp.delete_instance(recursive=True)
                    self._logger.info("Deleted SpeciesCompositions record ID={}, SM={}.".format(
                        spec_comp.species_composition, spec_comp.sample_method))
        except Catches.DoesNotExist:
            self._logger.warning('Could not find catch with ID (for deletion) {}'.format(catch_id))

    def add_catch(self, catch):
        """
        Adds peewee model catch to the FramListModel and sets properties
        :param catch: peewee model cursor
        """
        self._current_catch_model_idx = self._catch_model.add_catch(catch)
        return self._current_catch_model_idx

    @staticmethod
    def get_next_catch_num_for_this_haul(fishing_activity_pk, logger):
        """
        Catch_num is used by At-Center Observer for ordering the display of catches.
        Goal: display catches in order in which they were created.
        Assign from 1. Re-use a catch number for a deleted catch, but only if it were the last entered.
        I.e., it's OK to have gaps in catch_num due to deleted catches.

        :param fishing_activity_pk: Primary key for haul
        :param logger
        :return: The highest catch num used so far, plus one.
        """
        catch_query = Catches.select().where(Catches.fishing_activity == fishing_activity_pk)

        last_catch_num = 0
        for catch in catch_query:  # Not performant, but number of catches per haul is small.
            if catch.catch_num > last_catch_num:
                last_catch_num = catch.catch_num
        next_available_catch_num = last_catch_num + 1
        first_catch_msg = " (First catch of this haul)" if catch_query.count() == 0 else ""
        logger.info(f"Returning next catch number = {next_available_catch_num}{first_catch_msg}.")
        return next_available_catch_num

    @pyqtProperty(QStringListModel, notify=unusedSignal)
    def RockfishHandlingMethods(self):
        # Note: with this model, for text, don't use modelData, use display
        return self._rockfish_release_list  # 'TO', 'MV' etc

    @pyqtSlot(QVariant, result=QVariant)
    def getHandlingMethodDesc(self, desc):
        if desc:
            return self._rockfish_release_methods.release_methods_desc.get(desc, 'Not Found')

    def create_catch(self, catch_category_id, fishing_activity_pk, disposition=CatchVals.DispDiscarded):
        """
        Create a new trip in the DB
        @param catch_category_id: pk for catch category
        @param fishing_activity_pk: FISHING_ACTIVITY_ID
        @param disposition: 'D' or 'R'
        @return: new trip FramListModel
        """
        try:
            if self._is_fixed_gear:
                disposition = self.CATCH_DISCARD_REASON_UNKNOWN
            created_by = ObserverDBUtil.get_current_user_id()
            created_date = ObserverDBUtil.get_arrow_datestr()
            catch_num = ObserverCatches.get_next_catch_num_for_this_haul(fishing_activity_pk, self._logger)
            newcatch = Catches.create(catch_category=catch_category_id,
                                      catch_num=catch_num,
                                      fishing_activity=fishing_activity_pk,
                                      catch_weight_um=CatchVals.WeightUM,
                                      catch_disposition=disposition,
                                      created_by=created_by,
                                      created_date=created_date)

            self._logger.info('Created catch {}->{} '
                              'for fishing activity {} (Catch# {})'.format(newcatch.catch,
                                                                           newcatch.catch_category.catch_category_name,
                                                                           fishing_activity_pk, catch_num))
            self._current_catch_model_idx = self.add_catch(newcatch)
            self._current_catch = newcatch

            self.catchIdChanged.emit()  # New catch ID has been created
            return self._current_catch_model_idx
        except Exception as e:
            self._logger.error(e)
            return None

    @pyqtProperty(QVariant, notify=catchIdChanged)
    def CatchesModel(self):
        """
        Generally we will only have one Catch instance per haul/ set
        @return:
        """
        return self._catch_model

    @property
    def current_catch_db_id(self):
        return self._current_catch.catch if self._current_catch else None

    @pyqtProperty(bool, notify=catchIdChanged)
    def isPHLB(self) -> bool:
        return self._current_catch.catch_category.catch_category_code == self.PACIFIC_HALIBUT_CATCH_CATEGORY_CODE \
            if self._current_catch else False

    @pyqtProperty(bool, notify=catchIdChanged)
    def isSingleSpecies(self) -> bool:
        return self.get_catch_category_species_count(
            self._current_catch.catch_category.catch_category) == 1 if self._current_catch else False

    @staticmethod
    def get_catch_category_species_count(catch_category_id: id) -> int:
        """
        Given a catch category code, find out how many species are associated with it.
        Used to auto-determine Purity (Pure = 1, Mixed = Multi)
        Used for FIELD-1286 (Determine purity for Vessel retained in Logbook Mode)
        @param catch_category_id: e.g. 101
        @return: count of species in this catch category
        """

        found_species_count = 0
        try:
            # catch_category_id = CatchCategories. \
            #     select().where(catch_category_code == CatchCategories.catch_category_code)
            # if catch_category_id:
            related_species = SpeciesCatchCategories.select().where(
                SpeciesCatchCategories.catch_category == catch_category_id)
            found_species_count = len(related_species)
            logging.debug(f'Species count for {catch_category_id} catch cat: {found_species_count}')
            return found_species_count
        except Exception as e:
            logging.warning(f'Error looking up catch category {catch_category_id}, {e}')
            return found_species_count

    @pyqtProperty(QVariant)
    def currentMatchingSpeciesId(self):
        """
        For the current catch category, is there a species that is associated with the current category,
        either by:
        1. Having an entry in the SPECIES_CATCH_CATEGORIES table or
        2. A shared category code (PacFIN code) or
        3. A shared case-insensitive common name.

        Multiple match are OK; the match returned by peewee get() is used.

        :return: the species ID if a match is found, or None if not.
        """
        catchcat_common_name = self._current_catch.catch_category.catch_category_name
        catchcat_id = self._current_catch.catch_category.catch_category
        pacfin_code = self._current_catch.catch_category.catch_category_code

        try:
            matching_species = SpeciesCatchCategories.get(
                SpeciesCatchCategories.catch_category == catchcat_id)
            self._logger.info(f'Catch Category ID={catchcat_id} Code={pacfin_code} ' +
                              f'matched to SpeciesID={matching_species.species.species} ' +
                              f'in SPECIES_CATCH_CATEGORIES table.')
            return matching_species.species
        except SpeciesCatchCategories.DoesNotExist:
            self._logger.debug(f"No entry in SpeciesCatchCategoriesTable")

        try:
            if catchcat_common_name is None:
                self._logger.error('Species Common Name is None')
                return None

            matching_species = Species.get((fn.Lower(Species.common_name) == catchcat_common_name.lower()) |
                                           (Species.pacfin_code == pacfin_code))
            fmt_str = 'Catch Category (Code={} Name={}) matched to Species(ID={}, Code={}, Name={})'
            self._logger.info(fmt_str.format(
                pacfin_code, catchcat_common_name,
                matching_species.species, matching_species.pacfin_code, matching_species.common_name))
            return matching_species.species
        except Species.DoesNotExist:
            fmt_str = 'No match to a species found for catch category name "{}".'
            self._logger.warning(fmt_str.format(catchcat_common_name))
            return None

    @pyqtProperty(QVariant, notify=catchIdChanged)
    def currentCatchCatCode(self):
        if self._current_catch:
            return self._current_catch.catch_category.catch_category_code
        else:
            self._logger.warning('No current catch cat, cannot return code')
            return None

    @pyqtProperty(QVariant, notify=catchIdChanged)
    def currentCatch(self):
        # convert peewee model to dict, pass as QVariant
        if self._current_catch is not None:
            return self._add_temp_fields(model_to_dict(self._current_catch))
        else:
            return None

    @pyqtProperty(QVariant, notify=catchIdChanged)
    def currentCatchID(self):
        # convert peewee model to dict, pass as QVariant
        if self._current_catch is not None:
            return self._current_catch.catch
        else:
            return None

    @currentCatch.setter
    def currentCatch(self, data):
        """
        Convert QJSValue->QVariant->dict to peewee model.
        Emit signal if catch ID changed or if weight method changed.

        :param data: QJSValue passed from QML
        """
        # TODO Determine if this is needed any more - should set ID
        try:
            old_current_catch_model = self._current_catch

            if data is None:
                self._logger.info('Cleared current catch.')
                self._current_catch = None
                self._current_catch_model_idx = None
                self.sampleMethod = None
                self._current_handling_method = None
                return

            # self._logger.debug('Current catch set to {0}'.format(data.toVariant()))
            self._logger.debug('Set current catch data.')
            data_variant = data.toVariant()
            # cur_notes = data_variant['notes']
            data_dict = self._remove_temp_fields(data_variant)
            self._current_catch_model_idx = self._catch_model.get_item_index('catch', data_dict['catch'])
            # Save to DB

            self._current_catch = dict_to_model(Catches, data_dict)
            # self._current_catch.notes = cur_notes
            self._current_catch.density = None
            if self._current_catch.sample_count == 0:
                self._current_catch.sample_count = None
            if self._current_catch.sample_weight == 0:
                self._current_catch.sample_weight = None
            self._current_catch.save()

            # Emit signals of interest if associated fields have changed value.
            catch_id_changed, weight_method_changed = self._check_key_fields_for_change(
                old_current_catch_model, data_dict)
            if catch_id_changed:
                self.catchIdChanged.emit()
            if weight_method_changed:
                self.weightMethodChanged.emit()
            # FIELD-1828 this breaks DB writes, but was a fix for FIELD-1786
            # self.sampleMethodChanged.emit(self.sampleMethod)
        except AttributeError as e:
            self._logger.error('Expected QJSValue, got something else. ' + str(e))
        except KeyError as e:
            self._logger.warning(e)
        except IntegrityError as e:
            self._logger.error(e)

    @staticmethod
    def _remove_temp_fields(data_dict):
        # Remove "temp" values for Catches
        data_dict.pop('catch_category_code', None)
        data_dict.pop('catch_category_name', None)
        data_dict.pop('sample_method', None)
        data_dict.pop('catch_or_sample_weight', None)
        data_dict.pop('catch_or_sample_count', None)
        return data_dict

    @staticmethod
    def _add_temp_fields(data_dict):
        """
        Probably don't need extra fields, left here in case we do later
        @param data_dict:
        @return:
        """
        # Add "temp" values for Catches
        data_dict['catch_category_code'] = 'TODO'
        data_dict['catch_category_name'] = 'TODO'
        data_dict['sample_method'] = 'TODO'
        return data_dict

    @staticmethod
    def dict_compare(d1, d2):
        """ From http://stackoverflow.com/questions/4527942/comparing-two-dictionaries-in-python
        """
        d1_keys = set(d1.keys())
        d2_keys = set(d2.keys())
        intersect_keys = d1_keys.intersection(d2_keys)
        added = d1_keys - d2_keys
        removed = d2_keys - d1_keys
        modified = {o: (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
        same = set(o for o in intersect_keys if d1[o] == d2[o])
        return added, removed, modified, same

    def _check_key_fields_for_change(self, old_current_catch_model, new_current_catch_dict):
        """
        Check the two fields in Catches changes to which trigger a signal:
        - catch ID
        - weight method

        :param old_current_catch_model: Value before overwrite with new value.
        :param new_current_catch_dict: New value that is being saved by the setter.
        :return: a tuple of bools (catch_id_field_has_changed, weight_method_has_changed)
        """
        old_current_catch_dict = None if old_current_catch_model is None else \
            model_to_dict(old_current_catch_model)

        if new_current_catch_dict is None or old_current_catch_dict is None:
            return (False, False) if new_current_catch_dict is None and \
                                     old_current_catch_dict is None \
                else (True, True)

        # Both old and proposed dicts are not None

        added, removed, modified, same = ObserverCatches.dict_compare(
            old_current_catch_dict, new_current_catch_dict)

        catch_id_changed = "catch" not in same
        weight_method_changed = "catch_weight_method" not in same

        are_equal = len(added) == 0 and len(removed) == 0 and len(modified) == 0
        if not are_equal:
            self._logger.debug("currentCatch old/new differences:")
            if len(added) > 0:
                self._logger.debug("Added to new.")
            if len(removed) > 0:
                self._logger.debug("Removed from new.")
            if len(modified) > 0:
                self._logger.debug("Modified in new.")
        else:
            self._logger.debug("No currentCatch/savedCatch differences.")

        return catch_id_changed, weight_method_changed

    @pyqtSlot(str, result='QVariant', name='getData')
    def getData(self, data_name):
        """
        Shortcut to get data from the DB that doesn't deserve its own property
        :return: Value found in DB
        """
        if self._current_catch is None:
            self._logger.warning('Attempt to get data with null current catch.')
            return None
        data_name = data_name.lower()
        # self._logger.debug(f'GET DATA {data_name}')
        if data_name == 'catch_disposition':
            return self._current_catch.catch_disposition
        elif data_name == 'catch_weight_method':
            return self._current_catch.catch_weight_method
        elif data_name == 'catch_weight':  # Trawl
            return self._current_catch.catch_weight
        elif data_name == 'catch_count':  # Trawl
            return self._current_catch.catch_count
        elif data_name == 'sample_weight':  # FG
            return self._current_catch.sample_weight
        elif data_name == 'sample_count':  # FG
            return self._current_catch.sample_count
        elif data_name == 'discard_reason':
            return self._current_catch.discard_reason
        elif data_name == 'gear_segments_sampled':
            return self._current_catch.gear_segments_sampled
        elif data_name == 'hooks_sampled':
            return self._current_catch.hooks_sampled
        elif data_name == 'density':  # Translate to NOTES
            return self._get_current_catch_ratio()
        else:
            self._logger.warning('Attempt to get unknown data name: {}'.format(data_name))
            return None

    @pyqtSlot(str, QVariant, name='setData')
    def setData(self, data_name, data_val):
        """
        Set misc data to the DB - should do this for all properties instead of individual pyqtSlots...
        :return:
        """
        if self._current_catch is None:
            self._logger.warning('Attempt to set data with null current catch.')
            return

        data_name = data_name.lower()
        if data_name == 'catch_disposition':
            self._current_catch.catch_disposition = data_val
        elif data_name == 'catch_weight_method':
            self._current_catch.catch_weight_method = data_val
        elif data_name == 'catch_weight':
            try:
                data_val = float(data_val) if data_val else None
                self._current_catch.catch_weight = data_val
            except ValueError as e:
                self._logger.error('catch weight error: {}'.format(e))

        elif data_name == 'catch_count':
            try:
                current_wm = self._current_catch.catch_weight_method
                if current_wm in CatchCategory.WEIGHT_METHODS_WITH_NO_COUNT:
                    self._logger.info(f'Not saving catch count for weight method {current_wm}.')
                    data_val = None
                self._current_catch.catch_count = int(data_val) if (
                            data_val and data_val > 0) else None  # Cannot be 0 FIELD-1825

            except ValueError as e:
                self._logger.error('catch count error: {}'.format(e))
        elif data_name == 'catch_or_sample_weight' or data_name == 'catch_or_sample_count':
            pass  # Readonly values
        elif data_name == 'sample_weight':
            try:
                data_val = float(data_val) if data_val else None
                self._current_catch.sample_weight = data_val
                self._current_catch.sample_weight_um = 'LB'
            except ValueError as e:
                self._logger.error('sample weight error: {}'.format(e))

        elif data_name == 'sample_count':
            try:
                if self._current_catch.catch_weight_method != '13':
                    self._current_catch.sample_count = int(data_val) if (
                            data_val and data_val > 0) else None
            except ValueError as e:
                self._logger.error('sample count error: {}'.format(e))
        elif data_name == 'gear_segments_sampled':
            try:
                self._current_catch.gear_segments_sampled = int(data_val) if (
                        data_val and data_val > 0) else None
            except ValueError as e:
                self._logger.error('gear_segments_sampled error: {}'.format(e))
        elif data_name == 'hooks_sampled':
            try:
                self._current_catch.hooks_sampled = int(data_val) if (
                        data_val and data_val > 0) else None
            except ValueError as e:
                self._logger.error('hooks_sampled error: {}'.format(e))
        elif data_name == 'discard_reason':
            self._current_catch.discard_reason = data_val
        elif data_name == 'density':
            self._set_current_catch_ratio(data_val)
        else:
            self._logger.warning('Attempt to set unknown data name: {}'.format(data_name))
            return
        self._set_cur_prop(data_name, data_val)
        try:
            self._current_catch.save()
        except IntegrityError as e:
            self._logger.error(e)

        logging.info('Set {} to {}'.format(data_name, data_val))
        # Signals should be sent after the current property is set and saved
        if data_name == 'catch_disposition':
            self.dispositionChanged.emit()  # Used by CatchCategoriesScreen
        elif data_name == 'discard_reason':
            self.discardReasonChanged.emit()  # Used by CatchCategoriesScreen
        elif data_name == 'catch_weight_method':
            self.weightMethodChanged.emit()

    def _set_cur_prop(self, prop, value):
        """
        Helper function - set current catch properties in FramListModel
        @param prop: prop name
        @param value: value to store
        @return:
        """
        try:
            if not self._catch_model or self._current_catch_model_idx is None:
                self._logger.error(f'Catch model/ index not set. Cannot set {prop} -> {value}')
                return
            self._catch_model.setProperty(self._current_catch_model_idx, prop, value)
        except Exception as e:
            self._logger.error(f'{e} Index:{self._current_catch_model_idx} Prop: {prop} Value: {value}')

    def _set_current_catch_ratio(self, ratio):
        cur_notes = self._current_catch.notes if self._current_catch.notes else ''
        if ratio is None:
            self._logger.debug(f'Clearing ratio...')
            ratio_re = re.compile('Ratio=([\S_]+)')
            match = ratio_re.search(cur_notes)
            if match:
                orig_ratio = match.group(0)  # Whole string
                cur_notes = cur_notes.replace(orig_ratio, '')
                self.catchRatioChanged.emit(1.0)
            return
        ratio_str = f'Ratio={ratio:.6f}'
        ratio_re = re.compile('Ratio=([\S_]+)')
        match = ratio_re.search(cur_notes)
        if match:
            orig_ratio = match.group(0)  # Whole string
            cur_notes = cur_notes.replace(orig_ratio, ratio_str)
        else:
            cur_notes = cur_notes + f' {ratio_str}'

        self._current_catch.notes = cur_notes
        self._current_catch.save()

        # TODO set in model
        self._set_cur_prop('notes', cur_notes)
        self._logger.info(f'Stored Ratio {ratio_str}')
        self.catchRatioChanged.emit(ratio)

    def _get_current_catch_ratio(self):
        if not self._current_catch:
            return None

        cur_notes = self._current_catch.notes
        if not cur_notes:
            return None
        ratio = ObserverDBUtil.get_current_catch_ratio_from_notes(cur_notes)
        self._logger.info(f'Loaded Ratio {ratio}')
        return ratio

    @pyqtSlot(str, result=QVariant, name='getWMDesc')
    def getWMDesc(self, wm):
        if wm is None:
            self._logger.error('No description, WM is None')
            return '(No WM)'
        return self._wm_descs.get(wm, '(No Description)')

    @pyqtSlot(str, str, result=QVariant, name='checkExistingDispWM')
    def _check_existing_disp_wm(self, disp, wm) -> bool:
        """
        Check for existing Disposition and WM record for current catch
        :param disp: Disposition
        :param wm: weight method
        :return: True if exists
        """

        if self._current_catch:
            cc = self._current_catch.catch_category
        if disp and wm:
            catch_query = Catches.select().where((Catches.fishing_activity == self._current_catch.fishing_activity) &
                                                 (Catches.catch_disposition == disp) &
                                                 (Catches.catch_category == cc) &
                                                 (Catches.catch_weight_method == wm))
            if catch_query.count() > 0:  # Not performant, but number of catches per haul is small.
                self._logger.info(f'Record already exists: {disp} {wm}')
                return True

        return False

    @pyqtProperty(QVariant, notify=catchIdChanged)
    def currentCompID(self):
        if self._current_catch is None:
            self._logger.info("Called with null current catch.")
            return None
        try:
            existing = SpeciesCompositions.get(SpeciesCompositions.catch == self._current_catch.catch)
            # self._logger.debug("Returning '{}'".format(existing.species_composition))
            return existing.species_composition
        except SpeciesCompositions.DoesNotExist:
            self._logger.info("Species Composition record doesn't exist for Catch {}.".format(
                self._current_catch.catch))
            return None

    def _glean_sample_method_from_context(self, catch):
        # Sample method can be determined by catch category (the special case of Pacific Halibut)
        # or from reading this catch's SpeciesComposition record, which has a sample method field,
        # or from noting the absence of a species composition record and the presence of biospecimen data
        # or from noting the absence of any species composition records or any biospecimens records combined with the
        # presence of a weight method set to 7 or 14 (Vessel Estimate or Visual Experience).
        sample_method = None

        self._logger.info('Catch Category Code = {}'.format(catch.catch_category.catch_category_code))
        if catch.catch_category.catch_category_code == ObserverCatches.PACIFIC_HALIBUT_CATCH_CATEGORY_CODE:
            sample_method = self.SM_NO_SPECIES_COMP
        else:
            try:
                existing = SpeciesCompositions.get(SpeciesCompositions.catch == catch.catch)
                sample_method = existing.sample_method
            except SpeciesCompositions.DoesNotExist:
                # Catches with sample method of No Species Composition will come here.
                # If a biospecimen has been entered, return sample method of NSC.
                try:
                    existing = BioSpecimens.get(BioSpecimens.catch == catch.catch)
                    sample_method = self.SM_NO_SPECIES_COMP
                except BioSpecimens.DoesNotExist:
                    # It's possible to come here with an empty NSC CatchCategory - no biospecimens yet, or ever.
                    # Except for two last corner cases, there is insufficient data to distinguish
                    # from a newly added CatchCategory with no SM specified.

                    # Corner Case 1: if the weight method stores weight and count information
                    # at the catch level - and has done so without any spec comp records - then SM=NSC.
                    if not self._wm_uses_counts_and_weights_tab():
                        if self.getData('catch_weight') or self.getData('catch_count'):
                            self._logger.info("CC with WM with weight/count info in CC Details.")
                            sample_method = self.SM_NO_SPECIES_COMP
                    # Corner Case 2: If catch is WM7 or WM14, and has no species comp or biospecimen records, SM=NSC.
                    # (Strictly speaking, this corner case could be limited to catch categories without a mapped
                    # species, but WM7s and WM14s aren't likely to want to add spec composition or biospecimens records,
                    # so defaulting to NSC seems reasonable. And the user can change SM explicitly and add records.)
                    elif self.wmIsEitherVesselEstimateOrVisualExperience:
                        sample_method = self.SM_NO_SPECIES_COMP

                except Exception as e:
                    self._logger.error("Unexpected exception selecting BioSpecimens: {}".format(e))

        self._logger.info(
            "Sample method from inspecting for PHLB and related spec comp and biospecimen records: {}".format(
                sample_method))

        return sample_method

    @pyqtProperty(QVariant, notify=sampleMethodChanged)
    def sampleMethod(self):
        """
        This is a getter that does a set of the underlying property if it is None. This is because
        self._sample_method is not based upon a database value for Catches; i.e. Catches has no sample method field.
        So if _sample_method is None, this getter tries to initialize the value before returning it.
        :return:
        """
        if self._current_catch is None:
            return None

        if self._is_species_comp is not None:
            return self._is_species_comp

        # Before returning None, look in other locations and for special cases.
        self._is_species_comp = self._glean_sample_method_from_context(self._current_catch)

        return self._is_species_comp

    @sampleMethod.setter
    def sampleMethod(self, new_sm):
        """
        Set sample method
        @param new_sm: sample method ID, such as '1', '2', '3', or 'NSC' (No Species Composition)
        @return: None

        Four transitions of interest, current SM --> proposed SM:
        (None --> SpecComp): Pre-req: none. Add'l action: create SpecComp record.
        (None --> NoSpecComp): Pre-req: must have matching species. Add'l action: none
        (NoSpecComp --> SpecComp): Pre-req: none. Add'l action: create SpecComp record.
        (SpecComp --> NoSpecComp): Pre-req: No SpecCompItem records, matching species.
            Add'l action: delete SpecComp record

        Raise exception if pre-req fails. This places burden on caller to first satisfy pre-requisites.
        """
        if self._current_catch is None:
            self._logger.error("Cannot assign sampleMethod, no catch selected")
            self._is_species_comp = None
            return
        current_sample_method = self._is_species_comp
        if current_sample_method is None and new_sm is None:
            # No action necessary
            return
        if current_sample_method == new_sm:
            # No action necessary
            return

        # Calculate attributes of interest
        existing_comp = None
        try:
            existing_comp = SpeciesCompositions.get(SpeciesCompositions.catch == self._current_catch.catch)
        except SpeciesCompositions.DoesNotExist:
            pass

        cc_has_matching_species = self.currentMatchingSpeciesId is not None

        # Pre-requisite: Catch Category for SM=NSC must have matching species, with one exception:
        # current weight method is either 7 (vessel estimate) or 14 (visual experience).
        # This should have been checked before getting here. Raise exception if not the case.
        if new_sm == self.SM_NO_SPECIES_COMP:
            if not cc_has_matching_species and not self.wmIsEitherVesselEstimateOrVisualExperience:
                raise Exception("Catch without matching species cannot have sample method of NSC unless WM7 or WM14.")

        self._is_species_comp = new_sm
        self._set_cur_prop('sample_method', new_sm)  # for TableView display

        ##
        # Additional actions, besides setting sample method:
        ##
        # If moving to Species Composition, update or create SpeciesComposition record
        if new_sm != self.SM_NO_SPECIES_COMP:
            if existing_comp:
                existing_comp.sample_method = new_sm
                existing_comp.save()
                self._logger.info('Set species comp {} for catch {} with sample_method {}'.
                                  format(existing_comp.species_composition,
                                         existing_comp.catch.catch,
                                         existing_comp.sample_method))
            else:
                if new_sm is not None:
                    created_by = ObserverDBUtil.get_current_user_id()
                    created_date = ObserverDBUtil.get_arrow_datestr()
                    newcomp = SpeciesCompositions.create(catch=self._current_catch.catch, sample_method=new_sm,
                                                         created_by=created_by, created_date=created_date)
                    self._logger.info('Created species comp {} for catch {} with sample_method {}'.
                                      format(newcomp.species_composition, newcomp.catch.catch, newcomp.sample_method))

        # If moving to No Species Composition, delete any SpeciesComposition record.
        # Specify recursive so any dependent SpeciesCompositionItem record is deleted as well.
        if new_sm == self.SM_NO_SPECIES_COMP and existing_comp:
            existing_comp.delete_instance(recursive=True)

        # Signal the change in sample method
        self.sampleMethodChanged.emit(self._is_species_comp)
        self.smDescChanged.emit(self._is_species_comp)

    @pyqtProperty(str)
    def SM_NOT_YET_SPECIFIED(self):
        """Convention for catches.sampleMethod value before sample method specified."""
        return "?"

    @pyqtProperty(str, notify=unusedSignal)
    def SM_NO_SPECIES_COMP(self):
        """ Convention for catches.sampleMethod value when No Species Composition button is clicked.
            TODO: Consider removing this property definition and using CatchModel's generally.
                Only concern: OK to define pyqtProperties in CatchModel?
        """
        return self._catch_model.SM_NO_SPECIES_COMP

    @pyqtProperty(str, notify=unusedSignal)
    def SM_IS_SPECIES_COMP(self):
        """ Convention for catches.sampleMethod value when No Species Composition button is clicked.
            TODO: Consider removing this property definition and using CatchModel's generally.
                Only concern: OK to define pyqtProperties in CatchModel?
        """
        return self._catch_model.SM_IS_SPECIES_COMP

    @staticmethod
    def _sample_method_is_species_composition(sample_method):
        return sample_method is not None and sample_method in SampleMethodDescs().sm_descriptions.keys()

    @pyqtProperty(QVariant)
    def currentSampleMethodIsSpeciesComposition(self):
        """Species Composition? Both NSC and SC can be False if not set."""
        sm = self.sampleMethod
        sm_is_sc = sm is not None and sm == self.SM_IS_SPECIES_COMP
        # self._logger.debug("SM={}, smIsNSC={}".format(sm, sm_is_nsc))
        return sm_is_sc

    @pyqtProperty(QVariant)
    def currentSampleMethodIsNoSpeciesComposition(self):
        """No Species Composition? """
        sm = self.sampleMethod
        if self._is_fixed_gear:  # short circuit for FIELD-1857
            if sm is not None and sm == self.SM_IS_SPECIES_COMP:
                return False
            else:
                return True

        sm_is_nsc = sm is not None and sm == self.SM_NO_SPECIES_COMP
        # self._logger.debug("SM={}, smIsNSC={}".format(sm, sm_is_nsc))
        return sm_is_nsc

    @pyqtProperty(QVariant, notify=smDescChanged)
    def sampleMethodDesc(self):
        # Provide legends for cases in Catch Categories (but not Species)
        # where Sample Method is not yet specified, or No Species Composition is chosen.
        if self._is_species_comp is None:
            return '(Not Yet Specified)'
        if self._is_species_comp == self.SM_NO_SPECIES_COMP:
            return 'No Species Composition'

        return SampleMethodDescs().sm_descriptions.get(self._is_species_comp, '')

    @pyqtProperty(QVariant)
    def impedimentToSampleMethodTransition(self):
        """
        A catch category may change its sampling method from '1', '2', '3' to 'NSC' if
        1. No basket data exists AND
        2. No biospecimen data exists

        A catch category may change its sampling method from 'NSC' to '1', '2', or '3' if no biospecimen data exists;
        there's no opportunity to add basket data for NSC catch categories.

        :return: a string describing the first impediment found, or None if no impediment.

        Note: A shift of sample method to NSC could be allowed with existing biospecimen data -
        if that biospecimen data were all for the species that this Catch Category would map to.
        TODO: Consider implementing this exception if this is a frequent use case.
        """
        if self.currentSampleMethodIsSpeciesComposition and self._species.counts_weights.dataExists:
            return "basket data exists"
        if self._biospecimens.dataExists:
            return "biospecimen data exists"
        return None

    @pyqtProperty(QVariant, notify=weightMethodChanged)
    def weightMethod(self):
        if self._current_catch:
            return self._current_catch.catch_weight_method
        else:
            return ''

    @pyqtProperty(QVariant, notify=unusedSignal)
    def wmIsEitherVesselEstimateOrVisualExperience(self):
        if not self._current_catch:
            return False
        ret_val = self._current_catch.catch_weight_method in ['7', '14']
        return ret_val

    def _wm_uses_counts_and_weights_tab(self):
        """
        Checks if the weight method is OK to set aggregated counts/weights values
        (collected via the Counts/Weights tab screen).
        @return: OK if allowed to set values
        """
        # Do not update for weight methods:
        # For WMs 2, 6, 7, and 14, Catch Category Details screen provides a way to enter weights
        #   (and for WM14, count as well). Use values from CC Details for weight and count,
        #   not a summation of basket weights/counts from Counts/Weights tab.
        # WMs 9 and 19 are specific to Pacific Halibut, which has a hard-coded sample method of No Species Composition,
        #   which means that species-specific baskets can't be added,
        #   which means the inclusion of these two WMs here is redundant.
        wms_aggregating_at_catch_level = ['2', '6', '7', '9', '14', '19']
        if self._current_catch and \
                self._current_catch.catch_weight_method not in wms_aggregating_at_catch_level:
            return True
        else:
            return False

    def _wm_uses_counts_and_weights_tab_in_WM3_mode(self):
        """
        OPTECS provides a mode for a Weight Method 3 catch to use counts and weights to collect basket data
        at the catch level, not the species level. This basket information for WM3 catches is used to calculate
        the catch_weight.

        Note: WM3 catches may also uses counts and weights for basket information at the species level,
        but this species weight data is NOT used in calculating catch weight.
        :return: True if catch is WM3
        """
        return True if self._current_catch and self._current_catch.catch_weight_method == '3' else False

    def _handle_species_total_weight_changed(self, wt):
        """
        A catch weight based upon species basket data collected in counts and weights has changed.

        Note that Weight Method 3 uses counts-and-weights in a special mode, collecting catch-level unspeciated
        basket information. Catch weight totals for WM3 are handled elsewhere.

        :param wt:
        :return:
        """
        if not self._wm_uses_counts_and_weights_tab():
            return
        if self._wm_uses_counts_and_weights_tab_in_WM3_mode():
            return

        self._set_cur_prop('catch_weight', wt)

    def _handle_species_total_count_changed(self, ct):
        """
        A catch count based upon species basket data collected in counts and weights has changed.

        Note that Weight Method 3 uses counts-and-weights in a special mode, collecting catch-level unspeciated
        basket information. Catch count totals for not calculated for WM3.

        :param ct:
        :return:
        """
        if not self._wm_uses_counts_and_weights_tab():
            return
        if self._wm_uses_counts_and_weights_tab_in_WM3_mode():
            return

        self._set_cur_prop('catch_count', ct)

    def _handle_fg_total_weight_changed(self, wt):
        """
        Fixed Gear weight

        :param wt:
        :return:
        """

        self._set_cur_prop('sample_weight', wt)
        # TODO this is called twice when just weight or count changes, refactor to call less frequently
        self._calculate_OTC_FG()

    def _handle_fg_PHLB_weight_changed(self, ct):
        self._calculate_OTC_FG()

    def _handle_fg_total_count_changed(self, ct):
        """
        Fixed Gear Count
        :param ct:
        :return:
        """
        if self._current_catch.catch_weight_method != '13':
            self._set_cur_prop('sample_count', ct)
        self._calculate_OTC_FG()

    def _calculate_OTC_FG(self):
        if not self._is_fixed_gear:
            return
        current_set = FishingActivities.get(FishingActivities.fishing_activity == self._current_catch.fishing_activity)
        otc_sample_weight = ObserverCatches.calculate_OTC_FG(self._logger,
                                         current_set,
                                         current_set.total_hooks)

        # Update Model
        if otc_sample_weight:
            self.otcFGWeightChanged.emit(otc_sample_weight, self._current_catch.fishing_activity)

    @staticmethod
    def calculate_OTC_FG(logger, current_set: FishingActivities, total_hooks: int):
        # FIELD-1890: Calculate OTC
        # For FISHING_ACTIVITIES use OTC_WEIGHT_METHOD, populate OBSERVER_TOTAL_CATCH, OTC_WEIGHT_UM
        # 6: Should be blank, something weird happened - comment required
        # 11 (common choice): The sum of all the retained and discarded catch category weights.
        # 8: Extrapolation: OTC=(Sum of catch category wts./ number of gear units sampled) x number of gear units set
        otc_wm = current_set.otc_weight_method
        if otc_wm == '6':
            return
        otc_sample_weight = 0
        otc_sample_count = 0

        if otc_wm == '8':
            catches_q = Catches.select().where(Catches.fishing_activity == current_set)
            for c in catches_q:
                c_weight = c.sample_weight
                c_sampled = c.hooks_sampled
                # c_count = c.sample_count
                if c_weight and c_sampled and total_hooks:
                    otc_sample_weight += (c_weight / c_sampled) * total_hooks
        else:
            # WM 11, others?
            otc_sample_weight = Catches.select().where(Catches.fishing_activity == current_set).aggregate(
                fn.Sum(Catches.sample_weight))

        # # PHLB weights, other WM weights
        # phlb_weight = Catches.select().where(Catches.fishing_activity == current_set).aggregate(
        #     fn.Sum(Catches.catch_weight))
        #
        # if phlb_weight and otc_sample_weight is not None:
        #     otc_sample_weight += phlb_weight
        logger.debug(
            f'Calculated OTC for OTC Method {current_set.otc_weight_method}: wt {otc_sample_weight}, '
            f'ct {otc_sample_count}')

        current_set.observer_total_catch = otc_sample_weight
        current_set.otc_weight_um = 'LB'
        current_set.save()
        return otc_sample_weight


    @pyqtProperty(QVariant, notify=unusedSignal)
    def requiredCCDetailsAreSpecified(self):
        """
        Have all the prerequisite fields been filled in for the current catch category
        so that navigation to later tabs (Species, Counts/Weights, and Biospecimens) is allowed,
        from either the CatchCategoriesScreen or CatchCategoriesDetailsScreen?
        -   Discard Reason must be specified if SM=NSC and disposition is discard.
        -   Navigation to later tabs must be disallowed if NSC and the catch category doesn't have a mapped species.
            See discussion below on this rare corner case (Less than 25 catch categories don't have a matching species).

        :return:
                False if:
                - sample method OR weight method has not been specified.
                - sample method is NSC and discard reason is Dispose and discard reason has not been specified.
                - sample method is NSC and catch category doesn't have a mapped species
                - weight method is 15 and catch ratio (aka WM15 ratio) is null or equal to 1.
                True otherwise.

                A note on the last case of False: if sample method is NSC and the catch category has no matching species,
                no navigation forward is allowed. No Species Composition disallows adding Species Composition records,
                and without a matching species, Biospecimens records can't be added (no way to specify species). Both
                paths forward are forclosed.
        """
        # TODO: This gets called way too many times
        wm = self.getData('catch_weight_method')
        if not wm:
            self._logger.debug('No WM, no CC complete')
            return False

        sm = self.sampleMethod
        if not sm and not self._is_fixed_gear:
            self._logger.debug('No SM, no CC complete')
            return False

        # If Sample Method is No Species Composition, and Disposition is Discarded,
        # also require a Discard Reason to be specified. Rationale:
        # This is the only place to specify discard reason for NSC because the Counts/Weights tab is disabled.
        #
        # In addition, if SM=NSC and the catch category doesn't have a mapped species,
        # then disallow navigation to Biospecimens because there's no knowable species for biospecimens.
        if self.currentSampleMethodIsNoSpeciesComposition:
            catch_disposition = self.getData('catch_disposition')
            catch_discard_reason = self.getData('discard_reason')
            msg = "NSC CC: catch_disposition='{}', discard_reason='{}'"
            self._logger.info(msg.format(catch_disposition, catch_discard_reason))
            if catch_disposition == 'D' and not catch_discard_reason:  # Catch None or empty string discard reason
                self._logger.debug('No DR, no CC complete')
                return False

        if self.currentSampleMethodIsNoSpeciesComposition:
            cc_has_matching_species = self.currentMatchingSpeciesId is not None
            if not cc_has_matching_species:
                self._logger.info(f"Warning: NSC and catch category has no matching species.")
                # result = False

        if wm == '15':
            wm15_weighed_ratio = self._get_current_catch_ratio()
            wm15_weighed_ratio_is_specified = wm15_weighed_ratio is not None and wm15_weighed_ratio != 1.0
            if not wm15_weighed_ratio_is_specified:
                self._logger.info(f"Disallowing navigation because WM15 ratio={wm15_weighed_ratio}")
                return False

        catch_disposition = self._current_catch.catch_disposition if self._current_catch else None

        if self._is_fixed_gear and catch_disposition == self.CATCH_DISCARD_REASON_UNKNOWN:
            return False

        # self._logger.debug("{}OK to navigate to Species tab.".format("" if result else "Not "))
        self._logger.debug('CC looks complete!')
        return True

    @pyqtSlot(QVariant, name='updateWM3TotalCatchWeight')
    def update_WM3_total_catch_weight(self, total_catch_weight):
        if not self._current_catch:
            return

        self.setData("catch_weight", total_catch_weight)
        self._logger.info(
            f"WM3 Update catch_weight for Catch ID {self._current_catch.catch} to {total_catch_weight:.2f}.")


class TestObserverCatches(unittest.TestCase):
    """
    Note: any write/update interaction should be done with test_database...
    http://stackoverflow.com/questions/15982801/custom-sqlite-database-for-unit-tests-for-code-using-peewee-orm
    """
    test_db = APSWDatabase(':memory:')

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

    def _create_test_catches(self):
        """
        Note: intended to run with test_db, running alone will write to real DB
        Example of updating a trip in DB and in model
        """
        for t in range(3):
            newtrip = self.test.create_catch(observer_id=self.user_id_test + t,
                                             vessel_id=self.vessel_id_test + t,
                                             program_id=self.prog_id_test)
            newtrip.save()

    @staticmethod
    def _create_test_categories():
        """
            Intended to run with test_db, before catches created
            """
        for t in range(3):
            CatchCategories.create(catch_category=t, catch_category_name='CAT{}'.format(t), catch_category_code=str(t))

    @staticmethod
    def _create_test_activities():
        """
        Intended to run with test_db, before catches created
        """
        for t in range(3):
            FishingActivities.create(trip=t, fishing_activity_num=t, data_quality='UNK')

    def test_create(self):
        with test_database(self.test_db, [Catches, CatchCategories, FishingActivities]):
            self._create_test_activities()
            self._create_test_categories()
            self.test_catches = ObserverCatches()

            for i in range(3):
                self.test_catches.create_catch(catch_category_id=i, fishing_activity_pk=i)

            q = Catches.select()
            self.assertEqual(q.count(), 3)
