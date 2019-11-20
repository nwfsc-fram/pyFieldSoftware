import os
import logging
from math import radians, sin, cos, atan2, sqrt

from playhouse.shortcuts import model_to_dict
import arrow

from py.hookandline.HookandlineFpcDB_model import Lookups, Operations, Catch, OperationAttributes, Notes, \
    CatchContentLu, Specimen, \
    ImportHookLogger, ImportHookMatrix, ImportCutterStation, ImportSpecimen, Events, Sites, \
    SpeciesSamplingPlanLu, ProtocolLu, JOIN, Personnel, OperationDetails, TideStations
from py.hookandline.FpcMain import FpcMain

import xlrd


class SpecimenImporter():

    def __init__(self):
        super().__init__()

    def process_data(self):

        errors = list()

        finclip_lu = Lookups.get(Lookups.type=='Observation', Lookups.value=="Finclip ID").lookup

        results = SpecimenImport.select()
        for i, result in enumerate(results):

            # if i == 1:
            #     break

            logging.info(f"row={i+1} = {model_to_dict(result)}")

            try:

                # Find the sibling specimen where finclip ID = result.finclip
                sibling_specimen, sibling_specimen_created = Specimen.get_or_create(alpha_value=result.finclip,
                                                                                    action_type=finclip_lu)

                # Determine the specimen lookup value
                if "Age ID" in result.specimen_type:
                    subvalue = result.specimen_type.strip('Age ID').strip()
                    specimen_lu = Lookups.get(Lookups.type == 'Observation',
                                              Lookups.value == 'Age ID',
                                              Lookups.subvalue == subvalue).lookup

                else:
                    specimen_lu = Lookups.get(Lookups.type == 'Observation', Lookups.value == result.specimen_type).lookup

                # Determine the species sampling plan
                ssp_results = SpeciesSamplingPlanLu.select(SpeciesSamplingPlanLu, ProtocolLu) \
                            .join(ProtocolLu) \
                            .where(SpeciesSamplingPlanLu.plan_name==result.plan_name,
                                   ProtocolLu.action_type==specimen_lu)
                for ssp_result in ssp_results:
                    ssp_lu = ssp_result.species_sampling_plan
                    specimen, specimen_created = Specimen.get_or_create(parent_specimen=sibling_specimen.parent_specimen,
                                                                    species_sampling_plan=ssp_lu,
                                                                    action_type=specimen_lu,
                                                                    alpha_value=result.specimen_number,
                                                                    defaults={'catch': sibling_specimen.catch})
                    logging.info(f"Specimen created = {specimen_created}:  {result.specimen_type} = {result.specimen_number}"
                             f" > {specimen.specimen}")


            except Exception as ex:

                errors.append(f"row={i+1}, set_id={result.set_id} > {ex}")

        for err in errors:

            logging.info(f"{err}")


class CutterStationImporter():


    def __init__(self):
        super().__init__()

    def process_data(self):

        errors = list()

        set_op_type =  Lookups.get(Lookups.type=='Operation', Lookups.value=='Site').lookup
        drop_op_type = Lookups.get(Lookups.type=='Operation', Lookups.value=='Drop').lookup
        angler_op_type = Lookups.get(Lookups.type=='Operation', Lookups.value=='Angler').lookup

        length_lu = Lookups.get(Lookups.type=='Observation', Lookups.value=="Length").lookup
        weight_lu = Lookups.get(Lookups.type=='Observation', Lookups.value=="Weight").lookup
        sex_lu = Lookups.get(Lookups.type=='Observation', Lookups.value=="Sex").lookup
        finclip_lu = Lookups.get(Lookups.type=='Observation', Lookups.value=="Finclip ID").lookup
        otolith_lu = Lookups.get(Lookups.type=='Observation', Lookups.value=="Age ID", Lookups.subvalue=="Otolith").lookup
        descended_lu = Lookups.get(Lookups.type=='Observation', Lookups.value=="Disposition", Lookups.subvalue=="Descended").lookup
        released_lu = Lookups.get(Lookups.type=='Observation', Lookups.value=="Disposition", Lookups.subvalue=="Released").lookup
        sacrificed_lu = Lookups.get(Lookups.type=='Observation', Lookups.value=="Disposition", Lookups.subvalue=="Sacrificed").lookup

        cutter_recorder = Lookups.get(Lookups.type=='Cutter Attribute', Lookups.value=='Recorder Name').lookup

        specimen_dict = {"length": length_lu, "weight": weight_lu, "sex": sex_lu, "finclip": finclip_lu,
                         "otolith": otolith_lu}

        disposition_dict = {"Descended": descended_lu, "Released": released_lu, "Sacrificed": sacrificed_lu}

        receptacle_type = Lookups.get(Lookups.type=='Receptacle Type', Lookups.value=='Hook').lookup

        results = ImportCutterStation.select()
        for i, result in enumerate(results):

            # if i == 1:
            #     break

            logging.info(f"row={i+1} = {model_to_dict(result)}")

            try:
                set_op, set_created = Operations.get_or_create(operation_number=result.set_id,
                                                               defaults={'operation_type_lu': set_op_type})

                drop_op, drop_created = Operations.get_or_create(parent_operation=set_op.operation,
                                                                 operation_number=result.drop,
                                                                 defaults={'operation_type_lu': drop_op_type})

                angler_op, angler_created = Operations.get_or_create(parent_operation=drop_op.operation,
                                                           operation_number=result.angler,
                                                           defaults={'operation_type_lu': angler_op_type})

                # Catch / Hook - Insert
                species = result.species
                if species is not None:
                    species = species.strip()
                    cs_catch_content = CatchContentLu.get(CatchContentLu.display_name==species).catch_content
                    catch, catch_created = Catch.get_or_create(receptacle_seq=result.hook,
                                                               receptacle_type=receptacle_type,
                                                               operation=angler_op.operation,
                                                               defaults={'operation_type': angler_op_type,
                                                                         'cs_catch_content': cs_catch_content})
                    catch_id = catch.catch
                    logging.info(f"Catch created = {catch_created}:  Hook {result.hook} > {species}")

                    if not catch_created:
                        Catch.update(cs_catch_content=cs_catch_content).where(Catch.catch == catch_id).execute()
                        logging.info(f"CS Catch Content updated: {cs_catch_content}")


                # Parent Specimen - Insert
                parent_specimen, parent_specimen_created = Specimen.get_or_create(catch=catch_id)

                # Specimen / Observations - Insert
                for k, v in specimen_dict.items():

                    alpha_value = numeric_value = None
                    if k in ["length", "weight"]:
                        numeric_value = getattr(result, k)
                    else:
                        alpha_value = getattr(result, k)

                    # logging.info(f"{k} > {alpha_value} / {numeric_value} >>> {v}")

                    if alpha_value is not None or numeric_value is not None:
                        specimen, specimen_created = Specimen.get_or_create(parent_specimen=parent_specimen.specimen,
                                                                            catch=catch_id,
                                                                            action_type=v,
                                                                            alpha_value=alpha_value,
                                                                            numeric_value=numeric_value)
                        logging.info(f"Specimeen created = {specimen_created}: {k} > {alpha_value} / {numeric_value} > {specimen.specimen}")

                # Disposition - Insert
                alpha_value = result.tag_number
                numeric_value = None
                disposition = result.disposition
                if disposition:
                    disposition = disposition.strip()
                    specimen, specimen_created = Specimen.get_or_create(parent_specimen=parent_specimen.specimen,
                                                                        catch=catch_id,
                                                                        action_type=disposition_dict[disposition],
                                                                        alpha_value=alpha_value,
                                                                        numeric_value=numeric_value)
                    logging.info(
                        f"Specimeen created = {specimen_created}: Disposition = {result.disposition} > {alpha_value} / {numeric_value} > {specimen.specimen}")

                # Cutter Recorder - Insert

                # This is a bogus TODO below, as I never added a recorded_by directly into the SPECIMENS table
                # TODO Todd Hay - Okay for 2017 data, but will need to be updated for 2018 data as I'll add a recorded by in the SPECIMEN table
                if result.recorded_by is not None:
                    op_att, op_att_created = OperationAttributes.get_or_create(operation=angler_op,
                                                                               attribute_alpha=result.recorded_by,
                                                                               attribute_type_lu=v)
                    logging.info(f"Cutter recorded by created = {op_att_created}:  {result.recorded_by} > "
                                 f"{op_att.operation_attribute}")

                # Note - Insert
                if result.notes is not None:
                    note, note_created = Notes.get_or_create(note=result.notes,
                                                             operation=angler_op,
                                                             app_name="HookMatrix",
                                                             hl_drop=result.drop,
                                                             hl_angler=result.angler,
                                                             defaults={'date_time': arrow.now(tz="US/Pacific")}
                                                             )
                    logging.info(f"Note created = {note_created} > {result.notes}")

            except Exception as ex:

                errors.append(f"row={i+1}, set_id={result.set_id} > ERROR:  {ex}")

        for err in errors:

            logging.info(f"{err}")


class HookMatrixImporter():

    def __init__(self):
        super().__init__()

    def start_import(self):

        # wb = load_workbook(filename=fullpath, guess_types=True)
        # logging.info(f"names = {wb.sheetnames}")
        #
        # sh = wb["Aggressor"]
        # logging.info(f"{sh}")
        #
        #
        # for row in sh.iter_rows():
        #
        #     logging.info(f"{row}")

        map = {'SetID': 'text'}

        wb = xlrd.open_workbook(filename=fullpath)
        logging.info(f"{wb.sheet_names()}")

        sh = wb.sheet_by_name(sheet_name="Aggressor")
        logging.info(f"nrows: {sh.nrows}")

        for row in range(sh.nrows):
            if row == 0:
                header = sh.row_values(row)
                logging.info(f"header = {header}")
                continue

            if row == 1:
                for col in range(sh.ncols):
                    c = sh.cell(row, col)
                    # xf = sh.book.xf_list[c.xf_index]
                    # fmt_obj = sh.book.format_map[xf.format_key]
                    logging.info(f"{c}")
                    # logging.info(f"{c.value}, {c.type}")

                # logging.info(f"row = {sh.row_values(row)}")

    def process_data(self):

        errors = list()

        set_op_type =  Lookups.get(Lookups.type=='Operation', Lookups.value=='Site').lookup
        drop_op_type = Lookups.get(Lookups.type=='Operation', Lookups.value=='Drop').lookup
        angler_op_type = Lookups.get(Lookups.type=='Operation', Lookups.value=='Angler').lookup

        angler_name = Lookups.get(Lookups.type=='Angler Attribute', Lookups.value=='Angler Name').lookup
        angler_start = Lookups.get(Lookups.type=='Angler Time', Lookups.value=='Start').lookup
        angler_begin_fishing = Lookups.get(Lookups.type=='Angler Time', Lookups.value=='Begin Fishing').lookup
        angler_first_bite = Lookups.get(Lookups.type == 'Angler Time', Lookups.value == 'First Bite').lookup
        angler_retrieval = Lookups.get(Lookups.type=='Angler Time', Lookups.value=='Retrieval').lookup
        angler_at_surface = Lookups.get(Lookups.type=='Angler Time', Lookups.value=='At Surface').lookup

        drop_sinker_weight = Lookups.get(Lookups.type=='Drop Attribute', Lookups.value=='Sinker Weight').lookup
        drop_recorder = Lookups.get(Lookups.type=='Drop Attribute', Lookups.value=='Recorder Name').lookup

        angler_dict = {"angler_name": angler_name, "start": angler_start, "begin_fishing": angler_begin_fishing,
                       "first_bite": angler_first_bite, "retrieval": angler_retrieval, "at_surface": angler_at_surface}

        drop_dict = {"sinker_weight": drop_sinker_weight, "recorded_by": drop_recorder}

        receptacle_type = Lookups.get(Lookups.type=='Receptacle Type', Lookups.value=='Hook').lookup

        results = ImportHookMatrix.select()
        for i, result in enumerate(results):

            logging.info(f"row={i+1} = {model_to_dict(result)}")

            try:
                set_op, set_created = Operations.get_or_create(operation_number=result.set_id,
                                                               defaults={'operation_type_lu': set_op_type})

                drop_op, drop_created = Operations.get_or_create(parent_operation=set_op.operation,
                                                                 operation_number=result.drop,
                                                                 defaults={'operation_type_lu': drop_op_type})

                angler_op, angler_created = Operations.get_or_create(parent_operation=drop_op.operation,
                                                           operation_number=result.angler,
                                                           defaults={'operation_type_lu': angler_op_type})

                # Angler Attributes - Insert
                for k, v in angler_dict.items():

                    alpha_value = getattr(result, k)
                    if alpha_value is not None:
                        if k == "start":
                            alpha_value = alpha_value[:-4]

                        elif k in ['begin_fishing', 'first_bite', 'retrieval', 'at_surface']:
                            alpha_value = alpha_value[:-7]

                        op_att, op_att_created = OperationAttributes.get_or_create(operation=angler_op,
                                                                               attribute_alpha=alpha_value,
                                                                               attribute_type_lu=v)
                        logging.info(f"Angler attribute created = {op_att_created}:  {k} = {alpha_value} >>> "
                                 f"{op_att.operation_attribute}")

                    else:
                        if k == "start":

                            # Retrieve the start time from the HookLoggerImport table for this Angler
                            hook_logger_record = ImportHookLogger.get(ImportHookLogger.set_id==result.set_id,
                                                                      ImportHookLogger.drop_number==f"Drop {result.drop}")
                            if hook_logger_record:
                                alpha_value = hook_logger_record.drop_time[:-4]
                                logging.info(f"Angler start time: {alpha_value}")
                                op_att, op_att_created = OperationAttributes.get_or_create(operation=angler_op,
                                                                                       attribute_alpha=alpha_value,
                                                                                       attribute_type_lu=v)
                                logging.info(f"Angler attribute created = {op_att_created}:  {k} = {alpha_value} >>> "
                                         f"{op_att.operation_attribute}")


                # Angler Gear Performance - Insert
                if result.gear_performance is not None:
                    for perf in result.gear_performance.split(","):
                        try:
                            perf = perf.strip().replace("(", "").replace(")", "")
                            gp_id = Lookups.get(Lookups.type=="Angler Gear Performance", Lookups.value==perf).lookup
                            op_att, op_att_created = OperationAttributes.get_or_create(operation=angler_op,
                                                                                       attribute_type_lu=gp_id)
                            logging.info(
                                f"Angler attribute created = {op_att_created}:  {perf} >>> {op_att.operation_attribute}")

                        except Exception as ex:
                            logging.info(f"Error finding the gear performance lookup: {ex}")

                # Drop Attributes - Insert
                for k, v in drop_dict.items():

                    alpha_value = numeric_value = None
                    if k == "sinker_weight":
                        numeric_value = getattr(result, k)
                    elif k == "recorded_by":
                        alpha_value = getattr(result, k)
                    if alpha_value is not None or numeric_value is not None:
                        op_att, op_att_created = OperationAttributes.get_or_create(operation=drop_op,
                                                                               attribute_alpha=alpha_value,
                                                                               attribute_numeric=numeric_value,
                                                                               attribute_type_lu=v)
                        logging.info(f"Drop attribute created = {op_att_created}:  {k} = {alpha_value} / "
                                     f"{numeric_value} >>> "
                                     f"{op_att.operation_attribute}")

                # Hooks - Insert
                for j in range(1,6):
                    species = getattr(result, f"hook{j}")
                    if species is not None:
                        species = species.strip()
                        hm_catch_content = CatchContentLu.get(CatchContentLu.display_name==species).catch_content
                        catch, catch_created = Catch.get_or_create(receptacle_seq=j,
                                                                   receptacle_type=receptacle_type,
                                                                   operation=angler_op.operation,
                                                                   defaults={'operation_type': angler_op_type,
                                                                             'hm_catch_content': hm_catch_content})
                        logging.info(f"Catch created = {catch_created}:  Hook {j} > {species}")

                # Note - Insert
                if result.notes is not None:
                    note, note_created = Notes.get_or_create(note=result.notes,
                                                             operation=angler_op,
                                                             app_name="HookMatrix",
                                                             hl_drop=result.drop,
                                                             hl_angler=result.angler,
                                                             defaults={'date_time': arrow.now(tz="US/Pacific")}
                                                             )
                    logging.info(f"Note created = {note_created} > {result.notes}")

            except Exception as ex:

                errors.append(f"row={i+1}, set_id={result.set_id} > {ex}")

        for err in errors:

            logging.info(f"{err}")


class HookLoggerImporter():

    def __init__(self):
        super().__init__()

    def get_distance_to_tide_station(self, site_id, tide_station_id):
        """
        Method to calculate the distance to the tide station

        :param site_id:
        :param tide_station_id:
        :return:
        """
        site = Sites.get(Sites.site == site_id)
        tide_station = TideStations.get(TideStations.tide_station == tide_station_id)

        try:
            site_lat = float(site.latitude)
            site_lon = float(site.longitude)
            tide_lat = float(tide_station.latitude)
            tide_lon = float(tide_station.longitude)

            lon1, lat1, lon2, lat2 = map(radians, [site_lon, site_lat, tide_lon, tide_lat])
            dlon = lon2 - lon1
            dlat = lat2 - lat1

            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            arc = 6371 * c

            # Convert from KM to NM
            arc = 0.539957 * arc

            return float(f"{arc:.1f}")

        except Exception as ex:

            logging.error(f"Error calculating the distance to the tide station: {ex}")
            return None

    def get_lat_lon(self, input):
        """
        Method to convert lat/lon in DD MM.MMMM format to DD.DDDDDD
        :param input:
        :return:
        """
        value = None
        try:
            split = input.split(" ")
            value = float(split[0]) + float(split[1])/60

        except Exception as ex:
            pass

        return value

    def process_data(self):

        errors = list()

        site_op_type = Lookups.get(Lookups.type=='Operation', Lookups.value=='Site').lookup
        drop_op_type = Lookups.get(Lookups.type=='Operation', Lookups.value=='Drop').lookup
        site_type_lu_id = Lookups.get(Lookups.type=='Site Type', Lookups.value=='Fixed').lookup
        drop_type_lu_id = Lookups.get(Lookups.type=="Drop Type", Lookups.value=='Fixed').lookup

        results = ImportHookLogger.select()
        current_set_id = None
        for i, result in enumerate(results):

            # if i == 6:
            #     break

            logging.info(f"row={i+1} = {model_to_dict(result)}")

            try:

                vessel_lu_id = Lookups.get(Lookups.type == 'Vessel Number', Lookups.description == result.vessel)
                area = Sites.get(Sites.name == result.sites_name)
                fpc_name = result.recorded_by.split(" ")
                first_name = fpc_name[0]
                last_name = fpc_name[1]
                fpc_id = Personnel.get(Personnel.first_name == first_name, Personnel.last_name == last_name)
                include_in_survey = "True" if result.include_in_survey == "Y" else "False"
                op_date = f"{result.date}T00:00:00"

                # Create or get the Site OPERATIONS record
                defaults = {'vessel_lu': vessel_lu_id.lookup,
                            'day_of_cruise': result.day_of_survey,
                            'area': area.area_description,
                            'fpc': fpc_id.personnel,
                            'date': op_date,
                            'site': area.site,
                            'recorder': fpc_id.personnel,
                            'site_type_lu': site_type_lu_id,
                            'include_in_survey': include_in_survey,
                            'operation_type_lu': site_op_type,
                            'is_rca': 'False',
                            'is_mpa': 'False'
                            }
                set_op, set_created = Operations.get_or_create(operation_number=result.set_id, defaults=defaults)

                # Create or get the OPERATION_ATTRIBUTES records to include:
                #  TODO - Angler Start Time - need to get this from the ImportHookLogger Drop Time value, otherwise
                #          it is not captured anywhere else I don't believe.  Do this in HookMatrixImport instance

                # Create or get the OPERATION_DETAILS record - Site Comments
                # Get Tide Station + Distance to Station
                tide_station_id = area.tide_station.tide_station
                distance_to_tide_station_nm = self.get_distance_to_tide_station(site_id=area.site,
                                                                                tide_station_id=tide_station_id)
                details_defaults = {
                    'tide_station': tide_station_id,
                    'distance_to_tide_station_nm': distance_to_tide_station_nm,
                    'habitat_comments': result.habitat_notes,
                    'fish_meter_comments': result.fishfinder_notes,
                    'ocean_weather_comments': result.ocean_weather_notes,
                    'general_comments': result.general_notes
                }
                op_details, op_details_created = OperationDetails.get_or_create(operation=set_op.operation,
                                                                                defaults=details_defaults)

                # Create or get the EVENT record
                event_type_lu_id = Lookups.get(Lookups.type == "Event Type", Lookups.value == result.drop_number).lookup
                start_date_time = f"{result.date}T{result.drop_time}"
                start_latitude = self.get_lat_lon(input=result.start_latitude)
                start_longitude = self.get_lat_lon(input=result.start_longitude)
                if start_longitude is not None:
                    start_longitude = -start_longitude
                end_latitude = self.get_lat_lon(input=result.end_latitude)
                end_longitude = self.get_lat_lon(input=result.end_longitude)
                if end_longitude is not None:
                    end_longitude = -end_longitude

                event_defaults = {
                     'start_date_time': start_date_time,
                     'start_latitude': start_latitude,
                     'end_latitude': end_latitude,
                     'start_longitude': start_longitude,
                     'end_longitude': end_longitude,
                     'start_depth_ftm': result.start_depth_ftm,
                     'end_depth_ftm': result.end_depth_ftm,
                     'drop_type_lu': drop_type_lu_id,
                     'include_in_results': 'True'
                 }
                logging.info(f"\t\tevent_defaults={event_defaults}")
                event_item, event_created = Events.get_or_create(operation=set_op.operation,
                                                                 event_type_lu=event_type_lu_id,
                                                                 defaults=event_defaults)

            except Exception as ex:

                errors.append(f"row={i+1}, set_id={result.set_id} > {ex}")

        for err in errors:

            logging.info(f"{err}")


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


    # ***** NOTE NOTE NOTE - Update the HookandlineFpcDB_Model.py to point to the right xlsx path for the correct vessel

    # hli = HookLoggerImporter()
    # hli.process_data()

    # hmi = HookMatrixImporter()
    # hmi.process_data()

    csi = CutterStationImporter()
    csi.process_data()
    #
    # si = SpecimenImporter()
    # si.process_data()