import QtQuick 2.6
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0

import "../common"
import "."

Item {
    id: catchCatsBaskets

    ////
    // Properties, Functions and Pop-up Dialogs
    ////

    function page_state_id() { // for transitions
        return "cc_baskets_state";
    }

    Component.onCompleted: {
        var ccCode = appstate.catches.currentCatchCatCode(); //appstate.catches.currentCatch.catch_category.catch_category_code;
        console.debug("Updating WM3 catch weight calculation for CC Code " +  ccCode);

        init_ui();
    }

    function init_ui() {
        // Reload the view model of weighed baskets
        appstate.catches.catchBaskets.buildCatchBasketsViewModel();

        // Unweighed baskets are not included in model for table view of weighed baskets,
        // so just go to database to get the count of unweighed baskets.
        rowWM3Tally.tallyCount = appstate.catches.catchBaskets.countOfUnweighedCatchAdditionalBaskets;

        // Calculate and display on-entry Weight Method 3 estimate of catch weight.
        colWM3Calculation.recalculate();
    }

    Component.onDestruction: {
        // Ensure if we leave this screen that other screens with forward nav still work
        framHeader.forwardEnable(true);
    }

    property int dec_places: appstate.displayDecimalPlaces  // Number of decimal places to display weight values

    function basketWeightIsTooHigh(weight) {
        // Maximum trawling basket weight is specified in the SETTINGS table of Observer.db
        return (weight > appstate.trawlMaxBasketWeightLbs);
    }

    function basketWeightNeedsConfirmation(weight) {
        // Trawling basket weight requiring confirmation is specified in the SETTINGS table of Observer.db
        return (weight > appstate.trawlConfirmBasketWeightLbs);
    }

    FramNoteDialog {
        id: dlgBasketWeightTooHeavy
        property string invalidWeight
        property string weightMax
        message: "Weight of basket (" + invalidWeight + " lbs)\n" +
                " exceeds " + weightMax + " lbs."
        font_size: 18
    }

    Item {
        id: modeWM3

        ////////////////////////////
        // WEIGHT METHOD 3 BASKETS
        ////////////////////////////

        ////
        // WM3 Baskets: Properties and Functions
        ////
        function addWeighedFullBasket(weight) {
            console.log("wt " +  weight)
            appstate.catches.catchBaskets.addAdditionalWeighedFullBasket(parseFloat(weight))
        }

        Connections {
            target: appstate.catches.catchBaskets
            onAdditionalWeighedBasketAdded: {
                // console.debug("Weighed basket added with empty weight");
                modeWM3.selectNewestZeroWeightRow();
            }
        }

        function setBasketWeight(basket_id, weight) {
            appstate.catches.catchBaskets.setAdditionalBasketWeight(basket_id, weight);
        }

        function removeBasket(basket_id) {
            appstate.catches.catchBaskets.removeAdditionalBasket(basket_id);
            reset();
        }

        function reset() {
            tvWM3Baskets.isEditingBasket = false;
            tvWM3Baskets.currentRow = -1;
            tvWM3Baskets.selection.clear();
            btnWM3ManualWeight.checked = true;
            numPadWM3.setSkipButtonMode(false);
            numPadWM3.clearnumpad();
            btnWM3EditBasket.checked = tvWM3Baskets.isEditingBasket;
        }

        function selectNewestRow() {
            if (tvWM3Baskets.model.count > 0) {
                tvWM3Baskets.selection.clear();
                tvWM3Baskets.currentRow = 0;
                tvWM3Baskets.selection.select(0);  // Topmost Basket = newest

                // Unweighed baskets should not be shown in model
                if (!tvWM3Baskets.model.get(0).basket_weight) {
                    // If no weight set, then deselect - this is a tally basket
                    tvBaskets.currentRow = -1;
                    tvBaskets.selection.clear();
                    console.error("Unweighed baskets should not be shown in view model.");
                }
            }
        }

        function selectNewestZeroWeightRow() {
            // console.debug("#weighed baskets=" + tvWM3Baskets.model.count + ", currentRow=" +
            //        tvWM3Baskets.currentRow);
            if (tvWM3Baskets.model.count > 0) {
                tvWM3Baskets.currentRow = -1;
                tvWM3Baskets.selection.clear();
                var is_empty = tvWM3Baskets.model.get(0).basket_weight == 0.0;
                if (is_empty) {
                    tvWM3Baskets.currentRow = 0;
                    tvWM3Baskets.selection.select(0);
                }
            }
        }

        function removeNewestRowIfZeroWeight() {  // Use after heavy-ish basket is canceled or too-heavy dialog.
            if (tvWM3Baskets.model.count > 0) {
                var basket_weight = tvWM3Baskets.model.get(0).basket_weight;
                console.debug("Newest's row weight=" + basket_weight);
                if (basket_weight == 0.0) {
                    var basket_id = tvWM3Baskets.model.get(0).catch_addtl_baskets;
                    modeWM3.removeBasket(basket_id);
                    console.debug("Empty basket weight removed.");
                }
            }
        }

        function getBasketIdForCurrentRow() {
            return tvWM3Baskets.model.get(tvWM3Baskets.currentRow).catch_addtl_baskets;
        }

        GridLayout {
            id: grdWM3
            columns: 3
            columnSpacing: 20
            Column {
                id: colWM3Numpad
                topPadding: 28
                ////
                // WM3 Baskets: CW Numpad Column
                ////
                ObserverGroupBox {
                    id: grpWM3MeasurementType
                    x: 5
                    y: 15
                    width: 400
                    height: 552
                    title: "WM3 Basket Weight Entry"
                    ExclusiveGroup {
                        id: egWM3MeasurementType
                    }
                    ColumnLayout {
                        x: 10
                        y: 20
                        spacing: 10
                        Row {
                            id: rwWM3MeasurementTypes
                            spacing: 10
                            width: grpWM3MeasurementType.width
                            ObserverGroupButton {
                                id: btnWM3ScaleWeight
                                text: "Scale\nWeight"
                                exclusiveGroup: egWM3MeasurementType
                                visible: false  // Scale weight not yet implemented.
                            }
                            ObserverGroupButton {
                                id: btnWM3ManualWeight
                                text: "Manual\nWeight"
                                checked: true
                                exclusiveGroup: egWM3MeasurementType
                                onCheckedChanged: {
                                    if (checked) {
                                        if (tvWM3Baskets.currentRow != -1) {
                                            var curRowWeight =
                                                    tvWM3Baskets.model.get(tvWM3Baskets.currentRow).basket_weight;
                                            numPadWM3.setnumpadvalue(curRowWeight);
                                            numPadWM3.selectAll();
                                        }
                                        numPadWM3.show_no_count(false);
                                        numPadWM3.showDecimal(true);
                                    }
                                }
                            }
                            // No Manual Count button for Weight Method 3 - just weight.
                        }
                        Row {
                            FramNumPad {
                                id: numPadWM3
                                x: 175
                                y: 300
                                state: "weights"
                                limitToTwoDecimalPlaces: true   // Don't allow more than two decimal places for weight.
                                enable_audio: ObserverSettings.enableAudio
                                onNumpadok: {
                                    // console.debug("currentRow=" + tvWM3Baskets.currentRow);
                                    // If nothing is selected, do nothing
                                    if (tvWM3Baskets.currentRow == -1)
                                        return;
                                    // If something's selected, set its value accordingly.
                                    var basket_id = modeWM3.getBasketIdForCurrentRow();

                                    if (basket_id > 0) {
                                        if (btnWM3ManualWeight.checked) {
                                            numpadEnteredWeight(basket_id, stored_result);
                                        }
                                    }
                                    // Clear numpad to allow another basket to be entered.
                                    modeWM3.reset();
                                }

                                function clearAndSelect() {
                                    numPadWM3.clearnumpad();
                                    // Focus on the numPadWM3's output textbox and select the "0" cleared amount.
                                    numPadWM3.selectAll();
                                }

                                function numpadEnteredWeight(basket_id, value) {
                                    if (basketWeightIsTooHigh(value)) {
                                        // Throw up error dialog box
                                        dlgBasketWeightTooHeavy.invalidWeight = value;
                                        dlgBasketWeightTooHeavy.weightMax = appstate.trawlMaxBasketWeightLbs;
                                        dlgBasketWeightTooHeavy.open();
                                        modeWM3.removeNewestRowIfZeroWeight();
                                        numPadWM3.clearAndSelect();
                                    } else if (basketWeightNeedsConfirmation(value)) {
                                        console.debug("Weight of " + value + " requires confirmation dialog.");
                                        confirmWM3AddHeavyBasket.basket_id = basket_id;
                                        confirmWM3AddHeavyBasket.show("add this heavy basket", "add_heavy_basket")
                                    } else {
                                        // Typical - no error, no confirmation needed
                                        if (value === 0)
                                            value = null;
                                        modeWM3.setBasketWeight(basket_id, parseFloat(value));
                                        colWM3Calculation.recalculate();
                                        console.debug("Weight is OK without need for confirmation: " + value);
                                    }
                                }

                                onNumpadinput: {
                                    if (tvWM3Baskets.currentRow == -1) {
                                        // If user starts inputting without row selected, create new basket
                                        tvWM3Baskets.isEditingBasket = true;
                                        modeWM3.addWeighedFullBasket(0.0);  // Actual weight value entered on OK.
                                    }
                                }
                            }
                        }
                    }
                }  // GroupBox
            }  // Column: colWM3NumPad

            Column {  // Two rows: Weighed Basket TableView/Controls and Unweighed Basket Tally Group
                id: colDispositionAndBaskets
                spacing: 30


                ////
                // WM3 Baskets: Basket Table and Controls
                ////
                Row {  // Weighed Basket Table and Controls
                    ObserverGroupBox {
                        id: grpWM3WeighedBaskets
                        x: 5
                        y: 12
                        width: tvWM3Baskets.width + grdWM3BasketControls.width + 40
                        height: main.height - 300  // TODO: Subtract height of other rows.
                        title: "WM3 Weighed Baskets"

                        ObserverTableView {
                            id: tvWM3Baskets
                            //x: grpWM3MeasurementType.x + grpWM3MeasurementType.width + 20
                            x: 5
                            y: 25
                            width: 235
                            height: main.height - 335
                            enabled: isEditingBasket

                            model: appstate.catches.catchBaskets.CatchAdditionalBasketsViewModel

                            property bool isEditingBasket: false

                            selectionMode: SelectionMode.SingleSelection
                            headerVisible: true
                            TableViewColumn {
                                title: "#"
                                width: 50
                                delegate: Text {
                                    text: tvWM3Baskets.model.count - styleData.row
                                    font.pixelSize: 20
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                            TableViewColumn {
                                role: "basket_weight"
                                title: "Lb"
                                width: 100
                                delegate: Text {
                                    text: styleData.value ? styleData.value.toFixed(dec_places) : ""
                                    font.pixelSize: 20
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                            TableViewColumn {
                                role: "basket_type"
                                title: "Partial"
                                width: 80
                                delegate: Text {
                                    text: styleData.value == appstate.catches.catchBaskets.CAB_BASKET_TYPE_WEIGHED_PARTIAL ? "Y" : ""
                                    font.pixelSize: 20
                                    verticalAlignment: Text.AlignVCenter
                                    horizontalAlignment: Text.AlignHCenter
                                }
                            }

                            onCurrentRowChanged: {  // handle user clicking on disabled listview
                                if (!tvWM3Baskets.isEditingBasket) {
                                    modeWM3.reset();
                                } else if (currentRow != -1 && currentRow < model.count) {
                                    btnWM3ManualWeight.checked = true;
                                    var curval = model.get(currentRow).basket_weight;
                                    if (curval) {
                                        numPadWM3.setnumpadvalue(curval.toFixed(dec_places));
                                        numPadWM3.selectAll();
                                    }
                                    btnWM3PartialBasket.checked = Boolean(
                                            model.get(currentRow).basket_type ==
                                                    appstate.catches.catchBaskets.CAB_BASKET_TYPE_WEIGHED_PARTIAL);
                                }
                            }
                        }

                        ////
                        // WM3 Baskets: Controls for Basket Weight Editing
                        ////
                        GridLayout {
                            id: grdWM3BasketControls
                            x: tvWM3Baskets.x + tvWM3Baskets.width + 10
                            y: tvWM3Baskets.y
                            width: 100

                            rowSpacing: 20
                            columnSpacing: 20
                            Layout.alignment: Qt.AlignHCenter

                            ColumnLayout {
                                id: colWM3ColWeightInfo
                                Layout.column: 0
                                Layout.alignment: Qt.AlignHCenter

                                property int widthTF: 100
                                property int fontsize: 18

                                ObserverSunlightButton {
                                    id: btnWM3EditBasket
                                    text: "Edit\nBasket"
                                    Layout.preferredWidth: 100
                                    Layout.alignment: Qt.AlignHCenter
                                    checkable: true
                                    checked: tvWM3Baskets.isEditingBasket

                                    onClicked: {
                                        tvWM3Baskets.isEditingBasket = checked;
                                        // Clear numpad if editing stopped
                                        if (!checked) {
                                            modeWM3.reset();
                                        }
                                    }
                                }
                                ObserverSunlightButton {
                                    id: btnWM3DeleteBasket
                                    text: "Delete\nBasket"
                                    Layout.preferredWidth: 100
                                    Layout.alignment: Qt.AlignHCenter
                                    visible: tvWM3Baskets.isEditingBasket

                                    onClicked: {
                                        if (tvWM3Baskets.currentRow != -1 && tvWM3Baskets.rowCount > 0) {
                                            confirmWM3RemoveBasket.show("remove this basket", "remove_basket")
                                        }
                                    }
                                }
                                ObserverSunlightButton {
                                    id: btnWM3PartialBasket
                                    text: "Partial\nBasket"
                                    Layout.preferredWidth: 100
                                    Layout.alignment: Qt.AlignHCenter
                                    checkable: true
                                    visible: tvWM3Baskets.isEditingBasket

                                    onClicked: {
                                        if (tvWM3Baskets.currentRow != -1 && tvWM3Baskets.rowCount > 0) {
                                            appstate.catches.catchBaskets.setAdditionalWeighedBasketAsPartial(
                                                        modeWM3.getBasketIdForCurrentRow(),
                                                        checked);
                                            colWM3Calculation.recalculate();
                                        } else {
                                            console.debug("Partial Basket button pressed without row being selected.");
                                        }
                                    }
                                }
                            }
                        }
                    }  // GroupBox: Weighed basket table view and edit controls
                }  // Row: Basket TableView and Controls

                ////
                // WM3 Baskets: Unweighed Basket Tally
                ////
                Row {
                    id: rowWM3Tally
                    spacing: 20
                    property int fontsize: 18

                    property int tallyCount: 0

                    visible: true

                    ObserverGroupBox {
                        id: grpWM3UnweighedBasketTally
                        x: 5
                        y: 15
                        width: grpWM3WeighedBaskets.width
                        height: 110
                        title: "WM3 Unweighed Basket Tally"

                        GridLayout {
                            columns: 3
                            columnSpacing: 20
                            y: 20
                            Column {
                                leftPadding: 20
                                TextField {
                                    Layout.alignment: Qt.AlignHCenter
                                    id: tfWM3CurrentTally
                                    font.pixelSize: 30
                                    Layout.preferredWidth: 40
                                    text: rowWM3Tally.tallyCount
                                    width: 55
                                    height: 55
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }

                            Column {
                                leftPadding: 20
                                FramButton {
                                    id: btnWM3TallyPlus
                                    text: "+"
                                    fontsize: 60
                                    width: 80
                                    height: 80
                                    onClicked: {
                                        rowWM3Tally.tallyCount++;
                                        appstate.catches.catchBaskets.addAdditionalUnweighedFullBasket();
                                        colWM3Calculation.recalculate();
                                    }
                                }
                            }
                            Column {
                                leftPadding: 20
                                FramButton {
                                    id: btnWM3TallyMinus
                                    text: "-"
                                    fontsize: 60
                                    width: 80
                                    height: 80
                                    onClicked: {
                                        if (rowWM3Tally.tallyCount > 0) {
                                            rowWM3Tally.tallyCount--;
                                            appstate.catches.catchBaskets.removeAnAdditionalUnweighedFullBasket();
                                            colWM3Calculation.recalculate();
                                        }
                                    }
                                }
                            }
                        }  // GridLayout
                    }  // GroupBox grpWM3Tally
                }  // rowWM3Tally
            }  // Column: Disposition, Weighed Basket TableView/Controls, and Unweighed Basket Tally Group

            Column {
                ////
                // WM3 Baskets: WM3 Catch Weight Calculation
                ////
                id: colWM3Calculation
                x: 5
                y: 15
                topPadding: 20

                // Property aliases to allow recalculate() easy access to text field values in this control:
                property alias averageFullBasketWeight: tfWM3AverageFullBasketWeight.text
                property alias nFullBaskets: tfWM3NFullBaskets.text
                property alias fullBasketTotalWeight: tfWM3FullBasketTotalWeight.text
                property alias partialBasketTotalWeight: tfWM3PartialBasketTotalWeight.text
                property alias catchWeight: tfWM3CatchWeight.text

                function recalculate() {
                    // Pull values from rest of screen and insert into this control.
                    // N.B. Values returned in wm3CatchValues are floats or ints (not text).
                    var wm3CatchValues = appstate.catches.catchBaskets.getWM3CatchValues();

                    // Pull float/int values into local float or int variables.
                    var nUnweighedBaskets = wm3CatchValues["N_UNWEIGHED_BASKETS"];
                    var nWeighedPartialBaskets = wm3CatchValues["N_WEIGHED_PARTIAL_BASKETS"];
                    var nWeighedFullBaskets = wm3CatchValues["N_WEIGHED_FULL_BASKETS"];
                    var weighedFullTotalWeight = wm3CatchValues["WEIGHED_FULL_TOTAL_WEIGHT"];
                    var weighedPartialTotalWeight = wm3CatchValues["WEIGHED_PARTIAL_TOTAL_WEIGHT"];

                    // Write values to UI text fields, with floats rounded to dec_places decimal places.
                    var fltAverageFullBasketWeight = 0.0;
                    if (nWeighedFullBaskets > 0) {
                        fltAverageFullBasketWeight = weighedFullTotalWeight / nWeighedFullBaskets;
                    }
                    averageFullBasketWeight = fltAverageFullBasketWeight.toFixed(dec_places);

                    nFullBaskets = nWeighedFullBaskets + nUnweighedBaskets;
                    var fltFullBasketTotalWeight = (fltAverageFullBasketWeight * nFullBaskets)

                    fullBasketTotalWeight = fltFullBasketTotalWeight.toFixed(dec_places);
                    partialBasketTotalWeight = weighedPartialTotalWeight.toFixed(dec_places);
                    var fltCatchWeight = (fltFullBasketTotalWeight + weighedPartialTotalWeight);
                    catchWeight = fltCatchWeight.toFixed(dec_places);

                    // Call interested party catch categories screen of change in catch weight.
                    // TODO: If more than one interested party, convert to signal emission.
                    appstate.catches.updateWM3TotalCatchWeight(fltCatchWeight);
                }

                // Configuration values - don't recommend changing.
                property int descriptionWidth: 330

                Grid {
                    rows: 5
                    Row {  // Each row: Description, [operator], Value
                        height: 70
                        id: rowWM3AverageFullBasketWeight
                        Label {
                            width: colWM3Calculation.descriptionWidth
                            font.pixelSize: 20
                            text: "Average of weighed full baskets"
                        }
                        Label {
                            width: 20
                            font.pixelSize: 20
                            text: " "
                        }
                        TextField {
                            id: tfWM3AverageFullBasketWeight
                            readOnly: true
                            activeFocusOnPress: false
                            width: 100
                            font.pixelSize: 20
                            horizontalAlignment: TextInput.AlignRight
                        }
                    }
                    Row {
                        height: 70
                        id: rowWM3FullBasketCount
                        Label {
                            width: colWM3Calculation.descriptionWidth
                            font.pixelSize: 20
                            text: "# of full baskets"
                        }
                        Label {
                            width: 20
                            font.pixelSize: 20
                            text: "X"
                        }
                        TextField {
                            id: tfWM3NFullBaskets
                            readOnly: true
                            activeFocusOnPress: false
                            width: 100
                            font.pixelSize: 20
                            horizontalAlignment: TextInput.AlignRight
                        }
                    }
                    Row {  // Each row: Description, [operator], Value
                        height: 70
                        id: rowWM3FullBasketTotalWeight
                        Label {
                            width: colWM3Calculation.descriptionWidth
                            font.pixelSize: 20
                            text: "Full basket total weight"
                        }
                        Label {
                            width: 20
                            font.pixelSize: 20
                            text: "="
                        }
                        TextField {
                            id: tfWM3FullBasketTotalWeight
                            readOnly: true
                            activeFocusOnPress: false
                            width: 100
                            font.pixelSize: 20
                            horizontalAlignment: TextInput.AlignRight
                        }
                    }
                    Row {
                        height: 70
                        id: rowWM3PartialBasketTotalWeight
                        Label {
                            width: colWM3Calculation.descriptionWidth
                            font.pixelSize: 20
                            text: "Partial basket total weight"
                        }
                        Label {
                            width: 20
                            font.pixelSize: 25
                            //verticalAlignment: Text.AlignTop
                            text: "+"
                        }
                        TextField {
                            id: tfWM3PartialBasketTotalWeight
                            readOnly: true
                            activeFocusOnPress: false
                            width: 100
                            font.pixelSize: 20
                            horizontalAlignment: TextInput.AlignRight
                        }
                    }
                    Row {  // Each row: Description, [operator], Value
                        height: 70
                        id: rowWM3CatchTotalWeight
                        Label {
                            width: colWM3Calculation.descriptionWidth
                            font.pixelSize: 20
                            text: "WM3 Total Catch Weight"
                        }
                        Label {
                            width: 20
                            font.pixelSize: 20
                            text: "="
                        }
                        TextField {
                            id: tfWM3CatchWeight
                            readOnly: true
                            activeFocusOnPress: false
                            width: 100
                            font.pixelSize: 20
                            horizontalAlignment: TextInput.AlignRight
                        }
                    }
                }
            }  // Column colWM3Calculation
        } // GridLayout grdWM3
    } // Item modeWM3

    ////
    // WM3 Baskets: Pop-up Dialogs
    ////
    FramConfirmDialog {
        id: confirmWM3AddHeavyBasket
        visible: false
        anchors.horizontalCenterOffset: -1 * parent.width/3
        anchors.verticalCenterOffset: -1 * parent.height/5

        property int basket_id  // Set this before calling show()

        onConfirmed: {
            //var basket_id = modeWM3.getBasketIdForCurrentRow();
            var weight = numPadWM3.stored_result;
            modeWM3.setBasketWeight(basket_id, parseFloat(weight));
            colWM3Calculation.recalculate();
            console.debug("Weight of " + weight + " lbs added after confirmation.");
        }
        onCancelled: {
            var weight = numPadWM3.stored_result;
            console.debug("Weight of " + weight + " lbs abandoned after confirmation canceled.");
            modeWM3.removeNewestRowIfZeroWeight();
            numPadWM3.clearAndSelect();
        }
    }

    FramConfirmDialog {
        id: confirmWM3RemoveBasket
        visible: false
        anchors.horizontalCenterOffset: -1 * parent.width/3
        anchors.verticalCenterOffset: -1 * parent.height/5

        onConfirmedFunc: {
            if (action_name == "remove_basket") {
                var del_id = modeWM3.getBasketIdForCurrentRow();
                modeWM3.removeBasket(del_id);
                colWM3Calculation.recalculate();
                modeWM3.reset();
            } else if (action_name == "merge_baskets") {
                // TODO{wsmith} Merge Baskets functionality FIELD-437
            }
        }
    }
}
