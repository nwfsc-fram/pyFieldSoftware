import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.2

import "../common"
import "."

RowLayout {
    id: framFooter

    anchors.bottom: parent.bottom
    anchors.left: parent.left
    width: parent.width
    height: 50
    property int defaultitemwidth: 200
    
    property int defaultPixelSize: 28

    property ObserverSM obsSM: null
    property alias confirmLogout: confirmLogout
    property string logbook_list_mode: "Trip Hauls" // logbook_list_mode == "Current Haul" "Daily Hauls" or "Trip Hauls"
    property bool comments_enabled: true            // Some screens may wish to disable adding comment during long op.
    property real comments_disabled_opacity: 0.3

    signal clickedAdd // For anyone watching via Connections
    signal clickedNew
    signal clickedDelete
    signal clickedEdit
    signal clickedDone
    signal clickedEndTripComplete
    signal clickedCancel
    signal clickedLogout
    signal clickedLogbook
    signal clickedComments    
    signal clickedEndTrip
    signal clickedCurrentHaul
    signal clickedDailyHauls
    signal clickedTripHauls

    function resetDelete() {
        deleteButton.font.bold = false;
        deleteButton.text = "Delete";
    }

    function hideCommentButton(doHide) {
        if (doHide) {
            comments_enabled = false;
        } else {
            comments_enabled = true;
        }
    }

    function openComments(add_comment_text) {
        // Open the comments dialog, with optional text added
        commentsButton.openCommentsDialog(add_comment_text);
    }

    Row {
        id: framFooterRow

        Rectangle { // spacer instead of leftPadding
            width: 50
            height: parent.height
            color: "transparent"
        }

        Label {
            id: exitButton
            text: qsTr("Exit")
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            width: defaultitemwidth

            MouseArea {
                id: exitArea
                anchors.fill: parent
                onClicked: {
                    confirmQuit.open()
                }
            }
        }


        Label {
            id: addButton
            text: qsTr("Add")
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            width: defaultitemwidth
            visible: false

            MouseArea {
                id: addArea
                anchors.fill: addButton
                onClicked: {
                    framFooter.clickedAdd(); // emit
                }
            }
        }

        Label {
            id: newButton
            text: qsTr("New")
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            width: defaultitemwidth
            visible: false

            MouseArea {
                id: newArea
                anchors.fill: newButton
                onClicked: {
                    framFooter.clickedNew(); // emit
                }
            }
        }

        Label {
            id: editButton
            text: qsTr("Edit")
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            width: defaultitemwidth
            visible: false

            MouseArea {
                id: editArea
                anchors.fill: parent
                onClicked: {
                    framFooter.clickedEdit(); // emit
                }
            }
        }

        Label {
            id: doneButton
            text: qsTr("Done")
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            width: defaultitemwidth
            visible: false

            MouseArea {
                id: doneArea
                anchors.fill: parent
                onClicked: {
                    framFooter.clickedDone(); // emit
                }
            }
        }
        Label {
            id: endTripCompleteButton
            text: qsTr("Finalize & Validate")
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            width: defaultitemwidth
            visible: false

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    framFooter.clickedEndTripComplete(); // emit ACTUAL end trip signal
                }
            }
        }

        Label {
            id: cancelButton
            text: qsTr("Cancel")
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            width: defaultitemwidth
            visible: false

            MouseArea {
                id: cancelArea
                anchors.fill: parent
                onClicked: {
                    framFooter.clickedCancel(); // emit
                }
            }
        }
        Label {
            id: logbookButton
            text: qsTr("Logbook Mode")
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            width: defaultitemwidth
            visible: false

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    framFooter.clickedLogbook(); // emit
                }
            }
        }

        Label {
            id: deleteButton
            text: qsTr("Delete")
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            width: defaultitemwidth * 2
            visible: false

            MouseArea {
                id: areaDelete
                anchors.fill: deleteButton
                onClicked: {
                    deleteButton.font.bold = true;
                    deleteButton.text = "Delete - Select"
                    framFooter.clickedDelete(); // emit
                }
            }
        }

        Label {
            id: currentHaulButton
            text: appstate.isFixedGear ? "Current Set" : "Current Haul"
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            font.bold: logbook_list_mode == text
            width: defaultitemwidth
            visible: false

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    framFooter.clickedCurrentHaul();
                    logbook_list_mode = currentHaulButton.text;
                }
            }
        }
        Label {
            id: dailyHaulsButton
            text: appstate.isFixedGear ? "Daily Sets" : "Daily Hauls"
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            font.bold: logbook_list_mode == text
            width: defaultitemwidth
            visible: false // TODO Add when dates in DB //currentHaulButton.visible

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    framFooter.clickedDailyHauls();
                    logbook_list_mode = dailyHaulsButton.text;
                }
            }
        }
        Label {
            id: tripHaulsButton
            text: appstate.isFixedGear ? "Trip Sets" : "Trip Hauls"
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            font.bold: logbook_list_mode == text
            width: defaultitemwidth
            visible: currentHaulButton.visible

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    framFooter.clickedTripHauls();
                    logbook_list_mode = tripHaulsButton.text;
                }
            }
        }
    }
    Row {
        id: framFooterRowRight
        Layout.alignment: Qt.AlignRight
        Rectangle { // spacer instead of leftPadding
            width: 50
            height: parent.height
            color: "transparent"
        }
        Label {
            id: endTripButton
            text: qsTr("End Trip")
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: defaultPixelSize
            width: defaultitemwidth
            visible: true

            MouseArea {
                anchors.fill: endTripButton
                onClicked: {
                    framFooter.clickedEndTrip(); // emit - go to screen
                }
            }
        }
        Rectangle { // spacer
            width: commentsButton.width
            height: parent.height
            color: "transparent"
        }
        Label {
            id: commentsButton
            text: qsTr("Comments")
            verticalAlignment: Text.AlignVCenter
//            x: Window.width  - framFooter.defaultitemwidth
            font.pixelSize: defaultPixelSize
            width: framFooter.defaultitemwidth
            visible: true
            opacity: comments_enabled ? 1.0 : comments_disabled_opacity;

            function openCommentsDialog(add_text) {
                if (!comments_enabled) {
                    return;
                }
                if (appstate.currentTripId === null || appstate.currentTripId === '') {
                    console.log("Please select/create a trip + vessel before adding comments.")
                    selectTripDialog.open()
                    return;
                }

                appstate.updateComments();
                commentDialog.prevComments = appstate.comments;
                if (add_text.length) {
                    commentDialog.text = add_text;
                } else {
                    commentDialog.clearEntry();  // prevent cursor position warning
                }
                commentDialog.open();
                framFooter.clickedComments(); // emit
            }
            MouseArea {
                anchors.fill: commentsButton
                onClicked: {
                    commentsButton.openCommentsDialog("");
                }
            }
        }



        TrawlConfirmDialog {
            id: confirmQuit

            message: "Are you sure you want to exit?"
            action: ""

            onAccepted: {
                Qt.quit();
            }
        }

        TrawlConfirmDialog {
            id: confirmLogout

            message: "Are you sure you want to log out & exit?"
            action: ""

            onAccepted: {
                obsSM = null; // SM is owned by Home qml
                clickedLogout();
            }
        }

        FramCommentDialog {
            id: commentDialog
            prevComments: appstate.comments
            enable_audio: ObserverSettings.enableAudio
            onAccepted: {
                var state = "Login Page"
                if(obsSM)
                    state = obsSM.currentStateName;
                if (text.length > 0) {
                    var commentCharsAvailableAfterAdd = appstate.getFreeCommentSpaceAfterProposedAdd(text, state);
                    console.debug("Comments chars available after proposed comment add = " + commentCharsAvailableAfterAdd);
                    if (commentCharsAvailableAfterAdd >= 0) {
                        appstate.addComment(text, state);
                    } else {
                        console.warn("Comment addition rejected - out of comment space in Trips.notes (by " +
                                (-commentCharsAvailableAfterAdd) + ' characters, including context info.');
                        commentTooBigDialog.totalCommentCharactersAllowed = appstate.maxTextSizeOfObserverComments;
                        commentTooBigDialog.open();
                    }
                }
            }
        }
        FramNoteDialog {
            id: commentTooBigDialog
            property string totalCommentCharactersAllowed
            message: "Proposed comment is too long.\nMaximum characters of\ncomment text for a trip\n" +
                    "cannot exceed " + totalCommentCharactersAllowed + " characters."
        }
        FramNoteDialog {
            id: selectTripDialog
            message: "Please select or create\na trip + vessel name before\n adding comments."
        }

    }
    states: [
        State {
            name: "login"
            PropertyChanges{ target: exitButton; visible: true }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: false }
            PropertyChanges{ target: deleteButton; visible: false }
            PropertyChanges{ target: editButton; visible: false }
            PropertyChanges{ target: doneButton; visible: false }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: false }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }
            PropertyChanges{ target: commentsButton; visible: false }
        },State {
            name: "home"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: false }
            PropertyChanges{ target: deleteButton; visible: false }
            PropertyChanges{ target: editButton; visible: false }
            PropertyChanges{ target: doneButton; visible: false }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: false }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }
            PropertyChanges{ target: commentsButton; visible: true }
        },
        State {
            name: "add_edit"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: true }
            PropertyChanges{ target: newButton; visible: false }
            PropertyChanges{ target: deleteButton; visible: false }
            PropertyChanges{ target: editButton; visible: true }
            PropertyChanges{ target: doneButton; visible: false }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: false }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }
        },
        State {
            name: "new_edit"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: true }
            PropertyChanges{ target: deleteButton; visible: false }
            PropertyChanges{ target: editButton; visible: true }
            PropertyChanges{ target: doneButton; visible: false }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: false }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }
        },
        State {
            name: "new"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: true }
            PropertyChanges{ target: deleteButton; visible: false }
            PropertyChanges{ target: editButton; visible: false }
            PropertyChanges{ target: doneButton; visible: false }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: false }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }
        },
        State {
            name: "new_delete"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: true }
            PropertyChanges{ target: deleteButton; visible: true; font.bold: false; text: "Delete" }
            PropertyChanges{ target: editButton; visible: false }
            PropertyChanges{ target: doneButton; visible: false }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: false }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }
        },
        State {
            name: "hauls"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: false }
            PropertyChanges{ target: deleteButton; visible: true; font.bold: false; text: "Delete" }
            PropertyChanges{ target: editButton; visible: false }
            PropertyChanges{ target: doneButton; visible: false }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: true }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }

        },
        State {
            name: "sets"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: false }
            PropertyChanges{ target: deleteButton; visible: true; font.bold: false; text: "Delete" }
            PropertyChanges{ target: editButton; visible: false }
            PropertyChanges{ target: doneButton; visible: false }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: true }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }

        },
        State {
            name: "logbook"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: false }
            PropertyChanges{ target: deleteButton; visible: false }
            PropertyChanges{ target: editButton; visible: false }
            PropertyChanges{ target: doneButton; visible: false }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: true }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }
        },
        State {
            name: "logbook_mode"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: false }
            PropertyChanges{ target: deleteButton; visible: false }
            PropertyChanges{ target: editButton; visible: false }
            PropertyChanges{ target: doneButton; visible: false }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: false }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: true }

        },
        State {
            name: "done"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: false }
            PropertyChanges{ target: deleteButton; visible: false }
            PropertyChanges{ target: editButton; visible: false }
            PropertyChanges{ target: doneButton; visible: true }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: false }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }
        },
        State {
            name: "end_trip"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: false }
            PropertyChanges{ target: deleteButton; visible: false }
            PropertyChanges{ target: editButton; visible: false }
            PropertyChanges{ target: doneButton; visible: false }
            PropertyChanges{ target: endTripCompleteButton; visible: true }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: false }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }
        },
        State {
            name: "done_cancel"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: false }
            PropertyChanges{ target: deleteButton; visible: false }
            PropertyChanges{ target: editButton; visible: false }
            PropertyChanges{ target: doneButton; visible: true }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: true }
            PropertyChanges{ target: logbookButton; visible: false }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }
        },
        State {
            name: "none"
            PropertyChanges{ target: exitButton; visible: false }
            PropertyChanges{ target: addButton; visible: false }
            PropertyChanges{ target: newButton; visible: false }
            PropertyChanges{ target: deleteButton; visible: false }
            PropertyChanges{ target: editButton; visible: false }
            PropertyChanges{ target: doneButton; visible: false }
            PropertyChanges{ target: endTripCompleteButton; visible: false }
            PropertyChanges{ target: cancelButton; visible: false }
            PropertyChanges{ target: logbookButton; visible: false }
            PropertyChanges{ target: endTripButton; visible: false }
            PropertyChanges{ target: currentHaulButton; visible: false }
        }
    ]

}
