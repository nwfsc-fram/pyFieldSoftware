import QtQuick 2.5
import QtQuick.Controls 1.5
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0
import QtQuick.Dialogs 1.2

import "../common"

Item {
    id: itmFileManagement

//    property alias cbYear: cbYear;
//    property alias cbVessel: cbVessel;
    property url path;

    Component.onCompleted: {
        settings.vessel = cbVessel.model[cbVessel.currentIndex];
        settings.year = cbYear.model[cbYear.currentIndex];
    }
    Connections {
        target: dataCompleteness.dataCheckModel
        onBreakItEncountered: showBreakItMsg(msg);
    }

    Connections {
        target: fileManagement
        onFolderCreationError: errorCreatingFolder(status, msg);
    } // onFolderCreationError
    Connections {
        target: settings
        onYearChanged: yearVesselChanged();
    } // settings.yearChanged
    Connections {
        target: settings
        onVesselChanged: yearVesselChanged();
    } // settings.vesselChanged

    function showBreakItMsg(msg) {
        dlgOkay.message = msg;
        dlgOkay.open();
    }

    function yearVesselChanged() {
        if (settings.loggedInStatus)
            settings.loadFileManagementModels();
    }

    function errorCreatingFolder(status, msg) {
        dlgOkay.message = msg
        dlgOkay.open()
    }

    function deleteDatabases() {
        /* Function to delete all of the selected wheelhouse databases and all of the backdeck + sensor databases
        */
        var idx = [];
        var reverseIdx = [];

        // Remove all of the backdeck databases
        for (var i = tvBackdeck.model.items.length - 1; i >= 0; i--) {
            tvBackdeck.model.remove_item(i);
        }

        // Remove all of the sensor databases
        for (var i = tvSensors.model.items.length - 1; i >= 0; i--) {
            tvSensors.model.remove_item(i);
        }

        // Remove the selected wheelhouse databases - do these last as there are still links to the Operations
        // table records in the remove_item methods of tvBackdeck and tvSensors
        tvWheelhouse.selection.forEach( function(rowIndex) {
            idx.push(rowIndex);
        })
        reverseIdx = idx.slice();
        reverseIdx.sort(function(a, b) {return b-a});
        for (var i = 0; i < reverseIdx.length; i++) {
            tvWheelhouse.model.remove_item(reverseIdx[i]);
        }

    }

    RowLayout {
        id: rwlPath
        x: 20
        y: 20
        spacing: 10
//        Label {
//            Layout.preferredWidth: 60
//            id: lblYear
//            text: qsTr("Year")
//        } // lblYear
//        ComboBox {
//            id: cbYear
//            model: ["2015", "2016"]
//            currentIndex: 1
//            onCurrentIndexChanged: {
//                if (currentText != "")
//                    settings.year = currentText;
//            }
//        } // cbYear
//        Item { Layout.preferredWidth: 200 }
        Label {
            text: qsTr("Target Folder")
        } // lblTargetFolder
        TextField {
            id: tfTargetPath
//            text: qsTr("\\\\nwcfile\\FRAM\\Data\\")
//            text: qsTr("//nwcfile/FRAM/Data")
//            text: qsTr("C:\\")
            text: (settings.mode == "test") ? qsTr("C:\\") : qsTr("\\\\nwcfile\\FRAM\\Data\\WCBottomTrawlSurveyData\\SurveyData")
            Layout.preferredWidth: 400
        } // tfTargetPath
        Button {
            id: btnBrowse
            text: qsTr("Browse...")
            onClicked: {
                fileDialog.nameFilters = []

                // ToDo Todd Hay - Fix folder, Solution might be here:  http://stackoverflow.com/questions/24927850/get-the-path-from-a-qml-url

//                fileDialog.folder = Qt.resolvedUrl("file://" + tfTargetPath.text); // .resolvedUrl(tfTargetPath.text);
                fileDialog.folder = "file:////" + tfTargetPath.text //.replace("\\/g", "/");
//                fileDialog.folder = "file:////\\nwcfile\\FRAM\\Data"
                fileDialog.selectMultiple = false;
                fileDialog.selectFolder = true;
                fileDialog.dataType = "targetPath"
                fileDialog.open()
            }
        } // btnBrowse
        Item { Layout.preferredWidth: 200 }
        Button {
            id: btnRefreshCopyStatus
            text: qsTr("Refresh Status")
            enabled: false
            onClicked: {
                fileManagement.refresh_copy_status(tfTargetPath.text,
                                                    cbYear.currentText,
                                                    cbVessel.currentText);
            }
        } // btnRefreshCopyStatus
        Button {
            id: btnCopyFiles
            text: qsTr("Copy Files")
            onClicked: {
                fileManagement.copy_files(tfTargetPath.text,
                                          cbYear.currentText,
                                          cbVessel.currentText);
            }
        } // btnCopyFiles
    } // rwlPath
    ColumnLayout {
        id: cllNonSensors
        anchors.left: rwlPath.left
        anchors.top: rwlPath.bottom
        anchors.topMargin: 100
        width: parent.width * 0.5
        spacing: 10
        RowLayout {
            spacing: 20
            Label { text: qsTr("Wheelhouse DBs") }
            Button {
                id: btnAddWheelhouseFile
                text: "Add"
                onClicked: {
                    fileDialog.dataType = "wheelhouse";
                    fileDialog.selectFolder = false;
                    fileDialog.nameFilters = [ "SQLite Database files (*.db)", "All files (*)"]
                    fileDialog.selectMultiple = true;

                    path = Qt.resolvedUrl("////nwcfile/FRAM/Data/WCBottomTrawlSurveyData/SurveyData/RawData"); // No Errors
                    path = Qt.resolvedUrl("file://nwcfile/FRAM/Data/WCBottomTrawlSurveyData");  // Error
                    path = Qt.resolvedUrl("file://nwcfile/FRAM/Data/WCBottomTrawlSurveyData/SurveyData/");  // Error, opens:  //nwcfile/FRAM/Data/WCBottomTrawlSurveyData
                    path = "file://nwcfile/FRAM/Data/WCBottomTrawlSurveyData/SurveyData"; // Error
                    path = Qt.resolvedUrl("file://nwcfile/FRAM/Data/WCBottomTrawlSurveyData/SurveyData");  // Error
                    path = "file:///nwcfile/FRAM/Data/WCBottomTrawlSurveyData/SurveyData"; // Error
                    path = Qt.resolvedUrl("file:////nwcfile/FRAM/Data/WCBottomTrawlSurveyData");  // Error
                    path = Qt.resolvedUrl("file:///z:/FRAM/Data/WCBottomTrawlSurveyData");  //
                    path = Qt.resolvedUrl("file:///\\\\nwcfile\\FRAM\\Data\\"); // No error, returns app folder path
                    path = Qt.resolvedUrl("file:////\\\\nwcfile\\FRAM\\Data\\"); // No error, returns app folder path
                    path = Qt.resolvedUrl("\\\\nwcfile\\FRAM\\Data\\"); // No error, returns app folder path
                    path = "\\\\nwcfile\\FRAM\\Data\\"; // No error, returns app folder path
                    path = "//nwcfile/FRAM/Data/";  // No error, returns app folder path
                    path = Qt.resolvedUrl("file:///nwcfile/FRAM/Data/");   // Error, goes to \\nwcfile last folder however
                    path = "file:///Z:/" // WORKS - No Errors, goes to Z:\ drive
                    path = "file:///Z:/Data"  // WORKS
                    path = "file://///nwcfile.local/FRAM/Data" // ERROR
                    path = "file://///nwcfile.nmfs.local/FRAM/Data" // ERROR
                    path = "file:///nwcfile/FRAM/Data" // ERROR
                    path = "//nwcfile/FRAM/Data" // NO ERROR, turns path into qrc://nwcfile/FRAM/Data
                    path = Qt.resolvedUrl("file://///nwcfile/FRAM/Data"); // NO ERROR, path = file://
                    path = Qt.resolvedUrl("file:///nwcfile/FRAM/Data");  // ERROR
                    path = Qt.resolvedUrl("file:///\\nwcfile/FRAM/Data"); // ERROR
                    path = "file://////nwcfile/FRAM/Data";  // ERROR
                    path = "file:////\\\\nwcfile\\FRAM\\Data";  // No Error, path = file:////%5C%5Cnwcfile%5CFRAM%5CData, folder = file://
                    path = "file://///nwcfile/FRAM/Data/" // Error, folder: file:///nwcfile/FRAM/Data/
                    path = "////nwcfile/FRAM/Data/" // NO ERROR, returns  app folder path, path = qrc://nwcfile/FRAM/Data
                    path = "file:///\\nwcfile\FRAM\Data" // ERROR
                    path = "file:///\\\\nwcfile\\FRAM\\Data" // NO ERROR, folder is:  file://   >  returns to Computer
                    path = "file:///nwcfile.nwfsc.noaa.gov/FRAM/Data" // ERROR
                    path = "file:///nwcfile.nwfsc.noaa.gov/FRAM/Data" // ERROR
                    path = "file:///Z:/Data/WCBottomTrawlSurveyData/SurveyData/RawData"  // WORKS
                    fileDialog.folder = path;
//                    fileDialog.folder = (settings.mode == "test") ? fileDialog.shortcuts.home : path
//                    console.info('path: ' + path);
//                    console.info('folder: ' + fileDialog.folder);
                    fileDialog.open()
//                    fileDialog.visible = true;
                }
            } // btnAddWheelhouseFile
            Button {
                id: btnRemoveWheelhouseFile
                text: "Remove"
                enabled: false
                onClicked: {
                    if (tvWheelhouse.model.currentIndex != -1) {
                        var idx = [];
                        tvWheelhouse.selection.forEach( function(rowIndex) {
                            idx.push(rowIndex);
                        })

                        var copyStatus;
                        var dstFileName;
                        var item;
                        var reverseIdx = [];
                        reverseIdx = idx.slice();
                        reverseIdx.sort(function(a, b) {return b-a});
                        for (var i = 0; i < reverseIdx.length; i++) {
                            item = tvWheelhouse.model.get(reverseIdx[i]);
                            dstFileName = item.dstFileName;
                            if ((dstFileName == "") || (typeof dstFileName == 'undefined')) {
                                tvWheelhouse.model.remove_item(reverseIdx[i]);
                            } else if (tvWheelhouse.model.check_haul_count() > 0) {
                                dlgOkay.message = "Hauls have already been loaded for this database\n\n" +
                                    "The database must be removed manual from the database."
                                dlgOkay.open()
                            } else {
                                dlgOkayCancel.actionType = "databaseRemoval";
                                dlgOkayCancel.message = "You are about to delete a wheelhouse database that has been copied.\n\n" +
                                    tvWheelhouse.model.get(tvWheelhouse.model.currentIndex).dstFileName + '\n\n' +
                                    "This will remove all of the backdeck and sensor databases as well.\n\n" +
                                    "Do you wish to continue with this deletion?"
                                dlgOkayCancel.open()
                            }
                        }
                    }
                }
            } // btnRemoveWheelhouseFile
        } // wheelhouse
        TableView {
            id: tvWheelhouse
            Layout.preferredHeight: 200
//            Layout.preferredWidth: 620
            anchors.left: parent.left
            anchors.right: parent.right

            selectionMode: SelectionMode.ExtendedSelection
            model: fileManagement.wheelhouseModel
            TableViewColumn {
                title: "Source File Name"
                role: "srcFileName"
                width: 280
                delegate: Text {
                    text: styleData.value  ? styleData.value.replace(/^.*[\\\/]/, '') : ""
                    color: styleData.textColor
                    elide: styleData.elideMode
                    renderType: Text.NativeRendering
                }
            }
            TableViewColumn {
                title: "Destination File Name"
                role: "dstFileName"
                width: 280
                delegate: Text {
                    text: styleData.value  ? styleData.value.replace(/^.*[\\\/]/, '') : ""
                    color: styleData.textColor
                    elide: styleData.elideMode
                    renderType: Text.NativeRendering
                }
            }
            TableViewColumn {
                title: "Copied"
                role: "copyStatus"
                width: 55
            }
            onClicked: {
                btnRemoveWheelhouseFile.enabled = (model.currentIndex != -1) ? true : false;
                if (currentRow != -1) {
                    var item = model.get(currentRow);
                    var src = (item.srcFileName == null) ? "" : item.srcFileName
                    var dst = (item.dstFileName == null) ? "" : item.dstFileName
                    settings.statusBarMessage = "Source File: " + src + "\t\tDestination File: " + dst;
                }

            }

        } // tvWheelhouse
        Label { Layout.preferredHeight: 20}
        RowLayout {
            spacing: 20
            Label {
                text: qsTr("Backdeck DBs")
            }
            Button {
                id: btnAddBackdeckFile
                text: "Add"
                onClicked: {
                    fileDialog.dataType = "backdeck";
                    fileDialog.nameFilters = ["SQLite Database files (*.db)", "All files (*)"]
                    fileDialog.selectFolder = false;
                    fileDialog.selectMultiple = true;
//                    fileDialog.folder = Qt.resolvedUrl(tfTargetPath.text);
//                    fileDialog.visible = true;
                    path = "file:///Z:/Data/WCBottomTrawlSurveyData/SurveyData/RawData"  // WORKS
                    fileDialog.folder = path;

                    fileDialog.open()
                }
            }
            Button {
                id: btnRemoveBackdeckFile
                text: "Remove"
                enabled: false
                onClicked: {
                    if (tvBackdeck.model.currentIndex != -1) {
                        var idx = [];
                        tvBackdeck.selection.forEach( function(rowIndex) {
                            idx.push(rowIndex);
                        })
                        var reverseIdx = [];
                        reverseIdx = idx.slice();
                        reverseIdx.sort(function(a, b) {return b-a});
                        for (var i = 0; i < reverseIdx.length; i++) {
                            tvBackdeck.model.remove_item(reverseIdx[i]);
                        }
                    }
                }
            }
        } // backdeck
        TableView {
            id: tvBackdeck
            Layout.preferredHeight: 200
//            Layout.preferredWidth: 620
            anchors.left: parent.left
            anchors.right: parent.right
            selectionMode: SelectionMode.ExtendedSelection
            model: fileManagement.backdeckModel
            TableViewColumn {
                title: "Source File Name"
                role: "srcFileName"
                width: 280
                delegate: Text {
                    text: styleData.value  ? styleData.value.replace(/^.*[\\\/]/, '') : ""
                    color: styleData.textColor
                    elide: styleData.elideMode
                    renderType: Text.NativeRendering
                }
            }
            TableViewColumn {
                title: "Destination File Name"
                role: "dstFileName"
                width: 280
                delegate: Text {
                    text: styleData.value  ? styleData.value.replace(/^.*[\\\/]/, '') : ""
                    color: styleData.textColor
                    elide: styleData.elideMode
                    renderType: Text.NativeRendering
                }
            }
            TableViewColumn {
                title: "Copied"
                role: "copyStatus"
                width: 55
            }
            onClicked: {
                btnRemoveBackdeckFile.enabled = (model.currentIndex != -1) ? true : false;
                if (currentRow != -1) {
                    var item = model.get(currentRow);
                    var src = (item.srcFileName == null) ? "" : item.srcFileName
                    var dst = (item.dstFileName == null) ? "" : item.dstFileName
                    settings.statusBarMessage = "Source File: " + src + "\t\tDestination File: " + dst;
                }

            }
        } // tvBackdeck

    } // cllNonSensors
    ColumnLayout {
        id: cllSensors
        anchors.left: cllNonSensors.right
        anchors.leftMargin: 20
        anchors.top: cllNonSensors.top
        anchors.right: parent.right
        anchors.rightMargin: 20
        spacing: 10
        RowLayout {
            spacing: 20
            Label {
                text: qsTr("Sensor DBs")
            }
            Button {
                id: btnAddSensorFile
                text: "Add"
                onClicked: {
                    fileDialog.dataType = "sensors";
                    fileDialog.nameFilters = [ "SQLite Database files (*.db)", "All files (*)"]
                    fileDialog.selectFolder = false;
                    fileDialog.selectMultiple = true;
//                    fileDialog.folder = Qt.resolvedUrl(tfTargetPath.text);
//                    fileDialog.visible = true;
                    path = "file:///Z:/Data/WCBottomTrawlSurveyData/SurveyData/RawData"  // WORKS
                    fileDialog.folder = path;
                    fileDialog.open();
                }
            }
            Button {
                id: btnRemoveSensorFile
                text: "Remove"
                enabled: false
                onClicked: {
                    if (tvSensors.model.currentIndex != -1) {
                        var idx = [];
                        tvSensors.selection.forEach( function(rowIndex) {
                            idx.push(rowIndex);
                        })
                        var reverseIdx = [];
                        reverseIdx = idx.slice();
                        reverseIdx.sort(function(a, b) {return b-a});
                        var dataFound = false;
                        for (var i = 0; i < reverseIdx.length; i++) {
                            if (fileManagement.sensorsModel.check_operation_measurements_count(reverseIdx[i]) > 0) {
                                dataFound = true;
                                break;
                            }
                        }
                        if (dataFound) {
                            dlgOkayCancel.actionType = "deleteSensorDatabase";
                            dlgOkayCancel.message = "Sensor data has already been loaded from these sensor files.\n" +
                                "Deleting the sensor files will remove all assocated sensor data\nfrom FRAM_CENTRAL\n\n" +
                                "Do you wish to proceed with deleting this data?"
                            dlgOkayCancel.open()

                        } else {
                            for (var i = 0; i < reverseIdx.length; i++) {
                                tvSensors.model.remove_item(reverseIdx[i]);
                            }
                        }
                    }
                }
            }
        } // sensor dbs
        TableView {
            id: tvSensors
            Layout.preferredHeight: 600
//            Layout.preferredWidth: 600
            selectionMode: SelectionMode.ExtendedSelection
            anchors.left: parent.left
            anchors.right: parent.right
            model: fileManagement.sensorsModel

            TableViewColumn {
                title: "Source File Name"
                role: "srcFileName"
                width: 200
                delegate: Text {
                    text: styleData.value  ? styleData.value.replace(/^.*[\\\/]/, '') : ""
                    color: styleData.textColor
                    elide: styleData.elideMode
                    renderType: Text.NativeRendering
                }
            } // srcFileName
            TableViewColumn {
                title: "File Size"
                role: "fileSize"
                width: 60
                delegate: Text {
                    text: styleData.value  ? styleData.value.toFixed(1) + "MB" : ""
                    color: styleData.value > 10 ? styleData.textColor : "red"
                    font.weight: styleData.value > 10 ? Font.Normal : Font.Bold
                    elide: styleData.elideMode
                    renderType: Text.NativeRendering
                }
            } // fileSize
            TableViewColumn {
                title: "Destination File Name"
                role: "dstFileName"
                width: 250
                delegate: Text {
                    text: styleData.value  ? styleData.value.replace(/^.*[\\\/]/, '') : ""
                    color: styleData.textColor
                    elide: styleData.elideMode
                    renderType: Text.NativeRendering
                }
            } // dstFileName
            TableViewColumn {
                title: "Copied"
                role: "copyStatus"
                width: 55
            } // copyStatus
            onClicked: {
                btnRemoveSensorFile.enabled = (model.currentIndex != -1) ? true : false;
                if (currentRow != -1) {
                    var item = model.get(currentRow);
                    var src = (item.srcFileName == null) ? "" : item.srcFileName
                    var dst = (item.dstFileName == null) ? "" : item.dstFileName
                    settings.statusBarMessage = "Source File: " + src + "\t\tDestination File: " + dst;
                }
            }

        } // tvSensors
    } // cllSensors

    FileDialog {
        id: fileDialog
        title: "Please choose " + dataType + " files"
//        folder: shortcuts.home
        visible: false
        property string dataType: ""
        selectMultiple: true
        selectFolder: false
        nameFilters: [ "SQLite Database files (*.db)", "All files (*)"]
        onAccepted: {
            var item;
            for (var i=0; i<fileDialog.fileUrls.length; i++) {
                item = {"srcFileName": fileDialog.fileUrls[i], "copyStatus": null}
                switch (dataType) {
                    case "targetPath":
//                        console.info(fileDialog.fileUrls[i])
                        tfTargetPath.text = fileDialog.folder.toString().replace("file:///", "");
                        break;
                    case "wheelhouse":
//                        console.info(fileDialog.fileUrls[i])
                        fileManagement.wheelhouseModel.add_item(item)
                        break;

                    case "sensors":
                        fileManagement.sensorsModel.add_item(item)
                        break;

                    case "backdeck":
                        fileManagement.backdeckModel.add_item(item)
                        break;
                }
            }
        }
        onRejected: { }
    }
    FramDesktopOkayDialog { id: dlgOkay }
    FramDesktopOkayCancelDialog {
        id: dlgOkayCancel
        property string actionType: ""
        onAccepted: {
            switch (actionType) {
                case "databaseRemoval":
                    deleteDatabases();
                    break;

                case "deleteSensorDatabase":
                   var idx = [];
                    tvSensors.selection.forEach( function(rowIndex) {
                        idx.push(rowIndex);
                    })
                    var reverseIdx = [];
                    reverseIdx = idx.slice();
                    reverseIdx.sort(function(a, b) {return b-a});
                    for (var i = 0; i < reverseIdx.length; i++) {
                        tvSensors.model.remove_item(reverseIdx[i]);
                    }
                    break;
            }
        }
    }
}
