// FramKeyboardButton.qml

import QtQuick 2.5
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3

//import "." // Required for ScreenUnits singleton

// Calls the parent slot for keyboard entry
Button {
    implicitWidth: parent.buttonWidth
    implicitHeight: parent.buttonHeight

    onClicked: {
        parent.parent.keyentry(text)
    }

    style: ButtonStyle {

        label: Component {
            Text {
                renderType: Text.NativeRendering
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.family: "Helvetica"
                font.pixelSize: 25 // ScreenUnits.keyboardButtonTextHeight
                font.bold: true
                text: control.text
            }
        }
    }
}
