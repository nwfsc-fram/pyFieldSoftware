# -----------------------------------------------------------------------------
# Name:        CountsWeights.py
# Purpose:     Support class for Counts and Weights (Observer)
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Jan 24, 2016
# License:     MIT
# ------------------------------------------------------------------------------

import logging
from decimal import *

from PyQt5.QtCore import pyqtProperty, QVariant, QObject, pyqtSignal, pyqtSlot

from peewee import fn
from py.observer.ObserverBasketsModel import ObserverBasketsModel
from py.observer.ObserverData import ObserverData
from py.observer.ObserverDBModels import CatchAdditionalBaskets, SpeciesCompositionItems, SpeciesCompositionBaskets, \
    Trips, FishingActivities, Catches, Species, SpeciesCompositions
from py.observer.ObserverDBUtil import ObserverDBUtil


class CountsWeights(QObject):
    modelChanged = pyqtSignal(name='modelChanged')
    basketAdded = pyqtSignal(name='basketAdded')
    avgWeightChanged = pyqtSignal(QVariant, name='avgWeightChanged')
    speciesWeightChanged = pyqtSignal(QVariant, name='speciesWeightChanged')
    extrapolatedWeightChanged = pyqtSignal(QVariant, name='extrapolatedWeightChanged')
    speciesFishCountChanged = pyqtSignal(QVariant, QVariant, name='speciesFishCountChanged')
    actualWeightChanged = pyqtSignal(QVariant, name='actualWeightChanged')
    wm15RatioChanged = pyqtSignal(QVariant, name='wm15RatioChanged')
    discardReasonSelected = pyqtSignal(QVariant, name='discardReasonSelected')
    dataExistsChanged = pyqtSignal(name='dataExistsChanged')  # Only used in CC Details, so usually polled
    totalTallyChanged = pyqtSignal(QVariant, name='totalTallyChanged')  # for Trawl WM8?
    tallyFishCountChanged = pyqtSignal(QVariant, name='tallyFishCountChanged')
    tallyFGFishCountChanged = pyqtSignal(QVariant, name='tallyFGFishCountChanged')
    tallyTimesAvgWeightChanged = pyqtSignal(QVariant, name='tallyTimesAvgWeightChanged')
    tallyAvgWeightChanged = pyqtSignal(QVariant, name='tallyAvgWeightChanged')
    recalculateRetainedFishAvg = pyqtSignal()
    subsampleCountChanged = pyqtSignal(QVariant, arguments=['ct'])
    subsampleWeightChanged = pyqtSignal(QVariant, arguments=['wt'])
    subsampleAvgChanged = pyqtSignal(QVariant, arguments=['avg'])
    subsampleAvgModeChanged = pyqtSignal(QVariant, arguments=['mode'])
    unusedSignal = pyqtSignal()

    def __init__(self, observer_species):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._observer_species = observer_species
        self._observer_species.calculateTotalsForDrChange.connect(self._calculate_totals)
        
        # weight metrics
        self._species_weight = None
        self._total_tally = None
        self._extrapolated_species_weight = None
        self._species_fish_count = None
        self._extrapolated_species_fish_count = None
        self._tally_table_fish_count = None
        self._tally_fg_fish_count = None  # This is stored in the DB at species comp level

        self._actual_weight = None
        self._avg_weight = None
        self._subsample_weight = None
        self._subsample_count = None
        self._subsample_avg_weight = None
        self._subsample_avg_mode = None
        self._weighted_baskets = 0

        self._current_species_comp_item = None
        self._baskets_model = ObserverBasketsModel()

        self._wm15_ratio = 1.0
        self._current_weight_method = None
        self._is_fixed_gear = False

    @pyqtSlot(name='reset')
    def reset(self):
        """
        Clear CW data, reset states
        """
        self._current_species_comp_item = None
        self._wm15_ratio = 1.0
        self._clear_counts_and_weights()
        self.emit_calculated_weights()


    def _clear_counts_and_weights(self):
        self._avg_weight = None
        if not self._is_fixed_gear:  # subsample funcs only on trawl
            self.subsampleWeight = None  # use pyqtProperty to trigger setter
            self.subsampleCount = None  # use pyqtProperty to trigger setter
            self._subsample_avg_weight = None
        self._species_weight = None
        self._species_fish_count = None
        self._total_tally = None
        self._extrapolated_species_weight = None
        self._extrapolated_species_fish_count = None
        self._actual_weight = None
        self._tally_fg_fish_count = None
        self._weighted_baskets = 0
        if self._baskets_model:
            self._baskets_model.clear()
        # self.dataExistsChanged.emit()

    @pyqtProperty(bool, notify=unusedSignal)
    def isPaperEntry(self):
        return ObserverDBUtil.get_setting('current_collection_method', None) == 'FormsEntryOnly'

    @pyqtSlot(name="speciesIsNotCounted", result=bool)
    def _is_mixed_species(self):
        return True if self._current_species_comp_item and \
                       self._current_species_comp_item.species and \
                       self._current_species_comp_item.species.pacfin_code == ObserverData.MIX_PACFIN_CODE \
                    else False

    def _build_baskets_model(self):
        if self._current_species_comp_item is None:
            self._clear_counts_and_weights()
            self.emit_calculated_weights()
            return

        if self._is_mixed_species():
            self._logger.debug("Building ObserverBasketsModel from species MIX catch baskets.")
            current_catch_id = self._current_species_comp_item.species_composition.catch.catch
            baskets_q = CatchAdditionalBaskets. \
                select(). \
                where(CatchAdditionalBaskets.catch == current_catch_id)
        else:
            self._logger.debug("Building ObserverBasketsModel from a normal (non-MIX) species species comp baskets.")

            baskets_q = SpeciesCompositionBaskets. \
                select(). \
                where(SpeciesCompositionBaskets.species_comp_item == self._current_species_comp_item)

        self._baskets_model.clear()
        for basket in baskets_q:
            self._baskets_model.add_basket(basket)

        self._logger.debug('Loaded {} baskets.'.format(len(baskets_q)))

        try:
            self._current_weight_method = self._current_species_comp_item.species_composition.catch.catch_weight_method
            self._wm15_ratio = self._get_wm15_ratio()
        except Exception as e:
            self._logger.error(e)

        self._calculate_totals()

    def _get_wm15_ratio(self):
        """
        Check if we are weight method 15, and if so, set ratio other than 1.
        @return:
        """
        is_wm15 = self._current_weight_method == '15'
        if self._current_species_comp_item and is_wm15:
            notes = self._current_species_comp_item.species_composition.catch.notes
            wm15_ratio = ObserverDBUtil.get_current_catch_ratio_from_notes(notes)
            if wm15_ratio:
                self._logger.debug('Got WM15 ratio from DB: {}'.format(wm15_ratio))
                return wm15_ratio

        return 1.0

    @pyqtProperty(QVariant, notify=modelChanged)
    def BasketsModel(self):
        return self._baskets_model

    @pyqtSlot(QVariant, QVariant, name='addBasket')
    def addBasket(self, weight, count):
        return self._add_species_basket(weight, count) if not self._is_mixed_species() \
                else self._add_catch_basket(weight)  # Catch baskets don't store count

    def _add_species_basket(self, weight, count):
        """
        Add species comp item to DB and model
        Check for 0-weight basket
        @param weight: lbs
        @param count: fish num
        """
        self._logger.debug('Add species basket. wt: {}, ct: {}'.format(weight, count))
        if self._current_species_comp_item is None:
            self._logger.error('Species ID / Current Species Comp ID is None')
            return

        try:
            new_basket = SpeciesCompositionBaskets.create(
                    species_comp_item=self._current_species_comp_item,
                    basket_weight_itq=weight,
                    fish_number_itq=count,
                    created_by=ObserverDBUtil.get_current_user_id(),
                    # FIELD-2087: Using default dateformat for time display; reformat before sync later
                    created_date=ObserverDBUtil.get_arrow_datestr(date_format=ObserverDBUtil.default_dateformat),
                    is_fg_tally_local=1 if self._is_fixed_gear else None,
                    is_subsample=None
            )
            self._baskets_model.add_basket(new_basket)
            self._logger.info(f'Added basket wt: {weight} ct: {count}')

        finally:
            self._calculate_totals()
            self.basketAdded.emit()
            # self.dataExistsChanged.emit()

    def _add_catch_basket(self, weight):
        """
        Used only for special-case species MIX, a pseudo-species whose use indicates the basket data
        should be added to catch-level bucket, CATCH_ADDITIONAL_BASKETS rather than to a species-specific
        bucket, SPECIES_COMP_BASKETS.

        Add basket item to DB and model.

        Note: CATCH_ADDITIONAL_BASKETS does not have a field for count.

        @param weight: lbs
        """
        self._logger.debug(f'Add catch (not species) basket. wt: {weight}')
        # Get the current catch and exit if not defined
        current_catch_id = self._current_species_comp_item.species_composition.catch.catch
        if current_catch_id is None:
            self._logger.error('Catch ID is None')
            return

        if weight is None:
            weight = 0.0

        try:
            new_basket = CatchAdditionalBaskets.create(
                    catch=current_catch_id,
                    basket_weight=weight,
                    created_by=ObserverDBUtil.get_current_user_id(),
                    # FIELD-2087: Using default dateformat for time display; reformat before sync later
                    created_date=ObserverDBUtil.get_arrow_datestr(date_format=ObserverDBUtil.default_dateformat),
            )
            self._baskets_model.add_basket(new_basket)
            self._logger.info(f'Added addl basket wt: {weight}')

        finally:
            self._calculate_totals()
            self.basketAdded.emit()
            # self.dataExistsChanged.emit()

    @pyqtSlot(QVariant, QVariant, name='editBasketWeight')
    def editBasketWeight(self, basket_id, weight):
        self._edit_basket(basket_id, weight=weight)

    @pyqtSlot(QVariant, QVariant, name='editBasketCount')
    def editBasketCount(self, basket_id, count):
        self._edit_basket(basket_id, count=count)

    @pyqtSlot(QVariant, QVariant, name='editBasketSubsample')
    def editBasketSubsample(self, basket_id, flag):
        self._edit_basket(basket_id, is_subsample=flag)

    @pyqtProperty(QVariant, notify=subsampleWeightChanged)
    def subsampleWeight(self):
        """
        FIELD-1471: sum weight of actual fish weighed from baskets flagged as subsample (trawl only)
        :return: int
        """
        return self._subsample_weight

    @subsampleWeight.setter
    def subsampleWeight(self, wt):
        """
        FIELD-1471: if changed, set var, recalculate avg, and emit val
        :param wt: float
        :return: None (emit float)
        """
        if self._subsample_weight != wt or not self._subsample_weight:
            self._subsample_weight = wt
            self._calculate_subsample_avg()
            self.subsampleWeightChanged.emit(wt)
            self._logger.info(f"Subsample wt set to {wt}")

    @pyqtProperty(QVariant, notify=subsampleCountChanged)
    def subsampleCount(self):
        """
        FIELD-1471: Count of actual fish counted from baskets flagged as subsample (trawl only)
        :return: int
        """
        return self._subsample_count

    @subsampleCount.setter
    def subsampleCount(self, ct):
        """
        FIELD-1471: If changed, set var, recalculate avg, and emit val
        :param ct: count of fish from subsample baskets
        :return: None (emit int)
        """
        if self._subsample_count != ct or not self._subsample_count:
            self._subsample_count = ct
            self._calculate_subsample_avg()
            self.subsampleCountChanged.emit(ct)
            self._logger.info(f"Subsample ct set to {ct}")

    @pyqtProperty(QVariant, notify=subsampleAvgChanged)
    def subsampleAvgWeight(self):
        """
        FIELD-1471: See _calculate_subsample_avg; divides _subsample_weight by _subsample_count
        :return: float
        """
        return self._subsample_avg_weight

    @subsampleAvgWeight.setter
    def subsampleAvgWeight(self, avg):
        """
        FIELD-1471: if changed, set var amd emit val
        :param avg: float
        :return: None (emit float)
        """
        if self._subsample_avg_weight != avg or not self._subsample_avg_weight:
            self._subsample_avg_weight = avg
            self.subsampleAvgChanged.emit(self._subsample_avg_weight)
            self._logger.info(f'Subsample avg weight set to {self._subsample_avg_weight}')

    @pyqtProperty(QVariant, notify=subsampleAvgModeChanged)
    def subsampleAvgMode(self):
        """
        FIELD-1471: Set to true IF (trawl only)
            subsample count > trawl_subsample_count_threshold (param in SETTINGS) 75 by default &
            No actual fish counts have been entered &
            A daily subsample avg for the relevant species is available
        IF true, count of basket is extrapolated using the daily subsample avg
        :return: bool
        """
        return self._subsample_avg_mode

    @subsampleAvgMode.setter
    def subsampleAvgMode(self, mode):
        """
        FIELD-1471: set during _calculate_totals.
        If changed, emit bool
        :param mode: bool
        :return: None (emit bool)
        """
        if self._subsample_avg_mode != mode:
            self._subsample_avg_mode = mode
            self.subsampleAvgModeChanged.emit(mode)

    def _calculate_subsample_avg(self):
        """
        FIELD-1471: get subsample avg fish weight
        Catch if dividing by zero, or numerator or denominator is None
        :return: None, set subsample avg (val is then emitted)
        """
        try:
            self.subsampleAvgWeight = self._subsample_weight / self._subsample_count
            self._logger.info(f"Calculating subsample avg: {self._subsample_weight}/{self._subsample_count}")
        except (TypeError, ZeroDivisionError) as e:
            self.subsampleAvgWeight = None

    def _calculate_subsample_weight(self):
        """
        FIELD-1471: get rounded avg weight of fish in same day as haul (using created_date of current haul)
        species_list is usually single current species_id (except for hardcoded complexes in function def)
        :return: sets float val _todays_avg_weight (exposed as todaysAvgWeight property)
        """
        trip_id = ObserverDBUtil.get_current_trip_id()
        species_list = self._observer_species.get_related_species(self._observer_species.currentSpeciesItemSpeciesID)
        haulset_date = ObserverDBUtil.get_current_haulset_createddate()

        if not haulset_date or not species_list or not trip_id:
            self.logger.error(f"haulset_date/species/trip list not retrieved, can't calculate subsample weight")

        self._logger.info(f"Daily subsample weight calc'd, species {species_list} day {haulset_date[:10]} trip {trip_id}")

        self.subsampleWeight = Trips.select(
            fn.sum(SpeciesCompositionBaskets.basket_weight_itq)
        ).join(
            FishingActivities
        ).join(
            Catches, on=FishingActivities.fishing_activity == Catches.fishing_activity
        ).join(
            SpeciesCompositions
        ).join(
            SpeciesCompositionItems
        ).join(
            SpeciesCompositionBaskets
        ).join(
            Species, on=SpeciesCompositionItems.species == Species.species  # no rel_model in model def...
        ).where(
            (Trips.trip == trip_id) &
            (Species.species.in_(species_list)) &
            (fn.substr(SpeciesCompositionBaskets.created_date, 1, 10) == fn.substr(haulset_date, 1, 10)) &
            (SpeciesCompositionBaskets.is_subsample == 1)
        ).scalar()

    def _calculate_subsample_count(self):
        """
        FIELD-1471: get rounded avg weight of fish in same day as haul (using created_date of current haul)
        :return: sets float val _todays_avg_weight (exposed as todaysAvgWeight property)
        """
        trip_id = ObserverDBUtil.get_current_trip_id()
        species_list = self._observer_species.get_related_species(self._observer_species.currentSpeciesItemSpeciesID)
        haulset_date = ObserverDBUtil.get_current_haulset_createddate()

        if not haulset_date or not species_list or not trip_id:
            self.logger.error(f"haulset_date/species/trip list not retrieved, can't calculate subsample count")

        self._logger.info(f"Daily subsample count calc'd, species {species_list} day {haulset_date[:10]} trip {trip_id}")

        self.subsampleCount = Trips.select(
            fn.sum(SpeciesCompositionBaskets.fish_number_itq)
        ).join(
            FishingActivities
        ).join(
            Catches, on=FishingActivities.fishing_activity == Catches.fishing_activity
        ).join(
            SpeciesCompositions
        ).join(
            SpeciesCompositionItems
        ).join(
            SpeciesCompositionBaskets
        ).join(
            Species, on=SpeciesCompositionItems.species == Species.species  # no rel_model in model def...
        ).where(
            (Trips.trip == trip_id) &
            (Species.species.in_(species_list)) &
            (fn.substr(SpeciesCompositionBaskets.created_date, 1, 10) == fn.substr(haulset_date, 1, 10)) &
            (SpeciesCompositionBaskets.is_subsample == 1)
        ).scalar()

    def _edit_basket(self, basket_id, **kwargs):
        """
        Edit one or more properties of a basket, either in species composition baskets or catch additional baskets.
        @param basket_id: basket row id
        @param kwargs: weight, count
        """
        if not basket_id:
            self._logger.warning('Invalid basket ID {}, cannot set {}'.format(basket_id, kwargs))
            return
        set_weight = 'weight' in kwargs.keys()
        set_count = 'count' in kwargs.keys()
        set_subsample = 'is_subsample' in kwargs.keys()

        try:
            basket_q = self._get_basket_db_item(basket_id)
            # Both weight and count can be empty string. Map empty string to zero.
            count = None
            ss_flag = None
            if set_weight:
                weight = float(kwargs['weight']) if kwargs['weight'] else None
                if not self._is_mixed_species():
                    basket_q.basket_weight_itq = weight  # Type REAL in DB
                    self._logger.debug(f"Setting weight for species basket weight {basket_id} to {weight}.")
                else:
                    basket_q.basket_weight = weight  # Type REAL in DB
                    self._logger.debug(f"Setting weight for catch basket weight {basket_id} to {weight}.")
                self._logger.info(f'Edit basket wt: {weight}')

            if set_count and not self._is_mixed_species():  # No count field in CatchAdditionalBaskets
                count = int(kwargs['count']) if kwargs['count'] else 0
                basket_q.fish_number_itq = count  # Type INTEGER in DB
                self._logger.info(f'Edit basket ct: {count}')

            if set_subsample:
                ss_flag = int(kwargs['is_subsample']) if kwargs['is_subsample'] else 0
                basket_q.is_subsample = ss_flag
                self._logger.info(f'is_subsample flag set to {ss_flag}')

            basket_q.save()

            idx = self._baskets_model.get_item_index('basket_primary_key', basket_id)
            if idx >= 0:
                # Convention: roles in ObserverBasketsModels use the SpeciesCompositionBaskets field names.
                if set_weight:
                    self._baskets_model.setProperty(idx, 'basket_weight_itq', weight)  # FloatField in model
                if set_count and not self._is_mixed_species():
                    self._baskets_model.setProperty(idx, 'fish_number_itq', count)  # IntegerField in model
                if set_subsample:
                    self._baskets_model.setProperty(idx, 'is_subsample', ss_flag)  # IntegerField in model
            else:
                self._logger.error('Error looking up basket_primary_key in model.')
        except (SpeciesCompositionBaskets.DoesNotExist, CatchAdditionalBaskets.DoesNotExist) as e:
            self._logger.error(e)
            return
        except TypeError as e:
            self._logger.error('Error setting property {}: {}'.format(kwargs, e))
            return
        finally:
            self._calculate_totals()

    @pyqtSlot(QVariant, name='deleteBasket')
    def deleteBasket(self, basket_id):
        """ Delete a basket entry from SPECIES_COMPOSITION_BASKETS (overwhelmingly typical case)
            or from CATCH_ADDITIONAL_BASKETS (when the basket is for OPTECS-only pseudo-species MIX).
        """
        affected_table = "CATCH_ADDITIONAL_BASKETS" if self._is_mixed_species() else "SPECIES_COMPOSITION_BASKETS"
        self._logger.debug(f"Deleting entry {basket_id} from {affected_table}")
        try:
            basket_q = self._get_basket_db_item(basket_id)
            basket_q.delete_instance()
            self._logger.info(f'Deleted basket ID {basket_id}')
            idx = self._baskets_model.get_item_index('basket_primary_key', basket_id)
            if idx >= 0:
                self._baskets_model.remove(idx)
            else:
                self._logger.error('Error looking up catch_additional_basket to delete in model')
        except (SpeciesCompositionBaskets.DoesNotExist, CatchAdditionalBaskets.DoesNotExist) as e:
            self._logger.error(e)
            return
        finally:
            self._calculate_totals()

    def _get_basket_db_item(self, basket_id):
        if self._is_mixed_species():
            basket_q = CatchAdditionalBaskets.get(CatchAdditionalBaskets.catch_addtl_baskets == basket_id)
        else:
            basket_q = SpeciesCompositionBaskets.get(SpeciesCompositionBaskets.species_comp_basket == basket_id)
        return basket_q

    def _calculate_totals(self):
        """
        Calculate average and total fish weights
        """

        self._species_weight = None
        self._total_tally = None
        self._extrapolated_species_weight = None
        self._avg_weight = None
        self._species_fish_count = None
        self._extrapolated_species_fish_count = None
        self._tally_table_fish_count = None
        self._weighted_baskets = 0

        weighted_baskets = 0
        species_fish_count = 0
        species_extrapolated_count = 0
        species_counted_weight = 0.0  # weights that have a count, for averaging
        species_weight = 0.0
        extrapolated_species_weight = 0.0
        species_unweighted_count = 0
        tally_fish_count = 0

        if self._current_weight_method is None:
            self._logger.warning('WM not set, not calculating totals')
            return
        else:
            self._logger.debug('Calculate totals starting for WM {}'.format(self._current_weight_method))

        # noinspection PyBroadException
        try:
            for i in range(self._baskets_model.count):  # can't iterate, so just step through
                cur_wt = self._baskets_model.get(i)['basket_weight_itq']
                cur_fish_count = self._baskets_model.get(i)['fish_number_itq']

                if cur_wt is not None and cur_wt > 0:
                    self._weighted_baskets += 1
                    species_weight += cur_wt

                    if cur_fish_count is not None and cur_fish_count > 0:
                        species_fish_count += cur_fish_count
                        species_counted_weight += cur_wt

                elif cur_fish_count is not None:  # Unweighted fish - WM 8
                    species_unweighted_count += cur_fish_count

        except Exception as e:
            self._logger.error('Invalid weight/count data in DB, skipping calculations: {}'.format(e))
            return

        self._tally_table_fish_count = species_unweighted_count + species_fish_count
        self._species_fish_count = species_fish_count

        if self._weighted_baskets == 0:  # Didn't find any weight data
            self._species_weight = self._extrapolated_species_weight = self._actual_weight = self._avg_weight = None
            self.emit_calculated_weights()
            return

        self._species_weight = self._extrapolated_species_weight = self._actual_weight = species_weight

        if species_fish_count > 0:
            try:
                self._avg_weight = species_counted_weight / float(species_fish_count)
            except ZeroDivisionError:
                self._avg_weight = None
        else:
            self._avg_weight = None
            # self._logger.warning('No basket counts, not calculating avg weight.')

        try:
            if self._current_weight_method == '15':
                tmp_ex = (Decimal(self._species_weight) /
                          Decimal(self._wm15_ratio)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
                self._extrapolated_species_weight = float(tmp_ex)
            elif self._current_weight_method == '8':
                ex_wt = float(Decimal(Decimal(species_unweighted_count) *
                                      Decimal(self._avg_weight)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
                self._logger.info(
                    'WM8 adding to extrapolated weight: {} * {}'.format(species_unweighted_count, self._avg_weight))
                extrapolated_species_weight += self._species_weight + ex_wt
                self._extrapolated_species_weight = extrapolated_species_weight
                # Question: Should tally for WM8 be included in species_fish_count?
                # FIELD-1403: Including tally count in count incorrectly triggers TC1897. Don't.
                self._species_fish_count = species_fish_count
                # Save tally to species db entry
                self._total_tally = species_unweighted_count
                self._logger.info(f"WM8: species_fish_number={self._species_fish_count}, " +
                                  f"total tally={self._total_tally}.")
        except TypeError as e:
            self._logger.error(e)
            pass

        # Now that we recalculated average fish weight, calculate extrapolated counts
        # noinspection PyBroadException
        if not self.isFixedGear:
            self._calculate_subsample_weight()
            self._calculate_subsample_count()

            # use subsample avg extrapolation when species avg wt exists, tot basket ct is 0, and subsample ct > thresh
            count_threshold = ObserverDBUtil.get_setting('trawl_subsample_count_threshold', 75)
            if not self._species_fish_count and self._subsample_avg_weight and self._subsample_count > int(count_threshold) and not self.isPaperEntry:
                self.subsampleAvgMode = True
            else:
                self.subsampleAvgMode = False

            try:
                for i in range(self._baskets_model.count):  # can't iterate, so just step through
                    cur_wt = self._baskets_model.get(i)['basket_weight_itq']
                    cur_fish_count = self._baskets_model.get(i)['fish_number_itq']

                    indiv_extrapolated_number = Decimal(0)
                    if cur_wt and not cur_fish_count and self._subsample_avg_mode:  # extrapolate count with subsample
                        indiv_extrapolated_number = Decimal(cur_wt) / Decimal(self._subsample_avg_weight)
                        self._logger.info(f'Count for basket {i} using SUBSAMPLE avg = {indiv_extrapolated_number}')
                    elif cur_wt and self._avg_weight and not cur_fish_count:
                        indiv_extrapolated_number = Decimal(cur_wt) / Decimal(self._avg_weight)
                        self._logger.info(f'Count for basket {i} using OTHER avg = {indiv_extrapolated_number}')
                    indiv_extrapolated_number = float(indiv_extrapolated_number.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
                    self._baskets_model.setProperty(i, 'extrapolated_number', indiv_extrapolated_number)
                    species_extrapolated_count += indiv_extrapolated_number
            except Exception as e:
                self._logger.warning('Skipping extrapolated count calculation: {}'.format(e))

            self._logger.info('Extrapolated count calculation: {}'.format(species_extrapolated_count))
            self._extrapolated_species_fish_count = round(self._species_fish_count + species_extrapolated_count)
            if self._subsample_avg_mode == 1:
                note = f'SPECIES_NUMBER=WEIGHT/SUBSAMPLE_AVG={species_weight}/{round(self._subsample_avg_weight, 2)}'
                self._observer_species.species_comp_item_notes = note
            elif self._extrapolated_species_fish_count:
                note = f'SPECIES_NUMBER=(NO_COUNT_WEIGHT/FISH_AVG)+ACTUAL_COUNT=(' \
                       f'{species_weight - species_counted_weight}/{ObserverDBUtil.round_up(self._avg_weight)})+{species_fish_count}'
                self._observer_species.species_comp_item_notes = note

            if self._current_weight_method == '8' and self._total_tally is not None:
                self._logger.info(f"WM8: Adding total tally {self._total_tally} to extrapolated " +
                                   f"fish count of {self._extrapolated_species_fish_count}")
                self._extrapolated_species_fish_count += int(self._total_tally)
            self._logger.info(f'Extrapolated count: {self._extrapolated_species_fish_count},'
                               f' wt: {self._extrapolated_species_weight}')

        if self.isFixedGear:
            self._updateFGTallyCalculations(self._tally_fg_fish_count)
        self.emit_calculated_weights()

    def emit_calculated_weights(self):
        self.avgWeightChanged.emit(self._avg_weight)
        self.actualWeightChanged.emit(self._actual_weight)
        # Pass both the extrapolated total fish count as well the the tally count in the
        # FishCountChanged signal so that receiver can display the extrapolated count to the screen
        # but can also exclude a WM8 tally count from DB's SpeciesCompositionItems.species_number.
        self.tallyFGFishCountChanged.emit(self._tally_fg_fish_count)
        self.tallyFishCountChanged.emit(self._tally_table_fish_count)
        self.speciesWeightChanged.emit(self._species_weight)
        self.tallyTimesAvgWeightChanged.emit(self.tallyTimesAvgWeight)  # ws - is this FG only?
        if not self.isFixedGear:
            self.speciesFishCountChanged.emit(self._extrapolated_species_fish_count, self._total_tally)
            self.extrapolatedWeightChanged.emit(self._extrapolated_species_weight)
        self.totalTallyChanged.emit(self._total_tally)


    @pyqtProperty(QVariant, notify=avgWeightChanged)
    def avgWeight(self):
        """
        Average fish weight across all baskets in current haul
        @return: None or floating point calculated value
        """
        return self._avg_weight

    @pyqtProperty(QVariant, notify=speciesWeightChanged)
    def speciesWeight(self):
        """
        Total fish weight across all baskets in current haul
        @return: None or floating point calculated value
        """
        return self._species_weight

    @pyqtProperty(QVariant, notify=extrapolatedWeightChanged)
    def extrapolatedSpeciesWeight(self):
        """
        Extrapolated species weight
        @return: None or floating point calculated value
        """
        return self._extrapolated_species_weight

    @pyqtProperty(QVariant, notify=speciesFishCountChanged)
    def speciesFishCount(self):
        """
        Total fish count + extrapolated count across all baskets in current haul
        @return: None or floating point calculated value
        """
        return self._extrapolated_species_fish_count

    @pyqtProperty(QVariant, notify=tallyFishCountChanged)
    def tallyFishCount(self):
        """
        Total fish count across all baskets in current haul
        @return: None or floating point calculated value
        """
        return self._tally_table_fish_count

    @pyqtProperty(QVariant, notify=tallyFGFishCountChanged)
    def tallyFGFishCount(self):
        """
        Total fish count across all baskets in current haul
        @return: None or floating point calculated value
        """
        return self._tally_fg_fish_count if self._tally_fg_fish_count is not None else 0

    @tallyFGFishCount.setter
    def tallyFGFishCount(self, count: int):
        if not self.isFixedGear:
            return
        self._logger.debug(f'Tally FG count now {count}')
        try:
            self._tally_fg_fish_count = count
            self._updateFGTallyCalculations(int(count))
            self._calc_and_propage_species_comp()
        except Exception as e:  # catch CHK
            pass

    def _updateFGTallyCalculations(self, count: int):
        if not self.isFixedGear:
            return

        if self._current_species_comp_item:
            self._species_fish_count = count
            self._tally_fg_fish_count = count
            self._species_weight = self.tallyTimesAvgWeight
            self._logger.info(f'FG * {count} wt: {self.tallyTimesAvgWeight}')
            self._current_species_comp_item = self.currentSpeciesCompItem
            self._current_species_comp_item.species_number = count if count else None
            self._current_species_comp_item.total_tally = count if count else None
            self._current_species_comp_item.species_weight = self.tallyTimesAvgWeight if self.tallyTimesAvgWeight else None
            self._current_species_comp_item.species_weight_um = 'LB'
            # NOTE extrapolated_species_weight is used for Trawl only. For FG, species_weight is extrapolated.
            self._current_species_comp_item.save()
            # Send signals to propagate UI updates for other tables etc (e.g. Species tab)
            self.tallyFGFishCountChanged.emit(count)
            self.tallyTimesAvgWeightChanged.emit(self._species_weight)
            self.tallyAvgWeightChanged.emit(self.avgWeight)
        else:
            self._logger.error('No SC item set, cant save tally')

    @pyqtProperty(QVariant, notify=tallyFGFishCountChanged)
    def tallyTimesAvgWeight(self):
        # FIELD-1900: avoid nulling out weight for DR 12 and 15 with null avg (avg from retained will be used)
        if self._observer_species.discardReason in ['12', '15'] and self._weighted_baskets == 0:
            self._logger.info(f"DR12/15 without baskets, not calculating species weight with avg val = {self.avgWeight}")
            return self._current_species_comp_item.species_weight
        elif self.avgWeight and self.tallyFGFishCount:
            val = Decimal(self.avgWeight) * Decimal(self.tallyFGFishCount)
            round_val = val.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
            # https://stackoverflow.com/questions/56820/round-doesnt-seem-to-be-rounding-properly#56833
            return float(round_val)
        else:
            return None

    @pyqtSlot(QVariant)
    def addToTallyFGCount(self, count):
        """
        Add cout to fixed gear tally
        :param count:
        :return:
        """
        if count is None:
            return

        tmp = self.tallyFGFishCount
        if tmp + int(count) < 0:  # subtraction
            self.tallyFGFishCount = 0
        else:
            self.tallyFGFishCount += count

    @pyqtProperty(QVariant, notify=actualWeightChanged)
    def actualWeight(self):
        """
        Total fish weight across all baskets in current haul
        @return: None or floating point calculated value
        """
        return self._actual_weight

    @pyqtProperty(QVariant, notify=totalTallyChanged)
    def totalTally(self):
        """
        Total tally count for species
        @return: None or floating point calculated value
        """
        return self._total_tally

    @pyqtProperty(QVariant, notify=wm15RatioChanged)
    def wm15Ratio(self):
        """
        Ratio for weight method 15 (WM 15)
        @return:
        """
        return self._wm15_ratio

    @wm15Ratio.setter
    def wm15Ratio(self, value):
        if value:
            self._wm15_ratio = value
        else:
            self._wm15_ratio = 1.0
        self._calculate_totals()
        self.wm15RatioChanged.emit(self._wm15_ratio)

    @pyqtProperty(int)
    def currentSpeciesCompItem(self):
        if self._current_species_comp_item:
            current_id = self._current_species_comp_item.species_comp_item
            ## update and return
            self._current_species_comp_item = SpeciesCompositionItems.get(
                SpeciesCompositionItems.species_comp_item == current_id)
            return self._current_species_comp_item  # .species_comp_item  # _id
        else:
            return None

    @currentSpeciesCompItem.setter
    def currentSpeciesCompItem(self, item_id):
        if item_id is None:
            self._current_species_comp_item = None
            self._clear_counts_and_weights()
            self.emit_calculated_weights()
            self._logger.debug('Cleared')
        else:
            try:
                self._current_species_comp_item = SpeciesCompositionItems.get(
                    SpeciesCompositionItems.species_comp_item == item_id)
                species_name = self._current_species_comp_item.species.common_name
                self._clear_counts_and_weights()
                # self.emit_calculated_weights()

                self.tallyFGFishCount = self._current_species_comp_item.species_number
                self._logger.debug('Set species comp item id {} ({})'.format(item_id, species_name))
            except SpeciesCompositionItems.DoesNotExist as e:
                self._logger.warning('{}'.format(e))

        self._build_baskets_model()

    @pyqtProperty(bool, notify=dataExistsChanged)
    def dataExists(self):
        """
        If Counts/Weights (basket) data exists for current species item
        @return: True if data has been entered, False if clear
        """
        result = self._baskets_model.count > 0 if self._baskets_model else False
        self._logger.debug('Data exists: {}'.format(result))
        return result

    @pyqtSlot(int, result=bool, name='anyCCDataExists')
    def anyCCDataExists(self, cc_id):
        """
        If Counts/Weights (basket) data exists for current catch category
        @return: True if data has been entered, False if clear
        """
        sci_q = SpeciesCompositionItems.select().where(
            SpeciesCompositionItems.species_composition == cc_id)
        count = sci_q.count()
        self._logger.info(f'Checking for data in CC {cc_id}: {count} species comp items')
        for s in sci_q:
            if s.species_weight:
                return True

        return False

    @pyqtProperty(QVariant, notify=unusedSignal)
    def isFixedGear(self):
        return self._is_fixed_gear

    @isFixedGear.setter
    def isFixedGear(self, is_fixed):
        self._is_fixed_gear = is_fixed


    def _calc_and_propage_species_comp(self):
        # Set KP values in SPECIES_COMPOSITIONS and sum into CATCHES
        all_species_comp_item_q = SpeciesCompositionItems.\
            select().\
            where(self._current_species_comp_item.species_composition.species_composition ==
                  SpeciesCompositionItems.species_composition)

        total_number = 0
        total_weight = 0
        for item in all_species_comp_item_q:
            if item.species_number:
                total_number += item.species_number
            if item.species_weight:
                total_weight += item.species_weight

        self._logger.info(f'SC Data {total_number} @ {total_weight} LBS')

        self._current_species_comp_item = self.currentSpeciesCompItem
        self._current_species_comp_item.species_composition.species_weight_kp = total_weight
        self._current_species_comp_item.species_composition.species_number_kp = total_number
        self._current_species_comp_item.species_composition.save()

