# -----------------------------------------------------------------------------
# Name:        ObserverCatchBaskets.py
# Purpose:     Controller for Weight Method 3 use of DB Table CatchAdditionalBaskets and
#              CountsWeightsScreen for capturing catch-level basket data.
#
# Author:      Jim Stearns <jim.stearns@noaa.gov>
#
# Created:     5 May 2017
# License:     MIT
# ------------------------------------------------------------------------------

import logging
from typing import Dict

from PyQt5.QtCore import pyqtProperty, QObject, QVariant, pyqtSignal, pyqtSlot

from py.observer.ObserverCatchBasketsModel import CatchAdditionalBasketsViewModel
from py.observer.ObserverDBModels import CatchAdditionalBaskets, Lookups
from py.observer.ObserverDBUtil import ObserverDBUtil


class ObserverCatchBaskets(QObject):

    additionalWeighedBasketAdded = pyqtSignal(name='additionalWeighedBasketAdded')  # WM3 weighed baskets.
    unusedSignal = pyqtSignal(name='unusedSignal')  # Make QML warning go away

    # "CAB" is acronym for Table CATCH_ADDITIONAL_BASKETS. Use this for LOOKUPS.LOOKUP_TYPE for BASKET_TYPE.
    CAB_BASKET_TYPE_LOOKUP_TYPE = "CAB_BASKET_TYPE"
    # The convention for the LOOKUPS.LOOKUP_VALUE. Used in OPTECS as an integer, but stored as a
    # single digit string in Table LOOKUPS.
    LOOKUP_VALUE_CAB_BASKET_TYPE_UNWEIGHED_FULL = 0
    LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_PARTIAL = 1
    LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_FULL = 2

    def __init__(self, observer_catches):
        """
        
        :param observer_catches: Limited use: Used to determine if current catch's Weight Method is 3.
        """
        super().__init__()
        self._logger = logging.getLogger(__name__)

        self._observer_catches = observer_catches

        ####
        # Set up Table CATCH_ADDITIONAL_BASKETS for use with Weight Method 3 catch weight calculations
        ####

        # Until DB Sync is extended to include CATCHES_ADDITIONAL_BASKETS, it's possible this table
        # may not exist. Create it if it's missing
        if not CatchAdditionalBaskets.table_exists():
            CatchAdditionalBaskets.create_table()
            self._logger.info("Observer DB table CatchAdditionalBaskets doesn't exist. Created.")
        else:
            n_records = CatchAdditionalBaskets.select().count()
            self._logger.info(f"Table CatchAdditionalBaskets exists with {n_records} records.")

        self._catch_additional_baskets_view_model = CatchAdditionalBasketsViewModel(
                sort_role='catch_addtl_baskets', sort_reverse=True)

        # For convenience, build a dictionary of CAB_BASKET_TYPEs extracted from LOOKUPS Table.
        self._catch_additional_basket_types = self._get_catch_additional_basket_types_from_lookup_table()

        # Get signal that current catch has changed
        self._observer_catches.catchIdChanged.connect(self._handle_change_in_current_catch)

    def _handle_change_in_current_catch(self):
        # Update view model of catch additional baskets (used with Weight Method 3 calculation of catch weight)
        self.build_catch_additional_baskets_view_model()
        catch_id = self._current_catch.catch if self._current_catch else "(None)"
        self._logger.info(f"Detected change in Catch ID to {catch_id}.")

    def _get_catch_additional_basket_types_from_lookup_table(self) -> Dict[int, str]:
        """
        The types of additional baskets (unweighed full, weighed partial, weighed full)
        are stored as entries in the LOOKUPS Table with a LOOKUP_TYPE of "CAB_BASKET_TYPE".
        These values will not change during a run of OPTECS. For convenience, load these values
        into a dictionary.
        
        The digits stored in LOOKUPS are of type string. Convert to integer here
        (i.e. the key field of this dictionary is of type integer).
        
        :return: 
        """
        # Provide a backup in case values aren't in LOOKUPS.
        default_dict = {
            ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_UNWEIGHED_FULL: "Unweighed Full Basket",
            ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_PARTIAL: "Weighed Partial Basket",
            ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_FULL: "Weighed Full Basket"
        }

        basket_type_dict = {}
        try:
            cab_lookup_entries = Lookups.select(Lookups.lookup_value, Lookups.description).\
                    where(Lookups.lookup_type == ObserverCatchBaskets.CAB_BASKET_TYPE_LOOKUP_TYPE)
            for entry in cab_lookup_entries:
                basket_type_dict[int(entry.lookup_value)] = entry.description

            if len(basket_type_dict) < len(default_dict):
                self._logger.warning(f"Fewer entries than expected. Using default values.")
                self._logger.warning(f"Entries found in LOOKUPS: {basket_type_dict}.")
                basket_type_dict = default_dict

        except Exception as e:
            self._logger.warning("Could not read DB for CATCH_ADDITIONAL_BASKETS.BASKET_TYPE enumeration. " +
                                 f"Using default. Exception info: {e}.")
            basket_type_dict = default_dict

        self._logger.debug(f"Using these CATCH_ADDITIONAL_BASKET basket_type values: {basket_type_dict}.")
        return basket_type_dict

    @property
    def _current_catch(self):
        return self._observer_catches._current_catch

    @property
    def _weight_method(self):
        return self._observer_catches.weightMethod

    ####
    # Support for CatchAdditionalBaskets - DB access and view model.
    # Used in calculating catch weight with Weight Method 3.
    # * Access to database table CatchAdditionalBaskets for both weighed and unweighed baskets:
    # - Add
    # - Remove
    # - Edit weight (for weighed baskets)
    #
    # * Access to view model of CatchAdditionalBaskets for Weighed Baskets table view in CountsWeightsScreen:
    # - Build weighed baskets model for UI (should be called when catch category changes)
    # - Property for screen to reference model for use in table view.
    ####
    @pyqtProperty(int, notify=unusedSignal)
    def CAB_BASKET_TYPE_WEIGHED_PARTIAL(self) -> int:
        return ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_PARTIAL

    @pyqtSlot(name="buildCatchBasketsViewModel")
    def build_catch_additional_baskets_view_model(self):
        """
        Build a view model for the baskets table view in CatchCategoriesBasketsScreen when Weight Method == 3.
        :return: 
        """
        self._catch_additional_baskets_view_model.clear()
        if self._current_catch is None:
            return

        catch_id = self._current_catch.catch
        baskets_q = CatchAdditionalBaskets. \
            select(). \
            where(CatchAdditionalBaskets.catch == catch_id)

        # Only include weighed baskets - full or partial - in the basket list.
        # I.e. Skip unweighed baskets that are only included in a tally count.
        for basket in baskets_q:
            if basket.basket_type in (ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_PARTIAL,
                                      ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_FULL):
                self._catch_additional_baskets_view_model.add_basket(basket)

        self._logger.debug(f'Loaded {len(baskets_q)} catch additional baskets for catch ID {catch_id}.')

    def _add_additional_basket(self, basket_weight, basket_type):
        """
        Utility for adding weighed and unweighed baskets to CATCH_ADDITIONAL_BASKETS
        for use in WM3 calculation of catch weight.
        
        :param basket_weight: 
        :param basket_type: digit as text.
        :return: 
        """
        if basket_type not in self._catch_additional_basket_types:
            raise Exception(f"Unrecognized catch additional basket type {basket_type}")

        if self._weight_method != '3':
            msg = f"Weight Method is '{self._weight_method}', not '3'; additional baskets not allowed."
            self._logger.error(msg)
            raise Exception(msg)

        # Consistency check: if basket type is unweighed, basket weight should be 0 or None
        if basket_type == ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_UNWEIGHED_FULL and \
                basket_weight is not None and basket_weight != 0.0:
            msg = f"Basket type unweighed should have no or zero basket weight."
            self._logger.error(f"Basket type unweighed should have no or zero basket weight.")
            raise Exception(msg)

        basket_type_description = self._catch_additional_basket_types[basket_type]
        self._logger.debug(f'Add catch additional basket with wt={basket_weight} and '
                           f'type={basket_type_description}.')

        if basket_weight is None:
            basket_weight = 0.0
            self._logger.debug(f"Unweighted baskets will be given weight of 0.0")

        new_basket = None
        try:
            new_basket = CatchAdditionalBaskets.create(
                    catch=self._current_catch.catch,
                    basket_weight=float(basket_weight),
                    basket_type=basket_type,
                    created_by=ObserverDBUtil.get_current_user_id(),
                    created_date=ObserverDBUtil.get_arrow_datestr(date_format=ObserverDBUtil.oracle_date_format)
            )
        except Exception as e:
            self._logger.error(e)
        finally:
            return new_basket

    @pyqtSlot(QVariant, name='addAdditionalWeighedFullBasket')
    def add_additional_weighed_full_basket(self, basket_weight: float):
        """
        Add an entry to CATCH_ADDITIONAL_BASKETS. Used to retain data underlying Weight Method 3 calculation
        of catch weight.
        
        Should only be used if current Weight Method is '3'. Enforced.
        
        :param basket_weight: Allow zero-weight. Since basket_weight column is not nullable in DB Table,
            the value of 0 is used for an unweighed full basket.
        :return: None
        """
        new_basket = self._add_additional_basket(basket_weight,
                                                 ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_FULL)

        # Only add weighed baskets to view model (not unweighed). Same for signal to UI.
        if new_basket is not None:
            self._catch_additional_baskets_view_model.add_basket(new_basket)
            self.additionalWeighedBasketAdded.emit()

    @pyqtSlot(name='addAdditionalUnweighedFullBasket')
    def add_additional_unweighed_full_basket(self):
        """
        A "tally" basket. Loaded full but not weighted. Tally count used in WM3 calculation.
        :return: 
        """
        self._add_additional_basket(0.0, ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_UNWEIGHED_FULL)

        # Don't add unweighed baskets to view model, or send signal to UI.

    def _edit_additional_basket(self, basket_id, basket_weight: float, basket_type: int=None):
        """
        Change one or more non-null fields of an entry in CATCH_ADDITIONAL_BASKETS.
        Since all fields whose change is supported are non-nullable, a value of None indicates:
        don't change field.
        Changes to fields created_date and created_by are not supported - no need as yet.
        
        :param basket_id: Primary key to CATCH_ADDITIONAL_BASKETS
        :param basket_weight: as a float
        :param basket_type: as an integer
        :return: 
        """
        if not basket_id:
            self._logger.error(f"Passed a null id for CatchAdditionalBaskets. Taking no action.")
            return

        if basket_weight is None and basket_type is None:
            self._logger.info(f"Neither basket_weight nor basket_type specified. Taking no action.")
            return

        if self._weight_method != '3':
            msg = f"Weight Method is '{self._weight_method}', not '3';" \
                  f"editing additional baskets not allowed."
            self._logger.error(msg)
            raise Exception(msg)

        # Consistency check: if requested basket type is unweighed,
        # requested basket weight should be 0 or None
        if basket_type == ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_UNWEIGHED_FULL and \
                basket_weight is not None and basket_weight != 0.0:
            msg = f"Basket type unweighed should have no or zero basket weight."
            self._logger.error(f"Basket type unweighed should have no or zero basket weight.")
            raise Exception(msg)

        try:
            basket_q = CatchAdditionalBaskets.get(CatchAdditionalBaskets.catch_addtl_baskets == basket_id)
            weight_modified_msg = ""
            type_modified_msg = ""
            if basket_weight is not None:
                basket_q.basket_weight = basket_weight
                weight_modified_msg = f"Weight={basket_weight}"
            if basket_type is not None:
                # Note: Changing a basket from unweighed to weighed or vice versa is not allowed.
                basket_q.basket_type = basket_type  # DB type is integer
                type_modified_msg = f"Basket Type={basket_type}"
            basket_q.save()
            self._logger.debug(f"Updates to catch additional basket ID {basket_id}: " +
                               weight_modified_msg + " " + type_modified_msg)

            # Update view model containing weighed baskets (full or partial)
            if basket_q.basket_type in (ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_FULL,
                                        ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_PARTIAL):
                idx = self._catch_additional_baskets_view_model.get_item_index('catch_addtl_baskets',
                                                                               basket_id)
                if idx >= 0:
                    if basket_weight is not None:
                        self._catch_additional_baskets_view_model.setProperty(
                                idx, 'basket_weight', basket_weight)
                        self._logger.debug(f"Basket ID {basket_id}'s view model weight={basket_weight}.")
                    if basket_type is not None:
                        self._catch_additional_baskets_view_model.setProperty(
                                idx, 'basket_type', basket_type)
                        self._logger.debug(f"Basket ID {basket_id}'s view model type="
                                           f"{self._catch_additional_basket_types[basket_type]}.")

        except CatchAdditionalBaskets.DoesNotExist as e:
            self._logger.error(e)

    @pyqtSlot(QVariant, QVariant, name='setAdditionalWeighedBasketAsPartial')
    def set_additional_weighed_basket_as_partial(self, basket_id, mark_as_partial):
        """
        Changed a weighed catch additional basket from partial to full or vice versa.
        Must be a weighed basket - not an unweighed basket. All unweighed baskets are full.
        :param basket_id:
        :param mark_as_partial: 
        :return: 
        """
        basket_type = ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_PARTIAL if mark_as_partial \
            else ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_FULL
        self._edit_additional_basket(basket_id, None, basket_type)

    @pyqtSlot(QVariant, QVariant, name='setAdditionalBasketWeight')
    def set_additional_basket_weight(self, basket_id, basket_weight):
        self._edit_additional_basket(basket_id, basket_weight)

    @pyqtSlot(QVariant, name='removeAdditionalBasket')
    def remove_additional_basket(self, basket_id):
        """
        While this method can be used for either weighed or unweighed (tally) baskets, it's intended for use
        with weighed baskets. With unweighed baskets, any entry can be removed - it doesn't matter which -
        so it's easier to use remove_an_additional_unweighed_full_basket() (no basket id needed).
        
        :param basket_id: 
        :return: None
        """
        if not basket_id:
            self._logger.error(f"Passed a null id for CatchAdditionalBaskets. Taking no action.")
            return

        if self._weight_method != '3':
            msg = f"Weight Method is '{self._weight_method}', not '3'; removing additional baskets not allowed."
            self._logger.error(msg)
            raise Exception(msg)

        try:
            basket_q = CatchAdditionalBaskets.get(CatchAdditionalBaskets.catch_addtl_baskets == basket_id)
            basket_q.delete_instance()
            self._logger.debug(f"Deleted catch additional basket ID {basket_id} from database.")

            # Remove from view model - if a weighed basket. Unweighed baskets aren't added to view,
            # so won't be found here (i.e. idx < 0).
            idx = self._catch_additional_baskets_view_model.get_item_index('catch_addtl_baskets', basket_id)
            if idx >= 0:
                self._catch_additional_baskets_view_model.remove(idx)
                self._logger.debug(f"Deleted catch additional weighed basket ID {basket_id} from view model.")
            else:
                if basket_q.basket_type in (ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_PARTIAL,
                                            ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_FULL):
                    self._logger.error(f"Error looking up catch additional basket ID {basket_id} in view model")
            return
        except CatchAdditionalBaskets.DoesNotExist as e:
            self._logger.error(e)
            return

    @pyqtSlot(name='removeAnAdditionalUnweighedFullBasket')
    def remove_an_additional_unweighed_full_basket(self):
        """
        Use in Weight Method 3 data entry to reduce the tally of unweighed baskets by one.
        
        Remove one unweighed catch additional basket. Since the only purpose of these entries is to maintain
        a tally of unweighed baskets, and there's no data of interest other than the basket_type being unweighed,
        the implementation may remove any unweighed entry.
        
        Should not be called if no unweighed baskets are present, but in that case doesn't throw exception -
        just logs error message and returns.
        :return: 
        """
        try:
            # Get the first (earliest?) record for this catch with an unweighed basket type.
            basket_q = CatchAdditionalBaskets.get(
                    (CatchAdditionalBaskets.catch == self._current_catch.catch) &
                    (CatchAdditionalBaskets.basket_type == ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_UNWEIGHED_FULL))
            basket_q.delete_instance()
            self._logger.debug(
                    f"WM3: Deleted an unweighed catch additional basket for Catch ID {self._current_catch.catch}.")
        except CatchAdditionalBaskets.DoesNotExist:
            self._logger.error("WM3: No unweighed baskets to remove.")

    @pyqtProperty(QVariant, notify=unusedSignal)
    def CatchAdditionalBasketsViewModel(self):
        return self._catch_additional_baskets_view_model

    @pyqtProperty(QVariant, notify=unusedSignal)
    def countOfUnweighedCatchAdditionalBaskets(self):
        """
        :return: The number of unweighed catch additional baskets for the current catch.
        """
        if self._current_catch is None:
            self._logger.debug("No catch, no catch additional baskets")
            return 0
        self._logger.debug(f"Current catch ID is {self._current_catch.catch}.")
        try:
            basket_q = CatchAdditionalBaskets.select().where(
                    (CatchAdditionalBaskets.catch == self._current_catch.catch) &
                    (CatchAdditionalBaskets.basket_type == ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_UNWEIGHED_FULL))
            self._logger.info(f"Found {basket_q.count()} unweighed (tallied) catch additional baskets " +
                              f"for Catch ID {self._current_catch.catch}.")
            return basket_q.count()
        except CatchAdditionalBaskets.DoesNotExist:
            self._logger.debug("No unweighed catch additional baskets found for Catch ID {self._current_catch.catch.")
            return 0

    @pyqtProperty(QVariant, notify=unusedSignal)
    def hasWM3BasketData(self):
        """
        :return: True if any weighed or unweighed data for the current catch in Table CATCH_ADDITIONAL_BASKETS.
        """
        if self._current_catch is None:
            self._logger.debug("No catch, no catch additional baskets")
            return False

        try:
            basket_q = CatchAdditionalBaskets.select().where(CatchAdditionalBaskets.catch == self._current_catch.catch)
            self._logger.info(f"Found {basket_q.count()} weighed or unweighed (tallied) catch additional baskets " +
                              f"for Catch ID {self._current_catch.catch}.")
            return basket_q.count() > 0
        except CatchAdditionalBaskets.DoesNotExist:
            self._logger.debug("No catch additional baskets found for Catch ID {self._current_catch.catch}.")
            return False

    @pyqtSlot(result=QVariant, name='getWM3CatchValues')
    def get_WM3_catch_values(self) -> Dict[str, QVariant]:
        """
        Get all the Weight Method 3 information needed to display catch weight and its components.
        
        :return: Values are returned as float or int, not text.
        """
        if self._current_catch is None:
            return {}

        n_weighed_full_baskets = 0
        weighed_full_total_weight = 0.0
        n_weighed_partial_baskets = 0
        weighed_partial_total_weight = 0.0
        n_unweighed_baskets = 0

        baskets_q = CatchAdditionalBaskets.select().where(CatchAdditionalBaskets.catch == self._current_catch.catch)
        for basket in baskets_q:
            if basket.basket_type == ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_UNWEIGHED_FULL:
                n_unweighed_baskets += 1
            elif basket.basket_type == ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_PARTIAL:
                n_weighed_partial_baskets += 1
                weighed_partial_total_weight += basket.basket_weight
            elif basket.basket_type == ObserverCatchBaskets.LOOKUP_VALUE_CAB_BASKET_TYPE_WEIGHED_FULL:
                n_weighed_full_baskets += 1
                weighed_full_total_weight += basket.basket_weight
            else:
                self._logger.error(f"Unrecognized catch_type {basket.basket_type}. Ignored.")

        wm3_dict = {
            'N_WEIGHED_FULL_BASKETS': n_weighed_full_baskets,
            'WEIGHED_FULL_TOTAL_WEIGHT': weighed_full_total_weight,
            'N_WEIGHED_PARTIAL_BASKETS': n_weighed_partial_baskets,
            'WEIGHED_PARTIAL_TOTAL_WEIGHT': weighed_partial_total_weight,
            'N_UNWEIGHED_BASKETS': n_unweighed_baskets
        }
        return wm3_dict

