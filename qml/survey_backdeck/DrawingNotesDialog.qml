import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.2

Dialog {
    id: dlgDrawingNotes
    width: 800
    height: 550
    title: 'Drawing Notes'

    modality: Qt.ApplicationModal

    property int rlHeight: 60;
    property int rlWidth: 160;
    property int rlPixelSize: 20;
    property int arrowBtnWidth: 80;

    // Canvas properties
    property int xpos;
    property int ypos;
    property int strokeSize: 5;

    property alias canvas: canvas;
    property string noteStatus: "";

    // Reference
    // https://qmlbook.github.io/ch08-canvas/canvas.html

    Connections {
        target: notes
        onNoteSaved: openSaveConfirmation(imageNameStr)
    }
    function openSaveConfirmation(imageNameStr) {
        noteStatus = "Saved note to " + imageNameStr;
    }

    function backClicked() {
        console.info('load previous note');
    }

    function forwardClicked() {
        console.info('forward clicked');
    }

    contentItem: Rectangle {
        id: contentLayout
        ColumnLayout {
            spacing: 20
            RowLayout {
                id: rlInfo
                anchors.top: parent.top
                anchors.topMargin: 10
                anchors.leftMargin: 10
                spacing: 20
                Label {
                    text: stateMachine.angler ?
                        "Angler: " + stateMachine.angler :
                        "Angler: "
                    font.pixelSize: rlPixelSize;
                    Layout.preferredHeight: rlHeight;
                } // angler
                Label {
                    text: stateMachine.drop ? "Drop: " + stateMachine.drop :
                        "Drop: "
                    font.pixelSize: rlPixelSize;
                    Layout.preferredHeight: rlHeight;
                } // drop
                Label {
                    text: stateMachine.hook ? "Hook: " + stateMachine.hook :
                        "Hook: "
                    font.pixelSize: rlPixelSize;
                    Layout.preferredHeight: rlHeight;
                } // hook
                Label {
                    text: stateMachine.currentEntryTab ? "Observation: " + stateMachine.currentEntryTab :
                        "Observation: "
                    font.pixelSize: rlPixelSize;
                    Layout.preferredHeight: rlHeight;
                } // observation
                BackdeckButton {
                    id: btnClear
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 60
                    text: qsTr("Clear")
                    onClicked: {
                        canvas.clear_canvas();
                    }
                } // btnClear
                BackdeckButton {
                    id: btnSave
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 60
                    text: qsTr("Save &\nClose")
                    onClicked: {
                        var imageName = notes.getNextNoteName(); //'note_image.png';
                        canvas.save(imageName);
                        notes.insertNote(stateMachine.appName, stateMachine.screen, "Handwritten note",
                            stateMachine.siteOpId, stateMachine.drop, stateMachine.angler,
                            stateMachine.hook, stateMachine.currentEntryTab, imageName);
                        canvas.clear_canvas();
                        dlgDrawingNotes.accept();
                    }
                } // btnSave
            } // rlInfo - State information - A/D/H
            RowLayout {
                id: rlCanvasAndButtons
                spacing: 0
//                Rectangle {
//                    id: btnBack
//                    Layout.preferredHeight: dlgDrawingNotes.height - rlInfo.height - rlStatus.height
//                    Layout.preferredWidth: arrowBtnWidth
//                    anchors.left: parent.left
//                    anchors.leftMargin: 10
//                    visible: true;
//                    anchors.verticalCenter: parent.verticalCenter
//                    antialiasing: true
//                    Image {
//                        height: 80
//                        width: 40
//                        anchors.verticalCenter: parent.verticalCenter
//                        source: Qt.resolvedUrl("/resources/images/navigation_previous_item_dark.png")
//                    }
//                    MouseArea {
//                        anchors.left: parent.left
//                        anchors.top: parent.top
//                        anchors.bottom: parent.bottom
//                        width: parent.width
//                        onClicked: {
//                            backClicked();
//                        }
//                    }
//                } // btnBack

                Rectangle {
                    id: recDrawingArea
    //                height: dlgDrawingNotes.height - rlInfo.height - rlStatus.height;
                    height: dlgDrawingNotes.height - 150
                    width: dlgDrawingNotes.width //- btnBack.width - btnForward.width
                    border.width: 1

                    Canvas {
                        id: canvas
                        width: parent.width
                        height: parent.height
    //                    anchors.fill: parent;
                        property real lastX;
                        property real lastY;
                        property color color: "black";
                        property variant ctx;

                        function clear_canvas() {
                            noteStatus = "Not Saved"
                            ctx = getContext("2d");
                            ctx.reset();
                            canvas.requestPaint();
                        }

                        onPaint: {
                            ctx = getContext('2d')
                            ctx.lineWidth = 1.5
                            ctx.strokeStyle = canvas.color
                            ctx.beginPath()
                            ctx.moveTo(lastX, lastY)
                            lastX = area.mouseX
                            lastY = area.mouseY
                            ctx.lineTo(lastX, lastY)
                            ctx.stroke()
                        }
                        MouseArea {
                            id: area
                            anchors.fill: parent
                            onPressed: {
                                canvas.lastX = mouseX
                                canvas.lastY = mouseY
                                noteStatus = "Not Saved"
                            }
                            onPositionChanged: {
                                canvas.requestPaint()
                            }
                        }
                    }
                } // recDrawingArea

//                Rectangle {
//                    id: btnForward
//                    Layout.preferredHeight: dlgDrawingNotes.height - rlInfo.height - rlStatus.height
//                    Layout.preferredWidth: arrowBtnWidth
//                    anchors.left: recDrawingArea.right
//                    anchors.leftMargin: 10
//                    visible: true;
//                    anchors.verticalCenter: parent.verticalCenter
//                    antialiasing: true
//                    Image {
//                        height: 80
//                        width: 40
//                        anchors.verticalCenter: parent.verticalCenter
//                        source: Qt.resolvedUrl("/resources/images/navigation_next_item_dark.png")
//                    }
//                    MouseArea {
//                        anchors.right: parent.right
//                        anchors.top: parent.top
//                        anchors.bottom: parent.bottom
//                        width: parent.width
//                        onClicked: {
//                            forwardAction;
//                        }
//                    }
//                } // btnForward

            } // rlCanvasAndButtons
            RowLayout {
                id: rlStatus
                y: dlgDrawingNotes.height - 50
//                anchors.bottom: dlgDrawingNotes.bottom
//                anchors.bottomMargin: 0;
//                anchors.left: dlgDrawingNotes.left
                x: 10
//                anchors.leftMargin: 10
                Layout.preferredHeight: 30
                spacing: 10
                Label {
//                    x: 10
                    text: "Note Status:"
                    font.pixelSize: rlPixelSize
                }
                Label {
                    text: noteStatus
                    font.pixelSize: rlPixelSize
                }
            } // rlStatus
        }
    }
}
