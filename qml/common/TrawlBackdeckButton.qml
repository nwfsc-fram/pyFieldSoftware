import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

Button {
    id: btnMaster
    width: 120
    height: 60

    property string grdTopColor: "white"
    property string grdBottomColor: "#eee"
    property string txtColor: "black"

    style: ButtonStyle {
        label: Text {
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.family: "Helvetica"
            font.pixelSize: 20
            color: txtColor
            text: control.text
        }
        background: Rectangle {
            border.width: control.activeFocus ? 2 : 1
            border.color: "#888"
            radius: 3
            gradient: Gradient {
//                GradientStop { position: 0 ; color: control.pressed ? "#ccc" : "#eee" }
//                GradientStop { position: 1 ; color: control.pressed ? "#aaa" : "#ccc" }
//                GradientStop { position: 0; color: control.pressed || (control.checkable && control.checked) ? "#ddd" : "white" }
//                GradientStop { position: 1 ; color: control.pressed || (control.checkable && control.checked) ? "#bbb" : "#ddd" }
//                GradientStop { position: 0; color: control.pressed || (control.checkable && control.checked) ? "#aaa" : "white" }
//                GradientStop { position: 0.2; color: control.pressed || (control.checkable && control.checked) ? "#ccc" : "#eee" }
                GradientStop { position: 0; color: control.pressed || (control.checkable && control.checked) ? "#aaa" : grdTopColor }
                GradientStop { position: 0.5; color: control.pressed || (control.checkable && control.checked) ? "#ccc" : grdBottomColor }
            }
        }
    }

    states: [
        State {
            name: "enabled"
            PropertyChanges {
                target: btnMaster
                enabled: true
                txtColor: "black"
                grdTopColor: "white"
                grdBottomColor: "#eee"
            }
        },
        State {
            name: "disabled"
            PropertyChanges {
                target: btnMaster
                enabled: false
                txtColor: "gray"
//                grdTopColor: "lightgray"
//                grdBottomColor: "lightgray"
                grdTopColor: "#ccc"
                grdBottomColor: "#ccc"
            }
        }
    ]
}
