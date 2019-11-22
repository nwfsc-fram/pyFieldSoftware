# Method to test the rezipping of files
from buildzipper import buildzipper
deployed_path = 'build\exe.win64-3.6'
buildzipper.create_zip_changes_only_archive(base_folder=deployed_path, filedesc='trawl_analyzer')