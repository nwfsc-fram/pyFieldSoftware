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
    title: "Open Operation"

    property int id: -1

    Component.onCompleted: {
        console.info("OpenOperationDialog.qml completed");
    }

    onRejected: {  }
    onAccepted: {  }
    onVisibilityChanged: {
        if (visible) tvOperations.selection.clear();
    }

//    Connections {
//        target: fpcMain
//        onOperationsModelChanged: refreshOperations()
//    } // fpcMain.onOperationsModelChanged
//    function refreshOperations() {
//        console.info("ops Model changed, refresh the table");
//    }

    contentItem: Rectangle {
        color: SystemPaletteSingleton.window(true)
//        color: "#eee"

        TableView {
            id: tvOperations
            y: 20
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width - 20
            height: parent.height - rwlButtons.height - 40
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
            TableViewColumn {
                role: "set_id"
                title: "Set ID"
                width: 80
            } // set_id
            TableViewColumn {
                role: "start_date_time"
                title: "Start Date/Time"
                width: 150
            } // start_date_time
            TableViewColumn {
                role: "day_of_cruise"
                title: "Day of Cruise"
                width: 80
            } // day_of_cruise
            TableViewColumn {
                role: "event_count"
                title: "# Events"
                width: 70
            } // event_count
            TableViewColumn {
                role: "site"
                title: "Site"
                width: 50
            } // site
            TableViewColumn {
                role: "area"
                title: "Area"
                width: 230
            } // area

            selection.onSelectionChanged: {
                if (currentRow != -1) {
                    id = fpcMain.operationsModel.get(currentRow).id;
                }
            }
            onDoubleClicked: {
                if (currentRow != -1) {
                    id = fpcMain.operationsModel.get(currentRow).id;
                    dlg.accept();
                }
            }

            model: fpcMain.operationsModel
        } // tvOperations
        RowLayout {
            id: rwlButtons
            anchors.top: tvOperations.bottom
            anchors.topMargin: 10
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 20
            Button {
                id: btnOpen
                text: "Open"
                Layout.preferredWidth: 80
                Layout.preferredHeight: 40
                onClicked: { dlg.accept() }
            } // btnOpen
            Button {
                id: btnCancel
                text: "Cancel"
                Layout.preferredWidth: 80
                Layout.preferredHeight: 40
                onClicked: { dlg.reject() }
            } // btnCancel
            Button {
                id: btnDeleteTestSite
                text: "Delete\nTest Site"
                enabled: ((tvOperations.currentRow !== -1) &&
                    (fpcMain.check_sequence_type(tvOperations.model.get(tvOperations.currentRow).set_id.substring(2,4))));
                Layout.preferredWidth: 80
                Layout.preferredHeight: 40
                onClicked: {
                    if (tvOperations.currentRow !== -1) {
                        var set_id = tvOperations.model.get(tvOperations.currentRow).set_id;
                        var isSoftwareTest = fpcMain.check_sequence_type(set_id.substring(2,4))
                        if (isSoftwareTest) {
                            dlgOkayCancel.message = "You are about to delete the\nfollowing Software Test Site"
                            dlgOkayCancel.value = set_id;
                            dlgOkayCancel.accepted_action = "delete software test site";
                            dlgOkayCancel.open()
                        } else {
                            console.info('this is not a software test site, skipping deletion...');
                        }
                    }
                }
            } // btnDeleteTestSite

        } // rwlButtons
        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }

    OkayCancelDialog {
        id: dlgOkayCancel
        onAccepted: {
            switch (accepted_action) {
                case "delete software test site":
                    var isSoftwareTest = fpcMain.check_sequence_type(value.substring(2,4))
                    if (isSoftwareTest) {
                        fpcMain.deleteSoftwareTestSite(value);
                    }
                    break;
            }
        }
    }
}
