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

//        updateHaulDetails()
    }

    Connections {
        target: qaqc
        onBackupStatusChanged: showBackupStatusDialog(success, msg)
    }

    function showBackupStatusDialog(success, msg) {
        dlgOkay.title = "Backing up trawl_backdeck.db database file"
        dlgOkay.height = 350
        dlgOkay.width = 750
        dlgOkay.message = msg ? msg : ""
        dlgOkay.open()
    }

    function updateHaulDetails() {
//        tfHaulId.text = stateMachine.haul['haul_number'] ? stateMachine.haul['haul_number'] : ""
//        tfDate.text = stateMachine.haul['date'] ? stateMachine.haul["date"] : ""
//        tfStartTime.text = stateMachine.haul['start_time'] ? stateMachine.haul['start_time'] : ""
//        tfEndTime.text = stateMachine.haul['end_time'] ? stateMachine.haul['end_time'] : ""
//        tfStationNumber.text = stateMachine.haul["station_number"] ? stateMachine["station_number"] : ""

        btnProcessCatch.state = stateMachine.haul["haul_id"] ? qsTr('enabled') : qsTr('disabled')
    }

    Column {
        id: buttonsColumn
//        x: 50
//        y: (main.height - this.height)/2
//        y: 30
        anchors.left: parent.left
        anchors.leftMargin: 20
        anchors.top: parent.top
        anchors.topMargin: 20
        spacing: 20

        TrawlBackdeckMenuButton {
            id: btnHaulSelection
            text: qsTr("Select Haul")
            onClicked: {
                if (!screens.busy) {
                    screens.push(Qt.resolvedUrl("HaulSelectionScreen.qml"))
                    tbdSM.to_haul_selection_state()
                }
            }
        }
        TrawlBackdeckMenuButton {
            id: btnProcessCatch
            text: qsTr("Process Catch")
//            state: qsTr("disabled")
            state: stateMachine.haul["haul_id"] ? qsTr('enabled') : qsTr('disabled')
            onClicked: {
                if (!screens.busy) {
                    screens.push(Qt.resolvedUrl("ProcessCatchScreen.qml"))
                    tbdSM.to_process_catch_state()
                }
            }
        }
        TrawlBackdeckMenuButton {
            id: btnValidate
            text: qsTr("Finished Haul\n& Validate")
            state: qsTr("enabled")
            onClicked: {
                dlgValidate.btnOkay.text = "Haul\nComplete"
                dlgValidate.open()
//                if (!screens.busy) {
//                    screens.push(Qt.resolvedUrl("QAQCScreen.qml"))
//                    tbdSM.to_qaqc_state()
//                }
            }
        }
        TrawlBackdeckMenuButton {
            id: btnReport
            text: qsTr("Reports")
            state: qsTr("disabled")
            onClicked: {
                if (!screens.busy) {
                    screens.push(Qt.resolvedUrl("ReportScreen.qml"))
                    tbdSM.to_reports_state()
                }
            }
        }
    }
    ColumnLayout {
        id: colSettings
//        x: 50
//        y: 30
        anchors.right: parent.right
        anchors.rightMargin: 20
        anchors.top: parent.top
        anchors.topMargin: 20

        spacing: 20

        TrawlBackdeckMenuButton {
            id: btnSerialPortManager
            text: qsTr("Serial Port\nManager")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
                if (!screens.busy) {
                    screens.push(Qt.resolvedUrl("SerialPortManagerScreen.qml"))
                    tbdSM.to_serial_port_manager_state()
                }
            }
        }
        TrawlBackdeckMenuButton {
            id: btnCommunications
            text: qsTr("Network\nTesting")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
                if (!screens.busy) {
                    screens.push(Qt.resolvedUrl("NetworkTestingScreen.qml"))
                    tbdSM.to_serial_port_manager_state()
                }
            }
        }
        TrawlBackdeckMenuButton {
            id: btnSettings
            text: qsTr("Settings")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
                if (!screens.busy) {
                    screens.push(Qt.resolvedUrl("SettingsScreen.qml"))
                    tbdSM.to_serial_port_manager_state()
                }
            }
        }
        TrawlBackdeckMenuButton {
            id: btnProtocolManager
            text: qsTr("Protocol\nManager")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: screens.push(Qt.resolvedUrl("ProtocolManagerScreen.qml"))
        }
    }

    GroupBox {
        id: grpCurrentHaul
        x: buttonsColumn.x + buttonsColumn.width + 40
        y: buttonsColumn.y
        width: 400
        height: 320
        title: qsTr("Current Haul")
        style: Style {
            property Component panel: Rectangle {
                color: "transparent"
                border.width: 1
                Rectangle {
                    height: txtObj.height + 10
                    width: txtObj.width + 10
                    x: txtObj.x - 5
                    y: txtObj.y - 5
                    color: SystemPaletteSingleton.window(true)
                }
                Text {
                    id: txtObj
                    anchors.verticalCenter: parent.top
                    x: 10
                    text: control.title
                    font.pixelSize: 24
                }
            }
        }

        GridLayout {
            id: gridCurrentHaul
            columns: 2
            x: 20
            y: 30
            columnSpacing: 20
            rowSpacing: 20
            Label {
                id: lblHaulId
                text: qsTr("Haul ID")
                font.pixelSize: 24
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfHaulId
                text: stateMachine.haul["haul_number"] // "423"
                font.pixelSize: 24
                readOnly: true
                Layout.minimumWidth: 220
            }
            Label {
                id: lblDate
                text: qsTr("Date")
                font.pixelSize: 24
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfDate
                text: stateMachine.haul['date'] //"08/09/2015"
                Layout.minimumWidth: 170
            }
            Label {
                id: lblStartTime
                text: qsTr("Start Time")
                font.pixelSize: 24
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfStartTime
                text: stateMachine.haul['start_time'] // "17:35"
            }
            Label {
                id: lblEndTime
                text: qsTr("End Time")
                font.pixelSize: 24
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfEndTime
                text: stateMachine.haul['end_time'] // "17:55"
            }
            Label {
                id: lblStationNumber
                text: qsTr("Station ID")
                font.pixelSize: 24
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfStationNumber
                text: stateMachine.haul['station_number'] // "4267"
            }
        }
    } // grpCurrentHaul
    GroupBox {
        id: grpLastBackup
//        x: grpCurrentHaul.x + grpCurrentHaul.width + 30
//        y: buttonsColumn.y
        x: grpCurrentHaul.x
        y: grpCurrentHaul.y + grpCurrentHaul.height + 30
        width: 320
        height: grpCurrentHaul.height
        visible: true
        title: qsTr("Last Backup")
        style: Style {
            property Component panel: Rectangle {
                color: "transparent"
                border.width: 1
                Rectangle {
                    height: txtObj.height + 10
                    width: txtObj.width + 10
                    x: txtObj.x - 5
                    y: txtObj.y - 5
                    color: SystemPaletteSingleton.window(true)
                }
                Text {
                    id: txtObj
                    anchors.verticalCenter: parent.top
                    x: 10
                    text: control.title
                    font.pixelSize: 24
                }
            }
        }
        GridLayout {
            id: gridLastBackup
            columns: 2
            x: 20
            y: 30
            columnSpacing: 20
            rowSpacing: 20
            Label {
                id: lbLBHaulId
                text: qsTr("Haul ID")
                font.pixelSize: 24
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfLBHaulID
                text: ""
            }
            Label {
                id: lblLBDate
                text: qsTr("Date")
                font.pixelSize: 24
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfLBDate
                text: ""
                Layout.preferredWidth: 180
            }
            Label {
                id: lblLBTime
                text: qsTr("Time")
                font.pixelSize: 24
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfLBTime
                text: ""
                Layout.preferredWidth: 100
            }
        }
    } // grpLastBackup
    RowLayout {
        x: parent.width - this.width - 20
        y: parent.height - this.height - 20
        spacing: 10

        TrawlBackdeckButton {
            text: "Feeling\nLucky"
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            onClicked: {
                home.feelingLucky()
            }
        }
        TrawlBackdeckButton {
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
    TrawlNoteDialog {
        id: dlgNote
    }
    TrawlValidateDialog {
        id: dlgValidate
    }
    TrawlOkayDialog {
        id:  dlgOkay
    }

//    GroupBox {
//        id: grpQAQC
//        x: grpLastBackup.x
//        y: grpLastBackup.y + grpLastBackup.height + 40
//        width: grpLastBackup.width
//        height: grpLastBackup.height
//        visible: true
//        title: qsTr("QA/QC Statistics")
//        style: Style {
//            property Component panel: Rectangle {
//                color: "transparent"
//                border.width: 1
//                Rectangle {
//                    height: txtObj.height + 10
//                    width: txtObj.width + 10
//                    x: txtObj.x - 5
//                    y: txtObj.y - 5
//                    color: SystemPaletteSingleton.window(true)
//                }
//                Text {
//                    id: txtObj
//                    anchors.verticalCenter: parent.top
//                    x: 10
//                    text: control.title
//                    font.pixelSize: 24
//                }
//            }
//        }
//        GridLayout {
//            id: gridQAQC
//            columns: 2
//            x: 20
//            y: 30
//            columnSpacing: 20
//            rowSpacing: 20
//
//            Label {
//                id: lblCriticalFailures
//                text: qsTr("Critical Failures")
//                font.pixelSize: 24
//            }
//            TrawlBackdeckTextFieldDisabled {
//                id: tfCriticalFailures
//                text: "15"
//                Layout.maximumWidth: 80
//            }
//            Label {
//                id: lblTotalFailures
//                text: qsTr("Total Failures")
//                font.pixelSize: 24
//            }
//            TrawlBackdeckTextFieldDisabled {
//                id: tfTotalFailures
//                text: "34"
//                Layout.maximumWidth: 80
//            }
//            Label {
//                id: lblFailureRate
//                text: qsTr("Failure Rate")
//                font.pixelSize: 24
//            }
//            TrawlBackdeckTextFieldDisabled {
//                id: tfFailureRate
//                text: "12%"
//                Layout.maximumWidth: 80
//            }
//        }
//    } // grpQAQC


}
