import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 580
    height: 400
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "Validation Checks"
//    title: customizeTitle.checked ? windowTitleField.text : "Customized content"

//    property string linealType: "length"
//    property real linealValue
//    property real weight
//    property int age
    property string measurement: "Length"
    property real value: 20.0
    property string unit_of_measurement: "cm"
    property string errors: "1.  Bogus length value (a test)"
    property string action: "Do you want to keep this value?"

//    standardButtons: StandardButton.Ok | StandardButton.Cancel

    onRejected: {  }
    onAccepted: {  }
//    onButtonClicked: { console.info("onButtonClicked") }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        Label {
            id: lblMeasurementValue
            x: 20
            y: 20
            text: measurement + ":   " + value + " " + unit_of_measurement
            font.pixelSize: 20
        } // lblMeasurementValue
        Label {
            id: lblErrorTitle
            x: lblMeasurementValue.x
            anchors.top: lblMeasurementValue.bottom
            anchors.topMargin: 30
            text: "The following errors were encountered:"
            font.pixelSize: 20
        } // lblErrors
        Label {
            id: lblErrors
            x: lblMeasurementValue.x
            anchors.top: lblErrorTitle.bottom
            anchors.topMargin: 30
            text: errors
            font.pixelSize: 20
        } // lblErrors
        Label {
            id: lblAction
            x: lblMeasurementValue.x
            anchors.bottom: rwlButtons.top
            anchors.bottomMargin: 20
            text: action
            font.pixelSize: 20
        } // lblAction
        RowLayout {
            id: rwlButtons
            anchors.horizontalCenter: parent.horizontalCenter
            y: dlg.height - this.height - 20
            spacing: 20
            TrawlBackdeckButton {
                id: btnOkay
                text: "Okay"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.accept() }
            } // btnOkay
            TrawlBackdeckButton {
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
