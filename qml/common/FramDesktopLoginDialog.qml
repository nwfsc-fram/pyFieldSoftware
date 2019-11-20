import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 480
    height: 200
    title: "Login"
    property alias btnOkay: btnOkay
    property alias tfUsername: tfUsername

    onRejected: {  }
    onAccepted: {
        settings.login(tfUsername.text, tfPassword.text)
    }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        Label {
            id: lblMessage
            anchors.horizontalCenter: parent.horizontalCenter
            horizontalAlignment: Text.AlignHCenter
            y: 20
            text: qsTr("Login")
            font.pixelSize: 14
        } // lblErrors
        GridLayout {
            id: grlLogin
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: lblMessage.bottom
            anchors.topMargin: 20
            columnSpacing: 20
            rowSpacing: 20
            rows: 2
            columns: 2
            Label {
                id: lblUsername
                text: qsTr("Username")
            }
            TextField {
                id: tfUsername
                Layout.preferredWidth: 160
                text: settings.username

            } // tfUsername
            Label {
                id: lblPassword
                text: qsTr("Password")
            }
            TextField {
                id: tfPassword
                text: settings.password
                echoMode: TextInput.Password
                Layout.preferredWidth: 160
            } // tfPassword
        }

        RowLayout {
            id: rwlButtons
            anchors.horizontalCenter: parent.horizontalCenter
            y: dlg.height - this.height - 20
            spacing: 20
            Button {
                id: btnOkay
                text: "Okay"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.accept() }
            } // btnOkay
            Button {
                id: btnCancel
                text: "Cancel"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.reject() }
            } // btnOkay
        } // rwlButtons

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
}
