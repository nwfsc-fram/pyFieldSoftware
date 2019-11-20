import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4

Button {
    Layout.preferredWidth: idEntry.default_width / 2
    Layout.preferredHeight: buttonLogin.height
    Layout.alignment: Qt.AlignCenter
    property int font_size: 20
    style: ButtonStyle {
        label: Text {
            id: textButton
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.family: "Helvetica"
            font.pixelSize: font_size
            color: "black"
            text: control.text
        }
        background: Rectangle {
            implicitWidth: 100
            implicitHeight: 25
            border.width: checked ? 4 : 1
            border.color: checked ? "black" : "gray"
            radius: 4
            color: checked || control.pressed ? "white" : "lightgray"
        }
    }
    checkable: true
}
