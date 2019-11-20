import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import "../common"

Item {
    id: control
    function page_state_id() { // for transitions
        return "backup_state";
    }

    width: parent.width
    height: parent.height - framFooter.height
    property string backupDrive: ""  // d:\
    property alias backupPath: pathField.text  // optecs_backup

    property bool backupInProgress: false
    property bool successful: false


    ColumnLayout {
        spacing: 50
        anchors.fill: parent

        FramLabel {
            Layout.alignment: Qt.AlignHCenter
            text: "Last External Backup: " + appstate.lastBackupTime
        }

        FramLabel {
            id: labelNoExternal
            Layout.alignment: Qt.AlignHCenter
            text: "No external drives found."
            visible: !appstate.driveLetters

        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            ExclusiveGroup {
                id: driveGroup
            }

            FramLabel {
                visible: !labelNoExternal.visible
                text: "Back up to drive: "
            }

            GridLayout {
                columns: 2
                visible: !labelNoExternal.visible
                Repeater {
                    id: driveButtons
                    model: appstate.driveLetters //["D:\\", "E:\\"]
                    ObserverGroupButton {
                        exclusiveGroup: driveGroup
                        text: modelData
                        onClicked: {
                            performBackup.enabled = true;
                            backupDrive = modelData;
                            instructions.text = "Ready to perform backup to " + backupDrive + backupPath
                            successful = false;
                        }
                    }
                }
            }

            FramButton {
                text: "Refresh\nDrive Letters"
                fontsize: 20
                onClicked: {
                    appstate.updateDriveLetters();
                    successful = false;
                }
            }
        }

        ColumnLayout {
            Layout.alignment: Qt.AlignCenter
            FramLabel {
                text: "Backup Folder Name:"
            }

            TextField {
                id: pathField
                text: "optecs_backups\\" + appstate.currentObserver
                font.pixelSize: 20
                Layout.preferredWidth: 300
                onTextChanged: {
                    successful = false;
                }
            }
        }


        FramLabel {
            id: instructions
            Layout.alignment: Qt.AlignHCenter
            text: "Select a drive letter."
        }

        ProgressBar {
            value: 0.5
            visible: backupInProgress
            Layout.alignment: Qt.AlignCenter
        }

        FramButton {
            // Ideally we'd have signals for success and failure.
            // For simplicity, just parse the return string
            id: performBackup
            Layout.alignment: Qt.AlignHCenter
            text: successful ? "OK" : "Perform\nExternal Backup"
            enabled: false
            fontsize: 20            
            visible: !successful
            onClicked: {
                framHeader.backwardEnable(false);
                backupInProgress = true;
                instructions.text = appstate.backupToPath(backupDrive + backupPath);
            }
        }
        Connections {
            target: appstate
            onBackupStatusChanged: {
                backupInProgress = false;
                control.successful = success
                instructions.text = message;
                framHeader.backwardEnable(true);
            }

        }


    }
}
