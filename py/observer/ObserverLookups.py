# ObserverLookups.py - Helper classes for LOOKUPS table

import textwrap

from py.observer.ObserverDBModels import Lookups, Species


class CatchVals:
    """
    Static values for DB
    """
    WeightUM = 'LB'
    DispRetained = 'R'
    DispDiscarded = 'D'


class WeightMethodDescs:
    """
    Build dict of weight method descriptions
    TODO: could be static
    """

    def __init__(self):
        self._trawl_wm_descs = None
        self._fg_wm_descs = None
        self.load_weight_methods()

    def load_weight_methods(self):
        self._trawl_wm_descs = dict()
        wmd_q = Lookups.select().where(Lookups.lookup_type == 'TRAWL_WEIGHT_METHOD')
        self._trawl_wm_descs = {wm.lookup_value: textwrap.fill(wm.description, 20) for wm in wmd_q}

        self._fg_wm_descs = dict()
        fg_wmd_q = Lookups.select().where(Lookups.lookup_type == 'FG_WEIGHT_METHOD')
        self._fg_wm_descs = {wm.lookup_value: textwrap.fill(wm.description, 20) for wm in fg_wmd_q}

    @property
    def wm_trawl_descriptions(self):
        return self._trawl_wm_descs

    @property
    def wm_fg_descriptions(self):
        return self._fg_wm_descs


class SampleMethodDescs:
    """
    Build dict of sample method descriptions
    TODO: could be static
    """

    def __init__(self):
        self._sm_descs = dict()
        smd_q = Lookups.select().where(Lookups.lookup_type == 'SC_SAMPLE_METHOD')
        self._sm_descs = {sm.lookup_value: sm.description for sm in smd_q}

    @property
    def sm_descriptions(self):
        return self._sm_descs

class RockfishHandlingDescs:
    """
    Dict of rockfish handling short codes and descriptions
    """

    def __init__(self):
        self._rf = dict()  # translate code to description
        self._rfc = []  # list of codes
        rf_q = Lookups.select().where(Lookups.lookup_type == 'ROCKFISH_HANDLING')
        self._rf = {rf.lookup_value: rf.description for rf in rf_q}
        self._rfc = (rf.lookup_value for rf in rf_q)

    @property
    def release_method_codes(self):
        return self._rfc

    @property
    def release_methods_desc(self):
        return self._rf


class RockfishCodes:
    """
    Dict of rockfish handling short codes and descriptions
    """

    def __init__(self):
        # SELECT SPECIES_CODE, COMMON_NAME FROM SPECIES WHERE SPECIES_SUB_CATEGORY = 104 AND ACTIVE IS NOT 0
        rf_q = Species\
            .select(Species.species_code, Species.common_name)\
            .where((Species.species_sub_category == 104) &
                   (Species.active.is_null(True) | Species.active == 1))
        self._rockfish_codes = [r.species_code for r in rf_q]

    @property
    def codes(self):
        return self._rockfish_codes
