import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"
Dialog {
    id: dlg
    width: 500
    height: 400
    title: "Warning"

    property string btnAckText: "Acknowledge\nas is and save"
    property string btnOKText: "Return To Entry"

    property string message: ""
    property alias wrapMode: lblMessage.wrapMode


    contentItem: Rectangle {
        color: "#FA8072"
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
                font.pixelSize: 25
            }
            RowLayout {                
                FramButton {
                    id: btnOkay
                    text: btnOKText
                    Layout.preferredWidth: 200
                    Layout.preferredHeight: 150
                    Layout.alignment: Qt.AlignHCenter
                    fontsize: 20
                    bold: true
                    onClicked: { console.info("User clicked " + btnOkay); dlg.accept() }
                    isDefault: true
                } // btnOkay
                FramButton {
                    id: btnAck
                    text: btnAckText
                    Layout.preferredWidth: 200
                    Layout.preferredHeight: 150
                    Layout.alignment: Qt.AlignHCenter
                    fontsize: 20
                    onClicked: { console.info("User clicked " + btnAckText); dlg.reject(); }
                } // btnOkay
            }
        }

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.accept()
        Keys.onBackPressed: dlg.accept() // especially necessary on Android
    }
}
