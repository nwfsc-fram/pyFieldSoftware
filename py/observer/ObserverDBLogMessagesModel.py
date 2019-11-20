# -----------------------------------------------------------------------------
# Name:        ObserverDBLogMessagesModel.py
# Purpose:     Peewee model definitions for table to hold OPTECS log messages.
#              (Tables here is not part of Observer.db sync'ed with OBSPROD
#               - must be created by OPTECS)
#
# Author:      Jim Stearns <james.stearns@noaa.gov>
#
# Created:     19 September 2017
# License:     MIT
#
# ------------------------------------------------------------------------------

from peewee import *
from py.observer.ObserverDBBaseModel import BaseModel


class OptecsLogMessages(BaseModel):
    """
    OPTECS log messages. Written to DB table (as well as to file) to allow observer to upload
    with the database (one step rather than two).
    """
    optecs_log_message = PrimaryKeyField(db_column='OPTECS_LOG_MESSAGE_ID')
    # ISO 8061, with no T separator between date and time (space instead), plus milliseconds, no TZ.
    # Example:﻿ '2017-09-22 14:48:26.546'
    iso_date_time = TextField(db_column='ISO_DATE_TIME', null=True)
    # Most all log messages will be with a current trip defined.
    # But not all, so don't make trip a foreign key, and do allow it to be null.
    trip = IntegerField(db_column='TRIP_ID', null=True)
    # Considered using level number instead of level name to save a little space,
    # but integers are 8 bytes and the text is in the same ballpark, and more readable.
    level_name = TextField(db_column='LEVEL_NAME')
    file_name = TextField(db_column='FILE_NAME', null=True)
    line_no = IntegerField(db_column='LINE_NO', null=True)
    message = TextField(db_column='MESSAGE')
    # Thread names are MainThread and Dummy-n.
    # Thread IDs are a long integer. Save a little disk space by writing as thread identifier
    # as a single text digit: Map MainThread to "0" and Dummy-n threads to "n".
    thread = TextField(db_column='THREAD', null=True)

    class Meta:
        db_table = 'OPTECS_LOG_MESSAGES'
