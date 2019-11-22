# cx_freeze build script
# Written with cx-Freeze==4.3.4

# Outputs by default to build\exe.win32-3.4\
# Note: will NOT delete anything in that directory
# Modify path_platforms as required

# Usage:
# build_trawl_analyzer.py build

from buildzipper import buildzipper

# Prompt to nuke existing directory
deployed_path = r'build\exe.win64-3.6\trawl_analyzer'

# Zip up our creation
buildzipper.create_zip_archive(base_folder=deployed_path, filedesc='trawl_analyzer', folders_to_zip=['trawl_analyzer/trawl_analyzer.exe', 'trawl_analyzer/py'])
