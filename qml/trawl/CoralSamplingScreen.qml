import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0

import "../common"

Item {
    RowLayout {
        id: rwlHeader
        x: 20
        y: 20
        spacing: 10
        Label {
            id: lblSpecies
            text: qsTr("Species")
            font.pixelSize: 20
            Layout.preferredWidth: 80
        }
        TrawlBackdeckTextFieldDisabled {
            id: tfSpecies
            text: stateMachine.species["display_name"]
            font.pixelSize: 20
            readOnly: true
            Layout.preferredWidth: 300
        }
    }

    RowLayout {
        id: rwlMiscButtons
//        x: tvCorals.x
        x: rwlHeader.x
//        y: tvCorals.y - this.height - 20
        y: rwlHeader.y + rwlHeader.height + 20

        TrawlBackdeckButton {
            id: btnWholeSpecimen
            text: qsTr("Whole\nSpecimen")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
        }
        TrawlBackdeckButton {
            id: btnPhoto
            text: qsTr("Photo")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
        }
    }
    GroupBox {
        id: grpBarcodeMethod
        x: rwlHeader.x
        y: rwlMiscButtons.y + rwlMiscButtons.height + 20
//        y: rwlHeader.y + rwlHeader.height + 30
//        y: rwlHeader.y + rwlHeader.height + 20
        height: 560
        width: 400
        title: qsTr("Barcode")
        ExclusiveGroup {
            id: egBarcodeMethod
        }
        RowLayout {
            id: rwlBarcodeMethod
            x: 15
            y: 20
//            anchors.horizontalCenter: grpSex.horizontalCenter
            spacing: 10
            TrawlBackdeckButton {
                id: btnBarcodeReader
                text: qsTr("Barcode\nReader")
                checked: true
                checkable: true
                exclusiveGroup: egBarcodeMethod
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
            TrawlBackdeckButton {
                id: btnManual
                text: qsTr("Manual")
                checkable: true
                exclusiveGroup: egBarcodeMethod
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
        }
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
                    x: this.x + 10
                    text: control.title
                    font.pixelSize: 20
                }
            }
        }
        FramNumPad {
            id: numPad
 //           anchors.horizontalCenter: grpBarcodeMethod.horizontalCenter
            x: 180
//            y: rwlBarcodeMethod.y + rwlBarcodeMethod.height + 20
            y: 330
        }
    }

    ColumnLayout {
        id: cllAddDeleteButtons
        x: grpBarcodeMethod.x + grpBarcodeMethod.width + 20
        y: main.height/2 - this.height/2
//        anchors.verticalCenter: main.height/2

        TrawlBackdeckButton {
            id: btnAddEntry
            text: qsTr("Add\n>")
            enabled: true
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
    //        anchors.top: tvCorals.bottom + 20
        }
        TrawlBackdeckButton {
            id: btnDeleteEntry
            text: qsTr("Delete\nEntry")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
//            enabled: false
    //        anchors.top: tvCorals.bottom + 20
        }
    }

    TrawlBackdeckTableView {
        id: tvCorals
        x: main.width - this.width - 20
//        y: 300
        y: main.height / 2 - this.height/2
        width: 400
        height: 255
        TableViewColumn {
            role: "barcode"
            title: "Barcode"
            width: 150
        }
        TableViewColumn {
            role: "wholeSpecimen"
            title: "Whole Specimen"
            width: 100
        }
        TableViewColumn {
            role: "photo"
            title: "Photo"
            width: 80
        }
        model: CoralsModel {}
    }

    TrawlBackdeckButton {
        text: qsTr("Done")
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        onClicked: screens.pop()
    }
}