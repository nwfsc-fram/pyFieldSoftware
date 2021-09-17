import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Window 2.2
import QtQuick.Layouts 1.2

import "../common"
import "."

Item {
    id: main
    visible: true

    property alias textLeftBanner: framHeader.textLeftBanner
    property alias textRightBanner: framHeader.textRightBanner
    property alias framHeader: framHeader
    property var framFooter
    property var observerFooterRow  // same as framFooter
    property alias toolBar: framHeader
    property alias dlgGPS: dlgGPS

    property alias obsSM: obsSM

    property alias mainView: mainMenuView

    Timer {
        id: timerDelay
    }

    function delayCall(delayTime, cb) {
        timerDelay.interval = delayTime;
        timerDelay.repeat = false;
        timerDelay.triggered.connect(cb);
        timerDelay.start();
    }

    ObserverSM {
        id: obsSM
    }

    Rectangle { // Background for screen
        color: ObserverSettings.default_bgcolor
        anchors.fill: parent

    }

    Rectangle { // Header background
        color: "#BBBBBB"
        anchors.fill: framHeader
    }

    ObserverHeader {
        id: framHeader
        height: 50
    }

    Timer {
        id: timer
    }

    function delay(delayTime, cb) {
        timer.interval = delayTime;
        timer.repeat = false;
        timer.triggered.connect(cb);
        timer.start();
    }

    StackView {
        id: stackView
        objectName: "mainWindow"

        anchors.top: framHeader.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom


        focus: true

        Component.onCompleted: {
            framFooter = loginFooter;
            observerFooterRow = loginFooter;  // This exists throughout code, easier to have 2 aliases
            framFooter.obsSM = obsSM;

            // TEMP INSTANT NAV FOR DEVELOPMENT
//            stackView.push(Qt.resolvedUrl("BiospecimensScreen.qml"));
        }

        initialItem: Item {
            width: parent.width
            height: parent.height

            function page_state_id() { // for transitions
                return "home_state";
            }

            GridLayout {
                id: mainMenuView
                anchors.fill: parent
                anchors.margins: 50
                flow: GridLayout.TopToBottom

                columns: 2
                rows: 7

                property var butwidth: parent.width / 3 // 2.1
                property var trip_underway: (appstate.trips.currentTrip !== null)

                ListModel {
                    id: modelHomeButtons
                    ListElement {
                        name: "Start Trawl Trip"
                        link: "TripDetailsScreen.qml"
                        obsstate: "start_trawl_state"
                        item_enabled: true
                    }
                    ListElement {
                        name: "Hauls"
                        link: "HaulsScreen.qml"
                        obsstate: "hauls_state"
                        item_enabled: false
                    }
                    ListElement {
                        name: "BRD"
                        link: "NotImplementedScreen.qml"
                        obsstate: "brd_state"
                        item_enabled: false
                    }
                    ListElement {
                        name: "Species Interaction"
                        link: "NotImplementedScreen.qml"
                        obsstate: "mmsbt_state"
                        item_enabled: false
                    }
                    ListElement {
                        name: "Species Identification"
                        link: "NotImplementedScreen.qml"
                        obsstate: "mmsbt_state"
                        item_enabled: false
                    }
                    ListElement {
                        name: "Trip Discards"
                        link: "NotImplementedScreen.qml"
                        obsstate: "trip_discards_state"
                        item_enabled: false
                    }
                    ListElement {
                        name: "End Trawl Trip"
                        link: "EndTripScreen.qml"
                        obsstate: "end_trawl_state"
                        item_enabled: true
                    }
                    ListElement {
                        name: "Select Trip"
                        link: "TripSelectScreen.qml"
                        obsstate: "select_trip_state"
                        item_enabled: true
                    }
                    ListElement {
                        name: "Error Reports"
                        link: "TripErrorReportsScreen.qml"
                        obsstate: "trip_errors_state"
                        item_enabled: true
                    }
                    ListElement {
                        name: "Priority Species Report"
                        link: "NotImplementedScreen.qml"
                        obsstate: "priority_species_report_state"
                        item_enabled: false
                    }

                    ListElement {
                        name: "Upload Data"
                        item_enabled: true
                    }

                    ListElement {
                        name: "External Backup"
                        link: "BackupScreen.qml"
                        obsstate: "backup_state"
                        item_enabled: true
                    }

                    ListElement {
                        name: "Log Out"
                        item_enabled: true
                    }

                }

                function update_ui() {
                    // NOTE: Update indices if buttons reordered/ added/ etc
                    var start_edit_idx = 0;
                    var hauls_sets_idx = 1;
                    var end_idx = 6;
                    var startTrawlElem = { name: "Start Trawl Trip",
                                      link: "TripDetailsScreen.qml",
                                      obsstate: "start_trawl_state",
                                      item_enabled: true
                                    };
                    var editTrawlElem = { name: "Edit Trip #" + appstate.currentTripId,
                                      link: "TripDetailsScreen.qml",
                                      obsstate: "start_trawl_state",
                                      item_enabled: true
                                    };
                    var haulsButtonElem = {
                        name: "Hauls",
                        link: "HaulsScreen.qml",
                        obsstate: "hauls_state",
                        item_enabled: false
                    };
                    var setsButtonElem = {
                        name: "Sets",
                        link: "SetsScreen.qml",
                        obsstate: "sets_state",
                        item_enabled: false
                    };
                    var endTrawlTripElem = {
                        name: "End Trip",
                        link: "EndTripScreen.qml",
                        obsstate: "end_trawl_state",
                        item_enabled: true
                    };
                    var endFGTripElem = {
                        name: "End Trip",
                        link: "EndTripScreen.qml",
                        obsstate: "end_fg_state",
                        item_enabled: true
                    };

                    var startFGElem = { name: "Start Fixed Gear Trip",
                                      link: "TripDetailsFGScreen.qml",
                                      obsstate: "start_fg_state",
                                      item_enabled: true
                                    };
                    var editFGElem = { name: "Edit FG Trip #" + appstate.currentTripId,
                                      link: "TripDetailsFGScreen.qml",
                                      obsstate: "start_fg_state",
                                      item_enabled: true
                                    };
                    var haul_set_underway = Boolean(appstate.trips.currentTrip);
                    var isFixedGear = Boolean(appstate.isGearTypeTrawl);

                    var hauls_sets_button = modelHomeButtons.get(hauls_sets_idx);
                    var end_button = appstate.isFixedGear ? endFGTripElem : endTrawlTripElem;
                    if (isFixedGear) {
                        // Trawl
                        if (haul_set_underway) {
                            console.debug("ObserverHome showing Edit Trip")
                            hauls_sets_button.item_enabled = true;
                            end_button.item_enabled = true;
                            // FIELD-2107: Go to hauls only if fishery set (and collection method)
                            if (appstate.trips.currentFisheryName && appstate.trips.currentCollectionMethod) {
                                haulsButtonElem.item_enabled = true;
                            }
                            modelHomeButtons.set(start_edit_idx, editTrawlElem);

                        } else {
                            console.debug("ObserverHome showing Start Trip")
                            hauls_sets_button.item_enabled = false;
                            end_button.item_enabled = false;
                            haulsButtonElem.item_enabled = false;
                            modelHomeButtons.set(start_edit_idx, startTrawlElem);
                        }

                        modelHomeButtons.set(hauls_sets_idx, haulsButtonElem)
                        modelHomeButtons.set(end_idx, end_button)
                    } else {
                        // Fixed Gear
                        if (haul_set_underway) {
                            console.debug("ObserverHome showing Edit FG Trip")
                            hauls_sets_button.item_enabled = true;
                            end_button.item_enabled = true;
                            // FIELD-2107: Go to sets only if fishery set (and collection method)
                            if (appstate.trips.currentFisheryName && appstate.trips.currentCollectionMethod) {
                                setsButtonElem.item_enabled = true;
                            }
                            modelHomeButtons.set(start_edit_idx, editFGElem);

                        } else {
                            console.debug("ObserverHome showing Start Trip")
                            hauls_sets_button.item_enabled = false;
                            end_button.item_enabled = false;
                            setsButtonElem.item_enabled = false;
                            modelHomeButtons.set(start_edit_idx, startFGElem);
                        }
                        modelHomeButtons.set(hauls_sets_idx, setsButtonElem)
                        modelHomeButtons.set(end_idx, end_button)
                    }
                }

                Repeater {
                    model: modelHomeButtons
                    ObserverHomeButton {
                        text: name
                        Layout.preferredWidth: mainMenuView.butwidth
                        Layout.fillHeight: true
                        Layout.alignment: Qt.AlignHCenter
                        enabled: item_enabled
                        onClicked: {
                            if (!stackView.busy && item_enabled) {
                                // Trigger state machine transition BEFORE push
                                // (data will change upon push)
                                if (name == "Log Out") {
                                    console.log(framFooter);
                                    framFooter.confirmLogout.open()
                                    return;
                                }
                                if (name == "Upload Data") {
                                    login.dlgDBSync.initSync(appstate.users.currentUserName, appstate.users.currentUserPassword);
                                    return;
                                }

                                obsSM.state_change(obsstate);
                                stackView.push(Qt.resolvedUrl(link));
                            }
                        }
                    }
                }
            }
        }
    }

    Connections {
        target: db_sync
        onSuggestBackup: goToBackup()
    }
    function goToBackup() {
        obsSM.state_change("backup_state");
        stackView.push(Qt.resolvedUrl("BackupScreen.qml"))
    }

    function goToTripErrors() {
        obsSM.state_change("trip_errors_state");
        stackView.push(Qt.resolvedUrl("TripErrorReportsScreen.qml"))
    }
    Connections {
        target: observerFooterRow
        onClickedEndTripComplete: {
            obsSM.pendingEndTrip = true;
            delay(250, goToTripErrors);
        }
    }

    // Common Dialogs - moved here for performance reasons
    GPSEntryDialog {
        // Slow to load
        id: dlgGPS
        property var haul_num: null  // To ensure connections don't overlap - check haul being updated
        property var new_entry: false
        enable_audio: ObserverSettings.enableAudio
    }

    ObserverCCPickerDialog {
        id: dlgCCPicker
        property var haul_num: null  // To ensure connections don't overlap - check haul being updated
    }
}
