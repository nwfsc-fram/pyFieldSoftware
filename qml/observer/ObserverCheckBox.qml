import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

CheckBox {
    id: cb
    property int checkbox_size: 40
    property int font_size: 20
    style: CheckBoxStyle {
        spacing: 10
        indicator: Rectangle {
                implicitWidth: checkbox_size
                implicitHeight: checkbox_size
                radius: 3
                border.color: control.activeFocus ? "darkblue" : "gray"
                border.width: 1
                Label {
                    text: "\u2713"  // unicode check
                    font.pixelSize: font_size
                    opacity: control.checkedState === Qt.Checked ? control.enabled ? 1 : 0.5 : 0
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: 1
                    Behavior on opacity {NumberAnimation {duration: 80}}
                }
        }
        label: Text {
            font.pixelSize: font_size
            text: cb.text
        }
    }
}
