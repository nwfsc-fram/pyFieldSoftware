import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.2
import QtQuick.Window 2.2
import QtQuick.Extras 1.4


import "." // for ScreenUnits

Item {
    id: mainKeyboard
//    property TextField result_tf  // TextField to set on return
//    property string result_text // Text to set on return
    property variant suggestions
    property string keyboard_result
    property string last_text: "" // Workaround for weird around editText getting cleared
    property FramComboBox parent_combo

    signal attachresult_combo(FramComboBox src_model)
    onAttachresult_combo: {
        parent_combo = src_model;
        visible = true;
    }

    signal autokeyboardok
    onAutokeyboardok: {
        // Populate target combobox with the OK'd entry
        keyboard_result = comboTextField.text;
        console.log("onAutokeyboardok: " + keyboard_result);
        if (keyboard_result.length > 0) {
            parent_combo.model.append({text: keyboard_result});
            parent_combo.currentIndex = parent_combo.find(keyboard_result);
        } else {
            parent_combo.currentIndex = -1; // "clear"
        }
        setkeyboardtext(""); // Otherwise, this persists if you click on a different field

        if (state.indexOf("embedded_") == -1) {  // "Popup" Mode
            mainKeyboard.visible = false;
            parent.resetfocus();
        }

    }

    signal setkeyboardcaps
    onSetkeyboardcaps: {
        if (state.indexOf("embedded_") == -1)
            state = "caps";
        else
            state = "embedded_caps";
    }

    signal setkeyboardlowercase
    onSetkeyboardlowercase: {
        if (state.indexOf("embedded_") == -1)
            state = "lowercase";
        else
            state = "embedded_lowercase";
    }

    signal setkeyboardtext(string kbtext)
    onSetkeyboardtext: {
        if(kbtext === "") {
            last_text = ""; // Weirdness with clear
        }
        comboTextField.text = kbtext;
    }

    signal keyentry(string entry)
    onKeyentry: {
        comboTextField.text += entry
    }

    signal sethint(string hintstr)
    onSethint: {
        comboTextField.placeholderText = hintstr;
    }

    Rectangle {
        id: rectangleKeyBG
        x: -255
        y: -303
        width: 585
        height: 423
        color: "#e9d4a8"

        MouseArea {
            id: mouseArea1
            anchors.rightMargin: 0
            anchors.leftMargin: 0
            anchors.topMargin: 0
            anchors.bottomMargin: 0
            // catch mouse events from going through to surface below
            anchors.fill: parent

            ComboBox {
                id: comboAutoComplete
                x: 17
                y: 72
                width: 437
                height: 47
                editable: false  // This will be handled by separate text field

                model: ListModel {
                    id: comboAutoModel
                }
                Component.onCompleted: {
                    addAutoCompleteSuggestions("");
                }

                onVisibleChanged: {
                    // Initially populate edit box from parent combo box
                    if (visible) {
                        comboTextField.text = parent_combo.currentText;
                    }
                }

                onActivated: {
                    console.debug("Activated index: " + index );
                }

                function addAutoCompleteSuggestions(partialstr) {
                    // Perform AutoComplete here
                    //console.debug("Called addAutoCompleteSuggestions for "+ partialstr);
                    comboAutoModel.clear();
                    if (partialstr.length > 0) {
                        autocomplete.search(partialstr);
                        suggestions = autocomplete.suggestions;
                        console.log("Got suggestions " + suggestions);
                        for (var i = 0; i< autocomplete.suggestions.length; i++) {
                            comboAutoModel.append({text: autocomplete.suggestions[i]});
                        }
                        comboAutoComplete.currentIndex = 0;
                    } else {
                        comboAutoComplete.currentIndex = -1;
                    }
                }

                TextField {
                    // Instead of the "editable" combobox
                    id: comboTextField
                    x: 0
                    y: -58
                    width: 550
                    height: parent.height
                    placeholderText: ""
                    font.pixelSize: 25

                    onTextChanged: {
                        comboAutoComplete.addAutoCompleteSuggestions(text);
                    }
                }

                style: ComboBoxStyle {
                    dropDownButtonWidth: 45

                    //font.pixelSize: 25  // Needed to editable TextField font size (ignores label)
                    label: Text {
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                        color: "black"
                        text: control.currentText
                    }

                    // Drop-down customization here
                    property Component __dropDownStyle: MenuStyle {
                        __maxPopupHeight: 600
                        __menuItemType: "comboboxitem"

                        frame: Rectangle {              // background
                            color: "#fff"
                            border.width: 2
                            radius: 5
                        }

                        itemDelegate.label:             // item text
                            Text {
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                                font.pixelSize: 25
                                font.family: "Courier"
                                font.capitalization: Font.SmallCaps
                                color: styleData.selected ? "white" : "black"
                                text: styleData.text
                            }

                        itemDelegate.background: Rectangle {  // selection of an item
                            radius: 2
                            color: styleData.selected ? "darkGray" : "transparent"
                        }
                    }
                    property Component __popupStyle: Style {
                        property int __maxPopupHeight: 400
                        property int submenuOverlap: 0

                        property Component frame: Rectangle {
                            width: (parent ? parent.contentWidth : 0)
                            height: (parent ? parent.contentHeight : 0) + 2
                            border.color: "black"
                            property real maxHeight: 500
                            property int margin: 1
                        }

                        property Component __scrollerStyle: null
                    }
                }

            }

        }
    }

    Grid {
        id: grid1
        x: -239
        y: -178
        width: 553
        height: 184
        rows: 4
        columns: 10

        FramKeyboardButton {
            id: button1
            text: qsTr("1")
        }

        FramKeyboardButton {
            id: button2
            text: qsTr("2")
        }

        FramKeyboardButton {
            id: button3
            text: qsTr("3")
        }

        FramKeyboardButton {
            id: button4
            text: qsTr("4")
        }

        FramKeyboardButton {
            id: button5
            text: qsTr("5")
        }

        FramKeyboardButton {
            id: button6
            text: qsTr("6")
        }

        FramKeyboardButton {
            id: button7
            text: qsTr("7")
        }

        FramKeyboardButton {
            id: button8
            text: qsTr("8")
        }

        FramKeyboardButton {
            id: button9
            text: qsTr("9")
        }

        FramKeyboardButton {
            id: button0
            text: qsTr("0")
        }

        FramKeyboardButton {
            id: buttonKeyQ
            text: qsTr("q")
        }

        FramKeyboardButton {
            id: buttonKeyW
            text: qsTr("w")
        }

        FramKeyboardButton {
            id: buttonKeyE
            text: qsTr("e")
        }

        FramKeyboardButton {
            id: buttonKeyR
            text: qsTr("r")
        }

        FramKeyboardButton {
            id: buttonKeyT
            text: qsTr("t")
        }

        FramKeyboardButton {
            id: buttonKeyY
            text: qsTr("y")
        }

        FramKeyboardButton {
            id: buttonKeyU
            text: qsTr("u")
        }

        FramKeyboardButton {
            id: buttonKeyI
            text: qsTr("i")
        }

        FramKeyboardButton {
            id: buttonKeyO
            text: qsTr("o")
        }

        FramKeyboardButton {
            id: buttonKeyP
            text: qsTr("p")
        }

        FramKeyboardButton {
            id: buttonKeyA
            text: qsTr("a")
        }

        FramKeyboardButton {
            id: buttonKeyS
            text: qsTr("s")
        }

        FramKeyboardButton {
            id: buttonKeyD
            text: qsTr("d")
        }

        FramKeyboardButton {
            id: buttonKeyF
            text: qsTr("f")
        }

        FramKeyboardButton {
            id: buttonKeyG
            text: qsTr("g")
        }

        FramKeyboardButton {
            id: buttonKeyH
            text: qsTr("h")
        }

        FramKeyboardButton {
            id: buttonKeyJ
            text: qsTr("j")
        }

        FramKeyboardButton {
            id: buttonKeyK
            text: qsTr("k")
        }

        FramKeyboardButton {
            id: buttonKeyL
            text: qsTr("l")
        }

        FramKeyboardButton {
            id: buttonKeyBlank
            text: qsTr("")
            enabled: false
            visible: true
            style: ButtonStyle {
                background: Rectangle {
                    color: "#00000000"
                }
            }
        }

        FramKeyboardButton {
            id: buttonKeyBlank2
            text: qsTr("")
            enabled: false
            visible: true
            style: ButtonStyle {
                background: Rectangle {
                    color: "#00000000"
                }
            }
        }
        FramKeyboardButton {
            id: buttonKeyZ
            text: qsTr("z")
        }

        FramKeyboardButton {
            id: buttonKeyX
            text: qsTr("x")
        }

        FramKeyboardButton {
            id: buttonKeyC
            text: qsTr("c")
        }

        FramKeyboardButton {
            id: buttonKeyV
            text: qsTr("v")
        }

        FramKeyboardButton {
            id: buttonKeyB
            text: qsTr("b")
        }

        FramKeyboardButton {
            id: buttonKeyN
            text: qsTr("n")
        }

        FramKeyboardButton {
            id: buttonKeyM
            text: qsTr("m")
        }
    }

    Button {
        id: buttonKeySpace
        x: -75
        y: 55
        width: 215
        height: 55
        text: qsTr(" ")
        onClicked: {
            keyentry(text)
        }
    }

    Button {
        id: buttonCaps
        x: -239
        y: 55
        width: 90
        height: 55
        text: qsTr("CAPS")
        onClicked: {
            // Toggle all caps state
            if (mainKeyboard.state != "caps") {
                setkeyboardcaps()
            } else {
                setkeyboardlowercase()
            }
        }
        style: ButtonStyle {

            label: Component {
                Text {
                    renderType: Text.NativeRendering
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    font.family: "Helvetica"
                    font.pixelSize: ScreenUnits.keyboardButtonTextHeight * 0.75
                    text: control.text
                }
            }
        }
    }

    Button {
        id: buttonBkSp
        x: 140
        y: 55
        width: 73
        height: 55
        text: qsTr("\u2190")  // LEFT ARROW
        onClicked: {
            if (comboAutoComplete.editText.length > 1) {
                comboAutoComplete.editText = comboAutoComplete.editText.slice(0, -1);
            } else {
                // clear
                setkeyboardtext("");
            }
        }
        style: buttonCaps.style
    }

    Button {
        id: buttonOK
        x: 230
        y: 55
        width: 84
        height: 55
        text: qsTr("OK")
        onClicked: {
            autokeyboardok()
        }
        style: ButtonStyle {

            label: Component {
                Text {
                    renderType: Text.NativeRendering
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    font.family: "Helvetica"
                    font.pixelSize: ScreenUnits.keyboardButtonTextHeight
                    font.bold: true
                    text: control.text
                }
            }
        }
    }

    Button {
        id: buttonClear
        x: -149
        y: 55
        width: 73
        height: 55
        text: qsTr("Clr")
        onClicked: {
            setkeyboardtext("")
        }
        style: buttonCaps.style
    }

    Button {
        // Temporary - not ideal workflow
        id: buttonSelectAutocompleted
        x: 201
        y: -232
        width: 113
        height: 48
        text: qsTr("\u2190 Select")
        style: buttonCaps.style
        onClicked: {
            comboTextField.text = comboAutoComplete.currentText;
            autokeyboardok();
        }
    }

    states: [
        State {
            name: "lowercase"
        },
        State {
            name: "caps"

            PropertyChanges {
                target: buttonKeyQ
                text: qsTr("Q")
            }

            PropertyChanges {
                target: buttonKeyW
                text: qsTr("W")
            }

            PropertyChanges {
                target: buttonKeyE
                text: qsTr("E")
            }

            PropertyChanges {
                target: buttonKeyR
                text: qsTr("R")
            }

            PropertyChanges {
                target: buttonKeyT
                text: qsTr("T")
            }

            PropertyChanges {
                target: buttonKeyY
                text: qsTr("Y")
            }

            PropertyChanges {
                target: buttonKeyU
                text: qsTr("U")
            }

            PropertyChanges {
                target: buttonKeyI
                text: qsTr("I")
            }

            PropertyChanges {
                target: buttonKeyO
                text: qsTr("O")
            }

            PropertyChanges {
                target: buttonKeyP
                text: qsTr("P")
            }

            PropertyChanges {
                target: buttonKeyA
                text: qsTr("A")
            }

            PropertyChanges {
                target: buttonKeyS
                text: qsTr("S")
            }

            PropertyChanges {
                target: buttonKeyD
                text: qsTr("D")
            }

            PropertyChanges {
                target: buttonKeyF
                text: qsTr("F")
            }

            PropertyChanges {
                target: buttonKeyG
                text: qsTr("G")
            }

            PropertyChanges {
                target: buttonKeyH
                text: qsTr("H")
            }

            PropertyChanges {
                target: buttonKeyJ
                text: qsTr("J")
            }

            PropertyChanges {
                target: buttonKeyK
                text: qsTr("K")
            }

            PropertyChanges {
                target: buttonKeyL
                text: qsTr("L")
            }

            PropertyChanges {
                target: buttonKeyZ
                text: qsTr("Z")
            }

            PropertyChanges {
                target: buttonKeyX
                text: qsTr("X")
            }

            PropertyChanges {
                target: buttonKeyC
                text: qsTr("C")
            }

            PropertyChanges {
                target: buttonKeyV
                text: qsTr("V")
            }

            PropertyChanges {
                target: buttonKeyB
                text: qsTr("B")
            }

            PropertyChanges {
                target: buttonKeyN
                text: qsTr("N")
            }

            PropertyChanges {
                target: buttonKeyM
                text: qsTr("M")
            }

            PropertyChanges {
                target: buttonCaps
                text: qsTr("lowercase")
            }
        },
        State {
            name: "embedded_lowercase"

            PropertyChanges {
                target: rectangleKeyBG
                color: "#00000000"
            }
        },
        State {
            name: "embedded_caps"
            PropertyChanges {
                target: buttonKeyQ
                text: qsTr("Q")
            }

            PropertyChanges {
                target: buttonKeyW
                text: qsTr("W")
            }

            PropertyChanges {
                target: buttonKeyE
                text: qsTr("E")
            }

            PropertyChanges {
                target: buttonKeyR
                text: qsTr("R")
            }

            PropertyChanges {
                target: buttonKeyT
                text: qsTr("T")
            }

            PropertyChanges {
                target: buttonKeyY
                text: qsTr("Y")
            }

            PropertyChanges {
                target: buttonKeyU
                text: qsTr("U")
            }

            PropertyChanges {
                target: buttonKeyI
                text: qsTr("I")
            }

            PropertyChanges {
                target: buttonKeyO
                text: qsTr("O")
            }

            PropertyChanges {
                target: buttonKeyP
                text: qsTr("P")
            }

            PropertyChanges {
                target: buttonKeyA
                text: qsTr("A")
            }

            PropertyChanges {
                target: buttonKeyS
                text: qsTr("S")
            }

            PropertyChanges {
                target: buttonKeyD
                text: qsTr("D")
            }

            PropertyChanges {
                target: buttonKeyF
                text: qsTr("F")
            }

            PropertyChanges {
                target: buttonKeyG
                text: qsTr("G")
            }

            PropertyChanges {
                target: buttonKeyH
                text: qsTr("H")
            }

            PropertyChanges {
                target: buttonKeyJ
                text: qsTr("J")
            }

            PropertyChanges {
                target: buttonKeyK
                text: qsTr("K")
            }

            PropertyChanges {
                target: buttonKeyL
                text: qsTr("L")
            }

            PropertyChanges {
                target: buttonKeyZ
                text: qsTr("Z")
            }

            PropertyChanges {
                target: buttonKeyX
                text: qsTr("X")
            }

            PropertyChanges {
                target: buttonKeyC
                text: qsTr("C")
            }

            PropertyChanges {
                target: buttonKeyV
                text: qsTr("V")
            }

            PropertyChanges {
                target: buttonKeyB
                text: qsTr("B")
            }

            PropertyChanges {
                target: buttonKeyN
                text: qsTr("N")
            }

            PropertyChanges {
                target: buttonKeyM
                text: qsTr("M")
            }

            PropertyChanges {
                target: buttonCaps
                text: qsTr("lowercase")
            }

            PropertyChanges {
                target: rectangleKeyBG
                color: "#00000000"
            }
        }
    ]


}

