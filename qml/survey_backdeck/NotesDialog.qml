import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.2

//import "../common"

Dialog {
    id: dlgKeyboard
    width: 760
    height: 550
    title: placeholderText

    modality: Qt.ApplicationModal

    property var placeholderText: ""
    property int max_digits: -1
    property bool decimal: false
    property bool passwordMode: false

    property TextField connected_tf: null
    signal valueAccepted(var accepted_value)

    onVisibleChanged: {
        if (visible) {
            if(connected_tf) {
                //keyPad.textNumPad.text = connected_tf.text;
                keyPad.attach_external_tf(connected_tf, placeholderText);
            }
            keyPad.selectAll();
        }
    }

    function set_caps(is_caps) {
        if (is_caps) {
            keyPad.setkeyboardcaps();
        } else {
            keyPad.setkeyboardlowercase();
        }
    }

    onPasswordModeChanged: {
        keyPad.password_mode(passwordMode);
    }

    property int rlHeight: 40;
    property int rlWidth: 160;
    property int rlPixelSize: 20;

    contentItem: Rectangle {
        id: contentLayout
        ColumnLayout {
            spacing: 20
            RowLayout {
                id: rlInfo
                anchors.top: parent.top
                anchors.topMargin: 10
                spacing: 40
//                Label {
//                    text: stateMachine.appName ? "App: " + stateMachine.appName : "App: "
//                    font.pixelSize: rlPixelSize;
//                    Layout.preferredHeight: rlHeight;
//                } // appName
//                Label {
//                    text: stateMachine.siteOpId ? "Site Op ID: " + stateMachine.siteOpId :
//                        "Site Op ID: "
//                    font.pixelSize: rlPixelSize;
//                    Layout.preferredHeight: rlHeight;
//                } // siteOpId
//                Label {
//                    text: stateMachine.screen ? "Screen: " + stateMachine.screen.substr(0, 9) :
//                        "Screen: "
//                    font.pixelSize: rlPixelSize;
//                    Layout.preferredHeight: rlHeight;
//                } // screen
                Label {
                    text: stateMachine.angler ?
                        "Angler: " + stateMachine.angler :
                        "Angler: "
                    font.pixelSize: rlPixelSize;
                    Layout.preferredHeight: rlHeight;
                } // angler
                Label {
                    text: stateMachine.drop ? "Drop: " + stateMachine.drop :
                        "Drop: "
                    font.pixelSize: rlPixelSize;
                    Layout.preferredHeight: rlHeight;
                } // drop
                Label {
                    text: stateMachine.hook ? "Hook: " + stateMachine.hook :
                        "Hook: "
                    font.pixelSize: rlPixelSize;
                    Layout.preferredHeight: rlHeight;
                } // hook
                Label {
                    text: stateMachine.currentEntryTab ? "Observation: " + stateMachine.currentEntryTab :
                        "Observation: "
                    font.pixelSize: rlPixelSize;
                    Layout.preferredHeight: rlHeight;
                } // observation
            }
            FramScalingKeyboard {
                id: keyPad
                anchors.top: rlInfo.bottom
                anchors.topMargin: 40
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                state: "lowercase_state"
//                anchors.fill: parent
                placeholderText: dlgKeyboard.placeholderText
                onKeyboardok: {
                    dlgKeyboard.valueAccepted(keyboard_result);
                    notes.insertNote(stateMachine.appName, stateMachine.screen, keyboard_result,
                        stateMachine.siteOpId, stateMachine.drop, stateMachine.angler,
                        stateMachine.hook, stateMachine.currentEntryTab);

                    if(connected_tf) {
                        connected_tf.text = keyboard_result;
                        connected_tf.editingFinished();
                    }
                    connected_tf = null;
                    dlgKeyboard.passwordMode = false;

                    close();
                }
            }
        }

        Keys.onEnterPressed: dlgKeyboard.accept()
        Keys.onReturnPressed: dlgKeyboard.accept()
        Keys.onEscapePressed: dlgKeyboard.accept()
        Keys.onBackPressed: dlgKeyboard.accept() // especially necessary on Android
    }



}
