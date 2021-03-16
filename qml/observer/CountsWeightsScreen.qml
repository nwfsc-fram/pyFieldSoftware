import QtQuick 2.6
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0

import "../common"
import "."
import "codebehind/CountsWeightsNewBasketSM.js" as NBSM

Item {
    id: screenCW

    ////
    // Properties, Functions and Pop-up Dialogs
    ////
    property bool stateCW: false // set by signals, true if in CW state
    property bool is_mix: appstate.catches.species.currentSpeciesItemName === 'MIX'
    property int dec_places: appstate.displayDecimalPlaces  // Number of decimal places to display weight values

    Connections {
        target: obsSM
        onEnteringCW: {
            modeSC.reset();
        }
        onExitingCW: {  // FIELD-2039: warn if all baskets are no count (and not mix)
            if (!is_mix) {
                // check if we have all No Count baskets, warn if true
                if (tvBaskets.model.count > 0) {
                    var total_count = 0
                    for (var i = 0; i < tvBaskets.model.items.length; i++) {
                        total_count += tvBaskets.model.items[i].fish_number_itq
                    }
                    if (!total_count) {
                        framHeader.dlgCWNoCountCheck.open()
                    }
                }
            }
        }
    }
    Connections {
        // FIELD-2095: clears out sticky tab states after species switch
        target: appstate.catches.species
        onSelectedSpeciesItemChanged: {
            NBSM.unsaveTabEnableState()
        }
    }

    function basketWeightIsTooHigh(weight) {
        // Maximum trawling basket weight is specified in the SETTINGS table of Observer.db
        return (weight > appstate.trawlMaxBasketWeightLbs);
    }

    function basketWeightNeedsConfirmation(weight) {
        // Trawling basket weight requiring confirmation is specified in the SETTINGS table of Observer.db
        return (weight > appstate.trawlConfirmBasketWeightLbs);
    }

    function warnIfAvgWeightShowsAsZero() {
        // FIELD-1423: Pop up a warning if average weight displayed is '0.00'
        // (Weight is non-zero but less than 0.005)
        // Called in two contexts:
        // 1. On entering a new weight-and-count basket (numpad.numpadEnteredCount())
        // 2. On deleting a basket (confirmRemoveBasket.onConfirmedFunc)
        //
        // A third context was considered but dropped as being too annoying:
        // 3. At entry to screen (obsSM.onEnteringCW)

        console.assert(numPad.limitToTwoDecimalPlaces,
            'Method assumes numpad entry is limited to two decimal digits - the default.');

        var avgWeight = appstate.catches.species.counts_weights.avgWeight;

        console.debug("Displayed average weight ='" + tfAvgWeight.text + "'.");
        if (avgWeight < 0.005) {
            dlgAvgWeightDisplayedAsZero.nearZeroWeight = avgWeight.toFixed(4);
            dlgAvgWeightDisplayedAsZero.open();
        }
    }

    // All species except 'MIX' are counted.
    // If the screen is for MIX species, provide a test for removing count-related buttons, columns, and fields.
    function speciesIsCounted() {
        return !appstate.catches.species.counts_weights.speciesIsNotCounted();
    }

    FramNoteDialog {
        id: dlgBasketWeightTooHeavy
        property string invalidWeight
        property string weightMax
        message: "Weight of basket (" + invalidWeight + " lbs)\n" +
                " exceeds " + weightMax + " lbs."
        font_size: 18
    }

    FramNoteDialog {
        id: dlgBasketWeightBadDecimalDigits
        property string invalidWeight
        message: "Weight of basket (" + invalidWeight + " lbs)\n" +
                " has two decimal digits\nnot ending in 0 or 5."
        font_size: 18
    }

    FramNoteDialog {
        id: dlgAvgWeightDisplayedAsZero
        property string nearZeroWeight
        message: "Warning: Average Fish Weight\n" +
                "(" + nearZeroWeight + " lbs)\n" +
                "is less than 0.005 pounds."
        font_size: 18
    }

    Item {
        id: modeSC  // Implementation of Species Composition Basket Counts/Weights

        ///////////////////////
        // SPECIES COMP BASKETS
        ///////////////////////

        ////
        // Species Comp Baskets: Properties and Functions
        ////
        property var currentSpeciesName
        property var discardModel: discardReason.DiscardReasonModel

        function addNewBasket(weight, count) {
            console.log("wt " +  weight + " ct " + count)
            appstate.catches.species.counts_weights.addBasket(weight, count)
        }

        function addTallyBasket(count) {
            console.log("tally ct " + count)
            appstate.catches.species.counts_weights.addBasket(null, count)
        }

        Connections {
            target: appstate.catches.species.counts_weights
            onBasketAdded: {
                modeSC.selectNewestBlankRow();
            }
        }

        Connections {
            target: appstate
            onSpeciesNameChanged: {
                modeSC.currentSpeciesName = appstate.speciesName;
            }
        }

        function editBasketWeight(basket_id, weight) {
            appstate.catches.species.counts_weights.editBasketWeight(basket_id, weight)
        }

        function editBasketCount(basket_id, count) {
            appstate.catches.species.counts_weights.editBasketCount(basket_id, count)
        }

        function removeBasket(basket_id) {
            appstate.catches.species.counts_weights.deleteBasket(basket_id);
            reset();
        }

        function reset() {
            console.debug('Reset called');
            tvBaskets.isEditingExistingBasket = false;
            NBSM.resetNewBasketState();
            tvBaskets.currentRow = -1;
            tvBaskets.selection.clear();
            btnManualWeight.checked = true;
            btnManualCount.enabled = false;  // Disable until editing existing basket.
            numPad.setSkipButtonMode(false);
            numPad.clearnumpad();
            btnEditBasket.checked = false;
            var msgStartState = tvBaskets.model.count > 0? NBSM.msgStartStateWithBaskets: NBSM.msgStartState;
            basketEntryStatusMessage.update(msgStartState);
        }

        function selectNewestRow() {
            if (tvBaskets.model.count > 0) {
                tvBaskets.selection.clear();
                tvBaskets.currentRow = 0;
                tvBaskets.selection.select(0);  // Topmost Basket = newest

                if (!tvBaskets.model.get(0).basket_weight_itq) {
                    // If no weight set, then deselect - this is a tally basket
                    tvBaskets.currentRow = -1;
                    tvBaskets.selection.clear();
                }

            }
        }

        function selectNewestBlankRow() {
            if (tvBaskets.model.count > 0) {
                tvBaskets.currentRow = -1;
                tvBaskets.selection.clear();
                var is_blank = !tvBaskets.model.get(0).basket_weight_itq &&
                                !tvBaskets.model.get(0).fish_number_itq;
                if (is_blank) {
                    tvBaskets.currentRow = 0;
                    tvBaskets.selection.select(0);
                }
            }
        }

        function getBasketIdForCurrentRow() {
            return tvBaskets.model.get(tvBaskets.currentRow).basket_primary_key
        }

        function addBasketWeight(basket_id, weight) {
            modeSC.editBasketWeight(basket_id, weight);
            if (screenCW.speciesIsCounted()) {
                btnManualCount.enabled = true;
                btnManualCount.checked = true;
                numPad.selectAll();
            } else {
                // Pseudo-species 'MIX' is weighed but not counted. Get ready to enter another weight.
                modeSC.reset();
            }
        }

        ColumnLayout {
            id: colDispDR
            x: 5
            y: -35  // Sneak this into the TabView area
            Row {
                Label {
                    id: lblDisposition
                    text: "Disposition:"
                    width: 150
                    height: 40
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 20
                }
                ExclusiveGroup { id: dispSpeciesGroup }
                ObserverGroupButton {
                    id: buttonDispD
                    text: "Discarded"
                    width: 125
                    height: lblDisposition.height
                    exclusiveGroup: dispSpeciesGroup
                    checked: !appstate.catches.species.isRetained
                    enabled: false
                    visible: checked

                }
                ObserverGroupButton {
                    id: buttonDispR
                    text: "Retained"
                    width: buttonDispD.width
                    height: lblDisposition.height
                    exclusiveGroup: dispSpeciesGroup
                    checked: !buttonDispD.checked
                    enabled: false
                    visible: checked
                }
            }

            Row {
                id: rowDR
                visible: !appstate.catches.species.isRetained && !is_mix  // FIELD-2028
                signal drCleared
                function clear_discard_reason() {
                    gridDR.current_discard_id = null;
                    gridDR.set_discard_desc();
                    drCleared();
                }

                Label {
                    text: "Discard Reason:"
                    width: lblDisposition.width
                    height: lblDisposition.height
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 20
                }

                GridLayout {
                    id: gridDR
                    columns: modeSC.discardModel.count
                    property var current_discard_id: null


                    function is_dr_set() { // check if discard reason is set
                        return current_discard_id !== null;
                    }

                    function is_dr_available(discard_id) { // discard reason may already be used by current species
                        var currentSpecies = appstate.catches.species.currentSpeciesItemSpeciesID;

                        console.debug("Current species ID is " + currentSpecies);
                        var isAvailable = !appstate.catches.species.speciesWithDiscardReasonInSelected(
                                currentSpecies, discard_id);
                        console.debug("Discard Reason " + discard_id +
                                (isAvailable ? " Available" : " Not Available") +
                                " for Species " + currentSpecies);
                        return isAvailable;
                    }

                    function set_discard_desc() {
                        if (gridDR.current_discard_id === null) {
                            labelDRDesc.text = "Please select Discard Reason.";
                            labelDRDesc.color = "red";
                            return;
                        } else if (labelDRDesc.color !== "black") {
                           labelDRDesc.color = "black";
                        }

                        // set textfield desc
                        var idx = modeSC.discardModel.get_item_index('discard_id', gridDR.current_discard_id)
                        if (idx >= 0) {
                            labelDRDesc.text = modeSC.discardModel.get(idx).text
                            appstate.catches.species.discardReason = gridDR.current_discard_id;
                        }
                        tabView.enableBiospecimensTab(true);
                    }

                    Connections {
                        target: tvBaskets
                        onModelChanged: {
                            gridDR.current_discard_id = appstate.catches.species.discardReason;
                            if (!gridDR.current_discard_id) {
                                rowDR.clear_discard_reason();
                            } else {
                                gridDR.set_discard_desc();
                            }
                        }
                    }

                    ExclusiveGroup { id: groupDR }
                    Repeater {
                        id: rptDRButtons

                        model: modeSC.discardModel

                        ObserverGroupButton {
                            visible: ['-1', '12', '15'].indexOf(discard_id) == -1  // FIELD-2104
                            text: discard_id
                            exclusiveGroup: groupDR
                            Layout.preferredWidth: 50
                            Layout.preferredHeight: 40
                            checked: discard_id == gridDR.current_discard_id
                            onClicked: {
                                var current_DR = appstate.catches.species.discardReason;

                                if (gridDR.is_dr_available(discard_id)) {
                                    if (appstate.catches.biospecimens.dataWithDiscardReasonExists(current_DR)) {
                                        console.info("A biospecimen record exists for this spec comp item; changing DR anyway.");
                                        dlgWarnDRChange.askDRChange(discard_id);
                                        return;
                                    }
                                    gridDR.current_discard_id = discard_id;
                                    gridDR.set_discard_desc();
                                } else {
                                    var commonName = appstate.catches.species.currentSpeciesItemName;
                                    console.warn("Discard " + discard_id + " already in use " +
                                            "in existing row for species " + commonName + " " +
                                            "in Species tab");
                                    dlgDiscardReasonUsed.commonName = commonName;
                                    dlgDiscardReasonUsed.discardReason = discard_id;
                                    dlgDiscardReasonUsed.open();
                                    rptDRButtons.restoreCheckedButton();
                                }

                                if (ObserverSettings.enableAudio) {
                                    soundPlayer.play_sound("click", false)
                                }
                            }

                            Connections {
                                target: rowDR
                                onDrCleared: {
                                    checked = false;
                                }
                            }
                            Connections {
                                // Ensure correct button is highlighted
                                target: appstate.catches.species
                                onDiscardReasonChanged: {
                                    checked = Boolean(text == discard_reason);
                                }
                            }
                        }
                        function restoreCheckedButton() {
                            var cur_DR = appstate.catches.species.discardReason;
                            if (cur_DR == null) {
                                console.debug("Current DR (before error) was undefined. No action taken.");
                                rowDR.clear_discard_reason();
                                return;
                            }
                            console.debug("Current DR (before error) was " + cur_DR);
                            var checkedDRButtonIdx = model.get_item_index('discard_id', cur_DR);
                            var checkedDRButton = rptDRButtons.itemAt(checkedDRButtonIdx);
                            groupDR.current = checkedDRButton;
                            console.debug("Restored checked DR button to '" + checkedDRButton.text + "'.");
                        }
                    }
                }
                Label {
                    // Spacer
                    width: 15
                }
                Label {
                    id: labelDRDesc
                    width: 200
                    height: lblDisposition.height
                    Layout.preferredHeight: 40
                    font.pixelSize: 20
                    font.bold: true
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        ////
        // Species Comp Baskets: CW Numpad, Disposition, Discard Reason
        ////
        ObserverGroupBox {
            id: grpMeasurementType
            x: 5
            y: 80
            width: 400
            height: 550
            title: "Counts & Weights"

            ExclusiveGroup {
                id: egMeasurementType
            }
            ColumnLayout {
                x: 10
                y: 20
                spacing: 10
                Row {
                    id: rwMeasurementTypes
                    spacing: 10
                    width: grpMeasurementType.width
                    ObserverGroupButton {
                        id: btnScaleWeight
                        text: "Scale\nWeight"
                        exclusiveGroup: egMeasurementType
                        visible: false  // Scale weight not yet implemented.
                    }
                    ObserverGroupButton {
                        id: btnManualWeight
                        text: "Manual\nWeight"
                        checked: true
                        exclusiveGroup: egMeasurementType
                        onCheckedChanged: {
                            if (checked) {
                                if (tvBaskets.currentRow != -1) {
                                    numPad.setnumpadvalue(tvBaskets.model.get(tvBaskets.currentRow).basket_weight_itq);
                                    numPad.selectAll();
                                }
                                numPad.show_no_count(false);
                                numPad.showDecimal(true);
                                NBSM.handleNewBasketEvent(NBSM.NEW_BASKET_EVENT.MANUAL_WEIGHT, btnEditBasket.checked);
                            }
                        }

                    }
                    ObserverGroupButton {
                        id: btnManualCount
                        text: "Manual\nCount"
                        exclusiveGroup: egMeasurementType
                        // Species 'MIX' is weighed but not counted
                        visible: screenCW.speciesIsCounted()
                        onCheckedChanged: {
                            if (checked) {
                                if (tvBaskets.currentRow != -1) {
                                    // load fish count value
                                    numPad.setnumpadvalue(tvBaskets.model.get(tvBaskets.currentRow).fish_number_itq);
                                    numPad.selectAll();
                                }
                                numPad.show_no_count(true);
                                numPad.showDecimal(false);
                            }
                        }                        
                    }
                }
                Row {
                    FramNumPad {
                        id: numPad
                        x: 175
                        y: 300
                        state: "weights"
                        limitToTwoDecimalPlaces: true   // Don't allow more than two decimal places for weight.
                        enable_audio: ObserverSettings.enableAudio

                        onNumpadok: {


                            // If nothing is selected, do nothing
                            if (tvBaskets.currentRow == -1 ||
                                    (!gridDR.is_dr_set() && !appstate.catches.species.isRetained && !is_mix))  // FIELD-2028
                                return;

                            // If zero, do nothing
                            if ( stored_result === "0") {
                                console.log("Zero value- ignoring basket OK button click.");
                                return;
                            }
                            NBSM.handleNewBasketEvent(NBSM.NEW_BASKET_EVENT.OK, btnEditBasket.checked);

                            // If something's selected, set its value accordingly.
                            var basket_id = modeSC.getBasketIdForCurrentRow();

                            if (basket_id > 0) {
                                if (btnManualWeight.checked) {
                                    if (stored_result > 0.0) {
                                        numpadEnteredWeight(basket_id, stored_result);
                                    }

                                } else {
                                    numpadEnteredCount(basket_id, stored_result);
                                }
                            }

                        }

                        onClearnumpad: {
                            // Added operation for CLR key iff:
                            // 1. Entering a new basket (not editing an existing)
                            // 2. Entering a weight (not a count)
                            // 3. At least one digit has been entered (so a null basket has been entered).
                            if (NBSM.isEnteringNewBasketWeight() &&
                                    tvBaskets.currentRow == 0) {
                                console.debug("CLR btn while entering weight for new basket: new basket row removed.");
                                tvBaskets.removeCurrentBasket();
                                modeSC.reset();
                            }
                        }

                        function clearAndSelect() {
                            numPad.clearnumpad();
                            // Focus on the numPad's output textbox and select the "0" cleared amount.
                            numPad.selectAll();
                        }

                        function numpadEnteredWeight(basket_id, value) {
                            if (basketWeightIsTooHigh(value)) {
                                // Throw up error dialog box
                                dlgBasketWeightTooHeavy.invalidWeight = value;
                                dlgBasketWeightTooHeavy.weightMax = appstate.trawlMaxBasketWeightLbs;
                                dlgBasketWeightTooHeavy.open();
                                numPad.clearAndSelect();
                            } else if (basketWeightNeedsConfirmation(value)) {
                                console.debug("Weight of " + value + " requires confirmation dialog.");
                                confirmAddHeavyBasket.show("add this heavy basket", "add_heavy_basket")
                            } else if (!decimalPortionOfWeightIsOK(value)) {
                                // FIELD-1423: Require that decimal portion of weight ends in .x0 or .x5
                                console.debug("Decimal digits of weight " + value +
                                        " don't end in .x0 or .x5.");
                                dlgBasketWeightBadDecimalDigits.invalidWeight = value;
                                dlgBasketWeightBadDecimalDigits.open();
                            } else {
                                // Typical - no error, no confirmation needed
                                if (value === 0)
                                    value = null;
                                modeSC.addBasketWeight(basket_id, value);
                                console.debug("Weight is OK without need for confirmation: '",
                                    value, "'.");
                            }
                        }

                        function numpadEnteredCount(basket_id, value) {
                            console.debug("numPad Entered Count")
                            dlgCounts.validate(basket_id, value)
                        }
                        ProtocolWarningDialog {
                            // dlg wrapper for count value validations
                            id: dlgCounts
                            btnAckText: "Yes, count is correct"
                            btnOKText: "No, return to entry"
                            property int _count
                            property int _basket

                            function save() {
                            // reusable save func
                                if (_basket) {
                                    modeSC.editBasketCount(_basket, _count)
                                    warnIfAvgWeightShowsAsZero();
                                    modeSC.reset()
                                } else {
                                    console.debug("Basket id not set, unable to save count")
                                }
                            }
                            function validate(basket_id, value) {
                            // place to customize validations for yes/no dialogs
                                _count = value
                                _basket = basket_id
                                // validations go here: open() and return for custom validations
                                if (_count > 250) {  // FIELD-1224
                                    dlgCounts.message = "Warning! Count is greater than expected.\nIs this count correct?"
                                    dlgCounts.open()
                                    return
                                } else {
                                    dlgCounts.save()
                                }
                            }
                            onAccepted: { // select numpad txt field and set to 0
                                numPad.clearAndSelect()
                            }
                            onRejected: { // save basket count, reset
                                dlgCounts.save()
                            }
                        }

                        function decimalPortionOfWeightIsOK(weight_string) {
                            // FIELD-1423: Given a string with a float value with two decimal places,
                            // return false if the second decimal digit is not 0 or 5.
                            // TODO: Consider using regular expression. Current implementation
                            // may be clearer, and it's only called on a numpad OK click.
                            console.assert(typeof weight_string === 'string',
                                    "Weight should be of type string.");
                            console.assert(limitToTwoDecimalPlaces,
                                'decimal place checking assuming two decimal digits');

                            var decimalPtIdx = weight_string.indexOf('.');
                            if (decimalPtIdx < 0) {
                                // Weight has no decimal portion.
                                return true;
                            }
                            var decimalDigits = weight_string.substring(decimalPtIdx+1);
                            if (decimalDigits.length < 2) {
                                // Weight has less than two decimal digits. A zero may be implied.
                                return true;
                            }
                            if (decimalDigits.endsWith('0') || decimalDigits.endsWith('5')) {
                                // Last of two decimal digits is either zero or five.
                                return true;
                            }
                            // weight_string has two decimal places and does not end in 0 or 5.
                            return false;
                        }

                        function containsAValue() {
                            return (numPad.textNumPad.text &&
                                    numPad.textNumPad.text.length > 0);
                        }

                        function decimalPointHasBeenEntered() {
                            if (numPad.containsAValue() &&
                                    numPad.textNumPad.text.indexOf(".") > -1) {
                                return true;
                            } else {
                                return false;
                            }
                        }

                        onNumpadinput: {
                            //console.debug("Stored numpad result is '" + numPad.textNumPad.text + "'.");
                            if (!gridDR.is_dr_set() && !appstate.catches.species.isRetained && !is_mix) {  // FIELD-2028
                                dlgSelectDRWarning.open();
                                clearnumpad();
                                return;
                            }

                            if (!appstate.hauls.isCalWeightSpecified) {
                                dlgNoWM.open();
                                clearnumpad();
                                return;
                            }

                            NBSM.handleNewBasketEvent(NBSM.NEW_BASKET_EVENT.DIGIT, btnEditBasket.checked);


                            // Could be handling digit for weight, or for count
                            if (tvBaskets.currentRow == -1) { // Handling first digit for weight
                                // If user starts inputting without row selected, create new basket
                                modeSC.addNewBasket(null, null);
                            }
                        }
                        onNoCountPressed: {
                            var basket_id = modeSC.getBasketIdForCurrentRow();
                            NBSM.handleNewBasketEvent(NBSM.NEW_BASKET_EVENT.NO_COUNT, btnEditBasket.checked);
                            numpadEnteredCount(basket_id, "0");
                            if (ObserverSettings.enableAudio) {
                                soundPlayer.play_sound("noCount", false)
                            }
                        }
                    }
                }
            }
        }
        ColumnLayout {
            x: grpMeasurementType.x + grpMeasurementType.width + 20
            y: 80
            width: tvBaskets.width
            height: 50

            Row {
                 id: dispositionRow
                 anchors.fill: parent                                  
                 Label {
                     id: lblProtocol
                     text: "Protocol:"
                     font.pixelSize: 20
                     height: 40
                     verticalAlignment: Text.AlignVCenter
                }
                ObserverTextField {
                    id: tfProtocol
                    text: appstate.catches.species.currentProtocols +
                          (appstate.catches.species.currentBiolist ?
                               " (" + appstate.catches.species.currentBiolist + ")" : "")
                    font.pixelSize: 20
                    readOnly: true
                    width: buttonDispD.width * 3
                    height: lblDisposition.height
                }
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
                    text: appstate.hauls.currentBiolistNum
                    font.pixelSize: 20
                    height: lblDisposition.height
                    width: 50
                }
            }

            Row {
                topPadding: 10
                leftPadding: 10
                bottomPadding: 5
                Rectangle {
                    id: basketEntryStatusMessage
                    visible: true
                    opacity: 0.0
                    property alias text: lblStatusMessage.text
                    width: 375
                    height: 70
                    color: "#BED838" //light greenish yellow
                    radius: 5

                    Label {
                        id: lblStatusMessage
                        font.pixelSize: 22
                        anchors.left: parent.left
                        anchors.margins: 5
                    }

                    function update(message) {
                        if (message == null || message == "") {
                            text = "";
                            opacity = 0.0
                        } else {
                            text = message;
                            opacity = 1.0
                        }
                    }
                }
            }
        }

        ////
        // Species Comp Baskets: Basket Table and Its TrawlOKDialog
        ////
        ObserverTableView {
            id: tvBaskets
            x: grpMeasurementType.x + grpMeasurementType.width + 20
            y: 190
            width: 400
            height: main.height - 335
            enabled: !isEditingExistingBasket && !NBSM.isEnteringNewBasket()

            model: appstate.catches.species.counts_weights.BasketsModel

            property bool isEditingExistingBasket: false

            selectionMode: SelectionMode.SingleSelection
            headerVisible: true

            function removeCurrentBasket() {
                var del_id = modeSC.getBasketIdForCurrentRow();
                modeSC.removeBasket(del_id);
            }

            TableViewColumn {
                title: "#"
                width: 50
                delegate: Text {
                    text: tvBaskets.model.count - styleData.row
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            }
            TableViewColumn {
                role: "basket_weight_itq"
                title: "Lb"
                width: 100
                delegate: Text {
                    text: styleData.value !== undefined && (typeof styleData.value == 'number') ? styleData.value.toFixed(dec_places) : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            }
            TableViewColumn {
                role: "fish_number_itq"
                title: "Count"
                visible: screenCW.speciesIsCounted()
                width: 100
                delegate: Text {
                    text: styleData.value === "0" ? "X" : (styleData.value ? styleData.value : "")
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            }
            TableViewColumn {
                role: "extrapolated_number"
                title: "E-Count"
                visible: screenCW.speciesIsCounted()
                width: 110
                delegate: Text {
                    text: styleData.value ? styleData.value.toFixed(dec_places) : ""
                    font.pixelSize: 20
                    font.italic: true
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
            }


            onClicked: {
                if (!btnEditBasket.checked) {
                    tvBaskets.selection.clear();
                    currentRow = -1;
                }
            }

            onDoubleClicked: {
                // FIELD-1788 do not allow double click
                tvBaskets.selection.clear();
                currentRow = -1;
            }

            onCurrentRowChanged: {
                // console.debug("currentRow='" + currentRow + "'.");
                if (currentRow != -1 && currentRow < model.count) {
                    // Either: (1) a row was clicked: -> go into edit mode of existing basket
                    // or (2) a new row was created by clicking digit in numpad (new basket).
                    btnManualWeight.checked = true;
                    var curval = model.get(currentRow).basket_weight_itq;
                    if (btnEditBasket.checked && curval) {
                        numPad.setnumpadvalue(curval.toFixed(dec_places));
                        numPad.selectAll();
                    }
                    if (NBSM.isEnteringNewBasket()) {
                        btnEditBasket.checked = false;
                        btnManualCount.enabled = false; // Require OK'd weight before moving to count
                        basketEntryStatusMessage.update(NBSM.msgNBWIP);
                    } else if (btnEditBasket.checked) {
                        btnManualCount.enabled = true;
                        basketEntryStatusMessage.update(NBSM.msgStartEditingExistingBasket);
                    }
                }
            }

            TrawlOkayDialog {
                id: dlgProtocolRequested
                title: "Sample " + req_type

                property string req_type: "requested/required"
                function prompt_if_bio_needed() {

                    var current_biolist_num = appstate.hauls.currentBiolistNum;
                    var biolist_name = appstate.catches.species.currentBiolist;
                    var current_species_biolist_num = biolist_name ? parseInt(biolist_name.charAt(biolist_name.length - 1)) : null;
                    var matching_bios = current_species_biolist_num &&
                            (current_species_biolist_num === current_biolist_num);

                    if (appstate.catches.species.currentProtocols === '-') {
                        return;
                    } else if (current_species_biolist_num && !matching_bios) {
                        console.log("Species Biolist: " + biolist_name + " doesn't match " +
                                     current_biolist_num +", not requiring biospecimens.")
                        return;
                    } else {
                        var bs_model = appstate.catches.biospecimens.BiospecimenItemsModel;
                        if (!bs_model || bs_model.count === 0 ) {
                            message = "NOTE: Sample " + req_type + " for this species : \n" +
                                    appstate.catches.species.currentProtocols + "\nGo to BIOSPECIMENS tab, if required."
                            open();
                        }
                    }
                }

                Connections {
                    target: tabView
                    onCurrentIndexChanged : {
                        if (screenCW.stateCW && currentIndex < 2) {
                            // CW and Biospecimens are index 2 and 3
                            dlgProtocolRequested.prompt_if_bio_needed();
                        }
                        screenCW.stateCW = (currentIndex == 2) ? true : false;
                    }

                }

                Connections {
                    target: obsSM
                    onEnteringCW: {
                        screenCW.stateCW = true;
                    }
                }
            }
        }

        ////
        // Species Comp Baskets: Basket Weight and Edit Controls
        ////
        GridLayout {  // Species Controls for Baskets
            x: tvBaskets.x + tvBaskets.width + 10
            y: tvBaskets.y
            width: 100

            rowSpacing: 20
            columnSpacing: 20
            Layout.alignment: Qt.AlignHCenter

            ColumnLayout {
                id: colWeightInfo
                Layout.column: 0
                Layout.alignment: Qt.AlignHCenter

                property int widthTF: 100
                property int fontsize: 18

                Label {
                    // Set on counts weights model change
                    id: lblMultiplier
                    text: "WM 15 Multiplier: " + (1 / appstate.catches.species.counts_weights.wm15Ratio).toFixed(dec_places)
                    visible: appstate.catches.weightMethod === "15"
                    font.pixelSize: 15
                    Layout.alignment: Qt.AlignHCenter
                }
                Label {
                    id: lblExpandedWeight
                    text: "Expanded Weight"
                    visible: tfExpandedWeight.visible
                    font.pixelSize: colWeightInfo.fontsize
                    Layout.alignment: Qt.AlignHCenter
                }
                ObserverTextField {
                    id: tfExpandedWeight
                    text: appstate.catches.species.counts_weights.extrapolatedSpeciesWeight ?
                              appstate.catches.species.counts_weights.extrapolatedSpeciesWeight.toFixed(dec_places) : ""
                    visible: appstate.catches.weightMethod === "8" ||
                             appstate.catches.weightMethod === "15"
                    Layout.preferredWidth: colWeightInfo.widthTF
                    font.pixelSize: colWeightInfo.fontsize
                    readOnly: true
                    Layout.alignment: Qt.AlignHCenter
                    horizontalAlignment: TextInput.AlignRight
                }
                Label {
                    // spacer
                }
                Label {
                    id: lblActualWeight
                    text: "Total Basket Weights"
                    font.pixelSize: colWeightInfo.fontsize
                    visible: tfActualWeight.visible
                    Layout.alignment: Qt.AlignHCenter
                }
                ObserverTextField {
                    id: tfActualWeight
                    text: appstate.catches.species.counts_weights.actualWeight ?
                              appstate.catches.species.counts_weights.actualWeight.toFixed(dec_places) : ""
                    Layout.preferredWidth: colWeightInfo.widthTF
                    font.pixelSize: colWeightInfo.fontsize
                    readOnly: true
                    Layout.alignment: Qt.AlignHCenter
                    horizontalAlignment: TextInput.AlignRight
                }
                Label {
                    // spacer
                }

                Label {
                    id: lblAvgWeight
                    text: "Average Fish Weight"
                    visible: screenCW.speciesIsCounted()
                    font.pixelSize: colWeightInfo.fontsize
                    Layout.alignment: Qt.AlignHCenter
                }
                ObserverTextField {
                    id: tfAvgWeight
                    text: appstate.catches.species.counts_weights.avgWeight ?
                              appstate.catches.species.counts_weights.avgWeight.toFixed(dec_places) : ""
                    visible: screenCW.speciesIsCounted()
                    Layout.preferredWidth: colWeightInfo.widthTF
                    font.pixelSize: colWeightInfo.fontsize
                    readOnly: true
                    Layout.alignment: Qt.AlignHCenter
                    horizontalAlignment: TextInput.AlignRight
                }
                Label {
                    // spacer
                }
                Label {
                    id: lblTotalExCount
                    text: "Total + Extrapolated Count"
                    visible: screenCW.speciesIsCounted()
                    font.pixelSize: colWeightInfo.fontsize
                    Layout.alignment: Qt.AlignHCenter
                }
                ObserverTextField {
                    id: tfExCount
                    text: appstate.catches.species.counts_weights.speciesFishCount ?
                              appstate.catches.species.counts_weights.speciesFishCount : ""
                    visible: screenCW.speciesIsCounted()
                    Layout.preferredWidth: colWeightInfo.widthTF
                    font.pixelSize: colWeightInfo.fontsize
                    readOnly: true
                    Layout.alignment: Qt.AlignHCenter
                    horizontalAlignment: TextInput.AlignRight
                }
                Label {
                    // spacer
                }
                ObserverSunlightButton {
                    id: btnEditBasket
                    text: "Edit Basket"
                    Layout.preferredWidth: 150
                    Layout.alignment: Qt.AlignHCenter
                    checkable: true
                    checked: tvBaskets.isEditingExistingBasket

                    onClicked: {
                        if (!checked) {
                            // User has de-selected edit. Return to default state, ready for new basket entry.
                            modeSC.reset();
                        } else {
                            if (tvBaskets.currentRow != -1 && tvBaskets.rowCount > 0) {
                                tvBaskets.isEditingExistingBasket = true;
                                basketEntryStatusMessage.update(NBSM.msgStartEditingExistingBasket);
                            } else {
                                basketEntryStatusMessage.update(NBSM.msgEditClickedWithoutBasketSelected);
                            }
                        }
                    }
                }
                ObserverSunlightButton {
                    id: btnDeleteBasket
                    text: "Delete Basket"
                    Layout.preferredWidth: 150
                    Layout.alignment: Qt.AlignHCenter
                    visible: false  // Until btnEditBasket checked

                    // Only show button if Edit Basket button is checked.
                    Connections {
                        target: btnEditBasket
                        onCheckedChanged: {
                            console.debug("btnEditBasket.checked now = " + btnEditBasket.checked);
                            btnDeleteBasket.visible = btnEditBasket.checked;
                        }
                    }
                    onClicked: {
                        if (tvBaskets.currentRow != -1 && tvBaskets.rowCount > 0) {
                            confirmRemoveBasket.show("remove this basket", "remove_basket")
                        }
                    }
                }
            }


            ColumnLayout {
                id: colTally
                Layout.column: 1
                spacing: 20
                Layout.alignment: Qt.AlignHCenter
                property int fontsize: 18

                property int tallyCount: 0

                visible: appstate.catches.weightMethod === "8" ||
                         appstate.catches.weightMethod === "19"


                FramButton {
                    id: bTallyPlus
                    text: "Tally +"
                    fontsize: colTally.fontsize
                    onClicked: {
                        colTally.tallyCount++;
                    }
                }
                FramButton {
                    id: bTallyMinus
                    text: "Tally -"
                    fontsize: colTally.fontsize
                    onClicked: {
                        if (colTally.tallyCount > 0)
                            colTally.tallyCount--;
                    }
                }
                FramLabel {
                    text: "Current Tally:"
                    font.pixelSize: colTally.fontsize
                    Layout.alignment: Qt.AlignHCenter
                }
                ObserverTextField {
                    Layout.alignment: Qt.AlignHCenter
                    id: tfCurrentTally
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 60
                    text: colTally.tallyCount
                    font.pixelSize: 25
                    readOnly: true
                }
                FramButton {
                    id: bAddTally
                    text: "Add Tally\n to Sample"
                    Layout.preferredHeight: 100
                    fontsize: colTally.fontsize
                    enabled: parseInt(tfCurrentTally.text) > 0
                    onClicked: {
                        if (colTally.tallyCount > 0) {
                            modeSC.addTallyBasket(colTally.tallyCount)
                            colTally.tallyCount = 0;
                        }
                    }
                }

            } // Column Tally

        } // GridLayout
    } // Species Basket Item

    ////
    // Species Comp Baskets: Pop-up Dialogs.
    // Kept out of Species Basket Item (ended just above) because pop-up was partially off-screen.
    ////
    FramNoteDialog {
        id: dlgSelectDRWarning
        message: "Select a discard reason\nprior to adding baskets."
        font_size: 18
    }

    FramNoteDialog {
        id: dlgNoWM
        message: "Weight calibration value\nmust be specified before\n adding baskets. Set this value\n in Catch Category Details."
        font_size: 18
    }

    FramNoteDialog {
        id: dlgDiscardReasonUsed
        property string discardReason
        property string commonName
        message: "Error:" +
            "\nSpecies '" + commonName + "'" +
            "\nis already in Selected Species list " +
            "\nwith discard reason " + discardReason + "."
    }

    FramNoteDialog {
        id: dlgCannotChangeDiscardReasonIfBiospecimens
        message: "Can't change discard reason\nbecause this species comp item\nhas Biospecimen data.\n" +
                "Either delete Biospecimen data\nor add new Species entry."
        font_size: 18
    }

    FramConfirmDialog {
        id: confirmAddHeavyBasket
        visible: false
        anchors.horizontalCenterOffset: -1 * parent.width/3
        anchors.verticalCenterOffset: -1 * parent.height/5

        onConfirmed: {
            var basket_id = modeSC.getBasketIdForCurrentRow();
            var weight = numPad.stored_result;
            modeSC.addBasketWeight(basket_id, weight);
            NBSM.handleNewBasketEvent(NBSM.NEW_BASKET_EVENT.OK, btnEditBasket.checked);
            console.debug("Weight of " + weight + " lbs added after confirmation.");
        }
        onCancelled: {
            var weight = numPad.stored_result;
            console.debug("Weight of " + weight + " lbs abandoned after confirmation canceled.");
            numPad.clearAndSelect();
        }
    }

    FramConfirmDialog {
        id: confirmRemoveBasket
        visible: false
        anchors.horizontalCenterOffset: -1 * parent.width/3
        anchors.verticalCenterOffset: -1 * parent.height/5

        onConfirmedFunc: {
            if (action_name == "remove_basket") {
                tvBaskets.removeCurrentBasket();
                modeSC.reset();
                warnIfAvgWeightShowsAsZero();
            } else if (action_name == "merge_baskets") {
                // TODO{wsmith} Merge Baskets functionality FIELD-437
            }
        }
    }

    ProtocolWarningDialog {
        id: dlgWarnDRChange
        message: "You are about to change the\ndiscard reason associated with\nthis species and its biosamples."
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

            // FIELD-1779 Allow change if other DR isn't already in place
            if (gridDR.is_dr_available(pendingDR)) {
                gridDR.current_discard_id = pendingDR;
                gridDR.set_discard_desc();
            } else {
              console.error("Double checked but DR is not available. Not setting to " + pendingDR);
            }
        }
        onAccepted: {
            rptDRButtons.restoreCheckedButton();
        }
    }
}
