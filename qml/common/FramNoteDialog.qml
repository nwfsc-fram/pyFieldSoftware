import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

Dialog {
    id: dlg
    width: 350
    height: 300
    title: "Note"

    property string message: ""
    property alias font_size: lblMessage.font.pixelSize
    property alias wrapMode: lblMessage.wrapMode

    contentItem: Rectangle {
        color: "#eee"
        anchors.fill: parent       
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 50
            Label {
                id: lblMessage
                text: dlg.message
                Layout.fillWidth: true
                Layout.fillHeight: true
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 20
            }
            TrawlBackdeckButton {
                id: btnOkay
                text: "OK"
                Layout.preferredWidth: 100
                Layout.preferredHeight: 50
                Layout.alignment: Qt.AlignHCenter
                onClicked: { dlg.accept() }
            } // btnOkay
        }

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject() // especially necessary on Android
    }
}
