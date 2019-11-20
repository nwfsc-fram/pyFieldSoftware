# from peewee import *
from playhouse.apsw_ext import TextField, IntegerField, PrimaryKeyField
from py.trawl_analyzer.Settings import SensorsModel as BaseModel


# database = SqliteDatabase('data\clean_sensors.db', **{})


class UnknownField(object):
    def __init__(self, *_, **__): pass


class EnviroNetRawFiles(BaseModel):
    activation_datetime = TextField(db_column='ACTIVATION_DATETIME', null=True)
    deactivation_datetime = TextField(db_column='DEACTIVATION_DATETIME', null=True)
    deployed_equipment = IntegerField(db_column='DEPLOYED_EQUIPMENT_ID', null=True)
    enviro_net_raw_files = PrimaryKeyField(db_column='ENVIRO_NET_RAW_FILES_ID')
    haul = TextField(db_column='HAUL_ID', null=True)
    raw_file = TextField(db_column='RAW_FILE', null=True)

    class Meta:
        db_table = 'ENVIRO_NET_RAW_FILES'

class EnviroNetRawStrings(BaseModel):
    date_time = TextField(db_column='DATE_TIME', index=True, null=True)
    deployed_equipment = IntegerField(db_column='DEPLOYED_EQUIPMENT_ID', null=True)
    enviro_net_raw_strings = PrimaryKeyField(db_column='ENVIRO_NET_RAW_STRINGS_ID')
    haul = TextField(db_column='HAUL_ID', null=True)
    raw_strings = TextField(db_column='RAW_STRINGS', null=True)

    class Meta:
        db_table = 'ENVIRO_NET_RAW_STRINGS'

class RawSentences(BaseModel):
    date_time = TextField(db_column='DATE_TIME', null=True)
    deployed_equipment = IntegerField(db_column='DEPLOYED_EQUIPMENT_ID', null=True)
    raw_sentence = TextField(db_column='RAW_SENTENCE', null=True)
    raw_sentence_id = PrimaryKeyField(db_column='RAW_SENTENCE_ID')

    class Meta:
        db_table = 'RAW_SENTENCES'

