# -----------------------------------------------------------------------------
# Name:        Biospecimens.py
# Purpose:     Support class for BiospecimensModel (Observer)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     2016
# License:     MIT
# ------------------------------------------------------------------------------

from PyQt5.QtCore import pyqtProperty, QVariant, QObject, pyqtSignal, pyqtSlot, QStringListModel

from py.observer.BiospecimenItemsModel import BiospecimenItemsModel
from py.observer.CatchCategory import CatchCategory
from py.observer.DissectionsModel import DissectionsModel
from py.observer.ObserverDBModels import BioSpecimens, BioSpecimenItems, Catches, Species, Lookups, Dissections, \
    Settings
from py.observer.ObserverDBUtil import ObserverDBUtil
from py.observer.ObserverPHLBWeightLookup import PHLBCorrelation

import logging


class ParentalDiscardReasonTracker(QObject):
    """
    Tracker of the 'parental' discard reason that a newly created Biospecimen record should use.

    Biospecimens.discard_reason is not saved from a value provided by the user via the interface,
    but rather is copied from the 'parent': either the current species composition item's discard reason
    or from the catch's discard reason (if sampling method is No Species Comp).

    This class monitors the latest species composition item's discard reason.
    It also can determine whether the current catch is No Species Composition and use the Catch's discard reason.

    Finally, this class also monitors the catch's disposition. If disposition is Retained, return null -
    there is no discard reason.
    """

    def __init__(self, logger, observer_catches):
        super().__init__()
        self._logger = logger
        self._observer_catches = observer_catches
        self._last_species_comp_item_discard_reason = None

        # Set up slot to capture signal of change of discard reason.
        self._observer_catches.species.discardReasonChanged.connect(self._handle_discard_reason_signal)

    def _handle_discard_reason_signal(self, discard_reason):
        self._logger.debug(f"ParentalDiscardReasonTracker: got a species comp item discard reason = {discard_reason}.")
        self._last_species_comp_item_discard_reason = discard_reason

    def get_discard_reason(self):
        if self._observer_catches.getData('catch_disposition') == 'R':
            self._logger.debug("Catch's disposition is Retained; returning None for discard reason.")
            return None
        if self._observer_catches.currentSampleMethodIsSpeciesComposition:
            self._logger.debug(f"Using discard reason {self._last_species_comp_item_discard_reason}" +
                               " from current species composition item.")
            return self._last_species_comp_item_discard_reason
        else:
            # NSC Catch: no Species Comp Items, so use the Catch's discard reason.
            catch_discard_reason = self._observer_catches.getData('discard_reason')
            self._logger.debug(f"Using discard reason {catch_discard_reason} from Catch (No Species Composition).")
            return catch_discard_reason


class Biospecimens(QObject):
    modelChanged = pyqtSignal(name='modelChanged')
    bioSpecimenItemAdded = pyqtSignal(name='bioSpecimenItemAdded')
    totalPHLBWeightChanged = pyqtSignal(QVariant, arguments=['weight'], name='totalPHLBWeightChanged')
    avgPHLBWeightChanged = pyqtSignal(QVariant, name='avgPHLBWeightChanged')
    currentPHLBSampleWeightChanged = pyqtSignal(QVariant, name='currentSampleWeightChanged')
    tallyCountChanged = pyqtSignal(int, name='tallyCountChanged')
    currentWMChanged = pyqtSignal(name='currentWMChanged')
    dataExistsChanged = pyqtSignal(name='dataExistsChanged')  # Only used in CC Details, so usually polled
    currentSpeciesIDChanged = pyqtSignal(name='currentSpeciesIDChanged')
    unusedSignal = pyqtSignal(name='unusedSignal')  # Make QML warning go away
    bioCountChanged = pyqtSignal(QVariant, arguments=['bio_count'], name='bioCountChanged')

    phlb_correlation = PHLBCorrelation()

    def __init__(self, observer_catches, db):
        super().__init__()
        self._logger = logging.getLogger(__name__)

        self._db = db
        # Parameter observer_catches is only used to track discard reason to use for biospecimen
        self._parental_discard_reason_tracker = ParentalDiscardReasonTracker(self._logger, observer_catches)

        self._current_species = None
        self._current_catch = None

        self._is_fixed_gear = False
        self._bios = None
        self._current_bio_specimen = None
        self._bio_items = None
        self._bio_items_model = BiospecimenItemsModel()
        self._current_bio_item = None
        self._current_bio_item_idx = None
        self._current_weight_method = None
        self._current_catch_disposition = None
        self._current_parent_discard_reason = None

        self._dissections = None
        self._dissections_model = DissectionsModel()
        self._dissections_item = None
        self._dissections_model_idx = None

        self._tags = None  # existing and observer tags
        self._existing_tags_model = DissectionsModel()
        self._tags_item = None
        self._tags_idx = None

        self._biosample_descriptions = self.get_bio_descriptions()

        self._current_phlb_weight = None
        self._total_sample_weight = None
        self._total_sample_count = None
        self._avg_sample_weight = None
        self._tally_count = 0

        self._translated_viability = {  # from VIABILITY in LOOKUPS
            'E': 'Excellent', 'P': 'Poor', 'D': 'Dead', 'S': 'Severe',  # PHLB (Pot)
            'MO': 'Moderate', 'MI': 'Minor',  # PHLB Longline
            'F': 'Fair', 'G': 'Good',  # GSTG unique; also uses 'Poor' and 'Dead' above
            'A': 'Alive'  # CHLB unique; also uses 'Dead' above
        }


    @staticmethod
    def get_bio_descriptions():
        """
        Biosample Method Descriptions dict
        @return: {'6': 'description', ...}
        """
        descriptions = dict()
        desc_q = Lookups.select().where(Lookups.lookup_type == 'BS_SAMPLE_METHOD')
        for d in desc_q:
            descriptions[d.lookup_value] = d.description

        return descriptions

    def _load_bios(self):
        try:
            if not self._current_catch or not self._current_species:
                self._logger.warning('Do not have both catch and species id, no biosamples can be loaded')
                if not self._current_catch:
                    self._logger.warning('Current catch is null')
                if not self._current_species:
                    self._logger.warning('Current species is null')
                self._bio_items_model.clear()
                return

            catch_id = self._current_catch.catch
            species_id = self._current_species.species
            catch_disposition_is_retained = True if self._current_catch_disposition == 'R' else False
            parent_discard_reason = self._current_parent_discard_reason

            self._total_sample_weight = None
            self._total_sample_count = None
            self._avg_sample_weight = None
            self._current_phlb_weight = None
            self._bios = []

            self._bio_items_model.clear()
            if catch_disposition_is_retained:
                # No discard reason if catch's disposition is retained.
                self._bios = BioSpecimens.select().where((BioSpecimens.catch == catch_id) &
                                                         (BioSpecimens.species == species_id) &
                                                         (BioSpecimens.discard_reason >> None))
            else:
                # Restrict biospecimens displayed to those not only matching catch and species but discard reason as well.
                if parent_discard_reason:
                    self._bios = BioSpecimens.select().where((BioSpecimens.catch == catch_id) &
                                                             (BioSpecimens.species == species_id) &
                                                             (BioSpecimens.discard_reason == parent_discard_reason))
                    self._logger.info(f'Loading {self._bios.count()} top-level BIOSPECIMENS for DR {parent_discard_reason}')
                else:
                    self._logger.error('Parent discard reason not set. No bios loaded.')

            new_bio_count = 0
            for bio in self._bios:  # Can be more than one for PHLB, which has BM 7 and 10
                self._current_bio_specimen = bio
                items = BioSpecimenItems.select().where(BioSpecimenItems.bio_specimen == bio.bio_specimen)
                self._logger.info('Found {} biospecimen items.'.format(items.count()))
                new_bio_count += items.count()
                for i in items:
                    self._logger.debug('Load biospecimen item {}'.format(i.bio_specimen_item))
                    self._current_bio_item = i
                    if self._is_phlb_bio_item(self._current_bio_item):
                        if i.specimen_length:
                            int_length = int(i.specimen_length)
                            phlb_temp_weight = self.phlb_correlation.get_weight(int_length)
                            self._current_bio_item_idx = \
                                self._bio_items_model.add_biospecimen_item(i, phlb_temp_weight=phlb_temp_weight)
                        else:
                            self._current_bio_item_idx = \
                                self._bio_items_model.add_biospecimen_item(i, phlb_temp_weight=0)
                            self._logger.warning('Loaded PHLB specimen with no length.')
                    else:
                        self._current_bio_item_idx = self._bio_items_model.add_biospecimen_item(i)
                self.modelChanged.emit()
            self.bioCountChanged.emit(new_bio_count)

            self._calculate_phlb_weight()

        except BioSpecimens.DoesNotExist as e:
            self._logger.error(e)

    def _is_phlb_bio_item(self, biospecimen_item):
        try:
            phlb_species_id = 10141
            species_id = biospecimen_item.bio_specimen.species.species
            return species_id == phlb_species_id
        except Exception:
            return False

    @pyqtProperty(QVariant, notify=modelChanged)
    def bioSpecimenMethodsModel(self):
        method_numbers = [x[:2] for x in self._db._bs_samplemethods]
        bs_methods = [str(int(num)) for num in method_numbers]
        return bs_methods

    @pyqtSlot(str, result=str, name='getBiosampleMethodDesc')
    def getBiosampleMethodDesc(self, value):
        """
        Given a single digit value, get description of biosample method
        @param value: '6' - '10' etc
        @return: str description
        """
        return self._biosample_descriptions[value]

    @pyqtProperty(bool, notify=unusedSignal)
    def isFixedGear(self):
        return self._is_fixed_gear

    @isFixedGear.setter
    def isFixedGear(self, is_fixed):
        self._logger.debug(f'Is fixed gear: {is_fixed}')
        self._is_fixed_gear = is_fixed

    @pyqtProperty(QVariant)
    def currentCatchID(self):
        return self._current_catch.catch if self._current_catch else None

    @currentCatchID.setter
    def currentCatchID(self, current_id):
        try:
            if self.currentCatchID == current_id:
                self._logger.debug(f'Catch already set to {current_id}, abort setting it.')
                return
            self._current_catch = Catches.get(Catches.catch == current_id)
            self._logger.info('Current catch to {}'.format(self._current_catch.catch))

            # Clear species
            self._current_species = None

            # Clear biospecimen, phlb weights
            self._clear_current()

        except Catches.DoesNotExist as e:
            self._logger.warning(e)

    @pyqtProperty(QVariant, notify=currentSpeciesIDChanged)
    def currentSpeciesID(self):
        if self._current_species:
            return self._current_species.species
        else:
            return None

    @currentSpeciesID.setter
    def currentSpeciesID(self, current_id):
        try:
            # Clear biospecimen, phlb weights
            self._clear_current()  # TODO check if current_id is already set
            if current_id is None:
                return
            self._current_species = Species.get(Species.species == current_id)
            self._logger.info('Current species ID to {}, {}'.format(
                self._current_species.species, self._current_species.common_name))

            # Populate bio items
            self._load_bios()
            self.currentSpeciesIDChanged.emit()
        except Species.DoesNotExist as e:
            self._logger.warning(e)

    @pyqtProperty(QVariant, notify=currentSpeciesIDChanged)
    def currentSpeciesCommonName(self):
        if self._current_species:
            return self._current_species.common_name
        else:
            # "None Selected" matches convention used by ObserverSpecies.currentSpeciesItemName
            # Returning None or empty string causes error in ObserverSpecies.requiredProtocolsBarcodes
            return "None Selected"

    @pyqtProperty(QVariant)
    def currentCatchDisposition(self):
        if self._current_catch_disposition:
            return self._current_catch_disposition
        else:
            return None

    @currentCatchDisposition.setter
    def currentCatchDisposition(self, current_catch_disposition):
        """
        Retained or Discarded. Used in connection with discard reason to determine what biospecimens
        are relevant for display in Biospecimens.

        :param current_catch_disposition:
        :return:
        """
        self._current_catch_disposition = current_catch_disposition

    @pyqtProperty(QVariant, notify=unusedSignal)
    def currentParentDiscardReason(self):
        return self._parental_discard_reason_tracker.get_discard_reason()

    @currentParentDiscardReason.setter
    def currentParentDiscardReason(self, current_parent_discard_reason):
        """
        11 .. 19. Used in connection with catch disposition to determine what biospecimens
        are relevant for display in Biospecimens.

        Note that this value is set in CatchCategoriesScreen or CountsWeightsScreen.
        Biospecimens uses this value to determine what Biospecimens are related to this catch category,
        species, and discard reason.

        :param current_parent_discard_reason:
        :return:
        """
        self._logger.debug(f'Set current parent discard reason to {current_parent_discard_reason}')
        self._current_parent_discard_reason = current_parent_discard_reason

    def _clear_current(self):
        self._current_bio_item = None
        self._current_bio_item_idx = None
        self._bio_items_model.clear()
        self._total_sample_weight = None
        self._total_sample_count = None
        self._avg_sample_weight = None
        self._current_phlb_weight = None
        self._tally_count = 0
        self.tallyCountChanged.emit(self._tally_count)
        # self.dataExistsChanged.emit()

    @pyqtProperty(QVariant, notify=unusedSignal)
    def currentBiospecimenIdx(self):
        return self._current_bio_item_idx

    @currentBiospecimenIdx.setter
    def currentBiospecimenIdx(self, item_idx):
        self._logger.debug(f'Set currentBiospecimenIdx to {item_idx}')
        try:
            if item_idx is None or item_idx < 0:
                self._current_bio_item_idx = None
                self._current_bio_item = None
                self._current_bio_specimen = None
                self._logger.debug('Cleared currentBiospecimenIdx')
                return
            self._current_bio_item_idx = item_idx
            db_id = self._bio_items_model.get(self._current_bio_item_idx)['bio_specimen_id']
            self._current_bio_item = BioSpecimenItems.get(BioSpecimenItems.bio_specimen_item == db_id)
            # also need to set parent biospecimen
            self._current_bio_specimen = self._current_bio_item.bio_specimen
        except Exception as e:
            self._logger.error('currentBiospecimenIdx setter: {}'.format(e))

    @pyqtProperty(QVariant, notify=modelChanged)
    def BiospecimenItemsModel(self):
        return self._bio_items_model

    @pyqtProperty(QVariant, notify=modelChanged)
    def ExistingTagsModel(self):
        """
        Just the ET tags, not the OT tags. Use to populate the list of existing tags in BioTagsScreen.
        :return:
        """
        return self._existing_tags_model

    @pyqtProperty(QVariant, notify=modelChanged)
    def bioSampleMethod(self):
        """
        Biosample Method for current Biospecimens row
        @return:
        """
        if self._current_bio_specimen:
            return self._current_bio_specimen.sample_method
        else:
            return None

    @bioSampleMethod.setter
    def bioSampleMethod(self, method):
        """
        Set Biosample Method for current Biospecimens row
        @param method:
        @return:
        """
        if self._current_bio_specimen:
            self._logger.debug("Set bioSampleMethod to " + method)
            self._current_bio_specimen.sample_method = method
            self._current_bio_specimen.save()
            self.modelChanged.emit()

    @pyqtProperty(QVariant, notify=modelChanged)
    def discardReason(self):
        """
        TODO How do we specify biospecimen Discard Reason- currently at counts/ weights ??
        @return:
        """
        if self._current_bio_specimen:
            return self._current_bio_specimen.discard_reason
        else:
            return None

    # No setter for discardReason: discard reason is set when a biospecimens record is created.

    @pyqtSlot(QVariant, int, QVariant, name='addBiospecimenItem')
    def add_biospecimen_item(self, species_name, method, sex):
        if self._current_catch is None:
            self._logger.error('Current catch is still None, cannot add biospecimen')
            return
        try:
            spec_id = Species.get(Species.common_name == species_name).species
            user_id = ObserverDBUtil.get_current_user_id()
            created_date = ObserverDBUtil.get_arrow_datestr()
            discard_reason = self._parental_discard_reason_tracker.get_discard_reason()
            self._current_bio_specimen, created = BioSpecimens.get_or_create(catch=self._current_catch.catch,
                                                                             species=spec_id,
                                                                             sample_method=method,
                                                                             discard_reason=discard_reason,
                                                                             defaults={'created_by': user_id,
                                                                                       'created_date': created_date})
            self._logger.info(
                f"{'Created' if created else 'Got'} biospecimen record (discard_reason={discard_reason}).")

            self._current_bio_item = BioSpecimenItems.create(bio_specimen=self._current_bio_specimen.bio_specimen,
                                                             specimen_sex=sex,
                                                             created_by=user_id,
                                                             created_date=created_date)

            self._current_bio_item_idx = self._bio_items_model.add_biospecimen_item(self._current_bio_item)
        except Species.DoesNotExist as e:
            self._logger.error(e)
        except Exception as e:
            self._logger.error(e)
        finally:
            self.bioSpecimenItemAdded.emit()
            self._calculate_phlb_weight()
            self.bioCountChanged.emit(self._bio_items_model.count)
            # self.dataExistsChanged.emit()

    @pyqtSlot(int, name='addPHLBTally')
    def addPHLBTally(self, method):
        if self._current_catch is None:
            self._logger.error('Current catch is still None, cannot add biospecimen')
            return
        try:
            spec_id = Species.get(Species.common_name == 'Pacific Halibut').species  # TODO refactor to const
            user_id = ObserverDBUtil.get_current_user_id()
            created_date = ObserverDBUtil.get_arrow_datestr()
            discard_reason = self._parental_discard_reason_tracker.get_discard_reason()
            self._current_bio_specimen, _ = BioSpecimens.get_or_create(catch=self._current_catch.catch,
                                                                       species=spec_id,
                                                                       sample_method=method,
                                                                       discard_reason=discard_reason,
                                                                       defaults={'created_by': user_id,
                                                                                 'created_date': created_date}
                                                                       )

            self._current_bio_item = BioSpecimenItems.create(bio_specimen=self._current_bio_specimen.bio_specimen,
                                                             notes="Tally",
                                                             created_by=user_id,
                                                             created_date=created_date)
            self._current_bio_item_idx = self._bio_items_model.add_biospecimen_item(self._current_bio_item)
        except Species.DoesNotExist as e:
            self._logger.error(e)
        except Exception as e:
            self._logger.error(e)
        finally:
            self._calculate_phlb_weight()
            # self.dataExistsChanged.emit()

    @pyqtSlot(name='delPHLBTally')
    def delPHLBTally(self):
        """
        Look for a phlb with no length set and delete it from DB and BiospecimenItemsModel
        """
        if self._current_catch is None:
            return
        spec_id = Species.get(Species.common_name == 'Pacific Halibut').species  # TODO refactor to const
        current_biospecimens = BioSpecimens.select().where(
            (BioSpecimens.catch == self._current_catch.catch) &
            (BioSpecimens.species == spec_id))
        for bio in current_biospecimens:
            # Get first "blank" biospecimen item and delete it
            try:
                tally_entry_q = BioSpecimenItems.get(BioSpecimenItems.bio_specimen == bio.bio_specimen,
                                                     BioSpecimenItems.specimen_length >> None)
                if tally_entry_q:
                    del_idx = tally_entry_q.bio_specimen_item
                    self.delete_biospecimen_item(del_idx)
                    del_model_idx = self._bio_items_model.get_item_index('bio_specimen_item', del_idx)
                    if del_model_idx >= 0:
                        self._bio_items_model.removeItem(del_model_idx)
                        self._calculate_phlb_weight()
                    else:
                        self._logger.warning('Could not remove biospecimen item {} from model.'.format(del_model_idx))

            except BioSpecimenItems.DoesNotExist:
                pass
                # self.dataExistsChanged.emit()

    def _log_dependencies(self, dependencies, context_message=""):
        """
        Log the non-null fields of records in the list of dependencies.

        :param dependencies: from Peewee model_instance.dependencies()
        :return: None
        """
        self._logger.info('Peewee dependency information. Context: {}:'.format(
            context_message if not None else "(None supplied)"))
        for (query, fk) in dependencies:
            model = fk.model_class
            query_result = model.select().where(query).execute()
            if query_result:
                try:
                    for row in query_result:
                        ObserverDBUtil.log_peewee_model_instance(self._logger, row)

                except Exception as e:
                    self._logger.error(e)

    @pyqtSlot(QVariant, bool, name='deleteBiospecimenItem')
    def delete_biospecimen_item(self, bio_speciment_item_id, recursive=False):
        """
        Delete a record in BIO_SPECIMEN_ITEMS if it exists,
        and if recursive, delete any subsidiary records in DISSECTIONS (barcodes).

        This is the data equivalent to deleting a row in the table on the Biospecimens screen.

        Recalculate Pacific Halibut weight in case record deleted was of species PHLB.

        :param bio_speciment_item_id:
        :param recursive:
            T:  Delete any subsidiary records in DISSECTIONS (barcodes).
            F:  Leave DISSECTION records as zombies
        :return: None
        """
        try:
            current_item = BioSpecimenItems.get(bio_specimen_item=bio_speciment_item_id)
            current_biospecimen = current_item.bio_specimen
            ObserverDBUtil.log_peewee_model_instance(self._logger, current_item, "About to be deleted")
            dependency_context_msg = "About to delete these" if recursive else "These will be left as zombies"
            self._log_dependencies(current_item.dependencies(), dependency_context_msg)

            current_item.delete_instance(recursive=recursive)
            self._logger.info('Deleted BIO_SPECIMEN_ITEMS item {}'.format(bio_speciment_item_id))

            # If parent biospecimen is childless, remove it as well
            remaining_items = BioSpecimenItems.select().where(
                BioSpecimenItems.bio_specimen == current_biospecimen.bio_specimen)
            if remaining_items.count() > 0:
                self._logger.info("Not deleting parent BIO_SPECIMENS record; it has other children.")
            else:
                current_biospecimen.delete_instance()
                self._logger.info("Deleted parent BIO_SPECIMENS record, as it had no other children.")

                # Currently, model deletion handled in QML
        except BioSpecimenItems.DoesNotExist as e:
            self._logger.error(e)
        finally:
            self._calculate_phlb_weight()
            self.bioCountChanged.emit(self._bio_items_model.count)  # might need to hack to -1
            # self.dataExistsChanged.emit()

    @pyqtSlot(str, result='QVariant', name='getData')
    def getData(self, data_name):
        """
        Shortcut to get data from the DB that doesn't deserve its own property
        (Note, tried to use a dict to simplify this, but DB cursors were not updating)
        :return: Value found in DB
        """
        if self._current_bio_item_idx is None or self._current_bio_item is None:
            # self._logger.warning('Attempt to get data with null current trip.')
            return None
        data_name = data_name.lower()
        if data_name == 'specimen_length':
            return self._current_bio_item.specimen_length
        if data_name == 'specimen_weight':
            return self._current_bio_item.specimen_weight
        if data_name == 'specimen_sex':
            return self._current_bio_item.specimen_sex
        elif data_name == 'viability':
            # Translate single/double-letter viability codes in database to full-word equivalent.
            try:
                return self._translated_viability[self._current_bio_item.viability]
            except:
                return self._translate_viability_to_key(self._current_bio_item.viability)
        elif data_name == 'maturity':
            return self._current_bio_item.maturity
        elif data_name == 'adipose_present':
            return self._current_bio_item.adipose_present
        else:
            self._logger.warning('Attempt to get unknown data name: {}'.format(data_name))
            return None

    def _set_cur_prop(self, bio_property, value):
        """
        Helper function - set current haul properties in BiospecimensItemsModel
        @param bio_property: property name
        @param value: value to store
        @return:
        """
        self._bio_items_model.setProperty(self._current_bio_item_idx,
                                          bio_property, value)

    @pyqtSlot(str, QVariant, name='setData')
    def setData(self, data_name, data_val):
        if self._current_bio_item_idx is None or self._current_bio_item is None:
            self._logger.warning('No Biospecimen Item is currently active/selected')
            return
        self._logger.info(f'*** Biospecimen index {self._current_bio_item_idx} <= {data_name} {data_val}')
        try:
            data_name = data_name.lower()
            self._bio_items_model.setProperty(self._current_bio_item_idx, data_name, data_val)
            if data_name == 'specimen_weight':
                if not self._is_PHLB_wm():
                    self._current_bio_item.specimen_weight = data_val
                    if data_val:
                        self._current_bio_item.specimen_weight_um = 'LB'
            elif data_name == 'specimen_length':
                self._current_bio_item.specimen_length = data_val
                if data_val:
                    self._current_bio_item.specimen_length_um = 'CM'
                if self._is_PHLB_wm():
                    int_length = int(self._current_bio_item.specimen_length) \
                        if self._current_bio_item.specimen_length else None
                    self._current_phlb_weight = self.phlb_correlation.get_weight(int_length)

                    if not self._current_phlb_weight:
                        self._logger.error(f'Unable to look up PHLB weight for length {int_length}, setting to 0')
                        self._current_phlb_weight = 0
                    # Update model before recalculating phlb weight
                    self.setData('specimen_weight', self._current_phlb_weight)
                    self._calculate_phlb_weight()
                    self.currentPHLBSampleWeightChanged.emit(self._current_phlb_weight)

            elif data_name == 'specimen_sex':
                self._current_bio_item.specimen_sex = data_val
            elif data_name == 'viability':
                # Translate
                viability_val = data_val
                via_key = self._translate_viability_to_key(viability_val)
                if via_key:
                    self._current_bio_item.viability = via_key
                    data_val = via_key
                else:
                    self._current_bio_item.viability = None
            elif data_name == 'maturity':  # eggs present?
                data_val = self._lookup_maturity_value_for_database(data_val)
                self._current_bio_item.maturity = data_val
            elif data_name == 'adipose_present':  # Salmon
                self._current_bio_item.adipose_present = data_val
            elif data_name == 'biosample_method':  # Sets parent Biospecimen biosample method
                self.update_or_create_biospecimen_bm(data_val)
            else:
                self._logger.warning('Attempt to set unknown data name: {}'.format(data_name))
                return

            self._set_cur_prop(data_name, data_val)
            self._current_bio_item.save()
            logging.debug('Set {} to {}'.format(data_name, data_val))
        except Exception as e:
            self._logger.error(e)

    def _translate_viability_to_key(self, viability_val):
        if not viability_val:
            return
        try:
            for key, value in self._translated_viability.items():
                if value == viability_val:
                    return key
            # didn't find, fall through
            return viability_val
        except Exception as e:
            # self._logger.debug(e)
            return viability_val


    def _lookup_maturity_value_for_database(self, ui_maturity_value) -> str:
        """
        Choices for Biospecimens Maturity for Dungeness Crabs are displayed on the screen as "Eggs Yes" and "Eggs No".
        These values are currently stored as '0' or '1' in IFQ at Center.
        Map "Y" or True to the Lookup value for Eggs Yes and all other values to the Lookup value for Eggs No.

        :return: a text value, currently either '0' or '1', but current value is Lookups-based.
        """
        if ui_maturity_value == "Y" or ui_maturity_value is True:
            try:
                eggs_value_in_db = Lookups.get((Lookups.lookup_type == 'MATURITY') &
                                               (Lookups.description == 'DCRB Eggs Yes')).lookup_value
            except Lookups.DoesNotExist:
                self._logger.error("Lookup of type 'MATURITY' and of description 'DCRB Eggs Yes' failed. Using '1'.")
                eggs_value_in_db = '1'
        else:
            try:
                eggs_value_in_db = Lookups.get((Lookups.lookup_type == 'MATURITY') &
                                               (Lookups.description == 'DCRB Eggs No')).lookup_value
            except Lookups.DoesNotExist:
                self._logger.error("Lookup of type 'MATURITY' and of description 'DCRB Eggs No' failed. Using '0'.")
                eggs_value_in_db = '0'

        self._logger.debug(f"Using {eggs_value_in_db} for database value for eggs maturity.")
        return eggs_value_in_db

    def update_or_create_biospecimen_bm(self, biosample_method):
        """
        Ensure all biospecimens have biospecimen_items attached
        """
        previous_sm = self._current_bio_specimen.sample_method
        species = self._current_bio_specimen.species

        self._logger.info(f'Changing biosample method from {previous_sm} to {biosample_method}')

        # Count other biospecimen items tied to previous BM
        count_bio_items_bm = BioSpecimenItems. \
            select().where(
            (BioSpecimenItems.bio_specimen == self._current_bio_specimen) &
            (BioSpecimenItems.bio_specimen_item != self._current_bio_item)).count()

        if count_bio_items_bm == 0:
            self._logger.debug(f'Now childless, deleting BioSpecimen id={self._current_bio_specimen.bio_specimen}')
            self._current_bio_specimen.delete_instance()
            self._current_bio_specimen = None
        else:
            self._logger.debug(f'Other BiospecimenItems tied to same BM: {count_bio_items_bm}')

        user_id = ObserverDBUtil.get_current_user_id()

        discard_reason = self._parental_discard_reason_tracker.get_discard_reason()
        created_date = ObserverDBUtil.get_arrow_datestr()
        self._current_bio_specimen, created = \
            BioSpecimens.get_or_create(catch=self._current_catch.catch,
                                       species=species,
                                       sample_method=biosample_method,
                                       discard_reason=discard_reason,
                                       defaults={'created_by': user_id,
                                                 'created_date': created_date})
        self._current_bio_item.bio_specimen = self._current_bio_specimen.bio_specimen
        action_text = 'Created new' if created else 'Switched to existing'
        self._logger.debug(f'{action_text} parent BioSpecimen (id={self._current_bio_specimen.bio_specimen}, '
                           f'sm={biosample_method})')

    @pyqtSlot(QVariant, QVariant, name='set_existing_tag')
    def set_existing_tag(self, index, tag_value):
        try:
            model_item = self._existing_tags_model.get(index)
            db_item = Dissections.get(dissection=model_item['dissection'])
            db_item.band = tag_value
            db_item.save()
            self._logger.info('Set bio item {} to {}'.format(index, tag_value))
            self._existing_tags_model.setProperty(index, 'band', tag_value)
        except Dissections.DoesNotExist as e:
            self._logger.error(e)
        except Exception as e:
            self._logger.error(e)

    @pyqtSlot(QVariant, name='add_existing_tag')
    def add_existing_tag(self, existing_tag_value):
        """
        Add existing tag dissection. This is the only dissection type that supports multiple tags.
        @param existing_tag_value: str
        @return: new item idx
        """
        if self._current_bio_item is None:
            self._logger.error('Current bio item None, cannot add dissection')
            return
        try:
            # Existing Tag - Dissection Type = 8, write existing_tag_value to BAND_ID
            existing_tag_type = '8'
            user_id = ObserverDBUtil.get_current_user_id()
            self._tags_item = Dissections.create(bio_specimen_item=self._current_bio_item.bio_specimen_item,
                                                 dissection_type=existing_tag_type,
                                                 band=existing_tag_value,
                                                 created_by=user_id,
                                                 created_date=ObserverDBUtil.get_arrow_datestr()
                                                 )

            self._tags_idx = self._existing_tags_model.add_item(self._tags_item)
            self._logger.info(f"Existing tag count = {self._existing_tags_model.count}.")

        except Exception as e:
            self._logger.error(e)

    @pyqtSlot(QVariant, name='delete_existing_tag')
    def delete_existing_tag(self, index):
        """
        Used in BioTagsScreen.qml.

        :param index: index in ExistingTagsModel
        :return:
        """
        try:
            model_item = self._existing_tags_model.get(index)
            db_item = Dissections.get(Dissections.dissection == model_item['dissection'])
            if db_item.dissection_type != '8':
                raise IndexError("Method intended to delete dissections of type existing tag ('8').")
            db_item.delete_instance()
            self._logger.info('Deleted Existing Tag Dissection {}'.format(index))
            self._existing_tags_model.removeItem(index)

        except Dissections.DoesNotExist as e:
            self._logger.error(e)

        except Exception as e:
            self._logger.error(e)

    @pyqtSlot(QVariant, QVariant, result=bool, name='deleteExistingDissectionByBarcodeTypeAndValue')
    def delete_existing_dissection_by_barcode_type_and_value(self, barcode_type, barcode_value):
        delete_succeeded = True
        try:
            # Delete from the database. The database field holding the barcode value varies upon the type:
            # - Field dissection_barcode for any type except 8 and 9
            # - Field band for type 8 or 9
            if barcode_type == '8' or barcode_type == '9':
                db_item = Dissections.get((Dissections.dissection_type == barcode_type) &
                                          (Dissections.band == barcode_value))
            else:
                db_item = Dissections.get((Dissections.dissection_type == barcode_type) &
                                          (Dissections.dissection_barcode == barcode_value))
            db_item.delete_instance()
            self._logger.info(f'Deleted Dissection item for Barcode={barcode_value} of Type {barcode_type}.')

            # Delete from the view model by refreshing from the database.
            self.update_barcodes_str()

            self.modelChanged.emit()

            return delete_succeeded

        except Dissections.DoesNotExist as e:
            self._logger.error(e)
            return not delete_succeeded

        except Exception as e:
            self._logger.error(e)
            return not delete_succeeded

    @pyqtSlot(name='clearTags')
    def clear_tags_model(self):
        self._existing_tags_model.clear()

    @pyqtSlot(name='loadExistingTags')
    def load_existing_tags(self):
        """
        Load Existing Tags (but not Observer Tags) into view model used by the ListView for Existing Tags
        """
        self.clear_tags_model()
        tag_type = '8'
        codes = self._get_dissections(dissection_type=tag_type)
        count = 0
        if codes is not None:
            count = len(codes)
            for c in codes:
                self._tags_item = c
                self._tags_idx = self._existing_tags_model.add_item(self._tags_item)
        self._logger.debug(f'Loaded {count} dissections of Type {tag_type}.')

    @pyqtSlot(result=str, name='load_barcode_types_str')
    def load_barcode_types_str(self):
        """
        Load a string with the barcode types for this specimen
        @return: 'FL, WS', '' if none
        """

        if self._current_bio_item is None:
            return ''

        translate_dict = {  # from spreadsheet, LOOKUPS
            # value : abbrev
            '1': 'O',
            '2': 'SC',
            '3': 'SS',
            '4': 'FC',
            '5': 'FR',
            '6': 'TS',  # corals only?
            '7': 'WS',
            '8': 'ET',  # should filter this out: External Tag
            '9': 'OT'  # should filter this out: Observer Tag
        }

        found_abbrevs = []
        bio_dissections = Dissections.select().where(
            (Dissections.bio_specimen_item == self._current_bio_item.bio_specimen_item) &
            (Dissections.dissection_type != '8') &
            (Dissections.dissection_type != '9'))
        if len(bio_dissections) == 0:
            return ''

        for b in bio_dissections:
            abbrev = translate_dict.get(b.dissection_type, '?')
            found_abbrevs.append(abbrev)

        return ','.join(found_abbrevs)

    @pyqtSlot(name='update_barcodes_str')
    def update_barcodes_str(self):
        if self._bio_items_model and self._current_bio_item:
            self._bio_items_model.update_barcodes(self._current_bio_item)

    @pyqtSlot(name='update_tags_str')
    def update_tags_str(self):
        if self._bio_items_model and self._current_bio_item:
            self._bio_items_model.update_tag(self._current_bio_item)

    @pyqtSlot(name='update_biosample_method')
    def update_biosample_method(self):
        if self._bio_items_model and self._current_bio_item:
            self._bio_items_model.update_biosample_method(self._current_bio_item)

    @pyqtSlot(str, result=str, name='get_barcode_value_by_type')
    def get_barcode_value_by_type(self, barcode_type):
        if self._current_bio_item is None:
            return ''
        item_id = self._current_bio_item.bio_specimen_item
        try:
            barcode_row = Dissections.get((Dissections.bio_specimen_item == item_id) &
                                          (Dissections.dissection_type == barcode_type))
            if barcode_row is None:
                return ''
            elif barcode_type == '8' or barcode_type == '9':
                self._logger.debug('Loaded {}'.format(barcode_row.band))
                if barcode_row.band is not None:
                    return str(barcode_row.band)
                else:
                    return ''
            else:
                self._logger.debug('Loaded {}'.format(barcode_row.dissection_barcode))
                if barcode_row.dissection_barcode is not None:
                    return str(barcode_row.dissection_barcode)
                else:
                    return ''
        except Dissections.DoesNotExist:
            return ''
        except Exception as e:
            self._logger.error(e)

    def lookup_dissection_type(self, dissection_type):
        """
        Lookup up the description of the dissection type.
        """
        try:
            return Lookups.get((Lookups.lookup_type == 'DISSECTION_TYPE') &
                               (Lookups.lookup_value == dissection_type)).description
        except Lookups.DoesNotExist as e:
            self._logger.error(str(e))
        return "undefined"

    @pyqtSlot(str, str, result=QVariant, name='getBarcodeEntryInfo')
    def get_barcode_entry_info(self, barcode_type, barcode):
        """
        Return a dictionary of information on a DISSECTIONS row.
        Chose not to return a model_to_dict of an entry but a dict with at lookups in other tables
        (e.g. the description of the dissection_type rather than the ID).

        Depending upon barcode type, the barcode value is stored in two alternative locations in DISSECTIONS table:
        the dissection_barcode field for types 1..7, and band for types 8 and 9.

        :param barcode_type: a digit from 1..9, as a string.
        :param barcode:
        :return: dictionary of information on a DISSECTIONS entry or None
            Dictionary keys: 'trip_id', 'haul_id', 'catch_category_code',
                'species_common_name', 'dissection_type_description'
        """
        if barcode_type == '8' or barcode_type == '9':
            barcode_entries = Dissections.select().where((Dissections.band == barcode) &
                                                         (Dissections.dissection_type == barcode_type))
        elif int(barcode_type) in range(1, 12):
            barcode_entries = Dissections.select().where(Dissections.dissection_barcode == barcode)
        else:
            raise IndexError(f"Unexpected barcode type of '{barcode_type}'. Known values are '1' ... '9'.")
        if len(barcode_entries) == 0:
            return None
        if len(barcode_entries) > 1:
            self._logger.error("Unexpectedly got {} entries rather than 1.".format(len(barcode_entries)))
        barcode_entry = barcode_entries[0]
        dissection_type_description = self.lookup_dissection_type(barcode_entry.dissection_type)
        return_dict = {
            "trip_id": barcode_entry.bio_specimen_item.bio_specimen.catch.fishing_activity.trip.trip,
            "haul_id": barcode_entry.bio_specimen_item.bio_specimen.catch.fishing_activity.fishing_activity,
            "catch_category_code": barcode_entry.bio_specimen_item.bio_specimen.catch.catch_category.catch_category_code,
            "species_common_name": barcode_entry.bio_specimen_item.bio_specimen.species.common_name,
            "dissection_type_description": dissection_type_description,
        }
        return return_dict

    @pyqtSlot(QVariant, result=bool, name='barcodeTypeRequiresNineDigitBarcode')
    def barcode_type_requires_nine_digit_barcode(self, barcode_type):
        self._logger.debug(f"Barcode Type = '{barcode_type}'.")
        # Only Barcode type 8,9 are exempt from 9-digits barcodes
        EXEMPT_NINE_DIGIT_BARCODE_TYPES = (8, 9)
        # Barcode types are defined in Observer.db LOOKUPS WHERE LOOKUP_TYPE = 'DISSECTION_TYPE'
        if barcode_type and int(barcode_type) not in EXEMPT_NINE_DIGIT_BARCODE_TYPES:
            return True
        else:
            return False

    @pyqtSlot(QVariant, str, result=bool, name='barcodeExists')
    def barcode_exists(self, barcode_type, barcode):
        """
        Observer.db's DISSECTIONS table enforces an unique constraint upon DISSECTION_BARCODE.
        Instead of handling the ConstraintError as an exception when adding a barcode,
        this method may be used to determine if it already exists.

        Only reliable if database access limited to a single thread.

        The field where the barcode is stored depends upon the barcode type:
        - If barcode type is '8' or '9', barcode value is in Dissections.band
        - All other barcodes, barcode value is in Dissections.dissection_barcode

        Constraints imposed:
        1. The database's: for types 1..7, the barcode exists if present in dissection_barcode field
        2. For BandId (8) and ObserverTag (9), the barcode exists if present in BAND_ID for that type.
        I.e. the same barcode value can be used once for BandId and once for ObserverTag and once for the other types.

        :param barcode_type: a text digit, 1..9.
        :param barcode: an integer value as a string
        :return: T: barcode already exists in DISSECTIONS table. F: free to add.
        """
        try:
            if barcode_type == '8' or barcode_type == '9':
                entry = Dissections.get((Dissections.band == barcode) &
                                        (Dissections.dissection_type == barcode_type))
            elif barcode_type and int(barcode_type) in range(1, 12):
                entry = Dissections.get(Dissections.dissection_barcode == barcode)
            else:
                self._logger.error(f"Unrecognized Barcode Type of '{barcode_type}'.")
                return False

            return True

        except Dissections.DoesNotExist as e:
            return False

    @pyqtSlot(str, str, name='save_dissection_type')
    def save_dissection_type(self, dissection_type, barcode):
        """ Save a barcode (dissection types '1' .. '7' or an Observer Tag (dissection type '9').
            All of these types have one value, so create or update the record for that type as needed.
            Dissection Type '8' (existing tag) is not supported because multiple existing tags are allowed;
            throw exception if attempt is use with existing tag
        """
        if barcode is None or dissection_type is None or len(barcode) == 0:
            return
        if dissection_type == '8':
            raise IndexError('save_dissection_type() does not support adding existing tags')
        self._logger.info('Save barcode {}, type {} '.format(barcode, dissection_type))
        try:
            user_id = ObserverDBUtil.get_current_user_id()
            created_date = ObserverDBUtil.get_arrow_datestr()
            new_barcode, created = Dissections.get_or_create(bio_specimen_item=self._current_bio_item.bio_specimen_item,
                                                             dissection_type=dissection_type,
                                                             defaults={'created_by': user_id,
                                                                       'created_date': created_date}
                                                             )
            if dissection_type == '9':
                new_barcode.band = barcode
                self._logger.info(f'Dissection record with a tag entry {"created" if created else "updated"}.')
            else:
                new_barcode.dissection_barcode = barcode
                self._logger.info(f'Dissection record with a barcode entry {"created" if created else "updated"}.')

            new_barcode.save()
        except Exception as e:
            fmt_str = "Attempt to add barcode that already exists ({}). Details: {}"
            exception_msg = fmt_str.format(barcode, e)
            self._logger.error(exception_msg)
            raise IndexError(exception_msg)

    def _get_dissections(self, dissection_type):
        """
        using current biospecimen item ID, load existing dissections
        @return: iterator of Dissections
        """
        try:
            if self._current_bio_item_idx is None or self._current_bio_item is None:
                self._logger.debug('Biospecimen ID not set, aborting load')
                return None

            codes = Dissections.select().where(
                (Dissections.bio_specimen_item == self._current_bio_item.bio_specimen_item) &
                (Dissections.dissection_type == dissection_type))
            return codes

        except Dissections.DoesNotExist as e:
            self._logger.error(e)

        except Exception as e:
            self._logger.error(e)

    def _is_PHLB_wm(self):
        return self._current_weight_method == '9' or self._current_weight_method == '19'

    def _calculate_phlb_weight(self):
        self._total_sample_weight = 0.0
        self._total_sample_count = 0
        weighted_samples = 0
        self._avg_sample_weight = 0.0
        self._tally_count = 0
        for i in self._bio_items_model.items:
            if i['specimen_weight']:
                self._total_sample_weight += i['specimen_weight']
                weighted_samples += 1
            self._total_sample_count += 1
        self._logger.debug('Total weight: {:.2f}'.format(self._total_sample_weight))
        if weighted_samples:
            self._avg_sample_weight = self._total_sample_weight / weighted_samples

        self._tally_count = unweighted_samples = self._total_sample_count - weighted_samples
        # Add unweighted samples * average weight to total
        if unweighted_samples:
            average_tally_total = unweighted_samples * self._avg_sample_weight
            self._total_sample_weight += average_tally_total
            self._logger.debug('Adding tally {} * {:.2f} avg lbs = {:.2f}, total weight now = {:.2f}'.format(
                unweighted_samples, self._avg_sample_weight, average_tally_total,
                self._total_sample_weight
            ))

        if self._is_PHLB_wm():
            self._save_retained_catch_weight_count(self._total_sample_weight, self._total_sample_count)
            self.totalPHLBWeightChanged.emit(self._total_sample_weight)
            self.avgPHLBWeightChanged.emit(self._avg_sample_weight)
            self.tallyCountChanged.emit(self._tally_count)
            self._save_tally_count(self._tally_count)

    @pyqtProperty(QVariant, notify=currentWMChanged)
    def currentWM(self):
        """
        Rely on external QML to set this for us, we don't have direct access to this info
        @return: current weight method str, e.g. "9" or "19" for PHLB
        """
        return self._current_weight_method

    @currentWM.setter
    def currentWM(self, weight_method):
        self._logger.debug('Biospecimens: WM set to {}'.format(weight_method))
        self._current_weight_method = weight_method
        self.currentWMChanged.emit()

    @pyqtProperty(bool, notify=currentWMChanged)
    def isWM9or19(self):
        """
        useful for PHLB
        @return: True if WM is 9 or 19
        """
        if self._current_weight_method == '9' or self._current_weight_method == '19':
            return True
        else:
            return False

    @pyqtProperty(bool, notify=currentWMChanged)
    def isWM19(self):
        """
        useful for PHLB
        @return: True if WM 19
        """
        if self._current_weight_method == '19':
            return True
        else:
            return False

    @pyqtProperty(QVariant, notify=currentPHLBSampleWeightChanged)
    def currentPHLBSampleWeight(self):
        """
        for PHLB
        @return: PHLB weight
        """
        return self._current_phlb_weight

    @pyqtProperty(QVariant, notify=totalPHLBWeightChanged)
    def totalPHLBWeight(self):
        """
        Total weight for PHLB biospecimens
        Lengths * lookup table = weights
        @return: None or floating point calculated value
        """
        return self._total_sample_weight

    @pyqtProperty(QVariant, notify=avgPHLBWeightChanged)
    def avgPHLBWeight(self):
        """
        Average weight for PHLB biospecimens
        @return: None or floating point calculated value
        """
        return self._avg_sample_weight

    @pyqtProperty(int, notify=tallyCountChanged)
    def tallyCount(self):
        """
        Tally count for PHLB biospecimens
        @return: None or floating point calculated value
        """
        return self._tally_count

    @pyqtProperty(QVariant, notify=bioCountChanged)
    def bioCount(self):
        return self._bio_items_model.count if self._bio_items_model else None

    @pyqtProperty(bool, notify=dataExistsChanged)
    def dataExists(self):
        """
        If Biospecimen data exists for current species item
        @return: True if data has been entered, False if clear
        """
        result = self._bio_items_model.count > 0 if self._bio_items_model else False
        self._logger.debug(f'Biospecimen data exists: {result}.')
        return result

    @pyqtSlot(str, result=bool, name='dataWithDiscardReasonExists')
    def data_with_discard_reason_exists(self, discard_reason):
        """
        Unlike property dataExists, this method looks for Biospecimen records
        for the current catch, the current species ID, and the supplied discard_reason.

        :param discard_reason:
        :return: True if Biospecimen record exists for this catch, species, and discard_reason.
        """

        if not self._current_catch or not self._current_catch.catch \
                or not self._current_species or not self._current_species.species:
            self._logger.error('No species selected, return False')
            return False
        catch_id = self._current_catch.catch
        species_id = self._current_species.species

        self._logger.info(
            f'Checking for existing discard data for {discard_reason} for catch {catch_id} and species {species_id}')
        bios_query = BioSpecimens.select().where((BioSpecimens.catch == catch_id) &
                                                 (BioSpecimens.species == species_id) &
                                                 (BioSpecimens.discard_reason == discard_reason))
        result = True if bios_query.count() > 0 else False
        return result

    @pyqtSlot(str, int, result=bool, name='dataWithDRSpeciesExists')
    def data_with_discard_reason_species_exists(self, discard_reason, species_id):
        """
        Unlike property dataExists, this method looks for Biospecimen records
        for the current catch, the specified discard_reason, a specified species ID.

        :param discard_reason:
        :return: True if Biospecimen record exists for this catch, species, and discard_reason.
        """

        catch_id = self._current_catch.catch
        self._logger.info(
            f'Checking for existing discard data for {discard_reason} for catch {catch_id} and species {species_id}')
        bios_query = BioSpecimens.select().where((BioSpecimens.catch == catch_id) &
                                                 (BioSpecimens.species == species_id) &
                                                 (BioSpecimens.discard_reason == discard_reason))
        result = True if bios_query.count() > 0 else False
        return result

    def _save_tally_count(self, tally_value):
        """
        Temporary way to save tally value (can be derived from catch count)
        @param tally_value:
        @return:
        """
        try:
            self._current_bio_specimen.notes = f'OPTECS Tally: {tally_value}'
            self._current_bio_specimen.save()
        except:
            pass

    def _save_retained_catch_weight_count(self, catch_weight, catch_num):
        """
        Save catch weight to CATCHES table, no counts for WM 1,3,6,7,15
        @param catch_weight: weight in lbs
        """
        try:
            catch_id = self._current_catch
            catch = Catches.get(Catches.catch == catch_id)

            catch.catch_weight = float(catch_weight) if catch_weight else None
            if catch.catch_weight_method in CatchCategory.WEIGHT_METHODS_WITH_NO_COUNT:
                self._logger.info(f'Not saving catch count for weight method {catch.catch_weight_method}.')
                catch_num = None
            catch.catch_count = int(catch_num) if catch_num else None
            catch.save()
            self._logger.debug('Saved weight {:.2f}, count {} to catch ID {}'.format(
                catch_weight,
                catch_num,
                catch_id.catch))
        except Exception as e:
            self._logger.warning(e)


    @pyqtSlot(QVariant, QVariant, name="setDiscardReasonSpeciesID")
    def set_discard_reason_species_id(self, dr, species_id):
        catch_id = self._current_catch.catch
        if species_id and dr and catch_id:
            self._logger.debug(f'Changing DR to {dr} for species {species_id} and catch {catch_id}')
            try:
                bio = BioSpecimens.get((BioSpecimens.catch == catch_id) &
                                          (BioSpecimens.species == species_id))
                bio.discard_reason = dr
                bio.save()
                self._logger.info(f'Changed DR to {dr} for species {species_id} and catch {catch_id}')

                # update model
                self._load_bios()
            except BioSpecimens.DoesNotExist as e:
                self._logger.error(e)
                self._logger.error(f'Could not find any biospecimen records to change DR to {dr} for species '
                                   f'{species_id} and catch {catch_id}')
        else:
            self._logger.error('Tried to set DR for species, but missingspecies_id, DR, or catch_id')
