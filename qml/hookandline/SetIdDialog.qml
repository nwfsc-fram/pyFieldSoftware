import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 380
    height: 250
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "Set ID"

//    property int screen_id: -1
    property string message: ""
    property string action: ""
    property string accepted_action: ""
//    property string screen: ""

    property int day_of_cruise: -1
    property string date: ""
    property bool include_in_survey
    property bool is_mpa
    property bool is_rca

    property int sequence
    property int camera_sequence
    property int test_sequence
    property int software_test_sequence

    property alias tfYear: tfYear
    property alias cbSamplingType: cbSamplingType
//    property alias cbVesselNumber: cbVesselNumber
    property alias tfId: tfId

    onRejected: {  }
    onAccepted: {  }

    function getNextSequenceNumber() {
        if (cbSamplingType.currentText.indexOf("Camera Drop") >= 0) {
            if (camera_sequence > 0)
                return ("000" + (camera_sequence + 1).toString()).slice(-3);
        } else if (cbSamplingType.currentText.indexOf("Test Drop") >= 0) {
            console.info('inside test drop');
            if (test_sequence > 0) {
                console.info('test seq > 0');
                return ("000" + (test_sequence + 1).toString()).slice(-3);
            }
        } else if (cbSamplingType.currentText.indexOf("Software Test") >= 0) {
            console.info('software test');
            if (software_test_sequence > 0) {
                console.info('software test seq > 0');
                return ("000" + (software_test_sequence + 1).toString()).slice(-3);
            }
        } else {
            if (sequence > 0)
                return ("000" + (sequence + 1).toString()).slice(-3);
        }
        return "001"
    }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        GridLayout {
            id: gridHeader
            anchors.horizontalCenter: parent.horizontalCenter
            y: 20
            columns: 2
            rows: 4
            columnSpacing: 40
            rowSpacing: 20
            flow: GridLayout.TopToBottom

            Label {
                id: lbYear
                text: qsTr("Year")
            } // lblYear
            Label {
                id: lblSamplingType
                text: qsTr("Sampling Type")
            } // lblSamplingType
            Label {
                id: lblVesselNumber
                text: qsTr("Vessel Number")
            } // lblVesselNumber
            Label {
                id: lblId
                text: qsTr("ID")
            } // lblId
            TrawlBackdeckTextFieldDisabled {
                id: tfYear
                text: (new Date().getFullYear()).toString().substr(2,2)
                font.pixelSize: 11
                readOnly: true
                Layout.preferredWidth: 60
                Layout.preferredHeight: 30
            } // tfYear
            ComboBox {
                id: cbSamplingType
                currentIndex: 0
                model: fpcMain.samplingTypesModel
            } // cbSamplingType
            TextField {
                id: tfVesselNumber
//                currentIndex: 0
//                model: fpcMain.vesselsModel
                text: fpcMain.vesselNumber + " - " + fpcMain.vesselName
                enabled: false
            } // tfVesselNumber
            TextField {
                id: tfId
                text: getNextSequenceNumber()
//                font.pixelSize: 18
                Layout.preferredWidth: 60
                Layout.preferredHeight: 30
            } // tfId
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
                onClicked: {
                    if (tfId.text.length != 3) {
                        dlgOkay.message = "The ID should be three digits long"
                        dlgOkay.value = tfId.text;
                        dlgOkay.action = "Please correct"
                        dlgOkay.open()
                        return;
                    }

                    var set_id = tfYear.text +
                        cbSamplingType.model.get(cbSamplingType.currentIndex)["sampling_type_number"] +
                        tfVesselNumber.text.split("-")[0].trim() +
                        tfId.text;
//                    var set_id = tfYear.text +
//                        cbSamplingType.model.get(cbSamplingType.currentIndex)["sampling_type_number"] +
//                        cbVesselNumber.model.get(cbVesselNumber.currentIndex)["vessel_number"] +
//                        tfId.text;

                    var exists = fpcMain.check_for_duplicate_operation(set_id);

                    if (exists) {
                        dlgOkay.message = "You attempted to create a Set ID that already exists"
                        dlgOkay.value = set_id;
                        dlgOkay.action = "Please select a different Set ID"
                        dlgOkay.open()
                    } else {
                        // Insert a new OPERATIONS table record
                        fpcMain.add_operations_row(set_id, day_of_cruise, date, include_in_survey, is_mpa, is_rca);
                        tfSetId.text = set_id
                        dlg.accept()
                    }
                }
            } // btnOkay
            Button {
                id: btnCancel
                text: "Cancel"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.reject() }
            } // btnCancel
        } // rwlButtons

//        Keys.onEnterPressed: dlg.accept()
        Keys.onEnterPressed: btnOkay.clicked()
        Keys.onReturnPressed: btnOkay.clicked()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()

        states: [
            State {
                name: "original"
//                PropertyChanges { target: taNote; text: ""}
            }, // general
            State {
                name: "haulLevelValidation"
//                PropertyChanges { target: btnHaulLevelValidationType; checked: true}
//                PropertyChanges { target: taNote; implicitWidth: dlg.width - 40; implicitHeight: dlg.height - rwlButtons.height - 60}
//                PropertyChanges { target: colTypes; enabled: false; visible: false}
            } // haulLevelValidation
        ]

    }
}
