import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"
import "."

Dialog {
    id: dlg
    width: 500
    height: 650
    title: "Catch Category + Weight"

    // Note: parent should call clear() after dealing with onAccepted result

    // User selects Catch Category and Retained Weight from this dialog
    property string cc_code: ""
    property int weight: 0

    function clear() {
        cc_code = "";
        weight = 0;

        tvAvailableCC.selection.clear();
        tfWeight.text = "";
        numPadWeight.clearnumpad();
        keyboardCC.setText("");

    }

    contentItem: Rectangle {
        color: "lightgray"


        ColumnLayout {
            anchors.fill: parent
            spacing: 3

            ObserverTableView {
                id: tvAvailableCC
                Layout.fillWidth: true
                Layout.preferredHeight: 250
                headerVisible: false

                model: catchCategory.catchCategoryFullModel

                TableViewColumn {
                    role: "catch_category_code"
                    title: "Code"
                }
                TableViewColumn {
                    role: "catch_category_name"
                    title: "Name"
                }
                onClicked: {                    
                    dlg.cc_code = model.get(row).catch_category_code;
                    keyboardCC.active_tf.text = dlg.cc_code;
                }

            }
            Rectangle {
                Layout.preferredHeight: 300
                Layout.fillWidth: true
                FramScalingKeyboard {
                    id: keyboardCC
                    anchors.fill: parent
                    placeholderText: "Code or Name"
                    hide_ok: true  // hide OK button
                    hide_shift: true // hide SHIFT
                    enable_audio: ObserverSettings.enableAudio
                    function setText(text) {
                        active_tf.text = text;
                    }
                    onKbTextChanged: {
                        catchCategory.filter = kbtext;
                    }

                }
            }
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                FramLabel {
                    text: "Weight"
                }
                TextField {
                    id: tfWeight
                    font.pixelSize: 25
                    text: ""
                    onActiveFocusChanged: {
                        if (focus) {
                            focus = false;
                            numPadWeight.open();
                        }
                    }
                }
            }
            ObserverNumPadDialog {
                id: numPadWeight
                onValueAccepted: {
                    tfWeight.text = accepted_value;
                    dlg.weight = parseInt(accepted_value);
                }
                enable_audio: ObserverSettings.enableAudio
            }
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                FramButton {
                    Layout.preferredHeight: 40
                    Layout.alignment: Qt.AlignHCenter
                    text: "Cancel"
                    onClicked: dlg.reject()
                }
                FramButton {
                    Layout.preferredHeight: 40
                    Layout.alignment: Qt.AlignHCenter
                    text: "OK"
                    enabled: cc_code.length > 0 && weight != 0
                    onClicked: {                        
                        dlg.accept()
                    }
                }

            }
        }

        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
    onRejected: clear();
}
