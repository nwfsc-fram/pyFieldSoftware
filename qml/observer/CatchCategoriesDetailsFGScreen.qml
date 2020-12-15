import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Controls.Styles 1.4

// Custom Model
import "../common"
import "."

Item {
    id: catchCatsDetailsFG
    function page_state_id() { // for transitions
        return "cc_details_fg_state";
    }

    signal resetfocus()
    onResetfocus: {
        // Just set focus to something benign
        lblDiscardReason.forceActiveFocus();
    }

    function set_model_index(model, idx) {
        // Pass the Catch Category model and index from parent
        ccModel = model;
        ccIndex = idx;
        init_ui();
    }

    // Model, Index, and ID of Catch Category Screen are expected to be set externally
    // via the properties argument of stackView.push() supplied by the parent pusher, CatchCategoriesScreen.qml.
    property var ccModel
    property var ccIndex
    property CatchCategoriesFGScreen ccScreenId

    property bool is_phlb: false
    property bool detailsComplete: true

    property int dec_places: appstate.displayDecimalPlaces  // Number of decimal places to display weight values

    onDetailsCompleteChanged: {
        framHeader.forwardEnable(detailsComplete);
        framHeader.backwardEnable(detailsComplete);
    }

    Component.onDestruction: {
        // Ensure if we leave this screen that other screens with forward nav still work
        framHeader.forwardEnable(true);
        framHeader.backwardEnable(true);
    }

    Connections {
        target: framHeader
        onBackClicked: {
            // FIELD-1891
            if (appstate.catches.sampleMethod === appstate.catches.SM_NO_SPECIES_COMP) {
                const prompt = get_prompt_if_bio_needed();
                if (prompt !== "") {
                    ccScreenId.showBioNeededWarning(prompt);
                }
            }
            // FIELD-1995
            appstate.catches.recalcOTCFG();
        }
        onForwardClicked: {
            // FIELD-1995
            appstate.catches.recalcOTCFG();
        }

        function get_prompt_if_bio_needed() {
            // NOTE this is basically copied from BiospecimensScreen so if that updates, should update this function accordingly
            var discard_reason = gridDR.current_discard_id;
            if (appstate.catches.biospecimens.currentWM !== '14') {
                console.log('Not wm 14, not prompting for bios');
                return "";
            }

            if (discard_reason === '12' || discard_reason === 15)
            {
                console.log('DR is dropoff/pred, not warning about Biospecimens.');
                return "";
            }
            // FIELD-1929: No prompt for Retained Sablefish
            if (appstate.isFixedGear && appstate.catches.species.currentSpeciesItemCode === "203" &&
                buttonDispR.checked) {
                console.log("Ret. sablefish, not prompting for req. biospecimens");
                return "";
            }

            var current_biolist_num = appstate.sets.currentBiolistNum;
            var biolist_name = appstate.catches.species.currentBiolist;
            var current_species_biolist_num = biolist_name ? parseInt(biolist_name.charAt(biolist_name.length - 1)) : null;
            var matching_bios = current_species_biolist_num &&
                    (current_species_biolist_num === current_biolist_num);

            if (appstate.catches.species.currentProtocols === '-') {
                return "";
            } else if (current_species_biolist_num && !matching_bios) {
                console.log("Species Biolist: " + biolist_name + " doesn't match " +
                             current_biolist_num +", not requiring biospecimens.")
                return "";
            } else {
                var bs_model = appstate.catches.biospecimens.BiospecimenItemsModel;
                if (!bs_model || bs_model.count === 0 ) {
                    const warning = "NOTE: Sample requested/required for this species : \n" +
                            appstate.catches.species.currentProtocols + "\nGo to BIOSPECIMENS tab, if required."
                    return warning;
                }
            }
        }
    }

    function check_details_complete() {
        // Allow movement to Species or Biospecimens
        var newDetailsComplete = appstate.catches.requiredCCDetailsAreSpecified;
        if (newDetailsComplete !== catchCatsDetailsFG.detailsComplete) {
            console.info("Change in property detailsComplete from " + catchCatsDetailsFG.detailsComplete + " to " +
                newDetailsComplete);
            catchCatsDetailsFG.detailsComplete = newDetailsComplete;
            if (catchCatsDetailsFG.detailsComplete) {
                console.debug("Sending signal catchCatsDetailsCompleted");
                ccScreenId.catchCatsDetailsFGCompleted();   // So Catch Categories can catch and activate CC.
            }
        }
    }

    Component.onCompleted: {
        init_ui();
    }

    function init_ui() {

        // Initialize UI to all model info passed to it (most of this occurs in components below)
        var curElem = ccModel.get(ccIndex);

        // ----------------
        // Catch Category
        tfDetailsCatchCategory.text = curElem.catch_category_code + " " + curElem.catch_category_name;

        // Special case: PHLB
        is_phlb = curElem.catch_category_code === "PHLB"
        if (is_phlb) {
            // Set the sample method to No Species Composition,
            // the only catch category whose sample method must be NSC.
            console.log("PHLB Mode selected.")
            appstate.catches.sampleMethod = appstate.catches.SM_NO_SPECIES_COMP;
        }
        check_details_complete();

    }

    function connect_page(page) {
        parentPage = page;
    }

    function setReadonlyFields(wm) {
        // Set readonly property for text fields as appropriate
        var hasNumpad = weightMethodHasNumpadOnThisScreen(wm);
        tfCW.readOnly = !hasNumpad;
        tfFish.readOnly = !hasNumpad;
    }

    function weightMethodHasNumpadOnThisScreen(wm) {
        // For certain weight methods, a numpad for weight entry is provided on this Catch Cat Details screen.
        if (wm === "13" || wm === '6' || wm === '14') { // '2' || wm === '6' || wm === '7' || wm === '14') {
            return true;
        }
        return false;
    }

    Connections {
        target: appstate
        onCatchCatNameChanged: {
            console.debug("Got CC change signal on appstate.catchCatName to '" + appstate.catchCatName + "'.");
        }
    }

    property var parentPage // colSpeciesControllers for elementUpdated signal

    property FramAutoComplete current_ac // Currently active autocomplete

    property var wmModel: weightMethod.WeightMethodModel
    property var discardModel: discardReason.DiscardReasonModel
    property var smModel: null

    ListView
    {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: parent.height - toolBar.height - 15

        function resetfocus() {  // For weights numpad
            lblCC.forceActiveFocus();
        }

        RowLayout {
            id: layoutCCFGDetails
            anchors.fill: parent
            anchors.margins: 50

            property int itemheight: 50
            property int labelwidth: 200
            property int itemwidth: labelwidth * 1.4
            property int fontsize: 20
            property int buttonsize: 60 // height and width

            Column {
                id: detailsColCC
                spacing: 20
                RowLayout {
                    id: rowBanner
                    spacing: 57
                    ObserverSunlightButton {
                        id: buttonCancel
                        Layout.alignment: Qt.AlignLeft
                        text: "  Cancel " + appstate.catches.currentCatchCatCode + "  "
                        txtColor: "red"
                        visible: !appstate.catches.biospecimens.dataExists && !appstate.catches.species.counts_weights.dataExists
                        onClicked: {  // simulate back click followed by CC delete
                            obsSM.state_change('cc_entry_state')
                            framHeader.backward_enabled = true;
                            framHeader.backClicked(obsSM.leftButtonStateName, textLeftBanner.text);
                            appstate.catches.ccCancelled()  // signals back to CC entry to delete
                        }
                    }
                    Label {
                        Layout.alignment: Qt.AlignLeft
                        id: labelRequiredFields
                        Layout.preferredWidth: layoutCCFGDetails.itemwidth
                        text: "Please complete all fields."
                        color: "red"
                        font.bold: true
                        font.pixelSize: 25
                        visible: !detailsComplete
                    }
                }
                RowLayout {
                    Label {
                        id: lblCC
                        text: "Catch Category"
                        Layout.preferredWidth: layoutCCFGDetails.labelwidth
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: layoutCCFGDetails.fontsize
                    }
                    TextField {
                        id: tfDetailsCatchCategory
                        Layout.preferredWidth: layoutCCFGDetails.itemwidth
                        Layout.preferredHeight: layoutCCFGDetails.itemheight
                        font.pixelSize: 17
                        readOnly: true

                    }
                }
                RowLayout {
                     id: dispositionRow

                     property bool allowDispChange: !appstate.catches.species.counts_weights.dataExists &&
                                                  !appstate.catches.biospecimens.dataExists

                     Label {
                         text: "Disposition"
                         Layout.preferredWidth: layoutCCFGDetails.labelwidth
                         verticalAlignment: Text.AlignVCenter
                         font.pixelSize: layoutCCFGDetails.fontsize
                     }

                     function catchIsNoSpeciesCompWithBiospecimens() {
                         // Don't allow the catch's Disposition to be changed if its sample method is
                         // NoSpeciesComposition and it has biospecimen data.
                         // Reason: the biospecimen records set their discard_reason to match that of the catch.
                         // Keep the catch discard reason and its biospecimen discard reasons consistent.
                         if (appstate.catches.currentSampleMethodIsNoSpeciesComposition &&
                                 appstate.catches.biospecimens.dataExists) {
                             console.debug("Catch is NSC and has biospecimen data.");
                             return true;
                         }
                         return false;
                     }

                     ExclusiveGroup { id: dispGroup }
                     ObserverGroupButton {
                         id: buttonDispD
                         text: "Discarded"
                         Layout.preferredWidth: layoutCCFGDetails.itemwidth / 2 - 5
                         Layout.preferredHeight: layoutCCFGDetails.buttonsize
                         exclusiveGroup: dispGroup
                         checked: appstate.catches.getData('catch_disposition') === 'D'
                         onClicked: {
                             var currentDisposition = appstate.catches.getData('catch_disposition');
                             if (checked && currentDisposition !== 'D') {
                                 console.debug("Discard newly clicked");

                                 if (!dispositionRow.allowDispChange) {
                                     dlgCannotChangeDispositionWithData.open();
                                     checked = false;
                                     buttonDispR.checked = true;
                                 } else if (dispositionRow.catchIsNoSpeciesCompWithBiospecimens()) {
                                     dlgCannotChangeDispositionIfNoSpeciesCompWithBiospecimens.open();
                                     checked = false;
                                     buttonDispR.checked = true;
                                 } else {
                                     appstate.catches.setData('catch_disposition', 'D')
                                     appstate.catches.species.isRetained = false;
                                 }
                                 catchCatsDetailsFG.check_details_complete();
                             }
                         }
                     }
                     Connections {
                         target: appstate.catches
                         onDispositionChanged: {
                             gridDR.update_disposition();
                         }
                     }

                     ObserverGroupButton {
                         id: buttonDispR
                         text: "Retained"
                         Layout.preferredWidth: layoutCCFGDetails.itemwidth / 2
                         Layout.preferredHeight: layoutCCFGDetails.buttonsize
                         exclusiveGroup: dispGroup
                         checked: appstate.catches.getData('catch_disposition') === 'R'
                         onClicked: {
                             var currentDisposition = appstate.catches.getData('catch_disposition');
                             var currentWM = appstate.catches.weightMethod;
                             if ( checked && currentWM && appstate.catches.checkExistingDispWM('R', currentWM)) {
                                 dlgNoExistingRetWM.display(currentWM);
                                 checked = false;
                                 buttonDispD.checked = true;
                                 return;
                             }
                             if (checked && currentDisposition !== 'R') {
                                 console.debug("Retained newly checked");

                                 if (!dispositionRow.allowDispChange) {
                                     dlgCannotChangeDispositionWithData.open();
                                     checked = false;
                                     buttonDispD.checked = true;
                                 } else if (dispositionRow.catchIsNoSpeciesCompWithBiospecimens()) {
                                     dlgCannotChangeDispositionIfNoSpeciesCompWithBiospecimens.open();
                                     checked = false;
                                     buttonDispD.checked = true;
                                 } else {
                                     appstate.catches.setData('catch_disposition', 'R')
                                     // Note: setData is asynchronous, not instant
                                     rowDR.clear_discard_reason();
                                     appstate.catches.species.isRetained = true;
                                 }
                                 catchCatsDetailsFG.check_details_complete();
                             }
                         }
                     }
               }
                RowLayout {
                    Label {
                        text: qsTr("Weight Method")
                        Layout.preferredWidth: layoutCCFGDetails.labelwidth
                        font.pixelSize: layoutCCFGDetails.fontsize
                    }
                    GridLayout {
                        id: gridWMButtons
                        columns: 5
                        rows: 3
                        enabled: true

                        ExclusiveGroup { id: wmGroup }

                        property bool allowWMChange: !appstate.catches.species.counts_weights.dataExists &&
                                                     !appstate.catches.biospecimens.dataExists

                        function clean_desc(desc) {
                            // Description, remove LL for Trawl
                            if (appstate.isGearTypeTrawl) {
                                desc = desc.replace('(LL)', '');
                            }
                            return desc;
                        }

                        Repeater {
                            id: rptWMButtons

                            model: ["13", "14", "9", "19"]

                            ObserverGroupButton {
                                text: modelData
                                exclusiveGroup: wmGroup
                                Layout.preferredWidth: layoutCCFGDetails.buttonsize
                                Layout.preferredHeight: layoutCCFGDetails.buttonsize
                                checked: appstate.catches.weightMethod === text

                                // Hide Weight Methods 9 and 19 unless Catch Category is PHLB
                                visible: is_phlb ? modelData == '9' || modelData == '19': modelData != '9' && modelData != '19'// PHLB = show 9/19 only


                                onClicked: {
                                    if (!gridWMButtons.allowWMChange) {
                                        console.error("Data exists, not allowing WM change.");
                                        dlgDataExists.display();
                                        rptWMButtons.restoreCheckedButton();
                                        return;
                                    }
                                    if (appstate.catches.getData('catch_disposition') === 'R' &&
                                        appstate.catches.checkExistingDispWM('R', modelData)) {
                                        dlgNoExistingRetWM.display(modelData);
                                        rptWMButtons.restoreCheckedButton();
                                        return;
                                    }


                                    // Switching from WM 7 or 14 to a WM other than these two can not be allowed
                                    // if SM is NSC and the Catch Category does not have a mapped species.
                                    // Reason: Biospecimens can be allowed with SM=NSC only if the Catch Category
                                    // has a mapped species (there's no default species, and there's no access to
                                    // the Species tab when SM=NSC).
                                    if (appstate.catches.wmNoSpeciesCompRequired &&
                                            modelData != 14 &&
                                            appstate.catches.currentSampleMethodIsNoSpeciesComposition &&
                                            (appstate.catches.currentMatchingSpeciesId === null)) {
                                        console.error("Trying to switch WM from 7 or 14 with SM=NSC for CC w/o mapped species.")
                                        dlgNoSwitchFromWM7or14IfNoSpecCompAndNoDefaultSpecies.display();
                                        rptWMButtons.restoreCheckedButton();
                                        return;
                                    }

                                    // If weight method was switched to 14, assign spec comp
                                    if (modelData == "13") {
                                        buttonYesSpecComp.checked= true;
                                        appstate.catches.sampleMethod = appstate.catches.SM_IS_SPECIES_COMP;
                                        rowDR.clear_discard_reason();
                                        appstate.catches.speciesCompChanged();
                                    }

                                    check_controls();  // Sets WM
//                                    if (modelData == "8" && appstate.catches.sampleMethod === "1") {
//                                        console.log("WM 8 cannot have sample method 1, changing to 2.");
//                                        appstate.catches.sampleMethod = "2";

//                                    }

                                    // set readonly properties
                                    catchCatsDetailsFG.setReadonlyFields(modelData);

                                    numPad.clearnumpad()
                                    tfCW.text = "";
                                    tfFish.text = "";
                                    appstate.catches.setData('sample_weight', null)
                                    appstate.catches.setData('sample_count', null)
                                    gridDR.update_wm();
                                }

                                Component.onCompleted: {
                                    check_controls();
                                    gridDR.update_wm();
                                }

                                function check_controls() {
                                    // Note, other method is used for WM 3 and 15 (see wm3button etc)
                                    if (checked) {
                                        appstate.catches.setData('catch_weight_method', text);
                                        appstate.catches.biospecimens.currentWM = text;
                                        tfWMDesc.text = gridWMButtons.clean_desc(appstate.catches.getWMDesc(text));

                                        switch(modelData) {
                                        case "6":
                                        case "14":
                                            if (buttonNoSpecComp.checked === true) {
                                                numPadRect.visible = true;
                                                btnManualWt.visible = true;
                                            } else {
                                                numPadRect.visible = false;
                                                btnManualWt.visible = false;
                                            }
                                            break;
                                        default:
                                            numPadRect.visible = false;
                                            btnManualWt.visible = false;
                                        }

                                        switch(modelData) {
                                        case "6":
                                            rowTotalFish.visible = false;
                                            rowCW.visible = true;
                                            rowHooksPotsSampled.visible = true;
                                            break;
                                        case "14":
                                            if (buttonNoSpecComp.checked === true) {
                                                rowTotalFish.visible = true;
                                                rowCW.visible = true;
                                            } else {
                                                tfCW.text = "";
                                                tfFish.text = "";
                                                rowTotalFish.visible = false;
                                                rowCW.visible = false;
                                            }
                                            rowHooksPotsSampled.visible = true;
                                            break;
                                        case "13":
                                        case "9":
                                        case "19":
                                            rowTotalFish.visible = false;
                                            rowCW.visible = false;
                                            rowHooksPotsSampled.visible = true;
                                            break;
                                        default:
                                            rowHooksPotsSampled.visible = false;
                                            rowTotalFish.visible = false;
                                            rowCW.visible = false;
                                        }
                                    }
                                    catchCatsDetailsFG.check_details_complete();
                                }
                            }
                            function restoreCheckedButton() {
                                var cur_WM = appstate.catches.weightMethod;
                                var checkedWMButtonIdx = model.indexOf(cur_WM);
                                var checkedWMButton = rptWMButtons.itemAt(checkedWMButtonIdx);
                                wmGroup.current = checkedWMButton;
                                console.info("Restored checked WM button to '" + checkedWMButton.text + "'.");
                            }
                        }

                        TextArea {
                            id: tfWMDesc
                            Layout.columnSpan: 4
                            Layout.fillWidth: true
                            Layout.preferredHeight: 50
                            font.pixelSize: 16
                            readOnly: true
                            verticalAlignment: Text.AlignVCenter
                        }
                        Component.onCompleted: {
                            tfWMDesc.text = gridWMButtons.clean_desc(appstate.catches.getWMDesc(appstate.catches.getData('catch_weight_method')));
                        }
                    }
                    // Pop-up Dialogs for Weight Methods
                   FramNoteDialog {
                        id: dlgNotYetImplemented
                        function display(wm) {
                            message = "Weight Method '" + wm + "'\nnot yet implemented.";
                            open();
                        }
                    }
                    FramNoteDialog {
                        id: dlgDataExists
                        function display() {
                            var data_arr = [];
                            if (appstate.catches.species.counts_weights.dataExists)
                                data_arr.push("basket");
                            if (appstate.catches.biospecimens.dataExists)
                                data_arr.push("biospecimen");

                            var data_msg = data_arr.join(' and ');
                            message = "Can't change weight method:\ndata (" + data_msg + ") exists.";
                            open();
                        }
                    }
                    FramNoteDialog {
                        id: dlgNoSwitchFromWM7or14IfNoSpecCompAndNoDefaultSpecies
                        function display() {
                            message = "Switch from Weight Method 7 or 14\n" +
                            "not allowed if WM=NoSpecComp and\n" +
                            "Catch Category has no default species.";
                            open();
                        }
                    }
                    FramNoteDialog {
                        id: dlgNoSwitchToWM3IfSM1OrSMNSC;
                        function display() {
                            message = "Switch to Weight Method 3\n" +
                            "not allowed if\nSample Method = 1 or NoSpecComp"
                            open();
                        }
                    }
                    FramNoteDialog {
                        id: dlgNoExistingRetWM;
                        function display(wm) {
                            message = "A Retained + WM " + wm + " record\nfor this species already exists."
                            open();
                        }
                    }
                    FramNoteDialog {
                        id: dlgNoSwitchFromWM3IfAdditionalBasketData
                        function display() {
                            message = "Switch from Weight Method 3\n" +
                            "not allowed if\ncatch-level basket data exists.\n" +
                            "To switch, first please remove\nWM3 basket data (see\n" +
                            " button on Catch Categories screen).";
                            open();
                        }
                    }
                }   // End Weight Method

                GridLayout {
                    columns: 2
                    visible: !is_phlb
                    Label {
                        text: qsTr("Species Comp")
                        Layout.preferredWidth: layoutCCFGDetails.labelwidth
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: layoutCCFGDetails.fontsize
                    }

                    RowLayout {
                        id: sampleMethodButtons
                        function restoreButtonDisplayStateAfterError() {
                            // Restore sample method display to that before an unsuccessful attempt.
                            if (appstate.catches.currentSampleMethodIsSpeciesComposition) {
                                // Restore checked numeric sample method:
                                buttonYesSpecComp.checked = true;
                            } else if (appstate.catches.currentSampleMethodIsNoSpeciesComposition) {
                                // Restore NSC
                                buttonNoSpecComp.checked = true;
                            } else {
                                buttonNoSpecComp.checked = false;    // Leave no SM button checked
                            }
                        }

                        ExclusiveGroup { id: smGroup }

                        ObserverGroupButton {
                            id: buttonYesSpecComp
                            exclusiveGroup: smGroup
                            text: "Yes"
                            Layout.preferredWidth: 100
                            Layout.preferredHeight: layoutCCFGDetails.buttonsize
                            checked: appstate.catches.sampleMethod === appstate.catches.SM_IS_SPECIES_COMP
                            onClicked: {
                                if (enabled) {
                                    // Don't allow transition from NoSpeciesComp if Biospecimen data exists.
                                    if (appstate.catches.currentSampleMethodIsNoSpeciesComposition) {
                                        var existingDataproblem = appstate.catches.impedimentToSampleMethodTransition;
                                        if (existingDataproblem != null) {
                                            console.warn(existingDataproblem + ".");
                                            sampleMethodButtons.restoreButtonDisplayStateAfterError();
                                            dlgExistingDataImpediment.message = "Cannot switch from NCS:\n" +
                                                existingDataproblem;
                                            dlgExistingDataImpediment.open();
                                            return;
                                        }
                                    }

                                    // If weight method is 14, turn off the side number pad, total fish, and catch count
                                    var cur_WM = appstate.catches.weightMethod;
                                    if (cur_WM == '14') {
                                        tfCW.text = "";
                                        tfFish.text = "";
                                        numPadRect.visible = false;
                                        btnManualWt.visible = false;
                                        rowTotalFish.visible = false;
                                        rowCW.visible = false;
                                    }

                                    // create/ set SpeciesComposition record for current catch
                                    appstate.catches.sampleMethod = appstate.catches.SM_IS_SPECIES_COMP;
                                    rowDR.clear_discard_reason();
                                    appstate.catches.speciesCompChanged();
                                }
                                catchCatsDetailsFG.check_details_complete();
                            }
                        }

                        ObserverGroupButton {
                            id: buttonNoSpecComp
                            visible: (appstate.catches.weightMethod !== '13')
                            text: "No"
                            exclusiveGroup: smGroup
                            Layout.preferredWidth: 100
                            Layout.preferredHeight: layoutCCFGDetails.buttonsize
                            checked: appstate.catches.sampleMethod === appstate.catches.SM_NO_SPECIES_COMP //appstate.catches.currentSampleMethodIsNoSpeciesComposition;

                            onClicked: {
                                if (enabled) {
                                    if (appstate.catches.currentMatchingSpeciesId == null) {
                                        if (appstate.catches.wmNoSpeciesCompRequired) {
                                            console.debug("NSC allowed, even with CC with no mapped species, " +
                                                    "because WM is either 7 (vessel est.) or 14 (viz exp).");
                                        } else {
                                            sampleMethodButtons.restoreButtonDisplayStateAfterError();
                                            console.info("Catch can't be NoSpecComp: No mappable species.");
                                            dlgNoMatchingSpecies.open();
                                            return;
                                        }
                                    }

                                    var existingDataproblem = appstate.catches.impedimentToSampleMethodTransition;
                                    if (existingDataproblem != null) {
                                        console.warn(existingDataproblem + ".");
                                        sampleMethodButtons.restoreButtonDisplayStateAfterError();
                                        dlgExistingDataImpediment.message = "Cannot switch to NCS:\n" + existingDataproblem;
                                        dlgExistingDataImpediment.open();
                                        return;
                                    }

                                    // enable numpad, catch weight, and total fish for WM 14, composition No
                                    var cur_WM = appstate.catches.weightMethod;
                                    if (cur_WM == '14') {
                                        numPadRect.visible = true;
                                        btnManualWt.visible = true;
                                        rowTotalFish.visible = true;
                                        rowCW.visible = true;
                                    }

                                    // sampleMethod setter deletes any existing SpeciesComposition record.
                                    appstate.catches.sampleMethod = appstate.catches.SM_NO_SPECIES_COMP;
                                    appstate.catches.speciesCompChanged();

                                    catchCatsDetailsFG.check_details_complete();
                                }
                            }
                        }
                        ////
                        // Pop-up Dialogs - Triggered by press of No Species Comp button, but not part of typical layout.
                        ////
                        FramNoteDialog {
                            id: dlgNoMatchingSpecies
                            message: "Catch Cat. has no matching species.\n" +
                                    "Except for WM7 and WM14,\n" +
                                    "a Catch Cat. must have at least\n" +
                                    "one matching species to allow\n" +
                                    "Sample Method = No Species Comp."
                        }
                        FramNoteDialog {
                            id: dlgExistingDataImpediment
                        }
                    }
                }
                RowLayout {
                    id: rowHooksPotsSampled
                    Label {
                        text: "Gear Units Sampled?"
                        Layout.preferredWidth: layoutCCFGDetails.labelwidth
                        font.pixelSize: layoutCCFGDetails.fontsize
                    }
                    TextField {
                        id: tfUnitsSampled
                        Layout.preferredWidth: layoutCCFGDetails.itemwidth
                        Layout.preferredHeight: layoutCCFGDetails.itemheight
                        font.pixelSize: 17
                        placeholderText: "Units Sampled"
                        readOnly: false
                        text: appstate.catches.getData('gear_segments_sampled') ? appstate.catches.getData('gear_segments_sampled') : ""
                        onActiveFocusChanged: {
                            if (focus) {
                                focus = false;  // otherwise, dialogs opened forever
                                numpadUnitsSampled.open()
                            }
                        }
                        onTextChanged: {
                            var unitsSampled = parseInt(text)
                            appstate.catches.setData('gear_segments_sampled', unitsSampled);
                            var hooksSampled = Math.round(unitsSampled * appstate.trips.currentAvgHookCount);
                            console.info('Calculated hooks_sampled to be ' + hooksSampled);
                            appstate.catches.setData('hooks_sampled', hooksSampled);
                            appstate.catches.setData('hooks_sampled_unrounded', unitsSampled * appstate.trips.currentAvgHookCount);
                            lblHooksSampled.visible = true;
                            lblHooksSampled.text = " = " + hooksSampled + " hooks/pots"
                        }
                    }
                    Label {
                        id: lblHooksSampled
                        visible: appstate.catches.getData('hooks_sampled') > 0
                        text: " = " + appstate.catches.getData('hooks_sampled') + " hooks/pots"
                        Layout.preferredWidth: layoutCCFGDetails.labelwidth
                        font.pixelSize: layoutCCFGDetails.fontsize
                    }
                    ObserverNumPadDialog {
                        id: numpadUnitsSampled
                        placeholderText: tfUnitsSampled.placeholderText
                        enable_audio: ObserverSettings.enableAudio
                        onValueAccepted: {
                            tfUnitsSampled.text = accepted_value;
                        }
                    }

                }

                RowLayout {
                    id: rowDR
                    visible: (buttonDispD.checked && appstate.catches.weightMethod === '14') || (buttonDispD.checked && is_phlb)
                    signal drCleared

                    Label {
                        text: "Discard Reason"
                        Layout.preferredWidth: layoutCCFGDetails.labelwidth
                        font.pixelSize: layoutCCFGDetails.fontsize
                    }
                    function clear_discard_reason() {
                        ccModel.setProperty(ccIndex, "discard_reason", "");
                        ccModel.get(ccIndex).discard_reason = null;
                        appstate.catches.setData('discard_reason', null);
                        gridDR.current_discard_id = null;
                        gridDR.set_discard_desc();
                        drCleared();
                    }
                    GridLayout {
                        id: gridDR
                        columns: 5
                        rows: 3
                        property var current_discard_id: null

                        Component.onCompleted: {
                            current_discard_id = appstate.catches.getData('discard_reason');
                            gridDR.set_discard_desc(gridDR.current_discard_id);
                        }

                        function set_discard_desc() {
                            if (gridDR.current_discard_id === null) {
                                tfDRDesc.text = "";
                                return;
                            }

                            // set textfield desc and save to db
                            var idx = discardModel.get_item_index('discard_id', gridDR.current_discard_id)
                            if (idx >= 0) {
                                tfDRDesc.text = discardModel.get(idx).text
                                ccModel.setProperty(ccIndex, "discard_reason", gridDR.current_discard_id);
                                appstate.catches.setData('discard_reason', ccModel.get(ccIndex).discard_reason);
                                console.debug("Model Discard Reason set to " + ccModel.get(ccIndex).discard_reason);

                                // appstate.catches.species.discardReason = gridDR.current_discard_id;

                                // FIELD-1779 also set underlying BIO_SPECIMENS record
                                var speciesID = appstate.catches.biospecimens.currentSpeciesID;
                                var dr = gridDR.current_discard_id;
                                // FIELD-1820 also set underlying Biospecimens model
                                appstate.catches.biospecimens.setDiscardReasonSpeciesID(dr, speciesID);

                                // Check if PHLB can navigate to Biospecimens:
                                catchCatsDetailsFG.check_details_complete();
                            }
                        }

                        function update_wm() {
                            // FIELD-1327
                            appstate.catches.biospecimens.currentWM = appstate.catches.weightMethod;
                            console.log("Updated WM to " + appstate.catches.biospecimens.currentWM);
                        }

                        function update_disposition() {
                            // FIELD-1327
                            appstate.catches.biospecimens.currentCatchDisposition = appstate.catches.getData('catch_disposition');
                            if (appstate.catches.biospecimens.currentCatchDisposition === 'R') {
                                // clear DR for retained
                                appstate.catches.species.discardReason = null;
                                appstate.catches.biospecimens.currentParentDiscardReason = null;
                            }

                            console.log("Updated disp to " + appstate.catches.biospecimens.currentCatchDisposition);
                        }

                        function restoreCheckedButton() {
                            var cur_DR = appstate.catches.getData('discard_reason');
                            if (cur_DR === null) {
                                console.debug("Current DR (before error) was undefined. No action taken.");
                                return;
                            }
                            console.debug("Current DR (before error) was " + cur_DR);
                            var checkedDRButtonIdx = discardModel.get_item_index('discard_id', cur_DR);
                            var checkedDRButton = rptDRButtons.itemAt(checkedDRButtonIdx);
                            groupDR.current = checkedDRButton;
                            console.debug("Restored checked DR button to '" + checkedDRButton.text + "'.");
                        }

                        ExclusiveGroup { id: groupDR }
                        Repeater {
                            id: rptDRButtons

                            model: discardModel
                            ObserverGroupButton {
                                visible: discard_id != -1
                                text: discard_id
                                exclusiveGroup: groupDR
                                Layout.preferredWidth: layoutCCFGDetails.buttonsize
                                Layout.preferredHeight: layoutCCFGDetails.buttonsize
                                checked: discard_id == gridDR.current_discard_id
                                onClicked: {
                                    var current_DR = appstate.catches.getData('discard_reason');
                                    var speciesID = appstate.catches.biospecimens.currentSpeciesID;
                                    if (appstate.catches.biospecimens.dataWithDRSpeciesExists(current_DR, speciesID)) {
                                        dlgWarnDRChange.askDRChange(discard_id);
                                        return;
                                    } else {
                                        console.info("No biospecimen record existing for this NSC; changing DR.");
                                        gridDR.current_discard_id = discard_id;
                                        gridDR.set_discard_desc();
                                    }
                                }
                                Connections {
                                    target: rowDR
                                    onDrCleared: {
                                        checked = false;
                                    }
                                }
                            }

                        }
                        TextArea {
                            id: tfDRDesc
                            Layout.columnSpan: 5
                            Layout.fillWidth: true
                            Layout.preferredHeight: layoutCCFGDetails.buttonsize
                            font.pixelSize: 16
                            readOnly: true
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }

            } // End First Column
            ColumnLayout {
                RowLayout {
                    FramLabel {  // FIELD-2060, added in label
                        text: "Protocol: " + appstate.catches.species.currentProtocols
                        + (appstate.catches.species.currentBiolist ? "(" + appstate.catches.species.currentBiolist + ")" : "")
                        + "; Biolist: " + appstate.hauls.currentBiolistNum
                        font.pixelSize: 18
                        font.italic: true
                        Layout.preferredHeight: 35
                    }
                }
                RowLayout {
                    id: rowCW
                    visible: false
                    FramLabel {
                        text: "Catch Weight"
                        Layout.preferredWidth: 200
                        font.pixelSize: 18
                    }
                    ObserverTextField {
                        id: tfCW
                        Layout.preferredWidth: 250
                        Layout.preferredHeight: 50
                        font.pixelSize: 18
                        text: setTextValue()    // May vary according to Weight Method
                        placeholderText: "Enter Weight"
                        Component.onCompleted: {
                            numPad.directConnectTf(tfCW);
                            numPad.textNumPad.cursorPosition = cursorPosition;
                            tfCW.forceActiveFocus();
                        }

                        function setTextValue() {
                            var cur_WM = appstate.catches.weightMethod;

                            tfCW.text = appstate.catches.species.counts_weights.actualWeight ?
                                    appstate.catches.species.counts_weights.actualWeight.toFixed(dec_places) : "";


                            // For WMs with a numpad on this screen for weight,
                            // initialize the catch weight with the persisted value.
                            if (catchCatsDetailsFG.weightMethodHasNumpadOnThisScreen(cur_WM)) {
                            var weight_field = appstate.isFixedGear ? 'sample_weight' : 'catch_weight';
                                tfCW.text = appstate.catches.getData(weight_field) ?
                                        appstate.catches.getData(weight_field).toFixed(dec_places) : "";
                            }
                        }

                        onActiveFocusChanged:  {
                            if (focus) {
//                                console.debug("tfCW (CatchWeight) got focus.");
                                numPad.showDecimal(false);
                                numPad.directConnectTf(this);
                                cursorPosition  = text.length;
                                catchCatsDetailsFG.check_details_complete();
                            }
                        }

                        onTextChanged: {
                            if (numPad.adding_mode || numPad.subtracting_mode) {
                                console.debug("Adding or subtracting");
                            } else {
                                var value = parseFloat(text);
                                var weight_field = appstate.isFixedGear ? 'sample_weight' : 'catch_weight';
                                if (value > 0.0) {
                                  appstate.catches.setData(weight_field, value)
                                } else {
                                  appstate.catches.setData(weight_field, null)
                                }
                                appstate.catches.species.totalCatchWeightChanged(value)
                                catchCatsDetailsFG.check_details_complete();
                            }
                        }
                    }
                }

                RowLayout {
                    // Only used by Weight Method 14
                    id: rowTotalFish
                    visible: false
                    FramLabel {
                        text: "Total # of Fish"
                        Layout.preferredWidth: 200
                        font.pixelSize: 18
                    }
                    ObserverTextField {
                        id: tfFish
                        Layout.preferredWidth: 250
                        Layout.preferredHeight: 50
                        font.pixelSize: 18
                        text: setTextValue()
                        placeholderText: "Enter Count"

                        function setTextValue() {
                            var cur_WM = appstate.catches.weightMethod;

                            placeholderText = "Enter Count";

                            // For WMs with a numpad on this screen for fish count (WM14),
                            // initialize the catch count with the persisted value.
                            var count_field = appstate.isFixedGear ? 'sample_count' : 'catch_count';
                            var textValue = appstate.catches.getData(count_field) ?
                                        appstate.catches.getData(count_field) : "";
                            return textValue;
                        }

                        onActiveFocusChanged:  {
                            if (focus) {
                                console.debug("tfFish (catch count) got focus.");
                                numPad.showDecimal(false);
                                numPad.directConnectTf(this);
                                cursorPosition  = text.length;
                                numPad.textNumPad.cursorPosition = cursorPosition;
                            }
                        }

                        onTextChanged: {
                            if (numPad.adding_mode || numPad.subtracting_mode) {
                                console.debug("Adding or subtracting");
                            } else {
                                var value = parseFloat(text);
                                var count_field = appstate.isFixedGear ? 'sample_count' : 'catch_count';
                                if (value > 0.0) {
                                  appstate.catches.setData(count_field, value)
                                } else {
                                  appstate.catches.setData(count_field, null)
                                }
                                appstate.catches.species.totalCatchCountChanged(value)
                            }
                        }
                    }
                }


                Rectangle {
                    id: numPadRect
                    color: "darkgray"
                    Layout.preferredHeight: 400
                    Layout.preferredWidth: 400
                    Layout.alignment: Qt.AlignRight  // Put numpad under ratio text fields
                    visible: false

                    function getNumPadState() {
                        // In all weight methods other than 15, the numpad will be used for weight information.
                        // WM15 uses for setting numerator and denominator of a ratio; use "popup_basic":
                        var cur_WM = appstate.catches.weightMethod;
                        var numPadState = (cur_WM !== "15")? "weights_ok": "counts_ok";
                        console.debug("CC Details's NumPad state is " + numPadState);
                        return numPadState;
                    }
                    Connections {
                        target: appstate.catches
                        onWeightMethodChanged: {
                            numPad.setstate(numPadRect.getNumPadState());
                        }
                    }
                    FramScalingNumPad {
                        id: numPad
                        anchors.fill: numPadRect
                        state: numPadRect.getNumPadState()
                        direct_connect: true
                        btnOk.visible: true    // Only show OK when add or subtract is in progress.
                        limitToTwoDecimalPlaces: true   // Don't allow more than two decimal places for weight.
                        enable_audio: ObserverSettings.enableAudio

                        onNumpadok: {
                            var cur_WM = appstate.catches.weightMethod;
                            switch(cur_WM) {
                            //NotYet case "2": // Bin/Trawl alley est.
                            //NotYet case "7": // Vessel Estimate
                            case "6": // Other
                                tfCW.text = textNumPad.text;
                                break;

                            case "8": // Extrapolation
                            case "14": // Visual Experience
                                // set value
                                if (tfFish.focus) {
                                    tfCW.forceActiveFocus();

                                } else {
                                    tfFish.forceActiveFocus();
                                }

                                break;
                            case "15": // Visual Spatial
                                if (wpRow.tfNumerator.focus) {
                                    wpRow.tfDenominator.forceActiveFocus();
                                }
                            }

                        }
                    }
                }
                RowLayout {
                    ExclusiveGroup {
                        id: grpWt
                    }

                    ObserverGroupButton {
                        text: "Scale Wt"
                        exclusiveGroup: grpWt
                        Layout.preferredHeight: 50
                        Layout.preferredWidth: 150
                        visible: false
                        // TODO: IMPLEMENT
                        //visible: numPadRect.visible
                    }
                    ObserverGroupButton {
                        id: btnManualWt
                        text: "Manual Wt"
                        exclusiveGroup: grpWt
                        checked: true
                        Layout.preferredHeight: 50
                        Layout.preferredWidth: 150
                        visible: false
                    }
                }
            }
        } // RowLayout


    } // ListView

    // Pop-up Dialogs
    FramNoteDialog {
        id: dlgCannotChangeDispositionIfNoSpeciesCompWithBiospecimens
        message: "This catch has a sample method\nof No Species Composition\n" +
                "and has biospecimen data.\nTo change disposition, please either\n" +
                "delete the biospecimen data\n" +
                "or add a new catch category."
    }

    FramNoteDialog {
        id: dlgCannotChangeDispositionWithData
        function get_data_str() {
            var cw_str = appstate.catches.species.counts_weights.dataExists ? "counts/weights" : "";
            var bs_str = appstate.catches.biospecimens.dataExists ? "biospecimen" : "";
            if (cw_str.length > 0 && bs_str.length > 0) {
                return cw_str + ", " + bs_str;
            } else {
                return (cw_str + " " + bs_str).trim();
            }


        }

        message: "Existing data\n(" + get_data_str() +
                 ")\n for catch category.\n" +
                 "Cannot change disposition."
    }

    ProtocolWarningDialog {
        id: dlgWarnDRChange
        message: "You are about to change the\ndiscard reason associated with\nthis catch's biosamples."
        btnAckText:"Yes,\n Change discard\nreason to " + pendingDR
        btnOKText: "No,\n Do not change"
        property string pendingDR: ""
        function askDRChange(dr) {
            pendingDR = dr;
            open();
        }
        onRejected: {
            // Acknowledged that this is OK
            console.info("User acknowledged change to DR " + pendingDR);
            // FIELD-1779
            gridDR.current_discard_id = pendingDR;
            gridDR.set_discard_desc();
        }
        onAccepted: {
            // User responded Do Not change
            console.info("User response: Do Not Change DR");
            gridDR.restoreCheckedButton();
        }
    }

//        Connections {
//            target: tabView
//            onCurrentIndexChanged : {
//                if (screenCW.stateCW && currentIndex < 2) {
//                    // CW and Biospecimens are index 2 and 3
//                    dlgProtocolRequested.prompt_if_bio_needed();
//                }
//                screenCW.stateCW = (currentIndex == 2) ? true : false;
//            }

//        }
}
