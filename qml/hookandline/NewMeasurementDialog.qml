import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 500
    height: 150
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "New Measurement"

//    property int screen_id: -1
    property string message: ""
    property string action: ""
    property string accepted_action: ""
//    property string screen: ""

    property alias cbMeasurement: cbMeasurement
    property alias cbUnitOfMeasurement: cbUnitOfMeasurement

    onRejected: {  }
    onAccepted: {
        sensorDataFeeds.add_new_measurement(cbMeasurement.editText,
            cbUnitOfMeasurement.editText);
    }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        GridLayout {
            id: gridHeader
            anchors.horizontalCenter: parent.horizontalCenter
            y: 20
            columns: 2
            rows: 2
            columnSpacing: 40
            rowSpacing: 20
            flow: GridLayout.TopToBottom

            Label {
                id: lblMeasurement
                text: qsTr("Measurement")
//                font.pixelSize: 18
            } // lblYear
            Label {
                id: lblUnitOfMeasurement
                text: qsTr("Unit of Measurement")
//                font.pixelSize: 18
            } // lblSamplingType
            ComboBox {
                id: cbMeasurement
                currentIndex: 0
                editable: true
                model: sensorDataFeeds.measurementsModel
                Layout.preferredWidth: 200
            } // cbMeasurement
            ComboBox {
                id: cbUnitOfMeasurement
                currentIndex: 0
                editable: true
                model: sensorDataFeeds.unitsOfMeasurementModel
                Layout.preferredWidth: 200
            } // cbUnitsOfMeasurement
//            TextField {
//                id: tfId
//                text: "001"
//                font.pixelSize: 18
//                Layout.preferredWidth: 60
//                Layout.preferredHeight: 30
//            } // tfId
        } // gridHeader
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
