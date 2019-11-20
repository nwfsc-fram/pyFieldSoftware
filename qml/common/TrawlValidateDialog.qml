import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 760
    height: 700
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "Haul-Level Validation Checks"
//    title: customizeTitle.checked ? windowTitleField.text : "Customized content"

    property alias btnOkay: btnOkay
    property string measurement: "Length"
    property real value: 20.0
    property string unit_of_measurement: "cm"
    property string errors: "1.  Bogus length value (a test)"
    property string action: "Do you want to keep this value?"

    onRejected: {  }
    onAccepted: {

        if (stateMachine.screen == "home"){

            // TODO Todd Hay - Fix for when the selected haul is not in Today's haul, yet
            // only Today's hauls are being shown
            var model = haulSelection.HaulsModel;
            var index = model.get_item_index("status", "Selected")
    //        console.info('selected index: ' + index)
            if (index != -1) {
                // If a row is selected and the user is on the home screen, set the haul to Completed
                var currentId = stateMachine.haul["haul_id"]
                var haulId = model.get(index).haulId
                model.set_haul_processing_status(currentId, haulId, "Completed")
            }

            // Push trawl_backdeck.db to wheelhouse PyCollector\data folder, with date-time stamp
            qaqc.backup_files()

        }
    }

    Connections {
        target: tvValidations.selection
        onSelectionChanged: selectionChanged()
    } // selectionChanged()

    function selectionChanged() {
        if (tvValidations.currentRow != -1) {
            btnNote.state = qsTr("enabled")
            var item = tvValidations.model.get(tvValidations.currentRow);
            taDescription.text = item["description"]
            taErrors.text = item["errors"] ? item["errors"] : "Description of any errors that were encountered"
        } else {
            btnNote.state = qsTr("disabled")
            taDescription.text = ""
            taErrors.text = ""
        }
    }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        RowLayout {
            id: rwlHeader
            x: 20
            y: 20
            spacing: 20
            Label {
                id: lblHaul
                text: "Haul ID"
                font.pixelSize: 24
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfHaul
                font.pixelSize: 24
                text: stateMachine.haul["haul_number"]
                Layout.preferredWidth: 220
                Layout.preferredHeight: this.height
            }
        } // rwlHeader
        TrawlBackdeckButton {
            id: btnRun
            text: "Run Checks"
//            anchors.right: dlg.width
//            anchors.rightMargin: 20
            x: dlg.width - this.width-10
            y: 10
            onClicked: {
                var row = tvValidations.currentRow;
                var index;
                var item;
                var results = qaqc.runHaulLevelValidations()
                var name
                if (results) {
                    for (var i=0; i<results.length; i++) {
                        name = results[i]["name"]
                        index = tvValidations.model.get_item_index("name", name)
                        item = tvValidations.model.get(index)
                        tvValidations.model.setProperty(index, "status", results[i]["status"])
                        tvValidations.model.setProperty(index, "errors", results[i]["errors"])
                        tvValidations.model.setProperty(index, "errorCount", results[i]["errorCount"])
                    }
                }
                if (row == -1)
                    tvValidations.selection.clear()
                else
                    tvValidations.selection.select(row)
            }
        }

        TrawlBackdeckTableView {
            id: tvValidations
            x: rwlHeader.x
            anchors.top: rwlHeader.bottom
            anchors.topMargin: 20

//            x: rwlHeader.x
//            y: rwlHeader.y + rwlHeader.height + 30
//            width: 700
            width: dlg.width - 40
//            height: main.height - rwlHeader.height - 130
            height: 220
            selectionMode: SelectionMode.SingleSelection
            headerVisible: true
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
            model: qaqc.ValidationModel

            TableViewColumn {
                role: "name"
                title: "Validation"
                width: 368
            }
//            TableViewColumn {
//                role: "description"
//                title: "Description"
//                width: 200
//            }
            TableViewColumn {
                role: "status"
                title: "Status"
                width: 100
            }
            TableViewColumn {
                role: "errorCount"
                title: "# Errors"
                width: 100
            }
            TableViewColumn {
                role: "noteAdded"
                title: "Noted?"
                width: 150
            }
        } // tvValidations
        RowLayout {
            id: rwlDescription
//            anchors.horizontalCenter: dlg.horizontalCenter
//            y: tvValidations.y + tvValidations.height + 20
            x: rwlHeader.x
            anchors.top: tvValidations.bottom
            anchors.topMargin: 20
            spacing: 20
            Label {
                id: lblDescription
                text: qsTr("Description")
                verticalAlignment: Text.AlignTop
                font.pixelSize: 20
            }
            TextArea {
                id: taDescription
                text: qsTr("Description of the validation test")
                font.pixelSize: 20
                implicitWidth: dlg.width - lblDescription.width - 60
                implicitHeight: 60
                readOnly: true
            }
        }
        RowLayout {
            id: rwlErrors
//            anchors.horizontalCenter: dlg.horizontalCenter
//            y: tvValidations.y + tvValidations.height + 20
            x: rwlHeader.x
            anchors.top: rwlDescription.bottom
            anchors.topMargin: 20
            spacing: 20
            Label {
                id: lblErrors
                text: qsTr("Errors")
                verticalAlignment: Text.AlignTop
                font.pixelSize: 20
//                Layout.preferredWidth: 80
            }
            TextArea {
                id: taErrors
                text: qsTr("Description of any errors that were encountered")
                font.pixelSize: 20
                implicitWidth: dlg.width - cllButtons.width - lblErrors.width - 80
                implicitHeight: 290
                readOnly: true
            }
        }
        TrawlBackdeckButton {
            id: btnNote
            text: "Note"
            anchors.left: rwlErrors.right
            anchors.leftMargin: 20
            anchors.top: rwlErrors.top
            state: qsTr("disabled")
            onClicked: {
                var row = tvValidations.currentRow;
                if (row != -1) {
                    var item = tvValidations.model.get(row)
                    dlgNote.validationNote = true;
                    dlgNote.reset(tvValidations)
                    dlgNote.btnHaulLevelValidationType.checked = true
//                        dlgNote.taNote.text = item["name"] + "\n\n"
                    dlgNote.open()

                }
            }
        } // btnNote


        ColumnLayout {
            id: cllButtons
//            anchors.horizontalCenter: parent.horizontalCenter
//            y: dlg.height - this.height - 20
//            anchors.right: parent.width
//            anchors.rightMargin: 20
//            anchors.bottom: parent.height
            x: dlg.width - this.width - 20
            y: dlg.height - this.height - 20
            spacing: 10
            TrawlBackdeckButton {
                id: btnOkay
                text: "Okay"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.accept() }
            } // btnOkay
            TrawlBackdeckButton {
                id: btnCancel
                text: "Cancel"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.reject() }
            } // btnCancel
        } // rwlButtons

        TrawlNoteDialog {
            id: dlgNote
        }

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
}
