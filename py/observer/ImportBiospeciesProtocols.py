# -----------------------------------------------------------------------------
# Name:        ImportBiospecProtocols.py
# Purpose:     Import CSV file into biospecimens protocols
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     August 23, 2016
# License:     MIT
# ------------------------------------------------------------------------------

# TO RUN THE IMPORT, ENABLE test_perform_import UNIT TEST BELOW

import logging
import unittest

from apsw import ConstraintError
from playhouse.csv_loader import *

# noinspection PyPackageRequirements
from py.observer.ObserverDBModels import StratumLu, StratumGroups, Programs, ProgramStratumGroupMtx, \
    FisheryStratumGroupsMtx, GeartypeStratumGroupMtx, SpeciesSamplingPlanLu, Lookups, Species, \
    ProtocolGroups, ProtocolGroupMtx
# noinspection PyPackageRequirements


class BiospeciesProtocolsLoader:
    """
    Create an in-memory CSV database and use it to populate protocols
    """
    # csv_db = None
    BioProtocols = None

    def __init__(self, db_filename):

        # Shut up peewee's SQL logging, if desired
        # logger = logging.getLogger('peewee')
        # logger.setLevel(logging.WARNING)

        self.csv_db = SqliteDatabase(':memory:')
        col_count = 16

        fields = [TextField(null=True) for _ in range(0, col_count)]
        self.BioProtocols = load_csv(self.csv_db, db_filename, fields=fields)

    def import_to_db(self, clear_old=False):
        """
        Import data into observer DB
        @param clear_old: clear old tables
        """
        logging.info('Importing {rec_cnt} records.'.format(rec_cnt=len(self.BioProtocols.select())))
        if clear_old:
            SpeciesSamplingPlanLu.raw('DELETE FROM SQLITE_SEQUENCE WHERE NAME="SPECIES_SAMPLING_PLAN_LU"').execute()
            SpeciesSamplingPlanLu.delete().execute()

            StratumLu.raw('DELETE FROM SQLITE_SEQUENCE WHERE NAME="STRATUM_LU"').execute()
            StratumLu.delete().execute()

            StratumGroups.raw('DELETE FROM SQLITE_SEQUENCE WHERE NAME="STRATUM_GROUPS"').execute()
            StratumGroups.delete().execute()

            ProtocolGroups.raw('DELETE FROM SQLITE_SEQUENCE WHERE NAME="PROTOCOL_GROUPS"').execute()
            ProtocolGroups.delete().execute()

            ProtocolGroupMtx.raw('DELETE FROM SQLITE_SEQUENCE WHERE NAME="PROTOCOL_GROUP_MTX"').execute()
            ProtocolGroupMtx.delete().execute()

            ProgramStratumGroupMtx.raw('DELETE FROM SQLITE_SEQUENCE WHERE NAME="PROGRAM_STRATUM_GROUP_MTX"').execute()
            ProgramStratumGroupMtx.delete().execute()

            FisheryStratumGroupsMtx.raw('DELETE FROM SQLITE_SEQUENCE WHERE NAME="FISHERY_STRATUM_GROUP_MTX"').execute()
            FisheryStratumGroupsMtx.delete().execute()

            GeartypeStratumGroupMtx.raw('DELETE FROM SQLITE_SEQUENCE WHERE NAME="GEARTYPE_STRATUM_GROUP_MTX"').execute()
            GeartypeStratumGroupMtx.delete().execute()

        self.create_default_groups()

        for rec in self.BioProtocols.select():  # all rows in CSV
            # noinspection PyUnusedLocal
            protocol_id = self.build_protocol_group(protocol_list=rec.protocol)
            fishery_id = self.build_fishery_group(fishery_list=rec.fishery, name=rec.fishery_group_name)
            geartype_id = self.build_geartype_group(geartype_list=rec.gear_type, name=rec.gear_type_group_name)

            program_id = self.get_program_group_id(rec.uber_program)

            biolist_id = self.get_biolist_id(name=rec.biosampling_list)
            disposition = 'D' if rec.disposition.lower()[0] == 'd' else 'R'  # Translate for consistency

            stratum_id = self.build_stratum(depth_name=rec.depth,
                                            program_id=program_id,
                                            fishery_id=fishery_id,
                                            geartype_id=geartype_id,
                                            disposition=disposition)

            species_ids = rec.species_codes.split(',') if rec.species_codes else None
            if species_ids is None:
                logging.warning(f'No species codes for {rec.species_species_group}')
            species_ids = [int(s.strip()) for s in species_ids] if species_ids else None
            self.build_species_sampling_plan(species_ids=species_ids,
                                             common_name=rec.species_species_group,
                                             disposition=disposition,
                                             protocol_group_id=protocol_id,
                                             stratum_id=stratum_id,
                                             biosample_list_lu_id=biolist_id)

    @staticmethod
    def build_stratum(depth_name, program_id, fishery_id, geartype_id, disposition):
        """
        Build STRATUM_LU
        @param depth_name: all, <30 fathoms, >30 fathoms -> determines RANGE_MIN, MAX, UNITS
        @param program_id: Program Group FK
        @param fishery_id: Fishery Group FK
        @param geartype_id: Gear Type FK
        @param disposition: 'DISCARD' /'RETAINED'
        @return: STRATUM_ID
        """
        depth_name_nosp = depth_name.lower().replace(' ', '')
        range_min = 0.
        range_max = -1.0
        if depth_name_nosp == '<30fathoms':
            range_max = 30.0
        elif depth_name_nosp == '>30fathoms':
            range_min = 30.001
        new_stratum = StratumLu.create(name=depth_name,
                                       program_group=program_id,
                                       fishery_group=fishery_id,
                                       gear_type_group=geartype_id,
                                       disposition=disposition,
                                       range_min=range_min,
                                       range_max=range_max,
                                       range_units='fathoms')
        return new_stratum.stratum

    @staticmethod
    def get_program_group_id(program_str):
        """
        Translate string to
        @param program_str: program string, e.g. 'ncs,cs'
        @return: record ID
        """
        try:
            program_str = program_str.lower()
            if program_str == 'ncs,cs':
                return StratumGroups.get(StratumGroups.group == 18).group
            elif program_str == 'cs':
                return StratumGroups.get(StratumGroups.group == 17).group
            elif program_str == 'cs':
                return StratumGroups.get(StratumGroups.group == 16).group
        except StratumGroups.DoesNotExist:
            logging.error('** cannot look up program id {}'.format(program_str))

    @staticmethod
    def create_default_groups():
        """
        Automatically create groups in STRATUM_GROUPS
        """
        # Fisheries, Programs, Gear Types

        premade = [
            {'group': 16, 'name': 'Non Catchshares', 'group_type': 'Programs'},
            {'group': 17, 'name': 'Catchshares', 'group_type': 'Programs'},
            {'group': 18, 'name': 'All', 'group_type': 'Programs'},
        ]
        for g in premade:
            StratumGroups.create(**g)

        for prog in Programs.select():
            ProgramStratumGroupMtx.create(group=18, program=prog.program)
            if 'Catch Shares' == prog.program_name:
                ProgramStratumGroupMtx.create(group=17, program=prog.program)
            else:
                ProgramStratumGroupMtx.create(group=16, program=prog.program)

    def build_protocol_group(self, protocol_list):
        """
        Build a PROTOCOL_GROUP
        @param protocol_list:  e.g. 'FL,FC,FORM'
        @return: ID of protocol group
        """
        try:
            protocol_list = protocol_list.strip().upper().replace(' ', '')  # ensure format like 'FL,FC,FORM'
            query = ProtocolGroups.select().where(ProtocolGroups.name == protocol_list)
            if query.exists():
                item = ProtocolGroups.get(ProtocolGroups.name == protocol_list)
                logging.debug('{} group already created, id = {}'.format(protocol_list, item.group))
                return item.group  # ID

            # use NAME as protocol list for easy reference
            pgroup = ProtocolGroups.create(name=protocol_list)

            protocol_ids = self.lookup_protocols(protocol_list)
            # Link ID's to this group
            # noinspection PyTypeChecker
            for prot_id in protocol_ids:
                ProtocolGroupMtx.create(group=pgroup.group, protocol_lu=prot_id)
            logging.info('Created {} -> {}'.format(protocol_list, protocol_ids))
            return pgroup.group  # ID
        except Exception as err:
            logging.error(f'Error building protocol group for {protocol_list}: {err}')

    @staticmethod
    def get_biolist_id(name):
        """
        Given a biolist name lookup or create new entry in STRATUM_GROUPS
        @param name: e.g. 'Biosample list 1'
        @return: group_id of new/existing biolist name
        """
        if not name:
            return None
        group_type = 'Biolist'
        biolist_id, _ = StratumGroups.get_or_create(name=name.lower().strip(), group_type=group_type)
        return biolist_id.group

    def build_fishery_group(self, fishery_list, name):
        """
        Build FISHERY_STRATUM_GROUPS_MTX and STRATUM_GROUPS
        NAME will be composed of fishery_list and nonunique name on spreadsheet
        @param fishery_list:  e.g. '1,2,3'
        @param name: name of fishery group from sheet, e.g. 'Nearshore', 'Trawl'
        @return: ID of fishery group
        """
        try:

            fishery_list = fishery_list.strip().replace(' ', '')  # ensure format like '1,2,3'
            group_name = '{name} ({fishery_list})'.format(name=name, fishery_list=fishery_list)
            query = StratumGroups.select().where(StratumGroups.name == group_name)
            if query.exists():
                item = StratumGroups.get(StratumGroups.name == group_name)
                logging.debug('{} group already created, id = {}'.format(group_name, item.group))
                return item.group  # ID

            fgroup = StratumGroups.create(name=group_name, group_type='Fishery')
            f_ids = self.lookup_fisheries(fishery_list)
            # Link ID's to this group
            # noinspection PyTypeChecker
            for f_lu_id in f_ids:
                FisheryStratumGroupsMtx.create(group=fgroup.group, fishery_lu=f_lu_id)
            logging.info('Created fisheries {} -> {}'.format(fishery_list, f_ids))
            return fgroup.group  # ID
        except Exception as err:
            logging.error('Error building fisheries group: {}'.format(err))

    def build_geartype_group(self, geartype_list, name):
        """
        Build GEARTYPE_STRATUM_GROUPS_MTX and STRATUM_GROUPS
        NAME will be composed of geartype_list and nonunique name on spreadsheet
        @param geartype_list:  e.g. '1,2,3'
        @param name: name of gear type group from sheet
        @return: ID of geartype group
        """
        try:

            geartype_list = geartype_list.strip().replace(' ', '')  # ensure format like '1,2,3'
            group_name = '{name} ({geartype_list})'.format(name=name, geartype_list=geartype_list)
            query = StratumGroups.select().where(StratumGroups.name == group_name)
            if query.exists():
                item = StratumGroups.get(StratumGroups.name == group_name)
                logging.debug('{} group already created, id = {}'.format(group_name, item.group))
                return item.group  # ID

            g_group = StratumGroups.create(name=group_name, group_type='Gear Type')
            g_ids = self.lookup_geartypes(geartype_list)
            # Link ID's to this group
            # noinspection PyTypeChecker
            for g_lu_id in g_ids:
                GeartypeStratumGroupMtx.create(group=g_group.group, geartype_lu=g_lu_id)
            logging.info('Created gear types {} -> {}'.format(geartype_list, g_ids))
            return g_group.group  # STRATUM_GROUPS GROUP_ID
        except Exception as err:
            logging.error('Error building gear type group: {}'.format(err))

    @staticmethod
    def build_species_sampling_plan(species_ids, common_name, disposition, protocol_group_id, stratum_id, biosample_list_lu_id):
        """
        SPECIES_SAMPLE_PLAN_LU
        @param species_ids: actual ID's of species to create plan for
        @param common_name: name or special category to build
        @param disposition: 'R' or 'D'
        @param protocol_group_id:
        @param stratum_id:
        @return:
        """
        ids = species_ids if species_ids else BiospeciesProtocolsLoader.get_species_id(common_name)
        if ids:
            for species_id in ids:
                if not protocol_group_id:
                    raise Exception(f'NO PROTOCOL GROUP ID for name {common_name} {species_ids}')
                plan_name = '{name} ({protname}, {stratname})'. \
                    format(name=common_name,
                           protname=ProtocolGroups.get(ProtocolGroups.group == protocol_group_id).name,
                           stratname=StratumLu.get(StratumLu.stratum == stratum_id).name
                           )
                logging.info('Building SpeciesSamplingPlanLu {}'.format(plan_name))
                try:
                    SpeciesSamplingPlanLu.create(plan_name=plan_name,
                                                 display_name=plan_name,
                                                 disposition=disposition,
                                                 species=species_id,
                                                 protocol_group=protocol_group_id,
                                                 stratum=stratum_id,
                                                 biosample_list_lu=biosample_list_lu_id
                                                 )
                except ConstraintError:
                    logging.warning('Species already in plan')
                    # possibly TODO(?): weight method, count, biosample_list_lu

    @staticmethod
    def get_species_id(common_name):
        """
        Return list of ID's for common name, or special cases such as Corals
        @param common_name: common name to try and match
        @return: [id, id...], None on fail
        """
        matches = []
        try:
            matched = Species.get(fn.lower(Species.common_name) == common_name.lower())
            matches.append(matched.species)  # ID
            return matches
        except Species.DoesNotExist:
            logging.warning('TODO: determine species for {}'.format(common_name))
            return None

    @staticmethod
    def lookup_protocols(protocols_str):
        """
        Given protocols, convert to list and return list of ID's
        @param protocols_str: e.g. 'FL,WS'
        @return: e.g. [8, 19]
        """
        found_ids = []
        try:
            prot_abbrevs = protocols_str.strip().replace(' ', '').split(',')
            for pa in prot_abbrevs:
                prot_id = Lookups.get((Lookups.lookup_type == 'PROTOCOL') & (Lookups.lookup_value == pa.strip())).lookup
                found_ids.append(prot_id)
            return found_ids

        except Lookups.DoesNotExist:
            # noinspection PyUnboundLocalVariable
            logging.error('*** Unable to look up protocol {} in group {} '
                          '(does not exist, check spreadsheet.)'.format(pa, protocols_str))
        except Exception as e:
            logging.error(f'{e}')

    @staticmethod
    def lookup_fisheries(fisheries_str):
        """
        Given fisheries, convert to list and return list of ID's from LOOKUPS
        @param fisheries_str: e.g. '15,16'
        @return: e.g. [608, 688]
        """
        found_ids = []
        try:
            fishery_ids = fisheries_str.strip().replace(' ', '').split(',')
            for fish in fishery_ids:
                fish_id = Lookups.get((Lookups.lookup_type == 'FISHERY') &
                                      (Lookups.lookup_value == fish.strip())).lookup
                found_ids.append(fish_id)
            return found_ids

        except Lookups.DoesNotExist:
            # noinspection PyUnboundLocalVariable
            logging.error('*** Unable to look up fishery {} in group {} '
                          '(does not exist, check db.)'.format(fish, fisheries_str))

    @staticmethod
    def lookup_geartypes(geartypes_str):
        """
        Given gear types, convert to list and return list of ID's from LOOKUPS
        @param geartypes_str: e.g. '15,16'
        @return: e.g. [608, 688]
        """
        found_ids = []
        try:
            gear_ids = geartypes_str.strip().replace(' ', '').split(',')
            for geartype in gear_ids:
                gear_id = Lookups.get(((Lookups.lookup_type == 'FG_GEAR_TYPE') |
                                       (Lookups.lookup_type == 'TRAWL_GEAR_TYPE')) &
                                      (Lookups.lookup_value == geartype.strip())).lookup
                found_ids.append(gear_id)
            return found_ids

        except Lookups.DoesNotExist:
            # noinspection PyUnboundLocalVariable
            logging.error('*** Unable to look up gear type {} in group {} '
                          '(does not exist, check db.)'.format(geartype, geartypes_str))

    def get_matching_species(self):
        """
        Find species that match, return list of non matching
        @return: [list of matching id #'s], [list of non matching name strings]
        """
        matching_species = []
        non_matching_species = []
        for species in [x.species_species_group for x in self.BioProtocols.select()]:
            try:
                matched = Species.get(fn.lower(Species.common_name) == species.lower())
                matching_species.append(matched.species)  # ID
            except Species.DoesNotExist:
                non_matching_species.append(species)
                pass

        logging.info('Non-matching species in CSV: {}'.format(str(non_matching_species)))
        return matching_species, non_matching_species


class TestImportBiospecies(unittest.TestCase):
    """
    Two purposes:
    * Perform actual import (undef skip test below)
    * Run tests for validity
    """

    imported = None
    # Look for subdirectory "data" in PWD, PWD's parent, or PWD's grandparent
    datapath = ""
    db_filename = "biospec_protocol.csv"
    for datapath_candidate in ("data", "..\data", "..\..\data"):
        if os.path.exists(datapath_candidate):
            datapath = datapath_candidate
            break
    import_filename = os.path.join(datapath, db_filename)

    protocols_loader = None

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        logging.info('Importing {}'.format(self.import_filename))
        self.assertTrue(os.path.isfile(self.import_filename), 'Cannot find file')
        self.protocols_loader = BiospeciesProtocolsLoader(self.import_filename)

    def test_initialization(self):
        pass

    # @unittest.skip
    def test_perform_import(self):
        """
        NOT a test- Intended for doing actual import of CSV.
        """
        logging.info('Performing Import of CSV...')
        self.protocols_loader.import_to_db(clear_old=True)
        logging.info('Import complete. DB Checkpoint set, .db file written.')

    # @unittest.skip
    def test_protocols(self):
        cases = [['FL,WS', [5007, 5019]],
                 ['FL,WS, FORM', [5007, 5019, 5022]],
                 ]
        for c in cases:
            ids = self.protocols_loader.lookup_protocols(c[0])
            self.assertEqual(ids, c[1])

    def test_fisheries(self):
        cases = [['15,16, 20', [608, 688, 852]],
                 ]
        for c in cases:
            ids = self.protocols_loader.lookup_fisheries(c[0])
            self.assertEqual(ids, c[1])

    def test_matching_species(self):
        match_cases = [10107, 10491]
        no_match_cases = ['All other rockfish species', 'Pinnipeds-Other']

        species_matched, species_no_match = self.protocols_loader.get_matching_species()

        self.assertLess(len(species_no_match), len(species_matched))
        for m in match_cases:
            self.assertTrue(m in species_matched)

        for n in no_match_cases:
            self.assertTrue(n in species_no_match)

