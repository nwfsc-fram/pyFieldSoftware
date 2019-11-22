from peewee import *

from py.trawl_analyzer.Settings import BaseModel


class UnknownField(object):
    def __init__(self, *_, **__): pass


class OperationsFlattenedVw(BaseModel):
    operation = PrimaryKeyField(db_column='operation_id', null=False)
    operation_type = TextField(null=False)
    project_name = TextField(null=False)
    year_name = TextField()
    pass_name = TextField()
    cruise_name = TextField()
    vessel_name = TextField()
    leg_name = TextField()
    tow_name = TextField()
    project_lu = IntegerField(db_column="project_lu_id", null=False)
    year = IntegerField(db_column="year_id", null=False)
    pass_id = IntegerField(db_column="pass_id", null=False)
    cruise = IntegerField(db_column="cruise_id", null=False)
    leg = IntegerField(db_column="leg_id", null=False)
    tow = IntegerField(db_column="tow_id", null=False)
    parent_operation = IntegerField(db_column="parent_operation_id", null=False)
    target_station = IntegerField(db_column="target_station_id", null=False)
    target_station_code = TextField()
    vessel = IntegerField(db_column="vessel_id", null=False)
    trawl_survey_vessel = IntegerField(db_column="trawl_survey_vessel_id", null=False)
    operation_load_date = DateTimeField()
    catch_load_date = DateTimeField()
    sensor_load_date = DateTimeField()
    alternate_operation_name = TextField()

    class Meta:
        db_table = 'operations_flattened_vw'
        schema = 'fram_central'


class ParsingRulesVw(BaseModel):
    parsing_rules = PrimaryKeyField(db_column='parsing_rules_id', null=False)
    equipment = IntegerField(db_column='equipment_id', null=False)
    equipment_name = TextField()
    logger_or_serial = TextField()
    line_starting = TextField()
    fixed_or_delimited = TextField()
    delimiter = TextField()
    number_fields_in_line_name = IntegerField(db_column='number_fields_in_line_name', null=False)
    field_position = IntegerField(db_column='field_position', null=False)
    line_ending = TextField()
    field_format = TextField()
    display_format = TextField()
    is_numeric = BooleanField()
    uom = TextField()
    uom_position = IntegerField(db_column='uom_position')
    hemisphere = TextField()
    hemisphere_position = IntegerField(db_column='hemisphere_position')
    quality_status = TextField()
    quality_status_position = IntegerField(db_column='quality_status_position')
    channel = TextField()
    channel_position = IntegerField(db_column='channel_position')
    measurement_to = TextField()
    measurement_to_position = IntegerField(db_column='measurement_to_position')
    measurement_from = TextField()
    measurement_from_position = IntegerField(db_column='measurement_from_position')
    true_relative_magnetic = TextField()
    trurelmag_position = IntegerField(db_column='trurelmag_position')
    reading_type = TextField()
    reading_basis = TextField()
    reading_type_position = IntegerField(db_column='reading_type_position')
    reading_type_code = TextField()
    is_parsed = BooleanField()
    parsing_priority = IntegerField(db_column='parsing_priority')
    data_line = IntegerField(db_column='data_line_id')
    data_field = IntegerField(db_column='data_field_id')
    graph_type = TextField()

    class Meta:
        db_table = 'parsing_rules_vw'
        schema = 'fram_central'


class ParsingSentencesVw(BaseModel):
    equipment = IntegerField(db_column='equipment_id', null=False)
    line_name = TextField()
    data_line = IntegerField(db_column='data_line_id')
    fixed_or_delimited = TextField()
    delimiter = TextField()
    number_fields_in_line_name = IntegerField(db_column='number_fields_in_line_name', null=False)
    line_ending = TextField()
    is_parsed = BooleanField()
    parsing_priority = IntegerField(db_column='parsing_priority')

    class Meta:
        db_table = 'parsing_sentences_vw'
        schema = 'fram_central'


class CruiseListVw(BaseModel):
    survey_schedule = PrimaryKeyField(db_column='survey_schedule_id', null=False)
    operation_type = TextField()
    survey = TextField()
    survey_year = TextField()
    survey_pass = TextField()
    cruise_name = TextField()
    vessel_name = TextField()
    vessel = IntegerField(db_column='vessel_id', null=False)
    trawl_survey_vessel = IntegerField(db_column='trawl_survey_vessel_id', null=False)

    class Meta:
        db_table = 'cruise_list_vw'
        schema = 'fram_central'


class AuxiliaryStats(BaseModel):
    auxiliary_stats = PrimaryKeyField(db_column='auxiliary_stats_id')
    derivation_type_lu = IntegerField(db_column='derivation_type_lu_id', null=True)
    operation_attribute = IntegerField(db_column='operation_attribute_id', null=True)
    parameter_alpha = TextField(null=True)
    parameter_numeric = DecimalField(null=True)
    parameter_type_lu = IntegerField(db_column='parameter_type_lu_id', null=True)

    class Meta:
        db_table = 'auxiliary_stats'
        schema = 'fram_central'

class Lookups(BaseModel):
    lookup = PrimaryKeyField(db_column='lookup_id')
    type = TextField()
    value = TextField()
    subvalue = TextField(null=True)
    description = TextField(null=True)
    activation_date = DateTimeField()
    deactivation_date = DateTimeField(null=True)

    hook_and_line = IntegerField(db_column='hook_and_line_id', null=True)
    bottom_trawl = IntegerField(db_column='bottom_trawl_id', null=True)
    acoustics = IntegerField(db_column='acoustics_id', null=True)
    master_legacy = IntegerField(db_column='master_legacy_id', null=True)
    is_active = BooleanField()
    data_type = TextField(null=True)
    optecs_legacy = IntegerField(db_column='optecs_legacy_id', null=True)
    equivalent_observer_lookup = IntegerField(db_column='equivalent_observer_lookup_id', null=True)
    group_name = TextField(null=True)
    name = TextField(null=True)
    atomic_or_group = TextField(null=True)

    class Meta:
        db_table = 'lookups'
        schema = 'fram_central'

class LookupGroups(BaseModel):
    lookup_group = PrimaryKeyField(db_column="lookup_group_id")
    group_name_lu = ForeignKeyField(db_column='group_name_lu_id', model=Lookups, to_field='lookup')
    # group_member_lu = ForeignKeyField(db_column='group_member_lu_id', model=Lookups, to_field='lookup')
    group_member_lu = IntegerField(null=True)
    activation_date = DateTimeField()
    deactivation_date = DateTimeField(null=True)

    class Meta:
        db_table = 'lookup_groups'
        schema = 'fram_central'

class GroupMemberVw(BaseModel):
    # lookup_id_grp = ForeignKeyField(db_column='lookup_id_grp', model='Lookups', to_field='lookup')
    lookup_id_grp = IntegerField()
    atomic_or_group_grp = TextField()
    lookup_type_grp = TextField()
    group_name = TextField()
    # lookup_id_member = ForeignKeyField(db_column='lookup_id_member', model='Lookups', to_field='lookup')
    lookup_id_member = IntegerField()
    atomic_or_group_member = TextField()
    lookup_type_member = TextField()
    lookup_name_member = TextField(null=True)
    lookup_value_member = TextField(null=True)

    class Meta:
        db_table = 'group_member_vw'
        schema = 'fram_central'
        primary_key = False

class EquipmentLu(BaseModel):
    activation_date = DateTimeField()
    deactivation_date = DateTimeField(null=True)
    description = TextField(null=True)
    equipment_category_lu = ForeignKeyField(db_column='equipment_category_lu_id', model=Lookups, to_field='lookup')
    equipment = PrimaryKeyField(db_column='equipment_id')
    is_active = BooleanField(null=True)
    is_backdeck = BooleanField(null=True)
    is_sensor_file = BooleanField(null=True)
    is_wheelhouse = BooleanField(null=True)
    model = TextField(null=True)
    name = TextField()
    organization_type_lu = ForeignKeyField(db_column='organization_type_lu_id', model=Lookups, related_name='lookups_organization_type_lu_set', to_field='lookup')

    class Meta:
        db_table = 'equipment_lu'
        schema = 'fram_central'

class ClockedComplexLu(BaseModel):
    clocked_complex = IntegerField(db_column='clocked_complex_id')
    primary_unit = ForeignKeyField(db_column='primary_unit_id', null=True, model=EquipmentLu, to_field='equipment')
    subunit = ForeignKeyField(db_column='subunit_id', null=True, model=EquipmentLu, related_name='equipment_lu_subunit_set', to_field='equipment')

    class Meta:
        db_table = 'clocked_complex_lu'
        schema = 'fram_central'

class VesselLu(BaseModel):
    acoustics_survey = IntegerField(db_column='acoustics_survey_id', null=True)
    activation_date = DateTimeField(null=True)
    deactivation_date = DateTimeField(null=True)
    groundfish_permit = TextField(null=True)
    hook_and_line_survey = IntegerField(db_column='hook_and_line_survey_id', null=True)
    registration_number = TextField(null=True)
    trawl_survey = IntegerField(db_column='trawl_survey_id', null=True)
    vessel_2byte_abbreviation = TextField(null=True)
    vessel = PrimaryKeyField(db_column='vessel_id')
    vessel_name = TextField()

    class Meta:
        db_table = 'vessel_lu'
        schema = 'fram_central'

class PersonnelLu(BaseModel):
    person = PrimaryKeyField(db_column='person_id')
    first_name = TextField()
    middle_initial = TextField(null=True)
    last_name = TextField()
    nick_name = TextField(null=True)
    is_active = BooleanField(null=True)
    email_address = TextField(null=True)
    phone_number = TextField(null=True)
    full_name = TextField(null=True)

    class Meta:
        db_table = 'personnel_lu'
        schema = 'fram_central'

class StationInventoryLu(BaseModel):
    area_description = TextField(null=True)
    area_hectares = DecimalField(null=True)
    centroid = IntegerField(db_column='centroid_id', null=True)
    date_of_introduction = CharField(null=True)
    datum = TextField(null=True)
    design_depth_max_ftm = DecimalField(null=True)
    design_depth_min_ftm = DecimalField(null=True)
    design_ns_of_34pt5 = CharField(null=True)
    is_cowcod_conservation_area = BooleanField(null=True)
    is_in_selection_set = BooleanField(null=True)
    legacy_station = IntegerField(db_column='legacy_station_id', null=True)
    ll_lat_dd = DecimalField(null=True)
    ll_lon_dd = DecimalField(null=True)
    lr_lat_dd = DecimalField(null=True)
    lr_lon_dd = DecimalField(null=True)
    point_latitude_dd = DecimalField(null=True)
    point_longitude_dd = DecimalField(null=True)
    prediction = TextField(null=True)
    site_abbreviation = TextField(null=True)
    site_name = TextField(null=True)
    state = TextField(null=True)
    station_code = TextField(null=True)
    station_design_type_lu = ForeignKeyField(db_column='station_design_type_lu_id', model=Lookups, to_field='lookup')
    station_inventory = PrimaryKeyField(db_column='station_inventory_id')
    station_name = TextField(null=True)
    tide_stn_parent = ForeignKeyField(db_column='tide_stn_parent_id', null=True, model='self', to_field='station_inventory')
    time_zone = TextField(null=True)
    ul_lat_dd = DecimalField(null=True)
    ul_lon_dd = DecimalField(null=True)
    ur_lat_dd = DecimalField(null=True)
    ur_lon_dd = DecimalField(null=True)

    class Meta:
        db_table = 'station_inventory_lu'
        schema = 'fram_central'

class SurveyScheduleLu(BaseModel):
    activation_date = DateTimeField()
    arriving_at = TextField(null=True)
    crew_role_lu = ForeignKeyField(db_column='crew_role_lu_id', null=True, model=Lookups, to_field='lookup')
    deactivation_date = DateTimeField(null=True)
    deactivation_reason = TextField(null=True)
    departing_from = TextField(null=True)
    name = TextField()
    operation_type_lu = ForeignKeyField(db_column='operation_type_lu_id', model=Lookups, related_name='lookups_operation_type_lu_set', to_field='lookup')
    person = ForeignKeyField(db_column='person_id', null=True, model=PersonnelLu, to_field='person')
    project_lu = ForeignKeyField(db_column='project_lu_id', model=Lookups, related_name='lookups_project_lu_set2', to_field='lookup')
    schedule_entry_description = TextField(null=True)
    schedule_parent = ForeignKeyField(db_column='schedule_parent_id', null=True, model='self', to_field='survey_schedule')
    scheduled_arrival_date = DateTimeField()
    scheduled_departure_date = DateTimeField()
    survey_schedule = PrimaryKeyField(db_column='survey_schedule_id')
    vessel_color = TextField(null=True)
    vessel = ForeignKeyField(db_column='vessel_id', null=True, model=VesselLu, to_field='vessel')

    class Meta:
        db_table = 'survey_schedule_lu'
        schema = 'fram_central'

class TargetStationsLu(BaseModel):
    activation_date = DateTimeField()
    deactivation_date = DateTimeField(null=True)
    distance_to_primary_nm = DecimalField(null=True)
    is_active = BooleanField(null=True)
    legacy = IntegerField(db_column='legacy_id', null=True)
    notes = TextField(null=True)
    station_inventory = ForeignKeyField(db_column='station_inventory_id', model=StationInventoryLu, to_field='station_inventory')
    survey_schedule = ForeignKeyField(db_column='survey_schedule_id', model=SurveyScheduleLu, to_field='survey_schedule')
    target_rank = IntegerField(null=True)
    target_station = PrimaryKeyField(db_column='target_station_id')
    target_station_id_primary = ForeignKeyField(db_column='target_station_id_primary', null=True, model='self', to_field='target_station')

    class Meta:
        db_table = 'target_stations_lu'
        schema = 'fram_central'

class Operations(BaseModel):
    alternate_operation_name = TextField(null=True)
    captain = ForeignKeyField(db_column='captain_id', null=True, model=PersonnelLu, to_field='person')
    catch_load_date = DateTimeField(null=True)
    fpc = ForeignKeyField(db_column='fpc_id', null=True, model=PersonnelLu, related_name='personnel_lu_fpc_set', to_field='person')
    operation = PrimaryKeyField(db_column='operation_id')
    operation_load_date = DateTimeField()
    operation_name = TextField(null=True)
    operation_type_lu = ForeignKeyField(db_column='operation_type_lu_id', model=Lookups, to_field='lookup')
    parent_operation = ForeignKeyField(db_column='parent_operation_id', null=True, model='self', to_field='operation')
    project_lu = IntegerField(db_column='project_lu_id')
    recorder = ForeignKeyField(db_column='recorder_id', null=True, model=PersonnelLu, related_name='personnel_lu_recorder_set', to_field='person')
    scientist_1 = ForeignKeyField(db_column='scientist_1_id', null=True, model=PersonnelLu, related_name='personnel_lu_scientist_1_set', to_field='person')
    scientist_2 = ForeignKeyField(db_column='scientist_2_id', null=True, model=PersonnelLu, related_name='personnel_lu_scientist_2_set', to_field='person')
    sensor_load_date = DateTimeField(null=True)
    target_station = ForeignKeyField(db_column='target_station_id', null=True, model=TargetStationsLu, to_field='target_station')
    vessel = ForeignKeyField(db_column='vessel_id', null=True, model=VesselLu, to_field='vessel')

    class Meta:
        db_table = 'operations'
        schema = 'fram_central'

class Events(BaseModel):
    event_datetime = DateTimeField()
    event = PrimaryKeyField(db_column='event_id')
    event_latitude = DecimalField(null=True)
    event_longitude = DecimalField(null=True)
    event_type_lu = ForeignKeyField(db_column='event_type_lu_id', null=True, model=Lookups, to_field='lookup')
    operation = ForeignKeyField(db_column='operation_id', null=True, model=Operations, to_field='operation')
    unspecified_event_label = TextField(null=True)
    best_event_datetime = DateTimeField()
    best_event_latitude = DecimalField(null=True)
    best_event_longitude = DecimalField(null=True)

    class Meta:
        db_table = 'events'
        schema = 'fram_central'

class OperationFiles(BaseModel):
    database_name = TextField()
    end_date_time = TextField(null=True)
    final_path_name = TextField(null=True)
    load_completed_datetime = TextField(null=True)
    operation_file_type_lu = ForeignKeyField(db_column='operation_file_type_lu_id', model=Lookups, to_field='lookup')
    operation_file = PrimaryKeyField(db_column='operation_file_id')
    project_lu = ForeignKeyField(db_column='project_lu_id', model=Lookups, related_name='lookups_project_lu_set', to_field='lookup')
    start_date_time = TextField(null=True)

    class Meta:
        db_table = 'operation_files'
        schema = 'fram_central'

class OperationFilesMtx(BaseModel):
    operation_file = ForeignKeyField(db_column='operation_file_id', null=True, model=OperationFiles, to_field='operation_file')
    operation_files_mtx = PrimaryKeyField(db_column='operation_files_mtx_id')
    operation = ForeignKeyField(db_column='operation_id', null=True, model=Operations, to_field='operation')
    status = CharField(null=True)

    class Meta:
        db_table = 'operation_files_mtx'
        schema = 'fram_central'

class MeasurementStreams(BaseModel):
    attachment_position = TextField(null=True)
    equipment_field = IntegerField(db_column='equipment_field_id')
    measurement_stream = PrimaryKeyField(db_column='measurement_stream_id')
    operation_files_mtx = IntegerField(db_column='operation_files_mtx_id', null=True)
    operation = ForeignKeyField(db_column='operation_id', model=Operations, to_field='operation')
    stream_offset_seconds = IntegerField(null=True)
    raw_files = IntegerField(db_column='raw_files_id', null=True)

    class Meta:
        db_table = 'measurement_streams'
        schema = 'fram_central'

class ReportingRules(BaseModel):
    derivation_type_lu = ForeignKeyField(db_column='derivation_type_lu_id', null=True, model=Lookups, to_field='lookup')
    is_numeric = BooleanField(null=True)
    project_type_lu = ForeignKeyField(db_column='project_type_lu_id', model=Lookups, related_name='lookups_project_type_lu_set', to_field='lookup')
    reading_basis_lu = ForeignKeyField(db_column='reading_basis_lu_id', model=Lookups, related_name='lookups_reading_basis_lu_set', to_field='lookup')
    reading_type_lu = ForeignKeyField(db_column='reading_type_lu_id', model=Lookups, related_name='lookups_reading_type_lu_set', to_field='lookup')
    reporting_rule = PrimaryKeyField(db_column='reporting_rule_id')
    rule_type = TextField(null=True)
    source_db_field_name = TextField(null=True)
    units_of_measure_in_lu = ForeignKeyField(db_column='units_of_measure_in_lu_id', null=True, model=Lookups, related_name='lookups_units_of_measure_in_lu_set', to_field='lookup')
    units_of_measure_out_lu = IntegerField(db_column='units_of_measure_out_lu_id', null=True)

    class Meta:
        db_table = 'reporting_rules'
        schema = 'fram_central'

class OperationAttributes(BaseModel):
    attribute_alpha = TextField(null=True)
    attribute_numeric = DecimalField(null=True)
    is_best_value = BooleanField(null=True)
    measurement_stream = ForeignKeyField(db_column='measurement_stream_id', null=True, model=MeasurementStreams, to_field='measurement_stream')
    operation_attribute = PrimaryKeyField(db_column='operation_attribute_id')
    operation = ForeignKeyField(db_column='operation_id', model=Operations, to_field='operation')
    raw_files = IntegerField(db_column='raw_files_id', null=True)
    reporting_rules = ForeignKeyField(db_column='reporting_rules_id', model=ReportingRules, to_field='reporting_rule')

    class Meta:
        db_table = 'operation_attributes'
        schema = 'fram_central'

class OperationTracklines(BaseModel):
    operation_trackline = PrimaryKeyField(db_column='operation_trackline_id')
    operation = ForeignKeyField(db_column='operation_id', null=True, model=Operations, to_field='operation')
    date_time = DateTimeField()
    latitude = DecimalField(null=True)
    longitude = DecimalField(null=True)
    reporting_rule = ForeignKeyField(db_column='reporting_rule_id', model=ReportingRules, to_field='reporting_rule')

    class Meta:
        db_table = 'operation_tracklines'
        schema = 'fram_central'

class Comments(BaseModel):
    comment_id = PrimaryKeyField()
    comment_type_lu = ForeignKeyField(db_column='comment_type_lu_id', model=Lookups, to_field='lookup')
    comment = TextField(null=True)
    operation = ForeignKeyField(db_column='operation_id', null=True, model=Operations, to_field='operation')
    operation_attribute = ForeignKeyField(db_column='operation_attribute_id', null=True, model=OperationAttributes, to_field='operation_attribute')
    event = ForeignKeyField(db_column='event_id', null=True, model=Events, to_field='event')
    operation_files_mtx = ForeignKeyField(db_column='operation_files_mtx_id', null=True, model=OperationFilesMtx, to_field='operation_files_mtx')
    date_time = DateTimeField(null=True)
    measurement_stream = ForeignKeyField(db_column='measurement_stream_id', null=True, model=MeasurementStreams, to_field='measurement_stream')


    class Meta:
        db_table = 'comments'
        schema = 'fram_central'

class DataLinesLu(BaseModel):
    data_line = PrimaryKeyField(db_column='data_line_id')
    data_line_parent = ForeignKeyField(db_column='data_line_parent_id', null=True, model='self', to_field='data_line')
    delimiter = TextField(null=True)
    fixed_or_delimited = TextField()
    line_description = TextField(null=True)
    line_ending = TextField(null=True)
    line_name = TextField()
    line_order = IntegerField(null=True)
    logger_or_serial = TextField()
    note = TextField(null=True)
    number_fields_in_line_name = IntegerField(null=True)

    class Meta:
        db_table = 'data_lines_lu'
        schema = 'fram_central'

class DataFieldsLu(BaseModel):
    data_field = PrimaryKeyField(db_column='data_field_id')
    data_field_parent = ForeignKeyField(db_column='data_field_parent_id', null=True, model='self', to_field='data_field')
    data_line = ForeignKeyField(db_column='data_line_id', model=DataLinesLu, to_field='data_line')
    field_datatype = TextField()
    field_description = TextField(null=True)
    field_format = TextField(null=True)
    field_name = TextField()
    field_size = DecimalField(null=True)
    field_type_lu = IntegerField(db_column='field_type_lu_id')
    hemisphere = TextField(null=True)
    position = DecimalField(null=True)
    reading_type_lu = ForeignKeyField(db_column='reading_type_lu_id', null=True, model=Lookups, to_field='lookup')
    true_relative_magnetic = TextField(null=True)
    units_of_measure = TextField(null=True)
    uom_position = IntegerField(null=True)

    class Meta:
        db_table = 'data_fields_lu'
        schema = 'fram_central'

class FieldValidValuesLu(BaseModel):
    activation_date = DateTimeField()
    data_field = ForeignKeyField(db_column='data_field_id', model=DataFieldsLu, to_field='data_field')
    deactivation_date = DateTimeField(null=True)
    field_valid_value_lu = PrimaryKeyField(db_column='field_valid_value_lu_id')
    field_valid_value_parent = ForeignKeyField(db_column='field_valid_value_parent_id', null=True, model='self', to_field='field_valid_value_lu')
    is_target_value = BooleanField(null=True)
    reading_type_lu = IntegerField(db_column='reading_type_lu_id', null=True)
    valid_value = TextField()
    valid_value_description = TextField(null=True)

    class Meta:
        db_table = 'field_valid_values_lu'
        schema = 'fram_central'

class EquipmentFieldsLu(BaseModel):
    activation_date = DateTimeField()
    data_field = ForeignKeyField(db_column='data_field_id', model=DataFieldsLu, to_field='data_field')
    deactivation_date = DateTimeField(null=True)
    display_format = TextField(null=True)
    equipment_field = PrimaryKeyField(db_column='equipment_field_id')
    equipment = ForeignKeyField(db_column='equipment_id', model=EquipmentLu, to_field='equipment')
    idx_field_valid_value_lu = ForeignKeyField(db_column='idx_field_valid_value_lu_id', null=True, model=FieldValidValuesLu, to_field='field_valid_value_lu')
    is_parsed = BooleanField(null=True)
    parsing_priority = IntegerField(null=True)
    project_type_lu = ForeignKeyField(db_column='project_type_lu_id', model=Lookups, to_field='lookup')
    reading_basis_lu = IntegerField(db_column='reading_basis_lu_id', null=True)

    class Meta:
        db_table = 'equipment_fields_lu'
        schema = 'fram_central'

class MasterMeasurementType(BaseModel):
    meas_type_desc = CharField(null=True)
    meas_type_name = CharField(primary_key=True)
    name_of_coord1 = CharField(null=True)
    name_of_coord2 = CharField(null=True)

    class Meta:
        db_table = 'master_measurement_type'
        schema = 'fram_central'

class MasterMeasurement(BaseModel):
    graph_category = CharField(null=True)
    meas_storage_field_coord1 = CharField(null=True)
    meas_storage_field_coord2 = CharField(null=True)
    meas_storage_table = CharField(null=True)
    meas_type_name = ForeignKeyField(db_column='meas_type_name', null=True, model=MasterMeasurementType, to_field='meas_type_name')
    measurement_desc = CharField(null=True)
    measurement_name = CharField(primary_key=True)
    reference_field = CharField(null=True)
    reference_field_tag = CharField(null=True)
    units_of_measure_coord1 = CharField(null=True)
    units_of_measure_coord2 = CharField(null=True)
    value_type = CharField(null=True)
    variable_type = CharField(null=True)

    class Meta:
        db_table = 'master_measurement'
        schema = 'fram_central'

class MasterEstimator(BaseModel):
    derivn_method_code = TextField(null=True)
    doe = DateTimeField()
    estimator = PrimaryKeyField(db_column='estimator_id')
    estimator_name = TextField()
    measurement_name = ForeignKeyField(db_column='measurement_name', model=MasterMeasurement, to_field='measurement_name')
    precedence = IntegerField(null=True)
    tow_pt_est_deactivation_date = DateTimeField(null=True)

    class Meta:
        db_table = 'master_estimator'
        schema = 'fram_central'

class MasterRawDataDeviceSensor(BaseModel):
    device_code = TextField()
    device_sensor = PrimaryKeyField(db_column='device_sensor_id')
    sensor_max_reading1 = DecimalField(null=True)
    sensor_max_reading2 = DecimalField(null=True)
    sensor_min_reading1 = DecimalField(null=True)
    sensor_min_reading2 = DecimalField(null=True)
    sensor_type_code = TextField()

    class Meta:
        db_table = 'master_raw_data_device_sensor'
        schema = 'fram_central'

class MasterEstimatorComponent(BaseModel):
    device_sensor = ForeignKeyField(db_column='device_sensor_id', null=True, model=MasterRawDataDeviceSensor, to_field='device_sensor')
    estimator_component = DecimalField(db_column='estimator_component_id', primary_key=True)
    estimator = ForeignKeyField(db_column='estimator_id', null=True, model=MasterEstimator, to_field='estimator')
    measurement_name = ForeignKeyField(db_column='measurement_name', null=True, model=MasterMeasurement, to_field='measurement_name')

    class Meta:
        db_table = 'master_estimator_component'
        schema = 'fram_central'

class MasterRawDataRecordedErrorType(BaseModel):
    data_test = CharField(null=True)
    error_description = CharField(null=True)
    error = DecimalField(db_column='error_id', primary_key=True)
    error_indication = CharField(null=True)
    error_name = CharField(null=True, unique=True)
    resolution_strategy = CharField(null=True)
    sw_tag = CharField(null=True)

    class Meta:
        db_table = 'master_raw_data_recorded_error_type'
        schema = 'fram_central'

class OperationLatLon(BaseModel):
    attachment_position = TextField(null=True)
    data_sentence_field = IntegerField(db_column='data_sentence_field_id')
    enviro_net_raw_strings = IntegerField(db_column='enviro_net_raw_strings_id', null=True)
    is_outright_bad = BooleanField(null=True)
    latitude_dd = DecimalField(null=True)
    longitude_dd = DecimalField(null=True)
    measurement_stream = ForeignKeyField(db_column='measurement_stream_id', null=True, model=MeasurementStreams, to_field='measurement_stream')
    operation_lat_lon = PrimaryKeyField(db_column='operation_lat_lon_id')
    reading_datetime = TextField(null=True)
    sensor_db_files = IntegerField(db_column='sensor_db_files_id', null=True)

    class Meta:
        db_table = 'operation_lat_lon'
        schema = 'fram_central'

class OperationMeasurements(BaseModel):
    date_time = DateTimeField(null=True)
    is_not_valid = BooleanField(null=True)
    measurement_stream = ForeignKeyField(db_column='measurement_stream_id', model=MeasurementStreams, to_field='measurement_stream')
    operation_measurement = PrimaryKeyField(db_column='operation_measurement_id')
    raw_string = IntegerField(db_column='raw_string_id', null=True)
    reading_alpha = TextField(null=True)
    reading_numeric = DecimalField(null=True)
    validation_lu = ForeignKeyField(db_column='validation_lu_id', null=True, model=Lookups, to_field='lookup')

    class Meta:
        db_table = 'operation_measurements'
        schema = 'fram_central'

class OperationMeasurements2016(BaseModel):
    date_time = DateTimeField(null=True)
    is_not_valid = BooleanField(null=True)
    measurement_stream = IntegerField(db_column='measurement_stream_id')
    operation_measurement = IntegerField(db_column='operation_measurement_id')
    raw_file = IntegerField(db_column='raw_file_id', null=True)
    raw_string = IntegerField(db_column='raw_string_id', null=True)
    reading_alpha = TextField(null=True)
    reading_number = DecimalField(null=True)
    validation_lu = IntegerField(db_column='validation_lu_id', null=True)

    class Meta:
        db_table = 'operation_measurements_2016'
        schema = 'fram_central'

class OperationMeasurements2017(BaseModel):
    date_time = DateTimeField(null=True)
    is_not_valid = BooleanField(null=True)
    measurement_stream = IntegerField(db_column='measurement_stream_id')
    operation_measurement = IntegerField(db_column='operation_measurement_id')
    raw_file = IntegerField(db_column='raw_file_id', null=True)
    raw_string = IntegerField(db_column='raw_string_id', null=True)
    reading_alpha = TextField(null=True)
    reading_number = DecimalField(null=True)
    validation_lu = IntegerField(db_column='validation_lu_id', null=True)

    class Meta:
        db_table = 'operation_measurements_2017'
        schema = 'fram_central'

class OperationMeasurementsErr(BaseModel):
    date_time = DateTimeField(null=True)
    is_not_valid = BooleanField(null=True)
    measurement_stream = IntegerField(db_column='measurement_stream_id')
    operation_measurement = IntegerField(db_column='operation_measurement_id')
    raw_file = IntegerField(db_column='raw_file_id', null=True)
    raw_string = IntegerField(db_column='raw_string_id', null=True)
    reading_alpha = TextField(null=True)
    reading_number = DecimalField(null=True)
    validation_lu = IntegerField(db_column='validation_lu_id', null=True)

    class Meta:
        db_table = 'operation_measurements_err'
        schema = 'fram_central'

class OperationsTest(BaseModel):
    activation_date = TextField(null=True)
    captain = IntegerField(db_column='captain_id', null=True)
    date = TextField(null=True)
    deactivation_date = TextField(null=True)
    fpc = IntegerField(db_column='fpc_id', null=True)
    operation = IntegerField(db_column='operation_id', null=True)
    operation_name = TextField(null=True)
    operation_number = TextField(null=True)
    operation_type_lu = IntegerField(db_column='operation_type_lu_id', null=True)
    parent_operation = IntegerField(db_column='parent_operation_id', null=True)
    project_lu = IntegerField(db_column='project_lu_id', null=True)
    recorder = IntegerField(db_column='recorder_id', null=True)
    scientist_1 = IntegerField(db_column='scientist_1_id', null=True)
    scientist_2 = IntegerField(db_column='scientist_2_id', null=True)
    sequence_number = IntegerField(null=True)
    target_station = IntegerField(db_column='target_station_id', null=True)
    vessel = IntegerField(db_column='vessel_id', null=True)

    class Meta:
        db_table = 'operations_test'
        schema = 'fram_central'

class PerformanceDetails(BaseModel):
    is_unsat_factor = BooleanField(null=True)
    operation = ForeignKeyField(db_column='operation_id', model=Operations, to_field='operation')
    performance_detail = PrimaryKeyField(db_column='performance_detail_id')
    performance_type_lu = ForeignKeyField(db_column='performance_type_lu_id', model=Lookups, to_field='lookup')
    is_postseason = BooleanField(null=True)

    class Meta:
        db_table = 'performance_details'
        schema = 'fram_central'

class StationRemovals(BaseModel):
    activation_date = DateTimeField()
    deactivation_date = DateTimeField(null=True)
    is_active = BooleanField(null=True)
    removal_type_lu = ForeignKeyField(db_column='removal_type_lu_id', model=Lookups, to_field='lookup')
    station_inventory = ForeignKeyField(db_column='station_inventory_id', model=StationInventoryLu, to_field='station_inventory')
    station_removal = PrimaryKeyField(db_column='station_removal_id')

    class Meta:
        db_table = 'station_removals'
        schema = 'fram_central'

class StationStatus(BaseModel):
    operation = IntegerField(db_column='operation_id', null=True)
    station_inventory = ForeignKeyField(db_column='station_inventory_id', model=StationInventoryLu, to_field='station_inventory')
    station_status = PrimaryKeyField(db_column='station_status_id')
    station_status_note = TextField(null=True)
    station_status_type_lu = ForeignKeyField(db_column='station_status_type_lu_id', model=Lookups, to_field='lookup')
    status_date = IntegerField(null=True)

    class Meta:
        db_table = 'station_status'
        schema = 'fram_central'

class TagMask(BaseModel):
    format_mask = CharField(null=True)
    tag_mask_code = CharField(primary_key=True)
    tag_mask_desc = CharField(null=True)

    class Meta:
        db_table = 'tag_mask'
        schema = 'fram_central'

class TaxonomicLevel(BaseModel):
    activation_date = DateTimeField()
    deactivation_date = DateTimeField(null=True)
    is_para_phyletic = BooleanField(null=True)
    taxon_level_name = TextField()
    taxonomic_level = PrimaryKeyField(db_column='taxonomic_level_id')

    class Meta:
        db_table = 'taxonomic_level'
        schema = 'fram_central'

class Taxonomy(BaseModel):
    activation_date = DateTimeField()
    deactivation_date = DateTimeField(null=True)
    scientific_label = TextField()
    taxon_name = TextField()
    taxonomic_level = ForeignKeyField(db_column='taxonomic_level_id', null=True, model=TaxonomicLevel, to_field='taxonomic_level')
    taxonomy = PrimaryKeyField(db_column='taxonomy_id')
    taxonomy_parent = ForeignKeyField(db_column='taxonomy_parent_id', null=True, model='self', to_field='taxonomy')

    class Meta:
        db_table = 'taxonomy'
        schema = 'fram_central'

class TaxonAlias(BaseModel):
    activation_date = DateTimeField()
    deactivation_date = DateTimeField(null=True)
    is_valid_for_field = BooleanField(db_column='is_valid_for_field_id', null=True)
    taxon_alias = TextField()
    taxon_alias_id = PrimaryKeyField()
    taxon_alias_type = TextField()
    taxonomy = ForeignKeyField(db_column='taxonomy_id', model=Taxonomy, to_field='taxonomy')

    class Meta:
        db_table = 'taxon_alias'
        schema = 'fram_central'

class TaxonomyDim(BaseModel):
    abbreviated_name = CharField(null=True)
    acoustics_species = IntegerField(db_column='acoustics_species_id', null=True)
    class_30 = CharField(null=True)
    common_name = CharField(null=True)
    family_50 = CharField(null=True)
    genus_70 = CharField(null=True)
    grp_nonstandard_taxon_99 = CharField(null=True)
    grp_reg_depth_category = CharField(null=True)
    hookandline_species = IntegerField(db_column='hookandline_species_id', null=True)
    infraclass_34 = CharField(null=True)
    infraorder_44 = CharField(null=True)
    itis_taxonomic_serial_no = IntegerField(null=True)
    kingdom_10 = CharField(null=True)
    norpac_species = IntegerField(db_column='norpac_species_id', null=True)
    observer_species = IntegerField(db_column='observer_species_id', null=True)
    order_40 = CharField(null=True)
    pacfin_nom_spid = CharField(null=True)
    pacfin_spid = CharField(null=True)
    phylum_20 = CharField(null=True)
    record_type = CharField(null=True)
    scientific_name = CharField(null=True)
    scientific_name_taxonomic_level = CharField(null=True)
    species_80 = CharField(null=True)
    species_category = CharField(null=True)
    species_sub_category = CharField(null=True)
    structure_source = CharField(null=True)
    subclass_32 = CharField(null=True)
    subfamily_52 = CharField(null=True)
    suborder_42 = CharField(null=True)
    subphylum_22 = CharField(null=True)
    subspecies_82 = CharField(null=True)
    superclass_28 = CharField(null=True)
    superfamily_48 = CharField(null=True)
    superorder_38 = CharField(null=True)
    taxonomy_whid = IntegerField(null=True)
    trawl_survey_species = IntegerField(db_column='trawl_survey_species_id', null=True)
    tribe_60 = CharField(null=True)
    worms_aphiaid = IntegerField(null=True)

    class Meta:
        db_table = 'taxonomy_dim'
        schema = 'fram_central'

