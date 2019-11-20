import QtQuick 2.4
import QtQuick.Dialogs 1.0
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.1
import QtQml.Models 2.2
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0

ApplicationWindow {
    title: "Settings"
    width: 1100
    height: 850
    visible: false

    property int pending_edits_row: -1
    property string pending_edits

    Component.onCompleted: {
        var index = settings.settingsModel.get_item_index("parameter", "Depth Output Serial Port Status");
        if (index != -1) {
            var status = settings.settingsModel.get(index).value;
            if (status == "On") {
                startSerialPortWriter()
            }
        }

        console.info("SettingsScreen.qml completed");
    }

    Connections {
        target: serialPortManager
        onExceptionEncountered: exceptionEncountered(com_port, msg, resolution, exception)
    } // serialPortManager.onExceptionEncountered

    function exceptionEncountered(com_port, msg, resolution, exception) {
        dlgOkay.title = "Serial Port Exception"
        dlgOkay.message = msg
        dlgOkay.value = com_port
        dlgOkay.action = "Please select a different COM port"
        dlgOkay.open()
    }

    function startSerialPortWriter() {
        var index = settings.settingsModel.get_item_index("parameter", "Depth Output Serial Port");
        var com_port = settings.settingsModel.get(index).value;

        index = settings.settingsModel.get_item_index("parameter", "Depth Output Serial Port Baud Rate");
        var baud_rate = settings.settingsModel.get(index).value;

        serialPortManager.stop_serial_port_writer(com_port);

        var item = {}
        item["status"] = "On"
        item["com_port"] = com_port;
        item["baud_rate"] = parseInt(baud_rate);

        settings.depthRebroadcastInfo = item
        serialPortManager.add_serial_port_writer(item);
        serialPortManager.start_serial_port_writer(com_port);
    }

    function stopSerialPortWriter() {
        var index = settings.settingsModel.get_item_index("parameter", "Depth Output Serial Port");
        var com_port = settings.settingsModel.get(index).value;

        var item = {}
        item["status"] = "Off"
        item["com_port"] = com_port;
        item["baud_rate"] = 9600;

        settings.depthRebroadcastInfo = item

        serialPortManager.stop_serial_port_writer(com_port);
    }

    Component {
        id: cpTextField
        TextField {
            width: parent.width
            anchors.verticalCenter: parent.verticalCenter
            text: value ? value : ""
            onTextChanged: {
                pending_edits_row = row;
                pending_edits = text;
            }
            onEditingFinished: {
                if ((text != "") & (text != value)) {
                    settings.settingsModel.update_row(row, text);
                    pending_edits_row = -1;
                }
            }
        }
    } // cpTextField
    Component {
        id: cpSwitch
        Switch {
            anchors.verticalCenter: parent.verticalCenter
            checked: value == "On" ? true : false
            onCheckedChanged: {
                value = checked ? "On" : "Off";
                if (settings.settingsModel.get(row).parameter == "Depth Output Serial Port Status") {
                    if (value == "On") {
                        startSerialPortWriter();
                    } else {
                        stopSerialPortWriter();
                    }
                }
                settings.settingsModel.update_row(row, value);
            }
        }
    } // cpSwitch
    Component {
        id: cpDialogListView
        TextField {
            width: parent.width
            anchors.verticalCenter: parent.verticalCenter
            text: value ? value : ""

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    this.cursorShape = Qt.IBeamCursor;
                    dlgListView.row = row;
                    dlgListView.lvModel = getModelType(row)
                    dlgListView.initial_value = text
                    var index = dlgListView.lvModel.get_item_index("displayText", text);
                    dlgListView.lvItems.positionViewAtIndex(index, ListView.Center)
                    dlgListView.lvItems.currentIndex = index;
                    dlgListView.open()
                }
            }
            onTextChanged: {
                pending_edits_row = row;
                pending_edits = text;
            }
            onEditingFinished: {
                if ((text != "") & (text != value)) {
                    settings.settingsModel.update_row(row, text);
                    pending_edits_row = -1;
                }
            }
        }
    } // cpDialogListView
    Component {
        id: cpComboBox
        ComboBox {

            // ToDo - Todd Hay - Fix the currentIndex and onCurrentIndexChanged code
            currentIndex: 0 //getCurrentIndex(model, value)
            enabled: false
            model: getModelType(row)
            onCurrentIndexChanged: {
                if (currentIndex != -1) {
//                    console.info('updating the cpComboBox because currentIndex is: ' + model.get(currentIndex).text);
//                    updateSetting(row, value);
                }
            }
        }
    } // cpComboBox
    Component {
        id: cpFolderBrowser
        RowLayout {
            width: parent.width
            spacing: 10
            TextField {
                id: tfFolderPath
                Layout.preferredWidth: 300
                Layout.preferredHeight: 30
                anchors.verticalCenter: parent.verticalCenter
                text: value ? value : ""
                onTextChanged: {
                    pending_edits_row = row;
                    pending_edits = text;
                }
                onEditingFinished: {
                    if ((text != "") & (text != value)) {
                        settings.settingsModel.update_row(row, text);
                        pending_edits_row = -1;
                    }
                }
            }
            Button {
                id: btnBrowse
                text: qsTr("Browse...")
                Layout.preferredWidth: 80
                onClicked: {
                    fileDialog.row = row;
                    fileDialog.open()
                }
            }
        }
    } // cpFolderBrowser

    onClosing: {
        if (pending_edits_row >= 0) {
            settings.settingsModel.update_row(pending_edits_row, pending_edits);
        }
    }

    function getDelegateType(index) {
        var type = tvSettings.model.get(index).delegate_type;
        switch (type) {
            case "TextField":
                return cpTextField;
                break;
            case "Switch":
                return cpSwitch;
                break;
            case "DialogListView":
                return cpDialogListView;
                break;
            case "ComboBox":
                return cpComboBox;
                break;
            case "DatePicker":

                break;
            case "FolderBrowser":
                return cpFolderBrowser;
                break;
            default:
                return cpTextField;
                break;
        }
    }

    function getModelType(index) {
        var type = tvSettings.model.get(index).model_type;
        switch (type) {
            case "Vessels":
                return settings.vesselsModel;
                break;
            case "Scientists":
                return settings.scientistsModel;
                break;
            case "Crew":
                return settings.crewModel;
                break;
            case "ComPorts":
                return settings.comPortsModel;
                break;
            case "BaudRates":
                return settings.baudRatesModel;
                break;
            default:
                return ["Empty Model"];
        }
    }

    function getCurrentIndex(model, value) {

        var index = 0;

        // TODO Todd - Return the current index of the given model based on the Settings Table/Model
        if ((value != "") & (value != undefined)) {
            index = model.get_item_index("text", value)
        }
        console.info('model: ' + model + ', value: ' + value + ', index: ' + index);
        return index;
    }

    function updateSetting(row, value) {
        settings.settingsModel.update_row(row, value);
    }

    Label {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 20
        id: lblInstructions
        text: qsTr("Change a pulldown or Tab out of a text field or hit Enter to save the parameter modification. " +
                    "Once the correct value appears in the Saved Value column then you know it has been saved.")
    } // lblInstructions
    TableView {
        id: tvSettings
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: lblInstructions.bottom
        anchors.topMargin: 20
        width: parent.width - 60
        height: parent.height - lblInstructions.height - 60
        selectionMode: SelectionMode.NoSelection

        model: settings.settingsModel

        rowDelegate: Rectangle {
            height: 30
            color: styleData.selected ? "#448" : (styleData.alternate? "#eee" : "#fff")
        }

        TableViewColumn {
            role: "parameter"
            title: "Parameter"
            width: 200
        } // parameter
        TableViewColumn {
            role: "value"
            title: "Saved Value"
            width: 300
            delegate: Item {
                Label {
                    anchors.verticalCenter: parent.verticalCenter
                    text: styleData.value ? styleData.value : ""
                }
            }
        } // value
        TableViewColumn {
            role: "new_value"
            title: "New Value"
            width: 300
            delegate: Component {
                Loader {
                    property int row: styleData.row
                    property string value: styleData.value ? styleData.value : ""
                    anchors.fill: parent
                    sourceComponent: getDelegateType(styleData.row)
                }
            }
        } // new_value
    }

    OkayDialog {
        id: dlgOkay
    }

    ListViewDialog {
        id: dlgListView
        title: "Select an Item"
        onAccepted: {
            console.info('updating the listview dialog')
            updateSetting(row, lvModel.get(lvItems.currentIndex).displayText)
            pending_edits_row = -1;

            if (settings.settingsModel.get(row).parameter.indexOf("Depth Output Serial Port") >= 0) {
                var index = settings.settingsModel.get_item_index("parameter", "Depth Output Serial Port Status")
                if (index != -1) {
                    var status = settings.settingsModel.get(index).value;
                    if (status == "On") {
                        startSerialPortWriter();
                    } else {
                        stopSerialPortWriter();
                    }
                }
            }
        }
        onRejected: {}
    }
    FileDialog {
        id: fileDialog
        title: "Please choose a folder"
        property url folderPath: "file:///C:"
        folder: folderPath
        selectFolder: true
        property int row: -1
        onAccepted: {
            var path = fileUrl.toString();
            path = path.replace(/^(file:\/{3})/,"");
            path = path.replace(/\/{1}/g, '\\');
            console.info('update the FileDialog path');
            updateSetting(row, path)
            pending_edits_row = -1;
//            Qt.quit()
        }
        onRejected: { }
    } // fileDialog
    Calendar {
        id: calDatePicker
        visible: false
    }
}