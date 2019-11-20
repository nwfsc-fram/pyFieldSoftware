import QtQuick 2.4
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQml.Models 2.2

TreeView {
    id: obsTreeView

    property var selModel: selModel
    selection: ItemSelectionModel {
        id: selModel
            model: obsTreeView.model
    }

    style: TreeViewStyle {
        activateItemOnSingleClick: true
        itemDelegate: Item {
            height: textItem.implicitHeight * 1.2
//                width: 300
 //           height: 20
       //     width: textItem.implicitWidth
            Text {
                id: textItem
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: styleData.textAlignment
                anchors.leftMargin: 12
                text: styleData.value
//                    elide: Text.ElideRight
//                    color: "black"
//                    renderType: Text.NativeRendering
                font.pixelSize: 20
            }

            Rectangle {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 1
                anchors.topMargin: 1
                height: 50
//                color: "gray"
//                    color:  styleData.alternate ? "#eeeeee" : "#ffffff"
            }

        }


        rowDelegate: Rectangle {
            height: 50
            color: styleData.selected ? "skyblue" : (styleData.alternate? "#eee" : "#fff")
/*
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    msg.show(control.model.get(styleData.row).species)
                }
            }
*/
        }

        headerDelegate: Rectangle {
            height: textItem.implicitHeight * 1.2
            width: textItem.implicitWidth
//            color: "lightsteelblue"
            gradient: Gradient {
                GradientStop { position: 0.0; color: "white" }
                GradientStop { position: 1.0; color: "lightgray" }
            }
            border.color: "gray"
            border.width: 1
            Text {
                id: textItem
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
//                color: "#ccc"
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "white" }
                    GradientStop { position: 1.0; color: "#eee" }
//                    GradientStop { position: 1.0; color: "lightgray" }
                }
            }
        }
    }
}
