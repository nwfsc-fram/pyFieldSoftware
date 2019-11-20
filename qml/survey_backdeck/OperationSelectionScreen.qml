import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0

import "../common"

Item {

    Component.onDestruction: {
        tbdSM.to_home_state()
    }

    function addOperation() {
        // Method to add a test operation
        var item = {"status": "active", "siteId": "test12345", "date": "today", "startTime": "13:33", "endTime": "14:23"}
    }

    function deleteOperation(index) {

        if ((tvOperations.model.count > 0) && (index != -1)) {
            // Delete only the given row defined by the index

            if (tvOperations.model.get(index).haulNumber.indexOf('t') != -1) {
                var is_data = tvOperations.model.check_operation_for_data(index);

                if (is_data) {
                    // Data Exists - Dialog box to the user to confirm that he/she wants to delete the data
                    dlgConfirm.title = "Delete Test Haul"
                    dlgConfirm.message = "Catch and/or specimen data exists for this haul."
                    dlgConfirm.action = "Are you sure that you want to delete it?"
                    dlgConfirm.accepted_action = "delete test haul"
                    dlgConfirm.open()

                } else {
//                    var haulId = tvOperations.model.get(index).haulId
                    operationSelection.OperationsModel.delete_test_operation(index)

                }
            }
//                    }
//                )
//            }
        }
    }

    function operationSelected() {
        var row = tvOperations.currentRow;
        if (row != -1) {
            var item = tvOperations.model.get(row);
            if (item["status"] == "Completed") {
                dlgConfirm.title = "Confirm Haul Selection"
                dlgConfirm.message = "This haul has already been completed"
                dlgConfirm.action = "Are you sure that you want to select it?"
                dlgConfirm.accepted_action = "set haul processing status"
                dlgConfirm.open()

            } else {

                var currentId = stateMachine.haul["haul_id"]
                var haulId = tvOperations.model.get(row).haulId
                operationSelection.OperationsModel.set_operation_processing_status(currentId, haulId, "Selected")

            }
        }
    }

    TrawlBackdeckTableView {
        id: tvOperations
//        anchors.horizontalCenter: parent.horizontalCenter
        x: 40
        y: 20
        width: 750
        height: main.height - rwlActionButtons.height - 60
        selectionMode: SelectionMode.SingleSelection
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

        model: operationSelection.OperationsModel

        onDoubleClicked: {

            operationSelected()

        }

        onClicked: {
            this.selection.forEach(
                function(rowIndex) {
                   if ((tvOperations.model.get(rowIndex).status == "Active") ||
                        (tvOperations.model.get(rowIndex).status == "Completed"))
                        btnSelectOperation.state = qsTr("enabled")
                    else
                        btnSelectOperation.state = qsTr("disabled")
                }
            )
        }

        TableViewColumn {
            role: "status"
            title: "Status"
            width: 120
        } // status
        TableViewColumn {
            role: "operationId"
            title: "Site ID"
            width: 200
        } // haulNumber
        TableViewColumn {
            role: "date"
            title: "Date"
            width: 150
        } // date
        TableViewColumn {
            role: "startTime"
            title: "Start Time"
            width: 140
        } // startTime
        TableViewColumn {
            role: "endTime"
            title: "End Time"
            width: 140
        } // endTime
    } // tvOperations

    ColumnLayout {
        id: cllActions
        y: tvOperations.y
        anchors.right:  parent.right
        anchors.rightMargin: 40

        spacing: 10
        BackdeckButton {
            id: btnGetOperations
            text: qsTr("Get Sites")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
                operationSelection._get_operations_from_wheelhouse()
            }
        } // btnGetOperations
        Label {
            font.pixelSize: 12
        }
        Label {
            text: "Sites Filter"
            font.pixelSize: 20
            Layout.preferredWidth: btnGetOperations.width
            horizontalAlignment:  Text.AlignHCenter
        } // Operations Filter
        ExclusiveGroup {
            id: egOperations
        }
        BackdeckButton {
            id: btnTodaysOperations
            text: qsTr("Today")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            checked: true
            exclusiveGroup: egOperations
            onClicked: {
                operationSelection._get_operations_from_db("today")
            }
        } // btnTodaysOperations
        BackdeckButton {
            id: btnLastTwoDaysOperations
            text: qsTr("Today +\nYesterday")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            exclusiveGroup: egOperations
            onClicked: {
                operationSelection._get_operations_from_db("two days")

            }
        } // btnLastTwoDaysOperations
        BackdeckButton {
            id: btnAllOperations
            text: qsTr("All")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            exclusiveGroup: egOperations
            onClicked: {
                operationSelection._get_operations_from_db("all")
            }
        } // btnAllOperations

        Label {
            font.pixelSize: 12
        }
        Label {
            text: qsTr("Test Site")
            font.pixelSize: 20
            Layout.preferredWidth: btnGetOperations.width
            horizontalAlignment:  Text.AlignHCenter
        } //  Test Operations Label
        BackdeckButton {
            id: btnAddTestOperation
            text: qsTr("Add Test")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
                operationSelection.OperationsModel.add_test_operation()
            }
            function addZero(i) {
                if (i < 10) {
                    i = "0" + i;
                }
                return i;
            }
        } // btnAddTestOperation
        BackdeckButton {
            id: btnDeleteTestOperation
            text: qsTr("Delete\nTest")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
                var index = tvOperations.currentRow;
                if (index != -1)
                    deleteOperation(index);

            }
        } // btnDeleteTestOperation
    } // cllActions

    RowLayout {
        id: rwlActionButtons
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        BackdeckButton {
            id: btnSelectOperation
            text: qsTr("Select\nOperation")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            state: qsTr("disabled")
            onClicked: {
                operationSelected()
            }
        } // btnSelectOperation
        BackdeckButton {
            id: btnNotes
            text: qsTr("Note")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: 60
            onClicked: {
                dlgNote.reset(tvOperations)
                dlgNote.open()
            }
        } // btnNotes
        BackdeckButton {
            id: btnBack
            text: qsTr("<<")
            Layout.preferredWidth: 60
            Layout.preferredHeight: this.height
            onClicked: screens.pop()
        } // btnBack
    }

    NoteDialog { id: dlgNote }

    OkayDialog {
        id: dlgConfirm
        onAccepted: {

            switch (accepted_action) {
                case "set haul processing status":
                    var row = tvOperations.currentRow
                    if (row != -1) {
                        var currentId = stateMachine.haul["haul_id"]
                        var haulId = tvOperations.model.get(row).haulId
                        haulSelection.HaulsModel.set_haul_processing_status(currentId, haulId, "Selected")
                    }
                    break;

                case "delete test haul":
                    var index = tvOperations.currentRow;
                    if (index != -1) {
//                        var haulId = tvOperations.model.get(index).haulId
                        haulSelection.HaulsModel.delete_test_haul(index)
                    }
                    break;

            }
        }
    }
}