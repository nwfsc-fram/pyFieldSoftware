import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Window 2.2
import QtQuick.Extras 1.4

import "."

Item {
    id: keyPad
    property TextField result_tf  // TextField to set on return
    property alias btnOk: buttonKeyOK
    property alias textNumPad: textNumPad

    property string stored_result: "" // For - and + key operation
    property bool adding_mode: false // For - and + key operation
    property bool subtracting_mode: false // For - and + key operation
    property bool limitToTwoDecimalPlaces: false // Set true if using pad to enter weights.

    property bool skip_button_mode: false // Show "Skip" instead of OK button when nothing entered
    property bool leading_zero_mode: false // Allow leading zeros to be entered (instead of being stripped)

    property bool direct_connect: false // show text area if not "direct connected"    
    property bool duplicate_connect: false // show text area and duplicate
    property TextField connect_tf: textNumPad
    property bool decimalKeyMode: false // Show decimal button
    property int buttonKey0ColumnSpan: 2

    property bool time_mode: false // Show : button
    property bool entering_hour: true  // depends on time_mode

    property var cached_key_input: null  // User enters value, cache it while record is created, then re-enter

    property bool enable_audio: false

    anchors.fill: parent
    anchors.margins: 20

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

    signal attachresult_tf(TextField tf)
    onAttachresult_tf: {
        // Hook up the text box for returning the result
        result_tf = tf
    }

    signal directConnectTf(TextField tf)
    onDirectConnectTf: {
        // Hook up the text box for returning the result
        direct_connect = true;
        connect_tf = tf;
        textNumPad.text = tf.text; // set any existing text
        textNumPad.selectAll();
    }

    signal directConnectWithTf(TextField tf)
    onDirectConnectWithTf: {
        // Hook up the text box for returning the result - show text field
        duplicate_connect = true;
        connect_tf = tf;
        textNumPad.text = tf.text; // set any existing text
    }

    signal clearnumpad
    onClearnumpad: {
        setnumpadvalue(0);
        textNumPad.cursorPosition = 0;
        if (connect_tf && (direct_connect || duplicate_connect)) {
            connect_tf.text = "";
        }
        if (time_mode) {
            textNumPad.text = "";
        }
        if (skip_button_mode) {

            textNumPad.text = "";
            setSkipButtonMode(true); // reset skip text
        }
    }

    signal backspacenumpad
    onBackspacenumpad: {
        var numtxt = textNumPad.text
        if(numtxt.length > 0) {
            numtxt = numtxt.slice(0, -1);
            textNumPad.text = qsTr(numtxt);
            if (direct_connect || duplicate_connect) {
                connect_tf.text = qsTr(numtxt);
            }

            if (skip_button_mode && textNumPad.text == "") {
                setSkipButtonMode(true); // reset skip text
            }
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
        if (enable_audio) {
            soundPlayer.play_sound("click", false)
        }
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
        if (enable_audio) {
            soundPlayer.play_sound("click", false)
        }

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
        if (connect_tf && (direct_connect || duplicate_connect)) {
            connect_tf.text = floatval;
        }

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
        if (!leading_zero_mode && textNumPad.text.length >= 1 && textNumPad.text.substring(0, 1) == "0" &&
                textNumPad.text.substring(0,2) != "0.")
            textNumPad.text = textNumPad.text.substring(1,1) + input_key;  // parse out leading 0
        else if (time_mode) {
            // fix CLR button for time_mode - allow only 1 leading zero
            if (input_key != "0") {
                textNumPad.insert(textNumPad.cursorPosition, input_key);
            } else if (textNumPad.text.length == 0 || textNumPad.text.substring(0, 1) !== "0") {
                    textNumPad.text += input_key;
            } else {
                textNumPad.text = "00";
            }
        }
        else {
            textNumPad.insert(textNumPad.cursorPosition, input_key);
        }

        if (direct_connect || duplicate_connect) {
            if (connect_tf) {
                connect_tf.text = textNumPad.text;
                connect_tf.cursorPosition = textNumPad.cursorPosition;                
            }
        }

        if (skip_button_mode) {
            buttonKeyOK.setText()  // show OK again
        }

        if (enable_audio) {
            soundPlayer.play_sound("numpadInput", false)
        }
    }

    signal setstate(string set_state)
    onSetstate: {
        // Options: base state, counts, weights, popup_basic, popup_weights
        state = set_state
    }

    function cache_input(input) {
        cached_key_input = input;
    }

    function enter_cached_input() {
        // for "Delayed" entry after row creation.
        if (cached_key_input) {
            numpadinput(cached_key_input);
            cached_key_input = null;
        }
    }

    function selectAll() {
        textNumPad.selectAll();
    }

    function showDecimal(show) {
        decimalKeyMode = show;
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

    onDecimalKeyModeChanged: {
        buttonKey0ColumnSpan = decimalKeyMode ? 1 : 2;
    }

    MouseArea {
        anchors.fill: parent
    }

    GridLayout {
        id: gridKeys
        anchors.fill: parent
        columns: 4
        columnSpacing: 4
        rowSpacing: 4
        property int buttonWidth: parent.width / 4 - 5
        property int buttonHeight: parent.height / 7

        Keys.onReturnPressed: {
            numpadok();
        }

        Keys.onEnterPressed: {

            numpadok();
        }

        // Row 1 - Top
        TextField {
            id: textNumPad
            implicitWidth: parent.width
            implicitHeight: gridKeys.buttonHeight
            font.pixelSize: ScreenUnits.numPadButtonTextHeight
            horizontalAlignment: Text.AlignRight
            placeholderText: qsTr("")
            Layout.columnSpan: 4
            visible: !direct_connect
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
        }

        Button {
            id: buttonKeyClear
            Layout.preferredWidth: gridKeys.buttonWidth
            Layout.preferredHeight: gridKeys.buttonHeight
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

        Button {
            id: buttonKeyBkSp
            Layout.preferredWidth: gridKeys.buttonWidth
            Layout.preferredHeight: gridKeys.buttonHeight
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
        Rectangle { // spacer
            color: "transparent"
            Layout.preferredWidth: gridKeys.buttonWidth
            Layout.preferredHeight: gridKeys.buttonHeight
            Layout.columnSpan: 2
        }

        FramScalingNumPadButton {
            id: buttonKey7            
            text: qsTr("7")
        } // buttonKey7
        FramScalingNumPadButton {
            id: buttonKey8
            text: qsTr("8")
        } // buttonKey8
        FramScalingNumPadButton {
            id: buttonKey9
            text: qsTr("9")
        } // buttonKey9

        Button {
            id: buttonKeyMinus
            Layout.preferredWidth: gridKeys.buttonWidth
            Layout.preferredHeight: gridKeys.buttonHeight
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
        Rectangle { // spacer
            color: "transparent"
            Layout.preferredWidth: gridKeys.buttonWidth
            Layout.preferredHeight: gridKeys.buttonHeight
            visible: !buttonKeyMinus.visible
        }

        FramScalingNumPadButton {
            id: buttonKey4
            text: qsTr("4")
        } // buttonKey4
        FramScalingNumPadButton {
            id: buttonKey5
            text: qsTr("5")
        } // buttonKey5
        FramScalingNumPadButton {
            id: buttonKey6
            text: qsTr("6")
//            Layout.columnSpan: buttonKeyMinus.visible ? 1: 2  // span 2 columns if minus key is hidden
        } // buttonKey6

        Button {
            id: buttonKeyPlus
            Layout.preferredWidth: gridKeys.buttonWidth
            Layout.preferredHeight: gridKeys.buttonHeight
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
        Rectangle { // spacer
            color: "transparent"
            Layout.preferredWidth: gridKeys.buttonWidth
            Layout.preferredHeight: gridKeys.buttonHeight
            visible: !buttonKeyPlus.visible
        }


        // Row 4
        FramScalingNumPadButton {
            id: buttonKey1
            text: qsTr("1")
        } // buttonKey1
        FramScalingNumPadButton {
            id: buttonKey2
            text: qsTr("2")
        } // buttonKey2
        FramScalingNumPadButton {
            id: buttonKey3
            text: qsTr("3")
            // TODO: Think about presence of +/- mode.
            Layout.columnSpan: 2
        } // buttonKey3


        // Row 5 - Bottom
        FramScalingNumPadButton {
            id: buttonKey0
            Layout.columnSpan: buttonKey0ColumnSpan
            text: qsTr("0")
        } // buttonKey0
        FramScalingNumPadButton {
            id: buttonKeyDecimal
            text: qsTr(".")
            visible: decimalKeyMode
            onClicked: {
                decimalnumpad()
            }
        } // buttonKeyDecimal
        Button {
            id: buttonKeyOK
            x: 110
            y: 137
            Layout.preferredWidth: gridKeys.buttonWidth
            Layout.preferredHeight: gridKeys.buttonHeight
            text: time_mode ? (entering_hour ? ":" : default_text) : default_text
            property string default_text: "OK"
            checkable: false
            visible: (!time_mode || (time_mode && entering_hour))

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
                target: buttonKeyPlus
                visible: true
            }

            PropertyChanges {
                target: buttonKeyMinus
                visible: true
            }
        },
        State {
            name: "counts"

            PropertyChanges {
                target: buttonKeyDecimal
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

        },
        State {
            name: "weights_ok"

            PropertyChanges {
                target: buttonKeyDecimal
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
                target: buttonKeyOK
                visible: true
            }

        },
        State {
            name: "counts_ok"

            PropertyChanges {
                target: buttonKeyDecimal
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
                target: buttonKeyOK
                visible: true
            }

        },
        State { // The same as "counts", but adding a synonym
                // for the benefit of screens (e.g. BioSLWScreen) that use this numpad state
                // to distinguish using this numpad for length values vis-a-vis weight values.
            name: "integer_lengths"

            PropertyChanges {
                target: buttonKeyDecimal
                visible: false  // Whole integer values only
            }

            PropertyChanges {
                target: buttonKeyPlus
                visible: true
            }

            PropertyChanges {
                target: buttonKeyMinus
                visible: true
            }
        },
        State {
            name: "fractional_lengths"  // Currently exactly the same as weights, but adding this synonym state
                            // for the benefit of screens (e.g. BioSLWScreen) that use this state
                            // to distinguish using this numpad for integer lengths, fractional lengths, or weights.
                            // Here: Allow a float value (not just integer, as in "integer_lengths").

            PropertyChanges {
                target: buttonKeyDecimal
                visible: true   // Allow float value
            }

            PropertyChanges {
                target: buttonKeyPlus
                visible: true
            }

            PropertyChanges {
                target: buttonKeyMinus
                visible: true
            }
        },
        State {
            name: "popup_basic"

            PropertyChanges {
                target: buttonKeyDecimal
                visible: false
            }

            PropertyChanges {
                target: buttonKeyPlus
                visible: false
            }

            PropertyChanges {
                target: buttonKeyMinus
                visible: false
            }

        },
        State {
            name: "popup_weights"
            PropertyChanges {
                target: buttonKeyDecimal
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

        }
    ]



}

