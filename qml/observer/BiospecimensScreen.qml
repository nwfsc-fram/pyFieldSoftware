import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Dialogs 1.2

import "../common"
import "."

ColumnLayout {
    id: screenBio

    property bool stateBio: false
    property alias modifyEntryChecked: bModifyEntry.checked

    property BioSLWScreen slw_screen: null  // screens set on component complete
    property BioViabilityScreen via_screen: null
    property BioTagsScreen tags_screen: null
    property BioBarcodesScreen barcodes_screen: null
    property int dec_places: appstate.displayDecimalPlaces  // Number of decimal places to display weight values

    signal addEntry()
    Timer {
        id: timer
    }

    Component.onCompleted: {
        appstate.catches.biospecimens.isFixedGear = appstate.isFixedGear;
    }

    function delay(delayTime, cb) {
        timer.interval = delayTime;
        timer.repeat = false;
        timer.triggered.connect(cb);
        timer.start();
    }

    function selectNewestRow() { // newest = top row
        tvBioEntries.selection.clear();
        tvBioEntries.currentRow = 0;
        tvBioEntries.selection.select(tvBioEntries.currentRow);
    }

    function unselect() {
        // deselect all in tv model
        tvBioEntries.selection.clear()
        tvBioEntries.currentRow = -1
    }

    function set_biospecimen_species_from_catch_category() {
        // I don't think this should be necessary here in Biospecimens, so encapsulate for possible deletion.
        // Species tab is disabled. Set up species here using matching species from catch category.
        // Should only be used if catch's sample method is no species composition.
        var matchingSpeciesId = appstate.catches.currentMatchingSpeciesId;
        if (matchingSpeciesId === null) {
            console.debug("Catch category does not have a matching species.");
        }
        // ## Shouldn't this have been done in Catch Category's active_cc_selected()?
        appstate.catches.biospecimens.currentSpeciesID = matchingSpeciesId;
        console.debug("NSC Catch: setting current species ID to CatchCat's matching species ID =" + matchingSpeciesId);
        // Setting currentSpeciesID above sets currentSpeciesCommonName.
    }

    function set_tabs_for_no_species_composition() {

        tabView.enableSpeciesTab(false);
        tabView.enableCountWeightTab(false);
        // If all the needed Catch Category detail information has been entered (e.g. weight method, purity),
        // allow Biospecimens to be entered.
        tabView.enableBiospecimensTab(appstate.catches.requiredCCDetailsAreSpecified);
    }

    function set_biospecimen_context() {
        // Seems a strange place to set the general appstate's species, but Biospecimens knows
        // whether the species is coming from the Species tab or if no species composition,
        // from the species matching the NSC catch category.
        appstate.speciesName = appstate.catches.biospecimens.currentSpeciesCommonName;

        tfSpecies.text = appstate.catches.biospecimens.currentSpeciesCommonName;
        tfProtocol.text = appstate.catches.species.currentProtocols;
        var biolist = appstate.catches.species.currentBiolist;
        if (biolist && biolist.length > 0) {
            tfProtocol.text += " (" + biolist + ")";
        }

        clear_selection();
        // Clear Biosample Method, which will clear (disable) Add and Delete Entry buttons.
        labelBSMethodDesc.reset();
        // For reason not clear, clearing Biosample Method doesn't disable Modify Entry button. Do so explicitly.
        bModifyEntry.enabled = false;
        bModifyEntry.checked = false;
    }

    function add_new_biospecimen_entry() {
        // Return true if successful.
        if(!labelBSMethodDesc.is_selected()) {
            dlgSelectBMWarning.open();
            return false;
        }

        console.log("* New Entry")
        clear_selection();
        tvBioEntries.add_biospecimen_item();
        selectNewestRow();        
        tabsBiospecimens.moveToNextTab();
        bModifyEntry.checked = true;
        addEntry();  // for Connections in bio tabs
        return true;
    }

    function clear_selection() {
        tvBioEntries.selection.clear();
        tvBioEntries.currentRow = -1;
    }

    function current_row_idx() {
        return tvBioEntries.currentRow;
    }

    function save_biospecimen_entry() {
        // Checking for existing protocols is done in a dialog- this always "saves."
        bModifyEntry.checked = false;
        clear_selection();
        // TODO Smart-switch to appropriate tab?
        tabsBiospecimens.currentIndex = 0;
    }

    Connections {
        target: appstate.catches

        onSampleMethodChanged: {
            // Catches corner case where catch category isn't changed (so no onSelectedCatchCatChanged)
            // but the currently selected catch category's sample method is changed to NSC.
            // console.log('SAMPLE METHOD CHANGED. IsNSC? ' + appstate.catches.currentSampleMethodIsNoSpeciesComposition )
            if (appstate.catches.currentSampleMethodIsNoSpeciesComposition) {
                console.debug("Biospecimens got onSampleMethodChanged signal w/NoSpecComp catch.");
                // Species tab is disabled. Set up species here using matching species from catch category.
                set_biospecimen_species_from_catch_category(); // TODO: Let CatchCat do var setting for Biospecimens, and delete this.
                set_biospecimen_context();
                set_tabs_for_no_species_composition();
            }
        }
    }

    Connections {
        target: tabView

        onSelectedCatchCatChanged: {
            // Handle Catch Category with Sample Method == No Species Composition
            // When new Catch Category selected on first tab,
            // and the new Catch Category is skipping the Species and Counts/Weights tabs to come here,
            // update Biospecimen species information to that matching the catch category,
            // and set up the biospecimen context.
            if (appstate.catches.currentSampleMethodIsNoSpeciesComposition) {
                console.debug("Selected catch category changed (to one NOT using Species Composition) ...");
                set_biospecimen_context();  // For NSC catches
                set_tabs_for_no_species_composition();
            }
        }

        onSelectedSpeciesChanged: {            
            set_biospecimen_context();  // For non-NSC catches
        }
    }

    RowLayout {
        id: glBio

        property int defaultMedFont: 20
        property int defaultSmallFont: 16

        ColumnLayout {
            // Left side of screen
            id: glBioEntries
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.margins: 15
            ColumnLayout {
                id: l1
                Layout.leftMargin: 20
                Layout.bottomMargin: 20
                RowLayout {
                    Label {
                        id: labelSpecies
                        text: "Species"
                        font.pixelSize: glBio.defaultMedFont
                        Layout.preferredHeight: 40
                        Layout.preferredWidth: 150
                    }
                    ObserverTextField {
                        id: tfSpecies
                        font.pixelSize: glBio.defaultMedFont
                        placeholderText: "Common Name"
                        Layout.preferredHeight: 40
                        Layout.preferredWidth: 300
                        text: appstate.catches.biospecimens.currentSpeciesCommonName
                        readOnly: true
                        onTextChanged: {
                            console.debug("Current species common name='" + text + "'.");
                            tfProtocol.text = appstate.catches.species.lookupProtocolsBySpeciesName(text);
                            console.debug("Setting protocols on species change to '" + tfProtocol.text + "'.");
                            // This sets the various booleans e.g. appstate.catches.species.bio_FL_enabled
                        }
                    }

                    FramLabel {
                        text: "Current Biolist:"
                        font.pixelSize: 20
                        Layout.preferredWidth: 150
                        Layout.preferredHeight: 40
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignRight
                    }
                    ObserverTextField {
                        id: bioListText
                        readOnly: true
                        text: appstate.isFixedGear ? appstate.sets.currentBiolistNum : appstate.hauls.currentBiolistNum
                        font.pixelSize: 20
                        Layout.preferredWidth: 50
                        Layout.preferredHeight: 40
                    }

                }

                RowLayout {
                    Label {
                        text: "Protocol"
                        font.pixelSize: glBio.defaultMedFont
                        Layout.preferredHeight: 40
                        Layout.preferredWidth: 150
                    }
                    ObserverTextField {
                        id: tfProtocol
                        text: appstate.catches.species.currentProtocols
                        readOnly: true
                        font.pixelSize: glBio.defaultMedFont
                        Layout.preferredHeight: 40
                        Layout.preferredWidth: 400
                    }
                }
                RowLayout {
                    id: rowBiosample
                    property var currentBM: appstate.catches.biospecimens.bioSampleMethod
                    Label {
                        text: "Biosample\nMethod"
                        font.pixelSize: glBio.defaultMedFont
                        Layout.preferredHeight: 40
                        Layout.preferredWidth: 150
                    }
                    ExclusiveGroup {
                        id: grpBSMethod
                    }

                    Repeater {
                        model: appstate.catches.biospecimens.bioSpecimenMethodsModel //["6", "7", "8", "9", "10"]
                        ObserverGroupButton {
                            Layout.preferredWidth: 70
                            Layout.preferredHeight: 50
                            text: modelData
                            exclusiveGroup: grpBSMethod
                            checked: rowBiosample.currentBM === modelData
                            enabled: bModifyEntry.checked || tvBioEntries.model.count === 0 || tvBioEntries.selection.count === 0
                            onClicked: {                                                                
                                rowBiosample.currentBM = modelData;
                                labelBSMethodDesc.text = appstate.catches.biospecimens.getBiosampleMethodDesc(modelData)
                                if (bModifyEntry.checked) {
                                    console.log("Modify Current BS Method to " + modelData)
                                    appstate.catches.biospecimens.setData('biosample_method', modelData)
                                    appstate.catches.biospecimens.update_biosample_method()
                                }
                                if (ObserverSettings.enableAudio) {
                                    soundPlayer.play_sound("click", false)
                                }

                            }
                            Connections {
                                target: rowBiosample
                                onCurrentBMChanged: {
                                    checked = rowBiosample.currentBM === modelData;
                                    if (rowBiosample.currentBM) {
                                        labelBSMethodDesc.text =
                                                appstate.catches.biospecimens.getBiosampleMethodDesc(rowBiosample.currentBM)
                                    }
                                }
                            }
                        }
                    }
                }
                Label {
                    id: labelBSMethodDesc
                    Layout.alignment: Qt.AlignCenter
                    text: appstate.catches.biospecimens.bioSampleMethod ?
                              labelBSMethodDesc.get_bs_desc() : defaultUnselectedText
                    font.pixelSize: glBio.defaultMedFont
                    font.italic: true
                    horizontalAlignment: Text.AlignHCenter
                    property string defaultUnselectedText: "Select Biosample Method"

                    function is_selected() {
                        return text !== labelBSMethodDesc.defaultUnselectedText;
                    }


                    function reset() {
                        text = defaultUnselectedText;
                        rowBiosample.currentBM = null;
                    }

                    function get_bs_desc() {
                        return appstate.catches.biospecimens.getBiosampleMethodDesc(appstate.catches.biospecimens.bioSampleMethod);
                    }

                }


            } // GridLayout top buttons

            ObserverTableView {
                id: tvBioEntries
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width

                model: appstate.catches.biospecimens.BiospecimenItemsModel
                item_height: 60

                property bool is_wm_9_or_19: appstate.catches.biospecimens.isWM9or19
                property bool is_wm_19: appstate.catches.biospecimens.isWM19

                function add_biospecimen_item() {

                    if (appstate.catches.biospecimens.currentSpeciesID === undefined) {
                        console.error("No species ID selected")
                        return;
                    }

                    if (appstate.catches.biospecimens.bioSampleMethod === undefined &&
                            rowBiosample.biosample_method === null) {
                        console.log("No bioSampleMethod selected")
                        return;
                    }

                    // Carry-over Biosample Method from last entry, but require re-entry of SLW fields.
                    var biospecimen_sex = null;
                    console.log("addBiospecimenItem " + tfSpecies.text);
                    appstate.catches.biospecimens.addBiospecimenItem(tfSpecies.text,
                                                                     rowBiosample.currentBM,
                                                                     biospecimen_sex);

                }

                Connections {
                    target: appstate.catches.species
                    onSelectedItemChanged: {
                        // Species ID changed, reset BS method.
                        labelBSMethodDesc.reset();
                    }
                }

                Connections {
                    target: via_screen
                    onViabilityChanged: {
                        tvBioEntries.model = appstate.catches.biospecimens.BiospecimenItemsModel;
                    }
                }

                Connections {
                    target: appstate.catches.biospecimens
                    onTallyCountChanged: {
                        tvBioEntries.model.modelReset();  // FIELD-1479: Hack to force refresh of model
                    }
                }

                function updateBiosampleButtonAndDescription() {
                    if (currentRow >= 0 && appstate.catches.biospecimens.bioSampleMethod) {  //
                        rowBiosample.currentBM = model.get(currentRow).biosample_str;
                        labelBSMethodDesc.text = labelBSMethodDesc.get_bs_desc();
                    } else if (tvBioEntries.model.count == 0) {
                        labelBSMethodDesc.reset();
                    }
                }

                onClicked: {
                    // If selected row has just been deleted, the currentRow isn't changed, so a
                    // select may not register as a row change, even though the contents may have.
                    // Just in case, make sure it's updated.
                    updateBiosampleButtonAndDescription();
                }

                onCurrentRowChanged: {
                    console.debug("tvBioEntries.currentRow changed to " + currentRow)
                    bModifyEntry.checked = false;
                    bModifyEntry.enabled = true;
                    appstate.catches.biospecimens.currentBiospecimenIdx = currentRow;
                    slw_screen.currentID = currentRow;
                    via_screen.currentID = currentRow;
                    tags_screen.currentID = currentRow;
                    barcodes_screen.currentID = currentRow;
                    updateBiosampleButtonAndDescription();

                    console.log("Current BM changed to " + rowBiosample.currentBM);
                }

                Connections {
                    target: appstate.catches.biospecimens
                    onTotalPHLBWeightChanged: {
                        if (tvBioEntries.is_wm_9_or_19) {
                            if (appstate.isFixedGear) {
                                console.info("WM=={9,19}: sample_count set to " + tvBioEntries.model.count + ".");
                                appstate.catches.setData('sample_count', tvBioEntries.model.count)
                                appstate.catches.species.totalCatchCountChanged(tvBioEntries.model.count)
                            } else {
                                console.info("WM=={9,19}: catch_count set to " + tvBioEntries.model.count + ".");
                                appstate.catches.setData('catch_count', tvBioEntries.model.count)
                                appstate.catches.species.totalCatchCountChanged(tvBioEntries.model.count)
                            }


                        }

                    }
                }

                TableViewColumn {
                    title: "#"
                    width: 50
                    delegate: Text {
                        text: tvBioEntries.model.count - styleData.row
                        font.pixelSize: 20
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                TableViewColumn {
                    role: "biosample_str"
                    title: "BM"
                    width: 50
                }
                TableViewColumn {
                    role: "specimen_sex"
                    title: "Sex"
                    width: 50
                }
                TableViewColumn {
                    role: "specimen_length"
                    title: "Len"
                    width: 60
                    delegate: Text {
                        text: styleData.value ? styleData.value : (tvBioEntries.is_wm_19 ? "Tally" : "")
                        font.pixelSize: 20
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                TableViewColumn {
                    role: "specimen_weight"
                    title: "Wt"
                    width: 80
                    delegate: Text {
                        text: styleData.value ? styleData.value.toFixed(dec_places) : ""
                        font.pixelSize: 20
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
                TableViewColumn {
                    // Either Viability, Adipose, or Maturity
                    id: colTVia
                    role: via_screen.isSalmon ? "adipose_present" : (via_screen.isCrab ? "maturity" : "viability")
                    title: "V/P"
                    width: 50
                    delegate: Text {
                        text: styleData.value ?
                                  (via_screen.isCrab ?
                                       (styleData.value[0] === "1" ? "Y": "N")
                                     : styleData.value)
                                : ""
                        font.pixelSize: 20
                        verticalAlignment: Text.AlignVCenter
                    }
                }                
                TableViewColumn {
                    role: "barcodes_str"
                    title: "Barcodes"
                    width: 160
                }

                TableViewColumn {
                    role: "tags_str"
                    title: "Tags"
                    width: 160
                    delegate: Text {
                        function getFontPixelSize(tag_string) {
                            var standard_size = 18;
                            var small_size = 12;

                            var tag_separator = "\n";
                            var re = RegExp(tag_separator, 'g');  // Find all CRs in tags_str
                            var n_separators = (tag_string.match(re) || []).length;
                            var n_rows = n_separators + 1;

                            // Use the standard size for up to three rows, the small size for four or more rows.
                            return n_rows <= 3 ? standard_size : small_size;
                        }
                        // QML provides the value returned by role "tags_str" in styleData.value. Not obvious!
                        text: styleData.value ? styleData.value : ""
                        font.pixelSize: getFontPixelSize(styleData.value ? styleData.value : "")
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                FramConfirmDialog {
                    id: confirmDeleteEntry
                    visible: false
                    action_label: qsTr("Remove highlighted biospecimen entry?")

                    onConfirmed: {
                        console.debug("Delete BS model row " + tvBioEntries.currentRow);
                        var delete_id = tvBioEntries.model.get(tvBioEntries.currentRow).bio_specimen_id;
                        console.debug("Delete BIO_SPECIMEN_ITEM_ID: " + delete_id);
                        tvBioEntries.model.remove(tvBioEntries.currentRow);
                        // Delete subsidiary records in DISSECTIONS
                        var deleteRecursively = true;
                        appstate.catches.biospecimens.deleteBiospecimenItem(delete_id, deleteRecursively);
                        bModifyEntry.checked = false;
                        visible = false;
                        clear_selection();
                        // Unselect Biosample Method.
                        // --> User must select biosample - no default.
                        labelBSMethodDesc.reset();
                    }
                }
            }
            RowLayout {
                ObserverTriStateButton {
                    id: bModifyEntry
                    text: "Modify\nEntry"
                    Layout.preferredWidth: 150
                    Layout.preferredHeight: 50
                    enabled: labelBSMethodDesc.is_selected() && tvBioEntries.currentRow >= 0                    
                }
                ObserverSunlightButton {
                    id: bDeleteEntry
                    text: "Delete\nEntry"
                    Layout.preferredWidth: 150
                    Layout.preferredHeight: 50
                    enabled: labelBSMethodDesc.is_selected() && tvBioEntries.currentRow >= 0
                    onClicked: {
                        if (tvBioEntries.currentRow >= 0) {
                            confirmDeleteEntry.visible = true;
                        }
                    }
                }

                Rectangle {  // Spacer. First three buttons above are a set: Add/Modify/Delete.
                             // The next button, Enable-All-Tabs, controls the visibility on right side of this screen.
                             // A different beast.
                    color: "transparent"
                    Layout.preferredWidth: 15
                }
                ObserverTriStateButton {
                    id: bEnableTabs
                    text: "Enable All\nBio Tabs"
                    font_size: 18
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 50
                    enabled: true
                    function enableAllProtocols(enable) {
                        slw_screen.showAll(enable);
                        barcodes_screen.showAll(enable);
                    }
                    onClicked: {
                        enableAllProtocols(checked);
                    }
                }
                Rectangle {  // Spacer. First three buttons above are a set: Add/Modify/Delete.
                             // The next button, Enable-All-Tabs, controls the visibility on right side of this screen.
                             // A different beast.
                    color: "transparent"
                    Layout.preferredWidth: 30
                }
                ObserverSunlightButton {
                    // button trigger for length matrix
                    id: btnLengthMtx
                    text: "Length\nMatrix"
                    Layout.preferredWidth: 100
                    Layout.preferredHeight: 50
                    // hide if modify button checked, isPHLB and not BSM 10, or something other than length required
                    visible: (!bModifyEntry.checked && ((appstate.catches.isPHLB && rowBiosample.currentBM == '10') || (appstate.catches.species.isLengthOnlyProtocols)))
                    onClicked: {
                        if(!labelBSMethodDesc.is_selected()) {
                            dlgSelectBMWarning.open()
                        } else { // set phlb or non-phlb models
                            if (appstate.catches.isPHLB) {
                                mtx.setModel(10)
                            } else {
                                mtx.setModel(1)
                            }
                            dlgLengthMatrix.open()
                        }
                    }
                    Dialog {
                        id: dlgLengthMatrix
                        title: 'BS Length Matrix'
                        width: mtx.matrixWidth + 70
                        height: mtx.matrixHeight + 70
                        property bool opened: false  // used to fake onClosed signal
                        signal dlgClosed  // used to fake onClosed signal
                        signal dlgOpened  // used to fake onClosed signal
                        contentItem: Rectangle {
                            anchors.margins: 20
                            anchors.fill: parent
                            color: "#eee"
                            RowLayout {
                                id: rlMtx
                                FramLabel {
                                    id: lblMtx
                                    text: "Select a biospecimen length (cm):"
                                    font.pixelSize: 20
                                    Layout.preferredHeight: 40
                                }
                                ObserverMatrix {
                                    id: mtx
                                    anchors.top: lblMtx.bottom
                                    enable_audio: true
                                    lowerRange: 1
                                    upperRange: 250
                                    increment: 1
                                    columns: 5
                                    buttonHeight: 50
                                    precision: 0
                                    onValClicked: {
                                        // TODO: option to save or retract low or high bs length
                                        if (val < 10 && !appstate.catches.isPHLB && !appstate.hauls.isShrimpGear) {
                                            dlgLengthWarning.display("Warning! Low length value selected:\n\n" + val + "cm < 10")
                                        } else if (val > 100 && !appstate.catches.isPHLB) {
                                            dlgLengthWarning.display("Warning! High length value selected:\n\n" + val + "cm > 100")
                                        }
                                        appstate.catches.biospecimens.addBiospecimenItem(
                                            tfSpecies.text,
                                            rowBiosample.currentBM,
                                            null
                                        );
                                        appstate.catches.biospecimens.setData('specimen_length', val)
                                        screenBio.selectNewestRow()
                                    }
                                    FramNoteDialog {
                                        id: dlgLengthWarning
                                        title: "Length Warning"
                                        bkgcolor: "#FA8072"
                                        height: 250
                                        message: ""
                                        function display(msg) {
                                            message = msg
                                            dlgLengthWarning.open()
                                        }
                                    }
                                    Component.onCompleted: {
                                        mtx.addModel(10, 10, 249) // custom PHLB model
                                    }
                                }
                            }
                        }
                        // not sure why onClosed doesnt work for Dialog, but this mess below does
                        onVisibleChanged : {
                            if (!this.visible) {
                                dlgClosed()
                            } else {
                                dlgOpened()
                            }
                        }
                        onDlgClosed: {
                            opened = false
                            screenBio.unselect()
                        }
                        onDlgOpened: {
                            opened = true
                        }
                    }
                }
                ObserverSunlightButton {
                    id: bSaveEntry
                    text: "Save\nEntry"
                    Layout.preferredWidth: 150
                    Layout.preferredHeight: 50
                    enabled: labelBSMethodDesc.is_selected() && tvBioEntries.currentRow >= 0 && !dlgLengthMatrix.opened
                    txtBold: true
                    highlightColor: "lightgreen"

                    onClicked: {
                        slw_screen.check_pending_protocols();
                        if (tabsBiospecimens.remainingProtocolsCount() > 0) {
                            dlgMissingProtocols.showNeeded();
                        // check for length less then 10 for non-shrimp trips (not gear type 12 or 13)
                        } else if ((appstate.catches.biospecimens.getData('specimen_length') < 10) &&
                                   !(appstate.hauls.isShrimpGear)) {
                            slw_screen.trigger_sm_len_warning();
                        } else if ((appstate.catches.isPHLB) || (appstate.catches.biospecimens.getData('specimen_length') < 100)) {
                            save_biospecimen_entry();
                            slw_screen.updateSex();  // clear selection
                            if (ObserverSettings.enableAudio) {
                                soundPlayer.play_sound("saveRecord", false)
                            }
                        }
                        // If length is 100 or over, don't follow through with save until
                        // after warning
                        else {
                            slw_screen.trigger_len_warning();
                        }
                    }
                }

            }

            FramNoteDialog {
                id: dlgSelectBMWarning
                message: "Select biosample method\nprior to adding entry."
                font_size: 18
            }

            ProtocolWarningDialog {
                id: dlgMissingProtocols
                message: "Warning! The record is not complete.\nPlease enter " + protocolsNeeded + "\nprior to starting\na new record/ exiting.";
                property string protocolsNeeded: ""
                function showNeeded() {
                    if(tabsBiospecimens.remainingProtocolsCount() > 0) {
                        protocolsNeeded = tabsBiospecimens.remainingProtocols();
                        open();
                    }
                }
                onRejected: {
                    // Acknowledge that this is OK
                    // TODO Store this rejection, and don't prompt again?                    
                    save_biospecimen_entry();
                    if (ObserverSettings.enableAudio) {
                        soundPlayer.play_sound("keyOK", false)
                    }
                }
                onAccepted: {
                    if (tabView.currentIndex != 3) {
                        tabView.currentIndex = 3;
                    }
                    if (ObserverSettings.enableAudio) {
                        soundPlayer.play_sound("reject", false)
                    }
                }
            }
            Connections {
                target: tabView
                onCurrentIndexChanged : {
                    if (screenBio.stateBio && currentIndex < 3 && tabSLW.enable_entry) {
                        // CW and Biospecimens are index 2 and 3
                        dlgMissingProtocols.showNeeded();
                    } else {
                        // FIELD-1766 disable Enable All Protocols if enabled
                        bEnableTabs.checked = false;
                        bEnableTabs.enableAllProtocols(false);
                    }

                    screenBio.stateBio = (currentIndex == 3) ? true : false;
                }

            }

            Connections {
                target: obsSM
                onEnteringBio: {
                    screenBio.stateBio = true;
                }
            }
        }

        FramTabView {
            id: tabsBiospecimens
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.margins: 15
            tabsAlignment: Qt.AlignRight
            tabPosition: Qt.BottomEdge
            enabled: true; //tvBioEntries.rowCount > 0

            function remainingProtocolsCount() {
                var remainingCount = slw_screen.remaining_protocol_count() +
                        via_screen.remaining_protocol_count() +
                        tags_screen.remaining_protocol_count() +
                        barcodes_screen.remaining_protocol_count();
                console.log("Remaining protocols required: " + remainingCount);
                return remainingCount;
            }

            function remainingProtocols() {
                var remaining = slw_screen.pending_protocols + " " +
                        via_screen.pending_protocols + " " +
                        tags_screen.pending_protocols_array + " " +
                        barcodes_screen.pending_protocols;
                remaining = remaining.trim().replace(" ", ","); // fill in spaces as commas
                console.log("Remaining protocols required: " + remaining);
                return remaining.trim();
            }

            function moveToNextTab() {

                var needSLW = slw_screen ? slw_screen.remaining_protocol_count() > 0 : false
                var needVia = via_screen ? via_screen.remaining_protocol_count() > 0 : false
                var needTags = tags_screen ? tags_screen.remaining_protocol_count() > 0 : false
                var needBC = barcodes_screen ? barcodes_screen.remaining_protocol_count() > 0 : false

                // FIELD-1554: premature tab switch when entering barcode
                // To fix this, if we're on a tab that needs protocols, don't change currentIndex
                var doNotSwitch = false;
                switch(currentIndex) {
                    case 0: // SLW:
                        if (needSLW) doNotSwitch = true;
                        break
                    case 1: // Viability:
                        if (needVia) doNotSwitch = true;
                        break
                    case 2: // Tags:
                        if (needTags) doNotSwitch = true;
                        break
                    case 3: // Barcodes:
                        if (needBC) doNotSwitch = true;
                        break
                }

                if (doNotSwitch) {
                    console.log("Not switching tabs, currently working on a tab with missing protocols.")
                    return;
                }

                if (needSLW) {
                    console.log("Switch to SLW");
                    currentIndex = 0;
                } else if (needVia) {
                    console.log("Switch to Viability");
                    currentIndex = 1;
                } else if (needTags) {
                    console.log("Switch to Tags");
                    currentIndex = 2;
                } else if (needBC) {
                    console.log("Switch to BC");
                    currentIndex = 3;
                } else {
                    // TODO: test this code path before auto unchecking Modify
//                    console.log("Appear to be done with everything.. disable Modify?")
//                    bModifyEntry.checked = false;
                }
            }

            Tab {
                id: tabSLW
                title: "Sex/Length/\nWeight"
                active: true  // Load tab at runtime
                enabled: true; //appstate.catches.species.bio_SLW_enabled || bEnableTabs.checked
                property alias enable_entry: bModifyEntry.checked
                BioSLWScreen {
                    id: screenSLW
                    enable_entry: bModifyEntry.checked
                    Component.onCompleted: {
                        slw_screen = screenSLW;
                    }
                    onReadyNextTab: {
                        tabsBiospecimens.moveToNextTab();
                    }
                    onAddTally: {
                        if(!labelBSMethodDesc.is_selected()) {
                            dlgSelectBMWarning.open();
                            return false;
                        }
                        const biosampleMethod = rowBiosample.currentBM;
                        //appstate.catches.biospecimens.bioSampleMethod;
                        console.log('BIOSAMPLE METHOD ' + biosampleMethod);
                        appstate.catches.biospecimens.addPHLBTally(biosampleMethod);
                        // No longer relevant:
                        // FIELD-1527
                        // Uses 7 instead of appstate.catches.biospecimens.bioSampleMethod for all Tally
                    }
                    onDecTally: {
                        appstate.catches.biospecimens.delPHLBTally();
                    }
                }
            }
            Tab {
                id: tabViability
                title: "Viability/\nPresence"
                active: true  // Load tab at runtime
                enabled: appstate.catches.species.bio_VP_enabled || bEnableTabs.checked
                BioViabilityScreen {
                    id: screenViability
                    enable_entry: bModifyEntry.checked
                    Component.onCompleted: {
                        via_screen = screenViability;
                    }
                    onReadyNextTab: {
                        tabsBiospecimens.moveToNextTab();
                    }
                }
            }
            Tab {
                id: tabPhotos
//                title: "Photos &\nExisting Tags"
                title: "Existing &\nObserver Tags"
                active: true  // Load tab at runtime
                enabled: appstate.catches.species.bio_ET_enabled || bEnableTabs.checked
                BioTagsScreen {
                    id: screenExistingTags
                    enable_entry: bModifyEntry.checked
                    Component.onCompleted: {
                        tags_screen = screenExistingTags;
                    }
                    onReadyNextTab: {
                        tabsBiospecimens.moveToNextTab();
                    }
                }
            }
            Tab {
                id: tabBarcodes
                title: "Dissection\nBarcodes"
                active: true  // Load tab at runtime
                enabled: appstate.catches.species.bio_BC_enabled || bEnableTabs.checked
                BioBarcodesScreen {
                    id: screenBarcodes
                    enable_entry: bModifyEntry.checked
                    Component.onCompleted: {
                        barcodes_screen = screenBarcodes;
                    }
                    onReadyNextTab: {
                        tabsBiospecimens.moveToNextTab();
                    }
                }
            }

        }
    }
}
