import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

// ObserverSunlightButton: A large, high-contrast button.
// Large in order to allow easy use with a gloved hand.
// High contrast for use in direct sunlight conditions.
// Enabled: bold black text on white background.
// Disabled: black text on gray background.
Button {
    id: btnMaster
    width: 120
    height: 60

    property string grdTopColor: "white"
    property string grdBottomColor: "white"
    property string txtColor: "black"
    property string bgColor: "lightgray"
    property string highlightColor: "white"
    property int fontsize: 20

    property bool txtBold: false

    style: ButtonStyle {
        label: Text {
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.family: "Helvetica"
            font.pixelSize: fontsize
            color: txtColor
            font.bold: txtBold
            text: control.text
        }
        background: Rectangle {
            border.width: checked ? 4 : 1
            border.color: checked ? "black" : "gray"
            radius: 4
            color: enabled || checked  ? (control.pressed ? "#ddd" : highlightColor) : bgColor
        }
    }
}

