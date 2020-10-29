import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.2
import QtQuick.Controls.Styles 1.2

//import "../common"
import "."

RowLayout {
    id: framFooter
    spacing: 80
    anchors.bottom: parent.bottom
    anchors.left: parent.left
    anchors.leftMargin: 20
    anchors.right: parent.right
    anchors.rightMargin: 20
//    width: parent.width
    height: 50
    property int defaultitemwidth: 200
    property string previousDropTimeState: "enter"
    property int buttonHeight: 40
    property int buttonWidth: 160

    property alias lblSpeciesList: lblSpeciesList

    state: "sites"

    signal clickedSpeciesList(string speciesList);

    Connections {
        target: stateMachine
        onDropTimeStateChanged: actionClicked()
    }
//    Connections {
//        target: drops
//        onOperationAttributeDeleted: actionClicked("delete")
//    } // drops.onOperationAttributeDeleted
    function actionClicked() {
        // Return all labels to standard state
        editTime.font.bold = false;
        editTime.font.italic = false;
        deleteTime.font.bold = false;
        deleteTime.font.italic = false;
//        btnDelete.deleteStatus = false;
        lblMove.font.bold = false;
        lblMove.font.italic = false;
        lblSwap.font.bold = false;
        lblSwap.font.italic = false;
        switch (stateMachine.dropTimeState) {
            case "enter":
                break;
            case "edit":
                if (stateMachine.dropTimeState === previousDropTimeState) {
                    editTime.font.bold = false;
                    editTime.font.italic = false;
                    stateMachine.dropTimeState = "enter"
                } else {
                    editTime.font.bold = true;
                    editTime.font.italic = true;
                }
                break;
            case "delete":
                if (stateMachine.dropTimeState === previousDropTimeState) {
                    deleteTime.font.bold = false;
                    deleteTime.font.italic = false;
//                    btnDelete.deleteStatus = false;
                    stateMachine.dropTimeState = "enter"
                } else {
                    deleteTime.font.bold = true;
                    deleteTime.font.italic = true;
//                    btnDelete.deleteStatus = true;
                }
                break;
            case "Move":
                break;
            case "Swap":
                break;
        }
    }

    function printTags(printer) {
        var equipment = "";
        switch (printer) {
            case "bow":
                equipment = "Zebra Printer Bow";
                break;
            case "aft":
                equipment = "Zebra Printer Aft";
                break;
            case "mid":
                equipment = "Zebra Printer Aft";
                break;
        }
        var angler = stateMachine.angler;
        var drop = stateMachine.drop;
        var hooks = {1: parent.hook1, 2: parent.hook2, 3: parent.hook3,
                     4: parent.hook4, 5: parent.hook5}
        var species = null;
        for (var i in hooks) {
            species = hooks[i].tfHook.text;
            if ((species !== "Bait Back") &&
                (species !== "No Bait") &&
                (species !== "No Hook") &&
                (species !== "Multiple Hook") &&
                (species !== "")) {
                console.info('printing ADH:  angler=' + angler + ', drop=' + drop + ', hook=' + i + ', species=' + species);
                labelPrinter.printADHLabel(equipment, angler, drop, i, species);
            }
        }
    }

    function printTest(printer) {
        var equipment = "";
        switch (printer) {
            case "bow":
                equipment = "Zebra Printer Bow";
                break;
            case "aft":
                equipment = "Zebra Printer Aft";
                break;
        }
        labelPrinter.printADHLabel(equipment, "A", "1", "1", "Test Species");
    }

    // Drops Items
    Label {
        id: lblTime
        text: qsTr("Time:")
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 25
        width: defaultitemwidth
        visible: true
    } // lblTime

//    BackdeckButton {
//        id: editTime
//        text: qsTr("Edit")
//        Layout.preferredWidth: buttonWidth
//        Layout.preferredHeight: buttonHeight
//        onClicked: {
//            previousDropTimeState = stateMachine.dropTimeState;
//            stateMachine.dropTimeState = "edit";
//        }
//    } // editTime
    Label {
        id: editTime
        text: qsTr("Edit")
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 25
        width: defaultitemwidth
        visible: true
        MouseArea {
            anchors.fill: parent
            onClicked: {
                previousDropTimeState = stateMachine.dropTimeState;
                stateMachine.dropTimeState = "edit";
            }
        }
    } // editTime

    Label {
        id: deleteTime
        text: qsTr("Delete")
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 25
        width: defaultitemwidth
        visible: true
        MouseArea {
            anchors.fill: parent
            onClicked: {
                previousDropTimeState = stateMachine.dropTimeState;
                stateMachine.dropTimeState = "delete";
            }
        }
    } // deleteTime
    Label {
        id: lblMove
        text: qsTr("Move")
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 25
        width: defaultitemwidth
        visible: true
        MouseArea {
            anchors.fill: parent
            onClicked: {
//                previousDropTimeState = stateMachine.dropTimeState;
//                stateMachine.dropTimeState = "move"
            }
        }
    } // lblMove
    Label {
        id: lblSwap
        text: qsTr("Swap")
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 25
        width: defaultitemwidth
        visible: true
        MouseArea {
            anchors.fill: parent
            onClicked: {
//                previousDropTimeState = stateMachine.dropTimeState;
//                stateMachine.dropTimeState = "swap"
            }
        }
    } // lblSwap

    // Hooks Items
//    Label {
//        id: printBow
//        text: qsTr("Print Bow")
//        verticalAlignment: Text.AlignVCenter
//        font.pixelSize: 25
//        width: defaultitemwidth
//        visible: true
//        MouseArea {
//            anchors.fill: parent
//            onClicked: {
//                printTags("bow");
//            }
//        }
//    } // printBow

    BackdeckButton {
        id: printBow
        text: qsTr("Print Bow")
        Layout.preferredWidth: buttonWidth
        Layout.preferredHeight: buttonHeight
        onClicked: {
            printTags("bow");
        }
    } // printBow
    BackdeckButton {
        id: printAft
        text: qsTr("Print Aft")
        Layout.preferredWidth: buttonWidth
        Layout.preferredHeight: buttonHeight
        onClicked: {
            printTags("aft");
        }
    } // printAft

    BackdeckButton {
        id: printBowTest
        text: qsTr("Print Bow Test")
        Layout.preferredWidth: buttonWidth
        Layout.preferredHeight: buttonHeight
        onClicked: {
            printTest("bow");
        }
    } // printBowTest
    BackdeckButton {
        id: printAftTest
        text: qsTr("Print Aft Test")
        Layout.preferredWidth: buttonWidth
        Layout.preferredHeight: buttonHeight
        onClicked: {
            printTest("aft");
        }
    } // printAftTest


//    Label {
//        id: printAft
//        verticalAlignment: Text.AlignVCenter
//        font.pixelSize: 25
//        width: defaultitemwidth
//        visible: true
//        MouseArea {
//            anchors.fill: parent
//            onClicked: {
//                printTags("aft");
//            }
//        }
//    } // printAft

    Label {
        id: lblSpacer
        text: qsTr("")
        width: 600
    } // lblSpace
    Label {
        id: lblSpeciesList
        text: qsTr("Full List")
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 25
        width: 100
        visible: true
        MouseArea {
            anchors.fill: parent
            onClicked: {
                clickedSpeciesList(parent.text);
            }
        }
    } // lblSpeciesList
    Label {
        id: lblNotes
        text: qsTr("Notes")
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 25
        width: defaultitemwidth
        visible: true
        MouseArea {
            anchors.fill: parent
            onClicked: {
//                dlgNotes.open();
                dlgDrawingNotes.open();
                dlgDrawingNotes.canvas.clear_canvas();
            }
        }
    } // lblNotes
    NotesDialog {
        id: dlgNotes
    }
    DrawingNotesDialog { id: dlgDrawingNotes }

    states: [
        State {
            name: "sites"
            PropertyChanges {target: lblTime; visible: false}
            PropertyChanges { target: editTime; visible: false}
            PropertyChanges { target: deleteTime; visible: false}
//            PropertyChanges { target: btnDelete; visible: false}

            PropertyChanges { target: lblMove; visible: false}
            PropertyChanges { target: lblSwap; visible: false}
            PropertyChanges { target: printBow; visible: false}
            PropertyChanges { target: printAft; visible: false}
//            PropertyChanges { target: lblReprint; visible: false}
            PropertyChanges { target: lblSpeciesList; visible: false; }
            PropertyChanges {target: lblSpacer; width: 800}
            PropertyChanges { target: printBowTest; visible: false }
            PropertyChanges { target: printAftTest; visible: false }
        }, // sites
        State {
            name: "drops"
            PropertyChanges {target: lblTime; visible: true;}
            PropertyChanges { target: editTime; visible: true}
            PropertyChanges { target: deleteTime; visible: true}
//            PropertyChanges { target: btnDelete; visible: true}

            PropertyChanges { target: lblMove; visible: false}
            PropertyChanges { target: lblSwap; visible: false}
            PropertyChanges { target: printBow; visible: false}
            PropertyChanges { target: printAft; visible: false}
//            PropertyChanges { target: lblReprint; visible: false}
            PropertyChanges { target: lblSpeciesList; visible: false; }
            PropertyChanges {target: lblSpacer;  width: 300}
            PropertyChanges { target: printBowTest; visible: false }
            PropertyChanges { target: printAftTest; visible: false }

        }, // drops
        State {
            name: "hooks"
            PropertyChanges {target: lblTime; visible: false;}
            PropertyChanges { target: editTime; visible: false}
            PropertyChanges { target: deleteTime; visible: false}
            PropertyChanges { target: lblMove; visible: false}
            PropertyChanges { target: lblSwap; visible: false}
            PropertyChanges { target: printBow; visible: true}
            PropertyChanges { target: printAft; visible: true}
//            PropertyChanges { target: lblReprint; visible: true}
            PropertyChanges { target: lblSpeciesList; visible: true; }
            PropertyChanges {target: lblSpacer;  width: 100}
            PropertyChanges { target: printBowTest; visible: false }
            PropertyChanges { target: printAftTest; visible: false }

        }, // hooks
        State {
            name: "gear performance"
            PropertyChanges {target: lblTime; visible: false;}
            PropertyChanges { target: editTime; visible: false}
            PropertyChanges { target: deleteTime; visible: false}
            PropertyChanges { target: lblMove; visible: false}
            PropertyChanges { target: lblSwap; visible: false}
            PropertyChanges { target: printBow; visible: false}
            PropertyChanges { target: printAft; visible: false}
//            PropertyChanges { target: lblReprint; visible: false}
            PropertyChanges { target: lblSpeciesList; visible: false; }
            PropertyChanges {target: lblSpacer;  width: 700}
            PropertyChanges { target: printBowTest; visible: false }
            PropertyChanges { target: printAftTest; visible: false }

        }  // gear performance
    ]
}
