import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQml.Models 2.2

import "../common"
import "."

ColumnLayout {
    id: rectBarcodes
    Layout.fillWidth: true
    Layout.preferredHeight: 300
    property bool enable_entry: true
    property bool isCoral: false

    property var currentID: null
    property var numPad: null

    signal entryModifiedOK

    property var pending_protocols: null
    signal readyNextTab

    property bool showAllButtons: false

    function showAll(show_all) {
        showAllButtons = show_all;
    }

    onCurrentIDChanged: {
        // current biospecimen changed
        console.log("Biospecimen ID changed to " + currentID + ".");
        layoutBarcodes.resetBarcodes();
        layoutBarcodes.active_barcode_type = null;
        layoutBarcodes.loadBioBarcodes();
        layoutBarcodes.loadValueForActiveBarcodeType();
        pending_protocols = appstate.catches.species.requiredProtocolsBarcodes;

        check_pending_protocols();
    }

    function check_pending_protocols() {
        for (var i=0; i < modelDissectionBarcodeButtons.count; i++) {
            var short_name = modelDissectionBarcodeButtons.get(i).short_name;
            var req_pos = pending_protocols.indexOf(short_name);
            if (req_pos != -1) {
                var type_value = modelDissectionBarcodeButtons.get(i).type_value;
                var check_val = appstate.catches.biospecimens.get_barcode_value_by_type(type_value);
                if (check_val && check_val.length > 0) {
//                    console.log("Finished, removing " + short_name)
                    pending_protocols.splice(req_pos, 1);
                } else {
//                    console.log("I need a " + short_name)
                    layoutBarcodes.selectBarcodeButton(short_name);
                    return pending_protocols.length;
                }
            }
        }

        if (pending_protocols.length > 0) {
            console.log('Pending required barcode protocols: ' + pending_protocols)
        } else {
            console.log('All barcode protocols complete!')
            rectBarcodes.readyNextTab();
        }

        return pending_protocols.length
    }

    function remaining_protocol_count() {
        return pending_protocols ? pending_protocols.length : 0;
    }

    Connections {
        target: tabView
        onSelectedSpeciesChanged: {
            layoutBarcodes.resetBarcodes();
        }
    }

    onEnable_entryChanged: {
        tfBarcode.forceActiveFocus();
    }

    GridLayout {
        id: layoutBarcodes
        Layout.margins: 15
        columns: 4

        property var active_barcode_type: null

        ExclusiveGroup {
            id: egBarcodes
        }

        ListModel {
            id: modelDissectionBarcodeButtons
            ListElement {
                short_name: "FC"
                button_name: "Fin Clip"
                type_value: "10"  // from LOOKUP_VALUE in LOOKUPS.DISSECTION_TYPE
            }
            ListElement {
                short_name: "O"
                button_name: "Otolith"
                type_value: "1"
            }
            ListElement {
                short_name: "WS"
                button_name: "Whole\nSpecimen"
                type_value: "7"                
            }
            ListElement {
                short_name: "TS"
                button_name: "Tissue\nSample"
                type_value: "11"
            }
            ListElement {
                short_name: "FR"
                button_name: "Fin Ray"
                type_value: "5"  // DB note: dead GSTG only
            }
            ListElement {
                short_name: "SS"
                button_name: "Snout\nSample"
                type_value: "3"
            }
            ListElement {
                short_name: "SC"
                button_name: "Scales"
                type_value: "2"
            }
        }

        function activeBarcodeTypeRequiresNineDigits() {
            var barcode_type = getActiveBarcodeType();
            return appstate.catches.biospecimens.barcodeTypeRequiresNineDigitBarcode(barcode_type);
        }

        function saveNewBarcode(barcode_val) {
            if (active_barcode_type !== null && barcode_val !== null) {
                appstate.catches.biospecimens.save_dissection_type(active_barcode_type, barcode_val);
            }
        }

        signal resetBarcodes
        signal selectBarcodeButton(var barcode_label)

        onResetBarcodes: {
            console.log("Reset barcodes signal received, clearing.")
            active_barcode_type = null;
            numpadBarcodes.clearnumpad();
        }

        function loadBioBarcodes() {
            var types = appstate.catches.biospecimens.load_barcode_types_str();
            console.log("Got the following barcode types for this specimen: " + types);
            if (types && types.length > 0) {
                var type_array = types.split(",");
                console.log("Try to select a button for " + type_array[0])
                layoutBarcodes.selectBarcodeButton(type_array[0]);
            }
        }

        function getActiveBarcodeType() {
            return layoutBarcodes.active_barcode_type;
        }

        function loadValueForActiveBarcodeType() {
            tfBarcode.text = "";
            var activeBarcodeType = getActiveBarcodeType();
            console.log("Load barcode value for barcode type='" + activeBarcodeType + "'.");
            var activeBarcodeValue = appstate.catches.biospecimens.get_barcode_value_by_type(activeBarcodeType);
            if (activeBarcodeValue && activeBarcodeValue.length > 0) {
                console.log("Loaded value " + activeBarcodeValue);
                tfBarcode.text = activeBarcodeValue;
            } else {
                console.debug("No active barcode value found.");
            }
            if (screenBio.modifyEntryChecked) {
                // Hook up numpad to barcode text field.
                numpadBarcodes.directConnectWithTf(tfBarcode);
                tfBarcode.forceActiveFocus();
                numpadBarcodes.setnumpadvalue(activeBarcodeValue);
                console.debug("Modify Entry button checked; setting up barcode text field for mod.");
            } else {
                console.debug("Modify Entry button not checked; display current val, but disable mod.");
                numpadBarcodes.connect_tf = null;
            }
        }

        Repeater {
            model: modelDissectionBarcodeButtons
            ObserverGroupButton {
                Layout.preferredWidth: rectBarcodes.width / 5
                Layout.preferredHeight: 80
                text: button_name
                exclusiveGroup: egBarcodes
                enabled: enable_entry
                onClicked: {
                    console.debug("Barcode button clicked on " + short_name +
                            " with dissection row ID=" + currentID + ".");
                    var dissectionRowIsSelected = (currentID !== null && currentID >= 0);
                    if (dissectionRowIsSelected) {
                        setActiveBarcodeType();
                        layoutBarcodes.loadValueForActiveBarcodeType();
                    } else {
                        // Don't light up button if no dissection row has been selected.
                        console.debug("Barcode type button clicked but no dissection row selected; " +
                                "no action taken.");
                    }
                }

                function setActiveBarcodeType() {
                    if (currentID !== null && currentID >= 0) {
                        layoutBarcodes.active_barcode_type = type_value;
                        console.info("Set active barcode type for current row ID '" + currentID +
                                "' to short name='" + short_name +
                                "', type=" + type_value + ".");
                    } else {
                        console.info("No dissection row selected; barcode type not set.");
                        layoutBarcodes.active_barcode_type = null;
                    }
                }

                Connections {
                    target: layoutBarcodes
                    onResetBarcodes: {
                        checked = false;
                    }
                    onSelectBarcodeButton: {
                        if (short_name == barcode_label) {
                            console.log("Select barcode button: " + short_name + " vs. " + barcode_label);
                            checked = true;
                            setActiveBarcodeType();
                            layoutBarcodes.loadValueForActiveBarcodeType();
                        }
                    }

                }
                Connections {
                    target: appstate.catches.species
                    onCurrentProtocolsChanged: {
                        determine_enabled();
                    }
                }
                Connections {
                    target: rectBarcodes
                    onShowAllButtonsChanged: {
                        determine_enabled();
                    }
                }
                function determine_enabled() {
                    enabled = showAllButtons || appstate.catches.species.bioControlEnabled(short_name);
                    visible = showAllButtons || appstate.catches.species.bioControlEnabled(short_name);
                }

            }            
        }
    }
    RowLayout {
        TextField {
            id: tfBarcode
            font.pixelSize: 24
            placeholderText: "Barcode"
            enabled: enable_entry
            style: TextFieldStyle {
                background: Rectangle {
                            border.width: tfBarcode.activeFocus ? 3 : 1
                }
            }
            onActiveFocusChanged: {
                if(focus) {
                    if (screenBio.modifyEntryChecked) {
                        numpadBarcodes.directConnectWithTf(tfBarcode);
//                        console.debug("Modify enabled - connecting numpad to tfBarcode");
                    } else {
                        numpadBarcodes.connect_tf = null;
                        layoutBarcodes.loadValueForActiveBarcodeType();
//                        console.debug("Modify button disabled: disconnecting numpad from tfBarcode" +
//                                ", restoring active tfBarcode value.");
                    }
                }
            }
            onTextChanged: {
                console.debug("Barcode so far = " + text + "; not yet OK'd; " +
                        "ModifyEntry button is " +
                        (screenBio.modifyEntryChecked ? "" : "not") + " checked.");
            }
        }
        TextField {
            id: tfCoral
            font.pixelSize: 24
            placeholderText: "Coral Taxon"
            enabled: enable_entry
            visible: rectBarcodes.isCoral
            style: TextFieldStyle {
                background: Rectangle {
                            border.width: tfCoral.activeFocus ? 3 : 1
                }
            }
            onActiveFocusChanged: {
                if(focus) {
                    numpadBarcodes.directConnectWithTf(tfCoral);
                }
            }
        }
    }

    Connections {
        target: screenBio
        onAddEntry: {
            numpadBarcodes.enter_cached_input();
        }
    }

    RowLayout {
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 300
            color: "lightgray"
            FramScalingNumPad {
                id: numpadBarcodes
                anchors.fill: parent                
                direct_connect: true
                enable_audio: ObserverSettings.enableAudio

                function getActiveBarcodeOfActiveType() {
                    var activeBarcodeType = layoutBarcodes.active_barcode_type
                    return appstate.catches.biospecimens.get_barcode_value_by_type(activeBarcodeType);
                }

                function proposedBarcodeMatchesActive(newBarcode) {
                    var activeBarcode = getActiveBarcodeOfActiveType();
                    var isMatch = newBarcode === activeBarcode;

                    var activeBarcodeType = layoutBarcodes.active_barcode_type
                    console.debug("New barcode '" + newBarcode + "' does" + (isMatch ? "" : " not") +
                            " match current barcode '" + activeBarcode +
                            "' for dissection type " + activeBarcodeType + ".");

                    return isMatch;
                }

                function saveNewBarcode() {
                    const barcodeSaved = true; // For readability
                    var activeBarcodeType = layoutBarcodes.active_barcode_type;
                    if (!connect_tf) {
                        console.debug("No connected TF.");
                        return !barcodeSaved;
                    }
                    var newBarcodeValue = connect_tf ? connect_tf.text : "";
                    console.debug("newBarcodeValue is '" + newBarcodeValue + "', active type is " +
                            activeBarcodeType + ".");

                    if (layoutBarcodes.activeBarcodeTypeRequiresNineDigits() && newBarcodeValue.length != 9) {
                        console.debug("Proposed barcode value " + newBarcodeValue +
                                " doesn't have the nine digits needed for Barcode Type " + activeBarcodeType + ".");
                        dlgBarcodeTypes1Thru7MustBe9Digits.barcodeTypeDescription = activeBarcodeType;
                        dlgBarcodeTypes1Thru7MustBe9Digits.attemptedBarcodeValue = newBarcodeValue;
                        dlgBarcodeTypes1Thru7MustBe9Digits.open()
                        return !barcodeSaved;
                    }
                    if(newBarcodeValue.length > 15) {
                        dlgBarcodeMoreThan15Digits.barcodeTypeDescription = activeBarcodeType;
                        dlgBarcodeMoreThan15Digits.attemptedBarcodeValue = newBarcodeValue;
                        dlgBarcodeMoreThan15Digits.open()
                        return !barcodeSaved;
                    }

                    // Do nothing if newly entered value equals active value in model,
                    // for that dissection type.
                    if (proposedBarcodeMatchesActive(newBarcodeValue)) {
                        console.info("User OK'ing pre-existing active barcode value; no action taken.")
                        return barcodeSaved;    // Allow advance to next empty field.
                    }

                    // If new value is empty string, and active value is non-empty,
                    // delete the entry for the active barcode value from DB and from view model.
                    if (newBarcodeValue.length == 0) {
                        var activeBarcodeValue = getActiveBarcodeOfActiveType();
                        // This check for match of new to active should always fail after the above context.
                        if (activeBarcodeValue.length == 0) {
                            // This should not occur.
                            CommonUtil.quitApp(
                                    "Fatal Error: The active barcode value (loaded from DB) should not be empty.");
                        }

                        console.debug("Checking that barcode '" + activeBarcodeValue + "' exists in DB ...");
                        var activeBarcodeExistsInDb =
                                appstate.catches.biospecimens.barcodeExists(activeBarcodeType, activeBarcodeValue);
                        if (!activeBarcodeExistsInDb) {
                            // This should not occur.
                            CommonUtil.quitApp(
                                    "Fatal Error: The active barcode value (purportedly loaded from DB) " +
                                    " could not be found in DB.");
                        }

                        var deleteSucceeded =
                                appstate.catches.biospecimens.deleteExistingDissectionByBarcodeTypeAndValue(
                                        activeBarcodeType, activeBarcodeValue);

                        if (deleteSucceeded) {
                            console.info("User cleared entry for dissection type " +
                                    layoutBarcodes.active_barcode_type + "; deleted specified " +
                                    "barcode value of " + activeBarcodeValue + ".");
                        } else {
                            console.error("User attempt to clear entry for dissection type " +
                                    layoutBarcodes.active_barcode_type + " with " +
                                    "barcode value of " + activeBarcodeValue + " failed.");
                        }
                        // Even if delete succeeded, return false to prevent auto-advance to next empty field.
                        return !barcodeSaved;
                    }

                    // Before adding new barcode, make sure it doesn't violate uniqueness constraint of barcode_type.
                    // For example, barcode values must be unique within barcodes 1 thru 7.
                    if (appstate.catches.biospecimens.barcodeExists(activeBarcodeType, newBarcodeValue)) {
                        displayErrorMessage(activeBarcodeType, newBarcodeValue);
                        return !barcodeSaved;
                    } else {
                        // Finally - a new barcode eligible to be saved to DB and loaded into view model:
                        layoutBarcodes.saveNewBarcode(newBarcodeValue);
                        appstate.catches.biospecimens.update_barcodes_str(); // update model
                        console.info("Barcode " + newBarcodeValue + " added to database and model.");
                        return barcodeSaved;
                    }
                }

                function displayErrorMessage(barcode_type, barcode) {
                    var barcodeEntry = appstate.catches.biospecimens.getBarcodeEntryInfo(barcode_type, barcode);
                    dlgBarcodeAlreadyInUse.barcode = barcode;
                    dlgBarcodeAlreadyInUse.trip_id = barcodeEntry.trip_id;
                    dlgBarcodeAlreadyInUse.haul_id = barcodeEntry.haul_id;
                    dlgBarcodeAlreadyInUse.catch_category_code = barcodeEntry.catch_category_code;
                    dlgBarcodeAlreadyInUse.species_where_used = barcodeEntry.species_common_name;
                    dlgBarcodeAlreadyInUse.dissection_type_where_used = barcodeEntry.dissection_type_description;
                    dlgBarcodeAlreadyInUse.open();

                    console.error("Barcode " + barcode + " already exists. Used with " +
                            "dissection type:" + barcodeEntry["dissection_type_description"] +
                            ", species common name:" + barcodeEntry.species_common_name);
                }

                onNumpadinput: {
                    if (currentID === null || currentID < 0) {
                        console.debug("Create New Row");
                        cache_input(input_key);
                        if (!screenBio.add_new_biospecimen_entry())
                            cache_input(null); // clear
                    }
                }

                onNumpadok: {
                    var operationOK = saveNewBarcode();
                    if (operationOK) {
                        numpadBarcodes.connect_tf = null;
                        numpadBarcodes.forceActiveFocus();
                        check_pending_protocols();
                        entryModifiedOK();
                    }
                }                
            }

            ////
            // Pop-up Dialog - Triggered by Rectangle components, but not part of normal display.
            ////
            FramNoteDialog {
                id: dlgBarcodeAlreadyInUse
                height: 350
                property string barcode
                property string trip_id;
                property string haul_id;
                property string catch_category_code;
                property string dissection_type_where_used
                property string species_where_used
                message: "Barcode " + barcode +
                    "\nalready used with:" +
                    "\nTrip#: " + trip_id +
                    "\nHaul#: " + haul_id +
                    "\nCatch Cat. Code: " + catch_category_code +
                    "\nSpecies: " + species_where_used +
                    "\nDissection Type: " + dissection_type_where_used
            }
            FramNoteDialog {
                id: dlgBarcodeTypes1Thru7MustBe9Digits
                property string barcodeTypeDescription;
                property string attemptedBarcodeValue;
                message: "Barcodes of Type " + barcodeTypeDescription +
                    "\nmust be 9 digits." +
                    "\nAttempted barcode value of " +
                    "\n" + attemptedBarcodeValue + " has " + attemptedBarcodeValue.length + " digits."
            }

            FramNoteDialog {
                id: dlgBarcodeMoreThan15Digits
                property string barcodeTypeDescription;
                property string attemptedBarcodeValue;
                message: "Barcode longer than 15 digits." +
                    "\nAttempted barcode value of " +
                    "\n" + attemptedBarcodeValue + "\nhas " + attemptedBarcodeValue.length + " digits."
            }


        }
    }
}
