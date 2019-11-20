import os
import sys
import logging
import csv
from py.hookandline.HookandlineFpcDB_model import database, TideStations, Sites


class SiteManager:

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

    def import_sites(self):
        """
        Method to import sites from a csv file and insert itnto the database
        :return:
        """
        app_dir = os.path.abspath(os.path.dirname(__file__))
        data_dir = os.path.normpath(os.path.join(app_dir, "..\..", "data", "hookandline"))
        sites_file = os.path.join(data_dir, "sites.csv")
        if not os.path.isfile(sites_file):

            return

        f = open(sites_file, 'r')
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:

                continue

            lat_items = row[2].split(' ')
            lat = int(lat_items[0]) + float(lat_items[1]) / 60
            lon_items = row[3].split(' ')
            lon = int(lon_items[0]) + float(lon_items[1]) / 60
            try:
                tide_station_id = TideStations.get(station_name=row[4]).tide_station
                Sites.insert(name=row[0], is_active=row[1], latitude=lat, longitude=lon,
                             tide_station=tide_station_id, area_description=row[5],
                             is_cowcod_conservation_area=row[6]).execute()
                print('{0} > {1} > {2}'.format(row[0], tide_station_id, row))

            except Exception as ex:
                Sites.insert(name=row[0], is_active=row[1], latitude=lat, longitude=lon,
                             area_description=row[5],
                             is_cowcod_conservation_area=row[6]).execute()
                print('{0} > {1}'.format(row[0], row))
        f.close()

if __name__ == '__main__':

    sm = SiteManager()

    # Import sites
    sm.import_sites()