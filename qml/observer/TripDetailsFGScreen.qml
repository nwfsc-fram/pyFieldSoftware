// TripDetailsScreen.qml - Start or Edit Trip Details (Fixed Gear)

import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Controls.Styles 1.4

import "../common"
import "."

Item {
    id: detailsPageItem

    function page_state_id() { // for transitions
        return "start_fg_state";
    }

    width: parent.width
    height: parent.height - framFooter.height

    signal resetfocus
    onResetfocus: {
        // "Clear" active focus by setting to a label
        vesselLabel.forceActiveFocus();
    }

    property FramAutoComplete current_ac // Currently active autocomplete
    property TextField current_tf // Currently active textfield

    function checkDetailsComplete() {
        // Have all required fields been specified?
        var vesselIsSpecified = (tfVesselName.length > 0);
        if (!vesselIsSpecified) {
            console.debug("Trip's vessel not yet specified.");
        }

        var fisheryIsSpecified = (tfFishery.text.length > 0);
        if (!fisheryIsSpecified) {
            console.debug("Trip's fishery not yet specified.");
        }

        // Update navigation
        var detailsComplete = vesselIsSpecified && fisheryIsSpecified;
        framHeader.forwardEnable(detailsComplete);

        // Update highlights of labels of required field
        vesselLabel.highlight(!vesselIsSpecified);
        fisheryLabel.highlight(!fisheryIsSpecified);
    }

    Keys.forwardTo: [framNumPadDetails, keyboardMandatory] // Required for capture of Enter key

    Component.onCompleted: {
        keyboardMandatory.showbottomkeyboard(false);
        keyboardMandatory.hide_ok_if_empty_text = false;  // Default: allow empty field to be OK'd
        keyboardPermits.showbottomkeyboard(false);

        checkDetailsComplete();
    }

    Component.onDestruction: {
        save_fields();
    }

    function hide_all_popups() {
        console.debug("Hiding all popups");
        keyboardMandatory.showbottomkeyboard(false);
        keyboardPermits.showbottomkeyboard(false);
        framNumPadDetails.show(false);
        framNumPadDetails.visible = false;
        dateStartPicker.close();
    }

    function save_fields() {
        // This is to support the FramListModel        
        if (tfVesselName.length === 0) {
            console.log("No vessel selected. Not saving trip.");
            return;
        }
        if (!appstate.trips.currentTrip) {
            // Entry into this screen implies we are starting a trip
            appstate.create_trip(tfVesselName.text);
            console.log("Current trip is undefined. Created trip for vessel:" + tfVesselName.text);
            checkDetailsComplete();
        }
        console.log("Saving trip data.");

        var modified_trip = appstate.trips.currentTrip;
        modified_trip.vessel_name = appstate.trips.currentVesselName;  // This will be looked up by FK in python
        modified_trip.notes = appstate.db_formatted_comments;  // this seems to get wiped out, so need to re-set it here.
        // update list model entries
        appstate.trips.currentTrip = modified_trip;

    }

    ////
    // Validation for Permits/Licenses removed
    ////


    function validate_permit_or_license(per_or_lic_text) {
        // Return values: -1 (validation not performed
        //  0: failed, with an error dialog box displayed.
        //  1: passed, permit/license number validated.
        per_or_lic_text = String(per_or_lic_text);
        if (per_or_lic_text.length === 0) {
            return -1;
        }
        return 1;
    }

    function popup_duplicate_permit_or_license(per_or_lic_text) {
        dlgValidationError.offending_value = "'" + per_or_lic_text + "'";
        dlgValidationError.details = "\nis already entered for this trip.";

        // After popup is OK'd, force focus here to re-display keyboard.
        dlgValidationError.textfield_to_get_focus = textNewCert;
        dlgValidationError.open();
    }

    function popup_certification_max_reached(max_count) {
        dlgValidationError.offending_value = "";
        dlgValidationError.details = "The maximum of " + max_count + " certifications"
            + "\nhave already entered for this trip.";

        // After popup is OK'd, leave focus unfocused on any particular field - just the grid in general.
        dlgValidationError.textfield_to_get_focus = null;
        gridStartTrip.forceActiveFocus();
        dlgValidationError.open();
    }

    GridLayout
    {
        id: gridStartTrip
        anchors.fill: parent
        columns: 2
        columnSpacing: 100
        rows: 6
        anchors.leftMargin: 50
        anchors.rightMargin: 50
        anchors.topMargin: 0
        anchors.bottomMargin: 50
        flow: GridLayout.TopToBottom


        property int labelColWidth: 250
        property int dataColWidth: Math.min( 400, root.width/2 - 50) // limit width

        RowLayout {
            FramLabelHighlightCapable {
                id: vesselLabel
                text: qsTr("Vessel Name")
                Layout.preferredWidth: gridStartTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25

            }
            TextField {
                id: tfVesselName
                Layout.fillWidth: true
                Layout.preferredHeight: ObserverSettings.default_tf_height
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
                placeholderText: vesselLabel.text
                text: appstate.trips.currentVesselName
                onActiveFocusChanged: {
                    if (focus) {
                        hide_all_popups();
                        autocomplete.suggest("vessels");
                        keyboardMandatory.connect_tf(tfVesselName, placeholderText); // Connect TextField
                        keyboardMandatory.showbottomkeyboard(true);
                        keyboardMandatory.hide_ok_if_empty_text = true;  // Required field: don't allow empty field to be OK'd
                    }
                }
                onTextChanged: {
                    appstate.trips.setVesselNameUSCG(text) // expects "Name - USCG/REG" format, ignore just Name
                    var lastIndex = text.lastIndexOf(" - ");
                    if (lastIndex > 0) {
                        // Remove coast guard #
                        text = text.substring(0, lastIndex);
                    }
                    save_fields();
                    textUSCG.text = rowUSCG.get_uscg();

                    // This could be a new trip, which requires non-null Vessel Name, so trigger load_hauls()
                    appstate.currentTripId = appstate.trips.tripId;
                    db_sync.markTripInProgress(appstate.currentTripId);

                    checkDetailsComplete();
                }
            }
        }

        RowLayout {
            id: rowUSCG
            Label {
                id: labelUSCG_StateReg
                text: "USCG #"
                Layout.preferredWidth: gridStartTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
            }
            function get_uscg() {
                if (typeof appstate.trips.currentTrip == 'undefined'
                    || typeof appstate.trips.currentTrip.vessel == 'undefined') {
                    console.debug("current trip vessel not yet defined");
                    return "";
                }

                if (appstate.trips.currentTrip.vessel.coast_guard_number) {
                    console.debug("appstate.trips.currentTrip.vessel.coast_guard_number=" +
                        appstate.trips.currentTrip.vessel.coast_guard_number);
                    labelUSCG_StateReg.text = "USCG #";
                    return appstate.trips.currentTrip.vessel.coast_guard_number;
                } else if (appstate.trips.currentTrip.vessel.state_reg_number) {
                    console.debug("appstate.trips.currentTrip.vessel.state_reg_number=" +
                        appstate.trips.currentTrip.vessel.state_reg_number);
                    labelUSCG_StateReg.text = "State Reg. #"
                    return appstate.trips.currentTrip.vessel.state_reg_number;
                } else {
                    console.debug("Neither coast_guard_number nor state_reg_number defined");
                    return "";
                }
            }

            TextField {
                id: textUSCG
                text: rowUSCG.get_uscg()
                Layout.fillWidth: true
                Layout.preferredHeight: ObserverSettings.default_tf_height
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
                enabled: false
            }
        }

        RowLayout {
            FramLabelHighlightCapable{
                id: fisheryLabel
                text: qsTr("Fishery")
                Layout.preferredWidth: gridStartTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
            }
            TextField {
                id: tfFishery
                Layout.fillWidth: true
                Layout.preferredHeight: ObserverSettings.default_tf_height
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 18
                enabled: tfVesselName.text.length > 0 // && appstate.trips.allowFisheryChange
                text: appstate.trips.currentFisheryName
                placeholderText: fisheryLabel.text
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (!appstate.trips.allowFisheryChange) {
                            console.warn("Not allowing fishery change (underlying data)");
                            dlgNoChangeFisheryError.open();
                        } else {
                            tfFishery.forceActiveFocus();
                        }
                    }
                }
                onActiveFocusChanged: {
                    if (focus) {
                        hide_all_popups();
                        autocomplete.suggestFisheriesByProgID(appstate.users.currentProgramID, appstate.isFixedGear);
                        keyboardMandatory.connect_tf(tfFishery, placeholderText); // Connect TextField
                        keyboardMandatory.addAutoCompleteSuggestions(text); // Force display of all
                        keyboardMandatory.showbottomkeyboard(true);
                        keyboardMandatory.hide_ok_if_empty_text = false;  // Not required field: Allow empty field to be OK'd
                    }
                }
                onTextChanged: {
                    appstate.trips.currentFisheryName = text;
                    // Required field - check if it's entered.
                    checkDetailsComplete();
                }
            }
        }

        RowLayout {
            Label {
                id: lblSkipper
                text: qsTr("Skipper's Name")
                Layout.preferredWidth: gridStartTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
            }
            TextField {
                id: tfSkipper
                Layout.fillWidth: true
                Layout.preferredHeight: ObserverSettings.default_tf_height
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
                enabled: tfVesselName.text.length > 0
                text: appstate.trips.currentSkipperName
                placeholderText: lblSkipper.text
                onActiveFocusChanged: {
                    if (focus) {
                        hide_all_popups();
                        autocomplete.fullSearch = true;
                        autocomplete.suggest("captains");
                        autocomplete.suggestCaptainsByVesselId(appstate.trips.currentTrip.vessel.vessel)
                        keyboardMandatory.connect_tf(tfSkipper, placeholderText); // Connect TextField
                        keyboardMandatory.addAutoCompleteSuggestions(text); // Force display of all
                        keyboardMandatory.showbottomkeyboard(true);
                        keyboardMandatory.hide_ok_if_empty_text = false;  // Not required field: Allow empty field to be OK'd
                    }
                }
                onTextChanged: {
                    appstate.trips.currentSkipperName = text;
                }
            }

        }

        RowLayout {
            Label {
                text: qsTr("# of Crew")
                Layout.preferredWidth: gridStartTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
            }
            TextField {
                id: textCrewNum
                Layout.fillWidth: true
                Layout.preferredHeight: ObserverSettings.default_tf_height
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
                enabled: tfVesselName.text.length > 0
                placeholderText: qsTr("Number")
                text: appstate.trips.currentCrewCount
                onFocusChanged: {
                    if (focus) {
                        hide_all_popups();
                        framNumPadDetails.visible = true;
                        framNumPadDetails.attachresult_tf(textCrewNum);
                        framNumPadDetails.setnumpadhint("# of Crew");
                        framNumPadDetails.setnumpadvalue(text);
                        framNumPadDetails.setstate("popup_basic");
                        framNumPadDetails.show(true);
                    }
                }
                onTextChanged: {
                    if (text != "") {
                        appstate.trips.currentCrewCount = text;
                    }
                }
            }
        }

        RowLayout {
            Label {
                text: qsTr("Observer Logbook #")
                Layout.preferredWidth: gridStartTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
            }
            TextField {
                id: textObserverLogNum
                Layout.fillWidth: true
                Layout.preferredHeight: ObserverSettings.default_tf_height
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
                placeholderText: qsTr("Number")
                enabled: tfVesselName.text.length > 0
                text: appstate.trips.currentLogbookNum
                onFocusChanged: {
                    if (focus) {
                        hide_all_popups();
                        framNumPadDetails.visible = true;
                        framNumPadDetails.attachresult_tf(textObserverLogNum);
                        framNumPadDetails.setnumpadhint("Logbook #");
                        framNumPadDetails.setnumpadvalue(text);
                        framNumPadDetails.setstate("popup_basic");
                        framNumPadDetails.show(true);
                    }
                }
                onTextChanged: {
                    if (text != "") {
                        appstate.trips.currentLogbookNum = text;
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            flow: GridLayout.TopToBottom
            columns: 3
            rows: appstate.trips.TripCertsModel.count + 1
            Layout.rowSpan: appstate.trips.TripCertsModel.count / 2 + 1

            // First Column
            Label {
                id: lblPermit
                text: qsTr("Permit / License #")
                Layout.preferredWidth: gridStartTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
                Layout.rowSpan: appstate.trips.TripCertsModel.count + 1
            }
            TextField {
                id: textNewCert
                Layout.fillWidth: true
                Layout.preferredHeight: ObserverSettings.default_tf_height
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
                placeholderText: qsTr("Permit/ License #")
                text: ""
                enabled: tfVesselName.text.length > 0
                Layout.rowSpan: 1
                // Custom property: more than 7 certificates forces a new column and messes up the layout.
                // Users tell us seven are more than adequate.
                property int max_count: 7
                onActiveFocusChanged: {
                    if (focus) {
                        hide_all_popups();
                        console.debug("Count of existing certs=" + appstate.trips.TripCertsModel.count);
                        if (appstate.trips.TripCertsModel.count < textNewCert.max_count) {
                            keyboardPermits.connect_tf(textNewCert, placeholderText);
                            keyboardPermits.showbottomkeyboard(true);
                        } else {
                            popup_certification_max_reached(textNewCert.max_count);
                        }
                    }
                }
                onTextChanged: {
                    var val_result = validate_permit_or_license(textNewCert.text);
                    if (val_result === -1)
                        return;

                    // Permit/License # entered is valid.
                    if (!appstate.trips.TripCertsModel.is_item_in_model(
                            "certificate_number", textNewCert.text)) {
                        appstate.trips.addTripCert(textNewCert.text);
                    } else {
                        popup_duplicate_permit_or_license(textNewCert.text);
                        console.error("Certificate#" + textNewCert.text + " has already been added "
                            + "to Trip#" + appstate.currentTripId);
                    }

                    // Clear the field on error or on success (successful value moved to another field).
                    textNewCert.text = "";
                }
            }
            Repeater {  // Cert #'s - Can't be edited
                id: rptrCertText
                model: appstate.trips.TripCertsModel
                Layout.rowSpan: appstate.trips.TripCertsModel.count
                TextField {
                    Layout.fillWidth: true
                    Layout.preferredHeight: ObserverSettings.default_tf_height
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25
                    text: certificate_number
                    readOnly: true
                }
            }

            FramButton {
                id: buttonAddCert
                Layout.preferredWidth: 50
                Layout.preferredHeight: 40
                fontsize: 24
                enabled: tfVesselName.text.length > 0
                Layout.rowSpan: 1
                text: "+"
                onClicked: {
                    console.debug("Add Button: Count of existing certs="
                        + appstate.trips.TripCertsModel.count);
                    hide_all_popups();
                    if (appstate.trips.TripCertsModel.count < textNewCert.max_count) {
                        keyboardPermits.connect_tf(textNewCert, textNewCert.placeholderText);
                        keyboardPermits.showbottomkeyboard(true);
                    } else {
                        popup_certification_max_reached(textNewCert.max_count);
                    }
                }
            }
            Repeater {  // Delete buttons for Cert #'s
                model: appstate.trips.TripCertsModel
                Layout.rowSpan: appstate.trips.TripCertsModel.count
                FramButton {
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 40
                    fontsize: 24
                    text: "-"
                    enabled: tfVesselName.text.length > 0
                    onClicked: {
                        appstate.trips.delTripCert(certificate_number);
                    }
                }
            }
        }

        RowLayout {
            Label {
                text: qsTr("Departure Date / Time")
                Layout.preferredWidth: gridStartTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
            }
            TextField {
                id: textDepDate
                Layout.fillWidth: true
                Layout.preferredHeight: ObserverSettings.default_tf_height
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
                enabled: tfVesselName.text.length > 0
                placeholderText: qsTr("Calendar")
                text: ObserverSettings.format_date(appstate.trips.currentStartDateTime)
                onActiveFocusChanged: {
                    if (focus) {
                        hide_all_popups();
                        focus = false;  // otherwise, dialogs opened forever
                        dateStartPicker.message = "Start Time"
                        dateStartPicker.open();
                    }
                }
            }
            FramDatePickerDialog {
                id: dateStartPicker
                //Layout.alignment: Qt.AlignCenter
                enable_audio: ObserverSettings.enableAudio
                onDateAccepted: {
                    console.info("Picked: start datetime: " + selected_date);
                    appstate.trips.currentStartDateTime = selected_date;
                }
            }
        }

        RowLayout {
            Label {
                id: lblDP
                text: qsTr("Departure Port")
                Layout.preferredWidth: gridStartTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
            }
            TextField {
                id: tfDepPort
                Layout.fillWidth: true
                Layout.preferredHeight: ObserverSettings.default_tf_height
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
                enabled: tfVesselName.text.length > 0
                placeholderText: lblDP.text
                text: appstate.trips.currentStartPortName
                onActiveFocusChanged: {
                    if (focus) {
                        hide_all_popups();
                        autocomplete.clear_suggestions();
                        keyboardMandatory.clearList();
                        autocomplete.suggest("ports");
                        keyboardMandatory.connect_tf(tfDepPort, placeholderText); // Connect TextField
                        keyboardMandatory.showbottomkeyboard(true);
                        keyboardMandatory.hide_ok_if_empty_text = false;  // Not required field: Allow empty field to be OK'd
                    }
                }
                onTextChanged: {
                    appstate.trips.currentStartPortName = text;
                }
            }
        }

        RowLayout {
            FramButton {
                id: buttonHookCounts
                Layout.preferredWidth: gridStartTrip.labelColWidth
                Layout.preferredHeight: ObserverSettings.default_tf_height
                fontsize: 25
                enabled: tfVesselName.text.length > 0
                Layout.rowSpan: 1
                text: "Hook Count Avg."
                onClicked: {
                    if (!appstate.trips.allowAvgHookCountChange) {
                        console.warn("Not allowing avg hook count change (underlying data)");
                        dlgNoHookChange.open();
                    } else {
                        hide_all_popups();
                        dlgHC.open();
                    }
                }
            }
            TextField {
                id: tfHookCounts
                Layout.fillWidth: true
                Layout.preferredHeight: ObserverSettings.default_tf_height
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
                placeholderText: qsTr("Number")
                text: appstate.trips.currentAvgHookCount
                readOnly: true;
            }
        }
    } // GridLayout

    Rectangle {
     id: keyboardFrame // add a background for the autocomplete dropdown
     color: ObserverSettings.default_bgcolor
     visible: keyboardMandatory.visible
     height: keyboardMandatory.height
     width: parent.width
     x: keyboardMandatory.x - 25
     y: keyboardMandatory.y
    }

    FramWideKeyboardAndList {
        id: keyboardMandatory
        desired_height: 365
        opaque: true
        mandatory_autocomplete: true // force choice from list
        enable_audio: ObserverSettings.enableAudio
        onButtonOk: {
            resetfocus();
            if(current_ac)
                current_ac.showautocompletebox(false);
        }

    }

    Rectangle {
     // Had to hack together a simple keyboard with background for Permit
     id: keyboardFramePermit // add background for keyboard
     color: ObserverSettings.default_bgcolor
     visible: false
     height: 365
     width: parent.width
     x: 0
     y: parent.height - 365
     function show(show_kb) {
         // the keyboard tends to set its own visibility, so ensure correct behavior here
         visible = show_kb;
         keyboardBG.visible = show_kb;
         keyboardPermit.visible = show_kb;
     }

    }
    Rectangle {
     id: keyboardBG // size keyboard
     color: "transparent"
     visible: false
     height: 365
     width: parent.width - 400
     x: 200
     y: parent.height - 365

     FramScalingKeyboard {  // fills parent rect
         id: keyboardPermit
         visible: false
         state: "caps"
         enable_audio: ObserverSettings.enableAudio
         onKeyboardok: {
             resetfocus();
         }
     }
    }

    Rectangle {
     id: keyboardFrame2 // add a background for the autocomplete dropdown
     color: "darkgray"
     visible: keyboardPermits.visible
     height: keyboardPermits.height
     width: keyboardPermits.width + 50
     x: keyboardPermits.x - 25
     y: keyboardPermits.y
    }

    FramWideKeyboard {
        id: keyboardPermits
        desired_height: 365
        opaque: true
        visible: false
        width: parent.width / 2
        x: width / 2
        enable_audio: ObserverSettings.enableAudio

        onButtonOk: {
            resetfocus();
            if(current_ac)
                current_ac.showautocompletebox(false);
        }
    }


    FramNumPad {
        id: framNumPadDetails
        x: 328
        y: 327

        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter
        visible: false
        enable_audio: ObserverSettings.enableAudio
    }


    // Error dialog box if permit/license number not in proper format.
    FramNoteDialog {
        id: dlgValidationError
        property string offending_value;
        property string details;
        property TextField textfield_to_get_focus : null;
        message: offending_value + details;
        font_size: 18
        onAccepted: {
            if (textfield_to_get_focus)
                textfield_to_get_focus.forceActiveFocus();
        }
    }

    // Error - don't allow fishery to be changed with data
    FramNoteDialog {
        id: dlgNoChangeFisheryError
        message: "To change fishery, you must do\n this on the observer website\n after data is synced.";
        font_size: 18
    }

    FramNoteDialog {
        id: dlgNoHookChange
        message: "To change hook count\n average, you must do\n this on the observer website\n after data is synced.";
        font_size: 18
    }

    HookCountsDialog {
        id: dlgHC
        enable_audio: ObserverSettings.enableAudio

        onAccepted: {
//            if (avgHookCount > 0.0) {
              // Allow 0 average
              appstate.trips.currentAvgHookCount = avgHookCount.toFixed(2);
              appstate.sets.updateTripHookCounts(appstate.currentTripId, avgHookCount)
//            } else {
//                console.error("Avg hook count invalid, not setting data: " + avgHookCount)
////                appstate.trips.currentAvgHookCount = null;
//            }

        }
    }

}
