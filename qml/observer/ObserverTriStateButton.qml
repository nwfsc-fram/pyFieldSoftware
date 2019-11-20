import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4
// Very similar to ObserverGroupButton ("OGB") with only change being support of a third state:
// Disabled (and checked is don't-care): thin gray border, black text on gray background. Same as OGB.
// Enabled and not checked: thin black border, black text on white background. This is the difference from OGB.
// Enabled and checked: thick black border, black text on white background. Same as OGB.
Button {
    Layout.preferredWidth: idEntry.default_width / 2
    Layout.preferredHeight: buttonLogin.height
    Layout.alignment: Qt.AlignCenter
    property int font_size: 20
    style: ButtonStyle {
        label: Text {
            id: textButton
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.family: "Helvetica"
            font.pixelSize: font_size
            color: "black"
            text: control.text
        }
        background: Rectangle {
            implicitWidth: 100
            implicitHeight: 25
            border.width: checked ? 4 : 1
            border.color: enabled ? "black" : "gray"    // In OGB, "enabled" is "checked"
            radius: 4
            color: enabled || control.pressed ? "white" : "lightgray"
        }
    }
    checkable: true
}
