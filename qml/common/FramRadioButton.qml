import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

RadioButton {
    property int fontsize: 16
    style: RadioButtonStyle  {
////        background: Rectangle {
////            implicitWidth: 200
////            implicitHeight: 50
////            border.width: control.activeFocus ? 2 : 1
////            border.color: "#888"
////            radius: 4
////            gradient: Gradient {
////                GradientStop { position: 0 ; color: control.pressed ? "#ccc" : "#eee" }
////                GradientStop { position: 1 ; color: control.pressed ? "#aaa" : "#ccc" }
////            }
////        }
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
