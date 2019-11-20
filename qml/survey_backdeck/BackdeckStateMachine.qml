import QtQuick 2.2
import QtQml.StateMachine 1.0 as DSM

DSM.StateMachine {
    initialState: sites_state
    running: true

    // Aliases to various states
    property alias sites_state: sites_state
    property alias fish_sampling_state: fish_sampling_state

    // Signals for transitioning to the different screens/states
    signal to_sites_state
    signal to_fish_sampling_state

    DSM.State {
        id: sites_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen;
            stateMachine.screen = "sites";
            if (stateMachine.previousScreen === "fishsampling") {
                if (screens.busy) return;
                screens.pop();
            }
        }
        DSM.SignalTransition {
            targetState: fish_sampling_state
            signal: to_fish_sampling_state
        } // to_haul_selection_state
    } // sites_state
    DSM.State {
        id: fish_sampling_state
        onEntered: {
            stateMachine.previousScreen = stateMachine.screen;
            stateMachine.screen = "fishsampling";
            if (stateMachine.previousScreen === "sites") {
                screens.push(Qt.resolvedUrl("FishSamplingScreen.qml"));
                fishSampling.specimensModel.populate_model()
                fishSampling.personnelModel.getRecorder()
                fishSampling.getRandomDrops();
            }
        }
        DSM.SignalTransition {
            targetState: sites_state
            signal: to_sites_state
        }
    } // fish_sampling_state
}