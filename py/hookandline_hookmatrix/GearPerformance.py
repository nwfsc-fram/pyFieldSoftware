# Standard Python Libraries
import logging

# Third Party Libraries
from PyQt5.QtCore import QVariant, pyqtSlot, pyqtSignal, QObject


class GearPerformance(QObject):

    gearPerformanceSelected = pyqtSignal(QVariant, arguments=["results", ])
    gearPerformanceChanged = pyqtSignal(QVariant, arguments=['angler_op_id'])
    hooksUndeployed = pyqtSignal(QVariant, arguments=['angler_op_id'])

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db
        self._rpc = self._app.rpc

    @pyqtSlot(name="getAnglerOpId", result=QVariant)  # 143: expose as pyqtSlot
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
        return op_id

    @pyqtSlot(str, name="addGearPerformance")
    def add_gear_performance(self, gear_performance: str):
        """
        #239: Revamp of gp button relationships.  Removing delete all when "No Problems" selected
        Upsert gear performance record for existing operation id
        :param gear_performance: str (select value from  lookups where type = 'Angler Gear Performance')
        :return: None (inserts to db, emits for GP Label update (DropAngler.qml)
        """
        op_id = self.get_angler_op_id()
        try:
            self._app.drops.upsert_operation_attribute(
                operation_id=op_id,
                lu_type="Angler Gear Performance",
                lu_value=gear_performance,
                value_type="alpha",
                value=None,
                indicator=None
            )
            logging.debug(f"Upserting gear performance {gear_performance} with operation_id {op_id}")
            self.gearPerformanceChanged.emit(op_id)
        except Exception as ex:
            logging.error(f"Error adding the no problems gear performances: {ex}")

    @pyqtSlot(str, name="deleteGearPerformance")
    def delete_gear_performance(self, gear_performance: str):
        """
        Method to delete a gear performance issue for the angler operation ID from OPERATION_ATTRIBUTES
        :param gear_performance: str (select value from  lookups where type = 'Angler Gear Performance')
        :return: None (inserts to db, emits for GP Label update (DropAngler.qml)
        """
        op_id = self.get_angler_op_id()
        try:
            sql = """
                DELETE FROM OPERATION_ATTRIBUTES WHERE OPERATION_ID = ? AND ATTRIBUTE_TYPE_LU_ID IN
                    (SELECT LOOKUP_ID FROM LOOKUPS WHERE TYPE = 'Angler Gear Performance' AND
                                                         VALUE = ?);
            """
            params = [op_id, gear_performance]
            self._rpc.execute_query(sql=sql, params=params)
            self.gearPerformanceChanged.emit(op_id)
        except Exception as ex:
            logging.error(f"Error deleting the gear performance: {ex}")

    @pyqtSlot(name="selectGearPerformance", result=QVariant)
    def select_gear_performance(self):
        """
        Method to retrieve the gear performance when the GearPerformanceScreen is made visible
        :return:
        """
        op_id = self.get_angler_op_id()
        sql = """
            SELECT l.VALUE FROM LOOKUPS l
                INNER JOIN OPERATION_ATTRIBUTES oa ON oa.ATTRIBUTE_TYPE_LU_ID = l.LOOKUP_ID
                WHERE oa.OPERATION_ID = ? AND l.TYPE = 'Angler Gear Performance';
        """
        params = [op_id, ]
        results = self._rpc.execute_query(sql=sql, params=params)
        # logging.info(f'getting gear, params: {params} > results: {results}')
        if results:
            results = [x[0] for x in results]
        self.gearPerformanceSelected.emit(results)

        return results

    @staticmethod
    def abbreviate_gear_perfs(gear_list):
        """
        Map gear to abbrev. string and abbreviate to format for Drops label
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

    @pyqtSlot(name="upsertHooksToUndeployed")
    def upsert_hooks_to_undeployed(self):
        """
        Loop through 1-5 and query hook records for current angler for that iteration
        Record found --> update catch to Undeployed
        Record not found --> insert catch with angler_op_id, hook_number, and undeployed
        :return: None (emit op_id to DropAngler.qml for updating hooks label on Drops screen)
        """
        op_id = self.get_angler_op_id()
        for hook_num in range(1, 6):
            hook_records = self._rpc.execute_query(
                sql='''
                    select  c.catch_id
                    from    catch c
                    join    lookups l
                            on c.receptacle_type_id = l.lookup_id
                    where   c.operation_id = ?
                            and l.type = 'Receptacle Type'
                            and l.value = 'Hook'
                            and c.receptacle_seq = ?
                ''',
                params=[op_id, hook_num]
            )
            if len(hook_records) > 1:
                logging.error(f"Multiple records returned for angler op id {op_id} hook {hook_num}")
                continue
            elif len(hook_records) == 1:
                self._rpc.execute_query(
                    sql="""
                        update  catch
                        set     hm_catch_content_id = (
                                    select  catch_content_id 
                                    from    catch_content_lu 
                                    where   display_name = 'Undeployed'
                                )
                        where   catch_id = ?
                        """,
                    params=[hook_records[0][0], ]
                )
                logging.info(f"Angler op id {op_id} hook {hook_num} updated to 'Undeployed'")
            else:
                self._rpc.execute_query(
                    sql="""
                        insert into catch (
                            operation_id
                            ,hm_catch_content_id
                            ,receptacle_type_id
                            ,receptacle_seq
                        )
                        values (
                            ?
                            ,(select catch_content_id from catch_content_lu where display_name = 'Undeployed')
                            ,(select lookup_id from lookups where value = 'Hook' and type = 'Receptacle Type')
                            ,?
                        )
                    """,
                    params=[op_id, hook_num]
                )
                logging.info(f"Undeployed hook {hook_num} for angler op id {op_id} inserted.")
        self.hooksUndeployed.emit(op_id)
