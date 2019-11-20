# -----------------------------------------------------------------------------
# Name:        ObserverDBErrorReportsModels.py
# Purpose:     Peewee model definitions for TER (Trip Error Reporting) tables.
#              (Tables here are not part of Observer.db sync'ed with OBSPROD - must be created by OPTECS)
#
# Author:      Jim Stearns <james.stearns@noaa.gov>
#
# Created:     15 March 2017
# License:     MIT
#
# ------------------------------------------------------------------------------

from peewee import *
from py.observer.ObserverDBBaseModel import BaseModel
from py.observer.ObserverDBModels import TripChecks, Trips


class TripIssues(BaseModel):
    """
    All of OBSPROD.TRIP_ISSUES fields except:
        CHECK_RESOLVED
        MODIFIED_*
        RESOLVED_*
    Primary Key: TRIP_ISSUE_ID
    Foreign Keys: TRIP_CHECKS.TRIP_CHECK_ID, TRIPS.TRIP_ID
    Non-nullable Fields (other than Keys):
        CHECK_RESOLVED, CREATED_DATE

    Created by hand from IFQTST DDL, but follows the Peewee convention
    of omitting "_id" from then python names of key fields.

    But note that key values that are not keys, but stored simply as data values
    for the error report, do have "_id" in their python names (e.g. bio_specimen_id).
    """
    trip_issue = PrimaryKeyField(db_column='TRIP_ISSUE_ID')
    trip_check = ForeignKeyField(db_column='TRIP_CHECK_ID', rel_model=TripChecks, to_field='trip_check')
    trip = ForeignKeyField(db_column='TRIP_ID', rel_model=Trips, to_field='trip')
    trip_issue_ack_id = IntegerField(db_column='TRIP_ISSUE_ACK_ID', null=True)
    notes = TextField(db_column='NOTES', null=True)
    created_by = IntegerField(db_column='CREATED_BY', null=True)
    # The field 'created_date' is required in IFQTST, yet CHECK_SQL doesn't insert value.
    # In order to use CHECK_SQL syntax without change, make field not required,
    # with the responsibility to set this field to the run date immediately after inserting it.
    created_date = TextField(db_column='CREATED_DATE', null=True)   # Not required but non-null is essential.
    fishing_activity_id = IntegerField(db_column='FISHING_ACTIVITY_ID', null=True)
    fishing_activity_num = IntegerField(db_column='FISHING_ACTIVITY_NUM', null=True)
    fishing_location_id = IntegerField(db_column='FISHING_LOCATION_ID', null=True)
    fishing_location = TextField(db_column='FISHING_LOCATION', null=True)
    catch_id = IntegerField(db_column='CATCH_ID', null=True)
    catch_num = IntegerField(db_column='CATCH_NUM', null=True)
    species_composition_id = IntegerField(db_column='SPECIES_COMPOSITION_ID', null=True)
    species_comp_item_id = IntegerField(db_column='SPECIES_COMP_ITEM_ID', null=True)
    bio_specimen_id = IntegerField(db_column='BIO_SPECIMEN_ID', null=True)
    species_name = TextField(db_column='SPECIES_NAME', null=True)
    bio_specimen_item_id = IntegerField(db_column='BIO_SPECIMEN_ITEM_ID', null=True)
    length_frequency_id = IntegerField(db_column='LENGTH_FREQUENCY_ID', null=True)
    dissection_id = IntegerField(db_column='DISSECTION_ID', null=True)
    error_value = TextField(db_column='ERROR_VALUE', null=True)
    error_item = TextField(db_column='ERROR_ITEM', null=True)
    fish_ticket_id = IntegerField(db_column='FISH_TICKET_ID', null=True)

    class Meta:
        db_table = 'TRIP_ISSUES'


class TripChecksOptecs(BaseModel):
    """
    A subsidiary table to TripChecks containing OPTECS-specific additional fields.
    Convention: all fields end with _optecs in order to emphasize their specificity to OPTECS.
    """
    trip_check = ForeignKeyField(db_column='TRIP_CHECK_ID', rel_model=TripChecks, to_field='trip_check')
    trip_check_optecs = PrimaryKeyField(db_column='TRIP_CHECK_OPTECS_ID')
    check_status_optecs = IntegerField(db_column='CHECK_STATUS_OPTECS', null=True)
    # Hold SQL if modified version required to run in OPTECS. Null => Not run or run as-is. See check_status_optecs.
    check_sql_optecs = TextField(db_column='CHECK_SQL_OPTECS', null=True)

    class Meta:
        db_table = 'TRIP_CHECKS_OPTECS'
