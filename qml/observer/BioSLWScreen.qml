import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2

import "../common"
import "."

ColumnLayout {
    id: slw
    Layout.fillWidth: true
    Layout.preferredHeight: 300
    property var currentID: appstate.catches.biospecimens.currentBiospecimenIdx
    property var currentSex: null
    property bool enable_entry: false
    property bool showAllEntry: false
    property int dec_places: appstate.displayDecimalPlaces  // Number of decimal places to display weight values

    function showAll(show_all) {
        showAllEntry = show_all;
    }

    property bool is_wm_9_19: appstate.catches.biospecimens.isWM9or19

    signal entryModifiedOK
    signal updateSex
    signal clearEntry

    signal readyNextTab  // this tab is complete, move to next tab

    signal addTally // PHLB Add tally
    signal decTally // PHLB Decrement tally

    property var pending_protocols: null            // required protocols for this species not yet filled in

    function isMeasuringLength() {
        // Whether this screen is measuring a specimen length is determined by the state of the numPad.
        var isML = numpadSLW.state == "integer_lengths" || numpadSLW.state == "fractional_lengths";
        console.debug("isMeasuringLength=" + isML);
        return isML;
    }

    // Most species measure length to nearest inch and use numpad in "integer_lengths" state.
    // At least one species (Dungeness Crab) measure lengths in tenths of inches (numpad "fractional_lengths").
    function measureSpeciesLengthFractionally() {
        console.debug("Current species measured fractionally=" +
                appstate.catches.species.currentSpeciesLengthMeasuredFractionally);
        return appstate.catches.species.currentSpeciesLengthMeasuredFractionally;
    }

    // Set up numpad to accept value for length, not weight.
    // Depending on species, allow fractional values or not. (So far, only Dungeness Crab uses fractional lengths).
    function updateNumpadStateToLength() {
        var showWeightOnly = !appstate.catches.species.bio_length_enabled && appstate.catches.species.bio_weight_enabled

        // FIELD-1548 If WT only (no length) then also show fractional mode
        if (slw.measureSpeciesLengthFractionally() || showWeightOnly) {
            numpadSLW.state = "fractional_lengths";
        } else {
            numpadSLW.state = "integer_lengths";
        }
        console.debug("Updated numpadSLW state to accept length value (" + numpadSLW.state + ").");
    }

    onCurrentIDChanged: {
        console.log("BioSLW ID Changed to " + currentID);
        var len = appstate.catches.biospecimens.getData('specimen_length');
        tfLength.text = len ? len : "";
        var wt = appstate.catches.biospecimens.getData('specimen_weight');
        tfWeight.text = wt ? wt.toFixed(dec_places) : "";
        var sex = appstate.catches.biospecimens.getData('specimen_sex');
        slw.currentSex = sex ? sex : "";
        updateSex();
        check_pending_protocols();
    }

    function check_pending_protocols() {
        // Check for missing protocols. Focus on 'first' required missing protocol.
        // where 'first' is order on screen: sex then length then weight.
        //
        // Give the active focus to the first missing protocol text field: length then weight.
        // If sex is a missing protocol, highlight its label to highlight that it's missing.

        // Start from full list of required protocols, redoing all fields,
        // in order to handle case of formerly filled field that has been cleared.
        var required_SLW_protocols = appstate.catches.species.requiredProtocolsSLW;
        console.debug("** Required protocols are " + required_SLW_protocols + ".");

        var weight_in_protocols = (required_SLW_protocols.indexOf('WT') != -1);
        var length_in_protocols = (required_SLW_protocols.indexOf('FL') != -1);
        var sex_in_protocols = (required_SLW_protocols.indexOf('S') != -1 || required_SLW_protocols.indexOf('SD') != -1);

        pending_protocols = required_SLW_protocols;

        // check weight
        var weight_populated = (tfWeight.text.length > 0);
        if (weight_in_protocols && weight_populated) {
            console.log('pending Weight protocol is filled, removed.');
            var this_protocol_pos = pending_protocols.indexOf('WT');
            pending_protocols.splice(this_protocol_pos, 1);
            console.debug("After splice: " + pending_protocols);
        } else if (weight_in_protocols) {
            console.debug("Focus on weight.")
            tfWeight.forceActiveFocus();
        }

        // check length
        // Simplified all lengths to FL
        var length_populated = (tfLength.text.length > 0);
        if (length_in_protocols && length_populated) {
            console.log('pending Length protocol is filled, removed.');
            var this_protocol_pos = pending_protocols.indexOf('FL');
            pending_protocols.splice(this_protocol_pos, 1);
            console.debug("After splice: " + pending_protocols);
        } else if (length_in_protocols) {
            console.log("Focus on length")
            tfLength.forceActiveFocus();
        }

        // check sex
        var sex_populated = slw.currentSex !== null && (slw.currentSex.length > 0);
        if (sex_in_protocols && sex_populated) {
            console.log('pending Sex protocol is ' + slw.currentSex + ', removed.');
            var this_protocol_pos_sd = pending_protocols.indexOf('SD');
            if (this_protocol_pos_sd !== -1)
                pending_protocols.splice(this_protocol_pos_sd, 2);
            var this_protocol_pos = pending_protocols.indexOf('S');
            if (this_protocol_pos !== -1)
                pending_protocols.splice(this_protocol_pos, 1);
//            console.debug("After protocol slice: " + pending_protocols);
            lblSex.highlight(false);
        }

        // Highlight labels of protocol fields that are in protocol set and aren't yet entered.
        check_label_highlighting(
                weight_in_protocols, weight_populated,
                length_in_protocols, length_populated,
                sex_in_protocols, sex_populated);
        return pending_protocols.length;
    }

    function check_label_highlighting(
            weight_in_protocols, weight_populated,
            length_in_protocols, length_populated,
            sex_in_protocols, sex_populated) {
        // Highlight or un-highlight labels depending on:
        // - Modify enabled or not.
        // - Protocol specified for this species or not.
        // - Field has been filled in or not
        var highlightSex = false;
        var highlightLength = false;
        var highlightWeight = false;
        if (screenBio.modifyEntryChecked) {
            highlightSex = sex_in_protocols && !sex_populated;
            highlightLength = length_in_protocols && !length_populated;
            highlightWeight = weight_in_protocols && !weight_populated;
        }
        lblSex.highlight(highlightSex);
        lblLength.highlight(highlightLength);
        lblWeight.highlight(highlightWeight);
    }

    function remaining_protocol_count() {
        return pending_protocols.length;
    }

    function move_to_next_tab_if_done() {
        if (pending_protocols.length > 0) {
            console.log('Not ready to move to next tab. Pending required SLW protocols: ' + pending_protocols);
        } else {
            // Done on this tab; move on to next tab.
            console.log('All SLW protocols complete! Moving to next tab.')
            numpadSLW.connect_tf = null;
            numpadSLW.forceActiveFocus();
            entryModifiedOK();
            slw.readyNextTab();
        }
    }

    function clear_values() {
        tfLength.text = "";
        tfWeight.text = "";
        // TODO: Clear Sex selection, or OK to leave sticky?
        numpadSLW.clearnumpad();
    }

    Connections {
        target: appstate.catches.species
        onSelectedItemChanged: {  // Current species ID has changed
            slw.updateNumpadStateToLength();
        }
    }

    onEnable_entryChanged: {
        tfLength.forceActiveFocus();
    }

    onClearEntry: {
        // clear text boxes etc
        slw.currentSex = null;
        updateSex();
        tfLength.text = '';
        tfWeight.text = '';
    }

    RowLayout {
        id: rlSex
        // Weight Methods 9 and 19 are weight and length but not sex
        visible: (appstate.catches.species.bio_sex_enabled && !slw.is_wm_9_19) || showAllEntry
        Layout.margins: 15
        property var cached_sex_val: null;

        FramLabelHighlightCapable {
            id: lblSex
            text: "Sex"
            font.pixelSize: 18
            Layout.preferredWidth: 75
        }

        ExclusiveGroup {
            id: egSex
        }

        function cache_sex_input(input) {
            // Cache input while record is created
            cached_sex_val = input;
        }

        function enter_cached_sex_input() {
            if (cached_sex_val) {
                set_sex(cached_sex_val);
                cached_sex_val = null;
                slw.updateSex();  // triggers buttons to update themselves
            }
        }

        function set_sex(label) {
            if (!enable_entry) {
                console.log("Not setting sex, enable_entry = false.");
                return;
            }
            // set currentSex
            switch(label) {
            case "Female":
                slw.currentSex = "F";
                break;
            case "Male":
                slw.currentSex = "M";
                break;
            case "Transtl.":
                slw.currentSex = "T";
                break;
            case "Juvenile":
                slw.currentSex = "J";
                break;
            case "Undet.":
                slw.currentSex = "U";
                break;
            case "N/A":                
            default:
                console.log('Sex set to null')
                slw.currentSex = null;
                break;
            }
        }

        Repeater {
            id: rptSex
            model: appstate.catches.species.currentSpeciesItemCode === '794' ?
                   ["Female", "Male", "Transtl.", "Juvenile", "Undet.", "N/A"] : ["Female", "Male", "Undet.", "N/A"]
            ObserverGroupButton {
                Layout.preferredWidth: model.length < 5 ? slw.width / (model.length - 1) : 60
                font_size: model.length < 5 ? 20: 16
                Layout.preferredHeight: 50
                text: modelData
                exclusiveGroup: egSex
                enabled: true  // enable_entry
                checked: compare_sex(modelData, slw.currentSex)
                onClicked: {
                    rlSex.set_sex(modelData);
                    updateSex();
                    if (!enable_entry) {
                        rlSex.cache_sex_input(modelData);
                        if (!screenBio.add_new_biospecimen_entry()) {
                            console.log("Not added");
                            rlSex.cache_sex_input(null); // clear
                        }
                    }
                    if (ObserverSettings.enableAudio) {
                        soundPlayer.play_sound("click", false)
                    }
                }
                function updateSex(){
                    // Update UI
                    if (currentID >= 0) {
                        checked = compare_sex(modelData, slw.currentSex);
                        if (checked) {
                            appstate.catches.biospecimens.setData('specimen_sex', slw.currentSex)
                            check_pending_protocols();
                            move_to_next_tab_if_done();
                        }
                    } else {
                        checked = false;
                    }
                }

                Connections {
                    target: slw
                    onUpdateSex: {
                        updateSex();
                    }
                }
                Connections {
                    target: appstate.catches.species
                    onCurrentProtocolsChanged: {
                        var sex_in_protocols = appstate.catches.species.bioControlEnabled('S') ||
                                appstate.catches.species.bioControlEnabled('SD');
                        var is_visible =  sex_in_protocols || showAllEntry;
                        rptSex.visible = is_visible;
                        lblSex.visible = is_visible;
                    }
                }

                function compare_sex(label, expected_val) {
                    switch(label) {
                    case "Female":
                        return expected_val === "F";                        
                    case "Male":
                        return expected_val === "M";                        
                    case "Transtl.":
                        return expected_val === "T";
                    case "Juvenile":
                        return expected_val === "J";
                    case "Undet.":
                        return expected_val === "U";                        
                    case "N/A":
                        return expected_val === null;
                    }
                }
            }
        }
    }
    GridLayout {
        columns: 2

        ColumnLayout {
            RowLayout {
                visible: slw.is_wm_9_19
                FramLabel {
                    text: "Total PHLB\nWeight"
                    font.pixelSize: 18
                    Layout.preferredWidth: 150
                }
                TextField {
                    readOnly: true
                    font.pixelSize: 18
                    text: appstate.catches.biospecimens.totalPHLBWeight ?
                              appstate.catches.biospecimens.totalPHLBWeight.toFixed(dec_places) :
                              ""

                }
                FramLabel {
                    text: "Avg PHLB\nWeight"
                    font.pixelSize: 18
                    Layout.preferredWidth: 100
                }
                TextField {
                    readOnly: true
                    font.pixelSize: 18
                    Layout.preferredWidth: 75
                    text: appstate.catches.biospecimens.avgPHLBWeight ?
                              appstate.catches.biospecimens.avgPHLBWeight.toFixed(dec_places) :
                              ""

                }
            }
            RowLayout {
                visible: appstate.catches.species.bio_length_enabled || showAllEntry
                FramLabelHighlightCapable {
                    id: lblLength
                    text: "Length"
                    font.pixelSize: 18
                    Layout.preferredWidth: 100
                }
                TextField {
                    id: tfLength
                    enabled: enable_entry
                    font.pixelSize: 18
                    style: TextFieldStyle {
                        background: Rectangle {
                                    border.width: tfLength.activeFocus ? 3 : 1
                        }
                    }
                    onTextChanged: {
                        if(tfLength.text.length > 0)
                            numpadSLW.save_specimen_length(tfLength.text)
                    }

                    onActiveFocusChanged: {
                        if(focus) {
                            numpadSLW.directConnectTf(tfLength);
                            slw.updateNumpadStateToLength();
                        }
                    }
                }
            }
        }
        RowLayout {
            visible: (appstate.catches.species.bio_weight_enabled || showAllEntry) &&
                     !slw.is_wm_9_19
            FramLabelHighlightCapable {
                id: lblWeight
                text: "Weight"
                font.pixelSize: 18                
            }
            TextField {
                id: tfWeight
                enabled: enable_entry
                Layout.preferredWidth: tfLength.width
                font.pixelSize: 18                
                style: TextFieldStyle {
                    background: Rectangle {
                                border.width: tfWeight.activeFocus ? 3 : 1
                    }
                }
                onTextChanged: {
                    if(tfWeight.text.length > 0)
                        numpadSLW.save_specimen_weight(tfWeight.text)
                }

                onActiveFocusChanged: {
                    if(focus) {
                        numpadSLW.directConnectTf(tfWeight);
                        numpadSLW.state = "weights"
                    }
                }
            }
        }
    }
    RowLayout {
        Rectangle {
            Layout.preferredHeight: 400
            Layout.preferredWidth: 400
            Layout.fillWidth: true
            color: "lightgray"
            FramScalingNumPad {
                id: numpadSLW
                anchors.fill: parent
                direct_connect: true
                state: slw.measureSpeciesLengthFractionally()? "fractional_lengths": "integer_lengths";
                limitToTwoDecimalPlaces: true   // Don't allow more than two decimal places for weight.
                enable_audio: ObserverSettings.enableAudio


                onNumpadok: {
                    console.debug("Numpad OK pressed! (state=" + state + ").");
                    check_pending_protocols();
                    move_to_next_tab_if_done();

                    if (slw.isMeasuringLength() && tfWeight.visible) {
                        // In Length text field. Move on to Weight.
                        numpadSLW.state = "weights";
                        tfWeight.forceActiveFocus();
                        console.debug("Moving on to Weight");
                    }
                }
                onNumpadinput: {
                    if (!enable_entry && (tfLength.visible || tfWeight.visible)) {
                        console.log("Numpad entry without modify enabled, creating new row.");
                        // clear selection, or we overwrite current Selection

                        cache_input(input_key);
                        if (!screenBio.add_new_biospecimen_entry())
                            cache_input(null); // clear
                    }
                }

                Connections {
                    target: screenBio
                    onAddEntry: {
                        console.debug("On Add Entry, clearing SLW tab");
                        tfLength.text = "";                        
                        tfWeight.text = "";

                        numpadSLW.clearnumpad();
                        check_pending_protocols();
                        // One of these should be triggered:
                        rlSex.enter_cached_sex_input();
                        numpadSLW.enter_cached_input();

                    }
                    onModifyEntryClicked: {
                        console.debug("Biospecimens's modify button is checked? " + screenBio.modifyEntryChecked);
                        check_pending_protocols();
                    }
                }

                function save_specimen_length(length_text) {
                    if(!enable_entry) {
                        console.log("Ignoring save_specimen_length input, entry disabled.")
                        return;
                    }

                    var len = parseFloat(length_text);
                    appstate.catches.biospecimens.setData('specimen_length', len ? len : null)
                    if (len)
                        console.debug("Saved specimen length " + len);
                }

                function save_specimen_weight(weight_text) {
                    if(!enable_entry) {
                        console.log("Ignoring save_specimen_weight input, entry disabled.")
                        return;
                    }
                    var wt = parseFloat(weight_text);

                    if (slw.is_wm_9_19)
                        wt = parseFloat(appstate.catches.biospecimens.currentPHLBSampleWeight);
                    appstate.catches.biospecimens.setData('specimen_weight',
                                                          wt ? wt : null)
                    // Round the value displayed in the numpad to std number of decimal places
                    tfWeight.text = wt ? wt.toFixed(dec_places) : "";
                    if (wt)
                        console.debug("Saved specimen weight " + wt);
                }
            }


        }
        ColumnLayout {
            id: columnTallyPHLB
            visible: appstate.catches.biospecimens.isWM19 && appstate.catches.isPHLB
            Layout.preferredWidth: 200
            enabled: true

            RowLayout {
                FramLabel {
                    font.pixelSize: 18
                    Layout.preferredWidth: 50
                    text: "Tally\nCount"
                }
                TextField {
                    id: tfTallyCount
                    font.pixelSize: 18
                    Layout.preferredWidth: 50
                    text: appstate.catches.biospecimens.tallyCount
                    readOnly: true                    
                }
            }

            FramButton {
                Layout.preferredHeight: 105
                Layout.preferredWidth: 105
                text: "+"
                fontsize: 30
                onClicked: {
                    slw.addTally();
                }
            }
            FramButton {
                Layout.preferredHeight: 105
                Layout.preferredWidth: 105
                text: "-"
                fontsize: 30
                onClicked: {
                    slw.decTally();
                }
            }

        }
    }
}
