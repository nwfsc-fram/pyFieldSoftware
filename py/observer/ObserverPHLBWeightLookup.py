# -----------------------------------------------------------------------------
# Name:        ObserverPHLBWeightLookup.py
# Purpose:     Preload lookups for PHLB lengths to weights
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Nov 22, 2016
# License:     MIT
# ------------------------------------------------------------------------------

from py.observer.ObserverDBModels import SpeciesCorrelation


class PHLBCorrelation:
    """
    Correlations for PHLB: Length in CM -> weight in LBS (?)
    """

    def __init__(self):
        phlb_species_id = 10141
        correlation_q = SpeciesCorrelation.select(SpeciesCorrelation.length, SpeciesCorrelation.weight).where(
            (SpeciesCorrelation.species == phlb_species_id))

        self._correlations = {int(c.length): c.weight for c in correlation_q}

    def get_weight(self, length: int):
        """
        Get PHLB weight from given integer length
        @param length: length in CM
        @return: None if out of range, else corresponding weight
        """
        if length in self._correlations.keys():
            return self._correlations[length]
        return None
