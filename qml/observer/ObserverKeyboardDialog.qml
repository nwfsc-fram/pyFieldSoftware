import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.2

import "."
import "../common"

Dialog {
    id: dlgKeyboard
    width: 660
    height: 470
    title: placeholderText
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

    contentItem: Rectangle {
        id: contentLayout
        anchors.fill: parent
        FramScalingKeyboard {
            id: keyPad
            anchors.fill: parent
            placeholderText: dlgKeyboard.placeholderText
            enable_audio: ObserverSettings.enableAudio
            onKeyboardok: {
                dlgKeyboard.valueAccepted(keyboard_result);
                if(connected_tf) {
                    connected_tf.text = keyboard_result;
                    connected_tf.editingFinished();
                }
                connected_tf = null;
                dlgKeyboard.passwordMode = false;
                close();
            }
        }

        Keys.onEnterPressed: dlgKeyboard.accept()
        Keys.onReturnPressed: dlgKeyboard.accept()
        Keys.onEscapePressed: dlgKeyboard.accept()
        Keys.onBackPressed: dlgKeyboard.accept() // especially necessary on Android
    }



}
