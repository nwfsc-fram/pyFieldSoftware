import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 700
    height: 300
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "Adjust Waypoint Times"
//    title: customizeTitle.checked ? windowTitleField.text : "Customized content"

//    property alias btnOkay: btnOkay
//    standardButtons: StandardButton.Ok | StandardButton.Cancel

    property variant row: null
    property string event: ""
    property string start_date_time: ""
    property string end_date_time: ""
    property string previous_end: ""
    property string next_start: ""
    property string next_waypoint_name: ""
    property bool end_time_exists: false

    property alias sldStartTime: sldStartTime
    property alias sldEndTime: sldEndTime
    property alias lblStartTimeNew: lblStartTimeNew
    property alias lblEndTimeNew: lblEndTimeNew

    property string startTimeCurrent: ""
    property string startTimeNew: ""
    property string startTimeChange: ""
    property string endTimeCurrent: ""
    property string endTimeNew: ""
    property string endTimeChange: ""

    onRejected: {  }
    onAccepted: {  }

    Component.onCompleted: {
        if (!Math.trunc) {
            Math.trunc = function(v) {
                v = +v;
                if (!isFinite(v)) return v;
                return (v - v % 1)   ||   (v < 0 ? -0 : v === 0 ? v : 0);
            };
        }
    }

    function addZero(i) {
        if (i < 10) {
            i = "0" + i;
        }
        return i;
    }

    function sliderValueChanged(slider, value) {

        // Get the current time for the given slider
        var currentTime = (slider === "start") ? startTimeCurrent : endTimeCurrent;
        var sliderWidget = (slider === "start") ? sldStartTime : sldEndTime

        // Create a new Date object for the current time for the given slider
        var elems = currentTime.split(":");
        var currentDateTime = new Date();
        currentDateTime.setHours(parseInt(elems[0]), parseInt(elems[1]), parseInt(elems[2]));

        // Create Date objects for newDateTime for comparison checking + adjust forward based on value (= seconds)
        var newDateTime = new Date(currentDateTime.getTime());
        newDateTime.setSeconds(newDateTime.getSeconds() + value);

        // Create a well-formatted timestring for newDateTime to pass back for display
        var timeStr = addZero(newDateTime.getHours()) + ":" +
                        addZero(newDateTime.getMinutes()) + ":" +
                        addZero(newDateTime.getSeconds());

        // Create Date objects for previousEndDateTime and nextStartDateTime for comparison checking
        var previousEndDateTime = null;
        if (previous_end.length === 8) {
            elems = previous_end.split(":");
            previousEndDateTime = new Date(currentDateTime.getTime());
            previousEndDateTime.setHours(parseInt(elems[0]), parseInt(elems[1]), parseInt(elems[2]));
        }
        var nextStartDateTime = null;
        if (next_start.length === 8) {
            elems = next_start.split(":");
            nextStartDateTime = new Date(currentDateTime.getTime());
            nextStartDateTime.setHours(parseInt(elems[0]), parseInt(elems[1]), parseInt(elems[2]));
        }

        // Create Date objects for startTimeNew and endTimeNew for comparison checking
        var startDateTimeNew = null;
        if (startTimeNew.length === 8) {
            elems = startTimeNew.split(":");
            startDateTimeNew = new Date(currentDateTime.getTime());
            startDateTimeNew.setHours(parseInt(elems[0]), parseInt(elems[1]), parseInt(elems[2]));
        }
        var endDateTimeNew = null;
        if (endTimeNew.length === 8) {
            elems = endTimeNew.split(":");
            endDateTimeNew = new Date(currentDateTime.getTime());
            endDateTimeNew.setHours(parseInt(elems[0]), parseInt(elems[1]), parseInt(elems[2]));
        }

        var msg;
        var breakIt = false;
        var delta = null;

        // Test if slider === start and newDateTime > endDateTimeNew
        if ((slider === "start") && (endDateTimeNew !== null)) {
            if (newDateTime.getTime() >= endDateTimeNew.getTime()) {
                msg = 'Error: cannot create a new start time past the new end time'
                delta = -5;
                breakIt = true;
            }
        }

        // Test if slider === start and newDateTime < previousEndDateTime
        if ((slider === "start") && (previousEndDateTime !== null)) {
            if (newDateTime.getTime() <= previousEndDateTime.getTime()) {
                msg = 'Error: cannot set the new start time before the end of the previous waypoint'
                delta = 5;
                breakIt = true;
            }
        }

        // Test if slider === end and newDateTime < startDateTimeNew
        if ((slider === "end") && (startDateTimeNew !== null)) {
            if (newDateTime.getTime() <= startDateTimeNew.getTime()) {
                msg = 'Error: cannot set the new end time before the new start time';
                delta = 5;
                breakIt = true;
            }
        }

        // Test if slider === end and newDateTime > nextStartDateTime
        if ((slider === "end") && (nextStartDateTime !== null)) {
            if ((newDateTime.getTime() >= nextStartDateTime.getTime()) &&
                (next_waypoint_name !== "CTD") &&
                (next_waypoint_name !== "")) {
                msg = 'Error: cannot set the new end time after the start of the next waypoint';
                delta = -5;
                breakIt = true;
            }
        }

        if (breakIt) {
            console.info(msg);
            dlgOkay.message = msg;
            dlgOkay.open();
            sliderWidget.value = sliderWidget.value + delta;
            return;
        }

        // Passed all tests, update the New + Change values
        if (slider === "start") {
            startTimeNew = timeStr;
            startTimeChange = formatValue(value);

        } else if (slider === "end") {
            endTimeNew = timeStr;
            endTimeChange = formatValue(value);
        }
    }

    function getNewTime(start_or_end, currentTime, value) {
        var elems = currentTime.split(":");
        var newDateTime = new Date();
        newDateTime.setHours(parseInt(elems[0]), parseInt(elems[1]), parseInt(elems[2]));

        // Get the full current date/time, previous end date/time, and next start date/time
        var currentDateTime = new Date(newDateTime.getTime());
        var previousEndDateTime = new Date(newDateTime.getTime());
        if (previous_end.length === 8) {
            elems = previous_end.split(":");
            previousEndDateTime.setHours(parseInt(elems[0]), parseInt(elems[1]), parseInt(elems[2]));
        }
        var nextStartDateTime = new Date(newDateTime.getTime());
        if (next_start.length === 8) {
            elems = next_start.split(":");
            nextStartDateTime.setHours(parseInt(elems[0]), parseInt(elems[1]), parseInt(elems[2]));
        }

        // Existing New Start and End Times - Used to ensure that the newDateTime isn't before or after these
        var existingNewStartDateTime = new Date(newDateTime.getTime());
        if (lblStartTimeNew.text.length === 8) {
            elems = lblStartTimeNew.text.split(":");
            existingNewStartDateTime.setHours(parseInt(elems[0]), parseInt(elems[1]), parseInt(elems[2]));
        }
        var existingNewEndDateTime = new Date(newDateTime.getTime());
        if (lblEndTimeNew.text.length === 8) {
            elems = lblEndTimeNew.text.split(":");
            existingNewEndDateTime.setHours(parseInt(elems[0]), parseInt(elems[1]), parseInt(elems[2]));
        }

        // Adjust the newDateTime forward/backwards by the value of seconds
        newDateTime.setSeconds(newDateTime.getSeconds() + value);

        var timeStr = addZero(newDateTime.getHours()) + ":" +
                        addZero(newDateTime.getMinutes()) + ":" +
                        addZero(newDateTime.getSeconds())

        // Test if start_or_end === start and newTime > current end time
        if ((start_or_end === "start") && (lblEndTimeNew.text.length === 8)) {
            if (newDateTime.getTime() > existingNewEndDateTime.getTime()) {
                console.info('Error: cannot create a new start time past the new end time');
                return
            }

        // Test if start_or_end === start and newTime < previous_ned
        }  //else if ((start_or_end === "start") && ()) {

        // Test if start_or_end === end and newTime < current start time
//        } else if ((start_or_end === "end") && (lblStartTimeNew)) {
//
//        // Test if start_or_end === end and newTime > next_start
//        } else if ((start_or_end === "end") && ()) {
//
//        }

        console.info(previous_end + ' >>> ' + start_or_end + ' - ' + timeStr + ' >>> ' + next_start);

        return timeStr;
    }

    function formatValue(value) {
        var timeStr;
        var mm = Math.trunc(value / 60);
        var ss = addZero(Math.abs(value % 60))
        if ((value < 0) && (mm === 0)) {
            mm = "-" + mm
        }
        timeStr = mm + ":" + ss;
        return timeStr;
    }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        ColumnLayout {
            y: 20
            spacing: 40
            anchors.horizontalCenter: parent.horizontalCenter
            Label {
                id: lblMessage
                anchors.horizontalCenter: parent.horizontalCenter
                font.pixelSize: 20
                text: "Waypoint: " + event
            } // lblMessage
            RowLayout {
                spacing: 20
                ColumnLayout {
                    Label { text: "Start time - Current" }
                    Label {
                        id: lblStartTimeCurrent
                        text: startTimeCurrent
                    } // lblStartTimeCurrent
                } // Current - Start
                Button {
                    id: btnStartBack
                    text: qsTr("<")
                    Layout.preferredWidth: 25
                    onClicked: {
                        sldStartTime.value = sldStartTime.value - 1;
                    }
                } // btnStartBack
                Slider {
                    id: sldStartTime
                    minimumValue: -480
                    maximumValue: 120
                    value: 0
                    stepSize: 1
                    Layout.preferredWidth: 300
                    onValueChanged: {
                        sliderValueChanged("start", value);
                    }
                } // sldStartTime
                Button {
                    id: btnStartForward
                    text: qsTr(">")
                    Layout.preferredWidth: 25
                    onClicked: {
                        sldStartTime.value = sldStartTime.value + 1;
                    }
                } // btnStartForward
                ColumnLayout {
                    Label { text: "Start time - New" }
                    Label {
                        id: lblStartTimeNew
                        text: startTimeNew  //  getNewTime("start", start_date_time, sldStartTime.value)
                    } // lblStartTimeNew
                } // New - Start
                ColumnLayout {
                    Label { text: "Time Change" }
                    Label {
                        id: lblStartTimeChange
                        text: startTimeChange //  formatValue(sldStartTime.value)
                    } // lblStartTimeChange
                } // Time Change - Start
            } // rlStart
            RowLayout {
                spacing: 20
                ColumnLayout {
                    Label { text: "End time - Current" }
                    Label { text: endTimeCurrent }
                } // Current - End
                Button {
                    id: btnEndBack
                    text: qsTr("<")
                    Layout.preferredWidth: 25
                    enabled:  endTimeCurrent !== "" ? true : false
//                    enabled: end_time_exists
                    onClicked: {
                        sldEndTime.value = sldEndTime.value - 1;
                    }
                } // btnEndBack
                Slider {
                    id: sldEndTime
//                    enabled: end_time_exists
                    minimumValue: -480
                    maximumValue: 120
                    value: 0
                    stepSize: 1
                    Layout.preferredWidth: 300
                    enabled:  endTimeCurrent !== "" ? true : false
                    onValueChanged: {
                        sliderValueChanged("end", value);
                    }
                } // sldEndTime
                Button {
                    id: btnEndForward
                    text: qsTr(">")
//                    enabled: end_time_exists
                    enabled:  endTimeCurrent !== "" ? true : false
                    Layout.preferredWidth: 25
                    onClicked: {
                        sldEndTime.value = sldEndTime.value + 1;
                    }
                }
                ColumnLayout {
                    Label { text: "End time - New" }
                    Label { id: lblEndTimeNew; text: endTimeNew }
                } // New - End
                ColumnLayout {
                    Label { text: "Time Change" }
                    Label { text: endTimeChange }
                } // Time Change - End
            } // rlEnd
        }
        RowLayout {
            id: rwlButtons
            anchors.horizontalCenter: parent.horizontalCenter
            y: dlg.height - this.height - 20
            spacing: 20
            Button {
                id: btnOkay
                text: "Okay"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.accept() }
            } // btnOkay
            Button {
                id: btnCancel
                text: "Cancel"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.reject() }
            } // btnCancel

        } // rwlButtons
        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
    OkayDialog {
        id: dlgOkay
        action: "Please select a different time"
    }
}
