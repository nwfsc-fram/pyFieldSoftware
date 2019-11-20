import QtQuick 2.5
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0

import "../common"

Item {
//    id: homeScreen

//    Connections {
//        target: stateMachine
//        onHaulSelected: {
//            updateHaulDetails()
//        }
//    }

    Component.onCompleted: {
//        if (tbdSM.is_haul_selected)
//            btnProcessCatch.state = qsTr("enabled")
//        else
//            btnProcessCatch.state = qsTr("disabled")

        main.title = qsTr("ASHOP - Home");
//        updateHaulDetails()
    }

//    Connections {
//        target: qaqc
//        onBackupStatusChanged: showBackupStatusDialog(success, msg)
//    }

    function showBackupStatusDialog(success, msg) {
        dlgOkay.title = "Backing up trawl_backdeck.db database file"
        dlgOkay.height = 350
        dlgOkay.width = 750
        dlgOkay.message = msg ? msg : ""
        dlgOkay.open()
    }

    function updateHaulDetails() {
        btnProcessCatch.state = stateMachine.haul["haul_id"] ? qsTr('enabled') : qsTr('disabled')
    }

    Column {
        id: buttonsColumn
        anchors.left: parent.left
        anchors.leftMargin: 20
        anchors.top: parent.top
        anchors.topMargin: 20
        height: parent.height
        spacing: 20

        BackdeckMenuButton {
            id: btnOperationSelection
            text: qsTr("Select\nTrip")
            onClicked: {
                if (!screens.busy) {
                    screens.push(Qt.resolvedUrl("OperationSelectionScreen.qml"))
                    bdSM.to_operation_selection_state()
                }
            }
        } // btnOperationSelection
        BackdeckMenuButton {
            id: btnSpeciesComposition
            text: qsTr("Species\nComposition")
            state: qsTr("enabled")
            onClicked: {
                if (!screens.busy) {
                    screens.push(Qt.resolvedUrl("SpeciesSelectionScreen.qml"))
                    bdSM.to_fish_sampling_state()
                }
            }
        } // btnSpeciesComposition
        BackdeckMenuButton {
            id: btnValidate
            text: qsTr("Finish Trip\n& Validate")
            onClicked: {
                dlgValidate.btnOkay.text = "Haul\nComplete"
                dlgValidate.open()
            }
        } // btnValidate
//        BackdeckMenuButton {
//            id: btnReport
//            text: qsTr("Reports")
//            state: qsTr("disabled")
//            onClicked: {
//                if (!screens.busy) {
//                    screens.push(Qt.resolvedUrl("ReportScreen.qml"))
//                    bdSM.to_reports_state()
//                }
//            }
//        }
//        BackdeckMenuButton {
//            id: btnSerialPortManager
//            text: qsTr("Serial Port\nManager")
//            Layout.preferredWidth: this.width
//            Layout.preferredHeight: this.height
//            onClicked: {
//                if (!screens.busy) {
//                    screens.push(Qt.resolvedUrl("SerialPortManagerScreen.qml"))
//                    bdSM.to_serial_port_manager_state()
//                }
//            }
//        }

        Label { Layout.fillHeight: true }

        BackdeckMenuButton {
            id: btnSettings
            text: qsTr("Settings")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
                if (!screens.busy) {
                    screens.push(Qt.resolvedUrl("SettingsScreen.qml"))
                    bdSM.to_serial_port_manager_state()
                }
            }
        }
    }

    RowLayout {
        x: parent.width - this.width - 20
        y: parent.height - this.height - 20
        spacing: 10

        BackdeckButton {
            id: btnNotes
            text: qsTr("Note")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: 60
            onClicked: {
                dlgNote.reset()
                dlgNote.open()
            }
        } // btnNotes
    }
    NoteDialog {
        id: dlgNote
    }
    ValidateDialog {
        id: dlgValidate
    }
    OkayDialog {
        id:  dlgOkay
    }
}
