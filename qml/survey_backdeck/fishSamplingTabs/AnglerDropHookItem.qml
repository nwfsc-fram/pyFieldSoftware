import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.3
import ".."

Item {
    property string action: "adh";
    property string angler: "";
    property string drop: "";
    property string hook: "";
    property int buttonBaseSize: 70
    property alias bgAngler: bgAngler;
    property alias bgDrop: bgDrop;
    property alias bgHook: bgHook;

    property alias btnAnglerA: btnAnglerA;
    property alias btnAnglerB: btnAnglerB;
    property alias btnAnglerC: btnAnglerC;
    property alias btnDrop1: btnDrop1;
    property alias btnDrop2: btnDrop2;
    property alias btnDrop3: btnDrop3;
    property alias btnDrop4: btnDrop4;
    property alias btnDrop5: btnDrop5;
    property alias btnHook1: btnHook1;
    property alias btnHook2: btnHook2;
    property alias btnHook3: btnHook3;
    property alias btnHook4: btnHook4;
    property alias btnHook5: btnHook5;

    signal serialPortTest(string action, variant value, string uom, bool dbUpdate);

    signal labelSet(string action, variant value, string uom, bool dbUpdate, variant actionSubType);
    signal advanceTab();
    function setLabel(component, value) {
        switch (component) {
            case "angler":
                angler = value;
                stateMachine.angler = value;
                break;
            case "drop":
                drop = value;
                stateMachine.drop = value;
                break;
            case "hook":
                hook = value;
                stateMachine.hook = value;
                break;
        }
        labelSet(action, angler + drop + hook, null, true, null);
//        serialPortTest(action, angler + drop + hook, null, true);



//        if ((angler !== "") && (drop !== "") && (hook !== "")) {

            // Check if that ADH already exists and if so and if we are dealing with
            // orphaned data, i.e. specimen data that is tied to a site operation and not
            // to a angler operation, if the data should be overwritten or not
//            dlgOkayCancel.message = "You are about to delete this specimen"
//            dlgOkayCancel.action = "Do you wish to proceed?"
//            dlgOkayCancel.accepted_action = "select adh";
//            dlgOkayCancel.open();
//            advanceTab();
//        }
    }
    GridLayout {
        id: glADH
        columns: 3
        rows: 6
        columnSpacing: 60
        rowSpacing: 10
        flow: GridLayout.TopToBottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter

        ButtonGroup { id: bgAngler }
        ButtonGroup { id: bgDrop }
        ButtonGroup { id: bgHook }

        // Column 1
        Label { text: qsTr("Angler"); font.pixelSize: 20; horizontalAlignment: Text.AlignHCenter; }
        BackdeckButton2 {
            id: btnAnglerA
            text: qsTr("A")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgAngler
            checkable: true
            activeFocusOnTab: false
            onClicked: {
                setLabel("angler", text);
            }
        } // btnAnglerA
        BackdeckButton2 {
            id: btnAnglerB
            text: qsTr("B")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgAngler
            checkable: true
            activeFocusOnTab: false
            onClicked: {
                setLabel("angler", text);
            }
        } // btnAnglerB
        BackdeckButton2 {
            id: btnAnglerC
            text: qsTr("C")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgAngler
            checkable: true
            activeFocusOnTab: false
            onClicked: {
                setLabel("angler", text);
            }
        } // btnAnglerC
        Label {}
        Label {}

        // Column 2
        Label { text: qsTr("Drop"); font.pixelSize: 20; horizontalAlignment: Text.AlignHCenter; }
        BackdeckButton2 {
            id: btnDrop1
            text: qsTr("1")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgDrop
            checkable: true
            checked: false
            activeFocusOnTab: false
            onClicked: {
                setLabel("drop", text);
            }
        } // btnDrop1
        BackdeckButton2 {
            id: btnDrop2
            text: qsTr("2")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgDrop
            checkable: true
            checked: false
            activeFocusOnTab: false
            onClicked: {
                setLabel("drop", text);
            }
        } // btnDrop2
        BackdeckButton2 {
            id: btnDrop3
            text: qsTr("3")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgDrop
            checkable: true
            checked: false
            activeFocusOnTab: false
            onClicked: {
                setLabel("drop", text);
            }
        } // btnDrop3
        BackdeckButton2 {
            id: btnDrop4
            text: qsTr("4")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgDrop
            checkable: true
            checked: false
            activeFocusOnTab: false
            onClicked: {
                setLabel("drop", text);
            }
        } // btnDrop4
        BackdeckButton2 {
            id: btnDrop5
            text: qsTr("5")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgDrop
            checkable: true
            checked: false
            activeFocusOnTab: false
            onClicked: {
                setLabel("drop", text);
            }
        } // btnDrop5

        // Column 3
        Label { text: qsTr("Hook"); font.pixelSize: 20; horizontalAlignment: Text.AlignHCenter; }
        BackdeckButton2 {
            id: btnHook1
            text: qsTr("1")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgHook
            checkable: true
            checked: false
            activeFocusOnTab: false
            onClicked: {
                setLabel("hook", text);
            }
        } // btnHook1
        BackdeckButton2 {
            id: btnHook2
            text: qsTr("2")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgHook
            checkable: true
            checked: false
            activeFocusOnTab: false
            onClicked: {
                setLabel("hook", text);
            }
        } // btnHook2
        BackdeckButton2 {
            id: btnHook3
            text: qsTr("3")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgHook
            checkable: true
            checked: false
            activeFocusOnTab: false
            onClicked: {
                setLabel("hook", text);
            }
        } // btnHook3
        BackdeckButton2 {
            id: btnHook4
            text: qsTr("4")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgHook
            checkable: true
            checked: false
            activeFocusOnTab: false
            onClicked: {
                setLabel("hook", text);
            }
        } // btnHook4
        BackdeckButton2 {
            id: btnHook5
            text: qsTr("5")
            Layout.preferredWidth: buttonBaseSize
            Layout.preferredHeight: buttonBaseSize
            ButtonGroup.group: bgHook
            checkable: true
            checked: false
            activeFocusOnTab: false
            onClicked: {
                setLabel("hook", text);
            }
        } // btnHook5
    }
    BackdeckButton2 {
        id: btnSerialPortManager
        text: qsTr("Serial Port\nManager")
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: glADH.right
        anchors.leftMargin: 100
        onClicked: {
            dlgSPM.open();
        }
    }
    BackdeckButton2 {
        id: btnSPMWeightTest
        text: qsTr("Serial ADH\nTest")
        anchors.top: btnSerialPortManager.bottom
//        visible: false
        anchors.topMargin: 10
        anchors.left: btnSerialPortManager.left
        anchors.leftMargin: 0
        onClicked: {
            serialPortManager.serialTest("COM21", "adh", "string of stuff", "A45")
        }
    }
    SerialPortManagerDialog { id: dlgSPM }
}