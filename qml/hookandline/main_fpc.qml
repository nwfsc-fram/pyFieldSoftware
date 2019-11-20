import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.2
//import io.thp.pyotherside 1.5

import "../common"

ApplicationWindow {
    title: qsTr("HookLogger - v" + settings.softwareVersion)
    width: 1280
    height: 900
    visible: true
    objectName: "appWindow"
//    opacity: 1.0
//    flags: Qt.Desktop
//    flags: Qt.Widget

    onClosing: {
//        console.info('stopping all threads, application is closing')
        fpcMain.stop_all_threads();
    }

    toolBar:ToolBar {
        RowLayout {
            anchors.fill: parent


            Button {
                id: btnNewSite
                width: 80
                height: 40
                text: "New Site"
//                iconSource: "qrc:/resources/images/new.png"
                tooltip: "Start New Site"
                onClicked: {
                    // TODO Todd - Save all fields + run validations

                    main.tfSetId.text = ""
                    main.resetWidgets();
                    main.toggleControls(false);

                    var sequences = fpcMain.get_set_id_sequences();
                    main.sequence = sequences["sequence"];
                    main.camera_sequence = sequences["camera_sequence"];
                    main.test_sequence = sequences["test_sequence"];
                    main.software_test_sequence = sequences["software_test_sequence"];
                }
            }
            Button {
                id: btnOpenCollection
                text: "Open Previous Site"
//                iconSource: "qrc:/resoures/images/open.png"
                tooltip: "Open Previous Site"
                onClicked: {
                    fpcMain.operationsModel.populate_model()
                    openOperationsDialog.open()
                }
            }
            Button {
                id: btnReviewSpecies
                text: "Review Species"
                tooltip: "Review Species"
                onClicked: {
                    speciesReview.operationsModel.populateModel()
                    reviewSpeciesDialog.open();
                }
            }

            Button {
                id: btnEndCollection
                text: "Review Site"
                tooltip: "Close out the site"
                onClicked: {
                    endOfSiteValidation.operationsModel.populateModel()
                    validationDialog.open();
                    console.info("Nothing so far, coming soon");
                }

            } // btnEndCollection
            Button {
                id: btnSerialPortManager
                text: "Sensor Data Feeds"
//                iconSource: "qrc:/resources/images/lightning-bolt.png"
                tooltip: "Sensor Data Feeds"
                onClicked: sdf.show()
            }

            Button {
                id: btnSettings
                text: "Settings"
                onClicked: settingsScreen.show()
            }
            Button {
                id: btnBackup
                text: "Backup"
                tooltip: "Backup"
                onClicked: { fpcMain.start_backup() }
            }
            Item { Layout.fillWidth: true }
        }

    }

    MainForm {
        id: main
        anchors.rightMargin: 0
        anchors.bottomMargin: 0
        anchors.leftMargin: 0
        anchors.topMargin: 0
        anchors.fill: parent
    }

    SensorDataFeeds {
        id: sdf
    }

    SettingsScreen {
        id: settingsScreen
    }

    OpenOperationDialog {
        id: openOperationsDialog
        onAccepted: {
            if (id != -1) main.loadOperation(id);
        }
    }
    SpeciesReviewDialog {
        id: reviewSpeciesDialog
        onAccepted: {
        }
    }
    EndOfSiteValidationDialog {
        id: validationDialog
        onAccepted: {}
    }

    MessageDialog {
        id: messageDialog
        title: qsTr("May I have your attention, please?")

        function show(caption) {
            messageDialog.text = caption;
            messageDialog.open();
        }
    }
    MessageDialog {
        id: dlgMessage
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
}
