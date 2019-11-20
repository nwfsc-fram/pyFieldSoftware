import QtQuick 2.2
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
            text: qsTr("Sebastes aurora")
            font.pixelSize: 20
            readOnly: true
            Layout.preferredWidth: 300
        }
        Label {
            id: lblProtocol
            text: qsTr("Protocol")
            font.pixelSize: 20
            Layout.preferredWidth: 80
        }
        TrawlBackdeckTextFieldDisabled {
            id: tfProtocol
            text: qsTr("SL100AW15")
            font.pixelSize: 20
            readOnly: true
            Layout.preferredWidth: 300
        }
    }

    TrawlBackdeckButton {
        id: btnDisableProtocol
        x: main.width - this.width - 20
        y: rwlHeader.y
        text: qsTr("Disable\nProtocol")
        checkable: true
    }

    GroupBox {
        id: grpSex
        x: rwlHeader.x
        y: rwlHeader.y + rwlHeader.height + 20
        height: 90
        width: 410
        title: qsTr("Sex")
        ExclusiveGroup {
            id: egSexType
        }
        RowLayout {
            x: 15
            y: 20
            spacing: 10
            TrawlBackdeckButton {
                id: btnFemale
                text: qsTr("Female")
                checked: true
                checkable: true
                exclusiveGroup: egSexType
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
            TrawlBackdeckButton {
                id: btnMale
                text: qsTr("Male")
                checkable: true
                exclusiveGroup: egSexType
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
            TrawlBackdeckButton {
                id: btnUnsex
                text: qsTr("Unsex")
                checkable: true
                exclusiveGroup: egSexType
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
        }
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
                    x: this.x + 10
                    text: control.title
                    font.pixelSize: 20
                }
            }
        }
    }

    GroupBox {
        id: grpLength
        x: grpSex.x
        y: grpSex.y + grpSex.height + 20
//        y: rwlHeader.y + rwlHeader.height + 20
        height: 550
        width: grpSex.width
        title: qsTr("Length")
        ExclusiveGroup {
            id: egLengthMethod
        }
        RowLayout {
            x: 15
            y: 20
//            anchors.horizontalCenter: grpSex.horizontalCenter
            spacing: 10
            TrawlBackdeckButton {
                id: btnFishBoard
                text: qsTr("Fish Board")
                checked: true
                checkable: true
                exclusiveGroup: egLengthMethod
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
            TrawlBackdeckButton {
                id: btnManual
                text: qsTr("Manual")
                checkable: true
                exclusiveGroup: egLengthMethod
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
            TrawlBackdeckButton {
                id: btnCalipers
                text: qsTr("Calipers")
                checkable: true
                exclusiveGroup: egLengthMethod
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
    }

    FramNumPad {
        id: numPad
        x: 210
        y: 500
//        anchors.top: btnFishBoard.y + btnFishBoard.height + 20
        state: qsTr("weights")
    }

    TrawlBackdeckTableView {
        id: tvLengths
        x: grpSex.x + grpSex.width + 60
        y: grpSex.y + 20
        width: 500
        height: 450
        selectionMode: SelectionMode.SingleSelection
        headerVisible: true
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

        onClicked: {
//            msg.show(row)
        }
        onDoubleClicked: {
            screens.push(Qt.resolvedUrl("StandardProtocolScreen.qml"))
        }

        TableViewColumn {
            role: "length"
            title: "Length"
            width: 80
        }
        TableViewColumn {
            role: "sex"
            title: "Sex"
            width: 60
        }
        TableViewColumn {
            role: "weight_kg"
            title: "Weight"
            width: 100
            delegate: Text {
                text: {
                    if (styleData.value)
                        styleData.value.toFixed(3)
                    else
                        ""
                }
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        }
        TableViewColumn {
            role: "special"
            title: "Special"
            width: 100
        }
        TableViewColumn {
            role: "barCode"
            title: "Barcode"
            width: 160
            delegate: Text {
                text: {
                    if (styleData.value)
                        styleData.value
                    else
                        ""
                }
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        }
        model: LengthsModel {}
    }
    Column {
        anchors.left: tvLengths.left
        y: tvLengths.y + tvLengths.height + 10
        spacing: 10
        Label {
            text: qsTr("Total Fish Measured")
            font.pixelSize: 20
        }
        TrawlBackdeckTextFieldDisabled {
            text: qsTr("3")
            font.pixelSize: 20
        }
    }
    Row {
        anchors.right: tvLengths.right
        y: tvLengths.y + tvLengths.height + 10
        spacing: 10
        TrawlBackdeckButton {
            id: btnModifyEntry
            text: qsTr("Modify\nEntry")
        }
        TrawlBackdeckButton {
            id: btnDeleteEntry
            text: qsTr("Delete\nEntry")
        }
    }

    TrawlBackdeckButton {
        id: btnDone
        text: qsTr("Done")
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        onClicked: screens.pop()
    }
}