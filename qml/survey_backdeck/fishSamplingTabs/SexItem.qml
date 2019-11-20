import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.3
import ".."

Item {
    property string action: "sex";
    property int buttonBaseSize: 80
    property alias bgSexType: bgSexType;
    property alias btnFemale: btnFemale;
    property alias btnMale: btnMale;
    property alias btnUnsex: btnUnsex;

    signal labelSet(string action, variant value, string uom, bool dbUpdate, variant actionSubType);
    signal advanceTab();

    function changeSex(value) {
        labelSet(action, value, null, true, null);
        advanceTab();
    }
    RowLayout {
        id: rlSex
        spacing: 20
        Layout.fillWidth: false
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        ButtonGroup { id: bgSexType }
        BackdeckButton2 {
            id: btnFemale
            text: qsTr("Female")
            checkable: true
            ButtonGroup.group: bgSexType
            Layout.preferredWidth: buttonBaseSize * 2
            Layout.preferredHeight: buttonBaseSize
            onClicked: changeSex("F")
            activeFocusOnTab: false
        } // btnFemale
        BackdeckButton2 {
            id: btnMale
            text: qsTr("Male")
            checkable: true
            ButtonGroup.group: bgSexType
            Layout.preferredWidth: buttonBaseSize * 2
            Layout.preferredHeight: buttonBaseSize
            onClicked: changeSex("M")
            activeFocusOnTab: false
        } // btnMale
        BackdeckButton2 {
            id: btnUnsex
            text: qsTr("Unsex")
            checkable: true
            ButtonGroup.group: bgSexType
            Layout.preferredWidth: buttonBaseSize * 2
            Layout.preferredHeight: buttonBaseSize
            onClicked: changeSex("U")
            activeFocusOnTab: false
        } // btnUnsex
    }
}