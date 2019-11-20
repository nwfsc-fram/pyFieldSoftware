// "Big" Keyboard *without* scrollable autocomplete list. For landscape screen mode.

import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Controls.Styles 1.4

import "."

Rectangle {  // Encompasses just a keyboard - no autocomplete list to the right.
    id: keyboardRect
    width: parent.width
    height: desired_height
    x: 0
    y: parent.y + parent.height - height
    color: "#AAAAAA"

    property int desired_height: 315 // Hidden text field
    property FramScalingKeyboard keyboard: keyboardEmbedded
    property TextField active_tf: keyboardEmbedded.active_tf
    property int fontsize: 25
    property bool opaque: false
    property bool autocomplete_active: true
    property bool mandatory_autocomplete: false
    property alias enable_audio: keyboardEmbedded.enable_audio


    Keys.forwardTo: [keyboardEmbedded]

    FramScalingKeyboard {
        id: keyboardEmbedded
        width: parent.width
        height: parent.height
        anchors.fill: parent
        state: "embedded_lower"
        cancel_only: keyboardRect.mandatory_autocomplete
        enable_audio: false

        // Propagate these signals up:
        onKeyboardok: {
            buttonOk();
        }
        onKeyboardCancel: {
            buttonCancel();
        }

        onKeyentry: {
            keyEntry();

        }
        onKbTextChanged: {
            //addAutoCompleteSuggestions(kbtext);
        }
    }

    signal showbottomkeyboard(bool show)
    onShowbottomkeyboard: {
        keyboardRect.visible = show;
        keyboardRect.height = show ? keyboardRect.height = keyboardRect.desired_height : keyboardRect.height = 0;
    }

    function connect_tf(tf, placeholder) {  // TextField
        keyboardEmbedded.attach_external_tf(tf, placeholder);
        active_tf.forceActiveFocus();
        keyboardEmbedded.selectAll();
    }

    function connect_ta(ta) {  // TextArea
        connect_tf(ta);
        // same connection as TextField since it has .text property
    }

    signal buttonOk() // OK button hit
    onButtonOk: {
        showbottomkeyboard(false);
    }

    signal buttonCancel() // Cancel button hit
    onButtonCancel: {
        showbottomkeyboard(false);
    }

    signal keyEntry() // key entered

    function password_mode(is_set) {
        keyboardEmbedded.password_mode(is_set);
    }
}
