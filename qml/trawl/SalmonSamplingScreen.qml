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

    GroupBox {
        id: grpSalmon
        x: rwlHeader.x
        y: rwlHeader.y + rwlHeader.height + 30
        height: 310
        width: main.width - 2 * rwlHeader.x
        title: qsTr("Individual Salmon")
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
            id: glSalmonOptions
            x: 60
            y: 40
//            anchors.verticalCenter: grpSalmon.verticalCenter
            columns: 2
            columnSpacing: 10
            rowSpacing: 30

            ExclusiveGroup {
                id: egMaturity
            }
            ExclusiveGroup {
                id: egBirthLocation
            }
            ExclusiveGroup {
                id: egDeadOrAlive
            }

            TrawlBackdeckButton {
                text: qsTr("Adult")
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                checkable: true
                exclusiveGroup: egMaturity
            }
            TrawlBackdeckButton {
                text: qsTr("Sub-Adult")
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                checkable: true
                exclusiveGroup: egMaturity
            }
            TrawlBackdeckButton {
                text: qsTr("Wild")
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                checkable: true
                exclusiveGroup: egBirthLocation
            }
            TrawlBackdeckButton {
                text: qsTr("Hatchery")
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                checkable: true
                exclusiveGroup: egBirthLocation
            }
            TrawlBackdeckButton {
                id: btnDead
                text: qsTr("Dead")
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                checkable: true
                exclusiveGroup: egDeadOrAlive
            }
            TrawlBackdeckButton {
                text: qsTr("Alive")
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                checkable: true
                exclusiveGroup: egDeadOrAlive
            }
        }
        ColumnLayout {
            id: cllAddRemoveButtons
            x: glSalmonOptions.x + glSalmonOptions.width + 60
            anchors.verticalCenter: glSalmonOptions.verticalCenter
            spacing: 20
            TrawlBackdeckButton {
                id: btnAddSalmon
                text: qsTr("Add\n>")
                Layout.preferredHeight: this.height
                Layout.preferredWidth: this.width
            }
            TrawlBackdeckButton {
                id: btnDeleteSalmon
                text: qsTr("Delete\nEntry")
                Layout.preferredHeight: this.height
                Layout.preferredWidth: this.width
            }
        }

        TrawlBackdeckTableView {
            id: tvSalmon
            x: cllAddRemoveButtons.x + cllAddRemoveButtons.width + 60
            y: 10
            width: 380
            height: 290
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
            TableViewColumn {
                role: "salmonID"
                title: "ID"
                width: 40
            }
            TableViewColumn {
                role: "stage"
                title: "Stage"
                width: 100
            }
            TableViewColumn {
                role: "population"
                title: "Population"
                width: 120
            }
            TableViewColumn {
                role: "condition"
                title: "Condition"
                width: 120
            }
            model: SalmonModel {}
        }

    }
    Label {
        id: lblSalmonCounts
        text: qsTr("Salmon Counts")
        font.pixelSize: 20
        x: grpSalmon.x
        y: grpSalmon.y + grpSalmon.height + 20
    }

    TrawlBackdeckTableView {
        id: tvSalmonCounts
        x: grpSalmon.x
//        y: 20
        y: lblSalmonCounts.y + lblSalmonCounts.height + 10
        width: 420
        height: 270
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
        TableViewColumn {
            role: "stage"
            title: "Stage"
            width: 100
        }
        TableViewColumn {
            role: "population"
            title: "Population"
            width: 120
        }
        TableViewColumn {
            role: "condition"
            title: "Condition"
            width: 110
        }
        TableViewColumn {
            role: "count"
            title: "Count"
            width: 90
        }
        model: SalmonCountModel {}
    }
    ColumnLayout {
        id: rwlCountsFilter
        x: tvSalmonCounts.x + tvSalmonCounts.width + 20
        anchors.verticalCenter: tvSalmonCounts.verticalCenter
        spacing: 10
        ExclusiveGroup {
            id: egHaulGroup
        }
        TrawlBackdeckButton {
            text: qsTr("Current\nHaul")
            exclusiveGroup: egHaulGroup
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            checked: true
        }
        TrawlBackdeckButton {
            text: qsTr("Today's\nHauls")
            exclusiveGroup: egHaulGroup
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
        }
        TrawlBackdeckButton {
            text: qsTr("Leg's\nHauls")
            exclusiveGroup: egHaulGroup
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
        }
        TrawlBackdeckButton {
            text: qsTr("All\nHauls")
            exclusiveGroup: egHaulGroup
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
        }
    }

    TrawlBackdeckButton {
        text: qsTr("Done")
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        onClicked: screens.pop()
    }
}