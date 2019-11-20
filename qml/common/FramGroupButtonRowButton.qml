import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2

import "../common"
import "."

Button {
    id: button
    width: parent.bwidth // custom property
    height: parent.height
    property int font_size: 20
    style: ButtonStyle {
        label: Text {
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.family: "Helvetica"
            font.pixelSize: button.font_size
            color: "black"
            text: control.text
        }
    }
    checkable: true
}
