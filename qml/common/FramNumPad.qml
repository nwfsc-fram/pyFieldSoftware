import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Window 2.2
import QtQuick.Extras 1.4

import "." // For ScreenUnits

Item {
    id: keyPad
    property TextField result_tf  // TextField to set on return
    property alias btnOk: buttonKeyOK
    property alias recBackground: rectangleNPBackground
    property alias textNumPad: textNumPad

    property string stored_result: "" // For - and + key operation
    property bool adding_mode: false // For - and + key operation
    property bool subtracting_mode: false // For - and + key operation
    property bool limitToTwoDecimalPlaces: false // Set true if using FramNumPad to enter weights.

    property bool skip_button_mode: false // Show "Skip" instead of OK button when nothing entered
    property bool enable_audio: false

    Component.onCompleted: {
        setnumpadvalue(0);
    }

    Keys.onEnterPressed: {
        // NOTE: to get numpad keyboard entry, the parent window must forward keystrokes:
        // e.g. Keys.forwardTo: [framNumPadDetails, framKeyboardDetails]
        numpadok();
    }

    signal show(bool show)
    onShow: {
        if (show) { // Select all when shown for easier re-entry
            textNumPad.selectAll();
        }

        if (!keyPad.visible) {
            keyPad.visible = show;            
        }
    }

    signal numpadok
    onNumpadok: {
        // "OK" Button pressed
        // NOTE: For non-popup modes, do nothing: the parent should handle onNumpadok
        stored_result = textNumPad.text;
        if (state.indexOf("popup_") != -1) {
            // Popup mode: hide window and set target textfield
            keyPad.visible = false;
            result_tf.text = textNumPad.text;
            parent.resetfocus();
        }
        if (enable_audio) {
            soundPlayer.play_sound("numpadOK", false)
        }
    }

    signal noCountPressed  // pressed No Count button
    signal noWeightPressed  // pressed No Count button

    function show_no_count(show) {
        buttonNoCount.visible = show;
    }
    function show_no_weight(show) {
        buttonNoWeight.visible = show;
    }

    signal attachresult_tf(TextField tf)
    onAttachresult_tf: {
        // Hook up the text box for returning the result
        result_tf = tf
    }

    signal clearnumpad
    onClearnumpad: {
        setnumpadvalue(0);
        if (skip_button_mode) {
            textNumPad.text = ""
            setSkipButtonMode(true); // reset skip text
        }        
    }

    signal backspacenumpad
    onBackspacenumpad: {
        var numtxt = textNumPad.text
        if(numtxt.length > 1) {
            numtxt = numtxt.slice(0, -1);
            textNumPad.text = qsTr(numtxt);
            if (skip_button_mode && textNumPad.text == "") {
                setSkipButtonMode(true); // reset skip text
            }
        } else {
            setnumpadvalue(0);
        }
        if (enable_audio) {
            soundPlayer.play_sound("numpadBack", false)
        }
    }

    signal minusnumpad
    onMinusnumpad: {
        // - key

        if(adding_mode) { // finish prior operations
            buttonKeyOK.adding_mode_ok();
        } else if(subtracting_mode) {
            buttonKeyOK.subtracting_mode_ok();
        }
        setSkipButtonMode(false);
        subtracting_mode = true
        stored_result = textNumPad.text;
        buttonKeyOK.setText("=");
        setnumpadvalue(0);
    }

    signal plusnumpad
    onPlusnumpad: {
        // + key
        if(adding_mode) { // finish prior operations
            buttonKeyOK.adding_mode_ok();
        } else if(subtracting_mode) {
            buttonKeyOK.subtracting_mode_ok();
        }
        setSkipButtonMode(false);
        adding_mode = true
        stored_result = textNumPad.text;
        buttonKeyOK.setText("=");
        setnumpadvalue(0);

    }

    signal decimalnumpad
    onDecimalnumpad: {
        // . key. Set the regex validator to allow unlimited decimal places, or up to two.
        //console.debug("limitToTwoDecimalPlaces = " + limitToTwoDecimalPlaces);
        textNumPad.validator = limitToTwoDecimalPlaces ?
                regexValMaxTwoDecimalPlaces :
                regexValUnlimitedDecimalPlaces;
        if (enable_audio) {
            soundPlayer.play_sound("numpadDecimal", false)
        }
    }

    RegExpValidator {
        id: regexValUnlimitedDecimalPlaces
        regExp:  /[0-9]*\.?[0-9]*/
    }

    RegExpValidator {
        id: regexValMaxTwoDecimalPlaces
        regExp:  /[0-9]*\.?[0-9]{0,2}/
    }

    signal setnumpadhint(string numpadhint)
    onSetnumpadhint: {
        textNumPad.placeholderText = numpadhint;
    }

    signal setnumpadvalue(string numpadvalue)
    onSetnumpadvalue: {
        var floatval = numpadvalue; // parseFloat(numpadvalue)
        textNumPad.text = floatval;
        if (skip_button_mode) {
            buttonKeyOK.setText()  // show OK again
        }
    }

    function addnumpadvalue(numpadvalue) {
        var floatval = numpadvalue; // parseFloat(numpadvalue)
        textNumPad.text = floatval;
        if (skip_button_mode) {
            buttonKeyOK.setText()  // show OK again
        }
    }

    signal numpadinput(string input_key)
    onNumpadinput: {
        textNumPad.text = textNumPad.text.replace(textNumPad.selectedText, "")
        if (textNumPad.text.length >= 1 && textNumPad.text.substring(0, 1) == "0" &&
                textNumPad.text.substring(0,2) != "0.")
            textNumPad.text = textNumPad.text.substring(1,1) + input_key;  // parse out leading 0
        else
            textNumPad.text += input_key;

        if (skip_button_mode) {
            buttonKeyOK.setText()  // show OK again
        }
        if (enable_audio) {
            soundPlayer.play_sound("numpadInput", false)
        }

    }

    signal setstate(string set_state)
    onSetstate: {
        // Options: base state, weights, popup_basic, popup_weights
        state = set_state
    }

    function selectAll() {
        textNumPad.selectAll();
    }

    function showDecimal(show) {
        buttonKeyDecimal.visible = show;
    }


    function setSkipButtonMode(skip_mode) {
        // Change text on OK button
        skip_button_mode = skip_mode
        if (skip_mode && textNumPad.text == "") {
            buttonKeyOK.setText("Skip");
        } else {
            buttonKeyOK.setText()  // show OK
        }
    }

    MouseArea {
        anchors.rightMargin: 35
        anchors.bottomMargin: 11
        anchors.leftMargin: -35
        anchors.topMargin: -11
        anchors.fill: parent
    }

    Rectangle {
        id: rectangleNPBackground
        x: -164
        y: -227
        width: 359
        height: 449
        color: "#00000000"

        MouseArea {
            anchors.bottomMargin: 0
            anchors.leftMargin: 0
            anchors.topMargin: 0
            anchors.rightMargin: 0
            // catch mouse events from going through to surface below
            anchors.fill: parent
        }
    }

    GridLayout {
        columns: 4
        rows: 5
        columnSpacing: 6
        rowSpacing: 6
        x: rectangleNPBackground.x
        y: rectangleNPBackground.y

        // Row 1 - Top
        TextField {
            id: textNumPad
            Layout.preferredWidth: 268
            Layout.preferredHeight: ScreenUnits.numPadButtonSize
            Layout.columnSpan: 3
            font.pixelSize: 30
            horizontalAlignment: Text.AlignRight
            validator: regexValUnlimitedDecimalPlaces // By default
            onTextChanged: {
                // Zero pad if leftmost char is just a decimal
                if (textNumPad.text.charAt(0) == ".") {
                    textNumPad.text = "0" + textNumPad.text
                }

                if (!acceptableInput) {  // check validator
                    textNumPad.text = textNumPad.text.slice(0,-1); // remove bad input
                } else {
                }

            }

        } // textNumPad
        Button {
            id: buttonKeyClear
//            x: 109
//            y: -227
//            width: ScreenUnits.numPadButtonSize
//            height: ScreenUnits.numPadButtonSize
            Layout.preferredWidth: ScreenUnits.numPadButtonSize
            Layout.preferredHeight: ScreenUnits.numPadButtonSize
            text: qsTr("CLR")
            onClicked: {
                clearnumpad()
            }
            style: ButtonStyle {

                label: Component {
                    Text {
                        renderType: Text.NativeRendering
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        font.family: "Helvetica"
                        font.pixelSize: ScreenUnits.numPadButtonTextHeight
                        text: control.text
                    }
                }
            }
        } // buttonKeyClear

        // Row 2
        FramNumPadButton {
            id: buttonKey7
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            text: qsTr("7")
        } // buttonKey7
        FramNumPadButton {
            id: buttonKey8
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            text: qsTr("8")
        } // buttonKey8
        FramNumPadButton {
            id: buttonKey9
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            text: qsTr("9")
        } // buttonKey9
        Button {
            id: buttonKeyBkSp
            Layout.preferredWidth: ScreenUnits.numPadButtonSize
            Layout.preferredHeight: ScreenUnits.numPadButtonSize
            text: qsTr("\u2190")  // LEFT ARROW
            visible: true
            checkable: false
            onClicked: {
                backspacenumpad()
            }

            style: ButtonStyle {
                label: Component {
                    Text {
                        text: control.text
                        font.pixelSize: ScreenUnits.numPadButtonTextHeight
                        font.family: "Helvetica"
                        verticalAlignment: Text.AlignVCenter
                        renderType: Text.NativeRendering
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        } // buttonKeyBkSp

        // Row 3
        FramNumPadButton {
            id: buttonKey4
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            text: qsTr("4")
        } // buttonKey4
        FramNumPadButton {
            id: buttonKey5
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            text: qsTr("5")
        } // buttonKey5
        FramNumPadButton {
            id: buttonKey6
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            text: qsTr("6")
            Layout.columnSpan: buttonKeyMinus.visible ? 1: 2  // span 2 columns if minus key is hidden
        } // buttonKey6
        Button {
            id: buttonKeyMinus
            Layout.preferredWidth: ScreenUnits.numPadButtonSize
            Layout.preferredHeight: ScreenUnits.numPadButtonSize
            text: qsTr("-")
            visible: false
            checkable: false
            onClicked: {
                minusnumpad()
            }
            style: ButtonStyle {
                label: Component {
                    Text {
                        text: control.text
                        font.pixelSize: ScreenUnits.numPadButtonTextHeight
                        verticalAlignment: Text.AlignVCenter
                        font.family: "Helvetica"
                        renderType: Text.NativeRendering
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        } // buttonKeyMinus

        // Row 4
        FramNumPadButton {
            id: buttonKey1
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            text: qsTr("1")
        } // buttonKey1
        FramNumPadButton {
            id: buttonKey2
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            text: qsTr("2")
        } // buttonKey2
        FramNumPadButton {
            id: buttonKey3
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            text: qsTr("3")
        } // buttonKey3
        Button {
            id: buttonKeyPlus
            Layout.preferredWidth: ScreenUnits.numPadButtonSize
            Layout.preferredHeight: ScreenUnits.numPadButtonSize
            text: qsTr("+")
            visible: false
            checkable: false
            onClicked: {
                plusnumpad()
            }
            style: ButtonStyle {
                label: Component {
                    Text {
                        text: control.text
                        font.pixelSize: ScreenUnits.numPadButtonTextHeight
                        verticalAlignment: Text.AlignVCenter
                        font.family: "Helvetica"
                        renderType: Text.NativeRendering
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        } // buttonKeyPlus

        // Row 5 - Bottom
        FramNumPadButton {
            id: buttonKey0
            Layout.preferredWidth: buttonNoWeight.visible ? buttonKeyDecimal.width : 177
            Layout.preferredHeight: this.height
            Layout.columnSpan: buttonNoWeight.visible ? 1: 2
            text: qsTr("0")
        } // buttonKey0
        FramNumPadButton {
            id: buttonKeyDecimal
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            text: qsTr(".")
            visible: false
            onClicked: {
                decimalnumpad()
            }
        } // buttonKeyDecimal
        Label {
            id: lblDecimalPosition
            visible: true
        } // lblDecimalPosition
        Button {
            id: buttonNoCount
            Layout.preferredWidth: ScreenUnits.numPadButtonSize
            Layout.preferredHeight: ScreenUnits.numPadButtonSize
            text: qsTr("No\nCount")
            visible: false
            onClicked: {
                keyPad.noCountPressed();
            }
            style: ButtonStyle {

                label: Component {
                    Text {
                        renderType: Text.NativeRendering
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        font.family: "Helvetica"
                        font.pixelSize: ScreenUnits.numPadButtonTextHeight
                        text: control.text
                    }
                }
            }
        } // buttonNoCount
        Button {
            id: buttonNoWeight
            Layout.preferredWidth: ScreenUnits.numPadButtonSize
            Layout.preferredHeight: ScreenUnits.numPadButtonSize
            text: qsTr("No\nWeight")
            visible: false
            onClicked: {
                keyPad.noWeightPressed();
            }
            style: ButtonStyle {

                label: Component {
                    Text {
                        renderType: Text.NativeRendering
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        font.family: "Helvetica"
                        font.pixelSize: ScreenUnits.numPadButtonTextHeight
                        text: control.text
                    }
                }
            }
        } // buttonNoWeight
        Button {
            id: buttonKeyOK
            x: 110
            y: 137
            Layout.preferredWidth: ScreenUnits.numPadButtonSize
            Layout.preferredHeight: ScreenUnits.numPadButtonSize
            text: default_text
            property string default_text: "OK"
            checkable: false
            visible: true

            function adding_mode_ok() {
                adding_mode = false;
                var sr_val = parseFloat(stored_result);
                var add_val = parseFloat(textNumPad.text);
                setnumpadvalue(sr_val + add_val);
            }

            function subtracting_mode_ok() {
                subtracting_mode = false;
                var sr_val = parseFloat(stored_result);
                var sub_val = parseFloat(textNumPad.text);
                setnumpadvalue(sr_val - sub_val);
            }

            onClicked: {
                if (adding_mode) {
                    adding_mode_ok();
                    buttonKeyOK.setText(); // show OK instead of =
                } else if (subtracting_mode) {
                    subtracting_mode_ok();
                    buttonKeyOK.setText(); // show OK instead of =
                } else {
                    numpadok();
                }
            }
            function setText(ok_text) {
                if (ok_text)
                    text = ok_text;
                else
                    text = default_text;

            }

            style: ButtonStyle {

                label: Component {
                    Text {
                        renderType: Text.NativeRendering
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        font.family: "Helvetica"
                        font.pixelSize: ScreenUnits.numPadButtonTextHeight
                        text: control.text
                    }
                }
            }
        } // buttonKeyOK
    }

    states: [
        State {
            name: "weights"

            PropertyChanges {
                target: buttonKeyDecimal
                visible: true
            }
            PropertyChanges {
                target: lblDecimalPosition
                visible: false
            }

            PropertyChanges {
                target: buttonKeyPlus
                visible: true
            }

            PropertyChanges {
                target: buttonKeyMinus
                visible: true
            }

            PropertyChanges {
                target: rectangleNPBackground
                color: "transparent"
            }
        },
        State {
            name: "counts"

            PropertyChanges {
                target: buttonKeyDecimal
                visible: false
            }
            PropertyChanges {
                target: lblDecimalPosition
                visible: true
            }

            PropertyChanges {
                target: buttonKeyPlus
                visible: true
            }

            PropertyChanges {
                target: buttonKeyMinus
                visible: true
            }

            PropertyChanges {
                target: rectangleNPBackground
                color: "transparent"
            }

        },
        State {
            name: "popup_basic"

            PropertyChanges {
                target: buttonKeyDecimal
                visible: false
            }
            PropertyChanges {
                target: lblDecimalPosition
                visible: true
            }


            PropertyChanges {
                target: buttonKeyPlus
                visible: false
            }

            PropertyChanges {
                target: buttonKeyMinus
                visible: false
            }

            PropertyChanges {
                target: rectangleNPBackground
                color: "#a4a4a4"
            }

        },
        State {
            name: "popup_weights"
            PropertyChanges {
                target: buttonKeyDecimal
                visible: true
            }
            PropertyChanges {
                target: lblDecimalPosition
                visible: false
            }

            PropertyChanges {
                target: buttonKeyPlus
                visible: true
            }

            PropertyChanges {
                target: buttonKeyMinus
                visible: true
            }

            PropertyChanges {
                target: rectangleNPBackground
                x: -194
                y: -261
                width: 412
                height: 511
                color: "#a4a4a4"

            }
        }
    ]



}

