// High-level DSM.State with built-in Home transition

import QtQuick 2.5
import QtQml.StateMachine 1.0 as DSM

import "."
import "../common"

DSM.State {

    onEntered: {
    }
    DSM.SignalTransition {
        targetState: home_state
        signal: to_home_state
    }
}
