import QtQuick 2.2
import QtQml.StateMachine 1.0 as DSM

import "."
import "../common"

DSM.StateMachine {
//    id: trawlBackdeckSM
    initialState: home_state
    running: true

    // Aliases to various states
    property alias home_state: home_state
    property alias haul_selection_state: haul_selection_state
    property alias process_catch_state: process_catch_state
    property alias qaqc_state: qaqc_state
    property alias serial_port_manager_state: serial_port_manager_state
    property alias fish_sampling_state: fish_sampling_state
    property alias weigh_baskets_state: weigh_baskets_state
//    property alias corals_sampling_state: corals_sampling_state
//    property alias salmon_sampling_state: salmon_sampling_state
    property alias special_actions_state: special_actions_state
    property alias settings_state: settings_state
    property alias network_testing_state: network_testing_state
    property alias protocol_manager_state: protocol_manager_state

    // Signals for transitioning to the different screens/states
    signal to_home_state
    signal to_haul_selection_state
    signal to_process_catch_state
    signal to_weigh_baskets_state
    signal to_fish_sampling_state
    signal to_special_actions_state
    signal to_serial_port_manager_state
    signal to_qaqc_state
    signal to_reports_state
    signal to_settings_state
    signal to_network_testing_state
    signal to_protocol_manager_state
    signal to_salmon_sampling_state
    signal to_corals_sampling_state

    DSM.State {
        id: home_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen

//            console.info('entered home_state')
            stateMachine.screen = "home"
            // TODO (Todd Hay) Call the haulSelected signal
//            settings.haul

            // #213: Update home screen with app version whenever home state is entered
            main.title = qsTr("Field Collector - Trawl Survey - Backdeck " + stateMachine.version + " - Home");
        }

        DSM.SignalTransition {
            targetState: haul_selection_state
            signal: to_haul_selection_state
        } // to_haul_selection_state
        DSM.SignalTransition {
            targetState: process_catch_state
            signal: to_process_catch_state
        } // to_process_catch_state
        DSM.SignalTransition {
            targetState: serial_port_manager_state
            signal: to_serial_port_manager_state
        } // to_serial_port_manager_state
        DSM.SignalTransition {
            targetState: qaqc_state
            signal: to_qaqc_state
        } // to_qaqc_state
        DSM.SignalTransition {
            targetState: reports_state
            signal: to_reports_state
        } // to_reports_state
        DSM.SignalTransition {
            targetState: settings_state
            signal: to_settings_state
        } // to_settings_state
        DSM.SignalTransition {
            targetState: network_testing_state
            signal: to_network_testing_state
        } // to_network_testing_state
        DSM.SignalTransition {
            targetState: protocol_manager_state
            signal: to_protocol_manager_state
        } // to_network_testing_state

    } // home_state
    DSM.State {
        id: haul_selection_state
        DSM.SignalTransition {
            targetState: home_state
            signal: to_home_state
        }

        onEntered: {
            stateMachine.previousScreen = stateMachine.screen
//            console.info('entered haul_selection_state')
            haulSelection._get_hauls_from_wheelhouse()

            stateMachine.screen = "haulselection"
            // TODO (todd.hay) - retrieve all hauls from wheelhouse computer
        }

//        signal haulSelected(int haulId)
//        onHaulSelected: {
//            stateMachine.selectedHaulId = haulId
//            console.info(is_haul_selected)
//            if (!stateMachine.haul["haul_id"])
//                is_haul_selected = false
//            else
//                is_haul_selected = true
//            console.info(is_haul_selected)
//
//        }

//        function selectHaul(haulId) {

            // Get the currently selectedHaulId
//            var currentId = stateMachine.haul["haul_id"]

            // Update the HaulsListModel + DB
//            haulSelection.HaulsModel.set_selected_haul(currentId, haulId)

//        }
    } // haul_selection_state
    DSM.State {
        id: process_catch_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen
//            console.info('entered process_catch_state')

            if (stateMachine.previousScreen == "home") {
                processCatch.initialize_lists()
                processCatch.initialize_tree()
            } else if (stateMachine.previousScreen == "weighbaskets") {

                processCatch.updateWeightCount();

            }

            // Reset the specimen to nothing
            stateMachine.specimen = {"row": -1, "parentSpecimenId": null}

            stateMachine.screen = "processcatch"

        }

        function selectSpecies(catchId) {
            var catchId = stateMachine.species["catch_id"]

        }

//        function selectHaul(haulId) {
//            var currentId = stateMachine.haul["haul_id"]
//            haulSelection.HaulsModel.set_selected_haul(currentId, haulId)
//        }

        DSM.SignalTransition {
            targetState: home_state
            signal: to_home_state
        } // to_home_state
        DSM.SignalTransition {
            targetState: weigh_baskets_state
            signal: to_weigh_baskets_state
        } // to_weigh_baskets_state
        DSM.SignalTransition {
            targetState: fish_sampling_state
            signal: to_fish_sampling_state
        } // to_fish_sampling_state
        DSM.SignalTransition {
            targetState: special_actions_state
            signal: to_special_actions_state
        } // to_special_actions_state
    } // process_catch_state
    DSM.State {
        id: weigh_baskets_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen

//            console.info('entered weigh_baskets_state')
            weighBaskets.initialize_list()

            stateMachine.screen = "weighbaskets"
        }

        DSM.SignalTransition {
            targetState: process_catch_state
            signal: to_process_catch_state
        } // to_process_catch_state
    } // weigh_baskets_state
    DSM.State {
        id: fish_sampling_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen

//            console.info("entered fish_sampling_state")

            if (stateMachine.previousScreen == "processcatch") {
                fishSampling.initialize_list()
            } else if (stateMachine.previousScreen == "specialactions") {
                var row = stateMachine.specimen["row"]
                if (row != -1) {
                    var value = fishSampling._get_special_actions_indicator(row)
                    fishSampling.model.setProperty(row, "special", value)
                }
            }

            stateMachine.screen = "fishsampling"
        }
        DSM.SignalTransition {
            targetState: process_catch_state
            signal: to_process_catch_state
        }
        DSM.SignalTransition {
            targetState: special_actions_state
            signal: to_special_actions_state
        }
    } // fish_sampling_state
    DSM.State {
        id: special_actions_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen
//            console.info("entered special_actions_state")
            if (stateMachine.previousScreen == "processcatch") {
                specialActions.standardSurveySpecimen = false;
                specialActions.initialize_process_catch_list()
            } else if (stateMachine.previousScreen == "fishsampling") {
                specialActions.standardSurveySpecimen = true;
                specialActions.initialize_fish_sampling_list()
            }
//            specialActions.initialize_list()
            specialActions.initialize_pi_project_list()

            stateMachine.screen = "specialactions"
        }
        DSM.SignalTransition {
            targetState: process_catch_state
            signal: to_process_catch_state
        }
        DSM.SignalTransition {
            targetState: fish_sampling_state
            signal: to_fish_sampling_state
        }
    } // special_actions_state
    DSM.State {
        id: serial_port_manager_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen
//            console.info('entered serial_port_manager_state')
            serialPortManager.serialPortSort()
//            serialPortManager.initialize_serial_ports()     // Does nothing currently, just returns at top

            stateMachine.screen = "serialportmanager"
        }
        DSM.SignalTransition {
            targetState: home_state
            signal: to_home_state
        } // to_home_state
    } // serial_port_manager_state
    DSM.State {
        id: settings_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen
            stateMachine.screen = "settings"
        }
        DSM.SignalTransition {
            targetState: home_state
            signal: to_home_state
        } // to_home_state
    } // settings_state
    DSM.State {
        id: network_testing_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen
            stateMachine.screen = "networktesting"
        }
        DSM.SignalTransition {
            targetState: home_state
            signal: to_home_state
        } // to_home_state
    } // network_testing_state
    DSM.State {
        id: protocol_manager_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen
            stateMachine.screen = "protocolmanager"
        }
        DSM.SignalTransition {
            targetState: home_state
            signal: to_home_state
        } // to_home_state
    } // protocol_manager_state
    DSM.State {
        id: qaqc_state
        DSM.SignalTransition {
            targetState: home_state
            signal: to_home_state
        } // to_home_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen
//            console.info('entered qaqc_state')
            stateMachine.screen = "qaqc"
        }
        onExited: {}
    } // qaqc_state
    DSM.State {
        id: reports_state
        DSM.SignalTransition {
            targetState: home_state
            signal: to_home_state
        } // to_home_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen
            stateMachine.screen = "reports"
        }
    } // reports_state
}