# -----------------------------------------------------------------------------
# Name:        HookandlineFPCConfig.py
# Purpose:     Hold global variables to be shared across all modules of the HookLogger program.
#
# Author:      Jim Fellows <james.fellows@noaa.gov>
#
# Created:     July 2021
# ------------------------------------------------------------------------------
"""
The convention for version string follows the standard proposed by
Semantic Versioning 2.0.0 (http://semver.org/#semantic-versioning-200) -
the standard three major, minor, and patch fields, plus a field for an incrementing
build number.  Because this software is released annually, the major version represents the calendar
year (see https://calver.org/#scheme) for a more intuitive version number.

From semver:cdi

"Given a version number MAJOR.MINOR.PATCH, increment the:

* MAJOR version when you make incompatible API changes,
* MINOR version when you add functionality in a backwards-compatible manner, and
* PATCH version when you make backwards-compatible bug fixes.

"Additional labels for pre-release and build metadata are available as extensions to the MAJOR.MINOR.PATCH format."

Paragraph 10 of the semver standard allows a build metadata field to be appended to these three fields,
separated with a plus sign (not a period).

The HookMatrix version string convention is:

    <Major>.<Minor>.<Patch>+<BuildNumber>

BuildNum may increase independently of the first three fields. The simplest convention for build number
is to have the build system auto-increment the build number with each build.

The justification for including a build number: it is useful when supporting apps in the field to know
that each build has a unique version string which could be used to bring up the source tree
as it stood for that particular build.
"""

HOOKLOGGER_VERSION = "2021.0.0+2"