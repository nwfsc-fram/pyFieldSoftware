import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

Dialog {
    id: dlg
    width: 670
    height: 550
    title: "Serial Port Manager"

    onRejected: {  }
    onAccepted: {  }

    function togglePort() {
        if (tvComports.currentRow !== -1) {
            var item = tvComports.model.get(tvComports.currentRow);
            var comport = item.comPort;
            var status = item.status;
            if (status === "Stopped") {
                serialPortManager.start_thread(comport);
            } else {
                serialPortManager.stop_thread(comport);
            }
        }
    }

    contentItem: Rectangle {
        color: "#eee"
        BackdeckTableView {
            id: tvComports
            width: 650
            height:400
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 20
            selectionMode: SelectionMode.SingleSelection
            headerVisible: true
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

            onDoubleClicked: {
                togglePort();
            }
            model: serialPortManager.serialPortsModel

            TableViewColumn {
                role: "equipment"
                title: "Equipment"
                width: 180
            } // equipmentName
            TableViewColumn {
                role: "station"
                title: "Station"
                width: 130
            } // station
            TableViewColumn {
                role: "comPort"
                title: "COM Port"
                width: 110
            } // comPort
            TableViewColumn {
                role: "baudRate"
                title: "Baud Rate"
                width: 110
            } // baudRate
            TableViewColumn {
                role: "status"
                title: "Status"
                width: 100
            } // status

        }
        RowLayout {
            id: rwlButtons
            anchors.horizontalCenter: parent.horizontalCenter
            y: dlg.height - this.height - 20
            spacing: 20
            BackdeckButton {
                id: btnToggle
                text: "Toggle\nPort"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                state: tvComports.currentRow != -1 ? "enabled" : "disabled"
                onClicked: {
                    togglePort()
                }
            } // btnToggle
            BackdeckButton {
                id: btnEdit
                text: "Edit\nPort"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
//                state: tvComports.currentRow != -1 ? "enabled" : "disabled"
                state: "disabled"
                onClicked: {
                    var item = tvComports.model.get(tvComports.currentRow);
                    var comport = item.comPort;
                    var status = item.status;
                    if (status === "Started") {
                        serialPortManager.stop_thread(comport);
                    }
                    console.info('build editing dialog');

                }
            } // btnEdit
            BackdeckButton {
                id: btnClose
                text: "Close"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.reject() }
            } // btnClose
        } // rwlButtons

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject() // especially necessary on Android
    }
}
