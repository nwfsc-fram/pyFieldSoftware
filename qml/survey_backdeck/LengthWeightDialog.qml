/*****************************************************************************
Custom dialog created for #94 length weight relationship warning check

******************************************************************************/

import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

//import "../common"

Dialog {
    id: dlg
    width: 580
    height: 580
    modality: Qt.ApplicationModal  // force acknowledgement here before going elsewhere
    title: "L-W Relationship Warning"

    property string message: ""

    signal proceed
    signal proceedWNote
    signal editSex
    signal editWeight
    signal editLength

    // signal actions defined in FishSamplingEntryDialog.qml
    onRejected: {  }
    onAccepted: {  }
    onProceed: {  }
    onProceedWNote: {  }
    onEditSex: {  }
    onEditWeight: {  }
    onEditLength: {  }

    contentItem: Rectangle {
        color: "#eee"
        RowLayout {
            id: rwlMsg
            anchors.left: parent.left
            Label {
                id: lblMessage
                anchors.left: parent.left
                horizontalAlignment: Text.AlignCenter
                text: message
                font.pixelSize: 20
            } // lblMessage
        }
        RowLayout {
            id: rwlContinue
            anchors.top: rwlMsg.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 20
            BackdeckButton {
                id: btnContinue
                text: "Proceed\nto Age"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.proceed() }
            }
            BackdeckButton {
                id: btnContinueWNote
                text: "Proceed w.\nnote"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.proceedWNote() }
            }
        }
        RowLayout {
            id: rwlEdits
            Layout.fillHeight: false
            anchors.top: rwlContinue.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 20
            BackdeckButton {
                id: btnEditWeight
                text: "Edit\nWeight"
                Layout.topMargin: 20
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.editWeight() }
            }
            BackdeckButton {
                id: btnEditLength
                text: "Edit\nLength"
                Layout.topMargin: 20
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.editLength() }
            }
            BackdeckButton {
                id: btnEditSex
                text: "Edit\nSex"
                Layout.topMargin: 20
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.editSex() }
            }
        } // rwlEdits



//        Keys.onPressed: if (event.key === Qt.Key_R && (event.modifiers & Qt.ControlModifier)) dlg.click(StandardButton.Retry)
        Keys.onEnterPressed: dlg.proceed()
        Keys.onReturnPressed: dlg.proceed()
        Keys.onEscapePressed: dlg.proceed()
        Keys.onBackPressed: dlg.proceed() // especially necessary on Android
    }
}