import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Controls.Styles 1.4

import "../common"
import "."

Item {
    id: detailsPageItem
    function page_state_id() { // for transitions
        return "end_trawl_state";
    }

    width: parent.width
    height: parent.height - framFooter.height
    signal resetfocus
    onResetfocus: {
        // "Clear" active focus by setting to any label
        lblTotalFishDays.forceActiveFocus();
    }

    property FramAutoComplete current_ac // Currently active autocomplete
    property TextField current_tf // Currently active textfield

    Keys.forwardTo: [framNumPadDetails, keyboardMandatory] // Required for capture of Enter key

    Component.onCompleted: {
        keyboardMandatory.showbottomkeyboard(false);
        keyboardFishTicket.showbottomkeyboard(false);
        btnAddFishTicket.state = "disabled"
        btnDeleteFishTicket.state = "disabled"
    }

    Connections {
        target: observerFooterRow
        onClickedEndTripComplete: {
            save_fields();
            db_sync.markTripForSync(appstate.currentTripId);
            framHeader.backClicked("home_state", "End Trip");
        }
    }

    function save_fields() {
        var modified_trip = appstate.trips.currentTrip;
        modified_trip.vessel_name = appstate.trips.currentVesselName;  // This will be looked up by FK in python
        // update list model entries
        appstate.trips.currentTrip = modified_trip;
        appstate.updateComments(); // FIELD-1470: This was overwriting NOTES, so re-write them here
    }

    function update_fields() {
        // Hack- Force update of fields
        appstate.trips.tripId = appstate.trips.tripId
    }

    function update_state_of_add_fish_ticket_button() {
        btnAddFishTicket.state = buttonRowTickets.add_ok() ? "enabled" : "disabled";
    }

    GridLayout
    {
        id: gridEndTrip
        anchors.fill: parent
        columns: 2
        rows: 7

        flow: GridLayout.TopToBottom
        anchors.leftMargin: 50
        anchors.rightMargin: 50
        anchors.topMargin: 0
        anchors.bottomMargin: 50

        property int labelColWidth: 200
        property int labelFontSize: 24
        property int editFontSize: 24
        property int defaultTFHeight: 50    // TextField height default

        RowLayout {

            ObserverCheckBox {
                id: checkPartialTrip
                text: "Partial Trip"
                checkbox_size: 40
                Layout.fillWidth: true
                checked: appstate.trips.getData("partial_trip")
                onCheckedChanged: {
                    appstate.trips.setData("partial_trip", checked);
                }
            }
            Rectangle { // spacer
                color: "transparent"
                Layout.preferredWidth: 10
            }

            Label {
                text: "Fish Processed\nDuring Trip"
                font.pixelSize: 20
            }

            ExclusiveGroup {
                id: grpFishProc
            }

            ObserverCheckBox {
                id: checkFishProcessedY
                text: "Yes"
                checkbox_size: 30
                Layout.fillWidth: true
                exclusiveGroup: grpFishProc
                checked: appstate.trips.getData("fish_processed") === '1'
                onCheckedChanged: {
                    if (checked) {
                        // Center OBSPROD expects '1' rather than 'T' or 'Y'
                        appstate.trips.setData("fish_processed", '1')
                    }
                }
            }
            ObserverCheckBox {
                id: checkFishProcessedN
                text: "No"
                checkbox_size: 30
                Layout.fillWidth: true
                exclusiveGroup: grpFishProc
                checked: appstate.trips.getData("fish_processed") === '0'
                onCheckedChanged: {
                    if (checked) {
                        // Center OBSPROD expects '0' rather than 'F' or 'N'
                        appstate.trips.setData("fish_processed", '0')
                    }
                }
            }
        }

        Rectangle { // spacer
            visible: !rowTotalFishing.visible
            Layout.preferredWidth: 1
        }

        RowLayout {
            id: rowTotalFishing
            visible: checkPartialTrip.checked
            Label {
                id: lblTotalFishDays
                text: qsTr("Total # of\nFishing Days")

                Layout.preferredWidth: gridEndTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: gridEndTrip.labelFontSize
            }

            TextField {
                id: textTotalFishDays
                Layout.fillWidth: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: gridEndTrip.editFontSize
                placeholderText: qsTr("Number")
                text: appstate.trips.getData("fishing_days_count") ? appstate.trips.getData("fishing_days_count") : ""
                onFocusChanged: {
                    if (focus && !framNumPadDetails.visible){
                        framNumPadDetails.visible = true;
                        framNumPadDetails.attachresult_tf(textTotalFishDays);
                        framNumPadDetails.setnumpadhint("Total Days");
                        framNumPadDetails.setnumpadvalue(text);
                        framNumPadDetails.setstate("popup_basic");
                        framNumPadDetails.show(true);
                    } else {
                        framNumPadDetails.show(false);
                    }
                }
                onTextChanged: {
                    if (text != "") {
                        appstate.trips.setData("fishing_days_count", text);
                    }
                }
            }
        }

        RowLayout {
            id: rowLogbook
            Label {
                id: labelLogbookName
                text: qsTr("Vessel Logbook\nName")
//                    Layout.fillWidth: true
                Layout.preferredWidth: gridEndTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: gridEndTrip.labelFontSize
            }
            TextField {
                id: textLogbookName
                Layout.fillWidth: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 25
                placeholderText: "Vessel Logbook"
                text: appstate.trips.getData("logbook_type") ? appstate.trips.getData("logbook_type") : ""
                onActiveFocusChanged: {
                    if (focus) {
                        autocomplete.suggest("vessel_logbooks");
                        keyboardMandatory.connect_tf(textLogbookName, placeholderText); // Connect TextField
                        keyboardMandatory.addAutoCompleteSuggestions(text); // Force display of all
                    }
                    keyboardMandatory.showbottomkeyboard(true);
                }
                onTextChanged: {
                    if (text != "") {
                        appstate.trips.setData("logbook_type", text);
                    }
                }
            }
        }

        RowLayout {
            Label {
                text: qsTr("Vessel Logbook\nPage #")
//                    Layout.fillWidth: true
                Layout.preferredWidth: gridEndTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: gridEndTrip.labelFontSize
            }
            TextField {
                id: textLogbookPageNum
                Layout.fillWidth: true
//                    Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: gridEndTrip.editFontSize
                placeholderText: qsTr("Number")
                text: appstate.trips.getData("logbook_number") ? appstate.trips.getData("logbook_number") : ""
                onFocusChanged: {
                    if (focus && !framNumPadDetails.visible){
                        framNumPadDetails.visible = true;
                        framNumPadDetails.attachresult_tf(textLogbookPageNum);
                        framNumPadDetails.setnumpadhint("Page #");
                        framNumPadDetails.setnumpadvalue(text);
                        framNumPadDetails.setstate("popup_basic");
                        framNumPadDetails.show(true);
                    } else {
                        framNumPadDetails.show(false);
                    }
                }
                onTextChanged: {
                    if (text != "") {
                        appstate.trips.setData("logbook_number", text);
                    }
                }
            }
        }

        RowLayout {
            Label {
                id: lblRP
                text: qsTr("Return Port")
//                    Layout.fillWidth: true
                Layout.preferredWidth: gridEndTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: gridEndTrip.labelFontSize
            }
            TextField {
                id: tfRetPort
                Layout.fillWidth: true
//                    Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: gridEndTrip.editFontSize
                placeholderText: lblRP.text
                text: appstate.trips.currentEndPortName
                onActiveFocusChanged: {
                    if (focus) {
                        autocomplete.fullSearch = false;
                        autocomplete.suggest("ports");
                        keyboardMandatory.connect_tf(tfRetPort, placeholderText); // Connect TextField
                    }
                    keyboardMandatory.showbottomkeyboard(true);
                }
                onTextChanged: {
                    if (text != "") {
                        appstate.trips.currentEndPortName = text;
                    }
                }
            }
        }

        RowLayout {
            Label {
                text: qsTr("Return Date/Time")
//                    Layout.fillWidth: true
                Layout.preferredWidth: gridEndTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: gridEndTrip.labelFontSize
            }
            TextField {
                id: textRetDate
                Layout.fillWidth: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: gridEndTrip.labelFontSize
                Layout.preferredHeight: tfRetPort.height
                placeholderText: qsTr("Calendar")
                text: ObserverSettings.format_date(appstate.trips.currentEndDateTime)
                onActiveFocusChanged: {
                    if (focus) {
                        focus = false;  // otherwise, dialogs opened forever
                        datePicker.message = "Return Time"
                        datePicker.open();
                    }
                }
            }
            FramDatePickerDialog {
                id: datePicker
                enable_audio: ObserverSettings.enableAudio
                onDateAccepted: {
                    textRetDate.text = CommonUtil.get_date_str(selected_date);
                    appstate.trips.currentEndDateTime = selected_date;

                }
            }
        }

        RowLayout {
            Label {
                id: lblFirstRcvr
                text: qsTr("First Receiver")
                Layout.preferredWidth: gridEndTrip.labelColWidth
//                    Layout.fillWidth: true
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: gridEndTrip.labelFontSize
            }
            TextField {
                id: tfFirstReceiver
                Layout.fillWidth: true
                // FIELD-829 Fix (EndTripScreen freezes): don't reference textRetDate.height
                //Layout.preferredHeight: textRetDate.height
                Layout.preferredHeight: gridEndTrip.defaultTFHeight
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: text.length > 0 ? 15 : gridEndTrip.editFontSize
                text: appstate.trips.firstReceiver
                placeholderText: lblFirstRcvr.text
                onActiveFocusChanged: {
                    if (focus) {
                        autocomplete.suggest("first_receivers");
                        keyboardMandatory.connect_tf(tfFirstReceiver, "First Receiver/ Port"); // Connect TextField
                        keyboardMandatory.addAutoCompleteSuggestions(text); // Force display of all
                    }
                    keyboardMandatory.showbottomkeyboard(true);
                }
                onTextChanged: {
                    if (text != "") {
                        appstate.trips.firstReceiver =  text;
                    }
                }
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignLeft
            Label {
                text: qsTr("Fish Ticket #")
                Layout.preferredWidth: gridEndTrip.labelColWidth
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignRight
                font.pixelSize: gridEndTrip.labelFontSize

            }
            TextField {
                id: textFishTicketNum
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: gridEndTrip.editFontSize
                placeholderText: qsTr("Number")
                text: appstate.trips.fishTicketNum
                onActiveFocusChanged: {
                    if (focus) {
                        keyboardFishTicket.connect_tf(textFishTicketNum, "Fish Ticket #");
                    }
                    keyboardFishTicket.showbottomkeyboard(true);
                }
                onTextChanged: {
                    appstate.trips.fishTicketNum = text;
                    update_state_of_add_fish_ticket_button();
                }
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignLeft

            Label {
                text: qsTr("State")
                Layout.preferredWidth: gridEndTrip.labelColWidth / 2
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignRight
                font.pixelSize: gridEndTrip.labelFontSize

            }
            RowLayout {
                id: rowWOC
                function clear() {
                    var b1 = repeatWOC.itemAt(0);
                    var b2 = repeatWOC.itemAt(1);
                    var b3 = repeatWOC.itemAt(2);
                    b1.checked = false;
                    b2.checked = false;
                    b3.checked = false;
                }

                ExclusiveGroup {
                    id: groupState
                }
                Repeater {
                    id: repeatWOC
                    model: ["W", "O", "C"]
                    ObserverGroupButton {
                        Layout.preferredWidth: 60
                        Layout.preferredHeight: 60
                        font_size: 20
                        exclusiveGroup: groupState
                        text: modelData

                        onClicked: {
                            appstate.trips.fishTicketState = text;
                            update_state_of_add_fish_ticket_button();
                        }
                    }
                }
            }

            RowLayout {
//                Layout.alignment: Qt.AlignLeft
//                Rectangle {
//                    color: "transparent"
//                    Layout.preferredWidth: 70
//                }
                Label {
                    text: qsTr("Date")
//                    Layout.fillWidth: true
//                        Layout.preferredWidth: gridEndTrip.labelColWidth
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: gridEndTrip.labelFontSize
                }
                TextField {
                    id: textTicketDate
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 20
                    Layout.fillWidth: true
                    placeholderText: qsTr("Calendar")
                    text: appstate.trips.fishTicketDate
                    onActiveFocusChanged: {
                        if (focus) {
                            focus = false;  // otherwise, dialogs opened forever
                            dateFishTicketPicker.message = "Date"
                            dateFishTicketPicker.open();
                        }
                    }
                    onTextChanged: {
                        if (text != "") {
                            appstate.trips.fishTicketDate = text;
                        }
                    }
                }
                FramDatePickerDialog {
                    id: dateFishTicketPicker
                    date_only: true
                    enable_audio: ObserverSettings.enableAudio
                    onDateAccepted: { // Show date only (no time)
                        textTicketDate.text = (selected_date.getMonth()+1) +
                                '/' + selected_date.getDate() +
                                '/' +  selected_date.getFullYear();
//                            appstate.trips.currentStartDateTime = datePicker.selectedDateTime;
                        update_state_of_add_fish_ticket_button();
                    }
                }
            }
        }

        RowLayout {
            id: buttonRowTickets
            Layout.alignment: Qt.AlignCenter
            Layout.preferredHeight: 50
            spacing: 20
            function add_ok() {
                return (appstate.trips.fishTicketNum.length > 0 &&
                        appstate.trips.fishTicketState.length > 0 &&
                        appstate.trips.fishTicketDate.length > 0);
            }

            ObserverSunlightButton {
                id: btnAddFishTicket
                text:"Add Fish\nTicket"
                Layout.preferredWidth: 150
                Layout.preferredHeight: 50
                onClicked: {
                    if  (buttonRowTickets.add_ok()) {
                        appstate.trips.addFishTicket();
                        textFishTicketNum.text = "";
                        textTicketDate.text = "";
                        rowWOC.clear()
                    } else {
                        // TODO warning dialog
                        console.log("Didn't insert fish ticket, not all fields filled")
                    }
                }
            }
            ObserverSunlightButton {
                id: btnDeleteFishTicket
                text:"Delete\nFish Ticket"
                Layout.preferredWidth: 150
                Layout.preferredHeight: 50
                onClicked: {
                    var row = ticketView.currentRow;
                    var ticket_num = appstate.trips.FishTicketsModel.get(row).fish_ticket_number;
                    appstate.trips.delFishTicket(ticket_num)
                    enabled = false;
                    ticketView.selection.clear();
                }
            }
        }

        ObserverTableView {
            id: ticketView
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.leftMargin: 40
            Layout.rowSpan: 4
            Layout.alignment: Qt.AlignCenter
            model: appstate.trips.FishTicketsModel

            TableViewColumn {
                role: "fish_ticket_number"
                title: "Number"
                width: 200
            }
            TableViewColumn {
                role: "fish_ticket_date"
                title: "Date"
                width: 200
            }
            TableViewColumn {
                role: "state_agency"
                title: "State"
                width: 100
            }

            onClicked: {
                btnDeleteFishTicket.state = "enabled";
            }
        }
    } // GridLayout

    Rectangle {
     id: keyboardFrame // add a background for the autocomplete dropdown
     color: ObserverSettings.default_bgcolor
     visible: keyboardMandatory.visible
     height: keyboardMandatory.height
     width: parent.width
     x: keyboardMandatory.x - 25
     y: keyboardMandatory.y
    }

    FramWideKeyboardAndList {
        id: keyboardMandatory
        desired_height: 400
        opaque: true
        mandatory_autocomplete: true
        enable_audio: ObserverSettings.enableAudio

        onButtonOk: {
            resetfocus();
            if(current_ac)
                current_ac.showautocompletebox(false);
        }
    }


    Rectangle {
     id: keyboardFrame2 // add a background for the autocomplete dropdown
     color: "darkgray"
     visible: keyboardFishTicket.visible
     height: keyboardFishTicket.height
     width: keyboardFishTicket.width + 50
     x: keyboardFishTicket.x - 25
     y: keyboardFishTicket.y
    }

    FramWideKeyboard {
        id: keyboardFishTicket
        desired_height: 365
        opaque: true
        visible: false
        width: parent.width / 2
        x: width / 2
        autocomplete_active: false
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
        onNumpadok: {
            resetfocus();
        }
    }
}
