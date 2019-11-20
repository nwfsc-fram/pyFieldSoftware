# -----------------------------------------------------------------------------
# Name:        ObserverUtility.py
# Purpose:     General purpose utility methods
#
# Author:      Jim Stearns <james.stearns@noaa.gov>
#
# Created:     17 Oct 2017
# License:     MIT
# ------------------------------------------------------------------------------
import sys

class ObserverUtility:
    @staticmethod
    def platform_is_windows():
        """
        Is OPTECS running on a Windows platform? (Typically the case)
        """
        # Even 64-bit Windows returns 'win32', for compatibility reasons
        # (https://stackoverflow.com/questions/23956229/i-have-a-win7-64bits-os-but-the-value-of-sys-platform-is-win32-why)
        return sys.platform == 'win32'
