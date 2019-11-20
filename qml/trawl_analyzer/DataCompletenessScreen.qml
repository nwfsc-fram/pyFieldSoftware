import QtQuick 2.5
import QtQuick.Controls 1.5
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0
import SortFilterProxyModel 0.1

import "../common"

Item {
    id: itmDataCompleteness
    anchors.fill: parent

    property bool canLoad: false

    Connections {
        target: dataCompleteness
        onHaulLoaded: haulLoaded(index, loadDate);
    } // onHaulLoaded

    Connections {
        target: dataCompleteness
        onLoadingFinished: haulLoadingFinished(status, msg);
    } // onLoadingFinished

    Connections {
        target: dataCompleteness
        onHaulSensorSerialDataLoaded: haulSensorSerialDataLoaded(index, loadDate);
    } // onHaulSensorSerialDataLoad

//    Connections {
//        target: dataCompleteness
//        onSensorSerialLoadingFinished: sensorSerialLoadingFinished(status, msg);
//    } // onSensorSerialLoadingFinished

    Connections {
        target: dataCompleteness
        onSensorFileLoadingFinished: sensorFileLoadingFinished(status, msg);
    } // onSensorFileLoadingFinished

    Connections {
        target: dataCompleteness
        onHaulSensorFileDataLoaded: haulSensorFileDataLoaded(index, loadDate);
    }

    Connections {
        target: tvDataCompleteness.selection
        onSelectionChanged: changeToggleButtonStatus()
    } // onSelectionChanged

    Connections {
        target: dataCompleteness
        onShowMessage: displayMessage(job, status, msg)
    }

    Connections {
        target: dataCompleteness
        onHaulDataRemoved: removeHaul(index)
    }

    function removeHaul(index) {
        tvDataCompleteness.model.setProperty(index, "opsLoadStatus", "");
        tvDataCompleteness.model.setProperty(index, "sensorsLoadStatus", "");
        tvDataCompleteness.model.setProperty(index, "catchLoadStatus", "");
    }

    function changeToggleButtonStatus() {
        btnToggle.enabled = (tvDataCompleteness.selection.count > 0) ? true : false;
    }

    function displayMessage(job, status, msg) {
        dlgOkay.message = (status) ? job + "Success" : job + "Failed"
        dlgOkay.message = dlgOkay.message + '\n\n' + msg
        dlgOkay.open()
        canLoad = true;
        settings.isLoading = false;
    }

    function sensorFileLoadingFinished(status, msg) {
        var str = "Haul Sensor Data Loading Finished: "
        dlgOkay.message = (status) ? str + "Success" : str + "Failed"
        dlgOkay.message = dlgOkay.message + '\n\n' + msg
        dlgOkay.open()
        canLoad = true;
        settings.isLoading = false;
    }

    function haulSensorSerialDataLoaded(index, loadDate) {
        // This function is called once a haul has been successfully loaded to update the TableView with the date/time
        // of the load
//        console.info('index, loadDate: ' + index + ', ' + loadDate);
        tvDataCompleteness.model.setProperty(index, "sensorsLoadStatus", loadDate);
    }

    function haulSensorFileDataLoaded(index, loadDate) {
        console.info('updated: ' + index + ', ' + loadDate);
        tvDataCompleteness.model.setProperty(index, "sensorsLoadStatus", loadDate);
    }

    function haulLoadingFinished(status, msg) {
        var str = "Haul Loading Finished: "
        dlgOkay.message = (status) ? str + "Success" : str + "Failed"
        dlgOkay.message = dlgOkay.message + '\n\n' + msg
        dlgOkay.open()
        canLoad = true;
        settings.isLoading = false;
    }

    function haulLoaded(index, loadDate) {
        // This function is called once a haul has been successfully loaded to update the TableView with the date/time
        // of the load
//        console.info('index, loadDate: ' + index + ', ' + loadDate);
        tvDataCompleteness.model.setProperty(index, "opsLoadStatus", loadDate);
    }

    function toggleLoadValues() {
        var item, value;
        tvDataCompleteness.selection.forEach(
            function(rowNum) {
//                item = tvDataCompleteness.model.source.get(rowNum);
                item = tvDataCompleteness.model.get(rowNum);
                if (item.haul.indexOf("t") == -1) {
                    value = (item.load == "yes") ? "no" : "yes";
//                    tvDataCompleteness.model.source.setProperty(rowNum, "load", value);
                    tvDataCompleteness.model.setProperty(rowNum, "load", value);
                }
            }
        )
        var idx = tvDataCompleteness.model.get_item_index("load", "yes")
        canLoad = (idx == -1) ? false : true
    }

    RowLayout {
        id: rwlTools
        width: parent.width
        x: 20
        y: 20
        spacing: 20
        Button {
            id: btnToggle
            text: qsTr("Toggle")
            enabled: false
            onClicked: {
                toggleLoadValues()
            }
        } // btnToggle
        Button {
            id: btnSelectAll
            text: qsTr("Select All")
            onClicked: {
                if (text == "Select All") {
                    dataCompleteness.dataCheckModel.selectAll();
                    canLoad = true;
                    text = "Deselect All";
                } else {
                    dataCompleteness.dataCheckModel.deselectAll();
                    canLoad = false;
                    text = "Select All";
                }
            }
        } // btnSelectAll
        Button {
            id: btnLinkTows
            text: qsTr("Link Tows")
            enabled: false
            onClicked: {
                var indexes = [];
                tvDataCompleteness.selection.forEach(
                    function(rowNum) {
                        indexes.push(rowNum);
                    }
                )

                if (text == qsTr("Link Tows")) {
                    if (indexes.length == 2) {
                        var item1 = tvDataCompleteness.model.get(indexes[0]);
                        var item2 = tvDataCompleteness.model.get(indexes[1]);

                        var index;

                        // Remove any existing links for item1 or item2
                        if ((item1.linked != "") & (item1.linked != null)) {
                            index = tvDataCompleteness.model.get_item_index("linked", item1.haul);
                            tvDataCompleteness.model.setProperty(index, "linked", null);
                        }
                        if ((item2.linked != "") & (item2.linked != null)) {
                            index = tvDataCompleteness.model.get_item_index("linked", item2.haul);
                            tvDataCompleteness.model.setProperty(index, "linked", null);
                        }
                        // TODO Todd Hay - Need to update the database if the hauls have actually been already loaded

                        tvDataCompleteness.model.setProperty(indexes[0], "linked", item2.haul);
                        tvDataCompleteness.model.setProperty(indexes[1], "linked", item1.haul);
                        text = qsTr("Unlink Tows")
                    }
                } else if (text == qsTr("Unlink Tows")) {
                    var value, idx;
                    for (var i=0; i<indexes.length; i++) {
                        value = tvDataCompleteness.model.get(indexes[i]).linked;
                        idx = tvDataCompleteness.model.get_item_index("haul", value);
                        tvDataCompleteness.model.setProperty(idx, "linked", null);
                        tvDataCompleteness.model.setProperty(indexes[i], "linked", null);
                    }
                    text = qsTr("Link Tows")
                }
            }
        } // btnLinkTows
        Item { Layout.preferredWidth: 100}
        Button {
            id: btnLoadHauls
            text: qsTr("Load Hauls")
            enabled: !settings.isLoading
            onClicked: {
                settings.isLoading = true;
                canLoad = false;
                var item;
                var items = tvDataCompleteness.model.items
                var yesItems = {};
                for (var i=0; i<items.length; i++) {
                    item = items[i]
                    if (item.load == "yes")
                        yesItems[i] = item;
//                        yesItems.push({i: item});
//                        yesItems.push({"index": i, "item": item});
                }
                dataCompleteness.load_hauls(yesItems);
            }
        } // btnLoadHauls
        Button {
            id: btnLoadNewSensorData
            text: qsTr("Load New Sensor Data")
            enabled: !settings.isLoading
            onClicked: {
                settings.isLoading = true;
                canLoad = false;
                var item;
                var items = tvDataCompleteness.model.items
                var yesItems = {};
                for (var i=0; i<items.length; i++) {
                    item = items[i]
                    if (item.load == "yes") {
//                        if ((item.sensorDatabase == "") || (item.sensorDatabase == null)) {
//                            dlgOkay.message = "You are attempting to load sensor data for hauls\nwith no associated sensors databases.\n\n" +
//                                "Please add an appropriate sensor database."
//                            dlgOkay.open()
//                            canLoad = true;
//                            return;
//                        }
                        if ((item.sensorDatabase != "") & (item.sensorDatabase != null)) {
                            yesItems[i] = item;
                        }
                    }
                }
                dataCompleteness.load_sensor_data("load new", yesItems);
            }
        } // btnLoadNewSensorData
        Button {
            id: btnReloadSensorData
            text: qsTr("Reload Sensor Data")
            enabled: !settings.isLoading
            onClicked: {
                settings.isLoading = true;
//                canLoad = false;
                var item;
                var items = tvDataCompleteness.model.items
                var yesItems = {};
                for (var i=0; i<items.length; i++) {
                    item = items[i]
                    if (item.load == "yes") {
//                        if ((item.sensorDatabase == "") || (item.sensorDatabase == null)) {
//                            dlgOkay.message = "You are attempting to load sensor data for hauls\nwith no associated sensors databases.\n\n" +
//                                "Please select an appropriate sensor database."
//                            dlgOkay.open()
//                            canLoad = true;
//                            return;
//                        }
                        if ((item.sensorDatabase != "") & (item.sensorDatabase != null)) {
                            yesItems[i] = item;
                        }
                    }
                }
                dataCompleteness.load_sensor_data("reload", yesItems);
            }
        } // btnReloadSensorData
        Button {
            id: btnRemoveHaulSensor
            text: qsTr("Remove Haul + Sensor")
            enabled: !settings.isLoading
            onClicked: {
                dlgOkayCancel.message = "You are about to delete these hauls and their sensor data.\n\nDo you wish to proceed?";
                dlgOkayCancel.actionType = "removeHaulSensor";
                dlgOkayCancel.open();

            }
        } // btnRemoveHaulSensor
        Button {
            id: btnLoadCatch
            text: qsTr("Load Catch")
            enabled: !settings.isLoading
//            onClicked: {
//                settings.isLoading = true;
//            }
        } // btnLoadCatch
        Item { Layout.fillWidth: true }
        Button {
            id: btnStopProcessing
            anchors.right: parent.right
            anchors.rightMargin: 40
            text: qsTr("Stop Processing")
            enabled: true
            onClicked: {
                dlgOkayCancel.message = "You are about to cancel the data loading.\n\nDo you wish to cancel it?";
                dlgOkayCancel.actionType = "stopProcessing";
                dlgOkayCancel.open();
            }
        } // btnStopProcessing
    }

    SortFilterProxyModel {
        id: proxyModel
        source: dataCompleteness.dataCheckModel
        sortOrder: tvDataCompleteness.sortIndicatorOrder
        sortCaseSensitivity: Qt.CaseInsensitive
        sortRole: tvDataCompleteness.getColumn(tvDataCompleteness.sortIndicatorColumn).role
    }

    TableView {
        id: tvDataCompleteness
        anchors.top: rwlTools.bottom
        anchors.topMargin: 20
        anchors.left: parent.left
        anchors.right: parent.right
//        anchors.rightMargin: 20
        anchors.bottom: parent.bottom
//        anchors.bottomMargin: 20
        selectionMode: SelectionMode.ExtendedSelection

        model: dataCompleteness.dataCheckModel
//        model: proxyModel
//        sortIndicatorVisible: true

        TableViewColumn {
            title: "Load"
            role: "load"
            width: 35
        } // load
        TableViewColumn {
            title: "Haul Load Status"
            role: "opsLoadStatus"
            width: 100
        } // opsLoadStatus
        TableViewColumn {
            title: "Catch Load Status"
            role: "catchLoadStatus"
            width: 100
        } // catchLoadStatus
        TableViewColumn {
            title: "Sensor Load Status"
            role: "sensorsLoadStatus"
            width: 100
        } // sensorsLoadStatus
        TableViewColumn {
            title: "Linked"
            role: "linked"
            width: 40
        } // linked
        TableViewColumn {
            title: "Haul"
            role: "haul"
            width: 100
        } // haul
        TableViewColumn {
            title: "Haul Start"
            role: "haulStart"
            width: 100
        } // haulStart
        TableViewColumn {
            title: "Haul End"
            role: "haulEnd"
            width: 100
        } // haulEnd
        TableViewColumn {
            title: "Haul Database"
            role: "haulDatabase"
            width: 100
            delegate: Text {
                // Reference: http://stackoverflow.com/questions/423376/how-to-get-the-file-name-from-a-full-path-using-javascript
                text: styleData.value  ? styleData.value.replace(/^.*[\\\/]/, '') : ""
                color: styleData.textColor
                elide: styleData.elideMode

                // Reference:  NativeText.qml, found via everything desktop search
                renderType: Text.NativeRendering
            }
        } // haulDatabase
        TableViewColumn {
            title: "Catch Database"
            role: "catchDatabase"
            width: 100
            delegate: Text {
                text: styleData.value  ? styleData.value.replace(/^.*[\\\/]/, '') : ""
                color: styleData.textColor
                elide: styleData.elideMode
                renderType: Text.NativeRendering
            }
        } // database
        TableViewColumn {
            title: "Sensors Database"
            role: "sensorDatabase"
            width: 100
            delegate: Text {
                text: styleData.value  ? styleData.value.replace(/^.*[\\\/]/, '') : ""
                color: styleData.textColor
                elide: styleData.elideMode
                renderType: Text.NativeRendering
            }
        } // sensorDatabase
        TableViewColumn {
            title: "Haul Perf"
            role: "haulPerformance"
            width: 80
        } // haulPerformance
        TableViewColumn {
            title: "# Species"
            role: "catchSpeciesCount"
            width: 60
        } // catchSpeciesCount
        TableViewColumn {
            title: "# Specimens"
            role: "specimenCount"
            width: 70
        } // specimenCount
        TableViewColumn {
            title: "# 0 Basket Weight"
            role: "zeroBasketWeightCount"
            width: 90
        } // zeroBasketWeightCount

        onClicked: {
            var linkStatus = model.get(currentRow).linked;
            btnLinkTows.enabled = ((selection.count == 2) || ((selection.count == 1) &
                                                                ((linkStatus != "") & (linkStatus != null))))
            btnLinkTows.text = ((linkStatus != "") & (linkStatus != null)) ? "Unlink Tows" : "Link Tows"
        }
        onDoubleClicked: {
            toggleLoadValues()
        }

    } // tvDataCompleteness

    FramDesktopOkayDialog { id: dlgOkay }
    FramDesktopOkayCancelDialog {
        id: dlgOkayCancel
        property string actionType: ""
        onAccepted: {
            switch (actionType) {
                case "stopProcessing":
                    dataCompleteness.stop_data_loading();
                    break;

                case "removeHaulSensor":
                    settings.isLoading = true;
                    var item;
                    var items = tvDataCompleteness.model.items
                    var yesItems = {};
                    for (var i=0; i<items.length; i++) {
                        item = items[i]
                        if (item.load == "yes") {
                            yesItems[i] = item;
                        }
                    }
                    dataCompleteness.removeHaulSensorData(yesItems);
                    break;
            }
        }

    }
}
