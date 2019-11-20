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

    GroupBox {
        id: grpWeight
        x: rwlHeader.x
        y: rwlHeader.y + rwlHeader.height + 30
        height: 640
        width: 410
        title: qsTr("Weight")
        ExclusiveGroup {
            id: egWeightType
        }
        ColumnLayout {
            x: 15
            y: 20
            spacing: 10
            TrawlBackdeckButton {
                id: btnScaleWeight
                text: qsTr("Scale")
                checked: true
                checkable: true
                exclusiveGroup: egWeightType
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
            TrawlBackdeckButton {
                id: btnManualWeight
                text: qsTr("Manual")
                checkable: true
                exclusiveGroup: egWeightType
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
        }
        TextField {
            id: tfWeight
            x: btnScaleWeight.x + btnScaleWeight.width + 80
//            anchors.verticalCenter: btnScaleWeight.verticalCenter
            y: btnScaleWeight.y + 40
            text: qsTr("12.0")
            font.pixelSize: 20
            readOnly: true
            Layout.preferredWidth: 80
        }
        Label {
            id: lblWeight
            x: tfWeight.x + tfWeight.width + 10
            y: tfWeight.y
            text: qsTr("Kg")
            font.pixelSize: 20
            Layout.preferredWidth: 50
        }
        FramNumPad {
            id: numPad
            x: 190
            y: 400
            state: qsTr("weights")
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
        id: grpSex
        x: grpWeight.x + grpWeight.width + 20
        y: grpWeight.y
        width: 150
        height: 230
//        width: grpSex.width
        title: qsTr("Sex")
        ExclusiveGroup {
            id: egSex
        }
        ColumnLayout {
            x: 15
            y: 20
//            anchors.horizontalCenter: grpSex.horizontalCenter
            spacing: 10
            TrawlBackdeckButton {
                id: btnFemale
                text: qsTr("Female")
                checked: true
                checkable: true
                exclusiveGroup: egSex
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
            TrawlBackdeckButton {
                id: btnMale
                text: qsTr("Male")
                checkable: true
                exclusiveGroup: egSex
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
            TrawlBackdeckButton {
                id: btnUnsex
                text: qsTr("Unsex")
                checkable: true
                exclusiveGroup: egSex
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

    GroupBox {
        id: grpAge
        x: grpSex.x + grpSex.width + 20
        y: grpSex.y
        width: 380
        height: grpSex.height
        title: qsTr("Age")
        GridLayout {
            id: grdAge
            x: 15
            y: 20
            columns: 2
            columnSpacing: 20
            rowSpacing: 20
            Label {
                id: lblSampleType
                text: qsTr("Sample Type")
                font.pixelSize: 20
            }
            TrawlBackdeckComboBox {
                id: cbSampleType
                Layout.preferredHeight: 40
                Layout.preferredWidth: 220
                model: SampleTypesModel {}
            }
            Label {
                id: lblTagID
                text: qsTr("Tag ID")
                font.pixelSize: 20
            }
            TextField {
                id: tfTagID
                text: qsTr("100200300")
                font.pixelSize: 20
                Layout.preferredWidth: 150
            }


        }
        RowLayout {
    //        anchors.right: tvLengths.right
//            x: grdAge.x
            anchors.horizontalCenter: grdAge.horizontalCenter
            y: grdAge.y + grdAge.height + 40
            spacing: 10
            TrawlBackdeckButton {
                id: btnManualTag
                text: qsTr("Manual\nTag")
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
            TrawlBackdeckButton {
                id: btnDeleteTag
                text: qsTr("Delete\nTag")
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

    GroupBox {
        id: grpMiscellaneous
        x: grpSex.x
        y: grpSex.y + grpSex.height + 40
        width: 500
        height: 250
        title: qsTr("Miscellaneous")
        GridLayout {
            id: grdMiscellaneous
            x: 15
            y: 30
            columns: 2
            columnSpacing: 40
            rowSpacing: 20
            Label {
                id: lblTissueNumber
                text: qsTr("Tissue Number")
                font.pixelSize: 20
            }
            TextField {
                id: tfTissueNumber
                text: qsTr("100200300")
                font.pixelSize: 20
                Layout.preferredWidth: 150
            }
            Label {
                id: lblOvaryNumber
                text: qsTr("Ovary Number")
                font.pixelSize: 20
            }
            TextField {
                id: tfOvaryNumber
                text: qsTr("123445351")
                font.pixelSize: 20
                Layout.preferredWidth: 150
            }
            Label {
                id: lblStomachNumber
                text: qsTr("Stomach Number")
                font.pixelSize: 20
            }
            TextField {
                id: tfStomachNumber
                text: qsTr("1002034200")
                font.pixelSize: 20
                Layout.preferredWidth: 150
            }
            Label {
                id: lblFinclipNumber
                text: qsTr("Finclip Number")
                font.pixelSize: 20
            }
            TextField {
                id: tfFinclipNumber
                text: qsTr("100200300")
                font.pixelSize: 20
                Layout.preferredWidth: 150
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

/*
    GroupBox {
        id: grpSpecialSample
        x: grpAge.x
        y: grpAge.y + grpAge.height + 40
        width: grpAge.width / 2
        height: 90
        title: qsTr("Special Sample")

//        Component.onCompleted: {
//            msg.show('y: ' + grpAge.);
//        }

        TrawlBackdeckButton {
            id: btnSpecialSample3
            x: 30
//            anchors.horizontalCenter: grpSpecialSample.horizontalCenter
            y: 20
            text: qsTr("Special\nAction")
            onClicked: screens.push(Qt.resolvedUrl("SpecialSamplingScreen.qml"))
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
*/

    TrawlBackdeckButton {
        id: btnComments
        text: qsTr("Comments")
        x: main.width - this.width - btnDone.width - btnSpecialSample.width - 40
        y: main.height - this.height - 20
    }
    TrawlBackdeckButton {
        id: btnSpecialSample
        x: main.width - this.width - btnDone.width - 30
        y: main.height - this.height - 20
        text: qsTr("Special\nAction")
        onClicked: screens.push(Qt.resolvedUrl("SpecialSamplingScreen.qml"))
    }
    TrawlBackdeckButton {
        id: btnDone
        text: qsTr("Done")
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        onClicked: screens.pop()
    }
}