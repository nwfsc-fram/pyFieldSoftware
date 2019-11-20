import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

import "../common"

// bug https://bugreports.qt.io/browse/QTBUG-49360 show width binding loop
TableView {
    property int item_height: 50
    horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
    verticalScrollBarPolicy: Qt.ScrollBarAlwaysOff

    style: TableViewStyle {

        itemDelegate: Item {
            height: itextItem.implicitHeight * 1.2

            Text {
                id: itextItem
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: styleData.textAlignment
                anchors.leftMargin: 12
                text: styleData.value ? styleData.value : ""
                elide: Text.ElideRight
                font.pixelSize: 20
            }

            Rectangle {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 1
                anchors.topMargin: 1
                height: item_height
            }
        }

        rowDelegate: Rectangle {
            height: item_height
            color: styleData.selected ? "skyblue" : (styleData.alternate? "#eee" : "#fff")
            Text {
                id: txtRect
                elide: Text.ElideRight
            }
        }

        headerDelegate: Rectangle {
            height: htextItem.implicitHeight * 1.2
            width: htextItem.implicitWidth
            gradient: Gradient {
                GradientStop { position: 0.0; color: "white" }
                GradientStop { position: 1.0; color: "lightgray" }
            }
            border.color: "gray"
            border.width: 1
            Text {
                id: htextItem
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: styleData.textAlignment
                anchors.leftMargin: 12
                text: styleData.value
                elide: Text.ElideRight
                color: textColor
                renderType: Text.NativeRendering
                font.pixelSize: 20
            }
            Rectangle {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 1
                anchors.topMargin: 1
                width: 1
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "white" }
                    GradientStop { position: 1.0; color: "#eee" }
                }
            }
        }
    }
}
