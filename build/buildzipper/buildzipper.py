# -------------------------------------------------------------------------------
# Name:        buildzipper.py
# Purpose:     Zip up files in a subdirectory
#
# Author:      Todd Hay
# Updated:	   Will Smith
# Email:       Todd.Hay@noaa.gov, Will.Smith@noaa.gov
#
# Created:     Oct 24, 2014
# Updated:     March 24, 2016
# License:     MIT
# -------------------------------------------------------------------------------
import os
import zipfile
import argparse
import time

__author__ = 'Todd.Hay'


def zipfolders(folders_to_zip, zipf):

    for folder in folders_to_zip:
        print('\tZipping: ', folder)
        if os.path.isdir(folder):
            if folder == '.git' or folder == '__pycache__':
                continue
            for base, dirs, files in os.walk(folder):
                if folder == 'py' and base[-11:] == '__pycache__':
                    print('\t\tSkipping:', base)
                    continue
                for file in files:
                    zipf.write(os.path.join(base, file))

        elif os.path.isfile(folder):
            zipf.write(folder)


def create_zip_archive(base_folder, filedesc, outdir=r'dist', folders_to_zip=['.'], version=None):
    """
    If you want to create a new zipped bundle that only contains the python changes (and this assumes
    that you haven't added in any new python or QML packages), then you can pass in a value for the
    folders_to_zip parameter.  For instance, for the Trawl Analyzer software, this would be:
    
    folders_to_zip=['trawl_analyzer/trawl_analyzer.exe', 'trawl_analyzer/py']

    This creates a drastically reduced package (in size), making it easier to deploy to remote users.  Note that you want to be sure that the QRC > py file has been generated as a precursor, otherwise you might have made changes in your QML files, but they won't get reflected until the pyrcc has actually run to compile those into a qrc.py file    
    """

    if not os.path.exists(outdir):
        os.mkdir(outdir)

    if version:
        date = time.strftime('%Y%m%d')
        output_file = os.path.join(outdir, filedesc + '_' + date + '_v' + version + '.zip')
    else:
        date_time = time.strftime('%Y%m%d_%H%M')
        output_file = os.path.join(outdir, filedesc + '_' + date_time + '.zip')
    zipf = zipfile.ZipFile(output_file, 'w', compression=zipfile.ZIP_DEFLATED)
    current_folder = os.getcwd()
    os.chdir(base_folder)

    if folders_to_zip != ['.']:
        base_paths = base_folder.split(os.sep)
        app_path = base_paths[-1]
        new_folders = list()
        for f in folders_to_zip:
            zip_paths = os.path.normpath(f).split(os.sep)
            print('zip_paths: ', zip_paths)
            if zip_paths[0] == app_path:
                new_folders.append('\\'.join(zip_paths[1:]))
        folders_to_zip = new_folders

    print('Zipping folder: ', base_folder)
    zipfolders(folders_to_zip, zipf)
    zipf.close()
    os.chdir(current_folder)
    print('Created ' + output_file)
    return output_file


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Zip files in default output directory')

    parser.add_argument("-i", "--indir", help="Input Directory", default='exe.win32-3.4')
    parser.add_argument("-o", "--outdir", help="Output Directory", type=str, default=r"build\dist/")
    parser.add_argument("-f", "--filename", help="Base Output Filename", type=str, default="build")

    args = parser.parse_args()

    if not os.path.exists(args.outdir):
        print('Creating ' + str(args.outdir))
        os.mkdir(args.outdir)

    out_file = create_zip_archive(base_folder=args.indir, filedesc=args.filename, outdir=args.outdir)

    print('Distribution is bundled in ', out_file)
