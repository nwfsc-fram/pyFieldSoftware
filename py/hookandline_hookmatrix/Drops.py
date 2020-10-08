# Standard Python Libraries
import logging
from collections import OrderedDict

# Third Party Libraries
from PyQt5.QtCore import QVariant, pyqtProperty, pyqtSlot, pyqtSignal, QObject
import arrow
from apsw import ConstraintError
import apsw

# Project Libraries
from py.common.FramListModel import FramListModel
from py.common.SoundPlayer import SoundPlayer


class PersonnelModel(FramListModel):

    def __init__(self, app=None):
        super().__init__()
        self._app = app
        self._rpc = self._app.rpc
        self.add_role_name(name="id")
        self.add_role_name(name="text")

        self.populate_model()

    def populate_model(self):
        """"
        Method to initially populate the model on startup
        """
        self.clear()
        sql = """
            SELECT DISTINCT p.PERSONNEL_ID, p.FIRST_NAME, p.LAST_NAME FROM SETTINGS s
            INNER JOIN PERSONNEL p ON s.VALUE = p.PERSONNEL_ID
            WHERE s.TYPE = 'Personnel' and s.VALUE IS NOT NULL
            ORDER BY p.FIRST_NAME, p.LAST_NAME;
        """
        results = self._rpc.execute_query(sql=sql)
        for result in results:
            item = dict()
            item["id"] = result[0]
            item["text"] = result[1] + "\n" + result[2]
            self.appendItem(item)


class Drops(QObject):

    personnelModelChanged = pyqtSignal()
    selection_result_obtained = pyqtSignal(QVariant, name="selectionResultsObtained", arguments=["results", ])
    operationAttributeDeleted = pyqtSignal()
    new_drop_added = pyqtSignal(QVariant, name="newDropAdded", arguments=["dropJson", ])
    exception_encountered = pyqtSignal(str, str, name="exceptionEncountered", arguments=["message", "action"])
    anglerGpLabelsSelected = pyqtSignal(str, str, str, arguments=["drop", "angler", "label"])
    anglerHooksLabelSelected = pyqtSignal(str, str, str, arguments=["drop", "angler", "label"])

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db
        self._rpc = self._app.rpc

        self._personnel_model = PersonnelModel(app=self._app)
        self._sound_player = SoundPlayer(app=self._app)

    @pyqtProperty(FramListModel, notify=personnelModelChanged)
    def personnelModel(self):
        """
        Method to return the self._personnel_model
        :return:
        """
        return self._personnel_model

    @pyqtSlot(int, result=QVariant, name="insertOperations")
    def insert_operations(self, drop_number: int) -> dict:
        """
        Method to insert a new drop and angler operations.  This is called by the DropAngler when the Start time button
        is clicked.  Remember that clicking one of the start time buttons activates the times for all three anglers,
        so this will involved inserting a drop operation as well as three children operations, one for each angler

        This method will return the Drop ID and  Angler IDs if they already exist.

        :param drop_number: Integer of the drop number
        :param start_time: string containing the starting time for the drop
        :return: Operation IDs - dictionary containing the drop, angler A, angler B, and angler C operation IDs
        """
        results = []

        logging.info(f"insert_operations: drop_number={str(int(drop_number))}")

        try:
            # Get the DROP_TYPE_LU_ID and ANGLER_TYPE_LU_ID from LOOKUPS table
            sql = "SELECT LOOKUP_ID, VALUE FROM LOOKUPS WHERE Type = 'Operation' AND (VALUE = 'Drop' OR VALUE = 'Angler');"
            lu_ids = self._rpc.execute_query(sql=sql)
            if lu_ids:
                drop_type_lu_id = [x[0] for x in lu_ids if x[1] == "Drop"][0]
                angler_type_lu_id = [x[0] for x in lu_ids if x[1] == "Angler"][0]

            # Check if the drop operation already exists in the OPERATIONS table
            # Handled via UNIQUE constraint on the OPERATIONS table

            # Insert the Drop Operation
            sql = "INSERT INTO OPERATIONS(PARENT_OPERATION_ID, OPERATION_NUMBER, OPERATION_TYPE_LU_ID) VALUES(?, ?, ?);"
            params = [self._app.state_machine.siteOpId, drop_number, drop_type_lu_id]
            drop_op_id = self._rpc.execute_query_get_id(sql=sql, params=params)
            results = {"Drop " + str(int(drop_number)): drop_op_id}

        except Exception as ex:

            if "apsw.ConstraintError" in str(ex):

                logging.info(f"Drop operation exists, getting the existing primary key: {ex}")
                sql = """
                    SELECT OPERATION_ID FROM OPERATIONS 
                    WHERE PARENT_OPERATION_ID = ? AND OPERATION_NUMBER = ? AND OPERATION_TYPE_LU_ID = ?;
                """
                drop_op_id = self._rpc.execute_query(sql=sql, params=params)
                if drop_op_id:
                    drop_op_id = drop_op_id[0][0]
                    results = {"Drop " + str(int(drop_number)): drop_op_id}

            else:

                logging.error(f"Error reached: {ex}")
                self._app.state_machine.drop = None
                self._app.state_machine.dropOpId = None
                self._app.state_machine.anglerAOpId = None
                self._app.state_machine.anglerBOpId = None
                self._app.state_machine.anglerCOpId = None
                message = f"Failed to insert or select drop {drop_number}"
                action = f"Please try again"
                self.exception_encountered.emit(message, action)
                return

        self._app.state_machine.dropOpId = drop_op_id

        # Check if the angler operations already exist in the OPERATIONS table
        # Handled via UNIQUE constraint on the OPERATIONS table between PARENT_OPERATION_ID, OPERATION_NUMBER, OPERATION_TYPE_LU_ID

        # Insert the three Angler Operations
        for x in ["A", "B", "C"]:

            try:
                sql = "INSERT INTO OPERATIONS(PARENT_OPERATION_ID, OPERATION_NUMBER, OPERATION_TYPE_LU_ID) VALUES(?, ?, ?);"
                params = [drop_op_id, x, angler_type_lu_id]
                angler_op_id = self._rpc.execute_query_get_id(sql=sql, params=params)
                results["Angler " + x] = angler_op_id

            except Exception as ex:

                if "apsw.ConstraintError" in str(ex):

                    logging.info(f"Angler operation {x} exists, getting the existing primary key: {ex}")
                    sql = """
                        SELECT OPERATION_ID FROM OPERATIONS 
                        WHERE PARENT_OPERATION_ID = ? AND OPERATION_NUMBER = ? AND OPERATION_TYPE_LU_ID = ?;
                    """
                    angler_op_id = self._rpc.execute_query(sql=sql, params=params)
                    if angler_op_id:
                        angler_op_id = angler_op_id[0][0]
                        results["Angler " + x] = angler_op_id

                else:

                    logging.error(f"Error reached: {ex}")
                    self._app.state_machine.anglerAOpId = None
                    self._app.state_machine.anglerBOpId = None
                    self._app.state_machine.anglerCOpId = None
                    message = f"Failed to insert or select angler {x}"
                    action = f"Please try again"
                    self.exception_encountered.emit(message, action)
                    return

            if x == "A":
                self._app.state_machine.anglerAOpId = angler_op_id
            elif x == "B":
                self._app.state_machine.anglerBOpId = angler_op_id
            elif x == "C":
                self._app.state_machine.anglerCOpId = angler_op_id

        # logging.info(f"newly inserted operations: {results}")

        return results

    @pyqtSlot(QVariant, str, str, str, str, QVariant, name="upsertOperationAttribute")
    def upsert_operation_attribute(self, operation_id: QVariant, lu_type: str, lu_value: str,
                                   value_type: str, value: str, indicator: QVariant=None):
        """
        Method to insert or update an operational attribute
        :param operation_id: the operation_id as an integer as found in OPERATIONS table
        :param lu_type: lookup type (from the LOOKUPS table)
        :param lu_value: lookup value (from the LOOKUPS table)
        :param value_type: alpha or numeric
        :param value: new value to insert or update
        :param indicator: string used to send in additional information about the attribute being upserted.  In particular,
                    this is used when a angler person is sent in when the start time has not been captured.  This
                    creates new Drop + Angler operation IDs.  In this case, the input operation_id is None, so we need
                    to know what to assign to operation_id, i.e. which angler or drop for that matter
        :return:
        """
        try:
            # If operation_id is NONE, that means that the operation has not been insert ye
            #  that is a problem

            logging.info(f"upsertOperationalAttribute, inputs: operation_id={operation_id}, lu_type={lu_type}, "
                         f"lu_value={lu_value}, value_type={value_type}, value={value}, indicator={indicator}")

            # Get the LOOKUP_ID for the OPERATION_ATTRIBUTE type
            sql = "SELECT LOOKUP_ID FROM LOOKUPS WHERE TYPE = ? AND VALUE = ?"
            params = [lu_type, lu_value]
            att_type_lu_id = self._rpc.execute_query(sql=sql, params=params)
            if att_type_lu_id:
                att_type_lu_id = att_type_lu_id[0][0]

                # operation_id is not an int, need to insert a new operation.  This occurs
                if not isinstance(operation_id, int):

                    # Insert the new Drop + Angler Operation IDs.  Note that calling this method
                    #  also updates the state_machine with the new Drop + Angler operation IDs
                    logging.info(f"operation_id={operation_id} > drop={self._app.state_machine.drop}")
                    new_ops = self.insert_operations(drop_number=self._app.state_machine.drop)
                    logging.info(f"New drop/angler operations inserted, new_operations={new_ops}")

                    # Emit the drop_dict to update the siteResults JSON back in the DropsScreen.qml
                    drop_dict = dict()
                    drop_key = f"Drop {self._app.state_machine.drop}"
                    drop_dict[drop_key] = {"id": new_ops[drop_key],
                                           "Anglers": {
                                               "Angler A": {"id": new_ops["Angler A"]},
                                               "Angler B": {"id": new_ops["Angler B"]},
                                               "Angler C": {"id": new_ops["Angler C"]}
                                           }}
                    self.new_drop_added.emit(drop_dict)

                    # Set the operation_id to the newly created ID, based on the provided indicator, where
                    # indicator = Angler A, Angler B, Angler C, or Drop #
                    if indicator in new_ops:
                        operation_id = new_ops[indicator]

                # Check if the OPERATION_ATTRIBUTE type already exists
                sql = "SELECT * FROM OPERATION_ATTRIBUTES WHERE OPERATION_ID = ? AND ATTRIBUTE_TYPE_LU_ID = ?;"
                params = [operation_id, att_type_lu_id]
                results = self._rpc.execute_query(sql=sql, params=params)
                value_type = "ATTRIBUTE_ALPHA" if value_type == "alpha" else "ATTRIBUTE_NUMERIC"
                if value_type == "ATTRIBUTE_NUMERIC":
                    value = float(value)

                if results:
                    # Update the OPERATION_ATTRIBUTES table
                    logging.info(f'update oa')
                    sql = "UPDATE OPERATION_ATTRIBUTES SET " + value_type + " = ? WHERE " + \
                            "OPERATION_ID = ? AND ATTRIBUTE_TYPE_LU_ID = ?;"
                    params = [value, operation_id, att_type_lu_id]
                else:
                    # Insert into OPERATION_ATTRIBUTES Table
                    logging.info(f'insert into oa')
                    sql = "INSERT INTO OPERATION_ATTRIBUTES(OPERATION_ID, " + value_type + \
                          ", ATTRIBUTE_TYPE_LU_ID) VALUES(?, ?, ?);"
                    params = [operation_id, value, att_type_lu_id]

                logging.info(f"sql={sql}\nparams={params}")

                results = self._rpc.execute_query(sql=sql, params=params)

        except Exception as ex:

            logging.error(f"Error upserting an operation attribute: {ex}")

    @pyqtSlot(str, name="selectOperationAttributes")
    def select_operation_attributes(self, set_id: str):
        """
        Method to retrieve all of the OPERATION_ATTRIBUTES entries for all of the drops and anglers for the given
        set_id.  This will need to recurse through each of the OPERATIONS set_id children and then get all of the
        associated OPERATION_ATTRIBUTES entries for those children
        :param set_id: str
        :return:
        """
        sql = """
            WITH RECURSIVE children(n) AS (
                SELECT OPERATION_ID FROM OPERATIONS WHERE OPERATION_NUMBER = ?
                UNION
                SELECT o.OPERATION_ID FROM OPERATIONS o, children
                    WHERE o.PARENT_OPERATION_ID = children.n
            )
            SELECT l.VALUE, OPERATION_ID, PARENT_OPERATION_ID, OPERATION_NUMBER FROM OPERATIONS o 
                INNER JOIN LOOKUPS l ON l.lookup_id = o.OPERATION_TYPE_LU_ID
            WHERE OPERATION_ID IN children 
                AND l.TYPE = 'Operation'       
        """
        # AND l.VALUE IN ['Drop', 'Angler']
        params = [set_id, ]

        try:
            ids = []
            results = self._rpc.execute_query(sql=sql, params=params)
            logging.info(f"results: {results}")
            if results:
                site = [x for x in results if x[0] == "Site"]
                drops = {"Drop " + x[3]: {"id": x[1], "Sinker Weight": None, "Recorder Name": None} for x in results if x[0] == "Drop"}
                ids = []
                for k, v in drops.items():
                    ids.append(v["id"])
                    ids.extend([x[1] for x in results if x[2] == v['id']])
                    anglers = {"Angler " + x[3]: {"id": x[1]} for x in results if x[2] == v["id"]}
                    v["Anglers"] = anglers

                # Query to get all OPERATION_ATTRIBUTES that match the ids (i.e. for all drops + anglers for this given site
                sql = """
                    SELECT o.PARENT_OPERATION_ID, oa.OPERATION_ID, l2.VALUE || " " || o.OPERATION_NUMBER, 
                        oa.ATTRIBUTE_ALPHA, l.TYPE, l.VALUE, oa.ATTRIBUTE_NUMERIC
                    FROM OPERATION_ATTRIBUTES oa
                    INNER JOIN LOOKUPS l ON oa.ATTRIBUTE_TYPE_LU_ID = l.LOOKUP_ID
                    INNER JOIN OPERATIONS o ON o.OPERATION_ID = oa.OPERATION_ID
                    INNER JOIN LOOKUPS l2 ON o.OPERATION_TYPE_LU_ID = l2.LOOKUP_ID
                    WHERE oa.OPERATION_ID IN
                """
                sql += " " + str(tuple(ids))
                oa_results = self._rpc.execute_query(sql=sql)
                if oa_results:
                    for op_att in oa_results:
                        drop_angler_item_list = [v["Anglers"] for k, v in drops.items() if v["id"] == op_att[0]]

                        # Drop Angler Items
                        if len(drop_angler_item_list) > 0:
                            drop_angler_item = drop_angler_item_list[0]
                            angler_item = {k: v for k, v in drop_angler_item.items() if v["id"] == op_att[1]}
                            key = op_att[4] + " " + op_att[5]
                            angler_item[list(angler_item.keys())[0]][key] = op_att[3]

                        # Drop Attributes
                        elif "Drop Attribute" in op_att[4]:
                            drop_item_list = [v for k, v in drops.items() if v["id"] == op_att[1]]
                            if len(drop_item_list) == 1:
                                item = drop_item_list[0]
                                if "Sinker Weight" in op_att[5]:
                                    item["Sinker Weight"] = op_att[6]
                                elif "Recorder Name"  in op_att[5]:
                                    item["Recorder Name"] = op_att[3]

                self.selection_result_obtained.emit(drops)
                logging.info(f"drops: {drops}")

                if "Drop 1" in drops:
                    self._app.state_machine.dropOpId = drops["Drop 1"]["id"]
                    self._app.state_machine.anglerAOpId = drops["Drop 1"]["Anglers"]["Angler A"]["id"]
                    self._app.state_machine.anglerBOpId = drops["Drop 1"]["Anglers"]["Angler B"]["id"]
                    self._app.state_machine.anglerCOpId = drops["Drop 1"]["Anglers"]["Angler C"]["id"]
                    logging.info(f"inside Drop 1, after setting state machine")


        except Exception as ex:

            logging.error(f"Exception querying operation_attributes: {ex}")

    @pyqtSlot(int, str, str, name="deleteOperationAttribute")
    def delete_operation_attribute(self, op_id: int, lu_type: str, lu_value: str):
        """
        Method to delete an individual operation_attributes record
        :param set_id:
        :return:
        """
        try:
            # Delete the record
            sql = """
                DELETE FROM OPERATION_ATTRIBUTES WHERE
                    OPERATION_ID = ? AND
                    ATTRIBUTE_TYPE_LU_ID = 
                        (SELECT LOOKUP_ID FROM LOOKUPS WHERE
                            TYPE = ? AND VALUE = ?);
            """
            params = [op_id, lu_type, lu_value]
            logging.info(f"Deleting parameters: {params}")
            self._rpc.execute_query(sql=sql, params=params)

            # Return dropTimeState to enter mode
            self._app.state_machine.dropTimeState = "enter"

            self.operationAttributeDeleted.emit()

        except Exception as ex:

            logging.error(f"Error deleting an operation_attribute record: {ex}")

    @pyqtSlot(str, name="playSound")
    def play_sound(self, sound_name):
        """
        Method to play a sound.  The sound_name will indicate the purpose of the sound.  Currently
        the only sound played is when the first Drop/Angler timer hits 4:45, and so has 15 seconds
        until it should start retrieving the hooks
        :param sound_name:
        :return:
        """
        logging.info(f"playing sound: {sound_name}")
        self._sound_player.play_sound(sound_name=sound_name)

    @pyqtSlot(str, name="getSoundPlaybackTime", result=QVariant)
    def get_sound_playback_time(self, begin_fishing_time):
        """
        Method to determine the time that is 4:45 (min:sec) past the begin_fishing_time, for when
        to play the sound warning the HookMatrix user to have the anglers start pulling in their lines
        :param begin_fishing_time:
        :return:
        """

        min_shift = 4
        sec_shift = 45

        try:
            if ":" in begin_fishing_time:
                min, sec = begin_fishing_time.split(":")
                min = int(min)
                sec = int(sec)
                logging.info(f"min={min}, sec={sec}")
                start_time = arrow.now().replace(tzinfo="US/Pacific").replace(minute=min, second=sec)
                end_time = start_time.shift(minutes=min_shift, seconds=sec_shift).format("mm:ss")
                logging.info(f"end time to play the sound: {end_time}")

                return end_time

        except Exception as ex:

            logging.error(f"Error getting the play sound time: {ex}")

        return "04:45"

    @staticmethod
    def abbreviate_gear_perfs(gear_list):
        """
        Map gear to abbrev. string
        :param gear_list: list of gear names
        :return: concat. string of abbreviations
        """
        if not gear_list:
            return "Gear\nPerf."

        gfMap = {
            "No Problems": "NP",
            "Lost Hooks": "LH",
            "Lost Gangion": "LG",
            "Minor Tangle": "MI",
            "Major Tangle": "MA",
            "Undeployed": "UN",
            "Exclude": "EX",
            "Lost Sinker": "LS"
        }
        lbl_str = ''
        for lbl in gear_list:
            lbl_str += gfMap[lbl] + ','

        if len(lbl_str) > 6:
            return "Gear\n" + lbl_str[0:5] + '...'
        elif len(lbl_str) > 0 and lbl_str[-1] == ",":
            return "Gear\n" + lbl_str[:-1]
        else:
            return "Gear\n" + lbl_str

    @pyqtSlot(int, str, name="selectAnglerGpLabels", result=QVariant)
    def select_angler_gp_labels(self, drop_op_id: int, angler: str):
        """
        Gets Gear perfs per operation_id / angler, then abbreviates for label
        :param drop_op_id: int; operations table id
        :param angler: str (e.g. "A")
        :return: emits drop#, angler letter, and Gear Perf label to DropAngler.qml updateGearPerformanceLabel
        """
        # query gets drop and angler info, and group_concats gear perfs
        perfs = self._rpc.execute_query(
            sql="""
            with drops as (
                select
                        operation_id as drop_id
                        ,operation_number as drop_number
                FROM    operations o
                JOIN    lookups l
                        on o.operation_type_lu_id = l.lookup_id
                WHERE   l.value = 'Drop'
                        and operation_id = ?
            )

            ,anglers as (
                select
                        operation_id as angler_id
                        ,parent_operation_id as parent_drop_id
                        ,operation_number as angler_letter
                FROM	operations o
                JOIN	lookups l
                        on o.operation_type_lu_id = l.lookup_id
                WHERE	l.value = 'Angler'
                        and o.operation_number = ?
            )

            select
                        d.drop_id
                        ,d.drop_number
                        ,a.angler_id
                        ,a.angler_letter
                        ,group_concat(l.value) as gear_perfs
            FROM		drops d
            JOIN		anglers a
                        on d.drop_id = a.parent_drop_id
            left JOIN   operation_attributes oa
                        on a.angler_id = oa.operation_id
            left JOIN	lookups l
                        on oa.attribute_type_lu_id = l.lookup_id
                        and l.type = 'Angler Gear Performance'
            group by    d.drop_id
                        ,d.drop_number
                        ,a.angler_id
                        ,a.angler_letter
                """,
            params=[drop_op_id, angler, ]
        )
        if perfs and perfs[0][4]:  # did query return results, and were there gear perfs?
            self.anglerGpLabelsSelected.emit(
                perfs[0][1],  # drop number
                perfs[0][3],  # angler letter
                self.abbreviate_gear_perfs(perfs[0][4].split(","))  # split comma sep string and abbreviate
            )

    def format_hooks_label(self, hooks_list):
        """
        format hooks text for RichText QML text object
        :param hooks_list: list of dicts (e.g. [{'hookNum': 1, 'hookContent': 'Yelloweye', 'contentType': 'Fish Hooked'}]
        :return: string, rich text
        """
        hooks_lbl = 'Hooks<br>'

        if not hooks_list:
            return hooks_lbl + "\n_,_,_,_,_"
        elif all(h['hookContent'] == 'Undeployed' for h in hooks_list):  # if all undeployed, set label to UN
            return hooks_lbl + 'UN'
        else:
            for hook in hooks_list:
                content = hook['contentType']
                hook_num = hook['hookNum']

                # label uses rich text to color diff chars differently
                if content == 'Fish Hooked':
                    hooks_lbl += f"<font color=\"#008000\">{hook_num},</font>"  # green
                elif content == 'Other':
                    hooks_lbl += f"<font color=\"#000000\">{hook_num},</font>"  # black
                elif not content:
                    hooks_lbl += f"<font color=\"#000000\">_,</font>"  # black
                else:
                    logging.error(f"Unexpected value {content} for hook {hook_num}")

        return hooks_lbl

    @pyqtSlot(int, str, name="selectAnglerHooksLabel", result=QVariant)
    def select_angler_hooks_label(self, drop_op_id: int, angler: str):
        """
        Select hooks per op_id aka angler from DB.
        Left join to CTE ensures result will always have 5 rows,
        unpopulated hooks shown as null
        :param drop_op_id: operation id specific to drop
        :param angler: str (e.g. 'A', 'B', or 'C')
        :return: dict[], one per db row. E.g. [{hookNum: "1", hookContent: "Boccacio", contentType: "Fish Hooked"}...]
        """
        hooks = self._rpc.execute_query(
            sql="""
             with hooks as (
                select
                            o1.operation_number as drop_num
                            ,o2.operation_number as angler_letter
                            ,o2.operation_id
                            ,h.hook_num
                FROM		operations o1
                JOIN		operations o2
                            on o1.operation_id = o2.parent_operation_id
                JOIN		(
                                select '1' as hook_num
                                union all
                                select '2'
                                union all
                                select '3'
                                union all
                                select '4'
                                union all
                                select '5'
                            ) h
                            on 1 = 1
                WHERE		o1.operation_id = ?
                            and o2.operation_number = ?
                )

            select
                        h.drop_num
                        ,h.angler_letter
                        ,h.hook_num
                        ,cc.display_name
                        ,case
                                    when cc.content_type_lu_id = 129 then 'Fish Hooked'
                                    when cc.content_type_lu_id = 130 then 'Other'
                                    else null
                        end as content_type
            from        hooks h
            left join	catch c
                        on h.operation_id = c.operation_id
                        and h.hook_num = c.receptacle_seq
            left join   catch_content_lu cc
                        on c.hm_catch_content_id = cc.catch_content_id
            left JOIN	lookups l
                        on c.receptacle_type_id = l.lookup_id
                        and l.value = 'Hook'
            order by    h.hook_num desc
            """,
            params=[drop_op_id, angler]
        )
        # if results, emit drop num, pass along angler letter, and hooks label str
        if hooks:
            hooks_list = [{'dropNum': h[0], 'hookNum': h[2], 'hookContent': h[3], 'contentType': h[4]} for h in hooks]
            self.anglerHooksLabelSelected.emit(
                hooks_list[0]['dropNum'],
                angler,
                self.format_hooks_label(hooks_list)
            )
