import QtQuick 2.6
import QtQuick.Layouts 1.3

import "../common"
import "."

GridLayout {
    id: gridHaulRow
    columns: 15 + vess_ret_count
    columnSpacing: 0
    rowSpacing: 0

    property int vess_ret_count: 3
    property string haul_num: "#"  // Haul # in left column
    property var pos_num: null
    property var haul_db_id: null
    property string gear_type_num: ""
    property string target_strat: ""
    property string is_efp: ""
    property string has_brd: ""
    property var locationData: null
    // Note: dlgGPS moved to ObserverHome for performance. Connection below.

    property int cell_height: 70

    property ListModel location_model: ListModel {}

    signal modelUpdated // triggers new locationData from LogbookScreen
    signal vesselRetCountInc // temp

    onLocationDataChanged: {
        console.log("Location data changed, build location model.");
        buildLocationModel();
    }
    onVisibleChanged: {
        // Fixes FIELD-1405
        if(visible)
            buildLocationModel();
    }

    function buildLocationModel() {
        // Fill in cells accordingly - model is used to build tables

        // If we clear model now, it throws a bunch of warnings, so clear manually AFTER populating
        var initial_length = location_model.count;
        console.debug("Building Location Model");
        for (var i=0; i < locationData.length; i++) {
                var rowname;
                if (i==0)
                    rowname = "Set";
                else if (i==1)
                    rowname = "Up"
                else
                    rowname = "Loc #" + (i - 1);


                //console.debug('*** BUILDING LOC + ' locationData[i]["loc_id"] ' + ' POS ' +
//                  locationData[i]["position"] + ' depth ' + locationData[i]["depth"]);
                location_model.append({"rowname": rowname,
                                      "position": locationData[i]["position"],
                                      "loc_id": locationData[i]["loc_id"],
                                      "date_str": locationData[i]["date_str"],
                                      "time_str": locationData[i]["time_str"],
                                      "lat_deg": locationData[i]["lat_deg"],
                                      "lat_min": locationData[i]["lat_min"],
                                      "long_deg": locationData[i]["long_deg"],
                                      "long_min": locationData[i]["long_min"],
                                      "depth": locationData[i]["depth"]
                                      });
        }

        if (initial_length > 0) {
            location_model.remove(0, initial_length); // Now clear original entries.
        }

        if (location_model.count < 2) {
            if (location_model.count == 0) {
                location_model.clear();
                addPlaceholderEntry('Set', -1)
            }
            addPlaceholderEntry('Up', 0)
        }
    }

    function addPlaceholderEntry(name, pos) {
        location_model.append({"rowname": name,
                               "position": pos,
                                  "loc_id": -100,
                                  "date_str": "",
                                  "time_str": "",
                                  "lat_deg": 0,
                                  "lat_min": 0,
                                  "long_deg": 0,
                                  "long_min": 0,
                                  "depth": 0
                                  });
    }

    GridLayout {
        id: gridHauls
        columns: 2
        rows: location_model.count
        Layout.rowSpan: location_model.count > 0 ? location_model.count : 1
        Layout.columnSpan: 2
        columnSpacing: 0
        rowSpacing: 0
        LogbookCell {
            text: gridHaulRow.haul_num
            font_size: 18
            Layout.rowSpan: Math.max(location_model.count, 1)
            Layout.preferredHeight: cell_height * location_model.count

            FramButton {
                id: btnAddGPSLoc
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                anchors.left: parent.left
                implicitHeight: 50
                fontsize: 15
                text: "+ Loc"
                onClicked: {
                    dlgGPS.clear();
                    var newPositionLocation = location_model.count - 1;
                    if (location_model.count >= 1) {
                        // Check for placeholder entries
                        if (location_model.get(0).rowname === "Set" &&
                                location_model.get(0).loc_id === -100) {
                            newPositionLocation = -1;
                        } else if (location_model.get(1).rowname === "Up" &&
                                   location_model.get(1).loc_id === -100) {
                            newPositionLocation = 0;
                        }
                    }

                    console.log("Add New position location: "+ newPositionLocation);
                    dlgGPS.position_number = newPositionLocation;
                    gridHauls.newLocation(newPositionLocation);
                }
            }
        }

        function editLocation(loc_id, pos_num) {
            dlgGPS.position_number = pos_num;
            dlgGPS.location_id = loc_id;
            dlgGPS.new_entry = false;
            dlgGPS.haul_num = parseInt(gridHaulRow.haul_num);

            console.log("Got edit location for location id #" + loc_id + ", position " + pos_num)
            dlgGPS.open();
        }

        function newLocation(pos_num) {
            dlgGPS.new_entry = true;
            dlgGPS.position_number = pos_num;
            dlgGPS.haul_num = parseInt(gridHaulRow.haul_num);
            // Auto-build subtitle based on location ID passed
            var sub_title = "Haul " + gridHaulRow.haul_num + ": New ";
            if (pos_num === -1)
                sub_title += "Set Entry";
            else if (pos_num === 0)
                sub_title += "Up Entry";
            else
                sub_title += "GPS Loc. Entry"

            dlgGPS.sub_title = sub_title;
            console.log("New location for Haul #" + dlgGPS.haul_num)
            dlgGPS.open();
        }

        Repeater {
            id: rptLocations
            model: location_model

            RowLayout {
                spacing: 0
                function getLocationDecimalMinutesStr(min) {
                    // Follow the OPTECS convention for leading zero and number of decimal places
                    var includeLeadingZero = ObserverSettings.includeLeadingZeroInMinutes;
                    var nDecimalPlaces = ObserverSettings.nDecimalPlacesInMinutes;
                    return CommonUtil.getDecimalMinutesStr(min, includeLeadingZero, nDecimalPlaces);
                }

                LogbookCell {
                    text: rowname
                }
                LogbookCell {
                    text: date_str
                    implicitWidth: 90
                }
                LogbookCell {
                    text: time_str
                }
                LogbookCell {
                    text: lat_deg > 0 ? lat_deg.toFixed(0) : ""
                }
                LogbookCell {
                    text: lat_min > 0 ? getLocationDecimalMinutesStr(lat_min) : ""
                }
                LogbookCell {
                    text: long_deg != 0 ? long_deg.toFixed(0) : ""
                }
                LogbookCell {
                    text: long_min > 0 ? getLocationDecimalMinutesStr(long_min) : ""
                }
                LogbookCell {
                    text: depth > 0 ? depth : ""
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (rowname == 'Set' && loc_id == -100) {
                            gridHauls.newLocation(-1); // Shortcut to create new Set entry
                            return;
                        }
                        if (rowname == 'Up' && loc_id == -100) {
                            gridHauls.newLocation(0); // Shortcut to create new Up entry
                            return;
                        }


                        dlgGPS.location_id = loc_id;
                        dlgGPS.sub_title = "Edit Haul #" + gridHaulRow.haul_num + ": " + rowname;
                        dlgGPS.time_val = ObserverSettings.str_to_local(date_str + " " + time_str);
                        dlgGPS.lat_degs = lat_deg + CommonUtil.copySign(lat_min / 60.0, lat_deg);
                        dlgGPS.long_degs = long_deg + CommonUtil.copySign(long_min / 60.0, long_deg);
                        dlgGPS.depth = depth;
                        dlgGPS.set_values_from_decimal_degs();
                        console.log("Row? " + rowname);
                        console.log("Pos? " + position);
                        gridHauls.editLocation(loc_id, position);
                    }
                }
            }
        }
    }


// -------
    LogbookCell {
        text: is_efp
        Layout.rowSpan: location_model.count ? location_model.count : 1
        Layout.preferredHeight: cell_height * location_model.count
    }
    LogbookCell {
        text: gear_type_num
        Layout.rowSpan: location_model.count ? location_model.count : 1
        Layout.preferredHeight: cell_height * location_model.count
    }
    LogbookCell {
        text: target_strat
        Layout.rowSpan: location_model.count ? location_model.count : 1
        Layout.preferredHeight: cell_height * location_model.count
    }
    LogbookCell {
        text: has_brd
        Layout.rowSpan: location_model.count ? location_model.count : 1
        Layout.preferredHeight: cell_height * location_model.count
    }

    GridLayout {
        rows: 1
        columns: 5
        Layout.rowSpan: Math.max(location_model.count, 2)
        Layout.columnSpan: columns
        columnSpacing: 0
        rowSpacing: 0
        flow: GridLayout.TopToBottom

        // Observer Retained
        Repeater {
            id: repeatObsRet
            model: appstate.hauls.getObserverRetModel(gridHaulRow.haul_db_id)
            property int model_count: model.count

            Column {
                LogbookCell {
                    text: cc_code
                }
                LogbookCell {
                    text: weight === undefined ? "" : weight.toFixed(0);
                }
                Repeater {  // spacers - insert of others have more obs ret. entries
                    model: Math.max(location_model.count - 2, 0)
                    LogbookCell {
                        text: " "
                        border.width: 0
                    }
                }
            }
        }
        Repeater { // if some other row has more Obs Ret entries, insert blanks
            id: repeatObsRetSpacers
            model: calc_model_length()

            function calc_model_length() {
                return appstate.hauls.maxObsRetModelLength - repeatObsRet.model_count;
            }

            Column {
                LogbookCell {
                    text: ""
                }
                LogbookCell {
                    text: ""
                }
                Repeater {  // spacers - insert of others have more obs ret. entries
                    model: Math.max(location_model.count - 2, 0)
                    LogbookCell {
                        text: ""
                        border.width: 0
                    }
                }
            }
        }

        Repeater {
            id: repeatVesselRet
            model: get_vessel_retained(gridHaulRow.haul_db_id)

            function get_vessel_retained(db_id) {
                return appstate.hauls.getVesselRetModel(db_id);
            }

            Column {
                LogbookCell {
                    text: cc_code
                }
                LogbookCell {
                    text: weight
                }
                Repeater {  // spacers
                    model: Math.max(location_model.count - 2, 0)
                    LogbookCell {
                        text: " "
                        border.width: 0
                    }
                }
            }
        }
        Column {
            id: colAddVR
            LogbookCell {
                id: addVesselRetained
                text: "+"
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        dlgCCPicker.haul_num = gridHaulRow.haul_num
                        console.log("Opening Add Vessel Ret entry for haul # " + gridHaulRow.haul_num);
                        dlgCCPicker.open();
                    }
                }
            }
            Repeater {
                model: Math.max(location_model.count - 1, 1)
                LogbookCell {
                    text: " "
                    border.width: 0
                }
            }
        }


    }
    FramNoteDialog {
        id: dlgCCAlreadyObserverRetained
        property string cc_code
        message: "Catch Category " + cc_code +
                "\nis already used in this haul" +
                "\nas an observer-retained category."
    }

    Connections {
        target: dlgGPS
        onAccepted: {
            if (gridHaulRow.haul_num != dlgGPS.haul_num) {
                //console.log("IGNORED - not our haul");
                return;
            }
            var location_id = dlgGPS.location_id;
            var position_number = dlgGPS.position_number;
            var time_val = dlgGPS.time_val;
            var lat_degs = dlgGPS.lat_degs;
            var long_degs = dlgGPS.long_degs;
            var depth = dlgGPS.depth;

            if (dlgGPS.new_entry) {
                console.log("GPS Entry ACCEPTED for new position_number " + position_number);
            } else {
                console.log("GPS Entry ACCEPTED for location " + location_id + " and position " + position_number);
            }

            if (dlgGPS.new_entry) {
                dlgGPS.new_entry = false;
                appstate.hauls.locations.add_update_location_haul_id(
                            gridHaulRow.haul_db_id,
                            position_number,
                            CommonUtil.get_date_str(time_val),
                            lat_degs, // latitude
                            long_degs, // longitude
                            depth // depth (m)
                            );

            } else {  // Update existing
                appstate.hauls.locations.update_location_by_id(
                            location_id,
                            CommonUtil.get_date_str(time_val),
                            lat_degs, // latitude
                            long_degs, // longitude
                            depth // depth (m)
                            );
            }
            delayCall(200, function() {
                if (dlgGPS) {
                    dlgGPS.clear();
                }
            });
            // model changed, send signal (processed by LogbookScreen)
            gridHaulRow.modelUpdated();
        }
    }

    Connections {
        target: dlgCCPicker

        onCc_codeChanged: {

            if (gridHaulRow.haul_num != dlgCCPicker.haul_num) {
                //console.log("CC IGNORED - not our haul");
                return;
            }
            console.log("onCCChanged");
            // Don't allow a catch category to be added that's already been added as observer-retained.
            if (dlgCCPicker.cc_code != "") {
                console.debug("New catch category = '" + dlgCCPicker.cc_code + "'.");

                if (appstate.hauls.ccIsInObserverRetModel(gridHaulRow.haul_db_id, dlgCCPicker.cc_code)) {
                    console.debug("New catch category = '" + dlgCCPicker.cc_code + "' is already observer-retained.");
                    dlgCCAlreadyObserverRetained.cc_code = dlgCCPicker.cc_code;
                    dlgCCAlreadyObserverRetained.open();

                    // Leave the offending catch category selected, so user
                    // is given visual hint after clearing the dialog.
                    // But clear the saved code so clicking again gives this same dialog.
                    dlgCCPicker.cc_code = "";
                }
            }
        }
        onAccepted: {

            if (gridHaulRow.haul_num != dlgCCPicker.haul_num) {
                //console.log("AA IGNORED - not our haul");
                return;
            }
            console.log("onAccepted");
            var new_elem = {'cc_code': dlgCCPicker.cc_code, 'weight':  dlgCCPicker.weight};
            var haul_db_id = gridHaulRow.haul_db_id;
            if (!repeatVesselRet.model) {  // not sure why this gets cleared
                repeatVesselRet.model = repeatVesselRet.get_vessel_retained(haul_db_id);
            }
            appstate.hauls.addVesselRetained(haul_db_id, new_elem);
            console.log("Added Vessel Ret entry to " + haul_db_id);
            dlgCCPicker.clear();
        }
    }

}

