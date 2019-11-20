import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0

import "../common"

Item {

//    Connections {
//        target: stateMachine
//        onHaulSelected: {
//            updateHaulDetails()
//        }
//    }

    Component.onCompleted: {
        updateHaulDetails()
    }

    Component.onDestruction: {
        tbdSM.to_home_state()
    }

    function updateHaulDetails() {
        tfHaulId.text = stateMachine.haul['haul_number'] ? stateMachine.haul['haul_number'] : ""
    }

    RowLayout {
        id: rwlHeader
        x: 20
        y: 20
        spacing: 10

        Label {
            id: lblHaulID
            text: qsTr("Haul ID")
            font.pixelSize: 20
            Layout.preferredWidth: 80
        }
        TrawlBackdeckTextFieldDisabled {
            id: tfHaulId
            text: qsTr("345")
            font.pixelSize: 20
            readOnly: true
            Layout.preferredWidth: 100
        }
    }

    TrawlBackdeckTableView {
        id: tvValidations
        x: rwlHeader.x
        y: rwlHeader.y + rwlHeader.height + 20
        width: 600
        height: 500
        selectionMode: SelectionMode.SingleSelection
        headerVisible: true
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
        onClicked: {
//            msg.show(row)
        }
        TableViewColumn {
            role: "category"
            title: "Category"
            width: 100
        }
        TableViewColumn {
            role: "validation"
            title: "Validation"
            width: 400
        }
        TableViewColumn {
            role: "status"
            title: "Status"
            width: 100
        }
        model: ValidationsModel {}
    }
    RowLayout {
        id: rwlShowValidations
//        x: rwlHeader.x
        anchors.horizontalCenter: tvValidations.horizontalCenter
        y: tvValidations.y + tvValidations.height + 20
        spacing: 10

        Label {
            id: lblShowItems
            text: qsTr("Show")
            font.pixelSize: 20
            Layout.preferredWidth: 60
        }
        TrawlBackdeckButton {
            id: btnShowSuccesses
            text: qsTr("Successes\n(75)")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            checked: true
        }
        TrawlBackdeckButton {
            id: btnShowFailures
            text: qsTr("Failures\n(7)")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            checked: true

            onClicked: {

            }
        }
        TrawlBackdeckButton {
            id: btnShowResolved
            text: qsTr("Resolved\n(1)")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true

            onClicked: {

            }
        }
    }


    GroupBox {
        id: grpFailureDetails
        x: tvValidations.x + tvValidations.width + 20
        y: tvValidations.y
//        y: rwlHeader.y + rwlHeader.height + 20
        height: 550
        width: main.width - tvValidations.width - 60
        title: qsTr("Failure Details")

        style: Style {
            property Component panel: Rectangle {
                color: "transparent"
                border.width: 1
//                border.color: "#dddddd"
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
//                    x: this.x + 10
                    text: control.title
                    font.pixelSize: 20
                }
            }
        }
        ColumnLayout {
            id: cllFailureDetails
            x: 10
            y: 30
            spacing: 20

            Column {
                spacing: 10
                Label {
                    id: lblCurrentValueType
                    text: qsTr("Current Value Type")
                    font.pixelSize: 20
                        Layout.preferredWidth: 80
                }
                TrawlBackdeckTextFieldDisabled {
                    id: tfCurrentValueType
                    text: qsTr("Age Barcode Number")
                    font.pixelSize: 20
                    width: grpFailureDetails.width - 20
//                    Layout.preferredWidth: grpFailureDetails.width - 20
                }
            }
            Column {
                spacing: 10
                Label {
                    id: lblCurrentEntry
                    text: qsTr("Current Entry")
                    font.pixelSize: 20
                    Layout.preferredWidth: 80
                }
                TrawlBackdeckTextFieldDisabled {
                    id: tfCurrentEntry
                    text: qsTr("1234521505")
                    font.pixelSize: 20
                    width: grpFailureDetails.width - 20
                }
            }
            Column {
                spacing: 10
                Label {
                    id: lblCorrectedEntry
                    text: qsTr("Corrected Entry")
                    font.pixelSize: 20
                    Layout.preferredWidth: 80
                }
                TextField {
                    id: tfCorrectedEntry
                    text: qsTr("123000100")
                    font.pixelSize: 20
                    width: grpFailureDetails.width - 20
                }
            }

            Column {
                spacing: 10
                Label {
                    id: lblComment
                    text: qsTr("Comment")
                    font.pixelSize: 20
                    Layout.preferredWidth: 80
                }
                TextArea {
                    id: taComment
                    text: qsTr("This is a bogus barcode, don't know what happened")
                    font.pixelSize: 20
                    width: grpFailureDetails.width - 20
                    height: 150
                }
            }
            TrawlBackdeckButton {
                id: btnResolved
                text: qsTr("Resolve /\nSave")
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
        }
    }
    TrawlBackdeckButton {
        text: qsTr("Done")
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        onClicked: screens.pop()
    }
}