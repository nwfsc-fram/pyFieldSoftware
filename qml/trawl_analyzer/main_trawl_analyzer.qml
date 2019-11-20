import QtQuick 2.6
import QtQuick.Controls 1.3
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.2

import "../common"

ApplicationWindow {
    id: mainWindow
    title: settings.loggedInStatus ? "Trawl Analyzer - " + settings.year + " - " + settings.vessel : "Trawl Analyzer"
    width: 1280
    height: 900
    visible: true

    property alias sbMsg: sbMsg
    property alias cbVessel: cbVessel
    property alias cbYear: cbYear
    property alias cbHaul: cbHaul

//    opacity: 1.0
//    flags: Qt.Desktop
//    flags: Qt.Widget

    Connections {
        target: settings
        onPasswordFailed: passwordFailed()
    } // onSelectionChanged

    Connections {
        target: settings
        onLoggedInStatusChanged: resetHauls()
    }
    Connections {
        target: settings
        onYearChanged: resetHauls()
    }
    Connections {
        target: settings
        onVesselChanged: resetHauls()
    }
//    Connections {
//        target: timeSeries
//        onDisplaySeriesChanged: displaySeriesChanged()
//    }

    onClosing: {
//        messageDialog.show("CLOSING...");
//        console.info('stopping all threads, application is closing')
//        fpcMain.stop_all_threads();
    }

//    function displaySeriesChanged() {
//        if (timeSeries.displaySeries) {
//
//        }
//    }

    function resetHauls(status) {
        settings.haul = null;
        timeSeries.stopLoadingTimeSeries();
        timeSeries.haulsModel.populate_model();
        cbHaul.currentIndex = 0;
    }

    function passwordFailed() {
        dlgOkay.message = "Your authentication failed\n\nPlease try again"
        dlgOkay.open()
    }

    menuBar: MenuBar {
        Menu {
            title: "File"
            MenuItem {
                text: "Exit"
                onTriggered: Qt.quit();
            }
        }
    }
    toolBar:ToolBar {
        RowLayout {
            anchors.fill: parent

            ExclusiveGroup {
                id: egToolButtons
            }

            ToolButton {
                id: btnLogin
                iconSource: settings.loggedInStatus ? "qrc:/resources/images/lock.png" :
                                                    "qrc:/resources/images/unlock.png"
                tooltip: settings.loggedInStatus ? "Logout" : "Login"
                onClicked: {
                    if (iconSource == "qrc:/resources/images/unlock.png") {
                        dlgLogin.tfUsername.focus = true;
                        dlgLogin.open();
                    } else {
                        settings.logout()
                    }
                }
            } // btnLogin

            Item { Layout.preferredWidth: 20 }

            ToolButton {
                id: btnFileManagement
                iconSource: "qrc:/resources/images/filemanagement.png"
                enabled: settings.loggedInStatus
                tooltip: "File Management"
                checked: true
                checkable: true
                exclusiveGroup: egToolButtons
                onClicked: {
                    tvScreens.currentIndex = 0;
                }
            } // btnFileManagement
            ToolButton {
                id: btnDataCompleteness
                iconSource: "qrc:/resources/images/datacompleteness.png"
                enabled: settings.loggedInStatus
                tooltip: "Data Completeness"
                checked: false
                checkable: true
                exclusiveGroup: egToolButtons
                onClicked: {
                    tvScreens.currentIndex = 1;
                }
            } // btnDataCompleteness
            ToolButton {
                id: btnTimeSeries
                iconSource: "qrc:/resources/images/timeseries.png"
                enabled: settings.loggedInStatus
                tooltip: "Time Series + Track Line"
                checked: false
                checkable: true
                exclusiveGroup: egToolButtons
                onClicked: {
                    tvScreens.currentIndex = 2;
                }
            } // btnTimeSeries
            ToolButton {
                id: btnCatch
                iconSource: "qrc:/resources/images/fish.png"
                enabled: settings.loggedInStatus
                tooltip: "Catch"
                checked: false
                checkable: true
                exclusiveGroup: egToolButtons
                onClicked: {
                    tvScreens.currentIndex = 3;
                }
            } // btnTimeSeries
            ToolButton {
                id: btnReports
                iconSource: "qrc:/resources/images/reports.png"
                enabled: settings.loggedInStatus
                tooltip: "Reports & QA/QC"
                checked: false
                checkable: true
                exclusiveGroup: egToolButtons
                onClicked: {
                    tvScreens.currentIndex = 4;
                }
            } // btnReports
            Item { Layout.preferredWidth: 20 }

            ToolButton {
                id: btnSettings
                iconSource: "qrc:/resources/images/settings.png"
                tooltip: "Settings"
            } // btnSettings

//            Item { Layout.fillWidth: true }
            Item { Layout.preferredWidth: 100 }

            Label {
                id: lblYear
                text: qsTr("Year")
                Layout.preferredWidth: 30
            } // lblYear
            ComboBox {
                id: cbYear
                Layout.preferredWidth: 60
                enabled: settings.loggedInStatus & !settings.isLoading
                model: ["2019", "2018", "2017", "2016"]
                currentIndex: 0
                onCurrentIndexChanged: {
                    if (currentText != "") {
                        dataCompleteness.stop_data_loading();
                        dataCompleteness.dataCheckModel.stop_model_population();
                        settings.year = currentText;
                    }
                }
            } // cbYear
            Item { Layout.preferredWidth: 20 }
            Label {
                id: lblVessel
                text: qsTr("Vessel")
                Layout.preferredWidth: 40
            } // lblVessel
            ComboBox {
                id: cbVessel
                Layout.preferredWidth: 100
                enabled: settings.loggedInStatus & !settings.isLoading
                model: ["Excalibur", "Last Straw", "Ms. Julie", "Noah's Ark"]
                currentIndex: 0
                onCurrentIndexChanged: {
                    if (currentText != "") {
                        dataCompleteness.stop_data_loading();
                        dataCompleteness.dataCheckModel.stop_model_population();
                        settings.vessel = currentText;
                    }
                }
            } // cbVessel
            Item { Layout.preferredWidth: 20 }
            Label {
                id: lblHaul
                text: qsTr("Haul")
                Layout.preferredWidth: 30
            } // lblHaul
            ComboBox {
                id: cbHaul
                Layout.preferredWidth: 120
                enabled: settings.loggedInStatus & !settings.isLoading
                model: timeSeries.haulsModel
                onCurrentIndexChanged: {
                    if ((currentText == "Select Haul")) {
                        resetHauls();
                    } else if (currentText != "") {
                        settings.haul = currentText;
//                        timeSeries.stopLoadingTimeSeries();
                        timeSeries.load_haul(currentText);
                    }
                }
            } // cbHaul

            Item { Layout.fillWidth: true }
            Label {
                id: lblScanFiles
                text: qsTr("Scan Files:")
                Layout.preferredWidth: 50
            } // lblScanFiles
            Switch {
                id: swScanFiles
                checked: settings.scanFiles
                onClicked: {
                    settings.scanFiles = checked;
                }
            }

            Item { Layout.preferredWidth: 20 }

            Label {
                id: lblMode
                text: qsTr("Database:")
            } // lblMode
            Button {
                id: btnMode
                text: settings.mode
                onClicked: {
                    switch (text) {
                        case "Dev":
                            settings.mode = "Stage";
                            break;
                        case "Stage":
                            settings.mode = "Prod";
                            break;
                        case "Prod":
                            settings.mode = "Dev";
                            break;
                    }
                }
            }
        }
    }
    TabView {
        id: tvScreens
        enabled: settings.loggedInStatus
        anchors.rightMargin: 0
        anchors.bottomMargin: 0
        anchors.leftMargin: 0
        anchors.topMargin: 0
        anchors.fill: parent

        tabsVisible: false

        Tab {
            id: tabFileManagement
            title: "File Management"
            active: true
            source: "FileManagementScreen.qml"
            onVisibleChanged: settings.statusBarMessage = "";
        }
        Tab {
            id: tabDataCompleteness
            title: "Data Completeness"
            active: true
            source: "DataCompletenessScreen.qml"
            onVisibleChanged: settings.statusBarMessage = "";
        }
        Tab {
            id: tabTimeSeries
            title: "Time Series"
            active: true
            source: "TimeSeriesScreen.qml"
//            source: "TSChart.qml"
            onVisibleChanged: settings.statusBarMessage = "";
        }
        Tab {
            id: tabCatch
            title: "Catch"
            active: true
            source: "CatchScreen.qml"
            onVisibleChanged: settings.statusBarMessage = "";
        }
        Tab {
            id: tabReports
            title: "Reports"
            active: true
            source: "ReportsScreen.qml"
            onVisibleChanged: settings.statusBarMessage = "";
        }
    }
    statusBar: StatusBar {
        id: sbMsg
        Item {
            RowLayout {
                anchors.fill: parent
                Label { text: settings.statusBarMessage }
            }
        }
    }
    MessageDialog {
        id: messageDialog
        width: 600
        height: 800
        objectName: "dlgUnhandledException"
        title: qsTr("Unhandled Exception Occurred")
        icon: StandardIcon.Critical
        function show(caption) {
            messageDialog.text = caption;
            messageDialog.open();
        }
        onAccepted: {
            mainWindow.close();
        }
    }
    FramDesktopLoginDialog { id: dlgLogin }
    FramDesktopOkayDialog { id: dlgOkay }
}
