import QtQuick 2.7
import QtCharts 2.1
import QtQuick.Controls 1.5
import QtQuick.Layouts 1.1

ChartView {
    id: chartView
    antialiasing: true
    animationOptions: ChartView.NoAnimation
//    animationOptions: ChartView.AllAnimations
    theme: ChartView.ChartThemeQt
    backgroundRoundness: 0
    property bool openGL: true
    property bool openGLSupported: true
    property string title: ""

    signal zoomedIn(int x, int y, int width, int height);
    signal panning(int panX);
    signal hovering(variant chart, int x, int y);

    property int xScaleZoom: 0
    property int yScaleZoom: 0
//    property bool panEnabled: true

    margins.top: 0
    margins.bottom: 0
    margins.right: 0
    margins.left: 10

    legend.visible: false
    legend.alignment: Qt.AlignRight
//    legend.borderColor: "blue"
//    legend.width: parent.width * 0.2

    plotAreaColor: "azure"

    // Waypoints
    Rectangle {
        id: recStartHaul
        height: parent.height
        border.color: "purple"
        border.width: 1
        color: "purple"
        opacity: 0.3
        visible: false
    } // recStartHaul
    Rectangle {
        id: recSetDoors
        height: parent.height
        border.color: "steelblue"
        border.width: 1
        color: "steelblue"
        opacity: 0.3
        visible: true
    } // recSetDoors
    Rectangle {
        id: recDoorsFullyOut
        height: parent.height
        border.color: "steelblue"
        border.width: 1
        color: "steelblue"
        opacity: 0.3
        visible: true
    } // recDoorsFullyOut
    Rectangle {
        id: recBeginTow
        height: parent.height
        border.color: "green"
        border.width: 1
        color: "green"
        opacity: 0.3
        visible: true
    } // recBeginTow
    Rectangle {
        id: recStartHaulback
        height: parent.height
        border.color: "steelblue"
        border.width: 1
        color: "steelblue"
        opacity: 0.3
        visible: false
    } // recStartHaulback
    Rectangle {
        id: recNetOffBottom
        height: parent.height
        border.color: "steelblue"
        border.width: 1
        color: "steelblue"
        opacity: 0.3
        visible: false
    } // recNetOffBottom
    Rectangle {
        id: recDoorsAtSurface
        height: parent.height
        border.color: "steelblue"
        border.width: 1
        color: "steelblue"
        opacity: 0.3
        visible: false
    } // recDoorsAtSurface
    Rectangle {
        id: recEndOfHaul
        x: 50
        y: parent.y
        height: parent.height
        width: 3
        border.color: "steelblue"
        border.width: 1
        color: "steelblue"
        opacity: 0.3
        visible: false
    } // recEndOfHaul

    Text {
        id: txtTitle
        anchors.verticalCenter: parent.verticalCenter
        horizontalAlignment: TextInput.AlignHCenter
        text: title;
        transform:  Rotation { origin.x: 0; origin.y: 0; angle: 270;} Translate { y: parent.width }
    }
    Rectangle{
        id: recZoom
        border.color: "steelblue"
        border.width: 1
        color: "steelblue"
        opacity: 0.3
        visible: false
        transform: Scale { origin.x: 0; origin.y: 0; xScale: xScaleZoom; yScale: yScaleZoom}
    } // recZoom
    Rectangle{
        id: recMeasureTime
        border.color: "steelblue"
        border.width: 1
        color: "steelblue"
        opacity: 0.3
        visible: false
        transform: Scale { origin.x: 0; origin.y: 0; xScale: xScaleZoom; yScale: yScaleZoom}
    } // recMeasureTime
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        property bool isPanning: false
        property int previousX: 0
        cursorShape: isPanning ? Qt.OpenHandCursor : Qt.ArrowCursor
        onWheel: {
//            if (wheel.modifiers & Qt.ControlModifier) {
            var min = timeSeries.xMin;
            var max = timeSeries.xMax;
            var range = max - min;

            // Testing to center around the mouseX location when zooming in
//            var chartWidth = chartView.plotArea.width;
//            var xPercent = mouseX / chartWidth;
//            var xValue = xPercent * range;
//            var zoomType = (wheel.angleDelta.y < 0) ? "Zoom Out" : "Zoom In"
//            console.info(zoomType, min, " > ", max, " > ", xValue);

            // Zoom Out
            if (wheel.angleDelta.y < 0) {
                range *= 2;
                min.setMilliseconds(min.getMilliseconds() - range/4);
                max.setMilliseconds(max.getMilliseconds() + range/4);
//                min.setMilliseconds(min.getMilliseconds() + xValue - range/4);
//                max.setMilliseconds(min.getMilliseconds() + xValue + range/4);

//                chartView.zoomOut()
            // Zoom In
            } else {

                range /= 2;
                min.setMilliseconds(min.getMilliseconds() + range/2);
                max.setMilliseconds(max.getMilliseconds() - range/2);
//                min.setMilliseconds(min.getMilliseconds() + xValue + range/2);
//                max.setMilliseconds(min.getMilliseconds() + xValue - range/2);
//                chartView.zoomIn()
            }
//            console.info("\tnew min / max: " + min + " > " + max);

            timeSeries.xMin = min
            timeSeries.xMax = max;
        }
        onPressed: {
//            if (panEnabled) {
            if (timeSeries.toolMode == "pan") {
                previousX = mouseX;
                isPanning = true;
            } else if (timeSeries.toolMode == "measureTime" ) {

                recMeasureTime.x = mouseX;
                recMeasureTime.y = mouseY;
                recMeasureTime.visible = true;
            }


        }
        onReleased: {
//            if (panEnabled) {
            if (timeSeries.toolMode == "pan") {
                isPanning = false;
            } else if (timeSeries.toolMode == "measureTime") {
                var x = (mouseX >= recMeasureTime.x) ? recMeasureTime.x : mouseX
                var y = (mouseY >= recMeasureTime.y) ? recMeasureTime.y : mouseY
    //            chartView.zoomIn(Qt.rect(x, y, recZoom.width, recZoom.height));
                recMeasureTime.visible = false;
//                chartView.zoomedIn(x, y, recZoom.width, recZoom.height);
            }
        }
        onMouseXChanged: {
            settings.statusBarMessage = "x: " + mouseX + ", y: " + mouseY;

            chartView.hovering(chartView, mouseX, mouseY);
            timeSeries.onHover(chartView, mouseX, mouseY);
//            timeSeries.setTime(mapToValue((mouse.x, mouse.y), series(0)));

//            if (panEnabled) {
            if (timeSeries.toolMode == "pan") {
                if (isPanning) {
                    chartView.panning(previousX - mouseX);
                    previousX = mouseX;
                }

            } else if (timeSeries.toolMode == "measureTime") {
                if (mouseX - recMeasureTime.x >= 0) {
                    xScaleZoom = 1;
                    recMeasureTime.width = mouseX - recMeasureTime.x;
                } else {
                    xScaleZoom = -1;
                    recMeasureTime.width = recMeasureTime.x - mouseX;
                }
            }
        }
        onMouseYChanged: {
//            if (!panEnabled) {
            if (timeSeries.toolMode == "measureTime") {
                if (mouseY - recMeasureTime.y >= 0) {
                    yScaleZoom = 1;
                    recMeasureTime.height = mouseY - recMeasureTime.y;
                } else {
                    yScaleZoom = -1;
                    recMeasureTime.height = recMeasureTime.y - mouseY;
                }
            }
        }
    }


}

//RowLayout {
//    id: rllChart
//    spacing: 0
//    property alias chartView: chartView
//
//
//    Rectangle {
//        id: legend
//        color: "lightgray"
//
//        property int seriesCount: 0
//        property variant seriesNames: []
//        property variant seriesColors: []
//        signal entered(string seriesName)
//        signal exited(string seriesName)
//        signal selected(string seriesName)
//
//        Component {
//            id: legendDelegate
//            Rectangle {
//                id: rect
//                property string name: seriesNames[index]
//                property color markerColor: seriesColors[index]
//                gradient: buttonGradient
//                border.color: "#A0A0A0"
//                border.width: 1
//                radius: 4
//
//                implicitWidth: label.implicitWidth + marker.implicitWidth + 30
//                implicitHeight: label.implicitHeight + marker.implicitHeight + 10
//
//                Row {
//                    id: row
//                    spacing: 5
//                    anchors.verticalCenter: parent.verticalCenter
//                    anchors.left: parent.left
//                    anchors.leftMargin: 5
//                    Rectangle {
//                        id: marker
//                        anchors.verticalCenter: parent.verticalCenter
//                        color: markerColor
//                        opacity: 0.3
//                        radius: 4
//                        width: 12
//                        height: 10
//                    }
//                    Text {
//                        id: label
//                        anchors.verticalCenter: parent.verticalCenter
//                        anchors.verticalCenterOffset: -1
//                        text: name
//                    }
//                }
//
//                MouseArea {
//                    id: mouseArea
//                    anchors.fill: parent
//                    hoverEnabled: true
//                    onEntered: {
//                        rect.gradient = buttonGradientHovered;
//                        legend.entered(label.text);
//                    }
//                    onExited: {
//                        rect.gradient = buttonGradient;
//                        legend.exited(label.text);
//                        marker.opacity = 0.3;
//                        marker.height = 10;
//                    }
//                    onClicked: {
//                        legend.selected(label.text);
//                        marker.opacity = 1.0;
//                        marker.height = 12;
//                    }
//                }
//            }
//        }
//        Column {
//            id: legendRow
//            anchors.centerIn: parent
//            spacing: 10
//
//            Repeater {
//                id: legendRepeater
//                model: seriesCount
//                delegate: legendDelegate
//            }
//        }
//    }
//
//}
