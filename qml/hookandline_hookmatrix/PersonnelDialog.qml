import QtQuick 2.7
//import QtQuick.Controls 1.3
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Styles 1.3
import QtQuick.Window 2.2
import QtQuick.Extras 1.4
import QtQuick.Dialogs 1.2


import "." // For ScreenUnits

Dialog {
    id: dlg
    title: qsTr("Personnel")
    width: 800
    height: 600
    property variant currentPerson: anglerA

    property int buttonHeight: 80
    property int buttonWeight: buttonHeight * 2
    property int fontSize: 20

    property alias anglerA: anglerA;
    property alias anglerB: anglerB;
    property alias anglerC: anglerC;
    property alias recorder: recorder;
    property alias lblSpacer: lblSpacer;

    signal personnelSet(string anglerA, string anglerB, string anglerC, string recorder);

    onAccepted: {
        personnelSet(anglerA.tfPersonnel.text, anglerB.tfPersonnel.text, anglerC.tfPersonnel.text,
                    recorder.tfPersonnel.text);
    }

    Connections {
        target: anglerA
        onCurrentPersonnelChanged: changePerson(personnelName);
    } // anglerA.onCurrentPersonnelChanged
    Connections {
        target: anglerB
        onCurrentPersonnelChanged: changePerson(personnelName);
    } // anglerB.onCurrentPersonnelChanged
    Connections {
        target: anglerC
        onCurrentPersonnelChanged: changePerson(personnelName);
    } // anglerC.onCurrentPersonnelChanged
    Connections {
        target: recorder
        onCurrentPersonnelChanged: changePerson(personnelName);
    } // recorder.onCurrentPersonnelChanged

    function changePerson(personnelName) {
        anglerA.tfPersonnel.deselect();
        anglerB.tfPersonnel.deselect();
        anglerC.tfPersonnel.deselect();
        recorder.tfPersonnel.deselect();

        switch (personnelName) {
            case "Angler A":
                currentPerson = anglerA;
                break;
            case "Angler B":
                currentPerson = anglerB;
                break;
            case "Angler C":
                currentPerson = anglerC;
                break;
            case "Recorder":
                currentPerson = recorder;
                break;
        }
        currentPerson.tfPersonnel.selectAll();
        currentPerson.tfPersonnel.forceActiveFocus();
    }
    function populatePerson(person) {

        if (currentPerson === null) return;

        switch (currentPerson) {
            case anglerA:
                anglerA.tfPersonnel.text = person;
                anglerB.tfPersonnel.focus = true;
                anglerB.tfPersonnel.selectAll()
                currentPerson = anglerB;
                break;
            case anglerB:
                anglerB.tfPersonnel.text = person;
                anglerC.tfPersonnel.focus = true;
                anglerC.tfPersonnel.selectAll()
                currentPerson = anglerC;
                break;
            case anglerC:
                anglerC.tfPersonnel.text = person;
                recorder.tfPersonnel.focus = true;
                recorder.tfPersonnel.selectAll()
                currentPerson = recorder;
                break;
            case recorder:
                recorder.tfPersonnel.text = person;
                break;
        }
    }

    contentItem: Rectangle {
        color: "#eee"
        RowLayout {
            anchors.left: parent.left
            anchors.leftMargin: 20
            anchors.top: parent.top
            anchors.topMargin: 20
            ColumnLayout {
                spacing: 20
                PersonnelItem {
                    id: anglerA
                    personnelName: "Angler A"
                } // anglerA
                PersonnelItem {
                    id: anglerB
                    personnelName: "Angler B"
                } // anglerB
                PersonnelItem {
                    id: anglerC
                    personnelName: "Angler C"
                } // anglerC
                PersonnelItem {
                    id: recorder
                    personnelName: "Recorder"
                } // recorder
            }
            Label { id: lblSpacer; Layout.preferredWidth: 20 }
            GridLayout {
                rows: 5
                columns: 3
                rowSpacing: 20
                columnSpacing: 20
                Repeater {
                    model: drops.personnelModel
                    BackdeckButton {
                        Layout.preferredWidth: buttonWidth
                        Layout.preferredHeight: buttonHeight
                        text: model.text
                        onClicked: { populatePerson(text.replace('\n', ' ')); }
                    }
                }
            }
        }
        RowLayout {
            spacing: 20
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 20
            anchors.horizontalCenter: parent.horizontalCenter
            BackdeckButton {
                id: btnOkay
                Layout.preferredWidth: buttonWidth
                Layout.preferredHeight: buttonHeight
                text: qsTr("Okay")
                onClicked: {
                    dlg.accept();
                }
            } // btnOkay
            BackdeckButton {
                id: btnCancel
                Layout.preferredWidth: buttonWidth
                Layout.preferredHeight: buttonHeight
                text: qsTr("Cancel")
                onClicked: {
                    dlg.close();
                }
            } // btnCancel
        }
    }
}

