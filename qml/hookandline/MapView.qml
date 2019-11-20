import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1

SplitView {
    id: splitView1
    x: 0
    y: 0

//    width: parent.width
//    height: parent.height

    Rectangle {
        id: leftPanel
        width: 300
        Layout.minimumWidth: 300
        Layout.maximumWidth: 300

//            TreeView {
//                TableViewColumn {
//                    title: "Name"
//                    role: "fileName"
//                    width: 300
//                }
//                TableViewColumn {
//                    title: "Permissions"
//                    role: "filePermissions"
//                    width: 100
//                }
//                model: fileSystemModel
//            }

    }

    Rectangle {
        id: centerPanel
        Layout.fillWidth: true

        Button {
            iconSource: "qrc:/resources/images/btn_dragnor.png"
        }
        Button {
            iconSource: "qrc:/resources/images/btn_frameselectnor.png"
        }

        MouseArea {
            width: parent.width
            height: parent.height

        }

    }
}


