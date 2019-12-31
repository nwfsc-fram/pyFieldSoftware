import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.2

import "../common"

Dialog {
    id: dlg
    width: 900
    height: 600
    title: download_only ? "Retrieve Updates" : "Synchronize Database"

    property var username: null
    property var password: null

    property bool download_only: false

    // Defined in ObserverDBSyncController.py:
    //    signal abortSync(var reason)
    //    signal syncComplete(var result)
    //    signal performSync(var username, var password)

    onVisibleChanged: {
        reset_colors();
    }

    function initSync(uname, pw) {
        username = uname;
        password = pw;
        lblStatus.reset();
        open();
    }

    function updateUI(isSyncing) {
        pbSync.visible = isSyncing;
        btnCancelOK.visible = !isSyncing;
        btnRetrieveUpdates.visible = !isSyncing;
    }


    Connections {
        target: db_sync
        onSyncStarted: {
            dlg.updateUI(true);
        }

        onAbortSync: {
            console.log("Got abort sync: " + reason)
            show_result("Sync aborted: \n" + reason, false);
            dlg.updateUI(false);

        }
        onPullComplete: {
            console.log("Got pull-only complete message: " + result)
            dlg.updateUI(false);
            show_result(result, success);
            appstate.catches.species.reloadSpeciesDatabase();
            appstate.users.updateProgramsForUser(username);
            // TODO Other DB refreshes? Vessels etc
            if (recordsUpdated > 0) { // For now, force restart of software
                showRestartDlg();
            }
        }

        onPushComplete: {
            console.log("Got push complete message: " + result)
            dlg.updateUI(false);
            show_result(result, success);
            appstate.catches.species.reloadSpeciesDatabase();
            appstate.trips.tripsChanged();
            db_sync.updateDBSyncInfo();
        }

        onReadyToPush: {
            console.log("Got ready to push signal.")
            dlg.updateUI(false);
            if (db_sync.currentSOAPUsername !== null && db_sync.currentSOAPPassword !== null) {
                console.log("Performing upload with username " + db_sync.currentSOAPUsername)
                dlg.updateUI(true);
                db_sync.uploadTrips();
            } else {
                show_result("For upload, enter username + password.", false);
            }
        }
    }

    function show_result(message, success) {
        lblStatus.text = message
        if (!success) {
            btnCancelOK.text = "Cancel"
            lblStatus.color = "red";
            lblStatus.font.bold = true;
            lblStatus.font.pixelSize = 25;
            lblBackupReminder.visible = false;
        } else {
            btnCancelOK.text = "OK"
            lblStatus.color = "green";
            lblStatus.font.bold = true;
            lblStatus.font.pixelSize = 25;
            lblBackupReminder.visible = true;
        }
    }

    function reset_colors() {
        btnCancelOK.text = "Cancel";
        lblStatus.color = "black";
        lblStatus.font.bold = false;
        lblStatus.font.pixelSize = 20;
    }

    function showRestartDlg() {
        dlgRestartSoftware.display();
    }

    FramNoteDialog {
        id: dlgRestartSoftware
        function display() {
           message = "Databases updated.\nPlease restart software (closing now.)";
           open();
        }
        onAccepted: {
            Qt.quit() // close the app
        }
    }

    contentItem: ColumnLayout {
        anchors.fill: parent

        FramLabel {
            Layout.alignment: Qt.AlignCenter
            Layout.margins: 10
            font.pixelSize: 18
            text: "Ensure system is connected to the internet.\nNote that synchronization may take a minute or longer.\n"
        }
        FramLabel {
            id: lblStatus
            Layout.alignment: Qt.AlignCenter
            font.pixelSize: 18
            text: default_text
            property string default_text: download_only ? "Ready to retrieve updates..." : "Ready to perform DB synchronization..."
            function reset() {
                text = default_text;
            }
        }
        FramLabel {
            id: lblBackupReminder
            Layout.alignment: Qt.AlignCenter
            font.pixelSize: 20
            text: "Backup and upload your database to production using the scantrip function."
            visible: false
        }
        ObserverTableView {
            id: tableSyncStatus
            Layout.fillWidth: true
            model: db_sync.SyncInfoModel
            visible: !download_only
            selectionMode: appstate.trips.debrieferMode ? SelectionMode.SingleSelection : SelectionMode.NoSelection
            TableViewColumn {
                title: "Trip ID"
                role: "trip_id"
                width: 80
            }
            TableViewColumn {
                title: "Online Trip ID"
                role: "external_trip_id"
                width: 140
            }
            TableViewColumn {
                title: "Sync Status"
                role: "sync_status"
            }
            TableViewColumn {
                title: "Fishery"
                role: "fishery"
                width: 200
            }
            TableViewColumn {
                title: "User"
                role: "user_name"
                width: 180
            }

        }

        RowLayout {
            Layout.alignment: Qt.AlignCenter
            spacing: 100
            ProgressBar {
                id: pbSync
                value: 0.5
                visible: false
            }

            FramButton {
                id: btnRetrieveUpdates
                Layout.alignment: Qt.AlignCenter
                text: download_only ? "Retrieve\nUpdates" : (appstate.trips.debrieferMode ? "Sync All\n\"Ready to Sync\" Trips": "Perform\nSync")
                onClicked: {
                    db_sync.currentSOAPUsername = username;
                    db_sync.currentSOAPPassword = password;
                    if (download_only) {
                        lblStatus.text = "Downloading database updates.";
                        console.log(lblStatus.text);
                        if (db_sync.isOnline()) {
                            reset_colors();
                            db_sync.performRetrieveUpdates();
                        } else {
                            show_result("Offline, could not connect to internet.", false);
                        }

                    } else {

                        lblStatus.text = "Now uploading trip data.\n Please do not close this window.";
                        console.log(lblStatus.text);
                        if (db_sync.isOnline()) {
                            reset_colors();
                            db_sync.performSync();
                        } else {
                            show_result("Offline, could not connect to internet.", false);
                        }
                    }
                }
            }
            FramButton {
                id: btnCycleSyncStatus
                text: "Cycle Sync Status\n(Debriefer Mode)"
                visible: appstate.trips.debrieferMode
                enabled: tableSyncStatus.selection.count > 0
                onClicked: {
                    var row = tableSyncStatus.currentRow;
                    var trip_id = tableSyncStatus.model.get(row).trip_id;
                    if (trip_id) {
                        db_sync.cycleTripSyncStatus(trip_id);
                        db_sync.updateDBSyncInfo();
                    }
                }
            }
        }
        FramButton {
            id: btnCancelOK
            Layout.alignment: Qt.AlignCenter
            text: "Cancel"
            onClicked: {
                dlg.close()
            }
        }

    }    
}
