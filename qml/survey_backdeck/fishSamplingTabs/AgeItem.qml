import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.3
import ".."

Item {
    property string action: "ageID"
    property bool ageRecExists: false
    property int buttonBaseSize: 80
    property string type: ""
    property variant num: null

    property variant lastAgeID: null;
    property variant lastFinclipID: null;

    property alias btnOtolith: btnOtolith;
    property alias btnFinray: btnFinray;
    property alias btnSecondDorsalSpine: btnSecondDorsalSpine;
//    property alias btnVertebra: btnVertebra;
//    property alias btnScale: btnScale;
    property alias btnNotAvailable: btnNotAvailable;

    property alias btnAgeA: btnAgeA;
    property alias btnAgeB: btnAgeB;
//    property alias btnAgeG: btnAgeG;
    property alias btnAgeV: btnAgeV;

    property alias numPad: numPad;
    property alias bgAgeStructure: bgAgeStructure;
    property alias bgAgeCategory: bgAgeCategory;

    signal labelSet(string action, variant value, string uom, bool dbUpdate, variant actionSubType);
    signal advanceTab();

    function setDescriptor(descriptor) {
        // Method to set just the age descriptor (i.e. B, V, or A)
        console.info('age descriptor getting updated ... ' + descriptor);

        type = descriptor;
        switch (descriptor) {
            case "B":
                btnAgeB.checked = true;
                break;
            case "V":
                btnAgeV.checked = true;
                break;
            case "A":
                btnAgeA.checked = true;
                break;
            default:
                btnAgeB.checked = false;
                btnAgeV.checked = false;
                btnAgeA.checked = false;
                break;
        }
    }

    function validateEntries() {
        var isInvalid = false;
        var msg = "";

        // Check if the number is missing, if so, then delete the record
        if ((num === null) || (num === "")) {
            var specimenID = parent.retrieveSpecimenID();
            var actionSubType = bgAgeStructure.checkedButton ? bgAgeStructure.checkedButton.text : null;
            actionSubType = actionSubType.replace("\n", " ");
            num = null;
            fishSampling.deleteSpecimenObservation(specimenID, "Age ID", actionSubType, false);
            labelSet(action, "", null, false, actionSubType);
            ageRecExists = false;
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
        var existsResult = fishSampling.checkIfIDExists("Age ID", type + num);
        if ((existsResult.status === "invalid") || (existsResult.status === "found")) {
            isInvalid = true;
            msg = existsResult.msg;
        }

        // Check if finclipID !== ageID
        var finclipID = parent.retrieveFinclipID();
        if ((finclipID !== null) && (finclipID.type !== "") && (finclipID.num !== null) &&
            ((finclipID.type !== type) || (finclipID.num !== num)) ) {
            isInvalid = true;
            msg = "AgeID does not equal Finclip ID\n" + type + num + " <> " + finclipID.type + finclipID.num;
        }

        // Check if the descriptor is wrong
        var species = parent.retrieveSpecies();
        if (species !== null) {
            switch (species.replace("\n", " ")) {
                case "Bocaccio":
                    if (!btnAgeB.checked) {
                        isInvalid = true;
                        msg = species.replace("\n", " ") + " is selected, however B is not"
                    }
                    break;
                case "Vermilion Rockfish":
                    if (!btnAgeV.checked) {
                        isInvalid = true;
                        msg = species.replace("\n", " ") + " is selected, however V is not"
                    }
                    break;
                default:
                    if (!btnAgeA.checked) {
                        isInvalid = true;
                        msg = species.replace("\n", " ") + " is selected, however A is not"
                    }
                    break;
            }
        } else {
            isInvalid = true;
            msg = "You must select a species before entering an Age"
        }

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

        setAge();
    }

    function setAge() {

        var actionSubType = bgAgeStructure.checkedButton ? bgAgeStructure.checkedButton.text : null;
        console.info('setAge, next is labelSet: ' + type + num + ', actionSubType=' + actionSubType);

        labelSet(action, type + num, null, true, actionSubType);
        ageRecExists = true;
        advanceTab();

    }

    ColumnLayout {
        x: 20
        y: 20
        ButtonGroup { id: bgAgeStructure }
        Label {
            text: qsTr("Structure Type")
            font.pixelSize: 20
            Layout.preferredWidth: 100
        }
        BackdeckButton2 {
            id: btnOtolith
            text: qsTr("Otolith")
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
            checked: true
            checkable: true
            activeFocusOnTab: false
            ButtonGroup.group: bgAgeStructure
            onClicked: {
//                setAge(null, null);
            }
        } // btnOtolith
        BackdeckButton2 {
            id: btnFinray
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
            text: qsTr("Finray")
            checked: false
            checkable: true
            activeFocusOnTab: false
            ButtonGroup.group: bgAgeStructure
            onClicked: {
//                setAge(null, null);
            }
        } // btnFinray
        BackdeckButton2 {
            id: btnSecondDorsalSpine
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
            text: qsTr("2nd Dorsal\nSpine")
            checked: false
            checkable: true
            activeFocusOnTab: false
            ButtonGroup.group: bgAgeStructure
            onClicked: {
//                setAge(null, null);
            }
        } // btnSecondDorsalSpine
//        BackdeckButton2 {
//            id: btnVertebra
//            Layout.preferredWidth: 120
//            Layout.preferredHeight: 60
//            text: qsTr("Vertebra")
//            checked: false
//            checkable: true
//            activeFocusOnTab: false
//            ButtonGroup.group: bgAgeStructure
//        } // btnVertebra
//        BackdeckButton2 {
//            id: btnScale
//            text: qsTr("Scale")
//            Layout.preferredWidth: 120
//            Layout.preferredHeight: 60
//            checked: false
//            checkable: true
//            activeFocusOnTab: false
//            ButtonGroup.group: bgAgeStructure
//        } // btnScale
        BackdeckButton2 {
            id: btnNotAvailable
            text: qsTr("Not\nAvailable")
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
            checked: false
            checkable: true
            activeFocusOnTab: false
            ButtonGroup.group: bgAgeStructure
            onClicked: {
//                setAge(null, null);
            }
        } // btnNotAvailable
    } // Structures
    ColumnLayout {
        id: clAgeCategory
//                            anchors.horizontalCenter: parent.horizontalCenter
        x: parent.width/4
        anchors.verticalCenter: parent.verticalCenter
        spacing: 20
        ButtonGroup { id: bgAgeCategory }
        BackdeckButton2 {
            id: btnAgeB
            text: qsTr("B")
            Layout.preferredHeight: buttonBaseSize
            Layout.preferredWidth: buttonBaseSize * 2
            checkable: true
            checked: false
            ButtonGroup.group: bgAgeCategory
            activeFocusOnTab: false
            onClicked: {
                type = "B";
//                setAge("type", "B");
            }
        } // btnAgeB
        BackdeckButton2 {
            id: btnAgeV
            text: qsTr("V")
            Layout.preferredHeight: buttonBaseSize
            Layout.preferredWidth: buttonBaseSize * 2
            checkable: true
            checked: false
            ButtonGroup.group: bgAgeCategory
            activeFocusOnTab: false
            onClicked: {
                type = "V";
//                setAge("type", "V");
            }
        } // btnAgeV
//        BackdeckButton2 {
//            id: btnAgeG
//            text: qsTr("G")
//            Layout.preferredHeight: buttonBaseSize
//            Layout.preferredWidth: buttonBaseSize * 2
//            checkable: true
//            checked: false
//            ButtonGroup.group: bgAgeCategory
//            activeFocusOnTab: false
//            onClicked: {
//                setAge("type", "G");
//            }
//        } // btnAgeG
        BackdeckButton2 {
            id: btnAgeA
            text: qsTr("A")
            Layout.preferredHeight: buttonBaseSize
            Layout.preferredWidth: buttonBaseSize * 2
            checkable: true
            checked: true
            ButtonGroup.group: bgAgeCategory
            activeFocusOnTab: false
            onClicked: {
                type = "A";
//                setAge("type", "A");
            }
        } // btnAgeA
    } // Age Group
    FramNumPad {
        id: numPad
        x: parent.width/2 - 50
        y: 5
        state: qsTr("counts")
        onNumpadok: {
            num = numPad.textNumPad.text;
//            setAge("num", numPad.textNumPad.text);
//            setAge();
            validateEntries();
        }
        onClearnumpad: {
            num = null;
            if (state === "weights") setnumpadvalue(0);
            else if (state === "counts") setnumpadvalue("");
        }
    } // numPad
    ColumnLayout {
        id: clLastAgeID
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
        Label { Layout.preferredHeight: 20 }
        Label {
            text: qsTr("Last Age ID")
            font.pixelSize: 28
        }
        Label {
            text: (lastAgeID !== undefined && lastAgeID !== null) ? lastAgeID : ""
            font.pixelSize: 28
        }
    } // Last Age ID

    OkayDialog { id: dlgOkay } // dlgOkay
    OkayCancelDialog {
        id: dlgOkayCancel
        onAccepted: {
            switch (actionType) {
                case "sequenceGapCheck":
                    setAge();
                    break;
                default:
                    break;
            }
        }
    } // dlgOkayCancel
}