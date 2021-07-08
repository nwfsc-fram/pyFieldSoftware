import QtQuick 2.7
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.3
import QtQuick.Controls.Styles 1.2

Item {
    property string hookNumber: "5"
    property alias tfHook: tfHook

    signal currentHookChanged(string hookNumber);

    implicitWidth: clHook.implicitWidth
    implicitHeight: clHook.implicitHeight

    ColumnLayout {
        id: clHook
        spacing: 0
        Label {
            text: "Hook " + hookNumber
            font.pixelSize: 24
            font.underline: true
            horizontalAlignment: Text.AlignHCenter
            Layout.preferredWidth: 200
            Layout.preferredHeight: 40
            Layout.alignment: Qt.AlignRight
        }
        RowLayout {
            spacing: 10
            BackdeckButton {
                text: qsTr("X")
                Layout.preferredWidth: 60
                Layout.preferredHeight: 60
                onClicked: {
                    currentHookChanged(hookNumber);
                    hooks.deleteHook(hookNumber, tfHook.text)
                    tfHook.text = ""
                    tfHook.forceActiveFocus();
                    tfHook.color = "yellow";
                }
            }
            TextField {
                id: tfHook
//                placeholderText: "Hook " + hookNumber
                font.pixelSize: 24
                font.bold: hooks.isFish(tfHook.text)  // #82: bold fish items
                Layout.preferredWidth: 200
                Layout.preferredHeight: 60
                property string color: "white"
                onEditingFinished: {
                    tfHook.color = "white";
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked:{
                        parent.color = "yellow";
                        parent.forceActiveFocus();
                        parent.cursorPosition = 0;
                        currentHookChanged(hookNumber);
                    }
                }
                style: TextFieldStyle {
                    textColor: hooks.isFish(tfHook.text) ? "green" : "black"  // #82: highlight fish green
                    background: Rectangle {
//                        radius: 2
//                        implicitWidth: 100
//                        implicitHeight: 24
//                        border.color: "#333"
//                        border.width: 1
                        color: tfHook.color
                    }
                }
            }
        } // tfHook5
    }

}