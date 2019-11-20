import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Controls.Styles 1.4

import "../common"

Rectangle {  // Keyboard containing rectangle
    property int desired_height: 315 // Hidden text field
    property alias hide_ok: keyboardEmbedded.hide_ok // Explicitly hide the OK button
    property alias ok_text: keyboardEmbedded.ok_text
    property FramKeyboard keyboard: keyboardEmbedded

    property alias enable_audio: keyboardEmbedded.enable_audio

    id: keyboardRect
    width: parent.width
    height: desired_height
    color: "#cccccc"
    anchors.bottom: parent.bottom
    anchors.left: parent.left
    anchors.right: parent.right


    signal showbottomkeyboard(bool show)
    onShowbottomkeyboard: {
        keyboardRect.visible = show;
        keyboardRect.height = show ? keyboardRect.height = keyboardRect.desired_height : keyboardRect.height = 0;
    }

    function connect_tf(tf) {  // TextField
        keyboardEmbedded.attach_external_tf(tf);
    }

    function connect_ta(ta) {  // TextArea
        connect_tf(ta);
        // same connection as TextField since it has .text property
    }

    signal buttonOk() // OK button hit
    onButtonOk: {
        showbottomkeyboard(false);
    }

    signal keyEntry() // key entered

    FramKeyboard {
        id: keyboardEmbedded
        x: parent.width / 2
        y: parent.height - 65 - (desired_height - 315)
        state: "embedded_caps"
        Component.onCompleted: {
            hide_tf();
        }
        // Propagate these signals up:
        onKeyboardok: {
            buttonOk();
        }
        onKeyentry: {
            keyEntry();
        }
    }
}
