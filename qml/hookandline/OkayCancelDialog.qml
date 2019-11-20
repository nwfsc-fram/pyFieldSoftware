import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 400
    height: 180
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "Okay"
//    title: customizeTitle.checked ? windowTitleField.text : "Customized content"

    property string message: "Okay Message"
    property string value: ""
    property string action: "Do you wish to proceed?"
    property string accepted_action: ""

    property alias btnOkay: btnOkay
//    standardButtons: StandardButton.Ok | StandardButton.Cancel

    onRejected: {  }
    onAccepted: {  }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        Label {
            id: lblMessage
            anchors.horizontalCenter: parent.horizontalCenter
            horizontalAlignment: Text.AlignHCenter
            y: 20
            text: message
        } // lblErrors
        Label {
            id: lblValue
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: lblMessage.bottom
            anchors.topMargin: 20
            horizontalAlignment: Text.AlignHCenter
            text: value
//            font.pixelSize: 20
        } // lblAction
        Label {
            id: lblAction
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: lblValue.bottom
            anchors.topMargin: 20
            horizontalAlignment: Text.AlignHCenter
            text: action
//            font.pixelSize: 20
        } // lblAction
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
            } // btnCancel

        } // rwlButtons
        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
}
