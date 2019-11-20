import QtQuick 2.6
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 300
    height: 480
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
//    title: customizeTitle.checked ? windowTitleField.text : "Customized content"

    property string itemType: ""
    property int row: -1
    property string initial_value: ""
    property variant lvModel
    property alias lvItems: lvItems
//    standardButtons: StandardButton.Ok | StandardButton.Cancel

    onRejected: {  }
    onAccepted: {  }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        ListView {
            id: lvItems
            anchors.fill: parent
            width: 300
            height: 480
            model:  lvModel
            delegate: Rectangle {
                width: parent.width
                height: 30
                border.width: 0.5
                border.color: "lightgray"
                color: ListView.isCurrentItem ? "white" : "whitesmoke"
                Text {
                    text: displayText
                    font.pixelSize: 14
                    renderType: Text.NativeRendering
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        lvItems.currentIndex = index
                    }
                    onDoubleClicked: {
                        lvItems.currentIndex = index
                        dlg.accept()
                    }
                }
            }
//            highlight: Rectangle { color: "lightsteelblue"; radius: 5 }
//            focus: true
        } // lvItems
//        RowLayout {
//            id: rwlButtons
//            anchors.horizontalCenter: parent.horizontalCenter
//            y: dlg.height - this.height - 20
//            spacing: 20
//            Button {
//                id: btnOkay
//                text: "Okay"
//                Layout.preferredWidth: this.width
//                Layout.preferredHeight: this.height
//                onClicked: { dlg.accept() }
//            } // btnOkay
//            Button {
//                id: btnCancel
//                text: "Cancel"
//                Layout.preferredWidth: this.width
//                Layout.preferredHeight: this.height
//                onClicked: { dlg.reject() }
//            } // btnCancel
//
//        } // rwlButtons

//        Keys.onPressed: if (event.key === Qt.Key_R && (event.modifiers & Qt.ControlModifier)) dlg.click(StandardButton.Retry)
        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject() // especially necessary on Android
    }
}
