import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 580
    height: 240
    title: "Add Comment"
    property string message: "Okay Cancel Message"
    property string accepted_action: ""
    property alias btnOkay: btnOkay
    property alias btnCancel: btnCancel
    property alias taComment: taComment

    onRejected: {  }
    onAccepted: { timeSeries.addComment(taComment.text); }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        ColumnLayout {
            anchors.fill: parent
//            spacing: 10
            TextArea {
                id: taComment
                anchors.horizontalCenter: parent.horizontalCenter
                Layout.preferredWidth: parent.width * 0.9
                Layout.preferredHeight: parent.height * 0.6
            } // taComment

            RowLayout {
                id: rwlButtons
                anchors.horizontalCenter: parent.horizontalCenter
                y: dlg.height - this.height - 20
                spacing: 20
                Button {
                    id: btnOkay
                    text: "Okay"
//                    Layout.preferredWidth: this.width
//                    Layout.preferredHeight: this.height
                    onClicked: { dlg.accept() }
                } // btnOkay
                Button {
                    id: btnCancel
                    text: "Cancel"
//                    Layout.preferredWidth: this.width
//                    Layout.preferredHeight: this.height
                    onClicked: { dlg.reject() }
                } // btnCancel
            } // rwlButtons
        }

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
}
