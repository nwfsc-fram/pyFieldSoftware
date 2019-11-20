import QtQuick 2.6
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0

import "."

GroupBox {
    style: Style {
                property Component panel: Rectangle {
                    color: "transparent"
                    border.width: 1
                    Rectangle {
                        height: txtObj.height + 10
                        width: txtObj.width + 10
                        x: txtObj.x - 5
                        y: txtObj.y - 5
                        color: ObserverSettings.default_bgcolor
                    }
                    Text {
                        id: txtObj
                        anchors.verticalCenter: parent.top
                        x: parent.x + 10
                        text: control.title
                        font.pixelSize: 20
                    }
                }
            }
}