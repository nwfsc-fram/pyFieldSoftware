import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2

import "../common"
import "."

Row {
    id: wpRow
    property real portionValue: 0.0
    property int bwidth: 60 //root.width / 4 / 3 // used by FramGroupButtonRowButton
    property int labelWidth: 150 // root.width / 2
    property bool allowZeroDenominator: false

    property TextField tfNumerator: numerator
    property TextField tfDenominator: denominator

    signal numerFocusChanged(bool focus)
    signal denomFocusChanged(bool focus)

    function set_n_d(numer, denom) {
        numerator.text = numer;
        denominator.text = denom;
        calcPortionValue();
    }

    function set_value(value) {
        var fractional = CommonUtil.get_fraction(value)
        numerator.text = fractional[0];
        denominator.text = fractional[1];
        calcPortionValue();
    }

    Label {
        id: wpLabel
        text: "Ratio"
        width: labelWidth
        height: 80
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 20
    }

    ExclusiveGroup {
        id: wpGroup
    }

    FramGroupButtonRowButton {
        id: bQuarter
        text: "\u00BC" // 1/4
        exclusiveGroup: wpGroup
        onClicked: {
            numerator.text = 1
            denominator.text = 4
            calcPortionValue();
        }
    }

    FramGroupButtonRowButton {
        id: bThird
        text: "\u2153" // 1/3
        exclusiveGroup: wpGroup
        onClicked: {
            numerator.text = 1
            denominator.text = 3
            calcPortionValue();
        }
    }

    FramGroupButtonRowButton {
        id: bHalf
        text: "\u00BD" // 1/2
        exclusiveGroup: wpGroup
        onClicked: {
            numerator.text = 1
            denominator.text = 2
            calcPortionValue();
        }
    }
    Label {
        // spacer
        text: ""
        font.pixelSize: 25
        width: 25
    }

    function updateRatioButtonCheckedState() {
        // If the numerator and denominator text fields are used to enter a ratio,
        // uncheck all quick ratio buttons unless ratio matches.
        bQuarter.checked = numerator.text == 1 && denominator.text == 4;
        bThird.checked = numerator.text == 1 && denominator.text == 3;
        bHalf.checked = numerator.text == 1 && denominator.text == 2;
    }

    function calcPortionValue() {
       if (numerator && denominator) {
            portionValue = parseFloat(numerator.text) / parseFloat(denominator.text);
            updateRatioButtonCheckedState();
       } else {
            portionValue = 1.0;
       }
//       console.debug("Weighted Portion now: " + portionValue)
    }


    TextField {
        id: numerator
        width: bwidth
        height: wpLabel.height
        font.pixelSize: 25
        text: ""
        horizontalAlignment: Text.horizontalCenter
        onFocusChanged: {
            numerFocusChanged(focus);
        }
        onTextChanged: {
            calcPortionValue();
        }
    }
    Label {
        text: "/"
        font.pixelSize: 25
        height: wpLabel.height
        verticalAlignment: Text.AlignVCenter

    }

    TextField {
        id: denominator
        width: bwidth
        height: wpLabel.height
        font.pixelSize: 25
        text: ""
        horizontalAlignment: Text.horizontalCenter
        onFocusChanged: {
            denomFocusChanged(focus);
        }
        onTextChanged: {
            if (!allowZeroDenominator && text == "0") {
                dlgZeroDenominator.open();
                text = "";
            }
            calcPortionValue();
        }
    }

    FramNoteDialog {
        id: dlgZeroDenominator
        message: "Denominator can't be zero."
    }
}
