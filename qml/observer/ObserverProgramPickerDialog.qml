import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 400
    height: appstate.users.AvailablePrograms.rowCount() * 70;
    title: "Select Program"

    property string currentProgram: ""

    contentItem: Rectangle {
        color: "#eee"
        anchors.fill: parent       
        ColumnLayout {
            anchors.fill: parent
            Repeater {
                id: rptPrograms
                model: appstate.users.AvailablePrograms
                FramButton {                    
                    text: display
                    fontsize: 19
                    Layout.alignment: Qt.AlignHCenter
                    Layout.fillWidth: true
                    Layout.leftMargin: 10
                    Layout.rightMargin: 10
                    onClicked: {
                        currentProgram = text;
                        dlg.accept()
                    }
                }
            }
        }

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject() // especially necessary on Android
    }
}
