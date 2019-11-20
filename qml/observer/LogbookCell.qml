import QtQuick 2.6

Rectangle {
    property string text: ""
    property int font_size: 15

    border.width: 1
    border.color: "darkgray"
    color: "#EEEEEE" // almost white

    implicitWidth: 70
    implicitHeight: 70

    signal clicked

    Text {
        anchors.fill: parent
        text: parent.text
        font.pixelSize: parent.font_size
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    MouseArea {
        anchors.fill: parent
        onClicked: parent.clicked()
    }
}
