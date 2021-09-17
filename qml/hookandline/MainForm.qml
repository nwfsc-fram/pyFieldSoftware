import QtQuick 2.5
import QtQuick.Controls 1.5
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0
import FRAM 1.0

import "../common"

Item {
    id: item1

    /*
    The measurements dictionary identifies keys that represent the measurement and unit of measurement.
    The associated values are then a dictionary themselves and these could contain two keys, a target key identifying
    where the data should be pushed in terms of a UI element, and a function element that identifies a method
    to send the data to perform some intermediary processing before pushing to the UI element.  So a sample
    measurement dictionary would look like the following:

    property variant measurements: {
        "Time - UTC, hhmmss.ss": {"target": tfTime, "function": dataConverter.utc_to_local_time},
        "Latitude - Vessel, DDMM.MMM": {"target": tfLatitude},
        "Longitude - Vessel, DDDMM.MMM": {"target": tfLongitude},
    }

    Note that the target subkey is required, whereas the function subkey is optional
    */
    property variant measurements: {
        "Time - UTC, hhmmss.ss": {"target": tfTime, "function": dataConverter.utc_to_local_time},
        "Latitude - Vessel, DDMM.MMM": {"target": tfLatitude, "function": dataConverter.format_latitude},
        "Longitude - Vessel, DDDMM.MMM": {"target": tfLongitude, "function": dataConverter.format_longitude},
        "Depth, ftm": {"target": tfDepth},
        "Temperature - Sea Surface, C": {"target": tfSST},
        "Wind Speed - Relative, kts": {"target": tfRelWindSpeed},
        "Wind Direction - Relative, deg": {"target": tfRelWindDir},
        "Speed Over Ground, kts": {"target": tfSpeedOverGround},
        "Track Made Good, deg": {"target": tfDriftDir}
    }

    property variant parsing_line_starts: []
    property variant parsing_rules: {"test": ""}

    property bool is_streaming: false
    property int reload_row: -1      // Used to specify the cbDropType currentIndex in the tvEvents tableview

    property int enabled_row: -1    // Necessary for setting enabled status of tvEvent items (tide_height_ftm, etc.)

    property int operation_id
    property int operation_details_id

    property int sequence             // Regular sampling type seq #
    property int camera_sequence      // Camera sampling type seq #
    property int test_sequence;       // Test Drop sampling type seq #
    property int software_test_sequence;  // Software Test sampling type seq

    property variant meatballs: []
    property variant tooltips: []
    property alias tfSetId: tfSetId

    signal resetfocus()
    onResetfocus: { tvEvents.forceActiveFocus() }

    Connections {
        target: fpcMain.eventsModel
        onNoneValuesObtained: warnNoneValues(msg)
    } // fpcMain.eventsModel.onNoneValuesObtained

    Connections {
        target: fpcMain.eventsModel
        onErrorReceived: reportErrorReceived(msg)
    }

    function reportErrorReceived(msg) {
        dlgOkay.message = msg
        dlgOkay.action = ""
        dlgOkay.value = ""
        dlgOkay.accepted_action = ""
        dlgOkay.open()
        taGeneral.text = taGeneral.text + "  " + msg.replace("\n\n", " ");
        var items = [{"field": "general_comments", "value": taGeneral.text}]
        fpcMain.update_table_row("OperationDetails", operation_details_id, items);

    }

    function warnNoneValues(msg) {
        dlgOkay.message = msg
        dlgOkay.action = ""
        dlgOkay.value = ""
        dlgOkay.accepted_action = ""
        dlgOkay.open()
        taGeneral.text = taGeneral.text + "  " + msg.replace("\n\n", " ");
        var items = [{"field": "general_comments", "value": taGeneral.text}]
        fpcMain.update_table_row("OperationDetails", operation_details_id, items);

//        var items = [{"field": "habitat_comments", "value": taHabitat.text}]
//        fpcMain.update_table_row("OperationDetails", operation_details_id, items);
    }

    Connections {
        target: serialPortManager
        onPortDataStatusChanged: changedPortDataStatus(com_port, status)
    } // serialPortManager.onPortDataStatusChanged
    Connections {
        target: serialPortManager
        onDataReceived: parseReceivedData(com_port, data)
    } // serialPortManager.onDataReceived
    Connections {
        target: serialPortSimulator
        onDataReceived: parseSimulatedData(data)
    } // serialPortSimulator.onDataReceived
    Connections {
        target: sensorDataFeeds.sensorConfigurationModel
        onDataChanged: resetMeatballs()
    } // sensorDataFeeds.sensorConfigurationModel.onDataChanged
    Connections {
        target: sensorDataFeeds.sensorConfigurationModel
        onCountChanged: resetMeatballs()
    } // sensorDataFeeds.sensorConfigurationModel.onCountChanged
    Connections {
        target: sensorDataFeeds.measurementConfigurationModel
        onDataChanged: parsingRulesChanged()
    } // sensorDataFeeds.measurementConfigurationModel.onDataChanged
    Connections {
        target: sensorDataFeeds.measurementConfigurationModel
        onCountChanged: parsingRulesChanged()
    } // sensorDataFeeds.measurementConfigurationModel.onCountChanged
    Connections {
        target: fpcMain
        onOperationsRowAdded: operationsRowAdded(id, details_id, random_drops)
    } // fpcMain.onOperationsRowAdded
    Connections {
        target: fpcMain.eventsModel
        onEventsRowAdded: eventsRowAdded(index, id)
    } // fpcMain.onEventsRowAdded
    Connections {
        target: fpcMain.eventsModel
        onEventsRowDeleted: eventsRowDeleted(index)
    } // fpcMain.onEventsRowDeleted
    Connections {
        target: fpcMain
        onBackupStatusChanged: showBackupStatus(status, msg)
    } // fpcMain.backupStatusChanged
    Connections {
        target: fpcMain
        onSoftwareTestDeleted: checkScreenReset(setId)
    }
    function checkScreenReset(setId) {
        if (setId === tfSetId.text) {
            console.info('clearing the screen since this current setId was just deleted');

            tfSetId.text = ""
            resetWidgets();
            toggleControls(false);

            var sequences = fpcMain.get_set_id_sequences();
            sequence = sequences["sequence"];
            camera_sequence = sequences["camera_sequence"];
            test_sequence = sequences["test_sequence"];
            software_test_sequence = sequences["software_test_sequence"];
        }
    }

    Component {
        id: cvsMeatballGreen
        Canvas {
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "lime"
                ctx.ellipse(width/6,height/6, 2*width/3, 2*height/3)
                ctx.fill();
            }
        }
    } // cvsMeatballGreen
    Component {
        id: cvsMeatballRed
        Canvas {
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "red"
                ctx.ellipse(width/6,height/6, 2*width/3, 2*height/3)
                ctx.fill();
            }
        }
    } // cvsMeatballRed
    Component {
        id: cvsMeatballYellow
        Canvas {
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "yellow"
                ctx.lineWidth = 1
                ctx.ellipse(width/6,height/6, 2*width/3, 2*height/3)
                ctx.fill();
            }
        }
    } // cvsMeatballYellow
    OkayDialog {
        // #199: Remind to check system time
        id: dlgGpsTime
        title: "GPS Time Reminder"
        message: "Please ensure that the galley station, cutter station, and hook matrix\n" +
                "computer times have been manually synced with the GPS time.\n\n\n" +
                "GPS date and time can be reviewed on the 'Sensor Data Feeds' page\nor directly on the GPS."
        action: ""
    }
    Component.onCompleted: {
        console.info('Component.onCompleted ...');
        dlgGpsTime.open()
        meatballs = [rctMeatball1, rctMeatball2, rctMeatball3, rctMeatball4, rctMeatball5,
                    rctMeatball6, rctMeatball7, rctMeatball8, rctMeatball9, rctMeatball10];
        tooltips = [ttMeatball1, ttMeatball2, ttMeatball3, ttMeatball4,  ttMeatball5,
                    ttMeatball6, ttMeatball7, ttMeatball8, ttMeatball9, ttMeatball10];

        var item;
        var com_port;
        var moxa_port;
        var equipment;

        for (var i=0; i < sensorDataFeeds.sensorConfigurationModel.count; i++) {
            item = sensorDataFeeds.sensorConfigurationModel.get(i);
            com_port = item.com_port;
            equipment = (item.equipment != "") ? item.equipment : ""
            moxa_port = (item.moxa_port != "") ? "MOXA " + item.moxa_port : "MOXA <blank>"

            if (i < 10) {
                meatballs[i].enabled = true
                meatballs[i].com_port = com_port;
                meatballs[i].status = "red";
                tooltips[i].text = com_port + "\n" + moxa_port + "\n" + equipment;
            }
        }

        for (var i=sensorDataFeeds.sensorConfigurationModel.count; i<10; i++) {
            meatballs[i].enabled = false
        }
        console.info('\tSensor Configuration Model retrieved and meatballs/tooltips set');

        parsing_line_starts = sensorDataFeeds.measurementConfigurationModel.line_startings

        for (var i=0; i < parsing_line_starts.length; i++) {
            var sentence_rules = sensorDataFeeds.measurementConfigurationModel.sentence_rules(parsing_line_starts[i])
            parsing_rules[parsing_line_starts[i]] = sentence_rules;
        }
        delete parsing_rules["test"]
        console.info('\tParsing rules retrieved');

        toggleControls(false);
        console.info('\tControls toggled to false');

        var sequences = fpcMain.get_set_id_sequences()
        sequence = sequences["sequence"]
        camera_sequence = sequences["camera_sequence"]
        test_sequence = sequences["test_sequence"]
        software_test_sequence = sequences["software_test_sequence"]
        console.info('\tOperation sequences obtained');


    }

    function padZero(i) {
        if (i < 10) {
            i = "0" + i;
        }
        return i;
    }

    function getChecksum(value) {
        // Reference: https://rietman.wordpress.com/2008/09/25/how-to-calculate-the-nmea-checksum/
        var checksum = 0;
        for(var i = 0; i < value.length; i++) {
            checksum = checksum ^ value.charCodeAt(i);
        }
        return checksum;
    }

    function showBackupStatus(status, msg) {
        var success = (status) ? "Success" : "Failed"
        dlgOkay.message = "Backup status: " + success + "\n\n" + msg
        dlgOkay.action = ""
        dlgOkay.open()

        toggleLiveDataStream("off");
    }

    function parseReceivedData(com_port, data) {

        if (!is_streaming)
            return

        var field, rules, value, uom;
        var data_list = data.split(",");
        for (var i=0; i < parsing_line_starts.length; i++) {
            if (data.indexOf(parsing_line_starts[i]) == 0) {
                rules = parsing_rules[parsing_line_starts[i]];
                for (var j=0; j<rules.length; j++) {
                    field = rules[j]["field_position"]-1;
                    value = data_list[field];
                    if ("function" in measurements[rules[j]["measurement"]])
                        if ((rules[j]["measurement"].toLowerCase().indexOf("latitude") >= 0) ||
                            (rules[j]["measurement"].toLowerCase().indexOf("longitude") >= 0)) {
                            uom = data_list[field+1]
                            value = measurements[rules[j]["measurement"]]["function"](value, uom);
                        } else {
                            value = measurements[rules[j]["measurement"]]["function"](value);
                        }
                    measurements[rules[j]["measurement"]]["target"].text = value ? value : "";

                    // Rebroadcast if a Depth, ftm measurement
                    if ((rules[j]["measurement"] == "Depth, ftm") & (settings.depthRebroadcastInfo["status"] == "On")) {
                        var index = sensorDataFeeds.sensorConfigurationModel.get_item_index("com_port", com_port)
                        if (index != -1) {
                            if (sensorDataFeeds.sensorConfigurationModel.get(index).equipment == "Seabird SBE39") {
                                value = parseFloat(value)
                                value = "$SDDBT," +
                                    (value*6).toFixed(2).toString() + ",f," +
                                    (value*1.8288).toFixed(2).toString() + ",M," +
                                    value.toFixed(2).toString() + ",F"
                                value = value + "*" + getChecksum(value)
                                if (serialPortManager.serialPortWriters[settings.depthRebroadcastInfo["com_port"]]) {
                                    serialPortManager.serialPortWriters[settings.depthRebroadcastInfo["com_port"]]["worker"].add_sentence(value)
                                }
                            }
                        }
                    }
                }
                break;
            }
        }
    }

    function parseSimulatedData(data) {

        if (!is_streaming) return;

        tfTime.text = data["time"] ? data["time"] : "";
        tfLatitude.text = data["latitude"] ? data["latitude"] : "";
        tfLongitude.text = data["longitude"] ? data["longitude"] : "";
        tfSpeedOverGround.text = data["sog"] ? data["sog"] : "";
        tfDriftDir.text = data["drift_dir"] ? data["drift_dir"] : "";

    }

    function parsingRulesChanged() {
        parsing_line_starts = sensorDataFeeds.measurementConfigurationModel.line_startings
        parsing_rules = {"test": ""}
        for (var i=0; i < parsing_line_starts.length; i++) {
            var sentence_rules = sensorDataFeeds.measurementConfigurationModel.sentence_rules(parsing_line_starts[i])
            parsing_rules[parsing_line_starts[i]] = sentence_rules;
        }
        delete parsing_rules["test"]
    }

    function resetMeatballs() {

        // clear all meatballs
        for (var i=0; i<10; i++) {
            meatballs[i].com_port = ""
            meatballs[i].status = ""
            meatballs[i].enabled = false;
        }

        // update per sensorDataFeeds.sensorConfigurationModel
        var item;
        var com_port;
        var moxa_port;
        var equipment;
        for (var i=0; i<sensorDataFeeds.sensorConfigurationModel.count; i++) {
            item = sensorDataFeeds.sensorConfigurationModel.get(i)
            equipment = (item.equipment != "") ? item.equipment : ""
            moxa_port = (item.moxa_port != "") ? "MOXA " + item.moxa_port : "MOXA <blank>"
            if (i<10) {
                meatballs[i].enabled = true;
                meatballs[i].com_port = item.com_port;
                meatballs[i].status = item.data_status;
                tooltips[i].text = item.com_port + "\n" + moxa_port + "\n" + equipment;
            }
        }
    }

    function changedPortDataStatus(com_port, status) {

        status = (status == "green") ? "lime" : status;
        for (var i=0; i < meatballs.length; i++) {
            if (meatballs[i].com_port == com_port) {
                meatballs[i].status = status;
                break;
            }
        }
    }

    function getMeatballColor(status) {
        switch (status) {
            case "red": return cvsMeatballRed
            case "lime": return cvsMeatballGreen
            case "green": return cvsMeatballGreen
            case "yellow": return cvsMeatballYellow
            case "": return null
            default: return cvsMeatballRed
        }
    }

    function getDropTypeIndex(row) {
//        if (row == -1) return 0
        var index = fpcMain.eventsModel.get(row).drop_type_index;
//        console.info('\t\trow: ' + row + '\t\tdrop index: ' + index)
        return (index == -1) ? 0 : index

    }

    function getIncludeInResults(row) {
        var include_in_results = fpcMain.eventsModel.get(row).include_in_results
//        console.info('\t\trow: ' + row + '\t\tinclude_in_results: ' + include_in_results)
        return (include_in_results == -1) ? true : include_in_results
    }

    function getIncludeInResultsDefault(row) {
        if (row == -1) return 0
        var include_in_results = fpcMain.eventsModel.get(row).include_in_results
//        console.info('\t\trow: ' + row + '\t\tdefault: ' + include_in_results)
        return include_in_results
    }

    function getTideTextFieldStatus(active_row, row) {
//        var start = fpcMain.eventsModel.get(row).start;
//        var end = fpcMain.eventsModel.get(row).end;
//        var delete = fpcMain.eventsModel.get(row).delete;

        return (enabled_row === row) ? true : false;

//        return (status === "enabled") ? true : false
    }

    function resetWidgets() {

//        console.info('RESETTING')
        enabled_row = -1;

        operation_id = -1;
        operation_details_id = -1;
        sequence = -1;
        camera_sequence = -1;
        test_sequence = -1;
        software_test_sequence = -1;

        // Reset all of the ComboBoxes and TextFields to empty

        // grpOverview items
        tfDate.text = getToday();
        cbSiteName.currentIndex = 0;
        cbRecordedBy.currentIndex = 0;
        cbSiteType.currentIndex = 0;
        cbIncludeInSurvey.checked = true;
        cbRca.checked = false;
        cbMpa.checked = false;

        // tvEvents - clear out the events
        var properties =
            ["event_id",
            "start_date_time", "start_latitude", "start_longitude", "start_depth_ftm",
            "tide_height_m", "end_date_time", "end_latitude", "end_longitude", "end_depth_ftm",
            "surface_temperature_c", "true_wind_speed_avg_kts", "true_wind_direction_avg_kts",
            "drift_speed_kts", "drift_direction_deg", "drift_distance_nm", "operation_id"];

        for (var i=0; i < fpcMain.eventsModel.count; i++) {
            for (var j=0; j < properties.length; j++) {
                fpcMain.eventsModel.setProperty(i, properties[j], "");
            }
//            if (i > 0) {
            if ((i > 0) & (i < fpcMain.eventsModel.count - 1)) {
                fpcMain.eventsModel.setProperty(i, "start", "disabled");
            }
            fpcMain.eventsModel.setProperty(i, "adjustTime", "disabled");
            fpcMain.eventsModel.setProperty(i, "end", "disabled");
            fpcMain.eventsModel.setProperty(i, "delete", "disabled");

            // These aren't working to automatically update the delegates, why ???
//            fpcMain.eventsModel.setProperty(i, "drop_type", "Fixed")
            fpcMain.eventsModel.setProperty(i, "drop_type_index", 0)
            fpcMain.eventsModel.setProperty(i, "drop_type_lu_id", fpcMain.dropTypesModel.get(0).id)
            fpcMain.eventsModel.setProperty(i, "include_in_results", true)
            reload_row = i;

        }

        // final items
        tfSwellHeight.text = ""
        tfSwellDirection.text = ""
        tfWaveHeight.text = ""
        cbTideType.currentIndex = 0;
        cbTideState.currentIndex = 0;
        tfCtdDepth.text = "";
        tfBottomTemperature.text = "";
        tfDO.text = "";
        tfDO2.text = "";
        tfSalinity.text = "";
        tfFluorescence.text = "";
        tfTurbidity.text = "";
        taHabitat.text = "";
        taFishMeter.text = ""
        taOceanWeather.text = "";
        taGeneral.text = "";
        lblRandomDrop1.text = "";
        lblRandomDrop2.text = "";
    }

    function toggleLiveDataStream(status) {

        var isSoftwareTest = fpcMain.check_sequence_type(tfSetId.text.substring(2,4));

        if (status == "on") {
            btnSensorDataFeeds.iconSource = "qrc:/resources/images/lightning_green.png";
            if (isSoftwareTest) {
                console.info('software test, generate some bogus data...');
                serialPortSimulator.start();
            } else {
                serialPortManager.start_all_threads();
            }
            is_streaming = true;

        } else if (status == "off") {

            if (isSoftwareTest) {
                serialPortSimulator.stop();
            }

            btnSensorDataFeeds.iconSource = "qrc:/resources/images/lightning_yellow.png";
            tfTime.text = "";
            tfLatitude.text = "";
            tfLongitude.text = "";
            tfDepth.text = "";
            tfSST.text = "";
            tfRelWindSpeed.text = "";
            tfRelWindDir.text = "";
            tfSpeedOverGround.text = "";
            tfDriftDir.text = "";
            is_streaming = false;
        }
    }

    function toggleControls(status) {
        // Function to enable/disable controls based on if a new Operations record is set
        cbSiteName.enabled = status;
        cbRecordedBy.enabled = status;
        cbSiteType.enabled = status;
        cbIncludeInSurvey.enabled = status;
        cbRca.enabled = status;
        cbMpa.enabled = status;

        tvEvents.enabled = status;
        grpSeaState.enabled = status;
        grpTide.enabled = status;
        grpCtd.enabled = status;
        grpComments.enabled = status;
    }

    function operationsRowAdded(id, details_id, random_drops) {

        enabled_row = -1;

        resetWidgets();
        toggleControls(true);

        var sequences = fpcMain.get_set_id_sequences();
        sequence = sequences["sequence"];
        camera_sequence = sequences["camera_sequence"];
        test_sequence = sequences["test_sequence"];
        software_test_sequence = sequences["software_test_sequence"];

        operation_id = id;
        operation_details_id = details_id;

        // Populate the random drops in the General Comments Section
        lblRandomDrop1.text = random_drops[0];
        lblRandomDrop2.text = random_drops[1];
    }

    function eventsRowAdded(index, id) {

        // This function is called when a new event is added, to adjust the start/play/delete
        // buttons to enabled or disabled as appropriate
        enabled_row = index;

        // If the CTD Drop, then disable the start/stop/delete buttons of
        // the first five drops
        if (index == fpcMain.eventsModel.count-1) {
            for (var i=0; i < fpcMain.eventsModel.count - 1; i++) {
                fpcMain.eventsModel.setProperty(i, "start", "disabled");
                fpcMain.eventsModel.setProperty(i, "end", "disabled");
                fpcMain.eventsModel.setProperty(i, "delete", "disabled");
            }
        }
    }

    function eventsRowDeleted(index) {
        if (index > 0) {
            enabled_row = index-1;
        }

        // If the CTD drop event is deleted, then re-enable the last row
        // that has some data
        if (index == fpcMain.eventsModel.count - 1) {
            var item;
            for (var i=fpcMain.eventsModel.count-2; i >= 0; i--) {
                item = fpcMain.eventsModel.get(i);
                if ((item.end_date_time != "") & (item.end_date_time != undefined)) {
                    fpcMain.eventsModel.setProperty(i, "start", "disabled")
                    fpcMain.eventsModel.setProperty(i, "end", "disabled")
                    fpcMain.eventsModel.setProperty(i, "delete", "enabled")
                    fpcMain.eventsModel.setProperty(i+1, "start", "enabled")
                    break;
                } else if ((item.start_date_time != "") & (item.start_date_time != undefined)) {
                    fpcMain.eventsModel.setProperty(i, "start", "disabled")
                    fpcMain.eventsModel.setProperty(i, "end", "enabled")
                    fpcMain.eventsModel.setProperty(i, "delete", "enabled")
                    break;
                } else {
                    fpcMain.eventsModel.setProperty(i, "start", "disabled")
                    fpcMain.eventsModel.setProperty(i, "end", "disabled")
                    fpcMain.eventsModel.setProperty(i, "delete", "disabled")
                }
            }
        }
    }

    function getToday() {
        var now = new Date();
        return now.getMonth()+1 + "/" + now.getDate() + "/" + now.getFullYear();
    }

    function loadOperation(id) {
        resetWidgets()

        var data = fpcMain.get_site_data(id);

        // Reset the major variables for controlling the state of the screen
        enabled_row = -1;
        toggleControls(true);
        operation_id = id;
        operation_details_id = data["operation_details"]["operation_details"]

        // grpOverview
        var operation = data["operation"];
//        console.info('operation: ' + JSON.stringify(operation))

        // Row 1 - Do not reset tfArea.text as this is already controlled by cbSiteName.currentIndex
        tfVessel.text = operation["vessel_name"];
        tfDayOfCruise.text = operation["day_of_cruise"];
        tfFpc.text = operation["fpc"]["last_name"] + ", " + operation["fpc"]["first_name"];
        tfDate.text = operation["date"];

        // Row 2
        tfSetId.text = operation["operation_number"] ? operation["operation_number"] : "";
        cbSiteName.currentIndex = operation["site_name"] ? cbSiteName.find(operation["site_name"]) : 0;
        cbRecordedBy.currentIndex = operation["recorder"] ? cbRecordedBy.find(operation["recorder"]) : 0;
        cbSiteType.currentIndex = operation["site_type"] ? cbSiteType.find(operation["site_type"]) : 0;
        cbIncludeInSurvey.checked = operation["include_in_survey"] ? operation["include_in_survey"] : true;
        cbRca.checked = operation["is_rca"] ? operation["is_rca"] : false;
        cbMpa.checked = operation["is_mpa"] ? operation["is_mpa"] : false;

        // tvEvents
        var events = data["events"];
        var event;
        var row = -1;
        var last_row_with_data = -1;
        var update_keys = ["start_date_time", "start_latitude", "start_longitude", "start_depth_ftm",
                            "end_date_time", "end_latitude", "end_longitude", "end_depth_ftm",
                            "tide_height_m"] //, "drop_type"]
        var event_types = {0: "Drop 1", 1: "Drop 2", 2: "Drop 3",
                            3: "Drop 4", 4: "Drop 5", 5: "CTD"};

//        console.info('POPULATING EVENTS')
        for (var row=0; row < tvEvents.model.count; row++) {
            if (event_types[row] in events) {
                event = events[event_types[row]];
//                console.info('event: ' + JSON.stringify(event));
                for (var i=0; i < update_keys.length; i++) {
                    var update_key = update_keys[i];
                    if (update_key in event) {
                        fpcMain.eventsModel.setProperty(row, update_key, event[update_key])
                    }
                }

                // Update the drop_type_index, this changes the Drop Type ComboBox for each event
//                var drop_type_index = fpcMain.dropTypesModel.get_item_index("text", event["drop_type"])
                fpcMain.eventsModel.setProperty(row, "drop_type_index", event["drop_type_index"])
                fpcMain.eventsModel.setProperty(row, "include_in_results", event["include_in_results"])

                // Update items where the model name is different than the DB column (diff of _id)
                fpcMain.eventsModel.setProperty(row, "operation_id", operation["operation"])
                fpcMain.eventsModel.setProperty(row, "event_id", event["event"])
                fpcMain.eventsModel.setProperty(row, "event_type_lu_id", event["event_type_lu"])
                fpcMain.eventsModel.setProperty(row, "drop_type_lu_id", event["drop_type_lu"])

                // Enable the adjustTime item, for all rows that have at least a start waypoint captured
                fpcMain.eventsModel.setProperty(row, "adjustTime", "enabled")

                // Initiate reloading of the cbDropType and cbIncludeInResults widgets
                reload_row = row;

                last_row_with_data = row;
            }

            // Disable all of the action buttons - start  / end / delete
            fpcMain.eventsModel.setProperty(row, "start", "disabled")
            fpcMain.eventsModel.setProperty(row, "end", "disabled")
            fpcMain.eventsModel.setProperty(row, "delete", "disabled")
//            fpcMain.eventsModel.setProperty(row, "adjustTime", "disabled")
        }

       // Enable the proper tvEvents row based upon what events were returned
        if (last_row_with_data == -1) {  // No events captured, enabled first row, start button only

            fpcMain.eventsModel.setProperty(0, "start", "enabled")
            enabled_row = 0;

        } else {                        // One of the rows 0 - 5 should be active

            var item = fpcMain.eventsModel.get(last_row_with_data)

            // Enable the adjustTime as this will work for the two cases:  start-only exists or start+end exist
//            fpcMain.eventsModel.setProperty(last_row_with_data, "adjustTime", "enabled")

            if ((item.end_date_time != null) & (item.end_date_time != "")) {   // Start + End Exist
                fpcMain.eventsModel.setProperty(last_row_with_data, "delete", "enabled")
                if (last_row_with_data != 5)
                    fpcMain.eventsModel.setProperty(last_row_with_data+1, "start", "enabled")
            } else if ((item.start_date_time != null) & (item.start_date_time != "")) {  // Start only Exists
                fpcMain.eventsModel.setProperty(last_row_with_data, "end", "enabled")
                fpcMain.eventsModel.setProperty(last_row_with_data, "delete", "enabled")
            }

            enabled_row = last_row_with_data

        }

        // ADDED To enable CTD Drop Always
        if (last_row_with_data != fpcMain.eventsModel.count-1) {
            fpcMain.eventsModel.setProperty(fpcMain.eventsModel.count-1, "start", "enabled")
        }

        // OperationDetails data
        var operation_details = data["operation_details"];
//        console.info('operation_details: ' + JSON.stringify(operation_details));

        // grpSeaState
        tfSwellHeight.text = operation_details["swell_height_ft"]
        tfSwellDirection.text = operation_details["swell_direction_deg"]
        tfWaveHeight.text = operation_details["wave_height_ft"]

        // grpTides - Do not reset tfStation.text or tfDistance.text as these are controlled by cbSiteName.currentIndex already
        cbTideType.currentIndex = operation_details["tide_type"] ? cbTideType.find(operation_details["tide_type"]) : 0
        cbTideState.currentIndex = operation_details["tide_state"] ? cbTideState.find(operation_details["tide_state"]) : 0

        // grpMoon - currently empty

        // grpCtd
        tfCtdDepth.text = operation_details["ctd_depth_m"]
        tfBottomTemperature.text = operation_details["ctd_bottom_temp_c"];
        tfDO.text = operation_details["ctd_do2_sbe43_ml_per_l"]
        tfDO2.text = operation_details["ctd_do2_aanderaa_ml_per_l"]

        tfSalinity.text = operation_details["ctd_salinity_psu"]
        tfFluorescence.text = operation_details["ctd_fluorescence_ug_per_l"]
        tfTurbidity.text = operation_details["ctd_turbidity_ntu"];

        // grpComments
        taGeneral.text = operation_details["general_comments"]
        taFishMeter.text = operation_details["fish_meter_comments"]
        taOceanWeather.text = operation_details["ocean_weather_comments"]
        taHabitat.text = operation_details["habitat_comments"]

        // grpRandomDrops
        lblRandomDrop1.text = operation["random_drop_1"];
        lblRandomDrop2.text = operation["random_drop_2"];
    }

    GroupBox {
        id: grpOverview
        x: 8
        y: 13
        width: parent.width - 20
        height: 71
        title: qsTr("Site Overview")
        z: 1
        visible: true
        style: Style {
            property Component panel: Rectangle {
                color: "transparent"
                border.width: 1
                Rectangle {
                    height: txtObj.height + 10
                    width: txtObj.width + 10
                    x: txtObj.x - 5
                    y: txtObj.y - 5
                    color: SystemPaletteSingleton.window(true)
                }
                Text {
                    id: txtObj
                    anchors.verticalCenter: parent.top
                    x: 10
                    text: control.title
                    font.pixelSize: 14
                }
            }
        }

        GridLayout {
            id: glOverview
            x: 10
            y: 10
            rows: 2
            columns: 14
            columnSpacing: 20
            rowSpacing: 10
            Label {
                id: lblVessel
                text: qsTr("Vessel")
            } // lblVessel
            TextField {
                id: tfVessel
                enabled: false
//                text: qsTr("Toronado")
                text: fpcMain.vesselName
                Layout.preferredWidth: 100
                Layout.preferredHeight: 20
            } // tfVessel

            Label {
                id: lblDayOfCruise
                width: 86
                height: 13
                text: qsTr("Day of Cruise")
            } // lblDayOfCruise
            TextField {
                id: tfDayOfCruise
                enabled: false
                Layout.preferredWidth: 80
                Layout.preferredHeight: 20
                text: fpcMain.dayOfCruise
            } // tfDayOfCruise

            Label {
                id: lblArea
                text: qsTr("Area")
            } // lblArea
            TextField {
                id: tfArea
                Layout.preferredWidth: 160
                enabled: false
                text: (cbSiteName.currentIndex == 0) ? "" : fpcMain.sitesModel.get(cbSiteName.currentIndex)["area_description"]
            } // tfArea

            Label {
                id: lblFpc
                width: 86
                height: 13
                text: qsTr("FPC")
            } // lblFpc
            TextField {
                id: tfFpc
                enabled: false
                text: fpcMain.fpcName
                Layout.preferredWidth: 140
                Layout.preferredHeight: 20
            } // tfFpc

            Label {
                id: lblDate
                width: 86
                height: 13
                text: qsTr("Date")
            } // lblDate
            TextField {
                id: tfDate
                enabled: false
                Layout.preferredWidth: 80
                Layout.preferredHeight: 20
                text: getToday()
            } // tfDate

            Label {}
            Label {}
            Label {}
            Label {}

            Label {
                id: lblSetId
                text: qsTr("Set ID")
            } // lblSetId
            TextField {
                id: tfSetId
                Layout.preferredWidth: 100
                Layout.preferredHeight: 20
                text: qsTr("")
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        this.cursorShape = Qt.IBeamCursor;
//                        var vessel = fpcMain.vesselId + " - " + fpcMain.vesselName;
//                        dlgSetId.cbVesselNumber.currentIndex =
//                            dlgSetId.cbVesselNumber.find(vessel);
                        dlgSetId.day_of_cruise = tfDayOfCruise.text;
                        dlgSetId.date = tfDate.text;
                        dlgSetId.include_in_survey = cbIncludeInSurvey.checked;
                        dlgSetId.is_mpa = cbMpa.checked;
                        dlgSetId.is_rca = cbRca.checked;

                        dlgSetId.sequence = sequence;
                        dlgSetId.camera_sequence = camera_sequence;
                        dlgSetId.test_sequence = test_sequence;
                        dlgSetId.software_test_sequence = software_test_sequence;
                        dlgSetId.open()
                    }
                }
            } // tfSetId

            Label {
                id: lblSiteName
                text: qsTr("Site Name")
            } // lblSiteName
            ComboBox {
                id: cbSiteName
                currentIndex: 0
                model: fpcMain.sitesModel
                onCurrentIndexChanged: {
                    if (currentIndex != 0) {

                        var items = [{"field": "site", "value": fpcMain.sitesModel.get(currentIndex).site},
                                    {"field": "area", "value": fpcMain.sitesModel.get(currentIndex).area_description}]

//                        console.info('currentIndex: ' + currentIndex + '\n\t\t\titems: ' + JSON.stringify(items))

                        fpcMain.update_table_row("Operations", operation_id, items);

                        items = [{"field": "tide_station", "value": fpcMain.getTideStation(currentIndex, "id")},
                                {"field": "distance_to_tide_station_nm",
                                    "value": fpcMain.getDistanceToTideStation(currentIndex)}]
                        fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                    }
                }
            } // cbSiteName

            Label {
                id: lblRecordBy
                width: 86
                height: 13
                text: qsTr("Recorded By")
            } // lblRecordedBy
            ComboBox {
                id: cbRecordedBy
                Layout.preferredWidth: 160
                Layout.preferredHeight: 20
                model: fpcMain.personnelModel
                onCurrentIndexChanged: {
                    if (currentIndex != 0) {
                        var items = [{"field": "recorder", "value": fpcMain.personnelModel.get(currentIndex).id}]
                        fpcMain.update_table_row("Operations", operation_id, items);
                    }
                }
            } // cbRecordedBy

            Label {
                id: lblSiteType
                width: 86
                height: 13
                text: qsTr("Site Type")
            } // lblSiteType
            ComboBox {
                id: cbSiteType
                width: 120
                height: 20
                currentIndex: 0
                model: fpcMain.siteTypesModel
                onCurrentIndexChanged: {
                    if (currentIndex != 0) {
                        var items = [{"field": "site_type_lu", "value": fpcMain.siteTypesModel.get(currentIndex).id}]
                        fpcMain.update_table_row("Operations", operation_id, items);
                    }
                }
            } // cbSiteType

            Label {
                id: lblIncludeInSurvey
                width: 86
                height: 13
                text: qsTr("Include in Survey?")
            } // lblIncludeInSurvey
            CheckBox {
                id: cbIncludeInSurvey
                checked: true
                text: ""
                onClicked: {
                    var items = [{"field": "include_in_survey", "value": checked}]
                    fpcMain.update_table_row("Operations", operation_id, items);
                }
            } // cbIncludeInSurvey

            Label {
                id: lblInRca
                Layout.preferredWidth: 15
                text: qsTr("RCA ?")
            } // lblInRca
            CheckBox {
                id: cbRca
                Layout.preferredWidth: 20
                text: ""
                onClicked: {
                    var items = [{"field": "is_rca", "value": checked}]
                    fpcMain.update_table_row("Operations", operation_id, items);
                }
            } // cbRca

            Label {
                id: lblMPA
                Layout.preferredWidth: 15
                text: qsTr("MPA ?")
            } // lblMPA
            CheckBox {
                id: cbMpa
                Layout.preferredWidth: 10
                text: ""
                onClicked: {
                    var items = [{"field": "is_mpa", "value": checked}]
                    fpcMain.update_table_row("Operations", operation_id, items);
                }
            } // cbMpa
        }
    } // grpOverview
    GroupBox {
        id: grpLiveData
        title: qsTr("Live Data")
        anchors.left: grpOverview.left
        anchors.top: grpOverview.bottom
        anchors.topMargin: 20
        width: parent.width - 20
        height: 80
        visible: true

        style: Style {
            property Component panel: Rectangle {
                color: "transparent"
                border.width: 1
                Rectangle {
                    height: txtObj.height + 10
                    width: txtObj.width + 10
                    x: txtObj.x - 5
                    y: txtObj.y - 5
                    color: SystemPaletteSingleton.window(true)
                }
                Text {
                    id: txtObj
                    anchors.verticalCenter: parent.top
                    x: 10
                    text: control.title
                    font.pixelSize: 14
                }
            }
        }

        RowLayout {
            id: rlDataStream
            x: 10
            y: 20
            spacing: 20
            Button {
                id: btnSensorDataFeeds
                Layout.preferredWidth: 40
                Layout.preferredHeight: 40
                iconSource: "qrc:/resources/images/lightning_yellow.png"
                tooltip: "Start Sensor Data Feeds"
                onClicked: {
                    var status = (iconSource == "qrc:/resources/images/lightning_yellow.png") ?
                        "on" : "off"
                    toggleLiveDataStream(status);
                }
            } // btnSensorDataFeeds
            GridLayout {
                id: glDataStream
                rows: 2
                columns: 9
                columnSpacing: 20
                flow: GridLayout.TopToBottom
                Label {
                    id: lblTime
                    text: "Time"
                } // lblTime
                TextField {
                    id: tfTime
                    readOnly: true
                    text: ""
                    Layout.preferredWidth: 80
                } // tfTime
                Label {
                    id: lblLatitude
                    text: "Latitude"
                } // lblLatitude
                TextField {
                    id: tfLatitude
                    readOnly: true
                    text: ""
                    Layout.preferredWidth: 120
                } // tfLatitude
                Label {
                    id: lblLongitude
                    text: "Longitude"
                } // lblLongitude
                TextField {
                    id: tfLongitude
                    readOnly: true
                    text: ""
                    Layout.preferredWidth: 120
                } // tfLongitude
                Label {
                    id: lblDepth
                    text: "Depth (ftm)"
                } // lblDepth
                TextField {
                    id: tfDepth
                    readOnly: true
                    text: ""
                    Layout.preferredWidth: 80
                } // tfDepth
                Label {
                    id: lblSST
                    text: "SST (C)"
                } // lblSST
                TextField {
                    id: tfSST
                    readOnly: true
                    text: ""
                    Layout.preferredWidth: 80
                } // tfSST
                Label {
                    id: lblRelWindSpeed
                    text: "Rel Wind Speed (kts)"
                } // lblRelWindSpeed
                TextField {
                    id: tfRelWindSpeed
                    readOnly: true
                    text: ""
                    Layout.preferredWidth: 80
                } // tfRelWindSpeed
                Label {
                    id: lblRelWindDir
                    text: "Rel Wind Dir (deg)"
                } // lblRelWindDir
                TextField {
                    id: tfRelWindDir
                    readOnly: true
                    text: ""
                    Layout.preferredWidth: 80
                } // tfRelWindDir
                Label {
                    id: lblSpeedOverGround
                    text: "SOG (kts)"
                } // lblSpeedOverGround
                TextField {
                    id: tfSpeedOverGround
                    readOnly: true
                    text: ""
                    Layout.preferredWidth: 80
                } // tfSpeedOverGround
                Label {
                    id: lblDriftDir
                    text: "Drift Dir (deg)"
                } // lblDriftDir
                TextField {
                    id: tfDriftDir
                    readOnly: true
                    text: ""
                    Layout.preferredWidth: 80
                } // tfDriftDir
            } // glDataStream
        } // rlDataStream
        GridLayout {
            id: glMeatballs
            anchors.left: rlDataStream.right
            anchors.leftMargin: 20
            anchors.verticalCenter: parent.verticalCenter
            columns: 5
            rows: 2
            columnSpacing: 0
            rowSpacing: 5
            Rectangle {
                id: rctMeatball1
                property string com_port: ""
                property string status: ""
                width: 30; height: 30;
                color: SystemPaletteSingleton.window(true)
                Loader {
                    anchors.fill: parent
                    sourceComponent: getMeatballColor(parent.status)
                }
            } // rctMeatball1
            Rectangle {
                id: rctMeatball2
                property string com_port: ""
                property string status: ""
                width: 30; height: 30;
                color: SystemPaletteSingleton.window(true)
                Loader {
                    anchors.fill: parent
                    sourceComponent: getMeatballColor(parent.status)
                }
            } // rctMeatball2
            Rectangle {
                id: rctMeatball3
                property string com_port: ""
                property string status: ""
                width: 30; height: 30;
                color: SystemPaletteSingleton.window(true)
                Loader {
                    anchors.fill: parent
                    sourceComponent: getMeatballColor(parent.status)
                }
            } // rctMeatball3
            Rectangle {
                id: rctMeatball4
                property string com_port: ""
                property string status: ""
                width: 30; height: 30;
                color: SystemPaletteSingleton.window(true)
                Loader {
                    anchors.fill: parent
                    sourceComponent: getMeatballColor(parent.status)
                }
            } // rctMeatball4
            Rectangle {
                id: rctMeatball5
                property string com_port: ""
                property string status: ""
                width: 30; height: 30;
                color: SystemPaletteSingleton.window(true)
                Loader {
                    anchors.fill: parent
                    sourceComponent: getMeatballColor(parent.status)
                }
            } // rctMeatball5
            Rectangle {
                id: rctMeatball6
                property string com_port: ""
                property string status: ""
                width: 30; height: 30;
                color: SystemPaletteSingleton.window(true)
                Loader {
                    anchors.fill: parent
                    sourceComponent: getMeatballColor(parent.status)
                }
            } // rctMeatball6
            Rectangle {
                id: rctMeatball7
                property string com_port: ""
                property string status: ""
                width: 30; height: 30;
                color: SystemPaletteSingleton.window(true)
                Loader {
                    anchors.fill: parent
                    sourceComponent: getMeatballColor(parent.status)
                }
            } // rctMeatball7
            Rectangle {
                id: rctMeatball8
                property string com_port: ""
                property string status: ""
                width: 30; height: 30;
                color: SystemPaletteSingleton.window(true)
                Loader {
                    anchors.fill: parent
                    sourceComponent: getMeatballColor(parent.status)
                }
            } // rctMeatball8
            Rectangle {
                id: rctMeatball9
                property string com_port: ""
                property string status: ""
                width: 30; height: 30;
                color: SystemPaletteSingleton.window(true)
                Loader {
                    anchors.fill: parent
                    sourceComponent: getMeatballColor(parent.status)
                }
            } // rctMeatball9
            Rectangle {
                id: rctMeatball10
                property string com_port: ""
                property string status: ""
                width: 30; height: 30;
                color: SystemPaletteSingleton.window(true)
                Loader {
                    anchors.fill: parent
                    sourceComponent: getMeatballColor(parent.status)
                }
            } // rctMeatball10
        } // glMeatballs
    } // grpLiveData
    TableView {
        id: tvEvents
        anchors.top: grpLiveData.bottom
        anchors.topMargin: 20
        anchors.left: grpOverview.left
        width: parent.width - 2 * grpOverview.x
        height: 231
        selectionMode: SelectionMode.NoSelection
        model: fpcMain.eventsModel

        TableViewColumn {
            role: "delete"
            title: "Delete"
            width: 45
            delegate: Item {
                Button {
                    width: 25
                    height: 25
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    enabled: styleData.value == "enabled" ? true : false
                    onClicked: {
                        var event_id = tvEvents.model.get(styleData.row).event_id;
                        if (event_id != undefined) {
                            var start_or_end = tvEvents.model.get(styleData.row).end == "enabled" ? "start" : "end"

                            dlgOkayCancel.title = "Delete Event"
                            dlgOkayCancel.message = "You are about to delete the following event:"
                            dlgOkayCancel.value = tvEvents.model.get(styleData.row).event + " " + start_or_end
                            dlgOkayCancel.action = "Do you wish to delete this event?"
                            dlgOkayCancel.accepted_action = "delete event"
                            dlgOkayCancel.row = styleData.row;
                            dlgOkayCancel.start_or_end = start_or_end;
                            dlgOkayCancel.open()
                        }
                    }
                    style: ButtonStyle {
                        label: Item {
                            Canvas {
                                anchors.fill: parent
                                onPaint: {
                                    var ctx = getContext("2d");
                                    ctx.lineWidth = 3;
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
                }
            }
        } // delete
        TableViewColumn {
            role: "adjustTime"
            title: "Adjust\nTime"
            width: 45
            delegate: Item {
                Button {
                    width: 25
                    height: 25
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    enabled: styleData.value == "enabled" ? true : false
                    onClicked: {
                        var event_id = tvEvents.model.get(styleData.row).event_id;
                        if (event_id != undefined) {
                            var row = tvEvents.model.get(styleData.row)
                            dlgAdjustTime.event = row.event;
                            dlgAdjustTime.row = styleData.row;
                            dlgAdjustTime.startTimeCurrent = row.start_date_time
                            dlgAdjustTime.startTimeNew = row.start_date_time
                            dlgAdjustTime.startTimeChange = "00:00"

                            console.info('row.end_date_time = ' + row.end_date_time);
                            if (row.end_date_time !== undefined) {
                                dlgAdjustTime.endTimeCurrent = row.end_date_time
                                dlgAdjustTime.endTimeNew = row.end_date_time
                                dlgAdjustTime.endTimeChange = "00:00"
                            } else {
                                var elems = row.start_date_time.split(":");
                                var newDate = new Date();

                                console.info('elems = ' + JSON.stringify(elems));
                                newDate.setHours(parseInt(elems[0]), parseInt(elems[1]), parseInt(elems[2]));
                                newDate.setMinutes(newDate.getMinutes() + 5);
//                                console.info('newDate: ' + newDate);
//                                console.info('hours = ' + newDate.getHours() + ', min = ' + newDate.getMinutes() +
//                                    ', sec = ' + newDate.getSeconds());
                                dlgAdjustTime.endTimeNew = padZero(newDate.getHours()) + ":" +
                                    padZero(newDate.getMinutes()) + ":" +
                                    padZero(newDate.getSeconds());
                                dlgAdjustTime.endTimeCurrent = dlgAdjustTime.endTimeNew;
                                dlgAdjustTime.endTimeChange = "00:00"
                            }

                            if (styleData.row > 0) {
                                if (tvEvents.model.get(styleData.row-1).end_date_time !== undefined) {
                                    dlgAdjustTime.previous_end = tvEvents.model.get(styleData.row-1).end_date_time;

                                }
                            }
                            var startTime = null;

                            console.info('row = ' + styleData.row + ', count = ' + tvEvents.model.count);
                            if (styleData.row+1 < tvEvents.model.count) {
                                for (var i=styleData.row+1; i<tvEvents.model.count; i++) {
                                    startTime = tvEvents.model.get(i).start_date_time
                                    if (startTime.length === 8) {
                                        dlgAdjustTime.next_start = tvEvents.model.get(i).start_date_time
                                        dlgAdjustTime.next_waypoint_name = tvEvents.model.get(i).event;
                                        break;
                                    }
                                }
                            } else if (styleData.row === tvEvents.model.count-1) {
                                dlgAdjustTime.next_waypoint_name = "";
//                                dlgAdjustTime.next_waypoint_name = tvEvents.model.get(styleData.row).event;
                            }

                            console.info('start: ' + dlgAdjustTime.startTimeCurrent + ',    end: ' +
                                dlgAdjustTime.endTimeCurrent + ' >>> previous_end: ' + dlgAdjustTime.previous_end +
                                 ' >>> next_start: ' + dlgAdjustTime.next_start +
                                 '  -----> next_waypoint_name: ' + dlgAdjustTime.next_waypoint_name);

                            dlgAdjustTime.sldStartTime.value = 0
                            dlgAdjustTime.sldEndTime.value = 0

                            dlgAdjustTime.open()
                        }
                    }
                    style: ButtonStyle {
                        label: Item {
                            Canvas {
                                anchors.fill: parent
                                onPaint: {
                                    var ctx = getContext("2d");
                                    ctx.lineWidth = 3;
                                    ctx.strokeStyle = Qt.rgba(0, 0, 0, 1);
                                    ctx.beginPath();
                                    ctx.moveTo(-1, height/2);
                                    ctx.lineTo(width+1, height/2);
                                    ctx.stroke();

                                    ctx.lineWidth = 2;
                                    ctx.beginPath();
                                    ctx.moveTo(0, height/2);
                                    ctx.lineTo(6*width/16, 3*height/4);
                                    ctx.stroke();

                                    ctx.beginPath();
                                    ctx.moveTo(0, height/2);
                                    ctx.lineTo(6*width/16, height/4);
                                    ctx.stroke();

                                    ctx.beginPath();
                                    ctx.moveTo(width, height/2);
                                    ctx.lineTo(10*width/16, 3*height/4);
                                    ctx.stroke();

                                    ctx.beginPath();
                                    ctx.moveTo(width, height/2);
                                    ctx.lineTo(10*width/16, height/4);
                                    ctx.stroke();

                                }
                            }
                        }
                    }
                }
            }
        } // adjustTime
        TableViewColumn {
            role: "event"
            title: "Event"
            width: 50
        } // event
        TableViewColumn {
            id: tvcStart
            role: "start"
            title: "Start"
            width: 45
            delegate: Item {
                Button {
                    property variant value: styleData.value
                    width: 25
                    height: 25
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    enabled: styleData.value == "enabled" ? true : false
                    onClicked: {
                        if ((tfTime.text != "") & (tfLatitude.text != "") & (tfLongitude.text != "")) {
                            var item = {}
                            item["event_type_lu_id"] = tvEvents.model.get(styleData.row).event_type_lu_id;
                            item["start_date_time"] = tfTime.text;
                            item["start_latitude"] = tfLatitude.text;
                            item["start_longitude"] = tfLongitude.text;
                            item["start_depth_ftm"] = tfDepth.text == "" ? null : parseFloat(tfDepth.text);
                            item["drop_type_lu_id"] = tvEvents.model.get(styleData.row).drop_type_lu_id;
                            item["include_in_results"] = tvEvents.model.get(styleData.row).include_in_results;
                            item["operation_id"] = operation_id;
                            fpcMain.eventsModel.update_row(styleData.row, item);
                        } else {
                            dlgOkay.message = "You must have live data streaming to capture an event"
                            dlgOkay.value = "Click the lightning bolt to start live data streaming"
                            dlgOkay.action = ""
                            dlgOkay.open()
                        }
                    }
                    style: ButtonStyle {
                        label: Item {
                            Canvas {
                                anchors.fill: parent
                                onPaint: {
                                    var ctx = getContext("2d");
                                    ctx.clearRect(0, 0, width, height)
                                    ctx.fillStyle = "green";
                                    ctx.beginPath();
                                    ctx.moveTo(width/4, height/4);
                                    ctx.lineTo(3*width/4, height/2);
                                    ctx.lineTo(width/4, 3*height/4);
                                    ctx.lineTo(width/4, height/4);
                                    ctx.fill();
                                }
                            }
                        }
                    }
                }
            }
        } // start
        TableViewColumn {
            role: "end"
            title: "End"
            width: 45
            delegate: Item {
                Button {
                    width: 25
                    height: 25
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    enabled: styleData.value == "enabled" ? true : false
                    onClicked: {
                        if ((tfTime.text != "") & (tfLatitude.text != "") & (tfLongitude.text != "")) {
                            var item = {}
                            item["end_date_time"] = tfTime.text
                            item["end_latitude"] = tfLatitude.text
                            item["end_longitude"] = tfLongitude.text
                            item["end_depth_ftm"] = tfDepth.text == "" ? null : parseFloat(tfDepth.text);
                            fpcMain.eventsModel.update_row(styleData.row, item);
                        } else {
                            dlgOkay.message = "You must have live data streaming to capture an event"
                            dlgOkay.value = "Click the lightning bolt to start live data streaming"
                            dlgOkay.action = ""
                            dlgOkay.open()
                        }
                    }
                    style: ButtonStyle {
                        label: Item {
                            Canvas {
                                anchors.fill: parent
                                onPaint: {
                                    var ctx = getContext("2d");
                                    ctx.clearRect(0, 0, width, height)
                                    ctx.fillStyle = "red";
                                    ctx.fillRect(width/4, height/4, width/2, height/2)
                                    ctx.fill();
                                }
                            }
                        }
                    }

                }
            }
        } // end
        TableViewColumn {
            role: "start_date_time"
            title: "Start\nTime"
            width: 60
        } // start_date_time
        TableViewColumn {
            role: "start_latitude"
            title: "Start Lat"
            width: 80
            delegate: Text {
                text: ((styleData.value !== undefined) && (styleData.value !== null))  ? styleData.value : ""
                font.pixelSize: 11
                verticalAlignment: Text.AlignVCenter
                renderType: Text.NativeRendering;
            }
        } // start_latitude
        TableViewColumn {
            role: "start_longitude"
            title: "Start Lon"
            width: 90
            delegate: Text {
//                text: styleData.value !== null ? styleData.value : ""
                text: ((styleData.value !== undefined) && (styleData.value !== null))  ? styleData.value : ""
                font.pixelSize: 11
                verticalAlignment: Text.AlignVCenter
                renderType: Text.NativeRendering;
            }
        } // start_longitude
        TableViewColumn {
            role: "start_depth_ftm"
            title: "Start\nDepth"
            width: 60
            delegate: Text {
//                text: (typeof styleData.value == 'number') ? styleData.value.toFixed(3) : ""
//                text: (styleData.value !== undefined) ? ((styleData.value !== "None") ? styleData.value : "") : ""
                text: ((styleData.value !== undefined) && (styleData.value !== null))  ? styleData.value : ""
                font.pixelSize: 11
                verticalAlignment: Text.AlignVCenter
                renderType: Text.NativeRendering;
            }
        } // start_depth_ftm
        TableViewColumn {
            id: tvcTideHeight
            role: "tide_height_m"
            title: "Tide\nHeight"
            width: 50
            delegate: Item {
                TextField {
//                    property bool status: tvEvents.model.get(styleData.row).start
                    width: parent.width
                    anchors.verticalCenter: parent.verticalCenter
//                    enabled: (enabled_row == styleData.row) ? true : false
//                    enabled: true
//                    enabled: (fpcMain.eventsModel.get(styleData.row).start_date_time != "") ? true : false
                    enabled: getTideTextFieldStatus(enabled_row, styleData.row)
                    text: styleData.value ? styleData.value : ""
//                    inputMask: "##.#"
//                    validator: DoubleValidator {
//                        bottom: -2.0;
//                        top: 10.0;
//                        decimals: 1;
//                        notation: DoubleValidator.StandardNotation
//                    }

                    maximumLength: 4
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.IBeamCursor
                        onClicked: {
                            if (!parent.activeFocus) parent.forceActiveFocus();
                            parent.selectAll();
                        }
                    }
                    onEditingFinished: {
                        var value = parseFloat(text);
                        if ((value < -2.0) || (value > 10.0)) {
                            dlgOkay.message = "You entered:"
                            dlgOkay.value = text
                            dlgOkay.action = "Please enter a value between -2.0 <= x <= 10.0"
                            dlgOkay.accepted_action = "tide_height_m"
                            dlgOkay.open()
//                            text = ""
                            return;
                        }
                        var item = {};
                        item["tide_height_m"] = value;
                        fpcMain.eventsModel.update_row(styleData.row, item);
                    }
//                    MouseArea {
//                        anchors.fill: parent
//                        cursorShape: Qt.IBeamCursor
//                        onClicked: {
//                            if (!parent.activeFocus) parent.forceActiveFocus();
//                            parent.cursorPosition = 0;
//                        }
//                    }
                }
            }
        } // tide_height_m
        TableViewColumn {
            role: "end_date_time"
            title: "End\nTime"
            width: 60
        } // end_date_time
        TableViewColumn {
            role: "end_latitude"
            title: "End Lat"
            width: 80
            delegate: Text {
                text: ((styleData.value !== undefined) && (styleData.value !== null))  ? styleData.value : ""
                font.pixelSize: 11
                verticalAlignment: Text.AlignVCenter
                renderType: Text.NativeRendering;
            }
        } // end_latitude
        TableViewColumn {
            role: "end_longitude"
            title: "End Lon"
            width: 90
            delegate: Text {
                text: ((styleData.value !== undefined) && (styleData.value !== null))  ? styleData.value : ""
                font.pixelSize: 11
                verticalAlignment: Text.AlignVCenter
                renderType: Text.NativeRendering;
            }
        } // end_longitude
        TableViewColumn {
            role: "end_depth_ftm"
            title: "End\nDepth"
            width: 60
            delegate: Text {
                text: ((styleData.value !== undefined) && (styleData.value !== null))  ? styleData.value : ""
                font.pixelSize: 11
                verticalAlignment: Text.AlignVCenter
                renderType: Text.NativeRendering;
            }
        } // end_depth_ftm
        TableViewColumn {
            role: "surface_temperature_avg_c"
            title: "Sfc\nTemp"
            width: 60
        } // surface_temperature_avg_c
        TableViewColumn {
            role: "true_wind_speed_avg_kts"
            title: "True\nWind\nSpeed"
            width: 60
        } // true_wind_speed_avg_kts
        TableViewColumn {
            role: "true_wind_direction_avg_deg"
            title: "True\nWind\nDir"
            width: 60
        } // true_wind_direction_avg_deg
        TableViewColumn {
            role: "drift_speed_kts"
            title: "Drift\nSpeed"
            width: 50
        } // drift_speed_kts
        TableViewColumn {
            role: "drift_direction_deg"
            title: "Drift\nDir"
            width: 50
        } // drift_direction_deg
        TableViewColumn {
            role: "drop_type"
            title: "Drop\nType"
            width: 70
//            property bool status: false

            delegate: Item {
                ComboBox {
                    width: parent.width
                    anchors.verticalCenter: parent.verticalCenter
                    enabled: (enabled_row == styleData.row) ? true : false
                    currentIndex: (styleData.row == reload_row) ? getDropTypeIndex(reload_row) :
                           (fpcMain.eventsModel.get(styleData.row).drop_type_index) // currentIndex
                    model: fpcMain.dropTypesModel
                    onCurrentIndexChanged: {
                        if (enabled_row == styleData.row) {
                            var item = {};
                            item["drop_type_index"] = currentIndex;
                            item["drop_type_lu_id"] = fpcMain.dropTypesModel.get(item["drop_type_index"]).id;
                            fpcMain.eventsModel.update_row(styleData.row, item);
                        }
                    }
                }
            }
        } // drop_type
        TableViewColumn {
            id: tvcIncludeInResults
            role: "include_in_results"
            title: "Include\n?"
            width: 50
            delegate: Item {
                CheckBox {
                    Component.onCompleted: {
                        tvEvents.model.setProperty(styleData.row, "include_in_results", checked)
                    }
                    onClicked: {
//                        tvEvents.model.setProperty(styleData.row, "include_in_results", checked)

                        var item = {};
                        item["include_in_results"] = checked;
                        fpcMain.eventsModel.update_row(styleData.row, item);
                    }
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
//                    checked: fpcMain.eventsModel.get(styleData.row).include_in_results
                    checked: (styleData.row == reload_row) ? getIncludeInResults(reload_row) :
                        getIncludeInResultsDefault(styleData.row)

//                        fpcMain.eventsModel.get(styleData.row).include_in_results
                    enabled: (enabled_row == styleData.row) ? true : false
                }
            }
        } // include_in_results

        style: TableViewStyle {
            rowDelegate: Rectangle {
                height: 30
                color: styleData.selected ? "skyblue" : (styleData.alternate? "#eee" : "#fff")
            }
            headerDelegate: Rectangle {
                height: 50

                width: textItem.implicitWidth
    //            color: "lightsteelblue"
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "white" }
                    GradientStop { position: 1.0; color: "lightgray" }
                }
                border.color: "gray"
                border.width: 1
                Text {
                    id: textItem
                    anchors.fill: parent
                    verticalAlignment: Text.AlignVCenter
//                    horizontalAlignment: styleData.textAlignment
                    horizontalAlignment: Text.AlignHCenter
                    anchors.leftMargin: 12
                    text: styleData.value
                    elide: Text.ElideRight
                    color: textColor
                    renderType: Text.NativeRendering
                    font.pixelSize: 11
                }
                Rectangle {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 1
                    anchors.topMargin: 1
                    width: 1
    //                color: "#ccc"
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "white" }
                        GradientStop { position: 1.0; color: "#eee" }
    //                    GradientStop { position: 1.0; color: "lightgray" }
                    }
                }
            }
        }
    } // tvEvents
    GroupBox {
        id: grpSeaState
//        anchors.left: grpOverview.left
        anchors.top: tvEvents.bottom
        anchors.topMargin: 20
        anchors.left: tvEvents.left
//        x: 8
//        y: 250
        width: 176
        height: 150
        visible: true
        title: qsTr("Sea State")
        style: Style {
            property Component panel: Rectangle {
                color: "transparent"
                border.width: 1
                Rectangle {
                    height: txtObj.height + 10
                    width: txtObj.width + 10
                    x: txtObj.x - 5
                    y: txtObj.y - 5
                    color: SystemPaletteSingleton.window(true)
                }
                Text {
                    id: txtObj
                    anchors.verticalCenter: parent.top
                    x: 10
                    text: control.title
                    font.pixelSize: 14
                }
            }
        }
        GridLayout {
            id: glSeaState
            x: 20
            y: 20
            columns: 2
            rows: 3
            columnSpacing: 20
            rowSpacing: 10
            flow: GridLayout.TopToBottom
            Label {
                id: lblSwellHeight
                width: 86
                height: 13
                text: qsTr("Swell Height (ft)")
            } // lblSwellHeight
            Label {
                id: lblSwellDirection
                width: 86
                height: 13
                text: qsTr("Swell Direction")
            } // lblSwellDirection
            Label {
                id: lblWaveHeight
                width: 86
                height: 13
                text: qsTr("Wave Height (ft)")
            } // lblWaveHeight
            TextField {
                id: tfSwellHeight
                Layout.preferredWidth: 40
                Layout.preferredHeight: 20
//                inputMask: "##.#"
//                validator: DoubleValidator {bottom: 0.0; top: 9.5;
//                                            decimals: 1; notation: DoubleValidator.StandardNotation}
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.IBeamCursor
                    onClicked: {
                        if (!parent.activeFocus) parent.forceActiveFocus();
                        parent.selectAll();
//                        parent.cursorPosition = 0;
                    }
                }
                onEditingFinished: {
                    var value = parseFloat(text);
                    if ((value < 0.0) || (value > 9.5)) {
                        dlgOkay.message = "Warning:  You entered:"
                        dlgOkay.value = text
                        dlgOkay.action = "This is outside the typical range of 0.0 <= x <= 9.5"
                        dlgOkay.accepted_action = "tfSwellHeight"
                        dlgOkay.open()
//                        text = ""
//                        return;
                    }

                    var items = [{"field": "swell_height_ft", "value": parseFloat(text)}]
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // tfSwellHeight
            TextField {
                id: tfSwellDirection
                Layout.preferredWidth: 40
                Layout.preferredHeight: 20
//                inputMask: "###"
//                validator: IntValidator {bottom: 1; top: 360}
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.IBeamCursor
                    onClicked: {
                        if (!parent.activeFocus) parent.forceActiveFocus();
                        parent.selectAll();
//                        parent.cursorPosition = 0;
                    }
                }
                onEditingFinished: {
                    var value = parseFloat(text);
                    if ((value < 1) || (value > 360)) {
                        dlgOkay.message = "Warning:  You entered:"
                        dlgOkay.value = text
                        dlgOkay.action = "This is outside the typical range of 1 <= x <= 360"
                        dlgOkay.accepted_action = "tfSwellDirection"
                        dlgOkay.open()
//                        text = ""
//                        return;
                    }

                    var items = [{"field": "swell_direction_deg", "value": parseInt(text)}]
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // tfSwellDirection
            TextField {
                id: tfWaveHeight
                Layout.preferredWidth: 40
                Layout.preferredHeight: 20
//                inputMask: "##.#"
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.IBeamCursor
                    onClicked: {
                        if (!parent.activeFocus) parent.forceActiveFocus();
                        parent.selectAll();
//                        parent.cursorPosition = 0;
                    }
                }
//                validator: DoubleValidator {bottom: 0.0; top: 9.5;
//                                            decimals: 1; notation: DoubleValidator.StandardNotation}
                onEditingFinished: {
                    var value = parseFloat(text);
                    if ((value < 0.0) || (value > 9.5)) {
                        dlgOkay.message = "Warning:  You entered:"
                        dlgOkay.value = text
                        dlgOkay.action = "This is outside the typical range of 0.0 <= x <= 9.5"
                        dlgOkay.accepted_action = "tfWaveHeight"
                        dlgOkay.open()
//                        text = ""
//                        return;
                    }

                    var items = [{"field": "wave_height_ft", "value": parseFloat(text)}]
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // tfWaveHeight
        } // glSeaState
    } // grpSeaState
    GroupBox {
        id: grpTide
        title: qsTr("Tide")
        anchors.top: tvEvents.bottom
        anchors.topMargin: 20
        anchors.left: grpSeaState.right
        anchors.leftMargin: 20
        width: 300
        height: grpSeaState.height
        visible: true
        style: Style {
            property Component panel: Rectangle {
                color: "transparent"
                border.width: 1
                Rectangle {
                    height: txtObj.height + 10
                    width: txtObj.width + 10
                    x: txtObj.x - 5
                    y: txtObj.y - 5
                    color: SystemPaletteSingleton.window(true)
                }
                Text {
                    id: txtObj
                    anchors.verticalCenter: parent.top
                    x: 10
                    text: control.title
                    font.pixelSize: 14
                }
            }
        }
        GridLayout {
            id: glTide
            x: 20
            y: 20
            columns: 2
            rows: 5
            columnSpacing: 20
            Label {
                id: lblStation
                text: qsTr("Station")
            } // lblStation
            TextField {
                id: tfStation
                Layout.preferredWidth: 175
                horizontalAlignment: TextInput.AlignLeft
                enabled: false
                text: (cbSiteName.currentIndex == 0) ? "" : fpcMain.getTideStation(cbSiteName.currentIndex, "name")
            } // tfStation
            Label {
                id: lblDistance
                text: qsTr("Distance (NM)")
            } // lblDistance
            TextField {
                id: tfDistance
                text: (cbSiteName.currentIndex == 0) ? "" : fpcMain.getDistanceToTideStation(cbSiteName.currentIndex)
                enabled: false
            } // tfDistance
            Label {
                id: lblTideType
                width: 86
                height: 13
                text: qsTr("Type")
            } // lblTideType
            ComboBox {
                id: cbTideType
                model: fpcMain.tideTypesModel
                currentIndex: 0
                onCurrentIndexChanged: {
                    if (currentIndex != 0) {
                        var items = [{"field": "tide_type_lu", "value": fpcMain.tideTypesModel.get(currentIndex).id}]
                        fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                    }
                }
            } // cbTideType
            Label {
                id: lblTideState
                width: 86
                height: 13
                text: qsTr("Tide State")
            } // lblTideState
            ComboBox {
                id: cbTideState
                model: fpcMain.tideStatesModel
                currentIndex: 0
                onCurrentIndexChanged: {
                    if (currentIndex != 0) {
                        var items = [{"field": "tide_state_lu", "value": fpcMain.tideStatesModel.get(currentIndex).id}]
                        fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                    }
                }
            } // cbTideState
            Label {
                id: lblFlow
                text: qsTr("Flow (ft/hr)")
            } // lblFlow
            TextField {
                id: tfFlow
                text: ""
                enabled: false
            } // tfFlow

        }
        Button {
            id: btnTidePlot
            width: 40
            height: 40
            tooltip: qsTr("View tidal plot")
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 15
            anchors.right: parent.right
            anchors.rightMargin: 10
            Image {
                anchors.fill: parent
                anchors.margins: 4
                source: "qrc:/resources/images/wave.png"
            }
        }
    } // grpTide
    GroupBox {
        id: grpSunAndMoon
        anchors.top: tvEvents.bottom
        anchors.topMargin: 20
        anchors.left: grpTide.right
        anchors.leftMargin: 20
        width: 198
        height: grpSeaState.height
        visible: true
        title: qsTr("Sun and Moon")

        style: Style {
            property Component panel: Rectangle {
                color: "transparent"
                border.width: 1
                Rectangle {
                    height: txtObj.height + 10
                    width: txtObj.width + 10
                    x: txtObj.x - 5
                    y: txtObj.y - 5
                    color: SystemPaletteSingleton.window(true)
                }
                Text {
                    id: txtObj
                    anchors.verticalCenter: parent.top
                    x: 10
                    text: control.title
                    font.pixelSize: 14
                }
            }
        }
        GridLayout {
            id: glSunAndMoon
            x: 20
            y: 20
            columns: 2
            rows: 4
            columnSpacing: 20
//            rowSpacing: 10
            flow: GridLayout.TopToBottom

            Label {
                id: lblSunrise
                text: qsTr("Sunrise")
            } // lblSunrise
            Label {
                id: lblSunset
                text: qsTr("Sunset")
            } // lblSunset
            Label {
                id: lblMoonPercentFull
                text: qsTr("Moon % Full")
            } // lblMoonPercentFull
            Label {
                id: lblMoonPhase
                text: qsTr("Moon Phase")
            } // lblMoonPhase

            TextField {
                id: tfSunrise
                enabled: false
                inputMask: "##:##"
                Layout.preferredWidth: 60
                Layout.preferredHeight: 20
            } // tfSunrise
            TextField {
                id: tfSunset
                enabled: false
                inputMask: "##:##"
                Layout.preferredWidth: 60
                Layout.preferredHeight: 20
            } // tfSunset
            TextField {
                id: tfMoonPercentFull
                inputMask: "##"
                enabled: false
                Layout.preferredWidth: 60
                Layout.preferredHeight: 20
            } // tfMoonPercentFull
            TextField {
                id: tfMoonPhase
                enabled: false
                Layout.preferredWidth: 60
                Layout.preferredHeight: 20
            } // tfMoonPhase

        } // glSunAndMoon
    } // grpSunAndMoon
    GroupBox {
        id: grpCtd
        title: qsTr("CTD")
        anchors.top: tvEvents.bottom
        anchors.topMargin: 20
        anchors.left: grpSunAndMoon.right
        anchors.leftMargin: 20
        width: 430
        height: grpSeaState.height
        visible: true
        style: Style {
            property Component panel: Rectangle {
                color: "transparent"
                border.width: 1
                Rectangle {
                    height: txtObj.height + 10
                    width: txtObj.width + 10
                    x: txtObj.x - 5
                    y: txtObj.y - 5
                    color: SystemPaletteSingleton.window(true)
                }
                Text {
                    id: txtObj
                    anchors.verticalCenter: parent.top
                    x: 10
                    text: control.title
                    font.pixelSize: 14
                }
            }
        }
        GridLayout {
            id: glCtd
            x: 20
            y: 20
            columns: 4
            rows: 4
            columnSpacing: 20
            flow: GridLayout.TopToBottom

            // Column 1
            Label {
                id: lblCtdDepth
                text: "CTD Depth (m)"
            } // lblCtdDepth
            Label {
                id: lblBottomTemp
                text: "Bottom Temp (C)"
            } // lblBottomTemp
            Label {
                id: lblDO
                text: "DO2 (SBE43) (ml/l)"
            } // lblDO
            Label {
                id: lblDO2
                text: "DO<sub>2</sub> (Aanderaa (ml/l)"
            } // lblDO2

            // Column 2
            TextField {
                id: tfCtdDepth
                text: ""
                Layout.preferredWidth: 60
                Layout.preferredHeight: 20
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.IBeamCursor
                    onClicked: {
                        if (!parent.activeFocus) parent.forceActiveFocus();
                        parent.selectAll();
//                        parent.cursorPosition = 0;
                    }
                }

//                validator: TextFieldDoubleValidator {
//                    bottom: 20.0;
//                    top: 150.0;
//                    decimals: 1;
//                }
//                validator: DoubleValidator {
//                    bottom: 20.0;
//                    top: 150.0;
//                    decimals: 1;
//                    notation: DoubleValidator.StandardNotation
//                }

                maximumLength: 6
                onEditingFinished: {
                    var value = parseFloat(text);
                    if ((value < 20) || (value > 230)) {
                        dlgOkay.message = "Warning:  You entered:"
                        dlgOkay.value = text
                        dlgOkay.action = "This is outside the typical range of 20 <= x <= 230"
                        dlgOkay.accepted_action = "tfCtdDepth"
                        dlgOkay.open()
//                        text = ""
//                        return;
                    }
                    var items = [{"field": "ctd_depth_m", "value": parseFloat(text)}]
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // tfCtdDepth
            TextField {
                id: tfBottomTemperature
                text: ""
                Layout.preferredWidth: 60
                Layout.preferredHeight: 20
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.IBeamCursor
                    onClicked: {
                        if (!parent.activeFocus) parent.forceActiveFocus();
                        parent.selectAll();
//                        parent.cursorPosition = 0;
                    }
                }
//                validator: DoubleValidator {bottom: 5.0; top: 30.0;
//                                            decimals: 1; notation: DoubleValidator.StandardNotation}
                maximumLength: 4
                onEditingFinished: {
                    var value = parseFloat(text);
                    if ((value < 5.0) || (value > 30.0)) {
                        dlgOkay.message = "Warning:  You entered:"
                        dlgOkay.value = text
                        dlgOkay.action = "This is outside the typical range of 5.0 <= x <= 30.0"
                        dlgOkay.accepted_action = "tfBottomTemperature"
                        dlgOkay.open()
//                        text = ""
//                        return;
                    }

                    var items = [{"field": "ctd_bottom_temp_c", "value": parseFloat(text)}]
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // tfBottomTemperature
            TextField {
                id: tfDO
                text: ""
                Layout.preferredWidth: 60
                Layout.preferredHeight: 20
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.IBeamCursor
                    onClicked: {
                        if (!parent.activeFocus) parent.forceActiveFocus();
                        parent.selectAll();
//                        parent.cursorPosition = 0;
                    }
                }
//                validator: DoubleValidator {bottom: 0.10; top: 9.99;
//                                            decimals: 2; notation: DoubleValidator.StandardNotation}
                onEditingFinished: {
                    var value = parseFloat(text);
                    if ((value < 0.10) || (value > 9.99)) {
                        dlgOkay.message = "Warning:  You entered:"
                        dlgOkay.value = text
                        dlgOkay.action = "This is outside the typical range of 0.10 <= x <= 9.99"
                        dlgOkay.accepted_action = "tfDO"
                        dlgOkay.open()
//                        text = ""
//                        return;
                    }

                    var items = [{"field": "ctd_do2_sbe43_ml_per_l", "value": parseFloat(text)}]
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // tfDO
            TextField {
                id: tfDO2
                text: ""
                Layout.preferredWidth: 60
                Layout.preferredHeight: 20
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.IBeamCursor
                    onClicked: {
                        if (!parent.activeFocus) parent.forceActiveFocus();
                        parent.selectAll();
                    }
                }
//                validator: DoubleValidator {bottom: 0.10; top: 9.99;
//                                            decimals: 2; notation: DoubleValidator.StandardNotation}
                onEditingFinished: {
                    var value = parseFloat(text);
                    if ((value < 0.10) || (value > 9.99)) {
                        dlgOkay.message = "Warning:  You entered:"
                        dlgOkay.value = text
                        dlgOkay.action = "This is outside the typical range of 0.10 <= x <= 9.99"
                        dlgOkay.accepted_action = "tfDO2"
                        dlgOkay.open()
//                        text = ""
//                        return;
                    }
                    var items = [{"field": "ctd_do2_aanderaa_ml_per_l", "value": parseFloat(text)}]
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // tfDO2

            // Column 3
            Label {
                id: lblSalinity
                text: "Salinity (psu)"
            } // lblSalinity
            Label {
                id: lblFluorescence
                text: "Fluorescence (ug/l Chl)"
                Layout.preferredWidth: 60
                Layout.preferredHeight: 20
            } // lblFluorescence
            Label {
                id: lblTurbidity
                text: "Turbidity (NTU)"
                Layout.preferredWidth: 100
                Layout.preferredHeight: 20
            } // lblTurbidity
            Label {} // Blank

            // Column 4
            TextField {
                id: tfSalinity
                text: ""
                Layout.preferredWidth: 60
                Layout.preferredHeight: 20
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.IBeamCursor
                    onClicked: {
                        if (!parent.activeFocus) parent.forceActiveFocus();
                        parent.selectAll();
//                        parent.cursorPosition = 0;
                    }
                }
//                validator: DoubleValidator {bottom: 32; top: 37;
//                                            decimals: 2; notation: DoubleValidator.StandardNotation}
                maximumLength: 5
                onEditingFinished: {
                    var value = parseFloat(text);
                    if ((value < 32.00) || (value > 37.00)) {
                        dlgOkay.message = "Warning:  You entered:"
                        dlgOkay.value = text
                        dlgOkay.action = "This is outside the typical range of 32.00 <= x <= 37.00"
                        dlgOkay.accepted_action = "tfSalinity"
                        dlgOkay.open()
//                        text = ""
//                        return;
                    }

                    var items = [{"field": "ctd_salinity_psu", "value": parseFloat(text)}];
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // tfSalinity
            TextField {
                id: tfFluorescence
                text: ""
                Layout.preferredWidth: 60
                Layout.preferredHeight: 20
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.IBeamCursor
                    onClicked: {
                        if (!parent.activeFocus) parent.forceActiveFocus();
                        parent.selectAll();
//                        parent.cursorPosition = 0;
                    }
                }
//                validator: DoubleValidator {bottom: 0; top: 50;
//                                            decimals: 2; notation: DoubleValidator.StandardNotation}
                maximumLength: 5
                onEditingFinished: {
                    var value = parseFloat(text);
                    if ((value < 0.00) || (value > 50.00)) {
                        dlgOkay.message = "Warning:  You entered:"
                        dlgOkay.value = text
                        dlgOkay.action = "This is outside the typical range of 0.00 <= x <= 50.00"
                        dlgOkay.accepted_action = "tfFluorescence"
                        dlgOkay.open()
//                        text = ""
//                        return;
                    }

                    var items = [{"field": "ctd_fluorescence_ug_per_l", "value": parseFloat(text)}];
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // tfFluorescence
            TextField {
                id: tfTurbidity
                text: ""
                Layout.preferredWidth: 60
                Layout.preferredHeight: 20
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.IBeamCursor
                    onClicked: {
                        if (!parent.activeFocus) parent.forceActiveFocus();
                        parent.selectAll();
//                        parent.cursorPosition = 0;
                    }
                }
//                validator: DoubleValidator {bottom: 0; top: 50;
//                                            decimals: 2; notation: DoubleValidator.StandardNotation}
                maximumLength: 5
                onEditingFinished: {
                    var value = parseFloat(text);
                    if ((value < 0.00) || (value > 50.00)) {
                        dlgOkay.message = "Warning:  You entered:"
                        dlgOkay.value = text
                        dlgOkay.action = "This is outside the typical range of 0.00 <= x <= 50.00"
                        dlgOkay.accepted_action = "tfTurbidity"
                        dlgOkay.open()
//                        text = ""
//                        return;
                    }

                    var items = [{"field": "ctd_turbidity_ntu", "value": parseFloat(text)}];
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // tfTurbidity
            Label {} // Blank
        }

    } // grpCtd
    GroupBox {
        id: grpComments
        anchors.top: grpSeaState.bottom
        anchors.topMargin: 20
        anchors.left: grpSeaState.left
        width: parent.width - 20 //- btnFinishedSite.width - 40
//        height: parent.height - grpSeaState.bottom + 20
        height: 180
        flat: false
        title: qsTr("Comments")
        style: Style {
            property Component panel: Rectangle {
                color: "transparent"
                border.width: 1
                Rectangle {
                    height: txtObj.height + 10
                    width: txtObj.width + 10
                    x: txtObj.x - 5
                    y: txtObj.y - 5
                    color: SystemPaletteSingleton.window(true)
                }
                Text {
                    id: txtObj
                    anchors.verticalCenter: parent.top
                    x: 10
                    text: control.title
                    font.pixelSize: 14
                }
            }
        }
        GridLayout {
            id: glComments
            x: 10
            y: 10
            columns: 2
            rows: 3
            Label {
                id: lblHabitat
                text: qsTr("Habitat")
//                font.pointSize: 10
//                font.bold: true
            } // lblHabitat
            TextArea {
                id: taHabitat
                Layout.preferredWidth: grpComments.width - 130
                Layout.preferredHeight: 30
                onEditingFinished: {
                    var items = [{"field": "habitat_comments", "value": text}]
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // taHabitat
            Label {
                id: lblFishMeter
                text: qsTr("Fish Meter")
//                font.pointSize: 10
//                font.bold: true
            } // lblFishMeter
            TextArea {
                id: taFishMeter
                Layout.preferredWidth: taHabitat.width
                Layout.preferredHeight: 30
                onEditingFinished: {
                    var items = [{"field": "fish_meter_comments", "value": text}]
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // taFishMeter
            Label {
                id: lblOceanWeather
                text: qsTr("Ocean/Weather")
//                font.pointSize: 10
//                font.bold: true
            } // lblOceanWeather
            TextArea {
                id: taOceanWeather
                Layout.preferredWidth: taHabitat.width
                Layout.preferredHeight: 30
                onEditingFinished: {
                    var items = [{"field": "ocean_weather_comments", "value": text}]
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // taOceanWeather
            Label {
                id: lblGeneral
                text: qsTr("General")
//                font.pointSize: 10
//                font.bold: true
            } // lblGeneral
            TextArea {
                id: taGeneral
                Layout.preferredWidth: taHabitat.width
                Layout.preferredHeight: 50
                onEditingFinished: {
                    var items = [{"field": "general_comments", "value": text}]
                    fpcMain.update_table_row("OperationDetails", operation_details_id, items);
                }
            } // taGeneral
        }
    } // grpComments
    GroupBox {
        id: grpRandomDrops
        anchors.top: grpComments.bottom
        anchors.topMargin: 20
        anchors.left: grpComments.left
        width: 300
        height: 40
        flat: false
        title: qsTr("Random Drops")
        style: Style {
            property Component panel: Rectangle {
                color: "transparent"
                border.width: 1
                Rectangle {
                    height: txtObj.height + 10
                    width: txtObj.width + 10
                    x: txtObj.x - 5
                    y: txtObj.y - 5
                    color: SystemPaletteSingleton.window(true)
                }
                Text {
                    id: txtObj
                    anchors.verticalCenter: parent.top
                    x: 10
                    text: control.title
                    font.pixelSize: 14
                }
            }
        }
        RowLayout {
            x: 10
            y: 10
            spacing: 10
            Label {
                id: lblRandomDrop1Label
                text: qsTr("Random Drop 1:")
            } // lblRandomDrop1Label
            Label {
                id: lblRandomDrop1
                text: ""
                font.bold: true
                font.pixelSize: 20
            } // lblRandomDrop1
            Label {
                Layout.preferredWidth: 20
            }
            Label {
                id: lblRandomDrop2Label
                text: qsTr("Random Drop 2:")
            } // lblRandomDrop2Label
            Label {
                id: lblRandomDrop2
                text: ""
                font.bold: true
                font.pixelSize: 20
            } // lblRandomDrop2
        }
    } // grpRandomDrops


    SetIdDialog {
        id: dlgSetId
        onRejected: {
            resetfocus()
        }
        onAccepted: {
            resetfocus()
        }
    }
    AdjustWaypointTimeDialog {
        id: dlgAdjustTime
        onAccepted: {
            var startChanged = false;
            var endChanged = false;
            if (sldStartTime.value !== 0) {
                startChanged = true;
            }
            if (sldEndTime.value !== 0) {
                endChanged = true;
            }
            var date = tfDate.text
            fpcMain.eventsModel.update_times(row, date, startChanged, endChanged,
                                            lblStartTimeNew.text, lblEndTimeNew.text)
        }
    }
    OkayCancelDialog {
        id: dlgOkayCancel
        property int row
        property string start_or_end
        onAccepted: {
            switch (accepted_action) {
                case "delete event":
                    fpcMain.eventsModel.delete_row(row, start_or_end)
                    break;
            }
        }
    }
    OkayDialog {
        id: dlgOkay
        onAccepted: {
            switch (accepted_action) {
                case "tide_height_m":
//                    console.info('num children: ' + tvEvents.children.length)
//                    var item = tvEvents.children[0];
//                    console.info('item children: ' + item.children.length)
//                    for (var i=0; i < item.children.length; i++) {
//                        console.info('child: ' + item.children[i])
//                    }
//                    tvEvents.children[7].item.forceActiveFocus();
                    break;

                case "tfCtdDepth":
//                    tfCtdDepth.forceActiveFocus()
                    break;
                case "tfBottomTemperature":
//                    tfBottomTemperature.forceActiveFocus()
                    break;
//                case "tfDO":
//                    tfDO.forceActiveFocus()
//                    break;
//                case "tfDO2":
//                    tfDO2.forceActiveFocus()
//                    break;
                case "tfSalinity":
//                    tfSalinity.forceActiveFocus()
                    break;
                case "tfFluorescence":
//                    tfFluorescence.forceActiveFocus()
                    break;
                case "tfTurbidity":
//                    tfTurbidity.forceActiveFocus()
                    break;
                case "noneValueObtained":

                    break;
            }
        }
    }

    ToolTip {
        id: ttSwellHeight
        width: 200
        target: lblSwellHeight
        text: "Valid Range: 0.0 - 9.5 (modulo 0.5)\nSamples: 1.5, 4.0, 5.5"
    } // ttSwellHeight
    ToolTip {
        id: ttSwellDirection
        width: 200
        target: lblSwellDirection
        text: "Valid Range: 1 - 360 (modulo 5)\nSamples: 5, 30, 55, 185"
    } // ttSwellDirection
    ToolTip {
        id: ttWaveHeight
        width: 200
        target: lblWaveHeight
        text: "Valid Range: 0.0 - 9.5 (modulo 0.5)\nSamples: 1.5, 4.0, 5.5"
    } // ttWaveHeight
    ToolTip {
        id: ttCtdDepth
        width: text.length * 6
        target: lblCtdDepth
        text: "Valid Range: 20 - 230"
    } // ttCtdDepth
    ToolTip {
        id: ttBottomTemperature
        width: text.length * 6
        target: lblBottomTemp
        text: "Valid Range: 5 - 30"
    } // ttBottomTemperature
    ToolTip {
        id: ttDO
        width: text.length * 6
        target: lblDO
        text: "Valid Range: 0.10 - 9.99"
    } // ttDO
    ToolTip {
        id: ttDO2
        width: text.length * 6
        target: lblDO2
        text: "Valid Range: 0.10 - 9.99"
    } // ttDO2
    ToolTip {
        id: ttSalinity
        width: text.length * 6
        target: lblSalinity
        text: "Valid Range: 32.00 - 37.00"
    } // ttSalinity
    ToolTip {
        id: ttFluorescence
        width: text.length * 6
        target: lblFluorescence
        text: "Valid Range: 0.00 - 50.00"
    } // ttFluorescence
    ToolTip {
        id: ttTurbidity
        width: text.length * 6
        target: lblTurbidity
        text: "Valid Range: 0.00 - 50.00"
    } // ttTurbidity

    ToolTip {
        id: ttMeatball1
        width: 100
        target: rctMeatball1
        text: ""
    } // ttMeatball1
    ToolTip {
        id: ttMeatball2
        width: 100
        target: rctMeatball2
        text: ""
    } // ttMeatball2
    ToolTip {
        id: ttMeatball3
        width: 100
        target: rctMeatball3
        text: ""
    } // ttMeatball3
    ToolTip {
        id: ttMeatball4
        width: 100
        target: rctMeatball4
        text: ""
    } // ttMeatball4
    ToolTip {
        id: ttMeatball5
        width: 100
        target: rctMeatball5
        text: ""
    } // ttMeatball5
    ToolTip {
        id: ttMeatball6
        width: 100
        target: rctMeatball6
        text: ""
    } // ttMeatball6
    ToolTip {
        id: ttMeatball7
        width: 100
        target: rctMeatball7
        text: ""
    } // ttMeatball7
    ToolTip {
        id: ttMeatball8
        width: 100
        target: rctMeatball8
        text: ""
    } // ttMeatball8
    ToolTip {
        id: ttMeatball9
        width: 100
        target: rctMeatball9
        text: ""
    } // ttMeatball9
    ToolTip {
        id: ttMeatball10
        width: 100
        target: rctMeatball10
        text: ""
    } // ttMeatball10


}
