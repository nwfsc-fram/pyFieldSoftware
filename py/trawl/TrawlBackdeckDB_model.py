from peewee import *
import os

# Look for subdirectory "data" in PWD, PWD's parent, or PWD's grandparent
if os.path.exists("data"):
    db = r"data\trawl_backdeck.db"
elif os.path.exists(r"..\data"):
    db = r"..\data\trawl_backdeck.db"
elif os.path.exists(r"..\..\data"):
    db = r"..\..\data\trawl_backdeck.db"

database = SqliteDatabase(db)

class UnknownField(object):
    pass

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
    content_type = IntegerField(db_column='CONTENT_TYPE_ID', null=True)
    display_name = TextField(db_column='DISPLAY_NAME', null=True)
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    is_last_n_operations = TextField(db_column='IS_LAST_N_OPERATIONS', null=True)
    is_most_recent = TextField(db_column='IS_MOST_RECENT', null=True)
    taxonomy = ForeignKeyField(db_column='TAXONOMY_ID', null=True, model=TaxonomyLu, to_field='taxonomy')

    class Meta:
        db_table = 'CATCH_CONTENT_LU'

class Hauls(BaseModel):
    depth_max = FloatField(db_column='DEPTH_MAX', null=True)
    depth_min = FloatField(db_column='DEPTH_MIN', null=True)
    depth_uom = TextField(db_column='DEPTH_UOM', null=True)
    end_datetime = TextField(db_column='END_DATETIME', null=True)
    haul = PrimaryKeyField(db_column='HAUL_ID')
    haul_number = TextField(db_column='HAUL_NUMBER', null=True, unique=True)
    is_test = TextField(db_column='IS_TEST', null=True)
    latitude_max = FloatField(db_column='LATITUDE_MAX', null=True)
    latitude_min = FloatField(db_column='LATITUDE_MIN', null=True)
    leg_number = TextField(db_column='LEG_NUMBER', null=True)
    longitude_max = FloatField(db_column='LONGITUDE_MAX', null=True)
    longitude_min = FloatField(db_column='LONGITUDE_MIN', null=True)
    pass_number = TextField(db_column='PASS_NUMBER', null=True)
    processing_status = TextField(db_column='PROCESSING_STATUS', null=True)
    project = IntegerField(db_column='PROJECT_ID', null=True)
    start_datetime = TextField(db_column='START_DATETIME', null=True)
    station_code = FloatField(db_column='STATION_CODE', null=True)
    vessel_color = TextField(db_column='VESSEL_COLOR', null=True)
    vessel_name = TextField(db_column='VESSEL_NAME', null=True)
    vessel_number = IntegerField(db_column='VESSEL_NUMBER', null=True)

    class Meta:
        db_table = 'HAULS'

class Catch(BaseModel):
    catch_content = ForeignKeyField(db_column='CATCH_CONTENT_ID', null=True, model=CatchContentLu, to_field='catch_content')
    catch = PrimaryKeyField(db_column='CATCH_ID')
    content_action_type = IntegerField(db_column='CONTENT_ACTION_TYPE_ID', null=True)
    display_name = TextField(db_column='DISPLAY_NAME', null=True)
    is_debris = TextField(db_column='IS_DEBRIS', null=True)
    is_mix = TextField(db_column='IS_MIX', null=True)
    is_subsample = TextField(db_column='IS_SUBSAMPLE', null=True)
    is_weight_estimated = TextField(db_column='IS_WEIGHT_ESTIMATED', null=True)
    mix_number = IntegerField(db_column='MIX_NUMBER', null=True)
    note = TextField(db_column='NOTE', null=True)
    operation = ForeignKeyField(db_column='OPERATION_ID', null=True, model=Hauls, to_field='haul')
    operation_type = IntegerField(db_column='OPERATION_TYPE_ID', null=True)
    parent_catch = ForeignKeyField(db_column='PARENT_CATCH_ID', null=True, model='self', to_field='catch')
    receptacle_seq = TextField(db_column='RECEPTACLE_SEQ', null=True)
    receptacle_type = IntegerField(db_column='RECEPTACLE_TYPE_ID', null=True)
    result_type = IntegerField(db_column='RESULT_TYPE_ID', null=True)
    sample_count_int = IntegerField(db_column='SAMPLE_COUNT_INT', null=True)
    species_sampling_plan = ForeignKeyField(db_column='SPECIES_SAMPLING_PLAN_ID', null=True, model=SpeciesSamplingPlanLu, to_field='species_sampling_plan')
    weight_kg = FloatField(db_column='WEIGHT_KG', null=True)
    is_fishing_related = TextField(db_column='IS_FISHING_RELATED', null=True)
    is_military_related = TextField(db_column='IS_MILITARY_RELATED', null=True)

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
    com_port = IntegerField(db_column='COM_PORT', null=True)
    data_bits = IntegerField(db_column='DATA_BITS', null=True)
    deactivation_date = TextField(db_column='DEACTIVATION_DATE', null=True)
    deployed_equipment = PrimaryKeyField(db_column='DEPLOYED_EQUIPMENT_ID')
    equipment = ForeignKeyField(db_column='EQUIPMENT_ID', null=True, model=Equipment, to_field='equipment')
    flow_control = TextField(db_column='FLOW_CONTROL', null=True)
    measurement_type = IntegerField(db_column='MEASUREMENT_TYPE_ID', null=True)
    operational_segment = IntegerField(db_column='OPERATIONAL_SEGMENT_ID', null=True)
    parity = TextField(db_column='PARITY', null=True)
    reader_or_writer = TextField(db_column='READER_OR_WRITER', null=True)
    stop_bits = FloatField(db_column='STOP_BITS', null=True)

    class Meta:
        db_table = 'DEPLOYED_EQUIPMENT'

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

class LatdepthMinmaxPeter(BaseModel):
    common_name_1 = TextField(db_column='COMMON_NAME_1', null=True)
    lat_validate = TextField(db_column='LAT_VALIDATE', null=True)
    max_depth_m = FloatField(db_column='MAX_DEPTH_M', null=True)
    max_lat_dd = FloatField(db_column='MAX_LAT_DD', null=True)
    max_length_cm = TextField(db_column='MAX_LENGTH_CM', null=True)
    max_wt_kg = TextField(db_column='MAX_WT_KG', null=True)
    min_depth_m = FloatField(db_column='MIN_DEPTH_M', null=True)
    min_lat_dd = FloatField(db_column='MIN_LAT_DD', null=True)
    min_wt_kg = TextField(db_column='MIN_WT_KG', null=True)
    scientific_name = TextField(db_column='SCIENTIFIC_NAME', null=True)
    taxonomic_level = TextField(db_column='TAXONOMIC_LEVEL', null=True)
    taxon = IntegerField(db_column='TAXON_ID', null=True)
    taxon_id_parent = IntegerField(db_column='TAXON_ID_PARENT', null=True)
    p12_or_less_hits = TextField(db_column='p12_OR_LESS_HITS', null=True)

    class Meta:
        db_table = 'LatDepth_MinMax_Peter'

class Notes(BaseModel):
    data_item = IntegerField(db_column='DATA_ITEM_ID', null=True)
    date_time = TextField(db_column='DATE_TIME', null=True)
    haul = ForeignKeyField(db_column='HAUL_ID', null=True, model=Hauls, to_field='haul')
    is_data_issue = TextField(db_column='IS_DATA_ISSUE', null=True)
    is_haul_validation = TextField(db_column='IS_HAUL_VALIDATION', null=True)
    is_software_issue = TextField(db_column='IS_SOFTWARE_ISSUE', null=True)
    note = TextField(db_column='NOTE', null=True)
    note_id = PrimaryKeyField(db_column='NOTE_ID')
    person = TextField(db_column='PERSON', null=True)
    screen_type = IntegerField(db_column='SCREEN_TYPE_ID', null=True)

    class Meta:
        db_table = 'NOTES'

class ParsingRules(BaseModel):
    delimiter = TextField(db_column='DELIMITER', null=True)
    end_position = IntegerField(db_column='END_POSITION', null=True)
    equipment = ForeignKeyField(db_column='EQUIPMENT_ID', null=True, model=Equipment, to_field='equipment')
    field_position = IntegerField(db_column='FIELD_POSITION', null=True)
    fixed_or_delimited = TextField(db_column='FIXED_OR_DELIMITED', null=True)
    line_ending = TextField(db_column='LINE_ENDING', null=True)
    line_starting = TextField(db_column='LINE_STARTING', null=True)
    measurement_name = TextField(db_column='MEASUREMENT_NAME', null=True)
    measurement_type = IntegerField(db_column='MEASUREMENT_TYPE_ID', null=True)
    parsing_rules = PrimaryKeyField(db_column='PARSING_RULES_ID')
    start_position = IntegerField(db_column='START_POSITION', null=True)
    units_of_measurement = TextField(db_column='UNITS_OF_MEASUREMENT', null=True)

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
    catch = ForeignKeyField(db_column='CATCH_ID', null=True, model=Catch, to_field='catch')
    measurement_type = IntegerField(db_column='MEASUREMENT_TYPE_ID', null=True)
    note = TextField(db_column='NOTE', null=True)
    numeric_value = FloatField(db_column='NUMERIC_VALUE', index=True, null=True)
    parent_specimen = ForeignKeyField(db_column='PARENT_SPECIMEN_ID', null=True, model='self', to_field='specimen')
    species_sampling_plan = ForeignKeyField(db_column='SPECIES_SAMPLING_PLAN_ID', null=True, model=SpeciesSamplingPlanLu, to_field='species_sampling_plan')
    specimen = PrimaryKeyField(db_column='SPECIMEN_ID')
    cpu = TextField(db_column='CPU', null=True)

    class Meta:
        db_table = 'SPECIMEN'

class State(BaseModel):
    is_active = TextField(db_column='IS_ACTIVE', null=True)
    parameter = TextField(db_column='PARAMETER', null=True)
    state = PrimaryKeyField(db_column='STATE_ID')
    value = TextField(db_column='VALUE', null=True)

    class Meta:
        db_table = 'STATE'

class TypesLu(BaseModel):
    category = TextField(db_column='CATEGORY', null=True)
    subtype = TextField(db_column='SUBTYPE', null=True)
    type = TextField(db_column='TYPE', null=True)
    type_id = PrimaryKeyField(db_column='TYPE_ID')

    class Meta:
        db_table = 'TYPES_LU'
        indexes = (
            (('category', 'type', 'subtype'), True),
        )

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


