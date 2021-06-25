# -----------------------------------------------------------------------------
# Name:        ObserverConfig.py
# Purpose:     Hold global variables to be shared across all modules of the OPTECS program.
#
# Author:      Jim Stearns <james.stearns@noaa.gov>
#
# Created:     March 2017
# License:     MIT
# ------------------------------------------------------------------------------

"""
OPTECS VERSION STRING

The convention for the OPTECS version string follows the standard proposed by
Semantic Versioning 2.0.0 (http://semver.org/#semantic-versioning-200) -
the standard three major, minor, and patch fields, plus a field for an incrementing
build number.

From semver:cdi

"Given a version number MAJOR.MINOR.PATCH, increment the:

* MAJOR version when you make incompatible API changes,
* MINOR version when you add functionality in a backwards-compatible manner, and
* PATCH version when you make backwards-compatible bug fixes.

"Additional labels for pre-release and build metadata are available as extensions to the MAJOR.MINOR.PATCH format."

Paragraph 10 of the semver standard allows a build metadata field to be appended to these three fields,
separated with a plus sign (not a period).

The OPTECS version string convention is:

    <Major>.<Minor>.<Patch>+<BuildNumber>

BuildNum may increase independently of the first three fields. The simplest convention for build number
is to have the build system auto-increment the build number with each build.

The justification for including a build number: it is useful when supporting apps in the field to know
that each build has a unique version string which could be used to bring up the source tree
as it stood for that particular build.  
"""

optecs_version = "2.1.3+24"

# Number of floating point decimal places to display for weight etc.
display_decimal_places = 2

# Configuration values relating to trip comment constraints.
# Constraint #1: All comments go into one field - that trip's Trips.notes field, whose maximum is 4000 characters.
# Constraint #2: The unhandled exception handler will attempt to write a trip comment before exiting.
#               Reserve space for this possible comment so that it gets uploaded to Center servers on a DB sync upload.

max_text_size_trips_note_field = 4000
max_text_size_unhandled_exception_comment = 400
max_text_size_observer_comments = max_text_size_trips_note_field - max_text_size_unhandled_exception_comment

use_encrypted_database = True
