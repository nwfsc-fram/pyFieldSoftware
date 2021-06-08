import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

Button {
    id: framButton
    property int fontsize: 16
    property bool bold: false
    property color text_color: "black"
    property int implicitWidth: 200  // default width val

    style: ButtonStyle {
        id: framStyle
        background: Rectangle {
            implicitWidth: framButton.implicitWidth
            implicitHeight: 50
            border.width: control.activeFocus ? 2 : 1
            border.color: "#888"
            radius: 4
            gradient: Gradient {
                GradientStop { position: 0 ; color: control.pressed ? "#ccc" : "#eee" }
                GradientStop { position: 1 ; color: control.pressed ? "#aaa" : "#ccc" }
            }
        }
        label: Text {
            id: lblText
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.family: "Helvetica"
            font.pixelSize: fontsize
            font.bold: bold
            color: text_color
            text: control.text
        }
    }
}
