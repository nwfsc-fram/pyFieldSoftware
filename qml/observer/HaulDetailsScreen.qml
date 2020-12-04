import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Controls.Styles 1.4

import "../common"
import "."
import "codebehind/HelperFunctions.js" as HelperFunctions

Item {
    id: detailsPageItem

    function page_state_id() { // for transitions
        return "haul_details_state";
    }

    // Delay may be needed before selecting a row after the locations table is updated.
    // (Workaround from Will Smith)
    Timer {
        id: timer
    }

    function delay(delayTime, callback) {
        timer.interval = delayTime.repeat = false;
        timer.triggered.connect(callback);
        timer.start();
    }

    width: parent.width
    height: parent.height - framFooter.height
    signal resetfocus
    onResetfocus: {
        // "Clear" active focus by setting to a label
        // vesselLabel.forceActiveFocus();
    }


    Keys.forwardTo: [framNumPadDetails, slidingKeyboard] // Required for capture of Enter key

    property bool haulDetailsComplete: true
    onHaulDetailsCompleteChanged: {
        framHeader.forwardEnable(haulDetailsComplete);
    }

    property string noScaleText: "-1"; // Stored in DB instead of cal value

    function updateLabelHighlightingOfRequiredFields() {
        // Update highlighting - normal font if specified, bold/underlined if not
        // All these labels should be of type FramLabelHighlightCapable
        labelVisualOTC.highlight(!appstate.hauls.requiredHaulFieldIsSpecified("observer_total_catch"));
        labelBRD.highlight(!appstate.hauls.requiredHaulFieldIsSpecified("brd_present"));
        labelOTCWeight.highlight(!appstate.hauls.requiredHaulFieldIsSpecified("otc_weight_method"));
        // labelWeightCal.highlight(!appstate.hauls.requiredHaulFieldIsSpecified("cal_weight"));
        labelGearType.highlight(!appstate.hauls.requiredHaulFieldIsSpecified("gear_type"));
        labelGearPerf.highlight(!appstate.hauls.requiredHaulFieldIsSpecified("gear_performance"));
        labelBeaufortScale.highlight(!appstate.hauls.requiredHaulFieldIsSpecified("beaufort_value"));
    }

    function checkRequiredFieldsAreSpecified() {
        // Allow navigation to Catch screen if all required fields are specified.
        var newDetailsComplete = appstate.hauls.requiredHaulFieldsAreSpecified;
        if (newDetailsComplete != detailsPageItem.haulDetailsComplete) {
            console.info("Change in property haulDetailsComplete from " + detailsPageItem.haulDetailsComplete + " to " +
                newDetailsComplete);
            detailsPageItem.haulDetailsComplete = newDetailsComplete;
        }
        updateLabelHighlightingOfRequiredFields();
    }

    function initUI() {
        // console.debug("initUI");
        slidingKeyboard.showbottomkeyboard(false);
        keyboardMandatory.showbottomkeyboard(false);
        var cal_weight = appstate.hauls.getData('cal_weight');
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

    Component.onCompleted: {
        initUI();
        checkRequiredFieldsAreSpecified();
    }

    Component.onDestruction: {
        // Ensure if we leave this screen that other screens with forward nav still work
        framHeader.forwardEnable(true);
    }

    Connections {
        target: observerFooterRow
        onClickedDone: {
            // Logbook
        }
    }

    GridLayout
    {
        id: gridHaulDetails
        anchors.fill: parent
        columns: 2
        anchors.leftMargin: 50
        anchors.rightMargin: 50
        anchors.topMargin: 0
        anchors.bottomMargin: 50
        property int textFieldHeight: 80

        property int labelColWidth: 230
        property int dataColWidth: Math.min( 400, root.width/2 - 50) // limit width

            RowLayout {
                FramLabelHighlightCapable {
                    id: labelVisualOTC
                    text: qsTr("Visual OTC")
                    Layout.preferredWidth: gridHaulDetails.labelColWidth
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25

                    // DEVELOPMENT ONLY - DISABLED IN PRODUCTION
                    // PURPOSE: Provide an obscure way to force an unhandled exception,
                    //      so that unhandled exception handler can be tested.
                    // ACTION: raise an exception if the mouse is clicked ten times in a row without leaving label area.
                    property int clickCount : 0
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true // So onExited is triggered on leaving area, with or without mouse click.
                        property alias clickCount: labelVisualOTC.clickCount
                        property int clicksRequiredToRaiseException: 10
                        onClicked: {
                            if (appstate.isTestMode) {
                                clickCount += 1;
                                console.debug("Click count = " + clickCount + ".");
                                if (clickCount >= clicksRequiredToRaiseException) {
                                    console.warn("User clicked Haul Details's Visual OTC " + clicksRequiredToRaiseException +
                                            " times in a row without moving mouse out of label. Raising Exception.");
                                    appstate.raiseException();
                                }
                            }
                        }
                        onExited: {
                            if (appstate.isTestMode) {
                                console.debug("Mouse left Visual OTC label area.");
                                if (clickCount > 0) {
                                    console.debug("Click count reset to 0");
                                    clickCount = 0;
                                }
                            }
                        }
                    }
                }
                TextField {
                    id: tfVisualOTC
                    Layout.preferredWidth: gridHaulDetails.dataColWidth
                    Layout.preferredHeight: ObserverSettings.default_tf_height
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25
                    placeholderText: labelVisualOTC.text
                    text: appstate.hauls.getData('observer_total_catch')
                    onActiveFocusChanged: {
                        if (focus) {
                            initUI();
                            focus = false;  // otherwise, dialogs opened forever
                            numpadOTC.open()
                        }
                    }
                    onTextChanged: {
                        appstate.hauls.setData('observer_total_catch', text)
                        checkRequiredFieldsAreSpecified();
                    }
                }
                ObserverNumPadDialog {
                    id: numpadOTC
                    max_digits: 6
                    placeholderText: tfVisualOTC.placeholderText
                    enable_audio: ObserverSettings.enableAudio
                    onValueAccepted: {
                        tfVisualOTC.text = accepted_value;
                    }

                }
            }
            RowLayout {
                FramLabelHighlightCapable {
                    id: labelOTCWeight
                    text: qsTr("OTC Weight Method")
                    Layout.preferredWidth: gridHaulDetails.labelColWidth
                    Layout.fillHeight: true

                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignRight
                    font.pixelSize: 25
                    // DEVELOPMENT ONLY - REMOVE OR DISABLE IN PRODUCTION
                    // PURPOSE: Provide an obscure way to force displaying the UnusualCondition dialog
                    //      so that its display can be tested.
                    // ACTION: Display ObserverUnusualConditionDialog if the mouse is clicked ten times
                    //      in a row without leaving label area.
                    property int clickCount : 0
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true // So onExited is triggered on leaving area, with or without mouse click.
                        property alias clickCount: labelOTCWeight.clickCount
                        property int clicksRequiredToDisplayUnusualDialog: 10
                        onClicked: {
                            clickCount += 1;
                            console.debug("Click count = " + clickCount + ".");
                            if (clickCount >= clicksRequiredToDisplayUnusualDialog) {
                                console.warn("User clicked Haul Details's OTC Weight Method " +
                                        clicksRequiredToDisplayUnusualDialog +
                                        " times in a row without moving mouse out of label. Showing Dialog.");
                                //console.trace();

                                var msg = "Test of Unusual Condition Dialog";
                                var parent = detailsPageItem;
                                HelperFunctions.openUnusualConditionDialog(msg, parent);
                            }
                        }
                        onExited: {
                            console.debug("Mouse left OTC Weight Method label area.");
                            if (clickCount > 0) {
                                console.debug("Click count reset to 0");
                                clickCount = 0;
                            }
                        }
                    }
                }
                RowLayout {
                    id: rowOTCMethod
                    ExclusiveGroup {
                        id: groupOTCWeight
                    }

                    property var current_wm: choose_initial_wm()

                    function choose_initial_wm() {
                        var db_val = appstate.hauls.getData('otc_weight_method');
                        if (db_val)
                            return db_val;
                        else
                            appstate.hauls.setData('otc_weight_method', "14");
                            return "14"; // Default OTC WM
                    }

                    Repeater {
                        model: ["14", "6"]
                        ObserverGroupButton {
                            Layout.preferredWidth: 50
                            Layout.preferredHeight: 50
                            exclusiveGroup: groupOTCWeight
                            text: modelData
                            checked: modelData === rowOTCMethod.current_wm ? true: false
                            onClicked: {
                                initUI();
                                rowOTCMethod.current_wm = modelData;
                                appstate.hauls.setData('otc_weight_method', modelData);
                                checkRequiredFieldsAreSpecified();
                                if (modelData === "6") {
                                    dlgWM6Comment.open()
                                }
                            }
                        }
                    }
                    FramNoteDialog {
                        id: dlgWM6Comment
                        message: "Note: Comment is required\nfor OTC WM 6."
                        font_size: 18
                    }
                }
            }
            RowLayout {
                Layout.columnSpan: 2
                Label {
                    text: qsTr("Target Strategy")
                    Layout.preferredWidth: gridHaulDetails.labelColWidth
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25

                }
                TextField {
                    id: tfStrategy
                    font.pixelSize: 25
                    placeholderText: "Code"
                    Layout.preferredWidth: 150
                    Layout.preferredHeight: ObserverSettings.default_tf_height
                    text: appstate.hauls.getDataOrHaulDefault('target_strategy') ? appstate.hauls.getDataOrHaulDefault('target_strategy') : ""
                    onActiveFocusChanged: {
                        if (focus) {
                            initUI();
                            autocomplete.suggest("catch_categories");
                            keyboardMandatory.connect_tf(tfStrategy, "Target Strategy Code");
                            keyboardMandatory.addAutoCompleteSuggestions(text); 
                        }
                        keyboardMandatory.showbottomkeyboard(true);
                    }
                    onTextChanged: {
                        if (text !== appstate.hauls.getData('target_strategy')) {
                            appstate.hauls.setData('target_strategy', text);
                            text = appstate.hauls.getData('target_strategy'); // translated
                            checkRequiredFieldsAreSpecified();
                        }
                    }
                }
                FramLabelHighlightCapable {
                    id: labelBRD
                    text: qsTr("BRD Present?")
                    Layout.preferredWidth: gridHaulDetails.labelColWidth
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignRight
                    font.pixelSize: 25

                }
                RowLayout {
                    id: rowBRD
                    ExclusiveGroup {
                        id: groupBRD
                    }
                    function check_present(label) {
                        var present = appstate.hauls.getDataOrHaulDefault('brd_present');
                        if ((label === "Y" && present) || (label === "N" && present === false))
                            return true;
                        else
                            return false;                        
                    }

                    Repeater {
                        model: ["Y", "N"]
                        ObserverGroupButton {
                            Layout.preferredWidth: 50
                            Layout.preferredHeight: 50
                            checked: rowBRD.check_present(modelData)
                            exclusiveGroup: groupBRD
                            text: modelData
                            onClicked: {
                                if (modelData === "Y") {
                                    appstate.hauls.setData('brd_present', true);
                                } else {
                                    appstate.hauls.setData('brd_present', false);
                                }                                
                                checkRequiredFieldsAreSpecified();
                            }
                        }
                    }
                }
                FramLabelHighlightCapable {
                    id: labelEFP
                    text: qsTr("EFP?")
                    Layout.preferredWidth: gridHaulDetails.labelColWidth
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignRight
                    font.pixelSize: 25

                }
                RowLayout {
                    id: rowEFP
                    ExclusiveGroup {
                        id: groupEFP
                    }
                    function check_efp(label) {
                        var efp = appstate.hauls.getDataOrHaulDefault('efp');
                        if ((label === "Y" && efp) || (label === "N" && efp === false))
                            return true;
                        else
                            return false;
                    }

                    Repeater {
                        model: ["Y", "N"]
                        ObserverGroupButton {
                            Layout.preferredWidth: 50
                            Layout.preferredHeight: 50
                            checked: rowEFP.check_efp(modelData)
                            exclusiveGroup: groupEFP
                            text: modelData
                            onClicked: {
                                initUI();
                                if (modelData == "Y") {
                                    appstate.hauls.setData('efp', true);
                                } else {
                                    appstate.hauls.setData('efp', false);
                                }
                                checkRequiredFieldsAreSpecified();
                            }
                        }
                    }
                }
            }
            RowLayout {
                Layout.columnSpan: 2
                RowLayout {
                    Label {
                        id: labelFit
                        text: qsTr("Fit #")
                        Layout.preferredWidth: gridHaulDetails.labelColWidth
                        Layout.fillHeight: true
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25

                    }
                    TextField {
                        id: tfFit
                        Layout.preferredWidth: 100
                        Layout.preferredHeight: ObserverSettings.default_tf_height
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 25
                        placeholderText: labelFit.text
                        text: appstate.hauls.getData('fit')
                        onActiveFocusChanged: {
                            if (focus) {
                                initUI();
                                focus = false;  // otherwise, dialogs opened forever
                                numpadFit.open()
                            }
                        }
                        onTextChanged: {
                            appstate.hauls.setData('fit', text)
                            checkRequiredFieldsAreSpecified();
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
                        text: qsTr("Weight Calib.")
                        Layout.preferredWidth: gridHaulDetails.labelColWidth
                        Layout.fillHeight: true
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignRight
                        font.pixelSize: 25

                    }
                    ExclusiveGroup {
                        id: btnWeightCalGrp
                    }

                    ObserverGroupButton {
                        id: btnWeightCal1100
                        exclusiveGroup: btnWeightCalGrp
                        text: "11.00"
                        Layout.preferredWidth: 80
                        Layout.preferredHeight: ObserverSettings.default_tf_height
                        onClicked: {
                            checkRequiredFieldsAreSpecified();
                        }
                        onCheckedChanged: {
                            if (checked) {
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
                        onClicked: {
                            checkRequiredFieldsAreSpecified();
                        }
                        onCheckedChanged: {
                            if (checked) {
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
                        font_size: 18
                        onClicked: {
                            checkRequiredFieldsAreSpecified();
                        }
                        onCheckedChanged: {
                            if (checked) {
                                var current_cal = appstate.hauls.getData('cal_weight');
                                if (current_cal !== noScaleText) {
                                    framFooter.openComments("Scale Not Used Selected. Enter Reason: ");
                                }
                                appstate.hauls.setData('cal_weight', noScaleText)
                            }
                        }
                    }

                    FramLabelHighlightCapable {
                        id: labelGearType
                        text: qsTr("Gear Type")
                        Layout.preferredWidth: 130
                        Layout.fillHeight: true
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignRight
                        font.pixelSize: 25

                    }
                    TextField {
                        id: textGearType
                        Layout.preferredWidth: 50
                        Layout.preferredHeight: ObserverSettings.default_tf_height
                        font.pixelSize: 25
                        text: appstate.hauls.getDataOrHaulDefault('gear_type') ? appstate.hauls.getDataOrHaulDefault('gear_type') : ""

                        onActiveFocusChanged: {
                            if (focus) {
                                initUI();
                                autocomplete.suggest("trawl_gear_types");
                                keyboardMandatory.connect_tf(textGearType, "Gear Type");
                                keyboardMandatory.addAutoCompleteSuggestions(text);
                                keyboardMandatory.showbottomkeyboard(true);
                            }
                        }
                        onTextChanged: {
                            // Gear Code Convention:
                            // Outside of keyboardMandatory, any leading zero is stripped;
                            // i.e., when stored to db or displayed in other fields - including here.
                            // Inside keyboardMandatory: use a leading zero
                            // (to allow string sort by two digit code with leading zero).
                            if (text !== appstate.hauls.getData('gear_type')) {
                                appstate.hauls.setData('gear_type', text);
                                text = appstate.hauls.getData('gear_type'); // leading zero will be stripped.
                                console.debug("gear type in db = '" + appstate.hauls.getData('gear_type') + "'");
                                console.debug("gear type in Gear Type field = '" + text + "'");
                                checkRequiredFieldsAreSpecified();
                            }
                        }
                    }
                    FramLabel {
                        text: "Biolist"
                        Layout.preferredWidth: 100
                        horizontalAlignment: Text.AlignRight
                    }
                    ObserverTextField {
                        id: bioListText
                        readOnly: true
                        text: appstate.hauls.currentBiolistNum
                        font.pixelSize: 25
                        Layout.preferredHeight: 50
                        Layout.preferredWidth: 50
                    }

                } // nested RowLayout
            }
            RowLayout {
                Layout.columnSpan: 2
                FramLabelHighlightCapable {
                    id: labelGearPerf
                    text: qsTr("Gear Performance")
                    Layout.preferredWidth: gridHaulDetails.labelColWidth
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25

                }
                RowLayout {
                    id: rowGearPerf
                    ExclusiveGroup {
                        id: groupGearPerf
                    }
                    property var current_gearperf: appstate.hauls.getData('gear_performance')
                    Repeater {
                        model: ["1", "2", "3", "4", "5", "6", "7"]
                        ObserverGroupButton {
                            Layout.preferredWidth: 50
                            Layout.preferredHeight: 50
                            exclusiveGroup: groupGearPerf
                            text: modelData
                            checked: modelData === rowGearPerf.current_gearperf
                            onClicked: {
                                initUI();
                                labelGearPerfDesc.setDesc(modelData);
                                appstate.hauls.setData('gear_performance', modelData);
                                rowGearPerf.current_gearperf = modelData;
                                checkRequiredFieldsAreSpecified();
                            }
                        }

                    }
                    Component.onCompleted: {
                        if (current_gearperf)
                            labelGearPerfDesc.setDesc(current_gearperf)
                    }
                }
                Label {
                    id: labelGearPerfDesc
                    Layout.fillWidth: true
                    Layout.preferredHeight: 80
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignLeft
                    font.pixelSize: 20
                    font.italic: true
                    function setDesc(gearperf_val) {
                        text = appstate.hauls.getGearPerfDesc(gearperf_val)
                    }
                }
            }            
            RowLayout {
                Layout.columnSpan: 2
                FramLabelHighlightCapable {
                    id: labelBeaufortScale
                    text: qsTr("Beaufort Scale\nat Gear Set")
                    Layout.preferredWidth: gridHaulDetails.labelColWidth
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25

                }
                RowLayout {
                    id: rowBeauButtons
                    ExclusiveGroup {
                        id: groupBeaufort
                    }
                    property var current_beaufort: appstate.hauls.getData('beaufort_value')
                    Repeater {
                        model: ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "99"]
                        ObserverGroupButton {
                            Layout.preferredWidth: 50
                            Layout.preferredHeight: 50
                            exclusiveGroup: groupBeaufort
                            text: modelData
                            checked: modelData === rowBeauButtons.current_beaufort
                            onClicked: {
                                initUI();
                                labelBeaufortDesc.setDesc(modelData);
                                appstate.hauls.setData('beaufort_value', modelData);
                                rowBeauButtons.current_beaufortodelData;
                                checkRequiredFieldsAreSpecified();
                            }
                        }
                    }
                    Component.onCompleted: {
                        if (current_beaufort)
                            labelBeaufortDesc.setDesc(current_beaufort)
                    }
                }
                Text {
                    id: labelBeaufortDesc
                    Layout.fillWidth: true
                    Layout.preferredHeight: 80
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    font.pixelSize: 18
                    font.italic: true
                    wrapMode: Text.WrapAtWordBoundaryOrAnywhere

                    function setDesc(beaufort_val) {
                        text = appstate.hauls.getBeaufortDesc(beaufort_val)
                    }

                }
            }

            RowLayout {
                Layout.columnSpan: 2
                Label {
                    text: "Locations"
                    Layout.preferredWidth: gridHaulDetails.labelColWidth
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25
                }
                ObserverTableView {
                    id: tvLocations
                    Layout.preferredWidth: 600
                    Layout.fillHeight: true
                    model: appstate.hauls.locations.CurrentFishingLocationsModel
                    // To aid in selecting the active row after adding or editing a location:
                    property int idxLocationLastChanged : -1
		    
                    onClicked: {
                        console.debug("Location table row#" + row + " was clicked (Pos#" +
                                model.get(row).position + ").");
                        initUI();
                        enable_add_and_delete( (row >= 0) );
                    }

                    function get_position_desc(position) {
                        switch(position) {
                        case -1:
                            return "Set";
                        case 0:
                            return "Up";
                        default:
                            return "Loc#" + position;
                        }
                    }

                    function getDecimalMinutesStr(min) {
                        // Follow the OPTECS convention for leading zero and number of decimal places
                        var includeLeadingZero = ObserverSettings.includeLeadingZeroInMinutes;
                        var nDecimalPlaces = ObserverSettings.nDecimalPlacesInMinutes;
                        return CommonUtil.getDecimalMinutesStr(min, includeLeadingZero, nDecimalPlaces);
                    }

                    function format_coord(coord) {
                        var neg_mult = coord < 0 ? -1 : 1;  // maintain negative value
                        if (neg_mult < 0)
                            coord *= -1;
                        var deg_whole = Math.floor(coord);
                        var min_dec = (coord - deg_whole) * 60.0;
                        return neg_mult * deg_whole + " " + getDecimalMinutesStr(min_dec);
                    }

                    function enable_add_and_delete(do_enable) {
                        btnEditLocation.state = do_enable ? "enabled" : "disabled"
                        btnDeleteLocation.state = do_enable ? "enabled" : "disabled"
                    }

                    TableViewColumn {
                        role: "position"
                        title: "Type"
                        width: 70
                        delegate: Text {
                            text: model ? tvLocations.get_position_desc(model.position) : ""
                            font.pixelSize: 20
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                    TableViewColumn {
                        role: "location_date"
                        title: "Date/ Time"
                        width: 180
                        delegate: Text {
                            text: model ? model.location_date : ""
                            font.pixelSize: 20
                            verticalAlignment: Text.AlignVCenter
                        }
                    }

                    TableViewColumn {
                        role: "latitude"
                        title: "Lat"
                        width: 100
                        delegate: Text {
                            text: model ? tvLocations.format_coord(model.latitude) : ""
                            font.pixelSize: 20
                            verticalAlignment: Text.AlignVCenter                            
                        }
                    }
                    TableViewColumn {
                        role: "longitude"
                        title: "Long"
                        width: 100
                        delegate: Text {
                            text: model ? tvLocations.format_coord(model.longitude) : ""
                            font.pixelSize: 20
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                    TableViewColumn {
                        role: "depth"
                        title: "Depth"
                        width: 100
                    }

                    function editGPS(row) {
                        if (row < 0 || row > tvLocations.rowCount) {
                            console.warn("editGPS got bad row, not editing");
                            return;
                        }

                        dlgGPS.sub_title = tvLocations.get_position_desc(model.get(row).position);
                        console.debug("location_date string = '" + model.get(row).location_date + "'");
                        dlgGPS.time_val = ObserverSettings.str_to_local(model.get(row).location_date);
                        dlgGPS.lat_degs = model.get(row).latitude;
                        // Longitude in model must be negative to be valid.
                        // Provide the actual signed value (negative) and
                        // the absolute value (for insertion into text boxes).
                        dlgGPS.long_degs = model.get(row).longitude;
                        dlgGPS.set_values_from_decimal_degs();
                        dlgGPS.depth = model.get(row).depth;
                        dlgGPS.position_number = model.get(row).position;
                        console.debug("LocIdx/Posn before edit=(" + model.get(row).fishing_location + "/" +
                                dlgGPS.position_number + ").");
                        dlgGPS.open();
                    }

                    function deleteGPS(row) {
                        if (row < 0 || row > tvLocations.rowCount) {
                            console.warn("deleteGPS got bad row, not deleting");
                            return;
                        }

                        var position = model.get(row).position;

                        console.debug("Location row# = '" + row + ", position# = " + position + ".");
                        appstate.hauls.locations.delete_location_by_position(position);
                        // Disable the Edit and Delete buttons
                        enable_add_and_delete(false);
                        appstate.hauls.refresh();
                    }

                    function selectRowJustEdited() {
                        console.debug("tvLocations.idxLocationLastChanged = " +
                                tvLocations.idxLocationLastChanged);
                        var editedRow = getRowFromLocationIndex(tvLocations.idxLocationLastChanged);
                        if (editedRow >= 0 && editedRow < tvLocations.model.count) {
                            tvLocations.selection.clear();
                            tvLocations.selection.select(editedRow);
                            tvLocations.currentRow = editedRow;
                        } else {
                            console.error("Unable to select edited row. Model count = " + tvLocations.model.count);
                        }
                    }

                    // Knowing a location's primary key index, ask the model what row that's being displayed on.
                    function getRowFromLocationIndex(location_idx) {
                        var vrow;
                        for (vrow = 0; vrow < tvLocations.model.count; vrow++) {
                            if (tvLocations.model.get(vrow).fishing_location == location_idx) {
                                console.debug("Found location idx " + location_idx + " at view row " + vrow);
                                return vrow;
                            }
                        }
                        console.error("Could not find view row for location at index " + location_idx);
                        return -1;
                    }

                    GPSEntryDialog {
                        id: dlgGPS
                        enable_audio: ObserverSettings.enableAudio
                        onAccepted: {
                            tvLocations.idxLocationLastChanged = appstate.hauls.locations.add_update_location(
                                        position_number, // position number
                                        CommonUtil.get_date_str(time_val), // date - todo ISO
                                        lat_degs, // latitude
                                        long_degs, // longitude
                                        depth // depth (m)
                                        );
                            console.debug("Post-editGPS/Accepted location currentRow = " + tvLocations.currentRow +
                                    ", tvLocations.row = " + tvLocations.row +
                                     ", DB idx = " + tvLocations.idxLocationLastChanged);
                            dlgGPS.clear();

                            // Select the location just edited (whose row number may have changed by the edit)
                            // ## Kludge alert: a delay is needed to let view model complete its update.
                            delay(50, tvLocations.selectRowJustEdited);

                            tvLocations.enable_add_and_delete(true);
                            appstate.hauls.refresh();
                        }
                    }
                }
                ColumnLayout {
                    Layout.preferredWidth: 300
                    GridLayout {
                        columns: 1
                        Label {}  // temp spacer
                        FramButton {
                            id: btnAddLocation
                            fontsize: 20
                            text: "Add Location"
                            onClicked: {
                                dlgGPS.clear();
                                dlgGPS.position_number = tvLocations.model.count - 1;
                                dlgGPS.sub_title = tvLocations.get_position_desc(dlgGPS.position_number);
                                dlgGPS.open();
                            }
                        }
                        FramButton {
                            id: btnEditLocation
                            fontsize: 20
                            text: "Edit Location"
                            state: "disabled"
                            onClicked: {
                                console.debug("Edit Location currentRow = " + tvLocations.currentRow);
                                tvLocations.editGPS(tvLocations.currentRow);
                            }


                            states: [
                                State {
                                    name: "enabled" // All needed fields have been filled in
                                    PropertyChanges {
                                        target: btnEditLocation
                                        enabled: true
                                        text_color: "black"
                                        //bold: true
                                    }
                                },
                                State {
                                    name: "disabled"
                                    PropertyChanges {
                                        target: btnEditLocation
                                        enabled: false
                                        text_color: "gray"
                                        bold: false
                                    }
                                }
                            ]
                        }
                        FramButton {
                            id: btnDeleteLocation
                            fontsize: 20
                            text: "Delete Location"
                            state: "disabled"

                            onClicked: {
                                console.debug("Delete Location currentRow = " + tvLocations.currentRow);
                                tvLocations.deleteGPS(tvLocations.currentRow);
                            }

                            states: [
                                State {
                                    name: "enabled" // All needed fields have been filled in
                                    PropertyChanges {
                                        target: btnDeleteLocation
                                        enabled: true
                                        text_color: "black"
                                        //bold: true
                                    }
                                },
                                State {
                                    name: "disabled"
                                    PropertyChanges {
                                        target: btnDeleteLocation
                                        enabled: false
                                        text_color: "gray"
                                        bold: false
                                    }
                                }
                            ]
                        }
                    }
                }

            }

    } // GridLayout

    Rectangle {
     id: keyboardFrame // add a background for the autocomplete dropdown
     color: ObserverSettings.default_bgcolor
     visible: slidingKeyboard.visible
     height: slidingKeyboard.height
     width: parent.width
     x: slidingKeyboard.x - 25
     y: slidingKeyboard.y
    }

    FramWideKeyboardAndList {
        id: slidingKeyboard
        desired_height: 365
        opaque: true
        enable_audio: ObserverSettings.enableAudio
        onButtonOk: {
            resetfocus();
            if(current_ac)
                current_ac.showautocompletebox(false);
        }
    }

    FramNumPad {
        id: framNumPadDetails
        x: 328
        y: 327
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter
        visible: false
        enable_audio: ObserverSettings.enableAudio
    }

    Rectangle {
     id: keyboardFrame2 // add a background for the autocomplete dropdown
     color: ObserverSettings.default_bgcolor
     visible: keyboardMandatory.visible
     height: keyboardMandatory.height
     width: parent.width
     x: keyboardMandatory.x - 25
     y: keyboardMandatory.y
    }

    FramWideKeyboardAndList {
        id: keyboardMandatory
        desired_height: 365
        opaque: true
        mandatory_autocomplete: true
        enable_audio: ObserverSettings.enableAudio

        onButtonOk: {
            resetfocus();
        }

    }

}
