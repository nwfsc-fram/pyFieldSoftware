import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.2
import QtQml.Models 2.2

import "../common"
import "."
import "codebehind/HelperFunctions.js" as HelperFunctions

Item {
    id: screenCCFGEntry

    property string noScaleText: "-1"; // Stored in DB instead of cal value

    function page_state_id() { // for transitions
        return "cc_entry_fg_state";
    }
    property var ccdetailsPage
    property int dec_places: appstate.displayDecimalPlaces  // Number of decimal places to display weight values

    Component.onCompleted: {
        initUI();
    }

    function initUI() {
        slidingKeyboardCC.showbottomkeyboard(false);  // init sizing
        //run_automated_tests();


        var curhaulcatches = appstate.isFixedGear ?
        appstate.catches.load_catches(appstate.sets.current_fishing_activity_id) :
        appstate.catches.load_catches(appstate.hauls.current_fishing_activity_id);

        console.debug("Current Trip ID = " + appstate.currentTripId);

        enable_add_button(false);
        enable_remove_and_edit_buttons(false);
        hide_keyboard_clear_category_filter();

        var cal_weight = appstate.isFixedGear ? appstate.sets.getData('cal_weight') : appstate.hauls.getData('cal_weight');
        if (cal_weight) {
            switch (cal_weight) {
            case "11.00":
                btnWeightCal1100.checked = true;
                break;
            case "11.05":
                btnWeightCal1105.checked = true;
                break;
            case noScaleText:
                btnWeightCalNoScale.checked = true;
                break;
            }
        }
    }

    function showBioNeededWarning(warning) {
        console.warn(warning);
        dlgBioWarning.message = warning;
        dlgBioWarning.open();
    }

    TrawlOkayDialog {
        id: dlgBioWarning
        title: "Sample required/requested"
    }

    Timer {
        id: timer
    }

    // Define a signal here for the benefit of CCDetailsScreen, from where it's sent.
    // Defined here because as the parent, this CCScreen can pass properties to the "pushed" child, CCDetailsScreen.
    // I.e. CCDetailsScreen can use a signal defined here, but a signal defined there won't be received here.
    signal catchCatsDetailsFGCompleted
    onCatchCatsDetailsFGCompleted: {
            console.debug("CCDetailsFGScreen signaled: details completed.");
            // Activate the catch category so on transition to Biospecimens tab, that screen is enabled.
            tvSelectedCatchCat.activate_CC_selected();
    }

    function hide_keyboard_clear_category_filter() {
        // Hide the keyboard, clear the catch category textbox, take the cannoli.
        slidingKeyboardCC.showbottomkeyboard(false);
        tfCatchCategory.text = "";
        catchCategory.resetActiveList();
    }

    function delay(delayTime, cb) {
        timer.interval = delayTime;
        timer.repeat = false;
        timer.triggered.connect(cb);
        timer.start();
    }

    function run_automated_tests() {
        if (!ObserverSettings.run_automated_tests)
            return 0;
        // TODO Fully automated tests
        //        tvAvailableCC.selection.select(1); // choose CC
        //        delay(700, function() {
        //            columnAvailableCC.addCatchCat(); // add CC
        //            observerFooterRow.clickedDone(); // OK the details (delay or we get recursion guard error)
        //        } )
    }

    function add_button_is_enabled() {
        return btnAddCatchCategory.state == "enabled";
    }

    function enable_add_button(do_enable) {
        console.debug("Add button set " + do_enable);
        btnAddCatchCategory.enabled = do_enable;
    }

    function enable_remove_and_edit_buttons(do_enable) {
        console.debug("Remove button set " + do_enable);
        btnRemoveCatchCategory.enabled = do_enable;
        btnEditCC.enabled = do_enable;
    }

    signal resetFocus()
    onResetFocus: {
        // Just set focus to something benign
        tvAvailableCC.forceActiveFocus();
    }

    function isWM3() {
        var isWeightMethod3 = appstate.catches.weightMethod === '3';
        console.debug("isWM3=" + isWeightMethod3);
        return isWeightMethod3;
    }

    Keys.forwardTo: [slidingKeyboardCC] // Capture of Enter key

    ListView
    {
        id: lvCC
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        height: main.height - framFooter.height - framHeader.height

        TextField {
            id: tfCatchCategory
            x: 20
            y: 20
            height: 40
            width: 400
            placeholderText: qsTr("Catch Category")
            font.pixelSize: 20

            onTextChanged: {
                updateCatchCatText();
            }

            function updateCatchCatText() {
                catchCategory.filter = text;
                if (catchCategory.filter_matches_code) {
                    var matchingRow = get_row_with_code(text);
                    console.debug("Filter matches a code ('" + text + "') on Row " + matchingRow + ".");
                    tvAvailableCC.selection.clear();
                    tvAvailableCC.currentRow = matchingRow;
                    tvAvailableCC.selection.select(matchingRow);
                    enable_add_button(true);
                    tvAvailableCC.available_row_idx_when_add_enabled = matchingRow;
                }
                else {
                    enable_add_button(false);
                }
            }

            function get_row_with_code(code) {
                // If a row in tvAvailableCC has the specified code, return index of that row
                var r = 0;
                for (r = 0; r < tvAvailableCC.model.count; r++) {
                    var rowcode = tvAvailableCC.model.get(r).catch_category_code;
                    if (rowcode === code) {
                        console.debug("Code match of " + code + " on row " + r);
                        return r;
                    }
                }
                console.error("Failed to find match in tvAvailableCC for code = " + code);
                return 0; // Shouldn't happen
            }

            signal userCCSelected
            onUserCCSelected: {
                // Active focus seems to get set when switching to this page,
                // so this is an explicit slot for user clicks
                slidingKeyboardCC.showbottomkeyboard(true);
                slidingKeyboardCC.connect_tf(tfCatchCategory);

                // Clear any existing selection, disable the Add button.
                tvAvailableCC.selection.clear();
                enable_add_button(false);

                forceActiveFocus();
            }

            MouseArea {
                anchors.fill: parent
                propagateComposedEvents: true
                onClicked: {
                    tfCatchCategory.userCCSelected();
                }
            }
        }

        ObserverTableView {
            id: tvAvailableCC
            x: tfCatchCategory.x
            y: tfCatchCategory.y + tfCatchCategory.height + 10
            width: tfCatchCategory.width
            height: parent.height - tfCatchCategory.height - 110
            headerVisible: false

            property var fullModel: catchCategory.catchCategoryFullModel
            property var frequentModel: catchCategory.catchCategoryFrequentModel
            property var tripModel: catchCategory.catchCategoryTripModel

            // Track what row in available list was selected with Add button was last enabled
            property int available_row_idx_when_add_enabled: -1

            model: fullModel

            onClicked: {    // Passes a parameter, "row", the index of the selected row
                console.debug("Index of row selected = " + row);
                var current_available_row_idx = row;
                // If click occurs when a single catch category has been selected/highlighted,
                // and it's the same row when the Add button was enabled, add it on a single-click,
                // else highlight the row selected and enable the add button.
                if (add_button_is_enabled() && (current_available_row_idx === available_row_idx_when_add_enabled)) {
                    columnAvailableCC.addCatchCat();
                    available_row_idx_when_add_enabled = -1;
                } else {
                    enable_add_button(true);
                    available_row_idx_when_add_enabled = current_available_row_idx;
                }
            }

            TableViewColumn {
                role: "catch_category_code"
                title: "Code"
                width: 75
            }
            TableViewColumn {
                role: "catch_category_name"
                title: "Name"
                width: tfCatchCategory.width
            }
        }

        function toggleList(whichList) {
            tvAvailableCC.selection.clear();
            enable_add_button(false);
            hide_keyboard_clear_category_filter();  // Just in case autocomplete keyboard is up.
            if (whichList === "Full") {
                tvAvailableCC.model = catchCategory.catchCategoryFullModel;
                tfCatchCategory.visible = true; // Enable autocomplete filtering on Full
                console.info("Switching active catch category model to Full");
            } else if (whichList === "Frequent") {
                tvAvailableCC.model = catchCategory.catchCategoryFrequentModel;
                tfCatchCategory.visible = true; // Enable autocomplete filtering on Frequent
                console.info("Switching active catch category model to Frequent");
            } else if (whichList === "Trip") {
                catchCategory.initializeTripListCccs(appstate.currentTripId);
                tvAvailableCC.model = catchCategory.catchCategoryTripModel;
                tfCatchCategory.visible = true; // Enable autocomplete filtering on Trip
                console.info("Switching active catch category model to Trip");
            } else {
                console.error("Unrecognized catch category list '" + whichList + "'.");
                return;
            }
            catchCategory.setActiveListModel(whichList);
        }

        GroupBox {
            id: gbListSelect
            x: tvAvailableCC.x
            y: tvAvailableCC.y + tvAvailableCC.height + 10
            style: Style {
                property Component panel: Rectangle {
                    color: "transparent"
                    border.width: 0
                }
            }
            ExclusiveGroup {
                id: grpList
            }
           ObserverGroupButton {
                id: btnFullList
                text: qsTr("Full\nList")
                x: tvAvailableCC.x
                y: parent.y
                checked: true
                checkable: true
                exclusiveGroup: grpList
                onClicked: {
                    lvCC.toggleList("Full");
                }
            }
            ObserverGroupButton {
                id: btnFrequentList
                text: qsTr("Frequent\nList")
                x: btnFullList.x + btnFullList.width + 10
                y: parent.y
                checkable: true
                exclusiveGroup: grpList
                onClicked: {
                    lvCC.toggleList("Frequent");
                }

            }
             ObserverGroupButton {
                id: btnTripList
                text: qsTr("Trip\nList")
                x: btnFrequentList.x + btnFrequentList.width + 10
                y: parent.y
                checkable: true
                exclusiveGroup: grpList
                onClicked: {
                    lvCC.toggleList("Trip");
                }
            }
        }

        Column {
            id: columnAvailableCC
            x: tvAvailableCC.x + tvAvailableCC.width + 10
            y: 150
            width: 90
            spacing: 20

            function addCatchCat() {
                if(stackView.busy) {
                    console.warn('(Prevented multiple category input.)')
                    return; // Prevent double-spaz-click multi-add
                }

                if (!tvAvailableCC.selection || tvAvailableCC.selection.count <1) {
                    console.debug('No CC selected, not adding.')
                    return;
                }

                var newElem = tvAvailableCC.model.get(tvAvailableCC.currentRow);

                // Current row should be in range, but in some as yet uncharacterized cases it is not.
                // Show unusual condition dialog asking observer to email OPTECS team about the event.

                // This occurred when a search was entered in Frequent List, e.g. "P" and an item selected and added.
                // When we come out of the CC Details page, the selected row no longer corresponds to current model.
                // Fixed in FIELD-1410
                if (newElem === undefined || newElem.catch_category === undefined) {
                    console.warn('Row ' + tvAvailableCC.currentRow + ' is undefined. Not adding catch category.');
                    console.warn("(newElem='" + newElem + "', its catch_category='" + newElem.catch_category + "').");

                    // Notify observer of unusual condition, asking for email notification of problem:
                    var msg = "Invalid row index for Available Catch Categories table";
                    var parentWindow = screenCCFGEntry;
                    HelperFunctions.openUnusualConditionDialog(msg, parentWindow);

                    return;
                }

                // Add the catch category to the tvSelectedCatchCat TableView
                // Used to allow multiselect, but that won't work with edit details
                appstate.create_catch(newElem.catch_category);

                console.log('Added Catch Category ID# ' +
                                newElem.catch_category + ' (' +
                                newElem.catch_category_code + ')');

                appstate.catchCatName = newElem.catch_category_code;

                // Add newly selected catch category to trip list of catch categories.
                catchCategory.addCodeToTrip(newElem.catch_category_code);

                // About to transition away from this screen. Restore state to that desired upon return to this screen.
                hide_keyboard_clear_category_filter();

                // Highlight new entry in Selected Catch Categories.
                if (tvSelectedCatchCat.model.count >= 1) {
                    tvSelectedCatchCat.selectNewest();
                    console.debug("Selected newest entry in Selected Catch Category.");
                }

                // automatically jump to CC details
                obsSM.state_change("cc_details_state");
                var newestEntry = tvSelectedCatchCat.getNewestRowIdx();
                tvSelectedCatchCat.editItemDetails(newestEntry);
            }

            function removeCatchCat() {

                var selected_row = tvSelectedCatchCat.getSelRow();
                var selected_item = tvSelectedCatchCat.getSelItem();
                if (selected_item === null)
                    return;

                tvSelectedCatchCat.model.remove(selected_row);
                tvSelectedCatchCat.selection.clear();
                appstate.catches.deleteCatch(selected_item.catch)

                // Disable Remove button until another row is selected
                enable_remove_and_edit_buttons(false);

                // Disable navigation to other tabs.
                tabView.enableEntryTabs(false);
                appstate.catchCatName = ""
                appstate.catches.currentCatch = null
            }

            function showConfirmRemove() {
                var selected_item = tvSelectedCatchCat.getSelItem();
                if( selected_item !== null) {
                    confirmRemoveCC.categ_name = selected_item.catch_category_code + '\n(' +
                            selected_item.catch_category_name + ')'
                    confirmRemoveCC.visible = true;
                }
            }

            ObserverSunlightButton {
                id: btnAddCatchCategory
                text: qsTr("Add\n>")
                onClicked: {                    
                    columnAvailableCC.addCatchCat();
                    tvSelectedCatchCat.selection.clear();
                    tvAvailableCC.selection.clear();
                }                
            }
            ObserverSunlightButton {
                id: btnRemoveCatchCategory
                text: qsTr("Remove\n<")
                onClicked: {
                    var hasSpeciesData = (appstate.catches.species.observerSpeciesSelectedModel.count > 0);
                    var hasWM3BasketData = appstate.catches.catchBaskets.hasWM3BasketData;

                    // Check Weight Method 3 data first. Deleting WM3 data, then species data, works w/o issue.
                    // Deleting species data first leaves Counts/Weights screen visible but disabled.
                    if (hasWM3BasketData) {
                        dlgCCHasWM3BasketData.display();
                        return;
                    }

                    if (hasSpeciesData) {
                        dlgCCHasSpecies.display();
                        return;
                    }

                    columnAvailableCC.showConfirmRemove();
                }
            }
            FramNoteDialog {
                id: dlgCCHasSpecies
                function display() {
                    var spec_count = appstate.catches.species.observerSpeciesSelectedModel.count;
                    message = "Cannot delete catch category.\nContains " + spec_count +
                            " species comp " + (spec_count > 1 ? "entries." : "entry.");
                    open();
                }
            }

            FramNoteDialog {
                id: dlgCCHasWM3BasketData
                function display() {
                    message = "Cannot delete catch category.\nContains Weight Method 3 data.\n" +
                            "Please remove using button\n'" + btnWeightMethod3Data.text + "'.";
                    open();
                }
            }
        }

        ObserverTableView {
            id: tvSelectedCatchCat
            x: columnAvailableCC.x + columnAvailableCC.width + 40
            y: tfCatchCategory.y
            width: login.width - tvAvailableCC.width - columnAvailableCC.width - 90
            height: tvAvailableCC.height + tfCatchCategory.height
            selectionMode: SelectionMode.SingleSelection

            model: appstate.catches.CatchesModel
            // Sorting column (catch(_id)) isn't visible, but use this attribute to determine how model is sorted.
            sortIndicatorOrder: Qt.DescendingOrder  // Put newest catch category in top row.

            function updatedSampleMethod() {
                // Only allow later tabs to be enabled if the necessary Catch Category details have been specified.
                var ccDetailsAreSpecified = appstate.catches.requiredCCDetailsAreSpecified;

                var smIsSC = appstate.catches.currentSampleMethodIsSpeciesComposition;
                var smIsNSC = appstate.catches.currentSampleMethodIsNoSpeciesComposition;
                console.debug("ccDetailsAreSpecified=" + ccDetailsAreSpecified + ", SM=" + appstate.catches.sampleMethod +
                        ", smIsSC=" + smIsSC + ", smIsNSC=" + smIsNSC);

                // Tab enable/disable
                tabView.enableSpeciesTab(ccDetailsAreSpecified && smIsSC);
                tabView.enableCountWeightTab(ccDetailsAreSpecified && smIsSC);
                var smIsScAndDiscardReasonSpecified = smIsSC && (appstate.catches.species.discardReason !== undefined);
                if (smIsSC) {
                    console.debug("IsSC; species's discard reason is '" + appstate.catches.species.discardReason + "'");
                }
                tabView.enableBiospecimensTab(ccDetailsAreSpecified && (smIsNSC || smIsScAndDiscardReasonSpecified));

                // Update Species Composition ID if species composition sampling method was specified.
                // Set to undefined if no species composition or sampling method not defined.
                if (smIsSC) {
                    console.log("Setting species comp ID to '" +
                            appstate.catches.currentCompID + "'.");
                    appstate.catches.species.currentSpeciesCompID = appstate.catches.currentCompID;
                } else if (smIsNSC) {
                    console.info("No species composition; clearing species comp ID");
                    appstate.catches.species.currentSpeciesCompID = null;
                } else {
                    console.info("No sample method specified; setting currentSpeciesCompID to '" +
                            appstate.catches.species.currentSpeciesCompID + "'.");
                    appstate.catches.species.currentSpeciesCompID = null;
                }
            }

            function activate_CC_selected() {
                if (model.count <1 || model === null || model.get(currentRow) === null) {
                    console.error("model.count=" + model.count + ", model=" + model + ", currentRow=" + currentRow);
                    return false;
                }
                var selectedCC = model.get(currentRow);  // Not just currentIndex!

                appstate.catches.currentCatch = selectedCC;
                appstate.catchCatName = selectedCC.catch_category_code;
                console.info("Set appstate.catchCatName to '" + appstate.catchCatName + "'.");
                console.info("Setting appstate.catches.sampleMethod; was='" + appstate.catches.sampleMethod +
                        "', now='" + selectedCC.sample_method + "'.");
                appstate.catches.sampleMethod = selectedCC.sample_method;
                tvSelectedCatchCat.updatedSampleMethod();
                appstate.catches.species.isRetained = // for protocols
                            (appstate.catches.getData('catch_disposition') === 'R');

                // Only activate WM3 Baskets button if new CC is WM3
                btnWeightMethod3Data.visible = screenCCFGEntry.isWM3();
                console.debug("btnWM3.visible=" + screenCCFGEntry.isWM3());

                // Biospecimen setup
                appstate.catches.biospecimens.currentCatchID = selectedCC.catch;
                appstate.catches.biospecimens.currentWM = appstate.catches.weightMethod;
                appstate.catches.biospecimens.currentCatchDisposition = appstate.catches.getData('catch_disposition');
                // If the catch is No Species Composition, specify the catch's matching species and its discard reason.
                if (appstate.catches.sampleMethod === 'NSC') {
                    console.debug("NSC Catch: setting Biospecimen's parent discard reason to the catch's");
                    appstate.catches.biospecimens.currentParentDiscardReason = appstate.catches.getData('discard_reason');
                    console.debug("NSC Catch: setting Biospecimen's species to the catch's");
                    appstate.catches.biospecimens.currentSpeciesID = appstate.catches.currentMatchingSpeciesId;
                }

                enable_remove_and_edit_buttons(true);
                console.info('beginning of the line !!!!!!!!!!!!!!!!!!!!!!!!!!!!');
                tabView.selectedCatchCatChanged(); // Notify.
                console.info('end of the line !!!!!!!!!!!!!!!!!!!!!!!!!!!!');
                return true;
            }


            Connections {
                target: appstate.catches

                onSampleMethodChanged : {
                    console.debug("Connection in tvSelectedCatchCat received sample method change to " + sample_method);
                    tvSelectedCatchCat.updatedSampleMethod();
                }

                onDispositionChanged: {
                    console.debug("Connection in tvSelectedCatchCat received catch disposition change signal.");
                    // Notify Biospecimens tab et al of change.
                    tvSelectedCatchCat.activate_CC_selected();
                }

                onDiscardReasonChanged: {
                    console.debug("Connection in tvSelectedCatchCat received catch discard reason change signal.");
                    // Notify Biospecimens tab et al of change.
                    tvSelectedCatchCat.activate_CC_selected();
                }
            }

            // Persist to DB any changes to total fish weight made in CountsWeightsScreen
            // This connection handles Species weights, but not Weight Method 3, which is not at the species level.
            Connections {
                target: appstate.catches.species

                function handleTotalCatchChangedSignal(
                        parmValue) {

                    var curModel = tvSelectedCatchCat.getSelItem();
                    if (!curModel) {
                        log.error("Unexpected error: received a total " + parmName + " changed signal with no selected " +
                                "catch category.");
                        return;
                    }
                    appstate.catches.setData("sample_weight", parmValue);
                }

                onTotalCatchWeightFGChanged: {    // Parameter: weight
                    // console.debug("CATCH FG WEIGHT CHANGED")
                    handleTotalCatchChangedSignal(weight);
                    if (weight) {
                        //handleTotalCatchChangedSignal(weight);
                    }

                }
                onTotalCatchWeightChanged: {    // Parameter: weight
                    // console.debug("CATCH WEIGHT CHANGED")
                    handleTotalCatchChangedSignal(weight);
                }
            }

            Connections {
                target: appstate.catches.biospecimens
                onTotalPHLBWeightChanged: {
                    if (weight) {
                        appstate.catches.setData("sample_weight", weight);
                        appstate.catches.species.totalCatchWeightChanged(weight)
                    }
                }
            }
            onCurrentRowChanged:{
                activate_CC_selected();
            }

            onClicked: {
                activate_CC_selected();
                enable_remove_and_edit_buttons(true);
                console.debug("Row " + tvSelectedCatchCat.currentRow + " highlighted.");
            }

            function getSelRow() {
                return currentRow;
            }

            function getSelItem() {
                // Get currently selected item
                var selected_row = getSelRow();
                if (selected_row < 0)
                    return null;
                return model.get(selected_row);
            }

            function getNewestRowIdx() {
                var newestRowIdx = (tvSelectedCatchCat.sortIndicatorOrder == Qt.AscendingOrder) ?
                        tvSelectedCatchCat.model.count - 1 : 0;
                return newestRowIdx;
            }

            function selectRow(row) {
                tvSelectedCatchCat.selection.clear();
                tvSelectedCatchCat.currentRow = row;
                tvSelectedCatchCat.selection.select(row);
                if (!tvSelectedCatchCat.activate_CC_selected()) {
                    console.warn("activate_CC_selected() returned false.");
                }
                console.debug("Row " + row + " highlighted.");
            }

            function selectNewest() {
                var newRow = getNewestRowIdx();
                if (newRow >= 0) {
                    selectRow(newRow);
                }
            }

            function editItemDetails(item_index) {
                var detailProps = {
                    // properties for CC details page
                    'ccModel': model,
                    'ccIndex': item_index,
                    'ccScreenId': screenCCFGEntry}
                var ccdetailsPage =
                        stackView.push(
                            {item: Qt.resolvedUrl("CatchCategoriesDetailsFGScreen.qml"),
                             properties: detailProps});
            }

            function editItemBaskets(item_index) {  // For WM3 catch-level basket data
                // TODO - disabled for FG
                var ccBasketsPage = stackView.push(Qt.resolvedUrl("CatchCategoriesBasketsScreen.qml"));
            }

            TableViewColumn {
                role: "catch_disposition"
                title: "R/D"
                width: 55

            }
            TableViewColumn {
                role: "catch_category_code"
                title: "Code"
                // CATCH_CATEGORIES.CATCH_CATEGORY_CODE is at most 6 digits (max in DB)
                width: 80
            }
//            TableViewColumn {
//                role: "sample_weight"
//                title: "Weight"
//                width: 100
//                horizontalAlignment: Text.AlignRight    // Column header
//                delegate: Text {
//                    text: styleData.value ? styleData.value.toFixed(dec_places) : ""
//                    font.pixelSize: 20
//                    verticalAlignment: Text.AlignVCenter
//                    horizontalAlignment: Text.AlignRight  // Cell text
//                }
//            }
//            TableViewColumn {
//                role: "sample_count"
//                title: "Count"
//                width: 80
//                horizontalAlignment: Text.AlignRight
//            }
            TableViewColumn {
                role: "sample_weight"
                title: "Weight"
                width: 100
                horizontalAlignment: Text.AlignRight    // Column header
                delegate: Text {
                    text: styleData.value ? styleData.value.toFixed(dec_places) : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignRight  // Cell text
                }
            }
            TableViewColumn {
                role: "sample_count"
                title: "Count"
                width: 80
                horizontalAlignment: Text.AlignRight
            }
            TableViewColumn {
                role: "catch_weight_method"
                title: "Wt Meth"
                width: 100
                delegate: Text {
                    text: styleData.value ? styleData.value : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            TableViewColumn {
                role: "discard_reason"
                title: "D. Reas."
                width: 100
                delegate: Text {
                    text: styleData.value ? styleData.value : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            TableViewColumn {
                role: "gear_segments_sampled"
                title: "Gear Units Samp."
                width: 250
                visible: true
                delegate: Text {
                    text: styleData.value ? styleData.value : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
            }

            TableViewColumn {   // For debugging. Typically set to be invisible
                role: "catch"   // Table primary key, incremented with each entry added
                title: "ID"
                width: 50
                visible: false   // Make visible for debugging - to check sort order.
            }
//            TableViewColumn {
//                role: "notes"
//                title: "Notes"
//                width: 200
//            }
        }

        Row {
            x: tvSelectedCatchCat.x
            y: tvSelectedCatchCat.y + tvSelectedCatchCat.height + 10
            spacing: 10

            ObserverSunlightButton {
                id: btnEditCC
                text: qsTr("Edit\nDetails")
                onClicked: {
                    var row = tvSelectedCatchCat.getSelRow();
                    if ( !stackView.busy && row >= 0) {
                        obsSM.state_change("cc_details_state");
                        tvSelectedCatchCat.editItemDetails(tvSelectedCatchCat.getSelRow());
                    }
                    // For reasons not yet determined, when editing a selected category with a weight measure 6,
                    // upon return the row is no longer highlighted. This fixes that idiosyncracy in
                    // one but not all cases: When one returns without using the numpad.
                    tvSelectedCatchCat.selectRow(row);
                }
            }
            ObserverSunlightButton {
                id: btnWeightMethod3Data
                text: qsTr("Wt Meth 3\nBasket Data")
                visible: isWM3()
                enabled: isWM3()
                checked: false  // TODO: turn on if basket data has not been entered?
                onClicked: {
                    console.debug("WM3 Button pushed!");
                    console.debug("And it thinks current WM='" + appstate.catches.weightMethod + "',");

                    var row = tvSelectedCatchCat.getSelRow();
                    if (!stackView.busy && row >= 0) {
                        obsSM.state_change("cc_baskets_state");
                        tvSelectedCatchCat.editItemBaskets(tvSelectedCatchCat.getSelRow());
                    }
                    // For reasons not yet determined, when editing a selected category with a weight measure 6,
                    // upon return the row is no longer highlighted. This fixes that idiosyncracy in
                    // one but not all cases: When one returns without using the numpad.
                    tvSelectedCatchCat.selectRow(row);
                }
            }
            // WM3 Catch Weight will be displayed in list of catch categories

            ColumnLayout {
                Label {
                    id: labelFit
                    text: qsTr("Fit #")
                    Layout.preferredWidth: 50
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 20

                }
                TextField {
                    id: tfFit
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 30
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 20
                    placeholderText: labelFit.text
                    text: appstate.isFixedGear ? appstate.sets.getData('fit') : appstate.hauls.getData('fit')
                    onActiveFocusChanged: {
                        if (focus) {
                            // TODO load initUI();
                            focus = false;  // otherwise, dialogs opened forever
                            numpadFit.open()
                        }
                    }
                    onTextChanged: {
                        if (appstate.isFixedGear)
                          appstate.sets.setData('fit', text)
                        else
                          appstate.hauls.setData('fit', text);
                    }
                }
            }

            ObserverNumPadDialog {
                id: numpadFit
                max_digits: 2
                placeholderText: tfFit.placeholderText
                enable_audio: ObserverSettings.enableAudio
                onValueAccepted: {
                    tfFit.text = accepted_value;
                }
            }

            FramLabelHighlightCapable {
                id: labelWeightCal
                text: qsTr("Weight\nCalib.")
                Layout.preferredWidth: 100
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignRight
                font.pixelSize: 20

            }
            RowLayout {
                ExclusiveGroup {
                    id: btnWeightCalGrp
                }

                ObserverGroupButton {
                    id: btnWeightCal1100
                    exclusiveGroup: btnWeightCalGrp
                    text: "11.00"
                    Layout.preferredWidth: 80
                    Layout.preferredHeight: ObserverSettings.default_tf_height
                    font_size: 18
                    onCheckedChanged: {
                        if (checked) {
                            if(appstate.isFixedGear)
                              appstate.sets.setData('cal_weight', text)
                            else
                              appstate.hauls.setData('cal_weight', text)
                        }
                    }
                }
                ObserverGroupButton {
                    id: btnWeightCal1105
                    exclusiveGroup: btnWeightCalGrp
                    text: "11.05"
                    Layout.preferredWidth: btnWeightCal1100.width
                    Layout.preferredHeight: ObserverSettings.default_tf_height
                    font_size: 18
                    onCheckedChanged: {
                        if (checked) {
                            if(appstate.isFixedGear)
                              appstate.sets.setData('cal_weight', text)
                            else
                              appstate.hauls.setData('cal_weight', text)
                        }
                    }
                }
                ObserverGroupButton {
                    id: btnWeightCalNoScale
                    exclusiveGroup: btnWeightCalGrp
                    text: "Scale\nNot Used"
                    Layout.preferredWidth: btnWeightCal1100.width
                    Layout.preferredHeight: ObserverSettings.default_tf_height
                    font_size: 15
                    onCheckedChanged: {
                        if (checked) {
                            var current_cal = appstate.isFixedGear ? appstate.sets.getData('cal_weight') : appstate.hauls.getData('cal_weight');
                            if (current_cal !== noScaleText) {
                                framFooter.openComments("Scale Not Used Selected. Enter Reason: ");
                            }
                            if(appstate.isFixedGear)
                              appstate.sets.setData('cal_weight', noScaleText)
                            else
                              appstate.hauls.setData('cal_weight', noScaleText)
                        }
                    }
                }
            }
        }

        FramSlidingKeyboard {
            id: slidingKeyboardCC
            width: columnAvailableCC.width + tvSelectedCatchCat.width
            x: columnAvailableCC.x
            anchors.left: columnAvailableCC.left
            visible: false
            anchors.bottom: lvCC.bottom
            ok_text: "Cancel"
            enable_audio: ObserverSettings.enableAudio
            onButtonOk: {
                // OK button operates as cancel:
                hide_keyboard_clear_category_filter();
            }
        }
    } // ListView

    FramConfirmDialog {
        id: confirmRemoveCC
        visible: false
        property string categ_name: ""
        action_label: qsTr("Remove " + categ_name) // Are you sure you want to _____ ?

        anchors.horizontalCenterOffset: -1 * parent.width/3
        anchors.verticalCenterOffset: -1 * parent.height/5

        onConfirmed: {
            columnAvailableCC.removeCatchCat();
            visible = false;
        }
    }
}
