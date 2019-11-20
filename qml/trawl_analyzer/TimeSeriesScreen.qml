import QtQuick 2.7
//import QtQuick.Controls 2.0
import QtQuick.Controls 1.5
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0
import QtCharts 2.1
import QtQml 2.2
import QtQuick.Extras 1.4
//import MatplotlibFigure 1.0

import MplBackend 1.0

import "../common"

Item {
    id: itmTimeSeries
    objectName: "timeSeriesScreen"

    property bool openGL: true
    property bool openGLSupported: true
    property int tscHeight: 150

    property variant waypointObjects: {"Start Haul": null, "Set Doors": null, "Doors Fully Out": null, "Begin Tow": null,
                            "Start Haulback": null, "Net Off Bottom": null, "Doors At Surface": null, "End Of Haul": null}

    Component.onCompleted: {

        itmTimeSeries.state = "pan";


        // Create the waypoints
        var component;
        var waypointObject;
//        for (var wp in waypointObjects) {
//            component = Qt.createComponent("Waypoint.qml");
//            if ((wp == "Begin Tow") || (wp == "Start Haulback")) {
//                waypointObject = component.createObject(itmTimeSeries, {"x": -5, "y": 0});
//                waypointObject.h = mainWindow.height;
//            } else {
//                waypointObject = component.createObject(tscWaypoints, {"x": -5, "y": 0});
//                waypointObject.h = tscWaypoints.height;
//            }
//            waypointObject.name = wp;
//            waypointObjects[wp] = waypointObject;
//        }


    }

    Connections {
        target: timeSeries
        onErrorEncountered: errorEncountered(msg);
    } // timeSeries.onErrorEncountered
    Connections {
        target: timeSeries
        onCommentsPerformanceRetrieved: commentsPerformanceRetrieved(comments, performance_field, minimum_time_met_field,
                                            performance_qaqc, minimum_time_met_qaqc);
    } // timeSeries.onCommentsPerformanceRetrieved
    Connections {
        target: timeSeries
        onImpactFactorsRetrieved: impactFactorsRetrieved(impact_factors)
    } // timeSeries.onImpactFactorsRetrieved
    Connections {
        target: timeSeries
        onHaulDetailsRetrieved: haulDetailsRetrieved(haul_date, haul_start, haul_end, fpc)
    } // timeSeries.onHaulDetailsRetrieved
    Connections {
        target: timeSeries
        onCommentAdded: commentAdded(comment)
    } // timeSeries.onCommentAdded
    Connections {
        target: timeSeries
        onTowPerformanceAdjusted: towPerformanceAdjusted(status, tow_performance, minimum_time_met)
    } // timeSeries.onTowPerformanceAdjusted
    Connections {
        target: timeSeries
        onTimeSeriesThreadCompleted: timeSeriesLoadingCompleted(status, msg)
    } // timeSeries.onTimeSeriesThreadCompleted
    Connections {
        target: timeSeries
        onTimeSeriesCleared: clearTimeSeries(reading_type)
    } // timeSeries.onClearTimeSeries
    Connections {
        target: timeSeries
        onAllTimeSeriesCleared: clearAllTimeSeries()
    } // timeSeries.onAllTimeSeriesCleared
    Connections {
        target: timeSeries
        onShowInvalidsChanged: showInvalidsChanged()
    } // timeSeries.onShowInvalidsChanged
    Connections {
        target: timeSeries
        onMouseReleased: mouseReleased()
    } // timeSeries.onMouseReleased
    Connections {
        target: timeSeries.mplMap
        onDistanceCalculated: distanceCalculated(technique, distance, speed);
    } // timeSeries.mplMap.distanceCalculated
    Connections {
        target: timeSeries.mplMap
        onGearLinePlotted: gearLinePlotted(technique, created)
    } // timeSeries.mplMap.onGearLinePlotted
    Connections {
        target: timeSeries.mplMap
        onDistanceFishedCompleted: distanceFishedCompleted()
    } // timeSeries.mplMap.distanceFishedCompleted
    Connections {
        target: timeSeries.mplMap
        onTracklineSaved: tracklineSaved(technique)
    } // timeSeries.mplMap.tracklineSaved
    Connections {
        target: timeSeries
        onHaulLoading: haulLoading()
    } // timeSeries.onHaulLoading
    Connections {
        target: timeSeries
        onHaulLoadingFinished: haulLoadingFinished(technique, distance, speed)
    } // timeSeries.onHaulLoadingFinished
    Connections {
        target: timeSeries
        onMeansCalculated: meansCalculated(mean_type, legend_name, mean);
    } // timeSeries.onMeansCalculated
    Connections {
        target: timeSeries
        onMeansSaved: meansSaved(mean_types);
    } // timeSeries.onMeansSaved
    Connections {
        target: timeSeries
        onMeansLoaded: meansLoaded(mean_type, mean);
    } // timeSeries.onMeansLoaded
    Connections {
        target: timeSeries
        onMeansSeriesChanged: meansSeriesChanged(mean_type, series);
    } // timeSeries.onMeansSeriesChanged
    Connections {
        target: timeSeries
        onClearDistancesFished: clearDistancesFished();
    } // timeSeries.onClearDistancesFished

    function clearDistancesFished() {
        for (var i in tvDistanceFished.model.items) {
            tvDistanceFished.model.setProperty(i, "distance", "");
            tvDistanceFished.model.setProperty(i, "speed", "");
            tvDistanceFished.model.setProperty(i, "saved", "");
        }
    }

    function meansSeriesChanged(mean_type, series) {
        var index = tvCalculateMeans.model.get_item_index("meanType", mean_type);

//        console.info('meansSeriesChanged: ' + mean_type + ', series = ' + series + ', index = ' + index);

        if (index != -1) {
            tvCalculateMeans.model.setProperty(index, "timeSeries", series);
        }

    }

    function meansLoaded(mean_type, mean) {
        var index = tvCalculateMeans.model.get_item_index("meanType", mean_type);

//        console.info('meansLoaded: ' + mean_type + ', mean = ' + mean + ', index = ' + index);

        if (index != -1) {
            tvCalculateMeans.model.setProperty(index, "mean", mean);
            tvCalculateMeans.model.setProperty(index, "saved", "Yes");
        }
    }

    function meansSaved(mean_types) {
        var index;
        for (var i in mean_types) {
            index = tvCalculateMeans.model.get_item_index("meanType", mean_types[i]);
            tvCalculateMeans.model.setProperty(index, "saved", "Yes");
        }

        btnSaveMeans.enabled = true;
    }

    function meansCalculated(mean_type, legend_name, mean) {
//        console.info('mean_type: ' + mean_type + ', legend: ' + legend_name + ', mean: ' + mean);
        var index = tvCalculateMeans.model.get_item_index("meanType", mean_type);
        tvCalculateMeans.model.setProperty(index, "mean", mean);
        tvCalculateMeans.model.setProperty(index, "saved", "");
    }

    function clearMeansCalculated() {
        var model = tvCalculateMeans.model;
        for (var i in model.items) {
            model.setProperty(i, "mean", "");
            model.setProperty(i, "saved", "");
        }
    }

    function haulLoadingFinished (technique, distance, speed) {

        var index;

        console.info('technique: ' + technique);
//        if ((technique == null) || (technique == "")) {
        for (var i=0; i < tvDistanceFished.model.count; i++) {
            tvDistanceFished.model.setProperty(i, "saved", "");
            tvDistanceFished.model.setProperty(i, "distance", "");
            tvDistanceFished.model.setProperty(i, "speed", "");
        }
//            return;
//        }
        // Clear the existing save record
//        var index = tvDistanceFished.model.get_item_index("saved", "Saved");
//        if (index >= 0) {
//            tvDistanceFished.model.setProperty(index, "saved", "");
//        }

        index = tvDistanceFished.model.get_item_index("technique", technique);
        if (index >= 0) {
            tvDistanceFished.model.setProperty(index, "saved", "Saved");
            tvDistanceFished.model.setProperty(index, "distance", distance);
            tvDistanceFished.model.setProperty(index, "speed", speed);
        }

        toggleGearButtons(false);
        gearLinePlotted("Gear " + technique, false);
    }

    function toggleGearButtons(value) {
        console.info('toggling gear buttons: ' + value);
        btnGearCatenary.checked = value;
        btnGearVesselTrig.checked = value;
        btnGearGcdTrig.checked = value;
        btnGearItiRB.checked = value;
        btnGearItiIigll.checked = value;
        btnGearItiRBTrig.checked = value;

    }

    function enableVisiblityButtons(value) {
        console.info('enabling visibility: ' + value);
        btnVessel.enabled = value;
        btnGearRangeBearing.enabled = value;
        btnGearIti.enabled = value;

        btnGearCatenary.enabled = value;
        btnGearVesselTrig.enabled = value;
        btnGearGcdTrig.enabled = value;
        btnGearItiRB.enabled = value;
        btnGearItiIigll.enabled = value;
        btnGearItiRBTrig.enabled = value;

    }

    function haulLoading() {
        clearMeansCalculated();

        btnCalculateDistanceFished.enabled = false;
        btnSaveGearLine.enabled = false;
        btnReviewData.enabled = false;
        btnRunCalculation.enabled = false;
        btnChangeMeansTimeSeries.enabled = false;
        btnSaveMeans.enabled = false;

        enableVisiblityButtons(false);
    }

    function tracklineSaved(technique) {

        // Clear the existing save record
        var index = tvDistanceFished.model.get_item_index("saved", "Saved");
        if (index >= 0) {
            tvDistanceFished.model.setProperty(index, "saved", "");
        }

        index = tvDistanceFished.model.get_item_index("technique", technique);
        if (index >= 0) {
            tvDistanceFished.model.setProperty(index, "saved", "Saved");
        }
    }

    function distanceFishedCompleted() {
        btnCalculateDistanceFished.enabled = true;
        btnSaveGearLine.enabled = true;
        dlgOkay.message = "Distance Fished Calculations Completed";
        dlgOkay.open();
    }

    function gearLinePlotted(technique, created) {
        console.info("Gear Line Plotted Technique: " + technique + ', created: ' + created);
        if (created) {
            switch (technique) {
                case "Gear Catenary":
                    btnGearCatenary.checked = true;
                    break;
            }
        } else {
            switch (technique) {
                case "Gear Catenary":
                    btnGearCatenary.checked = true;
                    break;
                case "Gear Vessel + Trig":
                    btnGearVesselTrig.checked = true;
                    break;
                case "Gear GCD + Trig":
                    btnGearGcdTrig.checked = true;
                    break;
                case "Gear ITI R/B":
                    btnGearItiRB.checked = true;
                    break;
                case "Gear ITI $IIGLL":
                    btnGearItiIigll.checked = true;
                    break;
                case "Gear ITI R/B + Trig":
                    btnGearItiRBTrig.checked = true;
                    break;
            }
        }
    }

    function distanceCalculated(technique, distance, speed) {
//        console.info(technique + ", " + distance + ", " + speed);
        var index = tvDistanceFished.model.get_item_index("technique", technique);
        if (index >= 0) {
            tvDistanceFished.model.setProperty(index, "distance", distance);
            tvDistanceFished.model.setProperty(index, "speed", speed);
        }
    }

    function uncheckGearlineButtons () {
        btnGearCatenary.checked = false;
        btnGearVesselTrig.checked = false;
        btnGearGcdTrig.checked = false;
        btnGearItiRB.checked = false;
        btnGearItiIigll.checked = false;
        btnGearItiRBTrig.checked = false;

//        btnGearRangeExtCatenaryTrig.checked = false;
//        btnGearRangeExtTrig.checked = false;
    }

    function mouseReleased() {
        // Function to catch when the mouse is released from graphing manipulations
        if (timeSeries.toolMode == "addWaypoint") {
            btnBeginTow.checked = false;
            btnNetOffBottom.checked = false;
            btnDoorsAtSurface.checked = false;
        }
    }

    function errorEncountered(msg) {
        dlgOkay.message = msg;
        dlgOkay.open();
    }

    function towPerformanceAdjusted(status, tow_performance, minimum_time_met) {
        if (status == "both") {
            lblPerformanceValueQAQC.text = (tow_performance) ? "Satisfactory" : "Unsatisfactory"
            lblMinimumTimeMetValueQAQC.text = minimum_time_met ? "Yes" : "No"
        } else if (status == "tow_performance") {
            lblPerformanceValueQAQC.text = (tow_performance) ? "Satisfactory" : "Unsatisfactory"
        } else if (status == "minimum_time_met") {
            lblMinimumTimeMetValueQAQC.text = minimum_time_met ? "Yes" : "No"
        }
    }

    function commentAdded(comment) {
        lblComments.text = comment + lblComments.text;
    }

    function haulDetailsRetrieved(haul_date, haul_start, haul_end, fpc) {
        lblHaulDate.text = haul_date;
        lblHaulStartTime.text = haul_start;
        lblHaulEndTime.text = haul_end;
        lblFpc.text = fpc;
    }

    function impactFactorsRetrieved(impact_factors) {
        lblImpactFactorsValues.text = impact_factors;
    }

    function commentsPerformanceRetrieved(comments, performance_field, minimum_time_met_field, performance_qaqc, minimum_time_met_qaqc) {
        lblPerformanceValueField.text = performance_field;
        lblMinimumTimeMetValueField.text = minimum_time_met_field;
        lblPerformanceValueQAQC.text = performance_qaqc;
        lblMinimumTimeMetValueQAQC.text = minimum_time_met_qaqc;
        lblComments.text = comments;
    }

    function timeSeriesLoadingCompleted(status, msg) {

        btnCalculateDistanceFished.enabled = true;
        btnReviewData.enabled = true;
//        btnUndoInvalids.enabled = true;
        btnRunCalculation.enabled = true;
        btnChangeMeansTimeSeries.enabled = true;
        btnSaveMeans.enabled = true;

        btnVessel.checked = true;
        btnGearIti.checked = true;
        btnGearRangeBearing.checked = true;

        enableVisiblityButtons(true);

        return;

        var max_right_width = -1;
        var max_left_width = -1;
        var chart;
        for (var key in timeSeriesCharts) {
            chart = timeSeriesCharts[key]["chart"];
            max_left_width = chart.plotArea.x > max_left_width ? chart.plotArea.x : max_left_width
            max_right_width = chart.legend.width > max_right_width ? chart.legend.width : max_right_width

            console.info('key: ' + key + ', chart.plotArea.x: ' + chart.plotArea.x + ', leftMarg: ' + chart.margins.left + ', maxLeft: ' + max_left_width);
        }

        max_left_width = tscWaypoints.plotArea.x > max_left_width ? tscWaypoints.plotArea.x : max_left_width;
        max_right_width = tscWaypoints.legend.width > max_right_width ? tscWaypoints.legend.width : max_right_width

        console.info('key: Waypoints, chart.plotArea.x: ' + tscWaypoints.plotArea.x + ', leftMarg: ' + chart.margins.left + ', maxLeft: ' + max_left_width);

        console.info('#########################  AFTER ADJUSTMENTS  #########################');

        for (var key in timeSeriesCharts) {
            chart = timeSeriesCharts[key]["chart"];
//            if (chart.plotArea.x < max_left_width)
//               chart.margins.left = max_left_width - chart.plotArea.x;
            if (chart.legend.width < max_right_width)
                chart.margins.right = max_right_width - chart.legend.width;

            console.info('key: ' + key + ', chart.plotArea.x: ' + chart.plotArea.x + ', leftMarg: ' + chart.margins.left + ', plotArea.width: ' + chart.plotArea.width);

        }
//        if (tscWaypoints.plotArea.x < max_left_width)
//            tscWaypoints.margins.left = max_left_width - tscWaypoints.plotArea.x;
        if (tscWaypoints.legend.width < max_right_width)
            tscWaypoints.margins.right = max_right_width - tscWaypoints.legend.width;

        console.info('key: Waypoints, chart.plotArea.x: ' + tscWaypoints.plotArea.x + ', leftMarg: ' + chart.margins.left + ', plotArea.width: ' + tscWaypoints.plotArea.width);

    }

    function showInvalidsChanged() {}

    function zoomAllCharts(x, y, width, height) {

//        for (var tsc in timeSeriesCharts) {
//            console.info(timeSeriesCharts[tsc].axisY.max, timeSeriesCharts[tsc].axisY.min)
//            y = Math.round((timeSeriesCharts[tsc].axisY.max - timeSeriesCharts[tsc].axisY.min)/4);
//            height = Math.round((timeSeriesCharts[tsc].max - timeSeriesCharts[tsc].min)/2);
//            timeSeriesCharts[tsc].zoomIn(Qt.rect(x, y, width, height));
//        }
//        console.info(tscWaypoints.axisY(lsWaypoints).max);
        var xTotal = tscWaypoints.axisX(lsWaypoints).max - tscWaypoints.axisX(lsWaypoints).min
//        height = (tscWaypoints.axisY(lsWaypoints).max - tscWaypoints.axisY(lsWaypoints).min)/2;


        console.info(width, xTotal);
        tscWaypoints.zoom(xTotal/width);
        tscDepth.zoom(xTotal/width)
//        tscWaypoints.zoomIn(Qt.rect(x, y, xTotal/width, y));
//        tscWaypoints.zoomIn(Qt.rect(x, y, width, height));
    }

    function panAllCharts(panX) {

//        var max = tscWaypoints.axisX(lsWaypoints).max;
//        var min = tscWaypoints.axisX(lsWaypoints).min
        var max = timeSeries.xMax;
        var min = timeSeries.xMin
        var unitsTotal = max - min;
        var chartWidth = tscWaypoints.plotArea.width;
//        var diff = Math.round((panX/chartWidth) * unitsTotal)
        var diff = (panX/chartWidth) * unitsTotal
//        console.info(min, max, " >>> ", diff, unitsTotal, " >>> ", panX, chartWidth);
        max.setMilliseconds(max.getMilliseconds() + diff);
        min.setMilliseconds(min.getMilliseconds() + diff);
        timeSeries.xMin = min
        timeSeries.xMax = max;

//        console.info(timeSeries.xMin, timeSeries.xMax);

    }

    function loadWaypoints(waypoints) {

        return;

        tscWaypoints.removeAllSeries();
        var lsWaypoints  = tscWaypoints.createSeries(ChartView.SeriesTypeScatter, "Waypoints",
            waypointsAxisX, waypointsAxisY);
//        asWaypoints = tscWaypoints.createSeries(ChartView.AreaSeries, "Waypoints",
//            waypointsAxisY, waypointsAxisY);

//        maxLegendWidth = tscWaypoints.legend.width > maxLegendWidth ? tscWaypoints.legend.width : maxLegendWidth

        for (var wp in waypoints) {

            lsWaypoints.append(waypoints[wp], 1);
            lsWaypoints.useOpenGL = openGL;

//            if (!(wp in waypointObjects)) {
//                var component;
//                var waypointObject;
//                component = Qt.createComponent("Waypoint.qml");
//                if ((wp == "Begin Tow") || (wp == "Start Haulback")) {
//                    waypointObject = component.createObject(itmTimeSeries, {"x": 50, "y": 0});
//                } else {
//                    waypointObject = component.createObject(tscWaypoints, {"x": 50, "y": 0});
////                    wpObject.h = tscWaypoints.height;
//                }
//                waypointObject.h = parent.height;
//                waypointObject.name = wp;
//                waypointsObjects[wp] = waypointObject;
//            }
            if (waypointObjects[wp] != null) {
                var timeWidth = timeSeries.xMax - timeSeries.xMin;
                var pixelWidth = tscWaypoints.plotArea.width;
                var factor = pixelWidth / timeWidth;
                var deltaX = waypoints[wp] - timeSeries.xMin;
                waypointObjects[wp].posX = tscWaypoints.plotArea.x + factor * deltaX;

                console.info(wp + ' > x: ' + tscWaypoints.plotArea.x + ', posX: ' + waypointObjects[wp].posX + ', factor: ' + factor + ', deltaX: ' + deltaX);
                console.info('\tdeltaX: ' + deltaX);
                console.info('\twp: ' + waypoints[wp] + ', xMin: ' + timeSeries.xMin);

//                console.info("name: " + waypoint.name);
            }
        }
    }

    function createAxis(type, min, max, chart) {
        var qml = "import QtQuick 2.0; import QtCharts 2.1; " + type + " { min: "
                                  + min + "; max: " + max + "; }"
        return Qt.createQmlObject(qml, chart);
    }

    function clearAllTimeSeries() {
        btnCalculateDistanceFished.enabled = false;
        btnSaveGearLine.enabled = false;
        return;

        for (var key in timeSeriesCharts) {
            clearTimeSeries(key);
        }
        tscWaypoints.removeAllSeries();
    }

    function clearTimeSeries(reading_type) {

        return;

        // Function called that first clears times series from the reading_type chart
        if (reading_type in timeSeriesCharts) {
            timeSeriesCharts[reading_type]["chart"].removeAllSeries();
            timeSeriesCharts[reading_type]["yAxis"].max = -1;
        }
    }

    function loadTimeSeries(timeSeriesDict) {

        return;

        /* Function to load the data queried from the data and put it into a ChartView.  The reading type represents
            the type of data, i.e. Depth for instance, and so indicates to which time series chart to apply it
        */

        if (!timeSeries.displaySeries) return;

        if (timeSeriesDict["reading_type"] in timeSeriesCharts) {

            var reading_type = timeSeriesDict["reading_type"];
            var legend_name = timeSeriesDict["legend_name"];
            var points = timeSeriesDict["points"];
            var max_value = timeSeriesDict["max_value"];
            var min_value = timeSeriesDict["min_value"];

//            if (max_value > timeSeriesCharts[reading_type]["yAxisRight"].max)
//                timeSeriesCharts[reading_type]["yAxisRight"].max = max_value;
            var ts = timeSeriesCharts[reading_type];
            if (max_value > ts["yAxis"].max) ts["yAxis"].max = max_value;
            var series = ts["chart"].createSeries(ChartView.SeriesTypeLine, legend_name, ts["xAxis"], ts["yAxis"]);
//            series.axisYRight = ts["yAxisRight"];
//            ts["chart"].margins.right = 200;

            // WORKS
//            var series = timeSeriesCharts[reading_type]["chart"].createSeries(ChartView.SeriesTypeLine,
//                legend_name, timeSeriesCharts[reading_type]["xAxis"], timeSeriesCharts[reading_type]["yAxis"]);



//            timeSeriesCharts[reading_type]["chart"].margins.right = xRight - timeSeriesCharts[reading_type]["chart"].legend.width
//            timeSeriesCharts[reading_type]["chart"].margins.left = xLeft - timeSeriesCharts[reading_type]["chart"].plotArea.x

            series.useOpenGL = openGL;
            series.pointsVisible = true;
            series.pointLabelsVisible = false;
            series.name = legend_name;


            /* Reference - Connecting a signal with parameters dynamically
                https://gist.github.com/jdowner/4697780
            */
            series.hovered.connect(function(point, state) {
                console.log("onHovered: " + point.x + ", " + point.y);
                settings.statusBarMessage = point.x.toFixed(2) + ", " + point.y.toFixed(2);
            })

            // WORKS - Handle adding of the points in python
            timeSeries.addPoints(series, points)
            return;

            // WORKS
            for (var point in points) {
                series.append(points[point][0], points[point][1]);
            }
        }
    }

    function formatMeanValue(row, value) {
        if ((value == null) || (value == "")) {
            return "";
        }
        var model = tvCalculateMeans.model;
        if ((model.get(row).meanType == "Latitude") || (model.get(row).meanType == "Longitude")) {
            return parseFloat(value).toFixed(6);
        } else {
            return parseFloat(value).toFixed(2);
        }
    }

    SplitView {
        id: svTimeSeries
        anchors.fill: parent
        orientation: Qt.Horizontal
        onWidthChanged: {
            clControlPanel.width = btnMap.checked ? width * 0.5 : width * 0.2;
        }
        MplFigureCanvas {
            id: mplView
            objectName: "mplFigure"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 100
            Layout.minimumHeight: 100
        } // mplView
        ColumnLayout {
            id: clControlPanel
            GridLayout {
                id: glTools
                Layout.leftMargin: 10
                Layout.rightMargin: 10
                rows: 2
                columns: 8
                ExclusiveGroup { id: egTools }
                ToolButton {
                    id: btnPan
                    iconSource: "qrc:/resources/images/pan.png"
                    enabled: settings.loggedInStatus
                    tooltip: "Pan / Zoom Horizontal"
                    checked: true
                    checkable: true
                    exclusiveGroup: egTools
//                    ButtonGroup.group: bgTools
                    onClicked: {
                        timeSeries.toolMode = "pan";
//                        itmTimeSeries.state = "pan";
                    }
                } // btnPan
                ToolButton {
                    id: btnZoomVertical
                    iconSource: "qrc:/resources/images/pan_vertical.png"
                    enabled: settings.loggedInStatus
                    tooltip: "Pan / Zoom Vertical"
                    checked: false
                    checkable: true
//                    ButtonGroup.group: bgTools
                    exclusiveGroup: egTools
                    onClicked: {
                        timeSeries.toolMode = "zoomVertical";
//                        itmTimeSeries.state = "pan";
                    }
                } // btnZoomVertical
                ToolButton {
                    id: btnMeasureTime
                    iconSource: "qrc:/resources/images/clock.png"
                    tooltip: "Measure Time Span"
                    checked: false
                    checkable: true
//                    ButtonGroup.group: bgTools
                    exclusiveGroup: egTools
                    onClicked: {
                        timeSeries.toolMode = "measureTime";
                        itmTimeSeries.state = "measureTime";
                    }
                } // btnMeasureTime
                ToolButton {
                    id: btnAddWaypoint
                    iconSource: "qrc:/resources/images/waypoint.png"
                    tooltip: "Add Waypoint"
                    checked: false
                    checkable: true
//                    ButtonGroup.group: bgTools
                    exclusiveGroup: egTools
                    onClicked: {
                        timeSeries.toolMode = "addWaypoint";
                        itmTimeSeries.state = "addWaypoint";
                    }
                } // btnAddWaypoint
                ToolButton {
                    id: btnShiftTimeSeries
                    iconSource: "qrc:/resources/images/shift.png"
                    tooltip: "Shift Time Series"
                    checked: false
                    checkable: true
//                    ButtonGroup.group: bgTools
                    exclusiveGroup: egTools
                    onClicked: { timeSeries.toolMode = "shiftTimeSeries"; itmTimeSeries.state = "shiftTimeSeries"; }
                } // btnShiftTimeSeries
//                ToolButton {
//                    id: btnDataSplitter
//                    iconSource: "qrc:/resources/images/splitter.png"
//                    tooltip: "Data Splitter"
//                    checked: false
//                    checkable: true
////                    ButtonGroup.group: bgTools
//                    exclusiveGroup: egTools
//                    onClicked: { timeSeries.toolMode = "splitSeries"; itmTimeSeries.state = "splitSeries"; }
//                } // btnDataSplitter
                ToolButton {
                    id: btnCalculateMeans
                    iconSource: "qrc:/resources/images/mean.png"
                    tooltip: "Calculate Means"
                    checked: false
                    checkable: true
//                    ButtonGroup.group: bgTools
                    exclusiveGroup: egTools
                    onClicked: { timeSeries.toolMode = "calculateMeans"; itmTimeSeries.state = "calculateMeans" }
                } // btnCalculateMeans
                ToolButton {
                    id: btnBadData
                    iconSource: "qrc:/resources/images/invalid_data.png"
                    tooltip: "Mark as Invalid"
                    checked: false
                    checkable: true
//                    ButtonGroup.group: bgTools
                    exclusiveGroup: egTools
                    onClicked: { timeSeries.toolMode = "invalidData"; itmTimeSeries.state = "invalidData" }
                } // btnBadData
                ToolButton {
                    id: btnDistanceFished
                    iconSource: "qrc:/resources/images/distance.png"
                    tooltip: "Calculate Distance Fished"
                    checked: false
                    checkable: true
//                    ButtonGroup.group: bgTools
                    exclusiveGroup: egTools
                    onClicked: {
                        timeSeries.toolMode = "distanceFished"
                        itmTimeSeries.state = "distanceFished"
                    }
                } // btnDistanceFished
                ToolButton {
                    id: btnToggleLegend
                    iconSource: "qrc:/resources/images/legend.png"
                    tooltip: "Toggle Legends"
                    checked: false
                    checkable: true
                    onClicked: { timeSeries.toggleLegends(checked) }
                } // btnToggleLegend
                ToolButton {
                    id: btnToggleInvalids
                    iconSource: "qrc:/resources/images/eye.png"
                    tooltip: "Toggle Invalid Data Points"
                    checked: false
                    checkable: true
                    onClicked: { timeSeries.showInvalids = checked }
                } // btnToggleInvalids
                ToolButton {
                    id: btnToggleMeans
                    iconSource: "qrc:/resources/images/calculator.png"
                    tooltip: "Toggle Mean Lines/Points"
                    checked: false
                    checkable: true
                    onClicked: { timeSeries.showMeans = checked }
                } // btnToggleMeans
                ToolButton {
                    id: btnMap
                    iconSource: "qrc:/resources/images/map.png"
                    tooltip: "Show Track Lines"
                    checked: false
                    checkable: true
                    onClicked: {
                        itmTimeSeries.state = btnAddWaypoint.checked ? "addWaypoint" : (checked ? "trackLines" : "nonTrackLines");
                        clControlPanel.width = checked ? clControlPanel.parent.width / 2 : clControlPanel.parent.width / 5;
                    }
                } // btnMap
            } // glTools
            Item { Layout.preferredHeight: 10 }
            GroupBox {
                id: grpActions
                Layout.leftMargin: 10
                Layout.rightMargin: 10
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                title: qsTr("Actions")

                RowLayout {
                    id: rlMeasureTime
                    y:10
                    Layout.fillWidth: true
                    enabled: false
                    visible: false
                    Label {
                        id: lblTimeSpan
                        text: qsTr("Time Span:")
                        font.weight: Font.Bold;
                    }
                    Item { Layout.preferredWidth: 5 }
                    Label {
                        id: lblTimeSpanValue
                        Layout.preferredWidth: 60
                        text: timeSeries.timeMeasured
//                            enabled: false
                    }
                    Button {
                        id: btnClearSpan
                        text: qsTr("Clear")
                        onClicked: { timeSeries.clearTimeMeasurement() }
                    }
                } // rlMeasureTime
                ColumnLayout {
                    id: clAddWaypoint
                    y:10
                    enabled: false
                    visible: false
                    spacing: 10
//                    ButtonGroup { id: bgBcs }
                    ExclusiveGroup { id: egBcs }
                    RowLayout {
                        id: rlBcsSignals
                        Label { text: qsTr("Signal"); font.weight: Font.Bold; Layout.preferredWidth: 60; }
                        Button {
                            id: btnBcsP;
                            text: qsTr("BCS-P");
                            Layout.preferredWidth: 50;
                            enabled: timeSeries.bcsPExists
                            checkable: true;
                            checked: true;
//                            ButtonGroup.group: bgBcs
                            exclusiveGroup: egBcs
                        } // btnBcsP
                        Button {
                            id: btnBcsS;
                            text: qsTr("BCS-S");
                            Layout.preferredWidth: 50;
                            enabled: timeSeries.bcsSExists
                            checkable: true;
                            checked: false;
//                            ButtonGroup.group: bgBcs
                            exclusiveGroup: egBcs
                        } // btnBcsS
                        Button {
                            id: btnBcsC;
                            text: qsTr("BCS-C");
                            Layout.preferredWidth: 50;
                            enabled: timeSeries.bcsCExists
                            checkable: true;
                            checked: false;
//                            ButtonGroup.group: bgBcs
                            exclusiveGroup: egBcs
                        } // btnBcsC
                        Label { Layout.preferredWidth: 40; }
                        Button {
                            id: btnCalcWaypoints;
                            text: qsTr("Calculate")
                            enabled: ((settings.haul != null) & ((btnBcsP.enabled) || (btnBcsS.enabled) || (btnBcsC.enabled))) ? true : false
                            onClicked: { timeSeries.autoCalculateWaypoints(egBcs.current.text); }
                        } // btnCalcWaypoints
                    } // rlBcsSignals
                    RowLayout {
                        id: rlWaypoints
//                        ButtonGroup { id: bgWaypoints }
                        ExclusiveGroup { id: egWaypoints }
                        Label { text: qsTr("Waypoint"); font.weight: Font.Bold; Layout.preferredWidth: 60;}
                        Button {
                            id: btnBeginTow
                            text: qsTr("Begin Tow")
                            checkable: true
                            checked: false
//                            ButtonGroup.group: bgWaypoints
                            exclusiveGroup: egWaypoints
                            enabled: (settings.haul != null) ? true : false
                            onClicked: { timeSeries.activeWaypointType = "Begin Tow"}
                        } // btnBeginTow
                        Button {
                            id: btnNetOffBottom
                            text: qsTr("Net Off Bottom")
                            checkable: true
                            checked: false
//                            ButtonGroup.group: bgWaypoints
                            exclusiveGroup: egWaypoints
                            enabled: (settings.haul != null) ? true : false
                            onClicked: { timeSeries.activeWaypointType = "Net Off Bottom"}
                        } // btnNetOffBottom
                        Button {
                            id: btnDoorsAtSurface
                            text: qsTr("Doors At Surface")
                            checkable: true
                            checked: false
//                            ButtonGroup.group: bgWaypoints
                            exclusiveGroup: egWaypoints
                            enabled: (settings.haul != null) ? true : false
                            onClicked: { timeSeries.activeWaypointType = "Doors At Surface"}
                        } // btnDoorsAtSurface
                        Button {
                            id: btnClear
                            text: qsTr("Clear Waypoint")
                            enabled: (settings.haul != null) ? true : false
                            onClicked: {
                                timeSeries.clearManualWaypoint(timeSeries.activeWaypointType);
                            }
                            Layout.preferredWidth: 22
                            Layout.preferredHeight: 22
                            style: ButtonStyle {
                                label: Item {
                                    Canvas {
                                        anchors.fill: parent
                                        onPaint: {
                                            var ctx = getContext("2d");
                                            ctx.lineWidth = 2;
                                            ctx.strokeStyle = Qt.rgba(0, 0, 0, 1);
                                            ctx.beginPath();
                                            ctx.moveTo(width/4, height/4);
                                            ctx.lineTo(3*width/4, 3*height/4);
                                            ctx.stroke();
                                            ctx.beginPath();
                                            ctx.moveTo(3*width/4, height/4);
                                            ctx.lineTo(width/4, 3*height/4);
                                            ctx.stroke();
                                        }
                                    }
                                }
                            }
                        } // btnClear
                    } // rlWaypoints
                } // clAddWaypoint
                Item {
                    id: itmDistanceFished
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    enabled: false
                    visible: false

                    GridLayout {
                        id: glDistanceFished
                        y: 5
                        rows: 3
                        columns: 2
                        columnSpacing: 10

                        // Row 1 - Span
                        Label {
                            text: qsTr("Span");
                            Layout.preferredWidth: 30
                            font.weight: Font.Bold;
                        } // Span
                        TextField {
                            id: tfSpan
                            inputMask: "99"
                            text: qsTr("5")
                            Layout.preferredWidth: 30
                        } // tfSpan

                        // Row 2 - Depth
                        Label {
                            text: qsTr("Depth");
                            Layout.preferredWidth: 30
                            font.weight: Font.Bold;
                        } // Depth
                        ComboBox {
                            id: cbDepth
                            Layout.preferredWidth: 100
                            model: ListModel {
                                id: cbDepthItems
                                ListElement { text: "SBE39"; value: "SBE39" }
                                ListElement { text: "ITI $IIDBS"; value: "$IIDBS" }
                                ListElement { text: "ITI @IITPT"; value: "@IITPT" }
                                ListElement { text: "PI44"; value: "PI44"}
/*
                                ListElement { text: "FCV1100 $SDDBT"; value: "(FCV1100) ($SDDBT)"}
                                ListElement { text: "FCV1100 $SDDBS"; value: "(FCV1100) ($SDDBS)"}
*/
                                ListElement { text: "Sounder $SDDBT"; value: "$SDDBT"}
                                ListElement { text: "Sounder $SDDBS"; value: "$SDDBS"}
                            }
                        } // cbDepth

                        // Row 3
                        Button {
                            id: btnCalculateDistanceFished
                            text: qsTr("Calculate")
                            enabled: false
                            onClicked: {
                                this.enabled = false;
                                btnSaveGearLine.enabled = false;
                                uncheckGearlineButtons();
                                timeSeries.calculateDistanceFished(parseInt(tfSpan.text), cbDepthItems.get(cbDepth.currentIndex).value);
                            }
                        } // btnCalculateDistanceFished

                    } // glDistanceFished
                    TableView {
                        id: tvDistanceFished
                        anchors.left: glDistanceFished.right
                        anchors.leftMargin: 20
                        width: 320
                        height: 80
                        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
                        model: timeSeries.mplMap.distanceFishedModel
                        TableViewColumn {
                            role: "technique"
                            title: "Technique"
                            width: 130
                        } // technique
                        TableViewColumn {
                            role: "distance"
                            title: "Dist (NM)"
                            width: 60
                            delegate: Text {
                                text: styleData.value ? parseFloat(styleData.value).toFixed(2) : ""
                                renderType: Text.NativeRendering
                            }
                        } // distance
                        TableViewColumn {
                            role: "speed"
                            title: "Pre Spd (kts)"
                            width: 70
                            delegate: Text {
                                text: styleData.value ? parseFloat(styleData.value).toFixed(2) : ""
                                renderType: Text.NativeRendering
                            }
                        } // speed
                        TableViewColumn {
                            role: "saved"
                            title: "Saved"
                            width: 40
                        } // saved
                    } // tvDistanceFished
                    Button {
                        id: btnSaveGearLine
                        anchors.left: tvDistanceFished.right
                        anchors.leftMargin: 10
                        Layout.preferredWidth: 30
                        enabled: false
                        text: qsTr("Save")
                        onClicked: {
                            var index = tvDistanceFished.currentRow;
                            if (index != -1) {
                                // Save the current trackline to the database, delete the old one
                                var technique = tvDistanceFished.model.get(index).technique;
                                timeSeries.mplMap.save_gearline_to_db(settings.haul, technique, true);
                            }
                        }

                    } // btnSaveGearLine

                } // itmDistanceFished
                Item {
                    id: itmCalculateMeans
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    enabled: false
                    visible: false

                    GridLayout {
                        id: glCalculateMeans
                        rows: 2
                        columns: 2
                        rowSpacing: 10
                        columnSpacing: 10
                        flow: GridLayout.TopToBottom
                        Label {
                            text: qsTr("Portion of Signal")
                            Layout.alignment: Qt.AlignHCenter
                            font.weight: Font.Bold;
                        } // Portion of Signal
                        GridLayout {
                            id: glRange
                            rowSpacing: 10
                            columnSpacing: 10
                            columns: 2
                            rows: 2
                            Label { text: qsTr("Bottom"); Layout.alignment: Qt.AlignHCenter; }
                            Label { text: qsTr("Top"); Layout.alignment: Qt.AlignHCenter; }
                            TextField { id: tfRangeBottom; text: qsTr("10"); inputMask: "99"; Layout.preferredWidth: 40;}
                            TextField { id: tfRangeTop; text: qsTr("90"); inputMask: "99"; Layout.preferredWidth: 40;}
                        } // glRange
                        Button {
                            id: btnRunCalculation
                            text: qsTr("Calculate")
                            enabled: false
                            onClicked: {
                                clearMeansCalculated();
                                var bottom = parseInt(tfRangeBottom.text);
                                var top = parseInt(tfRangeTop.text);
                                console.info('bottom: ' + bottom +', top: ' + top);
                                if (bottom < top) {
                                    timeSeries.calculate_means(tfRangeBottom.text, tfRangeTop.text);
                                } else {
                                    dlgOkay.message = "The portion of signal bottom must be less than the top";
                                    dlgOkay.open()
                                }
//                            parseFloat(styleData.value).toFixed(2) : ""
                            }
                        } // btnRunCalculation
                        Button {
                            id: btnChangeMeansTimeSeries
                            text: qsTr("Change Series")
                            enabled: false
                            onClicked: {
                                dlgChangeMeansTimeSeries.populate_combo_boxes(tvCalculateMeans.model.items);
                                dlgChangeMeansTimeSeries.open();
                            }
                        } // btnChangeMeansTimeSeries
                    } // glCalculateMeans
                    TableView {
                        id: tvCalculateMeans
                        anchors.left: glCalculateMeans.right
                        anchors.leftMargin: 20
                        width: 360
                        height: 80
                        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
                        model: timeSeries.meansModel
                        TableViewColumn {
                            role: "meanType"
                            title: "Mean Type"
                            width: 80
                        } // meanType
                        TableViewColumn {
                            role: "timeSeries"
                            title: "Time Series"
                            width: 160
//                            delegate: Item {
//                                ComboBox {
//                                    width: parent.width
//                                    anchors.verticalCenter: parent.verticalCenter
//                                    model: fpcMain.dropTypesModel
//                                }
//                            }
                        } // timeSeries
                        TableViewColumn {
                            role: "mean"
                            title: "Mean"
                            width: 60
                            delegate: Text {
                                text: formatMeanValue(styleData.row, styleData.value)
                                renderType: Text.NativeRendering
                            }
                        } // mean
                        TableViewColumn {
                            role: "saved"
                            title: "Saved"
                            width: 40
                        } // saved

                    } // tvCalculateMeans
                    Button {
                        id: btnSaveMeans
                        anchors.left: tvCalculateMeans.right
                        anchors.leftMargin: 10
                        Layout.preferredWidth: 30
                        enabled: false
                        text: qsTr("Save")
                        onClicked: {
                            enabled = false;
                            timeSeries.save_means();
//                            var index = tvCalculateMeans.currentRow;
//                            if (index != -1) {
                                // Save the current trackline to the database, delete the old one
//                                var technique = tvCalculateMeans.model.get(index).technique;
//                                timeSeries.mplMap.save_gearline_to_db(settings.haul, technique, true);
//                            }
                        }
                    } // btnSaveMeans

                } // itmCalculateMeans
                Item {
                    id: itmInvalidData
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    enabled: false
                    visible: false

                    GridLayout {
                        id: glInvalidData
                        y: 5
                        rows: 2
                        columns: 3
                        columnSpacing: 10
                        rowSpacing: 10
                        // Row 1 - Span
                        Label {
                            text: qsTr("Time Series")
                        }
                        ComboBox {
                            id: cbTimeSeries
                            Layout.preferredWidth: 240
                            model: timeSeries.timeSeriesModel
                        } // cbTimeSeries
                        Button {
                            id: btnReviewData
                            text: qsTr("Review Data")
                            enabled: false
                            onClicked: {
                                var time_series = cbTimeSeries.currentText;
                                if (time_series != "Select Time Series") {
                                    timeSeries.populate_data_points_model(time_series);
                                    dlgInvalidData.time_series = time_series;
                                    dlgInvalidData.open()
                                }
                            }
                        } // btnReviewData
//                        Button {
//                            id: btnUndoInvalids
//                            text: qsTr("Undo")
//                            enabled: false
//                            onClicked: {
//                            }
//                        } // btnUndoInvalids

                    }
                } // itmInvalidData
                Item {
                    id: itmShiftTimeSeries
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    enabled: false
                    visible: false

                    GridLayout {
                        id: glShiftTimeSeries
                        y: 5
                        rows: 2
                        columns: 3
                        columnSpacing: 10
                        rowSpacing: 10
                        // Row 1 - Span
                        Label {
                            text: qsTr("Time Series")
                        }
                        ComboBox {
                            id: cbTimeSeriesShift
                            Layout.preferredWidth: 240
                            model: timeSeries.timeSeriesModel
                            onCurrentIndexChanged: {
                                if (currentText == "Select Time Series") {
                                    timeSeries.activeTimeSeries = null;
                                } else {
                                    timeSeries.activeTimeSeries = currentText;
                                }
                            }
                        } // cbTimeSeriesShift
                    }
                } // itmShiftTimeSeries
            } // grpActions
            ColumnLayout {
                id: clPerformance
                Item { Layout.preferredHeight: 10 }
                GroupBox {
                    id: gbHaulDetails
                    Layout.leftMargin: 10
                    Layout.rightMargin: 10
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70
                    title: qsTr("Haul Details")
                    GridLayout {
                        id: glHaulDetails
                        x: 10
                        y: 10
                        Layout.leftMargin: 10
                        Layout.rightMargin: 10
                        Layout.fillWidth: true
                        columnSpacing: 20
                        rowSpacing: 5
                        rows: 2
                        columns: 4
                        Label { text: qsTr("Haul Date"); font.weight: Font.Bold; }
                        Label { text: qsTr("Start Time"); font.weight: Font.Bold; }
                        Label { text: qsTr("End Time"); font.weight: Font.Bold; }
                        Label { text: qsTr("FPC"); font.weight: Font.Bold; }
                        Label { id: lblHaulDate; text: qsTr("--/--/----") }
                        Label { id: lblHaulStartTime; text: qsTr("00:00:00") }
                        Label { id: lblHaulEndTime; text: qsTr("00:00:00") }
                        Label { id: lblFpc; text: qsTr("-") }
                    } // glHaulDetails
                } // gbHaulDetails
                Item { Layout.preferredHeight: 10 }
                GroupBox {
                    id: gbPerformance
                    Layout.leftMargin: 10
                    Layout.rightMargin: 10
                    Layout.fillWidth: true
                    Layout.preferredHeight: 140
                    title: qsTr("Performance")
                    GridLayout {
                        id: glPerformance
                        x: 10
                        y: 10
                        Layout.leftMargin: 10
                        Layout.rightMargin: 10
                        rows: 3
                        columns: 3
                        columnSpacing: 20
                        rowSpacing: 10
                        Button {
                            id: btnAdjustPerformance
                            text: qsTr("Adjust")
    //                            anchors.top: parent.top
    //                            anchors.topMargin: 10
    //                            anchors.right: parent.right
                            enabled: (settings.haul != null) ? true : false
                            onClicked: {
                                if ((lblPerformanceValueQAQC.text == "Satisfactory") || (lblPerformanceValueQAQC.text == "Unsatisfactory")) {
                                    dlgAdjustPerformance.swTowPerformance.checked = (lblPerformanceValueQAQC.text == "Satisfactory") ? true : false
                                } else {
                                    dlgAdjustPerformance.swTowPerformance.checked = (lblPerformanceValueField.text == "Satisfactory") ? true : false
                                }
                                dlgAdjustPerformance.originalTowPerformanceStatus = dlgAdjustPerformance.swTowPerformance.checked;

                                if ((lblMinimumTimeMetValueQAQC.text == "Yes") || (lblMinimumTimeMetValueQAQC.text == "No")) {
                                    dlgAdjustPerformance.swMinimumTimeMet.checked = (lblMinimumTimeMetValueQAQC.text == "Yes") ? true : false
                                } else {
                                    dlgAdjustPerformance.swMinimumTimeMet.checked = (lblMinimumTimeMetValueField.text == "Yes") ? true : false
                                }
                                dlgAdjustPerformance.originalMinimumTimeMetStatus = dlgAdjustPerformance.swMinimumTimeMet.checked;
                                timeSeries.availableImpactFactorsModel.populate();
                                timeSeries.selectedImpactFactorsModel.populate();
                                dlgAdjustPerformance.open()
                            }
                        } // btnAdjustPerformance
                        Label { text: qsTr("Field"); font.weight: Font.Bold; }
                        Label { text: qsTr("QA/QC"); font.weight: Font.Bold; }
                        Label {
                            id: lblPerformance
                            text: qsTr("Tow Performance:")
                            font.weight: Font.Bold;
                        } // lblPerformance
                        Label {
                            id: lblPerformanceValueField
                            text: qsTr("-")
                            Layout.preferredWidth: 80
                        } // lblPerformanceValueField
                        Label {
                            id: lblPerformanceValueQAQC
                            text: qsTr("-")
                            Layout.preferredWidth: 80
                        } // lblPerformanceValueQAQC
                        Label {
                            id: lblMinimumTimeMet
                            text: qsTr("Minimum Time Met:")
                            font.weight: Font.Bold;
                        } // lblMinimumTimeMet
                        Label {
                            id: lblMinimumTimeMetValueField
                            text: qsTr("-")
                            Layout.preferredWidth: 80
                        } // lblMinimumTimeMetValueField
                        Label {
                            id: lblMinimumTimeMetValueQAQC
                            text: qsTr("-")
                            Layout.preferredWidth: 80
                        } // lblMinimumTimeMetValueQAQC
                    } // glPerformance
                    RowLayout {
                        id: rlPerformance
                        anchors.top: glPerformance.bottom
                        anchors.topMargin: 15
                        anchors.left: glPerformance.left
                        Label {
                            id: lblImpactFactors
                            text: qsTr("Impact Factors:")
                            font.weight: Font.Bold;
                            Layout.preferredWidth: 125
                        } // lblImpactFactors
                        Label {
                            id: lblImpactFactorsValues
                            text: qsTr("-")
                            Layout.preferredWidth: 150
                        } // lblImpactFactorsValues

                    } // rlPerformance
                } // gbPerformance
                Item { Layout.preferredHeight: 10 }
                GroupBox {
                    id: gbComments
                    Layout.leftMargin: 10
                    Layout.rightMargin: 10
                    Layout.fillWidth: true
                    Layout.preferredHeight: 250
                    title: qsTr("Comments")
                    Column {
    //                        x: 10
                        width: parent.width
                        height: parent.height
                        spacing: 10
                        topPadding: 10
                        Button {
                            id: btnAddComment
                            x: 10
    //                            anchors.left: parent.left
    //                            anchors.leftMargin: 10
                            text: qsTr("Add")
                            enabled: (settings.haul != null) ? true : false
                            onClicked: { dlgAddComment.taComment.text = ""; dlgAddComment.open(); }
                        } // btnAddComment
                        Label {
                            id: lblComments
                            width: parent.width
                            text: qsTr("Comments")
                            wrapMode: Text.WordWrap
                        } // lblComments
                    }
                } // gbComments
            } // clPerformance
            RowLayout {
                id: rlMapLayers
                anchors.left: parent.left
                anchors.leftMargin: 10
//                anchors.horizontalCenter: parent.horizontalCenter
                Layout.fillWidth: true
                Label {
                    id: lblTracks
                    text: qsTr("Tracks:")
                    font.weight: Font.Bold;
                } // lblTracks
                Item { Layout.preferredWidth: 5 }
                Button {
                    id: btnVessel
                    text: qsTr("Vessel")
                    enabled: false
                    checkable: true
                    checked: true
                    Layout.preferredWidth: 50
                    onClicked: { timeSeries.toggleTracklineVisiblity("vessel", checked); }
                } // btnVessel
                Button {
                    id: btnGearRangeBearing
                    text: qsTr("ITI R/B")
                    enabled: false
                    checkable: true
                    checked: true
                    Layout.preferredWidth: 50
                    onClicked: { timeSeries.toggleTracklineVisiblity("iti r/b", checked); }
                } // btnGearRangeBearing
                Button {
                    id: btnGearIti
                    text: qsTr("$IIGLL")
                    enabled: false
                    checkable: true
                    checked: true
                    Layout.preferredWidth: 50
                    onClicked: { timeSeries.toggleTracklineVisiblity("iti $iigll", checked); }
                } // btnGearIti
                Item { Layout.preferredWidth: 10 }

                Label {
                    id: lblSmoothed
                    text: qsTr("Smoothed:")
                    font.weight: Font.Bold;
                } // lblSmoothed
                Item { Layout.preferredWidth: 5 }
                Button {
                    id: btnGearCatenary
                    text: qsTr("Cat")
                    enabled: false
                    checkable: true
                    checked: false
                    tooltip: qsTr("Catenary")
                    Layout.preferredWidth: 60
                    onClicked: { timeSeries.toggleTracklineVisiblity("Gear Catenary", checked); }
                } // btnGearCatenary
                Button {
                    id: btnGearVesselTrig
                    text: qsTr("V+Trig")
                    enabled: false
                    checkable: true
                    checked: false
                    tooltip: qsTr("Vessel Smoothed + Trig Method")
                    Layout.preferredWidth: 60
                    onClicked: { timeSeries.toggleTracklineVisiblity("Gear Vessel + Trig", checked); }
                } // btnGearVesselTrig
                Button {
                    id: btnGearGcdTrig
                    text: qsTr("GCD+Trig")
                    enabled: false
                    checkable: true
                    checked: false
                    tooltip: qsTr("Vessel GCD + Trig Method")
                    Layout.preferredWidth: 60
                    onClicked: { timeSeries.toggleTracklineVisiblity("Gear GCD + Trig", checked); }
                } // btnGearGcdTrig
                Button {
                    id: btnGearItiRB
                    text: qsTr("ITI R/B")
                    enabled: false
                    checkable: true
                    checked: false
                    tooltip: qsTr("ITI Range/Bearing")
                    Layout.preferredWidth: 60
                    onClicked: { timeSeries.toggleTracklineVisiblity("Gear ITI R/B", checked); }
                } // btnItiRBSmoothed
                Button {
                    id: btnGearItiIigll
                    text: qsTr("$IIGLL")
                    enabled: false
                    checkable: true
                    checked: false
                    tooltip: qsTr("ITI $IIGLL")
                    Layout.preferredWidth: 60
                    onClicked: { timeSeries.toggleTracklineVisiblity("Gear ITI $IIGLL", checked); }
                } // btnGearItiIigll
                Button {
                    id: btnGearItiRBTrig
                    text: qsTr("R/B+Trig")
                    enabled: false
                    checkable: true
                    checked: false
                    tooltip: qsTr("ITI Range/Bearing + Trig Method")
                    Layout.preferredWidth: 60
                    onClicked: { timeSeries.toggleTracklineVisiblity("Gear ITI R/B + Trig", checked); }
                } // btnGearItiRBTrig


//                Button {
//                    id: btnGearRangeExtTrig
//                    text: qsTr("R+Trig")
//                    checkable: true
//                    checked: false
//                    tooltip: qsTr("Range Extrapolation + Trig Method")
//                    Layout.preferredWidth: 60
//                    onClicked: { timeSeries.toggleTracklineVisiblity("Gear Range Ext + Trig", checked); }
//                } // btnGearRangeExtTrig
//                Button {
//                    id: btnGearRangeExtCatenaryTrig
//                    text: qsTr("R+Cat+Trig")
//                    checkable: true
//                    checked: false
//                    tooltip: qsTr("Range Extrapolation + Catenary + Trig Method")
//                    Layout.preferredWidth: 60
//                    onClicked: { timeSeries.toggleTracklineVisiblity("Gear Range Ext + Cat + Trig", checked); }
//                } // btnGearRangeExtCatenaryTrig
//                Button {
//                    id: btnGearGcdTrig
//                    text: qsTr("GCD+Trig")
//                    checkable: true
//                    checked: false
//                    tooltip: qsTr("Vessel GCD + Trig Method")
//                    Layout.preferredWidth: 60
//                    onClicked: { timeSeries.toggleTracklineVisiblity("GCD + Trig smoothed", checked); }
//                } // btnGearGcdTrig

 // "ITI R/B", "ITI R/B + Trig", "Slope/Distance + Trig", "ITI $IIGLL", "GCD + Trig"

            } // rlMapLayers
            MplFigureCanvas {
                id: mplTracklines
                objectName: "mplTracklines"
                Layout.fillWidth: true
                Layout.fillHeight: true
//                Layout.minimumWidth: 100
//                Layout.minimumHeight: 100
            } // mplTracklines
        } // cllControlPanel
    } // svTimeSeries

    AddCommentDialog { id: dlgAddComment } // dlgAddComment
    AdjustPerformanceDialog { id: dlgAdjustPerformance } // dlgAdjustPerformance
    FramDesktopOkayDialog { id: dlgOkay } // dlgOkay
    InvalidDataDialog { id: dlgInvalidData }  // dlgInvalidData
    ChangeTimeSeriesDialog { id: dlgChangeMeansTimeSeries } // dlgChangeMeansTimeSeries

    states: [
        State {
            name: "pan"
//            PropertyChanges { target: rlMeasureTime; enabled: false; visible: false}
//            PropertyChanges { target: clAddWaypoint; enabled: false; visible: false}
//            PropertyChanges { target: grpActions; title: "Pan / Zoom"}
//            PropertyChanges { target: gbHaulDetails; enabled: false; visible: false;}
//            PropertyChanges { target: gbPerformance; enabled: false; visible: false;}
//            PropertyChanges { target: gbComments; enabled: false; visible: false;}

        }, // pan
        State {
            name: "measureTime"
            PropertyChanges { target: rlMeasureTime; enabled: true; visible: true}
            PropertyChanges { target: clAddWaypoint; enabled: false; visible: false}
            PropertyChanges { target: itmDistanceFished; enabled: false; visible: false; }
            PropertyChanges { target: itmCalculateMeans; enabled: false; visible: false; }
            PropertyChanges { target: itmInvalidData; enabled: false; visible: false; }
            PropertyChanges { target: itmShiftTimeSeries; enabled: false; visible: false; }

            PropertyChanges { target: grpActions; title: "Measure Time Span"}
            PropertyChanges { target: clPerformance; enabled: !btnMap.checked; visible: !btnMap.checked; }
        }, // measureTime
        State {
            name: "addWaypoint"
            PropertyChanges { target: rlMeasureTime; enabled: false; visible: false; }
            PropertyChanges { target: clAddWaypoint; enabled: true; visible: true; }
            PropertyChanges { target: itmDistanceFished; enabled: false; visible: false; }
            PropertyChanges { target: itmCalculateMeans; enabled: false; visible: false; }
            PropertyChanges { target: itmInvalidData; enabled: false; visible: false; }
            PropertyChanges { target: itmShiftTimeSeries; enabled: false; visible: false; }

            PropertyChanges { target: grpActions; title: "Calculate / Adjust Waypoints"}
            PropertyChanges { target: clPerformance; enabled: true; visible: true; }

//            PropertyChanges { target: gbHaulDetails; enabled: true; visible: true;}
//            PropertyChanges { target: gbPerformance; enabled: true; visible: true;}
//            PropertyChanges { target: gbComments; enabled: true; visible: true;}
        }, // addWaypoint
        State {
            name: "shiftTimeSeries"
            PropertyChanges { target: rlMeasureTime; enabled: false; visible: false; }
            PropertyChanges { target: clAddWaypoint; enabled: false; visible: false; }
            PropertyChanges { target: itmDistanceFished; enabled: false; visible: false; }
            PropertyChanges { target: itmCalculateMeans; enabled: false; visible: false; }
            PropertyChanges { target: itmInvalidData; enabled: false; visible: false; }
            PropertyChanges { target: itmShiftTimeSeries; enabled: true; visible: true; }

            PropertyChanges { target: grpActions; title: "Shift Time Series"}
            PropertyChanges { target: clPerformance; enabled: !btnMap.checked; visible: !btnMap.checked; }
        }, // shiftTimeSeries
        State {
            name: "splitSeries"
            PropertyChanges { target: rlMeasureTime; enabled: false; visible: false; }
            PropertyChanges { target: clAddWaypoint; enabled: false; visible: false; }
            PropertyChanges { target: itmDistanceFished; enabled: false; visible: false; }
            PropertyChanges { target: itmCalculateMeans; enabled: false; visible: false; }
            PropertyChanges { target: itmInvalidData; enabled: false; visible: false; }
            PropertyChanges { target: itmShiftTimeSeries; enabled: false; visible: false; }

            PropertyChanges { target: grpActions; title: "Split Time Series"}
            PropertyChanges { target: clPerformance; enabled: !btnMap.checked; visible: !btnMap.checked; }
        }, // splitSeries
        State {
            name: "calculateMeans"
            PropertyChanges { target: rlMeasureTime; enabled: false; visible: false}
            PropertyChanges { target: clAddWaypoint; enabled: false; visible: false}
            PropertyChanges { target: itmDistanceFished; enabled: false; visible: false; }
            PropertyChanges { target: itmCalculateMeans; enabled: true; visible: true; }
            PropertyChanges { target: itmInvalidData; enabled: false; visible: false; }
            PropertyChanges { target: itmShiftTimeSeries; enabled: false; visible: false; }

            PropertyChanges { target: grpActions; title: "Calculate Means"}
            PropertyChanges { target: clPerformance; enabled: !btnMap.checked; visible: !btnMap.checked; }
        }, // calculateMeans
        State {
            name: "invalidData"
            PropertyChanges { target: rlMeasureTime; enabled: false; visible: false}
            PropertyChanges { target: clAddWaypoint; enabled: false; visible: false}
            PropertyChanges { target: itmDistanceFished; enabled: false; visible: false; }
            PropertyChanges { target: itmCalculateMeans; enabled: false; visible: false; }
            PropertyChanges { target: itmInvalidData; enabled: true; visible: true; }
            PropertyChanges { target: itmShiftTimeSeries; enabled: false; visible: false; }

            PropertyChanges { target: grpActions; title: "Mark Data Points as Invalid"}
            PropertyChanges { target: clPerformance; enabled: !btnMap.checked; visible: !btnMap.checked; }
        }, // invalidData
        State {
            name: "distanceFished"
            PropertyChanges { target: rlMeasureTime; enabled: false; visible: false}
            PropertyChanges { target: clAddWaypoint; enabled: false; visible: false}
            PropertyChanges { target: itmDistanceFished; enabled: true; visible: true; }
            PropertyChanges { target: itmCalculateMeans; enabled: false; visible: false; }
            PropertyChanges { target: itmInvalidData; enabled: false; visible: false; }
            PropertyChanges { target: itmShiftTimeSeries; enabled: false; visible: false; }

            PropertyChanges { target: grpActions; title: "Calculate Distance Fished"}
            PropertyChanges { target: clPerformance; enabled: !btnMap.checked; visible: !btnMap.checked; }
        }, // distanceFished
        State {
            name: "trackLines"
            PropertyChanges { target: clPerformance; enabled: false; visible: false; }
        }, // trackLines
        State {
            name: "nonTrackLines"
            PropertyChanges { target: clPerformance; enabled: true; visible: true; }
        } // nonTrackLines
    ]
}
