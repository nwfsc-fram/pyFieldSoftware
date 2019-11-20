import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Window 2.2

import "../common"

ApplicationWindow {
    id: main
    visible: true
    width: 1024
    height: 768

//    flags: Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint
//    property var test: App.Actions
/*
    property alias stackView: stackView
*/
    property alias txtBanner: txtBanner

    property int obsTripNum: 12345
    property string obsStartDate: "11/15/2015"
    property string obsVessel: "Noah's Ark"
    property string obsGearType: ""
    property string obsFisheryType: ""

    function maximizeWindow() {
        // Tablet rotated
        main.x = 0
        main.y = 0
        main.width = Screen.width
        main.height = Screen.height - toolBar.height
    }

    Screen.onPrimaryOrientationChanged: {
        maximizeWindow()
    }

    Component.onCompleted: {
//        maximizeWindow()
        visible = true;
        {
            console.log("Pixel density: " + Screen.logicalPixelDensity);
        }
    }

    Rectangle {
//        color: "#EEEEEE"
        color: "white"
        anchors.fill: parent
    }

    toolBar: BorderImage {
        id: toolBar
        border.bottom: 35
        width: parent.width
        height: 45


        Rectangle {
            id: backButton
            width: opacity ? 60 : 0
            anchors.left: parent.left
            anchors.leftMargin: 20
            opacity: stackView.depth > 1 ? 1 : 0
            anchors.verticalCenter: parent.verticalCenter
            antialiasing: true
            height: 40
            radius: 4
            color: backmouse.pressed ? "#222" : "transparent"
            Behavior on opacity { NumberAnimation{} }
            Image {
                anchors.verticalCenter: parent.verticalCenter
                source: "../../resources/images/navigation_previous_item_dark.png"
            }
            MouseArea {
                id: backmouse
                anchors.fill: parent
                anchors.margins: -10
                onClicked: stackView.pop()
            }
        }


        Text {
            id: txtBanner
            font.pixelSize: 22
            Behavior on x { NumberAnimation{ easing.type: Easing.OutCubic} }
            x: backButton.x + backButton.width + 20
            anchors.verticalCenter: parent.verticalCenter
            color: "black"
//            text: "Noah's Ark - Trip #123456 - Fixed Gear"
            text: "Temp Trip #" + obsTripNum + " - " + obsStartDate + " - " + obsVessel
        }
    }
/*
    ListModel {
        id: mainPageModel

        ListElement {
            title: "Trip Details"
            page: "TripDetailsScreen.qml"
        }
    }

    StackView {
        id: stackView
        anchors.fill: parent
        focus: true
        Keys.onReleased: if (event.key === Qt.Key_Back && stackView.depth > 1) {
                             stackView.pop();
                             event.accepted = true;
                         }

        initialItem: Item {
            width: parent.width
            height: parent.height
            ListView {
                anchors.rightMargin: 0
                anchors.bottomMargin: 0
                anchors.leftMargin: 0
                anchors.topMargin: 0
                model: mainPageModel
                anchors.fill: parent
                delegate: DaylightDelegate {
                    text: title
                    onClicked: stackView.push(Qt.resolvedUrl(page))
                }
            }
        }
    }
*/
    Rectangle {
        color: "#EEEEEE"
        anchors.bottom: parent.bottom
        width: parent.width
        height: 60
    }
    Row {
//        id: FramFooter
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        width: parent.width
        height: 50
        Label {
            x: 4
            text: qsTr("Exit")
            verticalAlignment: Text.AlignVCenter
            font.pointSize: 18
            width: 110

            MouseArea {
                id: editHaulDetails
                anchors.fill: parent
                anchors.margins: -10
                onClicked: Qt.quit()
            }
        }
    }
}
