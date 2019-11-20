// Declarative State Machine for Observer

import QtQuick 2.5
import QtQml.StateMachine 1.0 as DSM

import "."
import "../common"

DSM.StateMachine {
    id: observerSM
    initialState: home_state
    running: true

    signal to_home_state
    signal to_backup_state
    signal to_start_trawl_state
    signal to_end_trawl_state
    signal to_start_fg_state
    signal to_end_fg_state
    signal to_logbook_state
    signal to_logbook_fg_state
    signal to_trip_errors_state
    signal to_select_trip_state
    signal to_sets_state
    signal to_set_details_state
    signal to_hauls_state
    signal to_haul_details_state
    signal to_cc_entry_state
    signal to_cc_entry_fg_state
    signal to_cc_details_state
    signal to_cc_details_fg_state
    signal to_cc_baskets_state
    signal to_species_entry_state
    signal to_species_fg_entry_state
    signal to_cw_entry_state
    signal to_tally_state // cw for FG
    signal to_bs_entry_state
    signal to_bs_details_state

    signal to_previous_state  // Define per state
    signal to_next_state  // Define per state

    signal enteringCW // custom signal for special cases
    signal enteringCWTally // custom signal for special cases
    signal enteringBio // custom signal for special cases


    // Banner Text
    property string btSp: " - "
    property string btTripNum: (appstate.trips.tripId !== "") ? "Temp. Trip #" + appstate.trips.tripId : ""
    property string btHaulSetNum: appstate.hauls.currentHaulId
    property string btVesselName: appstate.trips.currentVesselName
    property string btCatchCategory: appstate.catchCatName
    property string btSpecies: appstate.speciesName

    // Every state should set banner text appropriately
    property string bannerLeftText: ""
    property string leftButtonStateName: "" // set to desired state when left clicked
    property string bannerRightText: ""
    property string rightButtonStateName: "" // set to desired state when left clicked
    property string titleText: ""
    property string currentStateName: ""

    // At end of trip, show buttons once
    property bool pendingEndTrip: false


    Component.onCompleted: {
        console.log('Observer SM Loaded')
    }
    function haulBannerUpdate() {
            var isTrawl = !appstate.isFixedGear;
            btHaulSetNum = isTrawl ? "Haul #" +
                           appstate.hauls.currentHaulId : "Set #" +
                           appstate.sets.currentSetId;
    }


    function getBannerRightTextSpeciesOrBiospecimens() {
        // Forward navigation from Catch Categories's subsidiary Details or Baskets screens
        // is typically to "Species", but to "Biospecimens" if sample method is NSC.
        if (appstate.catches.currentSampleMethodIsSpeciesComposition) {
            return "Species";
        } else if (appstate.catches.currentSampleMethodIsNoSpeciesComposition) {
            // Hide forward navigation to Biospecimens if Catch Category has no matching species
            // (Adding a Biospecimen requires a species).
            return (appstate.catches.currentMatchingSpeciesId !== null) ? "Biospecimens" : "";
        } else {
            // Default to showing Species rather than empty string - better visual cue.
            // Use Species rather than Biospecimens because SM of 1, 2, or 3 is more likely than NSC.
            return "Species";
        }
    }

    function accessToWM3BasketsScreenIsNeeded() {
        return (appstate.catches.weightMethod === '3');
    }

    function getBannerRightTextForCatchCatDetails() {
        // Forward navigation from Catch Categories's subsidiary Details screen
        // is typically to "Species" or to "Biospecimens" if sample method is NSC.
        // If Weight Method is 3, then its forward navigation is to the Catch Categories WM3 Baskets screen.
        if (!accessToWM3BasketsScreenIsNeeded()) {
            return getBannerRightTextSpeciesOrBiospecimens();
        } else {
            return "WM3 Baskets";
        }
    }

    function getBannerRightTextForCatchCatBaskets() {
        // Forward navigation from Catch Categories's subsidiary Baskets screens (shown only if Weight Method == '3')
        // is to "Species" (WM3 and SM=NSC is not supported, so no nav to "Biospecimens".
        // But do the check just in case WM3+NSC non-support changes.
        return getBannerRightTextSpeciesOrBiospecimens();
    }

    function state_change(state_name) {
        // The reason for this helper function is so you can embed a string property
        // in a list element (e.g. property obsstate: "backup_state") for navigation
        // (See the ListModel in ObserverHome.qml)
        console.debug("state change requested: " + state_name)
        switch(state_name) {
            // State name string -> emit appropriate signal
            case "home_state":
                obsSM.to_home_state();
                break;
            case "backup_state":
                obsSM.to_backup_state();
                break;
            case "start_trawl_state":
                obsSM.to_start_trawl_state();
                break;
            case "end_trawl_state":
                obsSM.to_end_trawl_state();
                break;
            case "start_fg_state":
                obsSM.to_start_fg_state();
                break;
            case "end_fg_state":
                obsSM.to_end_fg_state();
                break;
            case "trip_errors_state":
                obsSM.to_trip_errors_state();
                break;
            case "select_trip_state":
                obsSM.to_select_trip_state();
                break;
            case "logbook_state":
                obsSM.to_logbook_state();
                break;
            case "logbook_fg_state":
                obsSM.to_logbook_fg_state();
                break;
            case "sets_state":
                obsSM.to_sets_state();
                break;
            case "set_details_state":
                obsSM.to_set_details_state();
                break;
            case "hauls_state":
                obsSM.to_hauls_state();
                break;
            case "haul_details_state":
                obsSM.to_haul_details_state();
                break;
            case "cc_entry_state":
                obsSM.to_cc_entry_state();
                break;
            case "cc_entry_fg_state":
                obsSM.to_cc_entry_fg_state();
                break;
            case "cc_details_state":
                obsSM.to_cc_details_state();
                break;
            case "cc_details_fg_state":
                obsSM.to_cc_details_fg_state();
                break;
            case "cc_baskets_state":
                obsSM.to_cc_baskets_state();
                break;
            case "species_entry_state":
                obsSM.to_species_entry_state();
                break;
            case "species_fg_entry_state":
                obsSM.to_species_fg_entry_state();
                break;
            case "tally_state": // cw entry for tally
                obsSM.to_tally_state();
                break;
            case "bs_entry_state":
                obsSM.to_bs_entry_state();
                break;
            case "bs_details_state":
                obsSM.to_bs_details_state();
                break;
            default:
                console.error("Unknown state change requested: " + state_name)
        }
    }

    DSM.State {
        id: home_state
        onEntered: {
            console.info(">>>>----> Entered HOME state");
            currentStateName = "home_state";
            framFooter.state = "home"
            bannerLeftText = btTripNum + (btVesselName == "" ? "" : btSp) + btVesselName;
            bannerRightText = ""
            leftButtonStateName = "unset";
            rightButtonStateName = "unset";
            titleText = "Home";
            main.mainView.update_ui();

        }
        DSM.SignalTransition {
            targetState: backup_state
            signal: to_backup_state
        }
        DSM.SignalTransition {
            targetState: start_trawl_state
            signal: to_start_trawl_state
        }
        DSM.SignalTransition {
            targetState: start_fg_state
            signal: to_start_fg_state
        }
        DSM.SignalTransition {
            targetState: trip_errors_state
            signal: to_trip_errors_state
        }
        DSM.SignalTransition {
            targetState: select_trip_state
            signal: to_select_trip_state
        }
        DSM.SignalTransition {
            targetState: sets_state
            signal: to_sets_state
        }
        DSM.SignalTransition {
            targetState: hauls_state
            signal: to_hauls_state
        }
        DSM.SignalTransition {
            targetState: end_trawl_state
            signal: to_end_trawl_state
        }
        DSM.SignalTransition {
            targetState: end_fg_state
            signal: to_end_fg_state
        }
    }

    ObserverSMState {
        id: backup_state
        onEntered: {
            console.info(">>>>----> Entered BACKUP state");
            currentStateName = "backup_state";
            framFooter.state = "home";
            bannerLeftText = "Home";
            bannerRightText = "";
            leftButtonStateName = "unset";
            rightButtonStateName = "unset";
            titleText = "External Backup";
        }
        DSM.SignalTransition {
            targetState: home_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: start_trawl_state
        onEntered: {
            console.info(">>>>----> Entered START TRAWL state");
            currentStateName = "start_trawl_state";
            framFooter.state = "none";
            bannerLeftText = "Home";
            bannerRightText = "Hauls" ;
            leftButtonStateName = "home_state"
            rightButtonStateName = "hauls_state"
            titleText = "Trip Details";
        }

        DSM.SignalTransition {
            targetState: home_state
            signal: to_previous_state
        }

        DSM.SignalTransition {
            targetState: hauls_state
            signal: to_next_state
        }
    }

    ObserverSMState {
        id: end_trawl_state
        onEntered: {
            console.info(">>>>----> Entered END TRAWL (Trip) state");
            currentStateName = "end_trawl_state";
            framFooter.state = "end_trip";
            bannerLeftText = "Home";
            bannerRightText = "";
            leftButtonStateName = "home_state"
            rightButtonStateName = "unset"
            titleText = "End Trip";
        }

        DSM.SignalTransition {
            targetState: home_state
            signal: to_previous_state
        }

        DSM.SignalTransition {
            targetState: hauls_state
            signal: to_next_state
        }
    }

    ObserverSMState {
        id: start_fg_state
        onEntered: {
            console.info(">>>>----> Entered START FG state");
            currentStateName = "start_fg_state";
            framFooter.state = "none";
            bannerLeftText = "Home";
            bannerRightText = "Sets";
            leftButtonStateName = "home_state"
            rightButtonStateName = "sets_state"
            titleText = "Trip Details";
        }

        DSM.SignalTransition {
            targetState: home_state
            signal: to_previous_state
        }

        DSM.SignalTransition {
            targetState: sets_state
            signal: to_next_state
        }
    }

    ObserverSMState {
        id: end_fg_state
        onEntered: {
            console.info(">>>>----> Entered END FG (Trip) state");
            currentStateName = "end_fg_state";
            framFooter.state = "end_trip";
            bannerLeftText = "Home";
            bannerRightText = "";
            leftButtonStateName = "home_state"
            rightButtonStateName = "unset"
            titleText = "End Trip";
        }

        DSM.SignalTransition {
            targetState: home_state
            signal: to_previous_state
        }

        DSM.SignalTransition {
            targetState: sets_state
            signal: to_next_state
        }
    }

    ObserverSMState {
        id: trip_errors_state
        onEntered: {
            console.info(">>>>----> Entered TRIP ERRORS state");
            currentStateName = "trip_errors_state";
            framFooter.state = "none";
            bannerLeftText = "Home";
            bannerRightText = "";
            leftButtonStateName = "unset";
            rightButtonStateName = "unset";
            titleText = "Trip Errors";

            errorReports.youAreUp && errorReports.youAreUp();
        }
        DSM.SignalTransition {
            targetState: home_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: select_trip_state
        onEntered: {
            console.info(">>>>----> Entered SELECT TRIP state");
            currentStateName = "select_trip_state";
            framFooter.state = "new_delete";
            bannerLeftText = "Home";
            bannerRightText = "";
            leftButtonStateName = "unset";
            rightButtonStateName = "unset";
            titleText = "Select Trip"
        }
        DSM.SignalTransition {
            targetState: home_state
            signal: to_previous_state
        }
        DSM.SignalTransition {
            targetState: start_trawl_state
            signal: to_start_trawl_state
        }
        DSM.SignalTransition {
            targetState: start_fg_state
            signal: to_start_fg_state
        }
    }

    ObserverSMState {
        id: logbook_state
        onEntered: {
            console.info(">>>>----> Entered LOGBOOK state");
            currentStateName = "logbook_state";
            framFooter.state = "logbook_mode";
            bannerLeftText = "Hauls";
            bannerRightText = "";
            leftButtonStateName = "hauls_state";
            rightButtonStateName = "unset";
            titleText = "Logbook Mode";
            catchCategory.setActiveListModel("Full");  // FIELD-1419
        }
        onExited: {
            appstate.hauls.refresh();
        }

        DSM.SignalTransition {
            targetState: hauls_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: logbook_fg_state
        onEntered: {
            console.info(">>>>----> Entered LOGBOOK FGstate");
            currentStateName = "logbook_fg_state";
            framFooter.state = "logbook_mode";
            bannerLeftText = "Sets";
            bannerRightText = "";
            leftButtonStateName = "sets_state";
            rightButtonStateName = "unset";
            titleText = "Logbook Mode";
            catchCategory.setActiveListModel("Full");  // FIELD-1419
        }
        onExited: {
            appstate.sets.refresh();
        }

        DSM.SignalTransition {
            targetState: sets_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: sets_state
        onEntered: {
            console.info(">>>>----> Entered SETS state");
            currentStateName = "sets_state";
            if (!appstate.isFixedGear) {
                console.error("Gear type is not set to FG.");
            }

            framFooter.state = "hauls";
            bannerLeftText = "Home"
            bannerRightText = "Add Set";
            leftButtonStateName = "home_state";
            rightButtonStateName = "set_details_state";
            appstate.catchCatName = "";
            appstate.speciesName = "";
            titleText = "Sets";

            // Let Python model underlying Hauls screen know that it's now active.
            appstate.sets.youAreUp && appstate.sets.youAreUp();
        }
        DSM.SignalTransition {
            targetState: set_details_state
            signal: to_set_details_state
        }
        DSM.SignalTransition {
            targetState: logbook_fg_state
            signal: to_logbook_fg_state
        }
        DSM.SignalTransition {
            targetState: species_fg_entry_state
            signal: to_species_fg_entry_state
        }
        DSM.SignalTransition {
            targetState: tally_state
            signal: to_tally_state
        }
        DSM.SignalTransition {
            targetState: bs_entry_state
            signal: to_bs_entry_state
        }
        DSM.SignalTransition {
            targetState: end_fg_state
            signal: to_end_fg_state
        }
        DSM.SignalTransition {
            targetState: home_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: set_details_state
        onEntered: {
            console.info(">>>>----> Entered SET DETAILS state");
            currentStateName = "set";
            framFooter.state = "logbook";
            // TODO ObserverData.py updates for set info
            bannerLeftText = "Sets"
            bannerRightText = "Catch";
            leftButtonStateName = "sets_state";
            rightButtonStateName = "cc_entry_fg_state";
            titleText = "Set " + appstate.hauls.currentHaulId + " Details";
        }
        DSM.SignalTransition {
            targetState: sets_state
            signal: to_previous_state
        }
        DSM.SignalTransition {
            targetState: logbook_fg_state
            signal: to_logbook_fg_state
        }
        DSM.SignalTransition {
            targetState: cc_entry_fg_state
            signal: to_next_state
        }
    }

    ObserverSMState {
        id: hauls_state
        onEntered: {
            console.info(">>>>----> Entered HAULS state");
            currentStateName = "hauls_state";
            if (!appstate.isGearTypeTrawl) {
                console.error("Gear type is not set to Trawl.");
            }

            framFooter.state = "hauls";
            bannerLeftText = "Home"
            bannerRightText = "Add Haul";
            leftButtonStateName = "home_state";
            rightButtonStateName = "haul_details_state";
            appstate.catchCatName = "";
            appstate.speciesName = "";
            titleText = "Hauls";

            // Let Python model underlying Hauls screen know that it's now active.
            appstate.hauls.youAreUp && appstate.hauls.youAreUp();
        }
        DSM.SignalTransition {
            targetState: haul_details_state
            signal: to_haul_details_state
        }
        DSM.SignalTransition {
            targetState: logbook_state
            signal: to_logbook_state
        }
        DSM.SignalTransition {
            targetState: species_entry_state
            signal: to_species_entry_state
        }
        DSM.SignalTransition {
            targetState: cw_entry_state
            signal: to_cw_entry_state
        }
        DSM.SignalTransition {
            targetState: bs_entry_state
            signal: to_bs_entry_state
        }
        DSM.SignalTransition {
            targetState: end_trawl_state
            signal: to_end_trawl_state
        }
        DSM.SignalTransition {
            targetState: home_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: haul_details_state
        onEntered: {
            console.info(">>>>----> Entered HAUL DETAILS state");
            currentStateName = "haul_details_state";
            framFooter.state = "logbook";
            // TODO ObserverData.py updates for set info
            bannerLeftText = "Hauls"
            bannerRightText = "Catch";
            leftButtonStateName = "hauls_state";
            rightButtonStateName = "cc_entry_state";
            titleText = "Haul " + appstate.hauls.currentHaulId + " Details";
        }
        DSM.SignalTransition {
            targetState: hauls_state
            signal: to_previous_state
        }
        DSM.SignalTransition {
            targetState: logbook_state
            signal: to_logbook_state
        }
        DSM.SignalTransition {
            targetState: cc_entry_state
            signal: to_next_state
        }
    }

    ObserverSMState {
        id: cc_entry_state

        function setCCTitleText() {
            var catchCatText = "";
            if (btCatchCategory && btCatchCategory.length > 0) {
                catchCatText = " - " + btCatchCategory;
            }
            if (appstate.isFixedGear)
                titleText = "Catch - Set " + appstate.sets.currentSetId + catchCatText;
            else
                titleText = "Catch - Haul " + appstate.hauls.currentHaulId + catchCatText;
        }
        onEntered: {
            console.info(">>>>----> Entered CATCH CATEGORIES state");
            currentStateName = "cc_entry_state";
            framFooter.state = "none";
            bannerLeftText = appstate.isFixedGear ? "Sets" : "Hauls"
            bannerRightText = "";
            leftButtonStateName = appstate.isFixedGear ? "sets_state" : "hauls_state";
            rightButtonStateName = "unset";
            setCCTitleText();
        }
        Connections {
            target: appstate
            onCatchCatNameChanged: {
                if(cc_entry_state.active) {
                    cc_entry_state.setCCTitleText();
                }
            }
        }
        DSM.SignalTransition {
            targetState: cc_details_state
            signal: to_cc_details_state
        }
        DSM.SignalTransition {
            targetState: cc_baskets_state
            signal: to_cc_baskets_state
        }
        DSM.SignalTransition {
            targetState: sets_state
            signal: to_sets_state
        }
        DSM.SignalTransition {
            targetState: hauls_state
            signal: to_hauls_state
        }
        DSM.SignalTransition {
            targetState: species_entry_state
            signal: to_species_entry_state
        }
        DSM.SignalTransition {
            targetState: cw_entry_state
            signal: to_cw_entry_state
        }
        DSM.SignalTransition {
            targetState: bs_entry_state
            signal: to_bs_entry_state
        }
        DSM.SignalTransition {
            targetState: appstate.isFixedGear ? sets_state : hauls_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: cc_entry_fg_state

        function setCCTitleText() {
            var catchCatText = "";
            if (btCatchCategory && btCatchCategory.length > 0) {
                catchCatText = " - " + btCatchCategory;
            }
            if (appstate.isFixedGear)
                titleText = "Catch - Set " + appstate.sets.currentSetId + catchCatText;
            else
                titleText = "Catch - Haul " + appstate.hauls.currentHaulId + catchCatText;
        }
        onEntered: {
            console.info(">>>>----> Entered CATCH CATEGORIES FG state");
            currentStateName = "cc_entry_fg_state";
            framFooter.state = "none";
            bannerLeftText = appstate.isFixedGear ? "Sets" : "Hauls"
            bannerRightText = "";
            leftButtonStateName = appstate.isFixedGear ? "sets_state" : "hauls_state";
            rightButtonStateName = "unset";
            setCCTitleText();
        }
        Connections {
            target: appstate
            onCatchCatNameChanged: {
                if(cc_entry_state.active) {
                    cc_entry_state.setCCTitleText();
                }
            }
        }
        DSM.SignalTransition {
            targetState: cc_details_fg_state
            signal: to_cc_details_state
        }
        DSM.SignalTransition {
            targetState: sets_state
            signal: to_sets_state
        }
        DSM.SignalTransition {
            targetState: species_fg_entry_state
            signal: to_species_fg_entry_state
        }
        DSM.SignalTransition {
            targetState: tally_state
            signal: to_tally_state
        }
        DSM.SignalTransition {
            targetState: bs_entry_state
            signal: to_bs_entry_state
        }
        DSM.SignalTransition {
            targetState: appstate.isFixedGear ? sets_state : hauls_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: cc_details_state
        onEntered: {
            console.info(">>>>----> Entered CC DETAILS state");
            currentStateName = "cc_details_state";
            framFooter.state = "none"
            bannerLeftText = "Catch Categories";
            bannerRightText = getBannerRightTextForCatchCatDetails();
            leftButtonStateName = "tabs_screen";
            rightButtonStateName = accessToWM3BasketsScreenIsNeeded()? "cc_baskets_state": "tabs_screen";
            titleText = "Details: " + btCatchCategory;
        }
        DSM.SignalTransition {
            targetState: cc_entry_state
            signal: to_previous_state
        }
        DSM.SignalTransition {
            // weird case where we go back to cc_entry_state first
            // and jump forward to Species is handled in observerHeader.forwardClicked
            targetState: !accessToWM3BasketsScreenIsNeeded()? cc_entry_state: cc_baskets_state
            signal: to_next_state
        }
        Connections {
            target: appstate.catches
            onSampleMethodChanged: {
                if(cc_details_state.active) {
                    console.debug("Got signal that Sample Method changed on Catch Categories Details.");
                    bannerRightText = getBannerRightTextForCatchCatDetails();
                }
            }
            onWeightMethodChanged: {
                if(cc_details_state.active) {
                    console.debug("Got signal that Weight Method changed on Catch Categories Details.");
                    bannerRightText = getBannerRightTextForCatchCatDetails();
                    rightButtonStateName = accessToWM3BasketsScreenIsNeeded()? "cc_baskets_state": "tabs_screen";
                }
            }
        }
    }

    ObserverSMState {
        id: cc_details_fg_state
        onEntered: {
            console.info(">>>>----> Entered CC DETAILS FG state");
            currentStateName = "cc_details_fg_state";
            framFooter.state = "none"
            bannerLeftText = "Catch Categories";
            bannerRightText = getBannerRightTextForCatchCatDetails();
            leftButtonStateName = "tabs_screen";
            // TODO update this for FG:
            rightButtonStateName = accessToWM3BasketsScreenIsNeeded()? "cc_baskets_state": "tabs_screen";
            titleText = "Details: " + btCatchCategory;
        }
        DSM.SignalTransition {
            targetState: cc_entry_fg_state
            signal: to_previous_state
        }
        DSM.SignalTransition {
            // weird case where we go back to cc_entry_state first
            // and jump forward to Species is handled in observerHeader.forwardClicked
            targetState: cc_entry_fg_state
            signal: to_next_state
        }
        Connections {
            target: appstate.catches
            onSampleMethodChanged: {
                if(cc_details_fg_state.active) {
                    console.debug("Got signal that Sample Method changed on Catch Categories Details.");
                    bannerRightText = getBannerRightTextForCatchCatDetails();
                }
            }
            onWeightMethodChanged: {
                if(cc_details_fg_state.active) {
                    console.debug("Got signal that Weight Method changed on Catch Categories Details.");
                    bannerRightText = getBannerRightTextForCatchCatDetails();
                    rightButtonStateName = accessToWM3BasketsScreenIsNeeded()? "cc_baskets_state": "tabs_screen";
                }
            }
            onSpeciesCompChanged: {
                if(cc_details_fg_state.active) {
                    console.debug("Got signal that Species Comp Yes/No changed on Catch Categories Details.");
                    bannerRightText = getBannerRightTextForCatchCatDetails();
                }
            }
        }
    }

    ObserverSMState {
        id: cc_baskets_state
        onEntered: {
            console.info(">>>>----> Entered CC BASKETS (WM3) state");
            currentStateName = "cc_baskets_state";
            framFooter.state = "none"
            bannerLeftText = "Catch Categories";    // Considered returning to Details, but CC main seems better.
            bannerRightText = getBannerRightTextForCatchCatBaskets();
            leftButtonStateName = "tabs_screen";
            rightButtonStateName = "tabs_screen";
            titleText = "WM3 Baskets: " + btCatchCategory;
        }
        DSM.SignalTransition {
            targetState: cc_entry_state
            signal: to_previous_state
        }
        DSM.SignalTransition {
            // weird case where we go back to cc_entry_state first
            // and jump forward to Species is handled in observerHeader.forwardClicked
            targetState: cc_entry_state
            signal: to_next_state
        }
        // This signal handler is not at present needed because WM3 in combination with SM=NSC is not supported.
        // I.e., the forward navigation for cc_baskets is always to Species.
        Connections {
            target: appstate.catches
            onSampleMethodChanged: {
                if(cc_baskets_state.active) {
                    console.debug("Got signal that Sample Method changed on Catch Categories Details.");
                    bannerRightText = getBannerRightTextForCatchCatBaskets();
                }
            }
        }
    }

    ObserverSMState {
        id: species_entry_state

        function setSpeciesText() {
            var retained_text =
                    (appstate.catches.biospecimens.currentCatchDisposition === 'R') ?
                        " - (Retained)" : "";
            titleText = "Catch - Haul " + appstate.hauls.currentHaulId + " - " + btCatchCategory +
                    (appstate.speciesName.length > 0 ? " - " + appstate.speciesName : "") + retained_text;
        }

        onEntered: {
            console.info(">>>>----> Entered SPECIES state");
            currentStateName = "species_entry_state";
            framFooter.state = "none";
            setSpeciesText();
        }
        Connections {
            target: appstate
            onSpeciesNameChanged: {
                if(species_entry_state.active) {
                    species_entry_state.setSpeciesText();
                }
            }
        }
        DSM.SignalTransition {
            targetState: hauls_state
            signal: to_hauls_state
        }
        DSM.SignalTransition {
            targetState: cc_entry_state
            signal: to_cc_entry_state
        }
        DSM.SignalTransition {
            targetState: cw_entry_state
            signal: to_cw_entry_state
        }
        DSM.SignalTransition {
            targetState: tally_state
            signal: to_tally_state
        }
        DSM.SignalTransition {
            targetState: bs_entry_state
            signal: to_bs_entry_state
        }
        DSM.SignalTransition {
            // TODO{wsmith} Needs custom back state - could be hauls or sets, or done
            targetState: hauls_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: species_fg_entry_state

        function setSpeciesText() {
            var retained_text =
                    (appstate.catches.biospecimens.currentCatchDisposition === 'R') ?
                        " - (Retained)" : "";
            titleText = "Catch - Set " + appstate.sets.currentSetId + " - " + btCatchCategory +
                    (appstate.speciesName.length > 0 ? " - " + appstate.speciesName : "") + retained_text;
        }

        onEntered: {
            console.info(">>>>----> Entered SPECIES FG state");
            currentStateName = "species_fg_entry_state";
            framFooter.state = "none";
            setSpeciesText();
        }
        Connections {
            target: appstate
            onSpeciesNameChanged: {
                if(species_fg_entry_state.active) {
                    species_fg_entry_state.setSpeciesText();
                }
            }
        }
        DSM.SignalTransition {
            targetState: sets_state
            signal: to_sets_state
        }
        DSM.SignalTransition {
            targetState: cc_entry_fg_state
            signal: to_cc_entry_fg_state
        }
        DSM.SignalTransition {
            targetState: tally_state // counts and weights + tally
            signal: to_tally_state
        }
        DSM.SignalTransition {
            targetState: bs_entry_state
            signal: to_bs_entry_state
        }
        DSM.SignalTransition {
            // TODO{wsmith} Needs custom back state - could be hauls or sets, or done
            targetState: sets_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: cw_entry_state

        function setSpeciesText() {
            var retained_text =
                    (appstate.catches.biospecimens.currentCatchDisposition === 'R') ?
                        " - (Retained)" : "";
            var speciesText = appstate.speciesName;
            titleText = "Catch - Haul " + appstate.hauls.currentHaulId + " - " + btCatchCategory + " - " + speciesText + retained_text;
        }

        onEntered: {
            console.info(">>>>----> Entered COUNTS/WEIGHTS state");
            currentStateName = "cw_entry_state";
            framFooter.state = "none";
            setSpeciesText();
            observerSM.enteringCW();
        }

        Connections {
            target: appstate
            onSpeciesNameChanged: {
                if(cw_entry_state.active) {
                    cw_entry_state.setSpeciesText();
                }
            }
        }
        DSM.SignalTransition {
            targetState: sets_state
            signal: to_sets_state
        }
        DSM.SignalTransition {
            targetState: hauls_state
            signal: to_hauls_state
        }
        DSM.SignalTransition {
            targetState: cc_entry_state
            signal: to_cc_entry_state
        }
        DSM.SignalTransition {
            targetState: species_entry_state
            signal: to_species_entry_state
        }
        DSM.SignalTransition {
            targetState: bs_entry_state
            signal: to_bs_entry_state
        }
        DSM.SignalTransition {
            // TODO{wsmith} Needs custom back state - could be hauls or sets, or done
            targetState: hauls_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: tally_state

        function setSpeciesText() {
            var retained_text =
                    (appstate.catches.biospecimens.currentCatchDisposition === 'R') ?
                        " - (Retained)" : "";
            var speciesText = appstate.speciesName;
            titleText = "Catch - Set " + appstate.sets.currentSetId + " - " + btCatchCategory + " - " + speciesText + retained_text;
        }

        onEntered: {
            console.info(">>>>----> Entered TALLY state");
            currentStateName = "tally_state";
            framFooter.state = "none";
            setSpeciesText();
            observerSM.enteringCWTally();
        }

        Connections {
            target: appstate
            onSpeciesNameChanged: {
                if(tally_state.active) {
                    tally_state.setSpeciesText();
                }
            }
        }
        DSM.SignalTransition {
            targetState: sets_state
            signal: to_sets_state
        }
        DSM.SignalTransition {
            targetState: cc_entry_fg_state
            signal: to_cc_entry_fg_state
        }
        DSM.SignalTransition {
            targetState: species_fg_entry_state
            signal: to_species_fg_entry_state
        }
        DSM.SignalTransition {
            targetState: bs_entry_state
            signal: to_bs_entry_state
        }
        DSM.SignalTransition {
            targetState: sets_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: bs_entry_state

        function setBiospecimensSpeciesText() {
            var discardReason = appstate.catches.biospecimens.currentParentDiscardReason;
            var discardReasonTitleText = "";
            console.debug("Catch disposition=" + appstate.catches.biospecimens.currentCatchDisposition +
                    "; Biospecimen discard reason = " + discardReason + ".");
            if (appstate.catches.biospecimens.currentCatchDisposition == 'R') {
                discardReasonTitleText = " - (Retained)"
            } else {

                if (discardReason && discardReason.length > 0) {
                    discardReasonTitleText = " - DR" + discardReason;
                } else {
                  discardReasonTitleText = " - DR" + appstate.catches.species.discardReason;
                }
            }
            if (appstate.isFixedGear) {
                titleText = "Set " + appstate.sets.currentSetId + " "
            } else {
                titleText = "Haul " + appstate.hauls.currentHaulId + " "
            }
            titleText += btCatchCategory +
                    " - Biospecimens - " +
                    (appstate.speciesName.length > 0 ? appstate.speciesName : "(None)") +
                    discardReasonTitleText;
        }

        onEntered: {
            console.info(">>>>----> Entered BIOSPECIMENS state");
            currentStateName = "bs_entry_state";
            framFooter.state = "none";
            setBiospecimensSpeciesText();
            observerSM.enteringBio();
       }

        Connections {
            target: appstate
            onSpeciesNameChanged: {
                if (bs_entry_state.active) {
                    bs_entry_state.setBiospecimensSpeciesText();
                }
            }
        }

        DSM.SignalTransition {
            targetState: sets_state
            signal: to_sets_state
        }
        DSM.SignalTransition {
            targetState: hauls_state
            signal: to_hauls_state
        }
        DSM.SignalTransition {
            targetState: cc_entry_state
            signal: to_cc_entry_state
        }
        DSM.SignalTransition {
            targetState: cc_entry_fg_state
            signal: to_cc_entry_fg_state
        }
        DSM.SignalTransition {
            targetState: tally_state // counts and weights + tally
            signal: to_tally_state
        }
        DSM.SignalTransition {
            targetState: species_entry_state
            signal: to_species_entry_state
        }
        DSM.SignalTransition {
            targetState: cw_entry_state
            signal: to_cw_entry_state
        }
        DSM.SignalTransition {
            targetState: bs_details_state
            signal: to_bs_details_state
        }
        DSM.SignalTransition {
            targetState: appstate.isFixedGear ? sets_state : hauls_state
            signal: to_previous_state
        }
    }

    ObserverSMState {
        id: bs_details_state
        onEntered: {
            console.info(">>>>----> Entered BS DETAILS state");
            currentStateName = "bs_details_state";
            framFooter.state = "done"
            bannerLeftText = btHaulSetNum + btSp + "Details: " + btSpecies;
            bannerRightText = "";
            leftButtonStateName = "unset";
            rightButtonStateName = "unset";
            titleText = "";
        }
        DSM.SignalTransition {
            targetState: bs_entry_state
            signal: to_previous_state
        }
    }
}



