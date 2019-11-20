import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Window 2.2
import QtQuick.Extras 1.4

import "." // for ScreenUnits

Item {
    id: mainKeyboard
    property TextField result_tf  // TextField to set on return
    property bool hide_ok: false    // Explicitly hide the OK button
    property alias ok_text: buttonOK.text

    property string keyboard_result
    property bool enable_audio: false

    signal attachresult_tf(TextField tf)
    onAttachresult_tf: {
        // Hook up the text box for returning the result
        result_tf = tf
    }

    function hide_tf() {
        textKeyboard.visible = false
    }

    property var active_tf:  textKeyboard // Update this TextField, TextArea, or anything with .text

    function attach_external_tf(external_tf) {
        // Attach an external textfield and hide the attached one
        hide_tf();
        active_tf = external_tf;
    }

    signal keyboardok
    onKeyboardok: {
        keyboard_result = active_tf.text;
        if (state.indexOf("embedded_") == -1) {
            // Note: for embedded states, the OK button won't hide the widget
            result_tf.text = active_tf.text;
            mainKeyboard.visible = false;
            parent.resetfocus();
        }
        if (enable_audio) {
            soundPlayer.play_sound("keyOK", false)
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
        // TODO: Should we update this to match newer keyboard classes?
        active_tf.text += entry
        if (enable_audio) {
            soundPlayer.play_sound("keyInput", false)
        }
    }

    Rectangle {
        id: rectangleKeyBG
        x: -255
        y: -303
        width: 575
        height: 376
        color: "#9fa6ca"

        TextField {
            id: textKeyboard
            x: 22
            y: 8
            width: 545
            height: 46
            font.pixelSize: ScreenUnits.keyboardButtonTextHeight
            placeholderText: qsTr("")
        }

        MouseArea {
            id: mouseArea1
            // catch mouse events from going through to surface below
            anchors.fill: parent
        }
    }

    Grid {
        id: grid1
        x: -238
        y: -242
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

        FramKeyboardButton {
            id: buttonKeyMinus
            text: qsTr("-")
        }

//        FramKeyboardButton {
//            id: buttonKeyComma
//            width: 55
//            height: 55
//            text: qsTr(",")
//        }

//        FramKeyboardButton {
//            id: buttonKeyDot
//            width: 55
//            height: 55
//            text: qsTr(".")
//        }
    }

    Button {
        id: buttonKeySpace
        x: -74
        y: 0
        width: 215
        height: 55
        text: qsTr(" ")
        onClicked: {
            keyentry(text)
        }
    }

    Button {
        id: buttonCaps
        x: -238
        y: 0
        width: 90
        height: 55
        text: qsTr("CAPS")
        onClicked: {
            // Toggle all caps state
            if (mainKeyboard.state != "caps" && mainKeyboard.state != "embedded_caps") {
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
        x: 141
        y: 0
        width: 73
        height: 55
        text: qsTr("\u2190")  // LEFT ARROW
        onClicked: {
            if (active_tf.text.length > 0) {
                active_tf.text = active_tf.text.slice(0, -1)
            }
            keyentry("")  // Emit signal for key entry
        }
        style: buttonCaps.style
    }

    Button {
        id: buttonOK
        x: 225
        y: 0
        width: 90
        height: 55
        text: qsTr("OK")
        visible: !hide_ok
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
        id: buttonClear
        x: -148
        y: 0
        width: 73
        height: 55
        text: qsTr("CLR")
        onClicked: {
            setkeyboardtext("")
        }
        style: buttonCaps.style
    }

    Button {
        id: buttonCR
        x: 259
        y: -130
        width: 51
        height: 107
        text: qsTr("\u21B5")  // Downwards left arrow
        style: buttonOK.style
        onClicked: {
            onClicked: {
                keyentry("\n");
            }
        }

        visible: false
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

