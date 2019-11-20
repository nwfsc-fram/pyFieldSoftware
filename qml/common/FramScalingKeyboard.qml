import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Window 2.2
import QtQuick.Extras 1.4

import "."

// Scalable keyboard -- expands to parent dimensions

Item {
    id: mainKeyboard
    property TextField result_tf: null  // TextField to set on return
    property bool cancel_only: false // For mandatory inputs, hide the OK button and only allow cancel
    property bool hide_ok: false // explicitly hide the OK button
    property bool hide_ok_if_empty_text: false // Hide the OK button if result_tf is empty (i.e. need text for OK)
    property bool hide_shift: false // explicitly hide the shift button
    property string currentText: active_tf.text
    property alias placeholderText: textKeyboard.placeholderText
    property string keyboard_result
    property bool enable_audio: false

    anchors.fill: parent

    signal attachresult_tf(TextField tf)
    onAttachresult_tf: {
        // Hook up the text box for returning the result
        result_tf = tf
    }

    function hide_tf() {
        textKeyboard.visible = false
    }

    property var active_tf:  textKeyboard // Update this TextField, TextArea, or anything with .text

    function set_active_tf(external_tf) {
        // Intended for use with hidden tf, use another textfield for input
        active_tf = external_tf;
    }

    function attach_external_tf(external_tf, placeholder) {
        result_tf = external_tf;
        active_tf.text = external_tf.text;
        active_tf.placeholderText = placeholder;
    }
    function attach_external_textarea(external_ta) {
        active_tf = external_ta;
    }

    signal keyboardCancel

    signal keyboardok
    onKeyboardok: {

        keyboard_result = active_tf.text;
        if (result_tf) {
            result_tf.text = active_tf.text;        
        }
        if (enable_audio) {
            soundPlayer.play_sound("keyOK", false)
        }
    }

    signal setkeyboardlowercase
    onSetkeyboardlowercase: {
        state = "lowercase_state";
    }

    signal setkeyboardcaps
    onSetkeyboardcaps: {
        state = "caps_state";
    }

    signal setkeyboardhint(string kbhint)
    onSetkeyboardhint: {
        active_tf.placeholderText = kbhint
    }
    signal setkeyboardtext(string kbtext)
    onSetkeyboardtext: {
        active_tf.text = kbtext
    }

    signal showCR(bool show)
    onShowCR: {
        buttonCR.visible = true;
    }

    signal keyentry(string entry)
    onKeyentry: {        
        clearSelected();
        var curpos = active_tf.cursorPosition;
        // insert into string (at cursor)
        active_tf.text = active_tf.text.slice(0, curpos) + entry +
                active_tf.text.slice(curpos);
        active_tf.cursorPosition = curpos + entry.length;
        if (enable_audio) {
            soundPlayer.play_sound("keyInput", false)
        }
    }

    signal kbTextChanged(string kbtext)

    signal selectAll()
    onSelectAll: {
        textKeyboard.selectAll();
        textKeyboard.forceActiveFocus();
    }

    function clearSelected() {       
       textKeyboard.text = textKeyboard.text.replace(textKeyboard.selectedText, "")
    }

    function password_mode(is_set) {
        if (is_set) {
            textKeyboard.echoMode = TextInput.Password;
        } else {
            textKeyboard.echoMode = TextInput.Normal;
        }
    }

    Rectangle {
        id: rectangleKeyBG
        anchors.fill: parent
        color: "transparent"

        MouseArea {
            id: mouseArea1
            // catch mouse events from going through to surface below
            anchors.fill: parent
        }
    }

    GridLayout {
        id: gridKeys
        anchors.fill: parent
        rows: 4
        columns: 13
        rowSpacing: 2
        columnSpacing: 2
        property int buttonWidth: (parent.width - (columnSpacing * columns - 1)) / columns
        property int buttonHeight: (parent.height - (rowSpacing * rows)) / (rows + 2) - rowSpacing

        Keys.onReturnPressed: {
            keyboardok();
        }

        Keys.onEnterPressed: {

            keyboardok();
        }

        TextField {
            id: textKeyboard
            implicitWidth: parent.width
            implicitHeight: gridKeys.buttonHeight
            font.pixelSize: ScreenUnits.keyboardButtonTextHeight
            placeholderText: qsTr("")
            Layout.columnSpan: 13
            onTextChanged: {
                kbTextChanged(text);
            }
        }

        FramScalingKeyboardButton {
            id: buttonBacktick
            text: qsTr("`")
        }

        FramScalingKeyboardButton {
            id: button1
            text: qsTr("1")
        }

        FramScalingKeyboardButton {
            id: button2
            text: qsTr("2")
        }

        FramScalingKeyboardButton {
            id: button3
            text: qsTr("3")
        }

        FramScalingKeyboardButton {
            id: button4
            text: qsTr("4")
        }

        FramScalingKeyboardButton {
            id: button5
            text: qsTr("5")
        }

        FramScalingKeyboardButton {
            id: button6
            text: qsTr("6")
        }

        FramScalingKeyboardButton {
            id: button7
            text: qsTr("7")
        }

        FramScalingKeyboardButton {
            id: button8
            text: qsTr("8")
        }

        FramScalingKeyboardButton {
            id: button9
            text: qsTr("9")
        }

        FramScalingKeyboardButton {
            id: button0
            text: qsTr("0")
        }

        FramScalingKeyboardButton {
            id: buttonKeyMinus
            text: qsTr("-")
        }

        FramScalingKeyboardButton {
            id: buttonKeyEquals
            text: qsTr("=")
        }

        FramScalingKeyboardButton {
            id: buttonKeyQ
            text: qsTr("Q")
        }

        FramScalingKeyboardButton {
            id: buttonKeyW
            text: qsTr("W")
        }

        FramScalingKeyboardButton {
            id: buttonKeyE
            text: qsTr("E")
        }

        FramScalingKeyboardButton {
            id: buttonKeyR
            text: qsTr("R")
        }

        FramScalingKeyboardButton {
            id: buttonKeyT
            text: qsTr("T")
        }

        FramScalingKeyboardButton {
            id: buttonKeyY
            text: qsTr("Y")
        }

        FramScalingKeyboardButton {
            id: buttonKeyU
            text: qsTr("U")
        }

        FramScalingKeyboardButton {
            id: buttonKeyI
            text: qsTr("I")
        }

        FramScalingKeyboardButton {
            id: buttonKeyO
            text: qsTr("O")
        }

        FramScalingKeyboardButton {
            id: buttonKeyP
            text: qsTr("P")
        }
        FramScalingKeyboardButton {
            id: buttonKeySquareLeft
            text: qsTr("[")
        }
        FramScalingKeyboardButton {
            id: buttonKeySquareRight
            text: qsTr("]")
        }

        FramScalingKeyboardButton {
            id: buttonKeyBackslash
            text: qsTr("\\")
        }

        FramScalingKeyboardButton {
            // Spacer
            text: qsTr("")
            enabled: false
            visible: true
            style: ButtonStyle {
                background: Rectangle {
                    color: "#00000000"
                }
            }
        }

        FramScalingKeyboardButton {
            id: buttonKeyA
            text: qsTr("A")
        }

        FramScalingKeyboardButton {
            id: buttonKeyS
            text: qsTr("S")
        }

        FramScalingKeyboardButton {
            id: buttonKeyD
            text: qsTr("D")
        }

        FramScalingKeyboardButton {
            id: buttonKeyF
            text: qsTr("F")
        }

        FramScalingKeyboardButton {
            id: buttonKeyG
            text: qsTr("G")
        }

        FramScalingKeyboardButton {
            id: buttonKeyH
            text: qsTr("H")
        }

        FramScalingKeyboardButton {
            id: buttonKeyJ
            text: qsTr("J")
        }

        FramScalingKeyboardButton {
            id: buttonKeyK
            text: qsTr("K")
        }

        FramScalingKeyboardButton {
            id: buttonKeyL
            text: qsTr("L")
        }

        FramScalingKeyboardButton {
            id: buttonKeySemicolon
            text: qsTr(";")
        }

        FramScalingKeyboardButton {
            id: buttonKeyQuote
            text: qsTr("'")
        }

        FramScalingKeyboardButton {
            // Spacer
            text: qsTr("")
            enabled: false
            visible: true
            style: ButtonStyle {
                background: Rectangle {
                    color: "#00000000"
                }
            }
        }

        FramScalingKeyboardButton {
            // Spacer
            text: qsTr("")
            enabled: false
            visible: true
            style: ButtonStyle {
                background: Rectangle {
                    color: "#00000000"
                }
            }
        }

        FramScalingKeyboardButton {
            id: buttonKeyZ
            text: qsTr("Z")
        }

        FramScalingKeyboardButton {
            id: buttonKeyX
            text: qsTr("X")
        }

        FramScalingKeyboardButton {
            id: buttonKeyC
            text: qsTr("C")
        }

        FramScalingKeyboardButton {
            id: buttonKeyV
            text: qsTr("V")
        }

        FramScalingKeyboardButton {
            id: buttonKeyB
            text: qsTr("B")
        }

        FramScalingKeyboardButton {
            id: buttonKeyN
            text: qsTr("N")
        }

        FramScalingKeyboardButton {
            id: buttonKeyM
            text: qsTr("M")
        }



        FramScalingKeyboardButton {
            id: buttonKeyComma
            width: 55
            height: 55
            text: qsTr(",")
        }

        FramScalingKeyboardButton {
            id: buttonKeyDot
            width: 55
            height: 55
            text: qsTr(".")
        }
        FramScalingKeyboardButton {
            id: buttonKeyFwdSlash
            width: 55
            height: 55
            text: qsTr("/")
        }

        FramScalingKeyboardButton {
            // Spacer
            text: qsTr("")
            enabled: false
            visible: true
            style: ButtonStyle {
                background: Rectangle {
                    color: "#00000000"
                }
            }
        }

        Button {
            id: buttonCR
            implicitWidth: gridKeys.buttonWidth
            implicitHeight: gridKeys.buttonHeight
            text: qsTr("\u21b5")  // CR Arrow
            visible: false
            onClicked: {
                keyentry("\n")
            }
            style: buttonOK.style
        }

        Button {
            id: buttonCaps
            implicitWidth: gridKeys.buttonWidth * 2
            implicitHeight: gridKeys.buttonHeight
            visible: !hide_shift
            text: qsTr("SHIFT")
            onClicked: {
                // Toggle all caps state
                if (mainKeyboard.state != "lowercase_state") {
                    setkeyboardlowercase()
                } else {
                    setkeyboardcaps()
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
            Layout.columnSpan: 2
        }

        Label { // show instead of shift
            id: noShiftSpacer
            visible: hide_shift
            Layout.columnSpan: 2
            Layout.preferredWidth: gridKeys.buttonWidth * 2
            Layout.preferredHeight: gridKeys.buttonHeight
        }

        Button {
            id: buttonKeySpace
            implicitWidth: gridKeys.buttonWidth * 7 +  6 * gridKeys.columnSpacing
            implicitHeight: gridKeys.buttonHeight
            text: qsTr(" ")
            onClicked: {
                keyentry(text)
            }
            Layout.columnSpan: 7

        }

        Button {
            id: buttonBkSp
            implicitWidth: gridKeys.buttonWidth
            implicitHeight: gridKeys.buttonHeight
            text: qsTr("\u2190")  // LEFT ARROW
            onClicked: {
                var text_len = active_tf.text.length;
                if (text_len > 0) {
                    clearSelected();
                    var del_cursor = active_tf.cursorPosition;
                    if (del_cursor > 0) {
                        if (del_cursor == text_len) {
                            active_tf.cursorPosition = del_cursor-1;  // warning/ bug workaround
                            active_tf.text = active_tf.text.slice(0, del_cursor-1);
                            active_tf.cursorPosition = del_cursor-1;
                        } else {
                            active_tf.text = active_tf.text.slice(0, del_cursor-1) +
                              active_tf.text.slice(del_cursor);
                            active_tf.cursorPosition = del_cursor-1;
                        }
                    }
                }                
                keyentry("")  // Emit signal for key entry
            }
            style: buttonCaps.style
        }

        Button {
            id: buttonClear
            implicitWidth: gridKeys.buttonWidth
            implicitHeight: gridKeys.buttonHeight
            text: qsTr("CLR")
            onClicked: {
                setkeyboardtext("")
            }
            style: buttonCaps.style
        }

        Button {
            id: buttonOK
            implicitWidth: gridKeys.buttonWidth
            implicitHeight: gridKeys.buttonHeight
            text: qsTr("OK")
            visible: !hide_ok &&
                    (!cancel_only || textKeyboard.text == "") &&
                    (!hide_ok_if_empty_text || textKeyboard.text.length > 0)
            onClicked: {
                keyboardok()
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
            id: buttonCancel
            implicitWidth: gridKeys.buttonWidth
            implicitHeight: gridKeys.buttonHeight
            text: qsTr("Cancel")
            visible: cancel_only && textKeyboard.text != "" ||
                    (hide_ok_if_empty_text && textKeyboard.text == "")  // If empty text not OK, allow cancel
            onClicked: {
                keyboardCancel()
            }
            style: ButtonStyle {

                label: Component {
                    Text {
                        renderType: Text.NativeRendering
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        font.family: "Helvetica"
                        font.pixelSize: 15
                        font.bold: true
                        text: control.text
                    }
                }
            }
        }

        FramScalingKeyboardButton {
            // Keep this around for formatting correctness
            id: buttonNeededForSpaceAtBottom
            implicitHeight: 20
            text: qsTr("")
            enabled: false
            visible: true
            style: ButtonStyle {
                background: Rectangle {
                    color: "#00000000"
                }
            }
            Layout.columnSpan: 5
        }

    }

    states: [
        State {
            name: "caps_state"
        },
        State {
            name: "lowercase_state"
            PropertyChanges {
                target: buttonKeyQ
                text: qsTr("q")
            }

            PropertyChanges {
                target: buttonKeyW
                text: qsTr("w")
            }

            PropertyChanges {
                target: buttonKeyE
                text: qsTr("e")
            }

            PropertyChanges {
                target: buttonKeyR
                text: qsTr("r")
            }

            PropertyChanges {
                target: buttonKeyT
                text: qsTr("t")
            }

            PropertyChanges {
                target: buttonKeyY
                text: qsTr("y")
            }

            PropertyChanges {
                target: buttonKeyU
                text: qsTr("u")
            }

            PropertyChanges {
                target: buttonKeyI
                text: qsTr("i")
            }

            PropertyChanges {
                target: buttonKeyO
                text: qsTr("o")
            }

            PropertyChanges {
                target: buttonKeyP
                text: qsTr("p")
            }

            PropertyChanges {
                target: buttonKeyA
                text: qsTr("a")
            }

            PropertyChanges {
                target: buttonKeyS
                text: qsTr("s")
            }

            PropertyChanges {
                target: buttonKeyD
                text: qsTr("d")
            }

            PropertyChanges {
                target: buttonKeyF
                text: qsTr("f")
            }

            PropertyChanges {
                target: buttonKeyG
                text: qsTr("g")
            }

            PropertyChanges {
                target: buttonKeyH
                text: qsTr("h")
            }

            PropertyChanges {
                target: buttonKeyJ
                text: qsTr("j")
            }

            PropertyChanges {
                target: buttonKeyK
                text: qsTr("k")
            }

            PropertyChanges {
                target: buttonKeyL
                text: qsTr("l")
            }

            PropertyChanges {
                target: buttonKeyZ
                text: qsTr("z")
            }

            PropertyChanges {
                target: buttonKeyX
                text: qsTr("x")
            }

            PropertyChanges {
                target: buttonKeyC
                text: qsTr("c")
            }

            PropertyChanges {
                target: buttonKeyV
                text: qsTr("v")
            }

            PropertyChanges {
                target: buttonKeyB
                text: qsTr("b")
            }

            PropertyChanges {
                target: buttonKeyN
                text: qsTr("n")
            }

            PropertyChanges {
                target: buttonKeyM
                text: qsTr("m")
            }

            PropertyChanges {
                target: buttonCaps
                text: qsTr("SHIFT")
            }

            PropertyChanges {
                target: buttonBacktick
                text: qsTr("~")
            }

            PropertyChanges {
                target: button1
                text: qsTr("!")
            }

            PropertyChanges {
                target: button2
                text: qsTr("@")
            }

            PropertyChanges {
                target: button3
                text: qsTr("#")
            }

            PropertyChanges {
                target: button4
                text: qsTr("$")
            }

            PropertyChanges {
                target: button5
                text: qsTr("%")
            }

            PropertyChanges {
                target: button6
                text: qsTr("^")
            }

            PropertyChanges {
                target: button7
                text: qsTr("&")
            }

            PropertyChanges {
                target: button8
                text: qsTr("*")
            }

            PropertyChanges {
                target: button9
                text: qsTr("(")
            }

            PropertyChanges {
                target: button0
                text: qsTr(")")
            }

            PropertyChanges {
                target: buttonKeyMinus
                text: qsTr("_")
            }

            PropertyChanges {
                target: buttonKeyEquals
                text: qsTr("+")
            }

            PropertyChanges {
                target: buttonKeySquareLeft
                text: qsTr("{")
            }

            PropertyChanges {
                target: buttonKeySquareRight
                text: qsTr("}")
            }

            PropertyChanges {
                target: buttonKeyBackslash
                text: qsTr("|")
            }
            PropertyChanges {
                target: buttonKeySemicolon
                text: qsTr(":")
            }

            PropertyChanges {
                target: buttonKeyQuote
                text: qsTr("\"")
            }

            PropertyChanges {
                target: buttonKeyComma
                text: qsTr("<")
            }

            PropertyChanges {
                target: buttonKeyDot
                text: qsTr(">")
            }

            PropertyChanges {
                target: buttonKeyFwdSlash
                text: qsTr("?")
            }

            PropertyChanges {
                target: rectangleKeyBG
                color: "transparent"
            }
        }
    ]


}

