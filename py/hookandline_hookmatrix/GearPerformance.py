# Standard Python Libraries
import logging

# Third Party Libraries
from PyQt5.QtCore import QVariant, pyqtSlot, pyqtSignal, QObject


class GearPerformance(QObject):

    gearPerformanceSelected = pyqtSignal(QVariant, arguments=["results", ])

    def __init__(self, app=None, db=None):
        super().__init__()
        self._app = app
        self._db = db
        self._rpc = self._app.rpc

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
        Method to add a gear performance problem
        :param problem:
        :return:
        """
        op_id = self.get_angler_op_id()

        # Delete the existing No Problems gear performance
        try:
            if gear_performance == "No Problems":
                sql = """
                    DELETE FROM OPERATION_ATTRIBUTES WHERE OPERATION_ID = ? AND ATTRIBUTE_TYPE_LU_ID IN
                        (SELECT LOOKUP_ID FROM LOOKUPS WHERE TYPE = 'Angler Gear Performance');
                """
            else:
                sql = """
                    DELETE FROM OPERATION_ATTRIBUTES WHERE OPERATION_ID = ? AND ATTRIBUTE_TYPE_LU_ID IN
                        (SELECT LOOKUP_ID FROM LOOKUPS WHERE TYPE = 'Angler Gear Performance' AND
                                                             VALUE = 'No Problems');
                """
            params = [op_id, ]
            self._rpc.execute_query(sql=sql, params=params)

        except Exception as ex:

            logging.error(f"Error deleting the gear performances: {ex}")

        try:
            self._app.drops.upsert_operation_attribute(operation_id=op_id, lu_type="Angler Gear Performance",
                                                     lu_value=gear_performance, value_type="alpha",
                                                       value=None, indicator=None)

        except Exception as ex:
            logging.error(f"Error adding the no problems gear performances: {ex}")

    @pyqtSlot(str, name="deleteGearPerformance")
    def delete_gear_performance(self, gear_performance: str):
        """
        Method to delete a gear performance issue for the angler operation ID from OPERATION_ATTRIBUTES
        :param gear_performance:
        :param str:
        :return:
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
