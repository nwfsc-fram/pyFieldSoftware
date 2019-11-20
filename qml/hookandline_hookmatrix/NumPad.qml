import QtQuick 2.7
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Window 2.2
import QtQuick.Extras 1.4
import QtQuick.Dialogs 1.2


import "." // For ScreenUnits

Item {
    id: keyPad
    width: 360
    height: 450
    property TextField result_tf  // TextField to set on return
//    property alias btnOk: buttonKeyOK
//    property alias textNumPad: textNumPad

    property string minutes;
    property string seconds;
    property alias tfMinutes: tfMinutes;
    property alias tfSeconds: tfSeconds;

    property variant activeTF: tfMinutes;

    property string stored_result: "" // For - and + key operation
    property bool adding_mode: false // For - and + key operation
    property bool subtracting_mode: false // For - and + key operation
    property bool limitToTwoDecimalPlaces: false // Set true if using FramNumPad to enter weights.

    property bool skip_button_mode: false // Show "Skip" instead of OK button when nothing entered

    Component.onCompleted: { setnumpadvalue(0); }

    signal show(bool show)
    onShow: {
        if (show) { // Select all when shown for easier re-entry
            textNumPad.selectAll();
        }

        if (!keyPad.visible) {
            keyPad.visible = show;            
        }
    }

    signal resultCaptured(string result);

    signal numpadok
    onNumpadok: {
        // "OK" Button pressed
        // NOTE: For non-popup modes, do nothing: the parent should handle onNumpadok
        stored_result = textNumPad.text;
//        result_tf.text = textNumPad.text;
        resultCaptured(stored_result);

        keyPad.close();

        if (state.indexOf("popup_") != -1) {
            // Popup mode: hide window and set target textfield
            keyPad.visible = false;
            result_tf.text = textNumPad.text;
            parent.resetfocus();
        }
    }

    signal noCountPressed  // pressed No Count button

    function show_no_count(show) { buttonNoCount.visible = show; }

    signal attachresult_tf(TextField tf)
    onAttachresult_tf: {
        // Hook up the text box for returning the result
        result_tf = tf
    }

    signal clearnumpad
    onClearnumpad: {

        tfMinutes.text = ""
        tfSeconds.text = ""
        tfMinutes.forceActiveFocus();
        activeTF = tfMinutes;

        setnumpadvalue(0);
        if (skip_button_mode) {
            textNumPad.text = ""


            setSkipButtonMode(true); // reset skip text
        }
    }

    signal backspacenumpad
    onBackspacenumpad: {
        var tfText = activeTF.text;
        if (tfText.length > 0) {
            tfText = tfText.slice(0, -1);
            activeTF.text = qsTr(tfText)
        } else if (tfText.length === 0) {
            if (activeTF === tfSeconds) {
                activeTF = tfMinutes;
                activeTF.forceActiveFocus();
                if (activeTF.text.length > 0)
                    activeTF.text = activeTF.text.slice(0, -1);
            }
        }

        var numtxt = textNumPad.text
        if(numtxt.length > 0) {
            numtxt = numtxt.slice(0, -1);
            textNumPad.text = qsTr(numtxt);
            if (skip_button_mode && textNumPad.text == "") {
                setSkipButtonMode(true); // reset skip text
            }
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
    onSetnumpadhint: { textNumPad.placeholderText = numpadhint; }

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

    Connections {
        target: buttonKey1
        onNumpadinput: catchNumpadInput(input_key);
    } // buttonKey1.onNumpadinput
    Connections {
        target: buttonKey2
        onNumpadinput: catchNumpadInput(input_key);
    } // buttonKey2.onNumpadinput
    Connections {
        target: buttonKey3
        onNumpadinput: catchNumpadInput(input_key);
    } // buttonKey3.onNumpadinput
    Connections {
        target: buttonKey4
        onNumpadinput: catchNumpadInput(input_key);
    } // buttonKey4.onNumpadinput
    Connections {
        target: buttonKey5
        onNumpadinput: catchNumpadInput(input_key);
    } // buttonKey5.onNumpadinput
    Connections {
        target: buttonKey6
        onNumpadinput: catchNumpadInput(input_key);
    } // buttonKey6.onNumpadinput
    Connections {
        target: buttonKey7
        onNumpadinput: catchNumpadInput(input_key);
    } // buttonKey7.onNumpadinput
    Connections {
        target: buttonKey8
        onNumpadinput: catchNumpadInput(input_key);
    } // buttonKey8.onNumpadinput
    Connections {
        target: buttonKey9
        onNumpadinput: catchNumpadInput(input_key);
    } // buttonKey9.onNumpadinput
    Connections {
        target: buttonKey0
        onNumpadinput: catchNumpadInput(input_key);
    } // buttonKey0.onNumpadinput
    Connections {
        target: buttonKeyDecimal
        onNumpadinput: catchNumpadInput(input_key);
    } // buttonKeyDecimal.onNumpadinput

//    signal numpadinput(string input_key)
//    onNumpadinput: {
    function catchNumpadInput(input_key) {
        activeTF.text = activeTF.text.replace(activeTF.selectedText, "");
        if (activeTF.text.length < 2) {

            if (activeTF.text.length === 0) {
                var inputInt = parseInt(input_key);
                if (inputInt < 6) activeTF.text += input_key;
            } else {
                activeTF.text += input_key;
            }
        }
        if ((activeTF === tfMinutes) & (activeTF.text.length === 2)) {
            activeTF = tfSeconds;
            activeTF.selectAll();
            activeTF.forceActiveFocus();
        }


        textNumPad.text = textNumPad.text.replace(textNumPad.selectedText, "")
        if (textNumPad.text.length >= 1 && textNumPad.text.substring(0, 1) == "0" &&
                textNumPad.text.substring(0,2) != "0.")
            textNumPad.text = textNumPad.text.substring(1,1) + input_key;  // parse out leading 0
        else
            textNumPad.text += input_key;

        if (skip_button_mode) {
            buttonKeyOK.setText()  // show OK again
        }

    }

    signal setstate(string set_state)
    onSetstate: {
        // Options: base state, weights, popup_basic, popup_weights
        state = set_state
    }

    function selectAll() { textNumPad.selectAll(); }

    function showDecimal(show) { buttonKeyDecimal.visible = show; }

    function setSkipButtonMode(skip_mode) {
        // Change text on OK button
        skip_button_mode = skip_mode
        if (skip_mode && textNumPad.text == "") {
            buttonKeyOK.setText("Skip");
        } else {
            buttonKeyOK.setText()  // show OK
        }
    }

    property int buttonSize: 85
    property int fontSize: 20

    state: qsTr("embedded")

    GridLayout {
        columns: 4
        rows: 5
        columnSpacing: 6
        rowSpacing: 6

        // Row 1 - Top
        TextField {
            id: textNumPad
            Layout.preferredWidth: 268
            Layout.preferredHeight: buttonSize
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
        RowLayout {
            id: rlTimes
            Layout.columnSpan: 3
            spacing: 6
            TextField {
                id: tfMinutes
                font.pixelSize: 30
                Layout.preferredWidth: buttonSize
                Layout.preferredHeight: buttonSize
                placeholderText: "MM"
                text: minutes;
                MouseArea {
                    anchors.fill: parent
                    onClicked:{
    //                    parent.color = "yellow";
                        parent.selectAll();
                        parent.forceActiveFocus();
    //                    parent.cursorPosition = 0;
                        activeTF = parent;
                    }
                }
            } // tfMinutes
            Label {
                id: lblColon
                text: qsTr(":")
                font.pixelSize: 30
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                Layout.preferredWidth: 10
                Layout.preferredHeight: 10
            } // lblColon
            TextField {
                id: tfSeconds
                font.pixelSize: 30
                Layout.preferredWidth: buttonSize
                Layout.preferredHeight: buttonSize
                placeholderText: "SS"
                text: seconds;
                MouseArea {
                    anchors.fill: parent
                    onClicked:{
                        parent.selectAll();
                        parent.forceActiveFocus();
                        activeTF = parent;
                    }
                }
            } // tfSeconds
        }
        Button {
            id: buttonKeyBkSp
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
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
                        font.pixelSize: fontSize
                        font.family: "Helvetica"
                        verticalAlignment: Text.AlignVCenter
                        renderType: Text.NativeRendering
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        } // buttonKeyBkSp

        // Row 2
        NumPadButton {
            id: buttonKey7
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
            text: qsTr("7")
        } // buttonKey7
        NumPadButton {
            id: buttonKey8
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
            text: qsTr("8")
        } // buttonKey8
        NumPadButton {
            id: buttonKey9
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
            text: qsTr("9")
        } // buttonKey9
        Button {
            id: buttonKeyClear
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
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
                        font.pixelSize: fontSize
                        text: control.text
                    }
                }
            }
        } // buttonKeyClear

        // Row 3
        NumPadButton {
            id: buttonKey4
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
            text: qsTr("4")
        } // buttonKey4
        NumPadButton {
            id: buttonKey5
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
            text: qsTr("5")
        } // buttonKey5
        NumPadButton {
            id: buttonKey6
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
            text: qsTr("6")
            Layout.columnSpan: buttonKeyMinus.visible ? 1: 2  // span 2 columns if minus key is hidden
        } // buttonKey6
        Button {
            id: buttonKeyMinus
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
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
                        font.pixelSize: fontSize
                        verticalAlignment: Text.AlignVCenter
                        font.family: "Helvetica"
                        renderType: Text.NativeRendering
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        } // buttonKeyMinus

        // Row 4
        NumPadButton {
            id: buttonKey1
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
            text: qsTr("1")
        } // buttonKey1
        NumPadButton {
            id: buttonKey2
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
            text: qsTr("2")
        } // buttonKey2
        NumPadButton {
            id: buttonKey3
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
            text: qsTr("3")
        } // buttonKey3
        Label { id: lblSpacer2} // lblSpacer2
        Button {
            id: buttonKeyPlus
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
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
                        font.pixelSize: fontSize
                        verticalAlignment: Text.AlignVCenter
                        font.family: "Helvetica"
                        renderType: Text.NativeRendering
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        } // buttonKeyPlus

        // Row 5 - Bottom
        NumPadButton {
            id: buttonKey0
            Layout.preferredWidth: 177
            Layout.preferredHeight: buttonSize
            Layout.columnSpan: 2
            text: qsTr("0")
        } // buttonKey0
        NumPadButton {
            id: buttonKeyDecimal
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
            text: qsTr(".")
            visible: false
            onClicked: {
                decimalnumpad()
            }
        } // buttonKeyDecimal
        Label { id: lblSpacer3} // lblSpacer3
        Label {
            id: lblDecimalPosition
            visible: true
        } // lblDecimalPosition
        Button {
            id: buttonNoCount
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
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
                        font.pixelSize: fontSize
                        text: control.text
                    }
                }
            }
        } // buttonNoCount
        Button {
            id: buttonKeyOK
            Layout.preferredWidth: buttonSize
            Layout.preferredHeight: buttonSize
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
                        font.pixelSize: fontSize
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
            } // buttonKeyDecimal
            PropertyChanges {
                target: lblDecimalPosition
                visible: false
            } // lblDecimalPosition
            PropertyChanges {
                target: buttonKeyPlus
                visible: true
            } // buttonKeyPlus
            PropertyChanges {
                target: buttonKeyMinus
                visible: true
            } // buttonKeyMinus
        }, // weights
        State {
            name: "counts"
            PropertyChanges {
                target: buttonKeyDecimal
                visible: false
            } // buttonKeyDecimal
            PropertyChanges {
                target: lblDecimalPosition
                visible: true
            } // lblDecimalPosition
            PropertyChanges {
                target: buttonKeyPlus
                visible: true
            } // buttonKeyPlus
            PropertyChanges {
                target: buttonKeyMinus
                visible: true
            } // buttonKeyMinus
        }, // counts
        State {
            name: "time"
            PropertyChanges {
                target: buttonKeyDecimal
                visible: false
            } // buttonKeyDecimal
            PropertyChanges {
                target: lblDecimalPosition
                visible: true
            } // lblDecimalPosition
            PropertyChanges {
                target: buttonKeyPlus
                visible: false
            } // buttonKeyPlus
            PropertyChanges {
                target: buttonKeyMinus
                visible: false
            } // buttonKeyMinus
        }, // time
        State {
            name: "embedded"
            PropertyChanges {
                target: buttonKeyDecimal
                visible: false
            } // buttonKeyDecimal
            PropertyChanges {
                target: lblDecimalPosition
                visible: false
            } // lblDecimalPosition
            PropertyChanges {
                target: buttonKeyPlus
                visible: false
            } // buttonKeyPlus
            PropertyChanges {
                target: buttonKeyMinus
                visible: false
            } // buttonKeyMinus
            PropertyChanges {
                target: buttonKeyOK
                visible: false
            } // buttonKeyOK
            PropertyChanges {
                target: buttonNoCount
                visible: false
            } // buttonNoCount
            PropertyChanges {
                target: textNumPad
                visible: false
            }
        } // embedded
    ]

}

