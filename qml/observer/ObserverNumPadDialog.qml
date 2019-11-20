import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.2

import "../common"

Dialog {
    id: dlgNumPad
    width: 360
    height: 470
    title: placeholderText
    property var placeholderText: ""
    property int max_digits: -1
    property bool decimal: false

    property alias enable_audio: numPad.enable_audio
    signal valueAccepted(var accepted_value)

    function clearnumpad() {
        numPad.clearnumpad();
    }

    function setValue(value) {
        numPad.setnumpadvalue(value);
    }

    onVisibleChanged: {
        if (visible) {
            numPad.textNumPad.selectAll();
            if (decimal) {
                numPad.state = "decimal";
            }
        }
    }

    contentItem: Rectangle {
        id: contentLayout

        ObserverNumPad {
            id: numPad
            anchors.fill: parent
            max_digits: dlgNumPad.max_digits
            placeholderText: dlgNumPad.placeholderText
            enable_audio: false
            onNumpadok: {
                dlgNumPad.valueAccepted(text_result);
                close();
            }
        }

        Keys.onEnterPressed: dlgNumPad.accept()
        Keys.onReturnPressed: dlgNumPad.accept()
        Keys.onEscapePressed: dlgNumPad.accept()
        Keys.onBackPressed: dlgNumPad.accept() // especially necessary on Android
    }



}
