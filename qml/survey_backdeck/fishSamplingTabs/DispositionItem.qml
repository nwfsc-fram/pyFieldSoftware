import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.3
import ".."

Item {
    property string action: "disposition"
    property int buttonBaseSize: 80
    property alias numPad: numPad;
    property alias bgDisposition: bgDisposition;

    property alias btnSacrificed: btnSacrificed;
    property alias btnReleased: btnReleased;
    property alias btnDescended: btnDescended;

    property variant type: null
    property variant num: null

    signal labelSet(string action, variant value, string uom, bool dbUpdate, variant actionSubType);
    signal advanceTab();

    function setDisposition(inputType, value) {
        switch (inputType) {
            case "type":
                type = value;
                break;
            case "num":
                num = value;
                break;
        }

        console.info('inside setDisposition: ' + inputType + ', ' + value);

        if (num !== null && num.length < 5) {

            // Pad the number if it is less than 5 digits in length
            var s = "00000" + num;
            num = s.substr(s.length - 5);
            if (s === "00000") {
                numPad.textNumPad.text = "";
                num = null;
            } else {
                numPad.textNumPad.text = num;
            }
        }

        numPad.enabled = (inputType === "type") & (value === "Sacrificed") ? false : true;
        if (value === "Sacrificed") {
            num = null;
            numPad.textNumPad.text = "";
        }
        if (((type !== null) && (num !== null)) || (type === "Sacrificed")) {

            console.info('updating disposition: ' + action + ', ' + num);
            labelSet(action, num, null, true, type);
            advanceTab();
        }
    }
    ColumnLayout {
        spacing: 20
        x: parent.width/4
        anchors.verticalCenter: parent.verticalCenter
        ButtonGroup { id: bgDisposition }
        BackdeckButton2 {
            id: btnSacrificed
            Layout.preferredWidth: buttonBaseSize * 2
            Layout.preferredHeight: buttonBaseSize
            text: qsTr("Sacrificed")
            activeFocusOnTab: false
            ButtonGroup.group: bgDisposition
            checkable: true
            checked: false
            onClicked: { setDisposition("type", "Sacrificed"); }
        } // btnSacrificed
        BackdeckButton2 {
            id: btnReleased
            Layout.preferredWidth: buttonBaseSize * 2
            Layout.preferredHeight: buttonBaseSize
            text: qsTr("Released\nat Surface")
            activeFocusOnTab: false
            ButtonGroup.group: bgDisposition
            checkable: true
            checked: false
            onClicked: { setDisposition("type", "Released"); }
        } // btnReleased
        BackdeckButton2 {
            id: btnDescended
            Layout.preferredWidth: buttonBaseSize * 2
            Layout.preferredHeight: buttonBaseSize
            text: qsTr("Descended")
            activeFocusOnTab: false
            ButtonGroup.group: bgDisposition
            checkable: true
            checked: false
            onClicked: { setDisposition("type", "Descended"); }
        } // btnDescended
    }
    Label {
        text: qsTr("Tag Number")
        font.pixelSize: 20
        anchors.centerIn: parent
        horizontalAlignment: Text.AlignHCenter
        rotation: 270
    }
    FramNumPad {
        id: numPad
        x: parent.width/2 + 40
        y: 5
        enabled: false
        state: qsTr("counts")
        onNumpadok: {
            setDisposition("num", numPad.textNumPad.text);
            if (tbActions.currentIndex < tbActions.count - 1) {
                tbActions.currentIndex = tbActions.currentIndex + 1;
            }
        }
    } // numPad
}
