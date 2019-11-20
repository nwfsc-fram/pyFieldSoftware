import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.3

import "."

Button {
    y: 0
    width: 60
    height: 40
    checked: false
    checkable: true
    style: ButtonStyle {
        label: Text {
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.family: "Helvetica"
            font.pixelSize: 20
            text: control.text            
        }
    }
}
