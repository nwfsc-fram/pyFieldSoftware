import os
import sys
import logging
from urllib import request
import shutil
import re
from datetime import datetime
from dateutil import parser

from py.hookandline.HookandlineFpcDB_model import database, TideStations, TideMeasurements
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model


class HarvestTidesData:

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db
        self.base_url = r'http://tidesandcurrents.noaa.gov/noaatidepredictions/NOAATidesFacade.jsp?datatype=Annual+Txt&Stationid='

    def get_tides_listing(self):

        app_dir = os.path.abspath(os.path.dirname(__file__))
        data_dir = os.path.normpath(os.path.join(app_dir, "..\..", "data", "hookandline"))
        tides_dir = os.path.join(data_dir, "tides")
        tide_file = os.path.join(data_dir, "TideStations.txt")

        if not os.path.isfile(tide_file):
            logging.error("File does not exist: {0}".format(tide_file))
            sys.exit(0)

        f = open(tide_file, 'r')
        tide_stations = f.read().split('\n')
        f.close()

        return tide_stations

    def retrieve_data(self):

        tide_stations = self.get_tides_listing()
        app_dir = os.path.abspath(os.path.dirname(__file__))
        data_dir = os.path.normpath(os.path.join(app_dir, "..\..", "data", "hookandline"))
        tides_dir = os.path.join(data_dir, "tides")

        for i, station in enumerate(tide_stations):

            try:

                url = self.base_url + station
                local_file, headers = request.urlretrieve(url)
                print('{0} > {1}'.format(station, local_file))
                shutil.move(local_file, os.path.join(tides_dir, station + ".txt"))

            except Exception as ex:

                print('failed to download: {0}'.format(station))

    def insert_tide_stations(self):
        """
        Method to insert the newly retrieved tide stations into the SQLite database
        :return:
        """
        tide_stations = self.get_tides_listing()

        app_dir = os.path.abspath(os.path.dirname(__file__))
        data_dir = os.path.normpath(os.path.join(app_dir, "..\..", "data", "hookandline"))
        tides_dir = os.path.join(data_dir, "tides")

        # for file in [f for f in os.listdir(tides_dir) if re.search(r'.*\.(hex|raw|asc|cnv)$', f)]:
        for file_name in [f for f in os.listdir(tides_dir) if re.search(r'(\d{7}|TWC\d{4}).txt', f)]:
            # if i == 1:
            #     break

            tide_file = os.path.join(tides_dir, file_name)
            f = open(tide_file, 'r')
            for line in f.read().split('\n'):
                if re.search(r'^StationName:', line):
                    station_name = line.replace("StationName:", "").strip()
                if "Stationid:" in line:
                    station_id = line.replace("Stationid:", "").strip()
                if "State:" in line:
                    state = line.replace("State:", "").strip()
                if "Time Zone:" in line:
                    time_zone = line.replace("Time Zone:", "").strip()
                if "Datum:" in line:
                    datum = line.replace("Datum:", "").strip()
                    break

            TideStations\
                .insert(station_name=station_name, station=station_id, state=state, time_zone=time_zone, datum=datum)\
                .execute()

            print(station_name, station_id, state, time_zone, datum)

            f.close()

    def insert_tidal_measurements(self):
        """
        Method to insert the yearly high and low tide information
        :return:
        """
        app_dir = os.path.abspath(os.path.dirname(__file__))
        data_dir = os.path.normpath(os.path.join(app_dir, "..\..", "data", "hookandline"))
        tides_dir = os.path.join(data_dir, "tides")

        data = []

        for i, file_name in enumerate([f for f in os.listdir(tides_dir) if re.search(r'(\d{7}|TWC\d{4}).txt', f)]):
            # if i == 1:
            #     break


            data_start_row = -1
            station_id = file_name.strip('.txt')

            print('{0}'.format(station_id))

            try:

                del data[:]
                tide_station_id = TideStations.get(station=station_id).tide_station
                f = open(os.path.join(tides_dir, file_name), 'r')
                lines = f.read().split('\n')
                for line in lines:

                    if data_start_row != -1:
                        elements = list(filter(bool, line.split('\t')))
                        if len(elements) == 0:
                            continue

                        del elements[1] # Remove the day  of the week value, we don't need it
                        elements[0] = parser.parse(elements[0]).strftime("%m/%d/%Y")
                        elements[1] = parser.parse(elements[1]).strftime("%H:%M:%S")
                        elements[2] = float(elements[2])
                        elements[3] = float(elements[3])
                        data.append({"tide_station": tide_station_id,
                                     "date": elements[0],
                                     "time": elements[1],
                                     "prediction_ft": elements[2],
                                     "prediction_cm": elements[3],
                                     "high_or_low": elements[4]})

                        continue

                    if "Date" in line and "Day" in line and "Time" in line and "Pred(Ft)" in line:
                        data_start_row = i+1

                f.close()

                # Insert into the database
                chunk_size = 100
                with database.atomic():
                    for idx in range(0, len(data), chunk_size):
                        TideMeasurements.insert_many(data[idx:idx + chunk_size]).execute()

            except Exception as ex:
                print('Error: {0}'.format(ex))
                logging.info('Error getting the tide station: {0}'.format(station_id))

if __name__ == '__main__':

    h = HarvestTidesData()

    # Retrieve data from NOAA Tides and Currents
    # h.retrieve_data()

    # Insert Tide Stations into the Database
    # h.insert_tide_stations()

    # Update Tide Stations with Latitude/Longitude Values (from separate CSV file

    # Insert Tidal Measurements into the Database
    h.insert_tidal_measurements()