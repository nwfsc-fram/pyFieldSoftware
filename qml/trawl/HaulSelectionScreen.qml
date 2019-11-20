import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0

import "../common"

Item {

//    signal haulSelected()
//    onHaulSelected: {

    Component.onDestruction: {
        tbdSM.to_home_state()
    }

    function deleteHaul(index) {

        if ((tvHauls.model.count > 0) && (index != -1)) {
            // Delete only the given row defined by the index
//            if ((tvHauls.model.count > 0) && (tvHauls.currentRow != -1)) {
//                tvHauls.selection.forEach(
//                    function(rowIndex) {
            if (tvHauls.model.get(index).haulNumber.indexOf('t') != -1) {
                var is_data = tvHauls.model.check_haul_for_data(index);

                if (is_data) {
                    // Data Exists - Dialog box to the user to confirm that he/she wants to delete the data
                    dlgConfirm.title = "Delete Test Haul"
                    dlgConfirm.message = "Catch and/or specimen data exists for this haul."
                    dlgConfirm.action = "Are you sure that you want to delete it?"
                    dlgConfirm.accepted_action = "delete test haul"
                    dlgConfirm.open()

                } else {
//                    var haulId = tvHauls.model.get(index).haulId
                    haulSelection.HaulsModel.delete_test_haul(index)

                }
            }
//                    }
//                )
//            }
        }
    }

    function haulSelected() {
        var row = tvHauls.currentRow;
        if (row != -1) {
            var item = tvHauls.model.get(row);
            if (item["status"] == "Completed") {
                dlgConfirm.title = "Confirm Haul Selection"
                dlgConfirm.message = "This haul has already been completed"
                dlgConfirm.action = "Are you sure that you want to select it?"
                dlgConfirm.accepted_action = "set haul processing status"
                dlgConfirm.open()

            } else {

                var currentId = stateMachine.haul["haul_id"]
                var haulId = tvHauls.model.get(row).haulId
                haulSelection.HaulsModel.set_haul_processing_status(currentId, haulId, "Selected")

//                tbdSM.haul_selection_state.selectHaul(haulId)       // Function

//                tvHauls.selection.forEach(
//                    function(rowIndex) {
//                        var haulId = tvHauls.model.get(rowIndex).haulId
//                        tbdSM.haul_selection_state.selectHaul(haulId)       // Function
//                    }
//                )

            }
        }
    }

    TrawlBackdeckTableView {
        id: tvHauls
//        anchors.horizontalCenter: parent.horizontalCenter
        x: 40
        y: 20
        width: 750
        height: main.height - rwlActionButtons.height - 60
        selectionMode: SelectionMode.SingleSelection
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

        model: haulSelection.HaulsModel

        onDoubleClicked: {

            haulSelected()

//            tvHauls.selection.forEach(
//                function(rowIndex) {
//                    var haulId = tvHauls.model.get(rowIndex).haulId
//                    tbdSM.haul_selection_state.selectHaul(haulId)
//                }
//            )

        }

        onClicked: {
            this.selection.forEach(
                function(rowIndex) {
                   if ((tvHauls.model.get(rowIndex).status == "Active") ||
                        (tvHauls.model.get(rowIndex).status == "Completed"))
                        btnSelectHaul.state = qsTr("enabled")
                    else
                        btnSelectHaul.state = qsTr("disabled")
                }
            )
        }

        TableViewColumn {
            role: "status"
            title: "Status"
            width: 120
        } // status
        TableViewColumn {
            role: "haulNumber"
            title: "Haul ID"
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
    } // tvHauls

    ColumnLayout {
        id: cllActions
        x: tvHauls.x + tvHauls.width + 40
        y: tvHauls.y
//        y: main.height/4 - this.height/2
        spacing: 10
        TrawlBackdeckButton {
            id: btnGetHauls
            text: qsTr("Get Real\nHauls")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
//                haulSelection._get_hauls_from_db()
                haulSelection._get_hauls_from_wheelhouse()
            }
        } // btnGetHauls
        Label {
            font.pixelSize: 12
        }
        Label {
            text: "Real Hauls Filter"
            font.pixelSize: 20
            Layout.preferredWidth: btnAddTestHaul.width
            horizontalAlignment:  Text.AlignHCenter
        } // Hauls Filter
        ExclusiveGroup {
            id: egHauls
        }
        TrawlBackdeckButton {
            id: btnTodaysHauls
            text: qsTr("Today")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            checked: true
            exclusiveGroup: egHauls
            onClicked: {
                haulSelection._get_hauls_from_db("today")
            }
        } // btnTodaysHauls
        TrawlBackdeckButton {
            id: btnLastTwoDaysHauls
            text: qsTr("Today +\nYesterday")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            exclusiveGroup: egHauls
            onClicked: {
                haulSelection._get_hauls_from_db("two days")

            }
        } // btnLastTwoDaysHauls
        TrawlBackdeckButton {
            id: btnAllHauls
            text: qsTr("All")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            exclusiveGroup: egHauls
            onClicked: {
                haulSelection._get_hauls_from_db("all")
            }
        } // btnAllHauls

        Label {
            font.pixelSize: 12
        }
        Label {
            text: qsTr("Test Hauls")
            font.pixelSize: 20
            Layout.preferredWidth: btnAddTestHaul.width
            horizontalAlignment:  Text.AlignHCenter
        } //  Test Hauls Label
        TrawlBackdeckButton {
            id: btnAddTestHaul
            text: qsTr("Add Test")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
                haulSelection.HaulsModel.add_test_haul()
            }
            function addZero(i) {
                if (i < 10) {
                    i = "0" + i;
                }
                return i;
            }
        } // btnAddTestHaul
        TrawlBackdeckButton {
            id: btnDeleteTestHaul
            text: qsTr("Delete\nTest")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
                var index = tvHauls.currentRow;
                if (index != -1)
                    deleteHaul(index);

//                if ((tvHauls.model.count > 0) && (tvHauls.currentRow != -1)) {
//                    tvHauls.selection.forEach(
//                        function(rowIndex) {
//                            if (tvHauls.model.get(rowIndex).haulNumber.indexOf('t') != -1) {
//                                var haulId = tvHauls.model.get(rowIndex).haulId
//                                haulSelection.HaulsModel.delete_test_haul(haulId, rowIndex)
//                            }
//                        }
//                    )
//                }
            }
        } // btnDeleteTestHaul
//        TrawlBackdeckButton {
//            id: btnDeleteAllTestHauls
//            text: qsTr("Delete\nAll Tests")
//            Layout.preferredWidth: this.width
//            Layout.preferredHeight: this.height
//            onClicked: {
//                var idx = []
//                var reverseIdx = []
//                for (var i=0; i < tvHauls.model.count; i++) {
//                    if (tvHauls.model.get(i).haulNumber.indexOf('t') != -1)
//                        idx.push(i)
//                }
//                reverseIdx = idx.slice()
//                reverseIdx.sort(function(a, b) {return b-a})
//                for (var i = 0; i < reverseIdx.length; i++) {
//                    var row_num = reverseIdx[i]
//                    var haul_id = tvHauls.model.get(row_num).haulId
//                    haulSelection.HaulsModel.delete_test_haul(haul_id, row_num)
//                }
//            }
//        } // betDeleteAllTestHauls
    } // cllActions

    RowLayout {
        id: rwlActionButtons
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        TrawlBackdeckButton {
            id: btnSelectHaul
            text: qsTr("Select\nHaul")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            state: qsTr("disabled")
            onClicked: {
                haulSelected()
            }
        } // btnSelectHaul
        TrawlBackdeckButton {
            id: btnNotes
            text: qsTr("Note")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: 60
            onClicked: {
                dlgNote.reset(tvHauls)
                dlgNote.open()
            }
        } // btnNotes
        TrawlBackdeckButton {
            id: btnBack
            text: qsTr("<<")
            Layout.preferredWidth: 60
            Layout.preferredHeight: this.height
            onClicked: screens.pop()
        } // btnBack
    }

    TrawlNoteDialog { id: dlgNote }

    TrawlConfirmDialog {
        id: dlgConfirm
//        title: "Confirm Haul Selection"
//        message: "This haul has already been completed"
//        action: "Are you sure that you want to select it?"
        onAccepted: {

            switch (accepted_action) {
                case "set haul processing status":
                    var row = tvHauls.currentRow
                    if (row != -1) {
                        var currentId = stateMachine.haul["haul_id"]
                        var haulId = tvHauls.model.get(row).haulId
                        haulSelection.HaulsModel.set_haul_processing_status(currentId, haulId, "Selected")
                    }
                    break;

                case "delete test haul":
                    var index = tvHauls.currentRow;
                    if (index != -1) {
//                        var haulId = tvHauls.model.get(index).haulId
                        haulSelection.HaulsModel.delete_test_haul(index)
                    }
                    break;

            }
        }
    }
}