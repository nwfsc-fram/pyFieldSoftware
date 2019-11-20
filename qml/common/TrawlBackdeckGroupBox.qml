import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

GroupBox {
    visible: true
/*
    style: Style {
        property Component panel: Rectangle {
            color: "transparent"
            border.width: 1
//                border.color: "#dddddd"
            Rectangle {
                height: txtObj.height + 10
                width: txtObj.width + 10
                x: txtObj.x - 5
                y: txtObj.y - 5
                color: SystemPaletteSingleton.window(true)
            }
            Text {
                id: txtObj
                anchors.verticalCenter: parent.top
                x: this.x + 10
                text: control.title
                font.pixelSize: 20
            }
        }
    }
*/
}
