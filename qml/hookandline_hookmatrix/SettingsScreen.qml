
/*************************************************************************
Created by:     Jim Fellows (james.fellows@noaa.gov)
Created date:   20210908

Description:    Expose all parameters of Setting table to UI
                to allow user to manipulate for current vessel.  TableView
                can be edited via loaded delegate or via "Restore Defaults"
                button, which pulls settings from "DEFAULT_SETTINGS" table.
                Settings changes are not allowed with collected data in database.
                "Clean DB" functionality exists to allow user to clear out collected
                data. See https://github.com/nwfsc-fram/pyFieldSoftware/issues/259

TODO: Add editable tableview as common widget for sharing with CutterStation
**************************************************************************/

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.2

import "../common"

// TODO: consolidate this into a single QML widget in COMMON to share with HookMatrix

Item {
    Component.onDestruction: {
        smHookMatrix.to_sites_state()
    }
    ColumnLayout {  // layout for entire
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        anchors.topMargin: 10
        anchors.bottomMargin: 10

        RowLayout {
            id: rlTable
            BackdeckTableView {
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
                    width: tvSettings.viewport.width - colNewValue.width - colCurValue.width
                }
                TableViewColumn {
                    id: colCurValue
                    title: "Current Value"
                    role: "value"
                    movable: false
                    resizable: false
                    width: tvSettings.viewport.width / 3
                }
                TableViewColumn {
                    id: colNewValue
                    title: "New Value"
                    role: "value"
                    movable: false
                    resizable: false
                    width: tvSettings.viewport.width / 3
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
                            if (styleData.column === 2) {  // only allow new val col for edits
                                loader.visible = true
                                loader.item.forceActiveFocus()
                            }
                        }
                    }
                    Loader {
                        // editable overlay for column cell
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
                                Keys.onEscapePressed: loader.visible = false
                                onAccepted:{
                                    if (styleData.value !== text) {
                                        console.info("Parameter " + model.parameter + " being set to " + text + " from " + styleData.value)
                                        // pass param, old val, and new val to confirm db update
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
                OkayCancelDialog {
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
                        dlgUpdateParam.message = 'Changing "' + param + '":\n\n"' + oldVal + '" --> "' + newVal + '"\n'
                        dlgUpdateParam.open()
                    }
                    onAccepted: {
                        settings.updateDbParameter(param, newVal)  // this func updates db and model
                    }
                }
            }
        }
        RowLayout {  //row for buttons along bottom of table
            id: rlButtons
            anchors.right: parent.right
            anchors.left: parent.left
            BackdeckButton {
                anchors.left: parent.left
                text: qsTr("<<")
                implicitHeight: 60
                implicitWidth: 100
                onClicked: {
                    smHookMatrix.to_sites_state()
                }
            }
            RowLayout {
                anchors.horizontalCenter: parent.horizontalCenter
                BackdeckButton {
                    id: btnRestore
                    text: qsTr("Save\nDefaults")
                    enabled: cbVessels.currentText
                    txtColor: cbVessels.currentText ? 'green' : 'gray'
                    boldFont: cbVessels.currentText
                    implicitHeight: 60
                    onClicked: {
                        dlgDefaults.ask()
                    }
                    OkayCancelDialog {
                        id: dlgDefaults
                        title: "Restore Settings"
                        message: ""
                        function ask() {
                            message = "Restoring default settings\nfor " + cbVessels.currentText + " vessel"
                            dlgDefaults.open()
                        }
                        onAccepted: {
                            // TODO: Create DEFAULT_SETTINGS table to pull these from
                            var vesselName = cbVessels.currentText;
                            var paramName = 'FPC IP Address'
                            var fpcIp;
                            switch (vesselName) {
                                case 'Aggressor':
                                    fpcIp = '192.254.241.5';
                                    break;
                                case 'Mirage':
                                    fpcIp = '192.254.242.5';
                                    break;
                                case 'Toronado':
                                    fpcIp = '192.254.243.5';
                                    break
                                default:
                                    fpcIp = '192.254.241.5';
                                    break
                            }
                            settings.updateDbParameter(paramName, fpcIp)  // this func updates db and model
                        }
                    }
                }
                FramComboBox {
                    // TODO: Pull these from DEFAULT_SETTINGS table
                    id: cbVessels
                    model: ['', 'Mirage', 'Aggressor', 'Toronado']
                    implicitWidth: 250
                    implicitHeight: 60
                    dropdownfontsize: 32
                }
            }
            RowLayout {
                id: rlPrintTest
                spacing: 10
                anchors.right: rlButtons.right
                BackdeckButton {
                    id: printBowTest
                    text: qsTr("Print Bow\nTest")
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 60
                    onClicked: {
                        printTest("bow");
                    }
                } // printBowTest
                BackdeckButton {
                    id: printAftTest
                    text: qsTr("Print Aft\nTest")
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 60
                    onClicked: {
                        printTest("aft");
                    }
                } // printAftTest
            }
        }
    }
    function printTest(printer) {
        var equipment = "";
        switch (printer) {
            case "bow":
                equipment = "Zebra Printer Bow";
                break;
            case "aft":
                equipment = "Zebra Printer Aft";
                break;
        }
        labelPrinter.printADHLabel(equipment, "A", "1", "1", "Test Species");
    }
    OkayDialog {
        // message when killing app during reboot
        id: dlgReboot
        message: ""
        onAccepted: {
            stateMachine.exitApp()
        }
            Connections {
                target: settings
                onRebootRequired: {
                    dlgReboot.message = param + " value has changed"
                    dlgReboot.action = "HookMatrix reboot required."
                    dlgReboot.open()
                }
            }
    }
}