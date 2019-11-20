import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2

import "../common"

ColumnLayout {
    id: rectVia
    Layout.fillWidth: true
    Layout.preferredHeight: 300
    property bool enable_entry: false

    property int bWidth: 100
    property int bHeight: 50

    property bool isCHLB: false
    property bool isPHLB: false
    property bool isGSTG: false
    property bool isCrab: false
    property bool isSalmon: false

    property bool isTrawl: true  // TODO appstate trawl/fixed gear

    property var pending_protocols: null

    signal viabilityChanged
    signal readyNextTab

    // Signals within this screen. Easiest way to get each button of a repeater to process the signal.
    signal updateViability
    signal updateEggs
    signal updateAdipose

    function update_ui(species_name) {
        isPHLB = false;
        isGSTG = false;
        isCHLB = false;
        isCrab = false;
        isSalmon = false;
        var species = species_name.toLowerCase();

        // TODO verify this covers all cases
        // TODO: Don't hardcode the species and protocols
        if (species.indexOf("pacific halibut") !== -1) {
            isPHLB = true;
            updateViability();
        } else if (species.indexOf("green sturgeon") !== -1) {
            isGSTG = true;
            updateViability();
        } else if (species.indexOf("california halibut") != -1) {
            isCHLB = true;
            updateViability();
        } else if (species.indexOf("crab") !== -1) {
            isCrab = true;
            updateEggs();
        } else if (species.indexOf("salmon") !== -1 && species.indexOf("shark") === -1 && species.indexOf("king of the") === -1) {
            // not salmon shark/ king of the salmon
            isSalmon = true;
            updateAdipose();
        }
        check_pending_protocols();
    }

    property var currentID: appstate.catches.biospecimens.currentBiospecimenIdx


    // For sample methods with species compositions (SM = '1', '2', or '3'), update show of buttons
    // on change of row selected in Species tab (a species composition item):
    Connections {
        target: appstate.catches.species
        onSelectedItemChanged: {
            if (appstate.catches.currentSampleMethodIsSpeciesComposition) {
                console.debug("CC w/SpecComp just set species name to item selected on Species tab: '" +
                        appstate.catches.species.currentSpeciesItemName + "'.");
                update_ui(appstate.catches.species.currentSpeciesItemName)
            }
        }
    }

    // For sample methods with no species composition, (i.e. using a species matched to the catch category),
    // update show of buttons on change of the species name in Observer.
    Connections {
        target: appstate
        onSpeciesNameChanged: {
            if (appstate.catches.currentSampleMethodIsNoSpeciesComposition) {
                console.debug("CC w/NoSpecComp just set appstate's species name to CC's matching species common name '" +
                        appstate.speciesName + "'.");
                update_ui(appstate.speciesName);
            }
        }
    }

    onCurrentIDChanged: {
        // TODO: update_ui is called here, onSpeciesNameChanged, and onSelectedItemChanged. Redundant?
        console.log("Biospecimen ID changed to " + currentID);
        update_ui(appstate.speciesName);
    }

    function check_pending_protocols() {

        pending_protocols = appstate.catches.species.requiredProtocolsViability;
        var via_prots = ['V', 'A', 'E'];
        var via_fields = ['viability', 'adipose_present', 'maturity'];
        for (var i = 0; i < via_prots.length; i++) {
            var pending_pos = pending_protocols.indexOf(via_prots[i]);
            var cur_field = via_fields[i];
            var current_val = appstate.catches.biospecimens.getData(cur_field);
            var protocol_specified = (pending_pos !== -1 && current_val && current_val.length > 0);
            if (protocol_specified) {
                console.log(cur_field + ' protocol set to ' + current_val + ', removed.');
                pending_protocols.splice(pending_pos, 1);
            }
            check_label_highlighting(cur_field, protocol_specified);
        }

        if (pending_protocols.length > 0) {
            console.log('Pending required Viability protocols: ' + pending_protocols)
        } else {
            console.log('All Viability protocols complete!')
            rectVia.readyNextTab();
        }

        return pending_protocols.length
    }

    function check_label_highlighting(currentProtocol, protocolSatisfied) {
        if (currentProtocol == 'viability') {
            if (isPHLB) {
                lblPhlbLongline.highlight(!protocolSatisfied);
                lblPhlbTrawl.highlight(!protocolSatisfied);
                console.debug("PHLB label highlighted: " + !protocolSatisfied);
            } else if (isGSTG) {
                lblGSTG.highlight(!protocolSatisfied);
                console.debug("GSTG label highlighted: " + !protocolSatisfied);
            } else if (isCHLB) {
                lblCHLB.highlight(!protocolSatisfied);
                console.debug("CHLB label highlighted: " + !protocolSatisfied);
            }
        } else if (currentProtocol == 'maturity') {
            if (isCrab) {
                lblCrab.highlight(!protocolSatisfied);
                console.debug("Crab label highlighted: " + !protocolSatisfied);
            }
        } else if (currentProtocol == 'adipose_present') {
            if (isSalmon) {
                lblSalmon.highlight(!protocolSatisfied);
                console.debug("Salmon label highlighted: " + !protocolSatisfied);
            }
        }
    }

    function remaining_protocol_count() {
        return pending_protocols.length;
    }

    function thisViabilityOptionIsChecked(viewOption, dbOption) {
        // Mapping for viability is straightforward: An exact match of the word. E.g. view option "Alive"
        // matches the database option as returned by getData, "Alive").
        // (The value stored in the database is a single letter, the first of the word; getData() does the mapping.
        var isChecked = (dbOption != null) ? (viewOption == dbOption): false;
//        console.debug("IsChecked:" + isChecked + "; viewOption:" + viewOption + "; dbOption:" + dbOption);
        return isChecked;
    }

    RowLayout {
        visible: isPHLB && isTrawl
        Layout.margins: 15
        ExclusiveGroup {
            id: egTrawl
        }

        FramLabelHighlightCapable {
            id: lblPhlbTrawl
            text: appstate.isFixedGear ? (appstate.sets.currentGearType === "10" ? "PHLB Pot" : "PHLB Longline") : "PHLB Trawl"
            font.pixelSize: 18
            Layout.preferredWidth: rectVia.width / 4
        }

        Repeater {
            model: appstate.isFixedGear && appstate.sets.currentGearType !== "10" ? ["Minor", "Moderate", "Dead", "Severe"] : ["Excellent", "Poor", "Dead"]
            ObserverGroupButton {
                Layout.preferredWidth: 85
                Layout.preferredHeight: bHeight
                text: modelData
                font_size: 18
                exclusiveGroup: egTrawl
                enabled: enable_entry
                onCheckedChanged: {
                    if(checked && enable_entry) {
                        save_phlb_trawl_viability(modelData);
                        viabilityChanged();
                    }
                }
                onClicked: {
                    if (ObserverSettings.enableAudio) {
                        soundPlayer.play_sound("click", false)
                    }
                }

                function save_phlb_trawl_viability(viability_desc) {
                    var viability = viability_desc;
                    appstate.catches.biospecimens.setData('viability', viability)
                    check_pending_protocols();
                }
                Connections {
                    target: rectVia
                    onUpdateViability: {
                        checked = thisViabilityOptionIsChecked(modelData, appstate.catches.biospecimens.getData('viability'));
                    }
                }
            }            
        }
    }
    RowLayout {
        visible: isPHLB && !isTrawl
        Layout.margins: 15
        ExclusiveGroup {
            id: egLongline
        }

        FramLabelHighlightCapable {
            id: lblPhlbLongline
            text: "PHLB Longline"
            font.pixelSize: 18
            Layout.preferredWidth: rectVia.width / 4
        }

        Repeater {
            model: ["Minor", "Moderate", "Severe", "Dead"]
            ObserverGroupButton {
                Layout.preferredWidth: 100
                Layout.preferredHeight: bHeight
                text: modelData
                exclusiveGroup: egLongline
                enabled: enable_entry
                onCheckedChanged: {
                    if(checked && enable_entry) {
                        save_phlb_ll_viability(modelData);
                        viabilityChanged();
                    }
                }
                onClicked: {
                    if (ObserverSettings.enableAudio) {
                        soundPlayer.play_sound("click", false)
                    }
                }

                function save_phlb_ll_viability(viability_desc) {
                    var viability = viability_desc; // TODO look up short code for viability?
                    appstate.catches.biospecimens.setData('viability', viability)
                    check_pending_protocols();
                }
                Connections {
                    target: rectVia
                    onUpdateViability: {
                        checked = thisViabilityOptionIsChecked(modelData, appstate.catches.biospecimens.getData('viability'));
                    }
                }
            }

        }
    }
    RowLayout {
        visible: isGSTG
        Layout.margins: 15
        ExclusiveGroup {
            id: egGreenSturg
        }

        FramLabelHighlightCapable {
            id: lblGSTG
            text: "Green Sturgeon"
            font.pixelSize: 18
            Layout.preferredWidth: 160
        }

        Repeater {
            model: ["Good", "Fair", "Poor", "Dead"]
            ObserverGroupButton {
                Layout.preferredWidth: 80
                Layout.preferredHeight: bHeight
                text: modelData
                exclusiveGroup: egGreenSturg
                enabled: enable_entry
                onCheckedChanged: {
                    if(checked && enable_entry) {
                        save_gstg_viability(modelData);
                        viabilityChanged();
                    }
                }
                onClicked: {
                    if (ObserverSettings.enableAudio) {
                        soundPlayer.play_sound("click", false)
                    }
                }

                function save_gstg_viability(viability_desc) {
                    var viability = viability_desc; // TODO look up short code for viability?
                    appstate.catches.biospecimens.setData('viability', viability)
                    check_pending_protocols();
                }
                Connections {
                    target: rectVia
                    onUpdateViability: {
                        checked = thisViabilityOptionIsChecked(modelData, appstate.catches.biospecimens.getData('viability'));
                    }
                }
            }
        }
    }
    RowLayout {
        visible: isCHLB
        Layout.margins: 15
        ExclusiveGroup {
            id: egCHLB
        }

        FramLabelHighlightCapable {
            id: lblCHLB
            text: "California Halibut"
            font.pixelSize: 18
            Layout.preferredWidth: rectVia.width / 4
        }

        Repeater {
            model: ["Alive", "Dead"]
            ObserverGroupButton {
                Layout.preferredWidth: bWidth
                Layout.preferredHeight: bHeight
                text: modelData
                exclusiveGroup: egCHLB
                enabled: enable_entry
                onCheckedChanged: {
                    if(checked && enable_entry) {
                        save_chlb_viability(modelData);
                        viabilityChanged();
                    }
                }
                onClicked: {
                    if (ObserverSettings.enableAudio) {
                        soundPlayer.play_sound("click", false)
                    }
                }

                function save_chlb_viability(viability_desc) {
                    var viability = viability_desc; // TODO look up short code for viability?
                    appstate.catches.biospecimens.setData('viability', viability)
                    check_pending_protocols();
                }
                Connections {
                    target: rectVia
                    onUpdateViability: {
                        checked = thisViabilityOptionIsChecked(modelData, appstate.catches.biospecimens.getData('viability'));
                    }
                }
            }            
        }
    }
    GridLayout {
        Layout.margins: 15
        columns: 4
        ExclusiveGroup {
            id: egCrabs
        }
        ExclusiveGroup {
            id: egSalmon
        }

        FramLabelHighlightCapable {
            id: lblCrab
            visible: isCrab
            text: "Crabs"
            font.pixelSize: 18
            Layout.columnSpan: 2
        }
        FramLabelHighlightCapable {
            id: lblSalmon
            visible: isSalmon
            text: "Salmon"
            font.pixelSize: 18
            Layout.columnSpan: 2
        }

        Repeater {
            model: ["Eggs Yes", "Eggs No"]
            ObserverGroupButton {
                visible: isCrab
                text: modelData
                exclusiveGroup: egCrabs
                enabled: enable_entry
                onCheckedChanged: {

                    if(checked && enable_entry) {
                        var maturity = modelData == "Eggs Yes" ? "Y" : "N"; // TODO look up short code for maturity?
                        appstate.catches.biospecimens.setData('maturity', maturity)
                        check_pending_protocols();
                    }
                }
                onClicked: {
                    if(checked) {
                        var sex = appstate.catches.biospecimens.getData("specimen_sex");
                        if (sex && sex === 'M' && modelData == "Eggs Yes") {
                            dlgNoMaleEggs.open();
                            checked = false;
                            return;
                        }
                    }

                    if (ObserverSettings.enableAudio) {
                        soundPlayer.play_sound("click", false)
                    }
                }

                Connections {
                    target: rectVia
                    onUpdateEggs: {
                        var eggs = appstate.catches.biospecimens.getData('maturity');
                        if (eggs) {
                            if (eggs === "1" && modelData === 'Eggs Yes') {
                                checked = true;
                            } else if (eggs === "0" && modelData === 'Eggs No') {
                                checked = true;
                            } else {
                                checked = false;
                            }
                        } else {
                            checked = false;
                        }
                    }
                }
            }

        }
        Repeater {            
            model: ["Adipose Yes", "Adipose No"]
            ObserverGroupButton {
                visible: isSalmon
                text: modelData
                exclusiveGroup: egSalmon
                enabled: enable_entry
                onCheckedChanged: {
                    if(checked) {
                        var adipose = modelData == "Adipose Yes" ? "Y" : "N"; // TODO look up short code for maturity?
                        appstate.catches.biospecimens.setData('adipose_present', adipose)
                        check_pending_protocols();
                    }
                }
                onClicked: {
                    if (ObserverSettings.enableAudio) {
                        soundPlayer.play_sound("click", false)
                    }
                }

                Connections {
                    target: rectVia
                    onUpdateAdipose: {
                        var adipose = appstate.catches.biospecimens.getData('adipose_present')
                        if (adipose === "Y" && modelData === "Adipose Yes") {
                            checked = true;
                        } else if (adipose === "N" && modelData === "Adipose No") {
                            checked = true;
                        } else {
                            checked = false
                        }
                    }
                }
            }
        }
        FramNoteDialog {
            id: dlgNoMaleEggs
            message: "Male crabs cannot have\n \"Eggs Yes\" selected."
            font_size: 18
        }
    }
}
