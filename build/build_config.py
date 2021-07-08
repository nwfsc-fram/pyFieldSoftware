
# -----------------------------------------------------------------------------
# Name:        build_config.py
# Purpose:     Central location for build related vars across different field software apps
#
# Author:      Jim Fellows <james.fellows@noaa.gov>
#
# Created:     July 2021
# ------------------------------------------------------------------------------

import os
import fileinput
import re
import sys


def increment_build_number(build_config_path, var_name, do_increment=True) -> str:
    """
    Increment build number.  Assumes format of versioning is MAJOR.MINOR.PATCH+BUILD,
    where each component is an undefined number of digits.  Copied from build_observer,
    but altered to accommodate other app version variables.

    :param build_config_path: relative path to config file where version# lives
    :param var_name: name of python version variable (assumes format VAR_NAME = '')
    :param do_increment: perform increment. For testing, can set this to False
    :return: version string
    """
    if not os.path.exists(build_config_path):
        print(f'*** Unable to increment build #.  Cant find config file {build_config_path}.')
        return ''
    version_info = None
    for i, line in enumerate(fileinput.input(build_config_path, inplace=1)):
        m = re.search(var_name + r' = \"[0-9]*\.[0-9]*\.[0-9]*\+(?P<build_num>[0-9]*)', line)
        if m:
            old_build_num = int(m.group('build_num'))
            if do_increment:
                line = line.replace('+' + str(old_build_num), '+' + str(old_build_num + 1))
            m = re.search(var_name + r' = \"(?P<ver>[0-9]*\.[0-9]*\.[0-9]*\+[0-9]*)', line)
            version_info = m.group('ver')
        sys.stdout.write(line)

    return version_info


if __name__ == '__main__':
    print(increment_build_number('../py/hookandline_hookmatrix/HookMatrixConfig.py', 'HOOKMATRIX_VERSION'))
