import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.3
import ".."

Item {
    property string action: "length";
    property alias numPad: numPad;

    signal labelSet(string action, variant value, string uom, bool dbUpdate, variant actionSubType);
    signal advanceTab();

    FramNumPad {
        id: numPad
        x: parent.width/2 - 180
        y: 5
        state: qsTr("counts")
        onNumpadok: {
            labelSet(action, numPad.textNumPad.text, "cm", true, null);
            advanceTab();
        }
    } // numPad
}