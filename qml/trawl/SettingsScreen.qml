
/*************************************************************************
Created by:     Jim Fellows (james.fellows@noaa.gov)
Created date:   20210607

Description:    Expose all parameters of Setting table to UI
                to allow user to manipulate for current vessel.  TableView
                can be edited via loaded delegate or via "Restore Defaults"
                button, which pulls settings from "DEFAULT_SETTINGS" table.
                Settings changes are not allowed with collected data in database.
                "Clean DB" functionality exists to allow user to clear out collected
                data.

**************************************************************************/

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.2

import "../common"

Item {
    Component.onDestruction: {
        tbdSM.to_home_state()
    }
    ColumnLayout {  // layout for entire
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        anchors.topMargin: 10
        anchors.bottomMargin: 10

        RowLayout {
            id: rlTable
            TrawlBackdeckTableView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                // editable tableview: https://stackoverflow.com/questions/43273240/how-to-make-a-cell-editable-in-qt-tableview
                // review this thread to understand how to update model
                // https://www.qtcentre.org/threads/68074-Tabview-update-after-the-model-data-changes

                id: tvSettings
                model: settings.model
                horizontalScrollBarPolicy: -1
                selectionMode: SelectionMode.SingleSelection

                TableViewColumn {
                    id: colParameter
                    title: "Parameter"
                    role: "parameter"
                    movable: false
                    resizable: false
                    width: tvSettings.viewport.width - colValue.width
                }

                TableViewColumn {
                    id: colValue
                    title: "Value"
                    role: "value"
                    movable: false
                    resizable: false
                    width: tvSettings.viewport.width / 2
                }

                itemDelegate: Rectangle {
                    Text {
                        anchors { verticalCenter: parent.verticalCenter; left: parent.left }
                        color: "black"
                        text: styleData.value
                        font.pixelSize: 18
                    }

                    MouseArea {
                        id: cellMouseArea
                        anchors.fill: parent
                        onClicked: {
                            // Column index are zero based
                            if (stateMachine.haulCount) {
                                dlgPreventEdit.open()
                            } else if (styleData.column === 1){
                                loader.visible = true
                                loader.item.forceActiveFocus()
                            }
                        }
                    }
                    Loader {
                        id: loader
                        anchors { verticalCenter: parent.verticalCenter; left: parent.left}
                        height: parent.height
                        width: parent.width
                        visible: false
                        sourceComponent: visible ? input : undefined


                        Component {
                            id: input
                            TextField {
                                anchors { fill: parent }
                                text: ""
                                font.pixelSize: 18
                                textColor: "Green"
                                onAccepted:{
                                    if (styleData.value !== text) {
                                        console.info("Parameter " + model.parameter + " being set to " + text + " from " + styleData.value)
                                        dlgUpdateParam.confirm(model.parameter, text, styleData.value)
                                    }
                                    loader.visible = false
                                }

                                onActiveFocusChanged: {
                                    if (!activeFocus) {
                                        loader.visible = false
                                    }
                                }
                            }
                        }
                    }
                }
                TrawlConfirmDialog {
                    id: dlgUpdateParam
                    message: ""
                    property string param: "";
                    property string oldVal: "";
                    property string newVal: "";

                    height: 250
                    width: 700
                    function confirm(p, nv, ov) {
                        param = p;
                        newVal = nv;
                        oldVal = ov;
                        // TODO move this outside to actual value change
                        tvSettings.model.setProperty(tvSettings.currentRow, "value", newVal)
                        settings.updateDbParameter(param, newVal)
                        dlgUpdateParam.message = 'Changing "' + param + '":\n\n"' + oldVal + '" --> "' + newVal + '"\n'
                        dlgUpdateParam.open()
                    }
                    onRejected: {
                        console.info("Param change reverted, setting " + param + " back to " + oldVal)
                        tvSettings.model.setProperty(tvSettings.currentRow, "value", oldVal)
                        settings.updateDbParameter(param, oldVal)
                    }
                }
            }
        }
        RowLayout {  //row for buttons along bottom of table
            id: rlButtons
            anchors.right: parent.right
            anchors.left: parent.left
            TrawlBackdeckButton {
                anchors.left: parent.left
                text: qsTr("<<")
                implicitHeight: 60
                implicitWidth: 100
                onClicked: screens.pop()
            }
            RowLayout {
                anchors.horizontalCenter: parent.horizontalCenter
                TrawlBackdeckButton {
                    id: btnRestore
                    text: qsTr("Restore\nDefaults")

                    implicitHeight: 60
                    onClicked: {
                        if (stateMachine.haulCount) {
                            dlgPreventEdit.open()
                        } else {
                            dlgDefaults.ask()
                        }
                    }
                    TrawlConfirmDialog {
                        id: dlgDefaults
                        title: "Restore Settings"
                        message: ""
                        function ask() {
                            message = "Restoring default settings\nfor " + cbVessels.currentText + " vessel"
                            dlgDefaults.open()
                        }
                        onAccepted: {
                            settings.restoreDefaultSettings(cbVessels.currentText)
                        }
                    }
                }
                FramComboBox {
                    id: cbVessels
                    model: ['Blue', 'Orange']
                    implicitWidth: 250
                    implicitHeight: 60
                }
            }
            TrawlBackdeckButton {
                text: qsTr("Clean\nDB")
                anchors.right: parent.right
                implicitHeight: 60
                onClicked: {
                    if (stateMachine.haulCount) {
                        console.info("Cleaning DB")
                        soundPlayer.playSound("cleanDB", 0, false)
                        dlgCleanDB.open()
                    } else {
                        dlgNoRecords.open()
                    }
                }
                TrawlConfirmDialog {
                    id: dlgCleanDB
                    title: "Warning!"
                    message: "WARNING! You are you about clear\ncollected data from the following\ntrawl_backdeck.db tables:
                            \n    HAULS: " + stateMachine.countTableRows("Hauls") +
                            "\n    CATCH: " + stateMachine.countTableRows("Catch") +
                            "\nSPECIMEN: " + stateMachine.countTableRows("Specimen") +
                            "\n    NOTES: " + stateMachine.countTableRows("Notes")
                    height: 400
                    onAccepted: {
                        dlgDoubleCheck.open()
                    }
                }
                TrawlOkayDialog {
                    id: dlgNoRecords
                    title: "Note"
                    message: "Database already clean."
                }
                TrawlConfirmDialog {
                    id: dlgDoubleCheck
                    title: "Warning!"
                    message: "Sure you don't need to backup any data?\nAll data will be lost at sea :("
                    height: 300
                    onAccepted: {
                        stateMachine.cleanDB()
                        haulSelection._get_hauls_from_db('all')
                    }
                }
            }
        }
    }
    TrawlOkayDialog {
        id: dlgPreventEdit
        title: "Warning"
        height: 300
        message: "Collected data exists, unable to update settings:" + "\n\nHaul Count: " + stateMachine.haulCount +
            "\n\nPlease backup any necessary data and clean database."
    }
}