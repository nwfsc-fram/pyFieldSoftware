import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 450
    height: 400
    title: "Change Mean Time Series"
    property string message: "Time Series"
    property string accepted_action: ""
    property alias btnSave: btnSave
    property alias btnCancel: btnCancel
    property string time_series: ""
    property int dropDownWidth: 300
    property variant timeSeriesCB: {"Depth": cbDepth,
                                "Doorspread": cbDoorspread,
                                "Latitude": cbLatitude,
                                "Longitude": cbLongitude,
                                "Net Height": cbNetHeight,
                                "Temperature": cbTemperature,
                                "Wingspread": cbWindspread}

    onRejected: {  }
    onAccepted: {  }

    function save_and_close() {
        save_changes();
        dlg.accept();
    }

    function save_changes() {
        var entries = {};
        for (var i in timeSeriesCB) {
            entries[i] = timeSeriesCB[i].currentText;
        }
        timeSeries.meansModel.update_model(entries);
    }

    function populate_combo_boxes(model_items) {
        var series = timeSeries.getMeanTypeTimeSeries();
        for (var i in series) {
            timeSeriesCB[i].model = series[i];
        }
        var index;
        for (var i in model_items) {
//            console.info('item: ' + model_items[i].meanType + ' > ' + model_items[i].timeSeries);
            index = timeSeriesCB[model_items[i].meanType].find(model_items[i].timeSeries);
            if (index != -1) {
                timeSeriesCB[model_items[i].meanType].currentIndex = index;
            }
        }
    }

    contentItem: Rectangle {
        color: "#eee"

        GridLayout {
            id: glChanges
            columnSpacing: 20
            rowSpacing: 20
            columns: 2
            rows: 7
            flow: GridLayout.TopToBottom
            anchors.top: parent.top
            anchors.topMargin: 20
            anchors.horizontalCenter: parent.horizontalCenter
            Label { text: qsTr("Depth"); }
            Label { text: qsTr("Doorspread"); }
            Label { text: qsTr("Latitude"); }
            Label { text: qsTr("Longitude"); }
            Label { text: qsTr("Net Height"); }
            Label { text: qsTr("Temperature"); }
            Label { text: qsTr("Wingspread"); }

            ComboBox {
                id: cbDepth
                model: ["Select Depth Signal"]
                Layout.preferredWidth: dropDownWidth
            } // cbDepth
            ComboBox {
                id: cbDoorspread
                model: ["Select Doorspread Signal"]
                Layout.preferredWidth: dropDownWidth
            } // cbDoorspread
            ComboBox {
                id: cbLatitude
                model: ["Select Latitude Signal"]
                Layout.preferredWidth: dropDownWidth
            } // cbLatitude
            ComboBox {
                id: cbLongitude
                model: ["Select Longitude Signal"]
                Layout.preferredWidth: dropDownWidth
            } // cbLongitude
            ComboBox {
                id: cbNetHeight
                model: ["Select Net Height Signal"]
                Layout.preferredWidth: dropDownWidth
            } // cbNetHeight
            ComboBox {
                id: cbTemperature
                model: ["Select Temperature Signal"]
                Layout.preferredWidth: dropDownWidth
            } // cbTemperature
            ComboBox {
                id: cbWindspread
                model: ["Select Wingspread Signal"]
                Layout.preferredWidth: dropDownWidth
            } // cbWingspread

        } // rlFilters

        RowLayout {
            id: rlButtons
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: glChanges.bottom
            anchors.topMargin: 40
            spacing: 20
            Button {
                id: btnSave
                text: "Save"
                onClicked: { save_changes() }
            } // btnSave
            Button {
                id: btnSaveAndClose
//                text: qsTr("\u0026")
                text: qsTr("Save && Close")
                onClicked: { save_and_close() }
            } // btnSaveAndClose
            Button {
                id: btnCancel
                text: "Cancel"
                onClicked: { dlg.reject() }
            } // btnCancel
        } // rwlButtons

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
}
