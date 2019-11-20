from peewee import *
import os
import sys
import __main__
# from pathlib import Path

try:
    app_name = os.path.basename(__main__.__file__).strip(".py")
except:
    app_name = sys.executable

if app_name == "ImportPaperData":
    homedir = os.path.expanduser("~")
    desktop = os.path.join(homedir, 'Desktop')
    # desktop = os.path.join(str(Path.home()), 'Desktop')

    # filename = "TO_2017_hookandline_fpc_MASTER.db"
    # filename = "MI_2017_hookandline_fpc_MASTER.db"
    # filename = "AG_2017_hookandline_fpc_MASTER.db"

    dir = r"C:\Todd.Hay\Projects\HookAndLine\2018 Data Processing\Mirage DBs"
    filename = "hookandline_fpc_1_recovered.db"

    db = os.path.join(dir, filename)

elif app_name == "MergeFpcDatabases":

    path = r'C:\Todd.Hay\Projects\HookAndLine\2018 Data Processing\Mirage DBs'
    db1 = 'hookandline_fpc_1_recovered.db'
    db2 = 'hookandline_fpc_2.db'
    db = os.path.join(path, db1)
    db2_full_path = os.path.join(path, db2)

else:
    if os.path.exists("data"):
        db = r"data\hookandline_fpc.db"
    elif os.path.exists(r"..\..\data"):
        db = r"..\..\data\hookandline_fpc.db"

database = SqliteDatabase(db, pragmas={'foreign_keys': 1})

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

class BarcodesLu(BaseModel):
    barcode = IntegerField(db_column='BARCODE', index=True)
    barcode_type = TextField(db_column='BARCODE_TYPE', null=True)
    duplicate_count = IntegerField(db_column='DUPLICATE_COUNT', null=True)
    year = IntegerField(db_column='YEAR', null=True)

    class Meta:
        db_table = 'BARCODES_LU'

class TideStations(BaseModel):
    datum = TextField(db_column='DATUM', null=True)
    latitude = TextField(db_column='LATITUDE', null=True)
    longitude = TextField(db_column='LONGITUDE', null=True)
    prediction = TextField(db_column='PREDICTION', null=True)
    state = TextField(db_column='STATE', null=True)
    station = TextField(db_column='STATION_ID', null=True)
    station_name = TextField(db_column='STATION_NAME', null=True)
    tide_station = PrimaryKeyField(db_column='TIDE_STATION_ID')
    time_zone = TextField(db_column='TIME_ZONE', null=True)

    class Meta:
        db_table = 'TIDE_STATIONS'

class Sites(BaseModel):
    abbreviation = TextField(db_column='ABBREVIATION', null=True)
    area_description = TextField(db_column='AREA_DESCRIPTION', null=True)
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    is_cowcod_conservation_area = TextField(db_column='IS_COWCOD_CONSERVATION_AREA', null=True)
    latitude = FloatField(db_column='LATITUDE', null=True)
    longitude = FloatField(db_column='LONGITUDE', null=True)
    name = TextField(db_column='NAME')
    site = PrimaryKeyField(db_column='SITE_ID')
    tide_station = ForeignKeyField(db_column='TIDE_STATION_ID', null=True, model=TideStations, to_field='tide_station')

    class Meta:
        db_table = 'SITES'

class Personnel(BaseModel):
    email_address = TextField(db_column='EMAIL_ADDRESS', null=True)
    first_name = TextField(db_column='FIRST_NAME', null=True)
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    is_science_team = TextField(db_column='IS_SCIENCE_TEAM', null=True)
    last_name = TextField(db_column='LAST_NAME', null=True)
    personnel = PrimaryKeyField(db_column='PERSONNEL_ID')
    phone_number = TextField(db_column='PHONE_NUMBER', null=True)

    class Meta:
        db_table = 'PERSONNEL'

class Operations(BaseModel):
    area = TextField(db_column='AREA', null=True)
    date = TextField(db_column='DATE', null=True)
    day_of_cruise = IntegerField(db_column='DAY_OF_CRUISE', null=True)
    fpc = ForeignKeyField(db_column='FPC_ID', null=True, model=Personnel, to_field='personnel')
    include_in_survey = TextField(db_column='INCLUDE_IN_SURVEY', null=True)
    is_mpa = TextField(db_column='IS_MPA', null=True)
    is_rca = TextField(db_column='IS_RCA', null=True)
    operation = PrimaryKeyField(db_column='OPERATION_ID')
    operation_number = TextField(db_column='OPERATION_NUMBER', null=True, unique=True)
    operation_type_lu = IntegerField(db_column='OPERATION_TYPE_LU_ID', null=True)
    parent_operation = ForeignKeyField(db_column='PARENT_OPERATION_ID', null=True, model='self', to_field='operation', on_delete='CASCADE')
    processing_status = TextField(db_column='PROCESSING_STATUS', null=True)
    recorder = ForeignKeyField(db_column='RECORDER_ID', null=True, model=Personnel, related_name='PERSONNEL_recorder_set', to_field='personnel')
    site = ForeignKeyField(db_column='SITE_ID', null=True, model=Sites, to_field='site')
    site_type_lu = IntegerField(db_column='SITE_TYPE_LU_ID', null=True)
    vessel_lu = IntegerField(db_column='VESSEL_LU_ID', null=True)
    random_drop_1 = IntegerField(db_column='RANDOM_DROP_1', null=True)
    random_drop_2 = IntegerField(db_column='RANDOM_DROP_2', null=True)

    class Meta:
        db_table = 'OPERATIONS'

class PrincipalInvestigatorLu(BaseModel):
    email_address = TextField(db_column='EMAIL_ADDRESS', null=True)
    full_name = TextField(db_column='FULL_NAME', null=True)
    last_name = TextField(db_column='LAST_NAME', null=True)
    organization = TextField(db_column='ORGANIZATION', null=True)
    phone_number = TextField(db_column='PHONE_NUMBER', null=True)
    principal_investigator = PrimaryKeyField(db_column='PRINCIPAL_INVESTIGATOR_ID')

    class Meta:
        db_table = 'PRINCIPAL_INVESTIGATOR_LU'

class TaxonomyLu(BaseModel):
    common_name_1 = TextField(db_column='COMMON_NAME_1', null=True)
    common_name_2 = TextField(db_column='COMMON_NAME_2', null=True)
    common_name_3 = TextField(db_column='COMMON_NAME_3', null=True)
    historical_depth_max = FloatField(db_column='HISTORICAL_DEPTH_MAX', null=True)
    historical_depth_min = FloatField(db_column='HISTORICAL_DEPTH_MIN', null=True)
    historical_lat_max = FloatField(db_column='HISTORICAL_LAT_MAX', null=True)
    historical_lat_min = FloatField(db_column='HISTORICAL_LAT_MIN', null=True)
    historical_length_max = FloatField(db_column='HISTORICAL_LENGTH_MAX', null=True)
    historical_length_min = FloatField(db_column='HISTORICAL_LENGTH_MIN', null=True)
    is_rare = TextField(db_column='IS_RARE', null=True)
    parent_taxonomy = ForeignKeyField(db_column='PARENT_TAXONOMY_ID', null=True, model='self', to_field='taxonomy')
    scientific_name = TextField(db_column='SCIENTIFIC_NAME', null=True)
    taxonomic_level = TextField(db_column='TAXONOMIC_LEVEL', null=True)
    taxonomy = PrimaryKeyField(db_column='TAXONOMY_ID')

    class Meta:
        db_table = 'TAXONOMY_LU'

class ProtocolLu(BaseModel):
    action_type = IntegerField(db_column='ACTION_TYPE_ID', null=True)
    activation_date = TextField(db_column='ACTIVATION_DATE', null=True)
    deactivation_date = TextField(db_column='DEACTIVATION_DATE', null=True)
    display_name = TextField(db_column='DISPLAY_NAME', null=True)
    parent_protocol = ForeignKeyField(db_column='PARENT_PROTOCOL_ID', null=True, model='self', to_field='protocol')
    protocol = PrimaryKeyField(db_column='PROTOCOL_ID')
    storage_type = IntegerField(db_column='STORAGE_TYPE_ID', null=True)

    class Meta:
        db_table = 'PROTOCOL_LU'

class StratumLu(BaseModel):
    name = TextField(db_column='NAME', null=True)
    range_max = FloatField(db_column='RANGE_MAX', null=True)
    range_min = FloatField(db_column='RANGE_MIN', null=True)
    range_units = TextField(db_column='RANGE_UNITS', null=True)
    stratum = PrimaryKeyField(db_column='STRATUM_ID')
    stratum_subtype = TextField(db_column='STRATUM_SUBTYPE', null=True)
    stratum_type = IntegerField(db_column='STRATUM_TYPE_ID', null=True)
    value = TextField(db_column='VALUE', null=True)

    class Meta:
        db_table = 'STRATUM_LU'

class SpeciesSamplingPlanLu(BaseModel):
    count = IntegerField(db_column='COUNT', null=True)
    count_type = IntegerField(db_column='COUNT_TYPE_ID', null=True)
    display_name = TextField(db_column='DISPLAY_NAME', null=True)
    parent_species_sampling_plan = ForeignKeyField(db_column='PARENT_SPECIES_SAMPLING_PLAN_ID', null=True, model='self', to_field='species_sampling_plan')
    plan_name = TextField(db_column='PLAN_NAME', null=True)
    principal_investigator = ForeignKeyField(db_column='PRINCIPAL_INVESTIGATOR_ID', null=True, model=PrincipalInvestigatorLu, to_field='principal_investigator')
    protocol = ForeignKeyField(db_column='PROTOCOL_ID', null=True, model=ProtocolLu, to_field='protocol')
    species_sampling_plan = PrimaryKeyField(db_column='SPECIES_SAMPLING_PLAN_ID')
    stratum = ForeignKeyField(db_column='STRATUM_ID', null=True, model=StratumLu, to_field='stratum')
    taxonomy = ForeignKeyField(db_column='TAXONOMY_ID', null=True, model=TaxonomyLu, to_field='taxonomy')

    class Meta:
        db_table = 'SPECIES_SAMPLING_PLAN_LU'
        indexes = (
            (('plan_name', 'taxonomy'), True),
        )

class CatchContentLu(BaseModel):
    catch_content = PrimaryKeyField(db_column='CATCH_CONTENT_ID')
    content_type_lu = IntegerField(db_column='CONTENT_TYPE_LU_ID', null=True)
    display_name = TextField(db_column='DISPLAY_NAME', null=True)
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    is_last_n_operations = TextField(db_column='IS_LAST_N_OPERATIONS', null=True)
    is_most_recent = TextField(db_column='IS_MOST_RECENT', null=True)
    taxonomy = ForeignKeyField(db_column='TAXONOMY_ID', null=True, model=TaxonomyLu, to_field='taxonomy')

    class Meta:
        db_table = 'CATCH_CONTENT_LU'

class Catch(BaseModel):
    catch = PrimaryKeyField(db_column='CATCH_ID')
    catch_content = ForeignKeyField(db_column='CATCH_CONTENT_ID', null=True, model=CatchContentLu,
                                    to_field='catch_content')
    best_catch_content = ForeignKeyField(db_column='BEST_CATCH_CONTENT_ID', null=True, model=CatchContentLu,
                                         related_name='best_catch_content', to_field='catch_content')
    hm_catch_content = ForeignKeyField(db_column='HM_CATCH_CONTENT_ID', null=True, model=CatchContentLu,
                                       related_name='hm_catch_content', to_field='catch_content')
    cs_catch_content = ForeignKeyField(db_column='CS_CATCH_CONTENT_ID', null=True, model=CatchContentLu,
                                       related_name='cs_catch_content', to_field='catch_content')
    content_action_type = IntegerField(db_column='CONTENT_ACTION_TYPE_ID', null=True)
    display_name = TextField(db_column='DISPLAY_NAME', null=True)
    is_debris = TextField(db_column='IS_DEBRIS', null=True)
    is_mix = TextField(db_column='IS_MIX', null=True)
    is_subsample = TextField(db_column='IS_SUBSAMPLE', null=True)
    is_weight_estimated = TextField(db_column='IS_WEIGHT_ESTIMATED', null=True)
    mix_number = IntegerField(db_column='MIX_NUMBER', null=True)
    note = TextField(db_column='NOTE', null=True)
    operation = ForeignKeyField(db_column='OPERATION_ID', null=True, model=Operations, to_field='operation', on_delete='CASCADE')
    operation_type = IntegerField(db_column='OPERATION_TYPE_ID', null=True)
    parent_catch = ForeignKeyField(db_column='PARENT_CATCH_ID', null=True, model='self', to_field='catch', on_delete='CASCADE')
    receptacle_seq = TextField(db_column='RECEPTACLE_SEQ', null=True)
    receptacle_type = IntegerField(db_column='RECEPTACLE_TYPE_ID', null=True)
    result_type = IntegerField(db_column='RESULT_TYPE_ID', null=True)
    sample_count_int = IntegerField(db_column='SAMPLE_COUNT_INT', null=True)
    species_sampling_plan = ForeignKeyField(db_column='SPECIES_SAMPLING_PLAN_ID', null=True, model=SpeciesSamplingPlanLu, to_field='species_sampling_plan')
    weight_kg = FloatField(db_column='WEIGHT_KG', null=True)

    class Meta:
        db_table = 'CATCH'
        indexes = (
            (('parent_catch', 'receptacle_seq'), True),
        )

class Equipment(BaseModel):
    activation_date = TextField(db_column='ACTIVATION_DATE', null=True)
    deactivation_date = TextField(db_column='DEACTIVATION_DATE', null=True)
    description = TextField(db_column='DESCRIPTION', null=True)
    equipment_category = IntegerField(db_column='EQUIPMENT_CATEGORY_ID', null=True)
    equipment = PrimaryKeyField(db_column='EQUIPMENT_ID')
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    is_backdeck = TextField(db_column='IS_BACKDECK', null=True)
    is_sensor_file = TextField(db_column='IS_SENSOR_FILE', null=True)
    is_wheelhouse = TextField(db_column='IS_WHEELHOUSE', null=True)
    model = TextField(db_column='MODEL', null=True)
    name = TextField(db_column='NAME', null=True)
    organization = IntegerField(db_column='ORGANIZATION_ID', null=True)

    class Meta:
        db_table = 'EQUIPMENT'

class DeployedEquipment(BaseModel):
    activation_date = TextField(db_column='ACTIVATION_DATE', null=True)
    baud_rate = IntegerField(db_column='BAUD_RATE', null=True)
    com_port = TextField(db_column='COM_PORT', null=True)
    data_bits = IntegerField(db_column='DATA_BITS', null=True)
    deactivation_date = TextField(db_column='DEACTIVATION_DATE', null=True)
    deployed_equipment = PrimaryKeyField(db_column='DEPLOYED_EQUIPMENT_ID')
    equipment = ForeignKeyField(db_column='EQUIPMENT_ID', null=True, model=Equipment, to_field='equipment')
    flow_control = TextField(db_column='FLOW_CONTROL', null=True)
    moxa_port = IntegerField(db_column='MOXA_PORT', null=True)
    parity = TextField(db_column='PARITY', null=True)
    reader_or_writer = TextField(db_column='READER_OR_WRITER', null=True)
    stop_bits = FloatField(db_column='STOP_BITS', null=True)

    class Meta:
        db_table = 'DEPLOYED_EQUIPMENT'

class Events(BaseModel):
    drift_direction_deg = FloatField(db_column='DRIFT_DIRECTION_DEG', null=True)
    drift_distance_nm = FloatField(db_column='DRIFT_DISTANCE_NM', null=True)
    drift_speed_kts = FloatField(db_column='DRIFT_SPEED_KTS', null=True)
    drop_type_lu = IntegerField(db_column='DROP_TYPE_LU_ID', null=True)
    end_date_time = TextField(db_column='END_DATE_TIME', null=True)
    end_depth_ftm = FloatField(db_column='END_DEPTH_FTM', null=True)
    end_latitude = FloatField(db_column='END_LATITUDE', null=True)
    end_longitude = FloatField(db_column='END_LONGITUDE', null=True)
    event = PrimaryKeyField(db_column='EVENT_ID')
    event_type_lu = IntegerField(db_column='EVENT_TYPE_LU_ID', null=True)
    include_in_results = TextField(db_column='INCLUDE_IN_RESULTS', null=True)
    operation = ForeignKeyField(db_column='OPERATION_ID', null=True, model=Operations, to_field='operation', on_delete='CASCADE')
    parent_event = ForeignKeyField(db_column='PARENT_EVENT_ID', null=True, model='self', to_field='event', on_delete='CASCADE')
    start_date_time = TextField(db_column='START_DATE_TIME', null=True)
    start_depth_ftm = FloatField(db_column='START_DEPTH_FTM', null=True)
    start_latitude = FloatField(db_column='START_LATITUDE', null=True)
    start_longitude = FloatField(db_column='START_LONGITUDE', null=True)
    surface_temperature_avg_c = FloatField(db_column='SURFACE_TEMPERATURE_AVG_C', null=True)
    tide_height_m = FloatField(db_column='TIDE_HEIGHT_M', null=True)
    true_wind_direction_avg_deg = FloatField(db_column='TRUE_WIND_DIRECTION_AVG_DEG', null=True)
    true_wind_speed_avg_kts = FloatField(db_column='TRUE_WIND_SPEED_AVG_KTS', null=True)

    class Meta:
        db_table = 'EVENTS'

class SensorDbFiles(BaseModel):
    end_date_time = TextField(db_column='END_DATE_TIME', null=True)
    file_name = TextField(db_column='FILE_NAME', null=True)
    sensor_db_file = PrimaryKeyField(db_column='SENSOR_DB_FILE_ID')
    start_date_time = TextField(db_column='START_DATE_TIME', null=True)

    class Meta:
        db_table = 'SENSOR_DB_FILES'

class EventMeasurements(BaseModel):
    date_time = TextField(db_column='DATE_TIME', null=True)
    event = ForeignKeyField(db_column='EVENT_ID', null=True, model=Events, to_field='event', on_delete='CASCADE')
    event_measurement = PrimaryKeyField(db_column='EVENT_MEASUREMENT_ID')
    measurement_alpha = TextField(db_column='MEASUREMENT_ALPHA', null=True)
    measurement_number = FloatField(db_column='MEASUREMENT_NUMBER', null=True)
    measurement_type_lu = IntegerField(db_column='MEASUREMENT_TYPE_LU_ID', null=True)
    raw_sentence = IntegerField(db_column='RAW_SENTENCE_ID', null=True)
    sensor_db_file = ForeignKeyField(db_column='SENSOR_DB_FILE_ID', null=True, model=SensorDbFiles, to_field='sensor_db_file')

    class Meta:
        db_table = 'EVENT_MEASUREMENTS'

class LengthWeightRelationshipLu(BaseModel):
    boundary_type = TextField(db_column='BOUNDARY_TYPE', null=True)
    final_regr_stderr = FloatField(db_column='FINAL_REGR_STDERR', null=True)
    length_weight_relationship = PrimaryKeyField(db_column='LENGTH_WEIGHT_RELATIONSHIP_ID')
    lw_coefficient_cmkg = FloatField(db_column='LW_COEFFICIENT_CMKG', null=True)
    lw_exponent_cmkg = FloatField(db_column='LW_EXPONENT_CMKG', null=True)
    lw_regression = IntegerField(db_column='LW_REGRESSION_ID', null=True)
    lw_regression_set = IntegerField(db_column='LW_REGRESSION_SET_ID', null=True)
    lw_rsquared = FloatField(db_column='LW_RSQUARED', null=True)
    lw_samplesize = TextField(db_column='LW_SAMPLESIZE', null=True)
    lw_source = TextField(db_column='LW_SOURCE', null=True)
    project = IntegerField(db_column='PROJECT_ID', null=True)
    set_name = TextField(db_column='SET_NAME', null=True)
    set_year = TextField(db_column='SET_YEAR', null=True)
    sex_code = TextField(db_column='SEX_CODE', null=True)
    taxonomy = IntegerField(db_column='TAXONOMY_ID', null=True)

    class Meta:
        db_table = 'LENGTH_WEIGHT_RELATIONSHIP_LU'

class Lookups(BaseModel):
    description = TextField(db_column='DESCRIPTION', null=True)
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    lookup = PrimaryKeyField(db_column='LOOKUP_ID')
    subvalue = TextField(db_column='SUBVALUE', null=True)
    type = TextField(db_column='TYPE', null=True)
    value = TextField(db_column='VALUE', null=True)

    class Meta:
        db_table = 'LOOKUPS'

class MoonPhases(BaseModel):
    moon_phase = PrimaryKeyField(db_column='MOON_PHASE_ID')

    class Meta:
        db_table = 'MOON_PHASES'

class Notes(BaseModel):
    data_item = IntegerField(db_column='DATA_ITEM_ID', null=True)
    date_time = TextField(db_column='DATE_TIME', null=True)
    is_data_issue = TextField(db_column='IS_DATA_ISSUE', null=True)
    is_haul_validation = TextField(db_column='IS_HAUL_VALIDATION', null=True)
    is_software_issue = TextField(db_column='IS_SOFTWARE_ISSUE', null=True)
    note = TextField(db_column='NOTE', null=True)
    note_id = PrimaryKeyField(db_column='NOTE_ID')
    operation = ForeignKeyField(db_column='OPERATION_ID', model=Operations, to_field='operation', null=True, on_delete='CASCADE')
    person = TextField(db_column='PERSON', null=True)
    app_name = TextField(db_column='APP_NAME', null=True)
    screen_name = TextField(db_column='SCREEN_NAME', null=True)
    hl_drop = TextField(db_column='HL_DROP', null=True)
    hl_angler = TextField(db_column='HL_ANGLER', null=True)
    screen_type = IntegerField(db_column='SCREEN_TYPE_ID', null=True)

    class Meta:
        db_table = 'NOTES'

class OperationDetails(BaseModel):
    ctd_bottom_temp_c = FloatField(db_column='CTD_BOTTOM_TEMP_C', null=True)
    ctd_depth_m = FloatField(db_column='CTD_DEPTH_M', null=True)
    ctd_do2_aanderaa_ml_per_l = FloatField(db_column='CTD_DO2_AANDERAA_ML_PER_L', null=True)
    ctd_do2_sbe43_ml_per_l = FloatField(db_column='CTD_DO2_SBE43_ML_PER_L', null=True)
    ctd_fluorescence_ug_per_l = FloatField(db_column='CTD_FLUORESCENCE_UG_PER_L', null=True)
    ctd_salinity_psu = FloatField(db_column='CTD_SALINITY_PSU', null=True)
    ctd_turbidity_ntu = FloatField(db_column='CTD_TURBIDITY_NTU', null=True)
    distance_to_tide_station_nm = FloatField(db_column='DISTANCE_TO_TIDE_STATION_NM', null=True)
    fish_meter_comments = TextField(db_column='FISH_METER_COMMENTS', null=True)
    flow_ft_per_hr = FloatField(db_column='FLOW_FT_PER_HR', null=True)
    general_comments = TextField(db_column='GENERAL_COMMENTS', null=True)
    habitat_comments = TextField(db_column='HABITAT_COMMENTS', null=True)
    moon_fullness_percent = FloatField(db_column='MOON_FULLNESS_PERCENT', null=True)
    moon_phase_lu = IntegerField(db_column='MOON_PHASE_LU_ID', null=True)
    ocean_weather_comments = TextField(db_column='OCEAN_WEATHER_COMMENTS', null=True)
    operation_details = PrimaryKeyField(db_column='OPERATION_DETAILS_ID')
    operation = ForeignKeyField(db_column='OPERATION_ID', null=True, model=Operations, to_field='operation', on_delete='CASCADE')
    sunrise_time = TextField(db_column='SUNRISE_TIME', null=True)
    sunset_time = TextField(db_column='SUNSET_TIME', null=True)
    swell_direction_deg = FloatField(db_column='SWELL_DIRECTION_DEG', null=True)
    swell_height_ft = FloatField(db_column='SWELL_HEIGHT_FT', null=True)
    tide_state_lu = IntegerField(db_column='TIDE_STATE_LU_ID', null=True)
    tide_station = ForeignKeyField(db_column='TIDE_STATION_ID', null=True, model=TideStations, to_field='tide_station')
    tide_type_lu = IntegerField(db_column='TIDE_TYPE_LU_ID', null=True)
    wave_height_ft = FloatField(db_column='WAVE_HEIGHT_FT', null=True)

    class Meta:
        db_table = 'OPERATION_DETAILS'

class OperationAttributes(BaseModel):

    operation_attribute = PrimaryKeyField(db_column='OPERATION_ATTRIBUTE_ID')
    operation = ForeignKeyField(db_column='OPERATION_ID', null=True, model=Operations, to_field='operation', on_delete='CASCADE')
    attribute_numeric = FloatField(db_column='ATTRIBUTE_NUMERIC', null=True)
    attribute_alpha = TextField(db_column='ATTRIBUTE_ALPHA', null=True)
    attribute_type_lu = IntegerField(db_column='ATTRIBUTE_TYPE_LU_ID', null=True)

    class Meta:
        db_table = 'OPERATION_ATTRIBUTES'

class ParsingRules(BaseModel):
    delimiter = TextField(db_column='DELIMITER', null=True)
    end_position = IntegerField(db_column='END_POSITION', null=True)
    equipment = ForeignKeyField(db_column='EQUIPMENT_ID', null=True, model=Equipment, to_field='equipment')
    field_position = IntegerField(db_column='FIELD_POSITION', null=True)
    fixed_or_delimited = TextField(db_column='FIXED_OR_DELIMITED', null=True)
    is_line_starting_substr = TextField(db_column='IS_LINE_STARTING_SUBSTR', null=True)
    line_ending = TextField(db_column='LINE_ENDING', null=True)
    line_starting = TextField(db_column='LINE_STARTING', null=True)
    measurement_lu = IntegerField(db_column='MEASUREMENT_LU_ID', null=True)
    parsing_rules = PrimaryKeyField(db_column='PARSING_RULES_ID')
    priority = IntegerField(db_column='PRIORITY', null=True)
    start_position = IntegerField(db_column='START_POSITION', null=True)

    class Meta:
        db_table = 'PARSING_RULES'

class PiActionCodesLu(BaseModel):
    action_type = IntegerField(db_column='ACTION_TYPE_ID', null=True)
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    pi_action_code = PrimaryKeyField(db_column='PI_ACTION_CODE_ID')
    principal_investigator = ForeignKeyField(db_column='PRINCIPAL_INVESTIGATOR_ID', null=True, model=PrincipalInvestigatorLu, to_field='principal_investigator')

    class Meta:
        db_table = 'PI_ACTION_CODES_LU'

class Settings(BaseModel):
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    parameter = TextField(db_column='PARAMETER', null=True)
    settings = PrimaryKeyField(db_column='SETTINGS_ID')
    type = TextField(db_column='TYPE', null=True)
    value = TextField(db_column='VALUE', null=True)

    class Meta:
        db_table = 'SETTINGS'

class Specimen(BaseModel):
    action_type = IntegerField(db_column='ACTION_TYPE_ID', null=True)
    alpha_value = TextField(db_column='ALPHA_VALUE', null=True)
    catch = ForeignKeyField(db_column='CATCH_ID', null=True, model=Catch, to_field='catch', on_delete='CASCADE')
    measurement_type = IntegerField(db_column='MEASUREMENT_TYPE_ID', null=True)
    note = TextField(db_column='NOTE', null=True)
    numeric_value = FloatField(db_column='NUMERIC_VALUE', index=True, null=True)
    parent_specimen = ForeignKeyField(db_column='PARENT_SPECIMEN_ID', null=True, model='self', to_field='specimen', on_delete='CASCADE')
    species_sampling_plan = ForeignKeyField(db_column='SPECIES_SAMPLING_PLAN_ID', null=True, model=SpeciesSamplingPlanLu, to_field='species_sampling_plan')
    specimen = PrimaryKeyField(db_column='SPECIMEN_ID')

    class Meta:
        db_table = 'SPECIMENS'

class Sitemetadata(BaseModel):
    active = TextField(db_column='Active', null=True)
    areadesc = TextField(db_column='AreaDesc', null=True)
    cowcodconservationarea_ = TextField(db_column='CowcodConservationArea?', null=True)
    sitelatitude = TextField(db_column='SiteLatitude', null=True)
    sitelongitude = TextField(db_column='SiteLongitude', null=True)
    sitename = TextField(db_column='SiteName', null=True)
    tidestation = TextField(db_column='TideStation', null=True)

    class Meta:
        db_table = 'SiteMetadata'

class TideMeasurements(BaseModel):
    date = TextField(db_column='DATE', null=True)
    high_or_low = TextField(db_column='HIGH_OR_LOW', null=True)
    prediction_cm = FloatField(db_column='PREDICTION_CM', null=True)
    prediction_ft = FloatField(db_column='PREDICTION_FT', null=True)
    tide_measurement = PrimaryKeyField(db_column='TIDE_MEASUREMENT_ID')
    tide_station = ForeignKeyField(db_column='TIDE_STATION_ID', null=True, model=TideStations, to_field='tide_station')
    time = TextField(db_column='TIME', null=True)

    class Meta:
        db_table = 'TIDE_MEASUREMENTS'

class ValidationsLu(BaseModel):
    description = TextField(db_column='DESCRIPTION', null=True)
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    method = TextField(db_column='METHOD', null=True)
    name = TextField(db_column='NAME', null=True)
    object = TextField(db_column='OBJECT', null=True)
    validation = PrimaryKeyField(db_column='VALIDATION_ID')
    validation_type = IntegerField(db_column='VALIDATION_TYPE_ID', null=True)

    class Meta:
        db_table = 'VALIDATIONS_LU'

class ImportHookLogger(BaseModel):
    set_id = TextField(db_column='SetID', null=True)
    sites_name = TextField(db_column='Sites Name', null=True)
    vessel = TextField(db_column='Vessel', null=True)
    date = TextField(db_column='Date', null=True)
    drop_time = TextField(db_column='Drop Time', null=True)
    day_of_survey = TextField(db_column='Day of Survey', null=True)
    recorded_by = TextField(db_column='Recorded By', null=True)
    include_in_survey = TextField(db_column='Include in Survey?', null=True)
    drop_number = TextField(db_column='Drop Number', null=True)
    start_latitude = TextField(db_column='Start Latitude', null=True)
    end_latitude = TextField(db_column='End Latitude', null=True)
    start_longitude = TextField(db_column='Start Longitude', null=True)
    end_longitude = TextField(db_column='End Longitude', null=True)
    start_depth_ftm = TextField(db_column='Start Depth (ftm)', null=True)
    end_depth_ftm = TextField(db_column='End Depth (ftm)', null=True)
    habitat_notes = TextField(db_column='Habitat Notes', null=True)
    fishfinder_notes = TextField(db_column='Fishfinder Notes', null=True)
    ocean_weather_notes = TextField(db_column='Ocean/Weather Notes', null=True)
    general_notes = TextField(db_column='General Notes', null=True)

    class Meta:
        db_table = 'ImportHookLogger'
        primary_key = False


class ImportHookMatrix(BaseModel):
    set_id = TextField(db_column='SetID', null=True)
    sites_name = TextField(db_column='SITES.NAME', null=True)
    vessel = TextField(db_column='VESSEL', null=True)
    drop = TextField(db_column='Drop', null=True)
    angler = TextField(db_column='Angler', null=True)
    angler_name = TextField(db_column='Angler Name', null=True)
    start = TextField(db_column='Start', null=True)
    begin_fishing = TextField(db_column='Begin Fishing', null=True)
    first_bite = TextField(db_column='First Bite', null=True)
    retrieval = TextField(db_column='Retrieval', null=True)
    at_surface = TextField(db_column='At Surface', null=True)
    include_in_survey = TextField(db_column='Include in Survey?', null=True)
    gear_performance = TextField(db_column='Gear Performance', null=True)
    hook1 = TextField(db_column='Hook 1', null=True)
    hook2 = TextField(db_column='Hook 2', null=True)
    hook3 = TextField(db_column='Hook 3', null=True)
    hook4 = TextField(db_column='Hook 4', null=True)
    hook5 = TextField(db_column='Hook 5', null=True)
    sinker_weight = TextField(db_column='Sinker Weight', null=True)
    recorded_by = TextField(db_column='Recorded By', null=True)
    notes = TextField(db_column='Notes', null=True)

    class Meta:
        db_table = 'ImportHookMatrix'
        primary_key = False


class ImportCutterStation(BaseModel):
    set_id = TextField(db_column='Set ID', null=True)
    sites_name = TextField(db_column='SITES.NAME', null=True)
    vessel = TextField(db_column='Vessel', null=True)
    drop_date_time = TextField(db_column='Drop Date-Time', null=True)
    angler = TextField(db_column='Angler', null=True)
    drop = TextField(db_column='Drop', null=True)
    hook = TextField(db_column='Hook', null=True)
    specimen = TextField(db_column='Specimen ID', null=True)
    species = TextField(db_column='Species', null=True)
    length = TextField(db_column='Length', null=True)
    weight = TextField(db_column='Weight', null=True)
    sex = TextField(db_column='Sex', null=True)
    finclip = TextField(db_column='Finclip ID', null=True)
    otolith = TextField(db_column='Otolith ID', null=True)
    disposition = TextField(db_column='Disposition', null=True)
    tag_number = TextField(db_column='Tag Number', null=True)
    recorded_by = TextField(db_column='Recorded By', null=True)
    notes = TextField(db_column='Notes', null=True)

    class Meta:
        db_table = 'ImportCutterStation'
        primary_key = False


class ImportSpecimen(BaseModel):
    set_id = TextField(db_column='Set ID', null=True)
    sites_name = TextField(db_column='SITES.NAME', null=True)
    vessel = TextField(db_column='Vessel', null=True)
    drop_date_time = TextField(db_column='Drop Date-Time', null=True)
    specimen = TextField(db_column='Specimen ID', null=True)
    parent_specimen = TextField(db_column='Parent Specimen ID', null=True)
    species = TextField(db_column='Species', null=True)
    finclip = TextField(db_column='Finclip ID', null=True)
    otolith = TextField(db_column='Otolith ID', null=True)
    plan_name = TextField(db_column='PLAN_NAME', null=True)
    specimen_type = TextField(db_column='Specimen Type', null=True)
    specimen_number = TextField(db_column='Specimen Number', null=True)

    class Meta:
        db_table = 'ImportSpecimen'
        primary_key = False


class HookLoggerDropView(BaseModel):
    set_id = TextField(db_column='Set ID', null=True)
    site = TextField(db_column='Site', null=True)
    vessel = TextField(db_column='Vessel', null=True)
    date_time = TextField(db_column='Date-Time', null=True)
    day_of_survey = IntegerField(db_column='Day of Survey', null=True)
    recorded_by = TextField(db_column='Recorded By', null=True)
    include_in_survey = TextField(db_column='Include in Survey?', null=True)
    drop_number = TextField(db_column='Drop Number', null=True)
    start_time = TextField(db_column='Start Time', null=True)
    end_time = TextField(db_column='End Time', null=True)
    start_latitude = FloatField(db_column='Start Latitude', null=True)
    end_latitude = FloatField(db_column='End Latitude', null=True)
    start_longitude = FloatField(db_column='Start Longitude', null=True)
    end_longitude = FloatField(db_column='End Longitude', null=True)
    start_depth = FloatField(db_column='Start Depth (ftm)', null=True)
    end_depth = FloatField(db_column='End Depth (ftm)', null=True)
    tide_height = FloatField(db_column='Tide Height (m)', null=True)
    drop_type = TextField(db_column='Drop Type', null=True)
    include_in_survey = TextField(db_column='Include in Survey?', null=True)
    habitat_notes = TextField(db_column='Habitat Notes', null=True)
    fishfinder_notes = TextField(db_column='Fishfinder Notes', null=True)
    ocean_weather_notes = TextField(db_column='Ocean/Weather Notes', null=True)
    general_notes = TextField(db_column='General Notes', null=True)

    class Meta:
        db_table = 'HookLogger_Drop_V'
        primary_key = False


class HookMatrixView(BaseModel):
    set_id = TextField(db_column='Set ID', null=True)
    site = TextField(db_column='Site', null=True)
    vessel = TextField(db_column='Vessel', null=True)
    drop_date_time = TextField(db_column='Drop Date-Time', null=True)
    drop = TextField(db_column='Drop', null=True)
    angler = TextField(db_column='Angler', null=True)
    angler_name = TextField(db_column='Angler Name', null=True)
    start = TextField(db_column='Start', null=True)
    begin_fishing = TextField(db_column='Begin Fishing', null=True)
    first_bite = TextField(db_column='First Bite', null=True)
    retrieval = TextField(db_column='Retrieval', null=True)
    at_surface = TextField(db_column='At Surface', null=True)
    include_in_survey = TextField(db_column='Include in Survey?', null=True)
    gear_performance = TextField(db_column='Gear Performance', null=True)
    hook1 = TextField(db_column='Hook 1', null=True)
    hook2 = TextField(db_column='Hook 2', null=True)
    hook3 = TextField(db_column='Hook 3', null=True)
    hook4 = TextField(db_column='Hook 4', null=True)
    hook5 = TextField(db_column='Hook 5', null=True)
    sinker_weight = TextField(db_column='Sinker Weight', null=True)
    recorded_by = TextField(db_column='Recorded By', null=True)

    class Meta:
        db_table = 'HookMatrix_V'
        primary_key = False


class CutterStationView(BaseModel):
    set_id = TextField(db_column='SetID', null=True)
    site = TextField(db_column='Site', null=True)
    vessel = TextField(db_column='Vessel', null=True)
    drop_date_time = TextField(db_column='Drop Date-Time', null=True)
    angler = TextField(db_column='Angler', null=True)
    drop = TextField(db_column='Drop', null=True)
    hook = TextField(db_column='Hook', null=True)
    operation_type = TextField(db_column='Operation Type', null=True)
    catch_id = TextField(db_column='CATCH_ID', null=True)
    specimen_id = TextField(db_column='Specimen ID', null=True)
    species = TextField(db_column='Species', null=True)
    length = FloatField(db_column='Length', null=True)
    weight = FloatField(db_column='Weight', null=True)
    sex = TextField(db_column='Sex', null=True)
    finclip = TextField(db_column='Finclip ID', null=True)
    otolith = TextField(db_column='Otolith ID', null=True)
    disposition = TextField(db_column='Disposition', null=True)
    tag_number = TextField(db_column='Tag Number', null=True)
    recorded_by = TextField(db_column='Recorded By', null=True)

    class Meta:
        db_table = 'CutterStation_V'
        primary_key = False


class SpeciesReviewView(BaseModel):
    set_id = TextField(db_column='SetID', null=True)
    angler = TextField(db_column='Angler', null=True)
    drop = TextField(db_column='Drop', null=True)
    hook = TextField(db_column='Hook', null=True)
    catch_id = IntegerField(db_column='Catch ID', null=True)
    cs_species = TextField(db_column='CS Species', null=True)
    hm_species = TextField(db_column='HM Species', null=True)
    best_species = TextField(db_column='Best Species', null=True)

    class Meta:
        db_table = 'SPECIES_REVIEW_V'
        primary_key = False


class SqliteSequence(BaseModel):
    name = UnknownField(null=True)  # 
    seq = UnknownField(null=True)  # 

    class Meta:
        db_table = 'sqlite_sequence'

