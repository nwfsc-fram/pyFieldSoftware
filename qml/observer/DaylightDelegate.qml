import QtQuick 2.5

Item {
    id: root
    width: parent.width
    height: 88

    property alias text: textitem.text
    property alias nextarrow: rightArrow
    property bool is_enabled: true
    signal clicked

    Rectangle {
        anchors.fill: parent
        color: "#11ffffff"
        visible: mouse.pressed
    }

    Text {
        id: textitem
        color: is_enabled ? "black" : "lightgray"
        font.pixelSize: 32
        text: modelData
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: 30
    }

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 15
        height: 1
        color: "#222222"
    }

    Image {
        id: rightArrow
        anchors.right: parent.right
        anchors.rightMargin: 20
        anchors.verticalCenter: parent.verticalCenter
        source: Qt.resolvedUrl("/resources/images/navigation_next_item_dark.png")
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        onClicked: root.clicked()

    }
}
