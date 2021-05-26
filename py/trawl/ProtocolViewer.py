__author__ = 'Todd.Hay'


# -------------------------------------------------------------------------------
# Name:        ProtocolViewer.py
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     April 13, 2016
# License:     MIT
#-------------------------------------------------------------------------------
import logging
import unittest
from py.trawl.TrawlBackdeckDB_model import SpeciesSamplingPlanLu
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model


class ProtocolViewer:
    """
    This class is concerned with accessing the protocol information from the SQLite database.
    It was built as the protocol information spans four tables, three of which are recursive
    and so trying to query this via the peewee ORM is complicated, so I opted to use pure
    SQL for the queries
    """

    def __init__(self, app=None, db=None):
        self._app = app
        self._db = db

    def get_special_actions(self, taxon_id):
        """
        Method to retrieve all of the special actions for the given taxon_id, or for a species_sampling_plan that
        has listed as its taxonomy for a Kingdom with scientific name of Animalia (i.e. all animals)
        :param taxon_id:
        :return:
        """
        if not isinstance(taxon_id, int):
            return

        plans_sql = """
        WITH RECURSIVE  --
        sampling_plan_children(specplan, parspecplan, display, prot, pi, taxon_id, plan_name)  AS (
            SELECT SPECIES_SAMPLING_PLAN_ID, PARENT_SPECIES_SAMPLING_PLAN_ID, DISPLAY_NAME, PROTOCOL_ID, PRINCIPAL_INVESTIGATOR_ID, TAXONOMY_ID, PLAN_NAME
                FROM SPECIES_SAMPLING_PLAN_LU WHERE
                    (TAXONOMY_ID IN ((SELECT TAXONOMY_ID FROM TAXONOMY_LU WHERE SCIENTIFIC_NAME = 'Animalia' AND TAXONOMIC_LEVEL = 'Kingdom'), ?))
            UNION
            SELECT s.SPECIES_SAMPLING_PLAN_ID, s.PARENT_SPECIES_SAMPLING_PLAN_ID, s.DISPLAY_NAME, s.PROTOCOL_ID,
                s.PRINCIPAL_INVESTIGATOR_ID, s.TAXONOMY_ID, s.PLAN_NAME
                    FROM SPECIES_SAMPLING_PLAN_LU s, sampling_plan_children
            WHERE s.PARENT_SPECIES_SAMPLING_PLAN_ID = sampling_plan_children.specplan
        )
        select s.specplan AS PLAN, s.parspecplan AS PARENT_PLAN, s.display AS DISPLAY, s.prot AS PROTOCOL, s.pi as PI_ID,
        IFNULL(pi.LAST_NAME, (select last_name from PRINCIPAL_INVESTIGATOR_LU pi2 inner join SPECIES_SAMPLING_PLAN_LU sspl
            on pi2.principal_investigator_id = sspl.principal_investigator_id WHERE sspl.SPECIES_SAMPLING_PLAN_ID = s.parspecplan)) AS PI,
        IFNULL(s.taxon_id, (select taxonomy_id from SPECIES_SAMPLING_PLAN_LU sspl where sspl.SPECIES_SAMPLING_PLAN_ID = s.parspecplan)) as TAXON_ID, s.plan_name
        FROM sampling_plan_children s
        LEFT JOIN PRINCIPAL_INVESTIGATOR_LU pi ON pi.PRINCIPAL_INVESTIGATOR_ID = s.pi ORDER BY PI
        """

        protocol_sql = """
        WITH RECURSIVE protocol_children(n) AS (
            SELECT PROTOCOL_ID from PROTOCOL_LU WHERE PROTOCOL_ID IN (?)
            UNION
            SELECT p.PROTOCOL_ID FROM PROTOCOL_LU p, protocol_children
            WHERE p.PARENT_PROTOCOL_ID = protocol_children.n
        )
        SELECT t.TYPE, t.SUBTYPE, p.ACTION_TYPE_ID
        FROM PROTOCOL_LU p
        INNER JOIN TYPES_LU t ON p.ACTION_TYPE_ID = t.TYPE_ID
        WHERE p.PROTOCOL_ID in protocol_children AND ACTION_TYPE_ID IS NOT NULL;
        """
        #         SELECT p.DISPLAY_NAME, p.ACTION_TYPE_ID

        params = [taxon_id, ]
        plans = []
        for plan in self._db.execute(query=plans_sql, parameters=params):

            # Check if coral or salmon.  If not either, yet plan_name = FRAM Standard Survey then skip it
            is_coral = self._app.process_catch.checkSpeciesType("coral", plan[6])
            is_sponge = self._app.process_catch.checkSpeciesType("sponge", plan[6])
            is_salmon = self._app.process_catch.checkSpeciesType("salmon", plan[6])
            if not is_coral and not is_sponge and not is_salmon and plan[2] != "Whole Specimen ID":
                if plan[7] == "FRAM Standard Survey":
                    continue

            newplan = dict()
            newplan["plan"] = plan[0]
            newplan["parentPlan"] = plan[1]
            newplan["displayName"] = plan[2] if plan[2] else ""
            newplan["topProtocol"] = plan[3]
            newplan["piId"] = plan[4]
            newplan["pi"] = plan[5]
            newplan["taxonId"] = plan[6]

            actions = []
            prot_params = [newplan["topProtocol"],]
            for action in self._db.execute(query=protocol_sql, parameters=prot_params):
                newprot = {}

                displayName = action[0] if action[0] else ""

                # Set the widgetType - this drives which UI widgets are displayed on the right side of SpecialActionsScreen.qml
                # TODO Todd Hay - Fix the determination of widgetType as this is a big hack right now
                # todo: note from AB 2021 - this could be done by using the database to determine the widgettype
                newprot["widgetType"] = "id"
                # logging.info(f"displayName = {displayName}")
                # AB - modified this to include any displayName that includes 'photo' - 5/6/21
                # AB - modified this to include any displayName that includes 'presence' - 5/26/21
                if displayName.lower() in ["is age weight sample", "is sex length sample"] or \
                        'photo' in displayName.lower() or 'presence' in displayName.lower():
                    newprot["widgetType"] = "yesno"
                elif "sex" in displayName.lower():
                    newprot["widgetType"] = "sex"
                # AB - moved id check to later since this is the default and replaced with a check for 'barcode'
                # so it wouldn't assign a tag for those that should intake a barcode; also added diameter - 5/6/21
                elif "length" in displayName.lower() or \
                     "width" in displayName.lower() or \
                     "weight" in displayName.lower() or \
                     "blood plasma" in displayName.lower() or \
                     "barcode" in displayName.lower() or \
                     "diameter" in displayName.lower():
                    newprot["widgetType"] = "measurement"
                elif "maturity level" in displayName.lower():
                    newprot["widgetType"] = "maturityLevel"
                elif "excision site" in displayName.lower():
                    newprot["widgetType"] = "categoricalList"
                # AB - added to deal with Pyrosome project - will ask for location of predator (A/W, length, or catch)
                elif "location" in displayName.lower():
                    newprot["widgetType"] = "location"
                elif "id" in displayName.lower():
                    newprot["widgetType"] = "id"

                # AB - coral, sponge seem to work better if not hard coded like this - commented out 5/6/21
                if self._app.process_catch.checkSpeciesType("salmon", newplan["taxonId"]) and newplan["pi"] == "FRAM":
                    newprot["widgetType"] = "salmon"
                #elif self._app.process_catch.checkSpeciesType("coral", newplan["taxonId"]) and newplan["pi"] == "FRAM":
                #    newprot["widgetType"] = "coral"
                #elif self._app.process_catch.checkSpeciesType("sponge", newplan["taxonId"]) and newplan["pi"] == "FRAM":
                #    newprot["widgetType"] = "sponge"

                if action[1]:
                    displayName = str(action[1]) + " " + displayName

                newprot["displayName"] = displayName
                newprot["actionTypeId"] = action[2] if action[2] else ""
                actions.append(newprot)
            newplan["actions"] = actions

            plans.append(newplan)

        return plans

    def get_actions(self, taxon_id, principal_investigator):
        """
        Method to query the SPECIES_SAMPLING_PLAN table by taxon_id
        :param taxon_id: int - the taxonomy_id of the species to query
        :return: list - of dicts representing the associated actions + action subtypes
        """
        if not isinstance(taxon_id, int) or not isinstance(principal_investigator, int):
            return

        sql = """
        WITH RECURSIVE
        sampling_plan_children(n) AS (
            SELECT SPECIES_SAMPLING_PLAN_ID FROM SPECIES_SAMPLING_PLAN_LU WHERE TAXONOMY_ID = ? AND PRINCIPAL_INVESTIGATOR_ID = ?
            UNION
            SELECT s.SPECIES_SAMPLING_PLAN_ID FROM SPECIES_SAMPLING_PLAN_LU s, sampling_plan_children
            WHERE s.PARENT_SPECIES_SAMPLING_PLAN_ID = sampling_plan_children.n
        ),
        sampling_protocol_children(n) AS (
            SELECT PROTOCOL_ID from PROTOCOL_LU WHERE PROTOCOL_ID IN
                (SELECT PROTOCOL_ID FROM SPECIES_SAMPLING_PLAN_LU WHERE SPECIES_SAMPLING_PLAN_ID in sampling_plan_children)
            UNION
            SELECT p.PROTOCOL_ID FROM PROTOCOL_LU p, sampling_protocol_children
            WHERE p.PARENT_PROTOCOL_ID = sampling_protocol_children.n
        )
        SELECT t.TYPE, t.SUBTYPE,
        IFNULL(ssp.COUNT, (SELECT COUNT FROM SPECIES_SAMPLING_PLAN_LU WHERE PROTOCOL_ID = p.PARENT_PROTOCOL_ID)) AS COUNT,
        (SELECT ct.TYPE FROM TYPES_LU ct INNER JOIN SPECIES_SAMPLING_PLAN_LU sspl ON sspl.COUNT_TYPE_ID = ct.TYPE_ID WHERE sspl.COUNT_TYPE_ID =
        IFNULL(ssp.COUNT_TYPE_ID, (SELECT COUNT_TYPE_ID FROM SPECIES_SAMPLING_PLAN_LU WHERE PROTOCOL_ID = p.PARENT_PROTOCOL_ID))) AS 'COUNT TYPE',
        t.TYPE_ID
        FROM PROTOCOL_LU p
        LEFT JOIN TYPES_LU t ON p.ACTION_TYPE_ID = t.TYPE_ID
        LEFT JOIN SPECIES_SAMPLING_PLAN_LU ssp ON ssp.PROTOCOL_ID = p.PROTOCOL_ID
        WHERE p.PROTOCOL_ID IN (SELECT * FROM sampling_protocol_children spc ORDER BY n) AND t.TYPE IS NOT NULL;
        """
        params = [taxon_id, principal_investigator]
        results = []
        for row in self._db.execute(query=sql, parameters=params):
            action = dict()
            action["type"] = row[0]
            action["subType"] = row[1] if row[1] else ""
            action["count"] = row[2] if row[2] else None
            action["countType"] = row[3] if row[3] else ""
            action["typeId"] = row[4] if row[4] else None
            results.append(action)

        return results

    def get_display(self, taxon_id, principal_investigator):
        """
        Method to get the protocol name that is used to display in the various areas in the application
        :param taxon_id:
        :return:
        """

        if not isinstance(taxon_id, int) or not isinstance(principal_investigator, int):
            return

        for plan in SpeciesSamplingPlanLu.select().where(SpeciesSamplingPlanLu.taxonomy == taxon_id,
                                                         SpeciesSamplingPlanLu.principal_investigator == principal_investigator):
            return plan.display_name


class TestProtocols(unittest.TestCase):

    def setUp(self):
        # self._db
        pass