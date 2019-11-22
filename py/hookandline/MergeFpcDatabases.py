import os
import logging
from playhouse.shortcuts import model_to_dict
from playhouse.migrate import *
import arrow
from peewee import PeeweeException
from collections import OrderedDict

from py.hookandline.HookandlineFpcDB_model import Lookups, Operations, Catch, OperationAttributes, Notes, \
    CatchContentLu, Specimen, HookMatrixImport, CutterStationImport, SpecimenImport, SpeciesSamplingPlanLu,\
    ProtocolLu, JOIN, database, db2_full_path

import xlrd


class DatabaseMerger():

    def __init__(self):
        super().__init__()

    def process_data(self):

        # Attach the database
        logging.info(f"db2 = {db2_full_path}")
        logging.info(f"db = {database}")
        database.execute_sql(f"ATTACH DATABASE '{db2_full_path}' AS main2;")

        # Modify the structure of the main DB file table to hold old primary keys
        schema = OrderedDict({
                  "NOTES": ["OLD_NOTE_ID"],
                  "OPERATION_DETAILS": ["OLD_OPERATION_DETAILS_ID"],
                  "OPERATION_ATTRIBUTES": ["OLD_OPERATION_ATTRIBUTE_ID"],
                  "SPECIMENS": ["OLD_PARENT_SPECIMEN_ID", "OLD_SPECIMEN_ID"],
                  "CATCH": ["OLD_PARENT_CATCH_ID", "OLD_CATCH_ID"],
                  "EVENTS": ["OLD_PARENT_EVENT_ID", "OLD_EVENT_ID"],
                  "OPERATIONS": ["OLD_PARENT_OPERATION_ID", "OLD_OPERATION_ID"]
                  })
        migrator = SqliteMigrator(database)
        int_field = IntegerField(null=True)
        for k, v in schema.items():
            for col in v:
                try:
                    # database.execute_sql(f"ALTER TABLE {k} ADD COLUMN {col} INTEGER default NULL")
                    migrate(migrator.add_column(table=k, column_name=col, field=int_field))

                    logging.info(f"Successfully created {k} > {col}")
                except Exception as ex:
                    logging.info(f"Column exists: {k} > {col}")

        # Sample query from the attached database that needs to be merged
        ops_cols = ['OPERATION_ID', 'PARENT_OPERATION_ID', 'VESSEL_LU_ID', 'DAY_OF_CRUISE', 'AREA', 'FPC_ID', 'DATE',
            'OPERATION_NUMBER', 'SITE_ID', 'RECORDER_ID', 'SITE_TYPE_LU_ID', 'INCLUDE_IN_SURVEY', 'IS_RCA', 'IS_MPA',
            'OPERATION_TYPE_LU_ID', 'PROCESSING_STATUS', 'CS_PROCESSING_STATUS'
        ]
        event_cols = ['EVENT_ID', 'PARENT_EVENT_ID', 'EVENT_TYPE_LU_ID', 'START_DATE_TIME', 'START_LATITUDE',
                      'START_LONGITUDE', 'START_DEPTH_FTM', 'END_DATE_TIME', 'END_LATITUDE', 'END_LONGITUDE',
                      'END_DEPTH_FTM', 'TIDE_HEIGHT_M', 'SURFACE_TEMPERATURE_AVG_C', 'TRUE_WIND_SPEED_AVG_KTS',
                      'TRUE_WIND_DIRECTION_AVG_DEG', 'DRIFT_SPEED_KTS', 'DRIFT_DIRECTION_DEG', 'DRIFT_DISTANCE_NM',
                      'DROP_TYPE_LU_ID', 'INCLUDE_IN_RESULTS', 'OPERATION_ID']
        op_details_cols = ['OPERATION_DETAILS_ID', 'OPERATION_ID', 'SWELL_HEIGHT_FT', 'SWELL_DIRECTION_DEG', 'WAVE_HEIGHT_FT',
                           'TIDE_STATION_ID', 'DISTANCE_TO_TIDE_STATION_NM', 'TIDE_TYPE_LU_ID', 'TIDE_STATE_LU_ID',
                           'FLOW_FT_PER_HR', 'SUNRISE_TIME', 'SUNSET_TIME', 'MOON_FULLNESS_PERCENT', 'MOON_PHASE_LU_ID',
                           'CTD_DEPTH_M', 'CTD_BOTTOM_TEMP_C', 'CTD_DO2_SBE43_ML_PER_L', 'CTD_DO2_AANDERAA_ML_PER_L',
                           'CTD_SALINITY_PSU', 'CTD_FLUORESCENCE_UG_PER_L', 'CTD_TURBIDITY_NTU', 'HABITAT_COMMENTS',
                           'FISH_METER_COMMENTS', 'OCEAN_WEATHER_COMMENTS', 'GENERAL_COMMENTS']
        op_attributes_cols = ['OPERATION_ATTRIBUTE_ID', 'OPERATION_ID', 'ATTRIBUTE_NUMERIC', 'ATTRIBUTE_ALPHA',
                              'ATTRIBUTE_TYPE_LU_ID']
        catch_cols = ['CATCH_ID', 'PARENT_CATCH_ID', 'CATCH_CONTENT_ID', 'BEST_CATCH_CONTENT_ID', 'CS_CATCH_CONTENT_ID',
                      'HM_CATCH_CONTENT_ID', 'SPECIES_SAMPLING_PLAN_ID', 'DISPLAY_NAME', 'RECEPTACLE_SEQ',
                      'RECEPTACLE_TYPE_ID', 'CONTENT_ACTION_TYPE_ID', 'RESULT_TYPE_ID', 'WEIGHT_KG', 'SAMPLE_COUNT_INT',
                      'NOTE', 'IS_MIX', 'MIX_NUMBER', 'IS_DEBRIS', 'OPERATION_ID', 'OPERATION_TYPE_ID', 'IS_SUBSAMPLE',
                      'IS_WEIGHT_ESTIMATED']
        specimens_cols = ['SPECIMEN_ID', 'PARENT_SPECIMEN_ID', 'CATCH_ID', 'SPECIES_SAMPLING_PLAN_ID', 'ACTION_TYPE_ID',
                          'ALPHA_VALUE', 'NUMERIC_VALUE', 'MEASUREMENT_TYPE_ID', 'NOTE']
        notes_cols = ['NOTE_ID', 'NOTE', 'SCREEN_TYPE_ID', 'DATA_ITEM_ID', 'PERSON', 'OPERATION_ID', 'DATE_TIME',
                      'IS_HAUL_VALIDATION', 'IS_DATA_ISSUE', 'IS_SOFTWARE_ISSUE', 'APP_NAME', 'SCREEN_NAME', 'HL_DROP',
                      'HL_ANGLER', 'HL_HOOK', 'CUTTER_OBSERVATION_NAME']

        # logging.info(f"ops cols = {Operations._meta.sorted_field_names}")

        # Insert the Operations
        sql = "SELECT * FROM main2.OPERATIONS"
        cursor = database.execute_sql(sql=sql)
        for i in cursor.fetchall():
            new_dict = dict(zip(ops_cols, i))
            # logging.info(f"new_dict = {new_dict}")
            insert_sql = """
                INSERT INTO OPERATIONS (VESSEL_LU_ID, DAY_OF_CRUISE, AREA, FPC_ID, DATE, OPERATION_NUMBER, SITE_ID,
                                        RECORDER_ID, SITE_TYPE_LU_ID, INCLUDE_IN_SURVEY, IS_RCA, IS_MPA, 
                                        OPERATION_TYPE_LU_ID, PROCESSING_STATUS, OLD_OPERATION_ID,
                                        OLD_PARENT_OPERATION_ID) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);                        
            """
            params = [new_dict['VESSEL_LU_ID'], new_dict['DAY_OF_CRUISE'], new_dict['AREA'], new_dict['FPC_ID'],
                      new_dict['DATE'], new_dict['OPERATION_NUMBER'], new_dict['SITE_ID'], new_dict['RECORDER_ID'],
                      new_dict['SITE_TYPE_LU_ID'], new_dict['INCLUDE_IN_SURVEY'], new_dict['IS_RCA'], new_dict['IS_MPA'],
                      new_dict['OPERATION_TYPE_LU_ID'], new_dict['PROCESSING_STATUS'], new_dict['OPERATION_ID'],
                      new_dict['PARENT_OPERATION_ID']]
            # database.execute_sql(sql=insert_sql, params=params)

        # Update Operations Parent Record
        # TODO - Hardcoded for 2018 data updates - only using those records greater than OPERATION_ID >= 1115
        sql = "SELECT * FROM OPERATIONS WHERE OPERATION_ID >= 1115;"
        logging.info(f"sql = {sql}")
        cursor = database.execute_sql(sql=sql)
        old_site_id = None
        new_site_id = None
        old_drop_id = None
        new_drop_id = None
        for i in cursor.fetchall():

            # Site Record - Get the old and new site IDs
            if i[2] is not None and i[4] is not None:
                old_site_id = i[-1]
                new_site_id = i[0]
                logging.info(f"Getting site ids: old = {old_site_id}, new = {new_site_id}\n")

            # Drop Record - Get the old and new drop IDs
            if i[-2] == old_site_id and i[7] in ['1', '2', '3', '4', '5']:
                old_drop_id = i[-1]
                new_drop_id = i[0]
                logging.info(f"Getting drop ids: old = {old_drop_id}, new = {new_drop_id}\n")

                # SQL for updating the drop record
                update_drop_sql = f"UPDATE OPERATIONS SET PARENT_OPERATION_ID = ? WHERE OPERATION_ID = ?;"
                params = [new_site_id, new_drop_id]
                # database.execute_sql(sql=update_drop_sql, params=params)

                logging.info(f"\tDrop record = {i}")
                logging.info(f"\tDrop Update sql = {update_drop_sql},  params = {params}\n")

            # Angler Record
            if i[-2] == old_drop_id and i[7] in ['A', 'B', 'C']:

                # SQL for updating the angler record
                update_angler_sql = f"UPDATE OPERATIONS SET PARENT_OPERATION_ID = ? WHERE OPERATION_ID = ?;"
                params = [new_drop_id, i[0]]
                # database.execute_sql(sql=update_angler_sql, params=params)

                logging.info(f"\t\tAngler record = {i}")
                logging.info(f"\t\tAngler Update sql = {update_angler_sql},  params = {params}\n")

        # Insert the Events
        sql = "SELECT * FROM main2.EVENTS"
        cursor = database.execute_sql(sql=sql)
        for i in cursor.fetchall():
            new_dict = dict(zip(event_cols, i))
            insert_sql = """
                INSERT INTO EVENTS (
                    EVENT_TYPE_LU_ID, START_DATE_TIME, START_LATITUDE,
                    START_LONGITUDE, START_DEPTH_FTM, END_DATE_TIME, END_LATITUDE, END_LONGITUDE, END_DEPTH_FTM,
                    TIDE_HEIGHT_M, SURFACE_TEMPERATURE_AVG_C, TRUE_WIND_SPEED_AVG_KTS, TRUE_WIND_DIRECTION_AVG_DEG,
                    DRIFT_SPEED_KTS, DRIFT_DIRECTION_DEG, DRIFT_DISTANCE_NM, DROP_TYPE_LU_ID, INCLUDE_IN_RESULTS,
                    OPERATION_ID, OLD_PARENT_EVENT_ID, OLD_EVENT_ID
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);                        
            """
            params = [new_dict['EVENT_TYPE_LU_ID'], new_dict['START_DATE_TIME'], new_dict['START_LATITUDE'], new_dict['START_LONGITUDE'],
                      new_dict['START_DEPTH_FTM'], new_dict['END_DATE_TIME'], new_dict['END_LATITUDE'], new_dict['END_LONGITUDE'],
                      new_dict['END_DEPTH_FTM'], new_dict['TIDE_HEIGHT_M'], new_dict['SURFACE_TEMPERATURE_AVG_C'], new_dict['TRUE_WIND_SPEED_AVG_KTS'],
                      new_dict['TRUE_WIND_DIRECTION_AVG_DEG'], new_dict['DRIFT_SPEED_KTS'], new_dict['DRIFT_DIRECTION_DEG'],
                      new_dict['DRIFT_DISTANCE_NM'], new_dict['DROP_TYPE_LU_ID'], new_dict['INCLUDE_IN_RESULTS'], new_dict['OPERATION_ID'],
                      new_dict['PARENT_EVENT_ID'], new_dict['EVENT_ID']]
            # database.execute_sql(sql=insert_sql, params=params)

        # Update the Events with the correct OPERATION_ID
        # TODO - 2018 Hardcoded - will need to change for subsequent years if you have to merge databases again
        sql = "SELECT * FROM EVENTS WHERE EVENT_ID >= 351;"
        cursor = database.execute_sql(sql=sql)
        for i in cursor.fetchall():
            logging.info(f"event record = {i}")

            sql = "SELECT OPERATION_ID FROM OPERATIONS WHERE OLD_OPERATION_ID = ?;"
            params = [i[-3], ]
            op_cursor = database.execute_sql(sql=sql, params=params)
            for op in op_cursor:
                logging.info(f"\told_op_id = {i[-3]}, new op_id = {op[0]}")
                update_sql = "UPDATE EVENTS SET OPERATION_ID = ? WHERE EVENT_ID = ?;"
                params = [op[0], i[0]]
                logging.info(f"\tsql = {update_sql},   params = {params}\n")
                # database.execute_sql(sql=update_sql, params=params)

        # Insert the Operation Details
        sql = "SELECT * FROM main2.OPERATION_DETAILS"
        cursor = database.execute_sql(sql=sql)
        for i in cursor.fetchall():
            new_dict = dict(zip(op_details_cols, i))
            insert_sql = """
                INSERT INTO OPERATION_DETAILS (
                    'OPERATION_ID', 'SWELL_HEIGHT_FT', 'SWELL_DIRECTION_DEG', 'WAVE_HEIGHT_FT',
                    'TIDE_STATION_ID', 'DISTANCE_TO_TIDE_STATION_NM', 'TIDE_TYPE_LU_ID', 'TIDE_STATE_LU_ID',
                    'FLOW_FT_PER_HR', 'SUNRISE_TIME', 'SUNSET_TIME', 'MOON_FULLNESS_PERCENT', 'MOON_PHASE_LU_ID',
                    'CTD_DEPTH_M', 'CTD_BOTTOM_TEMP_C', 'CTD_DO2_SBE43_ML_PER_L', 'CTD_DO2_AANDERAA_ML_PER_L',
                    'CTD_SALINITY_PSU', 'CTD_FLUORESCENCE_UG_PER_L', 'CTD_TURBIDITY_NTU', 'HABITAT_COMMENTS',
                    'FISH_METER_COMMENTS', 'OCEAN_WEATHER_COMMENTS', 'GENERAL_COMMENTS'
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
            """
            params = [
                new_dict['OPERATION_ID'], new_dict['SWELL_HEIGHT_FT'], new_dict['SWELL_DIRECTION_DEG'], new_dict['WAVE_HEIGHT_FT'],
                new_dict['TIDE_STATION_ID'], new_dict['DISTANCE_TO_TIDE_STATION_NM'], new_dict['TIDE_TYPE_LU_ID'], new_dict['TIDE_STATE_LU_ID'],
                new_dict['FLOW_FT_PER_HR'], new_dict['SUNRISE_TIME'], new_dict['SUNSET_TIME'], new_dict['MOON_FULLNESS_PERCENT'], new_dict['MOON_PHASE_LU_ID'],
                new_dict['CTD_DEPTH_M'], new_dict['CTD_BOTTOM_TEMP_C'], new_dict['CTD_DO2_SBE43_ML_PER_L'], new_dict['CTD_DO2_AANDERAA_ML_PER_L'],
                new_dict['CTD_SALINITY_PSU'], new_dict['CTD_FLUORESCENCE_UG_PER_L'], new_dict['CTD_TURBIDITY_NTU'], new_dict['HABITAT_COMMENTS'],
                new_dict['FISH_METER_COMMENTS'], new_dict['OCEAN_WEATHER_COMMENTS'], new_dict['GENERAL_COMMENTS']
            ]
            # database.execute_sql(sql=insert_sql, params=params)

        # Update the Operation Details with the correct OPERATION_ID
        # TODO - 2018 Hardcoded - will need to change for subsequent years if you have to merge databases again
        sql = "SELECT * FROM OPERATION_DETAILS WHERE OPERATION_DETAILS_ID >= 55;"
        cursor = database.execute_sql(sql=sql)
        for i in cursor.fetchall():
            logging.info(f"operation_details record = {i}")

            sql = "SELECT OPERATION_ID FROM OPERATIONS WHERE OLD_OPERATION_ID = ?;"
            params = [i[1], ]
            op_details_cursor = database.execute_sql(sql=sql, params=params)
            for op_det in op_details_cursor:
                logging.info(f"\t\top_id = {op_det[0]}")
                update_sql = "UPDATE OPERATION_DETAILS SET OPERATION_ID = ? WHERE OPERATION_DETAILS_ID = ?;"
                params = [op_det[0], i[0]]
                logging.info(f"\t\tupdate info: {update_sql} >>> {params}")

                # database.execute_sql(sql=update_sql, params=params)

        # Insert the Operation Attributes
        sql = "SELECT * FROM main2.OPERATION_ATTRIBUTES"
        cursor = database.execute_sql(sql=sql)
        for i in cursor.fetchall():
            # logging.info(f"op_atts record = {i}")
            new_dict = dict(zip(op_attributes_cols, i))
            insert_sql = """
                INSERT INTO OPERATION_ATTRIBUTES (
                    'OPERATION_ID', 'ATTRIBUTE_NUMERIC', 'ATTRIBUTE_ALPHA', 'ATTRIBUTE_TYPE_LU_ID'
                ) VALUES(?,?,?,?);
            """
            params = [
                new_dict['OPERATION_ID'], new_dict['ATTRIBUTE_NUMERIC'],
                new_dict['ATTRIBUTE_ALPHA'], new_dict['ATTRIBUTE_TYPE_LU_ID'],
            ]
            # database.execute_sql(sql=insert_sql, params=params)

        # Update the Operation Attributes with the correct OPERATION_ID
        # TODO - 2018 Hardcode - will need to change the where clause parameter for merging DBs in the future
        sql = "SELECT * FROM OPERATION_ATTRIBUTES WHERE OPERATION_ATTRIBUTE_ID >= 6033;"
        cursor = database.execute_sql(sql=sql)
        for i in cursor.fetchall():
            logging.info(f"operation_attributes record = {i}")

            sql = "SELECT OPERATION_ID FROM OPERATIONS WHERE OLD_OPERATION_ID = ?;"
            params = [i[1], ]
            catch_cursor = database.execute_sql(sql=sql, params=params)
            for catch_att in catch_cursor:
                logging.info(f"\t\top_id = {catch_att[0]}")
                update_sql = "UPDATE OPERATION_ATTRIBUTES SET OPERATION_ID = ? WHERE OPERATION_ATTRIBUTE_ID = ?;"
                params = [catch_att[0], i[0]]
                logging.info(f"\t\tupdate info: {update_sql} >>> {params}")

                # database.execute_sql(sql=update_sql, params=params)

        # Remove Unique Constraint on the Catch Records
        # migrate(migrator.drop_constraint('catch', 'UNQ_RECEPTACLE'))
        # NOTE - Must manually do this currently as it is not implemented in peewee for sqlite

        # Insert the Catch
        sql = "SELECT * FROM main2.CATCH"
        cursor = database.execute_sql(sql=sql)
        for i in cursor.fetchall():
            new_dict = dict(zip(catch_cols, i))
            insert_sql = """
                INSERT INTO CATCH (
                    'CATCH_CONTENT_ID', 'BEST_CATCH_CONTENT_ID', 'CS_CATCH_CONTENT_ID',
                    'HM_CATCH_CONTENT_ID', 'SPECIES_SAMPLING_PLAN_ID', 'DISPLAY_NAME', 'RECEPTACLE_SEQ',
                    'RECEPTACLE_TYPE_ID', 'CONTENT_ACTION_TYPE_ID', 'RESULT_TYPE_ID', 'WEIGHT_KG', 'SAMPLE_COUNT_INT',
                    'NOTE', 'IS_MIX', 'MIX_NUMBER', 'IS_DEBRIS', 'OPERATION_ID', 'OPERATION_TYPE_ID', 'IS_SUBSAMPLE',
                    'IS_WEIGHT_ESTIMATED', 'OLD_PARENT_CATCH_ID', 'OLD_CATCH_ID'
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
            """
            params = [
                new_dict['CATCH_CONTENT_ID'], new_dict['BEST_CATCH_CONTENT_ID'], new_dict['CS_CATCH_CONTENT_ID'],
                new_dict['HM_CATCH_CONTENT_ID'], new_dict['SPECIES_SAMPLING_PLAN_ID'], new_dict['DISPLAY_NAME'], new_dict['RECEPTACLE_SEQ'],
                new_dict['RECEPTACLE_TYPE_ID'], new_dict['CONTENT_ACTION_TYPE_ID'], new_dict['RESULT_TYPE_ID'], new_dict['WEIGHT_KG'], new_dict['SAMPLE_COUNT_INT'],
                new_dict['NOTE'], new_dict['IS_MIX'], new_dict['MIX_NUMBER'], new_dict['IS_DEBRIS'], new_dict['OPERATION_ID'], new_dict['OPERATION_TYPE_ID'], new_dict['IS_SUBSAMPLE'],
                new_dict['IS_WEIGHT_ESTIMATED'], new_dict['PARENT_CATCH_ID'], new_dict['CATCH_ID']
            ]
            # database.execute_sql(sql=insert_sql, params=params)

        #  Update the Catch with the correct OPERATION_ID
        # TODO - 2018 Hardcoded - will need to change the where clause parameter for merging DBs in the future
        sql = "SELECT * FROM CATCH WHERE CATCH_ID >= 8562;"
        cursor = database.execute_sql(sql=sql)
        for i in cursor.fetchall():
            logging.info(f"catch record = {i}")

            sql = "SELECT OPERATION_ID FROM OPERATIONS WHERE OLD_OPERATION_ID = ?;"
            params = [i[18], ]
            catch_cursor = database.execute_sql(sql=sql, params=params)
            for catch_att in catch_cursor:
                logging.info(f"\t\tnew op_id = {catch_att[0]}")
                update_sql = "UPDATE CATCH SET OPERATION_ID = ? WHERE CATCH_ID = ?;"
                params = [catch_att[0], i[0]]
                logging.info(f"\t\tupdate info: {update_sql} >>> {params}")

                # database.execute_sql(sql=update_sql, params=params)

        # Recreate the Unique Constraint on the Catch Records
        # migrate(migrator.add_unique('catch', 'receptacle_seq', 'receptacle_type_id', 'operation_id'))
        # NOTE - Must manually do this currently as it is not implemented in peewee for sqlite

        # Insert the Specimens
        sql = "SELECT * FROM main2.SPECIMENS"
        cursor = database.execute_sql(sql=sql)
        for i in cursor.fetchall():
            new_dict = dict(zip(specimens_cols, i))
            insert_sql = """
                INSERT INTO SPECIMENS (
                    'CATCH_ID', 'SPECIES_SAMPLING_PLAN_ID', 'ACTION_TYPE_ID',
                    'ALPHA_VALUE', 'NUMERIC_VALUE', 'MEASUREMENT_TYPE_ID', 'NOTE', 
                    'OLD_PARENT_SPECIMEN_ID', 'OLD_SPECIMEN_ID'                        
                ) VALUES(?,?,?,?,?,?,?,?,?);
            """
            params = [
                new_dict['CATCH_ID'], new_dict['SPECIES_SAMPLING_PLAN_ID'], new_dict['ACTION_TYPE_ID'],
                new_dict['ALPHA_VALUE'], new_dict['NUMERIC_VALUE'], new_dict['MEASUREMENT_TYPE_ID'], new_dict['NOTE'],
                new_dict['PARENT_SPECIMEN_ID'], new_dict['SPECIMEN_ID']
            ]
            # database.execute_sql(sql=insert_sql, params=params)

        # Update the Specimens with the correct CATCH_ID and PARENT_SPECIMEN_ID values
        # TODO - 2018 Hardcoded - will need to change the where clause parameter for merging DBs in the future
        sql = "SELECT * FROM SPECIMENS WHERE SPECIMEN_ID >= 14571;"
        cursor = database.execute_sql(sql=sql)
        old_parent_specimen_id = None
        for i in cursor.fetchall():
            logging.info(f"specimen record = {i}")

            # Update the CATCH_ID
            sql = "SELECT CATCH_ID FROM CATCH WHERE OLD_CATCH_ID = ?;"
            params = [i[2], ]
            catch_cursor = database.execute_sql(sql=sql, params=params)
            for catch_att in catch_cursor:
                logging.info(f"\t\tnew catch_id = {catch_att[0]},    old catch_id = {i[2]}")
                update_sql = "UPDATE SPECIMENS SET CATCH_ID = ? WHERE SPECIMEN_ID = ?;"
                params = [catch_att[0], i[0]]
                logging.info(f"\t\tupdate info: {update_sql} >>> {params}")

                # database.execute_sql(sql=update_sql, params=params)

            # Update the PARENT_SPECIMEN_ID
            if i[-2] is not None:

                sql = "SELECT SPECIMEN_ID FROM SPECIMENS WHERE OLD_SPECIMEN_ID = ?;"
                params = [i[-2],]
                spec_cursor = database.execute_sql(sql=sql, params=params)
                for spec in spec_cursor:
                    update_sql = "UPDATE SPECIMENS SET PARENT_SPECIMEN_ID = ? WHERE SPECIMEN_ID = ?;"
                    params = [spec[0], i[0]]
                    # database.execute_sql(sql=update_sql, params=params)

                    # logging.info(f"\t\tupdating spec:   {update_sql} >>> {params}\n")

        # Insert the Notes
        sql = "SELECT * FROM main2.NOTES"
        cursor = database.execute_sql(sql=sql)
        for i in cursor.fetchall():
            new_dict = dict(zip(notes_cols, i))
            insert_sql = """
                INSERT INTO NOTES (
                    'NOTE', 'SCREEN_TYPE_ID', 'DATA_ITEM_ID', 'PERSON', 'OPERATION_ID', 'DATE_TIME',
                    'IS_HAUL_VALIDATION', 'IS_DATA_ISSUE', 'IS_SOFTWARE_ISSUE', 'APP_NAME', 'SCREEN_NAME', 'HL_DROP',
                    'HL_ANGLER', 'HL_HOOK', 'CUTTER_OBSERVATION_NAME', 'OLD_NOTE_ID'
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);                        
            """
            params = [
                new_dict['NOTE'], new_dict['SCREEN_TYPE_ID'], new_dict['DATA_ITEM_ID'], new_dict['PERSON'], new_dict['OPERATION_ID'], new_dict['DATE_TIME'],
                  new_dict['IS_HAUL_VALIDATION'], new_dict['IS_DATA_ISSUE'], new_dict['IS_SOFTWARE_ISSUE'], new_dict['APP_NAME'], new_dict['SCREEN_NAME'], new_dict['HL_DROP'],
                  new_dict['HL_ANGLER'], new_dict['HL_HOOK'], new_dict['CUTTER_OBSERVATION_NAME'], new_dict['NOTE_ID']
                      ]
            # database.execute_sql(sql=insert_sql, params=params)

        # Update the Notes with the correct OPERATION_ID values
        # TODO - 2018 Hardcoded - will need to change the where clause parameter for merging DBs in the future
        sql = "SELECT * FROM NOTES WHERE NOTE_ID >= 77;"
        cursor = database.execute_sql(sql=sql)
        for i in cursor.fetchall():
            logging.info(f"note record = {i}")

            sql = "SELECT OPERATION_ID FROM OPERATIONS WHERE OLD_OPERATION_ID = ?;"
            params = [i[5], ]
            op_cursor = database.execute_sql(sql=sql, params=params)
            for op in op_cursor:
                logging.info(f"\told_op_id = {i[5]}, new op_id = {op[0]}")
                update_sql = "UPDATE NOTES SET OPERATION_ID = ? WHERE NOTE_ID = ?;"
                params = [op[0], i[0]]
                logging.info(f"\tsql = {update_sql},   params = {params}\n")
                # database.execute_sql(sql=update_sql, params=params)

        # Modify the main DB structure to remove the temporary columns that were used to insert the data from the 2nd db
        for k, v in schema.items():
            for col in v:
                try:
                    pass
                    # migrate(migrator.drop_column(table=k, column_name=col))
                    # logging.info(f"Successfully deleted {k} > {col}")
                except Exception as ex:
                    pass
                    # logging.info(f"Unable to drop {col} from {k}: {ex}")


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


    # ***** NOTE NOTE NOTE - Update the HookandlineFpcDB_Model.py to point to the right database path for the correct vessel

    dbm = DatabaseMerger()
    dbm.process_data()
