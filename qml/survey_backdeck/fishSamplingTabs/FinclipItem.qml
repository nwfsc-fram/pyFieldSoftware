import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.3
import ".."

Item {
    property string action: "finclipID"
    property bool finclipRecExists: false
    property int buttonBaseSize: 80
    property alias numPad: numPad;
    property string type: ""
    property variant num: null

    property variant lastFinclipID: null;

    property alias bgFinclipCategory: bgFinclipCategory;

    property alias btnFinclipA: btnFinclipA;
    property alias btnFinclipB: btnFinclipB;
//    property alias btnFinclipG: btnFinclipG;
    property alias btnFinclipV: btnFinclipV;

    signal labelSet(string action, variant value, string uom, bool dbUpdate, variant actionSubType);
    signal advanceTab();

    function setDescriptor(descriptor) {
        // Method to set just the age descriptor (i.e. B, V, or A)
        type = descriptor;
        switch (descriptor) {
            case "B":
                btnFinclipB.checked = true;
                break;
            case "V":
                btnFinclipV.checked = true;
                break;
            case "A":
                btnFinclipA.checked = true;
                break;
            default:
                btnFinclipB.checked = false;
                btnFinclipV.checked = false;
                btnFinclipA.checked = false;
                break;
        }
    }

    function validateEntries() {
        var isInvalid = false;
        var msg = "";

        // Check if the number is missing, if so then delete the record
        if ((num === null) || (num === "")) {
            var specimenID = parent.retrieveSpecimenID();
            num = null;
            fishSampling.deleteSpecimenObservation(specimenID, "Finclip ID", null, false);
            labelSet(action, "", null, false, null);
            finclipRecExists = false;
            return;
        }

        // Check if the type is missing
        if (type === "") {
            isInvalid = true;
            msg = "Type is missing, should be B, V, or A";
        }

        // Pad the number if it is less than 4 digits in length
        if (num.length < 4) {
            var s = "0000" + num;
            num = s.substr(s.length-4);
            numPad.textNumPad.text = num;
        }

        // Check if this ID already exists in the database
        var existsResult = fishSampling.checkIfIDExists("Finclip ID", type + num);
        if ((existsResult.status === "invalid") || (existsResult.status === "found")) {
            isInvalid = true;
            msg = existsResult.msg;
        }

        // Check if finclipID !== ageID
        var ageID = parent.retrieveAgeID();
        if ((ageID !== null) && (ageID.type !== "") && (ageID.num !== null) &&
            ((ageID.type !== type) || (ageID.num !== num)) ) {
            isInvalid = true;
            msg = "FinclipID does not equal AgeID\n" + type + num + " <> " + ageID.type + ageID.num;
        }

        // Check if the descriptor is wrong
        var species = parent.retrieveSpecies();
        if (species !== null) {
            switch (species.replace("\n", " ")) {
                case "Bocaccio":
                    if (!btnFinclipB.checked) {
                        isInvalid = true;
                        msg = species.replace("\n", " ") + " is selected, however B is not"
                    }
                    break;
                case "Vermilion Rockfish":
                    if (!btnFinclipV.checked) {
                        isInvalid = true;
                        msg = species.replace("\n", " ") + " is selected, however V is not"
                    }
                    break;
                default:
                    if (!btnFinclipA.checked) {
                        isInvalid = true;
                        msg = species.replace("\n", " ") + " is selected, however A is not"
                    }
                    break;
            }
        } else {
            isInvalid = true;
            msg = "You must select a species before entering an Age"
        }

        // If anything is invalid, show warning and halt processing
        if (isInvalid) {
            dlgOkay.message = msg;
            dlgOkay.action = "Please fix";
            dlgOkay.open();
            return;
        }

        // Check if a sequence gap exists.  Note that this can be overwritten if one does exist
        if (existsResult.status === "sequence gap") {
            dlgOkayCancel.actionType = "sequenceGapCheck";
            dlgOkayCancel.message = existsResult.msg;
            dlgOkayCancel.action = "Do you want to save this value anyways?";
            dlgOkayCancel.open();
            return;
        }

        setFinclip();
    }

    function setFinclip() {
        labelSet(action, type + num, null, true, null);
        finclipRecExists = true;
        advanceTab();
    }
    ColumnLayout {
        id: clFinclipCategory
//                            anchors.horizontalCenter: parent.horizontalCenter
        x: parent.width/4
        anchors.verticalCenter: parent.verticalCenter
        spacing: 20
        ButtonGroup { id: bgFinclipCategory }
        BackdeckButton2 {
            id: btnFinclipB
            text: qsTr("B")
            Layout.preferredHeight: buttonBaseSize
            Layout.preferredWidth: buttonBaseSize * 2
            checkable: true
            checked: false
            ButtonGroup.group: bgFinclipCategory
            activeFocusOnTab: false
            onClicked: {
                type = "B";
//                setFinclip("type", "B");
            }
        } // btnFinclipB
        BackdeckButton2 {
            id: btnFinclipV
            text: qsTr("V")
            Layout.preferredHeight: buttonBaseSize
            Layout.preferredWidth: buttonBaseSize * 2
            checkable: true
            checked: false
            ButtonGroup.group: bgFinclipCategory
            activeFocusOnTab: false
            onClicked: {
                type = "V";
//                setFinclip("type", "V");
            }
        } // btnFinclipV
//        BackdeckButton2 {
//            id: btnFinclipG
//            text: qsTr("G")
//            Layout.preferredHeight: buttonBaseSize
//            Layout.preferredWidth: buttonBaseSize * 2
//            checkable: true
//            checked: false
//            ButtonGroup.group: bgFinclipCategory
//            activeFocusOnTab: false
//            onClicked: {
//                setFinclip("type", "G");
//            }
//        } // btnFinclipG
        BackdeckButton2 {
            id: btnFinclipA
            text: qsTr("A")
            Layout.preferredHeight: buttonBaseSize
            Layout.preferredWidth: buttonBaseSize * 2
            checkable: true
            checked: true
            ButtonGroup.group: bgFinclipCategory
            activeFocusOnTab: false
            onClicked: {
                type = "A";
//                setFinclip("type", "A");
            }
        } // btnFinclipA
    }
    FramNumPad {
        id: numPad
        x: parent.width/2 - 50
        y: 5
        state: qsTr("counts")
        onNumpadok: {
            num = numPad.textNumPad.text;
            validateEntries();
        }
        onClearnumpad: {
            num = null;
            if (state === "weights") setnumpadvalue(0);
            else if (state === "counts") setnumpadvalue("");
        }
    } // numPad
    ColumnLayout {
        id: clLastFinclipID
        anchors.right: parent.right
        anchors.rightMargin: 20
        anchors.verticalCenter: parent.verticalCenter

        Label {
            text: qsTr("Last Finclip ID")
            font.pixelSize: 28
        }
        Label {
            text: (lastFinclipID !== undefined && lastFinclipID !== null) ? lastFinclipID : ""
            font.pixelSize: 28
        }
    } // Last Finclip ID
    OkayDialog {
        id: dlgOkay
    } // dlgOkay
    OkayCancelDialog {
        id: dlgOkayCancel
        onAccepted: {
            switch (actionType) {
                case "sequenceGapCheck":
                    setFinclip();
                    break;
                default:
                    break;
            }
        }
    } // dlgOkayCancel
}