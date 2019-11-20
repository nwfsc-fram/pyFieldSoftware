import QtQuick 2.3
import QtQuick.Controls 1.3
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.2

import "../common"

Dialog {
    id: dlg
    width: 800
    height: 620

    title: "Add Comment"

    property alias prevComments: commentText.text
    property alias text: commentEntry.text
    property alias enable_audio: kbdComment.enable_audio

    function clearEntry() {
        commentEntry.cursorPosition = 0;
        commentEntry.text = "";
    }
    standardButtons:  StandardButton.NoButton

    onVisibleChanged: {
       if (visible) {
           commentEntry.focus = true;
           if (commentText.length > 0) {
              var target = commentText.length - 1;
//              console.log("Set commentText cursor position to " + target.toString());
              commentText.cursorPosition = target;
           }
           if (commentEntry.length > 0) {
               var target = commentEntry.length - 1;
//               console.log("Set commentEntry cursor position to " + target.toString());
               commentEntry.cursorPosition = target;
           }
       }
    }

    ColumnLayout {
        anchors.fill: parent
        TextArea {
            id: commentText
            Layout.preferredHeight: 200
            Layout.fillWidth: true
            text: ""
            readOnly: true
            font.pixelSize: 15
        }
        TextArea {
            id: commentEntry
            Layout.preferredHeight: 100
            Layout.fillWidth: true
            text: ""
            font.pixelSize: 15
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 300
            color: "transparent"
            FramScalingKeyboard {
                id: kbdComment
                anchors.fill: parent
                onKeyboardok: {
                    dlg.accept();
                }
                Component.onCompleted: {
                    attach_external_textarea(commentEntry);
                    showCR(true);
                    hide_tf();
                }
            }
        }

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.accept()
        Keys.onBackPressed: dlg.accept() // especially necessary on Android
    }
}
