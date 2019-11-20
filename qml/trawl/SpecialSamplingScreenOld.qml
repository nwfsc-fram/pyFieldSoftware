import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0

import "../common"

Item {
    Label {
        id: lblPossibleSamples
        text: qsTr("Possible Samples")
        x: 20
        y: 20
        font.pixelSize: 20
    }
    TrawlBackdeckTableView {
        id: tvPossibleSamples
        x: 20
        y: lblPossibleSamples.y + lblPossibleSamples.height + 10
        width: 400
        height: 570
        selectionMode: SelectionMode.SingleSelection
        headerVisible: true
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
        onClicked: {
//            msg.show(row)
        }
        TableViewColumn {
            role: "investigator"
            title: "Investigator"
            width: 100
        }
        TableViewColumn {
            role: "specialAction"
            title: "Special Action"
            width: 300
        }
        model: SpecialActionsModel {}
    }
    ColumnLayout {
        id: cllAddRemoveButtons
//        x: tvPossibleSamples.x + tvPossibleSamples.width + 20
        x: main.width/2 - this.width/2
        anchors.verticalCenter: tvTakenSamples.verticalCenter
//        anchors.verticalCenter: tvPossibleSamples.verticalCenter
        TrawlBackdeckButton {
            id: btnAddSample
            text: qsTr("Add\n>")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
        }
        TrawlBackdeckButton {
            id: btnRemoveSample
            text: qsTr("Remove\n<")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
        }
    }
    Label {
        id: lblTakenSamples
        text: qsTr("Taken Samples")
        x: tvTakenSamples.x
        y: 20
        font.pixelSize: 20
    }
    TrawlBackdeckTableView {
        id: tvTakenSamples
        x: main.width - this.width - 20
        y: tvPossibleSamples.y
        width: tvPossibleSamples.width
        height: 260
        selectionMode: SelectionMode.SingleSelection
        headerVisible: true
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
        onClicked: {
//            msg.show(row)
        }
        TableViewColumn {
            role: "investigator"
            title: "Investigator"
            width: 100
        }
        TableViewColumn {
            role: "specialAction"
            title: "Special Action"
            width: 300
        }
        model: SpecialActionsModel {}
    }
    GroupBox {
        id: gbSampleDetails
        anchors.left: tvTakenSamples.left
        y: tvTakenSamples.y + tvTakenSamples.height + 20
        width: tvTakenSamples.width
//        height: 360
        height: tvPossibleSamples.height - tvTakenSamples.height - 20
        title: qsTr("Sample Details")
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
        GridLayout {
            id: gdlSampleDetails
            columns: 2
            columnSpacing: 30
            rowSpacing: 20
            x: 20
            y: 30
            Label {
                id: lblTissueSample
                text: qsTr("Tissue Sample")
                font.pixelSize: 20
            }
            TextField {
                id: tfTissueSample
                text: qsTr("100212345")
                font.pixelSize: 20
                Layout.preferredWidth: 180
            }
            Label {
                id: lblStomachSample
                text: qsTr("Stomach Sample")
                font.pixelSize: 20
            }
            TextField {
                id: tfStomachSample
                text: qsTr("10034221")
                font.pixelSize: 20
                Layout.preferredWidth: 180
            }
            Label {
                id: lblOvarySample
                text: qsTr("Ovary Sample")
                font.pixelSize: 20
            }
            TextField {
                id: tfOvarySample
                text: qsTr("12342123")
                font.pixelSize: 20
                Layout.preferredWidth: 180
            }
            Label {
                id: lblFinclipSample
                text: qsTr("Finclip Sample")
                font.pixelSize: 20
            }
            TextField {
                id: tfFinclipSample
                text: qsTr("12342123")
                font.pixelSize: 20
                Layout.preferredWidth: 180
            }
            Label {
                id: lblOtherSample
                text: qsTr("Other Sample")
                font.pixelSize: 20
            }
            TextField {
                id: tfOtherSample
                text: qsTr("12342123")
                font.pixelSize: 20
                Layout.preferredWidth: 180
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