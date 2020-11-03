import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.2
import QtQml.Models 2.2

import "../common"
import "."

Item {

    id: speciesFGPage

    property var currentCatchCategory: null

    Component.onCompleted: {
        slidingKeyboardSpecies.showbottomkeyboard(false);  // init sizing
        appstate.catches.species.isFixedGear = appstate.isFixedGear;
        appstate.catches.species.counts_weights.isFixedGear = appstate.isFixedGear;
    }

    function setTabsEnabled() {
        if (tvSelectedSpecies.model.count < 1) {
            // Empty
            tabView.enableCountWeightTab(false);
            tabView.enableBiospecimensTab(false);
        }
    }

    function clear_species_filter() {
        tfSpeciesFilter.text = "";
        var current_cc = appstate.catches.currentCatch.catch_category.catch_category;
        appstate.catches.species.reloadAvailableListModel();
    }

    function hide_keyboard_clear_species_filter() {
        // Hide the keyboard, clear the species textbox, take the cannoli.
        slidingKeyboardSpecies.showbottomkeyboard(false);
        clear_species_filter();
    }

    function enable_add_button(do_enable) {
        console.debug("Add button set " + do_enable);
        btnAddSpecies.enabled = do_enable;
    }

    function enable_remove_button(do_enable) {
        console.debug("Remove button set " + do_enable);
        btnRemoveSpecies.enabled = do_enable;
    }

    signal resetFocus()
    onResetFocus: {
        // Just set focus to something benign
        lvSp.forceActiveFocus();
    }

    function isWm3() {
        var isWeightMethod3 = appstate.catches.weightMethod === '3';
        console.debug("isWm3=" + isWeightMethod3);
        return isWeightMethod3;
    }
    function isWm15() {
        var isWeightMethod15 = appstate.catches.weightMethod === '15';
        console.debug("isWm15=" + isWeightMethod15);
        return isWeightMethod15;
    }
    Keys.forwardTo: [slidingKeyboardSpecies] // Capture of Enter key

    ListView {
        id: lvSp
        anchors.left: parent.left
        anchors.right: parent.right
        height: main.height - toolBar.height - framHeader.height - rowListSelect.height

        TextField {
            id: tfSpeciesFilter
            x: 20
            y: 20
            height: 40
            width: 500
            placeholderText: qsTr("Species")
            font.pixelSize: 20

            onTextChanged: {
                appstate.catches.species.filter = text;
                if (appstate.catches.species.filter_matches_code) {
                    var matchingRow = get_row_with_code(text);
                    console.debug("Filter matches species code of '" + text + "'.");
                    tvAvailableSpecies.selection.clear();
                    tvAvailableSpecies.currentRow = matchingRow;
                    tvAvailableSpecies.selection.select(matchingRow);
                    enable_add_button(true);
                } else {
                    enable_add_button(false);
                }
            }

            function get_row_with_code(code) {
                // If a row in tvAvailableSpecies has the specified species code,
                // return the index of that row
                var r = 0;
                for (r = 0; r < tvAvailableSpecies.model.count; r++) {
                    var rowcode = tvAvailableSpecies.model.get(r).species_code;
                    if (rowcode == code) {
                        console.debug("Code match of " + code + " on row " + r);
                        return r;
                    }
                }
                console.error("Failed to find match in tvAvailableSpecies for code = " + code);
                return 0; // Shouldn't happen
            }

            signal userSpeciesSelected
            onUserSpeciesSelected: {
                // Active focus seems to get set when switching to this page,
                // so this is an explicit slot for user clicks
                slidingKeyboardSpecies.showbottomkeyboard(true);
                slidingKeyboardSpecies.connect_tf(tfSpeciesFilter);

                // If no row selected, disable the Add button
                if (!tvAvailableSpecies.selection || tvAvailableSpecies.selection.count < 1) {
                    enable_add_button(false);
                }

                forceActiveFocus();
            }

            MouseArea {
                anchors.fill: parent
                propagateComposedEvents: true
                onClicked: {
                    tfSpeciesFilter.userSpeciesSelected()
                }
            }
        }


        ObserverTableView {
            id: tvAvailableSpecies
            x: tfSpeciesFilter.x
            y: tfSpeciesFilter.y + tfSpeciesFilter.height + 20
            width: tfSpeciesFilter.width
            height: parent.height - tfSpeciesFilter.height - 110

            headerVisible: true
            selectionMode: SelectionMode.MultiSelection

            property var availModel: appstate.catches.species.observerSpeciesAvailableModel
            //TODO: IMPLEMENT property var recentModel: appstate.catches.species.ObserverSpeciesRecentModel

            model: availModel

            onClicked: {
                enable_add_button(true);
            }

            TableViewColumn {
                role: "species_code"
                title: "Code"
                width: 75
            }
            TableViewColumn {
                role: "common_name"
                title: "Name"
                width: tfSpeciesFilter.width/2
            }

            TableViewColumn {
                role: "scientific_name"
                title: "Scientific Name"
                width: tfSpeciesFilter.width/2
            }

        }

        function toggleAvailableList(whichList) {
            if (whichList !== "Full" && whichList !== "Frequent" && whichList !== "Trip" &&
                    whichList !== "AssocSpecies") {
                console.error("Unrecognized species list type '" + whichList + "'.");
                return;
            }
            hide_keyboard_clear_species_filter(); // Just in case keyboard is up.
            tvAvailableSpecies.selection.clear();
            enable_add_button(false);
            var current_cc = appstate.catches.currentCatch.catch_category.catch_category;
            appstate.catches.species.setAvailableListModel(whichList, current_cc);
            console.info("Switching available species model to " + whichList);
        }

        RowLayout {
            id: rowListSelect
            x: tvAvailableSpecies.x
            y: tvAvailableSpecies.y + tvAvailableSpecies.height + 10
            property int buttonWidth: 120
            ExclusiveGroup {
                id: grpList
            }

            ObserverGroupButton {
                id: btnFullList
                text: qsTr("Full\nList")
                x: tvAvailableSpecies.x
                y: parent.y
                checked: true
                checkable: true
                Layout.preferredWidth: rowListSelect.buttonWidth
                exclusiveGroup: grpList
                onClicked: {
                    lvSp.toggleAvailableList("Full");
                }
            }
            ObserverGroupButton {
                id: btnFrequentList
                text: qsTr("Frequent\nList")
                x: btnFullList.x + btnFullList.width + 10
                y: parent.y
                checkable: true
                Layout.preferredWidth: rowListSelect.buttonWidth
                exclusiveGroup: grpList
                onClicked: {
                    lvSp.toggleAvailableList("Frequent");
                }
            }
            ObserverGroupButton {
                id: btnTripList
                text: qsTr("Trip\nList")
                x: btnFrequentList.x + btnFrequentList.width + 10
                y: parent.y
                checkable: true
                Layout.preferredWidth: rowListSelect.buttonWidth
                exclusiveGroup: grpList
                onClicked: {
                    lvSp.toggleAvailableList("Trip");
                }
            }
            ObserverGroupButton {
                id: btnAssocSpecies
                text: qsTr("Assoc.\nSpecies")
                x: btnTripList.x + btnTripList.width + 10
                y: parent.y
                checkable: true
                Layout.preferredWidth: rowListSelect.buttonWidth
                exclusiveGroup: grpList
                onClicked: {
                    lvSp.toggleAvailableList("AssocSpecies");
                }
            }
        }

        Column {
            id: columnAvailableSpecies
            x: tvAvailableSpecies.x + tvAvailableSpecies.width + 10
            y: 150
            width: 90
            spacing: 20

            function speciesHasUnassignedDiscardReasonEntry(species) {
                // Check the selected species list:
                // Does it contain an entry for this species with an unassigned discard reason?

                var discardReason = null;
                var exists = appstate.catches.species.speciesWithDiscardReasonInSelected(
                        species, discardReason);
                return exists;
            }

            function checkAllSpeciesToBeAdded() {
                // Before adding one or more entries from the available species list,
                // check the already selected list, looking for an entry with that species
                // and as-yet unassigned discard reason.
                //
                // Enforces the constraint that each row in the selected list must
                // have a unique <species>+<discard-reason> combination key.
                // This method handles the unassigned-discard-reason; Counts and Weights
                // handles the cases where selected species rows have an assigned discard reason.
                //
                // Return the row ID of an offender, or -1 if no issues.
                var offendingRowIndex = -1
                tvAvailableSpecies.selection.forEach(
                    function(rowIndex) {
                        // Check tvSelectedSpecies TableView for an unassigned discard reason row
                        var newElem = tvAvailableSpecies.model.get(rowIndex);
                        if (speciesHasUnassignedDiscardReasonEntry(newElem.species)) {
                            console.debug("Species " + newElem.species +
                                    " already in selected w/o discard reason");
                            offendingRowIndex = rowIndex;
                        }
                    }
                )

                if (offendingRowIndex < 0) {
                    console.debug("No issues with any of species to be added.");
                }

                return offendingRowIndex;
            }

            function addSpeciesSelected() {
                if(stackView.busy) {
                    console.warn('(Prevented multiple category input.)')
                    return; // Prevent double-spaz-click multi-add
                }

                if (!tvAvailableSpecies.selection || tvAvailableSpecies.selection.count <1) {
                    console.debug('No species selected, not adding.')
                    return;
                }

                var offendingRowIndex = checkAllSpeciesToBeAdded();
                if (offendingRowIndex >= 0) {
                    // Can't proceed with add. Reject entire set for one offender.
                    var problemElem = tvAvailableSpecies.model.get(offendingRowIndex);
                    console.error("Species " + problemElem.species +
                            " already has an entry in Selected Species with unassigned Discard Reason.");
                    dlgSpeciesAlreadyInSelected.common_name = problemElem.common_name;
                    dlgSpeciesAlreadyInSelected.open();
                    return;
                }

                var addedElementIDs = [];
                tvAvailableSpecies.selection.forEach(
                    function(rowIndex) {
                        // Add the species to the tvSelectedSpecies TableView
                        var newElem = tvAvailableSpecies.model.get(rowIndex);
                        appstate.catches.species.addSpeciesCompItem(newElem.species)
                        console.log('Added Species ID# ' +
                                        newElem.species + ' (' +
                                        newElem.common_name + ')');
                        // Add the species to Trip List of species
                        appstate.catches.species.addSpeciesToTrip(newElem.species_code);
                    }
                )

                tvAvailableSpecies.selection.clear();
                enable_add_button(false);

                appstate.speciesName = "";  // ##??

                // Restore the full list just in case add occurred with keybd/filter in effect.
                // If the keyboard is up, leave it up. Just clear the filter.
                clear_species_filter();
            }

            Connections {
                target: tabView
                onSelectedCatchCatChanged: {   // When new Catch Category selected on first tab,
                    // and the new Catch Category is not skipping the Species and Counts/Weights tabs,
                    if (appstate.catches.currentSampleMethodIsSpeciesComposition) {
                        console.debug("Selected catch category changed (to one using Species Composition) ...")
                        // If there is a species auto-added (corresponding to C.C.) then select it
                        // The Biospecimens tab depends on a species being automatically selected.
                        columnAvailableSpecies.selectFirst();
                    } else if (appstate.catches.currentSampleMethodIsNoSpeciesComposition) {
                        console.debug("Selected catch category changed to one not using Species Composition; " +
                            "no action taken in SpeciesScreen.");
                    } else {
                        console.debug("Selected catch category does not yet have a sample method selected.");
                    }
                    if (btnAssocSpecies.checked) { // update associated species if shown
                        var current_cc = appstate.catches.currentCatch.catch_category.catch_category;
                        appstate.catches.species.setAvailableListModel('AssocSpecies', current_cc);
                    }

                }
            }

            function selectNewest() {
                // Select new item
                var newRow = tvSelectedSpecies.model.count - 1;
                if (newRow >= 0) {
                    tvSelectedSpecies.selection.clear();
                    tvSelectedSpecies.currentRow = newRow;
                    tvSelectedSpecies.selection.select(newRow);
                    enable_remove_button(true);
                    console.debug("Selected row " + newRow + ".");
                } else {
                    console.debug("Model is empty, clearing selection")
                    clearSelected();
                    enable_remove_button(false);
                }
                tvSelectedSpecies.activate_selected_species();
            }

            function selectFirst() {
                // Select topmost item
                if (tvSelectedSpecies.model.count > 0) {
                    console.debug("Model item count: " + tvSelectedSpecies.model.count)
                    tvSelectedSpecies.selection.clear();
                    tvSelectedSpecies.currentRow = 0;
                    tvSelectedSpecies.selection.select(0);

                    enable_remove_button(true);
                } else {
                    clearSelected();
                    enable_remove_button(false);
                }
                tvSelectedSpecies.activate_selected_species();
            }

            function clearSelected() {
                console.debug("Deselecting Selected Species list");
                tvSelectedSpecies.currentRow = -1;
                tvSelectedSpecies.clear_selection();
            }

            function getSelRow() {
                return tvSelectedSpecies.currentRow;
            }

            function getSelItem() {
                // Get currently selected item
                var selected_row = getSelRow();
                if (selected_row < 0)
                    return null;
                return tvSelectedSpecies.model.get(selected_row);
            }

            function removeSpecies() {

                var selected_row = getSelRow();
                var selected_item = getSelItem();
                if (selected_item === null)
                    return;

                appstate.catches.species.delSpeciesCompItem(selected_item.species_comp_item);
                // automatically removes from model

                // Select the first row and enable the Remove button
                selectFirst();

                setTabsEnabled();
            }

            function showConfirmRemove() {
                var selected_item = getSelItem();
                if( selected_item !== null) {
                    var confirm_label = "remove " + selected_item.common_name;
                    confirmRemoveSpecies.show(confirm_label, "remove_species");
                }
            }

            ObserverSunlightButton {
                id: btnAddSpecies
                text: qsTr("Add\n>")
                enabled: false
                onClicked: {
                    columnAvailableSpecies.addSpeciesSelected();
                }
            }
            ObserverSunlightButton {
                id: btnRemoveSpecies
                text: qsTr("Remove\n<")
                enabled: false
                onClicked: {
                    if (appstate.catches.species.counts_weights.dataExists ||
                        appstate.catches.biospecimens.dataExists) {
                        dlgSpeciesNotEmpty.display();
                    } else {
                        columnAvailableSpecies.showConfirmRemove();
                    }
                }
            }            
            FramNoteDialog {
                id: dlgSpeciesNotEmpty
                function display() {
                    var data_arr = [];
                    if (appstate.catches.species.counts_weights.dataExists)
                        data_arr.push("basket");
                    if (appstate.catches.biospecimens.dataExists)
                        data_arr.push("biospecimen");

                    var data_msg = data_arr.join(' and ');
                    message = "Cannot delete species with\n" + data_msg + " data.";
                    open();
                }
            }
        }

        ObserverTableView {
            id: tvSelectedSpecies
            x: columnAvailableSpecies.x + columnAvailableSpecies.width + 40
            y: tfSpeciesFilter.y
            width: main.width - tvAvailableSpecies.width - columnAvailableSpecies.width - 90
            height: tvAvailableSpecies.height + tfSpeciesFilter.height
            headerVisible: true

            model: appstate.catches.species.observerSpeciesSelectedModel
            // Sorting column (catch(_id)) isn't visible, but use this attribute to determine how model is sorted.
            sortIndicatorOrder: Qt.DescendingOrder  // Put newest catch category in top row.

            onRowCountChanged: {
                if (rowCount == 0) {
                    tvSelectedSpecies.clear_selection();
                }
                else {
                    // Initialization of "downstream" tab screens (Counts/Weights and Biospecimens)
                    // depends upon the Species screen having selected an entry in the Selected species.
                    // Somewhat arbitrary, but reasonable choice: select the top entry.
                    // The first entry is the only entry with one species (typical), and the
                    // most recently added entry with more than one species.
                    columnAvailableSpecies.selectFirst();
                }
            }

            Connections {
                // A change in catch disposition (retained or discarded), or a change in discard reason
                // (if disposition is discarded) may affect whether the Biospecimens tab should be
                // enabled. Call function to check whether Biospecimens should be enabled.
                target: appstate.catches.species
                onIsRetainedChanged: {
                    // Catch disposition, (R)etained or (D)iscarded, changed.
                    console.debug("SpeciesScreen got signal of change of disposition - activating selected species.");
                    tvSelectedSpecies.activate_selected_species();
                }
                onDiscardReasonChanged: {
                    // Catch disposition is discarded. Discard reason changed.
                    console.debug("SpeciesScreen got signal of change of discard reason - activating selected species.");
                    tvSelectedSpecies.activate_selected_species();
                }
            }

            Connections {
                target: appstate.catches
                onDispositionChanged: {
                    // Async handler

                    var catch_category_disposition = appstate.catches.getData('catch_disposition');
                    if (catch_category_disposition === 'R') {
                        console.warn('Clearing Discard Reasons - disposition changed to R');
                        appstate.catches.species.clearDiscardReasons();
                    }

                }
                onCatchRatioChanged: {
                    if (isWm15()) {
                        console.info("Ratio changed: trigger recalc of weights with ratio " + ratio);
                        tvSelectedSpecies.activate_recalc_all();
                    }
                }

            }

            Connections {
                target: appstate.catches.biospecimens
                onBioCountChanged: {
                    appstate.catches.species.updateBioCount(bio_count);
                }
            }
            TableViewColumn {
                role: "species_comp_item"
                title: "#"
                width: 42
            }
            TableViewColumn {
                role: "common_name"
                title: "Name"
                width: 160
            }
            TableViewColumn {
                role: "discard_reason"
                title: "D.R."
                width: 50
            }            
            TableViewColumn {
                role: "species_weight"
                title: "Sample Wt"
                width: 120
                delegate: Text {
                   text: styleData.value ? styleData.value.toFixed(2) : ""
                   font.pixelSize: 20
                   verticalAlignment: Text.AlignVCenter
                   horizontalAlignment: Text.AlignHCenter
               }
            }

            TableViewColumn {
                // Display tally value
                title: "Count"
                role: "species_number"
                width: 70
                delegate: Text {
                   text: styleData.value ? styleData.value: ""
                   font.pixelSize: 20
                   verticalAlignment: Text.AlignVCenter
                   horizontalAlignment: Text.AlignHCenter
               }
            }
            TableViewColumn {
                role: "avg_weight"
                title: "Avg Wt"
                width: 100
                visible: true
                delegate: Text {
                   text: styleData.value ? styleData.value.toFixed(2) : ""
                   font.pixelSize: 20
                   verticalAlignment: Text.AlignVCenter
                   horizontalAlignment: Text.AlignHCenter
               }
            }
            TableViewColumn {
                role: "bio_count"
                title: "# Bio"
                width: 70
                visible: true
                delegate: Text {
                   text: styleData.value ? styleData.value: ""
                   font.pixelSize: 20
                   verticalAlignment: Text.AlignVCenter
                   horizontalAlignment: Text.AlignHCenter
               }
            }

            function activate_recalc_all() {
                // intended only for use with WM15 (perf reasons)
                console.warn("Recalculating weights for all " + rowCount + " rows.");
                for (var i = 0; i < rowCount; i++) {
                    clear_selection();
                    currentRow = i;
                    selection.select(i);
                    activate_selected_species();
                    // delay needed?
                    clear_selection();
                }
            }
            function activate_selected_species() {
                appstate.catches.species.currentFGBiolist = appstate.sets.currentBiolistNum; // Track Biolist #'s


                // Handle No Species Composition elsewhere; this tab is disabled for NSC catches.
                if (appstate.catches.currentSampleMethodIsNoSpeciesComposition) {
                    console.info("Not activating species in SpeciesScreen; catch sample method is no species composition");
                    return;
                }

                // If any catch categories details haven't been specified, disable all the follow-on tabs.
                if (!appstate.catches.requiredCCDetailsAreSpecified) {
                    console.info("Not activating species, counts/weights, or biospecimens tabs: " +
                            "not all catch category details (sample method, weight method, etc) have been specified.");
                    tabView.enableSpeciesTab(false);
                    tabView.enableCountWeightTab(false);
                    tabView.enableBiospecimensTab(true);
                    return;
                }

                console.debug("Species Screen: Activate Selected Species, currentRow = " + tvSelectedSpecies.currentRow)
                var species = null;
                var is_phlb = false;
                if (currentRow >= 0) {
                    species = model.get(tvSelectedSpecies.currentRow);
                    if (species.species_comp_item === appstate.catches.species.currentSpeciesCompItemID) {
                        return;
                    }


                    appstate.catches.species.currentSpeciesCompItemID = species.species_comp_item;
                    appstate.speciesName = species.common_name;

                    // This isn't a NSC catch - see test and early return above. Set biospecimen's discard from species.
                    appstate.catches.biospecimens.currentParentDiscardReason = appstate.catches.species.discardReason;
                    appstate.catches.biospecimens.currentSpeciesID = species.species.species;

                    var halibut_code = 101;
                    if (appstate.catches.currentMatchingSpeciesId === halibut_code) {
                        tabView.enableCountWeightTab(false);
                        is_phlb = true;
                    }
                    tabView.enableCountWeightTab(true);
                } else {
                    console.debug("No species row selected");
                    appstate.catches.species.clearCurrentSpeciesItemID();
                    appstate.speciesName = "";
                    tabView.enableCountWeightTab(false);
                }
                tabView.enableSpeciesTab(!is_phlb);
                tabView.enableBiospecimensTab(true);
                tabView.selectedSpeciesChanged();
            }

            function clear_selection() {
                selection.clear();
                appstate.catches.biospecimens.currentSpeciesID = null;
                appstate.catches.species.clearCurrentSpeciesItemID();
                appstate.speciesName = "";

                enable_remove_button(false);
            }

            onClicked: {
                activate_selected_species();
                enable_remove_button(true);
            }
        }
        RowLayout {
            x: tvSelectedSpecies.x
            y: rowListSelect.y
            FramLabel {
                text: "Current Biolist:"
                font.pixelSize: 20
                width: 200
                height: 40
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignRight
            }
            ObserverTextField {
                id: bioListText
                readOnly: true
                text: appstate.sets.currentBiolistNum
                font.pixelSize: 20
                Layout.preferredWidth: 50
            }
        }
    } // ListView


    FramSlidingKeyboard {
        id: slidingKeyboardSpecies
        width: tvSelectedSpecies.width + 30 // Fudge factor of 30 gets keyboard in right position
        x: columnAvailableSpecies.x + columnAvailableSpecies.width
        anchors.left: columnAvailableSpecies.right
        anchors.bottom: lvSp.bottom
        visible: false
        ok_text: "Cancel"
        enable_audio: ObserverSettings.enableAudio
        onButtonOk: {
            // OK button operates as cancel:
            hide_keyboard_clear_species_filter();
        }
    }

    ////
    // Pop-up Dialogs
    ////
    FramConfirmDialog {
        id: confirmRemoveSpecies
        visible: false
        anchors.horizontalCenterOffset: -1 * parent.width/3
        anchors.verticalCenterOffset: -1 * parent.height/5

        onConfirmedFunc: {
            console.debug("Confirmed " + action_name);
            columnAvailableSpecies.removeSpecies();
            visible = false;
        }
    }

    FramNoteDialog {
        id: dlgSpeciesAlreadyInSelected
        property string common_name
        message: "Error:" +
            "\nSpecies '" + common_name + "'" +
            "\nis already in Selected Species list " +
            "\nwithout a discard reason specified."
    }
}

