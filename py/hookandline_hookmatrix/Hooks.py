# Standard Python Libraries
import logging

# Third Party Libraries
from PyQt5.QtCore import QVariant, pyqtSlot, pyqtSignal, QObject, pyqtProperty
from PyQt5.QtQml import QJSValue

# Project Libraries
from py.common.FramListModel import FramListModel


class FullSpeciesListModel(FramListModel):

    def __init__(self, app=None):
        super().__init__()
        self._app = app
        self._rpc = self._app.rpc
        self.add_role_name(name="id")
        self.add_role_name(name="text")
        self.partition_size = 24

        self.populate_model()

    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()
        sql = """
            SELECT DISPLAY_NAME, CATCH_CONTENT_ID 
                FROM CATCH_CONTENT_LU
                WHERE CONTENT_TYPE_LU_ID = (SELECT LOOKUP_ID FROM LOOKUPS WHERE
                    TYPE = 'Catch Content' AND VALUE = 'Taxonomy')
                ORDER BY DISPLAY_NAME asc;
        """
        results = self._rpc.execute_query(sql=sql)
        for result in results:
            item = dict()
            item["id"] = result[1]
            item["text"] = result[0]
            self.appendItem(item)

    @pyqtSlot(int, name="getSubset", result=QVariant)
    def get_subset(self, index):
        """
        Method to return a subset of the FramListModel for use in a SwipeView for the fullSpecieslist
        :param index:
        :return:
        """
        return self.items[index * self.partition_size: (index+1) * self.partition_size]


class Hooks(QObject):

    fullSpeciesListModelChanged = pyqtSignal()
    hooksSelected = pyqtSignal(QVariant, arguments=["results", ])
    hooksChanged = pyqtSignal(QVariant, arguments=["angler_op_id"])  # signal to update hooks label in DropAngler.qml

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db
        self._rpc = self._app.rpc

        self._full_species_list_model = FullSpeciesListModel(self._app)
        self._non_fish_items = self._get_non_fish_items()  # added for issue #82

    def _get_non_fish_items(self):
        """
        Get list of hook items that are not fish/taxonomic
        e.g. Bait Back, No Bait, No Hook, Multiple Hook, Undeployed (subject to change going forward)
        :return: str[]
        """
        sql = '''
            select  display_name
            from    catch_content_lu
            where   taxonomy_id is null
        '''
        return [i[0] for i in self._rpc.execute_query(sql=sql)]

    @pyqtSlot(QVariant, name='isFish', result=bool)
    def is_fish(self, hooked_item):
        """
        Used for hook text styling (see #82)
        :param hooked_item: string from UI
        :return: bool
        """
        return hooked_item not in self._non_fish_items

    @pyqtProperty(FramListModel, notify=fullSpeciesListModelChanged)
    def fullSpeciesListModel(self):
        """
        Method to return the self._full_species_list for populating the repeater BackdeckButtons in the HooksScreen.qml
        :return:
        """
        return self._full_species_list_model

    def get_angler_op_id(self):
        """
        Method to return the angler operation id from the given state machine angler letter.  The Angler Operation ID
        is the OPERATIONS table record for the given angler, and all angler-related items are attached to that record.
        :return:
        """
        op_id = None
        mapping = {"A": self._app.state_machine.anglerAOpId,
                   "B": self._app.state_machine.anglerBOpId,
                   "C": self._app.state_machine.anglerCOpId}
        if self._app.state_machine.angler in ["A", "B", "C"]:
            op_id = mapping[self._app.state_machine.angler]

        logging.info(f"angler letter: {self._app.state_machine.angler} > op_id: {op_id}")

        return op_id

    @pyqtSlot(name="selectHooks")
    def select_hooks(self):
        """
        Method to select values for the five hooks
        :return:
        """
        angler_op_id = self.get_angler_op_id()
        sql = "SELECT RECEPTACLE_SEQ, DISPLAY_NAME FROM CATCH c WHERE c.OPERATION_ID = ?;"
        sql = """
            SELECT c.RECEPTACLE_SEQ, cc.DISPLAY_NAME
                FROM CATCH c LEFT JOIN CATCH_CONTENT_LU cc ON c.HM_CATCH_CONTENT_ID = cc.CATCH_CONTENT_ID
                WHERE c.OPERATION_ID = ?;
        """
        params = [angler_op_id, ]
        hooks = self._rpc.execute_query(sql=sql, params=params)
        if hooks:
            hooks = {x[0]: x[1] for x in hooks}
            logging.info(f"hooks = {hooks}")
        self.hooksSelected.emit(hooks)

    @pyqtSlot(int, str, name="saveHook")
    def save_hook(self, hook_number, species):
        """
        Method to save the hook data down to the database
        :param hooks: Dictionary of hook values
        :return:
        """
        # if isinstance(hooks, QJSValue):
        #     hooks = hooks.toVariant()

        # logging.info(f"hooks to save: {hooks}")

        angler_op_id = self.get_angler_op_id()

        species = species.replace("\n", " ")
        species_map = {"Bocaccio": "Bocaccio", "Vermilion": "Vermilion Rockfish",
                           "Bank": "Bank Rockfish", "Blue": "Blue Rockfish", "Canary": "Canary Rockfish",
                           "Copper": "Copper Rockfish",
                           "Cowcod": "Cowcod", "Greenblotched": "Greenblotched Rockfish",
                           "GSpot": "Greenspotted Rockfish", "Greenstriped": "Greenstriped Rockfish",
                           "Halfbanded": "Halfbanded Rockfish", "Lingcod": "Lingcod",
                           "Sanddab": "Sanddab Unidentified", "Speckled": "Speckled Rockfish",
                           "Squarespot": "Squarespot Rockfish", "Starry": "Starry Rockfish",
                           "Swordspine": "Swordspine Rockfish", "Widow": "Widow Rockfish",
                           "Yellowtail": "Yellowtail Rockfish"}
        species = species_map[species] if species in species_map else species

        # Insert CATCH table records
        try:
            # Determine if the CATCH record already exists (OPERATION_ID, RECEPTACLE_SEQ, and RECEPTACLE_TYPE_ID
            sql = """SELECT CATCH_ID FROM CATCH WHERE
                        OPERATION_ID = ? AND
                        RECEPTACLE_SEQ = ? AND
                        RECEPTACLE_TYPE_ID = (SELECT LOOKUP_ID FROM LOOKUPS WHERE
                                                TYPE = 'Receptacle Type' AND VALUE = 'Hook')
            """
            params = [angler_op_id, hook_number]
            results = self._rpc.execute_query(sql=sql, params=params)

            # UPDATE Results
            if results:
                sql = """
                    UPDATE CATCH 
                        SET HM_CATCH_CONTENT_ID = (SELECT CATCH_CONTENT_ID FROM CATCH_CONTENT_LU
                                WHERE DISPLAY_NAME = ?)
                    WHERE RECEPTACLE_SEQ = ? AND OPERATION_ID = ? AND CATCH_ID = ?;
                        
                """
                logging.info(f"catch results = {results}")
                params = [species, hook_number, angler_op_id, results[0][0]]
                logging.info(f"updating an existing catch record")

            # INSERT Results
            else:
                sql = """
                    INSERT INTO CATCH
                        (HM_CATCH_CONTENT_ID, RECEPTACLE_SEQ, RECEPTACLE_TYPE_ID, OPERATION_ID, OPERATION_TYPE_ID)
                        VALUES(
                            (SELECT CATCH_CONTENT_ID FROM CATCH_CONTENT_LU
                                WHERE DISPLAY_NAME = ?), 
                            ?, 
                            (SELECT LOOKUP_ID FROM LOOKUPS WHERE TYPE = 'Receptacle Type'
                                    AND VALUE = 'Hook'),
                            ?,
                            (SELECT LOOKUP_ID FROM LOOKUPS WHERE TYPE = 'Operation' AND VALUE = 'Angler')
                        );
                """
                params = [species, hook_number, angler_op_id]
                logging.info(f"inserting hook data: {params}")
            logging.info(f"params: {params}")
            adh = f"{self._app.state_machine.angler}{self._app.state_machine.drop}{self._app.state_machine.hook}"
            notify = {"speciesUpdate": {"station": "HookMatrix", "set_id": self._app.state_machine.setId, "adh": adh}}
            self._rpc.execute_query(sql=sql, params=params, notify=notify)
            logging.info(f"Hooks changed for angler op id {angler_op_id}")
            self.hooksChanged.emit(angler_op_id)  # received by DropAngler.qml

        except Exception as ex:

            logging.error(f"Error inserting hook data into CATCH table: {ex}")


        # ToDo - Todd Hay - INSERT SPECIMENS records

        # Insert SPECIMEN table records
        try:
            sql = "INSERT INTO SPECIMENS(CATCH_ID) VALUES(?);"
            params = []
            # self._rpc.execute_query(sql=sql, params=params)

        except Exception as ex:

            logging.error(f"Error inserting hook data into SPECIMENS table: {ex}")

    @pyqtSlot(int, str, name="deleteHook")
    def delete_hook(self, hook_number, species):
        """
        Method to delete an individual hook
        :param hook_number:
        :param species:
        :return:
        """
        logging.info(f"{hook_number}, {species}")

        try:
            angler_op_id = self.get_angler_op_id()

            # sql = """
            #     DELETE FROM CATCH WHERE
            #         DISPLAY_NAME = ? AND
            #         RECEPTACLE_SEQ = ? AND
            #         RECEPTACLE_TYPE_ID =
            #             (SELECT LOOKUP_ID FROM LOOKUPS WHERE TYPE = 'Receptacle Type'
            #                 AND VALUE = 'Hook') AND
            #         OPERATION_ID = ?
            # """

            # Check if Cutter Species or Best Species already exist, if so, don't delete the record, just remove the
            #   HM species
            sql = """
                SELECT CS_CATCH_CONTENT_ID, BEST_CATCH_CONTENT_ID FROM CATCH WHERE 
                    RECEPTACLE_SEQ = ? AND
                    RECEPTACLE_TYPE_ID = 
                        (SELECT LOOKUP_ID FROM LOOKUPS WHERE TYPE = 'Receptacle Type'
                            AND VALUE = 'Hook') AND
                    OPERATION_ID = ?                
            """
            params = [hook_number, angler_op_id]
            results = self._rpc.execute_query(sql=sql, params=params)
            if len(results) == 1:
                cs_species = results[0][0]
                best_species = results[0][1]

                # Nothing has been recorded by the cutter or fpc for this species, so go ahead and delete the catch record
                if cs_species is None and best_species is None:
                    sql = """
                        DELETE FROM CATCH WHERE
                            RECEPTACLE_SEQ = ? AND
                            RECEPTACLE_TYPE_ID = 
                                (SELECT LOOKUP_ID FROM LOOKUPS WHERE TYPE = 'Receptacle Type'
                                    AND VALUE = 'Hook') AND
                            OPERATION_ID = ?
                    """
                    params = [hook_number, angler_op_id]
                    logging.info(f"deleting the catch record, nothing else exists for it")

                # Something has been input for the cutter or best species, so just remove the hm species
                else:
                    sql = """
                        UPDATE CATCH SET HM_CATCH_CONTENT_ID = Null
                        WHERE
                            RECEPTACLE_SEQ = ? AND
                            RECEPTACLE_TYPE_ID = 
                                (SELECT LOOKUP_ID FROM LOOKUPS WHERE TYPE = 'Receptacle Type'
                                    AND VALUE = 'Hook') AND
                            OPERATION_ID = ?
                    """
                    params = [hook_number, angler_op_id]
                    logging.info(f"updating the catch record as cutter or best species exist")

            else:
                # We've hit a bad state as we should never encounter this
                sql = ""
                params = ""

            if sql != "":
                adh = f"{self._app.state_machine.angler}{self._app.state_machine.drop}{self._app.state_machine.hook}"
                notify = {"speciesUpdate": {"station": "HookMatrix", "set_id": self._app.state_machine.setId, "adh": adh}}
                self._rpc.execute_query(sql=sql, params=params, notify=notify)
                logging.info(f"hook deletion completed, params = {params}")
                self.hooksChanged.emit(angler_op_id)  # received by DropAngler.qml
                logging.info(f"Hooks changed for angler op id {angler_op_id}")

        except Exception as ex:

            logging.error(f"Error deleting a hook: {ex}")