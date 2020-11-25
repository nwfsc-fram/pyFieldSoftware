
// FramMatrixButton.qml

import QtQuick 2.5
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3

import "." // Required for ScreenUnits singleton

// Calls the parent slot for keypad entry
Button {
    width: ScreenUnits.numPadButtonSize
    height: ScreenUnits.numPadButtonSize
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
                font.pixelSize: ScreenUnits.numPadButtonTextHeight
                text: control.text
            }
        }
    }
}