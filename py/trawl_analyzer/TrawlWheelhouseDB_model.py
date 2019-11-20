from peewee import *
from py.trawl_analyzer.Settings import WheelhouseModel as BaseModel

class UnknownField(object):
    def __init__(self, *_, **__): pass


class CatchPartition(BaseModel):
    aggregate_catch = IntegerField(db_column='AGGREGATE_CATCH_ID', null=True)
    catch_partition = PrimaryKeyField(db_column='CATCH_PARTITION_ID')
    container_sequence = TextField(db_column='CONTAINER_SEQUENCE', null=True)
    notes = TextField(db_column='NOTES', null=True)
    sample_count = TextField(db_column='SAMPLE_COUNT', null=True)
    tare_weight = FloatField(db_column='TARE_WEIGHT', null=True)
    weight_kg = FloatField(db_column='WEIGHT_KG', null=True)

    class Meta:
        db_table = 'CATCH_PARTITION'

class TypesLu(BaseModel):
    category = TextField(db_column='CATEGORY', null=True)
    type = TextField(db_column='TYPE', null=True)
    type_id = PrimaryKeyField(db_column='TYPE_ID')

    class Meta:
        db_table = 'TYPES_LU'

class VesselLu(BaseModel):
    vessel = PrimaryKeyField(db_column='VESSEL_ID')
    vessel_name = TextField(db_column='VESSEL_NAME', null=True)

    class Meta:
        db_table = 'VESSEL_LU'

class Project(BaseModel):
    name = TextField(db_column='NAME', null=True)
    project = PrimaryKeyField(db_column='PROJECT_ID')
    project_type = ForeignKeyField(db_column='PROJECT_TYPE_ID', null=True, model=TypesLu, to_field='type_id')
    year = TextField(db_column='YEAR', null=True)

    class Meta:
        db_table = 'PROJECT'

class OperationalSegment(BaseModel):
    activation_datetime = TextField(db_column='ACTIVATION_DATETIME', null=True)
    deactivation_datetime = TextField(db_column='DEACTIVATION_DATETIME', null=True)
    fpc = IntegerField(db_column='FPC_ID', null=True)
    name = TextField(db_column='NAME', null=True)
    operational_segment = PrimaryKeyField(db_column='OPERATIONAL_SEGMENT_ID')
    operational_segment_type = ForeignKeyField(db_column='OPERATIONAL_SEGMENT_TYPE_ID', null=True, model=TypesLu, to_field='type_id')
    parent_segment = ForeignKeyField(db_column='PARENT_SEGMENT_ID', null=True, model='self', to_field='operational_segment')
    project = ForeignKeyField(db_column='PROJECT_ID', null=True, model=Project, to_field='project')
    scientist_1 = IntegerField(db_column='SCIENTIST_1_ID', null=True)
    scientist_2 = IntegerField(db_column='SCIENTIST_2_ID', null=True)
    sequence_number = IntegerField(db_column='SEQUENCE_NUMBER', null=True)
    vessel = ForeignKeyField(db_column='VESSEL_ID', null=True, model=VesselLu, to_field='vessel')

    class Meta:
        db_table = 'OPERATIONAL_SEGMENT'

class WorkstationsLu(BaseModel):
    workstation = PrimaryKeyField(db_column='WORKSTATION_ID')
    workstation_type = IntegerField(db_column='WORKSTATION_TYPE_ID', null=True)

    class Meta:
        db_table = 'WORKSTATIONS_LU'

class EquipmentCategoryLu(BaseModel):
    can_be_calibrated = TextField(db_column='CAN_BE_CALIBRATED', null=True)
    description = TextField(db_column='DESCRIPTION', null=True)
    equipment_category = PrimaryKeyField(db_column='EQUIPMENT_CATEGORY_ID')
    label = TextField(db_column='LABEL', null=True)
    name = TextField(db_column='NAME')

    class Meta:
        db_table = 'EQUIPMENT_CATEGORY_LU'

class OrganizationLu(BaseModel):
    name = TextField(db_column='NAME', null=True)
    organization = PrimaryKeyField(db_column='ORGANIZATION_ID')

    class Meta:
        db_table = 'ORGANIZATION_LU'

class Equipment(BaseModel):
    activation_date = TextField(db_column='ACTIVATION_DATE', null=True)
    deactivation_date = TextField(db_column='DEACTIVATION_DATE', null=True)
    description = TextField(db_column='DESCRIPTION', null=True)
    equipment_category = ForeignKeyField(db_column='EQUIPMENT_CATEGORY_ID', null=True, model=EquipmentCategoryLu, to_field='equipment_category')
    equipment = PrimaryKeyField(db_column='EQUIPMENT_ID')
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    is_sensor_file = TextField(db_column='IS_SENSOR_FILE', null=True)
    model = TextField(db_column='MODEL', null=True)
    name = TextField(db_column='NAME', null=True)
    organization = ForeignKeyField(db_column='ORGANIZATION_ID', null=True, model=OrganizationLu, to_field='organization')

    class Meta:
        db_table = 'EQUIPMENT'

class DeployedEquipment(BaseModel):
    activation_date = TextField(db_column='ACTIVATION_DATE', null=True)
    baud_rate = UnknownField(db_column='BAUD_RATE', null=True)  # NUMERIC
    com_port = UnknownField(db_column='COM_PORT', null=True)  # NUMERIC
    data_bits = UnknownField(db_column='DATA_BITS', null=True)  # NUMERIC
    deactivation_date = TextField(db_column='DEACTIVATION_DATE', null=True)
    deployed_equipment = PrimaryKeyField(db_column='DEPLOYED_EQUIPMENT_ID')
    equipment = ForeignKeyField(db_column='EQUIPMENT_ID', null=True, model=Equipment, to_field='equipment')
    flow_control = CharField(db_column='FLOW_CONTROL', null=True)
    is_serial_stream = TextField(db_column='IS_SERIAL_STREAM', null=True)
    moxa_port = UnknownField(db_column='MOXA_PORT', null=True)  # NUMERIC
    operational_segment = ForeignKeyField(db_column='OPERATIONAL_SEGMENT_ID', null=True, model=OperationalSegment, to_field='operational_segment')
    parity = CharField(db_column='PARITY', null=True)
    position = TextField(db_column='POSITION', null=True)
    stop_bits = UnknownField(db_column='STOP_BITS', null=True)  # NUMERIC
    workstation = ForeignKeyField(db_column='WORKSTATION_ID', null=True, model=WorkstationsLu, to_field='workstation')

    class Meta:
        db_table = 'DEPLOYED_EQUIPMENT'

class CatchRawStrings(BaseModel):
    catch_raw_strings = PrimaryKeyField(db_column='CATCH_RAW_STRINGS_ID')
    date_time = TextField(db_column='DATE_TIME', null=True)
    deployed_equipment = ForeignKeyField(db_column='DEPLOYED_EQUIPMENT_ID', null=True, model=DeployedEquipment, to_field='deployed_equipment')
    raw_strings = TextField(db_column='RAW_STRINGS', null=True)

    class Meta:
        db_table = 'CATCH_RAW_STRINGS'

class ConfigurationSettings(BaseModel):
    configuration_settings = PrimaryKeyField(db_column='CONFIGURATION_SETTINGS_ID')
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    parameter = TextField(db_column='PARAMETER', null=True)
    type = TextField(db_column='TYPE', null=True)
    value = TextField(db_column='VALUE', null=True)

    class Meta:
        db_table = 'CONFIGURATION_SETTINGS'

class CrewRole(BaseModel):
    crew_role_description = TextField(db_column='CREW_ROLE_DESCRIPTION', null=True)
    crew_role = PrimaryKeyField(db_column='CREW_ROLE_ID')
    crew_role_type = TextField(db_column='CREW_ROLE_TYPE', null=True)

    class Meta:
        db_table = 'CREW_ROLE'

class PersonnelLu(BaseModel):
    full_name = TextField(db_column='FULL_NAME', null=True)
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    person = PrimaryKeyField(db_column='PERSON_ID')

    class Meta:
        db_table = 'PERSONNEL_LU'

class CrewScheduleAssignment(BaseModel):
    crew_schedule_assignment = PrimaryKeyField(db_column='CREW_SCHEDULE_ASSIGNMENT_ID')
    date_off_of_leg = TextField(db_column='DATE_OFF_OF_LEG', null=True)
    date_onto_leg = TextField(db_column='DATE_ONTO_LEG', null=True)
    leg = IntegerField(db_column='LEG_ID', null=True)
    note = TextField(db_column='NOTE', null=True)
    person = ForeignKeyField(db_column='PERSON_ID', null=True, model=PersonnelLu, to_field='person')

    class Meta:
        db_table = 'CREW_SCHEDULE_ASSIGNMENT'

class DataSentences(BaseModel):
    data_sentence = UnknownField(db_column='DATA_SENTENCE_ID', primary_key=True)  # NUMERIC
    delimiter = TextField(db_column='DELIMITER', null=True)
    field_count = IntegerField(db_column='FIELD_COUNT', null=True)
    fixed_or_delimited = TextField(db_column='FIXED_OR_DELIMITED', null=True)
    note = TextField(db_column='NOTE', null=True)
    sentence_description = TextField(db_column='SENTENCE_DESCRIPTION', null=True)
    sentence_name = TextField(db_column='SENTENCE_NAME', null=True)

    class Meta:
        db_table = 'DATA_SENTENCES'

class DataSentenceFields(BaseModel):
    data_sentence_field = UnknownField(db_column='DATA_SENTENCE_FIELD_ID', primary_key=True)  # NUMERIC
    data_sentence = ForeignKeyField(db_column='DATA_SENTENCE_ID', null=True, model=DataSentences, to_field='data_sentence')
    field_description = TextField(db_column='FIELD_DESCRIPTION', null=True)
    field_name = TextField(db_column='FIELD_NAME', null=True)
    field_size = UnknownField(db_column='FIELD_SIZE', null=True)  # NUMERIC
    field_type = TextField(db_column='FIELD_TYPE', null=True)
    measurement_priority = IntegerField(db_column='MEASUREMENT_PRIORITY', null=True)
    measurement_type = ForeignKeyField(db_column='MEASUREMENT_TYPE_ID', null=True, model=TypesLu, to_field='type_id')
    position = UnknownField(db_column='POSITION', null=True)  # NUMERIC
    uom_position = IntegerField(db_column='UOM_POSITION', null=True)

    class Meta:
        db_table = 'DATA_SENTENCE_FIELDS'
        indexes = (
            (('measurement_type', 'measurement_priority'), True),
        )

class EnviroNetRawFiles(BaseModel):
    activation_datetime = TextField(db_column='ACTIVATION_DATETIME', null=True)
    deactivation_datetime = TextField(db_column='DEACTIVATION_DATETIME', null=True)
    deployed_equipment = ForeignKeyField(db_column='DEPLOYED_EQUIPMENT_ID', null=True, model=DeployedEquipment, to_field='deployed_equipment')
    enviro_net_raw_files = PrimaryKeyField(db_column='ENVIRO_NET_RAW_FILES_ID')
    haul = TextField(db_column='HAUL_ID', null=True)
    raw_file = TextField(db_column='RAW_FILE', null=True)

    class Meta:
        db_table = 'ENVIRO_NET_RAW_FILES'

class EnviroNetRawStrings(BaseModel):
    date_time = TextField(db_column='DATE_TIME', index=True, null=True)
    deployed_equipment = ForeignKeyField(db_column='DEPLOYED_EQUIPMENT_ID', null=True, model=DeployedEquipment, to_field='deployed_equipment')
    enviro_net_raw_strings = PrimaryKeyField(db_column='ENVIRO_NET_RAW_STRINGS_ID')
    haul = TextField(db_column='HAUL_ID', null=True)
    raw_strings = TextField(db_column='RAW_STRINGS', null=True)

    class Meta:
        db_table = 'ENVIRO_NET_RAW_STRINGS'

class EquipmentSentencesMtx(BaseModel):
    data_sentence = ForeignKeyField(db_column='DATA_SENTENCE_ID', null=True, model=DataSentences, to_field='data_sentence')
    equipment = ForeignKeyField(db_column='EQUIPMENT_ID', null=True, model=Equipment, to_field='equipment')
    equipment_sentence = PrimaryKeyField(db_column='EQUIPMENT_SENTENCE_ID')

    class Meta:
        db_table = 'EQUIPMENT_SENTENCES_MTX'

class EquipmentSettingTypesLu(BaseModel):
    equipment_setting_type = PrimaryKeyField(db_column='EQUIPMENT_SETTING_TYPE_ID')
    name = TextField(db_column='NAME', null=True)

    class Meta:
        db_table = 'EQUIPMENT_SETTING_TYPES_LU'

class EquipmentSettingsLu(BaseModel):
    equipment_setting = PrimaryKeyField(db_column='EQUIPMENT_SETTING_ID')
    equipment_setting_type = ForeignKeyField(db_column='EQUIPMENT_SETTING_TYPE_ID', null=True, model=EquipmentSettingTypesLu, to_field='equipment_setting_type')
    setting_value_number = FloatField(db_column='SETTING_VALUE_NUMBER', null=True)
    setting_value_text = TextField(db_column='SETTING_VALUE_TEXT', null=True)

    class Meta:
        db_table = 'EQUIPMENT_SETTINGS_LU'

class FpcLog(BaseModel):
    date_time = TextField(db_column='DATE_TIME', null=True)
    entry = TextField(db_column='ENTRY', null=True)
    fpc = IntegerField(db_column='FPC_ID', null=True)
    fpc_log = PrimaryKeyField(db_column='FPC_LOG_ID')
    is_tow_performance_note = TextField(db_column='IS_TOW_PERFORMANCE_NOTE', null=True)
    operational_segment = ForeignKeyField(db_column='OPERATIONAL_SEGMENT_ID', null=True, model=OperationalSegment, to_field='operational_segment')

    class Meta:
        db_table = 'FPC_LOG'

class ImpactFactorsLu(BaseModel):
    impact_category_type = ForeignKeyField(db_column='IMPACT_CATEGORY_TYPE_ID', null=True, model=TypesLu, to_field='type_id')
    impact_factor = TextField(db_column='IMPACT_FACTOR', null=True)
    impact_factor_id = PrimaryKeyField(db_column='IMPACT_FACTOR_ID')

    class Meta:
        db_table = 'IMPACT_FACTORS_LU'

class ManufacturerSettingsLu(BaseModel):
    equipment = ForeignKeyField(db_column='EQUIPMENT_ID', null=True, model=Equipment, to_field='equipment')
    equipment_setting_type = ForeignKeyField(db_column='EQUIPMENT_SETTING_TYPE_ID', null=True, model=EquipmentSettingTypesLu, to_field='equipment_setting_type')
    manufacturer_settings = PrimaryKeyField(db_column='MANUFACTURER_SETTINGS_ID')
    setting_value_text = TextField(db_column='SETTING_VALUE_TEXT', null=True)

    class Meta:
        db_table = 'MANUFACTURER_SETTINGS_LU'

class MeasurementPriorities(BaseModel):
    column = TextField(db_column='COLUMN', null=True)
    deployed_equipment = IntegerField(db_column='DEPLOYED_EQUIPMENT_ID', null=True)
    equipment = ForeignKeyField(db_column='EQUIPMENT_ID', null=True, model=Equipment, to_field='equipment')
    integrator_measurement = IntegerField(db_column='INTEGRATOR_MEASUREMENT_ID', null=True)
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    logger_or_serial = TextField(db_column='LOGGER_OR_SERIAL', null=True)
    measurement = ForeignKeyField(db_column='MEASUREMENT_ID', null=True, model=TypesLu, to_field='type_id')
    measurement_priorities = PrimaryKeyField(db_column='MEASUREMENT_PRIORITIES_ID')
    priority = IntegerField(db_column='PRIORITY', null=True)
    sentence = ForeignKeyField(db_column='SENTENCE_ID', null=True, model=DataSentences, to_field='data_sentence')

    class Meta:
        db_table = 'MEASUREMENT_PRIORITIES'

class OperationRoleMtx(BaseModel):
    crew_role = ForeignKeyField(db_column='CREW_ROLE_ID', null=True, model=CrewRole, to_field='crew_role')
    crew_schedule_assignment = ForeignKeyField(db_column='CREW_SCHEDULE_ASSIGNMENT_ID', null=True, model=CrewScheduleAssignment, to_field='crew_schedule_assignment')
    end_datetime = TextField(db_column='END_DATETIME', null=True)
    operation_role_mtx = PrimaryKeyField(db_column='OPERATION_ROLE_MTX_ID')
    start_datetime = TextField(db_column='START_DATETIME', null=True)

    class Meta:
        db_table = 'OPERATION_ROLE_MTX'

class PersonOrgAssociationLu(BaseModel):
    organization = ForeignKeyField(db_column='ORGANIZATION_ID', null=True, model=OrganizationLu, to_field='organization')
    person = ForeignKeyField(db_column='PERSON_ID', null=True, model=PersonnelLu, to_field='person')
    person_org_association = PrimaryKeyField(db_column='PERSON_ORG_ASSOCIATION_ID')

    class Meta:
        db_table = 'PERSON_ORG_ASSOCIATION_LU'

class TargetStationsLu(BaseModel):
    ll_latitude = UnknownField(db_column='LL_LATITUDE', null=True)  # NUMERIC
    ll_longitude = UnknownField(db_column='LL_LONGITUDE', null=True)  # NUMERIC
    lr_latitude = UnknownField(db_column='LR_LATITUDE', null=True)  # NUMERIC
    lr_longitude = UnknownField(db_column='LR_LONGITUDE', null=True)  # NUMERIC
    pass_ = TextField(db_column='PASS', null=True)
    primary_stn_code = UnknownField(db_column='PRIMARY_STN_CODE', null=True)  # NUMERIC
    station_code = UnknownField(db_column='STATION_CODE', null=True)  # NUMERIC
    target_rank = IntegerField(db_column='TARGET_RANK', null=True)
    target_station = PrimaryKeyField(db_column='TARGET_STATION_ID')
    ul_latitude = UnknownField(db_column='UL_LATITUDE', null=True)  # NUMERIC
    ul_longitude = UnknownField(db_column='UL_LONGITUDE', null=True)  # NUMERIC
    ur_latitude = UnknownField(db_column='UR_LATITUDE', null=True)  # NUMERIC
    ur_longitude = UnknownField(db_column='UR_LONGITUDE', null=True)  # NUMERIC
    vessel = ForeignKeyField(db_column='VESSEL_ID', null=True, model=VesselLu, to_field='vessel')

    class Meta:
        db_table = 'TARGET_STATIONS_LU'

class ProjectTargetStations(BaseModel):
    project = ForeignKeyField(db_column='PROJECT_ID', null=True, model=Project, to_field='project')
    project_target_station = TextField(db_column='PROJECT_TARGET_STATION', null=True)
    target_station = ForeignKeyField(db_column='TARGET_STATION_ID', null=True, model=TargetStationsLu, to_field='target_station')

    class Meta:
        db_table = 'PROJECT_TARGET_STATIONS'

class SearchDetails(BaseModel):
    activation_datetime = TextField(db_column='ACTIVATION_DATETIME', null=True)
    deactivation_datetime = TextField(db_column='DEACTIVATION_DATETIME', null=True)
    elapsed_search_time = TextField(db_column='ELAPSED_SEARCH_TIME', null=True)
    result = TextField(db_column='RESULT', null=True)
    result_reason = TextField(db_column='RESULT_REASON', null=True)
    search_details = PrimaryKeyField(db_column='SEARCH_DETAILS_ID')
    search = ForeignKeyField(db_column='SEARCH_ID', null=True, model=OperationalSegment, to_field='operational_segment')
    search_number = TextField(db_column='SEARCH_NUMBER', null=True)
    target_station = UnknownField(db_column='TARGET_STATION_ID', null=True)  # NUMERIC

    class Meta:
        db_table = 'SEARCH_DETAILS'

class Species(BaseModel):
    species = PrimaryKeyField(db_column='SPECIES_ID')
    species_name = TextField(db_column='SPECIES_NAME', null=True)

    class Meta:
        db_table = 'SPECIES'

class StationPolygons(BaseModel):
    polygon = TextField(db_column='POLYGON', null=True)
    station_polygon = PrimaryKeyField(db_column='STATION_POLYGON_ID')
    target_station = ForeignKeyField(db_column='TARGET_STATION_ID', null=True, model=TargetStationsLu, to_field='target_station')

    class Meta:
        db_table = 'STATION_POLYGONS'

class TowDetails(BaseModel):
    activation_datetime = TextField(db_column='ACTIVATION_DATETIME', null=True)
    deactivation_datetime = TextField(db_column='DEACTIVATION_DATETIME', null=True)
    elapsed_tow_time = TextField(db_column='ELAPSED_TOW_TIME', null=True)
    is_minimum_time_met = TextField(db_column='IS_MINIMUM_TIME_MET', null=True)
    is_satisfactory = TextField(db_column='IS_SATISFACTORY', null=True)
    manual_depth1_f = FloatField(db_column='MANUAL_DEPTH1_F', null=True)
    manual_depth2_f = FloatField(db_column='MANUAL_DEPTH2_F', null=True)
    net_height_m = FloatField(db_column='NET_HEIGHT_M', null=True)
    net_wingspread_m = FloatField(db_column='NET_WINGSPREAD_M', null=True)
    performance_comments = TextField(db_column='PERFORMANCE_COMMENTS', null=True)
    scope_f = FloatField(db_column='SCOPE_F', null=True)
    surface_temp_avg_c = FloatField(db_column='SURFACE_TEMP_AVG_C', null=True)
    swell_direction = TextField(db_column='SWELL_DIRECTION', null=True)
    swell_height_ft = FloatField(db_column='SWELL_HEIGHT_FT', null=True)
    target_station = FloatField(db_column='TARGET_STATION_ID', null=True)
    tow_details = PrimaryKeyField(db_column='TOW_DETAILS_ID')
    tow_direction = TextField(db_column='TOW_DIRECTION', null=True)
    tow = ForeignKeyField(db_column='TOW_ID', null=True, model=OperationalSegment, to_field='operational_segment')
    tow_number = TextField(db_column='TOW_NUMBER', null=True)
    vessel_speed_avg_kts = FloatField(db_column='VESSEL_SPEED_AVG_KTS', null=True)
    wave_direction = TextField(db_column='WAVE_DIRECTION', null=True)
    wave_height_ft = FloatField(db_column='WAVE_HEIGHT_FT', null=True)
    weather = TextField(db_column='WEATHER', null=True)
    weighted_bcs = TextField(db_column='WEIGHTED_BCS', null=True)
    wind_direction_avg = TextField(db_column='WIND_DIRECTION_AVG', null=True)
    wind_speed_avg_kts = FloatField(db_column='WIND_SPEED_AVG_KTS', null=True)

    class Meta:
        db_table = 'TOW_DETAILS'

class TowImpactFactors(BaseModel):
    impact_factor = ForeignKeyField(db_column='IMPACT_FACTOR_ID', null=True, model=ImpactFactorsLu, to_field='impact_factor_id')
    is_unsat_factor = TextField(db_column='IS_UNSAT_FACTOR', null=True)
    tow = ForeignKeyField(db_column='TOW_ID', null=True, model=OperationalSegment, to_field='operational_segment')
    tow_impact_factor = PrimaryKeyField(db_column='TOW_IMPACT_FACTOR_ID')

    class Meta:
        db_table = 'TOW_IMPACT_FACTORS'

class TowWaypoints(BaseModel):
    date_time = TextField(db_column='DATE_TIME', null=True)
    gear_depth_m = FloatField(db_column='GEAR_DEPTH_M', null=True)
    latitude = TextField(db_column='LATITUDE', null=True)
    longitude = TextField(db_column='LONGITUDE', null=True)
    manual_depth_ftm = FloatField(db_column='MANUAL_DEPTH_FTM', null=True)
    name = TextField(db_column='NAME', null=True)
    sounder_depth_ftm = FloatField(db_column='SOUNDER_DEPTH_FTM', null=True)
    speed_kts = FloatField(db_column='SPEED_KTS', null=True)
    tow = ForeignKeyField(db_column='TOW_ID', null=True, model=OperationalSegment, to_field='operational_segment')
    tow_waypoint = PrimaryKeyField(db_column='TOW_WAYPOINT_ID')
    tow_waypoint_type = ForeignKeyField(db_column='TOW_WAYPOINT_TYPE_ID', null=True, model=TypesLu, to_field='type_id')

    class Meta:
        db_table = 'TOW_WAYPOINTS'

class DataSentenceFieldsOld1150717145423(BaseModel):
    data_sentence_field = UnknownField(db_column='DATA_SENTENCE_FIELD_ID', primary_key=True)  # NUMERIC
    data_sentence = ForeignKeyField(db_column='DATA_SENTENCE_ID', null=True, model=DataSentences, to_field='data_sentence')
    field_description = TextField(db_column='FIELD_DESCRIPTION', null=True)
    field_name = TextField(db_column='FIELD_NAME', null=True)
    field_size = UnknownField(db_column='FIELD_SIZE', null=True)  # NUMERIC
    field_type = TextField(db_column='FIELD_TYPE', null=True)
    measurement_priority = IntegerField(db_column='MEASUREMENT_PRIORITY', null=True)
    measurement_type = ForeignKeyField(db_column='MEASUREMENT_TYPE_ID', null=True, model=TypesLu, to_field='type_id')
    position = UnknownField(db_column='POSITION', null=True)  # NUMERIC
    uom_position = IntegerField(db_column='UOM_POSITION', null=True)

    class Meta:
        db_table = '_DATA_SENTENCE_FIELDS_old_1150717145423'
        indexes = (
            (('measurement_type', 'measurement_priority'), True),
        )

class TowDetailsOld20170124(BaseModel):
    activation_datetime = TextField(db_column='ACTIVATION_DATETIME', null=True)
    deactivation_datetime = TextField(db_column='DEACTIVATION_DATETIME', null=True)
    elapsed_tow_time = TextField(db_column='ELAPSED_TOW_TIME', null=True)
    is_minimum_time_met = TextField(db_column='IS_MINIMUM_TIME_MET', null=True)
    is_satisfactory = TextField(db_column='IS_SATISFACTORY', null=True)
    manual_depth1_f = UnknownField(db_column='MANUAL_DEPTH1_F', null=True)  # NUMERIC
    manual_depth2_f = UnknownField(db_column='MANUAL_DEPTH2_F', null=True)  # NUMERIC
    net_height_m = UnknownField(db_column='NET_HEIGHT_M', null=True)  # NUMERIC
    net_wingspread_m = UnknownField(db_column='NET_WINGSPREAD_M', null=True)  # NUMERIC
    performance_comments = TextField(db_column='PERFORMANCE_COMMENTS', null=True)
    scope_f = FloatField(db_column='SCOPE_F', null=True)
    surface_temp_avg_c = FloatField(db_column='SURFACE_TEMP_AVG_C', null=True)
    swell_direction = TextField(db_column='SWELL_DIRECTION', null=True)
    swell_height_ft = UnknownField(db_column='SWELL_HEIGHT_FT', null=True)  # NUMERIC
    target_station = UnknownField(db_column='TARGET_STATION_ID', null=True)  # NUMERIC
    tow_details = PrimaryKeyField(db_column='TOW_DETAILS_ID')
    tow_direction = TextField(db_column='TOW_DIRECTION', null=True)
    tow = ForeignKeyField(db_column='TOW_ID', null=True, model=OperationalSegment, to_field='operational_segment')
    tow_number = TextField(db_column='TOW_NUMBER', null=True)
    vessel_speed_avg_kts = FloatField(db_column='VESSEL_SPEED_AVG_KTS', null=True)
    wave_direction = TextField(db_column='WAVE_DIRECTION', null=True)
    wave_height_ft = UnknownField(db_column='WAVE_HEIGHT_FT', null=True)  # NUMERIC
    weather = TextField(db_column='WEATHER', null=True)
    weighted_bcs = TextField(db_column='WEIGHTED_BCS', null=True)
    wind_direction_avg = TextField(db_column='WIND_DIRECTION_AVG', null=True)
    wind_speed_avg_kts = FloatField(db_column='WIND_SPEED_AVG_KTS', null=True)

    class Meta:
        db_table = '_TOW_DETAILS_old_20170124'

class TowDetailsOld201701241(BaseModel):
    activation_datetime = TextField(db_column='ACTIVATION_DATETIME', null=True)
    deactivation_datetime = TextField(db_column='DEACTIVATION_DATETIME', null=True)
    elapsed_tow_time = TextField(db_column='ELAPSED_TOW_TIME', null=True)
    is_minimum_time_met = TextField(db_column='IS_MINIMUM_TIME_MET', null=True)
    is_satisfactory = TextField(db_column='IS_SATISFACTORY', null=True)
    manual_depth1_f = FloatField(db_column='MANUAL_DEPTH1_F', null=True)
    manual_depth2_f = FloatField(db_column='MANUAL_DEPTH2_F', null=True)
    net_height_m = FloatField(db_column='NET_HEIGHT_M', null=True)
    net_wingspread_m = FloatField(db_column='NET_WINGSPREAD_M', null=True)
    performance_comments = TextField(db_column='PERFORMANCE_COMMENTS', null=True)
    scope_f = FloatField(db_column='SCOPE_F', null=True)
    surface_temp_avg_c = FloatField(db_column='SURFACE_TEMP_AVG_C', null=True)
    swell_direction = TextField(db_column='SWELL_DIRECTION', null=True)
    swell_height_ft = FloatField(db_column='SWELL_HEIGHT_FT', null=True)
    target_station = FloatField(db_column='TARGET_STATION_ID', null=True)
    tow_details = PrimaryKeyField(db_column='TOW_DETAILS_ID')
    tow_direction = TextField(db_column='TOW_DIRECTION', null=True)
    tow = ForeignKeyField(db_column='TOW_ID', null=True, model=OperationalSegment, to_field='operational_segment')
    tow_number = TextField(db_column='TOW_NUMBER', null=True)
    vessel_speed_avg_kts = FloatField(db_column='VESSEL_SPEED_AVG_KTS', null=True)
    wave_direction = TextField(db_column='WAVE_DIRECTION', null=True)
    wave_height_ft = FloatField(db_column='WAVE_HEIGHT_FT', null=True)
    weather = TextField(db_column='WEATHER', null=True)
    weighted_bcs = TextField(db_column='WEIGHTED_BCS', null=True)
    wind_direction_avg = TextField(db_column='WIND_DIRECTION_AVG', null=True)
    wind_speed_avg_kts = FloatField(db_column='WIND_SPEED_AVG_KTS', null=True)

    class Meta:
        db_table = '_TOW_DETAILS_old_20170124_1'

class TowDetailsOld201701242(BaseModel):
    activation_datetime = TextField(db_column='ACTIVATION_DATETIME', null=True)
    deactivation_datetime = TextField(db_column='DEACTIVATION_DATETIME', null=True)
    elapsed_tow_time = TextField(db_column='ELAPSED_TOW_TIME', null=True)
    is_minimum_time_met = TextField(db_column='IS_MINIMUM_TIME_MET', null=True)
    is_satisfactory = TextField(db_column='IS_SATISFACTORY', null=True)
    manual_depth1_f = UnknownField(db_column='MANUAL_DEPTH1_F', null=True)  # NUMERIC
    manual_depth2_f = UnknownField(db_column='MANUAL_DEPTH2_F', null=True)  # NUMERIC
    net_height_m = UnknownField(db_column='NET_HEIGHT_M', null=True)  # NUMERIC
    net_wingspread_m = UnknownField(db_column='NET_WINGSPREAD_M', null=True)  # NUMERIC
    performance_comments = TextField(db_column='PERFORMANCE_COMMENTS', null=True)
    scope_f = FloatField(db_column='SCOPE_F', null=True)
    surface_temp_avg_c = FloatField(db_column='SURFACE_TEMP_AVG_C', null=True)
    swell_direction = TextField(db_column='SWELL_DIRECTION', null=True)
    swell_height_ft = UnknownField(db_column='SWELL_HEIGHT_FT', null=True)  # NUMERIC
    target_station = UnknownField(db_column='TARGET_STATION_ID', null=True)  # NUMERIC
    tow_details = PrimaryKeyField(db_column='TOW_DETAILS_ID')
    tow_direction = TextField(db_column='TOW_DIRECTION', null=True)
    tow = ForeignKeyField(db_column='TOW_ID', null=True, model=OperationalSegment, to_field='operational_segment')
    tow_number = TextField(db_column='TOW_NUMBER', null=True)
    vessel_speed_avg_kts = FloatField(db_column='VESSEL_SPEED_AVG_KTS', null=True)
    wave_direction = TextField(db_column='WAVE_DIRECTION', null=True)
    wave_height_ft = UnknownField(db_column='WAVE_HEIGHT_FT', null=True)  # NUMERIC
    weather = TextField(db_column='WEATHER', null=True)
    weighted_bcs = TextField(db_column='WEIGHTED_BCS', null=True)
    wind_direction_avg = TextField(db_column='WIND_DIRECTION_AVG', null=True)
    wind_speed_avg_kts = FloatField(db_column='WIND_SPEED_AVG_KTS', null=True)

    class Meta:
        db_table = '_TOW_DETAILS_old_20170124_2'

class SqliteStat1(BaseModel):
    idx = UnknownField(null=True)  # 
    stat = UnknownField(null=True)  # 
    tbl = UnknownField(null=True)  # 

    class Meta:
        db_table = 'sqlite_stat1'

