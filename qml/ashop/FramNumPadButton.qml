// FramNumPadButton.qml

import QtQuick 2.5
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3

import "." // Required for ScreenUnits singleton

// Calls the parent slot for keypad entry
Button {

    property int buttonSize: 85
    property int fontSize: 20
    width: buttonSize
    height: buttonSize
    onClicked: {
        parent.parent.numpadinput(text)
    }
    style: ButtonStyle {

        label: Component {
            Text {
                renderType: Text.NativeRendering
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.family: "Helvetica"
                font.pixelSize: fontSize
                text: control.text
            }
        }
    }
}
