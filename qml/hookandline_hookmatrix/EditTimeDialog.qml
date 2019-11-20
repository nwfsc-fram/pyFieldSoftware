import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

//import "../common"

Dialog {
    id: dlg
    width: 380
    height: 620
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "Confirm"
//    title: customizeTitle.checked ? windowTitleField.text : "Customized content"

    property string currentMinutes: "00"
    property string currentSeconds: "00"
    property alias numPad: numPad;
    property variant editedButton;
    property alias btnCancel: btnCancel
    property alias btnOkay: btnOkay
    onRejected: {  }
    onAccepted: {  }
    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        ColumnLayout {
            anchors.horizontalCenter: parent.horizontalCenter
            RowLayout {
                id: rlCurrentData
                Label {
                    id: lblTimeLabel
                    text: qsTr("Current Time:")
                    font.pixelSize: 30
                    verticalAlignment: Text.AlignVCenter
                    Layout.preferredWidth: 200
                    Layout.preferredHeight: 80
                } // lblTimeLabel
                Label {
                    id: lblCurrentTime
                    text: currentMinutes + ":" + currentSeconds
                    font.pixelSize: 30
                    verticalAlignment: Text.AlignVCenter
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 80
                } // lblCurrentTime
            }

            NumPad {
                id: numPad
                minutes: currentMinutes;
                seconds: currentSeconds;
            } // numPad
            RowLayout {
                id: rlButtons
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
            } // rlButtons

        }
//        Keys.onPressed: if (event.key === Qt.Key_R && (event.modifiers & Qt.ControlModifier)) dlg.click(StandardButton.Retry)
        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject() // especially necessary on Android
    }
}
