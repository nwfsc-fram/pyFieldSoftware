import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.3

import "fishSamplingTabs"

Dialog {
    id: dlg
    width: 1060
    height: 600
    title: "Fish Sampling Entry - Random Drops " + randomDrops

    property variant specimenID: null;
    property variant anglerBtnMap: {
        "A": adhTab.btnAnglerA,
        "B": adhTab.btnAnglerB,
        "C": adhTab.btnAnglerC }
    property variant dropBtnMap: {
        "1": adhTab.btnDrop1,
        "2": adhTab.btnDrop2,
        "3": adhTab.btnDrop3,
        "4": adhTab.btnDrop4,
        "5": adhTab.btnDrop5
    }
    property variant hookBtnMap: {
        "1": adhTab.btnHook1,
        "2": adhTab.btnHook2,
        "3": adhTab.btnHook3,
        "4": adhTab.btnHook4,
        "5": adhTab.btnHook5
    }
    property variant ageTypeBtnMap: {
        "Otolith": ageTab.btnOtolith,
        "Finray": ageTab.btnFinray,
        "Second Dorsal Spine": ageTab.btnSecondDorsalSpine,
//        "Vertebra": ageTab.btnVertebra,
//        "Scale": ageTab.btnScale,
        "Not Available": ageTab.btnNotAvailable
    }
    property variant ageCategoryBtnMap: {
        "A": ageTab.btnAgeA,
        "B": ageTab.btnAgeB,
//        "G": ageTab.btnAgeG,
        "V": ageTab.btnAgeV
    }
    property variant finclipCategoryBtnMap: {
        "A": finclipTab.btnFinclipA,
        "B": finclipTab.btnFinclipB,
//        "G": finclipTab.btnFinclipG,
        "V": finclipTab.btnFinclipV
    }
    property variant dispositionCategoryBtnMap: {
        "Sacrificed": dispositionTab.btnSacrificed,
        "Released": dispositionTab.btnReleased,
        "Descended": dispositionTab.btnDescended
    }

    property bool wasTabPressed: false;

    onRejected: { }
    onAccepted: { clearTabs(); }

    signal specimenCleared;

    Connections {
        target: labelPrinter
        onPrinterStatusReceived: receivedPrinterStatus(comport, success, message)
    } // labelPrinter.onPrinterStatusReceived
    function receivedPrinterStatus(comport, success, message) {
        var result = success ? "success" : "failed"
        dlgOkay.message = "Print job to " + comport + " status: " + result;
        if (result === "failed") {
            dlgOkay.action = "Please try again";
        } else {
            dlgOkay.action = "Well done, continue on matey";
        }
        dlgOkay.open();
    }

    Connections {
        target: fishSampling
        onSpecimenConflictEncountered: encounteredSpecimenConflict(adh, hookMatrixResult, tempValues);
    } // fishSampling.onSpecimenConflictEncountered
    function encounteredSpecimenConflict(adh, hookMatrixResult, tempValues) {
        console.info('conflict found for A/D/H:' + adh);
        console.info('hookMatrixResult: ' + JSON.stringify(hookMatrixResult));
        console.info('temp values: ' + JSON.stringify(tempValues));

        dlgSpeciesConflict.message = "Species Conflict for " + adh + "\n\nHookMatrix species = " +
                                    hookMatrixResult["species"] +
                                    "\n\nDon't worry, no previous data has been " +
                                    "\ncollected for " + adh;
        dlgSpeciesConflict.action = "Click Okay to use the CutterStation data"
        dlgSpeciesConflict.tempValues = tempValues;
        dlgSpeciesConflict.open();
    }

    Connections {
        target: fishSampling
        onExceptionEncountered: showException(message, action);
        onLwRelationshipOutlier: {  // 94: when LW outlier message received, display in dialog
            dlgLwWarning.message = message
            dlgLwWarning.open()
        }
    } // fishSampling.onExceptionEncountered
    function showException(message, action) {
        dlgOkay.message = message;
        dlgOkay.action = action;
        dlgOkay.open();
    }

//    Connections {
//        target: serialPortManager
//        onExceptionEncountered: showSerialPortException(comPort, msg);
//    } // serialPortManager.onExceptionEncountered
//    function showSerialPortException(comPort, msg) {
//        msg = "Serial Port Exception Encountered:" + "\n\n" + msg
//        dlgOkay.message = msg;
//        dlgOkay.action = "Please take the value again";
//        dlgOkay.open();
//    }

    Connections {
        target: serialPortManager
        onDataReceived: serialPortDataReceived(action, value, uom, dbUpdate)
    } // serialPortManager.onDataReceived
    function serialPortDataReceived(action, value, uom, dbUpdate) {
//        console.info("Entry Dialog connections are still firing even when closed !!!!!!!!!!!!!");

        console.info("action=" + action + ", value=" + value + ", uom=" + uom + ", dbUpdate=" + dbUpdate);
//        console.info("value type = " + typeof value);
//        console.info("value len=" + value.length);
        switch (action) {
            case "adh":
                if (value.length === 3) {
                    var specimenResult = fishSampling.checkIfSpecimenExists(value[1], value[0], value[2]);
                    if ((specimenResult !== null) & (specimenResult !== undefined)) {
                        dlgOkay.message = "" + value + " specimen exists with " + specimenResult["species"] + ", opening it.";
                        dlgOkay.action = "FYI, you may have already worked up this fish."
                        dlgOkay.open();
                        fishSampling.selectSpecimenRecordByADH(value[0], value[1], value[2]);

                    } else {
                        anglerBtnMap[value[0]].checked = true;
                        dropBtnMap[value[1]].checked = true;
                        hookBtnMap[value[2]].checked = true;
                        adhTab.angler = value[0];
                        adhTab.drop = value[1];
                        adhTab.hook = value[2];
                        console.info("calling upsertADH: " + value[0] + value[1] + value[2]);
                        fishSampling.upsertADH(null, value);
                    }
                    soundPlayer.playSound("takeBarcode", 0, false);
                }
                break;
            case "weight":
                weightTab.numPad.textNumPad.text = value;
                updateLabel(action, value, uom, true, null);
                soundPlayer.playSound("takeWeight", 0, false);
                nextTab();  // For auto-advancing from the weight tab once it is sent via the scale print button
                break;
        }
    }

    Connections {
        target: fishSampling
        onSpecimenSelected: selectedSpecimen(specimen);
    } // fishSampling.onSpecimenSelected
    function selectedSpecimen(specimen) {
        console.info("selectedSpecimen in FishSamplingEntryDialog");
        clearTabs();
        populateTabs(specimen);
        console.info('populateTabs completed');
    }

    function getAgeFinclipDescriptor(species) {
        switch (species.replace("\n", " ")) {
            case "Bocaccio":
                return "B";
                break;
            case "Vermilion Rockfish":
                return "V";
                break;
            default:
                return "A";
                break;
        }
    }
    function populateTabs(specimen) {

        console.info('populateTabs');
        console.info('specimen=' + JSON.stringify(specimen));
        var lastAgeFinclipRecords = null;

        if ("specimenID" in specimen) {
            specimenID = specimen["specimenID"];
            for (var item in specimen) {
                if (specimen[item] !== undefined) {
//                    console.info('populating ' + item);
                    switch (item) {
                        case "adh":
                            if (adhTab.bgAngler.checkedButton === null) {
                                var anglerValue = specimen[item][0];
                                anglerBtnMap[anglerValue].checked = true;
                                adhTab.angler = anglerValue;
                                stateMachine.angler = anglerValue;
                            }
                            if (adhTab.bgDrop.checkedButton === null) {
                                var dropValue = specimen[item][1];
                                dropBtnMap[dropValue].checked = true;
                                adhTab.drop = dropValue;
                                stateMachine.drop = dropValue;
                            }
                            if (adhTab.bgHook.checkedButton === null) {
                                var hookValue = specimen[item][2];
                                hookBtnMap[hookValue].checked = true;
                                adhTab.hook = hookValue;
                                stateMachine.hook = hookValue;
                            }
                            if ((anglerValue !== "") & (dropValue !== "") & (hookValue !== "")) {
                                updateLabel("adh", anglerValue + dropValue + hookValue, null, false, null);
                                nextTab();
                            }
                            break;
                        case "species":
                            var isFound = false;
                            var speciesName;
                            var children;
                            var speciesFullList = [speciesTab.sfl1, speciesTab.sfl2, speciesTab.sfl3];
                            for (var num in speciesFullList) {
                                if (isFound) break;
                                children = speciesFullList[num].glSpecies.children
                                for (var i in children) {
                                    if (children[i].toString().indexOf("BackdeckButton2_QMLTYPE") === 0) {
                                        speciesName = children[i].text.replace("\n", " ");
                                        if (speciesName === specimen[item]) {
                                            isFound = true;
                                            children[i].checked = true;
                                            speciesTab.currentSpecies = speciesName;
                                            updateLabel("species", speciesName, null, false, null);

                                            var descriptor = getAgeFinclipDescriptor(speciesName);
//                                            console.info('specimen[ageID]=' + specimen['ageID']);
                                            if (!("ageRecID" in specimen)) {
                                                console.info('updating age descriptor....');
                                                ageTab.setDescriptor(descriptor);
//                                                console.info("ageID is undefined ********");
                                            }
//                                            console.info('specimen[finclipID]=' + specimen['finclipID']);
                                            if (!("finclipID" in specimen)) {
                                                finclipTab.setDescriptor(descriptor);
//                                                console.info("finclipID is undefined *******");
                                            }
                                            break;
                                        }
                                    }
                                }
                            }
                            if (!isFound) {
                                console.info('no species: ' + specimen[item]);
                            }

                            if (speciesName !== undefined) {
                                var descriptor = getAgeFinclipDescriptor(speciesName);
                                if (lastAgeFinclipRecords === null) {
                                    lastAgeFinclipRecords = fishSampling.getLastAgeFinclipIDs(descriptor);
                                }
                                if (specimen["ageID"] === undefined) {
                                    ageTab.type = descriptor;
                                    ageCategoryBtnMap[descriptor].checked = true;
                                    ageTab.lastAgeID = lastAgeFinclipRecords["age"];
                                    ageTab.lastFinclipID = lastAgeFinclipRecords["finclip"];
                                    ageTypeBtnMap["Otolith"].checked = true;
                                }
                                if (specimen["finclipID"] === undefined) {
                                    finclipTab.type = descriptor;
                                    finclipCategoryBtnMap[descriptor].checked = true;
                                    finclipTab.lastFinclipID = lastAgeFinclipRecords["finclip"];
                                }
                            }

                            break;
                        case "weight":
                            weightTab.numPad.textNumPad.text = specimen[item];
                            updateLabel("weight", specimen[item], "kg", false, null);
                            break;
                        case "length":
                            lengthTab.numPad.textNumPad.text = specimen[item];
                            updateLabel("length", specimen[item], "cm", false, null);
                            break;
                        case "sex":
                            switch (specimen[item]) {
                                case "M":
                                    sexTab.btnMale.checked = true;
                                    break;
                                case "F":
                                    sexTab.btnFemale.checked = true;
                                    break;
                                case "U":
                                    sexTab.btnUnsex.checked = true;
                                    break;
                            }
                            updateLabel("sex", specimen[item], null, false, null);
                            break;
                        case "ageID":
//                            if (specimen["speciesSamplingPlanID"] === undefined) {
                            if (specimen[item] !== undefined) {
                                var ageCategory = specimen[item][0];
                                ageCategory = (ageCategory === "G") ? "A" : ageCategory;
                                var ageID = specimen[item].substr(1);
                                console.info('ageCategory = ' + ageCategory);

                                ageCategoryBtnMap[ageCategory].checked = true;
                                ageTab.type = ageCategory;
                                ageTab.num = ageID;
                                ageTab.numPad.textNumPad.text = ageID;
                                if (lastAgeFinclipRecords === null) {
                                    lastAgeFinclipRecords = fishSampling.getLastAgeFinclipIDs(ageCategory);
                                }
                                ageTab.lastAgeID = lastAgeFinclipRecords["age"];
                                ageTab.lastFinclipID = lastAgeFinclipRecords["finclip"];

                                if ("ageRecID" in specimen) {
                                    ageTab.ageRecExists = true;
                                    console.info("****** SET ageRecExists to true ******");
                                }
                            }
                            ageTypeBtnMap[specimen["ageType"]].checked = true;
                            updateLabel("ageID", specimen[item], null, false, specimen["ageType"]);
//                            }
                            break;
                        case "finclipID":
                            var finclipCategory = specimen[item][0];
                            finclipCategory = (finclipCategory === "G") ? "A" : finclipCategory;
                            finclipCategoryBtnMap[finclipCategory].checked = true;
                            finclipTab.type = finclipCategory;
                            finclipTab.num = specimen[item].substr(1);
                            if (lastAgeFinclipRecords === null) {
                                lastAgeFinclipRecords = fishSampling.getLastAgeFinclipIDs(finclipCategory)
                            }
                            finclipTab.lastFinclipID = lastAgeFinclipRecords["finclip"];

                            if (specimen[item] !== undefined) {
                                finclipTab.numPad.textNumPad.text = specimen[item].substr(1);
                            }
                            if ("finclipRecID" in specimen) {
                                finclipTab.finclipRecExists = true;
                            }
                            updateLabel("finclipID", specimen[item], null, false, null);
                            break;
                        case "dispositionType":
                            dispositionCategoryBtnMap[specimen["dispositionType"]].checked = true;
                            if ((specimen["dispositionType"] === "Released") ||
                                (specimen["dispositionType"] === "Descended")) {
                                dispositionTab.numPad.enabled = true;
                            } else {
                                dispositionTab.numPad.enabled = false;
                            }
                            var value = null;
                            if (specimen["disposition"] !== undefined) {
                                dispositionTab.numPad.textNumPad.text = specimen["disposition"];
                                value = specimen["disposition"];
                            }
                            updateLabel("disposition", value, null, false, specimen["dispositionType"]);
                            break;
                    }
                }
            }

            // Special Tab
            console.info('populating specialTab');
            fishSampling.specialsModel.populateModel(specimenID);
            var specialValue = fishSampling.specialsModel.getSpecialTabLabel();
            if (specialValue !== "") {
                updateLabel("special", specialValue, null, false, null);
            }

            // Potentially setting the tab to the weight tab
            var adhText = tbActions.contentChildren[0].contentItem.text;
            var speciesText = tbActions.contentChildren[1].contentItem.text;
            if ((adhText !== "A-D-H\n") & (speciesText !== "Species\n")) {
                console.info('activating the weightTab');
                tbActions.setCurrentIndex(2);
                stateMachine.currentEntryTab = "weight";
                console.info('stateMachine.currentEntryTab: ' + stateMachine.currentEntryTab);
            }
        }
    }
    function clearTabs() {

        console.log('clearTabs');
        specimenID = null;

        var item;
        var titleSplit;
        var title;
        for (var i=0; i<tbActions.count; i++) {
            item = tbActions.itemAt(i);
            var titleSplit = item.contentItem.text.split("\n");
            if (titleSplit.length === 2) {
                title = titleSplit[0];
            } else {
                title = item.contentItem.text;
            }
            item.contentItem.text = title + "\n";

            if (item !== null) {
                var tabItem = slFishSamplingTabs.children[i];
                switch (title) {
                    case "A-D-H":
                        tabItem.angler = "";
                        tabItem.drop = "";
                        tabItem.hook = "";
                        tabItem.bgAngler.checkedButton = null;
                        tabItem.bgDrop.checkedButton = null;
                        tabItem.bgHook.checkedButton = null;
                        break;
                    case "Species":
                        tabItem.bgSpecies.checkedButton = null;
                        speciesTab.currentSpecies = null;
                        break;
                    case "Weight":
                        tabItem.numPad.textNumPad.text = "";
                        break;
                    case "Length":
                        tabItem.numPad.textNumPad.text = "";
                        break;
                    case "Sex":
                        tabItem.bgSexType.checkedButton = null;
                        break;
                    case "Age":
                        tabItem.bgAgeStructure.checkedButton = tabItem.btnOtolith;
                        tabItem.bgAgeCategory.checkedButton = null;
                        tabItem.type = "";
                        tabItem.num = null;
                        tabItem.lastFinclipID = null;
                        tabItem.lastAgeID = null;
                        tabItem.numPad.textNumPad.text = "";
                        tabItem.ageRecExists = false;
                        break;
                    case "Finclip":
                        tabItem.bgFinclipCategory.checkedButton = null;
                        tabItem.type = "";
                        tabItem.num = null;
                        tabItem.lastFinclipID = null;
                        tabItem.numPad.textNumPad.text = "";
                        tabItem.finclipRecExists = false;
                        break;
                    case "Disposition":
                        tabItem.bgDisposition.checkedButton = null;
                        tabItem.type = null;
                        tabItem.num = null;
                        tabItem.numPad.enabled = false;
                        tabItem.numPad.textNumPad.text = "";
                        break;
                    case "Special":
                        fishSampling.specialsModel.clear();
                        fishSampling.specialsModel.populateModel(null);
                        break;
                }
            }
        }
        stateMachine.currentEntryTab = "adh";  // Set this before the tbActions.setCurrentIndex, otherwise
                                                // may get stuck on species tab when cutter clicks Next Fish
        tbActions.setCurrentIndex(0);
        stateMachine.angler = null;
        stateMachine.drop = null;
        stateMachine.hook = null;
    }
    function nextTab() {
        if (tbActions.currentIndex < tbActions.count-1) {
            tbActions.setCurrentIndex(tbActions.currentIndex + 1);
        }
    }
    function updateLabel(action, value, uom, dbUpdate, actionSubType) {

        // Capture the current specimenID as the stateMachine.previousSpecimenId
        //
        stateMachine.previousSpecimenId = specimenID;

        var newLabel;
        var currentTab;
        var currentTabValue;
        var labelAction = fishSampling.observationToDbMapping(action);
        if ((labelAction.split(" ").length === 2) &
            (labelAction.indexOf(" ID") !== -1)) {
            // Drop the trailing ID for the Age ID and the Finclip ID
            labelAction = labelAction.split(" ")[0];
        }
        console.info('action=' + action + ', value=' + value + ', labelAction=' + labelAction +
                    ', dbUpdate=' + dbUpdate + ', actionSubType=' + actionSubType);

        // Get the tab in question and update it's label
        for (var i in tbActions.contentChildren) {
            if (tbActions.contentChildren[i].contentItem.text.indexOf(labelAction) !== -1) {
                currentTab = tbActions.contentChildren[i];

                if (action !== "disposition") {
                    newLabel = labelAction + "\n" + value.toString().replace("\n"," ").substring(0,11);
                    if (uom !== null) {
                        newLabel = newLabel + " " + uom;
                    }
                } else {
                    newLabel = value ? labelAction + "\n" + actionSubType.substring(0,1) + value :
                                        labelAction + "\n" + actionSubType.substring(0,1);

                }
                currentTab.contentItem.text = newLabel;
                break;
            }
        }

        // Update the Database entry (insert or update), only if dbUpdate = true
        if (dbUpdate) {

            switch (action) {
                case "adh":
                    if (value.length === 3) {

                        // Check if that ADH already exists and if so and if we are dealing with
                        // orphaned data, i.e. specimen data that is tied to a site operation and not
                        // to a angler operation, if the data should be overwritten or not
                        var angler = value[0];
                        var drop = value[1];
                        var hook = value[2];
                        var specimenResult = fishSampling.checkIfSpecimenExists(drop, angler, hook);
                        if ((specimenResult !== null) & (specimenResult !== undefined)) {
                            if ((specimenResult["specimen_id"] !== null) &
                                (specimenResult["specimen_id"] !== undefined) &
                                (specimenResult["specimen_id"] !== "")) {

                                dlgOkayCancel.accepted_action = "select adh";
                                dlgOkayCancel.message = value + " exists, HookMatrix = " + specimenResult["hm_species"]
                                                        +  ", Cutter = " + specimenResult["species"];
                                dlgOkayCancel.action = "Click Okay to open " + value + ", or Cancel to stay with this fish\n" +
                                    "The current fish is saved and you can return to it later"
                                dlgOkayCancel.open();
                            } else {
                                console.info('getting ready to call upsertADH');
                                fishSampling.upsertADH(specimenID, value);
                            }
                        } else {
                            console.info('specimenResult is null, calling upsertADH');
                            fishSampling.upsertADH(specimenID, value);
                        }
                    }
                    break;
                case "species":
                    if ((value !== null) && (value !== undefined)) {
                        value = value.replace("\n", " ");
                    }

                    var hm_species = fishSampling.getHookMatrixSpecies(specimenID);
                    if (value !== hm_species) {
                        var msg = "Cutter species (" + value + ") does not equal\nHookMatrix species (" + hm_species + ")";
                        dlgOkay.message = msg;
                        dlgOkay.action = "Please resolve";
                        dlgOkay.open();
                    }

                    console.info("Changing species, new species=" + value)
                    fishSampling.upsertSpecies(specimenID, value);

                    // Age / Finclip validation checking
                    if (
                        (((ageTab.type === "B") || (finclipTab.type === "B")) && (value !== "Bocaccio")) ||
                        (((ageTab.type === "V") || (finclipTab.type === "V")) && (value !== "Vermilion Rockfish")) ||
                        (((ageTab.type === "A") || (finclipTab.type === "A"))
                                && ((value === "Bocaccio") || (value === "Vermilion Rockfish")))
                        ) {
                            var msg = "Age ID and/or Finclip ID letters are incorrect for new species";
                            dlgOkay.message = msg;
                            dlgOkay.action = "Please fix";
                            dlgOkay.open();
                            console.info("********* " + msg + " *************");
                        }

                    // Check if the ageID exists, if not, set the ageDescriptor
                    var descriptor = getAgeFinclipDescriptor(value);
                    var lastAgeFinclipRecords = fishSampling.getLastAgeFinclipIDs(descriptor);
                    console.info('ageTab.ageRecExists=' + ageTab.ageRecExists);
                    if (!(ageTab.ageRecExists)) {
                        console.info('updating age descriptor....');
                        ageTab.setDescriptor(descriptor);
                        ageTab.lastFinclipID = lastAgeFinclipRecords["finclip"];
                        ageTab.lastAgeID = lastAgeFinclipRecords["age"];
                    }

                    // Check if the finclipID exists, if not, set the finclipDescriptor
                    console.info('finclipTab.finclipRecExists=' + finclipTab.finclipRecExists);
                    if (!(finclipTab.finclipRecExists)) {
                        finclipTab.setDescriptor(descriptor);
                        finclipTab.lastFinclipID = lastAgeFinclipRecords["finclip"];
                    }

                    nextTab();
                    break;
                default:
                    var dataType = null;
                    if (['weight', 'length'].indexOf(action) >= 0) {
                        dataType = 'numeric';
                    } else {
                        dataType = 'alpha'
                    }

                    // TODO Todd Hay - Do I need to properly set the subAction and speciesSamplingPlanId?
                    var speciesSamplingPlanId = null;
                    actionSubType = actionSubType ? actionSubType.replace("\n", " ") : null;
                    fishSampling.upsertObservation(specimenID, action, value, dataType,
                                                    actionSubType, speciesSamplingPlanId);

                    // # 94: check LW relationship when sex/length/weight changes
                    if (action === 'sex' || action === 'length' || action === 'weight') {
                        fishSampling.checkLWRelationship()
                    }
                    break;
            }
        }
    }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"

        ColumnLayout {
            spacing: 25
            anchors.fill: parent
            TabBar {
                id: tbActions
                currentIndex: slFishSamplingTabs.currentIndex
                Layout.preferredWidth: parent.width

                Repeater {
                    model: ["A-D-H", "Species", "Weight", "Length",
                        "Sex", "Age", "Finclip", "Disposition", "Special"]
                    TabButton {
//                        text: modelData
                        background: Rectangle {
                            implicitWidth: 100
                            implicitHeight: 60
                            opacity: enabled ? 1 : 0.3
                            color: checked ? "white" : "#dddddd"
                            border.color: "black"
                            border.width: 1
                            radius: 2
                        }
                        contentItem: Text {
                            text: modelData + "\n"
                            font.pixelSize: 20
                            color: "black"
                            opacity: enabled ? 1.0 : 0.3
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        onPressed: {
                            wasTabPressed = true;
                            console.info('tab ' + modelData + ' was pressed');
                        }
                    }
                }
                onCurrentIndexChanged: {

                    if (dlg.visible) {

                        console.info("Tab Changed: stateMachine tab: " + stateMachine.currentEntryTab +
                                    ", currentSpecies = " + speciesTab.currentSpecies +
                                    ', currentIndex: ' + currentIndex +
                                    ', wasTabPressed: ' + wasTabPressed);

                        // Clear the specialTab
                        specialTab.tvSpecial.selection.clear();
                        specialTab.tvSpecial.currentRow = -1;   // Need to set this as well otherwise btnAssignLabel can still be enabled

                        // Species tab - ensure that a species is collected
                        if ((stateMachine.currentEntryTab === "species") && (speciesTab.currentSpecies === null)) {
                            console.info("trying to leave the species tab and no species, require species entry");
                            dlgOkay.message = "You have not entered a species";
                            dlgOkay.action = "Please enter a species before proceeding";
                            dlgOkay.open();

                            currentIndex = 1;
                            stateMachine.currentEntryTab = "species";

                            return;

                        // Sex tab - ensure that a sex is collected
                        } else if ((stateMachine.currentEntryTab === "sex") &&
                            (speciesTab.currentSpecies !== null) &&
                            (sexTab.bgSexType.checkedButton === null)) {
                            console.info("trying to leave the sex tab with no sex entered");
                            dlgOkay.message = "You have not entered a sex";
                            dlgOkay.action = "Please enter a sex before proceeding";
                            dlgOkay.open();

                            currentIndex = 4;
                            stateMachine.currentEntryTab = "sex";

                            return;

                        // 20190916 - This is used by the
                        // for protocols for Bocaccio and Vermilion for the non-random drops, as follows:
                        //  If non-random and
                        //     bocaccio - skip age + finclip, go right to disposition
                        //     vermilion - skip age, go right to finclip
                        //
                        // Need to be careful about circular looping here, as stepping for the index will again
                        // call this onCurrentIndexChanged event
                        } else if (fishSampling.randomDrops.indexOf(parseInt(adhTab.drop)) === -1) {

                            if (wasTabPressed) {

                                wasTabPressed = false;

                            } else {
                                console.info('currentDrop = ' + adhTab.drop + ', int version: ' + parseInt(adhTab.drop) +
                                    ', randomDrops = ' + fishSampling.randomDrops +
                                    ', in randomDrops = ' + fishSampling.randomDrops.indexOf(parseInt(adhTab.drop)));

                                if ((speciesTab.currentSpecies === "Bocaccio") && (currentIndex === 5 || currentIndex === 6)) {

                                    currentIndex = 7;
                                    stateMachine.currentEntryTab = "disposition";
                                    return;

                                } else if ((speciesTab.currentSpecies.indexOf("Vermilion") >= 0) && (currentIndex === 5)) {

                                    currentIndex = 6;
                                    stateMachine.currentEntryTab = "finclipID";
                                    return;

                                }
                            }
                        }
//                        else if (fishSampling.randomDrops.indexOf(parseInt(adhTab.drop)) >= 0) {
//
//                            if ((stateMachine.currentEntryTab === "ageID") && (speciesTab.currentSpecies === "Bocaccio" ||
//                                speciesTab.currentSpecies === "Vermilion Rockfish") && ageTab.) {
//
//                            } else if ((stateMachine.currentEntryTab === "finclipID") && (speciesTab.currentSpecies === "Bocaccio")) {
//
//                            }
//                        }

                        // Retrieve + set state currentEntryTab
                        var currentAction = slFishSamplingTabs.itemAt(currentIndex).action;
                        stateMachine.currentEntryTab = currentAction;
                        console.info('Tab Changed: stateMachine.currentEntryTab=' + stateMachine.currentEntryTab);

                    }

                }
            } // tbActions
            StackLayout {
                id: slFishSamplingTabs
                width: parent.width
                currentIndex: tbActions.currentIndex

                function retrieveLabelElements() {
                    // Method to retrieve the elements for printing a Special Label.  The only item
                    // that I really need is the species, as this is used to define the 4-character observation
                    // number of the tag number label
                    var cb = speciesTab.bgSpecies.checkedButton;
                    if (cb === null) {
                        return null;
                    }
                    return cb.text.replace("\n", " ");
                }
                function retrieveSpecimenID() { return specimenID; }
                function retrieveSpeciesObservations() {
                    var item = {};
                    item["species"] = speciesTab.bgSpecies.checkedButton ?
                        speciesTab.bgSpecies.checkedButton.text.replace("\n", " ") : "";
                    item["length"] = lengthTab.numPad.textNumPad.text;
                    item["weight"] = weightTab.numPad.textNumPad.text;
                    item["sex"] = sexTab.bgSexType.checkedButton ?
                        sexTab.bgSexType.checkedButton.text : "";

                    return item;
                }
                function retrieveFinclipID() {
                    if ((finclipTab.type === "") & (finclipTab.num === null)) {
                        return null;
                    }
                    return {"type": finclipTab.type, "num": finclipTab.num};
                }
                function retrieveAgeID() {
                    if ((ageTab.type === "") & (ageTab.num === null)) {
                        return null;
                    }
                    return {"type": ageTab.type, "num": ageTab.num};
                }
                function retrieveSpecies() { return speciesTab.currentSpecies; }
                function retrieveDrop() {
                    // 20190916 - Function to retrieve the drop of the current specimen.  This is used by the
                    // for protocols for Bocaccio and Vermilion for the non-random drops, as follows:
                    //  If non-random and
                    //     bocaccio - skip age + finclip, go right to disposition
                    //     vermilion - skip age, go right to finclip
                    return adhTab.drop;
                }

                AnglerDropHookItem {
                    id: adhTab;
                    onSerialPortTest: serialPortDataReceived(action, value, uom, dbUpdate);
                    onLabelSet: updateLabel(action, value, uom, dbUpdate, actionSubType);
                    onAdvanceTab: nextTab();
                }
                SpeciesItem { id: speciesTab; onLabelSet: updateLabel(action, value, uom, dbUpdate, actionSubType); onAdvanceTab: nextTab(); }
                WeightItem { id: weightTab; onLabelSet: updateLabel(action, value, uom, dbUpdate, actionSubType); onAdvanceTab: nextTab(); }
                LengthItem { id: lengthTab; onLabelSet: updateLabel(action, value, uom, dbUpdate, actionSubType); onAdvanceTab: nextTab(); }
                SexItem { id: sexTab; onLabelSet: updateLabel(action, value, uom, dbUpdate, actionSubType); onAdvanceTab: nextTab(); }
                AgeItem { id: ageTab; onLabelSet: updateLabel(action, value, uom, dbUpdate, actionSubType); onAdvanceTab: nextTab(); }
                FinclipItem { id: finclipTab; onLabelSet: updateLabel(action, value, uom, dbUpdate, actionSubType); onAdvanceTab: nextTab(); }
                DispositionItem { id: dispositionTab; onLabelSet: updateLabel(action, value, uom, dbUpdate, actionSubType); onAdvanceTab: nextTab(); }
                SpecialItem { id: specialTab; onLabelSet: updateLabel(action, value, uom, dbUpdate, actionSubType); onAdvanceTab: nextTab(); }
            } // tab items
            RowLayout {
                id: rlButtons
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 10
                anchors.right: parent.right
                anchors.rightMargin: 10
                spacing: 10
                BackdeckButton {
                    id: btnNotes
                    text: "Notes"
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 60
                    onClicked: {
                        stateMachine.angler = adhTab.angler;
                        stateMachine.drop = adhTab.drop;
                        stateMachine.hook = adhTab.hook;
                        console.info('sm currentEntryTab: ' + stateMachine.currentEntryTab);
//                        dlgNotes.open();
                        dlgDrawingNotes.open();
//                        dlgDrawingNotes.canvas.clear_canvas();
                    }
                } // btnNotes
                BackdeckButton {
                    id: btnNextFish
                    text: "Next Fish"
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 60
                    onClicked: {
                        soundPlayer.playSound("hlCutterStationNextFish", 0, false);
                        clearTabs();
                        specimenCleared();
                    }
                } // btnNextFish
                BackdeckButton {
                    id: btnFinished
                    text: "Finished"
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 60
                    onClicked: {

                        dlg.accept()
                    }
                } // btnFinished
            } // rlButtons
        }

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }

//    NotesDialog { id: dlgNotes }
    DrawingNotesDialog { id: dlgDrawingNotes }
    OkayCancelDialog {
        id: dlgOkayCancel
        onAccepted: {
            switch (accepted_action) {
                case "select adh":
                    var angler = adhTab.angler;
                    var drop = adhTab.drop;
                    var hook = adhTab.hook;
                    console.info('opening ' + angler + drop + hook + ' record');
                    fishSampling.selectSpecimenRecordByADH(angler, drop, hook);
                    break;
            }
        }
        onRejected: {
            switch (accepted_action) {
                case "select adh":

                    console.info('staying with the exist record, using specimenID=' + stateMachine.previousSpecimenId);
                    if (stateMachine.previousSpecimenId !== undefined) {
                        fishSampling.selectSpecimenRecordByID(stateMachine.previousSpecimenId);
                    } else {
                        tbActions.itemAt(0).contentItem.text = "A-D-H\n";
                        adhTab.angler = "";
                        adhTab.drop = "";
                        adhTab.hook = "";
                        adhTab.bgAngler.checkedButton = null;
                        adhTab.bgDrop.checkedButton = null;
                        adhTab.bgHook.checkedButton = null;
                    }
                    break;
            }
        }
    }
    OkayDialog {
        id: dlgOkay
        modality: Qt.ApplicationModal
    }
    LengthWeightDialog {
        // #94: LW dialog to pop with message
        id: dlgLwWarning
        message: ""
        onProceed: {  // do nothing, go to age tab
            tbActions.setCurrentIndex(5)
            dlgLwWarning.close()
        }
        onProceedWNote: {  // do nothing, open note dialog
            tbActions.setCurrentIndex(5)
            dlgLwWarning.close()
            dlgDrawingNotes.open()
        }
        onEditWeight: {  // back to weight tab
            tbActions.setCurrentIndex(2)
            dlgLwWarning.close()
        }
        onEditLength: {  // back to length tab
            tbActions.setCurrentIndex(3)
            dlgLwWarning.close()
        }
        onEditSex: {  // back to sex tab
            tbActions.setCurrentIndex(4)
            dlgLwWarning.close()
        }
    }
    SpeciesConflictDialog {
        id: dlgSpeciesConflict
        onAccepted: {
            console.info("Realign catch");
            fishSampling.realignCatchRecord(tempValues);
        }
        onRejected: {
            console.info("reset the ADH tab label");
            tbActions.itemAt(0).contentItem.text = "A-D-H\n";
            adhTab.angler = "";
            adhTab.drop = "";
            adhTab.hook = "";
            adhTab.bgAngler.checkedButton = null;
            adhTab.bgDrop.checkedButton = null;
            adhTab.bgHook.checkedButton = null;
        }
    }
}
