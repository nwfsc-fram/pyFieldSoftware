import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

//import "../common"

Dialog {
    id: dlg
    width: 580
    height: 200
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "Confirm"
//    title: customizeTitle.checked ? windowTitleField.text : "Customized content"

//    property string linealType: "length"
//    property real linealValue
//    property real weight
//    property int age

    property string message: "Message"
    property string action: "Do you wish to proceed?"
    property string actionType: "delete"
    property string accepted_action: ""

    property alias btnCancel: btnCancel
    property alias btnOkay: btnOkay
//    standardButtons: StandardButton.Ok | StandardButton.Cancel

    onRejected: {  }
    onAccepted: {  }
//    onButtonClicked: { console.info("onButtonClicked") }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        Label {
            id: lblMessage
            anchors.horizontalCenter: parent.horizontalCenter
            horizontalAlignment: Text.AlignHCenter
            y: 20
//            anchors.top: lblErrorTitle.bottom
//            anchors.topMargin: 30
            text: message
            font.pixelSize: 20
        } // lblErrors
        Label {
            id: lblAction
//            x: lblMeasurementValue.x
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: rwlButtons.top
            anchors.bottomMargin: 20
            horizontalAlignment: Text.AlignHCenter
            text: action
            font.pixelSize: 20
        } // lblAction
        RowLayout {
            id: rwlButtons
            anchors.horizontalCenter: parent.horizontalCenter
            y: dlg.height - this.height - 20
            spacing: 20
            BackdeckButton {
                id: btnOkay
                text: "Okay"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.accept() }
            } // btnOkay
            BackdeckButton {
                id: btnCancel
                text: "Cancel"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.reject() }
            } // btnCancel
        } // rwlButtons

//        Keys.onPressed: if (event.key === Qt.Key_R && (event.modifiers & Qt.ControlModifier)) dlg.click(StandardButton.Retry)
        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject() // especially necessary on Android
    }
}
