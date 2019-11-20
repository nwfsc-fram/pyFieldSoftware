import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.2
import QtQml.Models 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 700
    height: 500
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "Add COM Port"

//    property int screen_id: -1
    property string message: ""
    property string action: ""
    property string accepted_action: ""
//    property string screen: ""
    property int equipment_id: -1

    property string active_test_com_port: ""

    property string com_port: ""
    property int baud_rate: 9600
    property int data_bits: 8
    property string parity: "None"
    property double stop_bits: 1
    property string flow_control: "None"

    property alias tvComport: tvComport
    property alias tvEquipment: tvEquipment
    property alias tvMoxaport: tvMoxaport

    onRejected: {  }
    onAccepted: {  }

    onVisibleChanged: {
        // Highlight/select the provided com_port
        if ((com_port != "") & (visible)) {
            var index = tvComport.model.get_item_index("com_port", com_port);
            if (index != -1) {
                tvComport.selection.select(index)
                tfComport.text = com_port
            }
        }
    }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        ColumnLayout {
            y: 20
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 20
            GridLayout {
                id: gridHeader
                anchors.horizontalCenter: parent.horizontalCenter
                y: 20
                columns: 3
                rows: 3
                columnSpacing: 40
                rowSpacing: 10
                flow: GridLayout.LeftToRight

                Label {
                    id: lblEquipment
                    text: qsTr("Equipment")
                } // lblEquipment
                Label {
                    id: lblComport
                    text: qsTr("COM Port")
                } // lblComport
                Label {
                    id: lblMoxaport
                    text: qsTr("Moxa Port")
                } // lblMoxaport
                TableView {
                    id: tvEquipment
                    TableViewColumn {
                        role: "equipment"
                        title: ""
                    }
                    TableViewColumn {
                        role: "equipment_type"
                        title: ""
                    }
                    Layout.preferredWidth: 350
                    Layout.preferredHeight: 300
                    model: sensorDataFeeds.equipmentModel
                    headerVisible: false
                    onClicked: {
                        tfEquipment.text = model.get(currentRow).equipment;
                        equipment_id = model.get(currentRow).equipment_id;
                    }
                    selection.onSelectionChanged: {
                        if (currentRow != -1) {
                            tfEquipment.text = model.get(currentRow).equipment;
                            equipment_id = model.get(currentRow).equipment_id;
                        } else {
                            tfEquipment.text = "";
                        }
                    }
                } // tvEquipment
                TableView {
                    id: tvComport
                    TableViewColumn {
                        role: "com_port"
                        title: ""
                    }
                    Layout.preferredWidth: 100
                    Layout.preferredHeight: 300
                    model: sensorDataFeeds.comportModel
                    headerVisible: false
                    onClicked: {
                        tfComport.text = model.get(currentRow).com_port;
                    }
                    selection.onSelectionChanged: {
                        tfComport.text = (currentRow != -1) ? model.get(currentRow).com_port : "";
                    }
                } // tvComport
                TableView {
                    id: tvMoxaport
                    TableViewColumn {
                        role: "moxaport"
                        title: ""
                    }
                    Layout.preferredWidth: 100
                    Layout.preferredHeight: 300
                    model: (Array.apply(0, Array(8)).map(function (x,y) {return y+1})).map(String)
                    headerVisible: false
                    onClicked: {
                        tfMoxaport.text = model.toString().split(',')[currentRow];
                    }
                    selection.onSelectionChanged: {
                        tfMoxaport.text = (currentRow != -1) ? model.toString().split(',')[currentRow] : "";
                    }
                } // tvMoxaport
                TextField {
                    id: tfEquipment
                    text: ""
                    Layout.preferredWidth: 350
                    readOnly: true
                } // tfEquipment
                TextField {
                    id: tfComport
                    text: ""
                    Layout.preferredWidth: 100
                    readOnly: true
                } // tfComport
                RowLayout {
                    id: rwlMoxaport
                    TextField {
                        id: tfMoxaport
                        text: ""
                        Layout.preferredWidth: 50
                        readOnly: true
                    } // tfMoxaport
                    Button {
                        text: qsTr("Clear")
                        Layout.preferredWidth: 50
                        onClicked: {
                            tfMoxaport.text = ""
                        }
                    }
                } // rwlMoxaport

            } // gridHeader
            Button {
                id: btnAdd
                text: "Add"
                anchors.horizontalCenter: parent.horizontalCenter
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: {
                    if ((tfEquipment.text != null) & (tfComport.text != null)) {

                        if ((sensorDataFeeds.sensorConfigurationModel.get_item_index("com_port", tfComport.text) >= 0) ||
                            (active_test_com_port == tfComport.text)) {
                            dlgOkay.message = "You selected an already used COM port, " +
                                                "please select another:\n\n" + tfComport.text
                            dlgOkay.open()
                        } else {
                            var moxa_port = (tfMoxaport.text != null) ? parseInt(tfMoxaport.text) : null
                            sensorDataFeeds.sensorConfigurationModel.add_row(equipment_id,
                                tfEquipment.text, tfComport.text, moxa_port,
                                baud_rate, data_bits, parity, stop_bits, flow_control)
                        }
                    }
                }
            } // btnAdd
            Label { text: ""}
            Button {
                id: btnClose
                text: "Close"
                anchors.horizontalCenter: parent.horizontalCenter
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.accept() }
            } // btnClose
        }

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }

    OkayDialog { id: dlgOkay }
}
