import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

Button {
    property int fontsize: 16
    property bool bold: false
    checkable: true
    style: ButtonStyle {
        label: Text {
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.family: "Helvetica"
            font.pixelSize: fontsize
            color: "black"
            text: control.text
        }
    }
}
