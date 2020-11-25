/**
 * CountsWeightsNewBasketSM.js: a state machine for handling entry of new basket weights and counts.
 * A little data on editing existing baskets (status messages) is placed here as well.
 */

// Note: no .pragma library, thus making variables of CountsWeightsScreen visible.

// Messages for editing existing baskets. A little out-of-place (everything else in this file is
// is related to entering new baskets), but having all the messages to display in the status message box
// in one place is useful.
var msgStartState = "Click numpad digit to add new basket.";
var msgStartStateWithBaskets = "Click numpad digit to add new basket\nor click Edit Basket button.";
var msgStartEditingExistingBasket = "Editing existing basket:\nEnter digit, decimal pt, or OK";
var msgEditClickedWithoutBasketSelected = "Please select existing basket";

// Messages for entering new baskets
var msgNBWIP = "New basket weight:\nEnter digit, decimal pt, or OK";
var msgNBWIP_DECPT_DONE = "New basket weight:\nEnter digit, or OK";
var msgRFNBC = "New basket count:\nEnter digit or No Count";
var msgNBCIP = "New basket count:\nEnter digit, No Count, or OK";

var NEW_BASKET_STATE = {
    RFNBW: {value: 0, name: "ReadyForNewBasketWeight"},
    NBWIP: {value: 1, name: "NewBasketWeightInProgress"},
    RFNBC: {value: 2, name: "ReadyForNewBasketCount"},
    NBCIP: {value: 3, name: "NewBasketCountInProgress"}
};
var curNewBasketState = NEW_BASKET_STATE.RFNBW;

var NEW_BASKET_EVENT = {
    // UI actions that may require an action and update in state
    DIGIT: {value: 0, name: "DigitPressed"},
    DELETE_CONFIRMED: {value: 1, name: "DeleteConfirmed"},
    OK: {value: 2, name: "OKPressed"},
    MANUAL_WEIGHT: {value: 3, name: "ManualWeightButton"},
    NO_COUNT: {value: 4, name: "NoCountButton"},
    MATRIX_WEIGHT: {value: 5, name: "MatrixWeightButton"}
};

function resetNewBasketState() {
    //console.trace();
    enableNavigation(true);
    updateBasketStatusMessage(null);
    numPad.btnOk.visible = true;    // Set to false in RFNBC
    btnEditBasket.visible = true;  // Set to false entering NBWIP
    curNewBasketState = NEW_BASKET_STATE.RFNBW;
}

function isEnteringNewBasket() {
    // Has a new basket entry been commenced?
    console.debug("curNewBasketState=" + curNewBasketState.name);
    var isEntering = (curNewBasketState !== NEW_BASKET_STATE.RFNBW);
    console.debug("isEnteringNewBasket=" + isEntering);
    //console.trace();
    return isEntering;
}

function isEnteringNewBasketWeight() {
    // Has a new basket entry been commenced, and at least one digit has been entered?
    var isEnteringWeight = curNewBasketState === NEW_BASKET_STATE.NBWIP;
    console.debug("isEnteringNewBasketWeight=" + isEnteringWeight);
    return isEnteringWeight;
}

function handleNewBasketEvent(basketEvent, isEditingExistingBasket) {
    console.info("Basket Event " + basketEvent.name + "State on entry =" +
        curNewBasketState.name + ", isEditingExistingBasket=" + isEditingExistingBasket);

    if (isEditingExistingBasket) {
        console.info("handleNewBasketEvent: no action taken - existing basket is being edited.");
        return;
    }

    saveTabEnableState();   // A one-shot, on first entry.

    if (basketEvent === NEW_BASKET_EVENT.DIGIT) {
        console.info("Current numPad text = '" + numPad.textNumPad.text + "'.");
        if (curNewBasketState === NEW_BASKET_STATE.RFNBW) {
            enableNavigation(false);
            // Hide editing existing basket until new basket completed.
            btnEditBasket.visible = false;
            updateBasketStatusMessage(msgNBWIP);
            curNewBasketState = NEW_BASKET_STATE.NBWIP;
            return;
        }

        if (curNewBasketState === NEW_BASKET_STATE.NBWIP) {
            // No state change, but message may need to be updated if a decimal point has been entered.
            var msg =  numPad.decimalPointHasBeenEntered()? msgNBWIP_DECPT_DONE: msgNBWIP;
            updateBasketStatusMessage(msg);
            return;
        }

        if (curNewBasketState === NEW_BASKET_STATE.RFNBC) {
            enableNavigation(false);
            updateBasketStatusMessage(msgNBCIP);
            curNewBasketState = NEW_BASKET_STATE.NBCIP;
            // Digit entered, so make sure OK button enabled leaving RFNBC state.
            numPad.btnOk.visible = true;
            return;
        }

        if (curNewBasketState === NEW_BASKET_STATE.NBCIP) {
            // No state change, no action needed. Carry on.
            return;
        }

        console.error("Unexpected unhandled basket transition. Cur state=" +
            curNewBasketState.name + ", event=" + basketEvent.name);
        return;
    }

    if (basketEvent === NEW_BASKET_EVENT.DELETE_CONFIRMED) {
        enableNavigation(true);
        updateBasketStatusMessage(null);
        curNewBasketState = NEW_BASKET_STATE.RFNBW;
        return;
    }

    if (basketEvent === NEW_BASKET_EVENT.OK) {
        if (curNewBasketState === NEW_BASKET_STATE.NBWIP) {
            if ( screenCW.speciesIsCounted() ) {
                enableNavigation(false);
                updateBasketStatusMessage(msgRFNBC);
                curNewBasketState = NEW_BASKET_STATE.RFNBC;
                // Hide OK (labeled Skip) until digit entered.
                // (No Count button provided for entering no count).
                numPad.btnOk.visible = false;
            } else {
                // MIX Species
                resetNewBasketState();
            }
            return;
        }

        if (curNewBasketState === NEW_BASKET_STATE.NBCIP) {
            resetNewBasketState();
            return;
        }
        console.error("Unexpected unhandled basket transition.");
        return;
    }

    if (basketEvent === NEW_BASKET_EVENT.MANUAL_WEIGHT) {
        // If Manual Weight button pressed while ready for new basket count or count in progress,
        // update state, update message, and show OK button if a weight has been entered.
        if (curNewBasketState === NEW_BASKET_STATE.RFNBC ||
                curNewBasketState === NEW_BASKET_STATE.NBCIP) {
            updateBasketStatusMessage(msgNBWIP);
            curNewBasketState = NEW_BASKET_STATE.NBWIP;
            if (numPad.containsAValue()) {
                numPad.btnOk.visible = true;
            }
        }
        return
    }

    if (basketEvent === NEW_BASKET_EVENT.NO_COUNT) {
        // Should only occur if current state is ready for count, or in count
        if (curNewBasketState === NEW_BASKET_STATE.RFNBC ||
                curNewBasketState === NEW_BASKET_STATE.NBCIP) {
            resetNewBasketState();
            numPad.btnOk.visible = true; // Would be hidden if RFNBC; redundant for NBCIP.
            return;
        }
        console.error("Unexpected unhandled basket transition.")
    }
    if (basketEvent === NEW_BASKET_EVENT.MATRIX_WEIGHT) {
        if (curNewBasketState === NEW_BASKET_STATE.RFNBC) {
            console.info("READY FOR MATRIX WEIGHT!!!")
        } else {
            console.info("NOT READY FOR MATRIX WEIGHT :(")
        }
    }
}

function enableNavigation(doEnable) {
    // Enable/Disable navigation to home
    framHeader.backwardEnable(doEnable);
    // Enable/Disable adding comment
    framFooter.hideCommentButton(!doEnable);

    enableTabNavigation(doEnable);  // removed problematic BS tab enabling

    // Enable/disable transitions on screen - Discard Reason, changing basket row.
    enableDiscardReason(doEnable);
    enableBasketRowChange(doEnable);
}

var originalTabCCEnable = true;
var originalTabSpEnable = true;
var originalTabBSEnable = true;

var originalTabEnablesSaved = false;
function saveTabEnableState() {
    if (!originalTabEnablesSaved) {
        originalTabCCEnable = tabView.tabCC.enabled;
        originalTabSpEnable = tabView.tabSp.enabled;
        originalTabBSEnable = tabView.tabBS.enabled;
        originalTabEnablesSaved = true;
    }
}

function enableTabNavigation(doEnable) {
    if (!doEnable) {
        // Consider adding CC to this: tabView.enableEntryTabs(false);
        tabView.enableCatchCategoriesTab(false);
        tabView.enableSpeciesTab(false);
        tabView.enableBiospecimensTab(false);
    } else {
        tabView.enableCatchCategoriesTab(originalTabCCEnable);
        tabView.enableSpeciesTab(originalTabSpEnable);
        tabView.enableBiospecimensTab(originalTabBSEnable);
        updateBasketStatusMessage("");
    }
}

function enableDiscardReason(doEnable) {
    gridDR.enabled = doEnable;
}

function enableBasketRowChange(doEnable) {
    tvBaskets.enabled = doEnable;
    console.debug("Enable basket row change = " + tvBaskets.enabled)
}

function updateBasketStatusMessage(message) {
    basketEntryStatusMessage.update(message);
}
