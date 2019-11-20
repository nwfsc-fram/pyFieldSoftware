import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.3
import ".."

Item {
    property string action: "weight";
    property alias numPad: numPad;

    signal labelSet(string action, variant value, string uom, bool dbUpdate, variant actionSubType);
    signal advanceTab();

    FramNumPad {
        id: numPad
        x: parent.width/2 - 180
        y: 5
        state: qsTr("weights")
        onNumpadok: {
            labelSet(action, numPad.textNumPad.text, "kg", true, null);
            advanceTab();
        }
    } // numPad
    BackdeckButton2 {
        id: btnSerialPortManager
        text: qsTr("Serial Port\nManager")
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: numPad.right
        anchors.leftMargin: 500
        onClicked: {
            dlgSPM.open();
        }
    }
    BackdeckButton2 {
        id: btnSPMWeightTest
        text: qsTr("Serial Weight\nTest")
        anchors.top: btnSerialPortManager.bottom
//        visible: false
        anchors.topMargin: 10
        anchors.left: numPad.right
        anchors.leftMargin: 500
        onClicked: {
            serialPortManager.serialTest("COM20", "weight", "string of stuff", "10.1kg")
        }
    }
    SerialPortManagerDialog { id: dlgSPM }
}