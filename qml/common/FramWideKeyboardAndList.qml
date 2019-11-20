// "Big" Keyboard with scrollable autocomplete list - for landscape screen mode

import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Controls.Styles 1.4

import "."

Rectangle {  // Encompasses keyboard on left and scrollable list on right.
    id: keyboardRect
    width: parent.width
    height: desired_height
    x: 0
    y: parent.y + parent.height - height
    color: "#AAAAAA"

    property int desired_height: 315 // Hidden text field
    property FramScalingKeyboard keyboard: keyboardEmbedded
    property alias hide_ok_if_empty_text: keyboardEmbedded.hide_ok_if_empty_text
    property TextField active_tf: keyboardEmbedded.active_tf
    property int fontsize: 25
    property bool opaque: false
    property bool autocomplete_active: true
    property bool mandatory_autocomplete: false
    property alias enable_audio: keyboardEmbedded.enable_audio


    Keys.forwardTo: [keyboardEmbedded]

    function clearList() {
        listAutocomplete.model = null;
    }

    Rectangle {
        id: keyboardLeft
        width: parent.width * 0.6
        height: parent.height
        FramScalingKeyboard {
            id: keyboardEmbedded
            // Typically every change in text of a keyboard will prompt an autocomplete search.
            // Allow an exception - when the keyboard text has been set from a selection of listAutocomplete.
            property bool doSearchOnTextChange: true
            anchors.fill: parent
            state: "embedded_lower"
            cancel_only: keyboardRect.mandatory_autocomplete
            enable_audio: false

            // Propagate these signals up:
            onKeyboardok: {
                buttonOk();
            }
            onKeyboardCancel: {
                buttonCancel();
            }

            onKeyentry: {
                keyEntry();

            }
            onKbTextChanged: {
                if (doSearchOnTextChange) {
                    addAutoCompleteSuggestions(kbtext);
                }
            }
        }
    }

    ////
    // Autocomplete Scrollable ListView
    ////
    Rectangle {
        id: listRight
        property int spacerWidth: 2 // Between right edge of keyboard and scrolling list
        width: (parent.width * 0.4) - spacerWidth
        height: parent.height
        x: keyboardLeft.x + keyboardLeft.width + spacerWidth
        y: 0
        z: 1
        clip: true

        FramBigScrollView {
            id: scrollAutocomplete
            anchors.fill: parent
            flickableItem.interactive: true     // This is key - not visible otherwise.

            ListView {
                id: listAutocomplete
                anchors.fill: parent
                model: ListModel {}

                highlight: Rectangle { color: "lightsteelblue"; radius: 5}
                focus: true
                delegate: delegateAC
                onCurrentItemChanged: {

                }

                Component {
                    id: delegateAC
                    Rectangle {
                        color: "white"
                        property var itemData: model.modelData
                        width: parent.width
                        height: 40
                        Row {
                            Text {
                                text: model.modelData
                                font.pixelSize: keyboardRect.fontsize
                            }
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                listAutocomplete.currentIndex = index;
                                // Avoid triggering another autocomplete search - already done!
                                keyboardEmbedded.doSearchOnTextChange = false;
                                keyboardEmbedded.setkeyboardtext(itemData);
                                // Restore the default in preparation for the next search.
                                keyboardEmbedded.doSearchOnTextChange = true;
                                console.debug("Set keyboard text to " + itemData);

                                // Even for non-mandatory_autocomplete keyboards (inputs other than on list allowed),
                                // close the keyboard here to accept the clicked-on item from the list.
                                keyboardEmbedded.keyboardok();
                            }
                        }
                    }
                }
            }
        }
    }

    signal showbottomkeyboard(bool show)
    onShowbottomkeyboard: {
        keyboardRect.visible = show;
        keyboardRect.height = show ? keyboardRect.height = keyboardRect.desired_height : keyboardRect.height = 0;
    }

    function connect_tf(tf, placeholder) {  // TextField
        keyboardEmbedded.attach_external_tf(tf, placeholder);
        active_tf.forceActiveFocus();
        keyboardEmbedded.selectAll();
    }

    function connect_ta(ta) {  // TextArea
        connect_tf(ta);
        // same connection as TextField since it has .text property
    }

    function clearCurrentText() {
        active_tf.text = "";
    }

    signal buttonOk() // OK button hit
    onButtonOk: {
        showbottomkeyboard(false);
    }

    signal buttonCancel() // Cancel button hit
    onButtonCancel: {
        showbottomkeyboard(false);
    }

    signal keyEntry() // key entered

    function addAutoCompleteSuggestions(partialstr) {
        if (!autocomplete_active)
            return;

        // Short lists like Fisheries will return full list on empty search
        autocomplete.search(partialstr);
        listAutocomplete.model = autocomplete.suggestions;
    }

    function password_mode(is_set) {
        keyboardEmbedded.password_mode(is_set);
    }
}
