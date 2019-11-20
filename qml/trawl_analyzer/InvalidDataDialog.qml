import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 600
    height: 800
    title: "Time Series Data Points"
    property string message: "Time Series Data Points"
    property string accepted_action: ""
    property alias btnSave: btnSave
    property alias btnCancel: btnCancel
    property string time_series: ""

    onRejected: {  }
    onAccepted: {  }

    function save_and_close() {
        save_changes();
        dlg.accept();
    }

    function save_changes() {
        timeSeries.dataPointsModel.save_validity_changes();
    }

    contentItem: Rectangle {
        color: "#eee"
        Label {
            id: lblTimeSeries
            y: 10
            anchors.horizontalCenter: parent.horizontalCenter
            text: time_series
            font.weight: Font.Bold
            font.pixelSize: 16
        } // lblTimeSeries
        RowLayout {
            id: rlFilters
            spacing: 10
            anchors.top: lblTimeSeries.bottom
            anchors.topMargin: 20
            anchors.left: parent.left
            anchors.leftMargin: 30
//            anchors.right: parent.right
//            anchors.rightMargin: 10
            Button {
                id: btnToggleChange
                text: qsTr("Toggle Change")
                onClicked: {
                    var value;
                    var new_value;
                    tvDataPoints.selection.forEach( function(rowIndex) {
                        if (rowIndex != -1) {
                            value = timeSeries.dataPointsModel.get(rowIndex).change;
                            new_value = value == "" ? "Yes" : ""
                            timeSeries.dataPointsModel.setProperty(rowIndex, "change", new_value);
                        }
                    })
                }
            } // btnToggleChange
            Label { Layout.preferredWidth: 230 }
            Label {
                id: lblFilters
                text: qsTr("Filters")
            } // lblFilters
            Button {
                id: btnValid
                text: qsTr("Valid")
                checkable: true
                checked: false
                onClicked: {
                    timeSeries.dataPointsModel.filter_values("valid", checked);
                }
            } // btnValid
            Button {
                id: btnInvalid
                text: qsTr("Invalid")
                checkable: true
                checked: true
                onClicked: {
                    timeSeries.dataPointsModel.filter_values("invalid", checked);
                }
            } // btnInvalid
        } // rlFilters
        TableView {
            id: tvDataPoints
            anchors.top: rlFilters.bottom
            anchors.topMargin: 20
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * 0.9
            height: parent.height * 0.8
            model: timeSeries.dataPointsModel
            selectionMode: SelectionMode.ExtendedSelection
            TableViewColumn {
                role: "id"
                title: "ID"
                width: 100
            } // id
            TableViewColumn {
                role: "datetime"
                title: "Date/Time"
                width: 180
            } // datetime
            TableViewColumn {
                role: "reading_numeric"
                title: "Data Value"
                width: 120
                delegate: Text {
                    text: styleData.value ?
                        (((time_series.indexOf("Latitude") >= 0) || (time_series.indexOf("Longitude") >=0))
                                ? styleData.value.toFixed(6) : styleData.value.toFixed(1) ) : ""
                    color: styleData.textColor
                    elide: styleData.elideMode
                    renderType: Text.NativeRendering
                }

            } // reading_numeric
            TableViewColumn {
                role: "status"
                title: "Status"
                width: 60
                delegate: Text {
                    text: styleData.value ? "Invalid" : "Valid"
                    color: styleData.value ? "red" : styleData.textColor
                    font.weight: styleData.value ? Font.Bold : Font.Normal
//                    color: styleData.textColor
                    elide: styleData.elideMode
                    renderType: Text.NativeRendering
                }
            } // status
            TableViewColumn {
                role: "change"
                title: "Change?"
                width: 60
            } // change

            onDoubleClicked: {
                var value;
                var new_value;
                tvDataPoints.selection.forEach( function(rowIndex) {
                    if (rowIndex != -1) {
                        value = timeSeries.dataPointsModel.get(currentRow).change;
                        new_value = value == "" ? "Yes" : ""
                        timeSeries.dataPointsModel.setProperty(currentRow, "change", new_value);
                    }
                })
            }
        } // tvDataPoints
        RowLayout {
            id: rwlButtons
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: tvDataPoints.bottom
            anchors.topMargin: 20
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
