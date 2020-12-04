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
        return "set_details_state";
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

    property bool setDetailsComplete: true
    onSetDetailsCompleteChanged: {
        framHeader.forwardEnable(setDetailsComplete);
    }

    property string noScaleText: "-1"; // Stored in DB instead of cal value

    function updateLabelHighlightingOfRequiredFields() {
        // Update highlighting - normal font if specified, bold/underlined if not
        // All these labels should be of type FramLabelHighlightCapable

        // TODO Highlighting for Required fields for Sets - other fields
        labelOTCWeight.highlight(!appstate.sets.requiredSetFieldIsSpecified("otc_weight_method"));
        labelGearType.highlight(!appstate.sets.requiredSetFieldIsSpecified("gear_type"));
        lblBiolist.highlight(appstate.sets.currentBiolistNum === 0);
        labelBeaufortScale.highlight(!appstate.sets.requiredSetFieldIsSpecified("beaufort_value"));
        labelSeabird.highlight(!appstate.sets.requiredSetFieldIsSpecified("deterrent_used"));
    }

    function checkRequiredFieldsAreSpecified() {
        // Allow navigation to Catch screen if all required fields are specified.
        var newDetailsComplete = appstate.sets.requiredSetsFieldsAreSpecified;
        if (newDetailsComplete !== detailsPageItem.setDetailsComplete) {
//            console.info("Change in property setDetailsComplete from " + detailsPageItem.setDetailsComplete + " to " +
//                newDetailsComplete);
            detailsPageItem.setDetailsComplete = newDetailsComplete;
        }
        updateLabelHighlightingOfRequiredFields();
    }

    function initUI() {
        // console.debug("initUI");
        slidingKeyboard.showbottomkeyboard(false);
        keyboardMandatory.showbottomkeyboard(false);

        // set fishing_activity_id in catches, but when we get to sets, so it always reflects the actual current faid
        console.info("Setting appstate.catches.currentFishingActivityId to " + appstate.sets.current_fishing_activity_id)
        appstate.catches.currentFishingActivityId = appstate.sets.current_fishing_activity_id

        var cal_weight = appstate.sets.getData('cal_weight');
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
        appstate.catches.recalcOTCFG()  // recalc when loading screen
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

        property int labelColWidth: 210
        property int dataColWidth: Math.min( 400, root.width/2 - 50) // limit width

            RowLayout {
                FramLabelHighlightCapable {
                    id: labelCalcOTC
                    text: qsTr("Calc. OTC")
                    Layout.preferredWidth: gridHaulDetails.labelColWidth
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25
                }
                TextField {
                    id: tfCalcOTC
                    Layout.preferredWidth: 150
                    Layout.preferredHeight: ObserverSettings.default_tf_height
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 22
                    placeholderText: rowOTCMethod.current_wm == "6" ? "Blank (WM6)" : labelCalcOTC.text
                    text: handleOtcTxt(appstate.sets.getData('observer_total_catch'))
                    readOnly: true

                    // handle different types of otcs emitted here
                    function handleOtcTxt(otc) {
                        // customize how blank strings, 0s are shown here
                        var otcTxt = ""
                        if(otc === 0) {
                            otcTxt = "0.0"
                        } else if (!otc) {
                            otcTxt = ""
                        } else {
                            otcTxt = otc.toFixed(2)
                        }
                        tfCalcOTC.text = otcTxt
                    }
                    // emitted with setData(otc) or hooks count changed
                    Connections {
                        target: appstate.sets
                        onOtcFGWeightChanged: tfCalcOTC.handleOtcTxt(otc)
                    }
                    // emitted when otc is recalculated
                    Connections {
                        target: appstate.catches
                        onOtcFGWeightChanged: tfCalcOTC.handleOtcTxt(otc_fg)
                    }
                }
                FramLabelHighlightCapable {
                    id: labelOTCWeight
                    text: qsTr("OTC Weight Method")
                    Layout.preferredWidth: gridHaulDetails.labelColWidth * 1.2
                    Layout.fillHeight: true

                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignRight
                    font.pixelSize: 25
                }
                RowLayout {
                    id: rowOTCMethod
                    ExclusiveGroup {
                        id: groupOTCWeight
                    }

                    property var current_wm: choose_initial_wm()

                    function choose_initial_wm() {
                        var db_val = appstate.sets.getData('otc_weight_method');
                        if (db_val)
                            return db_val;
                        else
                            appstate.sets.setData('otc_weight_method', "11");
                            return "11"; // Default OTC WM
                    }

                    Repeater {
                        model: ["8", "11", "6"]
                        ObserverGroupButton {
                            Layout.preferredWidth: 50
                            Layout.preferredHeight: 50
                            exclusiveGroup: groupOTCWeight
                            text: modelData
                            checked: modelData === rowOTCMethod.current_wm ? true: false
                            onClicked: {
                                initUI();
                                rowOTCMethod.current_wm = modelData;
                                appstate.sets.setData('otc_weight_method', modelData);
                                checkRequiredFieldsAreSpecified();
                                if (modelData == "6") {
                                    console.info("User selected WM 6, clear OTC");
                                    dlgWM6Comment.open();

                                } else {
                                    console.info("User selected OTC WM " + modelData);
                                }
                                appstate.catches.recalcOTCFG()  // otc is WM-dependent
                            }
                        }
                    }
                    FramNoteDialog {
                        id: dlgWM6Comment
                        message: "Note: Comment is required for OTC WM 6\ndocumenting the scenario and visual/vessel\nestimates for Retained Catch"
                        font_size: 18
                        width: 400
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
                    text: appstate.sets.getDataOrSetDefault('target_strategy') ? appstate.sets.getDataOrSetDefault('target_strategy') : ""
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
                        if (text !== appstate.sets.getData('target_strategy')) {
                            appstate.sets.setData('target_strategy', text);
                            text = appstate.sets.getData('target_strategy'); // translated
                            checkRequiredFieldsAreSpecified();
                        }
                    }
                }

                FramLabelHighlightCapable {
                    id: labelSeabird
                    text: "Seabird\nAvoidance"
                    Layout.preferredWidth: 100
                    font.pixelSize: 20
                    horizontalAlignment: Text.AlignRight
                    visible: appstate.sets.requireSeabird
                }
                RowLayout {
                    id: rowSeabird
                    visible: appstate.sets.requireSeabird
                    ExclusiveGroup {
                        id: groupSeabird
                    }
                    function check_seabird(label) {
                        var deterrent = appstate.sets.getData('deterrent_used'); // Seabird
                        if ((label === "Y" && deterrent === "1") || (label === "N" && deterrent === "0"))
                            return true;
                        else
                            return false;
                    }

                    Repeater {
                        model: ["Y", "N"]
                        ObserverGroupButton {
                            Layout.preferredWidth: 50
                            Layout.preferredHeight: 50
                            checked: rowSeabird.check_seabird(modelData)
                            exclusiveGroup: groupSeabird
                            text: modelData
                            onClicked: {
                                initUI();
                                if (modelData == "Y") {
                                    appstate.sets.setData('deterrent_used', true);
                                } else {
                                    appstate.sets.setData('deterrent_used', false);
                                }
                                checkRequiredFieldsAreSpecified();
                            }
                        }
                    }
                }

                FramLabelHighlightCapable {
                    id: labelEFP
                    text: qsTr("EFP?")
                    Layout.preferredWidth: gridHaulDetails.labelColWidth / 2
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
                        var efp = appstate.sets.getDataOrSetDefault('efp');
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
                                    appstate.sets.setData('efp', true);
                                } else {
                                    appstate.sets.setData('efp', false);
                                }
                                checkRequiredFieldsAreSpecified();
                            }
                        }
                    }
                }

                FramLabelHighlightCapable {
                    id: lblBiolist
                    text: "Biolist"
                    Layout.preferredWidth: 100
                    font.pixelSize: 25
                    horizontalAlignment: Text.AlignRight
                }
                RowLayout {
                    id: rowBiolist
                    ExclusiveGroup {
                        id: groupBiolist
                    }
                    property string nsfg_label: "NSFG\n(4)"
                    property string non_nsfg_label: "Non-\nNSFG\n(5)"

                    function isCheckedBioList(label) {
                        if (appstate.sets.currentBiolistNum <= 0)
                            return false;
                        var isNSFG = appstate.sets.currentBiolistNum === 4 ? true : false;
                        if (label === rowBiolist.nsfg_label && isNSFG || label === rowBiolist.non_nsfg_label && !isNSFG)
                            return true;
                        else
                            return false;
                    }

                    Repeater {
                        model: [rowBiolist.nsfg_label, rowBiolist.non_nsfg_label]
                        ObserverGroupButton {
                            Layout.preferredWidth: 70
                            Layout.preferredHeight: 70
                            checked: rowBiolist.isCheckedBioList(modelData)
                            exclusiveGroup: groupBiolist
                            text: modelData
                            font_size: 18
                            onClicked: {
                                initUI();
                                if (modelData == rowBiolist.nsfg_label) {
                                    appstate.sets.currentBiolistNum = 4;
                                } else {
                                    appstate.sets.currentBiolistNum = 5;
                                }
                                checkRequiredFieldsAreSpecified();
                            }
                        }
                    }
                }
//                ObserverTextField {
//                    id: bioListText
//                    readOnly: true
//                    text: appstate.sets.currentBiolistNum
//                    font.pixelSize: 25
//                    Layout.preferredHeight: 50
//                    Layout.preferredWidth: 50
//                }

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
                        text: appstate.sets.getData('fit')
                        onActiveFocusChanged: {
                            if (focus) {
                                initUI();
                                focus = false;  // otherwise, dialogs opened forever
                                numpadFit.open()
                            }
                        }
                        onTextChanged: {
                            appstate.sets.setData('fit', text)
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
                    // TODO: Only do calculations for 7, 9, 19
                   ObserverNumPadDialog {
                        id: numpadTotalGear
                        max_digits: 5
                        placeholderText: tfTotalGearSet.placeholderText
                        enable_audio: ObserverSettings.enableAudio
                        onValueAccepted: {
                            tfTotalGearSet.text = accepted_value;
                        }
                    }
                    ObserverNumPadDialog {
                        id: numpadTotalGearLost
                        max_digits: 5
                        placeholderText: tfTotalGearLost.placeholderText
                        enable_audio: ObserverSettings.enableAudio
                        onValueAccepted: {
                            tfTotalGearLost.text = accepted_value;
                        }
                    }
                    FramLabelHighlightCapable {
                        id: labelWeightCal
                        text: qsTr("Weight\nCalib.")
                        Layout.preferredWidth: gridHaulDetails.labelColWidth / 2
                        Layout.fillHeight: true
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignRight
                        font.pixelSize: 18

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
                                appstate.sets.setData('cal_weight', text)
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
                                appstate.sets.setData('cal_weight', text)
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
                                var current_cal = appstate.sets.getData('cal_weight');
                                if (current_cal !== noScaleText) {
                                    framFooter.openComments("Scale Not Used Selected. Enter Reason: ");
                                }
                                appstate.sets.setData('cal_weight', noScaleText)
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
                        text: appstate.sets.getDataOrSetDefault('gear_type') ? appstate.sets.getDataOrSetDefault('gear_type') : ""

                        onActiveFocusChanged: {
                            if (focus) {
                                initUI();
                                autocomplete.suggest("fg_gear_types");
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
                            if (text !== appstate.sets.getData('gear_type')) {
                                appstate.sets.setData('gear_type', text);
                                text = appstate.sets.getData('gear_type'); // leading zero will be stripped.
                                console.debug("gear type in db = '" + appstate.sets.getData('gear_type') + "'");
                                console.debug("gear type in Gear Type field = '" + text + "'");
                                checkRequiredFieldsAreSpecified();
                            }
                        }
                    }


                } // nested RowLayout
            }
            RowLayout {
                Layout.columnSpan: 2
                FramLabelHighlightCapable {
                    id: labelGearPerf
                    text: qsTr("Gear Perf.")
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
                    property var current_gearperf: appstate.sets.getData('gear_performance')
                    Repeater {
                        model: ["1", "5", "7", "8"]
                        ObserverGroupButton {
                            Layout.preferredWidth: 50
                            Layout.preferredHeight: 50
                            exclusiveGroup: groupGearPerf
                            text: modelData
                            checked: modelData === rowGearPerf.current_gearperf
                            onClicked: {
                                initUI();
                                labelGearPerfDesc.setDesc(modelData);
                                appstate.sets.setData('gear_performance', modelData);
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
                    Layout.preferredWidth: gridHaulDetails.labelColWidth
                    Layout.preferredHeight: 80
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignLeft
                    font.pixelSize: 20
                    font.italic: true
                    wrapMode: Label.WordWrap
                    function setDesc(gearperf_val) {
                        text = appstate.sets.getGearPerfDesc(gearperf_val);
                    }
                }
                Label {
                    id: labelSoakTime
                    text: "Avg. Soak Time"
                    Layout.preferredWidth: gridHaulDetails.labelColWidth
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25

                }
                TextField {
                    id: tfSoakTime
                    Layout.preferredWidth: 100
                    Layout.preferredHeight: ObserverSettings.default_tf_height
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25
                    placeholderText: "Avg. Range"
                    text: appstate.sets.getData('avg_soak_time')

                    onActiveFocusChanged: {
                        if (focus) {
                            initUI();
                            autocomplete.suggest("avg_soak_times");
                            keyboardMandatory.connect_tf(tfSoakTime, "Soak Time");
                            keyboardMandatory.addAutoCompleteSuggestions(text);
                            keyboardMandatory.showbottomkeyboard(true);
                        }
                    }
                    onTextChanged: {
                        if (text !== appstate.sets.getData('avg_soak_time')) {
                            appstate.sets.setData('avg_soak_time', text);
                            text = appstate.sets.getData('avg_soak_time');
                            checkRequiredFieldsAreSpecified();
                        }
                    }
                }
            }
            RowLayout {
                Label {
                    id: labelTotalGearSet
                    text: "Total Gear\nUnits Set"
                    Layout.preferredWidth: gridHaulDetails.labelColWidth/1.5
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignRight

                    font.pixelSize: 22

                }
                TextField {
                    id: tfTotalGearSet
                    Layout.preferredWidth: gridHaulDetails.labelColWidth/2
                    Layout.preferredHeight: ObserverSettings.default_tf_height
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25
                    placeholderText: "Units Set"
                    text: appstate.sets.getData('tot_gear_segments')
                    onActiveFocusChanged: {
                        if (focus) {
                            initUI();
                            focus = false;  // otherwise, dialogs opened forever
                            numpadTotalGear.setValue(text);
                            numpadTotalGear.open()
                        }
                    }
                    onTextChanged: {
                        if (text != "" && text !="0") {
                            var gearUnits = parseInt(text);
                            appstate.sets.setData('tot_gear_segments', gearUnits)
                            var totalHooks = Math.round(gearUnits * appstate.trips.currentAvgHookCount);
                            appstate.sets.setData('total_hooks', totalHooks)
                            appstate.sets.setData('total_hooks_unrounded', gearUnits * appstate.trips.currentAvgHookCount)
                            checkRequiredFieldsAreSpecified();
                            tfTotalHooks.text = totalHooks;
                        } else if (text == "0") {
                            appstate.sets.setData('tot_gear_segments', null)
                            appstate.sets.setData('total_hooks', null)
                            appstate.sets.setData('total_hooks_unrounded', null)
                            checkRequiredFieldsAreSpecified();
                            tfTotalHooks.text = "";
                            text = "";
                        }
                    }
                }
                Label {
                    id: labelTotalHooks
                    text: "Total Hooks"
                    Layout.preferredWidth: gridHaulDetails.labelColWidth/1.5
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignRight                 
                    font.pixelSize: 22
                    enabled: false

                }
                TextField {
                    id: tfTotalHooks
                    Layout.preferredWidth: gridHaulDetails.labelColWidth/2
                    Layout.preferredHeight: ObserverSettings.default_tf_height
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25
                    readOnly: true
                    enabled: false
                    placeholderText: "Total Hooks"
                    text: appstate.sets.getData('total_hooks')
                }
                Label {
                    id: labelTotalGearLost
                    text: "Total Gear\nUnits Lost"
                    Layout.preferredWidth: gridHaulDetails.labelColWidth/1.5
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignRight

                    font.pixelSize: 22

                }
                TextField {
                    id: tfTotalGearLost
                    Layout.preferredWidth: gridHaulDetails.labelColWidth/2
                    Layout.preferredHeight: ObserverSettings.default_tf_height
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25
                    placeholderText: "Units Lost"
                    text: appstate.sets.getData('gear_segments_lost')
                    onActiveFocusChanged: {
                        if (focus) {
                            initUI();
                            focus = false;  // otherwise, dialogs opened forever
                            numpadTotalGearLost.setValue(text);

                            numpadTotalGearLost.open()
                        }
                    }
                    onTextChanged: {
                        if (text != "" && text !="0") {
                            var gearUnits = parseInt(text);
                            appstate.sets.setData('gear_segments_lost', gearUnits);
                            var totalHooksLost = Math.round(gearUnits * appstate.trips.currentAvgHookCount);
                            appstate.sets.setData('total_hooks_lost', totalHooksLost)
                            checkRequiredFieldsAreSpecified();
                            tfTotalHooksLost.text = totalHooksLost;
                        } else if (text == "0"){
                            appstate.sets.setData('gear_segments_lost', null)
                            appstate.sets.setData('total_hooks_lost', null)
                            checkRequiredFieldsAreSpecified();
                            tfTotalHooksLost.text = "";
                            text = "";
                        }
                    }
                }
                Label {
                    id: labelTotalHooksLost
                    text: "Total Hooks\n Lost"
                    Layout.preferredWidth: gridHaulDetails.labelColWidth/1.5
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignRight
                    enabled: false

                    font.pixelSize: 22

                }
                TextField {
                    id: tfTotalHooksLost
                    Layout.preferredWidth: gridHaulDetails.labelColWidth/2
                    Layout.preferredHeight: ObserverSettings.default_tf_height
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 25
                    placeholderText: "Hooks Lost"
                    text: appstate.sets.getData('total_hooks_lost')
                    readOnly: true
                    enabled: false
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
                    property var current_beaufort: appstate.sets.getData('beaufort_value')
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
                                appstate.sets.setData('beaufort_value', modelData);
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
                        text = appstate.sets.getBeaufortDesc(beaufort_val)
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
                    model: appstate.sets.locations.CurrentFishingLocationsModel
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
                        appstate.sets.locations.delete_location_by_position(position);
                        // Disable the Edit and Delete buttons
                        enable_add_and_delete(false);
                        appstate.sets.refresh();
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
                            tvLocations.idxLocationLastChanged = appstate.sets.locations.add_update_location(
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
                            appstate.sets.refresh();
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
