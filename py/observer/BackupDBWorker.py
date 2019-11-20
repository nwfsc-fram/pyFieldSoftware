# -----------------------------------------------------------------------------
# Name:        BackupDBWorker.py
# Purpose:     Backup observer DB (encrypted only) to an external drive.
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Sept 29, 2017
# License:     MIT
# ------------------------------------------------------------------------------

import filecmp
import os
import shutil
import arrow
import glob
import zipfile

from PyQt5.QtCore import pyqtSignal, QObject
from py.observer.ObserverConfig import use_encrypted_database


class BackupDBWorker(QObject):
    """
    Class to copy encrypted DB without locking up UI
    """
    backupStatus = pyqtSignal(bool, str)  # Success/Fail, Result Description

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.dest_path = kwargs["dest_path"]
        self._is_running = False

    def zip_logs(self, log_files, outdir):
        """
        If you want to create a new zipped bundle that only contains the python changes (and this assumes
        that you haven't added in any new python or QML packages), then you can pass in a value for the
        folders_to_zip parameter.  For instance, for the Trawl Analyzer software, this would be:

        folders_to_zip=['trawl_analyzer/trawl_analyzer.exe', 'trawl_analyzer/py']

        This creates a drastically reduced package (in size), making it easier to deploy to remote users.  Note that you want to be sure that the QRC > py file has been generated as a precursor, otherwise you might have made changes in your QML files, but they won't get reflected until the pyrcc has actually run to compile those into a qrc.py file
        """

        if not os.path.exists(outdir):
            raise FileNotFoundError('Log zip error: Cannot find target directory ' + outdir)

        output_file = os.path.join(outdir, 'optecs_logs.zip')

        # print('Zipping', log_files, 'to', output_file)

        zipf = zipfile.ZipFile(output_file, 'w', compression=zipfile.ZIP_DEFLATED)
        for f in log_files:
            zipf.write(f)
        zipf.close()

    def run(self):
        self._is_running = True
        try:
            # Copy Database
            db_filename = 'observer_encrypted.db' if use_encrypted_database else 'observer.db'
            source_file = os.path.join(os.getcwd(), 'data\\' + db_filename)
            if not os.path.isfile(source_file):
                self.backupStatus.emit(False, f'Could not find {source_file}. Abort.')
                return
            if not os.path.isdir(self.dest_path):
                os.makedirs(self.dest_path)
            date_str = arrow.now().format('YYYYMMDD')
            log_filename = f'OptecsEncryptedBackup_{date_str}.db'
            dest_full_path = os.path.join(self.dest_path, log_filename)

            shutil.copyfile(source_file, dest_full_path)
            if not filecmp.cmp(source_file, dest_full_path):
                err_msg = f'File compare failed.\nCopied file likely has errors.\nTry new media.'
                self.backupStatus.emit(False, err_msg)

            # Zip log files
            log_file_current = glob.glob('*.log')
            log_file_arch = glob.glob('log_archive/*.log')
            self.zip_logs(log_file_current + log_file_arch, self.dest_path)

            self._is_running = False
            self.backupStatus.emit(True, f'SUCCESS: Copied {dest_full_path} + logs')
        except Exception as e:
            self.backupStatus.emit(False, f'ERROR: {e}')
