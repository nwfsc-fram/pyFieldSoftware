import os
import logging
import re
import apsw
from playhouse.shortcuts import model_to_dict
import arrow
from glob import glob

from py.hookandline.HookandlineFpcDB_model import Lookups, Operations, Catch, OperationAttributes, Notes, \
    CatchContentLu, Specimen, HookMatrixImport, CutterStationImport, SpecimenImport, SpeciesSamplingPlanLu,\
    ProtocolLu, JOIN


class SensorDBIntegrityChecker():

    def __init__(self):
        super().__init__()

    def check_databases(self):
        """
        Check all of the sensor databases to ensure that they are not malformed
        :return:
        """
        year = "2017"
        path = r"\\nwcfile\FRAM\Data\HookAndLineSurvey"
        master_fldr = os.path.join(path, year, "1_processed_data")

        master_fldr = r"C:\Users\Todd.Hay\Desktop\AG_DB"
        # master_fldr = r"C:\Users\Todd.Hay\Desktop\TO_DB"
        # master_fldr = r"C:\Users\Todd.Hay\Desktop\MI_DB"
        search_str = r'sensors_.*\.(db)$'
        sql = "PRAGMA integrity_check;"

        if os.path.exists(master_fldr):

            files = [x for x in os.listdir(master_fldr) if re.search(search_str, x)]
            for j, file in enumerate(files):
                # if j == 1:
                #     break

                db_path = os.path.join(master_fldr, file)
                conn = apsw.Connection(db_path)
                conn.setbusytimeout(10000)
                cursor = conn.cursor()
                result = cursor.execute(sql).fetchall()

                logging.info(f"{file} > {result[0][0]}")

            return

            for i, dir in enumerate(os.walk(master_fldr)):
                if i == 0:
                    continue
                folder = dir[0].split('\\')[-1]
                files = [x for x in dir[2] if re.search(search_str, x)]
                # logging.info(f"{folder}:  {files}")
                logging.info(f"{folder}")

                for j, file in enumerate(files):
                    # if j == 1:
                    #     break

                    db_path = os.path.join(master_fldr, folder, file)
                    conn = apsw.Connection(db_path)
                    conn.setbusytimeout(10000)
                    cursor = conn.cursor()
                    result = cursor.execute(sql).fetchall()
                    logging.info(f"\t\t{file} > {result}")



if __name__ == '__main__':

    # Create main app
    log_fmt = '%(levelname)s:%(filename)s:%(lineno)s:%(message)s'
    logging.basicConfig(level=logging.DEBUG, filename='HookLogger.log', format=log_fmt, filemode='w')

    logger = logging.getLogger("peewee")
    logger.setLevel(logging.WARNING)

    # Also output to console (stderr)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter(log_fmt)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    ic = SensorDBIntegrityChecker()
    ic.check_databases()
