import QtQuick 2.7
import QtCharts 2.1
import QtQuick.Controls 1.5
import QtQuick.Layouts 1.1

Item {
    id: waypoint

    property string name: ""
    property real posX: -5
    property real w: 3
    property real h: 50
    property variant colorMap: {"Start Haul": "navy", "Set Doors": "purple", "Doors Fully Out": "yellow", "Begin Tow": "green",
                            "Start Haulback": "black", "Net Off Bottom": "red", "Doors At Surface": "brown", "End Of Haul": "orange"}

    Rectangle {
        id: rec
        x: posX
        height: h
        width: w
//        border.color: "steelblue"
//        border.width: 1
        color: colorMap[name] ? colorMap[name] : "navy";
        opacity: 0.3
        visible: true

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onEntered: {
                settings.statusBarMessage = name + ', x: ' + mouseX + ', y: ' + mouseY;
            }
            onExited: {
                settings.statusBarMessage = "";
            }
        }
    }
}