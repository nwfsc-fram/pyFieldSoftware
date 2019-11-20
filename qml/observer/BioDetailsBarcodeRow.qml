import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Controls.Styles 1.4

import "../common"

Row {
    property alias label: lblBCR.text
    property alias placeholderText: textBCR.placeholderText
    property alias text: textBCR.text

    signal changed

    Label {
        id: lblBCR
        text: ""
        width: svBioDetails.labelColWidth
        height: 80
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 25
    }
    TextField {
        id: textBCR
        width: svBioDetails.dataColWidth
        height: 80
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 25
        placeholderText: ""
        onFocusChanged: {
            if (focus && !framNumPadDetails.visible){
                framNumPadDetails.attachresult_tf(textBCR)
                framNumPadDetails.setnumpadhint(placeholderText)
                framNumPadDetails.setnumpadvalue(text)
                framNumPadDetails.setstate("popup_basic")
                framNumPadDetails.show(true)
            } else {
                if (framNumPadDetails.stored_result == 0) {
                    text = "";
                }

                framNumPadDetails.show(false)
            }
        }
        onTextChanged: {
            changed()
        }
    }
}
