import QtQuick 2.6
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

//import "../common"

Dialog {
    id: dlg
    width: 580
    height: 600
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "Select Cutter"

    property alias btnCancel: btnCancel
    property alias btnOkay: btnOkay
    property alias lvPersonnel: lvPersonnel
//    property string currentRecorder: ""

    signal recorderChanged(int id, string name);

    onRejected: {  }
    onAccepted: {
        if (lvPersonnel.currentIndex !== -1) {
            var item = lvPersonnel.model.get(lvPersonnel.currentIndex);
            var id = item["id"];
            var name = item["displayText"];
            console.info('recorderChanged: ' + id + ', ' + name);
            recorderChanged(id, name);
        }
    }

    contentItem: Rectangle {
        color: "#eee"
        ColumnLayout {
            y: 20
            spacing: 20

            Label {
                id: lblMessage
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text: "Please select the Cutter for this site"
                font.pixelSize: 20
            } // lblMessage
            ListView {
                id: lvPersonnel
                Layout.preferredHeight: dlg.height - lblMessage.height - rwlButtons.height - 80
                Layout.preferredWidth: dlg.width;
                anchors.horizontalCenter: parent.horizontalCenter
                model: fishSampling.personnelModel
                delegate: Rectangle {
                    width: parent.width
                    height: 80
                    border.width: 0.5
                    border.color: "lightgray"
//                    color: ListView.isCurrentItem ? "light" : "whitesmoke"
                    color: ListView.isCurrentItem ? "skyblue" : "whitesmoke"
                    Text {
                        text: displayText //styleData.value
                        font.pixelSize: 24
                        renderType: Text.NativeRendering
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            lvPersonnel.currentIndex = index
                        }
                        onDoubleClicked: {
                            lvPersonnel.currentIndex = index
                            dlg.accept()
                        }
                    }
                }
            }
            RowLayout {
                id: rwlButtons
                anchors.horizontalCenter: parent.horizontalCenter
//                y: dlg.height - this.height - 20
                spacing: 20
                BackdeckButton {
                    id: btnOkay
                    text: "Okay"
                    Layout.preferredWidth: this.width
                    Layout.preferredHeight: this.height
                    enabled: lvPersonnel.currentIndex !== -1 ? true : false;
                    onClicked: { dlg.accept() }
                } // btnOkay
                BackdeckButton {
                    id: btnCancel
                    text: "Cancel"
                    Layout.preferredWidth: this.width
                    Layout.preferredHeight: this.height
                    onClicked: { dlg.reject() }
                } // btnCancel
            } // rwlButtons
        }

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject() // especially necessary on Android
    }
}
