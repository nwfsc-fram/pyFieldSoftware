# -----------------------------------------------------------------------------
# Name:        ObserverDBMigrations.py
# Purpose:     OPTECS SOAP support for db syncing, using zeep
# http://docs.python-zeep.org/en/master/
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     Dec 20, 2016
# License:     MIT
# -----------------------------------------------------------------------------
import logging
from PyQt5.QtCore import QObject
from apsw import SQLError

# from playhouse.migrate import *
from peewee import TextField, IntegerField, FloatField, ForeignKeyField
from playhouse.migrate import SqliteMigrator, migrate

from py.observer.ObserverDBBaseModel import database
from py.observer.ObserverDBModels import Trips, HookCounts
from py.observer.ObserverDBUtil import ObserverDBUtil


class ObserverDBMigrations(QObject):
    # Add fields required by DB sync, but not by ObserverDBModel
    nullable_text_field = TextField(null=True)
    nullable_int_field = IntegerField(null=True)
    nullable_float_field = FloatField(null=True)

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self.migrator = SqliteMigrator(database)

    def perform_migrations(self) -> None:
        self._logger.info('Performing any pending database migrations.')

        # LOOKUPS
        try:
            migrate(
                self.migrator.add_column('LOOKUPS', 'MODIFIED_BY', self.nullable_int_field),
                self.migrator.add_column('LOOKUPS', 'MODIFIED_DATE', self.nullable_text_field),
                self.migrator.add_column('LOOKUPS', 'SORT_ORDER', self.nullable_int_field),
                self.migrator.add_column('LOOKUPS', 'CREATED_BY', self.nullable_int_field),
                self.migrator.add_column('LOOKUPS', 'CREATED_DATE', self.nullable_text_field),
            )
            self._logger.info('Migrated LOOKUPS')
        except SQLError:
            pass

        # VESSEL_CONTACTS
        self.migrate_created_modified('VESSEL_CONTACTS')

        # VESSELS
        self.migrate_created_modified('VESSELS')

        # SPECIES
        self.migrate_created_modified('SPECIES')
        try:
            migrate(
                self.migrator.add_column('SPECIES', 'ACTIVE', self.nullable_int_field)
            )
            self._logger.info('Added SPECIES.ACTIVE')
        except SQLError:
            pass

        # USERS
        self.migrate_created_modified('USERS')

        # PORTS
        self.migrate_created_modified('PORTS')

        # FIRST_RECEIVER
        self.migrate_created_modified('FIRST_RECEIVER')

        # CATCH_CATEGORIES
        self.migrate_created_modified('CATCH_CATEGORIES')
        try:
            migrate(
                self.migrator.add_column('CATCH_CATEGORIES', 'ACTIVE', self.nullable_int_field)
            )
            self._logger.info('Added CATCH_CATEGORIES.ACTIVE')
        except SQLError:
            pass

        # USER_PROGRAM_ROLES
        self.migrate_created_modified('USER_PROGRAM_ROLES')

        # PROGRAMS
        self.migrate_created_modified('PROGRAMS')

        # PROGRAM_ROLES
        self.migrate_created_modified('PROGRAM_ROLES')

        # ROLES
        self.migrate_created_modified('ROLES')

        # SPECIES_COMPOSITION_ITEMS
        self.migrate_speciescomp_extrapolated_weight()

        # SPECIES_COMPOSITION_BASKETS
        self.migrate_speciescompbaskets_is_tally()
        self.migrate_speciescompbaskets_is_subsample()

        #TER flags TODO: remove this migration once all DB files used have these flags
        self.migrate_debriefer_only()  # FIELD-2101
        self.migrate_status_optecs()  # FIELD-2100

        # COMMENTS
        self.migrate_comments()

        # TRIPS
        trips_extra_fields = {"MODIFIED_BY": self.nullable_int_field,
                              "MODIFIED_DATE": self.nullable_text_field,
                              "ROW_PROCESSED": self.nullable_text_field,
                              "ROW_STATUS": self.nullable_text_field,
                              }

        try:
            for key, value in trips_extra_fields.items():
                migrate(
                    self.migrator.add_column('TRIPS', key, value),
                )
            self._logger.info('Migrated TRIPS')
        except SQLError:
            pass

        # Create HOOK_COUNTS
        self.create_hook_counts()

        # Track FG or TRAWL when creating a Trip
        try:
            migrate(
                self.migrator.add_column('TRIPS', 'IS_FG_TRIP_LOCAL', self.nullable_int_field)
                # 1 if FG trip
            )
            self._logger.info('Migrated TRIPS.IS_FG_TRIP_LOCAL')
        except SQLError:
            pass

        # Temp BIOLIST # for Sets
        try:
            migrate(
                self.migrator.add_column('FISHING_ACTIVITIES', 'BIOLIST_LOCALONLY', self.nullable_int_field)
            )
            self._logger.info('Migrated FISHING_ACTIVITIES.BIOLIST_LOCALONLY')
        except SQLError:
            pass

        # Track if user selected EFP as No to get around TER
        try:
            migrate(
                self.migrator.add_column('FISHING_ACTIVITIES', 'EFP_LOCALONLY', self.nullable_int_field)
            )
            self._logger.info('Migrated FISHING_ACTIVITIES.EFP_LOCALONLY')
        except SQLError:
            pass
        ObserverDBUtil.db_fix_empty_string_nulls(self._logger)

        # Add float fields to FISHING_ACTIVITIES
        try:
            migrate(
                self.migrator.add_column('FISHING_ACTIVITIES', 'TOTAL_HOOKS_UNROUNDED', self.nullable_float_field),
                self.migrator.add_column('CATCHES', 'HOOKS_SAMPLED_UNROUNDED', self.nullable_float_field)
            )
            self._logger.info('Migrated FISHING_ACTIVITIES.EFP_LOCALONLY')
        except SQLError:
            pass

    def migrate_created_modified(self, table_name: str) -> None:
        """
        Migration adds "standard" CREATED_BY, CREATED_DATE, 
        MODIFIED_BY, and MODIFIED_DATE columns
        @param table_name: 
        @return: 
        """
        migrate_columns = (('CREATED_BY', self.nullable_int_field),
                           ('CREATED_DATE', self.nullable_text_field),
                           ('MODIFIED_BY', self.nullable_int_field),
                           ('MODIFIED_DATE', self.nullable_text_field))
        for new_column in migrate_columns:
            try:
                column_name = new_column[0]
                column_type = new_column[1]
                migrate(
                    self.migrator.add_column(table_name, column_name, column_type)
                )
                self._logger.info(f'Added column {column_name} to {table_name}')
            except SQLError:
                pass

    def migrate_speciescomp_extrapolated_weight(self) -> None:
        """
        Easily track extrapolated weights for catch weight
        @return:
        """
        try:
            migrate(
                self.migrator.add_column('SPECIES_COMPOSITION_ITEMS', 'EXTRAPOLATED_SPECIES_WEIGHT',
                                         self.nullable_float_field),
            )
            self._logger.info('Added extrapolated_species_weight to SPECIES_COMPOSITION_ITEMS.')
        except SQLError:
            pass

    def migrate_speciescompbaskets_is_tally(self) -> None:
        """
        Easily track tally baskets
        @return:
        """
        try:
            migrate(
                self.migrator.add_column('SPECIES_COMPOSITION_BASKETS', 'IS_FG_TALLY_LOCAL',
                                         self.nullable_int_field),
            )
            self._logger.info('Added is_fg_tally_local to SPECIES_COMPOSITION_BASKETS.')
        except SQLError:
            pass

    def migrate_speciescompbaskets_is_subsample(self) -> None:
        """
        Easily track tally baskets
        @return:
        """
        try:
            migrate(
                self.migrator.add_column('SPECIES_COMPOSITION_BASKETS', 'IS_SUBSAMPLE',
                                         self.nullable_int_field),
            )
            self._logger.info('Added is_subsample to SPECIES_COMPOSITION_BASKETS.')
        except SQLError:
            pass

    def migrate_comments(self) -> None:
        """
        Add a FISHING_ACTIVITY_ID to COMMENT
        @return:
        """
        try:
            migrate(
                self.migrator.add_column('COMMENT', 'FISHING_ACTIVITY_ID', self.nullable_int_field)
                # Foreign Key is describe in ObserverDBModels.py
            )
            self._logger.info('Added column FISHING_ACTIVITY_ID to COMMENTS')
        except SQLError:
            pass

    def migrate_debriefer_only(self):
        """
        FIELD-2101: This column will be in the new versions 2.2, but old databases may be loaded in without
        This function will add it if missing.
        """
        try:
            """
            NOTE: migrator.add_column not working properly, throws
                SQLError: table TRIP_CHECKS__tmp__ has no column named CONSTRAINT", but still adds col
            migrate(self.migrator.add_column('TRIP_CHECKS', 'DEBRIEFER_ONLY', IntegerField(default=0, null=False)))
            """
            database.execute_sql('ALTER TABLE TRIP_CHECKS ADD COLUMN DEBRIEFER_ONLY INTEGER NOT NULL DEFAULT 0')
            self._logger.info(f"Adding column TRIP_CHECKS.DEBRIEFER_ONLY")
        except SQLError as e:
            self._logger.debug(f"TRIP_CHECKS.DEBRIEFER_ONLY col not added; {e}")

    def migrate_status_optecs(self):
        """
        FIELD-2100: This column will be in the new versions 2.2, but old databases may be loaded in without
        This function will add it if missing
        """
        try:
            """
            NOTE: migrator.add_column not working properly, throws
                SQLError: table TRIP_CHECKS__tmp__ has no column named CONSTRAINT"
            migrate(self.migrator.add_column('TRIP_CHECKS', 'STATUS_OPTECS', IntegerField(default=1, null=False)))
            """
            database.execute_sql('ALTER TABLE TRIP_CHECKS ADD COLUMN STATUS_OPTECS INTEGER NOT NULL DEFAULT 1')
            self._logger.info(f"Adding column TRIP_CHECKS.STATUS_OPTECS")
        except SQLError as e:
            self._logger.debug(f"TRIP_CHECKS.STATUS_OPTECS col not added; {e}")

    def create_hook_counts(self) -> None:
        """
        Add HOOK_COUNTS Table
        :return:
        """
        try:
            HookCounts.create_table()
            self._logger.info('Created HOOK_COUNTS table.')

        except SQLError:
            pass