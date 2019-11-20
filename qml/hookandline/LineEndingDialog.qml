import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 500
    height: 200
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "Line Ending"

//    property int screen_id: -1
    property string message: ""
    property string action: ""
    property string accepted_action: ""
//    property string screen: ""

    property alias tfLineEnding: tfLineEnding
    property variant lastCharacters: []

    onRejected: {}
    onAccepted: {}

    function add_character(str) {
        tfLineEnding.text = tfLineEnding.text + str;
        lastCharacters.push(str);
    }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        RowLayout {
            id: rwlCharacters
            anchors.horizontalCenter: parent.horizontalCenter
            y: 20
            spacing: 5
            Button {
                id: btnCR
                text: qsTr("CR")
                Layout.preferredWidth: 30
                onClicked: {
                    add_character("\\r")
                }
                tooltip: qsTr("\\r - Carriage Return")
            } // btnCR
            Button {
                id: btnLF
                text: qsTr("LF")
                Layout.preferredWidth: 30
                onClicked: {
                    add_character("\\n")
                }
                tooltip: qsTr("\\n - Line Feed")
            } // btnLF
            Button {
                id: btnAnyCharacter
                text: qsTr("Any Character")
                Layout.preferredWidth: 100
                onClicked: {
                    add_character(".")
                }
                tooltip: qsTr(". - Matches 1 of any character except a Line Feed, \\n")
            } // btnAnyCharacter
            Button {
                id: btnZeroOrOnePrevious
                text: qsTr("0 or 1 Previous")
                Layout.preferredWidth: 100
                onClicked: {
                    add_character("?")
                }
                tooltip: qsTr("? - Matches 0 or 1 copies of the previous character")
            } // btnZeroOrOnePrevious
            TextField {
                id: tfNPrevious
                text: qsTr("1")
                Layout.preferredWidth: 30
            } // tfNPrevious
            Button {
                id: btnNPrevious
                text: qsTr("N Previous")
                Layout.preferredWidth: 100
                onClicked: {
                    add_character("{" + tfNPrevious.text + "}")
                }
                tooltip: qsTr("{n} - Matches N copies of the previous character")
            } // btnZeroOrOnePrevious
        } // rwlCharacters
        RowLayout {
            id: rwlOutput
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: rwlCharacters.bottom
            anchors.topMargin: 20
            spacing: 20
            Label {
                id: lblFinalOutput
                text: qsTr("Final Output:")
            } // lblFinalOutput
            TextField {
                id: tfLineEnding
                text: ""
                enabled: false
            } // tfLineEnding
            ColumnLayout {
                id: cllRemovingItems
                spacing: 5
                Button {
                    id: btnLastCharacter
                    text: qsTr("Remove Last Character")
                    Layout.preferredWidth: 130
                    onClicked: {
                        var lastCharacter = lastCharacters.pop()
                        tfLineEnding.text =
                            tfLineEnding.text.slice(0, -(lastCharacter.length));
                    }
                } // btnRemoveLastCharacter
                Button {
                    id: btnClear
                    text: qsTr("Clear")
                    Layout.preferredWidth: 80
                    onClicked: {
                        tfLineEnding.text = ""
                    }
                } // btnClear
            } // cllRemovingItems

        } // rwlOutput

        RowLayout {
            id: rwlButtons
            anchors.horizontalCenter: parent.horizontalCenter
            y: dlg.height - this.height - 20
            spacing: 20
            Button {
                id: btnOkay
                text: "Okay"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.accept() }
            } // btnOkay
            Button {
                id: btnCancel
                text: "Cancel"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.reject() }
            } // btnCancel
        } // rwlButtons

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
}
