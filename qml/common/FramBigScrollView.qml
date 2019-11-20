// FramBigScrollView: Scroll view that has large easily-clicked horizontal and vertical handles.

import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Controls.Styles 1.4

import "."

ScrollView {

    id: bigScrollView
    horizontalScrollBarPolicy: Qt.ScrollBarAsNeeded
    verticalScrollBarPolicy: Qt.ScrollBarAsNeeded

    property int handleWidth: 50
    property int handleHeight: 50

    property int pageScrollDistance: 100 // root.height + viewport.height - 100

    Component.onCompleted: {
        // This __verticalScrollBar hack divined from secrets in:
        // src/controls/Private/ScrollViewHelper.qml and ScrollBar.qml
        bigScrollView.__verticalScrollBar.singleStep = pageScrollDistance;
    }

    style: ScrollViewStyle {
        handle: Item {
            implicitWidth: handleWidth
            implicitHeight: handleHeight
            Rectangle {
                color: "gray"
                anchors.fill: parent
                anchors.topMargin: 6
                anchors.leftMargin: 4
                anchors.rightMargin: 4
                anchors.bottomMargin: 6
            }
        }
        decrementControl:  Rectangle {
            implicitWidth: handleWidth
            implicitHeight: handleWidth
            Rectangle {
                anchors.fill: parent
                anchors.topMargin: styleData.horizontal ? 0 : -1
                anchors.leftMargin:  styleData.horizontal ? -1 : 0
                anchors.bottomMargin: styleData.horizontal ? -1 : 0
                anchors.rightMargin: styleData.horizontal ? 0 : -1
                color: "lightgray"
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 1
                    color: "transparent"
                    border.color: "#44ffffff"
                }
                Label {
                    width: parent.width
                    height: parent.height
                    text: styleData.horizontal ? "\u21e0" : "\u21e1" // left / up arrow
                    font.pixelSize: 30
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }

                gradient: Gradient {
                    GradientStop {color: styleData.pressed ? "lightgray" : "white" ; position: 0}
                    GradientStop {color: styleData.pressed ? "lightgray" : "lightgray" ; position: 1}
                }
                border.color: "#aaa"

            }
        }

        incrementControl:  Rectangle {
            implicitWidth: handleWidth
            implicitHeight: handleWidth
            Rectangle {
                anchors.fill: parent
                anchors.topMargin: styleData.horizontal ? 0 : -1
                anchors.leftMargin:  styleData.horizontal ? -1 : 0
                anchors.bottomMargin: styleData.horizontal ? -1 : 0
                anchors.rightMargin: styleData.horizontal ? 0 : -1
                color: "lightgray"
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 1
                    color: "transparent"
                    border.color: "#44ffffff"
                }
                Label {
                    width: parent.width
                    height: parent.height
                    // The isn't a right black arrow in current font (2B95)
                    // https://en.wikipedia.org/wiki/Miscellaneous_Symbols_and_Arrows
                    // So, use dashed arrow instead
                    text: styleData.horizontal ? "\u21e2" : "\u21e3" // right/ down arrow
                    font.pixelSize: 30
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
                gradient: Gradient {
                    GradientStop {color: styleData.pressed ? "lightgray" : "white" ; position: 0}
                    GradientStop {color: styleData.pressed ? "lightgray" : "lightgray" ; position: 1}
                }
                border.color: "#aaa"
            }

        }

        scrollBarBackground: Rectangle {
            implicitWidth: handleWidth
            implicitHeight: handleHeight
        }
    }

}

