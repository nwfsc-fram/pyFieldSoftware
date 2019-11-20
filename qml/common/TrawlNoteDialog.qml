import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 580
    height: 500
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "Add Note"

    property int screen_id: -1
    property string message: ""
    property string action: ""
    property string accepted_action: ""
    property string screen: ""
    property bool validationNote: false

//    property string pkField: ""
    property var primaryKey: null
//    property var widget: null

    property alias btnHaulLevelValidationType: btnHaulLevelValidationType
    property alias btnDataType: btnDataType
    property alias btnSoftwareType: btnSoftwareType
    property alias taNote: taNote

    onRejected: {  }
    onAccepted: {
        notes.insertNote(taNote.text, btnHaulLevelValidationType.checked,
                btnDataType.checked, btnSoftwareType.checked, primaryKey)
    }

    function reset(screen_widget) {
        btnHaulLevelValidationType.checked = false
        btnDataType.checked = false
        btnSoftwareType.checked = false
        taNote.text = ""
        var pkField;
        var itemType;

        switch (stateMachine.screen) {
            case "home":
                pkField = "validationId"
                itemType = "validation"
                break;
            case "haulselection":
                pkField = "haulId"
                itemType = "haul"
                break;
            case "processcatch":
                pkField = "catchId"
                itemType = "selected species"
                if (!validationNote) {
                    if (screen_widget) {
                        if (screen_widget.model.rowCount(screen_widget.rootItem) > 0) {
                            if (screen_widget.selModel) {
                                var idx = screen_widget.selModel.currentIndex
                                var role = screen_widget.model.getRoleNumber("catchId")
                                primaryKey = tvSelectedSpecies.model.data(idx, role)
    //                        var item = screen_widget.model.getItem()
                            }
                        }
                    }
                } else {
//                    pkField = ""
                }
                break;
            case "weighbaskets":
                pkField = "catchId"
                itemType = "basket"
                break;
            case "fishsampling":
                pkField = "parentSpecimenId"
                itemType = "specimen"
                break;
            case "specialactions":
                pkField = "specimenId"
                itemType = "specimen"
                break;
            case "serialportmanager":
                pkField = "deployedEquipmentId"
                itemType = "equipment"
                break;
        }
        if (screen_widget) {
            if ((pkField != "") && (screen_widget.currentRow != -1) && (screen_widget.model.count > 0)) {
                primaryKey = screen_widget.model.get(screen_widget.currentRow)[pkField]
            }
        }
        if ((stateMachine.screen != "home") && (primaryKey == null) && (!validationNote))
            taNote.text = "Please select the " + itemType + " of interest " +
                            "(if applicable) " +
                            "to get the database primary key." +
                            "\n\nThis allows the data team to do faster/better data processing at the end " +
                            "of the season."

        validationNote = false
    }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        GridLayout {
            id: gridHeader
            columns: 4
            x: 20
            y: 20
            columnSpacing: 20
            Label {
                id: lblHaulID
                text: qsTr("Haul ID")
                font.pixelSize: 18
            }
            Label {
                id: lblDateTime
                text: qsTr("Date Time")
                font.pixelSize: 18
            }
            Label {
                id: lblScreen
                text: qsTr("Screen")
                font.pixelSize: 18
            }
            Label {
                id: lblPrimaryKey
                text: qsTr("DB Key")
                font.pixelSize: 18
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfHaulId
                text: stateMachine.haul["haul_number"].substr(stateMachine.haul["haul_number"].length - 3)
                font.pixelSize: 18
                readOnly: true
    //            Layout.maximumWidth: 250
                Layout.preferredWidth: 80
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfDateTime
                text: new Date().toLocaleTimeString()
                font.pixelSize: 18
                readOnly: true
                Layout.preferredWidth: 120
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfScreen
                text: stateMachine.screen
                font.pixelSize: 18
                readOnly: true
                Layout.preferredWidth: 160
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfPrimaryKey
                text: primaryKey ? primaryKey : ""
                font.pixelSize: 18
                readOnly: true
                Layout.preferredWidth: 100
            }
        } // gridHeader

        TextArea {
            id: taNote
            anchors.top: gridHeader.bottom
            anchors.topMargin: 20
            anchors.left: gridHeader.left
            text: qsTr("")
            font.pixelSize: 20
            implicitWidth: dlg.width - colTypes.width - 60
            implicitHeight: dlg.height - gridHeader.height -  rwlButtons.height - 80
            MouseArea {
                anchors.fill: parent
                onEntered: {
                    parent.forceActiveFocus()
                    parent.selectAll()
                }
            }
        }
        ColumnLayout {
            id: colTypes
            spacing: 20
            anchors.left: taNote.right
            anchors.leftMargin: 20
            anchors.verticalCenter: taNote.verticalCenter
            Label {
                id: lblTypes
                text: "Note Type"
                font.pixelSize: 20
            }
            TrawlBackdeckButton {
                id: btnHaulLevelValidationType
                text: "Haul-Level\nValidation"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                checkable: true
                checked: false
            }
            TrawlBackdeckButton {
                id: btnDataType
                text: "Data Issue"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                checkable: true
                checked: false
            }
            TrawlBackdeckButton {
                id: btnSoftwareType
                text: "Software\nIssue"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                checkable: true
                checked: false
            }
        }
        RowLayout {
            id: rwlButtons
            anchors.horizontalCenter: parent.horizontalCenter
            y: dlg.height - this.height - 20
            spacing: 20
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

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()

        states: [
            State {
                name: "original"
                PropertyChanges { target: taNote; text: ""}
                PropertyChanges { target: btnHaulLevelValidationType; checked: false}
                PropertyChanges { target: btnDataType; checked: false}
                PropertyChanges { target: btnSoftwareType; checked: false}
                PropertyChanges { target: primaryKey; value: ""}


//                PropertyChanges { target: taNote;
//                                    implicitWidth: dlg.width - colTypes.width - 60;
//                                    implicitHeight: dlg.height - rwlButtons.height - 60}
//                PropertyChanges { target: colTypes; enabled: false; visible: false}
            }, // general
            State {
                name: "haulLevelValidation"
                PropertyChanges { target: btnHaulLevelValidationType; checked: true}
//                PropertyChanges { target: taNote; implicitWidth: dlg.width - 40; implicitHeight: dlg.height - rwlButtons.height - 60}
//                PropertyChanges { target: colTypes; enabled: false; visible: false}
            } // haulLevelValidation
        ]

    }
}
