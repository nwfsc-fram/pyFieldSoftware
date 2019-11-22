import logging
from copy import deepcopy

import arrow
from PyQt5.QtCore import QObject, QVariant, pyqtProperty, pyqtSlot, pyqtSignal

from py.hookandline.HookandlineFpcDB_model import Operations, Catch, CatchContentLu, Lookups, \
    SpeciesReviewView, JOIN
from playhouse.shortcuts import model_to_dict, dict_to_model

from py.common.FramListModel import FramListModel


class OperationsModel(FramListModel):

    def __init__(self, angler=""):
        super().__init__()
        self.add_role_name(name="id")
        self.add_role_name(name="text")

        self.populate_model()

    @pyqtSlot(name="populateModel")
    def populate_model(self):
        """
        Method to populate the operations model
        :return:
        """
        try:
            self.clear()

            self.appendItem({"id": -1, "text": "Set ID"})
            results = Operations.select()\
                .join(Lookups, on=(Lookups.lookup == Operations.operation_type_lu))\
                .where(Lookups.type=="Operation", Lookups.value=="Site")\
                .order_by(Operations.operation_number)
            for result in results:
                self.appendItem({'id': result.operation, 'text': result.operation_number})

        except Exception as ex:
            logging.error(f"Error populating the operations model: {ex}")


class AnglerSpeciesModel(FramListModel):

    operationsChanged = pyqtSignal()
    speciesChanged = pyqtSignal()
    resetBestSpecies = pyqtSignal()
    rowColorUpdated = pyqtSignal(str, int, arguments=['model', 'row'])
    bestSpeciesChanged = pyqtSignal(str, int, arguments=["model", "row"])

    def __init__(self, angler=""):
        super().__init__()
        self.add_role_name(name="catchId")
        self.add_role_name(name="adh")
        self.add_role_name(name="hookMatrixSpecies")
        self.add_role_name(name="cutterSpecies")
        self.add_role_name(name="bestSpecies")
        self.add_role_name(name="bestSpeciesIndex")
        self.add_role_name(name="rowColor")

        self._angler = angler
        self._species = self._load_species()
        self._operations = Operations()

        self.reset_model()

    @pyqtProperty(FramListModel, notify=operationsChanged)
    def operations(self):
        """
        Method to return the self._operations
        """
        return self._operations

    @pyqtProperty(QVariant, notify=speciesChanged)
    def species(self):
        """
        Method to return a list of all of the species
        :return:
        """
        return self._species

    @pyqtSlot()
    def reset_model(self):
        """
        Method to populate the model
        :return:
        """
        self.clear()

        try:
            template = {x: None for x in self._ordered_rolenames}
            for drop in ["1", "2", "3", "4", "5"]:
                for hook in ["1", "2", "3", "4", "5"]:
                    item = deepcopy(template)
                    item["adh"] = f"{self._angler}{drop}{hook}"
                    item["rowColor"] = None
                    self.appendItem(item)

        except Exception as ex:

            logging.error(f"Error populating the angler {self._angler} species model: {ex}")

    def _load_species(self):
        """
        Method to initialize the species for use with the Best Species ComboBox
        :return:
        """
        species = list()
        species.append({'id': -1, 'text': ""})
        results = CatchContentLu.select().order_by(CatchContentLu.display_name)
        for result in results:
            species.append({'id': result.catch_content, 'text': result.display_name})

        return species

    def save_best_species_to_db(self, set_id, adh, species):
        """
        Method to save the best species down to the database
        :param set_id: str - the set id of the operation for saving to the database
        :param adh:
        :param species:
        :return:
        """
        if len(adh) != 3:
            logging.error(f"ADH is not the right length for updating the best species: {adh}")
            return

        logging.info(f"save_best_species_to_db for set_id{set_id}, adh={adh}, species={species}")

        try:

            # Parse out the drop, angler, hook
            drop = adh[1]
            angler = adh[0]
            hook = adh[2]

            # Determine the best species catch content ID, it might be none if the best species is blank
            best_catch_content = None
            if species:
                best_catch_content = CatchContentLu.get(CatchContentLu.display_name == species).catch_content

            # Find the catch_id that matches this set_id and adh
            set_op = Operations.get(Operations.operation_number==set_id).operation
            drop_op = Operations.get(Operations.parent_operation==set_op, Operations.operation_number==drop).operation
            angler_op = Operations.get(Operations.parent_operation==drop_op, Operations.operation_number==angler).operation
            hook_type = Lookups.get(Lookups.type=="Receptacle Type", Lookups.value=="Hook").lookup
            operation_type = Lookups.get(Lookups.type=="Operation", Lookups.value=="Angler").lookup
            catch_record, created = Catch.get_or_create(operation=angler_op, receptacle_seq=hook,
                                                        receptacle_type=hook_type, operation_type=operation_type)

            logging.info(f"\t\tupdating catch best species with catch id={catch_record.catch} "
                         f"to best species content = {best_catch_content}")

            # NOT SURE WHY THE BELOW DOES NOT WORK, BUT IT DOESN'T
            # Sets = Operations.alias()
            # Drops = Operations.alias()
            # Anglers = Operations.alias()
            # results = Sets.select(Catch.catch) \
            #     .join(Drops, JOIN.LEFT_OUTER, on=(Drops.parent_operation == Sets.operation).alias('drop')) \
            #     .join(Anglers, JOIN.LEFT_OUTER, on=(Anglers.parent_operation == Drops.operation).alias('angler')) \
            #     .join(Catch, JOIN.LEFT_OUTER, on=(Catch.operation == Anglers.operation).alias('catch')) \
            #     .where(Sets.operation_number==set_id,
            #           Drops.operation_number==drop,
            #           Anglers.operation_number==angler,
            #           Catch.receptacle_seq==hook)
            # logging.info(f"the query is: {results}")
            #
            # if results.count() == 1:
            #
            #     logging.info(f"length is {results.count()}")

            # THIS BREAKS, AS DOES TRYING TO ITERATE ON results
            #     logging.info(f"result = {results.get().catch}")

            # Update the catch table with the new best species catch content ID
            Catch.update(best_catch_content=best_catch_content).where(Catch.catch==catch_record.catch).execute()

        except Exception as ex:

            logging.error(f"Error updating the best species: {ex}")

    @pyqtSlot(str, str, str, name="updateBestSpecies")
    def update_best_species(self, set_id, adh, species):
        """
        Method to update the model.  Inputs include the ADH, the source (HookMatrix or CutterStation)
            and the new species anme
        :param adh: values such as A12, C33, etc.  A/B/C followed by two digits from 1 - 5
        :param source: HookMatrix or CutterStation
        :param species: common name of the fish
        :return:
        """
        logging.info(f"update_best_species, set_id={set_id}, adh={adh}, species={species}")


        index = self.get_item_index(rolename="adh", value=adh)

        try:
            if index > -1:

                # Update the model with the latest best species
                self.setProperty(index=index, property="bestSpecies", value=species)
                best_species_list = [i for i, x in enumerate(self.species) if x["text"] == species]
                if len(best_species_list) == 1:
                    best_species_index = best_species_list[0]
                    logging.info(f"\t\tbest_species_index = {best_species_index}")
                    self.setProperty(index=index, property="bestSpeciesIndex", value=best_species_index)

                # Update the database with the latest best species
                self.save_best_species_to_db(set_id=set_id, adh=adh, species=species)

                item = self.get(index=index)
                hm_species = item["hookMatrixSpecies"]
                cs_species = item["cutterSpecies"]
                best_species = item["bestSpecies"]
                adh = item["adh"]
                row_color = "yellow"
                if hm_species != cs_species and best_species == "":
                    row_color = "pink"
                elif hm_species == cs_species:
                    if hm_species == best_species and hm_species is not None:
                        row_color = "lightgreen"
                    elif best_species in [None, ""]:
                        row_color = "pink"
                elif hm_species is None and cs_species is None and best_species in [None, ""]:
                    row_color = None
                elif best_species in [None, ""]:
                    row_color = None
                self.setProperty(index=index, property="rowColor", value=row_color)

                logging.info(f"\t\thm={hm_species}, cs={cs_species}, best={best_species}, color={row_color}")

                self.rowColorUpdated.emit(self._angler, index)


        except Exception as ex:
            logging.error(f"Error updating the best species: {ex}")

    def clear_species(self):
        """
        Method to clear the three species columns
        :return:
        """
        # cleared_items = [{"adh": x["adh"], "hookMatrixSpecies": None,
        #                   "cutterSpecies": None, "bestSpecies": x["bestSpecies"],
        #                   "rowColor": None} for x in self.items]
        # self.setItems(items=cleared_items)
        # self.resetBestSpecies.emit()
        #
        # return

        template = {x: None for x in self._ordered_rolenames}
        for index in range(self.rowCount()):
            old = self.get(index=index)
            new = deepcopy(template)
            new["adh"] = deepcopy(old["adh"])
            self.replace(index=index, item=new)

            # logging.info(f"index={index}, item={item}")
            # self.setProperty(index=index, property="adh", value=item["adh"])
            # self.setProperty(index=index, property="hookMatrixSpecies", value=None)
            # self.setProperty(index=index, property="cutterSpecies", value=None)
            # self.setProperty(index=index, property="bestSpecies", value="")
            # self.setProperty(index=index, property="rowColor", value=None)

        # self.resetBestSpecies.emit()


class SpeciesReview(QObject):

    anglerASpeciesModelChanged = pyqtSignal()
    anglerBSpeciesModelChanged = pyqtSignal()
    anglerCSpeciesModelChanged = pyqtSignal()
    operationsModelChanged = pyqtSignal()

    def __init__(self, app=None, db=None):
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._app = app
        self._db = db

        self._angler_a_species_model = AnglerSpeciesModel(angler="A")
        self._angler_b_species_model = AnglerSpeciesModel(angler="B")
        self._angler_c_species_model = AnglerSpeciesModel(angler="C")

        self._selected_set_id = "Set ID"
        self._operations_model = OperationsModel()

        # self.test_update_species_model()

    def test_update_species_model(self):
        """
        Test method for creating some bogus data for the species model
        :return:
        """
        items = [
            {"adh": "A11", "hookMatrixSpecies": "Bocaccio", "cutterSpecies": "Vermilion Rockfish"},
            {"adh": "A12", "hookMatrixSpecies": "Bocaccio", "cutterSpecies": "Bocaccio"},
            {"adh": "A13", "hookMatrixSpecies": "Canary Rockfish", "cutterSpecies": "Vermilion Rockfish"},
            {"adh": "A14", "hookMatrixSpecies": "Widow Rockfish", "cutterSpecies": "Cowcod"},
            {"adh": "A15", "hookMatrixSpecies": "Rosy Rockfish", "cutterSpecies": "Rosy Rockfish"},
            {"adh": "A21", "hookMatrixSpecies": "Cowcod", "cutterSpecies": ""},
            {"adh": "A22", "hookMatrixSpecies": "", "cutterSpecies": "Rosy Rockfish"},
            {"adh": "A23", "hookMatrixSpecies": "Bait Back", "cutterSpecies": "Bocaccio"},
            {"adh": "A24", "hookMatrixSpecies": "No Hook", "cutterSpecies": ""},
        ]
        for item in items:
            index = self._angler_a_species_model.get_item_index(rolename="adh", value=item["adh"])
            self._angler_a_species_model.setProperty(index=index,
                                                     property="hookMatrixSpecies", value=item["hookMatrixSpecies"])
            self._angler_a_species_model.setProperty(index=index,
                                                     property="cutterSpecies", value=item["cutterSpecies"])

    @pyqtProperty(FramListModel, notify=operationsModelChanged)
    def operationsModel(self):
        """
        Method to return the self._operations model
        :return:
        """
        return self._operations_model

    # @pyqtProperty(QVariant, notify=operationsChanged)
    # def operations(self):
    #     """
    #     Method to return a list of the site operations
    #     :return:
    #     """
    #     operations = list()
    #     operations.append({"id": -1, "text": "Set ID"})
    #     results = Operations.select()\
    #         .join(Lookups, on=(Lookups.lookup == Operations.operation_type_lu))\
    #         .where(Lookups.type=="Operation", Lookups.value=="Site")\
    #         .order_by(Operations.operation_number)
    #     for result in results:
    #         operations.append({'id': result.operation, 'text': result.operation_number})
    #     return operations

    @pyqtProperty(QVariant, notify=anglerASpeciesModelChanged)
    def anglerASpeciesModel(self):
        """
        Method to return the self._angler_a_species_model.  This is used for comparing HM v. CS species
        :return:
        """
        return self._angler_a_species_model

    @pyqtProperty(QVariant, notify=anglerBSpeciesModelChanged)
    def anglerBSpeciesModel(self):
        """
        Method to return the self._angler_b_species_model.  This is used for comparing HM v. CS species
        :return:
        """
        return self._angler_b_species_model

    @pyqtProperty(QVariant, notify=anglerCSpeciesModelChanged)
    def anglerCSpeciesModel(self):
        """
        Method to return the self._angler_c_species_model.  This is used for comparing HM v. CS species
        :return:
        """
        return self._angler_c_species_model

    @pyqtSlot(str, name="loadOperation")
    def load_operation(self, set_id):
        """
        Method to load the site operation's species data
        :param set_id:
        :return:
        """

        logging.info(f"before clearing A model")
        self.anglerASpeciesModel.reset_model()
        # self.anglerASpeciesModel.clear_species()
        logging.info(f"after clearing A model")

        self.anglerBSpeciesModel.reset_model()
        logging.info(f"after clearing B model")

        self.anglerCSpeciesModel.reset_model()
        logging.info(f"after clearing C model")

        logging.info(f"set_id = {set_id}")

        self._selected_set_id = set_id

        if set_id == "Set ID":
            return

        species = SpeciesReviewView.select().where(SpeciesReviewView.set_id == set_id)

        for f in species:

            try:

                if f.angler and f.drop and f.hook:
                    adh = f"{f.angler}{f.drop}{f.hook}"
                    if f.angler == "A":
                        model = self.anglerASpeciesModel
                    elif f.angler == "B":
                        model = self.anglerBSpeciesModel
                    elif f.angler == "C":
                        model = self.anglerCSpeciesModel
                    index = model.get_item_index(rolename="adh", value=adh)
                    if index >= 0:
                        model.setProperty(index=index, property="catchId", value=f.catch_id)

                        row_color = None
                        model.setProperty(index=index, property="hookMatrixSpecies", value=f.hm_species)
                        model.setProperty(index=index, property="cutterSpecies", value=f.cs_species)

                        best_species_list = [{"index": i, "text": x['text']}
                                             for i, x in enumerate(model.species) if x['text'] == f.best_species]
                        if len(best_species_list) == 1:
                            logging.info(f"best species exist, looks like: {best_species_list}")
                            best_species = best_species_list[0]["text"]
                            bs_index = best_species_list[0]["index"]
                            model.setProperty(index=index, property="bestSpecies", value=best_species)
                            model.setProperty(index=index, property="bestSpeciesIndex", value=bs_index)
                            if f.hm_species == f.cs_species and f.hm_species == best_species:
                                row_color = "lightgreen"
                            else:
                                row_color = "yellow"
                        else:
                            if f.hm_species == f.cs_species:
                                if f.hm_species is not None:
                                    row_color = "lightgreen"
                                    model.setProperty(index=index, property="bestSpecies", value=f.hm_species)
                                    bs_index_list = [i for i, x in enumerate(model.species) if x["text"] == f.hm_species]
                                    logging.info(f"best species DOES NOT exist, looks like: {bs_index_list}")
                                    if len(bs_index_list) == 1:
                                        bs_index = bs_index_list[0]
                                        model.setProperty(index=index, property="bestSpeciesIndex", value=bs_index)

                                    # Save new best species to the database
                                    model.save_best_species_to_db(set_id=set_id, adh=adh, species=f.hm_species)

                                else:
                                    row_color = None

                            else:
                                row_color = "pink"

                        logging.info(f"adh={adh}, rowColor={row_color}")

                        model.setProperty(index=index, property="rowColor", value=row_color)

            except Exception as ex:

                logging.error(f"Error updating the species review model: {ex}")

        logging.info(f"OPERATION LOADING IS FINISHED ... ")

    def species_changed(self, station, set_id, adh):
        """
        Method called by the HookLogger RpcServer when a species has been updated by either
        the HookMatrix or the CutterStation.  This method updates the table model accordingly
        :param station:
        :param set_id:
        :param adh:
        :return:
        """
        logging.info(f"species changed (via HookMatrix or Cutter): station={station}, set_id={set_id}, adh={adh}")

        if set_id != self._selected_set_id:
            logging.info(f"\t\tskipping update, not the same set_id")
            return

        if len(adh) != 3:
            logging.info(f"\t\tThe ADH is {len(adh)} characters long, so cannot determine"
                         f" which row to update, stopping SpeciesReviewDialog row update: adh={adh}")
            return

        if adh[0] not in ["A", "B", "C"]:
            logging.info(f"\t\tincorrect ADH provided, cannot determine which row to update: {adh}")
            return

        try:
            list_property = "cutterSpecies" if station == "CutterStation" else "hookMatrixSpecies"

            # Separate out the angler, drop, and hook
            angler = adh[0]
            drop = adh[1]
            hook = adh[2]

            # Find the appropriate model
            if angler == "A":
                model = self.anglerASpeciesModel
            elif angler == "B":
                model = self.anglerBSpeciesModel
            elif angler == "C":
                model = self.anglerCSpeciesModel
            index = model.get_item_index(rolename="adh", value=adh)

            # Query the SpeciesReviewView to see if a record exists, and if it does, update it, otherwise create it
            species = SpeciesReviewView.select().where(SpeciesReviewView.set_id == set_id,
                                                   SpeciesReviewView.angler == angler,
                                                   SpeciesReviewView.drop == drop,
                                                   SpeciesReviewView.hook == hook)

            if species.count() == 1:   # Row exists, update it
                record = species.get()
                cs_species = record.cs_species
                hm_species = record.hm_species
                best_species = record.best_species
                best_species_value = None
                best_species_index = -1
                row_color = None

                logging.info(f"\t\thm_species={hm_species}, cs_species={cs_species}, best_species={best_species}")

                # Determine the value to update the property
                list_property_value = cs_species if station == "CutterStation" else hm_species

                # Determine the correct row color
                best_species_list = [{"index": i, "text": x["text"]}
                                     for i, x in enumerate(model.species) if x['text'] == best_species]
                if len(best_species_list) == 1:
                    best_species_index = best_species_list[0]["index"]
                    best_species_value = best_species_list[0]["text"]
                    logging.info(f"\t\tbest_species_index = {best_species_index}")
                    if hm_species == cs_species and hm_species == best_species:
                        row_color = "lightgreen"
                    else:
                        row_color = "yellow"
                else:
                    if hm_species == cs_species:
                        if hm_species is not None and best_species is None:
                            best_species_list = [{"index": i, "text": x["text"]} for i, x in enumerate(model.species) if
                                                 x['text'] == hm_species]
                            if len(best_species_list) == 1:
                                best_species_index = best_species_list[0]["index"]
                                best_species_value = hm_species
                                logging.info(f"\t\tsaving best_species to db, best_series_index="
                                             f"{best_species_index} for best_species_value={best_species_value}")

                                model.save_best_species_to_db(set_id=set_id, adh=adh, species=best_species_value)
                                row_color = "lightgreen"
                        elif hm_species is None and best_species is None:
                            row_color = None

                    else:
                        row_color = "pink"

                logging.info(f"\t\trow_color={row_color}")

                # Update the model properties
                if index >= 0:
                    model.setProperty(index=index, property=list_property, value=list_property_value)
                    model.setProperty(index=index, property="bestSpecies", value=best_species_value)
                    model.setProperty(index=index, property="bestSpeciesIndex", value=best_species_index)
                    model.setProperty(index=index, property="rowColor", value=row_color)
                    model.rowColorUpdated.emit(angler, index)
                    model.bestSpeciesChanged.emit(angler, index)

            else:
                # This happens when a catch record is not found for the provided set_id + ADH
                logging.error(f"species_changed: Did not find a catch record to update ... hmmm, should never encounter this")

        except Exception as ex:

            logging.error(f"Unable to signal the species update: {ex}")
