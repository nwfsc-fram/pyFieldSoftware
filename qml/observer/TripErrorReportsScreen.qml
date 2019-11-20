import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Styles 1.4

// Custom Models
import "../common"
import "."

Item {
    id: pageErrorReports

    // Left and right margin spacing for Trip Issues table
    property int issuesRowHorizontalMargin: 20

    function page_state_id() { // for transitions
        return "trip_errors_state";
    }

    function getRowWithTripId(tripId) {
        var row = 0;
        if (tripErrorReportsTable.rowCount > 0) {
            for (var r = 0; r < tripErrorReportsTable.rowCount; r++) {
                if (tripErrorReportsTable.model.get(r).trip == tripId) {
                    row = r;
                    break;
                }
            }
        }
        return row;
    }

    Component.onCompleted: {
        // Observed: this method is called on every entry into TER screen.
        // At entry, set error report's current trip to OPTECS's current trip.
        errorReports.currentTripId = appstate.trips.tripId;
        // And select its row in this screen's list of trips:
        tripErrorReportsTable.currentRow = getRowWithTripId(errorReports.currentTripId);
        tripErrorReportsTable.selection.select(
                tripErrorReportsTable.currentRow,   // From
                tripErrorReportsTable.currentRow);  // To (range of 1)
        disableAllUiButCancelButton(false);
        enableBtnRunTERIfValidTrip();
        console.debug("Current OPTECS Trip", errorReports.currentTripId, "is selected (at row",
                tripErrorReportsTable.currentRow, ").");
        if (obsSM.pendingEndTrip) {
            obsSM.pendingEndTrip = false;
        }
    }

    Timer {
        id: timer
    }
    function delay(delayTimeSecs, callback) {
        timer.interval = delayTimeSecs * 1000;
        timer.repeat = false;
        timer.triggered.connect(callback);
        timer.start();
    }

    function disableAllUiButCancelButton(disableAllBut) {
        if (disableAllBut) {
            // Disable navigation to home
            framHeader.backwardEnable(false);
            // Disable adding comment
            framFooter.hideCommentButton(true);
            // Disable selecting row on trips
            tripErrorReportsTable.selectionMode = SelectionMode.NoSelection;
            // Disable selecting row on trip issues
            tripIssuesTable.selectionMode = SelectionMode.NoSelection;
        } else {
            framHeader.backwardEnable(true);
            framFooter.hideCommentButton(false);
            tripErrorReportsTable.selectionMode = SelectionMode.SingleSelection;
            tripIssuesTable.selectionMode = SelectionMode.SingleSelection;
        }
    }

    function runInProgress() {
        return btnCancelTER.enabled;
    }

    function enableBtnRunTERIfValidTrip() {
        var currentTripId = errorReports.currentTripId;
        var isValid = (currentTripId != null && currentTripId >= 0);
        if (isValid) {
            btnRunTER.enabled = true;
        }
    }

    RowLayout {
        id: rowTripErrorReportsTable
        Rectangle {  // spacer
            color: "transparent"
            Layout.preferredWidth: 40
        }

        ObserverTableView {
            id: tripErrorReportsTable

            Layout.preferredWidth:  960 // Leave room for RunTER and CancelTER
            Layout.preferredHeight: 185 //pageErrorReports.height * 0.25

            model: errorReports.tripErrorReportsViewModel

            onClicked: {
                console.debug("Row " + row + " was clicked.");
                enableBtnRunTERIfValidTrip();
            }

            onCurrentRowChanged: {
                if (!runInProgress()) {
                    var tripId = model.get(currentRow).trip;
                    console.debug("Current Row " + currentRow + " (0-rel) was CHANGED. Trip = " + tripId);
                    errorReports.currentTripId = tripId;

                } else {
                    console.debug("TER run in progress - not displaying a different trip's issues.");
                }
            }

            // Functions
            function getCurrentTripId() {
                var currentTripId = errorReports.currentTripId;
                console.debug("Current Trip ID = " + currentTripId);
                return currentTripId;
                //## CurrentRow is sometimes -1 when it shouldn't be. Not sure why.
                //return model.get(tripErrorReportsTable.currentRow).trip;
            }

            // Sub-elements
            TableViewColumn {
                role: "trip"
                title: "Trip#"
                width: 70
            }

            TableViewColumn {
                role: "completed"
                title: ""
                width: 20
                horizontalAlignment: Text.AlignLeft
            }

            TableViewColumn {
                role: "program"
                title: "Program"
                width: 180
            }

            TableViewColumn {
                role: "vessel"
                title: "Vessel"
                width: 200
            }

            TableViewColumn {
                role: "observer"
                title: "Observer"
                width: 150
            }

            TableViewColumn {
                role: "n_errors"
                title: "#Errs"
                width: 70
            }

            TableViewColumn {
                role: "last_run_date"
                title: "Last Run Date"
                width: 250
            }
        }

        Rectangle {  // spacer
            color: "transparent"
            Layout.preferredWidth: 25
        }

        GridLayout {
            columns: 1
            RowLayout {
                ObserverSunlightButton {
                    id: btnRunTER
                    text: "Run\nTER"
                    enabled: false
                    Layout.preferredWidth: 90

                    function runTER(currentTripId) {
                        console.info("Running Error Reporting on Trip# " + currentTripId + ".");
                        btnRunTER.enabled = false;
                        btnCancelTER.show(true);
                        progressBarTER.maximumValue = errorReports.currentTripChecksCount;
                        console.debug("Set progress bar max to " + progressBarTER.maximumValue);
                        progressBarTER.show(true);
                        isRunningLabel.visible = false;
                        // Disable navigation from screen. Only widget enabled: cancel button
                        pageErrorReports.disableAllUiButCancelButton(true);

                        errorReports.runChecksOnTrip(currentTripId);
                    }

                    function evaluateTripChecksThenRunTER(currentTripId) {

                        console.info("Trip checks have not been evaluated. Asking confirmation to perform eval.");
                        confirmDoTripCheckEvaluation.askTripCheck(currentTripId);
                    }

                    onClicked: {
                        var currentTripId = tripErrorReportsTable.getCurrentTripId();
                        if (currentTripId < 0) {
                            console.error("Unexpected invalid Trip ID = " + currentTripId + "; taking no action.");
                            return;
                        }

                        // Before running the trip checks, make sure the checks have been evaluated for running
                        // on OPTECS to a SQLite database.
                        if (!errorReports.tripChecksAreEvaluated()) {
                            evaluateTripChecksThenRunTER(currentTripId);
                        } else {
                            btnRunTER.runTER(currentTripId);
                        }
                    }
                }

                Rectangle {  // spacer
                    color: "transparent"
                    Layout.preferredWidth: 25
                }

                ObserverSunlightButton {
                    id: btnCancelTER
                    text: "Cancel\nTER"
                    visible: false
                    enabled: false
                    checked: false
                    Layout.preferredWidth: 90

                    function show(onNotOff) {
                        if (onNotOff) {
                            console.debug("Showing Cancel TER button.");
                            visible = true;
                            enabled = true;
                            isRunningLabel.visible = false;
                        } else {
                            console.debug("Hiding Cancel TER button.");
                            visible = false;
                            enabled = false;
                            isRunningLabel.visible = false;
                        }
                    }
                    onClicked: {
                        console.debug("TER run cancel button pressed.");
                        errorReports.cancelChecksOnTrip();
                        // ## This is important: take down progress bar ASAP, on click.
                        // ## This causes trip check chunk signal updates to the bar's value to be thrown away.
                        // ## If not thrown away, behavior is an OPTECS hang.
                        progressBarTER.show(false);
                        isRunningLabel.visible = false;
                    }
                }

            }
            RowLayout{
                    Label {
                        id: isRunningLabel
                        visible: false
                        text: "Running...\n please wait."
                        font.pixelSize: 25
                    }
                    ObserverSunlightButton {
                        id: btnSubmitTrip
                        text: "Submit\nTrip"
                        visible: btnRunTER.enabled && !isRunningLabel.visible
                        enabled: btnRunTER.enabled
                        Layout.preferredWidth: 90
                        onClicked: {
                            appstate.end_trip();
                            appstate.trips.tripsChanged();
                            dlgDBSync.initSync(appstate.users.currentUserName, appstate.users.currentUserPassword)
                            framHeader.backClicked("home_state", "End Trip");
                        }
                    }
                    ObserverSunlightButton {
                        id: btnEditTripData
                        text: "Edit Trip\nData"
                        visible: btnRunTER.enabled && !isRunningLabel.visible
                        enabled: btnRunTER.enabled
                        Layout.preferredWidth: 90
                        onClicked: {
                            framHeader.backClicked("home_state", "End Trip");
                        }
                    }
                }
            RowLayout {
                Rectangle {  // Establish the row height, with spacing.
                    color: "transparent"
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 100
                }
                ProgressBar {
                    id: progressBarTER
                    visible: false
                    enabled: false
                    Layout.preferredHeight: 50
                    function show(doShow) {
                        console.debug("ProgressBar visible: " + doShow);
                        progressBarTER.value = minimumValue;
                        if (doShow) {
                            progressBarTER.visible = true;
                        } else {
                            progressBarTER.visible = false;
                        }
                    }
                    minimumValue: 0
                    value: 0
                }
            }
        }

        Connections {
            target: errorReports
            function restoreUiAfterTerCompletes() {
                btnCancelTER.show(false);
                btnRunTER.enabled = true;
                progressBarTER.show(false);
                pageErrorReports.disableAllUiButCancelButton(false);
            }
            onTerRunCompleted: {
                console.debug("TER Run completed!");
                restoreUiAfterTerCompletes();
           }
            onTerRunCanceled: {
                console.debug("TER Run canceled.");
                restoreUiAfterTerCompletes();
            }
            onTerCheckChunkCompleted: {  // Signal parameters: "chunkSize" and "checksCompleted"
                // ## If OPTECS hangs after a Cancel, first try: disable next line.
                progressBarTER.value = checksCompleted;
            }
        }
    }

    // ## This isn't visible. Why not?
    RowLayout { // Spacer
        Rectangle {
            color: "blue" //"transparent"
            Layout.preferredHeight: 50
            height: 50
        }
    }

    RowLayout {
        anchors.fill: parent

        Rectangle {  // spacer
            color: "transparent"
            Layout.preferredWidth: issuesRowHorizontalMargin
        }

        ObserverTableView {
            id: tripIssuesTable

            Layout.preferredWidth: pageErrorReports.width - (2 * issuesRowHorizontalMargin)
            Layout.preferredHeight: 450 //pageErrorReports.height * 0.75

            //anchors.top: rowTripErrorReportsTable.bottom
            anchors.bottom: parent.bottom

            model: errorReports.tripIssuesViewModel

            TableViewColumn {
                role: "trip_check"
                title: "Trip\nCheck"
                width: 75
            }

            TableViewColumn {
                // Use fishing_activity_num instead of fishing_activity_id:
                // the former is an application-wide unique number, the latter is trip-relative.
                role: "fishing_activity_num"
                title: "Haul\n#"
                width: 65
            }

            TableViewColumn {
                role: "catch_num"   // Haul-relative number, unlike catch_id, which must be unique application-wide.
                title: "Catch\n#"
                width: 65
            }

            TableViewColumn {
                role: "species_name"
                title: "Species\nName"
                width: 140
            }

            TableViewColumn {
                role: "error_item"
                title: "Error\nItem"
                width: 200
            }

            TableViewColumn {
                role: "error_value"
                title: "Error\nValue"
                width: 65
            }

            TableViewColumn {
                role: "check_type"
                title: "E/\nW"
                width: 35
            }

            TableViewColumn {
                id: colMsg
                role: "check_message"
                title: "Error Message\n"
                width: 575
                // Properties to support squeezing in as much of CHECK_MESSAGE as possible.
                // Background: currently, the maximum length CHECK_MESSAGE is 132 characters (TRIP_CHECK 1941).
                // This limited flexibility code will handle up to 270 characters (3 rows of 90 characters).
                // If standard font size:
                property int charsPerStdFontLine: 60
                property int rowsWithStdFont: 2 // Row is about 40 pixels high, so two rows possible
                property int stdFontSize: 18
                // If small font size:
                property int charsPerSmallFontLine: 90
                property int smallFontSize: 12  // This size allows three rows to be shown.

                delegate: Text {
                    function stdPixelSizeWillDo(msg_string) {
                        return (msg_string.length <= colMsg.rowsWithStdFont * colMsg.charsPerStdFontLine);
                    }
                    function getFontPixelSize(msg_string) {

                        // Use the standard size for up to 2 * charsPerStdFontLine characters, small otherwise
                        if (stdPixelSizeWillDo(msg_string))
                            return colMsg.stdFontSize;
                        else
                            return colMsg.smallFontSize;
                    }
                    function splitMessage(msg) {
                        // TODO: split on word boundary.
                        // For now, insert newline after charsPerLine.
                        var charsPerLine = stdPixelSizeWillDo(msg)?
                                colMsg.charsPerStdFontLine:
                                colMsg.charsPerSmallFontLine;

                        if (msg <= charsPerLine)
                            return msg;

                        var returnMsg = "";
                        var startIdx = 0;
                        var remainder = msg;
                        while (remainder.length > 0) {
                            var line = remainder.substring(0, charsPerLine);
                            if (returnMsg.length > 0)
                                returnMsg += "\n";
                            returnMsg += line;
                            remainder = remainder.substring(charsPerLine);
                        }
                        return returnMsg;
                    }
                    // QML provides the value returned by role "tags_str" in styleData.value. Not obvious!
                    text: styleData.value ? splitMessage(styleData.value, 100) : ""
                    font.pixelSize: getFontPixelSize(styleData.value ? styleData.value : "")
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        // Dialog Boxes
        FramNoteDialog {
            id: dlgNoTripFound
            message: "No trip found for current users.\n" +
                    "Please enter a trip."
        }

        ProtocolWarningDialog {
            id: confirmDoTripCheckEvaluation
            message: "Trip Checks have changed and must be\n evaluated. " +
                        "This takes at least 15 seconds,\n and the screen will freeze up\n during this check. OK to proceed?"
            btnAckText:"No/Cancel"
            btnOKText: "Yes: Evaluate\nTrip Checks"
            property int currentTripId: -1
            function askTripCheck(trip_id) {
                isRunningLabel.visible = true;
                currentTripId = trip_id;
                open();
            }
            onAccepted: {
                // Acknowledged that this is OK
                console.info("Performing trip check evaluation");
                errorReports.evaluateTripChecks();
                btnRunTER.runTER(currentTripId);
            }
            onRejected: {
                isRunningLabel.visible = false;
            }
        }
    }
}
