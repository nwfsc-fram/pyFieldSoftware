// Covers the 4 primary data entry views: Catch Categories, Species, Weights, Biospecimens
import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import "."

TabView {
    id: tvFram
    property var tabsAlignment: Qt.AlignRight

    style: TabViewStyle {
        id: tabstyle
        frameOverlap: 1
        function tab_text_color(styleData) {
            // If disabled, make it look gray
            if (styleData.enabled === false) {
                return "darkgray";
            } else {
                return styleData.selected ? "white" : "black";
            }
        }
        function tab_bg_color(styleData) {
            return styleData.selected ? "gray" : "lightgray"
        }

        tabsAlignment: tvFram.tabsAlignment

        frame: Rectangle {
            color: "transparent"
            border.color: "transparent"
        }

        tab: Rectangle {
            color: tab_bg_color(styleData)
            border.color:  "black"
            implicitWidth: Math.max(text.width + 20, 80)
            implicitHeight: 50
            radius: 2

            Text {
                id: text
                anchors.centerIn: parent
                text: styleData.title
                color: tab_text_color(styleData) // styleData.selected ? "white" : "black"
                font.pixelSize: 20
                font.italic: styleData.enabled ? false : true
                font.bold: styleData.selected
            }
        }
    }
}
